"""Inventory joins preserve real original-row identities and replay generations."""
from hashlib import sha256
import importlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def inventory(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "examples/structure"))
    return importlib.import_module("refresh_fusion_inventory")


@pytest.fixture
def census(inventory):
    return {
        source["capture_id"]: source
        for source in inventory.read(inventory.BASE / "fusion-capture-field-coverage.json")["sources"]
    }


def test_new_real_fixture_registries_add_branches_without_recounting_original_rows(
    inventory, census,
):
    baseline, _ = inventory.fixture_rows(
        census, registries=(("fusion_contracts/provenance.json", None),))
    current, evidence = inventory.fixture_rows(census)

    def lines(rows, key):
        return [row["source_csv_line"] for row in rows[key]]

    kimi = ("a5_kimi_k3", "GroupedMatmul")
    assert 30512 not in lines(baseline, kimi)
    assert {30512, 30561, 30568, 30574} <= set(lines(current, kimi))
    # Source row 53 occurs in three retained slices, including a registry
    # without capture_id. Only its pinned original SHA identifies the capture.
    assert lines(current, kimi).count(53) == 1
    fia = ("a3_qwen35", "FusedInferAttentionScore")
    assert 4458 not in lines(baseline, fia)
    assert 4458 in lines(current, fia)
    assert next(row for row in current[fia] if row["source_csv_line"] == 4458)["contract"]
    for records in current.values():
        assert len(records) == len({row["source_csv_line"] for row in records})
    assert evidence["unique_original_record_count"] == sum(map(len, current.values()))
    assert evidence["unique_original_record_count"] > sum(map(len, baseline.values()))
    excluded = [
        source for registry in evidence["registries"] for source in registry["sources"]
        if source["status"] == "outside_inventory_capture_population"
    ]
    assert any(source["fixture"].endswith("a5_fia_paged_probe.csv") for source in excluded)
    assert all(source["capture_id"] is None for source in excluded)


def test_archive_member_provenance_uses_explicit_source_lines_and_current_contracts(
    inventory, census,
):
    from mindie_profiler.normalized import kernel_rows
    from mindie_profiler.tensor_contracts import observed_contract

    registry = ("body_fused/kimi_a5_norm_gate.provenance.json", "kimi_a5_norm_gate.csv")
    rows, evidence = inventory.fixture_rows(census, registries=(registry,))
    records = rows["a5_kimi_k3", "layer_norm_gated_fwd_kernel"]
    assert [record["source_csv_line"] for record in records] == [74, 30516]
    fixture = ROOT / "tests/fixtures/body_fused/kimi_a5_norm_gate.csv"
    original = list(kernel_rows(fixture))
    assert records[0]["contract"] == inventory.canonical(observed_contract(original[0]))
    assert records[1]["contract"] is None
    source, = evidence["registries"][0]["sources"]
    assert source["capture_id"] == "a5_kimi_k3"
    assert source["source_sha256"] == census["a5_kimi_k3"]["source_identity"]["sha256"]
    assert source["retained_rows"] == source["added_unique_rows"] == 2


def test_inventory_rejects_new_summary_generation_with_still_valid_case_and_mapping(
    inventory, tmp_path,
):
    original = json.loads((
        ROOT / "tests/fixtures/fusion_reporting/historical-cohorts.json"
    ).read_text())["declarations"]["a3_glm53_decode-reference"]

    def write(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value, separators=(",", ":")) + "\n")
        return {"file": name, "sha256": sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size}

    summary = original["summary"]
    prefix = "fusion-cohort-a3_glm53_decode-reference"
    summary["artifacts"] = {
        key: write(prefix + "." + key + ".json", original[key])
        for key in ("case", "mapping")
    }
    identity = write(prefix + ".json", summary)
    receipt = {"captures": [{
        "capture_key": summary["capture_key"],
        "source_identity": summary["source_identity"],
        "reports": [{"report": identity["file"], "summary_identity": identity}],
    }]}
    write("fusion-cohort-validation.json", receipt)
    replay, = inventory.replay_inputs(tmp_path)
    assert replay[1]["graph_id"] == original["mapping"]["graph_id"]
    summary["variant"] = "different_generation_same_artifacts"
    write(prefix + ".json", summary)
    with pytest.raises(ValueError, match="summary_generation_mismatch"):
        list(inventory.replay_inputs(tmp_path))


def test_shared_int32_source_selection_exposes_real_dequant_consumer_contract(
    inventory, census,
):
    pytest.importorskip("mindie_sim.prediction.family_shared_quant",
                        reason="requires matching optional sim source")
    from mindie_sim import target_operators
    from mindie_sim.structure import export_op_structure
    from mindie_sim.structure_contracts import predicted_contract

    saved = inventory.read(
        inventory.BASE / "fusion-cohort-a3_glm53_prefill_shared_quant-selected.case.json")
    selected = target_operators(saved, phase="prefill", tokens=4096, context=0,
                                resource_fusion=False)
    consumer = next(op for op in selected if op.family == "dequant_swiglu_quant")
    rows, _ = inventory.fixture_rows(census)
    real = rows["a3_glm53_prefill", "DequantSwigluQuant"]
    assert inventory.canonical(predicted_contract(consumer.to_dict(include_work=False))) in {
        row["contract"] for row in real
    }
    assert consumer.source_boundary == "kernel"
    manifest = export_op_structure(
        (consumer,), model={"name": saved["name"]},
        execution={"phase": "prefill"}, expand_calls=False)
    native = inventory.targets(manifest)["DequantSwigluQuant"]
    assert len(native) == 1
    assert inventory.canonical(native[0]["contract"]) == inventory.canonical(
        predicted_contract(consumer.to_dict(include_work=False)))
    baseline = json.loads(json.dumps(saved))
    del baseline["runtime"]["kernels"]["lowerings"]["shared_expert"]
    assert not any(op.family == "dequant_swiglu_quant" for op in target_operators(
        baseline, phase="prefill", tokens=4096, context=0, resource_fusion=False))


def test_selected_and_checkpoint_base_cases_do_not_become_catalog_default(inventory):
    cases = (
        ("a3_glm53_prefill-reference", "case_default"),
        ("a3_qwen35-reference", "case_default"),
        ("a3_glm53_prefill_shared_quant-selected", "source_selected_case_base"),
        ("a5_qwen38_steady-selected", "source_selected_case_base"),
        ("a5_kimi_k3_checkpoint-reference", "checkpoint_conditional_case_base"),
    )
    for declaration, expected in cases:
        summary = inventory.read(inventory.BASE / f"fusion-cohort-{declaration}.json")
        source = summary["declaration_source"]
        base = inventory.read(Path(source["case_path"]))
        assert inventory.base_declaration_basis(source, base) == expected
