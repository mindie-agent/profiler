"""Acceptance-contract validators for matched profile and C2 evidence.

[Role]
Shared pure validation for caller-explicit windows, measurement timing
summaries, and manifest SHA provenance used by the standalone acceptance driver.

[Invariants]
- Only finite numeric windows with positive duration are accepted.
- Timing count/total/min/max/mean must agree with each other.
- Provenance is accepted only when every declared file exists and its SHA256
  matches exactly; missing provenance is a failure, not an empty success.

[Timeouts & Locks]
Pure in-memory/file-hash validation; no network, subprocess, lock, or sleep.

[Side-Effect Policy]
Reads only caller-named files; no writes or source mutation.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping


def _valid_window(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, Mapping):
        return None
    start, end = value.get("start_ts"), value.get("end_ts")
    if not isinstance(start, (int, float)) or isinstance(start, bool):
        return None
    if not isinstance(end, (int, float)) or isinstance(end, bool):
        return None
    if float(end) <= float(start):
        return None
    return float(start), float(end)


def _close(left: Any, right: Any, *, rel: float = 1e-6) -> bool:
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return False
    if isinstance(left, bool) or isinstance(right, bool):
        return False
    scale = max(abs(float(left)), abs(float(right)), 1.0)
    return abs(float(left) - float(right)) <= rel * scale


def _valid_timing(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    count = value.get("count")
    total, minimum, maximum, mean = (
        value.get("total_ms"), value.get("min_ms"),
        value.get("max_ms"), value.get("mean_ms"),
    )
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        return False
    if not all(isinstance(item, (int, float)) and not isinstance(item, bool)
               for item in (total, minimum, maximum, mean)):
        return False
    if float(total) <= 0 or float(minimum) < 0 or float(maximum) < float(minimum):
        return False
    if not float(minimum) <= float(mean) <= float(maximum):
        return False
    return _close(mean, float(total) / count)


def _valid_measurement(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and _valid_window(value.get("measurement_window")) is not None
        and isinstance(value.get("duration_ms"), (int, float))
        and not isinstance(value.get("duration_ms"), bool)
        and float(value["duration_ms"]) > 0
        and isinstance(value.get("sample_count"), int)
        and not isinstance(value.get("sample_count"), bool)
        and value["sample_count"] > 0
        and _valid_timing(value.get("timing"))
        and value["timing"]["count"] == value["sample_count"]
    )


def validate_module_table(module_table: Mapping[str, Any] | None) -> tuple[bool, list[str]]:
    if not isinstance(module_table, Mapping) or not module_table.get("modules"):
        return False, ["module_table_missing"]
    reasons = []
    if module_table.get("status") != "comparable":
        reasons.append("module_table_not_comparable")
    for row in module_table["modules"]:
        module_id = row.get("module_id")
        if row.get("status") != "compared":
            reasons.append(f"module_not_compared:{module_id}")
        if row.get("baseline_mapping_coverage") != 1.0:
            reasons.append(f"baseline_mapping_incomplete:{module_id}")
        if row.get("candidate_mapping_coverage") != 1.0:
            reasons.append(f"candidate_mapping_incomplete:{module_id}")
    return not reasons, reasons


def _verify_provenance(manifest: Mapping[str, Any]) -> tuple[bool, list[str]]:
    provenance = manifest.get("provenance")
    files = provenance.get("source_files") if isinstance(provenance, Mapping) else None
    if not isinstance(files, Mapping) or not files:
        return False, ["provenance_source_files_missing"]
    failures: list[str] = []
    for name, item in files.items():
        if not isinstance(item, Mapping) or not isinstance(item.get("path"), str):
            failures.append(f"provenance_entry_invalid:{name}")
            continue
        path = Path(item["path"])
        if not path.is_file():
            failures.append(f"provenance_file_missing:{name}")
        elif not isinstance(item.get("sha256"), str) or _hash_bytes(path) != item["sha256"]:
            failures.append(f"provenance_hash_mismatch:{name}")
    return not failures, failures


def _hash_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


NATIVE_CANONICAL_SCHEMA = "mindie-profiler-a5-t16-canonical/1"
NATIVE_COMPARISON_SCHEMA = "mindie-profiler-native-comparison/1"
NATIVE_RECEIPT_SCHEMA = "mindie-profiler-independent-native-receipt/1"


def independent_native_receipt(
    canonical: Mapping[str, Any],
    comparison: Mapping[str, Any],
    *,
    sources: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project canonical native pairing and comparison outputs into one receipt.

    This helper consumes ``compare_acceptance`` without re-matching items: the
    canonical comparison owns pairing, coverage, and per-item errors.  Every
    observed item, unpaired entry, prediction status, and explicit reason is
    retained without promoting work-only entries into timed samples.
    """

    reasons: list[str] = []
    if canonical.get("schema") != NATIVE_CANONICAL_SCHEMA:
        reasons.append("canonical_schema_invalid")
    if comparison.get("schema") != NATIVE_COMPARISON_SCHEMA:
        reasons.append("comparison_schema_invalid")
    canonical_counts = canonical.get("counts") if isinstance(canonical.get("counts"), Mapping) else {}
    comparison_counts = comparison.get("counts") if isinstance(comparison.get("counts"), Mapping) else {}
    for name, left, right in (
        ("observations", canonical_counts.get("observations"), comparison_counts.get("observations")),
        ("predictions", canonical_counts.get("predictions"), comparison_counts.get("predictions")),
        ("paired", canonical_counts.get("paired"), comparison_counts.get("paired")),
    ):
        if isinstance(left, int) and isinstance(right, int) and left != right:
            reasons.append(f"count_mismatch:{name}:{left}!={right}")

    items: list[dict[str, Any]] = []
    per_item_errors: list[dict[str, Any]] = []
    for item in comparison.get("items") or ():
        if not isinstance(item, Mapping):
            continue
        detail = item.get("comparison") if isinstance(item.get("comparison"), Mapping) else {}
        verdicts = [dict(row) for row in (detail.get("sample_verdicts") or ()) if isinstance(row, Mapping)]
        record = {
            "item_id": item.get("item_id"),
            "request_id": item.get("request_id"),
            "prediction_id": item.get("prediction_id"),
            "observed_ms": item.get("observed_ms"),
            "predicted_ms": item.get("predicted_ms"),
            "observation_ids": list(item.get("observation_ids") or ()),
            "observation_samples": item.get("observation_samples"),
            "observation_range_ms": list(item.get("observation_range_ms") or ()),
            "observation_clock_domains": list(item.get("observation_clock_domains") or ()),
            "observation_window_ids": list(item.get("observation_window_ids") or ()),
            "observation_abi_digest": item.get("observation_abi_digest"),
            "prediction_abi_digest": item.get("prediction_abi_digest"),
            "condition_gaps": list(item.get("condition_gaps") or ()),
            "status": item.get("status"),
            "comparison": {
                "duration_available": detail.get("duration_available"),
                "reason": detail.get("reason"),
                "formal_policy": detail.get("formal_policy"),
                "observation_duration_ms": detail.get("observation_duration_ms"),
            },
            "sample_verdicts": verdicts,
        }
        items.append(record)
        for verdict in verdicts:
            per_item_errors.append({
                "item_id": item.get("item_id"),
                "observation_id": verdict.get("observation_id"),
                "observed_ms": verdict.get("observed_ms"),
                "predicted_ms": item.get("predicted_ms"),
                "relative_error": verdict.get("relative_error"),
                "within_tolerance": verdict.get("within_tolerance"),
            })
        if not verdicts:
            per_item_errors.append({
                "item_id": item.get("item_id"),
                "observation_id": (record["observation_ids"] or [None])[0],
                "observed_ms": item.get("observed_ms"),
                "predicted_ms": item.get("predicted_ms"),
                "relative_error": None,
                "within_tolerance": None,
                "reason": detail.get("reason") or "no_predicted_duration",
            })

    unpaired_observations = list(canonical.get("unpaired_observations") or ())
    unpaired_predictions = list(canonical.get("unpaired_predictions") or ())
    prediction_states = [
        {"prediction_id": row.get("id"), "status": "unpaired", "reason": row.get("reason")}
        for row in unpaired_predictions if isinstance(row, Mapping)
    ]
    for item in items:
        prediction_states.append({
            "prediction_id": item.get("prediction_id"),
            "status": item.get("status"),
            "reason": (item.get("comparison") or {}).get("reason"),
        })
    receipt = {
        "schema": NATIVE_RECEIPT_SCHEMA,
        "status": canonical.get("status") if not reasons else "invalid_source",
        "canonical_status": canonical.get("status"),
        "comparison_status": comparison.get("status"),
        "native_qualification": {
            "status": canonical.get("status"),
            "production_entry": canonical.get("production_entry"),
            "source_discovery": canonical.get("source_discovery"),
            "t12_bridge_counts": canonical.get("t12_bridge_counts"),
            "t12_reasons": canonical.get("t12_reasons"),
        },
        "reasons": reasons,
        "counts": {
            "canonical": dict(canonical_counts),
            "comparison": dict(comparison_counts),
        },
        "coverage": dict(comparison.get("coverage") or {}),
        "items": items,
        "canonical_paired": list(canonical.get("paired") or ()),
        "per_item_errors": per_item_errors,
        "prediction_states": prediction_states,
        "unpaired_observations": unpaired_observations,
        "unpaired_predictions": unpaired_predictions,
        "ambiguous": list(comparison.get("ambiguous") or ()),
        "failure_matrix": list(comparison.get("failure_matrix") or ()),
        "non_claims": list(canonical.get("non_claims") or ()),
        "sources": dict(sources or {}),
        "interpretation": (
            "Canonical ABI pairing and coverage are authoritative.  No duration "
            "pair or per-item error is fabricated for work_only or unpaired items."
        ),
    }
    return receipt
