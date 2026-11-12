"""Genuine original GLM51 cells through the existing piecewise predictor.

The only change is the measured cube service rate on the exact source-selected
``o_projection`` operator.  Physical work, stage work, state and every other
pipe remain the ordinary source values.  Heldout PMU is read after prediction.
"""
import copy
import csv
import gzip
import json
import os
from pathlib import Path
import statistics
import sys

import pytest

HERE = Path(__file__).resolve().parent
PROFILER = HERE.parent
SIM = PROFILER.parent / "sim"
CELLS = Path(os.environ.get(
    "MINDIE_TEST_ORIGINAL_CELLS",
    "/private/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl"))
SUPPLY = SIM / "tests" / "fixtures" / "r64_qbmm_dual_load" / "supply.json"
HARDWARE = "Ascend950DT_9582"
PROVENANCE = Path(os.environ.get(
    "MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT",
    "/private/tmp/mindie-7337-20261111-1457/header-provenance"))
DC_CSV = Path(os.environ.get(
    "MINDIE_TEST_R64_GLM51_HELDOUT_DC",
    "/Volumes/data/mindie-agent-workstreams/a5-multinode-fleet-rack06-20261107/"
    "out/glm51_dp16tp1ep16/dc_1k_c32/177.25.21.1/"
    "dp4_pp0_tp0_dcp0_ep4_rank0_1470_20261107100720369_ascend_pt/kernel_details.csv.gz"))
PF_CSV = Path(os.environ.get(
    "MINDIE_TEST_R64_GLM51_HELDOUT_PF",
    "/Volumes/data/mindie-agent-workstreams/a5-multinode-fleet-rack06-20261107/"
    "out/glm51_dp16tp1ep16/pf_2k_c1/177.25.21.1/"
    "dp6_pp0_tp0_dcp0_ep6_rank0_1466_20261107101241633_ascend_pt/kernel_details.csv.gz"))


def _z():
    if str(PROFILER / "examples" / "structure") not in sys.path:
        sys.path.insert(0, str(PROFILER / "examples" / "structure"))
    os.environ.setdefault("MINDIE_PROFILER_SOURCE", str(PROFILER))
    os.environ.setdefault("MINDIE_SIM_SOURCE", str(SIM))
    os.environ.setdefault("MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT", str(PROVENANCE))
    import zero_shot_piecewise_validation as z
    return z


def _cell(z, cell_id):
    for line in CELLS.open("rb"):
        raw = json.loads(line)
        if raw.get("cell_id") == cell_id:
            return z.cell_from_dict(raw).spec
    pytest.skip(f"original cell unavailable: {cell_id}")


def _op(z, spec):
    key = (spec.dataset, z._structure_fingerprint(spec))
    cached = z._COMPILED_MODELS[key]
    geometry = z._geometry(spec, spec.phase)
    sub = next(v for v in cached[3].values()
               if any(o.name == "o_projection" for o in v.operators))
    op = next(o for o in sub.operators if o.name == "o_projection")
    return op, geometry, cached[5], key


def _actual(path, m, owners):
    rows = []
    with gzip.open(path, "rt", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            if "QuantBatchMatmulV3" not in row.get("Name", ""):
                continue
            try:
                x = row["Input Shapes"].strip('"').split(";")[0]
                rm, rk = map(int, x.split(","))
                out = row["Output Shapes"].strip('"').split(";")[0]
                om, rn = map(int, out.split(","))
                block = int(row["Block Num"])
            except (KeyError, TypeError, ValueError):
                continue
            if (rm, rk, om, rn, block) != (m, 16384, m, 6144, owners):
                continue
            rows.append((float(row["Duration(us)"]),
                         float(row["aic_mac_time(us)"])))
    if not rows:
        pytest.skip(f"heldout rows unavailable: {path}")
    return tuple(statistics.median(values) for values in zip(*rows))


@pytest.mark.skipif(not CELLS.is_file(), reason="original cell dataset unavailable")
@pytest.mark.skipif(not SUPPLY.is_file(), reason="measured supply unavailable")
@pytest.mark.skipif(not DC_CSV.is_file() or not PF_CSV.is_file(),
                    reason="original captures unavailable")
@pytest.mark.parametrize("cell_id,m,owners,csv_path,expected_us,expected_mac_us", [
    ("glm51_dp16tp1ep16_dc_1k_c32", 2, 24, DC_CSV, 33.240142, 12.626),
    ("glm51_dp16tp1ep16_pf_2k_c1", 2048, 32, PF_CSV, 485.107739, 478.260),
])
def test_original_ordinary_operator_selected_rate_only(
        cell_id, m, owners, csv_path, expected_us, expected_mac_us):
    z = _z()
    spec = _cell(z, cell_id)
    first = z.predict_cell(spec)
    op, geometry, state, _ = _op(z, spec)
    base = op.evaluate(geometry, state)
    assert dict(base.work)["cube"] == (3221225472 if m == 2 else 412316860416)

    from mindie_sim.observations.calibration import import_profiler_supply
    rule = import_profiler_supply(
        SUPPLY, recipe="output", hardware=HARDWARE, required=True,
    )["service_regimes"][0]
    second = z.predict_cell(spec, measured_mac=rule)
    calibrated = op.evaluate(geometry, state)
    row = next(item for item in second.rows if item.name == "o_projection")
    assert row.native_call["typed"]["attrs"]["weight_layout"] == "FRACTAL_NZ"
    assert row.native_call["source"]["revision"] == "r64/8d422528"

    # The one-parameter proof: physical work and every non-MAC service are
    # byte-identical; only the cube stage's elapsed rate changed.
    assert calibrated.work == base.work
    assert calibrated.stage_work == base.stage_work
    assert dict((k, v) for k, v in calibrated.times if k != "cube") == \
        dict((k, v) for k, v in base.times if k != "cube")
    assert dict(calibrated.work)["cube"] == (3221225472 if m == 2 else 412316860416)
    assert float(dict(calibrated.times)["cube"]) * 1000 == pytest.approx(
        expected_mac_us, rel=1e-6)
    assert calibrated.duration_ms * 1000 == pytest.approx(expected_us, rel=1e-6)
    assert row.duration_ms * 1000 == pytest.approx(expected_us, rel=1e-6)

    # Synthetic wrong query scopes must fall back to the untouched analytic
    # result: wrong hardware, wrong role, and no source identity (R35).
    wrong_hw = z.predict_cell(spec, measured_mac=rule,
                              measured_hardware="Ascend910_9392")
    wrong_hw_row = next(item for item in wrong_hw.rows if item.name == "o_projection")
    assert wrong_hw_row.duration_ms * 1000 == pytest.approx(
        float(base.duration_ms) * 1000, rel=1e-12)
    wrong_rule = copy.deepcopy(rule)
    wrong_rule["match"]["recipe"] = "q_projection"
    wrong_role = z.predict_cell(spec, measured_mac=wrong_rule)
    wrong_role_row = next(item for item in wrong_role.rows if item.name == "o_projection")
    assert wrong_role_row.duration_ms * 1000 == pytest.approx(
        float(base.duration_ms) * 1000, rel=1e-12)

    # Read the independent heldout PMU only now.
    actual_elapsed, actual_mac = _actual(csv_path, m, owners)
    assert actual_mac == pytest.approx(12.615 if m == 2 else 477.821, rel=1e-9)
    assert float(dict(calibrated.times)["cube"]) * 1000 == pytest.approx(
        actual_mac, rel=0.01)
    assert row.duration_ms * 1000 == pytest.approx(actual_elapsed, rel=0.05)


def test_r35_source_identity_is_not_selected():
    z = _z()
    r35 = _cell(z, "glm53w8a8c8_dp32tp1ep32_on_prefill_1024_c2")
    from mindie_sim.observations.calibration import import_profiler_supply
    rule = import_profiler_supply(
        SUPPLY, recipe="output", hardware=HARDWARE, required=True,
    )["service_regimes"][0]
    base = z.predict_cell(r35)
    calibrated = z.predict_cell(r35, measured_mac=rule)
    base_row = next(item for item in base.rows if item.name == "o_projection")
    row = next(item for item in calibrated.rows if item.name == "o_projection")
    assert row.duration_ms == pytest.approx(base_row.duration_ms, rel=1e-12)
