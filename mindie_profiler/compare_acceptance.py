"""Matched-run binding/evidence helpers and standalone cross-run acceptance CLI.

[Role]
Provide explicit run-binding checks, operator-sequence structural classification,
median comparison tables, a two-run acceptance driver, and one independent native
ABI comparison.  The drivers never launch workloads; callers supply run roots,
telemetry and already-produced native predictions.

[Invariants]
- Binding comparisons require runtime, device, model, shape, dtype and clock
  identity; missing facts are never treated as equal because both are null.
- Operator-sequence classes come only from two explicit event-order
  ``structure.operator_sequence`` lists; ranked hotspots are never a substitute.
- The 5 Hz health check accepts only an explicit 0.2 s sample interval.
- Correctness and profiled/unprofiled benchmark separation are explicit inputs,
  never inferred from profile timing.
- Unknown or failed C2 telemetry keeps acceptance inconclusive/failed; a false
  throttle Boolean alone is not a positive no-throttle claim.
- Native pairing requires the content-addressed ABI, operator, boundary and
  declared conditions.  Observed durations never enter prediction requests;
  unpaired sides, fused boundaries and ambiguity remain explicit.

[Timeouts & Locks]
Pure in-memory helpers plus bounded, caller-supplied exported reads through the
existing analyzer.  No network, subprocess, lock, sleep, or NPU scheduling.

[Side-Effect Policy]
Reads only caller-named files; writes only the requested acceptance JSON.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import sys
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence
from .compare_acceptance_contract import (
    _close,
    _valid_measurement,
    _valid_timing,
    _valid_window,
    _verify_provenance,
    validate_module_table,
)
from .events import ProfilerError
from .module_trace import build_module_table

from .compare_acceptance_abi import (
    _native_abi, _native_boundary, _native_clock, _native_condition_conflict_rows,
    _native_condition_difference_paths, _native_condition_differences,
    _native_condition_gap_rows, _native_condition_meta, _native_condition_strings,
    _native_conditions, _native_coverage, _native_flat_conditions,
    _native_group_differences, _native_group_key, _native_identity,
    _native_item_condition_gaps, _native_observation_items, _native_occurrence,
    _native_request_bases, _native_scope_key, _native_window_id,
)
from .compare_acceptance_helpers import (
    ACCEPTANCE_SCHEMA, BINDING_FIELDS, FORMAL_NATIVE_TOLERANCE,
    NATIVE_COMPARISON_SCHEMA, STRUCTURE_BASIS, _NATIVE_FORMAL_IDENTITY_FIELDS,
    _NATIVE_KNOWN_IF_OBSERVED, _NATIVE_LEAK_KEYS, _NATIVE_OPTIONAL_IDENTITY_FIELDS,
    _NATIVE_REQUIRED_CONDITIONS, _benchmark_checks, _binding_present, _canon,
    _capture_matches, _check_acceptance, _explicit_sequence, _hash, _lim, _load_json,
    _load_manifest, _metric_row, _native_finite, _native_request_id, _native_sha,
    _native_timing_key, _payload_host, _prepare_run, _resolve, _sample_interval, _scene,
    _scene_device_card, _structure_container, _telemetry_cards, _telemetry_payload,
    _telemetry_raw, _window_bounds, build_median_tables, compare_run_binding,
)
from .compare_acceptance_items import (
    _native_discriminating_evidence, _native_failure_matrix, _native_group_reason,
    _native_pair_reason, _native_prediction_items, _native_root_cause,
    _unpaired_observation, _unpaired_prediction,
)
from .compare_acceptance_pairs import compare_native_predictions

def _load_native_payload(path: str | Path) -> Mapping[str, Any] | Sequence[Mapping[str, Any]]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(value, (Mapping, list)):
        return value
    raise ValueError(f"{path}: expected a native comparison JSON object or list")

def compare_native_files(
    observations_path: str | Path,
    predictions_path: str | Path,
    *,
    requests_path: str | Path | None = None,
    diagnostic_tolerance: Mapping[str, Any] | None = None,
    output: str | Path | None = None,
) -> dict[str, Any]:
    """Compare one exported observation file with one independent prediction file."""
    observations = _load_native_payload(observations_path)
    predictions = _load_native_payload(predictions_path)
    requests = _load_native_payload(requests_path) if requests_path is not None else None
    report = compare_native_predictions(
        observations, predictions, requests=requests,
        diagnostic_tolerance=diagnostic_tolerance)
    report["inputs"] = {
        "observations": str(observations_path),
        "predictions": str(predictions_path),
        "requests": str(requests_path) if requests_path is not None else None,
    }
    if output is not None:
        from .report import write_report
        write_report(report, output)
    return report

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m mindie_profiler.compare_acceptance",
        description="Matched two-run C7/C2 acceptance or native ABI comparison; "
                    "consumes exported evidence only.",
        allow_abbrev=False,
    )
    parser.add_argument("--baseline-run", help="baseline run manifest JSON")
    parser.add_argument("--candidate-run", help="candidate run manifest JSON")
    parser.add_argument("--rank", action="append", default=None, help="rank filter for both roots")
    parser.add_argument("--unit", choices=("us", "ns", "ms"), default="us", help="timestamp unit for explicit run windows (default: us)")
    parser.add_argument("--top", type=int, default=8, help="number of top hotspot deltas retained per run (default: 8)")
    parser.add_argument("--native-observations", help=(
        "native observation JSON or a real kernel_details.csv to export"))
    parser.add_argument("--predictions", help="independent native prediction JSON")
    parser.add_argument("--requests", help="optional timing-free request JSON")
    parser.add_argument("--requests-output", help="write timing-free prediction requests")
    parser.add_argument("--hardware", help="explicit hardware condition for a CSV export")
    parser.add_argument("--phase", help="explicit phase condition for a CSV export")
    parser.add_argument("--model", help="explicit model condition for a CSV export")
    parser.add_argument("--quant", help="explicit quantization condition for a CSV export")
    parser.add_argument("--deployment-image-id", help="explicit native deployment condition")
    parser.add_argument("--diagnostic-relative-tolerance", type=float, default=None,
                        help="diagnostic-only; formal A5 remains fixed at 10%%")
    parser.add_argument("--diagnostic-absolute-ms", type=float, default=None,
                        help="diagnostic-only; formal A5 has no absolute allowance")
    parser.add_argument("--output", help="atomically write acceptance JSON")
    return parser

def _edit_distance(left: Sequence[str], right: Sequence[str]) -> int:
    previous = list(range(len(right) + 1))
    for i, left_item in enumerate(left, start=1):
        current = [i]
        for j, right_item in enumerate(right, start=1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (0 if left_item == right_item else 1),
            ))
        previous = current
    return previous[-1]

def classify_operator_sequence(baseline: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Classify operator-sequence change as identical/small/medium/large."""
    b_sequence, c_sequence = _explicit_sequence(baseline), _explicit_sequence(candidate)
    if b_sequence is None or c_sequence is None:
        return {
            "status": "not_available",
            "basis": None,
            "classification": "unknown",
            "reuse_recommendation": "not_available",
            "limitations": [_lim(
                "operator_sequence_unavailable",
                "both reports need an actual event-order structure.operator_sequence; "
                "ranked hotspots are not execution structure",
            )],
        }
    basis = STRUCTURE_BASIS
    longest = max(len(b_sequence), len(c_sequence))
    if b_sequence == c_sequence:
        distance = 0
        prefix, suffix = len(b_sequence), 0
        b_middle_len = c_middle_len = 0
    else:
        prefix = 0
        while prefix < min(len(b_sequence), len(c_sequence)) and b_sequence[prefix] == c_sequence[prefix]:
            prefix += 1
        suffix = 0
        while (
            suffix < min(len(b_sequence), len(c_sequence)) - prefix
            and b_sequence[-1 - suffix] == c_sequence[-1 - suffix]
        ):
            suffix += 1
        b_middle = b_sequence[prefix:len(b_sequence) - suffix]
        c_middle = c_sequence[prefix:len(c_sequence) - suffix]
        b_middle_len, c_middle_len = len(b_middle), len(c_middle)
        distance = _edit_distance(b_middle, c_middle)
    similarity = 1.0 - distance / longest if longest else 1.0
    if b_sequence == c_sequence:
        classification = "identical"
        recommendation = "full_structure_reuse"
    elif distance <= max(1, int(0.10 * longest)):
        classification = "small"
        recommendation = "layer_identity_reuse_with_event_shape"
    elif distance <= max(2, int(0.35 * longest)):
        classification = "medium"
        recommendation = "block_level_only"
    else:
        classification = "large"
        recommendation = "none"
    return {
        "status": "classified",
        "basis": basis,
        "classification": classification,
        "reuse_recommendation": recommendation,
        "baseline_count": len(b_sequence),
        "candidate_count": len(c_sequence),
        "edit_distance": distance,
        "similarity": round(similarity, 6),
        "common_prefix": prefix,
        "common_suffix": suffix,
        "middle_length_baseline": b_middle_len,
        "middle_length_candidate": c_middle_len,
        "baseline_sha256": _hash(b_sequence),
        "candidate_sha256": _hash(c_sequence),
        "limitations": [],
    }

def run_acceptance(
    baseline_manifest: Mapping[str, Any],
    candidate_manifest: Mapping[str, Any],
    *,
    rank: Sequence[str] | None = None,
    unit: str = "us",
    top_n: int = 8,
) -> dict[str, Any]:
    """Run the matched two-run acceptance without launching any workload."""
    from .compare import compare_profiles

    baseline = _prepare_run(baseline_manifest, rank=rank, unit=unit, top_n=top_n)
    candidate = _prepare_run(candidate_manifest, rank=rank, unit=unit, top_n=top_n)
    comparison = compare_profiles(
        baseline["report"], candidate["report"], require_binding=True
    )
    baseline_structure = baseline["report"].get("structure")
    candidate_structure = candidate["report"].get("structure")
    if isinstance(baseline_structure, Mapping) and isinstance(candidate_structure, Mapping):
        module_table = build_module_table(baseline_structure, candidate_structure)
        if module_table["modules"]:
            comparison.setdefault("tables", {})["modules"] = module_table
            comparison["module_scope"] = module_table["scope"]
    acceptance = _check_acceptance(
        baseline_manifest, candidate_manifest,
        baseline["review"], candidate["review"], comparison,
    )
    return {
        "schema_version": ACCEPTANCE_SCHEMA,
        "status": acceptance["status"],
        "baseline_run_id": baseline_manifest.get("run_id"),
        "candidate_run_id": candidate_manifest.get("run_id"),
        "inputs": {
            "baseline_root": str(baseline_manifest.get("root")),
            "candidate_root": str(candidate_manifest.get("root")),
            "baseline_steps_file": str(baseline_manifest.get("steps_file")),
            "candidate_steps_file": str(candidate_manifest.get("steps_file")),
            "baseline_telemetry_sha256": _hash(baseline["payload"]),
            "candidate_telemetry_sha256": _hash(candidate["payload"]),
            "baseline_raw_telemetry_sha256": baseline["raw_sha256"],
            "candidate_raw_telemetry_sha256": candidate["raw_sha256"],
        },
        "telemetry": {
            "baseline": {key: value for key, value in baseline["review"].items() if not key.startswith("_")},
            "candidate": {key: value for key, value in candidate["review"].items() if not key.startswith("_")},
        },
        "comparison": comparison,
        "acceptance": acceptance,
    }

def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.native_observations:
            observations_path = Path(args.native_observations)
            diagnostic_tolerance = None
            if (args.diagnostic_relative_tolerance is not None
                    or args.diagnostic_absolute_ms is not None):
                diagnostic_tolerance = {
                    "relative": (0.10 if args.diagnostic_relative_tolerance is None
                                 else args.diagnostic_relative_tolerance),
                    "absolute_ms": (0.0 if args.diagnostic_absolute_ms is None
                                    else args.diagnostic_absolute_ms),
                }
            if observations_path.suffix.lower() in {".csv", ".gz"}:
                if args.rank and len(args.rank) > 1:
                    print("mindie-profiler acceptance: a single CSV needs at most "
                          "one --rank", file=sys.stderr)
                    return 2
                from .sim_bridge import export_native_observations, native_prediction_requests
                observations = export_native_observations(
                    observations_path, hardware=args.hardware, phase=args.phase,
                    model=args.model, quant=args.quant,
                    deployment_image_id=args.deployment_image_id,
                    rank=args.rank[0] if args.rank else None)
                if args.requests_output:
                    requests = native_prediction_requests(observations)
                    from .report import write_report
                    write_report(requests, args.requests_output)
                    print(json.dumps({
                        "output": args.requests_output,
                        "requests": requests["counts"]["requests"],
                        "no_observed_duration": True,
                    }))
                    return 0
                if not args.predictions:
                    print("mindie-profiler acceptance: --predictions is required for "
                          "--native-observations", file=sys.stderr)
                    return 2
                result = compare_native_predictions(
                    observations, _load_native_payload(args.predictions),
                    requests=(_load_native_payload(args.requests)
                              if args.requests else None),
                    diagnostic_tolerance=diagnostic_tolerance,
                )
                result["inputs"] = {
                    "observations": str(observations_path),
                    "predictions": str(args.predictions),
                    "requests": str(args.requests) if args.requests else None,
                }
            else:
                if args.requests_output:
                    from .sim_bridge import native_prediction_requests
                    observations = _load_native_payload(observations_path)
                    requests = native_prediction_requests(observations)
                    from .report import write_report
                    write_report(requests, args.requests_output)
                    print(json.dumps({
                        "output": args.requests_output,
                        "requests": requests["counts"]["requests"],
                        "no_observed_duration": True,
                    }))
                    return 0
                if not args.predictions:
                    print("mindie-profiler acceptance: --predictions is required for "
                          "--native-observations", file=sys.stderr)
                    return 2
                result = compare_native_files(
                    observations_path, args.predictions, requests_path=args.requests,
                    diagnostic_tolerance=diagnostic_tolerance,
                )
        else:
            if not args.baseline_run or not args.candidate_run:
                print("mindie-profiler acceptance: provide --baseline-run/--candidate-run "
                      "or --native-observations/--predictions", file=sys.stderr)
                return 2
            result = run_acceptance(
                _load_manifest(args.baseline_run), _load_manifest(args.candidate_run),
                rank=args.rank, unit=args.unit, top_n=args.top,
            )
    except TimeoutError:
        raise
    except (OSError, ValueError, KeyError, ProfilerError) as exc:
        print(f"mindie-profiler acceptance: {exc}", file=sys.stderr)
        return 2
    if args.output:
        from .report import write_report
        write_report(result, args.output)
        print(json.dumps({"output": args.output, "status": result["status"]}))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 3

if __name__ == "__main__":
    raise SystemExit(main())
