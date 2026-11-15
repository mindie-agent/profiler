"""Real r64 QBMM dual-load supply: rates, owners, boundaries and unknown data."""
import os
from pathlib import Path

import pytest

from mindie_profiler.analyze import analyze_profile
from mindie_profiler.pmu_derivation import (
    MEASURED_SUPPLY_SCHEMA,
    build_dual_load_service,
    derive_measured_supply,
)

FIXTURE = Path(__file__).parent / "fixtures" / "r64_qbmm_dual_load" / "kernel_details.csv"
REAL_CAPTURE = (
    Path(os.environ["MINDIE_TEST_R64_GLM51_CSV"])
    if os.environ.get("MINDIE_TEST_R64_GLM51_CSV") else None
)
R64 = "sha256:8d422528ac20a8babcbbf93762cde3b47d4db6c5f7ab777f4f1f65b32b89ab3e"
R35 = "sha256:5461a1a8253c6dc07868956166ad94751f84c82d00ff7791c59a9c1ac497de06"
REAL_R35_CAPTURE = Path(os.environ.get(
    "MINDIE_TEST_R35_GLM53_CSV",
    "/Volumes/data/mindie-agent-workstreams/a5-multinode-fleet-rack08-20261107/"
    "out/glm53w8a8c8_dp32tp1ep32_on/prefill_1024_c2/177.31.26.1/"
    "dp8_pp0_tp0_dcp0_ep8_rank0_610_20261107055757142_ascend_pt/kernel_details.csv.gz"))


def _report(path, deployment_image_id=None):
    return analyze_profile(path, full_range=True, source="csv", top_n=2,
                           aic_count=32, deployment_image_id=deployment_image_id)


def _pair(report):
    supply = report["enrichment"]["pmu_observations"]["measured_supply"]
    assert supply["schema_version"] == MEASURED_SUPPLY_SCHEMA
    assert supply["status"] == "measured_pair"
    return supply["pair"]


def test_real_fixture_separates_full_grid_from_tail_by_raw_counters():
    pair = _pair(_report(FIXTURE, R64))
    full, tail = pair["saturated"], pair["underfilled"]
    assert pair["identity"]["native_type"] == "QuantBatchMatmulV3"
    assert pair["identity"]["dtype"] == "fp8_e4m3"
    assert (pair["identity"]["n"], pair["identity"]["k"]) == (6144, 16384)
    assert (full["active_owners"], tail["active_owners"]) == (32, 24)
    assert (full["m"], tail["m"]) == (1024, 1)
    assert full["saturated"] is True
    assert tail["saturated"] is False
    assert full["mac_ratio"] > 0.9 > tail["mac_ratio"]
    assert full["limited_by"] == "aic_mac_ratio"
    assert tail["limited_by"] == "aic_mte2_ratio"
    assert full["rate_flops_per_s"] > tail["rate_flops_per_s"]
    assert full["logical_flops"] == full["issued_flops"] == 206158430208
    assert tail["logical_flops"] == 201326592
    assert tail["issued_flops"] == 3221225472
    # The rate is issued active-pipe work, never the elapsed kernel duration.
    assert full["rate_flops_per_s"] == pytest.approx(
        full["issued_flops"] / (full["pipe_times_ns"]["aic_mac_time"] * 1e-9))
    assert tail["rate_flops_per_s"] == pytest.approx(
        tail["issued_flops"] / (tail["pipe_times_ns"]["aic_mac_time"] * 1e-9))
    assert tail["effective_rate_flops_per_s"] != pytest.approx(tail["rate_flops_per_s"])
    assert 0.2 < pair["service_ratio"]["underfilled_over_saturated"] < 0.35
    rule = pair["service_regime"]
    assert rule["response"]["kind"] == "measured_dual_load"
    assert rule["response"]["scope"] == "matrix_pipe_service"
    assert rule["execution"]["kind"] == "mac_service"
    assert set(rule["coordinates"]) == {"m", "n", "k"}
    assert rule["response"]["owner_grid"] == {
        "tile_m": 128, "tile_n": 256, "cores": 32}
    assert rule["response"]["issue"]["m_alignment"] == 16
    assert rule["provenance"]["not_end_to_end_kernel_latency"] is True
    assert "work_min" not in rule["response"]["loads"][0]
    assert [load["id"] for load in rule["response"]["loads"]] == ["saturated", "underfilled"]


def test_missing_counters_and_shape_stay_unknown_instead_of_using_elapsed_time():
    record = derive_measured_supply(
        {"aic_total_time": 100.0},
        input_shapes="not-a-shape",
        input_dtypes="DT_FLOAT8_E4M3FN",
        output_shapes='"1,6144"',
        output_dtypes="DT_BF16",
        block_num=None,
        complete_in_window=True,
        duration_ns=10_000,
    )
    assert record["status"] == "unknown"
    assert record["rate_flops_per_s"] is None
    assert "input_matrix_shape_not_parsed" in record["missing"]
    assert "block_num_missing" in record["missing"]
    assert "aic_mac_time_missing" in record["missing"]
    assert record["duration_ns"] == 10_000  # retained as provenance, not rate


def test_physical_capacity_must_be_declared_not_inferred_from_sampled_block_num():
    report = analyze_profile(
        FIXTURE, full_range=True, source="csv", top_n=2)
    supply = report["enrichment"]["pmu_observations"]["measured_supply"]
    assert supply["status"] == "not_available"
    assert supply["pair"] is None
    assert "measured_supply_physical_owners_not_declared" in {
        item["code"] for item in supply["limitations"]}


def test_pair_construction_rejects_a_non_saturated_full_load():
    pair = _pair(_report(FIXTURE, R64))
    full = dict(pair["saturated"])
    tail = dict(pair["underfilled"])
    full["mac_ratio"] = 0.4
    with pytest.raises(ValueError, match="measured_supply_saturated_mac_ratio_below_threshold"):
        build_dual_load_service(full, tail, physical_owners=32)


@pytest.mark.skipif(REAL_CAPTURE is None or not REAL_CAPTURE.is_file(),
                    reason="set MINDIE_TEST_R64_GLM51_CSV to the real installed capture")
def test_real_installed_capture_pair_is_supported_by_the_same_public_path():
    pair = _pair(_report(REAL_CAPTURE))
    full, tail = pair["saturated"], pair["underfilled"]
    assert (full["active_owners"], tail["active_owners"]) == (32, 24)
    assert (full["event_count"], tail["event_count"]) == (78, 1326)
    assert full["issued_flops"] == 206158430208
    assert tail["logical_flops"] == 201326592
    assert tail["issued_flops"] == 3221225472
    assert full["rate_flops_per_s"] == pytest.approx(862.118639267344e12, rel=1e-9)
    assert tail["rate_flops_per_s"] == pytest.approx(255.1263640107714e12, rel=1e-9)
    assert full["pipe_times_ns"]["aic_mac_time"] == pytest.approx(239130, rel=1e-9)
    assert tail["pipe_times_ns"]["aic_mac_time"] == pytest.approx(12626, rel=1e-9)
    assert pair["identity"]["n"] == 6144
    assert pair["identity"]["k"] == 16384
    assert pair["service_regime"]["execution"]["tile_m"] == 128
    assert pair["service_regime"]["execution"]["tile_n"] == 256

def test_declared_r35_source_keeps_generic_measurements_without_r64_math():
    supply = _report(FIXTURE, R35)["enrichment"]["pmu_observations"]["measured_supply"]
    assert supply["status"] == "not_available"
    assert supply["pair"] is None
    assert supply["source_identity"]["source_scope"] == "r35"
    assert supply["candidate_conditions"] > 0
    assert all(item.get("issue_rule") is None for item in supply["candidates"])
    assert all(item.get("issued_flops") == item.get("logical_flops")
               for item in supply["candidates"] if item.get("status") == "measured")
    from mindie_sim.observations.calibration import import_profiler_supply
    with pytest.raises(ValueError, match="not_available"):
        import_profiler_supply(
            supply, hardware="Ascend950DT_9582", required=True)


@pytest.mark.skipif(not REAL_R35_CAPTURE.is_file(),
                    reason="set MINDIE_TEST_R35_GLM53_CSV to the real installed R35 capture")
def test_real_r35_capture_stays_r35_and_never_gets_r64_issue_rule():
    supply = _report(REAL_R35_CAPTURE)["enrichment"]["pmu_observations"]["measured_supply"]
    assert supply["status"] == "not_available"
    assert supply["pair"] is None
    assert supply["source_identity"]["source_scope"] == "r35"
    assert supply["source_identity"]["image_digest"].startswith("5461a1a8")
    assert supply["candidate_conditions"] > 0
    assert all(item.get("issue_rule") is None for item in supply["candidates"])
    assert all(item.get("issued_flops") == item.get("logical_flops")
               for item in supply["candidates"] if item.get("status") == "measured")
    from mindie_sim.observations.calibration import import_profiler_supply
    with pytest.raises(ValueError, match="not_available"):
        import_profiler_supply(
            supply, hardware="Ascend950DT_9582", required=True)

def test_bare_csv_keeps_generic_measurements_without_r64_stamp():
    supply = analyze_profile(
        FIXTURE, full_range=True, source="csv", top_n=2, aic_count=32,
    )["enrichment"]["pmu_observations"]["measured_supply"]
    assert supply["status"] == "not_available"
    assert supply["pair"] is None
    assert supply["source_identity"]["source_scope"] == "absent"
    assert supply["candidate_conditions"] > 0
    assert all(item.get("issue_rule") is None for item in supply["candidates"])
    assert any(item.get("status") == "measured" for item in supply["candidates"])
