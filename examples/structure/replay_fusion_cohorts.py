"""Replay the retained complete captures and compare declared fusion cohorts.

[Role] Run serial captures and independently bounded physical-program comparisons.
[Invariants] Historical windows and source hashes are verified, not inferred
  phases. Default/source declarations and selected resource recipes stay separate.
  Raw events are never retained or used to populate a model declaration.
[Timeouts & Locks] Bounded source scan, 256-event queues, 120s per physical program.
[Side-Effect Policy] Reads existing local captures; writes requested JSON only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from queue import Empty, Full, Queue
import resource
import subprocess
import sys
from threading import Event as StopEvent
import time

from mindie_profiler.events import Observation, QueryStats, SourceRef, Window
from mindie_profiler.sources_csv import CsvSource, probe_csv
from mindie_profiler.structure_mapping import StructureMapper


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "examples/structure/acceptance-20261029"
MAX_JSON_BYTES = 32 * 1024 * 1024
CAPTURE_KEYS = (
    "a3_glm53_prefill", "a3_glm53_decode", "a3_qwen35", "a3_qwen36",
    "a3_v4f", "a3_v4pro", "a5_kimi_k3", "a5_qwen38",
)


def _read(path):
    path = Path(path)
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"metadata_exceeds_32_mib:{path}")
    return json.loads(path.read_text())


def _write(path, value):
    data = json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n"
    if len(data.encode()) > MAX_JSON_BYTES:
        raise ValueError(f"report_exceeds_32_mib:{path}")
    Path(path).write_text(data)


def _hash(path):
    digest = sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rss():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # This only decodes the OS resource API's units; it never chooses placement.
    return int(raw if sys.platform == "darwin" else raw * 1024)


def _runtime_identity():
    import mindie_sim

    sim = Path(mindie_sim.__file__).resolve().parents[1]
    files = [
        *sorted((ROOT / "mindie_profiler").rglob("*.py")),
        *sorted((sim / "mindie_sim").rglob("*.py")),
        *sorted((sim / "mindie_sim/backends/profiles").glob("*.json")),
        *sorted((sim / "mindie_sim/model_configs").glob("*.json")),
        *sorted((sim / "examples/cases").glob("*.json")),
        Path(__file__).resolve(), BASE / "head-normalization-evidence.json",
    ]
    return {str(path): _hash(path) for path in files}


def _variant(key, old, *, decode=False, fused=False):
    execution = {name: old["declared_execution"][name]
                 for name in ("phase", "tokens", "context", "sequences")}
    if decode:
        execution.update(phase="decode", tokens=1, context=32768)
    case_path = Path(old["declaration_source"]["case_path"])
    case = _read(case_path)
    lowerings = {}
    passes = None
    norm_evidence = None
    if "glm53" in key or decode:
        lowerings["mla_prolog"] = "vllm_ascend_mla_prolog_v3"
    if "glm53" in key:
        evidence_path = BASE / "head-normalization-evidence.json"
        evidence = _read(evidence_path)
        selection = evidence["selected_glm_scenario"]
        lowerings.update(selection["kernels"]["lowerings"])
        passes = selection["lowering_passes"]
        case.setdefault("runtime", {})["lowering_passes"] = passes
        norm_evidence = {
            "file": str(evidence_path), "sha256": _hash(evidence_path),
            "basis": "independent_checkpoint_global_norm_bias_predicate_and_source",
            "checkpoint_metadata_sha256": evidence["glm_checkpoint"]["sha256"],
            "source_sha256": evidence["glm_runtime_source"]["sha256"],
            "capture_dispatch_identity_verified": False,
        }
    if fused:
        if "glm53" in key:
            options = {"roles": ["mla_prolog", "lightning_indexer"],
                       "traffic_profile": "preserve_workspaces"}
        else:
            options = {"roles": ["hc_pre", "hc_post"], "traffic_profile": {
                "hc_pre": "hc_pre_m_k_split_175ef4d4"}}
        lowerings["native_fusion"] = {
            "implementation": "declared_native_fusion", "options": options}
    case.setdefault("runtime", {}).setdefault("kernels", {}).setdefault("lowerings", {}).update(
        lowerings)
    base_key = key + ("_decode" if decode else "")
    name = base_key + ("-selected" if fused else "-reference")
    return {
        "name": name, "declaration_key": base_key, "case": case, "geometry": execution,
        "variant": "selected_native_fusion" if fused else (
            "source_declared_unfused_reference" if lowerings else "case_default"),
        "declaration_source": {
            "case_path": str(case_path), "case_sha256": _hash(case_path),
            "implementation_overrides": lowerings,
            "lowering_passes_override": passes,
            "override_basis": "caller_declared_source_selection",
            "capture_dispatch_identity_verified": False,
            "source_evidence": {
                "mla_prolog": "prediction/family_mla_prolog.py selected source declaration",
                "resource_reuse": "fusion_boundary.evidence in exported structure",
                "native_norm": norm_evidence,
            } if lowerings else None,
        },
    }


def _variants(key, old):
    values = [_variant(key, old)]
    if "glm53" in key or key in {"a3_v4f", "a3_v4pro"}:
        values.append(_variant(key, old, fused=True))
    elif key == "a5_kimi_k3":
        values.append(_variant(key, old, decode=True))
    return values


def _queue_events(queue, cancelled):
    while not cancelled.is_set():
        try:
            event = queue.get(timeout=1)
        except Empty:
            continue
        if event is None:
            return
        yield event
    raise RuntimeError("capture_consumer_cancelled")


def _map_consumer(mapper, observation, queue, cancelled):
    window = mapper.map_window(observation, events=_queue_events(queue, cancelled))
    return mapper.finish([window])


def _put(queue, event, future, deadline):
    while True:
        if future.done():
            future.result()
            raise RuntimeError("capture_consumer_finished_before_stream")
        if time.monotonic() >= deadline:
            raise TimeoutError("capture_mapping_deadline_exceeded")
        try:
            queue.put(event, timeout=min(1, max(.001, deadline - time.monotonic())))
            return
        except Full:
            continue


def _scan(key, old, variants, *, max_rows, timeout):
    from mindie_sim.structure import export_structure

    capture = Path(old["source_identity"]["path"])
    before = capture.stat()
    digest = _hash(capture)
    if digest != old["source_identity"]["sha256"]:
        raise ValueError(f"historical_capture_hash_changed:{capture}")
    schema = probe_csv(capture)
    ref = SourceRef(
        "rank_0", 0, "csv", str(capture), capture.name, digest, before.st_size,
        schema.schema_version, schema.schema_variant, schema.header_sha256,
        schema.optional_missing, mtime_ns=before.st_mtime_ns)
    window = Window(*old["capture_bounds_ns"], label="complete_capture_mixed_phase_possible")
    stats = QueryStats("rank_0", "complete_capture", budget=max_rows)
    observation = Observation("rank_0", 0, window, None, [], ref, stats)
    states = []
    for variant in variants:
        declared = export_structure(
            variant["case"], **variant["geometry"], scope="model",
            source=variant["declaration_source"])
        variant["graph_id"] = declared["graph_id"]
        variant["structure_counts"] = {
            "nodes": len(declared["nodes"]),
            "subgraphs": len(declared.get("subgraphs", ())),
            "resource_operators": len(declared.get("resource_operators", ())),
            "roles": dict(Counter(row["role"] for row in declared.get("subgraphs", ()))),
        }
        states.append(StructureMapper(declared, mapping_limit=0, max_events=max_rows))
    cancelled, queues = StopEvent(), [Queue(maxsize=256) for _ in states]
    started, minimum, maximum, count = time.perf_counter(), None, None, 0
    deadline = time.monotonic() + timeout
    with ThreadPoolExecutor(max_workers=len(states), thread_name_prefix="fusion-map") as pool:
        futures = [pool.submit(_map_consumer, mapper, observation, queue, cancelled)
                   for mapper, queue in zip(states, queues)]
        try:
            source = CsvSource(schema, rank_id="rank_0", rank_index=0)
            for event in source.iter_events(
                    max_rows=max_rows, timeout_s=timeout, stats=stats, strict=True):
                count += 1
                minimum = event.start_ns if minimum is None else min(minimum, event.start_ns)
                maximum = event.end_ns if maximum is None else max(maximum, event.end_ns)
                for queue, future in zip(queues, futures):
                    _put(queue, event, future, deadline)
            for queue, future in zip(queues, futures):
                _put(queue, None, future, deadline)
            results = [future.result(timeout=max(.001, deadline - time.monotonic()))
                       for future in futures]
        finally:
            cancelled.set()
    after = capture.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("capture_changed_during_scan")
    if [minimum, maximum] != old["capture_bounds_ns"]:
        raise ValueError("historical_bounds_disagree_with_fresh_full_scan")
    for result in results:
        if (result["event_window_count"] != count
                or sum(result["status_counts"].values()) != count
                or sum(row["event_count"] for row in result["windows"][0]["operators"]) != count):
            raise ValueError("capture_denominator_inconsistent")
        if result["status_counts"].get("bound", 0) or result["windows"][0]["layers"]:
            raise ValueError("occurrence_bound_without_occurrence_evidence")
    return results, {
        "source_identity": ref.content_identity(), "raw_query_stats": asdict(stats),
        "positive_event_count": count, "capture_bounds_ns": [minimum, maximum],
        "historical_bounds_verified": True, "parsed_capture_scans": 1,
        "binary_hash_reads": 1, "parallel_consumers": len(states),
        "queue_capacity_per_consumer": 256,
        "mapping_elapsed_seconds": round(time.perf_counter() - started, 3),
        "mapping_peak_rss_bytes": _rss(),
    }


def _comparison_input(mapping):
    return {**mapping, "comparison_selection": {
        "kind": "all_valid_physical_work_cohorts",
        "excluded_event_counts_by_type": {}, "excluded_event_count": 0,
        "reason": "Every mapper cohort is priced; raw events without a valid cohort remain unscored.",
    }}


def _compact_comparison(result):
    output = {key: value for key, value in result.items() if key != "windows"}
    output["kind"] = "historical_fusion_cohort_comparison_projection"
    output["report_schema_version"] = output.pop("schema_version")
    output["windows"] = []
    for window in result["windows"]:
        rows = []
        for row in window["cohorts"]:
            reduced = {key: value for key, value in row.items()
                       if key not in {"target_ids", "prediction", "resource_boundary"}}
            reduced["target_count"] = len(row["target_ids"])
            reduced["target_examples"] = row["target_ids"][:4]
            prediction = row.get("prediction")
            reduced["prediction"] = None if prediction is None else {
                key: prediction[key] for key in (
                    "boundary", "representative_target_id", "representative_operator_ids",
                    "per_call_ms", "physical_work_per_instance", "serviced",
                    "single_device_program", "observed_call_count_total_ms",
                    "per_declared_step_ms", "step_total_basis", "assumptions",
                    "prediction_coverage") if key in prediction}
            rows.append(reduced)
        output["windows"].append({**window, "cohorts": rows})
    return output


def _compare_worker(args):
    from mindie_sim.cohort_comparison import compare_cohorts

    started = time.perf_counter()
    mapping = _read(args.compare_input)
    if args.program_key:
        key = json.loads(args.program_key)
        mapping = {**mapping, "windows": [
            {**window, "cohorts": [
                row for row in window["cohorts"] if list(_program_key(row)) == key]}
            for window in mapping["windows"]]}
    result = compare_cohorts(args.case_input, mapping)
    projection = _compact_comparison(result)
    projection.update(
        comparison_selection=mapping["comparison_selection"],
        elapsed_seconds=round(time.perf_counter() - started, 3),
        maximum_resident_set_size_bytes=_rss())
    _write(args.compare_output, projection)


def _program_key(row):
    return (row["physical_signature"], row["replica"], row["stage"], row["target_kind"])


def _failed_cohort(row, failure):
    return {
        **{key: row.get(key) for key in (
            "cohort_id", "native_operator_type", "physical_signature", "target_kind",
            "replica", "stage", "phase", "contract_scope", "structural_classification",
            "declared_instance_count", "declared_layer_count", "multiplicity")},
        "observed": {key: row.get(key) for key in (
            "event_count", "complete_event_count", "clipped_event_count", "duration_ns",
            "activity_sum_ns", "complete_activity_sum_ns", "busy_union_ns", "status_counts")},
        "target_count": len(row["target_ids"]), "target_examples": row["target_ids"][:4],
        "status": "prediction_failed", "reason": failure["reason"],
        "prediction_failure": failure, "prediction": None, "comparison": None,
        "occurrence_binding_implied": False,
    }


def _compare_programs(args, prefix, mapping):
    started = time.perf_counter()
    compare_input = prefix.with_suffix(".comparison-input.json")
    output_path = prefix.with_suffix(".comparison.json")
    case_path = prefix.with_suffix(".case.json")
    _write(compare_input, _comparison_input(mapping))
    keys = dict.fromkeys(_program_key(row)
                         for window in mapping["windows"] for row in window["cohorts"])
    by_cohort, receipts, peak = {}, [], 0
    base = None
    for ordinal, key in enumerate(list(keys) or [None]):
        partial = prefix.with_suffix(f".program-{ordinal}.json")
        command = [
            sys.executable, str(Path(__file__).resolve()),
            "--compare-input", str(compare_input), "--case-input", str(case_path),
            "--compare-output", str(partial), "--program-key", json.dumps(key)]
        call_started = time.perf_counter()
        try:
            child = subprocess.run(command, capture_output=True, text=True,
                                   timeout=args.compare_timeout, check=False)
        except subprocess.TimeoutExpired:
            failure = {"reason": "physical_program_timeout",
                       "timeout_seconds": args.compare_timeout}
        else:
            failure = None if child.returncode == 0 else {
                "reason": "comparison_process_failed", "returncode": child.returncode,
                "stderr": child.stderr[-6000:]}
        receipt = {
            "physical_program_key": list(key) if key is not None else None,
            "elapsed_seconds_including_startup": round(time.perf_counter() - call_started, 3),
            "status": "failed" if failure else "completed",
        }
        if failure:
            receipt.update(failure)
            for window_index, window in enumerate(mapping["windows"]):
                for row in window["cohorts"]:
                    if _program_key(row) == key:
                        by_cohort[window_index, row["cohort_id"]] = _failed_cohort(row, failure)
        else:
            result = _read(partial)
            base = base or {key: value for key, value in result.items()
                            if key not in {"windows", "status_counts", "elapsed_seconds",
                                           "maximum_resident_set_size_bytes", "distinct_priced_programs"}}
            peak = max(peak, result["maximum_resident_set_size_bytes"])
            receipt["maximum_resident_set_size_bytes"] = result["maximum_resident_set_size_bytes"]
            receipt["distinct_priced_programs"] = result["distinct_priced_programs"]
            for window_index, window in enumerate(result["windows"]):
                by_cohort.update(((window_index, row["cohort_id"]), row)
                                 for row in window["cohorts"])
        receipts.append(receipt)
        print(json.dumps({
            "comparison": prefix.name, "program": ordinal + 1 if key is not None else None,
            "program_count": len(keys), "status": receipt["status"],
            "validation_only": key is None,
            "elapsed_seconds": receipt["elapsed_seconds_including_startup"],
            "physical_signature": None if key is None else key[0],
        }), flush=True)
        partial.unlink(missing_ok=True)
    windows = [
        {**{key: window.get(key) for key in (
            "rank_id", "step", "source_identity", "window", "rank_scope",
            "cohort_excluded_event_counts")},
         "cohorts": [by_cohort[window_index, row["cohort_id"]] for row in window["cohorts"]]}
        for window_index, window in enumerate(mapping["windows"])]
    counts = Counter(row["status"] for window in windows for row in window["cohorts"])
    output = {
        **(base or {"kind": "historical_fusion_cohort_comparison_projection",
                    "report_schema_version": "mindie-sim.cohort-comparison/1",
                    "graph_id": mapping["graph_id"]}),
        "windows": windows, "status_counts": dict(counts),
        "comparison_selection": _comparison_input(mapping)["comparison_selection"],
        "distinct_priced_programs": sum(row.get("distinct_priced_programs", 0) for row in receipts),
        "attempted_physical_programs": len(keys), "program_receipts": receipts,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "maximum_resident_set_size_bytes": peak,
    }
    _write(output_path, output)
    return output


def _family_table(mapping, comparison):
    grouped = {}
    for window_index, window in enumerate(comparison["windows"]):
        for row in window["cohorts"]:
            grouped.setdefault((window_index, row["native_operator_type"]), []).append(row)
    families = []
    for window_index, window in enumerate(mapping["windows"]):
        for operator in window["operators"]:
            kind = operator["operator_type"]
            cohorts = grouped.get((window_index, kind), [])
            scored = [row for row in cohorts if row["status"] == "compared"]
            actual = sum(row["observed"]["activity_sum_ns"] / 1e6 for row in scored)
            predicted = sum(row["prediction"]["observed_call_count_total_ms"] for row in scored)
            unscored = Counter(operator.get("cohort_excluded_event_counts", {}))
            for row in cohorts:
                if row["status"] != "compared":
                    unscored[row["reason"]] += row["observed"]["event_count"]
            missing_reasons = operator["event_count"] - sum(
                row["observed"]["event_count"] for row in scored) - sum(unscored.values())
            if "cohort_excluded_event_counts" in operator and missing_reasons:
                raise ValueError("native_family_unscored_denominator_inconsistent")
            families.append({
                **operator, "cohort_count": len(cohorts),
                "activity_sum_ns": operator.get("activity_sum_ns"),
                "complete_activity_sum_ns": operator.get("complete_activity_sum_ns"),
                "cohort_status_counts": dict(Counter(row["status"] for row in cohorts)),
                "cohort_event_count": sum(row["observed"]["event_count"] for row in cohorts),
                "scored_event_count": sum(row["observed"]["event_count"] for row in scored),
                "scored_activity_sum_ms": actual,
                "predicted_scored_activity_sum_ms": predicted,
                "signed_activity_residual_ms": predicted - actual if scored else None,
                "relative_activity_error": predicted / actual - 1 if actual > 0 else None,
                "unscored_event_reason_counts": dict(unscored),
                "unscored_events_without_reason_metadata": missing_reasons,
                "cohorts": [{
                    key: row.get(key) for key in (
                        "cohort_id", "target_kind", "physical_signature",
                        "contract_scope", "structural_classification", "status", "reason", "observed",
                        "declared_instance_count", "declared_layer_count", "multiplicity",
                        "prediction", "comparison")}
                    for row in cohorts],
            })
    has_duration = all(row["activity_sum_ns"] is not None for row in families)
    return {
        "kind": "complete_capture_native_family_conditional_errors",
        "graph_id": mapping["graph_id"],
        "event_denominator": "all_valid_positive_duration_events_in_complete_capture_window",
        "activity_denominator": "sum_of_event_intersections_with_window; overlapping_events_count_separately",
        "sort_basis": "complete_capture_activity_sum_ns" if has_duration else "complete_capture_event_count",
        "families": sorted(families, key=lambda row: (
            -(row["activity_sum_ns"] if has_duration else row["event_count"]), row["operator_type"])),
        "limitations": [
            "Every native type in the complete mapping denominator is included, including zero-cohort types.",
            "Residuals use only scored cohorts; they do not estimate errors for unscored events.",
            "Activity sums may overlap and are not full model latency or throughput.",
        ],
    }


def _capture_worker(args):
    started = time.perf_counter()
    old = _read(BASE / f"body-{args.capture_key}.json")
    variants = _variants(args.capture_key, old)
    if args.declaration_key:
        variants = [row for row in variants if row["declaration_key"] == args.declaration_key]
    results, scan = _scan(
        args.capture_key, old, variants, max_rows=args.max_rows, timeout=args.capture_timeout)
    reports = []
    for variant, mapping in zip(variants, results):
        prefix = args.output_dir / ("fusion-cohort-" + variant["name"])
        mapping_path = prefix.with_suffix(".mapping.json")
        compare_input = prefix.with_suffix(".comparison-input.json")
        case_path = prefix.with_suffix(".case.json")
        _write(mapping_path, mapping)
        _write(case_path, variant["case"])
        _write(compare_input, _comparison_input(mapping))
        window = mapping["windows"][0]
        summary = {
            "kind": "historical_full_capture_fusion_cohort_replay",
            "not_new_live_collection": True, "capture_key": args.capture_key,
            "declaration_key": variant["declaration_key"], "variant": variant["variant"],
            "declaration_source": variant["declaration_source"],
            "declared_execution": mapping["declared_execution"],
            "graph_id": mapping["graph_id"], "structure_counts": variant["structure_counts"],
            **scan, "status_counts": mapping["status_counts"],
            "reason_counts": mapping["reason_counts"],
            "diagnostic_counts": mapping["diagnostic_counts"],
            "cohort_count": len(window["cohorts"]),
            "cohort_event_count": mapping["cohort_event_window_count"],
            "cohort_excluded_event_counts": window["cohort_excluded_event_counts"],
            "operator_counts": {row["operator_type"]: row["event_count"] for row in window["operators"]},
            "comparison": {"status": "pending", "reason": "comparison_runs_after_scan_worker_exits"},
            "artifacts": {name: {"file": path.name, "sha256": _hash(path), "size_bytes": path.stat().st_size}
                          for name, path in (("mapping", mapping_path), ("case", case_path),
                                             ("comparison_input", compare_input))},
            "limitations": [
                "Capture-wide events may mix phases; the case geometry is a caller declaration.",
                "No Host/module evidence is supplied; no layer or invocation is bound.",
                "Multiple declarations reuse the same capture and are not independent hardware evidence.",
                "Source-selected fusion is a conditional resource model, not captured dispatch identification.",
                "Conditional cohort residuals are descriptive; they do not establish end-to-end accuracy.",
            ],
        }
        _write(prefix.with_suffix(".json"), summary)
        reports.append({"report": prefix.with_suffix(".json").name, "variant": variant["variant"],
                        "status_counts": mapping["status_counts"],
                        "cohort_event_count": mapping["cohort_event_window_count"],
                        "comparison": summary["comparison"]})
        print(json.dumps(reports[-1]), flush=True)
    worker_key = args.declaration_key or args.capture_key
    _write(args.output_dir / f"fusion-cohort-{worker_key}.worker.json", {
        "capture_key": args.capture_key, "reports": reports, **scan,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "maximum_resident_set_size_bytes": _rss()})


def _compare_report(args, report):
    summary_path = args.output_dir / report["report"]
    summary = _read(summary_path)
    prefix = summary_path.with_suffix("")
    mapping = _read(prefix.with_suffix(".mapping.json"))
    result = _compare_programs(args, prefix, mapping)
    failed = [row for row in result["program_receipts"] if row["status"] != "completed"]
    comparison = {
        "status": "failed" if failed or result["status_counts"].get("prediction_failed") else "completed",
        **{key: result[key] for key in (
            "status_counts", "distinct_priced_programs", "attempted_physical_programs",
            "elapsed_seconds", "maximum_resident_set_size_bytes")},
        "failed_physical_programs": len(failed),
    }
    family_path = prefix.with_suffix(".families.json")
    _write(family_path, _family_table(mapping, result))
    summary["comparison"] = comparison
    for name, path in (
            ("comparison_input", prefix.with_suffix(".comparison-input.json")),
            ("comparison", prefix.with_suffix(".comparison.json")), ("families", family_path)):
        summary["artifacts"][name] = {
            "file": path.name, "sha256": _hash(path), "size_bytes": path.stat().st_size}
    _write(summary_path, summary)
    report["comparison"] = comparison
    print(json.dumps({"report": summary_path.name, "comparison": comparison}), flush=True)


def _write_family_overview(args, captures):
    variants, lines = [], [
        "# Complete-Capture Operator Families And Conditional Errors", "",
        "Historical captures replayed locally; no new live collection.", "",
        "The event denominator is every valid positive-duration event in the complete capture window. "
        "Activity sums add event intersections separately, including overlapping events. "
        "Every native type remains in the JSON tables, including types with no valid cohort. "
        "This readable view shows the 20 highest measured-activity families per declaration "
        "(event count when old mapping metadata has no activity total), plus all subgraph cohorts. "
        "Errors cover only scored events; activity sums are not wall-clock latency or throughput.", "",
        "Several declarations may reuse one capture. Their event totals are not independent "
        "and must not be added as additional captures.", "",
    ]
    for capture in captures:
        for report in capture["reports"]:
            summary_path = args.output_dir / report["report"]
            summary = _read(summary_path)
            family_path = summary_path.with_suffix(".families.json")
            table = _read(family_path)
            variants.append({
                "capture_key": capture["capture_key"], "variant": summary["variant"],
                "declaration_key": summary["declaration_key"], "graph_id": summary["graph_id"],
                "source_identity": summary["source_identity"],
                "file": family_path.name, "sha256": _hash(family_path),
                "family_count": len(table["families"]),
                "event_count": sum(row["event_count"] for row in table["families"]),
            })
            lines.extend([
                f"## {summary['declaration_key']} / {summary['variant']}", "",
                f"Sort: `{table['sort_basis']}`. Graph: `{summary['graph_id']}`.", "",
                "| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ])
            for row in table["families"][:20]:
                actual_all = row["activity_sum_ns"]
                activity = "-" if actual_all is None else f"{actual_all / 1e6:.3f}"
                scored = row["scored_event_count"]
                actual = f"{row['scored_activity_sum_ms']:.3f}" if scored else "-"
                predicted = f"{row['predicted_scored_activity_sum_ms']:.3f}" if scored else "-"
                error = row["relative_activity_error"]
                error_text = "-" if error is None else f"{error * 100:+.1f}%"
                reasons = row["unscored_event_reason_counts"]
                reason = ", ".join(f"{key} ({count})" for key, count in
                                   sorted(reasons.items(), key=lambda item: -item[1])[:2])
                lines.append(
                    f"| {row['operator_type']} | {row['event_count']} | {activity} | {scored} | "
                    f"{actual} | {predicted} | {error_text} | {reason.replace('|', '/')} |")
            subgraphs = [(family["operator_type"], row)
                         for family in table["families"] for row in family["cohorts"]
                         if row["target_kind"] == "subgraph"]
            lines.extend([
                "", "| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |",
                "| --- | --- | ---: | --- | ---: | ---: | ---: |",
            ])
            for kind, row in subgraphs:
                actual = row["observed"]["duration_ns"].get("mean")
                predicted = (row["prediction"] or {}).get("per_call_ms")
                residual = (row["comparison"] or {}).get("per_call_mean", {}).get("relative_error")
                value = lambda item: "-" if item is None else f"{item:.6f}"
                lines.append(
                    f"| {kind} | {row['cohort_id'][-12:]} | {row['observed']['event_count']} | "
                    f"{row['status']} | {value(None if actual is None else actual / 1e6)} | "
                    f"{value(predicted)} | {'-' if residual is None else f'{residual * 100:+.1f}%'} |")
            if not subgraphs:
                lines.append("| - | - | 0 | No valid subgraph cohort | - | - | - |")
            lines.append("")
    suffix = "comparison" if args.compare_existing else "replay"
    unique_events = {row["source_identity"]["sha256"]: row["event_count"] for row in variants}
    _write(args.output_dir / f"fusion-cohort-{suffix}-families.json", {
        "kind": "complete_capture_native_family_tables", "variants": variants,
        "distinct_capture_count": len(unique_events),
        "unique_capture_event_count": sum(unique_events.values()),
        "variant_totals_are_not_independent_captures": True,
        "not_new_live_collection": True, "occurrence_binding_implied": False})
    (args.output_dir / f"fusion-cohort-{suffix}-top-errors.md").write_text("\n".join(lines).rstrip() + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", action="store_true", help="Execute; otherwise show the bounded plan")
    parser.add_argument("--compare-existing", action="store_true",
                        help="Compare saved mappings and exact cases without reading raw captures")
    parser.add_argument("--output-dir", type=Path, default=BASE)
    parser.add_argument("--only", choices=CAPTURE_KEYS, action="append")
    parser.add_argument("--capture-timeout", type=float, default=180)
    parser.add_argument("--compare-timeout", type=float, default=120)
    parser.add_argument("--worker-timeout", type=float, default=600)
    parser.add_argument("--max-rows", type=int, default=1_000_000)
    parser.add_argument("--capture-key", choices=CAPTURE_KEYS)
    parser.add_argument("--declaration-key")
    parser.add_argument("--compare-input", type=Path)
    parser.add_argument("--case-input", type=Path)
    parser.add_argument("--compare-output", type=Path)
    parser.add_argument("--program-key", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.compare_input:
        _compare_worker(args)
        return
    if args.capture_key:
        _capture_worker(args)
        return
    keys = args.only or CAPTURE_KEYS
    plan = []
    for key in keys:
        old = _read(BASE / f"body-{key}.json")
        variants = [{k: v[k] for k in ("name", "variant", "geometry", "declaration_source")}
                    for v in _variants(key, old)]
        if args.compare_existing:
            variants = []
            for variant in _variants(key, old):
                saved = _read(args.output_dir / f"fusion-cohort-{variant['name']}.json")
                variants.append({
                    "name": variant["name"], "variant": saved["variant"],
                    "geometry": {name: saved["declared_execution"][name]
                                 for name in ("phase", "tokens", "context", "sequences")},
                    "declaration_source": saved["declaration_source"],
                })
        plan.append({"capture_key": key, "source": old["source_identity"],
                     "variants": variants})
    if not args.run:
        print(json.dumps({"capture_jobs": plan,
                          "raw_parsed_scans_per_capture": {
                              key: 0 if args.compare_existing else 2 if key == "a5_kimi_k3" else 1
                              for key in keys},
                          "max_bounded_consumers": 2,
                          "kimi_phase_policy": "separate_serial_workers_to_stay_below_512_mib",
                          "comparison_scope": "all_valid_physical_work_cohorts",
                          "timeout_seconds_per_distinct_physical_program": args.compare_timeout},
                         indent=2))
        return
    if args.worker_timeout < args.capture_timeout + 30:
        raise ValueError("worker_timeout_must_cover_scan_and_cleanup")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    identity = _runtime_identity()
    started, completed, failures = time.perf_counter(), [], []
    for key in keys:
        if args.compare_existing:
            old = _read(BASE / f"body-{key}.json")
            reports = []
            for variant in _variants(key, old):
                name = f"fusion-cohort-{variant['name']}.json"
                summary = _read(args.output_dir / name)
                reports.append({"report": name, "variant": summary["variant"],
                                "status_counts": summary["status_counts"],
                                "cohort_event_count": summary["cohort_event_count"]})
            capture = {
                "capture_key": key, "reports": reports,
                "source_identity": summary["source_identity"],
                "positive_event_count": summary["positive_event_count"],
                "raw_capture_reads_this_run": 0,
                "maximum_resident_set_size_bytes": 0,
                "mapping_reused": True,
            }
            completed.append(capture)
        else:
            # The two Kimi declarations exceeded the memory target together.
            # One extra streamed read is cheaper than retaining two model graphs.
            jobs = [key, key + "_decode"] if key == "a5_kimi_k3" else [None]
            for declaration_key in jobs:
                command = [sys.executable, str(Path(__file__).resolve()), "--capture-key", key,
                           "--output-dir", str(args.output_dir), "--max-rows", str(args.max_rows),
                           "--capture-timeout", str(args.capture_timeout)]
                if declaration_key:
                    command.extend(["--declaration-key", declaration_key])
                try:
                    child = subprocess.run(command, timeout=args.worker_timeout, check=False)
                    if child.returncode:
                        failures.append({"capture_key": key, "declaration_key": declaration_key,
                                         "returncode": child.returncode})
                        continue
                except subprocess.TimeoutExpired:
                    failures.append({"capture_key": key, "declaration_key": declaration_key,
                                     "reason": "capture_worker_timeout"})
                    continue
                worker_key = declaration_key or key
                completed.append(_read(args.output_dir / f"fusion-cohort-{worker_key}.worker.json"))
        for capture in [row for row in completed if row["capture_key"] == key]:
            for report in capture["reports"]:
                _compare_report(args, report)
    after = _runtime_identity()
    _write_family_overview(args, completed)
    comparison_failures = [
        {"capture_key": capture["capture_key"], "report": report["report"],
         "comparison": report["comparison"]}
        for capture in completed for report in capture["reports"]
        if report["comparison"]["status"] != "completed"]
    peak_compare = max((
        report["comparison"].get("maximum_resident_set_size_bytes", 0)
        for capture in completed for report in capture["reports"]), default=0)
    cohort_statuses = Counter()
    for capture in completed:
        for report in capture["reports"]:
            cohort_statuses.update(report["comparison"].get("status_counts", {}))
    events_by_source = {}
    for capture in completed:
        source_sha = capture["source_identity"]["sha256"]
        count = capture["positive_event_count"]
        if source_sha in events_by_source and events_by_source[source_sha] != count:
            raise ValueError("same_capture_declarations_disagree_on_complete_event_denominator")
        events_by_source[source_sha] = count
    result = {
        "kind": "historical_full_capture_fusion_cohort_validation",
        "not_new_live_collection": True, "capture_plan": plan, "captures": completed,
        "comparison_only": args.compare_existing,
        "raw_parsed_capture_scans": sum(row.get("parsed_capture_scans", 0) for row in completed),
        "failures": failures, "runtime_source_identity": identity,
        "runtime_sources_unchanged": identity == after,
        "runtime_sources_changed": sorted(key for key in identity.keys() | after.keys()
                                          if identity.get(key) != after.get(key)),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "memory_limit_bytes": 512 * 1024 * 1024,
        "peak_worker_rss_bytes": max((row["maximum_resident_set_size_bytes"] for row in completed), default=0),
        "peak_comparison_rss_bytes": peak_compare,
        "comparison_failures": comparison_failures,
        "comparison_cohort_status_counts": dict(cohort_statuses),
        "unique_declaration_count": len({
            variant["name"].removesuffix("-reference").removesuffix("-selected")
            for capture in plan for variant in capture["variants"]}),
        "declaration_variant_count": sum(len(capture["variants"]) for capture in plan),
        "distinct_captured_sources": len({row["source_identity"]["sha256"] for row in completed}),
        "complete_capture_event_count_by_source_sha256": events_by_source,
        "unique_capture_event_count": sum(events_by_source.values()),
    }
    validation_name = "fusion-cohort-comparison-validation.json" if args.compare_existing else "fusion-cohort-validation.json"
    _write(args.output_dir / validation_name, result)
    print(json.dumps({key: result[key] for key in (
        "failures", "runtime_sources_unchanged", "elapsed_seconds",
        "peak_worker_rss_bytes", "distinct_captured_sources")}), flush=True)
    if (failures or comparison_failures or identity != after
            or max(result["peak_worker_rss_bytes"], peak_compare) > result["memory_limit_bytes"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
