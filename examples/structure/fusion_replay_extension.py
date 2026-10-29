"""Reuse verified completed declarations when adding new replay scenarios.

[Role] Validate existing evidence before extending one historical campaign.
[Invariants] Existing cases, geometry and execution sources must be identical.
  Changed factory controls may add declarations but cannot rewrite old results.
  Every reused artifact remains bound to its original completed receipt.
[Timeouts & Locks] Metadata is bounded by the replay reader; no locks or workers.
[Side-Effect Policy] Read-only validation; the caller executes only new jobs.
"""
from copy import deepcopy
from pathlib import Path

from fusion_replay_cases import _hash, _read


CONTROL_FILES = frozenset({
    "replay_fusion_cohorts.py", "fusion_replay_cases.py",
    "fusion_replay_extension.py", "fusion_replay_source_cases.py",
})


def _identity(path):
    return {"file": path.name, "sha256": _hash(path), "size_bytes": path.stat().st_size}


def _verify_artifact(directory, identity):
    path = directory / identity["file"]
    if _identity(path) != identity:
        raise ValueError(f"extension_artifact_identity_changed:{path.name}")
    return path


def _evidence_paths(value):
    if isinstance(value, dict):
        path = value.get("path", value.get("file"))
        if isinstance(path, str) and "sha256" in value:
            yield path, value["sha256"]
        for child in value.values():
            yield from _evidence_paths(child)
    elif isinstance(value, list):
        for child in value:
            yield from _evidence_paths(child)


def prepare_extension(directory, identity, declarations, capture_sources):
    """Return old completed workers and the exact new declaration job set."""
    directory = Path(directory)
    receipt_path = directory / "fusion-cohort-validation.json"
    original = _read(receipt_path)
    if (original["status"] != "completed" or original.get("comparison_only")
            or original["runtime_sources_unchanged"] is not True):
        raise ValueError("extension_requires_completed_raw_capture_replay")
    old_sources = original["runtime_source_identity"]
    changed = {
        path for path in old_sources.keys() | identity.keys()
        if old_sources.get(path) != identity.get(path)
    }
    control_root = Path(__file__).resolve().parent
    permitted = {str(control_root / name) for name in CONTROL_FILES}
    expected = {value["name"]: (key, value)
                for key, values in declarations.items() for value in values}
    seen, old_jobs = set(), set()
    for capture in original["captures"]:
        source = capture_sources.get(capture["capture_key"], {})
        if any(source.get(field) != capture["source_identity"].get(field)
               for field in ("path", "sha256", "size_bytes")):
            raise ValueError("extension_capture_source_changed:" + capture["capture_key"])
        for report in capture["reports"]:
            path = _verify_artifact(directory, report["summary_identity"])
            summary = _read(path)
            name = path.name.removeprefix("fusion-cohort-").removesuffix(".json")
            if name in seen or name not in expected:
                raise ValueError(f"extension_old_declaration_removed_or_duplicated:{name}")
            key, value = expected[name]
            if key != capture["capture_key"] or key != summary["capture_key"]:
                raise ValueError(f"extension_capture_identity_changed:{name}")
            artifacts = {
                role: _verify_artifact(directory, item)
                for role, item in summary["artifacts"].items()
            }
            geometry = {field: summary["declared_execution"][field]
                        for field in ("phase", "tokens", "context", "sequences")}
            if (_read(artifacts["case"]) != value["case"]
                    or geometry != value["geometry"]
                    or summary["declaration_source"] != value["declaration_source"]
                    or summary["variant"] != value["variant"]
                    or summary["declaration_key"] != value["declaration_key"]):
                raise ValueError(f"extension_existing_declaration_changed:{name}")
            if report["comparison"]["status"] != "completed":
                raise ValueError(f"extension_comparison_not_completed:{name}")
            seen.add(name)
            old_jobs.add((key, value["declaration_key"]))
    new_jobs = set()
    for name, (key, value) in expected.items():
        if name not in seen:
            job = (key, value["declaration_key"])
            if job in old_jobs:
                raise ValueError(f"extension_new_variant_reuses_old_worker_key:{name}")
            new_jobs.add(job)
    if not new_jobs:
        raise ValueError("extension_has_no_new_declarations")
    added_evidence = {
        path for name, (_, value) in expected.items() if name not in seen
        for path, digest in _evidence_paths(value["declaration_source"])
        if path not in old_sources and Path(path).suffix in {".json", ".md"}
        and identity.get(path) == digest
    }
    if changed - permitted - added_evidence:
        raise ValueError("extension_execution_sources_changed:" + ",".join(
            sorted(changed - permitted - added_evidence)))
    return {
        "captures": deepcopy(original["captures"]),
        "jobs": new_jobs,
        "base_elapsed_seconds": original["elapsed_seconds"],
        "provenance": {
            "mode": "append_independent_declarations_to_verified_completed_replay",
            "base_receipt_identity": _identity(receipt_path),
            "base_runtime_source_identity": old_sources,
            "base_declaration_variant_count": original["declaration_variant_count"],
            "base_raw_parsed_capture_scans": original["raw_parsed_capture_scans"],
            "base_elapsed_seconds": original["elapsed_seconds"],
            "base_runtime_sources_unchanged": original["runtime_sources_unchanged"],
            "base_captures": original["captures"],
            "changed_control_files": sorted(changed & permitted),
            "added_declaration_evidence_files": sorted(changed & added_evidence),
            "execution_sources_unchanged": True,
            "existing_cases_geometry_and_artifacts_unchanged": True,
            "new_jobs": [{"capture_key": key, "declaration_key": declaration}
                         for key, declaration in sorted(new_jobs)],
            "reused_predictions_executed_again": False,
        },
    }
