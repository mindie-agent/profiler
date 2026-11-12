"""Archive frame join for fleet operator modeling.

The producer document in ``resolved.geometry.frames`` is the step schedule.
Receipt query rows are not replayed into a prefix-plus-cumsum context, and a
designed prefix is not written over the observed cache. One applied producer
catalog sku is the hardware supply. A contrary template is not selected.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

_AUDIT_ROLES = {"contrary_template", "template_subtype_not_measurement"}
_MC2_PER_RANK_TOKEN_LIMIT = 512
_FLOAT_ACTIVATIONS = {"bf16", "fp16"}


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def _mc2_token_capacity(runtime: Mapping[str, Any], tp: int) -> int:
    if runtime.get("enable_prefill_mc2") is True:
        batched = runtime.get("max_num_batched_tokens")
        max_tokens = batched if isinstance(batched, int) and not isinstance(batched, bool) and batched > 0 else _MC2_PER_RANK_TOKEN_LIMIT * tp
    else:
        raw = runtime.get("graph_capture_keys") or runtime.get("graph_buckets") or ()
        sizes = [item for item in raw if isinstance(item, int) and not isinstance(item, bool) and item > 0]
        max_tokens = max(sizes) if sizes else _MC2_PER_RANK_TOKEN_LIMIT * tp
    return min((max_tokens + tp - 1) // tp, _MC2_PER_RANK_TOKEN_LIMIT) * tp


def _device_selects_mc2(sku: str, experts: int | None, ep: int) -> bool:
    if sku.startswith(("Ascend950", "Ascend910_95", "Ascend910_93")):
        return True
    if sku.startswith("Ascend910B") and isinstance(experts, int) and ep >= 16 and experts % ep == 0:
        return experts // ep <= 24
    return False


def _mc2_tp_caller_declaration(case: Mapping[str, Any], token_counts: Sequence[Any]) -> dict[str, Any] | None:
    model = case.get("model") if isinstance(case.get("model"), Mapping) else {}
    runtime = case.get("runtime") if isinstance(case.get("runtime"), Mapping) else {}
    if str(model.get("ffn") or "") != "moe":
        return None
    if str(model.get("quantization") or "none").strip().lower() not in {"", "none"}:
        return None
    if str(model.get("activation_dtype") or "") not in _FLOAT_ACTIVATIONS:
        return None
    if str(model.get("weight_dtype") or "") not in _FLOAT_ACTIVATIONS:
        return None
    latent = model.get("expert_latent_size")
    if isinstance(latent, int) and not isinstance(latent, bool) and latent not in {0, model.get("hidden_size")}:
        return None
    tp = _positive_int(runtime.get("tp"))
    dp = _positive_int(runtime.get("dp"))
    ep = _positive_int(runtime.get("ep"))
    pp = _positive_int(runtime.get("pp")) if runtime.get("pp") is not None else 1
    cp = _positive_int(runtime.get("cp")) if runtime.get("cp") is not None else 1
    pcp = _positive_int(runtime.get("pcp")) if runtime.get("pcp") is not None else 1
    if None in {tp, dp, ep, pp, cp, pcp} or tp < 2 or dp != 1 or ep != tp or cp != 1 or pcp != 1:
        return None
    if str(runtime.get("moe_recipe") or "alltoall") != "alltoall":
        return None
    if runtime.get("sequence_parallel") or runtime.get("enable_sequence_parallel"):
        return None
    kernels = runtime.get("kernels") if isinstance(runtime.get("kernels"), Mapping) else {}
    if "moe_token_partition" in kernels or "moe_transport" in kernels:
        return None
    experts = model.get("num_experts")
    machine = case.get("machine") if isinstance(case.get("machine"), Mapping) else {}
    if not _device_selects_mc2(str(machine.get("sku") or ""), experts if isinstance(experts, int) else None, ep):
        return None
    capacity = _mc2_token_capacity(runtime, tp)
    if not token_counts or any(
        isinstance(item, bool) or not isinstance(item, int) or item < 1 or item > capacity for item in token_counts
    ):
        return None
    return {
        "kind": "vllm_ascend_mc2_tp_slice",
        "padding": "right_to_tp",
        "padding_implementation": "concat",
        "gather_output_materialization": "view",
        "logits_dtype": "float32",
        "layer_scopes": ["body"],
    }


def _bind_mc2_tp_caller(case: dict[str, Any], token_counts: Sequence[Any]) -> None:
    declaration = _mc2_tp_caller_declaration(case, token_counts)
    runtime = case.get("runtime")
    if declaration is None or not isinstance(runtime, dict):
        return
    kernels = runtime.get("kernels")
    if not isinstance(kernels, dict):
        kernels = runtime["kernels"] = {}
    kernels["moe_token_partition"] = declaration


def archive_probe(resolved: Mapping[str, Any]) -> dict[str, Any]:
    """Join producer frames. Do not rebuild them from receipt forwards."""
    from fleet_operator_modeling import (
        _as_int,
        _failure_probe,
        _strip_measured_overrides,
        _structural_sha,
        _structural_workload,
    )

    role = "archive_case"
    diagnostics = [str(item) for item in (resolved.get("diagnostics") or [])]
    provenance = resolved.get("provenance") if isinstance(resolved.get("provenance"), Mapping) else {}
    relation = str(provenance.get("evaluation_relation") or "")
    if provenance.get("holdout_independent") and any(
        token in relation.lower() for token in ("retrospective", "previously_inspected", "not_blind", "in_sample")
    ):
        diagnostics.append("holdout_independent_conflicts_with_evaluation_relation")
    if resolved.get("status") != "resolved":
        return _failure_probe(
            str(resolved.get("status") or "insufficient_evidence"),
            diagnostics,
            resolved.get("needed") or [],
            role,
        )
    source = resolved.get("source") if isinstance(resolved.get("source"), Mapping) else {}
    if source.get("sha256_verified") is not True:
        return _failure_probe(
            "insufficient_evidence",
            diagnostics + ["source_sha256_not_verified"],
            ["verified physical source"],
            role,
        )
    geometry = resolved.get("geometry") if isinstance(resolved.get("geometry"), Mapping) else {}
    prefix = geometry.get("prefix") if isinstance(geometry.get("prefix"), Mapping) else {}
    observed_cache = prefix.get("observed_cached_tokens")
    designed = prefix.get("designed_prefix_tokens")
    designed_by_source = prefix.get("designed_prefix_by_source")
    if isinstance(observed_cache, int) and observed_cache >= 0:
        diagnostics.append(f"observed_cached_tokens_kept:{observed_cache}")
    if designed is not None or designed_by_source:
        diagnostics.append("designed_prefix_not_used_as_step_context")
    window_fields = geometry.get("window_fields") if isinstance(geometry.get("window_fields"), Mapping) else {}
    deployment_dp = window_fields.get("deployment_dp")
    if isinstance(deployment_dp, int):
        diagnostics.append("deployment_dp_is_cell_launch_not_per_window")
    phase = str(resolved.get("phase") or "").lower()
    producer_frames = [item for item in (geometry.get("frames") or []) if isinstance(item, Mapping)]
    captured_frame_scope = None
    if producer_frames:
        frames, steps, frame_notes, needed_by_id = _join_producer_frames(producer_frames, phase)
        diagnostics.extend(frame_notes)
        diagnostics.append("producer_frames_are_the_step_schedule")
        if not steps:
            captured_frame_scope = {
                "status": "insufficient_evidence", "needed": ["context_tokens"],
                "frames": frames, "needed_by_id": needed_by_id,
                "reason": "captured frame identity has no concrete context_tokens",
            }
            service = (
                _declared_service_step(resolved, geometry, phase)
                if resolved.get("predictable_scope") == "declared_service_request" else None
            )
            if service is None:
                return _failure_probe(
                    "insufficient_evidence",
                    diagnostics + ([] if "context_tokens_not_observed" in diagnostics else ["context_tokens_not_observed"]),
                    ["context_tokens"],
                    role,
                ) | _identity_hold(resolved, source, frames, needed_by_id, prefix, window_fields)
            frames = []
            steps = service["steps"]
            sequences, tokens, context = service["sequences"], service["tokens"], service["context"]
            context_source = service["context_source"]
            diagnostics.append("declared_service_scope_used")
            diagnostics.append("captured_frame_k_not_used_for_service_scope")
            populations = [{
                "sequences_per_replica": sequences, "tokens_per_sequence": tokens,
                "context_tokens": context, "forward_count": 1,
            }]
        else:
            sequences, tokens, context = steps[0][2], steps[0][0], steps[0][1]
        if steps and not captured_frame_scope:
            populations = [{
                "sequences_per_replica": step_sequences,
                "tokens_per_sequence": step_tokens,
                "context_tokens": step_context,
                "forward_count": 1,
            } for step_tokens, step_context, step_sequences in steps]
            context_source = "producer_geometry_frames"
    else:
        frames, steps, populations, sequences, tokens, context, context_source, population_notes = _population_schedule(
            resolved, geometry,
        )
        diagnostics.extend(population_notes)
        needed_by_id = {}
        if steps is None and not isinstance(context, int):
            return _failure_probe(
                "insufficient_evidence",
                diagnostics,
                ["context_tokens"] if "context_tokens_not_observed" in diagnostics else (resolved.get("needed") or []),
                role,
            )
    if phase not in {"decode", "prefill"} or not isinstance(sequences, int) or not isinstance(tokens, int) or not isinstance(context, int):
        return _failure_probe(
            "insufficient_evidence",
            diagnostics + ["archive_population_geometry_incomplete"],
            ["sequences", "tokens", "context"],
            role,
        )
    case = resolved.get("case")
    if not isinstance(case, Mapping):
        return _failure_probe("insufficient_evidence", diagnostics + ["archive_case_absent"], ["structural case"], role)
    prepared = copy.deepcopy(dict(case))
    prepared["workload"] = _structural_workload(phase, sequences, tokens, context)
    if isinstance(observed_cache, int) and observed_cache >= 0:
        workload = dict(prepared["workload"])
        workload["prefix_tokens"] = observed_cache
        prepared["workload"] = workload
        if isinstance(designed, int) and designed != observed_cache:
            diagnostics.append("designed_prefix_kept_off_workload_prefix")
    diagnostics.append("workload_supplied_from_structural_population")
    if relation:
        diagnostics.append(f"evaluation_relation:{relation}")
    blind, calibration = _strip_measured_overrides(prepared)
    parallel_in = geometry.get("parallel") or {}
    parallel: dict[str, int] = {}
    for axis in ("tp", "dp", "ep", "pp"):
        value = _as_int(parallel_in.get(axis) if isinstance(parallel_in, Mapping) else None)
        if value is None or value < 1:
            return _failure_probe("insufficient_evidence", diagnostics + [f"{axis}_not_declared"], [axis], role)
        parallel[axis] = value
    machine = blind.get("machine") if isinstance(blind.get("machine"), Mapping) else {}
    runtime = blind.get("runtime") if isinstance(blind.get("runtime"), Mapping) else {}
    decision = _supply_decision(machine, geometry)
    diagnostics.append(str(decision["diagnostic"]))
    if (decision["kind"] in {"template_sku_family_fallback", "case_sku_family_fallback"}
            and isinstance(machine, dict) and not machine.get("sku") and decision.get("sku")):
        machine = dict(machine)
        machine["sku"] = str(decision["sku"])
        blind["machine"] = machine
    labeled = _label_rows(decision["rows"], decision)
    needed = list(decision.get("needed") or [])
    single_sku_case = decision["kind"] == "single_sku"
    exact = None if single_sku_case else False
    contexts = [item[1] for item in steps] if isinstance(steps, list) else [context]
    capture_id = resolved.get("capture_id")
    if not needed_by_id and frames and needed:
        from hf_sample_scoring import sample_key
        for frame in frames:
            key = _frame_key(frame, sample_key)
            if key:
                needed_by_id[key] = list(needed)
    if isinstance(steps, list):
        _bind_mc2_tp_caller(blind, [item[0] for item in steps])
    ambiguous = {
        "machine_sku": machine.get("sku") if machine.get("sku") else None,
        "supply_kind": decision["kind"],
        "exact": exact,
        "unmapped_identities": list(decision.get("unmapped_identities") or []),
        "audit_candidates": list(decision.get("audit") or []),
    }
    return {
        "ok": True,
        "single_sku_case": single_sku_case,
        "exact": exact,
        "case": blind,
        "case_path": str(provenance.get("original_case_path") or ""),
        "deployment_sha256": str(provenance.get("physical_source_id") or provenance.get("original_case_sha256") or ""),
        "structural_sha256": _structural_sha(blind),
        "phase": phase,
        "parallel": parallel,
        "sequences": sequences,
        "tokens": tokens,
        "context": context,
        "context_tokens_min": min(contexts) if contexts else None,
        "context_tokens_max": max(contexts) if contexts else None,
        "context_source": context_source,
        "population": populations[0] if populations else {},
        "populations": populations,
        "frames": frames,
        "chunk_steps": steps,
        "calibration": calibration,
        "sku": str(decision.get("sku") or ""),
        "diagnostics": diagnostics,
        "needed": needed,
        "needed_by_id": needed_by_id,
        "runtime": dict(runtime),
        "graph_mode": runtime.get("graph_mode") or runtime.get("graph_capture_mode"),
        "mtp_proposal_tokens": 0,
        "source_role": role,
        "evaluation_relation": relation,
        "predictable_scope": "declared_service_request" if captured_frame_scope else resolved.get("predictable_scope"),
        "target_scope": "declared_service_request" if captured_frame_scope else resolved.get("predictable_scope"),
        "captured_frame_scope": captured_frame_scope,
        "service_scope": _declared_service_step(resolved, geometry, phase)["service_scope"] if captured_frame_scope else None,
        "source_sha256": str(source.get("sha256") or ""),
        "source_sha_basis": "verified_physical_source" if source.get("sha256") else "",
        "capture_id": capture_id,
        "hardware_alternatives": [],
        "hardware_candidates": labeled,
        "hardware_selection": decision.get("hardware_selection") or "",
        "supply_kind": decision["kind"],
        "supply": {key: value for key, value in decision.items() if key not in {"rows", "diagnostic"}},
        "observed_cached_tokens": observed_cache if isinstance(observed_cache, int) else None,
        "designed_prefix_tokens": designed if isinstance(designed, int) else None,
        "designed_prefix_by_source": list(designed_by_source) if isinstance(designed_by_source, list) else None,
        "deployment_dp": deployment_dp if isinstance(deployment_dp, int) else None,
        "deployment_dp_per_window": False,
        "ambiguous": ambiguous,
        "receipt_index_is_task_local": False,
    }


def frame_indexes(probe: Mapping[str, Any], material_indexes: Sequence[int] | None = None) -> list[int]:
    """Every declared step, unless the caller names a material window."""
    count = len(probe.get("chunk_steps") or [])
    if material_indexes is None:
        return list(range(count))
    chosen = [int(item) for item in material_indexes]
    if any(item < 0 or item >= count for item in chosen):
        raise ValueError("material index outside declared frames")
    return chosen


def publish_archive_prediction(
    probe: Mapping[str, Any],
    cfg: Mapping[str, Any],
    *,
    material_indexes: Sequence[int] | None = None,
) -> dict[str, Any] | None:
    """Price an agreed supply. One untouched catalog sku still uses the shared pricer.

    ``material_indexes`` limits a check to those declared frames. The ordinary
    caller omits it and every true frame is priced. A partial window is marked
    and is not an ordinary missing account.
    """
    if not probe.get("ok"):
        return None
    kind = probe.get("supply_kind")
    if kind == "single_sku":
        return None
    if kind == "unknown":
        return _unknown_publication(probe, cfg)
    if kind not in {"declared_producer_sku", "conditional_invariant"}:
        return None
    from fleet_operator_archive_engine import price_ordered_frames

    indexes = frame_indexes(probe, material_indexes)
    priced = price_ordered_frames(probe, indexes)
    return _publication(probe, cfg, priced, material_indexes is not None, indexes)


def price_archive_scenario(probe: Mapping[str, Any], sku: str, cfg: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Price only the agreed supply. A contrary template or alias is refused."""
    supply = probe.get("supply") if isinstance(probe.get("supply"), Mapping) else {}
    agreed = supply.get("kind") in {"declared_producer_sku", "conditional_invariant"} and sku == supply.get("sku")
    if not agreed:
        return {
            "sku": sku or None,
            "catalog_sku": sku or None,
            "priced": False,
            "selected": False,
            "exact": False,
            "reason": "not_the_agreed_hardware_supply",
        }
    published = publish_archive_prediction(probe, cfg or {})
    if not isinstance(published, dict):
        return {"sku": sku, "catalog_sku": sku, "priced": False, "selected": False, "exact": False, "reason": "supply_not_priced"}
    published["priced"] = published.get("status") == "modeled"
    published["catalog_sku"] = sku
    published["sku"] = sku
    published["selected"] = False
    published["exact"] = False
    return published


def _unknown_publication(probe: Mapping[str, Any], cfg: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "engine": "mindie_sim.prediction.body.body_forward",
        "measurement_features_read": False,
        "status": "insufficient_evidence",
        "ok": False,
        "capture_id": probe.get("capture_id") or cfg.get("capture_id"),
        "phase": probe.get("phase") or cfg.get("phase"),
        "hardware_tier": cfg.get("hardware_tier"),
        "source_role": probe.get("source_role") or "archive_case",
        "source_sha256": probe.get("source_sha256") or "",
        "source_sha_basis": probe.get("source_sha_basis") or "",
        "predicted_step_ms": None,
        "predicted_operator_ms": None,
        "hardware_candidates": list(probe.get("hardware_candidates") or []),
        "hardware_selection": "not_selected",
        "supply_kind": "unknown",
        "sku": "",
        "exact": False,
        "needed": list(probe.get("needed") or []),
        "needed_by_id": {str(key): list(value) for key, value in (probe.get("needed_by_id") or {}).items()},
        "diagnostics": list(probe.get("diagnostics") or []),
        "frames": list(probe.get("frames") or []),
        "ambiguous": probe.get("ambiguous") or {},
        "observed_cached_tokens": probe.get("observed_cached_tokens"),
        "designed_prefix_tokens": probe.get("designed_prefix_tokens"),
        "designed_prefix_by_source": probe.get("designed_prefix_by_source"),
        "deployment_dp": probe.get("deployment_dp"),
        "deployment_dp_per_window": False,
        "context_tokens_min": probe.get("context_tokens_min"),
        "context_tokens_max": probe.get("context_tokens_max"),
        "coverage": {
            "modeled": False,
            "exact_score": False,
            "hardware_selection": "not_selected",
            "absent_scopes_remain_in_denominator": True,
        },
    }


def _publication(
    probe: Mapping[str, Any],
    cfg: Mapping[str, Any],
    priced: Mapping[str, Any],
    material: bool,
    indexes: Sequence[int],
) -> dict[str, Any]:
    supply = probe.get("supply") if isinstance(probe.get("supply"), Mapping) else {}
    diagnostics = list(probe.get("diagnostics") or [])
    if not priced.get("ok"):
        diagnostics.extend(str(item) for item in (priced.get("diagnostics") or []))
        failure = _unknown_publication(probe, cfg)
        failure["status"] = priced.get("status") or "insufficient_evidence"
        failure["diagnostics"] = diagnostics
        failure["needed"] = list(priced.get("needed") or failure["needed"])
        return failure
    candidates = []
    for row in probe.get("hardware_candidates") or []:
        if not isinstance(row, Mapping):
            continue
        item = dict(row)
        item["priced"] = bool(item.get("supply")) and priced.get("status") == "modeled"
        item["selected"] = False
        item["exact"] = False
        item["serial_certified"] = False
        candidates.append(item)
    attribution = {
        "body": "recomputed_body_from_genuine_declaration",
        "wave5_original_in_sample_row": "separate",
        "target_timing_used_to_fit": False,
        "declaration_evaluation_relation": probe.get("evaluation_relation") or "",
    }
    record = {
        "engine": priced.get("engine") or "mindie_sim.prediction.body.body_forward",
        "measurement_features_read": False,
        "status": "modeled",
        "capture_id": probe.get("capture_id") or cfg.get("capture_id"),
        "phase": probe.get("phase") or cfg.get("phase"),
        "hardware_tier": cfg.get("hardware_tier"),
        "source_role": probe.get("source_role") or "archive_case",
        "source_sha256": probe.get("source_sha256") or "",
        "source_sha_basis": probe.get("source_sha_basis") or "",
        "predicted_step_ms": priced.get("predicted_step_ms"),
        "predicted_operator_ms": priced.get("predicted_operator_ms"),
        "predicted_by_scope_ms": priced.get("predicted_by_scope_ms") or {},
        "predicted_by_canonical_family_ms": priced.get("predicted_by_canonical_family_ms") or {},
        "predicted_by_family_ms": priced.get("predicted_by_family_ms") or {},
        "predicted_by_unified_family_ms": priced.get("predicted_by_unified_family_ms") or {},
        "predicted_by_core_ms": priced.get("predicted_by_core_ms") or {},
        "hardware_candidates": candidates,
        "hardware_selection": probe.get("hardware_selection"),
        "hardware_supply": {
            "sku": supply.get("sku"),
            "role": supply.get("role"),
            "kind": supply.get("kind"),
            "exact": False,
            "serial_certified": False,
            "equipment_proof": None,
            "declared_identity": supply.get("declared_identity"),
            "source_label": supply.get("source_label"),
            "provenance": supply.get("provenance") or supply.get("evidence"),
            "candidates": supply.get("candidates"),
            "not_from_measured_times": supply.get("not_from_measured_times"),
        },
        "attribution": attribution,
        "target_timing_used_to_fit": False,
        "target_scope": probe.get("target_scope") or probe.get("predictable_scope"),
        "captured_frame_scope": probe.get("captured_frame_scope"),
        "service_scope": probe.get("service_scope"),
        "exact": False,
        "sku": supply.get("sku") or "",
        "needed": [],
        "needed_by_id": {},
        "diagnostics": diagnostics,
        "frames": [dict(probe["frames"][index]) for index in indexes if index < len(probe.get("frames") or ())],
        "ambiguous": probe.get("ambiguous") or {},
        "observed_cached_tokens": probe.get("observed_cached_tokens"),
        "designed_prefix_tokens": probe.get("designed_prefix_tokens"),
        "designed_prefix_by_source": probe.get("designed_prefix_by_source"),
        "deployment_dp": probe.get("deployment_dp"),
        "deployment_dp_per_window": False,
        "context_tokens_min": min(probe["chunk_steps"][index][1] for index in indexes),
        "context_tokens_max": max(probe["chunk_steps"][index][1] for index in indexes),
        "material_window": material,
        "ordinary_frame_count": len(probe.get("chunk_steps") or []),
        "working_set": priced.get("working_set"),
        "engine_stats": priced.get("engine_stats"),
        "coverage": {
            "modeled": True,
            "exact_score": False,
            "serial_certified": False,
            "hardware_selection": probe.get("hardware_selection"),
            "material_window_is_not_the_ordinary_population": material,
            "ordinary_frame_count": len(probe.get("chunk_steps") or []),
            "priced_frames": len(indexes),
            "target_timing_used_to_fit": False,
            "recomputed_body_from_genuine_declaration": True,
            "wave5_original_in_sample_row": "separate",
            "core_forecast": priced.get("core_forecast"),
            "core_map_is_complete_forecast": priced.get("core_map_is_complete_forecast"),
            "unresolved_core_elapsed_ms": priced.get("unresolved_core_elapsed_ms"),
            "bound_core_elapsed_ms": priced.get("bound_core_elapsed_ms"),
        },
    }
    for name in (
        "prediction_boundary", "boundary_basis", "boundary_samples", "boundary_samples_ms",
        "boundaries", "predicted_operator_groups",
    ):
        if name in priced:
            record[name] = priced[name]
    # A defaulted request count is not a certificate. The qlen graph and the
    # forecast stay on the enrolled row. Decode frames are a different publication.
    if (
        str(record.get("phase") or "").lower() == "prefill"
        and "sequences_per_replica_absent_on_frame_uses_one_request" in diagnostics
    ):
        record["status"] = "conditional"
        record["coverage"]["modeled"] = False
        record["coverage"]["sequence_count_certified"] = False
        record["diagnostics"].append("sequence_count_not_certified:conditional_forecast_retained")
    return record


def _join_producer_frames(
    frames: Sequence[Mapping[str, Any]], phase: str,
) -> tuple[list[dict[str, Any]], list[tuple[int, int, int]], list[str], dict[str, list[str]]]:
    """Keep receipt identity, chunk ordinal, and the producer context together."""
    from hf_sample_scoring import sample_key

    notes: list[str] = []
    joined: list[dict[str, Any]] = []
    steps: list[tuple[int, int, int]] = []
    needed_by_id: dict[str, list[str]] = {}
    defaulted_sequences = False
    for raw in frames:
        item = dict(raw)
        item_phase = str(item.get("phase") or phase or "").lower()
        item["phase"] = item_phase
        if item.get("device_id") in (None, "") and item.get("receipt_device_id") not in (None, ""):
            item["device_id"] = item["receipt_device_id"]
        if item.get("rank_id") in (None, ""):
            item["rank_id"] = None
        if "receipt_rank_id" not in item:
            item["receipt_rank_id"] = ""
        chunk_forward = item.get("forward_id")
        item["chunk_forward_id"] = chunk_forward
        receipt_forward = item.get("receipt_forward_id")
        if receipt_forward not in (None, ""):
            item["forward_id"] = receipt_forward
        query = item.get("query_rows")
        context = item.get("context_tokens")
        sequences = item.get("sequences_per_replica")
        if not isinstance(sequences, int) or isinstance(sequences, bool) or sequences < 1:
            sequences = 1
            item["sequences_per_replica"] = sequences
            defaulted_sequences = True
        item["tokens_per_sequence"] = query if isinstance(query, int) and not isinstance(query, bool) else None
        gaps: list[str] = []
        if not isinstance(query, int) or isinstance(query, bool) or query < 1:
            gaps.append("query_rows")
        if not isinstance(context, int) or isinstance(context, bool) or context < 0:
            gaps.append("context_tokens")
        key = _frame_key(item, sample_key)
        if gaps:
            if key:
                needed_by_id[key] = gaps
            joined.append(item)
            continue
        steps.append((int(query), int(context), int(sequences)))
        joined.append(item)
    if defaulted_sequences:
        notes.append("sequences_per_replica_absent_on_frame_uses_one_request")
    return joined, steps, notes, needed_by_id


def _frame_key(frame: Mapping[str, Any], sample_key) -> str:
    identity = {}
    for name in ("phase", "device_id", "forward_id"):
        raw = frame.get(name)
        if raw in (None, ""):
            continue
        identity[name] = raw
    if not identity:
        return ""
    return str(sample_key(**identity))


def _declared_service_step(resolved: Mapping[str, Any], geometry: Mapping[str, Any],
                           phase: str) -> dict[str, Any] | None:
    """One initial service-request step from declared prompt and captured q shape.

    This is a different scope from a captured frame: the prompt is the declared
    initial KV, and the frame contributes only its genuine query/sequence axes.
    """
    case = resolved.get("case") if isinstance(resolved.get("case"), Mapping) else {}
    workload = case.get("workload") if isinstance(case.get("workload"), Mapping) else {}
    requests = [item for item in (workload.get("requests") or ()) if isinstance(item, Mapping)]
    prompts = {item.get("prompt_tokens") for item in requests
               if isinstance(item.get("prompt_tokens"), int) and not isinstance(item.get("prompt_tokens"), bool)
               and item.get("prompt_tokens") >= 0}
    populations = [item for item in (geometry.get("populations") or ()) if isinstance(item, Mapping)]
    if len(prompts) != 1 or len(populations) != 1:
        return None
    prompt = next(iter(prompts))
    pop = populations[0]
    sequences = pop.get("sequences_per_replica")
    tokens = pop.get("tokens_per_sequence")
    if not all(isinstance(value, int) and not isinstance(value, bool) and value >= 1 for value in (sequences, tokens)):
        return None
    if phase == "decode":
        context = prompt
        basis = "declared_service_initial_prompt_context"
    elif phase == "prefill":
        context = 0
        basis = "declared_service_prefill_chunk_start"
    else:
        return None
    return {
        "steps": [(tokens, context, sequences)],
        "sequences": sequences, "tokens": tokens, "context": context,
        "context_source": basis,
        "service_scope": {
            "kind": "declared_service_request", "phase": phase,
            "prompt_tokens": prompt, "query_tokens_per_sequence": tokens,
            "sequences_per_replica": sequences, "initial_context_tokens": context,
            "basis": basis, "trajectory_steps": 1,
            "captured_frame_k_used": False, "acceptance_or_chunk_rate_used": False,
        },
    }


def _population_schedule(resolved, geometry):
    """No producer frames. One declared population stays a service request.

    Receipt windows are not turned into token contexts here.
    """
    populations = list(geometry.get("populations") or [])
    notes: list[str] = []
    if len(populations) != 1 or not isinstance(populations[0], Mapping):
        notes.append("archive_population_not_singular")
        return [], None, [], None, None, None, "", notes
    pop = populations[0]
    sequences = pop.get("sequences_per_replica")
    tokens = pop.get("tokens_per_sequence")
    context = pop.get("context_tokens")
    phase = str(resolved.get("phase") or pop.get("phase") or "").lower()
    if context is None or not isinstance(context, int) or isinstance(context, bool) or context < 0:
        notes.append("context_tokens_not_observed")
        return [], None, [], sequences, tokens, None, "", notes
    if not resolved.get("predictable") and context != 0:
        notes.append("archive_population_not_predictable")
        return [], None, [], sequences, tokens, None, "", notes
    if context == 0:
        notes.append("context_zero_is_declared_initial_cache")
    if (
        phase not in {"decode", "prefill"}
        or not isinstance(sequences, int) or isinstance(sequences, bool) or sequences < 1
        or not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 1
    ):
        notes.append("archive_population_geometry_incomplete")
        return [], None, [], sequences, tokens, context, "", notes
    row = {
        "sequences_per_replica": sequences,
        "tokens_per_sequence": tokens,
        "forward_count": pop.get("forward_count"),
        "context_tokens": context,
    }
    return [], None, [row], sequences, tokens, context, "archive_population", notes


def _catalog_sku(row: Mapping[str, Any]) -> str:
    sku = row.get("catalog_sku")
    return sku if isinstance(sku, str) and sku else ""


def _identity_family(value: Any) -> str:
    text = str(value or "")
    if text.startswith("Ascend910B"):
        return "A2"
    if text.startswith("Ascend910_93"):
        return "A3"
    if text.startswith("Ascend950") or text.startswith("Ascend910_95"):
        return "A5"
    return ""


def _supply_decision(machine: Mapping[str, Any], geometry: Mapping[str, Any]) -> dict[str, Any]:
    """One applied producer sku, or a rate-invariant set. A template is not a supply."""
    from fleet_operator_archive_engine import priced_rate_signature

    raw = geometry.get("hardware_candidates")
    rows = [item for item in raw if isinstance(item, Mapping)] if isinstance(raw, list) else []
    sku = machine.get("sku") if isinstance(machine.get("sku"), str) and machine.get("sku") else ""
    producer = [
        row for row in rows
        if row.get("role") == "producer_deployment_setting" and row.get("applied") is True and _catalog_sku(row)
    ]
    other_applied = [row for row in rows if row.get("applied") is True and row not in producer]
    if len(producer) == 1 and not other_applied and sku == _catalog_sku(producer[0]):
        return {
            "kind": "declared_producer_sku",
            "sku": sku,
            "role": "producer_deployment_setting",
            "declared_identity": producer[0].get("declared_identity"),
            "source_label": producer[0].get("source"),
            "provenance": "hardware_sku_declared_not_serial_verified",
            "exact": False,
            "serial_certified": False,
            "equipment_proof": None,
            "hardware_selection": "declared_producer_sku",
            "diagnostic": "producer_deployment_setting_sku_applied",
            "needed": [],
            "rows": rows,
            "unmapped_identities": [],
            "audit": _audit_rows(rows),
        }
    if not rows and sku:
        return {
            "kind": "single_sku",
            "sku": sku,
            "hardware_selection": "",
            "diagnostic": "single_catalog_sku_on_case",
            "needed": [],
            "rows": [],
            "unmapped_identities": [],
            "audit": [],
        }
    true = [row for row in rows if _catalog_sku(row) and row.get("role") not in _AUDIT_ROLES]
    signatures = [priced_rate_signature(_catalog_sku(row)) for row in true]
    if len(true) >= 2 and signatures[0] and all(item == signatures[0] for item in signatures):
        return {
            "kind": "conditional_invariant",
            "sku": _catalog_sku(true[0]),
            "role": true[0].get("role"),
            "declared_identity": true[0].get("declared_identity"),
            "source_label": true[0].get("source"),
            "evidence": "catalog_priced_rates_identical",
            "candidates": [_catalog_sku(row) for row in true],
            "not_from_measured_times": True,
            "exact": False,
            "serial_certified": False,
            "hardware_selection": "conditional_invariant",
            "diagnostic": "conditional_invariant_rates_from_catalog_inputs",
            "needed": [],
            "rows": rows,
            "unmapped_identities": [],
            "audit": _audit_rows(rows),
        }
    unmapped = []
    needed = []
    for row in rows:
        if row.get("role") == "producer_deployment_setting" and not _catalog_sku(row):
            identity = row.get("declared_identity") or "undeclared"
            unmapped.append(identity)
            needed.append(f"catalogue sku for declared identity {identity}")
    template = [
        row for row in rows
        if row.get("role") == "template_subtype_not_measurement" and _catalog_sku(row)
    ]
    if unmapped and not producer and len(template) == 1 and _identity_family(_catalog_sku(template[0])) and all(
            _identity_family(identity) == _identity_family(_catalog_sku(template[0])) for identity in unmapped):
        template_sku = _catalog_sku(template[0])
        return {
            "kind": "template_sku_family_fallback",
            "sku": template_sku,
            "declared_identity": ",".join(str(item) for item in unmapped),
            "source_label": "template subtype sku; source deployment identity unmapped",
            "provenance": "source_identity_unmapped_template_sku_family_match",
            "exact": False,
            "serial_certified": False,
            "equipment_proof": None,
            "hardware_selection": "template_sku_family_fallback",
            "diagnostic": "template_sku_family_fallback_after_unmapped_source_identity",
            "needed": [],
            "rows": rows,
            "unmapped_identities": unmapped,
            "audit": _audit_rows(rows),
        }
    if sku and unmapped and _identity_family(sku) and all(
            _identity_family(identity) == _identity_family(sku) for identity in unmapped):
        return {
            "kind": "case_sku_family_fallback",
            "sku": sku,
            "declared_identity": ",".join(str(item) for item in unmapped),
            "source_label": "original case machine sku; source deployment identity unmapped",
            "provenance": "source_identity_unmapped_case_sku_family_match",
            "exact": False,
            "serial_certified": False,
            "equipment_proof": None,
            "hardware_selection": "case_sku_family_fallback",
            "diagnostic": "unmapped_source_identity_case_sku_family_fallback",
            "needed": [],
            "rows": rows,
            "unmapped_identities": unmapped,
            "audit": _audit_rows(rows),
        }
    return {
        "kind": "unknown",
        "sku": "",
        "exact": False,
        "hardware_selection": "not_selected",
        "diagnostic": "hardware_supply_not_concrete",
        "needed": needed,
        "rows": rows,
        "unmapped_identities": unmapped,
        "audit": _audit_rows(rows),
    }


def _audit_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"catalog_sku": _catalog_sku(row) or None, "role": row.get("role"), "applied": row.get("applied")}
        for row in rows if row.get("role") in _AUDIT_ROLES
    ]


def _label_rows(rows: Sequence[Mapping[str, Any]], decision: Mapping[str, Any]) -> list[dict[str, Any]]:
    chosen = decision.get("sku") if decision.get("kind") == "declared_producer_sku" else ""
    labeled = []
    for row in rows:
        sku = _catalog_sku(row) or None
        agreed = bool(
            chosen and sku == chosen and row.get("role") == "producer_deployment_setting" and row.get("applied") is True
        )
        entry = {
            "sku": sku,
            "declared_identity": row.get("declared_identity") or sku,
            "catalog_sku": sku,
            "role": row.get("role"),
            "applied": row.get("applied"),
            "priority": row.get("priority"),
            "host": row.get("host"),
            "source": row.get("source"),
            "equipment_proof": None,
            "priced": False,
            "selected": False,
            "exact": False,
            "serial_certified": False,
            "supply": agreed,
        }
        if not sku:
            entry["reason"] = "declared_identity_has_no_catalog_sku"
        elif row.get("role") in _AUDIT_ROLES or row.get("applied") is False:
            entry["reason"] = str(row.get("role") or "not_applied")
        labeled.append(entry)
    return labeled


def _identity_hold(resolved, source, frames, needed_by_id, prefix, window_fields) -> dict[str, Any]:
    return {
        "capture_id": resolved.get("capture_id"),
        "source_sha256": str(source.get("sha256") or ""),
        "frames": frames,
        "needed_by_id": needed_by_id,
        "observed_cached_tokens": prefix.get("observed_cached_tokens"),
        "designed_prefix_tokens": prefix.get("designed_prefix_tokens"),
        "designed_prefix_by_source": prefix.get("designed_prefix_by_source"),
        "deployment_dp": window_fields.get("deployment_dp"),
        "deployment_dp_per_window": False,
        "hardware_selection": "not_selected",
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """CLI r3 uses for the full declared-frame price. The default is every frame."""
    parser = argparse.ArgumentParser(prog="fleet_operator_archive")
    parser.add_argument("--jsonl", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--capture-id", action="append", default=[])
    parser.add_argument(
        "--ordinary-four-body",
        action="store_true",
        help="Price every row through the canonical caller. Ignores a material window.",
    )
    parser.add_argument(
        "--material-indexes",
        default="",
        help="Comma-separated declared frame indexes for a bounded check. Empty prices every frame.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def _material_indexes(text: str) -> list[int] | None:
    if not str(text or "").strip():
        return None
    return [int(item) for item in str(text).split(",") if item.strip()]


def main(argv: Sequence[str] | None = None) -> int:
    """Start an archive price. Ordinary four-body and the full 139 belong to r3."""
    args = parse_args(argv)
    if args.ordinary_four_body and args.material_indexes.strip():
        raise SystemExit("ordinary-four-body prices every declared frame")
    rows = []
    for line in Path(args.jsonl).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    wanted = set(args.capture_id)
    if wanted:
        rows = [row for row in rows if row.get("capture_id") in wanted]
    if args.ordinary_four_body:
        from fleet_operator_modeling import predict_capture_operators_and_step
        payload = {
            "mode": "ordinary_four_body",
            "rows": [predict_capture_operators_and_step(row) for row in rows],
        }
    else:
        import fleet_archive_case as archive_case
        archive_case.configure_archive_roots(receipt_index=None)
        indexes = _material_indexes(args.material_indexes)
        priced = []
        for row in rows:
            resolved = archive_case.resolve_archive_case(row)
            probe = archive_probe(resolved)
            priced.append(publish_archive_prediction(probe, row, material_indexes=indexes))
        payload = {"mode": "archive_frames", "material_indexes": indexes, "rows": priced}
    Path(args.out).write_text(json.dumps(payload, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
