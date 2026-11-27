"""Ascend Advisor rule scanners for AI_CPU fallbacks, alignment, freezes, and fusion (advisor_rules_scanners).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting ascend advisor rule scanners for ai_cpu fallbacks, alignment, freezes, and fusion.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
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

#: CANN HCCL collective schedule/controller kernels executed on AI_CPU when
#: ``HCCL_OP_EXPANSION_MODE=AICPU`` (co-scheduled with ``hcom_*`` collectives).
HCCL_AICPU_SCHEDULE_KERNELS: frozenset[str] = frozenset({
    "allreduceaicpukernel",
    "allgatheraicpukernel",
    "reducescatteraicpukernel",
    "alltoallaicpukernel",
    "alltoallvaicpukernel",
    "broadcastaicpukernel",
    "hccllaunchaicpukernel",
})

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

def _is_hccl_schedule_aicpu_name(op_type: str, name: str) -> bool:
    """Return True iff the kernel name matches a known HCCL AI_CPU schedule controller."""
    for raw in (op_type, name):
        base = re.sub(r"_\d+$", "", raw.strip())
        if base.replace("_", "").casefold() in HCCL_AICPU_SCHEDULE_KERNELS:
            return True
    return False


def _canon_op_token(op_type: str, name: str) -> str:
    raw = f"{op_type} {name}".lower()
    for needle, token in (
        # Already-fused CANN 9.2.x routing/cache ops must be recognized before
        # generic ``topk``/``scatter`` substrings, otherwise the advisor
        # recommends fusing a kernel the runtime already fused.
        ("moegatingtopk", "FusedMoeGatingTopK"), ("moe_gating_top_k", "FusedMoeGatingTopK"),
        ("moeinitrouting", "FusedMoeInitRouting"), ("moe_init_routing", "FusedMoeInitRouting"),
        ("scatterpakvcache", "FusedCacheEpilog"), ("scatter_pa_kv_cache", "FusedCacheEpilog"),
        ("kvcompressepilog", "FusedCacheEpilog"), ("kv_compress_epilog", "FusedCacheEpilog"),
        ("indexerquantcache", "FusedCacheEpilog"), ("indexer_quant_cache", "FusedCacheEpilog"),
        ("mhcpre", "MhcPre"), ("mhc_post", "MhcPost"), ("mhcpost", "MhcPost"), ("sinkhorn", "MhcPre"),
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
