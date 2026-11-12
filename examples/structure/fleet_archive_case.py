"""Structural case mapping for DSH, Wave 5, and extended fleet captures."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

import fleet_archive_producer as producer
import fleet_archive_sources as sources
from fleet_archive_model import _model_identity, _reconcile_model
from fleet_archive_route_geometry import apply_witnessed_route
from fleet_archive_typed_deployment import bind_witnessed_expert_caller

_DOMAIN = {
    "dsh_20261030_heldout": "dsh",
    "wave5_20261031": "wave5",
    "extended_a3_a5_workstream_captures": "extended",
}
_TIMING_KEYS = {
    "service_regimes", "rates", "resource_units", "work_units", "active_work",
    "response", "fixed_us", "us_per_unit", "observed_ms", "predicted_ms",
    "relative_error", "body_forward_span_ms", "body_activity_ms", "per_layer_ms",
}
_SCHEDULER_KEYS = (
    "max_model_len", "max_num_seqs", "max_num_batched_tokens", "kv_block_size",
    "enable_chunked_prefill", "graph_mode", "graph_buckets", "graph_capture_keys", "pp",
)
_A5_BASE = {
    "qwen3-30b-a3b": "decode-qwen35-35b-a5-tp4-c4-graph.json",
    "synth-qwen3-30b-a3b": "decode-qwen35-35b-a5-tp4-c4-graph.json",
    "qwen3.5-35b-a3b": "decode-qwen35-35b-a5-tp4-c4-graph.json",
    "synth-qwen3.5-35b-a3b": "decode-qwen35-35b-a5-tp4-c4-graph.json",
    "qwen3.6-27b": "a5-qwen36-tp4-long-context-source.json",
    "qwen3.8-27b": "a5-qwen38-tp4-long-context-source.json",
}

def configure_archive_roots(*, data_roots=None, results_dir=None, cases_dir=None,
                            archive_root=None, receipt_index=None, cases_index=None) -> None:
    sources.configure_roots(
        data_roots=data_roots, results_dir=results_dir, cases_dir=cases_dir,
        archive_root=archive_root, receipt_index=receipt_index, cases_index=cases_index,
    )


def clear_archive_caches() -> None:
    sources.clear_caches()


def archive_case_domain(row: Mapping[str, Any] | None) -> bool:
    return _suite(row) in _DOMAIN


def resolve_archive_case(row: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(row, Mapping) or not archive_case_domain(row):
        return None
    suite = _suite(row)
    kind = _DOMAIN[suite]
    capture_id = str(row.get("capture_id") or "")
    if kind == "extended":
        return _resolve_extended(row, capture_id)
    record = sources.registry().get(capture_id)
    if record is None:
        return _diagnostic(row, "insufficient_evidence", ["registry_record_missing"], ["registry result for capture_id"])
    return _resolve_record(row, record, alias_of=())


def select_population(result: Mapping[str, Any] | None, sequences: int, tokens: int) -> dict[str, Any] | None:
    if not isinstance(result, Mapping):
        return None
    populations = ((result.get("geometry") or {}).get("populations") or [])
    matches = [dict(item) for item in populations
               if item.get("sequences_per_replica") == sequences and item.get("tokens_per_sequence") == tokens]
    return matches[0] if len(matches) == 1 else None


def _suite(row: Mapping[str, Any] | None) -> str:
    if not isinstance(row, Mapping):
        return ""
    suite = row.get("suite")
    if isinstance(suite, str) and suite:
        return suite
    capture = str(row.get("capture_id") or "")
    if capture.startswith("dsh_heldout:"):
        return "dsh_20261030_heldout"
    if capture.startswith("wave5:"):
        return "wave5_20261031"
    if capture.startswith("extended_a3_a5_workstream_captures:"):
        return "extended_a3_a5_workstream_captures"
    return ""


def _diagnostic(row: Mapping[str, Any], status: str, diagnostics: list[str], needed: list[str], **extra: Any) -> dict[str, Any]:
    out = {
        "status": status, "capture_id": str(row.get("capture_id") or ""), "suite": _suite(row),
        "phase": extra.pop("phase", None),
        "source": extra.pop("source", {"path": None, "sha256": None, "size_bytes": None, "sha256_verified": False}),
        "provenance": extra.pop("provenance", {}),
        "geometry": extra.pop("geometry", {"populations": [], "missing": list(needed)}),
        "case": None, "case_ready_for_parse": False, "predictable": False,
        "diagnostics": diagnostics, "needed": needed,
    }
    out.update(extra)
    return out


def _holdout(relation: Any, fitted: Any = None) -> tuple[bool, str | None]:
    text = relation.strip() if isinstance(relation, str) else ""
    low = text.lower()
    blocked = fitted is True or not text or any(token in low for token in (
        "in_sample", "not_blind", "not_declared", "retrospective", "previously_inspected",
    ))
    if blocked:
        detail = text or ("target_timing_used_to_fit" if fitted is True else "absent")
        return False, f"registry_relation:{detail}"
    if any(token in low for token in ("not_used_for_fitting", "frozen_before_latency_read", "independent_heldout")):
        return True, None
    return False, f"relation_does_not_establish_independent_heldout:{text}"


def _sku_family(sku: str) -> str | None:
    if sku.startswith("Ascend910B"):
        return "A2"
    if sku.startswith("Ascend910_93"):
        return "A3"
    return "A5" if sku.startswith("Ascend950") or sku.startswith("Ascend910_95") else None


def _path_tokens(path: str) -> dict[str, int | str]:
    parts = Path(path).parts
    cell = parts[-2] if len(parts) >= 2 else ""
    ancestors = "/".join(parts[-4:-2])
    found: dict[str, int | str] = {}
    for axis in ("tp", "dp", "ep", "layers", "num_experts", "top_k"):
        chosen = _axis_token(cell, axis)
        if chosen is None:
            chosen = _axis_token(ancestors, axis)
        if isinstance(chosen, int):
            found[axis] = chosen
        elif isinstance(chosen, str):
            found[axis] = chosen
    return found


def _axis_token(text: str, axis: str) -> int | str | None:
    if not text:
        return None
    pattern = {"tp": "tp", "dp": "dp", "ep": "ep", "layers": "L", "num_experts": "E", "top_k": "K"}[axis]
    values = [int(item) for item in re.findall(rf"(?:^|[^A-Za-z]){pattern}(\d+)", text)]
    if axis == "dp":
        values.extend(int(item) for item in re.findall(r"tp\d+dp(\d+)", text))
    if axis == "ep":
        values.extend(int(item) for item in re.findall(r"tp\d+(?:dp\d+)?_?ep(\d+)", text))
    unique = list(dict.fromkeys(values))
    if not unique:
        return None
    if len(unique) == 1:
        return unique[0]
    if axis == "dp":
        cluster = list(dict.fromkeys(int(item) for item in re.findall(r"tp\d+dp(\d+)", text)))
        ranks = [item for item in unique if item not in cluster]
        if len(cluster) == 1 and ranks and all(re.search(rf"(?:^|_)dp{item}(?:[^0-9]|$)", text) for item in ranks):
            return cluster[0]
    return "conflict:" + axis + ":path=" + ",".join(str(item) for item in unique)


def _resolve_extended(row: Mapping[str, Any], capture_id: str) -> dict[str, Any]:
    rel = capture_id.split(":", 1)[1] if ":" in capture_id else ""
    paths = sources.locate_kernels(rel)
    if not paths:
        return _diagnostic(row, "insufficient_evidence", ["extended_source_not_found"], ["kernel_details under data root"])
    classified = sources.classify_kernels(paths)
    if isinstance(classified, dict):
        status = "conflict" if classified["diagnostics"][0] in {
            "kernel_serializations_disagree", "kernel_joins_disagree", "sha_matches_multiple_sources",
        } else "insufficient_evidence"
        return _diagnostic(row, status, classified["diagnostics"], classified["needed"], source=classified.get("source"))
    path, canonical, registered = classified
    if canonical is not None:
        alias = [{"suite": canonical["suite"], "capture_id": canonical["capture_id"], "source_path": canonical["source_path"]}]
        resolved = _resolve_record(row, canonical, alias_of=alias)
        resolved["capture_id"] = capture_id
        resolved["suite"] = _suite(row)
        resolved["provenance"]["alias_of"] = alias
        resolved["provenance"]["original_capture_id"] = capture_id
        return resolved
    if registered is not None:
        return _resolve_registered_alias(row, capture_id, path, registered)
    return _diagnostic(row, "insufficient_evidence", ["extended_source_has_no_structural_declaration"],
                       ["extraction receipt or registered case"])


def _resolve_registered_alias(row: Mapping[str, Any], capture_id: str, path: Path, registered: Mapping[str, Any]) -> dict[str, Any]:
    relation = registered.get("evaluation_relation")
    independent, reason = _holdout(relation, registered.get("target_timing_used_to_fit"))
    model_path = str(registered.get("model_path") or "")
    parallel = _registered_parallel(model_path, registered.get("model_sha256"))
    if isinstance(parallel, dict) and parallel.get("status"):
        return _diagnostic(row, parallel["status"], parallel["diagnostics"], parallel["needed"])
    provenance = {
        "evaluation_relation": relation,
        "holdout_independent": independent,
        "holdout_block_reason": reason,
        "alias_of": [{"suite": "registered", "capture_id": registered.get("case_id"), "source_path": registered.get("source_path")}],
        "original_capture_id": capture_id,
        "original_case_path": model_path or None,
        "expected_case_sha256": registered.get("model_sha256"),
        "generator_revision": None,
        "receipts": [],
    }
    extraction = registered.get("extraction_path")
    projections = []
    if isinstance(extraction, str) and extraction and not Path(extraction).name.startswith("pred_"):
        projections.append(sources.project_receipt(Path(extraction)))
    return _finish(row, phase=registered.get("phase"), source_path=str(path), projections=projections,
                   provenance=provenance, parallel=parallel if isinstance(parallel, dict) else {}, family=None, hw=None,
                   template_name=Path(model_path).name if model_path else None,
                   registry_layers=None, registry_experts=None, registry_top_k=None, cross_tp=False)


def _registered_parallel(model_path: str, expected_sha: Any) -> dict[str, Any]:
    if not model_path:
        return {}
    path = Path(model_path)
    if not path.is_file():
        path = sources.roots()["cases"] / Path(model_path).name
    if not path.is_file():
        return {}
    if isinstance(expected_sha, str) and sources.sha256(path) != expected_sha:
        return {"status": "conflict", "diagnostics": [f"original_case_sha256_mismatch:{sources.sha256(path)}!={expected_sha}"],
                "needed": ["case file matching registry sha256"]}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "insufficient_evidence", "diagnostics": ["original_case_unreadable"], "needed": ["structural case json"]}
    runtime = document.get("runtime") if isinstance(document, dict) and isinstance(document.get("runtime"), Mapping) else {}
    return {axis: sources.as_int(runtime.get(axis)) for axis in ("tp", "dp", "ep")}


def _resolve_record(row: Mapping[str, Any], record: Mapping[str, Any], alias_of: tuple | list) -> dict[str, Any]:
    source = str(record.get("source_path") or "")
    receipts = []
    for key in sources.rel_keys(source):
        receipts.extend(sources.receipt_index().get(key, ()))
    receipts = list(dict.fromkeys(receipts))
    projections = [sources.project_receipt(Path(item)) for item in receipts]
    relation = record.get("relation")
    independent = record.get("independent")
    if independent is None:
        independent = False
        reason = "registry_does_not_establish_independent_heldout"
    else:
        reason = None if independent else f"registry_relation:{relation}"
    provenance = {
        "generator_revision": record.get("generator"),
        "template_name": record.get("template"),
        "evaluation_relation": relation,
        "holdout_independent": bool(independent),
        "holdout_block_reason": reason,
        "alias_of": list(alias_of),
        "original_capture_id": str(row.get("capture_id") or record.get("capture_id")),
        "cross_tp_transfer": bool(record.get("cross_tp")),
        "receipts": [{"path": item.get("path"), "cache_version": item.get("cache_version"), "parser_identity": item.get("parser_identity")}
                     for item in projections if item.get("status") == "projected"],
    }
    return _finish(
        row, phase=record.get("phase"), source_path=source, projections=projections, provenance=provenance,
        parallel=dict(record.get("parallel") or {}), family=record.get("family"), hw=record.get("hw"),
        template_name=record.get("template"), registry_layers=record.get("layers"),
        registry_experts=record.get("experts"), registry_top_k=record.get("top_k"), cross_tp=bool(record.get("cross_tp")),
    )


def _finish(row, *, phase, source_path, projections, provenance, parallel, family, hw,
            template_name, registry_layers, registry_experts, registry_top_k, cross_tp) -> dict[str, Any]:
    usable = [item for item in projections if item.get("status") == "projected"]
    diagnostics: list[str] = []
    if not usable:
        return _diagnostic(row, "insufficient_evidence", ["extraction_receipt_missing"], ["native extraction receipt"],
                           phase=phase, provenance=provenance, source={"path": source_path, "sha256": None, "size_bytes": None, "sha256_verified": False})
    signatures = {sources.signature(item) for item in usable}
    if len(signatures) != 1:
        return _diagnostic(row, "conflict", ["receipt_structural_signature_disagrees"], ["one structural signature across parser versions"],
                           phase=phase, provenance=provenance, source={"path": source_path, "sha256": None, "size_bytes": None, "sha256_verified": False})
    chosen = usable[0]
    declared_sha = chosen.get("source_sha256")
    shas = {item.get("source_sha256") for item in usable}
    if len(shas) != 1 or not isinstance(declared_sha, str):
        return _diagnostic(row, "conflict", ["receipt_source_sha_disagrees"], ["one source sha256"], phase=phase, provenance=provenance)
    source = Path(str(chosen.get("source_path") or source_path))
    if not source.is_file():
        return _diagnostic(row, "insufficient_evidence", ["source_file_missing"], [str(source)], phase=phase, provenance=provenance,
                           source={"path": str(source), "sha256": declared_sha, "size_bytes": None, "sha256_verified": False})
    if chosen.get("source_size") is not None and source.stat().st_size != chosen["source_size"]:
        return _diagnostic(row, "insufficient_evidence", ["source_size_mismatch"], ["source bytes matching receipt size"],
                           phase=phase, provenance=provenance, source={"path": str(source), "sha256": declared_sha, "size_bytes": source.stat().st_size, "sha256_verified": False})
    actual_sha = sources.sha256(source)
    verified = actual_sha == declared_sha
    source_record = {"path": str(source), "sha256": actual_sha, "size_bytes": source.stat().st_size, "sha256_verified": verified,
                     "rank_ids": sorted({item.get("rank_id") or "" for item in chosen["populations"]}),
                     "device_ids": sorted({item.get("device_id") or "" for item in chosen["populations"]})}
    if not verified:
        return _diagnostic(row, "insufficient_evidence", [f"source_sha256_mismatch:{actual_sha}!={declared_sha}"],
                           ["source bytes matching receipt sha256"], phase=phase, provenance=provenance, source=source_record)
    row_phase = row.get("phase")
    receipt_phase = chosen.get("phase") or phase
    if isinstance(row_phase, str) and row_phase and isinstance(receipt_phase, str) and row_phase.lower() != receipt_phase.lower():
        return _diagnostic(row, "conflict", [f"phase_conflict:row={row_phase}:receipt={receipt_phase}"], ["one phase"],
                           phase=receipt_phase, provenance=provenance, source=source_record)
    tokens = _path_tokens(str(source))
    run_meta = _source_run_meta(source)
    if isinstance(run_meta, Mapping) and isinstance(run_meta.get("parallelism"), Mapping):
        run_parallel = run_meta["parallelism"]
        for axis in ("tp", "dp", "ep"):
            if sources.as_int(parallel.get(axis)) is None and sources.as_int(run_parallel.get(axis)) is not None:
                parallel[axis] = sources.as_int(run_parallel.get(axis))
    agreed, parallel_notes = _agree_parallel(parallel, tokens, chosen.get("model_declaration") or {})
    diagnostics.extend(parallel_notes)
    if any(note.startswith("conflict:") for note in parallel_notes):
        return _diagnostic(row, "conflict", diagnostics, ["tp/dp/ep agreement of path, registry, and receipt"],
                           phase=receipt_phase, provenance=provenance, source=source_record)
    case_path, case_doc, case_notes = _load_original_case(template_name, family, hw)
    diagnostics.extend(case_notes)
    expected_case_sha = provenance.get("expected_case_sha256") if isinstance(provenance, Mapping) else None
    if isinstance(expected_case_sha, str) and case_path is not None and sources.sha256(case_path) != expected_case_sha:
        return _diagnostic(row, "conflict", [f"original_case_sha256_mismatch:{sources.sha256(case_path)}!={expected_case_sha}"],
                           ["case file matching registry sha256"], phase=receipt_phase, provenance=provenance, source=source_record)
    model, model_notes, missing = _reconcile_model(
        case_doc, chosen.get("model_declaration") or {}, family, tokens, registry_layers, registry_experts, registry_top_k,
        source_path=source, parallel=agreed,
    )
    diagnostics.extend(model_notes)
    populations = [dict(item) for item in chosen["populations"]]
    hardware, hardware_notes = _hardware(case_doc, hw, row.get("hardware_tier"), agreed)
    diagnostics.extend(hardware_notes)
    if model is None or hardware is None or any(agreed.get(axis) is None for axis in ("tp", "dp", "ep")):
        _note_missing_context(populations, missing, diagnostics, interval=False)
        needed = [name for name, value in (("model", model), ("machine.sku", hardware), ("tp", agreed.get("tp")), ("dp", agreed.get("dp")), ("ep", agreed.get("ep"))) if value is None]
        status = "conflict" if any(str(item).startswith("conflict:") for item in diagnostics) else "insufficient_evidence"
        return _diagnostic(row, status, diagnostics, needed, phase=receipt_phase, provenance=provenance,
                           source=source_record, geometry={"parallel": agreed, "populations": populations, "missing": missing or needed})
    producer_doc = producer.producer_declaration(source, usable, phase=receipt_phase)
    diagnostics.extend(producer_doc.get("notes") or [])
    conflicts = list(producer_doc.get("conflicts") or [])
    conflicts.extend(_launch_axis_conflicts(producer_doc.get("launch"), agreed))
    if conflicts:
        diagnostics.extend(conflicts)
        return _diagnostic(row, "conflict", diagnostics, ["agreeing producer prompt, output, and launch axes"],
                           phase=receipt_phase, provenance=provenance, source=source_record,
                           geometry={"parallel": agreed, "populations": populations, "missing": missing})
    stripped: list[str] = []
    qwen30 = str(family or "") == "qwen3-30b-a3b" or str(family or "").startswith("synth-qwen3-30b")
    if qwen30 and isinstance(case_doc, Mapping) and str((case_doc.get("model") or {}).get("quantization") or "") not in {"", "none"}:
        diagnostics.append("unrelated_template_runtime_not_applied")
    runtime, scheduler, stale_scheduler = _runtime(None if qwen30 else case_doc, agreed, cross_tp or bool(provenance.get("cross_tp_transfer")), stripped)
    _bind_stripped_archive_gdn_store(runtime, stripped, hardware, diagnostics)
    replaced: list[dict[str, Any]] = []
    _apply_launch(runtime, producer_doc.get("launch"), replaced)
    bind_witnessed_expert_caller(runtime, model, source, replaced, diagnostics)
    frames = [dict(item) for item in (producer_doc.get("frames") or [])]
    apply_witnessed_route(runtime, model, source, frames, replaced, diagnostics)
    hardware, hw_candidates = _conditional_hardware(hardware, producer_doc.get("npu"))
    applied = [item for item in hw_candidates or [] if isinstance(item, dict) and item.get("applied") and item.get("catalog_sku")]
    if isinstance(model, dict) and isinstance(model.get("metadata"), dict) and isinstance(hardware, dict):
        if model["metadata"].get("architectural_basis") == "catalog_base_then_declared_downsize":
            sku = hardware.get("sku")
            if isinstance(sku, str) and sku:
                model["metadata"]["source_sku"] = sku
    if len(applied) == 1 and isinstance(hardware, dict) and hardware.get("sku") == applied[0]["catalog_sku"]:
        diagnostics.append("hardware_sku_declared_not_serial_verified")
    elif hw_candidates:
        diagnostics.append("hardware_sku_conditional_not_exact")
    pinned = _pin_prefill_context(populations, producer_doc, receipt_phase)
    frame_exact = bool(frames) and all(
        isinstance(item.get("context_tokens"), int) and not isinstance(item.get("context_tokens"), bool)
        for item in frames
    )
    per_step = pinned or frame_exact
    if not per_step and isinstance(run_meta, Mapping) and len(populations) == 1:
        meta_work = run_meta.get("workload") if isinstance(run_meta.get("workload"), Mapping) else {}
        if str(meta_work.get("mode") or "").lower() == "prefill":
            prefix = sources.as_int(meta_work.get("prefix_len"))
            if prefix is not None and prefix >= 0 and populations[0].get("context_tokens") is None:
                populations[0]["context_tokens"] = prefix
                populations[0]["context_basis"] = "run_meta.workload.prefix_len"
                per_step = True
                diagnostics.append("run_meta_prefill_context_applied")
    context = _context_record(populations, producer_doc, receipt_phase, per_step, frames)
    interval = isinstance(context.get("lower_bound_tokens"), int) and isinstance(context.get("upper_bound_tokens"), int)
    if context.get("per_step_context_observed") is not True:
        _note_missing_context(populations, missing, diagnostics, interval=False)
    workload = _declared_workload(producer_doc)
    provenance = dict(provenance)
    provenance.update({
        "original_case_path": str(case_path) if case_path else None,
        "original_case_sha256": sources.sha256(case_path) if case_path and case_path.is_file() else None,
        "template_parallel": _template_parallel(case_doc),
        "template_parallel_conflict": _template_conflicts(_template_parallel(case_doc), agreed),
        "physical_source_id": actual_sha,
        "stripped": stripped,
        "stale_scheduler_not_applied": stale_scheduler,
        "launch_replaced_template_fields": replaced,
        "producer_sources": producer_doc.get("sources") or [],
        "row_model_case_ignored": row.get("model_case") if isinstance(row.get("model_case"), str) else None,
    })
    local = sorted({item.get("sequences_per_replica") for item in populations})
    batch = dict(producer_doc.get("batch") or {})
    batch["local_sequences_per_replica"] = local[0] if len(local) == 1 else local
    case = {"machine": hardware, "model": model, "runtime": runtime, "workload": workload}
    ready = workload is not None
    predictable = bool(ready and (per_step or interval))
    geometry = {
        "parallel": agreed, "model": _public_model(model), "populations": populations,
        "scheduler": scheduler, "missing": sorted(set(missing)), "context": context, "batch": batch,
        "prefix": producer_doc.get("prefix"), "launch": producer_doc.get("launch"),
        "profile_window": producer_doc.get("profile_window"), "captured_window": producer_doc.get("captured_window"),
        "window_timebase": producer_doc.get("window_timebase"), "window_origin": producer_doc.get("window_origin"),
        "window_valid": producer_doc.get("window_valid"), "inflight_at_start": producer_doc.get("inflight_at_start"),
        "inflight_at_stop": producer_doc.get("inflight_at_stop"),
        "client_lane_is_not_physical_rank": producer_doc.get("client_lane_is_not_physical_rank"),
        "request_context_bounds": producer_doc.get("request_context_bounds"), "requests": producer_doc.get("requests"),
        "attention_shapes": producer_doc.get("attention_shapes"), "frames": frames, "hardware_candidates": hw_candidates,
        "receipt_windows": producer_doc.get("receipt_windows"), "executed_graph": producer_doc.get("executed_graph"),
        "window_fields": producer_doc.get("window_fields"), "device_inventory": producer_doc.get("npu"), "conditional_scenarios": sources.conditional_scenarios(case, hw_candidates),
        "service_request_separate_from_captured_forwards": bool(ready and (not per_step or len(frames) > 1 or context.get("mixed_context_observed"))),
    }
    needed = []
    if not ready:
        needed = ["workload.context_tokens"] if "context_tokens" in geometry["missing"] else ["declared producer workload"]
    elif "context_tokens" in geometry["missing"]:
        needed = ["context_tokens"]
    return {
        "status": "resolved", "capture_id": str(row.get("capture_id") or provenance.get("original_capture_id")),
        "suite": _suite(row), "phase": receipt_phase, "source": source_record, "provenance": provenance,
        "geometry": geometry, "case": case, "case_ready_for_parse": ready, "predictable": predictable,
        "predictable_scope": "captured_forward" if per_step and ready else ("declared_service_request" if predictable else None),
        "diagnostics": diagnostics,
        "needed": needed,
    }


def _note_missing_context(populations, missing, diagnostics, *, interval: bool) -> None:
    if interval or (populations and all(isinstance(item.get("context_tokens"), int) for item in populations)):
        return
    if "context_tokens" not in missing:
        missing.append("context_tokens")
    if "context_tokens_not_observed" not in diagnostics:
        diagnostics.append("context_tokens_not_observed")


def _launch_axis_conflicts(launch: Mapping[str, Any] | None, agreed: Mapping[str, Any]) -> list[str]:
    if not isinstance(launch, Mapping):
        return []
    notes = []
    for axis in ("tp", "dp", "ep"):
        value = launch.get(axis)
        if isinstance(value, int) and isinstance(agreed.get(axis), int) and value != agreed[axis]:
            notes.append(f"conflict:{axis}:launch={value},agreed={agreed[axis]}")
    return notes


def _apply_launch(runtime: dict, launch: Mapping[str, Any] | None, replaced: list[dict[str, Any]]) -> None:
    if not isinstance(launch, Mapping):
        return
    fields = {
        "max_model_len": launch.get("max_model_len"), "max_num_seqs": launch.get("max_num_seqs"),
        "max_num_batched_tokens": launch.get("max_num_batched_tokens"), "kv_block_size": launch.get("block_size"),
        "graph_capture_mode": launch.get("graph_capture_mode"), "gpu_memory_utilization": launch.get("gpu_memory_utilization"),
        "enable_chunked_prefill": launch.get("enable_chunked_prefill"),
    }
    for key, value in fields.items():
        if value is None:
            continue
        previous = runtime.get(key)
        if previous is not None and previous != value:
            replaced.append({key: previous})
        runtime[key] = value
    sizes = launch.get("graph_capture_sizes")
    if isinstance(sizes, (list, tuple)):
        keys = sorted({int(item) for item in sizes
                       if isinstance(item, (int, float)) and int(item) > 0})
        if keys:
            previous = runtime.get("graph_capture_keys")
            if previous is not None and list(previous) != keys:
                replaced.append({"graph_capture_keys": previous})
            runtime["graph_capture_keys"] = keys
    if launch.get("shared_expert_dp") is True:
        metadata = dict(runtime.get("metadata") or {})
        if metadata.get("enable_shared_expert_dp") is not True:
            metadata["enable_shared_expert_dp"] = True
            runtime["metadata"] = metadata


def _source_run_meta(source: Path) -> dict[str, Any] | None:
    """Read the retained run_meta.json beside the profiled kernel source."""
    path = Path(source).parent / "run_meta.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _declared_workload(producer_doc: Mapping[str, Any]) -> dict | None:
    if producer_doc.get("conflicts") or producer_doc.get("token_exact") is not True:
        return None
    cached = (producer_doc.get("prefix") or {}).get("observed_cached_tokens")
    requests = [item for item in (producer_doc.get("requests") or []) if item.get("ok") is True]
    if requests and all(isinstance(item.get("prompt_tokens"), int) and isinstance(item.get("output_tokens"), int) and item["prompt_tokens"] >= 1 and item["output_tokens"] >= 1 for item in requests):
        payload = []
        for index, item in enumerate(requests):
            row = {"id": f"r{item.get('idx') if item.get('idx') is not None else index}", "prompt_tokens": item["prompt_tokens"], "output_tokens": item["output_tokens"]}
            if isinstance(cached, int):
                row["prefix_tokens"] = cached
            payload.append(row)
        return {"requests": payload, "synthetic": False}
    prompt, output, count = producer_doc.get("prompt_tokens"), producer_doc.get("output_tokens"), producer_doc.get("concurrency")
    if all(isinstance(value, int) and value >= 1 for value in (prompt, output, count)):
        workload = {"num_requests": count, "prompt_tokens": prompt, "output_tokens": output, "synthetic": False}
        if isinstance(cached, int):
            workload["prefix_tokens"] = cached
        return workload
    return None


def _pin_prefill_context(populations: list[dict], producer_doc: Mapping[str, Any], phase: Any) -> bool:
    if str(phase or "").lower() != "prefill" or len(populations) != 1:
        return False
    item = populations[0]
    if isinstance(item.get("context_tokens"), int):
        return True
    shapes = producer_doc.get("attention_shapes") or {}
    cached = (producer_doc.get("prefix") or {}).get("observed_cached_tokens")
    uniform, prompt, query = shapes.get("uniform_query_rows"), producer_doc.get("prompt_tokens"), item.get("query_rows")
    if not all(isinstance(value, int) for value in (uniform, prompt, cached, query)):
        return False
    if uniform != prompt or query != prompt:
        return False
    item["context_tokens"] = cached
    item["context_basis"] = "producer_initial_cache_and_uniform_attention_query"
    return True


def _frame_context_record(frames: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    records = []
    for frame in frames or ():
        if not isinstance(frame, Mapping):
            continue
        raw = frame.get("context_tokens")
        observed = isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0
        records.append({
            "forward_id": frame.get("forward_id"),
            "phase": frame.get("phase"),
            "device_id": frame.get("device_id"),
            "rank_id": frame.get("rank_id"),
            "query_rows": frame.get("query_rows"),
            "context_tokens": raw if observed else None,
            "observed": observed,
            "basis": frame.get("basis"),
        })
    return records


def _context_record(populations, producer_doc, phase, per_step: bool, frames=None) -> dict[str, Any]:
    """Separate actual per-step K from an identifiable frame or request envelope.

    A frame identity is not a context value. Mixed frames keep their observed
    and missing context entries side by side.
    """
    evidence = producer_doc.get("context_evidence") or {}
    frame_contexts = _frame_context_record(frames)
    observed = [item for item in frame_contexts if item["observed"]]
    record = {
        "per_step_context_observed": False,
        "basis": evidence.get("basis"),
        "lower_bound_tokens": evidence.get("lower_bound_tokens"),
        "upper_bound_tokens": evidence.get("upper_bound_tokens"),
        "representative_tokens": evidence.get("representative_tokens"),
        "client_token_exact": evidence.get("client_token_exact"),
        "frame_contexts": frame_contexts or None,
        "frames_total": len(frame_contexts),
        "frames_with_observed_context": len(observed),
        "frames_with_missing_context": len(frame_contexts) - len(observed),
        "per_frame_context_complete": bool(frame_contexts) and len(observed) == len(frame_contexts),
        "mixed_context_observed": bool(observed) and len(observed) < len(frame_contexts),
    }
    if evidence.get("limitation"):
        record["limitation"] = evidence["limitation"]
    if frame_contexts and len(observed) == len(frame_contexts):
        values = [item["context_tokens"] for item in observed]
        record.update(lower_bound_tokens=min(values), upper_bound_tokens=max(values),
                      representative_tokens=values[0], basis=observed[0].get("basis"),
                      per_step_context_observed=True, evidence_kind="per_frame_context")
        return record
    if observed:
        values = [item["context_tokens"] for item in observed]
        record.update(lower_bound_tokens=min(values), upper_bound_tokens=max(values),
                      representative_tokens=values[0], basis="partial_per_frame_context",
                      evidence_kind="partial_per_frame_context")
    if per_step and populations and isinstance(populations[0].get("context_tokens"), int):
        value = populations[0]["context_tokens"]
        record.update(lower_bound_tokens=value, upper_bound_tokens=value, representative_tokens=value,
                      basis=populations[0].get("context_basis"),
                      per_step_context_observed=True, evidence_kind="bound_population_context")
        return record
    if record.get("lower_bound_tokens") is None and str(phase or "").lower() == "decode":
        prompt, output = producer_doc.get("prompt_tokens"), producer_doc.get("output_tokens")
        if isinstance(prompt, int) and isinstance(output, int):
            record.update(lower_bound_tokens=prompt, upper_bound_tokens=prompt + output,
                          representative_tokens=prompt,
                          basis="decode_request_token_span_not_a_step_context",
                          evidence_kind="request_envelope", request_envelope=True,
                          per_step_context_observed=False)
    elif not record["per_step_context_observed"]:
        envelope = bool(record.get("lower_bound_tokens") is not None) and record.get("evidence_kind") != "partial_per_frame_context"
        record["request_envelope"] = envelope
        if record.get("evidence_kind") is None and envelope:
            record["evidence_kind"] = "request_envelope"
    return record


def _agree_parallel(registry: Mapping[str, Any], tokens: Mapping[str, int], declaration: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    notes: list[str] = []
    agreed: dict[str, Any] = {"basis": "path_registry_receipt"}
    for axis in ("tp", "dp", "ep"):
        path_value = tokens.get(axis)
        if isinstance(path_value, str):
            notes.append(path_value if path_value.startswith("conflict:") else f"conflict:{axis}:{path_value}")
            agreed[axis] = None
            continue
        values = {}
        if registry.get(axis) is not None:
            values["registry"] = registry.get(axis)
        if isinstance(path_value, int):
            values["path"] = path_value
        if axis == "tp" and sources.as_int(declaration.get("tp")) is not None:
            values["receipt"] = sources.as_int(declaration.get("tp"))
        distinct = set(values.values())
        if len(distinct) > 1:
            notes.append("conflict:" + axis + ":" + ",".join(f"{key}={value}" for key, value in values.items()))
            agreed[axis] = None
        elif len(distinct) == 1:
            agreed[axis] = next(iter(distinct))
            agreed[f"{axis}_from"] = sorted(values)
        elif axis == "dp":
            agreed[axis] = 1
            agreed["dp_basis"] = "absent_from_path_and_registry_default_1"
        else:
            agreed[axis] = None
    agreed["pp"] = 1
    agreed["pp_basis"] = "default_pp_absent"
    return agreed, notes


def _template_parallel(case_doc: Mapping[str, Any] | None) -> dict[str, int | None] | None:
    if not isinstance(case_doc, Mapping):
        return None
    runtime = case_doc.get("runtime") if isinstance(case_doc.get("runtime"), Mapping) else {}
    return {axis: sources.as_int(runtime.get(axis)) for axis in ("tp", "dp", "ep")}


def _template_conflicts(template: Mapping[str, Any] | None, agreed: Mapping[str, Any]) -> bool:
    if not template:
        return False
    return any(template.get(axis) is not None and agreed.get(axis) is not None and template.get(axis) != agreed.get(axis)
               for axis in ("tp", "dp", "ep"))


def _load_original_case(template_name: Any, family: Any, hw: Any) -> tuple[Path | None, dict | None, list[str]]:
    name = str(template_name or "")
    search = []
    if name.endswith(".json"):
        search.append(name)
    elif name:
        search.append(name + ".json")
    base = _A5_BASE.get(str(family or ""))
    if base:
        search.append(base)
    roots = [sources.roots()["cases"], sources.roots()["archive"] / "wave5-eval" / "a2" / "templates",
             sources.roots()["archive"] / "wave5-eval" / "a3" / "templates", sources.roots()["archive"] / "wave5-eval" / str(hw or "") / "templates"]
    for candidate in search:
        for root in roots:
            path = root / candidate
            if path.is_file():
                document = json.loads(path.read_text(encoding="utf-8"))
                return path, document if isinstance(document, dict) else None, []
    if name or base:
        return None, None, [f"original_case_missing:{name or base}"]
    return None, None, ["original_case_path_absent"]


def _conditional_hardware(machine: dict | None, npu: Mapping[str, Any] | None) -> tuple[dict | None, list | None]:
    return sources.declared_hardware(machine, npu)


def _hardware(case_doc, hw, tier, agreed) -> tuple[dict | None, list[str]]:
    if not isinstance(case_doc, Mapping) or not isinstance(case_doc.get("machine"), Mapping):
        return None, ["machine_profile_missing"]
    machine = json.loads(json.dumps(case_doc["machine"]))
    device = machine.get("device")
    if isinstance(device, dict):
        for key in ("rates", "resource_units", "work_units"):
            device.pop(key, None)
        if not device:
            machine.pop("device", None)
    sku = str(machine.get("sku") or "")
    family = _sku_family(sku)
    wanted = str(tier or "").upper() or {"a2": "A2", "a3": "A3", "a5": "A5"}.get(str(hw or "").lower())
    if family and wanted and family != wanted:
        return None, [f"hardware_tier_{wanted}_disagrees_with_case_sku_{sku}"]
    world = (agreed.get("tp") or 0) * (agreed.get("dp") or 0)
    if world >= 1:
        machine["num_devices"] = world
        ranks = sources.as_int(machine.get("ranks_per_node")) or world
        machine["ranks_per_node"] = min(ranks, world)
        machine["deployment_basis"] = "declared_tp_times_dp"
    return machine, []


def _bind_stripped_archive_gdn_store(runtime: dict, stripped: list[str],
                                     hardware: Mapping[str, Any], diagnostics: list[str]) -> None:
    """Map a sanitized queue declaration to the selected SKU's physical contract.

    Only a surviving scalar-store resource/BF16 payload whose time fields were
    actively stripped is eligible. Complete source queues and DMA opt-outs are
    left untouched. Hardware support and parameters come from the SKU, never
    from the removed source numbers.
    """
    kernels = runtime.get("kernels") if isinstance(runtime.get("kernels"), dict) else None
    lowerings = kernels.get("lowerings") if isinstance(kernels, dict) and isinstance(kernels.get("lowerings"), dict) else None
    binding = lowerings.get("gdn_decode") if isinstance(lowerings, dict) else None
    options = binding.get("options") if isinstance(binding, Mapping) and isinstance(binding.get("options"), dict) else None
    store = options.get("gating_beta_store") if isinstance(options, dict) else None
    if not isinstance(store, Mapping) or store.get("from_hardware") is True:
        return
    if store.get("bytes_per_element") != 2 or store.get("resource") != "scalar_store_issue":
        return
    queue = store.get("queue")
    if not isinstance(queue, Mapping):
        return
    if not isinstance(queue.get("outstanding"), int) or not isinstance(queue.get("granule_bytes"), int):
        return
    removed_time = any(
        "gating_beta_store" in item and (item.endswith(".response_ms") or item.endswith(".row_control_ms"))
        for item in stripped
    )
    if not removed_time:
        return
    machine = hardware if isinstance(hardware, Mapping) else {}
    sku = machine.get("sku")
    if not isinstance(sku, str) or not sku:
        return
    try:
        from mindie_sim.backends import materialize
        device = materialize({"backend": "ascend", "sku": sku}).get("device") or {}
    except Exception:
        return
    queues = device.get("store_queues") if isinstance(device.get("store_queues"), Mapping) else {}
    hw_queue = queues.get("scalar_store_issue") if isinstance(queues.get("scalar_store_issue"), Mapping) else {}
    rates = device.get("rates") if isinstance(device.get("rates"), Mapping) else {}
    if hw_queue.get("element_bytes") != 2 or "scalar_store_issue" not in rates:
        return
    options["gating_beta_store"] = {
        "bytes_per_element": 2, "resource": "scalar_store_issue", "from_hardware": True,
    }
    diagnostics.append("gdn_stripped_queue_bound_to_selected_hardware")


def _runtime(case_doc, agreed, cross_tp, stripped: list[str]) -> tuple[dict, dict | None, dict | None]:
    runtime = {}
    if isinstance(case_doc, Mapping) and isinstance(case_doc.get("runtime"), Mapping):
        runtime = json.loads(json.dumps(case_doc["runtime"]))
    _strip(runtime, stripped, "runtime")
    runtime["tp"], runtime["dp"], runtime["ep"] = agreed.get("tp"), agreed.get("dp"), agreed.get("ep")
    runtime["pp"] = agreed.get("pp")
    template = _template_parallel(case_doc) or {}
    conflict = cross_tp or _template_conflicts(template, agreed)
    scheduler = None
    stale = None
    if conflict:
        stale = {key: runtime.pop(key) for key in _SCHEDULER_KEYS if key in runtime and key != "pp"}
        stripped.append("runtime.scheduler_fields_after_parallel_conflict")
    else:
        scheduler = {key: runtime.get(key) for key in _SCHEDULER_KEYS if key in runtime}
        scheduler["basis"] = "original_case_runtime_parallel_matches"
    metadata = runtime.get("metadata") if isinstance(runtime.get("metadata"), dict) else {}
    for key in ("calibration_origin", "evaluation_relation", "target_timing_used_to_fit"):
        if key in metadata:
            metadata.pop(key)
            stripped.append(f"runtime.metadata.{key}")
    if metadata:
        runtime["metadata"] = metadata
    elif "metadata" in runtime:
        runtime.pop("metadata")
    return runtime, scheduler, stale


def _strip(value: Any, stripped: list[str], prefix: str) -> None:
    if isinstance(value, dict):
        for key in list(value):
            if key in _TIMING_KEYS or key.endswith("_ms") or key.endswith("_us"):
                value.pop(key)
                stripped.append(f"{prefix}.{key}")
            else:
                _strip(value[key], stripped, f"{prefix}.{key}")
    elif isinstance(value, list):
        for item in value:
            _strip(item, stripped, prefix)


def _public_model(model: Mapping[str, Any]) -> dict[str, Any]:
    identity = _model_identity(model)
    identity["name"] = model.get("name") or identity.get("name")
    return {key: value for key, value in identity.items() if value is not None}


def archive_inventory_summary(rows) -> dict[str, Any]:
    counts = {"rows": 0, "outside": 0, "resolved": 0, "insufficient_evidence": 0, "conflict": 0, "predictable": 0, "context_missing": 0, "holdout_independent": 0, "aliases": 0}
    by_suite: dict[str, dict[str, int]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if not archive_case_domain(row):
            counts["outside"] += 1
            continue
        counts["rows"] += 1
        result = resolve_archive_case(row) or {}
        status = result.get("status") or "none"
        counts[status] = counts.get(status, 0) + 1
        bucket = by_suite.setdefault(_suite(row), {})
        bucket[status] = bucket.get(status, 0) + 1
        counts["predictable"] += bool(result.get("predictable"))
        missing = (result.get("geometry") or {}).get("missing") or []
        counts["context_missing"] += "context_tokens" in missing
        provenance = result.get("provenance") or {}
        counts["holdout_independent"] += bool(provenance.get("holdout_independent")); counts["aliases"] += bool(provenance.get("alias_of"))
    counts["by_suite"] = by_suite
    return counts
