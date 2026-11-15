"""Ordered body evaluation for one archive schedule.

The parsed case is compiled once for that schedule. Each distinct query,
context, and sequence count is one active state and is priced by the real
body engine. An identical state inside the same schedule reuses that result.
A different context does not. The store lives only on this evaluation.
"""
from __future__ import annotations

import copy
import json
from typing import Any, Mapping, Sequence

_SCOPES = {"captured_forward", "declared_service_request"}


def target_step_ms(scope: str, source_sha: str, values: Sequence[float]) -> float | None:
    """One row scalar only for a single in-scope sample with a real source."""
    if scope not in _SCOPES or not source_sha or len(values) != 1:
        return None
    value = values[0]
    if not isinstance(value, (int, float)):
        return None
    return float(value)


def estimate_working_set(steps: Sequence[tuple[int, int, int]]) -> dict[str, Any]:
    """Finite active states in first-seen order. This does not price them."""
    ordered: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int, int]] = set()
    for step in steps:
        if step not in seen:
            seen.add(step)
            ordered.append(step)
    contexts = [step[1] for step in ordered]
    return {
        "ordered_frames": len(steps),
        "unique_states": len(ordered),
        "queries": sorted({step[0] for step in ordered}),
        "context_min": min(contexts) if contexts else None,
        "context_max": max(contexts) if contexts else None,
        "states": ordered,
    }


def priced_rate_signature(sku: str) -> str | None:
    """Catalog inputs the device pricer uses. Measured time is not an input."""
    from mindie_sim.backends import materialize
    from mindie_sim.schema.common import ModelingError

    if not isinstance(sku, str) or not sku:
        return None
    try:
        device = materialize({"backend": "ascend", "sku": sku}).get("device") or {}
    except (ModelingError, KeyError, TypeError):
        return None
    if not isinstance(device, Mapping):
        return None
    payload = {
        "compute_units": device.get("compute_units"),
        "memory_bytes": device.get("memory_bytes"),
        "compute_peaks": device.get("compute_peaks"),
        "rates": device.get("rates"),
        "resource_units": device.get("resource_units"),
    }
    return json.dumps(payload, sort_keys=True, default=str)


def _case_invariant(parsed: Any) -> str:
    machine = parsed.machine
    model = parsed.model
    parallel = parsed.runtime.parallel
    return json.dumps({
        "sku": machine.sku,
        "layers": model.layers,
        "tp": parallel.tp,
        "dp": parallel.dp,
        "ep": parallel.ep,
        "pp": parallel.pp,
    }, sort_keys=True)


def _graphs_of(graphs: Any) -> list[Any]:
    mapping = graphs.graphs if hasattr(graphs, "graphs") else graphs
    return list(next(iter(mapping.values())))


def _verify_invariant_ops(parsed: Any, phase: str, left: tuple[int, int, int], right: tuple[int, int, int]) -> dict[str, Any]:
    """Count operators whose compiled signature is stable across two active states.

    A changed signature is recomputed by the real engine with that state.
    Durations are not copied from the other state.
    """
    from mindie_sim.prediction.operator_analysis import physical_signature, target_graphs

    def signatures(step: tuple[int, int, int]) -> list[tuple[str, str]]:
        built = target_graphs(
            parsed, phase=phase, tokens=step[0], context=step[1], sequences=step[2], scope="body",
        )
        rows = []
        for op in _graphs_of(built):
            family = str(getattr(op, "family", "") or "")
            rows.append((family, physical_signature(op)))
        return rows

    if left[0] != right[0] or left[2] != right[2] or left[1] == right[1]:
        return {"invariant_geometry": "not_comparable", "invariant_ops_reused": 0, "active_ops": 0}
    before = signatures(left)
    after = signatures(right)
    if len(before) != len(after):
        return {"invariant_geometry": "topology_changed", "invariant_ops_reused": 0, "active_ops": len(after)}
    reused = 0
    active = 0
    for (family_before, sig_before), (family_after, sig_after) in zip(before, after):
        if family_before != family_after:
            return {"invariant_geometry": "family_changed", "invariant_ops_reused": reused, "active_ops": active}
        if sig_before == sig_after:
            reused += 1
        else:
            active += 1
    state = "verified" if reused and active else ("identical_states" if reused else "unverified")
    return {"invariant_geometry": state, "invariant_ops_reused": reused, "active_ops": active}


def _close_compiled_downsize(parsed: Any, case: Mapping[str, Any]) -> list[str]:
    """Compiled layer classes must still match the source-matched catalog base."""
    model = parsed.model
    meta = dict(model.metadata or ())
    if meta.get("architectural_basis") != "catalog_base_then_declared_downsize":
        return []
    problems: list[str] = []
    raw = case.get("model") if isinstance(case, Mapping) else None
    if isinstance(raw, Mapping) and any(key in raw for key in ("catalog_key", "model_catalog_key", "preset")):
        problems.append("catalog_key_present_on_explicit_downsize")

    def need(label: str, actual: Any, key: str) -> None:
        expected = meta.get(key)
        if actual != expected:
            problems.append(f"dimensional_closure:{label}:compiled={actual}:source={expected}")

    need("hidden_size", model.hidden_size, "source_hidden_size")
    need("layers", model.layers, "source_layers")
    need("num_heads", model.num_heads, "source_num_heads")
    need("head_dim", model.head_dim, "source_head_dim")
    need("num_kv_heads", model.num_kv_heads, "source_num_kv_heads")
    need("num_experts", model.num_experts, "source_num_experts")
    need("top_k", model.top_k, "source_top_k")
    need("moe_intermediate_size", model.moe_intermediate_size, "source_moe_intermediate_size")
    need("intermediate_size", model.intermediate_size, "source_intermediate_size")
    need("vocab_size", model.vocab_size, "source_vocab_size")
    signatures = meta.get("class_signatures")
    if not isinstance(signatures, Mapping) or not signatures:
        problems.append("dimensional_closure:class_signatures_absent")
    else:
        grouped: dict[str, list[Any]] = {}
        for plan in model.layer_plans:
            grouped.setdefault(str(plan.attention), []).append(plan)
        if set(grouped) != set(signatures):
            problems.append(
                "dimensional_closure:attention_classes:"
                + ",".join(sorted(grouped)) + "!=" + ",".join(sorted(str(key) for key in signatures))
            )
        else:
            fields = ("num_heads", "num_kv_heads", "head_dim", "num_experts", "top_k", "moe_intermediate_size", "linear_heads", "linear_head_dim")
            for attention, plans in grouped.items():
                expect = signatures[attention]
                if not isinstance(expect, Mapping) or len(plans) != expect.get("count"):
                    problems.append(f"dimensional_closure:{attention}.count:compiled={len(plans)}:source={expect.get('count') if isinstance(expect, Mapping) else None}")
                    continue
                for plan in plans:
                    for field in fields:
                        actual = getattr(plan, field)
                        if actual != expect.get(field):
                            problems.append(f"dimensional_closure:{attention}.{field}:compiled={actual}:source={expect.get(field)}")
                            break
    tp = parsed.runtime.parallel.tp
    ep = parsed.runtime.parallel.ep
    need("tp", tp, "source_tp")
    need("ep", ep, "source_ep")
    width = int(model.num_heads) * int(model.head_dim)
    if not isinstance(tp, int) or tp < 1 or width % tp != 0:
        problems.append(f"dimensional_closure:head_width_not_divisible_by_tp:{width}%{tp}")
    if isinstance(ep, int) and ep > 1 and int(model.num_experts) % ep != 0:
        problems.append(f"dimensional_closure:experts_not_divisible_by_ep:{model.num_experts}%{ep}")
    need("sku", parsed.machine.sku, "source_sku")
    return problems


class OrderedBodyEvaluator:
    """One schedule. No process-wide step cache."""

    def __init__(self, case: Mapping[str, Any], phase: str):
        self.case = case
        self.phase = phase
        self.parsed = None
        self._refusal: list[str] | None = None
        self.invariant = ""
        self._states: dict[tuple[int, int, int], dict[str, Any]] = {}
        self.stats: dict[str, Any] = {
            "compilations": 0,
            "engine_calls": 0,
            "reused_states": 0,
            "working_set": 0,
            "invariant_geometry": "not_checked",
            "invariant_ops_reused": 0,
            "active_ops": 0,
        }

    def compile_invariant(self) -> None:
        if self.parsed is not None or self._refusal is not None:
            return
        from mindie_sim.prediction.structure import parse_case
        from mindie_sim.schema.common import ModelingError

        try:
            parsed = parse_case(self.case)
        except ModelingError as exc:
            self._refusal = [str(exc)]
            self.stats["compilations"] = 1
            return
        problems = _close_compiled_downsize(parsed, self.case)
        if problems:
            self._refusal = problems
            self.stats["compilations"] = 1
            self.stats["dimensional_closure"] = "refused"
            return
        self.parsed = parsed
        self.invariant = _case_invariant(parsed)
        self.stats["compilations"] = 1
        if dict(parsed.model.metadata or ()).get("architectural_basis") == "catalog_base_then_declared_downsize":
            self.stats["dimensional_closure"] = "closed"

    def evaluate(self, tokens: int, context: int, sequences: int) -> dict[str, Any]:
        from mindie_sim.prediction.body import body_forward
        from mindie_sim.prediction.structure import parse_case
        from mindie_sim.schema.common import ModelingError

        self.compile_invariant()
        if self.parsed is None:
            return {"ok": False, "status": "model_rejected", "diagnostics": list(self._refusal or ["model_rejected"])}
        key = (int(tokens), int(context), int(sequences))
        cached = self._states.get(key)
        if cached is not None:
            self.stats["reused_states"] += 1
            return dict(cached)
        if _case_invariant(self.parsed) != self.invariant:
            try:
                parsed = parse_case(self.case)
            except ModelingError as exc:
                return {"ok": False, "status": "model_rejected", "diagnostics": [str(exc)]}
            problems = _close_compiled_downsize(parsed, self.case)
            if problems:
                return {"ok": False, "status": "model_rejected", "diagnostics": problems}
            self.parsed = parsed
            self.stats["compilations"] += 1
            if _case_invariant(self.parsed) != self.invariant:
                return {"ok": False, "status": "model_rejected", "diagnostics": ["compiled_geometry_not_invariant"]}
        try:
            result = body_forward(
                self.parsed, phase=self.phase, tokens=key[0], context=key[1], sequences=key[2],
                event_limit=0, compact=True,
            )
        except ModelingError as exc:
            return {"ok": False, "status": "model_rejected", "diagnostics": [str(exc)]}
        priced = _priced_body(result)
        if not priced.get("ok"):
            return priced
        self._states[key] = priced
        self.stats["engine_calls"] += 1
        return dict(priced)

    def evaluate_ordered(self, steps: Sequence[tuple[int, int, int]]) -> list[dict[str, Any]]:
        plan = estimate_working_set(steps)
        self.stats["working_set"] = plan["unique_states"]
        self.compile_invariant()
        if self.parsed is None:
            return [{"ok": False, "status": "model_rejected", "diagnostics": list(self._refusal or ["model_rejected"])}]
        states = plan["states"]
        if len(states) >= 2:
            checked = _verify_invariant_ops(self.parsed, self.phase, states[0], states[1])
            self.stats.update(checked)
        priced = {step: self.evaluate(*step) for step in states}
        return [dict(priced[step]) for step in steps]


def _priced_body(result: Mapping[str, Any]) -> dict[str, Any]:
    from fleet_operator_modeling import _classify_compact_profile, _core_publication, _program_ledger

    profile = result.get("profile") if isinstance(result.get("profile"), Mapping) else None
    if not isinstance(profile, Mapping):
        return {"ok": False, "status": "model_rejected", "diagnostics": ["compact_profile_absent"]}
    bucket, elapsed_sum, counted = _classify_compact_profile(profile)
    ledger = _program_ledger(profile)
    core_pub = _core_publication(ledger, elapsed_sum)
    geometry = result.get("geometry") if isinstance(result.get("geometry"), Mapping) else {}
    resources = []
    for row in result.get("resources") or ():
        if isinstance(row, Mapping):
            resources.append({
                "resource": row.get("resource"),
                "busy_ms": row.get("busy_ms"),
                "capacity_bound_ms": row.get("capacity_bound_ms"),
                "unit": row.get("unit"),
            })
    return {
        "ok": True,
        "body_forward_ms": float(result["body_forward_ms"]),
        "family_elapsed_ms": elapsed_sum,
        "operator_events": counted,
        "by_scope_ms": bucket["scope"],
        "by_canonical_ms": bucket["canonical"],
        "by_benchmark_ms": bucket["benchmark"],
        "by_unified_ms": bucket["unified"],
        "by_core_ms": core_pub["predicted_by_core_ms"],
        "core_forecast": core_pub["core_forecast"],
        "core_map_is_complete_forecast": core_pub["core_map_is_complete_forecast"],
        "unresolved_core_elapsed_ms": core_pub["unresolved_core_elapsed_ms"],
        "resources": resources,
        "additive_rows": ledger,
        "engine_query": {
            "valid_query_tokens": geometry.get("valid_query_tokens"),
            "graph_query_tokens": geometry.get("graph_query_tokens"),
            "padded_query_tokens": geometry.get("padded_query_tokens"),
            "sequences_by_replica": geometry.get("sequences_by_replica"),
        },
    }


def _aligned(probe: Mapping[str, Any], indexes: Sequence[int]) -> tuple[list[dict[str, Any]], list[tuple[int, int, int]]] | dict[str, Any]:
    frames = [item for item in (probe.get("frames") or []) if isinstance(item, Mapping)]
    steps = probe.get("chunk_steps") if isinstance(probe.get("chunk_steps"), list) else []
    if len(frames) != len(steps):
        return {"ok": False, "status": "insufficient_evidence", "diagnostics": ["frame_step_misaligned"]}
    chosen_frames = []
    chosen_steps = []
    for index in indexes:
        if index < 0 or index >= len(steps):
            return {"ok": False, "status": "insufficient_evidence", "diagnostics": ["material_index_outside_declared_frames"]}
        step = steps[index]
        if not isinstance(step, tuple) or len(step) != 3:
            return {"ok": False, "status": "insufficient_evidence", "diagnostics": ["chunk_steps_malformed"]}
        chosen_steps.append(step)
        chosen_frames.append(dict(frames[index]))
    return chosen_frames, chosen_steps


def price_ordered_frames(probe: Mapping[str, Any], indexes: Sequence[int]) -> dict[str, Any]:
    """Price the requested declared frames. Indexes default to every frame upstream."""
    from fleet_operator_modeling import (
        _core_publication,
        _elapsed_boundary,
        _operator_groups_from_ledger,
        _round_map,
    )

    scope = str(probe.get("predictable_scope") or "")
    source_sha = str(probe.get("source_sha256") or "")
    if scope not in _SCOPES or not source_sha:
        return {
            "ok": False,
            "status": "insufficient_evidence",
            "diagnostics": ["target_scalar_requires_true_scope_and_source"],
            "needed": ["predictable scope and verified physical source"],
        }
    aligned = _aligned(probe, indexes)
    if isinstance(aligned, dict):
        return aligned
    frames, steps = aligned
    supply = probe.get("supply") if isinstance(probe.get("supply"), Mapping) else {}
    case = copy.deepcopy(dict(probe.get("case") or {}))
    machine = dict(case.get("machine") or {})
    sku = str(supply.get("sku") or probe.get("sku") or "")
    if supply.get("kind") == "conditional_invariant":
        machine["sku"] = sku
        case["machine"] = machine
    elif str(machine.get("sku") or "") != sku or not sku:
        return {
            "ok": False,
            "status": "insufficient_evidence",
            "diagnostics": ["hardware_supply_does_not_match_case_sku"],
            "needed": ["one agreed producer catalog sku"],
        }
    evaluator = OrderedBodyEvaluator(case, str(probe.get("phase") or ""))
    once_rows = evaluator.evaluate_ordered(steps)
    failed = next((item for item in once_rows if not item.get("ok")), None)
    if failed is not None:
        return {
            "ok": False,
            "status": failed.get("status") or "model_rejected",
            "diagnostics": list(probe.get("diagnostics") or []) + list(failed.get("diagnostics") or []),
            "engine_stats": dict(evaluator.stats),
        }
    span = 0.0
    elapsed = 0.0
    events = 0
    maps = {"scope": {}, "canonical": {}, "benchmark": {}, "unified": {}}
    resources: list[dict[str, Any]] = []
    additive: list[dict[str, Any]] = []
    chunk_rows: list[dict[str, Any]] = []
    values: list[float] = []
    for index, (once, step) in enumerate(zip(once_rows, steps)):
        tokens, context, sequences = step
        span += float(once["body_forward_ms"])
        elapsed += float(once["family_elapsed_ms"])
        events += int(once["operator_events"])
        for kind, source_name in (
            ("scope", "by_scope_ms"),
            ("canonical", "by_canonical_ms"),
            ("benchmark", "by_benchmark_ms"),
            ("unified", "by_unified_ms"),
        ):
            for name, value in once[source_name].items():
                maps[kind][name] = maps[kind].get(name, 0.0) + float(value)
        resources.extend(once["resources"])
        for row in once.get("additive_rows") or ():
            if isinstance(row, Mapping):
                copied = dict(row)
                copied["chunk_index"] = index
                additive.append(copied)
        boundary_ms = round(float(once["body_forward_ms"]), 9)
        values.append(boundary_ms)
        chunk_rows.append({
            "chunk_index": indexes[index],
            "phase": probe.get("phase"),
            "tokens_per_sequence": tokens,
            "context_tokens": context,
            "sequences_per_replica": sequences,
            "boundary_ms": boundary_ms,
            "family_elapsed_ms": round(float(once["family_elapsed_ms"]), 9),
            "boundary": "body_graph_span",
            "boundary_basis": "elapsed",
        })
    view = dict(probe)
    view["frames"] = frames
    view["chunk_steps"] = steps
    cached = {
        "predicted_step_ms": round(span, 9),
        "predicted_operator_ms": round(elapsed, 9),
        "chunk_rows": chunk_rows,
        "engine_query": once_rows[-1].get("engine_query") if once_rows else None,
        "additive_rows": additive,
    }
    boundary = _elapsed_boundary(view, cached, [])
    samples = []
    label = _sample_label(supply)
    for sample in boundary.get("boundary_samples") or ():
        row = dict(sample)
        row["hardware_supply"] = dict(label)
        samples.append(row)
    boundary["boundary_samples"] = samples
    if samples:
        boundary["boundary_samples_ms"] = [item.get("boundary_ms") for item in samples]
    scalar = target_step_ms(scope, source_sha, values)
    groups, group_status = _operator_groups_from_ledger(additive)
    core_pub = _core_publication(additive, elapsed)
    plan = estimate_working_set(tuple(steps))
    plan.pop("states", None)
    return {
        "ok": True,
        "status": "modeled",
        "measurement_features_read": False,
        "engine": "mindie_sim.prediction.body.body_forward",
        "predicted_step_ms": None if scalar is None else round(scalar, 9),
        "predicted_operator_ms": round(elapsed, 9),
        "predicted_by_scope_ms": _round_map(maps["scope"]),
        "predicted_by_canonical_family_ms": _round_map(maps["canonical"]),
        "predicted_by_family_ms": _round_map(maps["benchmark"]),
        "predicted_by_unified_family_ms": _round_map(maps["unified"]),
        "predicted_by_core_ms": core_pub["predicted_by_core_ms"],
        "core_forecast": core_pub["core_forecast"],
        "core_map_is_complete_forecast": core_pub["core_map_is_complete_forecast"],
        "unresolved_core_elapsed_ms": core_pub["unresolved_core_elapsed_ms"],
        "bound_core_elapsed_ms": core_pub["bound_core_elapsed_ms"],
        "resources": resources,
        "operator_events": events,
        "chunk_span_sum_ms": round(span, 9),
        "engine_stats": dict(evaluator.stats),
        "working_set": plan,
        "operator_groups_status": group_status,
        "predicted_operator_groups": groups,
        **boundary,
    }


def _sample_label(supply: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "sku": supply.get("sku"),
        "role": supply.get("role"),
        "kind": supply.get("kind"),
        "exact": False,
        "serial_certified": False,
        "equipment_proof": None,
        "label": supply.get("provenance") or supply.get("evidence") or "",
        "declared_identity": supply.get("declared_identity"),
        "source_label": supply.get("source_label"),
    }
