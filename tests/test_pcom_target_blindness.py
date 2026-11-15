"""Target blindness: the normal forecast never reads an original target table.

[Role]
  Verify `predict_cell` is a function of the declared model/runtime case, not
  of an original cell's `kernel_details` rows.  The same prediction must survive
  removing, reordering or fabricating those rows, and changing the source case
  directory must not change the physical result.

[Invariants]
  * Any attempt to open a `kernel_details` path during the forecast fails the
    test, even if the file is a valid fabricated capture.
  * The guarded target lives under the declared `source_case_dir`, so the old
    case-id/path binding, if restored, would read it.
  * A bounded ragged route is counted in aggregate cells but excluded from the
    formal 10% pass denominator.

[Timeouts & Locks]
  A few local structural forecasts; no device, network or subprocess.

[Side-Effect Policy]
  Writes only under pytest tmp_path.
"""
from __future__ import annotations

import builtins
import gzip
import sys
from pathlib import Path

import pytest

pytest.importorskip("mindie_sim")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
import zero_shot_piecewise_validation as z  # noqa: E402
from pcom_coverage import conditional_entries, coverage  # noqa: E402

MODEL_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen38_highconc_c4.json"


def _spec(source_case_dir: Path):
    return z.CellSpec("pcom-blind", "unit", "decode", MODEL_CASE,
                      "Qwen3.8-27B", 128, 2, 8, 4, 1, 1, 1, (1, 2, 4), 2,
                      source_case_dir=source_case_dir)


def _sentinel(case_dir: Path, rows: str, *, writer=builtins.open) -> Path:
    path = case_dir / "cell" / "host" / "dp0_pp0_tp0_dcp0_ep0_rank0_1_ascend_pt"
    path.mkdir(parents=True, exist_ok=True)
    with writer(path / "kernel_details.csv.gz", "wb") as handle:
        handle.write(gzip.compress(rows.encode()))
    return path


def _shape(prediction):
    return (prediction.per_layer, prediction.subgraphs, prediction.body_ms,
            prediction.rows, prediction.decode_body_ms, prediction.prefill_body_ms)


def test_normal_forecast_never_opens_target_kernel_details(tmp_path, monkeypatch):
    case_dir = tmp_path / "case"
    _sentinel(case_dir, "Type,Name,Input Shapes,Output Shapes\n"
                         "DynamicMxQuant,MoeTokenPermute,1024,6144,999999\n")
    opened: list[str] = []

    real_open = builtins.open
    real_path_open = Path.open
    real_gzip = gzip.open

    def guard_open(path, *args, **kwargs):
        if "kernel_details" in str(path):
            opened.append(str(path))
            raise AssertionError(f"forecast opened target kernel_details: {path}")
        return real_open(path, *args, **kwargs)

    def guard_path_open(self, *args, **kwargs):
        if "kernel_details" in str(self):
            opened.append(str(self))
            raise AssertionError(f"forecast opened target kernel_details: {self}")
        return real_path_open(self, *args, **kwargs)

    def guard_gzip(path, *args, **kwargs):
        if "kernel_details" in str(path):
            opened.append(str(path))
            raise AssertionError(f"forecast opened target kernel_details: {path}")
        return real_gzip(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guard_open)
    monkeypatch.setattr(Path, "open", guard_path_open)
    monkeypatch.setattr(gzip, "open", guard_gzip)

    z._COMPILED_MODELS.clear()
    z._AGG_CACHE.clear()
    first = z.predict_cell(_spec(case_dir))
    assert first.layers > 0 and first.body_ms > 0

    # Reordered+fabricated rows, then removal, then a different source dir:
    # the declared model/runtime inputs are unchanged.
    _sentinel(case_dir, "Type,Name,Input Shapes,Output Shapes\n"
                        "MoeDistributeDispatchV3,MoeDistributeDispatchV3,1,6144,0\n")
    z._COMPILED_MODELS.clear()
    z._AGG_CACHE.clear()
    second = z.predict_cell(_spec(case_dir))
    assert _shape(first) == _shape(second)

    for path in case_dir.rglob("kernel_details.csv.gz"):
        path.unlink()
    z._COMPILED_MODELS.clear()
    z._AGG_CACHE.clear()
    third = z.predict_cell(_spec(case_dir))
    assert _shape(first) == _shape(third)

    other = tmp_path / "other-case"
    other.mkdir()
    z._COMPILED_MODELS.clear()
    z._AGG_CACHE.clear()
    fourth = z.predict_cell(_spec(other))
    assert _shape(first) == _shape(fourth)
    assert not opened


def test_canonical_aggregate_keeps_mixed_bucket_samples():
    bounded = z.Comparison("L1", "collective", "collective", 0.016945, 0.927560,
                           "dispatch", "g", "link", "f", 1, cell_id="partial",
                           conditional=True)
    exact = z.Comparison("L1", "collective", "collective", 0.900000, 0.927560,
                         "dispatch", "g", "link", "f", 1, cell_id="matched")
    row = z.aggregate((bounded, exact))[0]
    assert row["cells"] == 2
    assert row["samples"] == 2
    assert "bounded_cells" not in row
    assert conditional_entries((bounded, exact)) == (bounded,)
    # Coverage is out-of-band, never a reason to drop a measured original row.
    partial = z.Prediction("partial", "unit", 1, {}, {}, 1.0, None, None, (),
                           notes=("bounded_moe_route",), formal_point=False,
                           partial_targets=("L1:collective", "L2:moe", "L3:body"))
    assert partial.formal_point is False
    assert "bounded_moe_route" in partial.notes
    assert coverage((partial,)) == {"cells": 1, "formal_cells": 0,
                                    "partial_cells": 1,
                                    "unresolved_targets": ("L1:collective", "L2:moe", "L3:body")}

def test_partial_body_marks_body_derived_l4_conditional():
    spec = _spec(ROOT / "examples" / "structure" / "cases")
    trace = z.KernelTrace(2000.0, {"gemm": 2000.0}, {"MatMulV3": 2000.0},
                          {"MatMulV3": 1}, (2000.0,))
    cell = z.MeasuredCell(spec, (), trace, None, 15.0, 2.0, 1, True)
    partial = z.Prediction(
        "pcom-blind", "Qwen3.8-27B", 1, {"gemm": 1.0}, {}, 15.0, 10.0, None,
        (), (), 15.0, 10.0, formal_point=False,
        partial_targets=("L1:collective", "L2:moe", "L3:body"))
    l4 = [item for item in z.compare_cell(cell, partial)
          if item.level == "L4"]
    assert l4 and all(item.conditional for item in l4)
    assert l4[0].measured_ms == 15.0
    assert l4[0].step_details

    formal = z.Prediction(
        "pcom-blind", "Qwen3.8-27B", 1, {"gemm": 1.0}, {}, 15.0, 10.0, None,
        (), (), 15.0, 10.0)
    formal_l4 = [item for item in z.compare_cell(cell, formal)
                 if item.level == "L4"]
    assert formal_l4 and not any(item.conditional for item in formal_l4)

