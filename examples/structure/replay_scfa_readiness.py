"""Reconcile source-selected SCFA against the retained complete A3 captures.

[Role] Provide a factory variant and a separate bounded SCFA acceptance lane.
[Invariants] Only real selected-recipe cohorts are priced. SWA/CFA and unknown
  occurrences stay distinct; source conditions never come from observed time.
[Timeouts & Locks] Serial mapping/comparison workers, 180s each; 32 MiB metadata
  and 512 MiB per process. No locks, remote calls or device contexts.
[Side-Effect Policy] Import is inert. CLI reads sources and writes requested
  case/mapping/comparison/evidence files; it does not update the primary reports.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import resource
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "examples/structure/acceptance-20261029"
IMPLEMENTATION = "vllm_ascend_sharedkv_scfa"
SELECTOR = {
    "implementation": IMPLEMENTATION,
    "options": {
        "owner_schedule": "one_query_per_core", "selected_rows": "valid_prefix",
        "sinks_dtype": "fp32", "metadata_s2_split": False,
        "return_softmax_lse": False, "scratch_policy": "offchip",
    },
}
LIMIT = 32 * 1024 * 1024
MEMORY_LIMIT = 512 * 1024 * 1024
SOURCE_FILES = (
    "mindie_sim/backends/profiles/ascend.json",
    "mindie_sim/prediction/family_sharedkv.py",
    "mindie_sim/prediction/sharedkv_attention.py",
)


def read(path):
    path = Path(path)
    if path.stat().st_size > LIMIT:
        raise ValueError(f"scfa_metadata_exceeds_32_mib:{path}")
    return json.loads(path.read_text())


def digest(path):
    value = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    return {"file": path.name, "sha256": digest(path), "size_bytes": path.stat().st_size}


def rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # resource API units differ; this does not select execution placement.
    return int(value if sys.platform == "darwin" else value * 1024)


def scfa_variant(key, baseline):
    """Add a source choice to an independent case, preserving device overrides."""
    if key not in {"a3_v4f", "a3_v4pro"}:
        return None
    value = deepcopy(baseline)
    runtime_root = Path(baseline["declaration_source"]["case_path"]).parents[2]
    lowerings = value["case"].setdefault("runtime", {}).setdefault(
        "kernels", {}).setdefault("lowerings", {})
    lowerings["sharedkv_attention"] = deepcopy(SELECTOR)
    value.update(
        name=key + "_scfa-selected", declaration_key=key + "_scfa",
        variant="source_scfa_offchip_conditional")
    source = value["declaration_source"]
    source["implementation_overrides"] = {
        **source.get("implementation_overrides", {}),
        "sharedkv_attention": deepcopy(SELECTOR),
    }
    source["override_basis"] = "caller_declared_scfa_source_program_and_existing_hardware"
    source["capture_dispatch_identity_verified"] = False
    source["source_evidence"] = {
        **(source.get("source_evidence") or {}),
        "scfa": {
            "native_source_revision": "175ef4d49c2072f9233619636f0309f4f88b4e2c",
            "implementation": IMPLEMENTATION,
            "files": [{"path": str(runtime_root / name), "sha256": digest(runtime_root / name)}
                      for name in SOURCE_FILES],
            "hardware_basis": "registered_nominal_analytical_profile_with_original_case_overrides",
            "hardware_overrides_changed": False,
            "context_observed": False, "phase_observed": False,
            "index_values_observed": False, "capture_dispatch_identity_verified": False,
            "selection_scope": "single_contiguous_prefill_with_compressed_index_producer",
            "excluded_branches": ["SWA", "CFA", "decode", "multiple_sequences"],
            "resource_limits": [
                "Profile copy rates are nominal analytical declarations, not measured peaks.",
                "AIV read rate maps the platform scalar to a per-owner analytical supply.",
                "Fixpipe GM supply extends the documented L0C-to-L1 instruction rate.",
                "Original device overrides remain effective, including the MTE3 rate.",
                "Offchip scratch, valid-prefix indices and owner scheduling are caller conditions.",
            ],
        },
    }
    return value


def _baseline(key):
    import mindie_sim

    old = read(BASE / f"body-{key}.json")
    root = Path(mindie_sim.__file__).resolve().parents[1]
    original = Path(old["declaration_source"]["case_path"])
    path = root / "examples/cases" / original.name
    return old, {
        "name": key + "-reference", "declaration_key": key, "variant": "case_default",
        "case": read(path),
        "geometry": {name: old["declared_execution"][name]
                     for name in ("phase", "tokens", "context", "sequences")},
        "declaration_source": {
            "case_path": str(path), "case_sha256": digest(path),
            "historical_case_path": str(original), "implementation_overrides": {},
        },
    }


def _select_cohorts(mapping, selected_ids):
    windows, counts = [], Counter()
    for window in mapping["windows"]:
        kept = []
        for cohort in window["cohorts"]:
            ids = set(cohort["target_ids"])
            if ids & selected_ids:
                if not ids <= selected_ids:
                    raise ValueError("scfa_cohort_mixes_selected_and_unselected_programs")
                kept.append(cohort)
                counts.update({cohort["native_operator_type"]: cohort["event_count"]})
        windows.append({**window, "cohorts": kept})
    return {**mapping, "windows": windows}, dict(counts)


def _map_worker(args):
    from mindie_profiler.events import Observation, QueryStats, SourceRef, Window
    from mindie_profiler.sources_csv import CsvSource, probe_csv
    from mindie_profiler.structure_mapping import StructureMapper
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure

    started = time.perf_counter()
    old, baseline = _baseline(args.capture_key)
    variant = scfa_variant(args.capture_key, baseline)
    case_path = Path(str(args.output_prefix) + ".case.json")
    case_identity = write(case_path, variant["case"])
    manifest = export_structure(
        variant["case"], **variant["geometry"], scope="model",
        source=variant["declaration_source"])
    selected = [node for node in manifest["nodes"]
                if node["operator"].get("recipe") == IMPLEMENTATION
                and node.get("event_matchable", True)]
    if not selected or any(node.get("contract") is None for node in selected):
        raise ValueError("selected_scfa_contract_missing")
    selected_ids = {node["node_id"] for node in selected}
    capture = Path(old["source_identity"]["path"])
    identity = old["source_identity"]
    if capture.stat().st_size != identity["size_bytes"] or digest(capture) != identity["sha256"]:
        raise ValueError("scfa_capture_source_identity_changed")
    schema = probe_csv(capture)
    source = CsvSource(schema, rank_id="rank_0", rank_index=0)
    stats = QueryStats("rank_0", "scfa_complete_capture", budget=1_000_000)
    source_ref = SourceRef(
        rank_id="rank_0", rank_index=0, kind="csv", path=str(capture),
        basename=capture.name, sha256=identity["sha256"], size_bytes=capture.stat().st_size,
        mtime_ns=capture.stat().st_mtime_ns, schema_version=schema.schema_version,
        schema_variant=schema.schema_variant, header_sha256=schema.header_sha256,
        optional_missing=schema.optional_missing)
    bounds = old["capture_bounds_ns"]
    observation = Observation(
        "rank_0", 0, Window(*bounds, label="complete_capture_mixed_phase_possible"),
        None, [], source_ref, stats)
    mapper = StructureMapper(manifest, mapping_limit=0, max_events=1_000_000)
    window = mapper.map_window(observation, events=source.iter_events(
        max_rows=1_000_000, timeout_s=60, stats=stats, strict=True))
    mapping = mapper.finish([window])
    if mapping["event_window_count"] != old["positive_event_count"]:
        raise ValueError("scfa_complete_capture_denominator_changed")
    mapping_path = Path(str(args.output_prefix) + ".mapping.json")
    comparison_input = Path(str(args.output_prefix) + ".comparison-input.json")
    focused, events = _select_cohorts(mapping, selected_ids)
    artifacts = {
        "case": case_identity, "mapping": write(mapping_path, mapping),
        "comparison_input": write(comparison_input, focused),
    }
    case = parse_case(variant["case"])
    device = case.machine.dies[0]
    result = {
        "kind": "historical_full_capture_source_scfa_focused_replay",
        "not_new_live_collection": True, "capture_key": args.capture_key,
        "variant": variant["variant"], "declaration_source": variant["declaration_source"],
        "source_identity": source_ref.content_identity(), "graph_id": mapping["graph_id"],
        "declared_execution": mapping["declared_execution"],
        "complete_capture_event_count": mapping["event_window_count"],
        "operator_counts": {row["operator_type"]: row["event_count"] for row in window["operators"]},
        "selected_source_cohort_events": events,
        "selected_source_target_count": len(selected),
        "selected_source_contract_scopes": list({
            json.dumps(node.get("contract_scope"), sort_keys=True) for node in selected}),
        "other_sparse_cohort_events": sum(
            row["event_count"] for row in window["cohorts"]
            if row["native_operator_type"] == "SparseAttnSharedkv"
            and not set(row["target_ids"]) & selected_ids),
        "sparse_operator": next(row for row in window["operators"]
                                if row["operator_type"] == "SparseAttnSharedkv"),
        "occurrence_bound_events": mapping["status_counts"].get("bound", 0),
        "hardware": {
            "rates": dict(device.rates), "service_modes": dict(device.service_modes),
            "resource_units": dict(device.resource_units),
            "assumptions": dict(case.machine.assumptions),
            "original_device_overrides": baseline["case"]["machine"].get("device", {}),
        },
        "artifacts": artifacts, "elapsed_seconds": time.perf_counter() - started,
        "maximum_resident_set_size_bytes": rss(),
    }
    write(Path(str(args.output_prefix) + ".mapping-receipt.json"), result)
    if rss() > MEMORY_LIMIT:
        raise RuntimeError("scfa_mapping_memory_budget_exceeded")


def _compare_worker(args):
    from mindie_sim.cohort_comparison import compare_cohorts

    started = time.perf_counter()
    result = compare_cohorts(
        Path(str(args.output_prefix) + ".case.json"),
        Path(str(args.output_prefix) + ".comparison-input.json"))
    result["validation_resources"] = {
        "elapsed_seconds": time.perf_counter() - started,
        "maximum_resident_set_size_bytes": rss(),
    }
    write(Path(str(args.output_prefix) + ".comparison.json"), result)
    if rss() > MEMORY_LIMIT:
        raise RuntimeError("scfa_comparison_memory_budget_exceeded")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--capture-key", required=True, choices=("a3_v4f", "a3_v4pro"))
    parser.add_argument("--output-prefix", required=True, type=Path)
    parser.add_argument("--worker", choices=("map", "compare"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        (_map_worker if args.worker == "map" else _compare_worker)(args)
        return
    import mindie_sim

    started = time.perf_counter()
    runtime_root = Path(mindie_sim.__file__).resolve().parents[1]
    revision = subprocess.check_output(
        ["git", "-C", str(runtime_root), "rev-parse", "HEAD"], text=True, timeout=5).strip()
    sources_before = {name: digest(runtime_root / name) for name in SOURCE_FILES}
    for worker in ("map", "compare"):
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--capture-key", args.capture_key,
             "--output-prefix", str(args.output_prefix), "--worker", worker],
            check=True, timeout=180)
    result = read(Path(str(args.output_prefix) + ".mapping-receipt.json"))
    comparison_path = Path(str(args.output_prefix) + ".comparison.json")
    comparison = read(comparison_path)
    rows = [row for window in comparison["windows"] for row in window["cohorts"]]
    result["comparison"] = comparison
    result["comparison_event_status_counts"] = dict(sum((
        Counter({row["status"]: row["observed"]["event_count"]}) for row in rows), Counter()))
    result["artifacts"]["comparison"] = {
        "file": comparison_path.name, "sha256": digest(comparison_path),
        "size_bytes": comparison_path.stat().st_size,
    }
    result["runtime"] = {"path": str(runtime_root), "revision": revision,
                         "source_sha256": sources_before, "python": sys.version}
    result["elapsed_seconds"] = time.perf_counter() - started
    result["maximum_resident_set_size_bytes"] = max(
        result["maximum_resident_set_size_bytes"],
        comparison["validation_resources"]["maximum_resident_set_size_bytes"], rss())
    result["runtime_source_unchanged"] = sources_before == {
        name: digest(runtime_root / name) for name in SOURCE_FILES}
    if not result["runtime_source_unchanged"]:
        raise RuntimeError("scfa_runtime_source_changed")
    write(Path(str(args.output_prefix) + ".json"), result)
    print(json.dumps({
        key: result[key] for key in (
            "capture_key", "selected_source_cohort_events", "comparison_event_status_counts",
            "elapsed_seconds", "maximum_resident_set_size_bytes", "runtime_source_unchanged")}))
    if comparison["status_counts"].get("prediction_failed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
