"""Offline prediction caches follow runtime code/data, without capture rehashing.

[Role] Exercise deterministic package identity and real prediction cache reuse.
[Invariants] Runtime changes invalidate; bytecode and checkout location do not.
[Timeouts & Locks] Tiny temporary package trees and one-layer CPU simulation.
[Side-Effect Policy] Writes only pytest tmp_path; never edits captures or packages.
"""
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))

import dsh_generalization_eval as dsh_eval
import wave5_generalization_eval as wave5_eval
from runtime_identity import prediction_report_identity, simulator_identity
from tests.sim_fixtures import case_path


def _package(root):
    files = {
        "__init__.py": "__version__ = 'test'\n",
        "prediction/body_defaults.py": "TILE = 64\n",
        "catalog/model.py": "HEADS = 32\n",
        "backends/profiles/ascend.json": '{"bandwidth": 123}\n',
    }
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return SimpleNamespace(__file__=str(root / "__init__.py"), __version__="test")


def test_identity_tracks_content_and_relative_paths_without_location_or_bytecode(tmp_path):
    module = _package(tmp_path / "original")
    original = simulator_identity(module)
    relocated = tmp_path / "relocated"
    shutil.copytree(Path(module.__file__).parent, relocated)
    copy = SimpleNamespace(__file__=str(relocated / "__init__.py"), __version__="test")
    assert simulator_identity(copy) == original
    bytecode = relocated / "__pycache__"
    bytecode.mkdir()
    (bytecode / "artifact.py").write_text("ignored", encoding="utf-8")
    (bytecode / "artifact.json").write_text("{}", encoding="utf-8")
    (relocated / "prediction" / "body_defaults.pyc").write_bytes(b"bytecode")
    assert simulator_identity(copy) == original
    source = relocated / "catalog" / "model.py"
    source.rename(source.with_name("other.py"))
    assert simulator_identity(copy) != original


@pytest.mark.parametrize("relative,replacement", (
    ("prediction/body_defaults.py", b"TILE = 32\n"),
    ("catalog/model.py", b"HEADS = 16\n"),
    ("backends/profiles/ascend.json", b'{"bandwidth": 456}\n'),
))
def test_runtime_changes_invalidate_the_prediction_cache(tmp_path, monkeypatch, relative, replacement):
    module = _package(tmp_path / "runtime")
    monkeypatch.setattr(dsh_eval, "mindie_sim", module)
    monkeypatch.setattr(wave5_eval, "mindie_sim", module)
    monkeypatch.setattr(dsh_eval, "CACHE_ROOT", tmp_path / "cache")
    old_identity = dsh_eval._sim_identity()
    assert wave5_eval._sim_identity() == old_identity
    monkeypatch.setattr(dsh_eval, "SIM_IDENTITY", old_identity)
    raw = json.loads(case_path("quickstart.json").read_text())
    raw["model"]["layers"] = 1
    calls = []
    actual_predict = dsh_eval.predict_body

    def counted_predict(*args, **kwargs):
        calls.append(1)
        return actual_predict(*args, **kwargs)

    monkeypatch.setattr(dsh_eval, "predict_body", counted_predict)
    item = (("test-template", "decode", 1, 64, 1), raw)
    _, first = dsh_eval._predict_worker(item)
    assert first["status"] == "modeled" and first["body_forward_span_ms"] > 0
    assert dsh_eval._predict_worker(item)[1]["body_forward_span_ms"] == first["body_forward_span_ms"]
    assert len(calls) == 1
    changed = Path(module.__file__).parent / relative
    changed.write_bytes(replacement)
    new_identity = dsh_eval._sim_identity()
    assert new_identity != old_identity
    assert wave5_eval._sim_identity() == new_identity
    monkeypatch.setattr(dsh_eval, "SIM_IDENTITY", new_identity)
    assert dsh_eval._predict_worker(item)[1]["status"] == "modeled"
    assert len(calls) == 2
    assert len(list(dsh_eval.CACHE_ROOT.glob("pred_*.json"))) == 2


def test_wave5_aggregation_preserves_missing_or_stale_prediction_identity():
    def report(identity=None):
        return {"parser_identity": wave5_eval.PARSER_IDENTITY,
                **({"sim_identity": identity} if identity is not None else {})}

    current = wave5_eval.SIM_IDENTITY
    mixed = wave5_eval.aggregate_chip_reports(report(), report("old-runtime"), report(current))
    identities = mixed["chip_report_identities"]
    assert identities["a2"]["sim_identity"] is None
    assert identities["a2"]["sim_identity_status"] == "missing"
    assert identities["a3"]["sim_identity"] == "old-runtime"
    assert identities["a3"]["sim_identity_status"] == "differs_from_current"
    assert identities["a5"]["sim_identity_status"] == "matches_current"
    assert mixed["sim_identity"] is None
    assert mixed["evaluator_sim_identity"] == current
    assert mixed["sim_identity_matches_current"] is False
    confirmed = wave5_eval.aggregate_chip_reports(*(report(current) for _ in range(3)))
    assert confirmed["sim_identity"] == current
    assert confirmed["sim_identity_matches_current"] is True


def test_registered_scoreboards_cannot_inherit_the_new_dsh_runtime_identity():
    current = dsh_eval.SIM_IDENTITY
    reports = {"registered_decode": {"sim_identity": "earlier-sim"},
               "registered_prefill": {}, "dsh_predictions": {"sim_identity": current}}
    mixed = prediction_report_identity(reports, current)
    assert mixed["sim_identity"] is None and not mixed["sim_identity_matches_current"]
    assert mixed["evaluator_sim_identity"] == current
    sources = mixed["source_report_identities"]
    assert sources["registered_decode"]["sim_identity"] == "earlier-sim"
    assert sources["registered_prefill"]["sim_identity_status"] == "missing"
    assert sources["dsh_predictions"]["sim_identity_status"] == "matches_current"
    legacy_runtime = {"algorithm": "older-package-hash", "package_sha256": "original-content-hash"}
    reports["registered_prefill"]["runtime"] = legacy_runtime
    legacy = prediction_report_identity(reports, current)["source_report_identities"]["registered_prefill"]
    assert legacy["reported_runtime"] == legacy_runtime
    assert legacy["sim_identity"] is None and legacy["sim_identity_status"] == "unverified_runtime_format"
    for source in reports.values():
        source["sim_identity"] = current
    confirmed = prediction_report_identity(reports, current)
    assert confirmed["sim_identity"] == current and confirmed["sim_identity_matches_current"]
    assert not prediction_report_identity({}, current)["sim_identity_matches_current"]
