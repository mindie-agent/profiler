"""Independent FP32 source selection against retained real A3 compressor rows."""
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path

import pytest

from mindie_profiler.normalized import kernel_rows
from mindie_profiler.structure_mapping import map_structure
from test_heterogeneous_structure_cohorts import observation


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples/structure/acceptance-20261029"


@pytest.fixture(scope="module")
def cases_module():
    path = ROOT / "examples/structure/fusion_replay_cases.py"
    spec = importlib.util.spec_from_file_location("compressor_replay_case_controls", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.MonkeyPatch.context() as patch:
        patch.syspath_prepend(str(path.parent))
        yield module


@pytest.fixture(scope="module", params=["a3_v4f", "a3_v4pro"])
def scenario(request, cases_module):
    structure = pytest.importorskip("mindie_sim.structure")
    sim = Path(structure.__file__).resolve().parents[1]
    filename, tokens = {
        "a3_v4f": ("v4f-a3-w8a8-tp8.json", 4096),
        "a3_v4pro": ("v4pro-a3-w4a8-tp16.json", 1024),
    }[request.param]
    path = sim / "examples/cases" / filename
    original = json.loads(path.read_text())
    old = {
        "declared_execution": {"phase": "prefill", "tokens": tokens, "context": 0, "sequences": 1},
        "declaration_source": {"case_path": str(path)},
    }
    variants = {row["name"]: row for row in cases_module.variants(request.param, old, BASE)}
    selected = [variants[request.param + suffix] for suffix in (
        "-reference", "-selected", "_compressor_fp32-reference")]
    return request.param, original, selected


def test_source_variant_changes_only_compressor_norm_precision_and_preserves_old_choices(scenario):
    from mindie_sim.prediction.structure import parse_case

    key, original, variants = scenario
    default, selected, conditional = variants
    assert default["case"]["model"] == selected["case"]["model"] == original["model"]
    assert conditional["declaration_key"] != default["declaration_key"] == selected["declaration_key"]
    old = parse_case(selected["case"]).model.layer_plans
    new = parse_case(conditional["case"]).model.layer_plans
    changed = []
    for before, after in zip(old, new):
        old_fields, new_fields = asdict(before), asdict(after)
        if before.compressor_kind != "none" and before.compress_ratio > 1:
            assert before.compressor_norm_dtype == "bf16"
            assert after.compressor_norm_dtype == "fp32"
            old_fields["compressor_norm_dtype"] = "fp32"
            changed.append(str(before.index))
        assert old_fields == new_fields
    assert set(changed) == set(conditional["declaration_source"]["model_layer_overrides"])
    # HC's independently chosen native resource boundary stays intact; no
    # compressor launch or reuse is invented by changing a parameter dtype.
    assert (selected["case"]["runtime"]["kernels"]
            == conditional["case"]["runtime"]["kernels"])
    assert conditional["declaration_source"]["source_evidence"]["compressor_norm"][
        "capture_dispatch_identity_verified"] is False
    assert conditional["case"]["model"]["layer_overrides"]
    assert "layer_overrides" not in original["model"]


def test_real_compressor_rows_gain_three_cohorts_but_only_unfused_references(scenario):
    from mindie_sim.structure import export_structure
    from mindie_sim.cohort_comparison import compare_cohorts

    key, _, variants = scenario
    selected, conditional = variants[1:]
    geometry = conditional["geometry"]
    before = export_structure(selected["case"], **geometry)
    after = export_structure(conditional["case"], **geometry)
    path = ROOT / "tests/fixtures/fusion_contracts" / (key + ".csv")
    events = [row.event for row in kernel_rows(path, rank_id="rank_0", rank_index=0)
              if row.kind == "Compressor"]
    obs = observation(path, events)
    assert map_structure([obs], before)["windows"][0]["cohorts"] == []
    mapped = map_structure([obs], after)
    groups = mapped["windows"][0]["cohorts"]
    assert len(groups) == len(events) == 3
    assert sum(group["event_count"] for group in groups) == 3
    assert {group["declared_instance_count"] for group in groups} == (
        {20, 21} if key == "a3_v4f" else {30, 31})
    old_groups = {group["subgraph_id"]: group for group in before["subgraphs"]
                  if group["role"] == "compressor"}
    new_groups = [group for group in after["subgraphs"] if group["role"] == "compressor"]
    for group in new_groups:
        old_group = old_groups[group["subgraph_id"]]
        norm_width = group["contract"][3][3][0][0]
        assert group["physical_work"]["launches"] == old_group["physical_work"]["launches"] == 5
        assert (group["physical_work"]["mte2_bytes"] - old_group["physical_work"]["mte2_bytes"]
                == norm_width * 2)
        assert group["physical_work"]["mte3_bytes"] == old_group["physical_work"]["mte3_bytes"]
        assert not group.get("resource_boundary")
    del before, after
    compared = compare_cohorts(conditional["case"], mapped)
    rows = compared["windows"][0]["cohorts"]
    assert len(rows) == 3
    assert all(row["status"] == "reference_only" for row in rows)
    assert all(row["reason"] == "unfused_subgraph_is_not_the_observed_native_kernel" for row in rows)
    assert all(row["comparison"] is None and row["accuracy_pass"] is None for row in rows)
    assert all(row["prediction"]["boundary"] == "unfused_subgraph_reference" for row in rows)
