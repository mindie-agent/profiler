"""Refresh declaration coverage from the cases saved by final capture replay.

[Role] Join retained capture census, original fixture rows and exact replay cases.
[Invariants] Source-selected cases do not become default-case capability. A fresh
  graph and verified artifact are required for full-replay evidence. Repeated
  declarations never increase the unique capture/event denominator.
[Timeouts & Locks] Serial finite graph exports; metadata files limited to 32 MiB.
[Side-Effect Policy] Reads local evidence and writes inventory JSON/Markdown only.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "examples/structure/acceptance-20261029"
LIMIT = 32 * 1024 * 1024
COMPLETE = {"complete_subgraph", "complete_semantic_subgraph", "declared_node_boundary"}
CAPABILITIES = {
    "AddRmsNormBias": (
        "prediction/family_ascend_norm.py",
        "Explicit native family supports optional beta, external Gemma gamma shift and rstd stores."),
    "AddRmsNormDynamicQuant": (
        "prediction/family_ascend_norm.py",
        "INT8 per-row scale contract requires residual_norm/norm_quant and caller affine declaration."),
    "RmsNormDynamicMxQuant": (
        "prediction/family_ascend_norm.py",
        "MX output requires declared FP8 activations and E8M0 block-32 scales; Kimi base remains BF16."),
    "SituMxQuant": (
        "prediction/gated_activation.py",
        "SiTU/MX group, active contract and local-reuse profile exist; Kimi base has no MX activation."),
    "GroupedMatmulSituQuant": (
        "prediction/gated_activation.py",
        "SiTU semantic work exists; exact grouped native ABI remains unverified."),
    "QuantBatchMatmulV4": (
        "structure_matrix_contracts.py",
        "Strict quantized matrix contracts preserve operand/scale domains; the case must declare them."),
    "MoeGatingTopK": (
        "prediction/feedforward.py",
        "Source-declared router selection excludes logits GEMM and preserves normalization scope."),
    "MoeGatingTopKHash": (
        "prediction/feedforward.py",
        "Hash router selection retains distinct table/renormalization semantics."),
    "RecurrentGatedDeltaRule": (
        "prediction/recurrent.py",
        "Decode/recurrent capability is separate from retained prefill declarations."),
    "AttentionUpdate": (
        "catalog/attention_common.py",
        "Context-parallel partial merge requires corresponding runtime selection."),
    "DequantSwigluQuant": (
        "prediction/feedforward.py",
        "Activation/quantization work exists; a matching native dequantization boundary is not established."),
}
NATIVE_BOUNDARY_GAPS = {"GroupedMatmulSituQuant", "DequantSwigluQuant"}


def read(path):
    path = Path(path)
    if path.stat().st_size > LIMIT:
        raise ValueError(f"inventory_metadata_exceeds_32_mib:{path}")
    return json.loads(path.read_text())


def digest(path):
    h = sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def artifact(directory, summary, name):
    record = summary["artifacts"][name]
    path = directory / record["file"]
    if path.stat().st_size != record["size_bytes"] or digest(path) != record["sha256"]:
        raise ValueError(f"replay_artifact_identity_mismatch:{path}")
    return path, read(path)


def replay_inputs(directory):
    """The batch receipt chooses reports; stale glob leftovers are not evidence."""
    receipt = read(directory / "fusion-cohort-validation.json")
    seen = set()
    for capture in receipt["captures"]:
        for reference in capture["reports"]:
            path = directory / reference["report"]
            if path.name in seen:
                raise ValueError(f"duplicate_replay_report:{path.name}")
            seen.add(path.name)
            summary = read(path)
            if summary["capture_key"] != capture["capture_key"]:
                raise ValueError(f"replay_capture_identity_mismatch:{path.name}")
            case_path, case = artifact(directory, summary, "case")
            mapping_path, mapping = artifact(directory, summary, "mapping")
            if mapping["graph_id"] != summary["graph_id"]:
                raise ValueError(f"replay_mapping_graph_mismatch:{path.name}")
            yield path, summary, case_path, case, mapping_path, mapping


def targets(manifest):
    by_kind = defaultdict(list)
    for target in (*manifest["nodes"], *manifest.get("subgraphs", ())):
        implementation = target.get("implementation", {})
        kinds = set(implementation.get("native_kinds", ()))
        if implementation.get("native_kind"):
            kinds.add(implementation["native_kind"])
        for kind in kinds:
            by_kind[kind].append(target)
    return by_kind


def coverage(target):
    default = "complete_subgraph" if "subgraph_id" in target else "declared_node_boundary"
    return target.get("coverage", {}).get("kind", default)


def summarize_targets(values):
    complete = [target for target in values if coverage(target) in COMPLETE]
    comparable = [target for target in complete
                  if target.get("contract") is not None and target.get("event_matchable", True)]
    return {
        "target_count": len(values), "complete_boundary_target_count": len(complete),
        "incomplete_boundary_target_count": len(values) - len(complete),
        "comparable_target_count": len(comparable),
        "coverage_kind_counts": dict(Counter(coverage(target) for target in values)),
        "coverage_limitations": sorted({
            item for target in values for item in target.get("coverage", {}).get("limitations", ())}),
        "contract_scopes": sorted({str(target.get("contract_scope")) for target in comparable}),
        "families": sorted({target["family"] for target in values}),
        "roles": sorted({str(target.get("role")) for target in values}),
        "blocks": sorted({str(target.get("block")) for target in values}),
    }, {canonical(target["contract"]) for target in comparable}


def fixture_rows():
    from mindie_profiler.normalized import kernel_rows
    from mindie_profiler.tensor_contracts import observed_contract, observed_contract_diagnostic

    root = ROOT / "tests/fixtures/fusion_contracts"
    result = defaultdict(list)
    for source in read(root / "provenance.json")["sources"]:
        locators = {row["fixture_csv_line"]: row["source_csv_line"] for row in source["rows"]}
        for row in kernel_rows(root / source["fixture"]):
            contract = observed_contract(row)
            result[source["capture_id"], row.kind].append({
                "source_csv_line": locators[row.line],
                "contract": canonical(contract) if contract is not None else None,
                "diagnostic": observed_contract_diagnostic(row)["reason"],
            })
    return result


def refresh(directory):
    import mindie_sim
    from mindie_sim.structure import export_structure

    template = read(directory / "fusion-coverage-inventory.json")
    audit = read(directory / "fusion-capture-field-coverage.json")
    sources = {row["capture_id"]: row for row in audit["sources"]}
    fixtures = fixture_rows()
    availability, contracts, replays = defaultdict(list), {}, defaultdict(list)
    declarations, default_keys = [], set()

    def register(manifest, declaration):
        declarations.append(declaration)
        for kind, values in targets(manifest).items():
            counts, supported = summarize_targets(values)
            availability[kind].append({
                "declaration": declaration["declaration"],
                "capture_id": declaration["capture_id"], "basis": declaration["basis"],
                "graph_id": manifest["graph_id"], **counts,
            })
            contracts[declaration["declaration"], kind] = supported

    for path, summary, case_path, case, mapping_path, mapping in replay_inputs(directory):
        capture_id = summary["capture_key"]
        source = sources[capture_id]
        if any(summary["source_identity"][key] != source["source_identity"][key]
               for key in ("path", "sha256", "size_bytes")):
            raise ValueError(f"historical_source_identity_mismatch:{path.name}")
        expected = {kind: row["event_count"] for kind, row in source["operators"].items()}
        if summary["operator_counts"] != expected:
            raise ValueError(f"complete_operator_denominator_mismatch:{path.name}")
        actual = Counter()
        for window in mapping["windows"]:
            actual.update({row["operator_type"]: row["event_count"] for row in window["operators"]})
        if dict(actual) != expected:
            raise ValueError(f"mapping_operator_denominator_mismatch:{path.name}")
        ex = summary["declared_execution"]
        geometry = {key: ex[key] for key in (
            "phase", "tokens", "context", "sequences", "scope", "expand_calls")}
        manifest = export_structure(case, **geometry, source=summary["declaration_source"])
        if manifest["graph_id"] != summary["graph_id"]:
            raise ValueError(f"replay_graph_is_stale:{path.name}")
        basis = summary["variant"]
        declaration = {
            "declaration": path.name, "capture_id": capture_id, "basis": basis,
            "graph_id": manifest["graph_id"], "execution": geometry,
            "case_path": str(case_path), "case_sha256": digest(case_path),
            "declaration_source": summary["declaration_source"],
            "full_capture_replay": {
                "status": "complete_capture_replayed_for_current_graph",
                "summary": path.name, "mapping": mapping_path.name,
                "mapping_sha256": digest(mapping_path),
                "comparison_status": summary["comparison"]["status"],
                "no_raw_rescan_by_inventory": True,
            },
        }
        register(manifest, declaration)
        for window in mapping["windows"]:
            for row in window["operators"]:
                replays[row["operator_type"]].append({
                    "capture_id": capture_id, "declaration": path.name, "basis": basis,
                    "graph_id": manifest["graph_id"], **{
                        key: row[key] for key in (
                            "event_count", "status_counts", "reason_counts", "contract_available_events",
                            "implementation_correspondence") if key in row},
                })
        default_key = (capture_id, canonical(geometry))
        if default_key not in default_keys:
            default_keys.add(default_key)
            base_path = Path(summary["declaration_source"]["case_path"])
            if digest(base_path) != summary["declaration_source"]["case_sha256"]:
                raise ValueError(f"replay_base_case_changed:{base_path}")
            base_case = read(base_path)
            default = export_structure(base_case, **geometry)
            register(default, {
                "declaration": summary["declaration_key"] + ":case_default",
                "capture_id": capture_id, "basis": "case_default",
                "graph_id": default["graph_id"], "execution": geometry,
                "case_path": str(base_path), "case_sha256": digest(base_path),
                "full_capture_replay": {
                    "status": "default_declaration_only_not_replayed",
                    "no_raw_rescan_by_inventory": True,
                },
            })
        del manifest, mapping

    sim = Path(mindie_sim.__file__).resolve().parent
    for entry in template["operators"]:
        kind, capture_ids = entry["operator_type"], set(entry["captures"])
        current = [item for item in availability[kind]
                   if item["capture_id"] in capture_ids]
        replayed = [item for item in current if item["declaration"].endswith(".json")]
        defaults = [item for item in current if item["basis"] == "case_default"]
        entry["declared_implementation_correspondence"] = current
        entry["declaration_coverage_by_basis"] = {}
        for basis in sorted({item["basis"] for item in declarations}):
            subset = [item for item in current if item["basis"] == basis]
            entry["declaration_coverage_by_basis"][basis] = {
                "capture_ids": sorted({item["capture_id"] for item in subset}),
                "declared": bool(subset),
                "complete_boundary": any(item["complete_boundary_target_count"] for item in subset),
                "comparable_contract": any(item["comparable_target_count"] for item in subset),
            }
        entry["captures_without_native_declaration"] = sorted(
            capture_ids - {item["capture_id"] for item in replayed})
        entry["captures_without_default_native_declaration"] = sorted(
            capture_ids - {item["capture_id"] for item in defaults})
        entry["captures_without_complete_boundary"] = sorted(capture_ids - {
            item["capture_id"] for item in replayed if item["complete_boundary_target_count"]})
        entry["captures_without_comparable_contract"] = sorted(capture_ids - {
            item["capture_id"] for item in replayed if item["comparable_target_count"]})
        entry["complete_boundary_status"] = (
            "complete_boundary_declared" if any(item["complete_boundary_target_count"] for item in replayed)
            else "incomplete_boundary_only" if replayed else "not_declared_in_replay_cases")
        entry["contract_capability_status"] = (
            "comparable_declared_contract" if any(item["comparable_target_count"] for item in replayed)
            else "declared_boundary_without_comparable_contract" if replayed
            else "no_native_declaration_in_replay_cases")
        entry["implementation_mapping_status"] = "declared" if replayed else "not_selected_in_replay_cases"
        entry.pop("implementation_mapping_reason", None)
        entry["mechanism_capability"] = None
        if kind in CAPABILITIES:
            module, detail = CAPABILITIES[kind]
            entry["mechanism_capability"] = {
                "source": str(sim / module), "sha256": digest(sim / module),
                "detail": detail, "does_not_imply_case_selection": True,
            }
        entry["declaration_gaps"] = [{
            "capture_id": capture_id,
            "category": ("semantic_work_available_native_boundary_not_established"
                         if kind in NATIVE_BOUNDARY_GAPS else
                         "capability_available_current_declaration_not_selected"
                         if kind in CAPABILITIES or current else "native_boundary_not_declared"),
            "detail": (CAPABILITIES[kind][1] if kind in CAPABILITIES else
                       "No native target is declared for this capture case/phase."),
        } for capture_id in entry["captures_without_native_declaration"]]
        entry["retained_fixture_contract_checks"] = {}
        for capture_id in sorted(capture_ids):
            rows = fixtures[capture_id, kind]
            supported = [row for row in rows if row["contract"] is not None]
            matched, by_declaration = set(), {}
            for item in current:
                if item["capture_id"] != capture_id:
                    continue
                matches = [row["source_csv_line"] for row in supported
                           if row["contract"] in contracts[item["declaration"], kind]]
                by_declaration[item["declaration"]] = {
                    "basis": item["basis"], "matched_source_csv_lines": matches}
                if item["declaration"].endswith(".json"):
                    matched.update(matches)
            entry["retained_fixture_contract_checks"][capture_id] = {
                "original_record_count": len(rows),
                "observed_contract_available_count": len(supported),
                "matching_declared_native_contract_count": len(matched),
                "matched_source_csv_lines": sorted(matched),
                "unavailable_reasons": dict(Counter(
                    row["diagnostic"] for row in rows if row["contract"] is None)),
                "by_declaration": by_declaration,
                "scope": "original_fixture_rows_only; union_deduplicated_by_capture_source_line",
            }
        entry["full_capture_replays"] = replays[kind]
        entry["full_capture_match_status"] = (
            "current_graph_replay_available" if replays[kind] else "no_current_graph_replay")
    required = [entry for entry in template["operators"] if entry["mapping_required"]]
    missing = [entry for entry in required
               if entry["complete_boundary_status"] == "not_declared_in_replay_cases"]
    counts = template["denominator"]
    counts.update(
        declared_boundary_type_count=len(required) - len(missing),
        missing_required_implementation_type_count=len(missing),
        missing_required_implementation_types=[entry["operator_type"] for entry in missing],
        missing_required_capture_kind_pairs=sum(len(entry["captures_without_native_declaration"])
                                                for entry in required),
        complete_boundary_type_count=sum(entry["complete_boundary_status"] ==
                                         "complete_boundary_declared" for entry in required),
        incomplete_boundary_only_types=[entry["operator_type"] for entry in required
                                        if entry["complete_boundary_status"] == "incomplete_boundary_only"],
        comparable_contract_type_count=sum(entry["contract_capability_status"] ==
                                           "comparable_declared_contract" for entry in required),
        fixture_matched_type_count=sum(any(row["matching_declared_native_contract_count"]
                                          for row in entry["retained_fixture_contract_checks"].values())
                                       for entry in required),
        required_capture_kind_pairs_without_complete_boundary=sum(
            len(entry["captures_without_complete_boundary"]) for entry in required),
        required_capture_kind_pairs_without_comparable_contract=sum(
            len(entry["captures_without_comparable_contract"]) for entry in required),
        current_graph_full_replay_declaration_count=sum(
            row["full_capture_replay"]["status"] == "complete_capture_replayed_for_current_graph"
            for row in declarations),
    )
    counts["missing_required_implementation_field_scope"] = (
        "No native target in saved replay declarations; not a count of unimplemented runtime mechanisms.")
    template.update(schema_version="mindie-native-fusion-coverage-inventory/3",
                    declarations=declarations,
                    refresh_basis="final_replay_saved_cases; verified_artifact_hashes_and_fresh_graphs",
                    refresh_script_sha256=digest(__file__),
                    refresh_execution={
                        "python_executable": sys.executable,
                        "python_version": platform.python_version(),
                        "python_implementation": platform.python_implementation(),
                        "scope": "Interpreter used for all fresh graph identity checks in this inventory.",
                    },
                    replay_validation_receipt_sha256=digest(directory / "fusion-cohort-validation.json"))
    explanation = (
        "Default-case exports and source-selected replay cases are separate. Capability code is not "
        "selected-case coverage. Full-capture counts are never added across declaration variants.")
    if explanation not in template["interpretation"]:
        template["interpretation"].append(explanation)
    return template


def markdown(result):
    counts = result["denominator"]
    execution = result["refresh_execution"]
    lines = [
        "# Native Fusion Coverage From Final Saved Cases", "",
        "Historical retained captures; no new live collection. Final `.case.json` artifacts, "
        "artifact hashes and freshly exported graph IDs determine replay evidence.", "",
        f"{counts['unique_capture_count']} unique captures contain {counts['event_count']:,} events "
        f"and {counts['native_type_count']} native types. Declaration variants do not enlarge that denominator.",
        "", f"Fresh graph verification: {counts['current_graph_full_replay_declaration_count']} saved replay "
        f"declarations, {execution['python_implementation']} {execution['python_version']}, "
        f"`{execution['python_executable']}`.",
        "", f"The {counts['required_body_correspondence_type_count']} required model-body types contain "
        f"{counts['required_body_correspondence_event_count']:,} events: "
        f"{counts['declared_boundary_type_count']} types have declared boundaries, "
        f"{counts['complete_boundary_type_count']} have complete boundaries, "
        f"{counts['comparable_contract_type_count']} have comparable contracts, and "
        f"{counts['fixture_matched_type_count']} match at least one retained original fixture row. "
        "These are distinct evidence levels, not a count of bound layer occurrences.",
        "", "Default declarations and source-selected variants remain separate. A Transformer block "
        "contains Attention and FFN; FFN may be MoE. Candidate geometry does not bind a layer occurrence.",
        "", "| Native type | Events | Default boundary | Replay boundary | Replay contract | Fixture matches |",
        "| --- | ---: | --- | --- | --- | ---: |",
    ]
    for entry in result["operators"]:
        if not entry["mapping_required"]:
            continue
        default = entry["declaration_coverage_by_basis"].get("case_default", {})
        matches = sum(row["matching_declared_native_contract_count"]
                      for row in entry["retained_fixture_contract_checks"].values())
        total = sum(row["original_record_count"]
                    for row in entry["retained_fixture_contract_checks"].values())
        lines.append(
            f"| `{entry['operator_type']}` | {entry['event_count']:,} | "
            f"{'complete' if default.get('complete_boundary') else 'incomplete' if default.get('declared') else 'not selected'} | "
            f"{entry['complete_boundary_status']} | {entry['contract_capability_status']} | {matches}/{total} |")
    lines.extend([
        "", "GLM native normalization uses the separately saved source/checkpoint-conditional choices; "
        "the catalog default is not retroactively changed. Kimi SiTU and RMS MX mechanisms can exist "
        "while the retained BF16 activation declaration does not select them. See "
        "`head-normalization-evidence.json` for the global bias predicate and precision limits.", "",
        f"{counts['missing_required_implementation_type_count']} required types have no native target "
        f"in the saved replay declarations ({counts['missing_required_capture_kind_pairs']} capture/type pairs). "
        "This is not an unimplemented-mechanism count. QuantBatchMatmulV4, RMS MX and SiTU MX need "
        "the appropriate precision/activation declaration; recurrent GDN and AttentionUpdate require "
        "the corresponding phase or parallelism. GroupedMatmulSituQuant retains an exact-native-boundary "
        "source gap. Per-capture reasons and capability sources remain in the JSON.", "",
        "ChunkKdaFwd and ChunkGatedDeltaRuleFwd incomplete native boundaries remain outside complete "
        "contract/resource coverage. Full JSON preserves all 148 types, raw missingness, source branches, "
        "per-declaration fixture matches and full-capture status/reason counts.", "",
        "Fixture examples are deduplicated by original capture and source line. Full-replay counts "
        "stay per declaration and must not be summed as additional hardware evidence. No inclusive "
        "fused duration is divided among member nodes.",
    ])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=BASE)
    parser.add_argument("--check-artifacts", action="store_true",
                        help="Verify saved case/mapping identities without graph export or output writes.")
    args = parser.parse_args()
    if args.check_artifacts:
        names = [path.name for path, *_ in replay_inputs(args.directory)]
        print(json.dumps({"saved_artifacts_verified": names, "graph_freshness_checked": False}))
        return
    result = refresh(args.directory)
    (args.directory / "fusion-coverage-inventory.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.directory / "fusion-coverage-inventory.md").write_text(markdown(result))
    print(json.dumps(result["denominator"], indent=2))


if __name__ == "__main__":
    main()
