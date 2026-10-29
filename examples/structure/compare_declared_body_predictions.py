"""Join completed declared-body costs to subsequently measured source windows.

[Role] Reuse an existing runtime arm without running a new predictor.
[Invariants] Case bytes and q/B/context must match the completed cost receipt.
  Recorded runtime identity stays historical; current source is not its runtime.
[Timeouts & Locks] Streaming source identity verification; no cost worker or lock.
[Side-Effect Policy] Reads retained local artifacts and writes a comparison report.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from body_forward_comparison import compare_body_forward, compare_layers
from replay_decode_forwards import _read, render, replay_manifest, sha256_file


def compare(manifest_path, saved_path, extraction_dir):
    manifest = _read(manifest_path)
    saved = _read(saved_path)
    predictions = {row["case_id"]: row for row in saved["cases"]}
    report = replay_manifest(manifest, base=manifest_path.parent, run_predictions=False,
                             reuse_extractions=extraction_dir)
    for row in report["cases"]:
        if row["status"] == "failed":
            continue
        source_id = row.get("source_case_id", row["case_id"])
        previous = predictions[source_id]
        if row["model_structure_identity"]["sha256"] != previous["case_identity"]["sha256"]:
            raise ValueError(f"Saved body cost uses different case bytes: {source_id}")
        for field, expected in previous["geometry"].items():
            if row["geometry"].get(field) != expected:
                raise ValueError(f"Saved body cost uses different {field}: {source_id}")
        worker = previous["prediction_execution"]
        if worker["status"] != "completed" or not worker["runtime_identity"]["sources_unchanged"]:
            raise ValueError(f"Saved body cost did not complete on unchanged source: {source_id}")
        predicted = previous["prediction"]
        row["prediction"] = predicted
        row["prediction_execution"] = {
            **worker, "reused_prediction": True,
            "reused_prediction_reference": {"path": str(saved_path), "sha256": sha256_file(saved_path)},
            "new_prediction_in_this_execution": False,
        }
        row["runtime_identity"] = worker["runtime_identity"]
        row["comparison"] = compare_body_forward(predicted, row["observed"])
        row["status"] = row["comparison"]["status"]
        row["per_layer_comparison"] = compare_layers(predicted, row["observed"])
        row["declared_coverage"] = previous["declared_coverage"]
    counts = Counter(row["status"] for row in report["cases"])
    report["summary"].update(compared_cases=counts["compared"], unresolved_cases=counts["unresolved"],
                             failed_cases=counts["failed"],
                             passed_cases=sum(row["comparison"]["passed"] is True for row in report["cases"]))
    report["runtime_provenance"] = {"source_commit": saved["runtime_source_commit"],
                                     "basis": "previously completed cost receipt; no new simulation",
                                     "new_prediction_workers": 0}
    report["manifest_identity"] = {"path": str(manifest_path), "sha256": sha256_file(manifest_path)}
    report["saved_prediction_identity"] = {"path": str(saved_path), "sha256": sha256_file(saved_path)}
    report["limitations"].append("Native MQSMLA implementation remains unmodeled in this historical analytic arm; measured native attention remains included in the complete body span.")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--extractions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.manifest, args.predictions, args.extractions)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.output.with_suffix(".md").write_text(render(report))
    print(json.dumps({"summary": report["summary"], "sha256": sha256_file(args.output)}))
