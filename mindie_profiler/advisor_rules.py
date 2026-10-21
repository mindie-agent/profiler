"""Ascend Advisor operator anomaly and timeline fusible sequence scanner.

[Role]
  Distill Ascend ``msprof-analyze`` advisor analyzers and MindIE operator
  forensics into deterministic, pure in-memory scanners over profiler
  observations, kernel events, and optional correlated host/runtime slices.

[Invariants]
  * All four scanners are pure functions of measured events; missing shapes,
    dtypes, PMU counters, or host slices remain ``None``/``uncertain`` and are
    never fabricated as zero.
  * Sequence matching is scoped strictly within ``(rank_id, step, stream_id)``
    and never crosses communication (``is_comm``) or AICPU (``is_aicpu``)
    barriers or large inter-kernel idle gaps.
  * Every emitted match and finding preserves rank/step/window/stream/task
    evidence scopes.

[Timeouts & Locks]
  Single-pass O(N log N) sorting and linear window scans in memory.  Zero I/O,
  zero subprocesses, zero network, and zero locks.

[Side-Effect Policy]
  Pure functional transforms returning plain JSON-serializable dicts.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence

from .anomaly_discovery import KernelEvent
from .events import Event, Observation

ADVISOR_SCHEMA = "mindie-profile-advisor/1"

DTYPE_ITEMSIZE_BYTES: dict[str, int] = {
    "FLOAT": 4, "FP32": 4, "FLOAT32": 4, "DT_FLOAT": 4,
    "FLOAT16": 2, "FP16": 2, "HALF": 2, "DT_FLOAT16": 2,
    "BFLOAT16": 2, "BF16": 2, "DT_BF16": 2,
    "DOUBLE": 8, "FP64": 8, "FLOAT64": 8, "DT_DOUBLE": 8,
    "INT64": 8, "UINT64": 8, "LONG": 8, "DT_INT64": 8, "DT_UINT64": 8,
    "INT32": 4, "UINT32": 4, "INT": 4, "DT_INT32": 4, "DT_UINT32": 4,
    "INT16": 2, "UINT16": 2, "SHORT": 2, "DT_INT16": 2, "DT_UINT16": 2,
    "INT8": 1, "UINT8": 1, "BOOL": 1, "BYTE": 1, "DT_INT8": 1, "DT_UINT8": 1, "DT_BOOL": 1,
    "FP8": 1, "HIFLOAT8": 1, "FLOAT8_E4M3FN": 1, "FLOAT8_E5M2": 1, "INT4": 1, "DT_INT4": 1,
}

DOUBLE_DTYPES = {"DOUBLE", "FP64", "FLOAT64", "DT_DOUBLE", "COMPLEX64", "COMPLEX128", "DT_COMPLEX64", "DT_COMPLEX128"}

AICPU_FALLBACK_CATALOG: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    ("aicpu_nonzero_dynamic_mask", ("nonzero", "where"), "torch.where / masked_fill (static-shape mask)",
     "Dynamic boolean indexing (NonZero/Where) falls back to AI_CPU and forces host-device stream sync; replace with static-shape torch.where, masked_fill, or fixed-capacity padded buffers."),
    ("aicpu_index_scatter_gather", ("indexput", "index_put", "scatter", "gather", "indexselect", "index_select", " index"),
     "torch_npu.npu_scatter / torch_npu.npu_moe_token_permute",
     "Unaligned or unsupported-dtype scatter/gather/index_put falls back to AI_CPU; ensure contiguous int32/int64 indices and float16/bfloat16/float32 payloads, or fuse into npu_moe_token_permute."),
    ("aicpu_topk_sort_fallback", ("topk", "sort", "argsort"), "torch_npu.npu_moe_gating_top_k_softmax / float16 TopK",
     "TopK/Sort on AI_CPU indicates k exceeds AI_CORE limit or unsupported dtype (float64/int64); downcast logits to float16/bfloat16/float32 or use torch_npu.npu_moe_gating_top_k_softmax."),
    ("aicpu_cast_transdata_fallback", ("cast", "transdata", "transpose", " permute", "contiguous"),
     "torch_npu.npu_format_cast / AMP dtype alignment",
     "Format/dtype conversion on AI_CPU indicates unsupported dtype (e.g. float64/bool/int64) or non-contiguous stride layout; align mixed-precision dtypes and materialize contiguous ND tensors on AI_CORE."),
    ("aicpu_index_generator", ("arange", "range", "linspace", "unique", "multinomial", "randperm"),
     "Pre-allocated NPU int32 index buffer",
     "Index/random generation on AI_CPU inside decode step stalls dispatch; pre-allocate position/index buffers on NPU during warmup with int32/float16 dtypes."),
)

SYNC_HOST_PATTERNS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("explicit_stream_sync", ("aclrtsynchronizestream", "aclrtsynchronizedevice", "aclrtsynchronizeevent", "cudastreamsynchronize"),
     "Explicit stream/device synchronization blocks host dispatch until NPU drains; remove per-layer syncs or replace with cross-stream aclrtStreamWaitEvent."),
    ("scalar_item_d2h_sync", ("aten::item", "aten::_local_scalar_dense", ".item(", "aten::cpu", "aten::to", "aclrtmemcpy"),
     "Host scalar extraction (.item() / .cpu() / synchronous D2H memcpy) forces an implicit stream sync; keep convergence/routing predicates on device tensors or batch D2H copies at step end."),
)


@dataclass(frozen=True)
class _AdvisorKernel:
    rank_id: str
    rank_index: int | None
    step: int | None
    window_label: str | None
    name: str
    op_type: str
    task_type: str
    core: str
    stream_id: str | None
    task_id: str | None
    start_ns: int
    end_ns: int
    duration_ns: int
    is_comm: bool
    is_aicpu: bool
    input_shapes: str | None
    input_dtypes: str | None
    input_formats: str | None
    size_bytes: int | None
    pmu: Mapping[str, float | None]
    bound_family: str


@dataclass(frozen=True)
class FusionPatternRule:
    pattern_code: str
    sequence: tuple[str, ...]
    replacement_api: str
    kernel_saving_ratio: float
    guidance: str


FUSION_PATTERN_RULES: tuple[FusionPatternRule, ...] = (
    FusionPatternRule("add_rms_norm_dynamic_quant", ("Add", "RmsNorm", "DynamicQuant"), "torch_npu.npu_add_rms_norm_quant", 0.50,
                      "Fuse residual Add + RmsNorm + DynamicQuant into torch_npu.npu_add_rms_norm_quant to eliminate two intermediate HBM round-trips and two kernel launches."),
    FusionPatternRule("decomposed_rms_norm_cast_chain", ("Cast", "Pow", "ReduceMean", "Add", "Rsqrt", "Mul", "Cast"), "torch_npu.npu_rms_norm", 0.70,
                      "Replace decomposed FP32 Cast + Pow + ReduceMean + Add + Rsqrt + Mul + Cast chain with fused torch_npu.npu_rms_norm."),
    FusionPatternRule("decomposed_rms_norm", ("Pow", "ReduceMean", "Rsqrt", "Mul"), "torch_npu.npu_rms_norm", 0.65,
                      "Replace decomposed elementwise RmsNorm chain (Pow + ReduceMean + Rsqrt + Mul) with fused torch_npu.npu_rms_norm."),
    FusionPatternRule("decomposed_rms_norm_eps", ("Pow", "ReduceMean", "Add", "Rsqrt", "Mul"), "torch_npu.npu_rms_norm", 0.65,
                      "Replace decomposed elementwise RmsNorm chain (Pow + ReduceMean + Add + Rsqrt + Mul) with fused torch_npu.npu_rms_norm."),
    FusionPatternRule("rotary_pos_emb_decomposed", ("Mul", "Slice", "Neg", "Concat", "Mul", "Add"), "torch_npu.npu_rotary_mul", 0.60,
                      "Fuse decomposed RoPE elementwise chain (Mul + Slice + Neg + Concat + Mul + Add) into torch_npu.npu_rotary_mul."),
    FusionPatternRule("rotary_pos_emb_cos_sin", ("Cos", "Sin", "Mul", "Mul", "Add"), "torch_npu.npu_rotary_mul", 0.55,
                      "Fuse decomposed Cos/Sin RoPE elementwise chain into torch_npu.npu_rotary_mul."),
    FusionPatternRule("swiglu_slice_chain", ("Slice", "SiLU", "Mul"), "torch_npu.npu_swiglu", 0.50,
                      "Fuse gate/up projection Slice/Split + SiLU/Swish + Mul into torch_npu.npu_swiglu."),
    FusionPatternRule("swiglu_concat_chain", ("Concat", "SiLU", "Mul"), "torch_npu.npu_swiglu", 0.50,
                      "Fuse gate/up Concat + SiLU/Swish + Mul into torch_npu.npu_swiglu."),
    FusionPatternRule("swiglu_activation_mul", ("SiLU", "Mul"), "torch_npu.npu_swiglu", 0.45,
                      "Fuse standalone Swish/SiLU + elementwise Mul into torch_npu.npu_swiglu."),
    FusionPatternRule("moe_routing_topk_permute", ("TopK", "Scatter", "Gather"), "torch_npu.npu_moe_gating_top_k_softmax + torch_npu.npu_moe_token_permute", 0.55,
                      "Fuse un-fused MoE TopK + Scatter + Gather token routing into npu_moe_gating_top_k_softmax and npu_moe_token_permute."),
    FusionPatternRule("moe_softmax_topk_gather", ("Softmax", "TopK", "Gather"), "torch_npu.npu_moe_gating_top_k_softmax + torch_npu.npu_moe_token_permute", 0.55,
                      "Fuse Softmax + TopK + Gather/IndexSelect MoE routing chain into npu_moe_gating_top_k_softmax and npu_moe_token_permute."),
    FusionPatternRule("moe_topk_histc_scatter", ("TopK", "Histc", "Scatter"), "torch_npu.npu_moe_init_routing / torch_npu.npu_moe_token_permute", 0.55,
                      "Fuse MoE TopK + Histc + Scatter expert counting/routing into torch_npu.npu_moe_init_routing."),
    FusionPatternRule("add_rms_norm", ("Add", "RmsNorm"), "torch_npu.npu_add_rms_norm", 0.40,
                      "Fuse residual Add + RmsNorm into torch_npu.npu_add_rms_norm to avoid materializing the pre-norm residual tensor to HBM."),
    FusionPatternRule("rms_norm_dynamic_quant", ("RmsNorm", "DynamicQuant"), "torch_npu.npu_rms_norm_quant / torch_npu.npu_add_rms_norm_quant", 0.40,
                      "Fuse RmsNorm + DynamicQuant into a single quantized norm kernel to eliminate intermediate HBM I/O."),
    FusionPatternRule("redundant_cast_chain", ("Cast", "Cast"), "Single-step Cast or native mixed-precision op", 0.80,
                      "Eliminate back-to-back redundant Cast->Cast conversions on the same stream."),
)


def _ms(ns: int | float | None) -> float:
    return 0.0 if ns is None else round(float(ns) / 1_000_000.0, 6)


def _canon_op_token(op_type: str, name: str) -> str:
    raw = f"{op_type} {name}".lower()
    for needle, token in (
        ("addrmsnormquant", "FusedAddRmsNormQuant"), ("add_rms_norm_quant", "FusedAddRmsNormQuant"),
        ("addrmsnorm", "FusedAddRmsNorm"), ("add_rms_norm", "FusedAddRmsNorm"),
        ("swiglu", "FusedSwiGLU"), ("rotarymul", "FusedRotary"), ("rotary_mul", "FusedRotary"),
        ("applyrotaryposemb", "FusedRotary"), ("rmsnorm", "RmsNorm"), ("rms_norm", "RmsNorm"),
        ("layernorm", "LayerNorm"), ("layer_norm", "LayerNorm"),
        ("dynamicquant", "DynamicQuant"), ("ascendquant", "DynamicQuant"), ("quantize", "DynamicQuant"),
        ("swish", "SiLU"), ("silu", "SiLU"), ("topk", "TopK"), ("top_k", "TopK"),
        ("softmax", "Softmax"), ("histc", "Histc"), ("bincount", "Histc"),
        ("scatter", "Scatter"), ("indexput", "Scatter"), ("index_put", "Scatter"),
        ("gather", "Gather"), ("indexselect", "Gather"), ("index_select", "Gather"),
        ("groupedmatmul", "GroupedMatmul"), ("grouped_matmul", "GroupedMatmul"),
        ("matmul", "MatMul"), ("gemm", "MatMul"), ("bmm", "MatMul"),
        ("flashattention", "FlashAttention"), ("pagedattention", "FlashAttention"),
        ("transdata", "TransData"), ("transpose", "Transpose"), ("cast", "Cast"),
        ("reducesum", "ReduceMean"), ("reducemean", "ReduceMean"), ("reduce_mean", "ReduceMean"),
        ("rsqrt", "Rsqrt"), ("pow", "Pow"), ("slice", "Slice"), ("split", "Slice"), ("chunk", "Slice"),
        ("concat", "Concat"), ("cat", "Concat"), ("neg", "Neg"), ("cos", "Cos"), ("sin", "Sin"),
    ):
        if needle in raw:
            return token
    if re.search(r"(^|[^a-z])add(v2|_|d|$|[^a-z])", raw) or op_type.lower() in {"add", "addv2", "addd"}:
        return "Add"
    if re.search(r"(^|[^a-z])mul(v2|_|d|$|[^a-z])", raw) or op_type.lower() in {"mul", "mulv2", "muld"}:
        return "Mul"
    return op_type or name or "Unknown"


def _event_to_kernel(ev: Event, rank_id: str, rank_index: int | None, step: int | None, wlabel: str | None) -> _AdvisorKernel:
    dur = max(0, int(ev.end_ns) - int(ev.start_ns))
    return _AdvisorKernel(
        rank_id=str(rank_id), rank_index=rank_index, step=step, window_label=wlabel,
        name=str(ev.name or ""), op_type=str(ev.op_type or ""), task_type=str(ev.task_type or ""),
        core=str(ev.core or ""), stream_id=str(ev.stream_id) if ev.stream_id is not None else None,
        task_id=str(ev.task_id) if ev.task_id is not None else None,
        start_ns=int(ev.start_ns), end_ns=int(ev.end_ns), duration_ns=dur,
        is_comm=bool(ev.is_comm), is_aicpu=bool(ev.is_aicpu),
        input_shapes=ev.input_shapes, input_dtypes=ev.input_dtypes, input_formats=ev.input_formats,
        size_bytes=None, pmu=dict(ev.pmu) if ev.pmu else {}, bound_family=str(ev.bound_family or ""),
    )


def _coerce_kernels(
    observations: Sequence[Observation] | None = None,
    events: Sequence[Event | KernelEvent | Mapping[str, Any]] | None = None,
) -> list[_AdvisorKernel]:
    kernels: list[_AdvisorKernel] = []
    if observations:
        for obs in observations:
            for ev in obs.events:
                kernels.append(_event_to_kernel(ev, obs.rank_id, obs.rank_index, obs.window.step, obs.window.label))
    if events:
        for idx, item in enumerate(events):
            if isinstance(item, Event):
                kernels.append(_event_to_kernel(item, item.rank_id or "rank_0", item.rank_index, None, None))
            elif isinstance(item, KernelEvent):
                s_ns = int(round(float(item.start_us) * 1000.0))
                d_ns = max(0, int(round(float(item.duration_us) * 1000.0)))
                tt = str(item.task_type or item.accelerator_core or "")
                is_aicpu = "AI_CPU" in tt.upper() or "AICPU" in tt.upper()
                is_comm = any(tok in tt.upper() or tok in str(item.name).upper() for tok in ("HCCL", "COMM", "HCOM"))
                kernels.append(
                    _AdvisorKernel(
                        rank_id=f"rank_{item.rank}" if item.rank is not None else "rank_0",
                        rank_index=item.rank, step=item.step,
                        window_label=f"step_{item.step}" if item.step is not None else None,
                        name=str(item.name or ""), op_type=str(item.name or ""), task_type=tt,
                        core=str(item.accelerator_core or tt),
                        stream_id=str(item.stream_id) if item.stream_id is not None else None,
                        task_id=str(item.event_id) if item.event_id is not None else str(idx),
                        start_ns=s_ns, end_ns=s_ns + d_ns, duration_ns=d_ns,
                        is_comm=is_comm, is_aicpu=is_aicpu,
                        input_shapes=None, input_dtypes=None, input_formats=None, size_bytes=None,
                        pmu=dict(item.pmu_counters) if item.pmu_counters else {}, bound_family="",
                    )
                )
            elif isinstance(item, Mapping):
                s_ns = item.get("start_ns")
                if s_ns is None and item.get("start_us") is not None:
                    s_ns = int(round(float(item["start_us"]) * 1000.0))
                s_ns = int(s_ns or 0)
                e_ns = item.get("end_ns")
                if e_ns is None:
                    d_ns = item.get("duration_ns")
                    if d_ns is None and item.get("duration_us") is not None:
                        d_ns = int(round(float(item["duration_us"]) * 1000.0))
                    e_ns = s_ns + int(d_ns or 0)
                e_ns = int(e_ns)
                tt = str(item.get("task_type") or item.get("core") or "")
                core = str(item.get("core") or tt)
                name = str(item.get("name") or item.get("op_name") or "")
                op_type = str(item.get("op_type") or name)
                is_aicpu = bool(item.get("is_aicpu") or "AI_CPU" in tt.upper() or "AICPU" in tt.upper() or "AI_CPU" in core.upper())
                is_comm = bool(
                    item.get("is_comm")
                    or any(tok in tt.upper() or tok in op_type.upper() or tok in name.upper() for tok in ("HCCL", "COMMUNICATION", "HCOM", "SDMA"))
                )
                kernels.append(
                    _AdvisorKernel(
                        rank_id=str(item.get("rank_id") or (f"rank_{item['rank']}" if item.get("rank") is not None else "rank_0")),
                        rank_index=int(item["rank_index"]) if item.get("rank_index") is not None else (int(item["rank"]) if isinstance(item.get("rank"), int) else None),
                        step=int(item["step"]) if item.get("step") is not None else None,
                        window_label=str(item["window_label"]) if item.get("window_label") is not None else None,
                        name=name, op_type=op_type, task_type=tt, core=core,
                        stream_id=str(item["stream_id"]) if item.get("stream_id") is not None else "0",
                        task_id=str(item["task_id"]) if item.get("task_id") is not None else str(idx),
                        start_ns=s_ns, end_ns=e_ns, duration_ns=max(0, e_ns - s_ns),
                        is_comm=is_comm, is_aicpu=is_aicpu,
                        input_shapes=str(item["input_shapes"]) if item.get("input_shapes") is not None else None,
                        input_dtypes=str(item["input_dtypes"]) if item.get("input_dtypes") is not None else None,
                        input_formats=str(item["input_formats"]) if item.get("input_formats") is not None else None,
                        size_bytes=int(item["size_bytes"]) if item.get("size_bytes") is not None else None,
                        pmu=dict(item["pmu"]) if isinstance(item.get("pmu"), Mapping) else {},
                        bound_family=str(item.get("bound_family") or ""),
                    )
                )
    return kernels


def _parse_tensor_shapes(shapes_str: str | None) -> list[list[int]]:
    if not shapes_str:
        return []
    cleaned = shapes_str.strip().strip('"').strip("'")
    tensors: list[list[int]] = []
    for part in cleaned.split(";"):
        dims = [int(t.strip()) for t in part.strip().strip("[]()").split(",") if t.strip().isdigit() and int(t.strip()) > 0]
        if dims:
            tensors.append(dims)
    return tensors


def _parse_dtypes(dtypes_str: str | None) -> list[str]:
    if not dtypes_str:
        return []
    return [tok.strip().upper() for tok in re.split(r"[;,]", dtypes_str.strip().strip('"').strip("'")) if tok.strip()]


def _estimate_tensor_bytes(shapes: list[list[int]], dtypes: list[str]) -> list[int]:
    sizes: list[int] = []
    for idx, dims in enumerate(shapes):
        numel = 1
        for dim in dims:
            numel *= dim
        dtype = dtypes[idx] if idx < len(dtypes) else (dtypes[0] if dtypes else "FP16")
        sizes.append(numel * DTYPE_ITEMSIZE_BYTES.get(dtype, 2))
    return sizes


def scan_aicpu_fallbacks(
    observations: Sequence[Observation] | None = None, *,
    events: Sequence[Event | KernelEvent | Mapping[str, Any]] | None = None,
    cast_storm_min_count: int = 4, cast_storm_share_threshold: float = 0.15,
) -> dict[str, Any]:
    """Detect AICPU fallback operators, float64 dtype fallbacks, and Cast/TransData storms."""
    kernels = _coerce_kernels(observations, events)
    if not kernels:
        return {"status": "not_applicable", "aicpu_event_count": 0, "aicpu_total_ms": 0.0,
                "double_dtype_fallback_count": 0, "cast_transdata_storm_count": 0,
                "cast_transdata_total_ms": 0.0, "matches": [], "findings": []}

    total_compute_ns = sum(k.duration_ns for k in kernels if not k.is_comm)
    aicpu_kernels = [k for k in kernels if k.is_aicpu]
    grouped_aicpu: dict[tuple[str, str], list[_AdvisorKernel]] = {}
    double_dtype_count = 0

    for k in aicpu_kernels:
        text = f"{k.op_type} {k.name}".lower()
        has_double = bool(set(_parse_dtypes(k.input_dtypes)) & DOUBLE_DTYPES)
        if has_double:
            double_dtype_count += 1
        matched_code = "aicpu_generic_fallback"
        for code, needles, _, _ in AICPU_FALLBACK_CATALOG:
            if any(needle in text for needle in needles):
                matched_code = code
                break
        if matched_code == "aicpu_generic_fallback" and has_double:
            matched_code = "aicpu_double_dtype_fallback"
        grouped_aicpu.setdefault((matched_code, k.op_type or k.name), []).append(k)

    for k in kernels:
        if not k.is_aicpu and (set(_parse_dtypes(k.input_dtypes)) & DOUBLE_DTYPES):
            double_dtype_count += 1
            grouped_aicpu.setdefault(("aicpu_double_dtype_fallback", k.op_type or k.name), []).append(k)

    matches: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    catalog_lookup = {code: (api, guide) for code, _, api, guide in AICPU_FALLBACK_CATALOG}
    catalog_lookup["aicpu_double_dtype_fallback"] = (
        "tensor.to(torch.float32) / torch.bfloat16",
        "Ascend AI_CORE lacks native float64 Cube/Vector acceleration; downcast float64 tensors to float32/bfloat16/float16.",
    )
    catalog_lookup["aicpu_generic_fallback"] = (
        "torch_npu native AI_CORE operator",
        "Operator executed on AI_CPU serializes stream execution; replace with an AI_CORE-supported dtype/shape or torch_npu operator.",
    )

    for (code, op_label), group in sorted(
        grouped_aicpu.items(), key=lambda item: (-sum(x.duration_ns for x in item[1]), item[0][0], item[0][1])
    ):
        dur_ns = sum(x.duration_ns for x in group)
        api, guide = catalog_lookup[code]
        dtypes_seen = sorted({dt for x in group for dt in _parse_dtypes(x.input_dtypes)})
        dtype_issue = "float64_unsupported_on_aicore" if (set(dtypes_seen) & DOUBLE_DTYPES) else None
        scopes = [{"rank_id": x.rank_id, "step": x.step, "stream_id": x.stream_id, "task_id": x.task_id,
                   "name": x.name, "start_ns": x.start_ns, "end_ns": x.end_ns,
                   "input_shapes": x.input_shapes, "input_dtypes": x.input_dtypes} for x in group[:5]]
        matches.append({"pattern_code": code, "op_type": op_label, "count": len(group),
                        "total_duration_ms": _ms(dur_ns), "input_dtypes": dtypes_seen,
                        "dtype_issue": dtype_issue, "replacement_api": api, "guidance": guide,
                        "evidence_scopes": scopes})
        findings.append({"finding_type": "advisor_aicpu_fallback",
                         "severity": "high" if any(x.is_aicpu for x in group) else "medium", "confidence": "high",
                         "summary": f"{op_label} triggered {code} ({len(group)}x, {_ms(dur_ns):.3f} ms); replace via {api}.",
                         "evidence_ref": code, "evidence_scope": scopes[0]})

    cast_trans_kernels = [k for k in kernels if not k.is_comm and _canon_op_token(k.op_type, k.name) in {"Cast", "TransData", "Transpose"}]
    cast_trans_ns = sum(k.duration_ns for k in cast_trans_kernels)
    cast_share = (cast_trans_ns / total_compute_ns) if total_compute_ns > 0 else 0.0
    storm_detected = len(cast_trans_kernels) >= cast_storm_min_count or (len(cast_trans_kernels) >= 2 and cast_share >= cast_storm_share_threshold)
    if storm_detected:
        scopes = [{"rank_id": x.rank_id, "step": x.step, "stream_id": x.stream_id, "task_id": x.task_id,
                   "name": x.name, "op_type": x.op_type, "start_ns": x.start_ns, "end_ns": x.end_ns} for x in cast_trans_kernels[:6]]
        matches.append({"pattern_code": "cast_transdata_storm", "op_type": "Cast/TransData/Transpose",
                        "count": len(cast_trans_kernels), "total_duration_ms": _ms(cast_trans_ns),
                        "share_of_compute": round(cast_share, 6), "dtype_issue": "excessive_format_or_dtype_conversion",
                        "replacement_api": "AMP dtype alignment + contiguous ND layout + operator fusion",
                        "guidance": f"Detected {len(cast_trans_kernels)} Cast/TransData/Transpose kernels consuming {_ms(cast_trans_ns):.3f} ms ({cast_share:.1%} of compute); unify model/adapter dtypes and fold layout/dtype casts into adjacent Cube/Norm kernels.",
                        "evidence_scopes": scopes})
        findings.append({"finding_type": "advisor_cast_transdata_storm",
                         "severity": "medium" if cast_share < 0.25 else "high", "confidence": "high",
                         "summary": f"Cast/TransData storm ({len(cast_trans_kernels)} kernels, {_ms(cast_trans_ns):.3f} ms, {cast_share:.1%} of compute).",
                         "evidence_ref": "cast_transdata_storm", "evidence_scope": scopes[0]})

    return {"status": "detected" if matches else "clean", "aicpu_event_count": len(aicpu_kernels),
            "aicpu_total_ms": _ms(sum(k.duration_ns for k in aicpu_kernels)),
            "double_dtype_fallback_count": double_dtype_count,
            "cast_transdata_storm_count": len(cast_trans_kernels) if storm_detected else 0,
            "cast_transdata_total_ms": _ms(cast_trans_ns) if storm_detected else 0.0,
            "matches": matches, "findings": findings}


def scan_alignment_and_mte_contention(
    observations: Sequence[Observation] | None = None,
    *,
    events: Sequence[Event | KernelEvent | Mapping[str, Any]] | None = None,
    mte2_contention_threshold: float = 0.35,
) -> dict[str, Any]:
    """Detect 32B/512B byte & Cube/FA shape alignment violations and multi-stream MTE contention."""
    kernels = _coerce_kernels(observations, events)
    if not kernels:
        return {
            "status": "not_applicable", "alignment_violation_count": 0, "alignment_violations": [],
            "mte_contention_count": 0, "mte_contention_windows": [],
            "total_contention_overlap_ms": 0.0, "findings": [],
        }

    alignment_violations: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    for k in kernels:
        shapes = _parse_tensor_shapes(k.input_shapes)
        dtypes = _parse_dtypes(k.input_dtypes)
        tensor_bytes = [k.size_bytes] if k.size_bytes is not None else _estimate_tensor_bytes(shapes, dtypes)
        canon = _canon_op_token(k.op_type, k.name)
        reasons: list[str] = []
        rule_codes: list[str] = []

        if k.is_comm or "memcpy" in k.name.lower() or "sdma" in k.task_type.lower():
            for bsize in tensor_bytes:
                if bsize is not None and bsize > 512 and (bsize % 512 != 0):
                    rule_codes.append("sdma_512b_unaligned")
                    reasons.append(f"Communication/SDMA payload {bsize}B is not aligned to 512B burst boundary")
                    break

        for idx, bsize in enumerate(tensor_bytes):
            if bsize is None or bsize <= 0:
                continue
            if bsize % 32 != 0:
                rule_codes.append("ub_32b_unaligned")
                reasons.append(f"Tensor[{idx}] size {bsize}B violates 32B AI Core UB burst alignment")
                break
            if bsize > 512 and (bsize % 512 != 0) and canon in {"MatMul", "GroupedMatmul", "FlashAttention", "TransData"}:
                rule_codes.append("hbm_512b_unaligned")
                reasons.append(f"Tensor[{idx}] size {bsize}B violates 512B HBM burst alignment")
                break

        if canon in {"MatMul", "GroupedMatmul"} and shapes:
            for dims in shapes:
                if len(dims) >= 2:
                    m_dim, k_dim = dims[-2], dims[-1]
                    if k_dim % 16 != 0 or m_dim % 16 != 0:
                        rule_codes.append("cube_fractal_16_unaligned")
                        reasons.append(f"Cube shape {dims} is not a multiple of 16 (fractal 16x16 padding overhead)")
                        break
                    if k_dim >= 256 and (k_dim % 256 != 0):
                        rule_codes.append("cube_tile_256_unaligned")
                        reasons.append(f"Cube inner axis {k_dim} in {dims} is not aligned to 256 tile boundary")
                        break
        elif canon == "FlashAttention" and shapes:
            for dims in shapes:
                if dims[-1] % 16 != 0:
                    rule_codes.append("fa_head_dim_unaligned")
                    reasons.append(f"FlashAttention head_dim={dims[-1]} is not aligned to 16")
                    break

        if rule_codes:
            alignment_violations.append({
                "rank_id": k.rank_id, "step": k.step, "stream_id": k.stream_id, "task_id": k.task_id,
                "name": k.name, "op_type": k.op_type, "input_shapes": k.input_shapes,
                "input_dtypes": k.input_dtypes, "rule_codes": sorted(set(rule_codes)),
                "reasons": reasons, "duration_ms": _ms(k.duration_ns),
                "guidance": "Pad tensor inner dimensions/communication buffers to multiples of 32B (UB) / 512B (HBM/SDMA) and align Cube K/N axes to multiples of 16/256 to avoid hardware tail-block padding.",
            })

    if alignment_violations:
        v0 = alignment_violations[0]
        findings.append({
            "finding_type": "advisor_memory_alignment_violation", "severity": "medium", "confidence": "high",
            "summary": f"Detected {len(alignment_violations)} kernels violating 32B/512B or Cube fractal alignment (first: {v0['name']}: {v0['reasons'][0]}).",
            "evidence_ref": v0["rule_codes"][0],
            "evidence_scope": {"rank_id": v0["rank_id"], "step": v0["step"], "stream_id": v0["stream_id"], "task_id": v0["task_id"]},
        })

    contention_windows: list[dict[str, Any]] = []
    by_rank_step: dict[tuple[str, int | None], list[_AdvisorKernel]] = {}
    for k in kernels:
        if k.duration_ns > 0 and not k.is_aicpu:
            by_rank_step.setdefault((k.rank_id, k.step), []).append(k)

    for (rank_id, step), group in sorted(by_rank_step.items(), key=lambda x: (x[0][0], x[0][1] or -1)):
        ordered = sorted(group, key=lambda x: (x.start_ns, x.end_ns))
        for i, a in enumerate(ordered):
            for b in ordered[i + 1 :]:
                if b.start_ns >= a.end_ns:
                    break
                if a.stream_id is None or b.stream_id is None or a.stream_id == b.stream_id:
                    continue
                overlap_ns = min(a.end_ns, b.end_ns) - max(a.start_ns, b.start_ns)
                if overlap_ns <= 0:
                    continue
                a_mte = float(a.pmu.get("mte2_ratio") or a.pmu.get("aic_mte2_ratio") or a.pmu.get("aiv_mte2_ratio") or 0.0)
                b_mte = float(b.pmu.get("mte2_ratio") or b.pmu.get("aic_mte2_ratio") or b.pmu.get("aiv_mte2_ratio") or 0.0)
                a_canon, b_canon = _canon_op_token(a.op_type, a.name), _canon_op_token(b.op_type, b.name)
                comm_compute_pair = (a.is_comm != b.is_comm) and (
                    a_canon in {"MatMul", "GroupedMatmul", "FlashAttention", "RmsNorm"}
                    or b_canon in {"MatMul", "GroupedMatmul", "FlashAttention", "RmsNorm"}
                    or max(a_mte, b_mte) >= mte2_contention_threshold
                )
                dual_compute_mte = (not a.is_comm and not b.is_comm) and (
                    (a_mte >= mte2_contention_threshold and b_mte >= mte2_contention_threshold)
                    or ({a.bound_family, b.bound_family} <= {"cube", "vector", "memory"} and max(a_mte, b_mte) >= mte2_contention_threshold)
                )
                if comm_compute_pair or dual_compute_mte:
                    kind = "sdma_compute_mte_contention" if comm_compute_pair else "multi_stream_cube_vector_mte_contention"
                    contention_windows.append({
                        "contention_type": kind, "rank_id": rank_id, "step": step, "overlap_ms": _ms(overlap_ns),
                        "stream_a": a.stream_id, "kernel_a": a.name, "mte2_ratio_a": round(a_mte, 4) if a_mte > 0 else None,
                        "stream_b": b.stream_id, "kernel_b": b.name, "mte2_ratio_b": round(b_mte, 4) if b_mte > 0 else None,
                        "start_ns": max(a.start_ns, b.start_ns), "end_ns": min(a.end_ns, b.end_ns),
                        "guidance": "Concurrent streams are competing for HBM/L2 MTE2 bandwidth; stagger SDMA/AllToAll transfers against MTE-heavy MatMul/Vector kernels or enable fine-grained Cube-Vector tiling.",
                    })

    total_overlap_ms = round(sum(w["overlap_ms"] for w in contention_windows), 6)
    if contention_windows:
        c0 = contention_windows[0]
        findings.append({
            "finding_type": "advisor_multi_stream_mte_contention",
            "severity": "medium" if total_overlap_ms < 1.0 else "high", "confidence": "high",
            "summary": f"Multi-stream MTE contention across {len(contention_windows)} overlapping pairs ({total_overlap_ms:.3f} ms total; e.g. stream {c0['stream_a']} {c0['kernel_a']} vs stream {c0['stream_b']} {c0['kernel_b']}).",
            "evidence_ref": c0["contention_type"],
            "evidence_scope": {"rank_id": c0["rank_id"], "step": c0["step"], "stream_ids": [c0["stream_a"], c0["stream_b"]]},
        })

    return {"status": "detected" if (alignment_violations or contention_windows) else "clean",
            "alignment_violation_count": len(alignment_violations), "alignment_violations": alignment_violations,
            "mte_contention_count": len(contention_windows), "mte_contention_windows": contention_windows,
            "total_contention_overlap_ms": total_overlap_ms, "findings": findings}


def scan_host_sync_and_gc_freezes(
    observations: Sequence[Observation] | None = None,
    *,
    events: Sequence[Event | KernelEvent | Mapping[str, Any]] | None = None,
    host_events: Sequence[Mapping[str, Any]] | None = None,
    gc_gap_threshold_ms: float = 10.0,
    sync_co_occurrence_threshold: float = 0.80,
) -> dict[str, Any]:
    """Distinguish forced host stream syncs (.item()/aclrtSynchronizeStream) and Python GC freezes."""
    kernels = _coerce_kernels(observations, events)
    host_rows: list[dict[str, Any]] = []
    for h in host_events or []:
        if not isinstance(h, Mapping):
            continue
        s_ns = int(h["start_ns"]) if h.get("start_ns") is not None else int(round(float(h.get("start_us") or 0.0) * 1000.0))
        e_ns = int(h["end_ns"]) if h.get("end_ns") is not None else (
            s_ns + (int(h["duration_ns"]) if h.get("duration_ns") is not None else int(round(float(h.get("duration_us") or 0.0) * 1000.0)))
        )
        host_rows.append(
            {
                "name": str(h.get("name") or h.get("api") or ""),
                "domain": str(h.get("domain") or h.get("cat") or "host"),
                "rank_id": str(h.get("rank_id") or "rank_0"),
                "step": h.get("step"), "start_ns": s_ns, "end_ns": e_ns, "duration_ns": max(0, e_ns - s_ns),
            }
        )

    sync_matches: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    node_launch_count = 0
    stream_sync_count = 0

    for h in host_rows:
        lower = h["name"].lower()
        if "nodelaunch" in lower or "aclopcompileandexecute" in lower or ("aclnn" in lower and "launch" in lower):
            node_launch_count += 1
        for code, needles, guide in SYNC_HOST_PATTERNS:
            if any(needle in lower for needle in needles):
                if "synchronizestream" in lower:
                    stream_sync_count += 1
                sync_matches.append(
                    {
                        "pattern_code": code, "api_name": h["name"], "rank_id": h["rank_id"], "step": h["step"],
                        "start_ns": h["start_ns"], "end_ns": h["end_ns"], "duration_ms": _ms(h["duration_ns"]),
                        "guidance": guide,
                    }
                )
                break

    co_ratio = round(stream_sync_count / float(node_launch_count), 4) if node_launch_count > 0 else None
    launch_blocking = bool(co_ratio is not None and stream_sync_count >= 2 and co_ratio >= sync_co_occurrence_threshold)
    if sync_matches:
        total_sync_ms = round(sum(m["duration_ms"] for m in sync_matches), 6)
        summary = (
            f"Detected {len(sync_matches)} forced host-device synchronization calls ({total_sync_ms:.3f} ms)"
            + (f" with NodeLaunch co-occurrence {co_ratio:.2f} (ASCEND_LAUNCH_BLOCKING=1 suspected)." if launch_blocking else ".")
        )
        findings.append(
            {
                "finding_type": "advisor_forced_stream_sync", "severity": "high", "confidence": "high",
                "summary": summary, "evidence_ref": "ascend_launch_blocking" if launch_blocking else sync_matches[0]["pattern_code"],
                "evidence_scope": {"rank_id": sync_matches[0]["rank_id"], "step": sync_matches[0]["step"], "api_name": sync_matches[0]["api_name"]},
            }
        )

    gc_freezes: list[dict[str, Any]] = []
    threshold_ns = int(round(gc_gap_threshold_ms * 1_000_000.0))

    for h in host_rows:
        lower = h["name"].lower()
        if "gc" in lower or "garbage" in lower or h["domain"].lower() == "gc":
            gc_freezes.append(
                {
                    "freeze_type": "explicit_python_gc_event", "rank_id": h["rank_id"], "step": h["step"],
                    "start_ns": h["start_ns"], "end_ns": h["end_ns"], "gap_ms": _ms(h["duration_ns"]),
                    "acl_busy_ratio": 0.0, "confidence": "high",
                    "guidance": "Disable automatic cyclic garbage collection during inference decode loops (gc.disable()).",
                }
            )

    by_group: dict[tuple[str, int | None], list[_AdvisorKernel]] = {}
    for k in kernels:
        by_group.setdefault((k.rank_id, k.step), []).append(k)

    for (rank_id, step), group in sorted(by_group.items(), key=lambda x: (x[0][0], x[0][1] or -1)):
        intervals = sorted((k.start_ns, k.end_ns) for k in group if k.end_ns > k.start_ns)
        if len(intervals) < 2:
            continue
        merged: list[list[int]] = [[intervals[0][0], intervals[0][1]]]
        for s_ns, e_ns in intervals[1:]:
            if s_ns <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e_ns)
            else:
                merged.append([s_ns, e_ns])

        for idx in range(len(merged) - 1):
            gap_start, gap_end = merged[idx][1], merged[idx + 1][0]
            gap_ns = gap_end - gap_start
            if gap_ns < threshold_ns:
                continue
            overlapping_host = [
                h for h in host_rows
                if h["rank_id"] == rank_id and h["end_ns"] > gap_start and h["start_ns"] < gap_end
                and "gc" not in h["name"].lower() and "synchronizestream" not in h["name"].lower()
            ]
            acl_busy_ns = sum(min(h["end_ns"], gap_end) - max(h["start_ns"], gap_start) for h in overlapping_host)
            acl_ratio = acl_busy_ns / float(gap_ns) if gap_ns > 0 else 0.0
            acl_rate_per_us = len(overlapping_host) / (gap_ns / 1000.0) if gap_ns > 0 else 0.0
            if host_rows:
                if acl_ratio < 0.01 and acl_rate_per_us < 0.0001:
                    gc_freezes.append({
                        "freeze_type": "suspected_python_gc_or_gil_freeze", "rank_id": rank_id, "step": step,
                        "start_ns": gap_start, "end_ns": gap_end, "gap_ms": _ms(gap_ns),
                        "acl_busy_ratio": round(acl_ratio, 6), "acl_event_rate_per_us": round(acl_rate_per_us, 6),
                        "confidence": "high",
                        "guidance": f"Device was idle for {_ms(gap_ns):.3f} ms with near-zero CANN/ACL host dispatch activity (ratio={acl_ratio:.4f}); inspect Python GC pauses (gc.disable()), GIL contention, or enable TASK_QUEUE_ENABLE=2 and CPU_AFFINITY_CONF=1.",
                    })
            else:
                gc_freezes.append({
                    "freeze_type": "unexplained_device_dispatch_freeze", "rank_id": rank_id, "step": step,
                    "start_ns": gap_start, "end_ns": gap_end, "gap_ms": _ms(gap_ns),
                    "acl_busy_ratio": None, "confidence": "medium",
                    "guidance": f"Large inter-kernel device uncovered stall ({_ms(gap_ns):.3f} ms); correlate host trace for Python GC pause or aclrtSynchronizeStream.",
                })

    if gc_freezes:
        g0 = gc_freezes[0]
        findings.append({
            "finding_type": "advisor_host_gc_or_dispatch_freeze",
            "severity": "high" if g0["gap_ms"] >= 20.0 else "medium", "confidence": g0["confidence"],
            "summary": f"Detected {len(gc_freezes)} host dispatch/GC freeze window(s) totaling {sum(x['gap_ms'] for x in gc_freezes):.3f} ms (max {max(x['gap_ms'] for x in gc_freezes):.3f} ms).",
            "evidence_ref": g0["freeze_type"],
            "evidence_scope": {"rank_id": g0["rank_id"], "step": g0["step"], "start_ns": g0["start_ns"], "end_ns": g0["end_ns"]},
        })

    return {"status": "detected" if (sync_matches or gc_freezes) else "clean",
            "forced_sync_count": len(sync_matches), "forced_sync_total_ms": round(sum(m["duration_ms"] for m in sync_matches), 6),
            "ascend_launch_blocking_suspected": launch_blocking, "node_launch_sync_co_occurrence_ratio": co_ratio,
            "gc_freeze_count": len(gc_freezes), "gc_freeze_total_ms": round(sum(g["gap_ms"] for g in gc_freezes), 6),
            "sync_events": sync_matches, "gc_freezes": gc_freezes, "findings": findings}


def scan_fusible_operator_sequences(
    observations: Sequence[Observation] | None = None, *,
    events: Sequence[Event | KernelEvent | Mapping[str, Any]] | None = None,
    custom_rules: Sequence[FusionPatternRule] | None = None, max_inter_kernel_gap_ms: float = 5.0,
) -> dict[str, Any]:
    """Scan ordered per-stream kernel timelines for fusible operator chains and estimate savings."""
    kernels = _coerce_kernels(observations, events)
    if not kernels:
        return {"status": "not_applicable", "total_matched_sequences": 0, "total_estimated_savings_ms": 0.0, "candidates": [], "findings": []}

    rules = tuple(custom_rules) if custom_rules is not None else FUSION_PATTERN_RULES
    sorted_rules = sorted(rules, key=lambda r: (-len(r.sequence), r.pattern_code))
    max_gap_ns = int(round(max_inter_kernel_gap_ms * 1_000_000.0))

    by_stream: dict[tuple[str, int | None, str], list[_AdvisorKernel]] = {}
    for k in kernels:
        by_stream.setdefault((k.rank_id, k.step, k.stream_id or "default"), []).append(k)

    by_pattern: dict[str, dict[str, Any]] = {}
    for (rank_id, step, stream_id), stream_kernels in sorted(by_stream.items(), key=lambda x: (x[0][0], x[0][1] or -1, x[0][2])):
        ordered = sorted(stream_kernels, key=lambda x: (x.start_ns, x.end_ns, x.task_id or ""))
        tokens = [_canon_op_token(k.op_type, k.name) for k in ordered]
        i, n = 0, len(ordered)
        while i < n:
            if ordered[i].is_comm or ordered[i].is_aicpu:
                i += 1
                continue
            matched_rule: FusionPatternRule | None = None
            for rule in sorted_rules:
                seq_len = len(rule.sequence)
                if i + seq_len > n:
                    continue
                w_slice = ordered[i : i + seq_len]
                if any(k.is_comm or k.is_aicpu for k in w_slice) or tuple(tokens[i : i + seq_len]) != rule.sequence:
                    continue
                if all(w_slice[p + 1].start_ns - w_slice[p].end_ns <= max_gap_ns for p in range(seq_len - 1)):
                    matched_rule = rule
                    break
            if matched_rule is None:
                i += 1
                continue

            seq_len = len(matched_rule.sequence)
            m_slice = ordered[i : i + seq_len]
            kernel_dur_ns = sum(k.duration_ns for k in m_slice)
            launch_gap_ns = sum(max(0, m_slice[p + 1].start_ns - m_slice[p].end_ns) for p in range(seq_len - 1))
            savings_ns = launch_gap_ns + int(round(kernel_dur_ns * matched_rule.kernel_saving_ratio))
            bucket = by_pattern.setdefault(matched_rule.pattern_code, {
                "pattern_code": matched_rule.pattern_code, "operator_sequence": list(matched_rule.sequence),
                "replacement_api": matched_rule.replacement_api, "occurrence_count": 0,
                "total_kernel_ns": 0, "total_launch_gap_ns": 0, "estimated_savings_ns": 0,
                "guidance": matched_rule.guidance, "sample_scopes": [],
            })
            bucket["occurrence_count"] += 1
            bucket["total_kernel_ns"] += kernel_dur_ns
            bucket["total_launch_gap_ns"] += launch_gap_ns
            bucket["estimated_savings_ns"] += savings_ns
            if len(bucket["sample_scopes"]) < 5:
                bucket["sample_scopes"].append({
                    "rank_id": rank_id, "step": step, "stream_id": stream_id,
                    "start_ns": m_slice[0].start_ns, "end_ns": m_slice[-1].end_ns,
                    "kernel_names": [k.name for k in m_slice], "task_ids": [k.task_id for k in m_slice],
                    "kernel_ms": _ms(kernel_dur_ns), "launch_gap_ms": _ms(launch_gap_ns), "estimated_savings_ms": _ms(savings_ns),
                })
            i += seq_len

    candidates: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for bucket in sorted(by_pattern.values(), key=lambda b: (-b["estimated_savings_ns"], -b["occurrence_count"], b["pattern_code"])):
        row = {
            "pattern_code": bucket["pattern_code"], "operator_sequence": bucket["operator_sequence"],
            "replacement_api": bucket["replacement_api"], "occurrence_count": bucket["occurrence_count"],
            "total_kernel_ms": _ms(bucket["total_kernel_ns"]), "total_launch_gap_ms": _ms(bucket["total_launch_gap_ns"]),
            "estimated_savings_ms": _ms(bucket["estimated_savings_ns"]), "guidance": bucket["guidance"],
            "sample_scopes": bucket["sample_scopes"],
        }
        candidates.append(row)
        findings.append({
            "finding_type": "advisor_fusible_operator_sequence",
            "severity": "medium" if row["estimated_savings_ms"] < 0.5 else "high", "confidence": "high",
            "summary": f"Fusible sequence {' -> '.join(row['operator_sequence'])} matched {row['occurrence_count']}x (est. savings {row['estimated_savings_ms']:.3f} ms via {row['replacement_api']}).",
            "evidence_ref": row["pattern_code"], "evidence_scope": row["sample_scopes"][0],
        })

    return {"status": "detected" if candidates else "clean", "total_matched_sequences": sum(c["occurrence_count"] for c in candidates),
            "total_estimated_savings_ms": round(sum(c["estimated_savings_ms"] for c in candidates), 6), "candidates": candidates, "findings": findings}


def evaluate_advisor_rules(
    observations: Sequence[Observation] | None = None,
    *,
    events: Sequence[Event | KernelEvent | Mapping[str, Any]] | None = None,
    host_events: Sequence[Mapping[str, Any]] | None = None,
    gc_gap_threshold_ms: float = 10.0,
) -> dict[str, Any]:
    """Run all four Ascend Advisor scanners and return a consolidated C7 fragment."""
    aicpu = scan_aicpu_fallbacks(observations, events=events)
    alignment = scan_alignment_and_mte_contention(observations, events=events)
    host_sync = scan_host_sync_and_gc_freezes(
        observations, events=events, host_events=host_events, gc_gap_threshold_ms=gc_gap_threshold_ms
    )
    fusion = scan_fusible_operator_sequences(observations, events=events)
    return {
        "schema_version": ADVISOR_SCHEMA,
        "aicpu_and_cast_storms": aicpu,
        "alignment_and_mte_contention": alignment,
        "host_sync_and_gc_freezes": host_sync,
        "fusible_operator_sequences": fusion,
        "findings": [*aicpu["findings"], *alignment["findings"], *host_sync["findings"], *fusion["findings"]],
    }


__all__ = [
    "ADVISOR_SCHEMA", "FUSION_PATTERN_RULES", "FusionPatternRule", "evaluate_advisor_rules",
    "scan_aicpu_fallbacks", "scan_alignment_and_mte_contention",
    "scan_fusible_operator_sequences", "scan_host_sync_and_gc_freezes",
]
