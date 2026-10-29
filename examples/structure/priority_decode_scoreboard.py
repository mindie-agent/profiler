"""Render body, layer and operator receipts without changing their measurements.

[Role] Put completed Decode comparisons and millisecond priorities on one page.
[Invariants] A kernel activity residual is not a causal wall-clock attribution.
  Missing matches are coverage gaps, not zero predictions or proven missing cost.
  Runtime, source and geometry identities remain attached to each comparison.
[Timeouts & Locks] Serial bounded JSON reads, no prediction subprocess or locks.
[Side-Effect Policy] Read local receipts and write the requested JSON/Markdown.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def _read(path):
    if path.stat().st_size > 50 * 1024 ** 2:
        raise ValueError(f"receipt exceeds bounded read limit: {path}")
    raw = path.read_bytes()
    return json.loads(raw), {"path": str(path.resolve()), "sha256": hashlib.sha256(raw).hexdigest()}


def _family(case_id):
    name = case_id.lower()
    for key, label in (("kimi", "Kimi-K3"), ("glm", "GLM-5.3"),
                       ("v41", "DeepSeek-V4.1-Flash"), ("v4", "DeepSeek-V4-Flash"),
                       ("qwen", "Qwen")):
        if key in name:
            return label
    return "other"


def _runtime_identity(receipt):
    sources = receipt.get("runtime_source_identity", {})
    sim = {path.split("/mindie_sim/", 1)[1]: digest for path, digest in sources.items()
           if "/mindie_sim/" in path}
    return {"recorded_sim_file_map_sha256": hashlib.sha256(
                json.dumps(sim, sort_keys=True).encode()).hexdigest() if sim else None,
            "recorded_sim_file_count": len(sim),
            "sources_unchanged": receipt.get("runtime_sources_unchanged"),
            "basis": "recorded_relative_sim_file_hash_map; full_receipt_retains_source_paths"}


def body_rows(receipt, identity):
    result = []
    for case in receipt["cases"]:
        comparison = case["comparison"]
        observed = case.get("observed", {})
        layers = case.get("per_layer_comparison") or {}
        row = {"model_group": _family(case["case_id"]), "case_id": case["case_id"],
               "variant_id": case.get("variant_id", receipt.get("variant_id")),
               "receipt": identity, "source_identity": case.get("source_identity"),
               "runtime_identity": case.get("runtime_identity"), "geometry": case.get("geometry"),
               "declared_runtime": case.get("declared_runtime"), "comparison": comparison,
               "display_status": ("prediction_deferred" if "prediction_deferred_by_population_priority"
                                  in comparison.get("reasons", []) else comparison["status"]),
               "body_activity_ms": observed.get("body_activity_ms"),
               "body_internal_gap_ms": observed.get("body_internal_gap_ms"),
               "per_layer": layers}
        result.append(row)
    return result


def operator_rows(receipt, identity):
    families, cohorts = [], []
    for case in receipt["cases"]:
        count = case["forward_count"]
        if count <= 0:
            raise ValueError("operator receipt has no complete body denominator")
        base = {"model_group": _family(case["case_id"]), "case_id": case["case_id"],
                "receipt": identity, "source_identity": case.get("source_identity"),
                "runtime_identity": _runtime_identity(receipt),
                "geometry": case.get("geometry"), "forward_count": count,
                "case_identity": case.get("case_identity")}
        for family in case["families"]:
            observed = family["observed_us"]
            measured_us = observed["count"] * observed["mean"]
            scored_us = sum(row["observed"]["complete_activity_sum_ns"] / 1000
                            for row in family.get("cohorts", []) if row["status"] == "compared")
            if scored_us > measured_us + 1e-6:
                raise ValueError("scored cohort activity exceeds its measured family")
            families.append({**base, **{key: family.get(key) for key in (
                "native_operator_type", "declared_role", "status", "evidence_strength",
                "observed_us", "scored_event_count", "unscored_event_count",
                "passed_cohort_count", "compared_cohort_count", "cohort_reasons")},
                "measured_activity_ms_per_forward": measured_us / count / 1000,
                "unscored_activity_ms_per_forward": max(0, measured_us - scored_us) / count / 1000,
                "missing_match_is_missing_cost": False})
            for cohort in family.get("cohorts", []):
                calls = cohort["observed"]["complete_event_count"]
                mean = cohort.get("observed_per_call_us")
                predicted = cohort.get("predicted_per_call_us")
                if mean is None or predicted is None:
                    continue
                diff = (predicted - mean) * calls / count / 1000
                cohorts.append({**base, "cohort_id": cohort["cohort_id"],
                    "native_operator_type": family["native_operator_type"],
                    "declared_role": family["declared_role"], "status": cohort["status"],
                    "physical_signature": cohort["physical_signature"], "observed_calls": calls,
                    "observed_us": mean, "predicted_us": predicted,
                    "per_call_diff_us": predicted - mean,
                    "measured_activity_ms_per_forward": mean * calls / count / 1000,
                    "predicted_activity_ms_per_forward": predicted * calls / count / 1000,
                    "signed_activity_residual_ms_per_forward": diff,
                    "absolute_activity_residual_ms_per_forward": abs(diff),
                    "heavy_call": mean > 50, "accuracy_pass": cohort.get("accuracy_pass"),
                    "accuracy_tier": cohort.get("accuracy_tier"),
                    "interpretation": "nonadditive_activity_priority_not_causal_body_error_contribution"})
    return families, cohorts


def build(body_paths, operator_paths, reference_paths=(), evidence_paths=()):
    bodies, families, cohorts, references, inputs = [], [], [], [], []
    for path in body_paths:
        receipt, identity = _read(path)
        inputs.append(identity)
        bodies.extend(body_rows(receipt, identity))
    for path in operator_paths:
        receipt, identity = _read(path)
        inputs.append(identity)
        actual, compared = operator_rows(receipt, identity)
        families.extend(actual)
        cohorts.extend(compared)
    for path in reference_paths:
        receipt, identity = _read(path)
        inputs.append(identity)
        for case in receipt["cases"]:
            for item in [*case["groups"], *case["source_role_gap_references"]]:
                observed = item.get("observed_activity_ms_per_forward")
                predicted = item.get("predicted_service_ms_per_forward")
                references.append({"case_id": case["case_id"], "receipt": identity,
                    "runtime_identity": _runtime_identity(receipt),
                    "source_identity": case["source_identity"], **{key: item.get(key) for key in (
                        "native_operator_type", "attention_kind", "block", "declared_roles", "status",
                        "observed_us", "predicted_us", "predicted_reference_us", "evidence_strength",
                        "model_program_already_costed", "additional_budget_allowed", "reason")},
                    "observed_activity_ms_per_forward": observed,
                    "predicted_service_ms_per_forward": predicted,
                    "reference_residual_ms_per_forward": predicted - observed if predicted is not None else None,
                    "scored": False})
    bodies.sort(key=lambda row: abs(row["comparison"].get("per_forward_diff_ms") or 0), reverse=True)
    cohorts.sort(key=lambda row: row["absolute_activity_residual_ms_per_forward"], reverse=True)
    families.sort(key=lambda row: row["measured_activity_ms_per_forward"], reverse=True)
    evidence = []
    for path in evidence_paths:
        _, identity = _read(path)
        evidence.append(identity)
    populations = {}
    for row in bodies:
        geometry, source = row["geometry"] or {}, row["source_identity"] or {}
        key = (source.get("sha256"), geometry.get("query_rows"),
               geometry.get("tokens_per_sequence"), geometry.get("sequences_per_replica"))
        observed = row["comparison"]["observed_ms"]
        if key in populations and populations[key] != observed:
            raise ValueError("different measured populations share a source/geometry identity")
        populations[key] = observed
    tiers = {}
    for heavy, label in ((True, "heavy_relative_15pct"), (False, "micro_absolute_15us")):
        selected = [row for row in cohorts if row["status"] == "compared" and row["heavy_call"] == heavy]
        tiers[label] = {"compared": len(selected), "passed": sum(row["accuracy_pass"] is True for row in selected)}
    return {"schema_version": "mindie-priority-decode-scoreboard/1",
            "coverage_status": "partial" if (not cohorts or any(row["comparison"]["status"] != "compared" for row in bodies)
                                                or any(row.get("unscored_event_count") for row in families)) else "compared",
            "inputs": inputs, "additional_evidence": evidence,
            "body_comparisons": bodies, "operator_families": families, "operator_cohorts": cohorts,
            "source_role_references": references,
            "summary": {"body_compared": sum(row["comparison"]["status"] == "compared" for row in bodies),
                        "body_passed": sum(row["comparison"].get("passed") is True for row in bodies),
                        "body_denominator": "prediction_variants; identical observed populations are not additional captures",
                        "unique_source_count": len({key[0] for key in populations}),
                        "unique_source_geometry_populations": len(populations),
                        "unique_observed_forward_count": sum(item["count"] for item in populations.values()),
                        "operator_status_counts": dict(Counter(row["status"] for row in cohorts)),
                        "operator_accuracy_by_tier": tiers,
                        "heavy_cohorts": sum(row["heavy_call"] for row in cohorts)},
            "limitations": [
                "Rows retain their own source/runtime/geometry; independently produced receipts are not merged into a synthetic run.",
                "Per-forward kernel activity residual ranks work to investigate; overlap prevents interpreting its sum as body wall-clock error.",
                "Unscored activity is a matching/model-boundary coverage gap, not proof that Sim omitted the corresponding work.",
                "Layer median-of-call-P50 and exact pooled P50 are distinct populations."]}


def _num(value, digits=3):
    return "—" if value is None else f"{value:.{digits}f}"


def _runtime_tag(row):
    identity = row.get("runtime_identity") or {}
    return (identity.get("package_sha256") or identity.get("recorded_sim_file_map_sha256") or "unknown")[:12]


def render(report):
    summary = report["summary"]
    lines = ["# Priority Decode body, layer and operator scoreboard", "",
             f"Coverage status: **{report['coverage_status']}**. Missing predictions and unmatched roles stay visible.", "",
             f"Body: **{summary['body_passed']}/{summary['body_compared']} prediction arms passed**; "
             f"{summary['unique_source_count']} unique sources, {summary['unique_source_geometry_populations']} measured geometry populations, "
             f"{summary['unique_observed_forward_count']} unique complete Forwards (includes deferred populations).", "",
             "Operator strict accuracy: " + "; ".join(f"{key}: **{value['passed']}/{value['compared']}**"
                 for key, value in summary["operator_accuracy_by_tier"].items()) + ". Conditional references are excluded.", "",
             "Local replay receipts with explicit comparison coverage. Body errors are measured wall-clock differences; "
             "operator priorities are nonadditive kernel activity residuals per complete Forward.", "",
             "## Whole Decode Body — sorted by absolute ms error", "",
             "| Case / variant | Status | Calls | Real Mean / P50 / P90 ms | Activity ms | Sim ms | Diff ms | Error |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in report["body_comparisons"]:
        comp, activity = row["comparison"], row["body_activity_ms"] or {}
        observed = comp["observed_ms"]
        error = comp.get("relative_error")
        lines.append(f"| {row['case_id']} / {row['variant_id']} / `{_runtime_tag(row)}` | {row['display_status']} | {observed['count']} | "
                     f"{_num(observed['mean'])} / {_num(observed['p50'])} / {_num(observed['p90'])} | "
                     f"{_num(activity.get('mean'))} | {_num(comp.get('predicted_ms'))} | "
                     f"{_num(comp.get('per_forward_diff_ms'))} | {_num(error * 100 if error is not None else None)}% |")
    lines += ["", "## Layer 0 and steady layer groups", "",
              "The steady P50 column is median of per-layer call P50, unless a separately linked receipt supplies exact pooled statistics.", "",
              "| Case | Group | Layers | Real Mean ms | Median layer-call P50 ms | Sim Mean ms | Mean error |",
              "|---|---|---:|---:|---:|---:|---:|"]
    from statistics import median
    for row in report["body_comparisons"]:
        groups = {}
        for layer in row["per_layer"].get("layers", []):
            key = ("Layer 0" if layer["layer_id"] == 0 else "Steady", layer.get("attention_kind"), layer["kind"])
            groups.setdefault(key, []).append(layer)
        for key, values in groups.items():
            observed = sum(item["observed_ms"]["mean"] for item in values) / len(values)
            p50 = median(item["observed_ms"]["p50"] for item in values)
            preds = [item.get("predicted_ms") for item in values]
            pred = sum(preds) / len(preds) if all(value is not None for value in preds) else None
            error = (pred / observed - 1) * 100 if pred is not None and observed else None
            lines.append(f"| {row['case_id']} / {row['variant_id']} | {' / '.join(str(part) for part in key)} | {len(values)} | "
                         f"{observed:.4f} | {p50:.4f} | {_num(pred, 4)} | {_num(error)}% |")
    for heavy in (True, False):
        lines += ["", f"## {'Heavy >50us' if heavy else 'Micro <=50us'} operators — activity residual priority", "",
                  "| Case | Operator / role | Calls | Real / Sim us | Diff us | Absolute ms / Forward | Tier pass |",
                  "|---|---|---:|---:|---:|---:|---|"]
        selected = [row for row in report["operator_cohorts"] if row["heavy_call"] == heavy]
        for row in selected[:40]:
            lines.append(f"| {row['case_id']} / `{_runtime_tag(row)}` | {row['native_operator_type']} / {row['declared_role']} | "
                         f"{row['observed_calls']} | {row['observed_us']:.3f} / {row['predicted_us']:.3f} | "
                         f"{row['per_call_diff_us']:.3f} | {row['absolute_activity_residual_ms_per_forward']:.3f} | "
                         f"{row['accuracy_pass']} ({row['status']}) |")
    lines += ["", "## Highest unscored activity — coverage gaps, not zero predictions", "",
              "| Case | Operator / role | Unscored calls | Unscored observed activity ms / Forward | Status |",
              "|---|---|---:|---:|---|"]
    gaps = sorted((item for item in report["operator_families"] if item.get("unscored_event_count")),
                  key=lambda row: row["unscored_activity_ms_per_forward"], reverse=True)
    for row in gaps[:40]:
        lines.append(f"| {row['case_id']} | {row['native_operator_type']} / {row['declared_role']} | "
                     f"{row['unscored_event_count']} | {row['unscored_activity_ms_per_forward']:.3f} | {row['status']} |")
    lines += ["", "## Source-role references — already costed work is not an extra budget", "",
              "Reference differences have distinct evidence and are excluded from strict cohort accuracy counts.", "",
              "| Case | Operator / region | Real / reference us | Real / Sim service ms per Forward | Residual ms | Boundary |",
              "|---|---|---:|---:|---:|---|"]
    references = sorted(report["source_role_references"],
                        key=lambda row: abs(row["reference_residual_ms_per_forward"] or 0), reverse=True)
    for row in references:
        prediction = row["predicted_us"] if row["predicted_us"] is not None else row["predicted_reference_us"]
        lines.append(f"| {row['case_id']} / `{_runtime_tag(row)}` | {row['native_operator_type']} / {row['attention_kind']} / {row['block']} | "
                     f"{_num(row['observed_us']['mean'])} / {_num(prediction)} | "
                     f"{_num(row['observed_activity_ms_per_forward'])} / {_num(row['predicted_service_ms_per_forward'])} | "
                     f"{_num(row['reference_residual_ms_per_forward'])} | {row['status']} |")
    lines += ["", "## Receipt identities", ""]
    lines += [f"- [{Path(item['path']).name}]({item['path']}), SHA256 `{item['sha256']}`" for item in report["inputs"]]
    if report["additional_evidence"]:
        lines += ["", "Additional coverage/source evidence (not silently promoted into body or operator predictions):", ""]
        lines += [f"- [{Path(item['path']).name}]({item['path']}), SHA256 `{item['sha256']}`" for item in report["additional_evidence"]]
    lines += ["", *[f"- {text}" for text in report["limitations"]], ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body", type=Path, action="append", default=[])
    parser.add_argument("--operators", type=Path, action="append", default=[])
    parser.add_argument("--references", type=Path, action="append", default=[])
    parser.add_argument("--evidence", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.body, args.operators, args.references, args.evidence)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    args.output.with_suffix(".md").write_text(render(report))
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    main()
