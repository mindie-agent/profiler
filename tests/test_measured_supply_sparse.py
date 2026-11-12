"""End-to-end R64 SFA MTE1 measured resource service.

The actual train raw capture -> ordinary C7 producer -> standard sim import ->
normal z.predict_cell for the independent R64 PF2048 cell.  The sparse query
geometry is supplied explicitly; a raw Q shape alone never selects a rate.
"""
import csv
import gzip
import json
import os
from pathlib import Path
import statistics
import sys

import pytest

from mindie_profiler.analyze import analyze_profile

pytestmark = pytest.mark.skipif(
    os.environ.get("MINDIE_TEST_SFA_END_TO_END") != "1",
    reason="set MINDIE_TEST_SFA_END_TO_END=1 for the real-capture SFA end-to-end proof",
)

HERE = Path(__file__).resolve().parent
PROFILER = HERE.parent
SIM = PROFILER.parent / "sim"
FIXTURES = HERE / "fixtures" / "r64_sfa_service"
TRAIN_GEOMETRY = FIXTURES / "train_geometry.json"
DC_GEOMETRY = FIXTURES / "dc_geometry.json"
REAL_CAPTURE = (Path(os.environ["MINDIE_TEST_R64_GLM51_CSV"])
                if os.environ.get("MINDIE_TEST_R64_GLM51_CSV") else None)
CELLS = Path(os.environ.get(
    "MINDIE_TEST_ORIGINAL_CELLS",
    "/private/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl"))
PF_CSV = Path(os.environ.get(
    "MINDIE_TEST_R64_GLM51_HELDOUT_PF",
    "/Volumes/data/mindie-agent-workstreams/a5-multinode-fleet-rack06-20261107/"
    "out/glm51_dp16tp1ep16/pf_2k_c1/177.25.21.1/"
    "dp6_pp0_tp0_dcp0_ep6_rank0_1466_20261107101241633_ascend_pt/kernel_details.csv.gz"))
DC_CAPTURE = Path(os.environ.get(
    "MINDIE_TEST_R64_GLM51_HELDOUT_DC",
    "/Volumes/data/mindie-agent-workstreams/a5-multinode-fleet-rack06-20261107/"
    "out/glm51_dp16tp1ep16/dc_1k_c32/177.25.21.1/"
    "dp4_pp0_tp0_dcp0_ep4_rank0_1470_20261107100720369_ascend_pt/kernel_details.csv.gz"))
R35_CAPTURE = Path(os.environ.get(
    "MINDIE_TEST_R35_GLM53_CSV",
    "/Volumes/data/mindie-agent-workstreams/a5-multinode-fleet-rack08-20261107/"
    "out/glm53w8a8c8_dp32tp1ep32_on/prefill_1024_c2/177.31.26.1/"
    "dp8_pp0_tp0_dcp0_ep8_rank0_610_20261107055757142_ascend_pt/kernel_details.csv.gz"))


def _z():
    if str(PROFILER / "examples" / "structure") not in sys.path:
        sys.path.insert(0, str(PROFILER / "examples" / "structure"))
    os.environ.setdefault("MINDIE_PROFILER_SOURCE", str(PROFILER))
    os.environ.setdefault("MINDIE_SIM_SOURCE", str(SIM))
    os.environ.setdefault("MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT",
                          "/private/tmp/mindie-7337-20261111-1457/header-provenance")
    import zero_shot_piecewise_validation as z
    return z


def _cell(z, cell_id):
    for line in CELLS.open("rb"):
        raw = json.loads(line)
        if raw.get("cell_id") == cell_id:
            return z.cell_from_dict(raw).spec
    pytest.skip(f"original cell unavailable: {cell_id}")


def _actual_pf_mte1(path):
    rows = []
    with gzip.open(path, "rt", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            if "KvQuantSparseFlashAttention" not in row.get("Name", ""):
                continue
            try:
                q = int(row["Input Shapes"].strip('"').split(";")[0].split(",")[0])
                block = int(row["Block Num"])
                mix = int(row["Mix Block Num"])
            except (KeyError, TypeError, ValueError):
                continue
            if (q, block, mix) != (2048, 32, 64):
                continue
            rows.append(float(row["aic_mte1_time(us)"]))
    if not rows:
        pytest.skip(f"heldout SFA rows unavailable: {path}")
    return statistics.median(rows)


@pytest.mark.skipif(REAL_CAPTURE is None or not REAL_CAPTURE.is_file(),
                    reason="set MINDIE_TEST_R64_GLM51_CSV")
@pytest.mark.skipif(not CELLS.is_file() or not PF_CSV.is_file(),
                    reason="original PF cell/heldout unavailable")
def test_real_train_sparse_service_prices_independent_pf2048(tmp_path):
    geometry = json.loads(TRAIN_GEOMETRY.read_text())
    report = analyze_profile(
        REAL_CAPTURE, full_range=True, source="csv", top_n=1,
        hash_sources=True, aic_count=32, sparse_geometry=geometry)
    supply = report["enrichment"]["pmu_observations"]["measured_supply"]
    assert supply["source_identity"]["source_scope"] == "r64"
    records = supply["resource_services"]
    assert len(records) == 1
    record = records[0]
    assert record["resource"] == "mte1"
    assert record["native_type"] == "KvQuantSparseFlashAttention"
    assert record["source_identity"]["source_scope"] == "r64"
    assert record["hardware"] == "Ascend950DT_9582"
    assert record["owners"] == 32 and record["mix_block_num"] == 64
    assert record["measured_q_tokens"] == 1024
    assert record["measured_critical_bytes"] == 93782016
    assert record["measured_total_bytes"] == 1566572544
    assert record["event_count"] == 78
    assert record["median_mte1_us"] == pytest.approx(270.2975, rel=1e-9)
    assert record["rate_bytes_per_s"] == pytest.approx(346.9585e9, rel=1e-5)
    assert record["op_state"] == "dynamic" and record["phase"] == "prefill"

    # The same raw train without a geometry binding has no sparse service.
    bare = analyze_profile(
        REAL_CAPTURE, full_range=True, source="csv", top_n=1, aic_count=32)
    assert bare["enrichment"]["pmu_observations"]["measured_supply"][
        "resource_services"] == []

    z = _z()
    spec = _cell(z, "glm51_dp16tp1ep16_pf_2k_c1")
    c7_path = tmp_path / "train_c7.json"
    c7_path.write_text(json.dumps(report), encoding="utf-8")
    prediction = z.predict_cell(spec, measured_supply=c7_path)
    assert prediction.body_ms > 0
    key = (spec.dataset, z._structure_fingerprint(spec),
           f"{c7_path.resolve()}:{c7_path.stat().st_size}:{c7_path.stat().st_mtime_ns}")
    compiled = z._COMPILED_MODELS[key]
    metadata = dict(compiled[6].metadata)
    installed = metadata["profiler_measured_supply"]
    assert installed["resource_services"][0]["rate_bytes_per_s"] == pytest.approx(
        346.9585e9, rel=1e-5)
    features_hardware = (metadata.get("hardware_key")
                         or metadata.get("hardware_sku")
                         or metadata.get("device"))
    assert features_hardware == "Ascend950DT_9582"

    from mindie_sim.observations.resource_services import select_resource_service
    altered = [dict(record, hardware="Ascend910_9392")]
    assert select_resource_service(
        altered, hardware=features_hardware,
        source_identity=installed["source_identity"],
        q_len=2048, context=0, kv_len=2048, causal=True, owners=32,
        phase="prefill", op_state="dynamic") is None
    query = next(iter(z._geometry(spec, spec.phase).requests))
    pf = select_resource_service(
        installed["resource_services"], hardware="Ascend950DT_9582",
        source_identity=installed["source_identity"],
        q_len=query.q_len, context=query.context, kv_len=query.kv_len,
        causal=True, owners=32, phase="prefill", op_state="dynamic")
    assert pf is not None
    assert pf["query_critical_bytes"] == 373948416
    assert pf["time_us"] == pytest.approx(1077.790031, rel=1e-6)
    actual_mte1 = _actual_pf_mte1(PF_CSV)
    assert actual_mte1 == pytest.approx(1080.211, rel=1e-9)
    assert pf["time_us"] == pytest.approx(actual_mte1, rel=0.01)


@pytest.mark.skipif(not DC_CAPTURE.is_file(),
                    reason="independent R64 DC capture unavailable")
def test_dc_underfilled_geometry_does_not_receive_saturated_service():
    geometry = json.loads(DC_GEOMETRY.read_text())
    report = analyze_profile(
        DC_CAPTURE, full_range=True, source="csv", top_n=1,
        hash_sources=True, aic_count=32, sparse_geometry=geometry)
    supply = report["enrichment"]["pmu_observations"]["measured_supply"]
    assert supply["source_identity"]["source_scope"] == "r64"
    assert supply["resource_services"] == []


@pytest.mark.skipif(not R35_CAPTURE.is_file(),
                    reason="independent R35 capture unavailable")
def test_r35_same_shape_does_not_receive_r64_service():
    geometry = json.loads(TRAIN_GEOMETRY.read_text())
    report = analyze_profile(
        R35_CAPTURE, full_range=True, source="csv", top_n=1,
        hash_sources=True, aic_count=32, sparse_geometry=geometry)
    supply = report["enrichment"]["pmu_observations"]["measured_supply"]
    assert supply["source_identity"]["source_scope"] == "r35"
    assert supply["resource_services"] == []
