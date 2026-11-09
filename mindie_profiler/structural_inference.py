"""Bottom-up structural module, speculative draft, and framework envelope inference.

[Role]
  Infer model execution structure directly from device kernel traces without
  requiring pre-declared layer plans or forcing unknown kernels into arbitrary
  operator buckets. Recognizes repeating layer modules (including hybrid
  Attention/Linear-Attention and Dense/MoE layer splits), fused composite
  subgraphs, speculative decoding draft/verify stacks (MTP/DSpark/DFlash),
  and O(1) per-step framework envelope operators, surfacing explicit structured
  evidence and decision hints for Agent reasoning.

[Invariants]
  * Unrecognized kernels are never silently dropped or force-mapped to an
    arbitrary single L1 family.
  * Fused composite kernels (e.g., MegaMoe, DispatchFFNCombine,
    _minimax_qknorm_rope_cache_kernel) bind to their enclosing L2 subgraph
    with explicit constituent families rather than polluting single-op L1 metrics.
  * Speculative decoding traces retain target-body layer counts (L_body)
    separate from draft/verify modules (L_draft), preventing target+draft runs
    from being misidentified as standalone draft models.

[Timeouts & Locks]
  Pure in-memory O(N log N) pass; no I/O, locks, or subprocesses.

[Side-Effect Policy]
  Read-only over inputs; returned maps are read-only proxies.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, fields, is_dataclass, replace
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence
from .classify import classify_event, fold_text
STRUCTURAL_INFERENCE_SCHEMA = "mindie-structural-inference/1"
CANONICAL_L1_FAMILIES: tuple[str, ...] = (
    "attention", "kv_cache", "rope", "gdn_kda", "indexer", "gemm",
    "moe_grouped", "moe_router", "activation", "norm_residual",
    "elementwise_quant", "hyperconnection", "collective",
)
_NQ = ("norm_quant_subgraph", ("norm_residual", "elementwise_quant"))
_AT = ("attn_subgraph", ("norm_residual", "rope", "kv_cache"))
KNOWN_FUSED_COMPOSITES: dict[str, tuple[str, tuple[str, ...]]] = {
    "megamoe": ("moe_subgraph", ("moe_router", "moe_grouped", "activation", "collective")),
    "dispatchffncombine": ("moe_subgraph", ("moe_grouped", "activation", "collective")),
    "dispatchgmmcombine": ("moe_subgraph", ("moe_grouped", "collective")),
    "groupedmatmulswigluquant": ("moe_subgraph", ("moe_grouped", "activation", "elementwise_quant")),
    "minimaxqknormropecachekernel": _AT, "kvrmsnormropecache": _AT,
    "mlaprolog": ("attn_subgraph", ("gemm", "norm_residual", "rope", "kv_cache")),
    "addrmsnormdynamicquant": _NQ, "addrmsnormdynamicmxquant": _NQ, "addrmsnormquant": _NQ, "rmsnormdynamicmxquant": _NQ,
    "dequantswigluquant": ("moe_subgraph", ("activation", "elementwise_quant")),
}
_SPEC_METHOD_TOKENS = ("dspark", "dflash", "mtp", "eagle", "speculative")
_STEP_BOUNDARY_TOKENS = ("argmax", "gatherv2", "embedding", "sampler", "multinomial", "lmhead", "logits")
_COMM_TOKENS = ("hcom", "hccl", "allreduce", "allgather", "reducescatter", "alltoall")
_GLUE_TOKENS = ("argmax", "gatherv2", "embedding", "scatterndupdate", "tanh", "realdiv", "concatd", "slice", "cast")
_PRIMARY_ANCHORS = {
    "attention": ("flashattentionscore", "fusedinferattentionscore", "sparseflashmla", "flashmla"),
    "gdn_kda": ("recurrentgateddeltarule", "chunkgateddeltarule", "recurrentkda", "causalconv1d"),
    "moe_router": ("moegatingtopk", "moeinitrouting"),
}
_LAYER_FAMS = frozenset({"attention", "gdn_kda", "moe_router", "moe_grouped", "indexer", "hyperconnection"})
_LAUNCH_SUFFIX = re.compile(r"(?:__\d+(?:_\d+)*)+$")
_TAIL_SUFFIX = re.compile(r"_\d+$")
_L2_KEYS = (
    "attn_subgraph", "moe_subgraph", "norm_quant_subgraph", "comm_subgraph", "dense_ffn_subgraph",
    "multi_family_composite", "speculative_draft", "framework_envelope", "unresolved_body",
)
_SINGLE_RULES: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("mhc", "hyperconnection", "sinkhorn", "streammix", "hcpre", "hcpost"), "hyperconnection", "norm_quant_subgraph"),
    (("lightningindexer", "quantlightningindexer", "prologuelightningindexer", "decodeqkscorekernel", "indexerscore"), "indexer", "attn_subgraph"),
    (("recurrentgateddeltarule", "chunkgateddeltarule", "recurrentkda", "chunkkda", "chunkfwd", "fusedrecurrent", "deltanet", "gdn", "kda", "causalconv", "mamba", "ssm"), "gdn_kda", "attn_subgraph"),
    (("flashattention", "fusedinferattentionscore", "pagedattention", "sparseflashattention", "sparseattentionscore", "sparseattnsharedkv", "sparseflashmla", "flashmla", "kvquantsparseflashattention", "increflashattention", "promptflashattention"), "attention", "attn_subgraph"),
    (("reshapeandcache", "scatterupdate", "kvcache", "concatv2d", "updkv", "loadkv", "storekv"), "kv_cache", "attn_subgraph"),
    (("rotary", "rope", "applyrotarypos"), "rope", "attn_subgraph"),
    (("moegating", "moeinitrouting", "moetokenpermute", "moetokenunpermute", "moefinalize", "router", "gatingtopk", "groupedtopk"), "moe_router", "moe_subgraph"),
    (("groupedmatmul", "groupedmm", "gmm"), "moe_grouped", "moe_subgraph"),
    (("swiglu", "silu", "gelu", "fastgelu"), "activation", "moe_subgraph"),
    (("matmul", "batchmatmul", "quantbatchmatmul", "transposebatchmatmul", "gemm"), "gemm", "unresolved_body"),
    (("rmsnorm", "layernorm", "gemma_rmsnorm", "gemmarmsnorm", "attnresfwd", "l2norm"), "norm_residual", "norm_quant_subgraph"),
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
def _to_plain(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {item.name: _to_plain(getattr(obj, item.name)) for item in fields(obj)}
    if isinstance(obj, Mapping):
        return {str(key): _to_plain(val) for key, val in obj.items()}
    if isinstance(obj, tuple):
        return [_to_plain(val) for val in obj]
    return obj
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
def _multi_family(folded: str) -> tuple[str, ...] | None:
    hits: list[str] = []
    def add(fam: str, cond: bool) -> None:
        if cond and fam not in hits:
            hits.append(fam)
    grouped = "groupedmatmul" in folded or "groupedmm" in folded
    add("moe_grouped", grouped)
    add("gemm", (not grouped) and ("matmul" in folded or "gemm" in folded))
    add("collective", any(tok in folded for tok in ("allreduce", "allgather", "reducescatter", "alltoall", "hcom", "hccl")))
    add("norm_residual", any(tok in folded for tok in ("rmsnorm", "layernorm", "addrmsnorm")))
    add("rope", "rope" in folded or "rotary" in folded)
    add("kv_cache", "kvcache" in folded or "ropecache" in folded or "cachekernel" in folded)
    add("activation", any(tok in folded for tok in ("swiglu", "silu", "gelu")))
    add("gdn_kda", any(tok in folded for tok in ("kda", "gdn", "deltanet")))
    add("attention", any(tok in folded for tok in ("flashattention", "pagedattention", "fusedinferattention", "sparseflashattention", "flashmla", "mla")))
    quantish = _has_cast_token(folded) or "dynamicquant" in folded or "dequant" in folded
    if len(hits) >= 2:
        add("elementwise_quant", quantish or ("quant" in folded and "collective" in hits))
        return tuple(hits)
    if hits == ["norm_residual"] and (quantish or "quant" in folded):
        return ("norm_residual", "elementwise_quant")
    return None
def _composite_subgraph(fams: Sequence[str]) -> str:
    owned = set(fams)
    if owned <= {"norm_residual", "elementwise_quant"}:
        return "norm_quant_subgraph"
    if "collective" in owned and "gemm" in owned:
        return "multi_family_composite"
    if owned & {"moe_grouped", "moe_router"}:
        return "moe_subgraph"
    if owned & {"rope", "kv_cache", "attention", "gdn_kda"} and "collective" not in owned:
        return "attn_subgraph"
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
        return "attention", "attn_subgraph", False, ("attention",)
    multi = _multi_family(folded)
    if multi:
        return None, _composite_subgraph(multi), True, multi
    if "communication" in folded_core or "hccl" in folded_core or any(
        tok in folded for tok in ("hcom", "hccl", "allreduce", "allgather", "reducescatter", "alltoall", "moedistributecombine", "moedistributedispatch")
    ):
        subgraph = "moe_subgraph" if "moedistribute" in folded or "alltoall" in folded else "comm_subgraph"
        return "collective", subgraph, False, ("collective",)
    for tokens, fam, subgraph in _SINGLE_RULES:
        if fam == "indexer" and _dsa_token(folded):
            return fam, subgraph, False, (fam,)
        if any(tok in folded for tok in tokens):
            return fam, subgraph, False, (fam,)
    quantish = _has_cast_token(folded) or any(tok in folded for tok in ("dynamicquant", "dynamicmxquant", "quant", "dequant", "transdata", "transpose"))
    if quantish or ("mul" in folded and "matmul" not in folded) or folded in {"add", "inplaceadd"} or _plain_add(folded, op_type):
        return "elementwise_quant", "norm_quant_subgraph", False, ("elementwise_quant",)
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
def _named_speculative(folded: str) -> bool:
    if any(tok in folded for tok in _SPEC_METHOD_TOKENS):
        return True
    if any(tok in folded for tok in _DRAFT_GLUE):
        return False
    return any(tok in folded for tok in ("draft", "rejectionsample", "verify"))
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
def _anchor_total(recs: Sequence[_Rec], pred: Callable[[_Rec], bool]) -> int:
    groups: dict[str, int] = defaultdict(int)
    for rec in recs:
        if pred(rec) and not _is_metadata(rec.folded):
            groups[rec.name] += 1
    counts = list(groups.values())
    if len(counts) <= 1:
        return counts[0] if counts else 0
    peak = max(counts)
    return sum(count for count in counts if count >= 0.5 * peak)
def _mark_named_drafts(recs: Sequence[_Rec]) -> set[int]:
    groups: dict[tuple, list[int]] = defaultdict(list)
    for rec in recs:
        groups[(rec.name, rec.family, _named_speculative(rec.folded))].append(rec.i)
    draft: set[int] = set()
    max_body: dict[str | None, int] = defaultdict(int)
    max_named: dict[str | None, int] = defaultdict(int)
    targets: set[int] = set()
    for (_name, fam, spec), idxs in groups.items():
        count = len(idxs)
        bucket = max_named if spec else max_body
        if count > bucket[fam]:
            bucket[fam] = count
        if not spec and (fam in _LAYER_FAMS or fam == "gemm"):
            targets.add(count)
    for (name, fam, spec), idxs in groups.items():
        count = len(idxs)
        if not spec or ("verify" in fold_text(name) and count in targets):
            continue
        sibling, named = max_body[fam], max_named[fam]
        layer_like = fam in _LAYER_FAMS or fam == "gemm"
        if sibling >= count * 2 or (count < named and count * 4 <= named) or not layer_like or (fam == "gemm" and sibling == 0):
            draft.update(idxs)
    return draft
def _mark_shape_drafts(recs: Sequence[_Rec], draft: set[int], steps: int, spec_mode: bool) -> None:
    if not spec_mode or steps <= 0:
        return
    groups: dict[tuple, list[int]] = defaultdict(list)
    for rec in recs:
        if rec.i in draft or _is_metadata(rec.folded) or any(tok in rec.folded for tok in _NOT_MULTIPLICITY_DRAFT):
            continue
        if rec.family not in {"attention", "gdn_kda", "moe_router", "moe_grouped"} and not _is_moe_comp(rec):
            continue
        groups[(rec.name, rec.op_type, rec.core)].append(rec.i)
    for idxs in groups.values():
        by_shape: dict[tuple, list[int]] = defaultdict(list)
        for index in idxs:
            by_shape[recs[index].shape].append(index)
        if len(by_shape) < 2 or any(not shape for shape in by_shape):
            continue
        counts = {shape: len(members) for shape, members in by_shape.items()}
        peak = max(counts.values())
        large = {shape for shape, count in counts.items() if count >= 0.5 * peak}
        small = [index for shape, members in by_shape.items() if shape not in large for index in members]
        large_n, small_n = sum(counts[shape] for shape in large), len(small)
        if small_n and large_n and small_n <= 0.25 * large_n and small_n % steps == 0 and large_n % steps == 0 and 1 <= small_n // steps < large_n // steps:
            draft.update(small)
def _boundary_steps(recs: Sequence[_Rec], cohorts: Sequence[int]) -> int | None:
    usable = [count for count in cohorts if count > 0]
    if not usable:
        return None
    peak = max(usable)
    grouped: Counter[str] = Counter()
    for rec in recs:
        if any(tok in rec.folded for tok in _STEP_BOUNDARY_TOKENS):
            grouped[rec.name] += 1
    counts = [count for count in grouped.values() if 1 < count < peak and peak % count == 0]
    if not counts:
        return None
    gcd = 0
    for count in counts:
        gcd = math.gcd(gcd, count)
    if gcd <= 1 or any(cohort % gcd for cohort in usable):
        return None
    return gcd
_AUX_ANCHOR = ("metadata", "mlaprolog", "mlapreprocess", "compressor", "statecopy")
_CTRL_TOKENS = ("launch", "ctrl", "notify", "wait", "record", "stream")
_PROJ_TOKENS = ("qkv", "qproj", "kproj", "vproj", "oproj", "outproj", "projection")
_DRAFT_GLUE = ("combinesampled", "gatherdraft", "sampledanddraft", "anddrafttoken")
_NOT_MULTIPLICITY_DRAFT = ("moeinitrouting", "fusedinferattentionscore", "flashmlametadata")
def _preferred_rows(recs: Sequence[_Rec], family: str) -> list[_Rec]:
    rows = [rec for rec in recs if rec.family == family and not any(tok in rec.folded for tok in _AUX_ANCHOR)]
    if not rows and family != "attention":
        rows = [rec for rec in recs if rec.family == family and not _is_metadata(rec.folded)]
    if family == "attention":
        return rows
    prim = [rec for rec in rows if any(tok in rec.folded for tok in _PRIMARY_ANCHORS.get(family, ()))]
    return prim or rows
def _linear_rows(rows: Sequence[_Rec]) -> Sequence[_Rec]:
    core = [rec for rec in rows if any(tok in rec.folded for tok in ("kda", "gdn", "deltanet"))]
    conv = [rec for rec in rows if "conv1d" in rec.folded or "causalconv" in rec.folded]
    return (core if len(core) >= len(conv) else conv) if core and conv else rows
def _consensus_layers(recs: Sequence[_Rec], steps: int) -> int:
    counts = list(Counter((rec.name, rec.shape) for rec in recs).values())
    divisors: set[int] = set()
    for count in counts:
        factor = 1
        while factor * factor <= count:
            if count % factor == 0:
                divisors.add(factor)
                divisors.add(count // factor)
            factor += 1
    best = (0, 0, 0)
    for layers in divisors:
        explained = peak = 0
        for count in counts:
            cover, rem = divmod(count, layers)
            if rem == 0 and 1 <= cover <= steps:
                explained += count
                peak = max(peak, cover)
        if (explained, peak) > (best[0], best[1]):
            best = (explained, peak, layers)
    return best[2] if best[0] else 0
def _family_total(recs: Sequence[_Rec], steps: int, family: str) -> int:
    chosen = _preferred_rows(recs, family)
    if family == "gdn_kda":
        chosen = list(_linear_rows(chosen))
    if not chosen:
        return 0
    if steps:
        counts = Counter(rec.name for rec in chosen)
        if counts and all(count % steps == 0 for count in counts.values()):
            return sum(counts.values())
    total = _anchor_total(chosen, lambda _rec: True)
    if steps and total % steps and (layers := _consensus_layers(chosen, steps)):
        return layers * steps
    return total
def _hint_steps(recs: Sequence[_Rec], hint: int | None) -> int | None:
    if not hint:
        return None
    lin_rows = list(_linear_rows(_preferred_rows(recs, "gdn_kda")))
    combined = len(_preferred_rows(recs, "attention")) + len(lin_rows)
    router = _anchor_total(_preferred_rows(recs, "moe_router"), lambda _rec: True)
    comp = _anchor_total(recs, _is_moe_comp)
    cand = combined // hint if combined and combined % hint == 0 else 0
    if cand and not any(n and (n % cand or n // cand > hint) for n in (router, comp)):
        return cand
    found: list[int] = []
    for total in (_anchor_total(lin_rows, lambda _rec: True), router):
        factor = 1
        while total > 1 and factor * factor <= total:
            if total % factor == 0:
                found.extend(s for s in (factor, total // factor) if 1 < s <= 512)
            factor += 1
    fit = lambda s: int(round(_family_total(recs, s, "attention") / s)) + int(round(_family_total(recs, s, "gdn_kda") / s)) == hint
    matches = [s for s in dict.fromkeys(found) if fit(s)]
    return max(matches) if matches else None
def _ffn_seen(rows: Sequence[_Rec], steps: int, layers: int) -> bool:
    if not (steps and layers):
        return False
    act = sum(rec.family == "activation" or any(tok in rec.folded for tok in ("swiglu", "silu", "gelu", "ffn", "mlp")) for rec in rows) / steps
    extra = sum(rec.family == "gemm" and not any(tok in rec.folded for tok in (*_PROJ_TOKENS, "lmhead", "logits")) for rec in rows) / steps
    return act + 1e-6 >= layers or extra + 1e-6 >= 2 * layers
def _gap_steps(recs: Sequence[_Rec], cohorts: Sequence[int]) -> int | None:
    anchors = sorted(rec.start for rec in recs if rec.start is not None and rec.family in {"attention", "gdn_kda", "moe_router"})
    gaps = [right - left for left, right in zip(anchors, anchors[1:])]
    positive = sorted(gap for gap in gaps if gap > 0)
    if len(positive) < 3:
        return None
    steps = sum(1 for gap in gaps if gap > positive[len(positive) // 2] * 8) + 1
    usable = [count for count in cohorts if count > 0]
    return steps if steps > 1 and usable and all(count % steps == 0 for count in usable) else None
def _factor_steps(total: int) -> int | None:
    first = next((steps for steps in range(1, 256) if total > 0 and total % steps == 0 and 20 <= total // steps <= 120), 0)
    layers = total // first if first else 0
    return layers if first and layers > 96 and 20 <= first <= 96 and layers <= 255 else None
def _busy_union_ns(spans: Sequence[tuple[int, int]]) -> int:
    ordered = sorted((start, end) for start, end in spans if end > start)
    if not ordered:
        return 0
    total, left, right = 0, *ordered[0]
    for start, end in ordered[1:]:
        if start <= right:
            right = max(right, end)
        else:
            total += max(0, right - left)
            left, right = start, end
    return total + max(0, right - left)
def _rate(count: float, steps: int) -> float:
    return count / steps if steps else float(count)
def infer_trace_structure(
    events: Sequence[Any], *, explicit_steps: int | None = None, hint_layers: int | None = None, model_hint: str | None = None,
) -> StructuralInferenceReport:
    recs: list[_Rec] = []
    missing = invalid = 0
    for index, raw in enumerate(events):
        rec, reason = _extract(index, raw)
        recs.append(rec)
        missing += reason == "missing_duration"
        invalid += reason == "invalid_duration"
    domains = Counter(rec.domain for rec in recs if rec.domain != ("", ""))
    scope_note = ""
    if len(domains) > 1:
        primary = max(domains, key=lambda item: (domains[item], item))
        recs = [rec for rec in recs if rec.domain == primary]
        scope_note = f"scoped_primary_domain={primary[0]}:{primary[1]}"
    recs.sort(key=lambda rec: (rec.start is None, rec.start or 0, rec.i))
    recs = [replace(rec, i=idx) for idx, rec in enumerate(recs)]
    hint_kind = next((tok for tok in ("dspark", "dflash", "mtp", "eagle") if tok in fold_text(model_hint or "")), None)
    draft = _mark_named_drafts(recs)
    spec_mode = bool(hint_kind or draft)
    notes: list[str] = []
    if missing:
        notes.append(f"missing_duration_events={missing}")
    if invalid:
        notes.append(f"invalid_duration_events={invalid}")
    if scope_note:
        notes.append(scope_note)
    def body_now() -> list[_Rec]:
        return [rec for rec in recs if rec.i not in draft]
    pre_body = body_now()
    totals = {fam: _family_total(pre_body, 0, fam) for fam in ("attention", "gdn_kda", "moe_router")}
    explicit = _positive_int(explicit_steps) if explicit_steps is not None else None
    hint = _positive_int(hint_layers) if hint_layers is not None else None
    cohorts = [count for count in totals.values() if count]
    if not recs:
        steps, basis = 0, "empty"
        notes.append("empty_trace" if not hint else "layer_hint_ignored_without_kernel_evidence")
    elif explicit_steps is not None and explicit is None:
        steps, basis = 0, "invalid_explicit_steps"
        notes.append("invalid_explicit_steps")
    elif explicit is not None:
        steps, basis = explicit, "explicit"
        notes.append(f"Used caller-provided explicit step count ({steps}).")
    else:
        hinted = _hint_steps(pre_body, hint)
        bounded = None if hinted else _boundary_steps(pre_body, cohorts)
        gapped = None if hinted or bounded else _gap_steps(pre_body, cohorts)
        factored = _factor_steps(max(cohorts)) if cohorts and not hinted and not bounded and not gapped else None
        if factored and any(count % factored for count in cohorts):
            factored = None
        if hinted:
            steps, basis = hinted, "hint_divisible"
            notes.append(f"Step count {steps} from hint_layers={hint} on combined attention; subset cohorts divide the candidate.")
        elif bounded:
            steps, basis = bounded, "boundary"
            notes.append(f"Step count {steps} from O(1) boundary anchors dividing layer cohorts.")
        elif gapped:
            steps, basis = gapped, "gaps"
            notes.append(f"Step count {steps} from inter-step timestamp gaps dividing layer cohorts.")
        elif factored:
            steps, basis = factored, "layer_band"
            notes.append(f"Conditional layer_band hypothesis only: step count {steps} keeps body layers inside 20..96 and is not an identified iteration boundary.")
        else:
            steps, basis = 0, "ambiguous"
            notes.append("ambiguous_step_factorization:" + ",".join(str(c) for c in cohorts) if cohorts else "step_count_unresolved")
    _mark_shape_drafts(recs, draft, steps, spec_mode)
    body = body_now()
    per = lambda fam: int(round(_rate(_anchor_total(body, lambda rec, fam=fam: rec.family == fam), steps))) if steps else 0
    l_attn = int(round(_rate(_family_total(body, steps, "attention"), steps))) if steps else 0
    l_linear = int(round(_rate(_family_total(body, steps, "gdn_kda"), steps))) if steps else 0
    if basis == "hint_divisible" and hint and steps and (l_attn + l_linear) not in (0, hint):
        alt_a = int(round(_anchor_total(_preferred_rows(body, "attention"), lambda _rec: True) / steps))
        alt_l = int(round(_anchor_total(list(_linear_rows(_preferred_rows(body, "gdn_kda"))), lambda _rec: True) / steps))
        if alt_a + alt_l == hint:
            l_attn, l_linear = alt_a, alt_l
        elif l_attn + l_linear:
            l_attn = int(round(hint * l_attn / (l_attn + l_linear))); l_linear = hint - l_attn
    l_indexer, l_hc = per("indexer"), per("hyperconnection")
    router = _family_total(body, steps, "moe_router")
    gmm, comp = (_anchor_total(body, lambda rec: rec.family == "moe_grouped"), _anchor_total(body, _is_moe_comp))
    l_attn_body = (l_attn + l_linear) if (l_attn and l_linear) else (l_attn or l_linear)
    l_moe = 0
    if steps and router and (not l_attn_body or _rate(router, steps) <= l_attn_body + 1e-6):
        l_moe = int(round(_rate(router, steps)))
    elif steps and comp and (not l_attn_body or _rate(comp, steps) <= l_attn_body + 1e-6):
        l_moe = int(round(_rate(comp, steps)))
    elif steps and gmm and l_attn_body:
        per_gmm = _rate(gmm, steps)
        l_moe = _largest_divisor_at_most(int(round(per_gmm)), l_attn_body)
        if l_moe and per_gmm > l_moe:
            notes.append(f"Grouped matmul multiplicity {per_gmm / l_moe:.0f} ({per_gmm:.0f} calls across {l_moe} MoE layers).")
    elif steps and (router or comp or gmm):
        l_moe = int(round(_rate(router or comp or gmm, steps)))
        notes.append("ffn_body_without_attention_anchor")
    l_body = (l_attn + l_linear) if (l_attn and l_linear) else (l_attn_body or l_moe)
    hc_ref = (int(round(_rate(_family_total(recs, steps, "attention"), steps))) if steps else l_attn) or l_body
    if hc_ref and l_hc > hc_ref and l_hc % hc_ref == 0 and l_hc // hc_ref <= 4:
        l_hc = hc_ref
    if l_body and l_hc > l_body:
        l_hc = l_body
    if l_attn and l_linear:
        notes.append(f"Detected hybrid attention stack: {l_attn} full/MLA + {l_linear} linear/KDA/GDN = {l_body} layers.")
    if l_moe and l_body and l_attn_body and l_moe <= l_body:
        l_dense = l_body - l_moe
        if l_dense:
            notes.append(f"Detected hybrid FFN stack: {l_dense} dense MLP + {l_moe} MoE = {l_body} layers.")
    elif l_moe == 0 and _ffn_seen(body, steps, l_body):
        l_dense = l_body
        notes.append("Dense FFN evidence from activation or non-projection gemm cohort; no MoE cohort.")
    else:
        l_dense = 0
        if l_body and not l_moe:
            notes.append("ffn_unaccounted")
    measured = [rec.dur for rec in recs if rec.dur is not None]
    activity = float(sum(measured))
    span_per = union_per = None
    spans = [(rec.start, rec.end) for rec in recs if rec.start is not None and rec.end is not None and rec.end > rec.start]
    if spans and steps:
        span_ns = max(end for _, end in spans) - min(start for start, _ in spans)
        span_per, union_per = span_ns / 1000.0 / steps, _busy_union_ns(spans) / 1000.0 / steps
    activity_per = _rate(activity, steps) if steps else 0.0
    basis_bits = ["empty" if not recs else "no_finite_duration" if not measured else "activity_sum"]
    if missing:
        basis_bits.append(f"missing_duration={missing}")
    if invalid:
        basis_bits.append(f"invalid_duration={invalid}")
    duration_basis = ",".join(basis_bits)
    notes.append("step_duration_us_is_activity_sum_not_elapsed_wall")
    covered, elementary = set(), set()
    fam_counts: Counter[str] = Counter(rec.family for rec in body if rec.family)
    for rec in body:
        if rec.is_comp:
            covered.update(rec.comp_fams)
        elif rec.family and steps and fam_counts[rec.family] / steps >= max(1.0, 0.25 * max(l_body, 1)):
            elementary.add(rec.family)
            covered.add(rec.family)
    l1_us = {fam: 0.0 for fam in CANONICAL_L1_FAMILIES}
    l2_us = {key: 0.0 for key in _L2_KEYS}
    fused: list[FusedCompositeInference] = []
    decisions: list[AgentDecisionItem] = []
    observations: list[OperatorObservation] = []
    groups: dict[tuple, list[_Rec]] = defaultdict(list)
    for rec in recs:
        groups[(rec.name, rec.op_type, rec.core, "speculative_draft" if rec.i in draft else "target_body")].append(rec)
    def bucket(rec: _Rec, calls: float) -> str:
        if rec.family == "gemm":
            if any(tok in rec.folded for tok in ("lmhead", "logits")):
                return "dense_ffn_subgraph"
            if any(tok in rec.folded for tok in _PROJ_TOKENS):
                return "attn_subgraph"
            return "dense_ffn_subgraph" if l_dense and l_moe == 0 else "unresolved_body"
        if rec.family == "activation":
            return "dense_ffn_subgraph" if l_moe == 0 else "moe_subgraph"
        return rec.subgraph or ("comm_subgraph" if rec.family == "collective" else "unresolved_body")
    unk_moe: list[str] = []
    if "moe_grouped" not in covered and l_moe and steps:
        for (uname, _ot, _core, uscope), members in groups.items():
            sample_u = members[0]
            if uscope == "target_body" and not sample_u.is_comp and sample_u.family is None and not _glue_op(sample_u.folded) and abs(len(members) / steps - l_moe) <= 0.51:
                unk_moe.append(uname)
    compete_moe = len(unk_moe) >= 2
    aicpu_us = 0.0
    ordered = sorted(groups.items(), key=lambda kv: (-sum(r.dur or 0.0 for r in kv[1]), kv[0][0]))
    for (name, op_type, _core, scope), members in ordered:
        count, sample = len(members), members[0]
        calls = _rate(count, steps) if steps else 0.0
        us = sum(rec.dur or 0.0 for rec in members)
        us_per = _rate(us, steps) if steps else 0.0
        share = (100.0 * us_per / activity_per) if activity_per else 0.0
        fam, subg, comp_fams, engine = sample.family, sample.subgraph, sample.comp_fams, sample.engine
        def observe(scope_name: str, subgraph: str | None, composite: bool, families: tuple[str, ...], primary: str | None) -> None:
            observations.append(OperatorObservation(
                name, op_type, sample.core, engine, count, us, calls, us_per, primary, subgraph, composite, families, scope_name,
            ))
        def decide(role: str, subgraph: str | None, families: tuple[str, ...], match: str, text: str) -> None:
            decisions.append(AgentDecisionItem(name, op_type, engine, calls, us_per, share, role, subgraph, families, match, text))
        if scope == "speculative_draft":
            l2_us["speculative_draft"] += us_per
            observe("speculative_draft", "speculative_draft", sample.is_comp, comp_fams, fam)
            decide("speculative_draft_op", "speculative_draft", comp_fams or ((fam,) if fam else ()), f"draft_cohort({calls:.1f}/step)", "Kept out of L_body before topology fitting.")
            continue
        if sample.is_comp and subg:
            known = any(tok in sample.folded for tok in KNOWN_FUSED_COMPOSITES)
            fused.append(FusedCompositeInference(
                name, engine, calls, us_per, subg, comp_fams,
                "known_fused_composite_signature" if known else "multi_family_name", not set(comp_fams) <= elementary,
            ))
            l2_us[subg] = l2_us.get(subg, 0.0) + us_per
            observe("target_body", subg, True, comp_fams, None)
            decide("fused_composite_module", subg, comp_fams, f"matches_layer_cohort({calls:.1f}/step)", f"Account at L2 {subg} covering {comp_fams}; do not assign one L1 bucket.")
            continue
        if fam == "collective" or any(tok in sample.folded for tok in _COMM_TOKENS):
            target = subg or ("moe_subgraph" if "alltoall" in sample.folded or "moedistribute" in sample.folded else "comm_subgraph")
            l1_us["collective"] += us_per
            l2_us[target] = l2_us.get(target, 0.0) + us_per
            observe("target_body", target, False, ("collective",), "collective")
            continue
        boundary_token = any(tok in sample.folded for tok in _STEP_BOUNDARY_TOKENS)
        aicpu = engine == "aicpu" or "aicpu" in sample.folded or "aicpu" in fold_text(sample.core)
        layer_scale = bool(l_body) and abs(calls - l_body) <= 0.51
        o1 = calls <= 2 and (not l_body or calls * 4 <= max(l_body, 1) or boundary_token)
        aicpu_env = aicpu and fam is None and calls <= 1 and any(tok in sample.folded for tok in _CTRL_TOKENS)
        if ((boundary_token and calls <= 2 and fam != "gemm") or aicpu_env) and o1 and not layer_scale and fam not in {"attention", "gdn_kda", "moe_grouped", "moe_router", "indexer", "gemm"}:
            l2_us["framework_envelope"] += us_per
            if aicpu:
                aicpu_us += us_per
            observe("framework_envelope", "framework_envelope", False, (), fam)
            decide("framework_step_envelope", "framework_envelope", (fam,) if fam else (), f"step_boundary_O(1)({calls:.1f}/step)", "O(1) boundary or AICPU controller. Per-layer AICPU stays in the body.")
            continue
        if fam is not None:
            l1_us[fam] += us_per
            target = bucket(sample, calls)
            l2_us[target] = l2_us.get(target, 0.0) + us_per
            observe("target_body", target, False, (fam,), fam)
            continue
        role, inferred_sub, cand, match = "layer_body_unknown_op", None, (), "unresolved_multiplicity"
        cube = engine == "aic" or ("aic" in fold_text(sample.core) and "aiv" not in fold_text(sample.core) and "vector" not in fold_text(sample.core))
        moe_named = any(tok in sample.folded for tok in ("moe", "expert", "ffn", "mlp", "gmm", "grouped", "swiglu"))
        if name in unk_moe and compete_moe:
            l2_us["unresolved_body"] += us_per
            decide("layer_body_unknown_op", None, (), "competing_unknown_candidates", f"Competing unknowns share L_moe={l_moe}; none is promoted.")
            observe("target_body", None, False, (), None)
            continue
        if name in unk_moe and share >= 5.0 and cube and moe_named:
            covered.add("moe_grouped")
            cand = ("moe_router", "moe_grouped", "activation", "collective")
            fused.append(FusedCompositeInference(name, engine, calls, us_per, "moe_subgraph", cand, "structural_multiplicity_and_missing_moe_complement", True))
            l2_us["moe_subgraph"] += us_per
            decide("inferred_fused_moe_composite", "moe_subgraph", cand, f"matches_L_moe({l_moe})", f"Unrecognized operator matches L_moe={l_moe} and moe_grouped is absent.")
            observe("target_body", "moe_subgraph", True, cand, None)
            continue
        if l_moe and abs(calls - l_moe) <= 0.51 and "moe_grouped" in covered:
            match = "moe_already_covered"
            text = "MoE constituents are already covered; do not invent a second fused MoE."
        else:
            text = "Multiplicity alone does not choose a subgraph."
        l2_us["unresolved_body"] += us_per
        decide(role, None, (), match, f"Unrecognized operator ({engine}, {calls:.1f} calls/step, {share:.1f}% of activity). {text}")
        observe("target_body", None, False, (), None)
    draft_layers = 0
    if steps:
        for fam in ("attention", "gdn_kda", "moe_router", "moe_grouped"):
            total = sum(recs[i].family == fam and not _is_metadata(recs[i].folded) for i in draft)
            draft_layers = max(draft_layers, total // steps) if total and total % steps == 0 else draft_layers
        comp_total = sum(_is_moe_comp(recs[i]) for i in draft)
        if comp_total and comp_total % steps == 0:
            draft_layers = max(draft_layers, comp_total // steps)
    draft_us = _rate(sum(recs[i].dur or 0.0 for i in draft), steps) if steps else 0.0
    kind = hint_kind
    if draft and kind is None:
        blob = " ".join(recs[i].folded for i in draft)
        kind = next((tok for tok in ("dspark", "dflash", "mtp", "eagle") if tok in blob), "inferred_draft_stack")
    if not draft:
        kind = None
    has_spec = bool(draft)
    if not has_spec:
        spec_basis = "no_speculative_module_detected"
    else:
        spec_basis = "named_or_shape_cohort_separated_before_body_fit" + (";L_draft_lt_L_body" if draft_layers and l_body and draft_layers < l_body else ";draft_depth_unproven")
    env_names = tuple(op.name for op in observations if op.structural_scope == "framework_envelope")
    env_us = l2_us["framework_envelope"]
    body_us = sum(op.us_per_step for op in observations if op.structural_scope == "target_body")
    confidence = "low"
    if basis in {"explicit", "boundary", "gaps"} and l_body > 0:
        confidence = "high" if l_body >= 8 or basis == "explicit" else "medium"
    elif basis == "hint_divisible" and l_body > 0:
        confidence = "medium"
    flavors_attn = tuple(label for cond, label in ((l_attn, "full_or_mla_attention"), (l_linear, "linear_gdn_kda_attention"), (l_indexer, "sparse_lightning_indexer")) if cond)
    flavors_ffn = tuple(label for cond, label in ((l_dense, "dense_mlp"), (l_moe, "moe_ffn")) if cond)
    signature = f"L{l_body}(attn={l_attn},lin={l_linear},idx={l_indexer};dense={l_dense},moe={l_moe},hc={l_hc})"
    return StructuralInferenceReport(
        schema_version=STRUCTURAL_INFERENCE_SCHEMA, total_events=len(recs), total_duration_us=activity,
        step_duration_us=activity_per, activity_sum_us_per_step=activity_per,
        observed_span_us_per_step=span_per, busy_union_us_per_step=union_per, duration_basis=duration_basis,
        target_body_us_per_step=body_us,
        body_topology=BodyTopologyInference(
            steps, l_body, l_attn, l_linear, l_indexer, l_moe, l_dense, l_hc, bool(l_attn and l_linear), bool(l_dense and l_moe),
            flavors_attn, flavors_ffn, signature, confidence, tuple(notes),
        ),
        fused_composites=tuple(fused),
        speculative_module=SpeculativeModuleInference(
            has_spec, kind if has_spec else None, draft_layers, draft_us,
            (100.0 * draft_us / activity_per) if activity_per else 0.0,
            tuple(dict.fromkeys(recs[i].name for i in sorted(draft))), spec_basis,
        ),
        framework_envelope=FrameworkEnvelopeInference(
            env_us, (100.0 * env_us / activity_per) if activity_per else 0.0, aicpu_us, env_names,
        ),
        l1_family_us_per_step=MappingProxyType(l1_us), l2_subgraph_us_per_step=MappingProxyType(l2_us),
        agent_decision_items=tuple(decisions), operators=tuple(observations),
    )
