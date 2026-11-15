"""R8/R9/R10 native MC2 routing operands and compulsory/aligned read ledgers.

[Role]
  Regress R8/R9/R10 routing contracts on authentic and synthetic descriptors.

[Invariants]
  IDs are mandatory INT32 [T,K]; supplied weights are FP32 [T,K]. Full
  Combine descriptors require weights. Explicit Dispatch absence costs no
  scale reads. Compact legacy controls preserve their implicit FP32 ledger.
  All columns keep their extent; mixed descriptors reject before geometry.

[Timeouts & Locks]
  Pure parsing and arithmetic; no device work or locks.

[Side-Effect Policy]
  Read-only golden access; mutations use private copies. No writes.
"""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from mindie_profiler.op_abi_bridge import AbiError, infer_request
from mindie_profiler.op_abi_descriptors import slot_descriptors
from mindie_profiler.op_abi_slots import slot_records
from mindie_profiler.op_formula_annotator import annotate_row
from mindie_sim.op_formulas import FormulaValidationError, evaluate_operator

ROOT = Path(__file__).resolve().parents[1]
STAGES = ("dispatch", "combine")
SOURCES = ("authentic", "synthetic")
FIELDS = ("compulsory_read_bytes", "compulsory_write_bytes",
          "granule_gm_bytes", "comm_bytes")


@pytest.fixture(scope="module")
def goldens():
    return json.loads((ROOT / "tests/fixtures/a5_op_goldens.json").read_text())


def native_row(stage, source, goldens):
    if source == "authentic":
        number = 112 if stage == "dispatch" else 100
        identity = f"kernel_r{number}_moe_distribute_{stage}"
        return deepcopy(next(p["raw_row"] for p in goldens["points"]
                             if p["id"] == identity))
    dispatch = stage == "dispatch"
    return dict(
        name="MoeDistribute" + stage.title() + "V3",
        input_shapes=f"1;{4 if dispatch else 8},16;4,2;"
                     + (";;4,2" if dispatch else "16;4;4,2"),
        input_data_types="DT_INT32;DT_BF16;DT_INT32;"
                         + ("DT_UNDEFINED;DT_UNDEFINED;FLOAT" if dispatch
                            else "DT_INT32;DT_INT32;FLOAT"),
        input_formats="ND;ND;ND;ND;ND;ND",
        output_shapes=f"{8 if dispatch else 4},16",
        output_data_types="DT_BF16", output_formats="ND",
        ep=2, experts_total=4, experts_local=2, topk=2, routed_rows=8,
    )


def change(row, field, index, value):
    values = row[field].split(";")
    values[index] = value
    row[field] = ";".join(values)


def card(row):
    before = deepcopy(row)
    result = annotate_row(row, measured_us=1e12, include_card=True)
    assert result["status"] == "clean", result
    assert row == before
    return result["formula_card"]


def invalid(row):
    before = deepcopy(row)
    with pytest.raises(AbiError):
        infer_request(row)
    result = annotate_row(row, include_card=True)
    assert result["status"] == "invalid_abi", result
    assert "formula_card" not in result
    assert row == before


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("ids,scales", [
    ("DT_INT32", "DT_FLOAT"), ("INT32", "FLOAT"), ("int32", "fp32"),
])
def test_r8_matching_routing_storage_has_exact_ledgers(stage, source, ids, scales, goldens):
    row = native_row(stage, source, goldens)
    change(row, "input_data_types", 2, ids)
    change(row, "input_data_types", 5, scales)
    c = card(row)
    b = c["bindings"]
    t, h, k, r, e = (b[n] for n in ("tokens", "hidden", "topk", "routed_rows", "experts_total"))
    align = lambda n: (n + 511) // 512 * 512
    read = 2*t*h + 8*t*k if stage == "dispatch" else 2*r*h + 4*t*k
    write = 2*r*h + 4*e if stage == "dispatch" else 2*t*h
    aligned = ((t+r)*align(2*h) + 2*t*align(4*k) + align(4*e)
               if stage == "dispatch" else (t+r)*align(2*h) + t*align(4*k))
    assert (c["compulsory_read_bytes"], c["compulsory_write_bytes"],
            c["granule_gm_bytes"]) == (read, write, aligned)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("index", [2, 5], ids=["expert_ids", "expert_scales"])
@pytest.mark.parametrize("shape", ["", "NULL", "bad", "-1,{k}", "{t},0",
                                  "{prev},{k}", "{t}", "1,{t},{k}", "[]"])
def test_r8_required_and_supplied_routing_shapes_reject(stage, source, index, shape, goldens):
    row = native_row(stage, source, goldens)
    t, k = map(int, row["input_shapes"].split(";")[2].split(","))
    change(row, "input_shapes", index, shape.format(t=t, k=k, prev=t-1))
    invalid(row)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("declared", [False, True])
def test_r8_scale_columns_reconcile_with_ids_and_declared_topk(stage, source, declared, goldens):
    row = native_row(stage, source, goldens)
    t, k = map(int, row["input_shapes"].split(";")[2].split(","))
    if declared:
        row["topk"] = k
    else:
        row.pop("topk", None)
    change(row, "input_shapes", 5, f"{t},1")
    invalid(row)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("index,dtype", [
    (index, dtype) for index in (2, 5)
    for dtype in ("", "DT_UNDEFINED", "DT_MYSTERY", "DT_FLOAT16", "DT_BF16",
                  "DT_INT64", "DT_UINT8", "BOOL")
] + [(2, "DT_FLOAT"), (5, "DT_INT32")])
def test_r8_routing_dtype_is_required_and_role_specific(stage, source, index, dtype, goldens):
    row = native_row(stage, source, goldens)
    change(row, "input_data_types", index, dtype)
    invalid(row)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("shape,dtype,layout", [
    ("", "", ""), ("", "DT_UNDEFINED", "ND"), ("NULL", "DT_UNDEFINED", "NULL"),
    ("NULL", "NULL", "ND"), ("", "", "ND"),
])
def test_r8_explicit_absence_is_optional_only_for_dispatch(stage, source, shape, dtype, layout, goldens):
    row = native_row(stage, source, goldens)
    baseline = card(row)
    for field, value in (("input_shapes", shape), ("input_data_types", dtype),
                         ("input_formats", layout)):
        change(row, field, 5, value)
    if stage == "combine":
        invalid(row)
        return
    c = card(row)
    t, k = (c["bindings"][n] for n in ("tokens", "topk"))
    assert c["compulsory_read_bytes"] == baseline["compulsory_read_bytes"] - 4*t*k
    assert c["granule_gm_bytes"] == baseline["granule_gm_bytes"] - t*((4*k+511)//512)*512
    assert c["compulsory_write_bytes"] == baseline["compulsory_write_bytes"]
    assert c["comm_bytes"] == baseline["comm_bytes"]
    assert infer_request(row)[1]["has_scales"] is False


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("count", [3, 4, 5])
def test_r8_legacy_compact_descriptors_keep_their_fp32_weight_contract(stage, count, goldens):
    row = native_row(stage, "synthetic", goldens)
    baseline = card(row)
    row.update(input_shapes="1;" + ("4,16" if stage == "dispatch" else "8,16") + ";4,2;4;4,2",
               input_data_types="DT_INT32;DT_BF16;DT_INT32;DT_INT32;FLOAT",
               input_formats="ND;ND;ND;ND;ND")
    for field in ("input_shapes", "input_data_types", "input_formats"):
        row[field] = ";".join(row[field].split(";")[:count])
    c = card(row)
    assert tuple(c[f] for f in FIELDS) == tuple(baseline[f] for f in FIELDS)
    if count == 5:
        change(row, "input_shapes", 4, "4,1")
        invalid(row)


@pytest.mark.parametrize("stage", STAGES)
def test_r8_later_slots_and_declared_topk_cannot_replace_ids(stage, goldens):
    row = native_row(stage, "synthetic", goldens)
    for field in ("input_shapes", "input_data_types", "input_formats"):
        row[field] = ";".join(row[field].split(";")[:2])
    invalid(row)


def test_r8_native_auxiliary_matrix_is_not_a_routing_operand(goldens):
    row = native_row("dispatch", "synthetic", goldens)
    baseline = card(row)
    change(row, "input_shapes", 3, "2,7")
    change(row, "input_data_types", 3, "FLOAT")
    c = card(row)
    assert c["bindings"]["topk"] == 2
    assert tuple(c[f] for f in FIELDS) == tuple(baseline[f] for f in FIELDS)


def test_r8_all_authentic_mc2_captures_keep_their_ledgers(goldens):
    points = [p for p in goldens["points"] if p["group"] == "kernel"
              and p["operator"].startswith("moe_distribute_")]
    assert len(points) == 15
    for p in points:
        c = card(deepcopy(p["raw_row"]))
        direct = evaluate_operator(p["operator"], p["params"]).formula_card
        assert tuple(c[f] for f in FIELDS) == tuple(getattr(direct, f) for f in FIELDS)


def test_r8_direct_scale_presence_is_strict(goldens):
    op, params, _ = infer_request(native_row("combine", "synthetic", goldens))
    for value in (False, 0, 1, "false"):
        with pytest.raises(FormulaValidationError):
            evaluate_operator(op, dict(params, has_scales=value))
    # The public registry consistently treats None as an omitted option.
    assert evaluate_operator(op, dict(params, has_scales=None)).formula_card == (
        evaluate_operator(op, params).formula_card)


@pytest.mark.parametrize("shape", ["bad", "-1,2", "4", "[]", "4,2"])
def test_r8_undefined_dtype_cannot_hide_a_supplied_scale_shape(shape, goldens):
    row = native_row("dispatch", "synthetic", goldens)
    change(row, "input_shapes", 5, shape)
    change(row, "input_data_types", 5, "DT_UNDEFINED")
    invalid(row)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("source", SOURCES)
def test_r8_ids_cannot_be_explicitly_absent(stage, source, goldens):
    row = native_row(stage, source, goldens)
    change(row, "input_shapes", 2, "NULL")
    change(row, "input_data_types", 2, "DT_UNDEFINED")
    invalid(row)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("missing", ["mapping", "shape_column", "dtype_column"])
def test_r8_full_layout_preserves_missing_scale_position(stage, missing, goldens):
    row = native_row(stage, "synthetic", goldens)
    if missing == "mapping":
        row["input_shapes"] = [dict(shape=[int(d) for d in s.split(",")], dtype=dt, layout="ND")
                               if s else dict(present=False)
                               for s, dt in zip(row["input_shapes"].split(";"),
                                                row["input_data_types"].split(";"))]
        row["input_shapes"][5] = dict(present=False)
        row.pop("input_data_types")
        row.pop("input_formats")
        if stage == "dispatch":
            assert infer_request(row)[1]["has_scales"] is False
            card(row)
            return
    else:
        field = "input_shapes" if missing == "shape_column" else "input_data_types"
        row[field] = ";".join(row[field].split(";")[:5])
    invalid(row)


def mapping_row(row, parallel=True):
    row = deepcopy(row)
    row["input_shapes"] = [dict(shape=s, dtype=d, layout=f) for s, d, f in zip(
        row["input_shapes"].split(";"), row["input_data_types"].split(";"),
        row["input_formats"].split(";"))]
    if not parallel:
        row.pop("input_data_types")
        row.pop("input_formats")
    return row


@pytest.mark.parametrize("direction", ["input", "output"])
@pytest.mark.parametrize("shapes,types,formats", [(3, 6, 6), (4, 7, 2),
                                                (5, 3, 8), (6, 3, 2)])
def test_r9_mapping_columns_preserve_extent_and_reject_conflicting_counts(direction, shapes, types, formats):
    row = {f"{direction}_shapes": [dict(shape=[4, 2], dtype="FLOAT", layout="ND")
                                  for _ in range(shapes)],
           f"{direction}_dtypes": ["FLOAT"] * types,
           f"{direction}_formats": ["ND"] * formats}
    before = deepcopy(row)
    parsed = slot_descriptors(row, direction)
    assert len(parsed["slots"]) == max(shapes, types, formats)
    assert {i["code"] for i in parsed["issues"]} == {"descriptor_column_mismatch"}
    for i, slot in enumerate(parsed["slots"][shapes:], shapes):
        assert slot["position"] == i and slot["shape"] is None
        assert not slot["shape_present"] and not slot["usable"]
        assert slot["dtype_raw"] == ("FLOAT" if i < types else "")
        assert slot["layout_raw"] == ("ND" if i < formats else "")
    with pytest.raises(AbiError, match="descriptor_column_mismatch"):
        slot_records(row, direction)
    assert row == before


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("count", [3, 4, 5])
@pytest.mark.parametrize("column", ["input_data_types", "input_formats", "both"])
def test_r9_partial_full_mapping_never_becomes_compact(stage, source, count, column, goldens):
    row = mapping_row(native_row(stage, source, goldens))
    baseline = card(row)
    # Retain topology when shortening slots that also supplied expert counts.
    topology = infer_request(row)[1]
    row.update({k: topology[k] for k in ("experts_total", "experts_local", "ep")})
    if count == 5:
        row["input_shapes"][4] = deepcopy(row["input_shapes"][5])
        change(row, "input_data_types", 4, "FLOAT")
    row["input_shapes"] = row["input_shapes"][:count]
    for field in ("input_data_types", "input_formats"):
        if column not in (field, "both"):
            row[field] = ";".join(row[field].split(";")[:count])
    invalid(row)
    # A consistently shortened record remains the supported compact contract.
    for field in ("input_data_types", "input_formats"):
        row[field] = ";".join(row[field].split(";")[:count])
    assert tuple(card(row)[f] for f in FIELDS) == tuple(baseline[f] for f in FIELDS)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("count", [3, 4, 5])
def test_r9_unknown_trailing_dtype_is_inspected_before_count_rejection(stage, count, goldens):
    row = mapping_row(native_row(stage, "synthetic", goldens))
    row["input_shapes"] = row["input_shapes"][:count]
    change(row, "input_data_types", 5, "DT_MYSTERY")
    parsed = slot_descriptors(dict(row, input_dtypes=row["input_data_types"]), "input")
    assert parsed["slots"][5]["dtype_raw"] == "DT_MYSTERY"
    with pytest.raises(AbiError, match="unknown_dtype"):
        infer_request(row)
    invalid(row)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("column", ["input_data_types", "input_formats"])
def test_r9_short_parallel_column_rejects_even_with_complete_inline_metadata(stage, column, goldens):
    row = mapping_row(native_row(stage, "synthetic", goldens))
    row[column] = ";".join(row[column].split(";")[:3])
    invalid(row)


@pytest.mark.parametrize("name", ["Matmul", "Mul", "AllReduce"])
@pytest.mark.parametrize("direction", ["input", "output"])
def test_r9_column_mismatches_reject_before_other_operator_geometry(name, direction):
    row = dict(name=name, world_size=2,
               input_shapes=[dict(shape=[2, 2], dtype="BF16", layout="ND")
                             for _ in range(1 if name == "AllReduce" else 2)],
               output_shapes=[dict(shape=[2, 2], dtype="BF16", layout="ND")])
    card(row)
    row[f"{direction}_dtypes"] = ["BF16"] * (len(row[f"{direction}_shapes"]) + 1)
    with pytest.raises(AbiError, match="descriptor_column_mismatch"):
        infer_request(row)
    invalid(row)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("descriptor", [
    {"present": True}, {"present": True, "layout": "ND"},
    {"declared_present": True}, {"shape_present": False},
    {"shape_present": False, "dtype": "DT_UNDEFINED"}, {"layout": "ND"},
    {"values": [1.0]}, {"storage_bytes": 32},
    {"present": True, "shape": "NULL", "dtype": "DT_UNDEFINED"},
    {"present": True, "shape_present": False, "layout": "ND"},
])
def test_r9_present_scale_without_metadata_rejects(stage, descriptor, goldens):
    row = mapping_row(native_row(stage, "synthetic", goldens), parallel=False)
    row["input_shapes"][5] = deepcopy(descriptor)
    slot = slot_descriptors(row, "input")["slots"][5]
    assert slot["present"] and not slot["omitted"] and not slot["usable"]
    invalid(row)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("descriptor", [None, {}, {"present": False},
    {"present": False, "shape_present": False, "layout": "ND"},
    *[dict(shape=s, dtype=d, layout="ND") for s in ("", "NULL", "NONE", "UNDEFINED")
      for d in ("", "DT_UNDEFINED")]])
def test_r9_genuine_mapping_absence_keeps_exact_dispatch_deduction(stage, descriptor, goldens):
    row = mapping_row(native_row(stage, "synthetic", goldens), parallel=False)
    baseline = card(row)
    row["input_shapes"][5] = deepcopy(descriptor)
    assert slot_descriptors(row, "input")["slots"][5]["omitted"]
    if stage == "combine":
        invalid(row)
        return
    c = card(row)
    assert infer_request(row)[1]["has_scales"] is False
    assert c["compulsory_read_bytes"] == baseline["compulsory_read_bytes"] - 32
    assert c["granule_gm_bytes"] == baseline["granule_gm_bytes"] - 2048
    assert (c["compulsory_write_bytes"], c["comm_bytes"]) == (
        baseline["compulsory_write_bytes"], baseline["comm_bytes"])


def test_r9_all_authentic_mapping_regressions(goldens):
    points = [p for p in goldens["points"] if p["group"] == "kernel"
              and p["operator"].startswith("moe_distribute_")]
    assert len(points) == 15
    for p in points:
        full = mapping_row(p["raw_row"])
        assert tuple(card(full)[f] for f in FIELDS) == tuple(card(p["raw_row"])[f] for f in FIELDS)
        for count in (3, 4, 5):
            row = deepcopy(full)
            row["input_shapes"][4] = deepcopy(row["input_shapes"][5])
            change(row, "input_data_types", 4, "FLOAT")
            row["input_shapes"] = row["input_shapes"][:count]
            invalid(row)
        for descriptor in ({"present": True, "layout": "ND"},
                           {"shape_present": False},
                           {"shape_present": False, "dtype": "DT_UNDEFINED"}):
            row = mapping_row(p["raw_row"], parallel=False)
            row["input_shapes"][5] = descriptor
            invalid(row)


def r10_partial(row, count, retained, representation):
    row = mapping_row(row)
    params = infer_request(row)[1]
    row.update({k: params[k] for k in ("ep", "experts_total", "experts_local")})
    if count == 5:
        row["input_shapes"][4] = deepcopy(row["input_shapes"][5])
        change(row, "input_data_types", 4, "FLOAT")
    row["input_shapes"] = row["input_shapes"][:count]
    if representation == "mixed":
        row["input_shapes"][0] = row["input_shapes"][0]["shape"]
    else:
        row["input_shapes"] = [s["shape"] for s in row["input_shapes"]]
    for field in ("input_data_types", "input_formats"):
        if retained not in (field, "both"):
            row[field] = ";".join(row[field].split(";")[:count])
    return row


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("count", [3, 4, 5])
@pytest.mark.parametrize("retained", ["input_data_types", "input_formats", "both"])
@pytest.mark.parametrize("representation", ["mixed", "tokens"])
def test_r10_partial_full_records_reject_with_paired_compact_controls(
        stage, source, count, retained, representation, goldens):
    full = native_row(stage, source, goldens)
    baseline = card(full)
    row = r10_partial(full, count, retained, representation)
    invalid(row)
    # Shortening every column is sufficient only for an unmixed representation.
    for field in ("input_data_types", "input_formats"):
        row[field] = ";".join(row[field].split(";")[:count])
    if representation == "mixed":
        invalid(row)
        row["input_shapes"][0] = dict(shape=row["input_shapes"][0])
    c = card(row)
    assert tuple(c[f] for f in FIELDS) == tuple(baseline[f] for f in FIELDS)


@pytest.mark.parametrize("direction", ["input", "output"])
@pytest.mark.parametrize("shapes,types,formats", [(3, 6, 6), (4, 7, 2),
                                                (5, 3, 8), (6, 3, 2)])
@pytest.mark.parametrize("representation", ["mixed", "tokens"])
def test_r10_parser_preserves_mixed_and_token_column_metadata(
        direction, shapes, types, formats, representation):
    entries = ["1"] + [dict(shape="4,2") for _ in range(shapes-1)]
    if representation == "tokens":
        entries = ["1"] + ["4,2"] * (shapes-1)
    else:
        entries[-1] = None
    row = {f"{direction}_shapes": entries,
           f"{direction}_dtypes": ["FLOAT"] * types,
           f"{direction}_formats": ["ND"] * formats}
    before = deepcopy(row)
    parsed = slot_descriptors(row, direction)
    assert len(parsed["slots"]) == max(shapes, types, formats)
    codes = {i["code"] for i in parsed["issues"]}
    assert "descriptor_column_mismatch" in codes
    for i, slot in enumerate(parsed["slots"]):
        assert slot["position"] == i
        assert slot["dtype_raw"] == ("FLOAT" if i < types else "")
        assert slot["layout_raw"] == ("ND" if i < formats else "")
        if i >= shapes:
            assert slot["shape"] is None and not slot["shape_present"]
            assert not slot["usable"]
    if representation == "mixed":
        assert "descriptor_not_a_mapping" in codes
        slot = parsed["slots"][0]
        assert slot["state"] == "invalid" and slot["present"]
        assert not slot["usable"] and not slot["omitted"]
        assert parsed["slots"][shapes-1]["omitted"]
    with pytest.raises(AbiError, match="descriptor_not_a_mapping|descriptor_column_mismatch"):
        slot_records(row, direction)
    assert row == before


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("count", [3, 4, 5])
@pytest.mark.parametrize("index", [0, 5])
def test_r10_mixed_unknown_dtype_survives_at_invalid_token_and_tail(stage, count, index, goldens):
    row = r10_partial(native_row(stage, "synthetic", goldens), count, "both", "mixed")
    change(row, "input_data_types", index, "DT_MYSTERY")
    parsed = slot_descriptors(dict(row, input_dtypes=row["input_data_types"]), "input")
    assert parsed["slots"][index]["dtype_raw"] == "DT_MYSTERY"
    with pytest.raises(AbiError, match="unknown_dtype"):
        infer_request(row)
    invalid(row)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("index", [0, 3, 4])
@pytest.mark.parametrize("parallel", [False, True])
def test_r10_full_mixed_records_reject_even_at_auxiliary_slots(stage, source, index, parallel, goldens):
    row = mapping_row(native_row(stage, source, goldens), parallel=parallel)
    baseline = card(row)
    descriptor = deepcopy(row["input_shapes"][index])
    row["input_shapes"][index] = descriptor["shape"]
    with pytest.raises(AbiError, match="descriptor_not_a_mapping"):
        infer_request(row)
    invalid(row)
    row["input_shapes"][index] = descriptor
    assert tuple(card(row)[f] for f in FIELDS) == tuple(baseline[f] for f in FIELDS)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("column", ["input_data_types", "input_formats"])
@pytest.mark.parametrize("encoding", ["semicolon", "pipe", "tuple"])
def test_r10_short_pure_token_columns_reject(stage, column, encoding, goldens):
    row = native_row(stage, "synthetic", goldens)
    card(row)
    row[column] = ";".join(row[column].split(";")[:3])
    for field in ("input_shapes", "input_data_types", "input_formats"):
        parts = row[field].split(";")
        row[field] = tuple(parts) if encoding == "tuple" else (
            ("|" if encoding == "pipe" else ";").join(parts))
    with pytest.raises(AbiError, match="descriptor_column_mismatch"):
        infer_request(row)
    invalid(row)


def test_r10_all_authentic_mixed_and_token_boundaries(goldens):
    points = [p for p in goldens["points"] if p["group"] == "kernel"
              and p["operator"].startswith("moe_distribute_")]
    assert len(points) == 15
    for p in points:
        full = p["raw_row"]
        card(full)
        for count in (3, 4, 5):
            for representation in ("mixed", "tokens"):
                for retained in ("input_data_types", "input_formats", "both"):
                    invalid(r10_partial(full, count, retained, representation))
            unknown = r10_partial(full, count, "both", "mixed")
            change(unknown, "input_data_types", 5, "DT_MYSTERY")
            invalid(unknown)
        for index in (0, 3, 4):
            row = mapping_row(full)
            row["input_shapes"][index] = row["input_shapes"][index]["shape"]
            invalid(row)
        # Null mapping entries remain genuine optional absence, not mixed tokens.
        row = mapping_row(full, parallel=False)
        baseline = card(row)
        row["input_shapes"][5] = None
        if p["operator"].endswith("combine"):
            invalid(row)
            continue
        c = card(row)
        t, k = (c["bindings"][n] for n in ("tokens", "topk"))
        assert infer_request(row)[1]["has_scales"] is False
        assert c["compulsory_read_bytes"] == baseline["compulsory_read_bytes"] - 4*t*k
        assert c["granule_gm_bytes"] == baseline["granule_gm_bytes"] - t*((4*k+511)//512)*512
        assert (c["compulsory_write_bytes"], c["comm_bytes"]) == (
            baseline["compulsory_write_bytes"], baseline["comm_bytes"])
