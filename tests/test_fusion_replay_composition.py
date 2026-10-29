"""Composed source recipes retain independently declared attention boundaries."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from mindie_profiler.normalized import kernel_rows
from mindie_profiler.structure_mapping import map_structure
from mindie_profiler.tensor_contracts import observed_contract
from test_heterogeneous_structure_cohorts import observation


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples/structure/acceptance-20261029"
SCENARIOS = [
    ("a3_qwen35", "qwen35-a3-tp4.json", 8192, "paged", 10),
    ("a3_qwen36", "qwen36-a3-tp4.json", 8192, "paged", 16),
    ("a5_qwen38", "qwen38-a5.json", 16384, "paged", 0),
    ("a5_qwen38", "qwen38-a5.json", 16384, "contiguous", 16),
]


@pytest.fixture(scope="module")
def cases_module():
    path = ROOT / "examples/structure/fusion_replay_cases.py"
    spec = importlib.util.spec_from_file_location("composed_replay_cases", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.MonkeyPatch.context() as patch:
        patch.syspath_prepend(str(path.parent))
        yield module


@pytest.fixture(scope="module", params=SCENARIOS,
                ids=["a3-q35-paged", "a3-q36-paged", "a5-q38-paged", "a5-q38-contiguous"])
def scenario(request, cases_module):
    structure = pytest.importorskip("mindie_sim.structure")
    sim = Path(structure.__file__).resolve().parents[1]
    key, filename, tokens, storage, instances = request.param
    path = sim / "examples/cases" / filename
    original = json.loads(path.read_text())
    old = {
        "declared_execution": {
            "phase": "prefill", "tokens": tokens, "context": 0, "sequences": 1},
        "declaration_source": {"case_path": str(path)},
    }
    variants = {row["name"]: row for row in cases_module.variants(key, old, BASE)}
    suffix = "combined" if key == "a5_qwen38" else "staged"
    selected = variants[f"{key}_{storage}_prefill_{suffix}-selected"]
    reference_name = (f"{key}_steady-selected" if storage == "contiguous"
                      else f"{key}_paged_prefill_q{tokens}-reference")
    return {
        "key": key, "storage": storage, "instances": instances,
        "original": original, "reference": variants[reference_name],
        "selected": selected, "sim": sim,
    }


def test_composition_preserves_the_case_except_explicit_recipe_and_storage(scenario):
    reference, selected = scenario["reference"], scenario["selected"]
    expected = deepcopy(reference["case"])
    source_name = ("paged-fia-a3-prefill-qwen36.json" if scenario["key"] == "a3_qwen36"
                   else "paged-fia-a3-prefill-qwen35.json")
    source_case = json.loads(
        (scenario["sim"] / "examples/source-families" / source_name).read_text())
    recipe = source_case["runtime"]["kernels"]["recipes"]["flash_attention_prefill"]
    kernels = expected["runtime"].setdefault("kernels", {})
    kernels.setdefault("recipes", {})["flash_attention_prefill"] = recipe
    policy = "auto" if scenario["storage"] == "contiguous" else "paged"
    expected["runtime"].setdefault("attention_policy", {})["kv_storage"] = policy
    if scenario["key"] == "a5_qwen38":
        steady = json.loads((scenario["sim"] / "data/verification"
                             / "matrix-cohort-wave4-20261029"
                             / "a5_qwen38-steady.case.json").read_text())
        kernels.setdefault("programs", {})["matmul"] = (
            steady["runtime"]["kernels"]["programs"]["matmul"])
    assert selected["case"] == expected
    assert selected["geometry"] == reference["geometry"]
    assert selected["case"]["model"] == scenario["original"]["model"]
    assert selected["case"]["machine"] == scenario["original"]["machine"]
    assert selected["declaration_key"] != reference["declaration_key"]
    assert selected["declaration_source"]["capture_dispatch_identity_verified"] is False
    assert "flash_attention_decode" not in kernels["recipes"]
    assert "kv_splits" not in recipe
    # Composition must not mutate the reference arm while merging nested maps.
    assert "flash_attention_prefill" not in reference["case"]["runtime"].get(
        "kernels", {}).get("recipes", {})


def test_recipe_selection_keeps_one_semantic_dag_and_respects_source_bindings(scenario):
    from mindie_sim.prediction.attention_prefill import StagedGQAPrefill
    from mindie_sim.prediction.matrix_steady import SteadyMatmul
    from mindie_sim.prediction.operator_analysis import target_operators
    from mindie_sim.prediction.program import RecipeBook

    reference, selected = scenario["reference"], scenario["selected"]
    before = target_operators(reference["case"], **reference["geometry"])
    after = target_operators(selected["case"], **selected["geometry"])
    assert len(before) == len(after)
    old_book = RecipeBook.from_mapping(reference["case"]["runtime"].get("kernels", {}))
    book = RecipeBook.from_mapping(selected["case"]["runtime"]["kernels"])
    attention_count = matrix_count = source_count = 0
    for old, new in zip(before, after):
        expected = old.to_dict()
        if new.family == "attention":
            expected["recipe"] = "flash_attention_prefill"
            assert isinstance(book.select(new), StagedGQAPrefill)
            geometry = dict(new.metadata)["gqa_prefill"]
            assert geometry["requests"] == ((selected["geometry"]["tokens"], 0),)
            attention_count += 1
        elif new.plan_required:
            # Source GDN kernels keep their own plan instead of the generic
            # matrix program or the independently selected attention recipe.
            assert type(book.select(new)) is type(old_book.select(old))
            assert new.recipe == old.recipe and new.source_boundary == old.source_boundary
            source_count += 1
        elif (dict(new.metadata).get("program_kind") == "matmul"
              and new.recipe not in book.recipes and new.family not in book.families):
            if scenario["key"] == "a5_qwen38":
                assert isinstance(book.select(new), SteadyMatmul)
            matrix_count += 1
        assert new.to_dict() == expected
    assert attention_count > 0 and matrix_count > 0
    if scenario["key"] == "a5_qwen38":
        assert source_count > 0


def test_real_mixed_step_rows_keep_the_same_population_and_exclude_other_storage(scenario):
    from mindie_sim.structure import export_structure

    path = ROOT / "tests/fixtures/mixed_step_body" / (scenario["key"] + ".csv")
    rows = [row for row in kernel_rows(path, rank_id="rank_0", rank_index=0)
            if row.kind == "FusedInferAttentionScore"]
    observed = observation(path, [row.event for row in rows])
    reports = []
    for value in (scenario["reference"], scenario["selected"]):
        manifest = export_structure(value["case"], **value["geometry"])
        reports.append(map_structure([observed], manifest))
    before, after = reports
    mapping_fields = (
        "event_id", "status", "node_ids", "subgraph_ids",
        "candidate_node_ids", "candidate_count", "observed_contract",
        "start_ns", "end_ns", "clipped_start_ns", "clipped_end_ns",
    )
    assert [{key: row[key] for key in mapping_fields} for row in after["event_mappings"]] == [
        {key: row[key] for key in mapping_fields} for row in before["event_mappings"]]
    window = after["windows"][0]
    assert window["event_count"] == len(rows)
    assert after["status_counts"].get("bound", 0) == 0
    assert window["nodes"] == window["layers"] == []
    if scenario["instances"] == 0:
        assert window["cohorts"] == []
        assert window["cohort_excluded_event_counts"] == {"no_tensor_candidates": len(rows)}
        return
    expected_kind = ("attention_paged_active_qkv" if scenario["storage"] == "paged"
                     else "attention_active_qkv")
    matching = [row for row in rows
                if observed_contract(row)[0] == expected_kind
                and row.input_shapes[0][0] == scenario["selected"]["geometry"]["tokens"]]
    assert len(matching) == 1
    group, = window["cohorts"]
    old_group, = before["windows"][0]["cohorts"]
    # The fixture retains one original event per descriptor, not a synthetic
    # repetition of the full capture's 11/17 occurrences.
    assert group["event_count"] == group["complete_event_count"] == 1
    assert group["activity_sum_ns"] == matching[0].end_ns - matching[0].start_ns
    assert group["declared_instance_count"] == scenario["instances"]
    for field in (
        "contract", "target_ids", "declared_instance_count", "event_count",
        "activity_sum_ns", "duration_ns", "busy_union_ns", "multiplicity",
    ):
        assert group[field] == old_group[field]
    assert group["physical_signature"] != old_group["physical_signature"]
    assert not group["occurrence_binding_implied"]
    assert group["multiplicity"]["steps_in_window"] is None
