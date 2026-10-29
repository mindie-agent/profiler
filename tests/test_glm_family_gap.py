"""Exact saved GLM call populations remain separate from body-span attribution."""
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("glm_gap", ROOT / "examples/structure/diagnose_glm_family_gap.py")
gap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gap)


@pytest.fixture(scope="module")
def c32():
    report = gap.read(ROOT / "examples/structure/acceptance-20261030-glm-operators-67ca7673/body-operator-family-scoreboard.json")
    case = next(row for row in report["cases"] if row["source_case_id"] == "a5_glm53flash_tp8_c32_p4k")
    return gap.diagnose_case(case)


def test_fp32_router_saved_population_and_cost_delta(c32):
    router = next(row for row in c32["families"] if row["declared_role"] == "router")
    assert router["all_calls"] == router["strict_calls"] == 1302
    assert router["strict_calls_per_forward"] == 42
    assert router["actual_p50_us"] == router["strict_observed_p50_us"] == 19.981
    assert router["actual_mean_us"] == pytest.approx(19.914667434715824)
    assert router["predicted_strict_mean_us"] == pytest.approx(19.74981818181818)
    assert router["baseline_observation_partition_identical"]
    assert router["cost_change_ms_per_forward"] == pytest.approx((19.74981818181818 - 159.6819393939394) * 42 / 1000)
    assert router["body_critical_path_attribution"] is False


def test_unmatched_recurrent_kda_keeps_observed_activity_without_zero_cost(c32):
    kda = next(row for row in c32["families"] if row["native_operator_type"] == "RecurrentKda")
    assert kda["all_calls"] == kda["unscored_calls"] == 1054
    assert kda["unscored_calls_per_forward"] == 34
    assert kda["unscored_activity_ms_per_forward"] == kda["measured_activity_ms_per_forward"] > 0
    assert kda["unscored_p50_us"] == kda["actual_p50_us"]
    assert kda["predicted_strict_mean_us"] is None
    assert kda["strict_activity_error_ms_per_forward"] is None
    assert kda["cost_change_ms_per_forward"] is None
    assert kda["semantic_regions"] == [("kda", "attention")]
    assert kda["saved_contract_sample_kinds"] == ["contract_unresolved"]


def test_a3_fused_native_retains_unfused_reference_without_promoting_accuracy():
    report = gap.read(ROOT / "examples/structure/acceptance-20261030-matrix-fix/glm-a3-livepre-86c1ee8f/body-operator-family-scoreboard.json")
    case = gap.diagnose_case(report["cases"][0])
    native = next(row for row in case["families"] if row["native_operator_type"] == "GroupedMatmulSwigluQuant")
    reference = next(row for row in case["conditional_references"] if row["native_operator_type"] == "GroupedMatmulSwigluQuant")
    assert native["strict_calls"] == 0
    assert reference["all_calls"] == native["all_calls"] == 1554
    assert reference["calls_per_forward"] == 42
    assert reference["actual_p50_us"] == 142.163
    assert reference["predicted_reference_mean_us"] == pytest.approx(285.78284272114325)
    assert reference["reference_activity_error_ms_per_forward"] == pytest.approx(6.021428799693421)
    assert reference["reference_boundary"] == "unfused_subgraph_reference"
    assert reference["strict_accuracy_implied"] is False
