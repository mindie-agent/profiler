"""Verify native observation inputs cannot reuse stale offline predictions.

[Role] Exercise response/adapter identity and real evaluator cache reuse.
[Invariants] Native profile identity is separate from the simulator identity.
[Timeouts & Locks] Tiny files and a one-layer CPU graph; no locks or network.
[Side-Effect Policy] Isolated tmp_path outputs and conftest runtime homes only.
"""
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
import dsh_generalization_eval as dsh
from native_observations import (
    PROFILE_FILES, PROFILER_SOURCE_FILES, ROOT as STRUCTURE_ROOT,
    native_observation_identity)
from tests.sim_fixtures import case_path


@pytest.mark.parametrize("relative", (
    "a5_native_observations.py", "capture_structure.py", "capture_ffn_guard.py",
    "profiles/a2_native_20261031.json",
    "profiles/a5_gdn_decode_native_20261106.json",
))
def test_profile_semantics_and_data_invalidate_actual_prediction_cache(tmp_path, monkeypatch, relative):
    source = ROOT / "examples" / "structure"
    for name in PROFILE_FILES:
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, destination)
    before = native_observation_identity(tmp_path)
    monkeypatch.setattr(dsh, "NATIVE_OBSERVATION_IDENTITY", before)
    monkeypatch.setattr(dsh, "CACHE_ROOT", tmp_path / "cache")
    raw = json.loads(case_path("quickstart.json").read_text())
    raw["model"]["layers"] = 1
    item = (("fixed-input", "decode", 1, 64, 1), raw)
    calls = []
    actual = dsh.predict_body

    def counted(*args, **kwargs):
        calls.append(1)
        return actual(*args, **kwargs)

    monkeypatch.setattr(dsh, "predict_body", counted)
    first = dsh._predict_worker(item)[1]
    assert dsh._predict_worker(item)[1] == json.loads(json.dumps(first))
    assert len(calls) == 1
    changed = tmp_path / relative
    changed.write_bytes(changed.read_bytes() + b"\n")
    after = native_observation_identity(tmp_path)
    assert before != after
    monkeypatch.setattr(dsh, "NATIVE_OBSERVATION_IDENTITY", after)
    second = dsh._predict_worker(item)[1]
    assert second["body_forward_span_ms"] == first["body_forward_span_ms"]
    assert len(calls) == 2 and len(list(dsh.CACHE_ROOT.glob("pred_*.json"))) == 2


@pytest.mark.parametrize("relative", (
    "normalized.py", "sources_db.py", "knowledge/db_source_mapping.json",
))
def test_reused_profiler_decoder_and_contract_sources_are_in_identity(
        tmp_path, relative):
    import mindie_profiler

    source = Path(mindie_profiler.__file__).resolve().parent
    copied = tmp_path / "profiler-source"
    copied.mkdir()
    for name in PROFILER_SOURCE_FILES:
        target = copied / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / name).read_bytes())
    before = native_observation_identity(STRUCTURE_ROOT, source_root=copied)
    target = copied / relative
    target.write_bytes(target.read_bytes() + b"\n")
    after = native_observation_identity(STRUCTURE_ROOT, source_root=copied)
    assert before != after
