"""Real retained MLA tensor descriptors control precision, not durations.

[Role] Verify captured MLA descriptor ingress and precision preservation.
[Invariants] Timing columns never drive structure precision selection.
[Timeouts & Locks] Tier 0 (<5s), uses pytest tmp_path isolation.
[Side-Effect Policy] Writes only to isolated tmp_path.
"""
from copy import deepcopy
import csv
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples/structure"))
from capture_mla_structure import apply_captured_mla_structure, MARKER
from capture_policy import import_capture_policy
from a3_mla_native_observations import apply_a3_mla_native_observations
from mindie_sim import operator_costs, target_operators

FIXTURES = ROOT / "tests/fixtures/native_observations"


def inputs(tmp_path, mutate=None):
    raw = json.loads((FIXTURES / "a3_dsv4f_mc2_padding.json").read_text())["raw"]
    with (FIXTURES / "a3_sharedkv_mla_abi.csv").open() as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames, list(reader)
    if mutate:
        mutate(rows)
    with (tmp_path / "kernel_details.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (tmp_path / "cmd.sh").write_bytes((FIXTURES / "a3_dsv4f_mc2_cmd.sh").read_bytes())
    return raw, tmp_path / "kernel_details.csv"


def test_normal_capture_ingress_preserves_native_precision_and_complete_boundary(tmp_path):
    raw, source = inputs(tmp_path)
    before = deepcopy(raw)
    changed, provenance = import_capture_policy(raw, capture_path=source)
    assert raw == before
    assert provenance["mla_structure"]["status"] == "applied"
    quant = changed["model"]["quant"]
    assert (quant["index_dtype"], quant["index_scale_dtype"]) == ("int8", "fp16")
    assert quant["category_overrides"]["mla.o_b"] == {
        "weight_format": "bf16", "activation_format": "bf16"}
    ops = target_operators(changed, phase="decode", tokens=1, context=4096)
    assert sum(op.recipe == "quant_lightning_indexer_v2" for op in ops) == 3
    assert all(op.dtype == "bf16" for op in ops if op.recipe == "grouped_output_b")
    assert not any(op.recipe in {"index_scores", "index_topk"} for op in ops)


def test_catalog_declaration_uses_resolved_structure_without_requiring_expanded_fields(tmp_path):
    raw, source = inputs(tmp_path)
    raw["model"] = {"catalog_key": "deepseek-v4-flash-0731",
                    "quantization": raw["model"]["quantization"],
                    "quant": raw["model"]["quant"]}
    assert apply_captured_mla_structure(raw, capture_path=source)["status"] == "applied"
    ops = target_operators(raw, phase="decode", tokens=2, context=4096)
    assert sum(op.recipe == "quant_lightning_indexer_v2" for op in ops) == 21
    assert all(op.dtype == "bf16" for op in ops if op.recipe == "grouped_output_b")


@pytest.mark.parametrize("column,value", [
    ("Input Data Types", "FLOAT;DT_BF16"),
    ("Output Shapes", '"1,2048"'),
    ("Output Formats", "FRACTAL_NZ"),
])
def test_wrong_native_output_abi_does_not_silently_correct_precision(tmp_path, column, value):
    raw, source = inputs(tmp_path, lambda rows: rows[1].update({column: value}))
    before = deepcopy(raw)
    provenance = apply_captured_mla_structure(raw, capture_path=source)
    assert provenance["status"] == "unsupported" and raw == before


def test_explicit_conflicting_precision_is_preserved_and_timing_is_irrelevant(tmp_path):
    raw, source = inputs(tmp_path, lambda rows: [row.update({"Duration(us)": "999999"}) for row in rows])
    raw["model"]["quant"]["category_overrides"] = {"mla.o_b": {
        "weight_format": "int8", "activation_format": "int8"}}
    before = deepcopy(raw)
    assert apply_captured_mla_structure(raw, capture_path=source)["status"] == "conflict"
    assert raw == before
    raw["model"]["quant"]["category_overrides"] = {}
    assert apply_captured_mla_structure(raw, capture_path=source)["status"] == "applied"
    assert raw["runtime"]["metadata"][MARKER]["quant_indexer"] is True


def test_inconsistent_indexer_sequence_metadata_preserves_the_input(tmp_path):
    def mutate(rows):
        shapes = rows[2]["Input Shapes"].strip('"').split(";")
        shapes[8] = "2"
        rows[2]["Input Shapes"] = '"' + ";".join(shapes) + '"'
    raw, source = inputs(tmp_path, mutate)
    before = deepcopy(raw)
    provenance = apply_captured_mla_structure(raw, capture_path=source)
    assert provenance["status"] == "unsupported" and raw == before


def test_existing_explicit_indexer_fusion_is_preserved(tmp_path):
    raw, source = inputs(tmp_path)
    raw["runtime"]["kernels"].setdefault("lowerings", {})["native_fusion"] = {
        "implementation": "declared_native_fusion", "options": {"roles": ["lightning_indexer"]}}
    before = deepcopy(raw)
    result = apply_captured_mla_structure(raw, capture_path=source)
    assert result["status"] == "conflict" and raw == before


def test_native_train_response_is_one_inclusive_call_with_strict_m_domain(tmp_path):
    raw, source = inputs(tmp_path)
    raw, _ = import_capture_policy(raw, capture_path=source)
    declared, provenance = apply_a3_mla_native_observations(
        raw, phase="decode", tokens=2, context=4096, sequences=1)
    assert provenance["status"] == "applied"
    op = next(op for op in target_operators(declared, phase="decode", tokens=2, context=4096)
              if op.recipe == "grouped_output_a")
    result = operator_costs(declared, (op,), input_ready_ms=7)["operators"][0]
    assert result["duration_ms"] == pytest.approx(.054359)
    assert result["program"] == "JointNativeService"
    assert not result["service_before_input"]
    # The static rule is installed for every qualified ABI. M1/M19 remain
    # analytical because the rule's own m in [2, 18] domain rejects them.
    for rows in (1, 19):
        declared_m, miss = apply_a3_mla_native_observations(
            raw, phase="decode", tokens=rows, context=4096, sequences=1)
        assert miss["status"] == "applied"
        assert "a3-sharedkv-output-a-native-m2-18" in {
            rule["id"] for rule in declared_m["runtime"]["kernels"]["service_regimes"]}
        fallback_op = next(op for op in target_operators(
            declared_m, phase="decode", tokens=rows, context=4096)
            if op.recipe == "grouped_output_a")
        fallback = operator_costs(
            declared_m, (fallback_op,), input_ready_ms=7)["operators"][0]
        assert fallback["program"] != "JointNativeService"
        assert fallback["duration_ms"] != pytest.approx(.054359)


def test_case_insensitive_headers_and_missing_tensor_columns(tmp_path):
    raw, source = inputs(tmp_path)
    with source.open() as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    lower_dir = tmp_path / "lower_dir"
    lower_dir.mkdir()
    lower_csv = lower_dir / "kernel_details.csv"
    lower_fields = [name.lower() for name in reader.fieldnames]
    with lower_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=lower_fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k.lower(): v for k, v in row.items()})
    trial = deepcopy(raw)
    assert apply_captured_mla_structure(trial, capture_path=lower_csv)["status"] == "applied"
    overrides = trial["model"]["quant"]["category_overrides"]
    assert overrides["mla.o_a"] is not overrides["mla.o_b"]

    missing_dir = tmp_path / "missing_dir"
    missing_dir.mkdir()
    missing_csv = missing_dir / "kernel_details.csv"
    with missing_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Name", "Type", "Duration(us)"], lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({"Name": row["Name"], "Type": row["Type"], "Duration(us)": row["Duration(us)"]})
    before = deepcopy(raw)
    missing_res = apply_captured_mla_structure(raw, capture_path=missing_csv)
    assert missing_res["status"] == "unsupported"
    assert missing_res["reason"] == "captured_mla_requires_complete_tensor_columns"
    assert raw == before


def test_inherited_mla_category_override_conflicts_are_preserved(tmp_path):
    raw, source = inputs(tmp_path)
    raw["model"]["quant"]["category_overrides"] = {
        "mla": {"weight_format": "int8", "activation_format": "int8"}
    }
    before = deepcopy(raw)
    res = apply_captured_mla_structure(raw, capture_path=source)
    assert res["status"] == "conflict"
    assert raw == before

    non_preset = deepcopy(raw)
    non_preset["model"]["quant"]["category_overrides"] = {}
    non_preset["model"]["quant"]["source"] = {"kind": "explicit"}
    before_np = deepcopy(non_preset)
    res_np = apply_captured_mla_structure(non_preset, capture_path=source)
    assert res_np["status"] == "conflict"
    assert non_preset == before_np


def test_die_queue_and_broad_rule_conflicts_and_idempotency(tmp_path):
    raw, source = inputs(tmp_path)
    raw, _ = import_capture_policy(raw, capture_path=source)

    die_conflict = deepcopy(raw)
    count = int(die_conflict["machine"].get("num_devices", 8))
    die_conflict["machine"]["dies"] = [{"rates": {"native_call_service": 500.0}} for _ in range(count)]
    untouched, prov = apply_a3_mla_native_observations(
        die_conflict, phase="decode", tokens=2, context=4096, sequences=1)
    assert prov["status"] == "conflict"
    assert prov["reason"] == "native_service_queue_conflicts_with_declaration"
    assert untouched == die_conflict

    broad_conflict = deepcopy(raw)
    broad_conflict["runtime"].setdefault("kernels", {}).setdefault("service_regimes", []).append({
        "id": "custom-broad-gemm",
        "match": {"phase": "decode", "family": "gemm"},
        "response": {"fixed_us": 10.0},
    })
    untouched_broad, prov_broad = apply_a3_mla_native_observations(
        broad_conflict, phase="decode", tokens=2, context=4096, sequences=1)
    assert prov_broad["status"] == "conflict"
    assert prov_broad["reason"] == "existing_output_a_service_preserved"
    assert untouched_broad == broad_conflict

    edited_id_conflict = deepcopy(raw)
    edited_id_conflict["runtime"].setdefault("kernels", {}).setdefault("service_regimes", []).append({
        "id": "a3-sharedkv-output-a-native-m2-18",
        "match": {"phase": "decode", "recipe": "grouped_output_a"},
        "response": {"fixed_us": 123.0},
    })
    untouched_edited, prov_edited = apply_a3_mla_native_observations(
        edited_id_conflict, phase="decode", tokens=2, context=4096, sequences=1)
    assert prov_edited["status"] == "conflict"
    assert prov_edited["reason"] == "existing_output_a_service_preserved"
    assert untouched_edited == edited_id_conflict

    ar_case = {
        "machine": {"hardware_key": "Ascend910_9599"},
        "model": {"layers": 8, "num_experts": 16, "top_k": 8},
        "runtime": {
            "moe_recipe": "local_expert_reduce",
            "kernels": {
                "service_regimes": [
                    {
                        "id": "a5-q30-prefill-allreduce",
                        "match": {"phase": "prefill", "family": "allreduce"},
                        "response": {"fixed_us": 500.0},
                    }
                ]
            },
        },
    }
    # Geometry used to mutate this foreign rule by +180 us and persist a
    # base_fixed_us marker; replaying another geometry then inherited 680 us.
    # A static binder must leave the foreign declaration untouched.
    once, prov_once = apply_a3_mla_native_observations(
        ar_case, phase="prefill", tokens=4096, context=0, sequences=1)
    twice, _ = apply_a3_mla_native_observations(
        once, phase="prefill", tokens=4096, context=0, sequences=1)
    assert prov_once["status"] == "not_applicable"
    assert once == ar_case
    assert once == twice
    assert once["runtime"]["kernels"]["service_regimes"][0]["response"]["fixed_us"] == 500.0
    assert "base_fixed_us" not in once["runtime"]["kernels"]["service_regimes"][0].get(
        "provenance", {})

    unmarked_l8 = deepcopy(raw)
    unmarked_l8["model"]["layers"] = 8
    unmarked_l8["runtime"]["metadata"].pop("captured_sharedkv_mla", None)
    unmarked_l8["runtime"]["metadata"].pop("compatible_caller_variant", None)
    unmarked_l8["runtime"]["kernels"]["service_regimes"] = [
        {"id": "a3-v4flash-grouped-gate-up-c32", "match": {"phase": "decode", "recipe": "grouped_gate_up"}, "response": {"fixed_us": 36.0}},
        {"id": "a3-retained-call-13d2f9a1640e2aa2", "match": {"phase": "decode", "recipe": "q_a"}, "response": {"fixed_us": 19.639}},
    ]
    m1_fallback, _ = apply_a3_mla_native_observations(
        unmarked_l8, phase="decode", tokens=1, context=4096, sequences=1)
    assert "a3-sharedkv-output-a-native-m2-18" not in {
        r["id"] for r in m1_fallback["runtime"]["kernels"]["service_regimes"]
    }




def test_descriptor_scan_streams_without_retaining_timing_rows(tmp_path):
    from capture_mla_structure import _descriptor_rows

    raw, source = inputs(tmp_path)
    stream = _descriptor_rows(source)
    assert stream is not None and not isinstance(stream, list)
    rows = list(stream)
    assert rows and all(hasattr(row, "input_shapes") for row in rows)


def test_timing_columns_do_not_change_structural_output(tmp_path):
    raw, source = inputs(tmp_path)
    fast, _ = import_capture_policy(deepcopy(raw), capture_path=source)
    with source.open() as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames, list(reader)
    slow = tmp_path / "slow.csv"
    with slow.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            row = dict(row)
            row["Duration(us)"] = "999999999"
            row["Start Time(us)"] = "1"
            writer.writerow(row)
    shifted, _ = import_capture_policy(deepcopy(raw), capture_path=slow)
    for declaration in (fast, shifted):
        declaration["runtime"].get("kernels", {}).pop("service_regimes", None)
    assert fast == shifted


def test_conflict_before_commit_never_creates_or_edits_runtime(tmp_path):
    raw, source = inputs(tmp_path)
    raw["model"]["quant"]["category_overrides"] = {
        "mla.o_a": {"weight_format": "int8", "activation_format": "int8"}}
    raw["runtime"].pop("kernels", None)
    before = deepcopy(raw)
    provenance = apply_captured_mla_structure(raw, capture_path=source)
    assert provenance["status"] == "conflict"
    assert raw == before
    assert "kernels" not in raw["runtime"]
