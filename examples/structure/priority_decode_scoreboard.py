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
import resource
import sys
import time


def _receipt_parts(path):
    """Read one case at a time; the native-cohort receipts carry large ABIs."""
    from mindie_profiler.sources_trace import _JsonStream
    with _JsonStream(path) as reader:
        reader.expect("{")
        while reader.peek() != "}":
            key = reader.value()
            reader.expect(":")
            if key == "cases":
                for case in reader.iter_array():
                    yield "case", case
            else:
                yield key, reader.value()
            if reader.peek() == ",":
                reader.expect(",")
            elif reader.peek() != "}":
                reader.expect("}")
        reader.expect("}")


def _operator_metadata(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    metadata = {key: value for key, value in _receipt_parts(path) if key != "case"}
    return metadata, {"path": str(path.resolve()), "sha256": digest.hexdigest()}


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


def _population(row):
    geometry, source = row.get("geometry") or {}, row.get("source_identity") or {}
    return (source.get("sha256"), geometry.get("query_rows"),
            geometry.get("tokens_per_sequence"), geometry.get("sequences_per_replica"))


def native_reference_rows(case, identity):
    """Keep each retained full-ABI histogram separate from strict cohorts."""
    rows = []
    for group in case["groups"]:
        if (group["prediction_status"] != "reference_only"
                or group["strict_accuracy_implied"]
                or group["additional_budget_allowed"]):
            raise ValueError("native source references cannot imply strict accuracy or extra work")
        observed = group["observed_activity_ms_per_forward"]
        predicted = group["predicted_service_ms_per_forward"]
        rows.append({
            "case_id": case["case_id"], "receipt": identity,
            "reference_origin": "external_native_partition",
            "runtime_identity": _runtime_identity(case),
            "source_identity": case["source_identity"], "geometry": case["geometry"],
            "case_identity": case["case_identity"], "partition_identity": case["partition_identity"],
            "group_id": group["group_id"], "partition_index": group["partition_index"],
            "native_abi_sha256": hashlib.sha256(json.dumps(
                group["native_abi"], sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "forward_count": case["forward_count"], "calls_per_forward": group["calls_per_forward"],
            "native_operator_type": group["native_operator_type"],
            "attention_kind": group.get("attention_kind"), "block": group.get("block"),
            "declared_roles": [group["declared_role"]], "layer_ids": group["layer_ids"],
            "status": "reference_only", "evidence_strength": "complete_native_abi_conditional_program_reference",
            "observed_us": group["observed_us"], "predicted_us": None,
            "predicted_reference_us": group["predicted_reference_us"],
            "observed_activity_ms_per_forward": observed,
            "predicted_service_ms_per_forward": predicted,
            "reference_residual_ms_per_forward": predicted - observed,
            "model_program_already_costed": True, "additional_budget_allowed": False,
            "boundary": group["reference_boundary"], "conditions": group["conditions"],
            "source_correspondence": group["source_correspondence"],
            "physical_program_signatures": group["physical_program_signatures"],
            "scored": False})
    return rows


def select_references(references, operator_selection):
    """Reference generations are selected independently, never by residual."""
    other, current = [], {}
    for row in references:
        population = _population(row)
        if row.get("reference_origin") != "external_native_partition":
            selected = operator_selection.get(population)
            if selected and (row["receipt"]["sha256"], row["case_id"]) != selected[1:]:
                continue
            other.append(row)
        else:
            key = (population, row["native_operator_type"],
                   tuple(sorted(row["declared_roles"])), tuple(sorted(row["layer_ids"])),
                   row["native_abi_sha256"])
            current[key] = row
    return other + list(current.values())


def body_rows(receipt, identity):
    result = []
    for case in receipt["cases"]:
        comparison = case["comparison"]
        observed = case.get("observed") or {}
        layers = case.get("per_layer_comparison") or {}
        row = {"model_group": _family(case["case_id"]), "case_id": case["case_id"],
               "variant_id": case.get("variant_id", receipt.get("variant_id")),
               "receipt": identity, "source_identity": case.get("source_identity"),
               "runtime_identity": case.get("runtime_identity"), "geometry": case.get("geometry"),
               "declared_runtime": case.get("declared_runtime"), "comparison": comparison,
               "error": case.get("error"),
               "prediction_failure": (case.get("prediction_execution")
                                      if comparison["status"] == "failed" else None),
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


def body_history_row(row):
    """Keep every historical arm without copying its full layer table again."""
    layers = row["per_layer"]
    return {**{key: value for key, value in row.items() if key != "per_layer"},
            "per_layer_reference": {
                "receipt_sha256": row["receipt"]["sha256"], "case_id": row["case_id"],
                "field": "per_layer_comparison",
                "sha256": hashlib.sha256(json.dumps(layers, sort_keys=True).encode()).hexdigest()}}


def build(body_paths, operator_paths, reference_paths=(), evidence_paths=(), invalidation_paths=()):
    bodies, families, cohorts, references, inputs = [], [], [], [], []
    invalidations = {}
    for path in invalidation_paths:
        receipt, identity = _read(path)
        inputs.append(identity)
        for item in receipt["invalidated_body_receipts"]:
            invalidations[item["sha256"]] = {"receipt": identity, "reason": receipt["reason"],
                                           "status": receipt["status"]}
    for path in body_paths:
        receipt, identity = _read(path)
        inputs.append(identity)
        rows = body_rows(receipt, identity)
        invalidation = invalidations.get(identity["sha256"])
        for row in rows:
            if invalidation:
                row["prediction_invalidation"] = invalidation
                row["original_comparison"] = row["comparison"]
                row["comparison"] = {**row["comparison"], "status": invalidation["status"],
                                     "passed": None, "predicted_ms": None,
                                     "per_forward_diff_ms": None, "relative_error": None}
                row["display_status"] = invalidation["status"]
        bodies.extend(rows)
    for path in operator_paths:
        receipt, identity = _operator_metadata(path)
        inputs.append(identity)
        for key, case in _receipt_parts(path):
            if key != "case":
                continue
            actual, compared = operator_rows({**receipt, "cases": [case]}, identity)
            families.extend(actual)
            cohorts.extend(compared)
            for family in case["families"]:
                for group in family.get("conditional_source_role_references", ()):
                    observed = group.get("observed_activity_ms_per_forward")
                    predicted = group.get("predicted_service_ms_per_forward")
                    references.append({
                        "case_id": case["case_id"], "receipt": identity,
                        "runtime_identity": _runtime_identity(receipt),
                        "source_identity": case["source_identity"], "geometry": case["geometry"],
                        "native_operator_type": group["native_operator_type"],
                        "attention_kind": group["attention_kind"], "block": group.get("block"),
                        "declared_roles": [group["declared_role"]], "layer_ids": group["layer_ids"],
                        "status": group["prediction_status"], "evidence_strength": group["evidence_strength"],
                        "observed_us": group["observed_us"], "predicted_us": None,
                        "predicted_reference_us": group.get("predicted_reference_us"),
                        "observed_activity_ms_per_forward": observed,
                        "predicted_service_ms_per_forward": predicted,
                        "reference_residual_ms_per_forward": predicted - observed if predicted is not None else None,
                        "model_program_already_costed": True, "additional_budget_allowed": False,
                        "boundary": group.get("boundary"), "conditions": group.get("conditions"),
                        "source_correspondence": group.get("source_correspondence"),
                        "physical_program_signatures": group["physical_program_signatures"], "scored": False})
    for path in reference_paths:
        receipt, identity = _read(path)
        inputs.append(identity)
        for case in receipt["cases"]:
            if receipt.get("schema_version") == "mindie-glm-native-reference-batch/1":
                references.extend(native_reference_rows(case, identity))
                continue
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
    current, latest_attempts = {}, {}
    for row in bodies:
        if (row["comparison"]["status"] in {"compared", "failed"}
                and row["comparison"]["observed_ms"]["count"]):
            latest_attempts[_population(row)] = row
        if row["comparison"]["status"] == "failed":
            continue
        key = _population(row)
        # CLI receipt order explicitly selects the latest completed arm. A
        # deferred population never erases an earlier completed prediction.
        if key not in current or row["comparison"]["status"] == "compared":
            current[key] = row
    current_rows = sorted(current.values(), key=lambda row: abs(
        row["comparison"].get("per_forward_diff_ms") or 0), reverse=True)
    bodies.sort(key=lambda row: abs(row["comparison"].get("per_forward_diff_ms") or 0), reverse=True)
    cohorts.sort(key=lambda row: row["absolute_activity_residual_ms_per_forward"], reverse=True)
    operator_selection = {}
    for row in families:
        # Input order, rather than activity rank, chooses the current program.
        rank = next(i for i, item in enumerate(inputs) if item == row["receipt"])
        key = _population(row)
        if key not in operator_selection or rank >= operator_selection[key][0]:
            operator_selection[key] = (rank, row["receipt"]["sha256"], row["case_id"])
    def selected_operator(row):
        selected = operator_selection[_population(row)]
        return (row["receipt"]["sha256"], row["case_id"]) == selected[1:]
    current_families = [row for row in families if selected_operator(row)]
    current_cohorts = [row for row in cohorts if selected_operator(row)]
    operator_runtimes = {
        _population(row): row["runtime_identity"]["recorded_sim_file_map_sha256"] or "unknown"
        for row in current_families
    }
    current_references = select_references(references, operator_selection)
    native_references = [row for row in current_references
                         if row.get("reference_origin") == "external_native_partition"]
    native_populations = {_population(row): row["forward_count"] for row in native_references}
    families.sort(key=lambda row: row["measured_activity_ms_per_forward"], reverse=True)
    current_families.sort(key=lambda row: row["measured_activity_ms_per_forward"], reverse=True)
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
        if not observed["count"]:
            continue
        if key in populations and populations[key] != observed:
            raise ValueError("different measured populations share a source/geometry identity")
        populations[key] = observed
    tiers = {}
    for heavy, label in ((True, "heavy_relative_15pct"), (False, "micro_absolute_15us")):
        selected = [row for row in current_cohorts if row["status"] == "compared" and row["heavy_call"] == heavy]
        tiers[label] = {"compared": len(selected), "passed": sum(row["accuracy_pass"] is True for row in selected)}
    history = [body_history_row(row) for row in bodies]
    return {"schema_version": "mindie-priority-decode-scoreboard/1",
            "coverage_status": "partial" if (not cohorts or any(row["comparison"]["status"] != "compared" for row in bodies)
                                                or any(row.get("unscored_event_count") for row in families)) else "compared",
            "inputs": inputs, "additional_evidence": evidence,
            "body_comparisons": history, "operator_families": families, "operator_cohorts": cohorts,
            "body_history_layer_storage": "source receipt field and content hash; current layer tables are expanded below",
            "current_body_comparisons": current_rows,
            "latest_body_attempts": [body_history_row(row) for row in latest_attempts.values()],
            "body_failed_attempts": [row for row in history if row["comparison"]["status"] == "failed"],
            "current_operator_families": current_families, "current_operator_cohorts": current_cohorts,
            "current_selection_policy": "last compared input receipt per source and measured geometry; prior arms retained",
            "source_role_references": references,
            "current_source_role_references": current_references,
            "reference_selection_policy": "last external native input per source/geometry/native operator/role/layer set/observed ABI; embedded references retain operator receipt selection",
            "summary": {"body_compared": sum(row["comparison"]["status"] == "compared" for row in bodies),
                        "body_passed": sum(row["comparison"].get("passed") is True for row in bodies),
                        "current_body_compared": sum(row["comparison"]["status"] == "compared" for row in current_rows),
                        "current_body_passed": sum(row["comparison"].get("passed") is True for row in current_rows),
                        "invalidated_body_prediction_arms": sum("prediction_invalidation" in row for row in bodies),
                        "body_failed_attempts": sum(row["comparison"]["status"] == "failed" for row in bodies),
                        "latest_body_attempt_count": len(latest_attempts),
                        "latest_body_attempt_completed": sum(row["comparison"]["status"] == "compared" for row in latest_attempts.values()),
                        "latest_body_attempt_failed": sum(row["comparison"]["status"] == "failed" for row in latest_attempts.values()),
                        "latest_body_attempt_passed": sum(row["comparison"].get("passed") is True for row in latest_attempts.values()),
                        "body_denominator": "prediction_variants; identical observed populations are not additional captures",
                        "unique_source_count": len({key[0] for key in populations}),
                        "unique_source_geometry_populations": len(populations),
                        "unique_observed_forward_count": sum(item["count"] for item in populations.values()),
                        "operator_status_counts": dict(Counter(row["status"] for row in cohorts)),
                        "operator_accuracy_by_tier": tiers,
                        "current_operator_source_populations": len(operator_selection),
                        "current_operator_runtime_populations": dict(Counter(operator_runtimes.values())),
                        "current_operator_scored_events": sum(row.get("scored_event_count") or 0 for row in current_families),
                        "current_operator_body_events": sum(row["observed_us"]["count"] for row in current_families),
                        "current_external_native_reference_groups": len(native_references),
                        "current_external_native_reference_calls": sum(row["observed_us"]["count"] for row in native_references),
                        "current_external_native_reference_populations": len(native_populations),
                        "current_external_native_reference_forwards": sum(native_populations.values()),
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
             f"Current selected Body arms: **{summary['current_body_passed']}/{summary['current_body_compared']} passed**. "
             "One latest completed receipt per measured source/geometry, selected in input order; each row retains its own runtime and case.", "",
             f"Latest attempted Body arms: **{summary['latest_body_attempt_completed']}/{summary['latest_body_attempt_count']} completed**, "
             f"**{summary['latest_body_attempt_failed']} failed**, **{summary['latest_body_attempt_passed']} passed**. "
             "An earlier completed prediction remains available above when the newest attempt fails; it is not a successful new replay.", "",
             f"Body: **{summary['body_passed']}/{summary['body_compared']} prediction arms passed**; "
             f"{summary['unique_source_count']} unique sources, {summary['unique_source_geometry_populations']} measured geometry populations, "
             f"{summary['unique_observed_forward_count']} unique complete Forwards (includes deferred populations).", "",
             f"Invalidated prediction rows: **{summary['invalidated_body_prediction_arms']}**. Their measured populations remain; "
             "superseded predictions and layer errors are excluded from accuracy statistics.", "",
             "Current operator strict accuracy (latest input receipt per source/geometry): " + "; ".join(f"{key}: **{value['passed']}/{value['compared']}**"
                 for key, value in summary["operator_accuracy_by_tier"].items()) + ". Conditional references are excluded.", "",
             "Operator runtime coverage (recorded Sim file-map hash → source/geometry populations): " + "; ".join(
                 f"`{digest[:12]}` → {count}" for digest, count in summary["current_operator_runtime_populations"].items())
                 + ". Scores retain the latest available receipt for each population; this aggregate can contain different runtimes.", "",
             f"Strict event coverage: **{summary['current_operator_scored_events']:,}/{summary['current_operator_body_events']:,}** "
             f"events across {summary['current_operator_source_populations']} measured source/geometry populations. "
             "A high pass rate within this subset does not establish whole-model accuracy.", "",
             "Local replay receipts with explicit comparison coverage. Body errors are measured wall-clock differences; "
             "operator priorities are nonadditive kernel activity residuals per complete Forward.", "",
             "## Whole Decode Body — sorted by absolute ms error", "",
             "| Case / variant | Status | Calls | Real Mean / P50 / P90 ms | Activity ms | Sim ms | Diff ms | Mean / P50 error |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in report["current_body_comparisons"]:
        comp, activity = row["comparison"], row["body_activity_ms"] or {}
        observed = comp["observed_ms"]
        error = comp.get("relative_error")
        p50_error = ((comp["predicted_ms"] / observed["p50"] - 1) * 100
                     if comp.get("predicted_ms") is not None and observed["p50"] else None)
        lines.append(f"| {row['case_id']} / {row['variant_id']} / `{_runtime_tag(row)}` | {row['display_status']} | {observed['count']} | "
                     f"{_num(observed['mean'])} / {_num(observed['p50'])} / {_num(observed['p90'])} | "
                     f"{_num(activity.get('mean'))} | {_num(comp.get('predicted_ms'))} | "
                     f"{_num(comp.get('per_forward_diff_ms'))} | {_num(error * 100 if error is not None else None)}% / {_num(p50_error)}% |")
    if report["body_failed_attempts"]:
        lines += ["", "### Failed local replay attempts", "",
                  "Failed attempts remain visible. Input failures do not create measured populations; prediction failures retain completed observations.", "",
                  "| Case | Failure | Later source comparison present |", "|---|---|---|"]
        completed_sources = {row["source_identity"]["sha256"] for row in report["current_body_comparisons"]
                             if row["comparison"]["status"] == "compared"}
        for row in report["body_failed_attempts"]:
            lines.append(f"| {row['case_id']} | {'; '.join(row['comparison']['reasons'])} | "
                         f"{row['source_identity']['sha256'] in completed_sources} |")
    lines += ["", "## Layer 0 and steady layer groups", "",
              "The steady P50 column is median of per-layer call P50, unless a separately linked receipt supplies exact pooled statistics.", "",
              "| Case | Group | Layers | Real Mean ms | Median layer-call P50 ms | Sim Mean ms | Mean / P50 error |",
              "|---|---|---:|---:|---:|---:|---:|"]
    from statistics import median
    for row in report["current_body_comparisons"]:
        groups = {}
        for layer in row["per_layer"].get("layers", []):
            key = ("Layer 0" if layer["layer_id"] == 0 else "Steady", layer.get("attention_kind"), layer["kind"])
            groups.setdefault(key, []).append(layer)
        for key, values in groups.items():
            observed = sum(item["observed_ms"]["mean"] for item in values) / len(values)
            p50 = median(item["observed_ms"]["p50"] for item in values)
            preds = [None if row.get("prediction_invalidation") else item.get("predicted_ms") for item in values]
            pred = sum(preds) / len(preds) if all(value is not None for value in preds) else None
            error = (pred / observed - 1) * 100 if pred is not None and observed else None
            p50_error = (pred / p50 - 1) * 100 if pred is not None and p50 else None
            lines.append(f"| {row['case_id']} / {row['variant_id']} | {' / '.join(str(part) for part in key)} | {len(values)} | "
                         f"{observed:.4f} | {p50:.4f} | {_num(pred, 4)} | {_num(error)}% / {_num(p50_error)}% |")
    for heavy in (True, False):
        lines += ["", f"## {'Heavy >50us' if heavy else 'Micro <=50us'} operators — activity residual priority", "",
                  "| Case | Operator / role | Calls | Real / Sim us | Diff us | Absolute ms / Forward | Tier pass |",
                  "|---|---|---:|---:|---:|---:|---|"]
        selected = [row for row in report["current_operator_cohorts"] if row["heavy_call"] == heavy]
        for row in selected[:40]:
            lines.append(f"| {row['case_id']} / `{_runtime_tag(row)}` | {row['native_operator_type']} / {row['declared_role']} | "
                         f"{row['observed_calls']} | {row['observed_us']:.3f} / {row['predicted_us']:.3f} | "
                         f"{row['per_call_diff_us']:.3f} | {row['absolute_activity_residual_ms_per_forward']:.3f} | "
                         f"{row['accuracy_pass']} ({row['status']}) |")
    lines += ["", "## Highest unscored activity — coverage gaps, not zero predictions", "",
              "| Case | Operator / role | Unscored calls | Unscored observed activity ms / Forward | Status |",
              "|---|---|---:|---:|---|"]
    gaps = sorted((item for item in report["current_operator_families"] if item.get("unscored_event_count")),
                  key=lambda row: row["unscored_activity_ms_per_forward"], reverse=True)
    for row in gaps[:40]:
        lines.append(f"| {row['case_id']} | {row['native_operator_type']} / {row['declared_role']} | "
                     f"{row['unscored_event_count']} | {row['unscored_activity_ms_per_forward']:.3f} | {row['status']} |")
    lines += ["", "## Source-role references — already costed work is not an extra budget", "",
              "Reference differences have distinct evidence and are excluded from strict cohort accuracy counts.", "",
              "External native references are selected independently by measured source/geometry, native operator, role, layer set and observed ABI. Each row retains its own histogram P50; rows are not averaged.", "",
              "| Case | Operator / region | Calls | Real Mean / P50 / reference us | Real / Sim service ms per Forward | Residual ms | Boundary |",
              "|---|---|---:|---:|---:|---:|---|"]
    references = sorted(report["current_source_role_references"],
                        key=lambda row: abs(row["reference_residual_ms_per_forward"] or 0), reverse=True)
    for row in references:
        prediction = row["predicted_us"] if row["predicted_us"] is not None else row["predicted_reference_us"]
        correspondence = row.get("source_correspondence") or {}
        boundary = correspondence.get("boundary_relation") or row["status"]
        roles = ' + '.join(row.get('declared_roles') or [])
        region = (f"layers {','.join(map(str, row['layer_ids']))}" if row.get("reference_origin") == "external_native_partition"
                  else f"{row['attention_kind']} / {row['block']}")
        lines.append(f"| {row['case_id']} / `{_runtime_tag(row)}` | {row['native_operator_type']} / {roles} / {region} | "
                     f"{row['observed_us']['count']} | {_num(row['observed_us']['mean'])} / {_num(row['observed_us'].get('p50'))} / {_num(prediction)} | "
                     f"{_num(row['observed_activity_ms_per_forward'])} / {_num(row['predicted_service_ms_per_forward'])} | "
                     f"{_num(row['reference_residual_ms_per_forward'])} | {boundary} |")
    lines += ["", "## Receipt identities", ""]
    lines += [f"- [{Path(item['path']).name}]({item['path']}), SHA256 `{item['sha256']}`" for item in report["inputs"]]
    if report["additional_evidence"]:
        lines += ["", "Additional coverage/source evidence (not silently promoted into body or operator predictions):", ""]
        lines += [f"- [{Path(item['path']).name}]({item['path']}), SHA256 `{item['sha256']}`" for item in report["additional_evidence"]]
    lines += ["", *[f"- {text}" for text in report["limitations"]], ""]
    return "\n".join(lines)


def main():
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-manifest", type=Path,
                        help="Ordered body/operators/references/evidence receipt lists; CLI inputs append")
    parser.add_argument("--body", type=Path, action="append", default=[])
    parser.add_argument("--operators", type=Path, action="append", default=[])
    parser.add_argument("--references", type=Path, action="append", default=[])
    parser.add_argument("--evidence", type=Path, action="append", default=[])
    parser.add_argument("--invalidations", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest_identity = None
    if args.input_manifest:
        manifest, manifest_identity = _read(args.input_manifest)
        for key in ("body", "operators", "references", "evidence", "invalidations"):
            paths = [Path(value) for value in manifest.get(key, [])]
            paths = [path if path.is_absolute() else args.input_manifest.parent / path for path in paths]
            setattr(args, key, paths + getattr(args, key))
    report = build(args.body, args.operators, args.references, args.evidence, args.invalidations)
    if manifest_identity:
        report["input_manifest_identity"] = manifest_identity
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["execution"] = {
        "aggregation_seconds": time.perf_counter() - started,
        "aggregation_peak_rss_bytes": int(peak if sys.platform == "darwin" else peak * 1024),
        "receipt_read_strategy": "stream_native_operator_cases; bounded_body_receipts",
        "raw_capture_scans": 0, "prediction_executions": 0,
    }
    with args.output.open("w") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    args.output.with_suffix(".md").write_text(render(report))
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    main()
