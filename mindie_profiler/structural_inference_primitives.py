"""Bottom-up prior-free operator subgraph and layer periodicity structural inference (structural_inference_primitives).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting bottom-up prior-free operator subgraph and layer periodicity structural inference.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, fields, is_dataclass, replace
from typing import Any, Callable, Mapping, Sequence
from .classify import classify_event, fold_text

STRUCTURAL_INFERENCE_SCHEMA = "mindie-structural-inference/1"

CANONICAL_L1_FAMILIES: tuple[str, ...] = (
    "attention", "kv_cache", "rope", "gdn_linear_attn", "kda_linear_attn", "indexer", "gemm",
    "moe_grouped", "moe_router", "activation", "norm_residual",
    "elementwise_quant", "hyperconnection", "collective",
)

_NQ = ("layernorm", ("norm_residual", "elementwise_quant"))

_AT = ("attention", ("norm_residual", "rope", "kv_cache"))

KNOWN_FUSED_COMPOSITES: dict[str, tuple[str, tuple[str, ...]]] = {
    "megamoe": ("routed_experts", ("moe_router", "moe_grouped", "activation", "collective")),
    "dispatchffncombine": ("routed_experts", ("moe_grouped", "activation", "collective")),
    "dispatchgmmcombine": ("routed_experts", ("moe_grouped", "collective")),
    "groupedmatmulswigluquant": ("routed_experts", ("moe_grouped", "activation", "elementwise_quant")),
    "minimaxqknormropecachekernel": _AT, "kvrmsnormropecache": _AT,
    "mlaprolog": ("mla_attention", ("gemm", "norm_residual", "rope", "kv_cache")),
    "addrmsnormdynamicquant": _NQ, "addrmsnormdynamicmxquant": _NQ, "addrmsnormquant": _NQ, "rmsnormdynamicmxquant": _NQ,
    "dequantswigluquant": ("routed_experts", ("activation", "elementwise_quant")),
}

_SPEC_METHOD_TOKENS = ("dspark", "dflash", "mtp", "eagle", "speculative")

_STEP_BOUNDARY_TOKENS = ("argmax", "gatherv2", "embedding", "sampler", "multinomial", "lmhead", "logits")

_COMM_TOKENS = ("hcom", "hccl", "allreduce", "allgather", "reducescatter", "alltoall")

_GLUE_TOKENS = ("argmax", "gatherv2", "embedding", "scatterndupdate", "tanh", "realdiv", "concatd", "slice", "cast")

_PRIMARY_ANCHORS = {
    "attention": ("flashattentionscore", "fusedinferattentionscore", "sparseflashmla", "flashmla"),
    "gdn_linear_attn": ("recurrentgateddeltarule", "chunkgateddeltarule", "causalconv1d"),
    "kda_linear_attn": ("recurrentkda", "chunkkda", "chunkfwd"),
    "moe_router": ("moegatingtopk", "moeinitrouting"),
}

_LAYER_FAMS = frozenset({"attention", "gdn_linear_attn", "kda_linear_attn", "moe_router", "moe_grouped", "indexer", "hyperconnection"})

_LINEAR_ATTN_FAMS = ("gdn_linear_attn", "kda_linear_attn")

_LAUNCH_SUFFIX = re.compile(r"(?:__\d+(?:_\d+)*)+$")

_TAIL_SUFFIX = re.compile(r"_\d+$")

_L2_KEYS = (
    "attention", "mla_attention", "dsa_attention", "mha_attention", "gqa_attention", "mqa_attention",
    "swa_attention", "csa_attention", "csa2_attention", "hca_attention",
    "gdn_linear_attn", "kda_linear_attn", "lightning_indexer", "attn_residual",
    "mlp", "routed_experts", "moe_router", "moe_token_dispatcher", "layernorm", "hyper_connection",
    "comm_subgraph", "multi_family_composite", "spec_decode", "framework_envelope", "unresolved_body",
)

_SINGLE_RULES: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("mhc", "hyperconnection", "sinkhorn", "streammix", "hcpre", "hcpost"), "hyperconnection", "hyper_connection"),
    (("lightningindexer", "quantlightningindexer", "prologuelightningindexer", "decodeqkscorekernel", "indexerscore"), "indexer", "lightning_indexer"),
    (("kda", "chunkkda", "recurrentkda", "chunkfwd"), "kda_linear_attn", "kda_linear_attn"),
    (("recurrentgateddeltarule", "chunkgateddeltarule", "deltanet", "gateddeltarule", "fusedrecurrent", "causalconv", "gdn", "mamba", "ssm"), "gdn_linear_attn", "gdn_linear_attn"),
    (("flashattention", "fusedinferattentionscore", "pagedattention", "sparseflashattention", "sparseattentionscore", "sparseattnsharedkv", "sparseflashmla", "flashmla", "kvquantsparseflashattention", "increflashattention", "promptflashattention", "mla", "mha", "gqa", "mqa"), "attention", "attention"),
    (("reshapeandcache", "scatterupdate", "kvcache", "concatv2d", "updkv", "loadkv", "storekv"), "kv_cache", "attention"),
    (("rotary", "rope", "applyrotarypos"), "rope", "attention"),
    (("moegating", "moeinitrouting", "moefinalize", "router", "gatingtopk", "groupedtopk"), "moe_router", "moe_router"),
    (("moetokenpermute", "moetokenunpermute"), "moe_router", "moe_token_dispatcher"),
    (("groupedmatmul", "groupedmm", "gmm"), "moe_grouped", "routed_experts"),
    (("swiglu", "silu", "gelu", "fastgelu"), "activation", "routed_experts"),
    (("matmul", "batchmatmul", "quantbatchmatmul", "transposebatchmatmul", "gemm"), "gemm", "unresolved_body"),
    (("attnresfwd",), "norm_residual", "attn_residual"),
    (("rmsnorm", "layernorm", "gemma_rmsnorm", "gemmarmsnorm", "l2norm"), "norm_residual", "layernorm"),
)

@dataclass(frozen=True, slots=True)
class OperatorObservation:
    name: str; op_type: str; core: str; execution_engine: str
    call_count: int; total_us: float; calls_per_step: float; us_per_step: float
    canonical_family: str | None; enclosing_subgraph: str | None
    is_fused_composite: bool; composite_families: tuple[str, ...]; structural_scope: str

@dataclass(frozen=True, slots=True)
class BodyTopologyInference:
    inferred_steps: int; total_body_layers: int; full_attention_layers: int; linear_attention_layers: int
    sparse_indexer_layers: int; moe_ffn_layers: int; dense_ffn_layers: int; hyperconnection_layers: int
    is_hybrid_attention: bool; is_hybrid_ffn: bool; attention_flavors: tuple[str, ...]; ffn_flavors: tuple[str, ...]
    topology_signature: str; confidence: str; evidence_notes: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class FusedCompositeInference:
    operator_name: str; execution_engine: str; calls_per_step: float; us_per_step: float
    enclosing_subgraph: str; constituent_families: tuple[str, ...]; detection_basis: str; replaces_unfused_families: bool

@dataclass(frozen=True, slots=True)
class SpeculativeModuleInference:
    has_speculative_decoding: bool; speculative_kind: str | None; inferred_draft_layers: int
    draft_us_per_step: float; draft_share_pct: float; draft_operators: tuple[str, ...]; target_vs_draft_separation_basis: str

@dataclass(frozen=True, slots=True)
class FrameworkEnvelopeInference:
    envelope_us_per_step: float; envelope_share_pct: float
    aicpu_controller_us_per_step: float; step_boundary_operators: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class AgentDecisionItem:
    operator_name: str; op_type: str; execution_engine: str; calls_per_step: float; us_per_step: float
    share_of_step_pct: float; inferred_role: str; inferred_subgraph: str | None
    candidate_families: tuple[str, ...]; multiplicity_match: str; agent_action_recommendation: str

def _to_plain(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {item.name: _to_plain(getattr(obj, item.name)) for item in fields(obj)}
    if isinstance(obj, Mapping):
        return {str(key): _to_plain(val) for key, val in obj.items()}
    if isinstance(obj, tuple):
        return [_to_plain(val) for val in obj]
    return obj

@dataclass(frozen=True, slots=True)
class StructuralInferenceReport:
    schema_version: str; total_events: int; total_duration_us: float; step_duration_us: float
    activity_sum_us_per_step: float; observed_span_us_per_step: float | None; busy_union_us_per_step: float | None
    duration_basis: str; target_body_us_per_step: float; body_topology: BodyTopologyInference
    fused_composites: tuple[FusedCompositeInference, ...]; speculative_module: SpeculativeModuleInference
    framework_envelope: FrameworkEnvelopeInference; l1_family_us_per_step: Mapping[str, float]
    l2_subgraph_us_per_step: Mapping[str, float]; agent_decision_items: tuple[AgentDecisionItem, ...]
    operators: tuple[OperatorObservation, ...]
    def as_dict(self) -> dict[str, Any]:
        return _to_plain(self)

@dataclass(frozen=True, slots=True)
class _Rec:
    i: int; name: str; op_type: str; core: str; engine: str; dur: float | None
    start: int | None; end: int | None; shape: tuple; family: str | None; subgraph: str | None
    is_comp: bool; comp_fams: tuple[str, ...]; folded: str; domain: tuple[str, str]

def _joined_fold(*parts: str) -> str:
    return "|".join(part for part in (fold_text(part) for part in parts) if part)

def _canonical_name(name: str) -> str:
    cur = (name or "").strip()
    prev = None
    while cur and cur != prev:
        prev = cur
        cur = _TAIL_SUFFIX.sub("", _LAUNCH_SUFFIX.sub("", cur))
    return cur or (name or "")

def _has_cast_token(folded: str) -> bool:
    scrubbed = folded.replace("broadcast", "").replace("forecast", "")
    return "cast" in scrubbed

def _dsa_token(folded: str) -> bool:
    return any(folded.startswith("dsa", i) and "adds" not in folded[max(0, i - 3): i + 3] for i in range(len(folded)))

def _plain_add(folded: str, op_type: str) -> bool:
    blocked = "matmul" in folded or "rmsnorm" in folded or "allreduce" in folded
    return not blocked and (fold_text(op_type) in {"add", "adds"} or "addaicore" in folded or "addsadd" in folded)

def _glue_op(folded: str) -> bool:
    indexed = "indexer" not in folded and "index" in folded
    return any(tok in folded for tok in _GLUE_TOKENS) or indexed or ("less" in folded and "lightning" not in folded)

def _attention_subgraph(folded: str) -> str:
    if "mla" in folded:
        return "dsa_attention" if any(tok in folded for tok in ("sparse", "indexer", "lightning")) else "mla_attention"
    if any(tok in folded for tok in ("candidate", "sharedcompress")):
        return "csa2_attention"
    if any(tok in folded for tok in ("hierarch", "hca")):
        return "hca_attention"
    if any(tok in folded for tok in ("winattention", "sliding")):
        return "swa_attention"
    if any(tok in folded for tok in ("compress", "csa")):
        return "csa_attention"
    if "mha" in folded:
        return "mha_attention"
    if "gqa" in folded:
        return "gqa_attention"
    if "mqa" in folded:
        return "mqa_attention"
    return "attention"

def _multi_family(folded: str) -> tuple[str, ...] | None:
    hits: list[str] = []
    def add(fam: str, cond: bool) -> None:
        if cond and fam not in hits:
            hits.append(fam)
    grouped = "groupedmatmul" in folded or "groupedmm" in folded
    add("moe_grouped", grouped)
    add("gemm", (not grouped) and ("matmul" in folded or "gemm" in folded))
    add("collective", any(tok in folded for tok in ("allreduce", "allgather", "reducescatter", "alltoall", "hcom", "hccl", "moedistribute")))
    add("norm_residual", any(tok in folded for tok in ("rmsnorm", "layernorm", "addrmsnorm")))
    add("rope", "rope" in folded or "rotary" in folded)
    add("kv_cache", "kvcache" in folded or "ropecache" in folded or "cachekernel" in folded)
    add("activation", any(tok in folded for tok in ("swiglu", "silu", "gelu")))
    add("kda_linear_attn", "kda" in folded)
    add("gdn_linear_attn", "kda" not in folded and any(tok in folded for tok in ("gdn", "deltanet", "gateddeltarule", "fusedrecurrent", "causalconv", "mamba", "ssm")))
    add("attention", any(tok in folded for tok in ("flashattention", "pagedattention", "fusedinferattention", "sparseflashattention", "flashmla", "mla")))
    quantish = _has_cast_token(folded) or "dynamicquant" in folded or "dequant" in folded
    if len(hits) >= 2:
        add("elementwise_quant", quantish or ("quant" in folded and "collective" in hits))
        return tuple(hits)
    if hits == ["norm_residual"] and (quantish or "quant" in folded):
        return ("norm_residual", "elementwise_quant")
    return None

def _composite_subgraph(fams: Sequence[str], folded: str = "") -> str:
    owned = set(fams)
    if owned <= {"norm_residual", "elementwise_quant"}:
        return "layernorm"
    if "collective" in owned and "gemm" in owned:
        return "multi_family_composite"
    if owned & {"moe_grouped", "moe_router"}:
        return "routed_experts"
    if owned & {"rope", "kv_cache", "attention", "gdn_linear_attn", "kda_linear_attn"} and "collective" not in owned:
        if "kda_linear_attn" in owned:
            return "kda_linear_attn"
        if "gdn_linear_attn" in owned:
            return "gdn_linear_attn"
        return _attention_subgraph(folded)
    return "multi_family_composite"

def classify_canonical_l1_family(
    name: str, op_type: str = "", core: str = "",
) -> tuple[str | None, str | None, bool, tuple[str, ...]]:
    folded = _joined_fold(_canonical_name(name), _canonical_name(op_type), name, op_type)
    folded_core = fold_text(core)
    if not folded:
        return None, None, False, ()
    for token, (subgraph, families) in KNOWN_FUSED_COMPOSITES.items():
        if token in folded:
            return None, subgraph, True, families
    if "mlapreprocess" in folded or "compressor" in folded:
        return "attention", "attention", False, ("attention",)
    multi = _multi_family(folded)
    if multi:
        return None, _composite_subgraph(multi, folded), True, multi
    if "communication" in folded_core or "hccl" in folded_core or any(
        tok in folded for tok in ("hcom", "hccl", "allreduce", "allgather", "reducescatter", "alltoall", "moedistributecombine", "moedistributedispatch")
    ):
        subgraph = "moe_token_dispatcher" if "moedistribute" in folded or "alltoall" in folded or ("moe" in folded and any(tok in folded for tok in ("allgather", "reducescatter"))) else "comm_subgraph"
        return "collective", subgraph, False, ("collective",)
    for tokens, fam, subgraph in _SINGLE_RULES:
        if fam == "indexer" and _dsa_token(folded):
            return fam, subgraph, False, (fam,)
        if any(tok in folded for tok in tokens):
            if fam == "attention":
                subgraph = _attention_subgraph(folded)
            return fam, subgraph, False, (fam,)
    quantish = _has_cast_token(folded) or any(tok in folded for tok in ("dynamicquant", "dynamicmxquant", "quant", "dequant", "transdata", "transpose"))
    if quantish or ("mul" in folded and "matmul" not in folded) or folded in {"add", "inplaceadd"} or _plain_add(folded, op_type):
        return "elementwise_quant", "layernorm", False, ("elementwise_quant",)
    return None, None, False, ()

def _nonneg_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float) and math.isfinite(value) and value >= 0 and value.is_integer():
        return int(value)
    return None

def _resolve_duration(dur_us: Any, dur_ns: Any, start: Any, end: Any) -> tuple[float | None, str | None]:
    if dur_us is not None:
        if isinstance(dur_us, bool) or not isinstance(dur_us, (int, float)) or not math.isfinite(float(dur_us)) or float(dur_us) < 0:
            return None, "invalid_duration"
        return float(dur_us), None
    if dur_ns is not None:
        ns = _nonneg_int(dur_ns)
        return (None, "invalid_duration") if ns is None else (ns / 1000.0, None)
    if start is not None or end is not None:
        left, right = _nonneg_int(start), _nonneg_int(end)
        if left is None or right is None or right < left:
            return None, "invalid_duration"
        return (right - left) / 1000.0, None
    return None, "missing_duration"

def _shape_key(shapes: Any) -> tuple:
    if not shapes:
        return ()
    if isinstance(shapes, str):
        text = shapes.strip().strip('"').strip("'")
        shapes = [piece.split(",") if piece else [] for piece in text.split(";")]
    parsed = []
    try:
        for shape in list(shapes)[:2]:
            if not shape:
                return ()
            parsed.append(tuple(int(str(dim).strip()) for dim in shape if str(dim).strip() != ""))
            if not parsed[-1]:
                return ()
    except (TypeError, ValueError):
        return ()
    return tuple(parsed)

def _pick(event: Any, keys: tuple[str, ...]) -> str:
    for obj in (event, getattr(event, "event", None)):
        if obj is None:
            continue
        for key in keys:
            raw = obj.get(key) if isinstance(obj, Mapping) else getattr(obj, key, None)
            if raw not in (None, ""):
                return str(raw)
    return ""

def _extract(index: int, event: Any) -> tuple[_Rec, str | None]:
    if isinstance(event, Mapping):
        name = str(event.get("name") or event.get("kernel_name") or "")
        op_type = str(event.get("op_type") or event.get("type") or event.get("OP Type") or "")
        core = str(event.get("core") or event.get("accelerator_core") or event.get("kernel_type") or "")
        if "dur_us" in event:
            dur_us = event.get("dur_us")
        elif "duration_us" in event:
            dur_us = event.get("duration_us")
        else:
            dur_us = None
        dur, reason = _resolve_duration(dur_us, event.get("duration_ns", event.get("dur_ns")), event.get("start_ns"), event.get("end_ns"))
        start, end, shapes = _nonneg_int(event.get("start_ns")), _nonneg_int(event.get("end_ns")), event.get("input_shapes")
    else:
        name = str(getattr(event, "name", "") or "")
        op_type = str(getattr(event, "op_type", "") or getattr(event, "kind", "") or "")
        core = str(getattr(event, "core", "") or getattr(event, "accelerator_core", "") or "")
        dur_us = getattr(event, "dur_us", None)
        if dur_us is None and not hasattr(event, "dur_us"):
            dur_us = getattr(event, "duration_us", None)
        dur, reason = _resolve_duration(dur_us, getattr(event, "duration_ns", None), getattr(event, "start_ns", None), getattr(event, "end_ns", None))
        start, end, shapes = _nonneg_int(getattr(event, "start_ns", None)), _nonneg_int(getattr(event, "end_ns", None)), getattr(event, "input_shapes", None)
    canon = _canonical_name(name) or _canonical_name(op_type) or "<unnamed>"
    fam, subg, is_comp, comp = classify_canonical_l1_family(canon, op_type, core)
    engine = classify_event(name=canon, op_type=op_type, core=core).execution_engine
    folded = _joined_fold(canon, op_type, name)
    domain = (_pick(event, ("rank_id", "rank")), _pick(event, ("device_id", "device")))
    return _Rec(index, canon, op_type, core, engine, dur, start, end, _shape_key(shapes), fam, subg, is_comp, comp, folded, domain), reason

def _positive_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None

def _is_metadata(folded: str) -> bool:
    return "metadata" in folded

def _is_moe_comp(rec: _Rec) -> bool:
    return rec.is_comp and "moe_grouped" in rec.comp_fams

def _largest_divisor_at_most(total: int, limit: int) -> int:
    if total <= 0 or limit <= 0:
        return 0
    best, factor = 0, 1
    while factor * factor <= total:
        if total % factor == 0:
            pair = total // factor
            if factor <= limit:
                best = max(best, factor)
            if pair <= limit:
                best = max(best, pair)
        factor += 1
    return best
