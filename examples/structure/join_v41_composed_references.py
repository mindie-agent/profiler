"""[Role] Join disjoint V4.1 native and normalized-cohort reference receipts.
[Invariants] Count each source Forward once; retain complete observation groups,
  individual cost provenance and strict=0. Neither input receipt is rewritten.
[Timeouts & Locks] Bounded local JSON only; no workers or locks.
[Side-Effect Policy] Write a separate report, without raw reads or new predictions.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from compare_glm_native_partitions import render
from replay_body_operator_families import identity, read, write


def join(native_path, normalized_path):
    paths = [Path(native_path), Path(normalized_path)]
    inputs = [read(path) for path in paths]
    pins = [identity(path) for path in paths]
    first, second = inputs
    if first["runtime_source_commit"] != second["runtime_source_commit"]:
        raise ValueError("reference_runtime_generations_differ")
    identities = dict(first["runtime_source_identity"])
    for path, digest in second["runtime_source_identity"].items():
        if path in identities and identities[path] != digest:
            raise ValueError("shared_reference_runtime_changed")
        identities[path] = digest
    right = {case["case_id"]: case for case in second["cases"]}
    if len(right) != len(second["cases"]) or set(right) != {c["case_id"] for c in first["cases"]}:
        raise ValueError("reference_source_populations_differ")
    cases = []
    for left in first["cases"]:
        other = right[left["case_id"]]
        for field in ("source_identity", "actual_identity", "case_identity", "geometry",
                      "conditional_context_tokens", "forward_count"):
            if left[field] != other[field]:
                raise ValueError("reference_population_join_differs:" + field)
        groups, keys = [], set()
        for arm, case in enumerate((left, other)):
            for group in case["groups"]:
                key = (group["native_operator_type"], group["declared_role"], tuple(group["layer_ids"]))
                if key in keys:
                    raise ValueError("overlapping_reference_observation_group")
                keys.add(key)
                groups.append({**group, "cost_receipt_identity": pins[arm],
                               "cost_receipt_case_id": case["case_id"]})
        unresolved = left["unresolved"] + other["unresolved"]
        cases.append({**left, "status": "partial" if unresolved else "completed",
            "groups": groups, "unresolved": unresolved,
            "native_event_count": left["native_event_count"] + other["native_event_count"],
            "referenced_event_count": sum(g["observed_us"]["count"] for g in groups),
            "runtime_source_identity": identities,
            "input_reference_receipts": pins,
            "coverage": {"native_groups": len(left["groups"]),
                "normalized_cohort_groups": len(other["groups"]),
                "forward_population_counted_once": True,
                "other_retained_rotary_cache_populations_included": False},
            "execution": {"raw_capture_reads": 0, "new_program_sets": 0,
                "saved_cost_receipts_joined": True,
                "antecedent_new_program_sets": sum(c["execution"]["new_program_sets"] for c in (left, other)),
                "maximum_resident_set_size_bytes": max(c["execution"]["maximum_resident_set_size_bytes"] for c in (left, other))}})
    return {"schema_version": "mindie-native-body-reference-batch/1",
        "status": "completed" if all(c["status"] == "completed" for c in cases) else "partial",
        "runtime_source_commit": first["runtime_source_commit"], "runtime_source_identity": identities,
        "cases": cases, "input_reference_receipts": pins,
        "raw_capture_reads": 0, "strict_compared": 0, "new_predictions_in_join": 0,
        "generator_identity": identity(Path(__file__)),
        "limitations": ["Native ABI and normalized-cohort references retain distinct evidence levels.",
            "All rows are conditional references, not strict accuracy or layer-occurrence bindings.",
            "Measured activity and predicted service residuals cannot be summed as Body wall-time error.",
            "The original seventy-group and twenty-eight-group cost receipts remain immutable."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-report", type=Path, required=True)
    parser.add_argument("--normalized-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = join(args.native_report, args.normalized_report)
    write(args.output, report)
    rendered = render(report).replace("No raw capture scan or old cost reuse.",
        "This report joins two completed same-runtime cost receipts; it performs no raw scan or new prediction.")
    args.output.with_suffix(".md").write_text(rendered)


if __name__ == "__main__":
    main()
