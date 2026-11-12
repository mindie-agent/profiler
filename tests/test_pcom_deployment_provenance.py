"""Original status.json deployment -> FeatureConfig source revision.

[Role]
  The ordinary forecast reads only deployment identity from the selected
  original `source_case_dir/status.json`: `spec.image` and the successful
  prepare record `image_id`.  It must not read target kernel_details.

[Invariants]
  * r64 is certified only by the witnessed 8d422528 image digest; the R35
    digest 5461a1a8 stays unpinned even with identical shape/MLA/query norm.
  * A caller-supplied image_id/revision is preserved; the actual digest
    overrides a conflicting label.
  * Absent/failed/foreign status leaves the case unpinned, no global guard.
  * Heldout trace/metric changes in status do not change the cache identity.

[Timeouts & Locks]
  Small local JSON only; no target CSV, device or network.

[Side-Effect Policy]
  Writes only under pytest tmp_path.
"""
from __future__ import annotations

import builtins
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("mindie_sim")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
import zero_shot_piecewise_validation as z  # noqa: E402
from zero_shot_native_windows import (  # noqa: E402
    _capture_status, deployment_metadata,
)

MODEL_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen38_highconc_c4.json"
R64 = "sha256:8d422528ac20a8babcbbf93762cde3b47d4db6c5f7ab777f4f1f65b32b89ab3e"
R35 = "sha256:5461a1a8253c6dc07868956166ad94751f84c82d00ff7791c59a9c1ac497de06"


def _case(tmp_path: Path, *, image: str, image_id: str, state: str = "completed",
          created: bool = True, captured: bool = True) -> Path:
    case = tmp_path / "case"
    case.mkdir(exist_ok=True, parents=True)
    (case / "status.json").write_text(json.dumps({
        "status": state, "finished": "2026-11-07T00:00:00Z",
        "spec": {"image": image, "nodes": ["10.0.0.1"]},
        "prepare": [{"node": "10.0.0.1", "hostname": "host-a", "created": created,
                     "image": image, "image_id": image_id, "dies_visible": 8}],
        "cells": [{"name": "pf_c2", "tag": "case_pf_c2", "captured": captured,
                   "failed": 0, "success": 1, "ttft_ms": 100.0}],
    }), encoding="utf-8")
    _capture_status.cache_clear()
    return case


def _spec(case: Path):
    return SimpleNamespace(source_case_dir=case, cell_id="case_pf_c2")


def _revision(raw):
    meta = dict(raw["runtime"].get("metadata") or {})
    from mindie_sim.prediction.subgraphs.instantiate import FeatureConfig
    return dict(FeatureConfig.from_runtime(
        SimpleNamespace(metadata=tuple(meta.items())), None).metadata)


def test_r64_status_certifies_r64_and_r35_stays_unpinned(tmp_path):
    raw = {"runtime": {"metadata": {}}}
    r64 = deployment_metadata(_spec(_case(tmp_path / "a", image="repo:r64", image_id=R64)), raw)
    assert r64["runtime"]["metadata"]["image_id"] == R64
    assert _revision(r64)["mx_quant_source_revision"] == "r64"

    r35 = deployment_metadata(_spec(_case(tmp_path / "b", image="repo:r35", image_id=R35)), raw)
    assert r35["runtime"]["metadata"]["image_id"] == R35
    assert _revision(r35)["mx_quant_source_revision"] == "unpinned"


def test_capture_outcome_or_precapture_does_not_erase_deployment_identity(tmp_path):
    raw = {"runtime": {"metadata": {}}}
    uncaptured = _case(tmp_path / "uncaptured", image="repo:r64", image_id=R64,
                       captured=False)
    bound = deployment_metadata(_spec(uncaptured), raw)
    assert bound["runtime"]["metadata"]["image_id"] == R64
    assert _revision(bound)["mx_quant_source_revision"] == "r64"

    # A successful prepare before the first capture is still real deployment.
    running = _case(tmp_path / "running", image="repo:r64", image_id=R64,
                    state="running")
    status = json.loads((running / "status.json").read_text())
    status.pop("cells", None)
    (running / "status.json").write_text(json.dumps(status))
    _capture_status.cache_clear()
    before_capture = deployment_metadata(_spec(running), raw)
    assert before_capture["runtime"]["metadata"]["image_id"] == R64
    assert _revision(before_capture)["mx_quant_source_revision"] == "r64"


def test_caller_declarations_and_actual_digest_over_label(tmp_path):
    # Explicit caller id survives even when the status digest differs.
    caller = {"runtime": {"metadata": {"image_id": R64}}}
    kept = deployment_metadata(_spec(_case(tmp_path / "a", image="repo:r35", image_id=R35)), caller)
    assert kept is caller

    # A caller label conflict is resolved by the actual digest, not the label.
    conflict = {"runtime": {"metadata": {"image": "repo:r64"}}}
    actual = deployment_metadata(_spec(_case(tmp_path / "b", image="repo:r35", image_id=R35)), conflict)
    assert actual["runtime"]["metadata"]["image_id"] == R35
    assert actual["runtime"]["metadata"]["image"] == "repo:r64"
    assert _revision(actual)["mx_quant_source_revision"] == "unpinned"

    explicit_revision = {"runtime": {"metadata": {
        "mx_quant_source_revision": "r64", "image": "repo:r35"}}}
    assert deployment_metadata(
        _spec(_case(tmp_path / "c", image="repo:r35", image_id=R35)),
        explicit_revision) is explicit_revision
    assert _revision(explicit_revision)["mx_quant_source_revision"] == "r64"


def test_absent_failed_or_foreign_status_stays_unpinned(tmp_path):
    raw = {"runtime": {"metadata": {}}}
    assert deployment_metadata(_spec(tmp_path / "missing"), raw) is raw
    failed = _case(tmp_path / "failed", image="repo:r64", image_id=R64, state="failed")
    assert deployment_metadata(_spec(failed), raw) is raw
    not_created = _case(tmp_path / "not-created", image="repo:r64", image_id=R64,
                        created=False)
    assert deployment_metadata(_spec(not_created), raw) is raw
    foreign = _case(tmp_path / "foreign", image="repo:r35", image_id=R35)

    class LabelDeclared(dict):
        pass
    foreign_spec = SimpleNamespace(source_case_dir=foreign, cell_id="case_pf_c2")
    status = json.loads((foreign / "status.json").read_text())
    status["spec"]["image"] = "repo:r64"
    (foreign / "status.json").write_text(json.dumps(status))
    _capture_status.cache_clear()
    assert deployment_metadata(foreign_spec, raw) is raw


def test_heldout_trace_change_keeps_fingerprint_and_no_target_open(tmp_path, monkeypatch):
    case = _case(tmp_path, image="repo:r64", image_id=R64)
    spec = z.CellSpec("case_pf_c2", "unit", "decode", MODEL_CASE,
                      "Qwen3.8-27B", 128, 2, 8, 4, 1, 1, 1, (1, 2, 4), 2,
                      source_case_dir=case)
    opened = []
    real_open = builtins.open

    def guard(path, *args, **kwargs):
        if "kernel_details" in str(path):
            opened.append(str(path))
            raise AssertionError(f"target opened: {path}")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guard)
    first = z._structure_fingerprint(spec)
    status = json.loads((case / "status.json").read_text())
    status["cells"][0].update(ttft_ms=999.0, tpot_ms=0.001,
                              export=[{"node": "pf_c2", "gz_bytes": 1}])
    (case / "status.json").write_text(json.dumps(status))
    _capture_status.cache_clear()
    z._COMPILED_MODELS.clear(); z._AGG_CACHE.clear()
    second = z._structure_fingerprint(spec)
    assert first == second
    assert not opened
