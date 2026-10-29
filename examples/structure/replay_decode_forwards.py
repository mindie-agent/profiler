"""Replay local Decode forward evidence without promoting step envelopes.

[Role] Join source-pinned profiler boundaries and the public Sim body API.
[Invariants] Automatic topology alignment remains labelled as an estimate,
  separate from explicit Host/module boundaries. Scenario targets are not
  measured capture facts; graph envelopes remain a separate diagnostic.
[Timeouts & Locks] Serial cases; bounded source scans and declaration reads.
[Side-Effect Policy] Read local captures and write requested reports; no devices.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

from mindie_profiler.events import ProfilerError, SourceRef, Window
from mindie_profiler.forward_spans import measure_forward_spans
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.sources_csv import probe_csv
from mindie_profiler.sources_db import DbSource, probe_db, sha256_file

from body_forward_comparison import GEOMETRY_FIELDS, _stats, compare_body_forward, compare_layers, compare_pooled_layers


class PredictionCache(dict):
    def __init__(self, directory=None):
        super().__init__()
        self.directory = Path(directory) if directory else None
        if self.directory:
            self.directory.mkdir(parents=True, exist_ok=True)


def _read(path):
    if path.stat().st_size > 50 * 1024 ** 2:
        raise ValueError(f"forward_declaration_too_large:{path}")
    return json.loads(path.read_text())


def _path(base, value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _empty_comparison(reasons):
    return {
        "status": "unresolved", "reasons": reasons, "observed_forward_count": 0,
        "observed_ms": {"count": 0, "mean": None, "p50": None, "p90": None,
                        "min": None, "max": None},
        "predicted_ms": None, "relative_error": None, "per_forward_diff_ms": None,
        "passed": None,
    }


def _source(path, declaration, boundaries, *, max_events, timeout_s):
    rank_id, rank_index = declaration.get("rank_id", ""), declaration.get("rank_index")
    digest = sha256_file(path)
    if declaration.get("sha256") and digest != declaration["sha256"]:
        raise ValueError("forward_capture_source_hash_mismatch")
    kind = declaration.get("kind", "db" if path.suffix == ".db" else "csv")
    if kind == "db":
        schema = probe_db(path, timeout_s=timeout_s)
        scopes = [scope for row in (boundaries or {}).get("forwards", []) for scope in row.get("scopes", [])]
        if not scopes:
            interval = DbSource(schema).capture_range_ns(timeout_s=timeout_s) if boundaries is None else None
            rows, stats = DbSource(schema).iter_window(
                Window(*interval), max_rows=max_events, timeout_s=timeout_s) if interval else ([], None)
            events = (replace(event, rank_id=rank_id, rank_index=rank_index) for event in rows)
        else:
            window = Window(min(s["start_ns"] for s in scopes), max(s["end_ns"] for s in scopes))
            rows, stats = DbSource(schema).iter_window(window, max_rows=max_events, timeout_s=timeout_s)
            if stats.bad_rows:
                raise ValueError("forward_source_has_invalid_event_rows")
            events = (replace(event, rank_id=rank_id, rank_index=rank_index) for event in rows)
    elif kind == "csv":
        schema = probe_csv(path)
        events = (row.event for row in kernel_rows(
            path, rank_id=rank_id, rank_index=rank_index,
            max_rows=max_events, timeout_s=timeout_s))
    else:
        raise ValueError(f"unsupported_forward_source_kind:{kind}")
    ref = SourceRef(
        rank_id=rank_id, rank_index=rank_index, kind=kind, path=str(path),
        basename=path.name, sha256=digest, size_bytes=path.stat().st_size,
        schema_version=schema.schema_version, schema_variant=schema.schema_variant,
        mtime_ns=path.stat().st_mtime_ns,
    )
    return events, ref


def _sim_identity():
    import mindie_sim

    package = Path(mindie_sim.__file__).resolve().parent
    files = {str(path.relative_to(package)): sha256_file(path)
             for path in sorted(package.rglob("*")) if path.suffix in {".py", ".json"}}
    return {"package_path": str(package), "version": mindie_sim.__version__,
            "package_sha256": sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
            "file_count": len(files), "algorithm": "sha256(sorted relative-path to file-sha256 JSON)"}


def _model_config(case):
    """Reuse the Sim front end to declare topology; these are not observed rows."""
    from mindie_sim import target_graphs
    from mindie_sim.prediction.structure import parse_case

    parsed = parse_case(case)
    config = parsed.model.to_dict()
    config["tp"] = parsed.runtime.parallel.tp
    proposals = int(dict(parsed.runtime.metadata).get("draft_proposal_tokens", 0))
    config["decode_max_tokens"] = max(32, parsed.runtime.max_num_seqs * (proposals + 1))
    graphs = target_graphs(parsed, phase="decode", tokens=1, context=0, sequences=1, scope="body")
    topology = []
    for op in next(iter(graphs.values())):
        if op.layer >= 0:
            topology.append({"layer_id": op.layer, "family": op.family, "recipe": op.recipe,
                             "local_shape": list(op.local_shape), "source_boundary": op.source_boundary})
    config["layer_signatures"] = topology
    config["layer_signature_geometry"] = {"tokens": 1, "context": 0, "basis": "declared_topology_only"}
    return config


def _declared_runtime(case):
    from mindie_sim.prediction.structure import parse_case

    runtime = parse_case(case).runtime
    placement = runtime.parallel
    metadata = dict(runtime.metadata)
    return {"tp": placement.tp, "dp": placement.dp, "ep": placement.ep, "pp": placement.pp,
            "graph_mode": runtime.graph_mode, "graph_capture_mode": runtime.graph_capture_mode,
            "captured_execution_mode": metadata.get("captured_execution_mode"),
            "captured_mode_basis": "source_bound_case_metadata"}


def _predict_bounded(case_path, geometry, cache, *, timeout_s):
    before = _sim_identity()
    key = (sha256_file(case_path), geometry["phase"], geometry["tokens_per_sequence"],
           geometry["context_tokens"], geometry["sequences_per_replica"])
    cache_key = (*key, before["package_sha256"])
    if cache_key in cache:
        return {**cache[cache_key], "reused_prediction": True}
    directory = getattr(cache, "directory", None)
    cached_path = (directory / (sha256(json.dumps(cache_key).encode()).hexdigest() + ".json")) if directory else None
    if cached_path and cached_path.is_file():
        receipt = _read(cached_path)
        if receipt.get("cache_key") != list(cache_key) or receipt.get("result", {}).get("status") != "completed":
            raise ValueError("body_prediction_cache_identity_mismatch")
        cache[cache_key] = receipt["result"]
        return {**receipt["result"], "reused_prediction": True}
    with tempfile.TemporaryDirectory(prefix="mindie-body-prediction-") as directory:
        output = Path(directory) / "prediction.json"
        command = [sys.executable, str(Path(__file__).with_name("body_forward_comparison.py")),
                   "--case", str(case_path), "--tokens", str(key[2]), "--context", str(key[3]),
                   "--sequences", str(key[4]), "--phase", key[1], "--output", str(output)]
        try:
            completed = subprocess.run(command, timeout=timeout_s, capture_output=True, text=True)
        except subprocess.TimeoutExpired:
            return {"status": "failed", "reason": "body_prediction_timeout",
                    "timeout_s": timeout_s, "runtime_identity": before}
        if completed.returncode:
            return {"status": "failed", "reason": "body_prediction_worker_failed",
                    "returncode": completed.returncode, "stderr": completed.stderr[-2000:],
                    "runtime_identity": before}
        value = _read(output)
    after = _sim_identity()
    value["runtime_identity"] = {**before, "sources_unchanged": before == after}
    value["case_identity"] = {"path": str(case_path), "sha256": key[0],
                              "source_unchanged": sha256_file(case_path) == key[0]}
    value["status"] = "completed"
    if before != after:
        value.update(status="failed", reason="sim_runtime_changed_during_prediction")
    elif value.get("adapter_identity", {}).get("sources_unchanged") is False:
        value.update(status="failed", reason="body_adapter_changed_during_prediction")
    elif not value["case_identity"]["source_unchanged"]:
        value.update(status="failed", reason="sim_case_changed_during_prediction")
    elif value["execution"]["peak_rss_bytes"] > 512 * 1024 ** 2:
        value.update(status="failed", reason="body_prediction_memory_budget_exceeded")
    value["reused_prediction"] = False
    if value["status"] == "completed":
        cache[cache_key] = value
        if cached_path:
            cached_path.write_text(json.dumps({"cache_key": cache_key, "result": value}) + "\n")
    return value


def compact_observation(observed):
    """Keep geometry-specific statistics and bounded original endpoint examples."""
    if "geometry_groups" in observed:
        return observed
    groups = {}
    for forward in observed.get("forwards", []):
        if forward.get("status") != "measured":
            continue
        geometry = forward.get("geometry") or observed.get("geometry") or {}
        key = json.dumps(geometry, sort_keys=True)
        groups.setdefault(key, {"geometry": geometry, "forwards": []})["forwards"].append(forward)
    result = {key: value for key, value in observed.items()
              if key not in {"forwards", "per_layer_ms", "stage_span_ms"}}
    result["geometry_groups"] = []
    for group in groups.values():
        forwards = group["forwards"]
        ids = {row["forward_id"] for row in forwards}
        sample_forwards = []
        for forward in forwards[:3]:
            sample_forwards.append({**forward, "stages": [
                scope for scope in forward.get("stages", [])
                if scope["kind"] not in {"dense_layer", "moe_layer"}]})
        entry = {"geometry": group["geometry"], "forward_count": len(forwards),
                 "body_forward_span_ms": _stats([row["body_forward_span_ms"] for row in forwards]),
                 "representative_forwards": sample_forwards}
        for field in ("per_layer_ms", "stage_span_ms"):
            entry[field] = []
            for layer in observed.get(field, []):
                samples = [sample for sample in layer.get("samples", [])
                           if sample["forward_id"] in ids and sample.get("status") == "measured"]
                if samples:
                    entry[field].append({**{key: value for key, value in layer.items()
                                           if key not in {"samples", "stats"}},
                                         "stats": _stats([sample["span_ms"] for sample in samples]),
                                         "sample_count": len(samples), "samples": samples[:1]})
        result["geometry_groups"].append(entry)
    result["detail_policy"] = "All statistics retain complete populations; up to three body endpoints and one example per layer/stage per geometry are retained."
    return result


def _automatic_scenarios(row, observed):
    """Keep captured q/batch separate from the declared representative context."""
    evidence = row.get("scenario_evidence", {})
    context = (row.get("geometry") or {}).get("context_tokens")
    context_basis = "explicit_case_geometry"
    if context is None:
        context = evidence.get("client", {}).get("input_len", evidence.get("request_input_len"))
        context_basis = "client_prompt_tokens_as_representative_initial_context"
    scenarios = []
    for group in observed.get("geometry_groups", []):
        geometry = dict(group["geometry"])
        geometry.update(phase="decode", context_tokens=context)
        geometry_key = tuple(geometry.get(field) for field in (
            "tokens_per_sequence", "context_tokens", "sequences_per_replica"))
        scenarios.append({"geometry": geometry, "geometry_resolved": all(value is not None for value in geometry_key), "observed": {
        **{key: observed.get(key) for key in (
            "schema_version", "metric_boundary", "status", "basis", "comparison_scope",
            "span_start_basis", "span_end_basis", "source_identity", "model_declaration")},
        **{key: group.get(key, []) for key in (
            "body_forward_span_ms", "per_layer_ms", "stage_span_ms", "representative_forwards")},
        **{key: group.get(key) for key in (
            "body_activity_ms", "body_internal_gap_ms", "per_stream_activity_ms")},
        "activity_interpretation": "Union of non-scheduler event intervals, including real HCOM protocol wait; this is not PMU-confirmed useful hardware busy time.",
        "geometry": geometry,
        "batch_evidence": {
            "execution_sequences_per_replica": geometry.get("sequences_per_replica"),
            "execution_query_rows": geometry.get("query_rows"),
            "client_concurrency": evidence.get("client", {}).get("concurrency"),
            "basis": geometry.get("batch_basis"),
            "interpretation": "Tensor-export execution batch may include graph padding; client concurrency is a request-level condition, not substituted for the captured execution batch.",
        },
        "comparison_assumptions": [
            f"Context basis: {context_basis}; active KV increments during this capture are not established.",
            "Forced load balance, acceptance=0.8/DSpark and prefix-hit=100% are not assumed to be captured facts.",
        ]}})
    return scenarios


def _compare_scenarios(result, scenarios, case_path, cache, *, prediction_timeout_s, run_predictions,
                       geometry_limit=None, on_geometry=None):
    rows = []
    scenarios = sorted(scenarios, key=lambda item: -item["observed"]["body_forward_span_ms"]["count"])
    for index, scenario in enumerate(scenarios):
        deferred = geometry_limit is not None and index >= geometry_limit
        if deferred:
            worker = {"status": "unresolved", "reason": "prediction_deferred_by_population_priority"}
        elif not scenario["geometry_resolved"] or not run_predictions:
            worker = {"status": "unresolved", "reason": "observed_forward_geometry_unresolved"
                      if not scenario["geometry_resolved"] else "prediction_not_requested"}
        else:
            worker = _predict_bounded(case_path, scenario["geometry"], cache, timeout_s=prediction_timeout_s)
        if worker["status"] != "completed":
            compare = _empty_comparison([worker["reason"]])
            compare.update(observed_ms=scenario["observed"]["body_forward_span_ms"],
                           observed_forward_count=scenario["observed"]["body_forward_span_ms"]["count"])
        else:
            compare = compare_body_forward(worker["prediction"], scenario["observed"])
        if worker["status"] == "failed":
            compare["status"] = "failed"
        geometry = scenario["geometry"]
        suffix = f"q{geometry.get('tokens_per_sequence')}_b{geometry.get('sequences_per_replica')}_m{geometry.get('query_rows')}"
        rows.append({
            **{key: value for key, value in result.items() if key not in {"observed", "prediction"}},
            "source_case_id": result["case_id"], "case_id": result["case_id"] + ":" + suffix,
            "status": compare["status"], "geometry": geometry, "observed": scenario["observed"],
            "comparison": compare, "prediction": worker.get("prediction"),
            "prediction_execution": {key: value for key, value in worker.items() if key != "prediction"},
            "runtime_identity": worker.get("runtime_identity"),
            "per_layer_comparison": compare_layers(worker["prediction"], scenario["observed"])
            if worker["status"] == "completed" else None,
        })
        if on_geometry is not None:
            on_geometry({"source_case_id": result["case_id"], "geometry_index": index + 1,
                         "geometry_count": len(scenarios), "forward_count": compare["observed_forward_count"],
                         "geometry": geometry, "status": compare["status"],
                         "reason": worker.get("reason"), "reused_prediction": worker.get("reused_prediction")})
    result["geometry_cases"] = rows


def replay_case(row, base, *, max_events=5_000_000, timeout_s=30,
                prediction_timeout_s=90, prediction_cache=None, run_predictions=True,
                reuse_extractions=None, geometry_limit=None, on_geometry=None):
    prediction_cache = prediction_cache if prediction_cache is not None else {}
    result = {
        "case_id": row["case_id"], "status": "unresolved",
        "variant_id": row.get("variant_id"),
        "source_identity": dict(row["source"]), "geometry": row.get("geometry"),
        "scenario_evidence": row.get("scenario_evidence", {}),
        "observed": None, "prediction": None, "runtime_identity": None,
        "comparison": _empty_comparison(list(row.get("unresolved_reasons", []))),
        "auxiliary_graph_envelopes": {
            "reference": row.get("graph_envelopes_path"), "not_body_forward": True},
    }
    automatic = not row.get("boundaries_path")
    if automatic and not row.get("sim_case_path"):
        result["comparison"]["reasons"].append("target_body_boundary_evidence_missing")
        return result
    boundary_path = _path(base, row["boundaries_path"]) if not automatic else None
    boundaries = _read(boundary_path) if boundary_path else None
    if automatic:
        from mindie_profiler.decode_segmentation import auto_segment_decode_forwards

        case_path = _path(base, row["sim_case_path"])
        case = _read(case_path)
        config = _model_config(case)
        config.update(row.get("segmentation_options", {}))
        result["declared_runtime"] = _declared_runtime(case)
        reused = (_path(base, row["extraction_path"]) if row.get("extraction_path") else
                  Path(reuse_extractions) / f"auto-forward-{row['case_id']}.json"
                  if reuse_extractions else None)
        if row.get("extraction_path") and not reused.is_file():
            raise ValueError("declared_forward_extraction_missing")
        if reused and reused.is_file():
            observed = _read(reused)
            identity = observed.get("source_identity") or {}
            current_hash = sha256_file(_path(base, row["source"]["path"]))
            if identity.get("sha256") != current_hash or current_hash != row["source"].get("sha256"):
                raise ValueError("reused_forward_extraction_source_hash_mismatch")
            for key in ("name", "layers", "hidden_size", "vocab_size", "tp"):
                if observed.get("model_declaration", {}).get(key) != config[key]:
                    raise ValueError(f"reused_forward_model_declaration_differs:{key}")
            result["extraction_identity"] = {"path": str(reused), "sha256": sha256_file(reused),
                                             "reused_existing_extraction": True}
        else:
            events, source = _source(_path(base, row["source"]["path"]), row["source"], None,
                                     max_events=max_events, timeout_s=timeout_s)
            observed = auto_segment_decode_forwards(events, config, source=source, max_events=max_events)
        observed = compact_observation(observed)
        result["source_identity"] = observed["source_identity"]
        result["model_structure_identity"] = {"path": str(case_path), "sha256": sha256_file(case_path)}
    else:
        events, source = _source(_path(base, row["source"]["path"]), row["source"], boundaries,
                                 max_events=max_events, timeout_s=timeout_s)
        result["source_identity"] = source.content_identity()
        result["boundary_identity"] = {"path": str(boundary_path), "sha256": sha256_file(boundary_path)}
        observed = measure_forward_spans(
            events, boundaries, source=source, clock_domain=row.get("clock_domain", "unix_wall_ns"),
            max_events=max_events)
    result["observed"] = observed
    if automatic:
        scenarios = _automatic_scenarios(row, observed)
        if scenarios:
            _compare_scenarios(result, scenarios, case_path, prediction_cache,
                               prediction_timeout_s=prediction_timeout_s, run_predictions=run_predictions,
                               geometry_limit=geometry_limit, on_geometry=on_geometry)
        else:
            result["comparison"] = _empty_comparison(["complete_decode_topology_not_found"])
            result["comparison"].update(observed_ms=observed["body_forward_span_ms"],
                                         observed_forward_count=observed["body_forward_span_ms"]["count"])
        return result
    reasons = []
    if not observed["body_forward_span_ms"]["count"]:
        reasons.append("measured_body_forward_unresolved")
    if not row.get("sim_case_path"):
        reasons.append("sim_case_declaration_missing")
    geometry = row.get("geometry") or {}
    for field in GEOMETRY_FIELDS:
        if geometry.get(field) is None:
            reasons.append(f"declared_geometry_missing:{field}")
        elif (observed.get("geometry") or {}).get(field) != geometry[field]:
            reasons.append(f"observed_declared_geometry_differs:{field}")
    if reasons:
        result["comparison"] = _empty_comparison(reasons)
        result["comparison"].update(observed_ms=observed["body_forward_span_ms"],
                                     observed_forward_count=observed["body_forward_span_ms"]["count"])
        return result
    case_path = _path(base, row["sim_case_path"])
    result["case_identity"] = {"path": str(case_path), "sha256": sha256_file(case_path)}
    if not run_predictions:
        result["comparison"] = _empty_comparison(["prediction_not_requested"])
        result["comparison"].update(observed_ms=observed["body_forward_span_ms"],
                                     observed_forward_count=observed["body_forward_span_ms"]["count"])
        return result
    worker = _predict_bounded(case_path, geometry, prediction_cache, timeout_s=prediction_timeout_s)
    result["prediction_execution"] = {key: value for key, value in worker.items() if key != "prediction"}
    result["runtime_identity"] = worker.get("runtime_identity")
    if worker["status"] != "completed":
        result["status"] = "failed"
        result["comparison"] = {**_empty_comparison([worker["reason"]]), "status": "failed"}
        result["comparison"].update(observed_ms=observed["body_forward_span_ms"],
                                     observed_forward_count=observed["body_forward_span_ms"]["count"])
        return result
    predicted = worker["prediction"]
    result["prediction"] = predicted
    result["comparison"] = compare_body_forward(predicted, observed)
    result["per_layer_comparison"] = compare_layers(predicted, observed)
    result["status"] = result["comparison"]["status"]
    return result


def replay_manifest(manifest, *, base, max_events=5_000_000, timeout_s=30,
                    prediction_timeout_s=90, run_predictions=True, reuse_extractions=None,
                    prediction_cache_dir=None, on_case=None, geometry_limit=None, on_geometry=None):
    if manifest.get("schema_version") != "mindie-decode-forward-replay/1":
        raise ValueError("unknown_decode_forward_manifest_schema")
    rows, seen, prediction_cache = [], set(), PredictionCache(prediction_cache_dir)
    for row in manifest["cases"]:
        if row["case_id"] in seen:
            raise ValueError(f"duplicate_forward_case:{row['case_id']}")
        seen.add(row["case_id"])
        try:
            result = replay_case(row, base, max_events=max_events, timeout_s=timeout_s,
                                 prediction_timeout_s=prediction_timeout_s, prediction_cache=prediction_cache,
                                 run_predictions=run_predictions, reuse_extractions=reuse_extractions,
                                 geometry_limit=geometry_limit, on_geometry=on_geometry)
            rows.extend(result.pop("geometry_cases", None) or [result])
        except (OSError, ValueError, ProfilerError) as error:
            rows.append({"case_id": row["case_id"], "status": "failed",
                         "source_identity": row["source"], "observed": None, "prediction": None,
                         "comparison": {**_empty_comparison([str(error)]), "status": "failed"},
                         "error": {"type": type(error).__name__, "message": str(error)}})
        if on_case is not None:
            on_case({"source_case_id": row["case_id"], "completed_source_cases": len(seen),
                     "total_source_cases": len(manifest["cases"]),
                     "geometry_rows": sum(result.get("source_case_id", result["case_id"]) == row["case_id"]
                                          for result in rows)})
    counts = Counter(row["status"] for row in rows)
    return {
        "schema_version": "mindie-decode-forward-replay-report/1",
        "variant_id": manifest.get("variant_id"),
        "baseline_reference": manifest.get("baseline_reference"),
        "not_new_live_collection": True, "cases": rows,
        "summary": {"case_count": len(rows), "source_case_count": len(seen),
                    "measured_cases": sum(bool(row.get("observed", {}).get("body_forward_span_ms", {}).get("count"))
                                          for row in rows if row.get("observed")),
                    "compared_cases": counts["compared"],
                    "passed_cases": sum(row["comparison"]["passed"] is True for row in rows),
                    "unresolved_cases": counts["unresolved"], "failed_cases": counts["failed"]},
        "limitations": ["Graph execution envelopes and TPOT are not target-body spans.",
                        "Automatic topology alignment is not exact Host/module occurrence binding.",
                        "Scenario targets do not establish capture conditions.",
                        "Sim TP peers are symmetric and initially ready at zero; measured collective elapsed can include peer wait. Single-rank intervals cannot separate payload transport from peer wait and must not be used to fit link bandwidth."],
    }


def attach_pooled_steady_layers(report, path):
    """Join source-pinned exact call populations without opening the source CSV."""
    sidecar = _read(path)
    if sidecar.get("schema_version", sidecar.get("schema")) != "mindie-steady-layer-pooled/1":
        raise ValueError("unknown_steady_layer_population_schema")
    cases = {row["case_id"]: row for row in sidecar["cases"]}
    for row in report["cases"]:
        if not row.get("per_layer_comparison"):
            continue
        pooled = cases[row.get("source_case_id", row["case_id"])]
        if pooled["source_identity"]["sha256"] != row["source_identity"]["sha256"]:
            raise ValueError("pooled_layer_source_identity_differs")
        extraction_path = _path(path.parent, pooled["extraction_identity"]["path"])
        if sha256_file(extraction_path) != pooled["extraction_identity"]["sha256"]:
            raise ValueError("pooled_layer_extraction_file_changed")
        extraction = _read(extraction_path)
        if (extraction["body_acceptance_identity"]["sha256"] != row["extraction_identity"]["sha256"]
                or extraction["source_identity"]["sha256"] != row["source_identity"]["sha256"]
                or extraction["forward_count"] != pooled["forward_count"]):
            raise ValueError("pooled_layer_body_population_differs")
        for field in ("query_rows", "tokens_per_sequence", "sequences_per_replica"):
            if pooled["geometry"].get(field) != row["geometry"].get(field):
                raise ValueError(f"pooled_layer_geometry_differs:{field}")
        row["per_layer_comparison"]["pooled_steady_layer_comparison"] = compare_pooled_layers(
            row["per_layer_comparison"]["steady_layer_comparison"], pooled)
    report["steady_layer_population_identity"] = {"path": str(path.resolve()), "sha256": sha256_file(path)}


def render(report):
    lines = ["# Decode body-forward replay", "",
             "Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.", ""]
    if report.get("runtime_provenance"):
        lines.extend(["Runtime source declaration: " + json.dumps(report["runtime_provenance"], sort_keys=True) + ".", ""])
    if report.get("variant_id"):
        lines.extend(["Variant: `" + report["variant_id"] + "`. Baseline: "
                      + json.dumps(report.get("baseline_reference"), sort_keys=True) + ".", ""])
    runtimes = {json.dumps(row["runtime_identity"], sort_keys=True)
                for row in report["cases"] if row.get("runtime_identity")}
    for runtime in sorted(runtimes):
        identity = json.loads(runtime)
        lines.extend([f"Sim {identity['version']}; {identity['file_count']} package files; SHA256 `{identity['package_sha256']}`; package `{identity['package_path']}`.", ""])
    lines.extend([
             "| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |",
             "|---|---:|---:|---:|---:|---:|---:|---|"])
    number = lambda value: "—" if value is None else f"{value:.6f}"
    for row in report["cases"]:
        compare = row["comparison"]
        stats = compare["observed_ms"]
        error = compare["relative_error"]
        lines.append("| " + " | ".join([
            row["case_id"], str(stats["count"]), number(stats["mean"]), number(stats["p50"]),
            number(stats["p90"]), number(compare["predicted_ms"]),
            "—" if error is None else f"{error:+.2%}",
            row["status"] + (": " + "; ".join(compare["reasons"]) if compare["reasons"] else ""),
        ]) + " |")
    lines.extend(["", "## Device activity and internal uncovered intervals", "",
                  "Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.", "",
                  "Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.", "",
                  "| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |",
                  "|---|---:|---:|---:|---:|---|---|---|"])
    for row in report["cases"]:
        observed = row.get("observed") or {}
        activity = (observed.get("body_activity_ms") or {}).get("mean")
        gap = (observed.get("body_internal_gap_ms") or {}).get("mean")
        body = row["comparison"]["observed_ms"].get("mean")
        declared = row.get("declared_runtime") or {}
        mode = ((row.get("scenario_evidence") or {}).get("runtime", {}).get("graph_mode")
                or declared.get("captured_execution_mode") or "not_established")
        lines.append("| " + " | ".join([
            row["case_id"], number(body), number(activity), number(gap),
            f"{gap / body:.2%}" if gap is not None and body else "—", mode,
            " / ".join(str(declared.get(field, "—")) for field in ("tp", "dp", "ep")),
            " / ".join(str(declared.get(field, "—")) for field in ("graph_mode", "graph_capture_mode")),
        ]) + " |")
    lines.extend(["", "## Per-layer comparison", "",
                  "Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.", "",
                  "| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |",
                  "|---|---|---:|---:|---:|---:|---:|---:|"])
    for row in report["cases"]:
        layers = row.get("per_layer_comparison") or {}
        for group in layers.get("ffn_kind_distributions", []):
            observed, predicted = group["observed_ms"], group["predicted_ms"]
            selected = [layer for layer in layers["layers"] if layer["kind"] == group["kind"]]
            passed = sum(layer["passed"] is True for layer in selected)
            count = sum(layer["status"] == "compared" for layer in selected)
            error = (predicted["mean"] - observed["mean"]) / observed["mean"]
            lines.append("| " + " | ".join([
                row["case_id"], group["kind"], f"{passed} / {count}", number(observed["mean"]),
                number(observed["p50"]), number(observed["p90"]), number(predicted["mean"]), f"{error:+.2%}",
            ]) + " |")
    lines.extend(["", "## Layers grouped by attention structure", "",
                  "Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.", "",
                  "| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |",
                  "|---|---|---:|---:|---:|---:|---:|---:|"])
    for row in report["cases"]:
        for group in (row.get("per_layer_comparison") or {}).get("attention_kind_distributions", []):
            observed, predicted = group["observed_ms"], group["predicted_ms"]
            error = (predicted["mean"] - observed["mean"]) / observed["mean"]
            lines.append("| " + " | ".join([
                row["case_id"], group["attention_kind"],
                f"{group['passed_layers']} / {group['compared_layers']}",
                number(observed["mean"]), number(observed["p50"]), number(observed["p90"]),
                number(predicted["mean"]), f"{error:+.2%}",
            ]) + " |")
    lines.extend(["", "| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |",
                  "|---|---|---:|---:|---:|"])
    for row in report["cases"]:
        for group in (row.get("per_layer_comparison") or {}).get("attention_kind_distributions", []):
            lines.append("| " + " | ".join([
                row["case_id"], group["attention_kind"], number(group["observed_ms"]["mean"]),
                number((group.get("observed_activity_ms") or {}).get("mean")),
                number((group.get("observed_internal_gap_ms") or {}).get("mean")),
            ]) + " |")
    lines.extend(["", "## Steady layer statistics excluding Layer 0", "",
                  "The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.", "",
                  "| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |",
                  "|---|---|---:|---:|---:|---:|---:|---:|"])
    for row in report["cases"]:
        steady = (row.get("per_layer_comparison") or {}).get("steady_layer_comparison")
        if not steady:
            continue
        for group in [steady["population"], *steady["attention_groups"]]:
            compare = group["comparison"]
            error = compare["relative_error"]
            lines.append("| " + " | ".join([
                row["case_id"], group["attention_kind"] or "all", str(group["layer_count"]),
                str(group["observed_call_count"]), number(group["observed_layer_mean_ms"]["mean"]),
                number(compare["observed_ms"]), number(compare["predicted_ms"]),
                "—" if error is None else f"{error:+.2%}",
            ]) + " |")
    if report.get("steady_layer_population_identity"):
        lines.extend(["", "### Exact pooled steady layer calls", "",
                      "This separate population uses the integer span of every aligned layer invocation except Layer 0. It provides an actual pooled P50; Sim repeats each matching layer prediction once per Forward. Full body timing above is unchanged.", "",
                      "| Case | Attention group | Layers | Layer calls | Real pooled mean ms | Real pooled P50 ms | Real pooled P90 ms | Sim pooled P50 ms | P50 error |",
                      "|---|---|---:|---:|---:|---:|---:|---:|---:|"])
        for row in report["cases"]:
            pooled = (row.get("per_layer_comparison") or {}).get("pooled_steady_layer_comparison") or {}
            for group in pooled.get("groups", []):
                observed, predicted = group["observed_ms"], group["predicted_ms"]
                error = group["relative_error_vs_p50"]
                lines.append("| " + " | ".join([
                    row["case_id"], group["attention_kind"] or "all", str(group["layer_count"]),
                    str(group["observed_call_count"]), number(observed["mean"]), number(observed["p50"]),
                    number(observed["p90"]), number(predicted["p50"]),
                    "—" if error is None else f"{error:+.2%}",
                ]) + " |")
    lines.extend(["", "Layer 0 remains in body latency and the complete-layer comparison:", "",
                  "| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |",
                  "|---|---:|---:|---:|---:|---:|---:|"])
    for row in report["cases"]:
        for layer in ((row.get("per_layer_comparison") or {}).get("steady_layer_comparison") or {}).get("excluded_layers", []):
            observed = layer["observed_ms"]
            error = layer["relative_error"]
            lines.append("| " + " | ".join([
                row["case_id"], str(observed["count"]), number(observed["mean"]),
                number(observed["p50"]), number(observed["p90"]), number(layer["predicted_ms"]),
                "—" if error is None else f"{error:+.2%}",
            ]) + " |")
    lines.extend(["", "## Execution batch and client TPOT", "",
                  "Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.", "",
                  "| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"])
    for row in report["cases"]:
        evidence = row.get("scenario_evidence") or {}
        tpot = evidence.get("tpot") or {}
        profiled = tpot.get("profiled_run_client_ms") or {}
        geometry = row.get("geometry") or {}
        lines.append("| " + " | ".join([
            row["case_id"], str(geometry.get("tokens_per_sequence", "—")),
            str(geometry.get("sequences_per_replica", "—")),
            str(geometry.get("query_rows", "—")), str(geometry.get("valid_rows") or "unknown"),
            str(geometry.get("context_tokens", "—")),
            str(evidence.get("client", {}).get("concurrency", "—")),
            number(profiled.get("mean")), number(profiled.get("median")),
            number(tpot.get("profiled_engine_window_estimate_ms")),
            number(tpot.get("unprofiled_sweep_ms")),
        ]) + " |")
    lines.extend(["", "## Separate model boundaries", "",
                  "These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.", "",
                  "| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |",
                  "|---|---|---:|---:|---:|---:|"])
    for row in report["cases"]:
        for stage in (row.get("observed") or {}).get("stage_span_ms", []):
            stats = stage["stats"]
            if stats["count"]:
                lines.append("| " + " | ".join([
                    row["case_id"], stage["kind"], str(stats["count"]), number(stats["mean"]),
                    number(stats["p50"]), number(stats["p90"]),
                ]) + " |")
    lines.extend(["", "Summary: " + json.dumps(report["summary"], sort_keys=True), ""])
    return "\n".join(lines)


def main():
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-events", type=int, default=5_000_000)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--prediction-timeout", type=float, default=90)
    parser.add_argument("--extract-only", action="store_true")
    parser.add_argument("--reuse-extractions", type=Path)
    parser.add_argument("--prediction-cache-dir", type=Path)
    parser.add_argument("--runtime-source-commit", help="Caller-declared source commit; selected package hash is independently recorded")
    parser.add_argument("--steady-pooled", type=Path, help="Source-pinned exact layer-call quantiles from a prior capture scan")
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--geometry-limit", type=int,
                        help="Predict the largest N Forward populations per source; retain every other bucket as deferred")
    args = parser.parse_args()
    manifest = _read(args.manifest)
    if args.case_id:
        available = {row["case_id"] for row in manifest["cases"]}
        if set(args.case_id) - available:
            parser.error("requested case ID is absent from manifest")
        manifest["cases"] = [row for row in manifest["cases"] if row["case_id"] in args.case_id]
    runtime_start = (_sim_identity() if not args.extract_only
                     and any(row.get("sim_case_path") for row in manifest["cases"]) else None)
    report = replay_manifest(manifest, base=args.manifest.resolve().parent,
                             max_events=args.max_events, timeout_s=args.timeout,
                             prediction_timeout_s=args.prediction_timeout,
                             run_predictions=not args.extract_only, reuse_extractions=args.reuse_extractions,
                             prediction_cache_dir=args.prediction_cache_dir,
                             geometry_limit=args.geometry_limit,
                             on_geometry=lambda row: print(json.dumps(row), flush=True),
                             on_case=lambda row: print(json.dumps(row), flush=True))
    if args.steady_pooled:
        attach_pooled_steady_layers(report, args.steady_pooled)
    if runtime_start:
        runtime_end = _sim_identity()
        report["runtime_generation"] = {"start": runtime_start, "end": runtime_end,
                                        "unchanged": runtime_start == runtime_end}
    report["manifest_identity"] = {"path": str(args.manifest.resolve()),
                                   "sha256": sha256_file(args.manifest)}
    if args.runtime_source_commit:
        report["runtime_provenance"] = {"source_commit": args.runtime_source_commit,
                                        "basis": "caller_identified_selected_package"}
    # getrusage has platform-specific units; placement is unchanged.
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak = int(peak if sys.platform == "darwin" else peak * 1024)
    report["execution"] = {"elapsed_seconds": time.perf_counter() - started,
                           "peak_rss_bytes": peak, "memory_limit_bytes": 512 * 1024 ** 2,
                           "memory_budget_passed": peak <= 512 * 1024 ** 2,
                           "prediction_timeout_seconds": args.prediction_timeout,
                           "source_scan_timeout_seconds": args.timeout}
    report["status"] = "failed" if (report["summary"]["failed_cases"]
        or not report["execution"]["memory_budget_passed"]
        or not report.get("runtime_generation", {"unchanged": True})["unchanged"]) else "completed"
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    args.output.with_suffix(".md").write_text(render(report))
    print(json.dumps(report["summary"]))
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
