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
from .profiler_configs import DEFAULT_STRUCTURAL_INFERENCE_CONFIG, StructuralInferenceConfig

from .structural_inference_primitives import (
    AgentDecisionItem, BodyTopologyInference, CANONICAL_L1_FAMILIES,
    FrameworkEnvelopeInference, FusedCompositeInference, KNOWN_FUSED_COMPOSITES,
    OperatorObservation, STRUCTURAL_INFERENCE_SCHEMA, SpeculativeModuleInference,
    StructuralInferenceReport, _AT, _COMM_TOKENS, _GLUE_TOKENS, _L2_KEYS, _LAUNCH_SUFFIX,
    _LAYER_FAMS, _LINEAR_ATTN_FAMS, _NQ, _PRIMARY_ANCHORS, _Rec, _SINGLE_RULES,
    _SPEC_METHOD_TOKENS, _STEP_BOUNDARY_TOKENS, _TAIL_SUFFIX, _attention_subgraph,
    _canonical_name, _composite_subgraph, _dsa_token, _extract, _glue_op,
    _has_cast_token, _is_metadata, _is_moe_comp, _joined_fold, _largest_divisor_at_most,
    _multi_family, _nonneg_int, _pick, _plain_add, _positive_int, _resolve_duration,
    _shape_key, _to_plain, classify_canonical_l1_family,
)

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

def _named_speculative(folded: str) -> bool:
    if any(tok in folded for tok in _SPEC_METHOD_TOKENS):
        return True
    if any(tok in folded for tok in _DRAFT_GLUE):
        return False
    return any(tok in folded for tok in ("draft", "rejectionsample", "verify"))

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

_NOT_MULTIPLICITY_DRAFT = ("moeinitrouting", "fusedinferattentionscore", "flashmlametadata")

def _mark_shape_drafts(recs: Sequence[_Rec], draft: set[int], steps: int, spec_mode: bool) -> None:
    if not spec_mode or steps <= 0:
        return
    groups: dict[tuple, list[int]] = defaultdict(list)
    for rec in recs:
        if rec.i in draft or _is_metadata(rec.folded) or any(tok in rec.folded for tok in _NOT_MULTIPLICITY_DRAFT):
            continue
        if rec.family not in {"attention", "gdn_linear_attn", "kda_linear_attn", "moe_router", "moe_grouped"} and not _is_moe_comp(rec):
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
        max_draft = DEFAULT_STRUCTURAL_INFERENCE_CONFIG.max_draft_fraction_ratio * large_n
        if small_n and large_n and small_n <= max_draft and small_n % steps == 0 and large_n % steps == 0 and 1 <= small_n // steps < large_n // steps:
            draft.update(small)

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

def _linear_attn_rows(recs: Sequence[_Rec]) -> list[_Rec]:
    return list(_linear_rows([*_preferred_rows(recs, "gdn_linear_attn"), *_preferred_rows(recs, "kda_linear_attn")]))

def _total_of(chosen: Sequence[_Rec], steps: int) -> int:
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

def _family_total(recs: Sequence[_Rec], steps: int, family: str) -> int:
    return _total_of(_preferred_rows(recs, family), steps)

def _linear_attn_total(recs: Sequence[_Rec], steps: int) -> int:
    return _total_of(_linear_attn_rows(recs), steps)

def _hint_steps(recs: Sequence[_Rec], hint: int | None) -> int | None:
    if not hint:
        return None
    lin_rows = _linear_attn_rows(recs)
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
    fit = lambda s: int(round(_family_total(recs, s, "attention") / s)) + int(round(_linear_attn_total(recs, s) / s)) == hint
    matches = [s for s in dict.fromkeys(found) if fit(s)]
    return max(matches) if matches else None

def _ffn_seen(rows: Sequence[_Rec], steps: int, layers: int) -> bool:
    if not (steps and layers):
        return False
    act = sum(rec.family == "activation" or any(tok in rec.folded for tok in ("swiglu", "silu", "gelu", "ffn", "mlp")) for rec in rows) / steps
    extra = sum(rec.family == "gemm" and not any(tok in rec.folded for tok in (*_PROJ_TOKENS, "lmhead", "logits")) for rec in rows) / steps
    return act + 1e-6 >= layers or extra + 1e-6 >= 2 * layers

def _gap_steps(
    recs: Sequence[_Rec],
    cohorts: Sequence[int],
    config: StructuralInferenceConfig = DEFAULT_STRUCTURAL_INFERENCE_CONFIG,
) -> int | None:
    anchors = sorted(rec.start for rec in recs if rec.start is not None and rec.family in {"attention", "gdn_linear_attn", "kda_linear_attn", "moe_router"})
    gaps = [right - left for left, right in zip(anchors, anchors[1:])]
    positive = sorted(gap for gap in gaps if gap > 0)
    if len(positive) < config.min_positive_gaps:
        return None
    median_gap = positive[len(positive) // 2]
    steps = sum(1 for gap in gaps if gap > median_gap * config.gap_median_multiple) + 1
    usable = [count for count in cohorts if count > 0]
    return steps if steps > 1 and usable and all(count % steps == 0 for count in usable) else None

def _factor_steps(
    total: int,
    config: StructuralInferenceConfig = DEFAULT_STRUCTURAL_INFERENCE_CONFIG,
) -> int | None:
    upper = config.candidate_step_upper_bound
    lo_layers, hi_layers = config.min_layer_candidates, config.max_layer_candidates
    sec_max = config.secondary_split_max_layers
    first = next(
        (steps for steps in range(1, upper + 1) if total > 0 and total % steps == 0 and lo_layers <= total // steps <= hi_layers),
        0,
    )
    layers = total // first if first else 0
    return layers if first and layers > sec_max and lo_layers <= first <= sec_max and layers <= upper else None

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
    events: Sequence[Any],
    *,
    explicit_steps: int | None = None,
    hint_layers: int | None = None,
    model_hint: str | None = None,
    config: StructuralInferenceConfig = DEFAULT_STRUCTURAL_INFERENCE_CONFIG,
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
    totals = {
        "attention": _family_total(pre_body, 0, "attention"),
        "linear_attention": _linear_attn_total(pre_body, 0),
        "moe_router": _family_total(pre_body, 0, "moe_router"),
    }
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
    l_linear = int(round(_rate(_linear_attn_total(body, steps), steps))) if steps else 0
    if basis == "hint_divisible" and hint and steps and (l_attn + l_linear) not in (0, hint):
        alt_a = int(round(_anchor_total(_preferred_rows(body, "attention"), lambda _rec: True) / steps))
        alt_l = int(round(_anchor_total(_linear_attn_rows(body), lambda _rec: True) / steps))
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
        groups[(rec.name, rec.op_type, rec.core, "spec_decode" if rec.i in draft else "target_body")].append(rec)
    def bucket(rec: _Rec, calls: float) -> str:
        if rec.family == "gemm":
            if any(tok in rec.folded for tok in ("lmhead", "logits")):
                return "mlp"
            if any(tok in rec.folded for tok in _PROJ_TOKENS):
                return "attention"
            return "mlp" if l_dense and l_moe == 0 else "unresolved_body"
        if rec.family == "activation":
            return "mlp" if l_moe == 0 else "routed_experts"
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
        if scope == "spec_decode":
            l2_us["spec_decode"] += us_per
            observe("spec_decode", "spec_decode", sample.is_comp, comp_fams, fam)
            decide("spec_decode_op", "spec_decode", comp_fams or ((fam,) if fam else ()), f"draft_cohort({calls:.1f}/step)", "Kept out of L_body before topology fitting.")
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
            target = subg or ("moe_token_dispatcher" if "alltoall" in sample.folded or "moedistribute" in sample.folded else "comm_subgraph")
            l1_us["collective"] += us_per
            l2_us[target] = l2_us.get(target, 0.0) + us_per
            observe("target_body", target, False, ("collective",), "collective")
            continue
        boundary_token = any(tok in sample.folded for tok in _STEP_BOUNDARY_TOKENS)
        aicpu = engine == "aicpu" or "aicpu" in sample.folded or "aicpu" in fold_text(sample.core)
        layer_scale = bool(l_body) and abs(calls - l_body) <= 0.51
        o1 = calls <= 2 and (not l_body or calls * 4 <= max(l_body, 1) or boundary_token)
        aicpu_env = aicpu and fam is None and calls <= 1 and any(tok in sample.folded for tok in _CTRL_TOKENS)
        if ((boundary_token and calls <= 2 and fam != "gemm") or aicpu_env) and o1 and not layer_scale and fam not in {"attention", "gdn_linear_attn", "kda_linear_attn", "moe_grouped", "moe_router", "indexer", "gemm"}:
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
            fused.append(FusedCompositeInference(name, engine, calls, us_per, "routed_experts", cand, "structural_multiplicity_and_missing_moe_complement", True))
            l2_us["routed_experts"] += us_per
            decide("inferred_fused_moe_composite", "routed_experts", cand, f"matches_L_moe({l_moe})", f"Unrecognized operator matches L_moe={l_moe} and moe_grouped is absent.")
            observe("target_body", "routed_experts", True, cand, None)
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
        for fam in ("attention", "moe_router", "moe_grouped"):
            total = sum(recs[i].family == fam and not _is_metadata(recs[i].folded) for i in draft)
            draft_layers = max(draft_layers, total // steps) if total and total % steps == 0 else draft_layers
        linear_total = sum(recs[i].family in _LINEAR_ATTN_FAMS and not _is_metadata(recs[i].folded) for i in draft)
        if linear_total and linear_total % steps == 0:
            draft_layers = max(draft_layers, linear_total // steps)
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
    flavors_attn = tuple(label for cond, label in ((l_attn, "full_or_mla_attention"), (l_linear, "linear_attention"), (l_indexer, "sparse_lightning_indexer")) if cond)
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
