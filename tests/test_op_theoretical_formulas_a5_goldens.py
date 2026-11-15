"""Authentic A5 golden validation: 428 operator points, provenance, zero floors.

[Role]
  Validate every retained live A5 measurement against the remediated engine:
  160 attention rows, 120 fabric collectives, all 36 MC2 dispatch/combine stage
  timings and all 112 modeled kernel rows (out of 140), plus the preserved
  padded-varlen ABI negative fixture and byte-identical fixture rebuild.

[Invariants]
  * All 428 points satisfy ``0 < tau_hw <= t_floor <= measured`` with zero floor
    violations and ``sol_floor_pct <= 100``.
  * Point IDs are unique; every point records source file, row index and the
    fixture records all five source SHA-256 digests.
  * Kernel rows are re-annotated from their raw descriptors, not pre-baked params.
  * The rejected padded-varlen record is reported as ``invalid_abi``.
  * MC2 calibration membership is explicit and honest.

[Timeouts & Locks]
  Pure in-memory evaluation; the optional rebuild reads the read-only capture
  mount once and is skipped when the mount is absent.

[Side-Effect Policy]
  Reads the hermetic fixture only; the rebuild test writes nothing.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import statistics
from pathlib import Path

import pytest

from mindie_profiler.op_formula_annotator import annotate_row
from mindie_sim.op_formulas import evaluate_operator

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "a5_op_goldens.json"
BUILDER = Path(__file__).resolve().parent / "fixtures" / "build_a5_op_goldens.py"
CAPTURE_DIR = Path("/Volumes/data/Codex/2026-11-12/kan-x/work/agy-closure/"
                   "live_a5_captures/data")


@pytest.fixture(scope="module")
def golden() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_provenance_and_counts(golden):
    assert golden["schema"] == "a5-op-goldens/2"
    assert golden["point_count"] == 428
    assert len(golden["points"]) == 428
    assert golden["counts"]["attention"] == 160
    assert golden["counts"]["fabric"] == 120
    assert golden["counts"]["mc2"] == 36
    assert golden["counts"]["kernel"] == 112
    assert golden["kernel_rows"]["raw"] == 140
    assert golden["kernel_rows"]["modeled"] == 112
    assert golden["kernel_rows"]["unmodeled"] == 28
    assert len(golden["kernel_rows"]["unmodeled_rows"]) == 28
    ids = [point["id"] for point in golden["points"]]
    assert len(ids) == len(set(ids))
    assert golden["rejected_points"]
    assert golden["rejected_points"][0]["expected_status"] == "invalid_abi"
    assert len(golden["source_files"]) == 5
    for source in golden["source_files"]:
        assert len(source["sha256"]) == 64
        assert source["bytes"] > 0
    assert len(golden["block_points"]) == 5


def test_every_golden_point_has_zero_floor_violations(golden):
    violations = []
    worst_sol = 0.0
    for point in golden["points"]:
        evaluation = evaluate_operator(
            point["operator"], point["params"],
            launch_mode=point["launch_mode"],
            steady_l2_warm=point["steady_l2_warm"])
        floor = evaluation.t_floor_us
        measured = point["measured_us"]
        tau = evaluation.latency.tau_hw_floor_us
        if not (0 < tau <= floor <= measured * (1.0 + 1e-9)):
            violations.append((point["id"], tau, floor, measured))
        worst_sol = max(worst_sol, 100.0 * floor / measured)
    assert violations == []
    assert worst_sol <= 100.0


def test_reference_accuracy_is_reported_for_calibrated_and_full_capture(golden):
    calibrated = []
    full = []
    for point in golden["points"]:
        evaluation = evaluate_operator(
            point["operator"], point["params"],
            launch_mode=point["launch_mode"],
            steady_l2_warm=point["steady_l2_warm"])
        ratio = point["measured_us"] / evaluation.t_ref_us
        full.append(ratio)
        if point.get("in_calibrated_ref_domain"):
            calibrated.append(ratio)
    assert len(calibrated) >= 30
    assert 0.5 <= statistics.median(calibrated) <= 1.6
    assert 0.3 <= statistics.median(full) <= 2.5
    attention = [p for p in golden["points"] if p["group"] == "attention"]
    fabric = [p for p in golden["points"] if p["group"] == "fabric"]
    assert len(attention) == 160 and len(fabric) == 120


def test_mc2_calibration_flags_match_the_declared_domain(golden):
    mc2 = [point for point in golden["points"] if point["group"] == "mc2"]
    assert len(mc2) == 36
    for point in mc2:
        params = point["params"]
        domain = point["fit_domain_status"]
        if params["tokens"] <= 64 and params["skew"] == 1.0:
            assert domain == "in_calibrated_ref_domain"
            assert point["in_calibrated_ref_domain"] is True
        else:
            assert domain != "in_calibrated_ref_domain"
            assert point["in_calibrated_ref_domain"] is False
    skew_rows = {point["params"]["skew"] for point in mc2}
    assert skew_rows == {1.0, 2.5}


def test_kernel_points_reannotate_from_raw_descriptors(golden):
    kernels = [point for point in golden["points"] if point["group"] == "kernel"]
    assert len(kernels) == 112
    modeled = 0
    for point in kernels:
        raw = dict(point["raw_row"])
        annotation = annotate_row(raw, launch_mode=point["launch_mode"],
                                  measured_us=point["measured_us"])
        assert annotation["status"] in {"clean", "unmeasured"}, point["id"]
        assert annotation["t_floor_us"] <= point["measured_us"]
        modeled += 1
    assert modeled == 112


def test_rejected_padded_varlen_record_is_invalid_abi(golden):
    rejected = golden["rejected_points"][0]
    annotation = annotate_row(rejected["raw_record"], measured_us=None)
    assert annotation["status"] == "invalid_abi"
    assert annotation["code"] == rejected["expected_code"]


def test_layer_block_points_are_consistent(golden):
    for point in golden["block_points"]:
        evaluation = evaluate_operator(
            point["operator"], point["params"],
            launch_mode=point["launch_mode"],
            steady_l2_warm=point["steady_l2_warm"])
        assert evaluation.latency.tau_hw_floor_us <= evaluation.t_floor_us
        assert evaluation.t_floor_us <= point["measured_us"]


@pytest.mark.skipif(not CAPTURE_DIR.exists(),
                    reason="read-only A5 capture mount is not present")
def test_fixture_rebuild_is_byte_identical(golden):
    spec = importlib.util.spec_from_file_location("a5_golden_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    rebuilt = module.build()
    expected = FIXTURE.read_text(encoding="utf-8")
    actual = json.dumps(rebuilt, indent=1, sort_keys=True) + "\n"
    assert actual == expected


# --------------------------------------------------------------------------- #
# Independent raw-descriptor oracles: parse the capture files directly and
# never call ``mindie_profiler.op_abi_bridge``.
# --------------------------------------------------------------------------- #
def _raw_shapes(text) -> list[list[int] | None]:
    out: list[list[int] | None] = []
    cleaned = str(text or "").strip().strip('"').strip("'")
    for token in cleaned.split(";"):
        token = token.strip().strip('"').strip("'")
        if not token:
            out.append(None)
            continue
        parts = [part for part in token.replace("x", ",").split(",")
                 if part.strip()]
        out.append([int(float(part)) for part in parts])
    return out


def _kernel_csv_rows() -> list[dict[str, str]]:
    with (CAPTURE_DIR / "kimi_layer_profile" / "kernel_details.csv").open(
            newline="", encoding="utf-8") as handle:
        raw_rows = list(csv.DictReader(handle))
    return [{
        "duration_us": row.get("Duration(us)"),
        "name": row.get("Name"),
        "type": row.get("Type"),
        "input_shapes": row.get("Input Shapes"),
        "input_data_types": row.get("Input Data Types"),
        "input_formats": row.get("Input Formats"),
        "output_shapes": row.get("Output Shapes"),
        "output_data_types": row.get("Output Data Types"),
        "output_formats": row.get("Output Formats"),
    } for row in raw_rows]


@pytest.mark.skipif(not CAPTURE_DIR.exists(),
                    reason="read-only A5 capture mount is not present")
def test_independent_raw_down_grouped_matmul_work(golden):
    rows = _kernel_csv_rows()
    down = [point for point in golden["points"]
            if point["operator"] == "grouped_matmul"
            and point["params"].get("mode") == "down"]
    assert len(down) == 8
    expected_flops = 180_388_626_432
    for point in down:
        raw = rows[point["source_row_index"]]
        inputs = _raw_shapes(raw["input_shapes"])
        outputs = _raw_shapes(raw["output_shapes"])
        assert inputs[0] == [4096, 3072]
        assert inputs[1] == [112, 3072, 7168]
        assert outputs[0] == [4096, 7168]
        dtypes = [item for item in str(raw["input_data_types"]).split(";")]
        assert dtypes[0] == "DT_BF16" and dtypes[1] == "DT_BF16"
        m_dim, k_dim = inputs[0]
        _, weight_k, n_dim = inputs[1]
        assert weight_k == k_dim
        flops = 2 * m_dim * k_dim * n_dim
        assert flops == expected_flops
        card = evaluate_operator(point["operator"], point["params"]).formula_card
        assert card.bindings["K"] == k_dim
        assert card.bindings["N"] == n_dim
        assert card.alg_flops == flops
        assert point["params"]["k_dim"] == k_dim
        assert point["params"]["n_dim"] == n_dim


@pytest.mark.skipif(not CAPTURE_DIR.exists(),
                    reason="read-only A5 capture mount is not present")
def test_independent_raw_matmul_and_grouped_flops(golden):
    rows = _kernel_csv_rows()
    checked = 0
    for point in golden["points"]:
        if point["group"] != "kernel":
            continue
        if point["operator"] not in {"matmul", "grouped_matmul"}:
            continue
        raw = rows[point["source_row_index"]]
        inputs = _raw_shapes(raw["input_shapes"])
        outputs = _raw_shapes(raw["output_shapes"])
        lhs = inputs[0]
        assert lhs is not None and len(lhs) == 2
        if point["operator"] == "matmul":
            weight = inputs[1]
            assert weight is not None and len(weight) == 2
            m_dim, k_dim = lhs
            assert weight[0] == k_dim
            n_dim = weight[1]
        else:
            weight = inputs[1]
            assert weight is not None and len(weight) == 3
            m_dim, k_dim = lhs
            assert weight[1] == k_dim
            n_dim = weight[2]
        assert outputs[0] == [m_dim, n_dim]
        flops = 2 * m_dim * k_dim * n_dim
        card = evaluate_operator(point["operator"], point["params"]).formula_card
        assert card.alg_flops == flops, point["id"]
        checked += 1
    assert checked == 37


@pytest.mark.skipif(not CAPTURE_DIR.exists(),
                    reason="read-only A5 capture mount is not present")
def test_independent_raw_collective_bytes(golden):
    source = json.loads((CAPTURE_DIR / "fabric_a5_16npu.json").read_text())
    fabric = [point for point in golden["points"] if point["group"] == "fabric"]
    assert len(fabric) == 120
    for point in fabric:
        raw = source["results"][point["source_row_index"]]
        assert raw["size_bytes"] == point["params"]["size_bytes"]
        elements = int(raw["size_bytes"]) // 2       # BF16 storage
        assert elements * 2 == int(raw["size_bytes"])
        card = evaluate_operator(point["operator"], point["params"]).formula_card
        assert card.bindings["bytes"] == int(raw["size_bytes"])
        assert card.bindings["dtype"] == "bf16"
        assert card.compulsory_read_bytes > 0
        assert card.compulsory_write_bytes > 0


@pytest.mark.skipif(not CAPTURE_DIR.exists(),
                    reason="read-only A5 capture mount is not present")
def test_independent_raw_attention_geometry(golden):
    source = json.loads((CAPTURE_DIR / "mha_gqa_mqa_and_padding_a5.json").read_text())
    checked = 0
    for point in golden["points"]:
        if point["group"] != "attention":
            continue
        section = point.get("source_section")
        if section not in {"A", "B", "C", "D"}:
            continue
        raw = source["results"][section][point["source_row_index"]]
        params = point["params"]
        if params.get("q_len") is None:
            continue
        assert params["hq"] == raw.get("hq", params["hq"])
        assert params["hkv"] == raw.get("hkv", params["hkv"])
        assert params["head_dim"] == 128
        if section == "C":
            q_len = kv_len = int(raw["T"])
            causal = bool(raw["causal"])
        elif section == "D":
            q_len, kv_len = int(raw["logical_m"]), 4096
            causal = False
        else:
            q_len, kv_len = int(raw["q_len"]), int(raw["kv_len"])
            causal = False
        assert params["q_len"] == q_len
        assert params["kv_len"] == kv_len
        if causal:
            offset = max(0, kv_len - q_len)
            pairs = sum(min(kv_len, offset + step + 1) for step in range(q_len))
        else:
            pairs = q_len * kv_len
        card = evaluate_operator(point["operator"], params).formula_card
        assert card.bindings["attended_pairs"] == pairs, point["id"]
        assert card.bindings["hq"] == params["hq"]
        assert card.bindings["hkv"] == params["hkv"]
        assert card.bindings["head_dim_qk"] == 128
        assert card.bindings["head_dim_v"] == 128
        checked += 1
    assert checked == 127


@pytest.mark.skipif(not CAPTURE_DIR.exists(),
                    reason="read-only A5 capture mount is not present")
def test_independent_raw_source_timings_match_fixture(golden):
    csv_rows = _kernel_csv_rows()
    mha = json.loads((CAPTURE_DIR / "mha_gqa_mqa_and_padding_a5.json").read_text())
    fabric = json.loads((CAPTURE_DIR / "fabric_a5_16npu.json").read_text())
    mc2 = json.loads((CAPTURE_DIR / "mc2_megamoe_ep_sweep.json").read_text())
    for point in golden["points"]:
        group = point["group"]
        index = point["source_row_index"]
        if group == "kernel":
            raw = csv_rows[index]
            measured = float(raw["duration_us"])
        elif group == "attention":
            measured = float(mha["results"][point["source_section"]][index]["p50_us"])
        elif group == "fabric":
            measured = float(fabric["results"][index]["p50_us"])
        else:
            stage = "dispatch" if point["operator"].endswith("dispatch") else "combine"
            measured = float(mc2["results"][index][f"{stage}_us"])
        assert measured == pytest.approx(point["measured_us"])
