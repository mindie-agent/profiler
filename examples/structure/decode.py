"""Replay local Decode forward evidence without promoting step envelopes.

[Role] Join source-pinned profiler boundaries and the public Sim body API.
[Invariants] Automatic topology alignment remains labelled as an estimate,
  separate from explicit Host/module boundaries. Scenario targets are not
  measured capture facts; graph envelopes remain a separate diagnostic.
[Timeouts & Locks] Serial cases; bounded source scans and declaration reads.
[Side-Effect Policy] Read local captures and write requested reports; no devices.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
import fnmatch
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile

from mindie_profiler.events import ProfilerError, SourceRef, Window
from mindie_profiler.forward_spans import measure_forward_spans
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.sources_csv import probe_csv
from mindie_profiler.sources_db import DbSource, probe_db, sha256_file

from body import GEOMETRY_FIELDS, _stats, compare_body_forward, compare_layers, compare_pooled_layers


def _read(path):
    if path.stat().st_size > 50 * 1024 ** 2:
        raise ValueError(f"forward_declaration_too_large:{path}")
    return json.loads(path.read_text())


def _path(base, value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def local_capture_directories(root, pattern):
    """Discover existing capture directories; their names are never model inputs."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f"local_capture_root_missing:{root}")
    for parent, directories, _ in os.walk(root):
        directories.sort()
        path = Path(parent)
        if fnmatch.fnmatch(path.name, pattern):
            yield path
            directories[:] = []


def _file_identity(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def _client_token_bounds(summary):
    """Usage covers the complete prompt; a shared prefix alone does not."""
    native = summary.get("native", {})
    records = summary.get("per_request") or summary.get("requests") or []
    prompts = summary.get("observed_prompt_tokens", [r.get("prompt_tokens") for r in records])
    outputs = summary.get("observed_completion_tokens", [r.get("completion_tokens") for r in records])
    prompts = [float(v) for v in prompts if v is not None]
    outputs = [float(v) for v in outputs if v is not None]
    inputs = native.get("InputTokens", {})
    requested = None
    if summary.get("prefix_len") is not None and summary.get("suffix_len") is not None:
        requested = summary["prefix_len"] + summary["suffix_len"]
    lower = (min(prompts) if prompts else inputs.get("Min", summary.get("input_tokens", requested)))
    upper_prompt = (max(prompts) if prompts else inputs.get("Max", summary.get("input_tokens", requested)))
    output = (max(outputs) if outputs else native.get("OutputTokens", {}).get("Max",
              summary.get("output_tokens", summary.get("decode_len", summary.get("output_len")))))
    lower, upper_prompt, output = [float(v) if v is not None else None for v in (lower, upper_prompt, output)]
    basis = ("retained_request_prompt_usage" if prompts else "literal_InputTokens_summary" if inputs else
             "literal_input_tokens" if summary.get("input_tokens") is not None else
             "requested_prefix_plus_suffix_condition" if requested is not None else "context_not_observed")
    return lower, upper_prompt, output, basis


def capture_metadata(directory):
    """Read bounded producer metadata, never derive active tokens from cache shapes."""
    directory = Path(directory)
    documents, identities = {}, {}
    for name in ("capture_metadata.json", "benchmark_summary.json", "profile_evidence.json", "manifest.json", "client_cell.json"):
        path = directory / name
        if path.is_file():
            documents[name] = _read(path)
            identities[name] = _file_identity(path)
    summary = documents.get("benchmark_summary.json", {})
    client_name = "benchmark_summary.json"
    client = summary
    if "client_cell.json" in documents:
        cell = documents["client_cell.json"]
        if not cell.get("label") or cell.get("label") != summary.get("label"):
            raise ValueError("client_cell_summary_label_not_linked")
        client, client_name = cell, "client_cell.json"
    client_metrics = client.get("summary", {})
    lower, upper_prompt, output, token_basis = _client_token_bounds(client)
    upper = upper_prompt + output if upper_prompt is not None and output is not None else None
    context = {
        "basis": token_basis,
        "representative_tokens": int(lower) if lower is not None else None,
        "lower_bound_tokens": int(lower) if lower is not None else None,
        "upper_bound_tokens": int(upper) if upper is not None else None,
        "per_step_context_observed": False,
        "source_identity": identities.get(client_name),
        "requested_prefix_tokens": client.get("prefix_len"),
        "requested_suffix_tokens": client.get("suffix_len"),
        "client_token_exact": client.get("token_exact", client_metrics.get("token_exact")),
        "limitation": "The initial prompt is a conditional representative, not a per-step KV length. "
                      "Token bounds describe the associated client run; cache/table capacities are not active context.",
    }
    fields = ("model", "hardware", "tp", "dp", "ep", "quant")
    parameters, parameter_sources = {}, {}
    conflicts = []
    for name, document in documents.items():
        # Producer-declared fields only. Launch argv/log adapters may write this
        # small mapping without importing model weights or inferring from paths.
        declarations = [("capture_parameters", document.get("capture_parameters", {})),
                        ("source_configuration", document.get("source_configuration", {}))]
        extra = document.get("extra", {})
        recipe = extra.get("recipe", {})
        flat = {"model": document.get("model_path", document.get("model")),
                "quant": extra.get("quantization", document.get("quantization")),
                "hardware": document.get("hardware_sku")}
        flat_paths = {"model": "model_path" if "model_path" in document else "model",
                      "quant": "extra.quantization" if "quantization" in extra else "quantization",
                      "hardware": "hardware_sku"}
        for field, key in (("tp", "tensor_parallel_size"), ("dp", "data_parallel_size"), ("ep", "expert_parallel_size")):
            flat[field] = document.get(key, recipe.get(key))
            flat_paths[field] = key if key in document else "extra.recipe." + key
        hardware_text = extra.get("host_deviation", {}).get("identical_hardware", "")
        if flat["hardware"] is None and isinstance(hardware_text, str):
            sku = re.search(r"\b(Ascend[A-Za-z0-9]+_[0-9]+)\b", hardware_text)
            flat["hardware"] = sku.group(1) if sku else None
            flat_paths["hardware"] = "extra.host_deviation.identical_hardware"
        # client_cell.model is often a served alias, not the model_path in its
        # linked benchmark summary; retain the authoritative deployment fields.
        if name != "client_cell.json":
            declarations.append((flat_paths, flat))
        for field_path, declaration in declarations:
            for field in fields:
                value = declaration.get(field, declaration.get(field.upper()))
                if value is None:
                    continue
                if field in parameters and parameters[field] != value:
                    conflicts.append(field)
                parameters[field] = value
                parameter_sources[field] = {"identity": identities[name], "field":
                    field_path[field] if isinstance(field_path, dict) else field_path + "." + field}
    common = summary.get("common_metrics", {})
    return {"identities": identities, "capture_parameters": parameters,
            "parameter_sources": parameter_sources, "conflicting_parameters": sorted(set(conflicts)),
            "context_evidence": context,
            "client": {"input_len": context["representative_tokens"],
                       "concurrency": client.get("concurrency", client_metrics.get("concurrency",
                           common.get("Max Concurrency", {}).get("total"))),
                       "output_tokens": int(output) if output is not None else None},
            "profile_round": summary.get("round")}


def _capture_source(directory):
    for name in ("kernel_details.csv", "kernel_details.csv.gz"):
        path = directory / name
        if path.is_file():
            return path, None
    candidates = []
    for parent, children, files in os.walk(directory):
        path = Path(parent)
        if len(path.relative_to(directory).parts) >= 4:
            children[:] = []
        for name in files:
            if name in {"kernel_details.csv", "kernel_details.csv.gz"}:
                candidates.append(path / name)
    rank_zero = [p for p in candidates if any(part in {"tp0", "rank0", "rank_0"} for part in p.relative_to(directory).parts)]
    selected = rank_zero if rank_zero else candidates
    if len(selected) == 1:
        return selected[0], None
    return None, "device_capture_missing" if not selected else "representative_rank_capture_ambiguous"


def prepare_local_capture(directory, registry, base, *, template_case_id=None):
    """Prepare one registry entry using explicit/exact declarations, never scores."""
    directory = Path(directory)
    metadata = capture_metadata(directory)
    source, source_reason = _capture_source(directory)
    reasons = ([source_reason] if source_reason else [])
    if metadata["conflicting_parameters"]:
        reasons.append("conflicting_capture_parameter_evidence")
    parameters = metadata["capture_parameters"]
    declarations = registry.get("capture_templates", [])
    if template_case_id:
        ids = [template_case_id]
        selection = "explicit_template_case_id"
    else:
        required = {"model", "hardware", "tp", "dp", "ep", "quant"}
        ids = [item["case_id"] for item in declarations if required <= parameters.keys()
               and required <= item["match"].keys()
               and all(parameters.get(k) == v for k, v in item["match"].items())]
        selection = "exact_capture_parameter_declaration"
    templates = [r for r in registry["cases"] if r["id"] in ids or r["case_id"] in ids]
    if len(templates) != 1:
        reasons.append("explicit_or_unique_exact_capture_template_required")
    template = templates[0] if len(templates) == 1 else None
    declaration = next((d for d in declarations if template and d["case_id"] in {template['id'], template['case_id']}), None)
    if declaration and any(parameters[k] != v for k, v in declaration["match"].items() if k in parameters):
        reasons.append("capture_template_parameter_mismatch")
    if template:
        model_case = _read(_path(base, template["sim_case_path"]))
        placement = _declared_runtime(model_case)
        declared = {**{k: placement[k] for k in ("tp", "dp", "ep")},
                    "hardware": model_case.get("machine", {}).get("sku")}
        if any(parameters[k] != v for k, v in declared.items() if k in parameters and v is not None):
            reasons.append("capture_template_deployment_mismatch")
    if metadata["context_evidence"]["representative_tokens"] is None:
        reasons.append("initial_context_evidence_missing")
    result = {"capture_directory": str(directory.resolve()), "status": "unresolved" if reasons else "prepared",
              "reasons": reasons, "metadata": metadata, "entry": None}
    if reasons:
        return result
    identity = _file_identity(source)
    if any(r.get("source", {}).get("sha256") == identity["sha256"] and r["phase"] == "decode" for r in registry["cases"]):
        result.update(status="already_registered", reasons=["same_capture_content_already_registered"])
        return result
    case_path = _path(base, template["sim_case_path"])
    expected = template["model_case"]
    model_identity = _file_identity(case_path)
    if any(model_identity[k] != expected[k] for k in ("sha256", "size_bytes")):
        raise ValueError("capture_template_model_declaration_changed")
    case_id = "local_" + identity["sha256"][:16]
    inherited = {k: deepcopy(template[k]) for k in ("segmentation_options",) if k in template}
    entry = {**inherited, "id": "decode:" + case_id, "case_id": case_id, "phase": "decode",
             "source": {**identity, "kind": "csv"}, "model_case": model_identity,
             "sim_case_path": str(case_path), "supported_scopes": ["body"], "geometry_limit": None,
             "geometry": {"phase": "decode", "context_tokens": metadata["context_evidence"]["representative_tokens"]},
             "context_evidence": metadata["context_evidence"],
             "scenario_evidence": {"client": metadata["client"], "capture_metadata": metadata["identities"],
                                   "capture_parameters": parameters},
             "calibration": {"origin": "unchanged_explicit_template_parameters", "evaluation_relation": "not_declared",
                             "evidence_refs": [model_identity]},
             "template_selection": {"basis": selection, "template_id": template["id"],
                 "template_model_identity": model_identity,
                 "observed_parameters": parameters,
                 "unobserved_parameters": [k for k in ("model", "hardware", "tp", "dp", "ep", "quant") if k not in parameters],
                 "missing_parameters_are_not_confirmed_capture_facts": True}}
    result['entry'] = entry
    return result


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
    """Reuse Sim's normalized layer plan without instantiating a physical run."""
    from mindie_sim.prediction.structure import parse_case

    parsed = parse_case(case)
    config = parsed.model.to_dict()
    config["tp"] = parsed.runtime.parallel.tp
    proposals = int(dict(parsed.runtime.metadata).get("draft_proposal_tokens", 0))
    config["decode_max_tokens"] = max(32, parsed.runtime.max_num_seqs * (proposals + 1))
    # Segmentation consumes layer_plans. A made-up B1/q1 graph can violate an
    # explicit HCCL/source program's geometry before any capture is inspected.
    # Physical graphs belong to prediction at the measured query geometry.
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


def _calibration_metadata(row, case=None):
    calibration = row.get("calibration", {})
    regimes = (case or {}).get("runtime", {}).get("kernels", {}).get("service_regimes", [])
    return {"calibration_origin": calibration.get("origin", row.get("calibration_origin", "not_declared")),
            "calibration_evidence": {"evaluation_relation": calibration.get("evaluation_relation", "not_declared"),
                "rule_count": len(regimes), "evidence_refs": calibration.get("evidence_refs", []),
                "parameter_source": row.get("model_case", row.get("sim_case_path"))}}


def _predict_bounded(case_path, geometry, cache, *, timeout_s):
    before = _sim_identity()
    key = (sha256_file(case_path), geometry["phase"], geometry["tokens_per_sequence"],
           geometry["context_tokens"], geometry["sequences_per_replica"])
    cache_key = (*key, before["package_sha256"])
    if cache_key in cache:
        return {**cache[cache_key], "reused_prediction": True}
    with tempfile.TemporaryDirectory(prefix="mindie-body-prediction-") as directory:
        output = Path(directory) / "prediction.json"
        command = [sys.executable, str(Path(__file__).with_name("body.py")),
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


def _automatic_scenarios(row, observed, case=None):
    """Keep captured q/batch separate from the declared representative context."""
    evidence = row.get("scenario_evidence", {})
    context = (row.get("geometry") or {}).get("context_tokens")
    context_basis = "explicit_case_geometry"
    context_evidence = row.get("context_evidence")
    if context_evidence:
        context = context_evidence.get("representative_tokens", context_evidence.get("initial_prompt_tokens"))
        context_basis = context_evidence.get("basis", context_evidence.get("initial_prompt_basis", "not_declared"))
    if context is None:
        context = evidence.get("client", {}).get("input_len", evidence.get("request_input_len"))
        context_basis = "client_prompt_tokens_as_representative_initial_context"
    scenarios = []
    for group in observed.get("geometry_groups", []):
        geometry = dict(group["geometry"])
        geometry.update(phase="decode", context_tokens=context)
        speculation = (case or {}).get("runtime", {}).get("metadata", {}).get("speculation", {})
        output_rows = geometry.get("output_query_rows")
        # With explicitly disabled speculation and q=1, the unpadded logits
        # rows identify valid requests. Body tensors still describe graph M.
        if (speculation.get("enabled") is False and geometry.get("tokens_per_sequence") == 1
                and output_rows and output_rows < geometry.get("query_rows", 0)):
            geometry.update(physical_query_rows=geometry["query_rows"],
                physical_sequences_per_replica=geometry["sequences_per_replica"],
                query_rows=output_rows, sequences_per_replica=output_rows,
                batch_basis="unpadded_lm_head_rows_with_source_explicit_no_speculation")
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
        "context_evidence": context_evidence,
        "batch_evidence": {
            "execution_sequences_per_replica": geometry.get("sequences_per_replica"),
            "execution_query_rows": geometry.get("query_rows"),
            "physical_query_rows": geometry.get("physical_query_rows", geometry.get("query_rows")),
            "output_query_rows": output_rows,
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
        **_calibration_metadata(row),
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
        result.update(_calibration_metadata(row, case))
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
        scenarios = _automatic_scenarios(row, observed, case)
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
    result.update(_calibration_metadata(row, _read(case_path)))
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
                    on_case=None, geometry_limit=None, on_geometry=None):
    if manifest.get("schema_version") != "mindie-decode-forward-replay/1":
        raise ValueError("unknown_decode_forward_manifest_schema")
    rows, seen, prediction_cache = [], set(), {}
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
                         **_calibration_metadata(row),
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
                        "Sim TP peers are symmetric and initially ready at zero; measured collective elapsed can include peer wait. Single-rank intervals do not identify pure link bandwidth without separating that wait. Same-boundary observed service may calibrate explicit per-call, per-group or payload-regime responses; evaluation provenance is reported separately from contract eligibility."],
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
