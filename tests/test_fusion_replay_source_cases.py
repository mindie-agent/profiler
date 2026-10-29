"""Real retained descriptors exercise additional independent source arms."""
from copy import deepcopy
import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples/structure/acceptance-20261029"


@pytest.fixture
def modules(monkeypatch):
    pytest.importorskip("mindie_sim.prediction.family_situ_mx",
                        reason="requires matching optional sim source")
    monkeypatch.syspath_prepend(str(ROOT / "examples/structure"))
    return (importlib.import_module("fusion_replay_cases"),
            importlib.import_module("fusion_replay_source_cases"))


def test_glm_shared_quant_keeps_independent_case_and_matches_real_decode_descriptor(modules):
    factory, source = modules
    from mindie_profiler.normalized import kernel_rows
    from mindie_profiler.tensor_contracts import observed_contract
    from mindie_sim import target_operators
    from mindie_sim.prediction.mechanism import Geometry
    from mindie_sim.prediction.program import RecipeBook
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure_contracts import predicted_contract

    old = factory._read(BASE / "body-a3_glm53_decode.json")
    baseline = factory._shared_quant_variant("a3_glm53_decode", old, BASE)
    before = deepcopy(baseline)
    value, = source.source_program_variants("a3_glm53_decode", baseline)
    assert baseline == before
    expected = deepcopy(baseline["case"])
    expected["machine"]["backend"] = "ascend"
    expected["runtime"]["kernels"]["lowerings"]["indexed_attention"] = {
        "implementation": source.INDEXED_IMPLEMENTATION,
        "options": {"scratch_policy": "offchip"},
    }
    assert value["case"] == expected
    assert value["geometry"] == baseline["geometry"]
    assert value["declaration_source"]["case_sha256"] == baseline[
        "declaration_source"]["case_sha256"]

    original = target_operators(baseline["case"], **baseline["geometry"], resource_fusion=False)
    selected = target_operators(value["case"], **value["geometry"], resource_fusion=False)
    actual = next(row for row in kernel_rows(
        ROOT / "tests/fixtures/fusion_contracts/a3_glm53_decode.csv")
                  if row.kind == "SparseFlashAttention")
    contract = observed_contract(actual)
    changed = []
    for left, right in zip(original, selected, strict=True):
        if right.recipe == source.INDEXED_IMPLEMENTATION:
            changed.append(right)
            assert right.deps == left.deps
            assert right.local_shape == left.local_shape
            assert right.source_boundary == "kernel"
            assert predicted_contract(right.to_dict(include_work=False)) == contract
        else:
            assert right == left
    assert len(changed) == 78
    case = parse_case(value["case"])
    geometry = Geometry.from_devices(case.machine.dies[:case.runtime.parallel.tp])
    prepared, _ = RecipeBook.from_mapping(case.runtime.kernels).prepare(changed[0], geometry)
    assert prepared.hbm_bytes > 0
    assert dict(prepared.metadata)["resource_work"]["mte2_aiv"] > 0


@pytest.mark.parametrize("decode,rows", [(False, 8192), (True, 1)])
def test_kimi_complete_situ_program_keeps_checkpoint_and_other_fusions(modules, decode, rows):
    factory, source = modules
    from mindie_profiler.normalized import kernel_rows
    from mindie_profiler.tensor_contracts import observed_contract
    from mindie_sim import target_operators
    from mindie_sim.prediction.mechanism import Geometry
    from mindie_sim.prediction.program import RecipeBook
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure_subgraphs import subgraph_contract

    old = factory._read(BASE / "body-a5_kimi_k3.json")
    baseline = factory._variant("a5_kimi_k3", old, BASE, decode=decode, checkpoint=True)
    ordinary = factory._variant("a5_kimi_k3", old, BASE, decode=decode)
    assert source.source_program_variants("a5_kimi_k3", ordinary) == []
    before = deepcopy(baseline)
    value, = source.source_program_variants("a5_kimi_k3", baseline)
    assert baseline == before
    expected = deepcopy(baseline["case"])
    options = expected["runtime"]["kernels"]["lowerings"]["native_fusion"]["options"]
    options["traffic_profile"]["situ_quant"] = "preserve_workspaces"
    options.setdefault("program_profiles", {})["situ_quant"] = source.SITU_PROGRAM
    assert value["case"] == expected
    assert value["geometry"] == baseline["geometry"]
    actual = next(row for row in kernel_rows(
        ROOT / "tests/fixtures/fusion_contracts/a5_kimi_k3.csv")
                  if row.kind == "SituMxQuant" and row.input_shapes[0][0] == rows)
    observed = observed_contract(actual)
    semantic = target_operators(value["case"], **value["geometry"], resource_fusion=False)
    baseline_semantic = target_operators(
        baseline["case"], **baseline["geometry"], resource_fusion=False)
    assert semantic == baseline_semantic
    physical = target_operators(value["case"], **value["geometry"])
    selected = [op for op in physical if op.recipe == source.SITU_PROGRAM]
    assert selected
    assert all(op.source_boundary == "kernel" for op in selected)
    matched = []
    for op in selected:
        meta = dict(op.metadata)
        contract = subgraph_contract({
            "role": meta["fusion_role"], "tensor_view": meta["fusion_tensor_view"],
        })
        if contract == observed:
            matched.append(op)
        else:
            # The independent dense first layer has a wider SiTU. It is not
            # silently attached to the real shared-expert width-768 fixture.
            assert op.local_shape == (rows, 4224)
    assert len(matched) == 92
    case = parse_case(value["case"])
    geometry = Geometry.from_devices(case.machine.dies[:case.runtime.parallel.tp])
    prepared, _ = RecipeBook.from_mapping(case.runtime.kernels).prepare(matched[0], geometry)
    # The complete BF16 2H -> FP8 H + E8M0 call has no materialized SiTU
    # intermediate. This payload holds for both real capture row geometries.
    assert prepared.hbm_bytes == rows * (1536 * 2 + 768 + 24)
    assert prepared.mte3_bytes == rows * (768 + 24)
    assert dict(prepared.metadata)["resource_work"]["mte2_aiv"] == rows * 1536 * 2
    other_roles = [op for op in physical
                   if dict(op.metadata).get("fusion_role") == "grouped_gate_up_situ_quant"]
    assert other_roles
    assert all(op.recipe != source.SITU_PROGRAM for op in other_roles)
