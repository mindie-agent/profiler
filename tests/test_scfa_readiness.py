"""Real SCFA branches preserve source conditions and independent hardware."""
from copy import deepcopy
import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def lane(monkeypatch):
    pytest.importorskip("mindie_sim.prediction.family_sharedkv",
                        reason="requires matching optional sim source")
    monkeypatch.syspath_prepend(str(ROOT / "examples/structure"))
    return importlib.import_module("replay_scfa_readiness")


@pytest.mark.parametrize("key,tokens,topk,selected_count", [
    ("a3_v4f", 4096, 512, 21),
    ("a3_v4pro", 1024, 1024, 30),
])
def test_source_variant_keeps_case_hardware_and_matches_only_real_indexed_branch(
    lane, key, tokens, topk, selected_count,
):
    from mindie_profiler.normalized import kernel_rows
    from mindie_profiler.tensor_contracts import observed_contract
    from mindie_sim import target_operators
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure_contracts import comparison_scope, predicted_contract

    _, baseline = lane._baseline(key)
    before = deepcopy(baseline)
    variant = lane.scfa_variant(key, baseline)
    assert baseline == before
    assert variant["case"]["machine"] == baseline["case"]["machine"]
    assert variant["case"]["model"] == baseline["case"]["model"]
    assert variant["geometry"] == baseline["geometry"]
    assert variant["declaration_source"]["case_sha256"] == baseline[
        "declaration_source"]["case_sha256"]
    expected = deepcopy(baseline["case"])
    expected.setdefault("runtime", {}).setdefault("kernels", {}).setdefault("lowerings", {})[
        "sharedkv_attention"] = lane.SELECTOR
    assert variant["case"] == expected

    base_ops = target_operators(baseline["case"], **baseline["geometry"], resource_fusion=False)
    selected_ops = target_operators(variant["case"], **variant["geometry"], resource_fusion=False)
    assert len(base_ops) == len(selected_ops)
    selected = []
    for original, operator in zip(base_ops, selected_ops, strict=True):
        if operator.recipe == lane.IMPLEMENTATION:
            selected.append(operator)
            assert operator.deps == original.deps
            assert operator.local_shape == original.local_shape
        else:
            assert operator == original
    assert len(selected) == selected_count
    fixture = ROOT / f"tests/fixtures/fusion_contracts/{key}.csv"
    row = next(row for row in kernel_rows(fixture)
               if row.kind == "SparseAttnSharedkv"
               and row.input_shapes[4] == (tokens, 1, topk))
    contract = observed_contract(row)
    assert contract is not None
    for operator in selected:
        value = operator.to_dict(include_work=False)
        assert value["source_boundary"] == "kernel"
        assert predicted_contract(value) == contract
        assert "dispatch_not_compared" in str(comparison_scope(value))

    device = parse_case(variant["case"]).machine.dies[0]
    # The existing explicit legacy device input overrides the nominal profile
    # rate; the source selection must not silently erase that independent input.
    assert dict(device.rates)["mte3"] == baseline["case"]["machine"]["device"][
        "mte_bw_bytes_per_s"]
    assert device.units("mte3") == device.units("mte2_aiv") == 40
    assert device.units("mte1") == device.units("mte2_aic") == device.units("fixpipe") == 20


@pytest.mark.parametrize("key,expected", [("a3_v4f", 21), ("a3_v4pro", 120)])
def test_focused_projection_does_not_recount_other_real_sparse_cohorts(lane, key, expected):
    mapping = lane.read(lane.BASE / f"fusion-cohort-{key}-reference.mapping.json")
    indexed = [
        cohort for window in mapping["windows"] for cohort in window["cohorts"]
        if cohort["native_operator_type"] == "SparseAttnSharedkv"
        and cohort.get("structural_classification", {}).get("common", {}).get(
            "structure", {}).get("indexer") is True
    ]
    assert indexed
    selected_ids = {key for cohort in indexed for key in cohort["target_ids"]}
    original_ids = [[cohort["cohort_id"] for cohort in window["cohorts"]]
                    for window in mapping["windows"]]
    focused, counts = lane._select_cohorts(mapping, selected_ids)
    assert counts == {"SparseAttnSharedkv": expected}
    actual = [cohort for window in focused["windows"] for cohort in window["cohorts"]]
    assert actual == indexed
    assert len({row["cohort_id"] for row in actual}) == len(actual)
    assert original_ids == [[row["cohort_id"] for row in window["cohorts"]]
                            for window in mapping["windows"]]
    # A partial selection cannot silently move a complete real event to one of
    # several same-contract layer subsets.
    with pytest.raises(ValueError, match="mixes_selected_and_unselected"):
        lane._select_cohorts(mapping, {next(iter(selected_ids))})
