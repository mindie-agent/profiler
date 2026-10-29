"""Completed real replay evidence may be reused only under unchanged declarations."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def completed_replay(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "examples/structure"))
    module = importlib.import_module("fusion_replay_extension")
    fixture = json.loads((ROOT / "tests/fixtures/fusion_reporting/historical-cohorts.json").read_text())
    name = "a3_glm53_decode-reference"
    retained = deepcopy(fixture["declarations"][name])
    summary = retained["summary"]
    summary["artifacts"] = {}
    for role in ("case", "mapping", "comparison"):
        path = tmp_path / f"{name}.{role}.json"
        path.write_text(json.dumps(retained[role]))
        summary["artifacts"][role] = module._identity(path)
    summary_path = tmp_path / f"fusion-cohort-{name}.json"
    summary_path.write_text(json.dumps(summary))
    source = summary["source_identity"]
    execution_file = str(ROOT / "mindie_profiler/structure_mapping.py")
    control_file = str((ROOT / "examples/structure/fusion_replay_cases.py").resolve())
    identity = {execution_file: module._hash(execution_file), control_file: "old-control"}
    capture = {
        "capture_key": summary["capture_key"], "source_identity": source,
        "reports": [{"summary_identity": module._identity(summary_path),
                     "comparison": {"status": "completed"}}],
    }
    receipt = {
        "status": "completed", "comparison_only": False,
        "runtime_source_identity": identity, "runtime_sources_unchanged": True,
        "captures": [capture], "elapsed_seconds": 1,
        "declaration_variant_count": 1, "raw_parsed_capture_scans": 1,
    }
    (tmp_path / "fusion-cohort-validation.json").write_text(json.dumps(receipt))
    declaration = {
        "name": name, "declaration_key": summary["declaration_key"],
        "variant": summary["variant"], "declaration_source": summary["declaration_source"],
        "case": retained["case"],
        "geometry": {key: summary["declared_execution"][key]
                     for key in ("phase", "tokens", "context", "sequences")},
    }
    new = deepcopy(declaration)
    new.update(name=name + "_new", declaration_key=summary["declaration_key"] + "_new")
    new["case"].setdefault("runtime", {})["graph_mode"] = "eager"
    identity = {**identity, control_file: "new-control"}
    return module, tmp_path, identity, {
        summary["capture_key"]: [declaration, new]}, {summary["capture_key"]: source}


def test_extension_reuses_identical_real_evidence_and_only_schedules_new_declaration(completed_replay):
    module, directory, identity, declarations, sources = completed_replay
    result = module.prepare_extension(directory, identity, declarations, sources)
    key = next(iter(declarations))
    assert result["jobs"] == {(key, declarations[key][1]["declaration_key"])}
    assert len(result["captures"]) == 1
    assert result["provenance"]["base_declaration_variant_count"] == 1
    assert result["provenance"]["reused_predictions_executed_again"] is False
    assert result["provenance"]["execution_sources_unchanged"]
    assert len(result["provenance"]["changed_control_files"]) == 1


def test_extension_rejects_rewriting_a_reused_real_case(completed_replay):
    module, directory, identity, declarations, sources = completed_replay
    old = next(iter(declarations.values()))[0]
    old["geometry"]["tokens"] += 1
    with pytest.raises(ValueError, match="existing_declaration_changed"):
        module.prepare_extension(directory, identity, declarations, sources)


def test_extension_records_new_program_evidence_without_changing_old_execution(completed_replay):
    module, directory, identity, declarations, sources = completed_replay
    new = next(iter(declarations.values()))[1]
    evidence = directory / "new-source-case.json"
    evidence.write_text(json.dumps(new["case"]))
    digest = module._hash(evidence)
    new["declaration_source"] = {
        **new["declaration_source"], "additional_source": {
            "path": str(evidence), "sha256": digest},
    }
    result = module.prepare_extension(
        directory, {**identity, str(evidence): digest}, declarations, sources)
    assert result["provenance"]["added_declaration_evidence_files"] == [str(evidence)]
    assert result["provenance"]["execution_sources_unchanged"]


def test_extension_rejects_changed_prediction_inputs_or_execution_source(completed_replay):
    module, directory, identity, declarations, sources = completed_replay
    runtime = str(ROOT / "mindie_profiler/structure_mapping.py")
    with pytest.raises(ValueError, match="execution_sources_changed"):
        module.prepare_extension(directory, {**identity, runtime: "changed"}, declarations, sources)
    path = directory / "a3_glm53_decode-reference.comparison.json"
    data = json.loads(path.read_text())
    data["windows"][0]["cohorts"][0]["observed"]["event_count"] += 1
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="artifact_identity_changed"):
        module.prepare_extension(directory, identity, declarations, sources)
