"""[Role] Price every valid current cohort with one bounded worker per physical program.
[Invariants] No historical cost reuse; tensor and resource eligibility remain in Sim.
[Timeouts & Locks] Explicit per-program timeout and bounded JSON; no locks.
[Side-Effect Policy] Read declarations and write results to the requested external directory.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
from mindie_sim.cohort_accuracy import accuracy_fields, accuracy_policy
from operators import read as _read, write as _write


def _rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == 'darwin' else value * 1024)


def _comparison_input(mapping):
    return {**mapping, "comparison_selection": {
        "kind": "all_valid_physical_work_cohorts",
        "excluded_event_counts_by_type": {}, "excluded_event_count": 0,
        "reason": "Every mapper cohort is priced; raw events without a valid cohort remain unscored.",
    }}


def _compact_comparison(result):
    from service_evidence import service_execution_evidence

    output = {key: value for key, value in result.items() if key != "windows"}
    output["kind"] = "current_cohort_comparison_projection"
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
            if prediction is not None and "parameters" in prediction:
                reduced["prediction"]["executed_service_response"] = service_execution_evidence(
                    prediction["parameters"], serviced=prediction.get("serviced"))
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
    result = {
        **{key: row.get(key) for key in (
            "cohort_id", "native_operator_type", "physical_signature", "target_kind",
            "replica", "stage", "phase", "placement", "device_id",
            "contract_scope", "structural_classification",
            "declared_candidate_instance_count", "declared_instance_count",
            "declared_layer_count", "multiplicity")},
        "observed": {key: row.get(key) for key in (
            "event_count", "complete_event_count", "clipped_event_count", "duration_ns",
            "activity_sum_ns", "complete_activity_sum_ns", "busy_union_ns", "status_counts")},
        "target_count": len(row["target_ids"]), "target_examples": row["target_ids"][:4],
        "status": "prediction_failed", "reason": failure["reason"],
        "prediction_failure": failure, "prediction": None, "comparison": None,
        "occurrence_binding_implied": False,
    }
    return {**result, **accuracy_fields(result)}


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
        **(base or {"kind": "current_cohort_comparison_projection",
                    "report_schema_version": "mindie-sim.cohort-comparison/1",
                    "graph_id": mapping["graph_id"]}),
        "windows": windows, "status_counts": dict(counts),
        "accuracy_policy": accuracy_policy(),
        "comparison_selection": _comparison_input(mapping)["comparison_selection"],
        "distinct_priced_programs": sum(row.get("distinct_priced_programs", 0) for row in receipts),
        "attempted_physical_programs": len(keys), "program_receipts": receipts,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "maximum_resident_set_size_bytes": peak,
    }
    _write(output_path, output)
    return output



def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compare-input',required=True,type=Path)
    parser.add_argument('--case-input',required=True,type=Path)
    parser.add_argument('--compare-output',required=True,type=Path)
    parser.add_argument('--program-key')
    _compare_worker(parser.parse_args())

if __name__=='__main__': main()
