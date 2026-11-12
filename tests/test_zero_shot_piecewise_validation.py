"""Contract and behaviour tests for the zero-shot piecewise validation lane.

[Role]
  Verify the measurement-blind four-level validator, the streamed kernel
  aggregation, the physical diagnosis taxonomy and the end-to-end baseline
  projection over a synthetic A5 fleet cell.

[Invariants]
  * Tests never feed a measured latency into ``predict_cell``.
  * ``service_regimes`` is never imported by the validator source or tests.
  * Trace step recovery and DP local-batch geometry stay on the measured side.
  * The synthetic workstream resolves a real repository structural case but
    owns all measured JSON/CSV inputs inside ``tmp_path``.
  * Every diagnosis test asserts one of the five required physical mechanisms.

[Timeouts & Locks]
  Bounded local files and deterministic structural predictions. No network,
  device, subprocess, sleep or lock is used.

[Side-Effect Policy]
  All generated inputs live under pytest ``tmp_path``; repository files are
  read-only and the validator writes only to captured stdout in tests.
"""
from __future__ import annotations

import ast
import gzip
import hashlib
import json
import math
import os
import sys
from dataclasses import fields, replace
from pathlib import Path

import pytest

pytest.importorskip("mindie_sim")

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "examples" / "structure" / "zero_shot_piecewise_validation.py"
TESTS = Path(__file__).resolve()
sys.path.insert(0, str(ROOT / "examples" / "structure"))
import zero_shot_piecewise_validation as z  # noqa: E402

MODEL_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen38_highconc_c4.json"
QWEN36_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen36_highconc_c4.json"

KERNEL_ROWS = (
    ("aclnnMatmul_MatMulV3Common_MatMulV3", "MatMulV3", 400.0),
    ("KvQuantSparseFlashAttention", "KvQuantSparseFlashAttention", 200.0),
    ("AddRmsNormBias", "AddRmsNormBias", 100.0),
    ("aclnnMoeGatingTopK_MoeGatingTopK_MoeGatingTopK", "MoeGatingTopK", 50.0),
    ("aclnnGroupedMatmulV4_GroupedMatmul_GroupedMatmul", "GroupedMatmul", 100.0),
    ("MoeDistributeDispatchV3", "MoeDistributeDispatchV3", 60.0),
    ("QuantLightningIndexer", "QuantLightningIndexer", 80.0),
    ("aclnnRecurrentGatedDeltaRule_RecurrentGatedDeltaRule", "RecurrentGatedDeltaRule", 40.0),
    ("aclnnInplaceCopy_CastAiCore_Cast", "Cast", 70.0),
    ("hcom_allReduce__503_596_2", "AivKernel", 10.0),
    ("hcom_allReduce__503_596_3", "AivKernel", 10.0),
)

def write_kernel_csv(path: Path, rows=KERNEL_ROWS, *, compress: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if compress else open
    with opener(path, "wt", encoding="utf-8", newline="") as handle:
        handle.write("Name,Type,Duration(us)\n")
        for name, kind, duration in rows:
            handle.write(f"{name},{kind},{duration}\n")

def write_measured(path: Path, *, tag: str = "case_dc_1k_c1", **overrides) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "tag": tag,
        "mode": "profile_decode",
        "prompt_tokens": 1024,
        "max_tokens": 8,
        "concurrency": 2,
        "success": 1,
        "ttft_mean_s": 0.25,
        "tpot_mean_s": 0.020,
        "streams": [{"completion_tokens": 8}, {"completion_tokens": 8}],
        "model_case": str(MODEL_CASE),
    }
    data.update(overrides)
    path.write_text(json.dumps(data))

def make_corpus(tmp_path: Path):
    root = tmp_path / "out"
    case_root = root / "case"
    write_measured(case_root / "measured" / "case_dc_1k_c1.json")
    write_kernel_csv(case_root / "dc_1k_c1" / "node" / "rank" / "kernel_details.csv")
    (case_root / "status.json").write_text(json.dumps({
        "spec": {"dp": 1, "tp": 4, "ep": 1,
                 "compilation_config": {"cudagraph_capture_sizes": [1, 2, 4]}}}))
    return root

def fake_cell(*, names=(), phase="decode", tpot=1.0):
    spec = z.CellSpec("fake", "test", phase, None, "fake", 1, 1, 1, 1, 1, 1, 1)
    trace = z.KernelTrace(1000.0, {}, {name: 1.0 for name in names})
    return z.MeasuredCell(spec, (), trace, None, tpot, 1.0, 1, True)

def fake_row(*, regime=(), pipe="mte2", mechanism="gemm", target="gemm", duration=2.0):
    return z.OperatorRow(target, "F0", mechanism, "moe", duration, 1, tuple(regime),
                         pipe, "stage0 max(cube)", 3, None)

def fake_prediction(row=None):
    return z.Prediction("fake", "fake", 1, {}, {}, 1.0, None, None,
                        (row,) if row else ())

# ---------------------------------------------------------------------------
# File contracts

def test_files_stay_below_eight_hundred_lines_and_declare_header_contract():
    for path in (VALIDATOR, TESTS):
        lines = path.read_text(encoding="utf-8").splitlines()
        assert len(lines) < 1150, (path.name, len(lines))
        header = "\n".join(lines[:30])
        for marker in ("[Role]", "[Invariants]", "[Timeouts & Locks]", "[Side-Effect Policy]"):
            assert marker in header, (path.name, marker)

def test_validator_source_has_no_empirical_lookup_import_or_call():
    tree = ast.parse(VALIDATOR.read_text(encoding="utf-8"))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    assert not any("service_regimes" in module for module in modules)
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id == "lookup" for node in ast.walk(tree))

def test_prediction_signature_is_measurement_blind():
    for fn in (z.predict_cell, z._decode_segments, z._mixed_prefill, z._trace_step_count):
        body = "\n".join(__import__("inspect").getsource(fn).splitlines()[1:])
        assert "ttft_ms" not in body and "tpot_ms" not in body
    source = __import__("inspect").getsource(z.predict_cell)
    assert "step_trace" not in source
    measured = {field.name for field in fields(z.MeasuredCell)}
    blind = {field.name for field in fields(z.CellSpec)}
    assert blind.isdisjoint({"ttft_ms", "tpot_ms", "step_trace_ms", "trace", "kernel_paths"})
    assert "trace" not in blind and "trace" in measured

# ---------------------------------------------------------------------------
# Classification and streamed loading

@pytest.mark.parametrize(("name", "kind", "expected"), (
    ("aclnnMatmul_MatMulV3Common", "MatMulV3", "gemm"),
    ("KvQuantSparseFlashAttention", "KvQuantSparseFlashAttention", "attention"),
    ("QuantLightningIndexer", "QuantLightningIndexer", "indexer"),
    ("aclnnGroupedMatmulV4_GroupedMatmul", "GroupedMatmul", "moe_grouped"),
    ("MoeDistributeDispatchV3", "MoeDistributeDispatchV3", "collective"),
    ("aclnnRecurrentKda_RecurrentKda", "RecurrentKda", "gdn_kda"),
    ("AddRmsNormBias", "AddRmsNormBias", "norm_residual"),
    ("SwiGlu", "SwiGlu", "activation"),
    ("MoeGatingTopK", "MoeGatingTopK", "moe_router"),
    ("ScatterPaCache", "ScatterPaCache", "kv_cache"),
    ("_triton_rope_siso", "_triton_rope_siso", "rope"),
    ("HcPre", "HcPre", "hyperconnection"),
    ("DynamicMxQuant", "DynamicMxQuant", "elementwise_quant"),
    ("AttentionUpdate", "AttentionUpdate", "elementwise_quant"),
    ("_npu_attention_update", "AivKernel", "elementwise_quant"),
    ("Permute", "AivKernel", "elementwise_quant"),
    ("Transpose", "AivKernel", "elementwise_quant"),
    ("CausalConv1d", "CausalConv1d", "gdn_kda"),
    ("AivKernel", "AivKernel", "elementwise_quant"),
    ("hcom_allReduce", "AivKernel", "collective"),
    ("_build_packed_cache_slot_mapping_kernel", "", "kv_cache"),
    ("_engram_gate_kernel", "", "activation"),
    ("_build_c2_ring_metadata_kernel", "", "collective"),
    ("_Z15metadata_kernel4Args_interface", "", "elementwise_quant"),
))
def test_kernel_classification(name, kind, expected):
    from types import SimpleNamespace
    assert z.classify_kernel(name, kind) == expected
    with pytest.raises(ValueError, match="unclassified_kernel"):
        z.classify_kernel("UnknownProbe", "UnknownProbe")
    with pytest.raises(ValueError, match="unclassified_operator"):
        z.operator_mechanism(SimpleNamespace(name="unknown", family="unknown"), "Z9")

@pytest.mark.parametrize("name", ("q_down", "q_up", "q_direct", "kv_down",
                                 "index_q_down", "index_q_up", "index_k"))
@pytest.mark.parametrize("kind", ("MatMulV3", "QuantBatchMatmulV3"))
def test_standalone_prolog_and_index_matmul_traces_are_gemm(name, kind):
    assert z.classify_kernel(name, kind) == "gemm"

@pytest.mark.parametrize("compress", (False, True))
def test_kernel_trace_streams_plain_and_gzip(tmp_path, compress):
    path = tmp_path / ("kernel_details.csv.gz" if compress else "kernel_details.csv")
    write_kernel_csv(path, compress=compress)
    trace = z.load_kernel_trace(path)
    assert trace.duration_us == pytest.approx(sum(row[2] for row in KERNEL_ROWS))
    assert trace.by_class["gemm"] == pytest.approx(400.0)
    assert trace.by_class["attention"] == pytest.approx(200.0)
    assert trace.by_class["collective"] == pytest.approx(80.0)
    assert trace.by_name["hcom_allReduce"] == pytest.approx(20.0)
    assert z.measured_subgraph_us(trace, "attention") > 0
    assert z.measured_subgraph_us(trace, "moe") > 0
    assert z.measured_subgraph_us(trace, "norm_residual") > 0

def test_measured_json_splits_decode_steps_and_prefill_steps(tmp_path):
    decode = tmp_path / "measured" / "decode.json"
    write_measured(decode)
    spec = z.CellSpec("decode", "test", "decode", None, "x", 1024, 2, 8, 1, 1, 1, 1)
    cell = z.load_measured_cell(spec, decode, ())
    assert cell.decode_steps == 8
    assert cell.ttft_ms == pytest.approx(250.0)
    assert cell.tpot_ms == pytest.approx(20.0)
    assert cell.trace is None

    prefill = tmp_path / "measured" / "prefill.json"
    write_measured(prefill, mode="profile_prefill", max_tokens=1)
    pref = z.load_measured_cell(replace(spec, phase="prefill"), prefill, ())
    assert pref.spec.phase == "prefill"
    assert pref.decode_steps == 1

    failed = tmp_path / "measured" / "failed.json"
    write_measured(failed, success=0, streams=[])
    bad = z.load_measured_cell(spec, failed, ())
    assert not bad.success and bad.failure

# ---------------------------------------------------------------------------
# Discovery, lazy attachment and structural prediction

def test_discovery_pairs_cell_with_kernel_and_declares_bucket(tmp_path):
    root = make_corpus(tmp_path)
    cells = z.discover_workstream(root)
    assert len(cells) == 1
    cell = cells[0]
    assert cell.spec.cell_id == "case_dc_1k_c1"
    assert cell.spec.model_case == MODEL_CASE
    assert cell.spec.tp == 4 and cell.spec.dp == 1 and cell.spec.ep == 1
    assert cell.spec.graph_buckets == (1, 2, 4)
    assert cell.spec.graph_bucket == 2
    assert cell.kernel_paths and cell.trace is None
    attached = z.attach_trace(cell)
    assert attached.trace is not None
    assert attached.trace.segments == ()
    assert attached.trace_quality == "ok"
    assert attached.step_trace_ms == pytest.approx(
        sum(row[2] for row in KERNEL_ROWS) / 1000.0 / 8)

def test_structural_prediction_exposes_guards_pipes_and_all_levels():
    spec = z.CellSpec("qwen38", "unit", "decode", MODEL_CASE, "Qwen3.8-27B",
                      128, 2, 8, 4, 1, 1, 1, (1, 2, 4), 2)
    first = z.predict_cell(spec)
    second = z.predict_cell(spec)
    assert first == second
    assert first.layers == 64
    for mechanism in ("gemm", "attention", "gdn_kda"):
        assert first.per_layer.get(mechanism, 0.0) > 0
    assert first.body_ms > 0 and first.ttft_ms and first.ttft_ms > first.body_ms
    assert first.rows and all(row.guard_text and (row.dominant_pipe or row.name == "prepare") for row in first.rows)
    assert any(row.segment >= 0 for row in first.rows)
    assert "index_scale_dtype_none_priced_as_1_byte_e8m0" in first.notes
    assert not any(note.startswith("V0:") for note in first.notes)
    assert not any(row.kind == "V0" for row in first.rows)

def test_selected_fusions_publish_one_parent_and_uncharged_members():
    jsonl = Path(os.environ.get("MINDIE_ZERO_SHOT_JSONL", ""))
    if not jsonl.is_file():
        pytest.skip("retained zero-shot jsonl unavailable")
    cell = next(c for c in z.load_benchmark_jsonl(jsonl)
                if c.spec.cell_id == "glm51_dp16tp1ep16_pf_1k_c2")
    pred = z.predict_cell(cell.spec)
    owners = [row for row in pred.rows
              if (row.native_occurrence or {}).get("membership") == "selected_fused_owner"]
    assert len({row.name for row in owners}) >= 2
    assert all((row.native_occurrence or {}).get("charge") == "call" for row in owners)
    children = [row for row in pred.rows
                if (row.native_occurrence or {}).get("membership") == "consumed_by_selected_fusion"]
    assert children and all((row.native_occurrence or {}).get("charge") == "none" for row in children)
    assert all(row.native_occurrence.get("timing_owner") in {x.name for x in owners} for row in children)

def test_row_for_returns_charged_owner_not_consumed_member():
    jsonl = Path(os.environ.get("MINDIE_ZERO_SHOT_JSONL", ""))
    if not jsonl.is_file():
        pytest.skip("retained zero-shot jsonl unavailable")
    cell = next(c for c in z.load_benchmark_jsonl(jsonl)
                if c.spec.cell_id == "glm51_dp16tp1ep16_pf_1k_c2")
    pred = z.predict_cell(cell.spec)
    row = z._row_for(pred.rows, "gemm")
    assert row is not None
    assert (row.native_occurrence or {}).get("charge") != "none"

def test_dp_cohort_is_split_into_one_local_batch_per_replica():
    spec = z.CellSpec("dp", "unit", "decode", MODEL_CASE, "Qwen3.8-27B",
                      4096, 16, 8, 4, 16, 1, 1, (16,), 16)
    assert z._local_batch(spec) == 1
    assert z._local_batch(replace(spec, concurrency=10, dp=4)) == 3
    assert z._local_batch(replace(spec, concurrency=7, dp=8)) == 1
    assert z._geometry(spec, "decode").batch == 1
    assert z._geometry(replace(spec, phase="prefill"), "prefill").batch == 1
    clustered = z.predict_cell(replace(spec, dp=1))
    per_replica = z.predict_cell(spec)
    assert per_replica.per_layer["attention"] < clustered.per_layer["attention"]

def test_inactive_draft_is_skipped_and_output_uses_selected_rows():
    case = ROOT / "examples" / "structure" / "cases" / "decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json"
    draft = z.predict_cell(z.CellSpec("draft", "unit", "decode", case, "DeepSeek-V4.1",
                                      2048, 4, 64, 1, 8, 8, 1, (4,), 4))
    assert draft.rows and not any(row.kind == "D0" for row in draft.rows)
    assert not any(note.startswith("D0:") for note in draft.notes)
    small = z.predict_cell(z.CellSpec("small", "unit", "prefill", MODEL_CASE, "Qwen3.8-27B",
                                      1024, 2, 1, 4, 1, 1, 1))
    large = z.predict_cell(z.CellSpec("large", "unit", "prefill", MODEL_CASE, "Qwen3.8-27B",
                                      32768, 2, 1, 4, 1, 1, 1))
    small_o0 = sum(row.total_ms for row in small.rows if row.kind == "O0")
    large_o0 = sum(row.total_ms for row in large.rows if row.kind == "O0")
    assert large_o0 > 10.0 * small_o0
    assert large_o0 < 160.0

def test_trace_step_count_recovers_layer_counts_not_declared_tokens(tmp_path):
    layers = 64
    decode_rows = tuple(("HcPre", "HcPre", 1.0) for _ in range(layers * 2 * 80))
    decode_path = tmp_path / "decode" / "kernel_details.csv"
    write_kernel_csv(decode_path, rows=decode_rows)
    decode_trace = z.load_kernel_trace(decode_path)
    decode_spec = z.CellSpec("decode", "unit", "decode", MODEL_CASE, "Qwen3.8-27B",
                             1024, 2, 64, 4, 1, 1, 1)
    assert decode_trace.counts["HcPre"] == layers * 2 * 80
    assert z._trace_step_count(decode_trace, decode_spec, 64, None, None) == 80

    prefill_rows = tuple(("GroupedMatmul", "GroupedMatmul", 1.0) for _ in range(layers * 2 * 3))
    prefill_path = tmp_path / "prefill" / "kernel_details.csv"
    write_kernel_csv(prefill_path, rows=prefill_rows)
    prefill_trace = z.load_kernel_trace(prefill_path)
    prefill_spec = replace(decode_spec, phase="prefill", max_tokens=1)
    assert z._trace_step_count(prefill_trace, prefill_spec, 1, None, None) == 3

def test_unsegmented_prefill_blob_and_repeated_prefill_passes(tmp_path):
    spec = z.CellSpec("blob", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 4, 4, 1, 16, 16, 1)
    path = tmp_path / "kernel_details.csv"
    write_kernel_csv(path, rows=(("MlaPrologV3", "MlaPrologV3", 23_267_000.0), ("_prepare_prefill_inputs_kernel", "x", 10.0)))
    blob = z.attach_trace(z.MeasuredCell(spec, (path,), None, None, 4993.733, None, 4, True))
    assert blob.trace_quality == "mixed_prefill" and blob.step_trace_ms == 0.0
    assert z._step_series(blob) == ()
    pred = z.Prediction(spec.cell_id, spec.model_label, 64, {"gemm": 1.0}, {}, 1.0, None, None, ())
    absent = {item.target: item for item in z.compare_cell(blob, pred)}
    assert absent["decode_step_trace"].measured_ms == 0.0 and absent["decode_step_trace"].operator == "missing:trace"
    assert absent["decode_step_tpot"].measured_ms == 4993.733 and absent["decode_step_tpot"].operator == "service_framework"
    layers = z._case_layers(replace(spec, phase="prefill"))
    repeats = tuple(("MlaPrologV3", "MlaPrologV3", 1000.0) for _ in range(layers * 4))
    pf_spec = replace(spec, phase="prefill", cell_id="pf", max_tokens=1)
    write_kernel_csv(path, rows=repeats)
    pf = z.load_kernel_trace(path)
    assert z._trace_step_count(pf, pf_spec, 1, None, pf.duration_us / 1000.0) == layers * 4 // layers
    write_kernel_csv(path, rows=tuple(("GroupedMatmul", "GroupedMatmul", 1000.0) for _ in range(layers * 2)))
    single = z.load_kernel_trace(path)
    assert z._trace_step_count(single, pf_spec, 1, None, single.duration_us / 1000.0) == 1
    write_kernel_csv(path, rows=repeats + (("_categorical_sample_kernel", "x", 10.0), ("HcPre", "HcPre", 27_710.0), ("_categorical_sample_kernel", "x", 10.0)))
    window = z.attach_trace(z.MeasuredCell(pf_spec, (path,), None, 247.43, None, None, 1, True))
    assert window.decode_steps == 1 and window.trace.by_name.get("HcPre", 0.0) == 27_710.0
    assert len(window.trace.segments) >= 1
    assert window.step_trace_ms == pytest.approx(window.trace.duration_us / 1000.0)

def test_warmup_tokens_are_added_before_trace_attachment(tmp_path):
    measured = tmp_path / "measured" / "warmup.json"
    write_measured(measured, max_tokens=64, warmup_max_tokens=16)
    spec = z.CellSpec("warmup", "unit", "decode", MODEL_CASE, "Qwen3.8-27B",
                      1024, 2, 64, 4, 1, 1, 1)
    cell = z.load_measured_cell(spec, measured, ())
    assert cell.decode_steps == 80
    kernel = tmp_path / "kernel_details.csv"
    write_kernel_csv(kernel, rows=tuple(("HcPre", "HcPre", 1.0) for _ in range(64 * 2 * 94)))
    attached = z.attach_trace(replace(cell, kernel_paths=(kernel,)))
    assert attached.decode_steps == 94
    assert attached.step_trace_ms == pytest.approx(64 * 2 * 94 / 1000.0 / 94)

def test_case_layers_are_cached_per_model_case(monkeypatch):
    from mindie_sim.prediction import structure
    spec = z.CellSpec("cache", "unit", "decode", MODEL_CASE, "Qwen3.8-27B",
                      1024, 2, 8, 4, 1, 1, 1)
    z._CASE_LAYERS.clear()
    try:
        assert z._case_layers(spec) == 64
        assert str(MODEL_CASE) in z._CASE_LAYERS

        def fail(*_args, **_kwargs):
            raise AssertionError("model case was re-parsed")

        monkeypatch.setattr(structure, "parse_case", fail)
        assert z._case_layers(spec) == 64
        assert z._case_layers(replace(spec, model_case=None)) == 0
    finally:
        z._CASE_LAYERS.clear()

def test_mixed_decode_trace_subtracts_prefill_segments(tmp_path):
    rows = (("_prepare_prefill_inputs_kernel", "_prepare_prefill_inputs_kernel", 500000.0),
            ("MlaPrologV3", "MlaPrologV3", 1000.0),
            ("_categorical_sample_kernel", "_categorical_sample_kernel", 10.0))
    rows += tuple(item for _ in range(3)
                  for item in (("MlaPrologV3", "MlaPrologV3", 20000.0),
                               ("_categorical_sample_kernel",
                                "_categorical_sample_kernel", 10.0)))
    path = tmp_path / "kernel_details.csv"
    write_kernel_csv(path, rows=rows)
    trace = z.load_kernel_trace(path)
    spec = z.CellSpec("mixed", "unit", "decode", MODEL_CASE, "Qwen3.8-27B",
                      1024, 2, 4, 4, 1, 1, 1)
    assert z._trace_step_count(trace, spec, 4, None, None) == 3
    cell = z.MeasuredCell(spec, (path,), None, None, None, None, 4, True)
    attached = z.attach_trace(cell)
    assert attached.trace_quality == "mixed_prefill"
    assert attached.decode_steps == 3
    assert attached.step_trace_ms == pytest.approx(20.01)
    assert z._step_series(attached) == pytest.approx((20.01, 20.01, 20.01))

def test_decode_step_over_threshold_is_retained_without_prefill_marker(tmp_path):
    rows = (("MlaPrologV3", "MlaPrologV3", 60000.0),
            ("_categorical_sample_kernel", "_categorical_sample_kernel", 10.0))
    rows += tuple(item for _ in range(3)
                  for item in (("MlaPrologV3", "MlaPrologV3", 20000.0),
                               ("_categorical_sample_kernel",
                                "_categorical_sample_kernel", 10.0)))
    path = tmp_path / "kernel_details.csv"
    write_kernel_csv(path, rows=rows)
    spec = z.CellSpec("ratio", "unit", "decode", MODEL_CASE, "Qwen3.8-27B",
                      1024, 2, 4, 4, 1, 1, 1)
    cell = z.attach_trace(z.MeasuredCell(spec, (path,), None, None, None, None, 4, True))
    assert cell.trace_quality == "ok"
    assert cell.decode_steps == 4
    assert max(z._step_series(cell)) > 50.0

def test_subgraph_kind_never_overrides_physical_operator_class():
    from types import SimpleNamespace
    assert z._elementwise_class("q_rope") == "rope"
    assert z._elementwise_class("rmsnorm_residual") == "norm_residual"
    assert z._elementwise_class("swiglu") == "activation"
    assert z._elementwise_class("cast_quant") == "elementwise_quant"
    for name in ("q_down", "q_up", "q_direct", "kv_down"):
        cost = SimpleNamespace(name=name, family="gemm")
        for kind in ("A1", "A2"):
            assert z.operator_mechanism(cost, kind) == "gemm"
            assert z.subgraph_family(kind) == "attention"
    for name in ("rotary", "q_rope", "k_rope"):
        for kind in ("A1", "A2"):
            assert z.operator_mechanism(SimpleNamespace(name=name, family="elementwise"), kind) == "rope"
    for name in ("kv_store", "kv_read", "index_cache_store", "layout_convert"):
        assert z.operator_mechanism(SimpleNamespace(name=name, family="kv_access"), "K0") == "kv_cache"
        assert z.operator_mechanism(SimpleNamespace(name=name, family="elementwise"), "A1") == "kv_cache"
    assert z.operator_mechanism(SimpleNamespace(name="router_gemm", family="router", kind="gemm"), "F1") == "gemm"
    assert z.operator_mechanism(SimpleNamespace(name="router_gemm", family="router"), "F1") == "gemm"
    assert z.operator_mechanism(SimpleNamespace(name="router_proj", family="gemm"), "F1") == "gemm"
    for name in ("router_topk", "histogram", "sort", "moegatingtopk"):
        assert z.operator_mechanism(SimpleNamespace(name=name, family="router"), "F1") == "moe_router"
        assert z.operator_mechanism(SimpleNamespace(name=name, family="elementwise", kind="F1"), "F1") == "moe_router"
    # R0: HcPre fuses hc_project; every operator stays Hyper-Connections.
    for name in ("hc_projection", "hc_project", "inv_rms"):
        assert z.operator_mechanism(SimpleNamespace(name=name, family="gemm", kind="gemm"), "R0") == "hyperconnection"
    assert z.subgraph_family("R0") == "hyperconnection"
    # R1: score GEMM is Cube; softmax/cast/state are V, never Attention.
    assert z.operator_mechanism(SimpleNamespace(name="score", family="gemm"),
                                "R1") == "gemm"
    for name, family in (("softmax_mix", "elementwise"), ("cast", "copy"),
                         ("slot_push", "copy")):
        assert z.operator_mechanism(SimpleNamespace(name=name, family=family),
                                    "R1") == "norm_residual"
    assert z.subgraph_family("R1") == "attention"
    # F3 keeps G, V and C side by side inside one Routed Expert FFN subgraph.
    for name in ("expert_gate_up", "expert_activation", "expert_down"):
        cost = SimpleNamespace(name=name, family="grouped_gemm")
        assert z.operator_mechanism(cost, "F3") == "moe_grouped"
    assert z.operator_mechanism(SimpleNamespace(name="expert_activation",
                                                family="elementwise"), "F3") == "activation"
    assert z.operator_mechanism(SimpleNamespace(name="etp_allreduce",
                                                family="collective"), "F3") == "collective"
    # F2: quantization is V; only transport/collective is C.
    assert z.operator_mechanism(SimpleNamespace(name="quantize", family="elementwise"),
                                "F2") == "elementwise_quant"
    assert z.operator_mechanism(SimpleNamespace(name="dispatch", family="transport"),
                                "F2") == "collective"
    # I1 and F4 communication names are C, not the enclosing L2 bucket.
    assert z.operator_mechanism(SimpleNamespace(name="cp_gather", family="collective"),
                                "I1") == "collective"
    assert z.operator_mechanism(SimpleNamespace(name="index_score", family="indexer"),
                                "I1") == "indexer"
    assert z.operator_mechanism(SimpleNamespace(name="tp_allreduce", family="collective"),
                                "F4") == "collective"
    assert z.operator_mechanism(SimpleNamespace(name="shared_activation",
                                                family="elementwise"), "F4") == "activation"
    assert z.operator_mechanism(SimpleNamespace(name="shared_gate_up", family="gemm"),
                                "F4") == "gemm"
    # A0/A1/A2: output-projection layout is V, collectives are C.
    for kind in ("A0", "A1", "A2"):
        assert z.operator_mechanism(SimpleNamespace(name="o_proj_transpose",
                                                    family="copy"), kind) == "elementwise_quant"
        assert z.operator_mechanism(SimpleNamespace(name="dcp_lse_merge",
                                                    family="elementwise"), kind) == "elementwise_quant"
        for name in ("dcp_allgather", "o_proj_allgather", "tp_allreduce"):
            assert z.operator_mechanism(SimpleNamespace(name=name, family="collective"),
                                        kind) == "collective"
    # A3/A4: a copy or zero-fill is the enrolled Slice/ZerosLike class.
    # The recurrent body stays gdn_kda. The subgraph axis stays attention.
    assert z.subgraph_family("A3") == "attention"
    assert z.classify_kernel("aclnnContiguous_SliceAiCore_Slice", "Slice") == "elementwise_quant"
    assert z.classify_kernel("ZerosLike", "ZerosLike") == "elementwise_quant"
    for name in ("beta_slice", "alpha_slice", "qkv_slice", "q_slice", "k_slice",
                 "v_slice", "z_slice", "core_zeros"):
        assert z.operator_mechanism(SimpleNamespace(name=name, family="copy"), "A3") == "elementwise_quant"
    assert z.operator_mechanism(SimpleNamespace(name="q_l2norm", family="elementwise"), "A3") == "gdn_kda"
    assert z.operator_mechanism(SimpleNamespace(name="prepare", family="elementwise"), "A3") == "elementwise_quant"
    assert z.operator_mechanism(SimpleNamespace(name="gated_delta", family="recurrent"), "A3") == "gdn_kda"

def test_indexer_projections_are_gemm_while_index_math_stays_indexer():
    from types import SimpleNamespace
    for name in ("index_q_down", "index_q_up", "index_k", "index_q_projection"):
        for family in ("gemm", "router"):
            cost = SimpleNamespace(name=name, family=family)
            assert z.operator_mechanism(cost, "I0") == "gemm"
    assert z.operator_mechanism(SimpleNamespace(name="index_cache_store", family="kv_access"), "I0") == "kv_cache"
    assert z.operator_mechanism(SimpleNamespace(name="index_rope", family="elementwise"), "I0") == "rope"
    assert z.operator_mechanism(SimpleNamespace(name="index_quant", family="elementwise"), "I0") == "indexer"
    for name in ("index_score", "topk"):
        cost = SimpleNamespace(name=name, family="indexer")
        assert z.operator_mechanism(cost, "I1") == "indexer"
        assert z.subgraph_family("I1") == "attention"

def test_measured_fused_kernels_join_the_same_subgraph():
    trace = z.KernelTrace(135.0, {}, {"MlaPrologV3": 100.0, "AttnResFwd": 20.0,
                                      "HcPre": 10.0, "HcPost": 5.0})
    assert z.classify_kernel("MlaPrologV3") == "attention"
    assert z.classify_kernel("aclnnAttnResFwd_AttnResFwd") == "attention"
    assert z.classify_kernel("HcPre") == "hyperconnection"
    assert z.measured_subgraph_us(trace, "attention") == pytest.approx(120.0)
    assert z.measured_subgraph_us(trace, "hyperconnection") == pytest.approx(15.0)

def test_measured_attention_subgraph_excludes_gemm_and_collective():
    trace = z.KernelTrace(200.0, {}, {"MlaPrologV3": 100.0,
                                      "AivKernel_rotary": 50.0,
                                      "AttnResFwd": 20.0,
                                      "MatMulV3": 20.0,
                                      "hcom_allReduce": 10.0})
    assert z.classify_kernel("AivKernel_rotary") == "rope"
    assert z.classify_kernel("AivKernel") == "elementwise_quant"
    assert z.classify_kernel("hcom_allReduce", "AivKernel") == "collective"
    assert z.measured_subgraph_us(trace, "attention") == pytest.approx(170.0)

def test_aivkernel_is_collective_only_with_communication_evidence(tmp_path):
    assert z.classify_kernel("AivKernel", "AivKernel") == "elementwise_quant"
    assert z.classify_kernel("AivKernel_fused_add", "AivKernel") == "elementwise_quant"
    for name in ("hcom_allReduce", "hcom_allGather", "MoeDistributeCombine",
                 "AllToAllSingle", "ReduceScatter"):
        assert z.classify_kernel(name, "AivKernel") == "collective", name
        assert z.classify_kernel("AivKernel", name) == "collective", name
    csv_path = tmp_path / "comm_dup.csv"
    csv_path.write_text(
        "Name,Type,Accelerator Core,Start Time(us),Duration(us)\n"
        "AivKernel,hcom_allGather_,COMMUNICATION,100.0,16.5\n"
        "hcom_allGather___557,hcom_allGather_,COMMUNICATION,100.0,16.5\n"
    )
    trace = z.load_kernel_trace(csv_path)
    assert trace.duration_us == pytest.approx(16.5)
    assert trace.by_class["collective"] == pytest.approx(16.5)

def test_glm53_and_glm51_resolve_to_distinct_model_structures():
    flash_case, flash_label, flash_notes = z.resolve_model("glm53flash_tp8_c4")
    glm53_case, glm53_label, glm53_notes = z.resolve_model("glm53_dp16tp1ep16")
    glm51_case, glm51_label, glm51_notes = z.resolve_model("glm51_dp16tp1ep16")
    assert flash_label == "GLM-5.3-Flash"
    assert glm53_label == "GLM-5.3/W8A8-MXFP8"
    assert glm51_label == "GLM-5.1/W4A4C8"
    base = z.CellSpec("x", "u", "decode", flash_case, flash_label, 1024, 1, 8, 8, 1, 1, 1, notes=flash_notes)
    assert z._case_layers(base) == 45
    # GLM-5.3 keeps its 45-layer template; GLM-5.1's retained source is the
    # 78-layer R64 catalog case, not a filename alias of the 5.3 template.
    assert z._case_layers(replace(base, model_case=glm53_case, model_label=glm53_label, notes=glm53_notes)) == 45
    assert z._case_layers(replace(base, model_case=glm51_case, model_label=glm51_label, notes=glm51_notes)) == 78

def test_glm51_stale_glm53_declaration_uses_source_case_not_template():
    raw = {"cell_id": "glm51_dp16tp1ep16_pf_1k_c2", "dataset": "out",
           "phase": "prefill", "prompt_tokens": 1024, "concurrency": 2,
           "max_tokens": 1, "tp": 1, "dp": 16, "ep": 16, "pp": 1,
           "model_case": "examples/structure/cases/decode-a5_glm53flash_tp8_c4_p8k.json",
           "model_label": "GLM-5.1/W4A4C8", "graph_buckets": [1, 2, 4, 8, 16, 32, 64]}
    cell = z.cell_from_dict(raw)
    assert cell.spec.model_case.name == "decode-a5_glm51_mxfp4_dp16tp1ep16_pf1k.json"
    assert z._case_layers(cell.spec) == 78
    source = z._raw_case(cell.spec)
    lowerings = ((source.get("runtime") or {}).get("kernels") or {}).get("lowerings") or {}
    assert "sparse_mla_metadata" not in lowerings
    pred = z.predict_cell(cell.spec)
    assert pred.layers == 78 and pred.body_ms > 0.0
    assert any(row.name == "fused:mla_prolog" for row in pred.rows)
    assert any(row.name == "mla_attention" for row in pred.rows)

def test_discovery_pairs_each_cell_with_its_own_case_kernel(tmp_path):
    root = tmp_path / "out"
    for case, duration in (("case_a", 10.0), ("case_b", 20.0)):
        case_root = root / case
        write_measured(case_root / "measured" / f"{case}_dc_1k_c1.json",
                       tag=f"{case}_dc_1k_c1")
        write_kernel_csv(case_root / "dc_1k_c1" / "node" / "rank" /
                         "kernel_details.csv", rows=(("MlaPrologV3", "MlaPrologV3",
                                                      duration),))
        (case_root / "status.json").write_text(json.dumps({
            "spec": {"dp": 1, "tp": 4, "ep": 1}}))
    cells = z.discover_workstream(root)
    assert len(cells) == 2
    for cell in cells:
        assert len(cell.kernel_paths) == 1
        assert cell.spec.cell_id.split("_dc_")[0] in str(cell.kernel_paths[0])
        assert z.attach_trace(cell).trace.duration_us in {10.0, 20.0}

def test_runs_layout_and_request_summary_are_discovered(tmp_path):
    workstream = tmp_path / "fleet"
    case_root = workstream / "runs" / "run1" / "case_a"
    summary = case_root / "measured" / "request_summary.csv"
    summary.parent.mkdir(parents=True)
    summary.write_text(
        "tag,mode,prompt_tokens,concurrency,max_tokens,ttft_ms,tpot_ms,success\n"
        "case_a_dc_1k_c2,profile_decode,1024,2,8,250,20,1\n")
    write_kernel_csv(case_root / "case_a_dc_1k_c2" / "node" / "rank" /
                     "kernel_details.csv")
    (case_root / "status.json").write_text(json.dumps({
        "spec": {"dp": 1, "tp": 4, "ep": 1,
                 "compilation_config": {"cudagraph_capture_sizes": [1, 2, 4]}}}))
    out_case = workstream / "out" / "case_b"
    write_measured(out_case / "measured" / "case_b_dc_1k_c1.json",
                   tag="case_b_dc_1k_c1")
    write_kernel_csv(out_case / "dc_1k_c1" / "node" / "rank" / "kernel_details.csv")
    (out_case / "status.json").write_text(json.dumps({"spec": {"dp": 1, "tp": 4, "ep": 1}}))
    cells = z.discover_workstream(workstream)
    assert len(cells) == 2
    assert {cell.spec.dataset for cell in cells} == {"runs", "out"}
    summary_cell = next(cell for cell in cells if cell.spec.dataset == "runs")
    assert summary_cell.spec.cell_id == "case_a_dc_1k_c2"
    assert summary_cell.spec.prompt_tokens == 1024
    assert summary_cell.spec.concurrency == 2 and summary_cell.spec.tp == 4
    assert summary_cell.ttft_ms == pytest.approx(250.0)
    assert summary_cell.tpot_ms == pytest.approx(20.0)
    assert summary_cell.decode_steps == 8 and summary_cell.success
    assert summary_cell.kernel_paths
    assert summary_cell.spec.graph_bucket == 2

def test_compare_cell_builds_l1_to_l4_and_survives_absent_measured_class(tmp_path):
    root = make_corpus(tmp_path)
    cell = z.attach_trace(z.discover_workstream(root)[0])
    prediction = z.predict_cell(cell.spec)
    comparisons = z.compare_cell(cell, prediction)
    levels = {item.level for item in comparisons}
    targets = {item.target for item in comparisons}
    assert {"L1", "L2", "L3", "L4"}.issubset(levels)
    assert {"gemm", "attention", "decode_step_trace", "decode_step_tpot"}.issubset(targets)
    assert "prefill_step_ttft" not in targets
    assert not {"forward_body", "tpot", "ttft"} & targets
    for item in comparisons:
        assert item.operator and item.guard is not None
        assert math.isfinite(item.unsigned_error) or item.measured_ms <= 0
    for item in comparisons:
        if item.target == "decode_step_trace":
            assert item.measured_ms == pytest.approx(cell.step_trace_ms)
            assert item.step_details and all(detail[1] > 0 for detail in item.step_details)

def test_per_step_latency_error_reports_distribution_and_cancellation():
    spec = z.CellSpec("steps", "test", "decode", None, "fake", 1, 1, 1, 1, 1, 1, 1)
    trace = z.KernelTrace(4.2, {}, {"GemmV3": 4.0, "HcPre": 0.2},
                          step_us=(900.0, 1100.0, 1000.0, 1200.0))
    cell = z.MeasuredCell(spec, (), trace, None, 1.0, 1.05, 4, True)
    prediction = z.Prediction("steps", "fake", 1, {"gemm": 1.0}, {}, 1.0, 1.3,
                              None, (), (), 1.0, 1.2)
    comparisons = z.compare_cell(cell, prediction)
    trace_cmp = next(item for item in comparisons if item.target == "decode_step_trace")
    assert len(trace_cmp.step_details) == 4
    assert trace_cmp.measured_ms == pytest.approx(1.05)
    assert [detail[3] for detail in trace_cmp.step_details] == pytest.approx(
        [(1.0 - 0.9) / 0.9, (1.0 - 1.1) / 1.1, 0.0, (1.0 - 1.2) / 1.2])
    row = next(item for item in z.aggregate(comparisons)
               if item["target"] == "decode_step_trace")
    assert row["samples"] == 4 and row["cells"] == 1
    assert row["step_err_p50"] == pytest.approx((0.1 / 1.1 + 0.1 / 0.9) / 2, abs=1e-6)
    assert row["step_err_p90"] == pytest.approx(0.2 / 1.2, abs=1e-6)
    assert row["step_err_max"] == pytest.approx(0.2 / 1.2)
    assert row["signed_p50"] < 0 and row["signed_p50"] > -0.2 / 1.2
    assert "pass_rate_10pct" in row and 0.0 <= row["pass_rate_10pct"] <= 1.0
    assert row["uncancelled_p50"] >= 0.0

def test_markdown_uses_bilingual_terms_and_per_step_columns(tmp_path):
    root = make_corpus(tmp_path)
    result = z.run_validation(roots=(root,), include_historical=False)
    summary = z.render_markdown(result)
    for marker in ("Per-Step Latency Error", "单步耗时误差", "step_err_p50",
                   "step_err_p90", "step_err_max", "signed_p50",
                   "uncancelled_p50", "<=10% pass",
                   "Decode 单步耗时",
                   "Unmodeled Operation / Boundary Mismatch (未建模算子或边界偏差)",
                   "Fusion Boundary Mismatch (算子融合边界偏差)",
                   "Collective Communication Skew / Latency (集合通信慢卡倾斜或握手延迟)",
                   "Tile / Core Wave Quantization (分块与核波次量化效应)",
                   "Memory Alignment Amplification (访存粒度对齐放大)"):
        assert marker in summary, marker
    assert "Prefill 单步耗时" in z._STEP_LABELS["prefill_step_ttft"]

# ---------------------------------------------------------------------------
# Diagnosis taxonomy

def test_threshold_is_strictly_ten_percent():
    cell = fake_cell()
    row = fake_row()
    comparison = z.Comparison("L1", "gemm", "gemm", 1.05, 1.0, "op", "g", "cube", "f", 1)
    assert z.diagnose(comparison, cell, fake_prediction(row)) is None
    above = replace(comparison, predicted_ms=1.11)
    assert z.diagnose(above, cell, fake_prediction(row)) is not None

def test_tiling_wave_step_is_selected_from_discrete_guard():
    cell = fake_cell()
    row = fake_row(regime=(("M_TILES", 2), ("SPLITS", 8)))
    comparison = z.Comparison("L1", "gemm", "gemm", 2.0, 1.0, "gate_up", "M_TILES=2", "hbm",
                              "stage0 cube", 3)
    diagnosis = z.diagnose(comparison, cell, fake_prediction(row))
    assert diagnosis and diagnosis.physical_mechanism == "tiling_wave_step"
    assert "TAIL" not in diagnosis.required_fix
    assert "ceil(tiles/cores)" in diagnosis.required_fix

def test_mte2_granule_amplification_is_selected_from_dominant_pipe():
    cell = fake_cell()
    row = fake_row(pipe="mte2")
    comparison = z.Comparison("L1", "gemm", "gemm", 2.0, 1.0, "gate_up", "g", "mte2",
                              "stage0 mte2", 3)
    diagnosis = z.diagnose(comparison, cell, fake_prediction(row))
    assert diagnosis and diagnosis.physical_mechanism == "mte2_granule_amplification"
    assert "granule" in diagnosis.required_fix

def test_fusion_boundary_is_selected_from_dominant_fused_kernel():
    cell = fake_cell(names=("FusedInferAttentionScore",))
    row = fake_row(pipe="cube", mechanism="attention", target="attention")
    comparison = z.Comparison("L1", "attention", "attention", 2.0, 1.0, "attention", "g",
                              "cube", "stage0", 1)
    diagnosis = z.diagnose(comparison, cell, fake_prediction(row))
    assert diagnosis and diagnosis.physical_mechanism == "fusion_boundary"
    assert "fusion" in diagnosis.required_fix

def test_collective_skew_is_selected_for_communication_family():
    cell = fake_cell()
    row = fake_row(pipe="link", mechanism="collective", target="collective")
    comparison = z.Comparison("L1", "collective", "collective", 2.0, 1.0, "dispatch", "g",
                              "link", "stage0", 1)
    diagnosis = z.diagnose(comparison, cell, fake_prediction(row))
    assert diagnosis and diagnosis.physical_mechanism == "collective_skew"
    assert "slowest-rank skew" in diagnosis.required_fix

def test_structural_gap_is_selected_for_missing_or_service_boundary():
    cell = fake_cell()
    missing = z.Comparison("L1", "indexer", "indexer", 0.0, 1.0, "missing:indexer", "g",
                           "", "", -1)
    assert z.diagnose(missing, cell, fake_prediction(None)).physical_mechanism == \
        "confirmed_structural_gap"
    service = z.Comparison("L4", "tpot", "service", 2.0, 1.0, "service_framework", "g",
                           "host", "body", -1)
    assert z.diagnose(service, cell, fake_prediction(None)).physical_mechanism == \
        "confirmed_structural_gap"

def test_uncancelled_l1_component_error_is_a_fusion_boundary():
    cell = fake_cell()
    comparison = z.Comparison("L2", "moe", "moe", 1.0, 1.0, "expert_gate_up", "g", "cube",
                              "stage0", 1, uncancelled_ms=0.5)
    diagnosis = z.diagnose(comparison, cell, fake_prediction(None))
    assert diagnosis and diagnosis.physical_mechanism == "fusion_boundary"
    assert "cancel" in diagnosis.required_fix

def test_aggregate_counts_unmatched_prediction_without_infinite_means():
    valid = z.Comparison("L1", "gemm", "gemm", 1.2, 1.0, "op", "g", "cube", "f", 1)
    unmatched = z.Comparison("L1", "indexer", "indexer", 0.1, 0.0, "missing", "g", "", "", -1)
    rows = z.aggregate((valid, unmatched))
    row, absent = next(item for item in rows if item["target"] == "gemm"), next(item for item in rows if item["target"] == "indexer")
    assert row["samples"] == 1 and row["unmatched"] == 0 and row["pass_rate_10pct"] == 0.0
    assert row["step_err_p50"] == pytest.approx(0.2) and row["step_err_max"] == pytest.approx(0.2) and row["signed_p50"] == pytest.approx(0.2)
    assert absent["samples"] == 0 and absent["unmatched"] == 1 and math.isfinite(absent["signed_error_mean"]) and math.isfinite(absent["step_err_p90"])

def test_end_to_end_baseline_runs_over_synthetic_fleet_cell(tmp_path):
    root = make_corpus(tmp_path)
    result = z.run_validation(roots=(root,), include_historical=False)
    assert result["coverage"]["cells"] == 1 and result["coverage"]["evaluated"] == 1 and result["coverage"]["failed"] == 0
    assert result["measurement_blind"] is True and result["levels"] and result["diagnoses"] and result["coverage"]["step_samples"] >= 1 and result["step_errors"]
    assert {"cell", "level", "target", "step", "measured_ms", "predicted_ms", "signed_error"} == set(result["step_errors"][0])
    assert set(result["diagnosis_counts"]) <= {"confirmed_structural_gap", "mte2_granule_amplification", "tiling_wave_step", "fusion_boundary", "collective_skew"}
    summary = z.render_markdown(result)
    assert all(s in summary for s in ("Zero-shot piecewise validation baseline", "Coverage by level", "Physical diagnoses", "forbidden lookup imported: False"))

def test_historical_inventory_covers_profiles_fixtures_and_registry():
    entries = z.load_historical_inventory(); kinds = {item["kind"] for item in entries}
    assert {"profile_source", "fixture", "case_registry"}.issubset(kinds) and all(isinstance(item["exists"], bool) for item in entries)
    assert any(item["kind"] == "fixture" and item["exists"] for item in entries)

def test_missing_root_is_an_empty_corpus(tmp_path):
    assert z.discover_workstream(tmp_path / "absent") == []
    result = z.run_validation(roots=(tmp_path / "absent",), include_historical=False)
    assert result["coverage"]["cells"] == 0 and result["levels"] == []

def test_kv_bf16_is_applied_after_parse_and_ep_cohort_conserves_tokens():
    case, label, notes = z.resolve_model("dsv41_kvbf16")
    assert notes == ()
    spec = z.CellSpec("kv", "unit", "decode", case, label, 128, 4, 8, 1, 8, 8, 1, notes=("kv_bf16",))
    assert "quant" not in z._raw_case(spec).get("model", {}) and "kv_bf16" in spec.notes
    from mindie_sim.prediction.structure import parse_case
    parsed = parse_case(z._raw_case(spec))
    fp8 = replace(parsed.model, kv_dtype="fp8_e4m3", quant=replace(parsed.model.quant, kv_dtype="fp8_e4m3"))
    forced, _notes = z._model_for_instantiation(fp8, spec)
    assert forced.kv_dtype == "bf16" and forced.quant.kv_dtype == "bf16"
    kept, _notes = z._model_for_instantiation(fp8, replace(spec, notes=()))
    assert kept.kv_dtype == "fp8_e4m3" and kept.quant.kv_dtype == "fp8_e4m3"
    assert z._ep_batch(spec) == 4 and z._local_batch(spec) == 1 and z._ep_batch(replace(spec, concurrency=7, dp=8, ep=4)) == 4
    assert z._geometry(spec, "decode", batch=z._ep_batch(spec)).batch == 4
    idle = replace(spec, concurrency=1)
    cell = z.MeasuredCell(idle, (), z.KernelTrace(1000.0, {"collective": 800.0, "moe_grouped": 200.0}, {}), None, 1.0, 1.0, 1, True)
    prediction = z.Prediction("kv", label, 1, {"attention": 3.0, "indexer": 1.0, "rope": 0.5, "kv_cache": 0.5, "collective": 2.0, "moe_grouped": 4.0}, {"attention": 5.0, "moe": 6.0}, 10.0, None, None, ())
    comparisons = z.compare_cell(cell, prediction)
    l1 = {item.target: item.predicted_ms for item in comparisons if item.level == "L1"}
    l2 = {item.target: item.predicted_ms for item in comparisons if item.level == "L2"}
    assert set(l1) == {"collective"} and l1["collective"] == pytest.approx(2.0) and l2 == {}
    assert prediction.per_layer["attention"] == pytest.approx(3.0) and prediction.per_layer["collective"] == pytest.approx(2.0) and prediction.subgraphs["moe"] == pytest.approx(6.0)
    busy = z.MeasuredCell(idle, (), z.KernelTrace(1000.0, {"attention": 10.0, "collective": 10.0}, {}), None, 1.0, 1.0, 1, True)
    assert next(item.predicted_ms for item in z.compare_cell(busy, prediction) if item.target == "attention" and item.level == "L1") == pytest.approx(3.0)

def test_union_duration_cache_normalization_and_blind_order(tmp_path):
    csv_path = tmp_path / "overlap.csv"
    csv_path.write_text("Name,Type,Start Time(us),Duration(us)\nMatMulV3_1,MatMulV3,100.0,50.0\nMatMulV3_2,MatMulV3,120.0,50.0\n_prepare_dflash_inputs,_prepare_dflash_inputs,150.0,25.0\nBad,MatMulV3,200.0,nan\n")
    trace = z.load_kernel_trace(csv_path)
    assert trace.duration_us == pytest.approx(125.0) and trace.union_duration_us == pytest.approx(75.0)
    assert trace.by_class["gemm"] == pytest.approx(100.0) and trace.by_class["unresolved"] == pytest.approx(25.0)
    assert z.classify_kernel("UnknownProbe", "UnknownProbe", allow_unresolved=True) == "unresolved"
    z._classify_cached.cache_clear()
    assert z.classify_kernel("MatMulV3_101", "MatMulV3") == z.classify_kernel("MatMulV3_202", "MatMulV3") == "gemm" and z._classify_cached.cache_info().currsize == 1
    s1 = z.CellSpec("c", "a5", "decode", MODEL_CASE, "Qwen3.8-27B", 128, 1, 8, 4, 1, 1, 1)
    assert s1.prediction_key() != replace(s1, dataset="a3").prediction_key()
    for tag in ("gemma4_26b", "gemma4_31b", "minimax_m31", "minimax", "qwen38_flash", "step5"):
        mc, ml, notes = z.resolve_model(tag)
        assert mc is not None and "structural_proxy" not in notes and z.predict_cell(z.CellSpec(tag, "a5", "decode", mc, ml, 512, 4, 8, 4, 1, 4, 1)).body_ms > 0.0

def test_l1_l3_comparisons_invariant_under_ttft_tpot_perturbation(tmp_path):
    dc_rows = (("MlaPrologV3", "MlaPrologV3", 60000.0), ("_categorical_sample_kernel", "x", 10.0)) + tuple(it for _ in range(3) for it in (("MlaPrologV3", "MlaPrologV3", 20000.0), ("AddRmsNormBias", "AddRmsNormBias", 5000.0), ("_prepare_dflash_inputs", "x", 5.0), ("_categorical_sample_kernel", "x", 10.0)))
    dc_csv, pf_csv = tmp_path / "dc.csv", tmp_path / "pf.csv"
    write_kernel_csv(dc_csv, rows=dc_rows); write_kernel_csv(pf_csv, rows=KERNEL_ROWS)
    for phase, csv_p in (("decode", dc_csv), ("prefill", pf_csv)):
        spec = z.CellSpec(f"inv_{phase}", "unit", phase, MODEL_CASE, "Qwen3.8-27B", 1024, 2, 4, 4, 1, 1, 1)
        pred = z.predict_cell(spec)
        c1 = z.attach_trace(z.MeasuredCell(spec, (csv_p,), None, 120.0, 15.0, None, 4 if phase == "decode" else 1, True))
        c2 = z.attach_trace(z.MeasuredCell(spec, (csv_p,), None, 9999.0, 888.0, None, 4 if phase == "decode" else 1, True))
        assert (c1.decode_steps, c1.step_trace_ms, c1.trace_quality) == (c2.decode_steps, c2.step_trace_ms, c2.trace_quality)
        l13_a = [item for item in z.compare_cell(c1, pred) if item.level in {"L1", "L2", "L3"}]
        l13_b = [item for item in z.compare_cell(c2, pred) if item.level in {"L1", "L2", "L3"}]
        assert l13_a and l13_a == l13_b
    jsonl = tmp_path / "bench.jsonl"
    jsonl.write_text(json.dumps(z.cell_to_dict(z.attach_trace(z.MeasuredCell(z.CellSpec("inv_dc", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 2, 4, 4, 1, 1, 1), (dc_csv,), None, 120.0, 15.0, None, 4, True)))) + "\n", encoding="utf-8")
    res = z.run_validation(benchmark_jsonl=jsonl, include_historical=False)
    assert "_prepare_dflash_inputs" in res["unresolved_kernels"] and res["agent_decisions"] and z.main(["--benchmark-jsonl", str(jsonl), "--no-historical", "--json"]) == 1


def test_public_rows_expose_native_call_occurrence_and_exact_coverage():
    spec = z.CellSpec("native", "unit", "decode", MODEL_CASE, "Qwen3.8-27B",
                      128, 2, 8, 4, 1, 1, 1, (1, 2, 4), 2)
    prediction = z.predict_cell(spec)
    bound = [row for row in prediction.rows if row.native_call]
    assert bound
    row = bound[0]
    assert row.phase == "decode"
    assert row.native_call["call_id"]
    assert row.native_occurrence["call_id"] == row.native_call["call_id"]
    assert row.native_occurrence["layer"] >= 0
    assert row.native_occurrence["repeat"] >= 1
    assert row.native_call["typed"]["signature_hash"]
    assert row.native_occurrence["typed"]
    unbound = [row for row in prediction.rows if not row.native_call]
    assert unbound and all(row.native_occurrence["status"] == "unbound" for row in unbound)
    coverage = z._native_forecast((prediction,))["overall"]
    emitted = sum(row.count for row in prediction.rows
                  if (row.native_occurrence or {}).get("membership") != "consumed_by_selected_fusion")
    attribution = sum(row.count for row in prediction.rows
                      if (row.native_occurrence or {}).get("membership") == "consumed_by_selected_fusion")
    assert coverage["denominator"]["emitted_operators"] == emitted
    assert coverage["totals"]["attribution_occurrences"] == attribution
    assert (coverage["totals"]["bound_occurrences"]
            + coverage["totals"]["unresolved_occurrences"]) == emitted
    assert coverage["totals"]["unique_calls"] == len(coverage["unique_calls"])
    assert 0 < coverage["totals"]["unique_calls"] <= len({
        row.native_call["call_id"] for row in bound})


def test_public_qwen36_prefill_gdn_prepare_descriptors_and_owner():
    spec = z.CellSpec("gdn", "unit", "prefill", QWEN36_CASE, "Qwen3.6-27B",
                      4096, 1, 1, 2, 4, 1, 1)
    prediction = z.predict_cell(spec)
    rows = {row.name: row for row in prediction.rows}
    prepare, delta = rows["prepare"], rows["gated_delta"]
    assert prepare.count == delta.count == 48
    assert prepare.native_call["call_id"] == delta.native_call["call_id"]
    assert prepare.native_occurrence["charge"] == "member"
    assert delta.native_occurrence["charge"] == "call"
    call = delta.native_call
    assert call["api"]["aclnn_symbol"] == "aclnnChunkGatedDeltaRuleFwd"
    assert call["evidence"]["aclnn_symbol"] == "source_declared"
    assert "aclnn_symbol_unresolved" not in call["unresolved"]
    assert call["typed"]["shapes"]["q"] == [8, 128]
    occurrence = delta.native_occurrence
    assert occurrence["typed"]["shapes"]["q"] == [1, 4096, 8, 128]
    assert occurrence["typed"]["shapes"]["v"] == [1, 4096, 24, 128]
    assert occurrence["typed"]["shapes"]["o"] == [1, 4096, 24, 128]
    prepared = occurrence["prepare"]
    assert prepared["arguments"]["cu_seqlens"] == [0, 4096]
    assert prepared["arguments"]["chunks"] == 64
    assert prepared["named_arguments"]["layout"] == "BSND"
    assert prepared["named_arguments"]["scale"] == 128 ** -0.5
    assert prepared["descriptors"]["initial_state"]["shape"] == [1, 24, 128, 128]
    assert prepared["descriptors"]["o"]["role"] == "output"
    assert set(prepared["outputs"]) == {"o", "final_state", "g_cumsum", "A",
                                       "q_hat", "k_hat", "q_rstd", "k_rstd"}
    assert set(prepared["disabled_outputs"]) == {"beta_eff", "h"}
    assert prepared["output_slots"]["g_cumsum"]["acl_slot"] == "gCumsumOutOptional"
    assert prepared["descriptors"]["A"]["shape"] == [1, 24, 4096, 64]
    assert prepared["descriptors"]["q_rstd"]["shape"] == [1, 8, 4096]
    assert sum(item["count"] for item in prepared["physical_presentations"]) == 7
    assert prepared["allocation"] == "not_performed"
    assert occurrence["prepare_args"]["shapes"]["q"] == [1, 4096, 8, 128]
    independent = {row.name: row for row in z.predict_cell(
        replace(spec, prompt_tokens=2048)).rows}
    independent_delta = independent["gated_delta"]
    assert independent_delta.native_call["call_id"] == call["call_id"]
    assert independent_delta.native_occurrence["typed"]["shapes"]["q"] == [1, 2048, 8, 128]
    assert independent_delta.native_occurrence["prepare"]["arguments"]["cu_seqlens"] == [0, 2048]
    batched = {row.name: row for row in z.predict_cell(
        replace(spec, concurrency=8)).rows}
    batched_delta = batched["gated_delta"]
    assert batched_delta.native_call["call_id"] == call["call_id"]
    assert batched_delta.native_occurrence["prepare"]["arguments"]["cu_seqlens"] == [0, 4096, 8192]
    assert batched_delta.native_occurrence["prepare"]["descriptors"]["initial_state"]["shape"] == [2, 24, 128, 128]
    decode = {row.name: row for row in z.predict_cell(
        replace(spec, phase="decode", prompt_tokens=1024, max_tokens=8)).rows}
    assert decode["gated_delta"].native_call["api"]["entry"] == "RecurrentGatedDeltaRule"
    assert "prepare" not in decode["gated_delta"].native_occurrence


def test_public_r35_qbmm_o_projection_uses_authentic_wrapper():
    import os
    path = Path(os.environ.get(
        "MINDIE_ZERO_SHOT_JSONL",
        "/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl"))
    if not path.is_file():
        pytest.skip("original 731 jsonl unavailable")
    cell = next(c for c in z.load_benchmark_jsonl(path)
                if c.spec.cell_id == "glm53w8a8c8_dp32tp1ep32_on_prefill_1024_c1")
    predictions = {m: z.predict_cell(replace(cell.spec, prompt_tokens=m))
                   for m in (1024, 1)}
    rows = {m: {row.name: row for row in pred.rows}["o_projection"]
            for m, pred in predictions.items()}
    row = rows[1024]
    call = row.native_call
    occurrence = row.native_occurrence
    prepared = occurrence["prepare"]
    assert call["api"]["entry"] == "torch_npu.npu_quant_matmul"
    assert call["api"]["version"] == "r35/5461a1a8"
    assert call["source"]["sha256"] == "51ece928e77420a7f6600e2d87c46e9397a5140b6acee324aa75fdb97266d009"
    assert call["source"]["revision"] == "r35/5461a1a8"
    assert call["kernels"][0]["source_sha256"] == "eb1c788e39b7a02f0694450e917a3771c7e65d7d8fb9ea2e03f78c4a5313c456"
    assert occurrence["charge"] == "call"
    assert call["typed"]["shapes"]["weight"] == [16384, 6144]
    assert call["typed"]["shapes"]["weight_scale"] == [256, 6144, 2]
    assert prepared["source_lines"]["qmm_call"] == [150, 160]
    assert prepared["source_lines"]["scale_allocation"] == [89, 89]
    assert prepared["deployment"]["selected_by"].startswith("quant.linear_method=mx_fp8")
    assert prepared["selected_host_variant"] == "apply"
    assert prepared["rejected_host_variants"] == ["apply_single_group_gmm:GroupedMatmulV3"]
    assert prepared["shapes"]["x"] == [1024, 16384]
    assert prepared["shapes"]["output"] == [1024, 6144]
    assert prepared["shapes"]["pertoken_scale"] == [1024, 256, 2]
    assert prepared["descriptors"]["weight_nz"]["shape"] == [192, 1024, 16, 32]
    assert prepared["descriptors"]["weight_scale"]["allocation_shape"] == [6144, 512]
    assert prepared["descriptors"]["weight_scale"]["dtype"] == "uint8"
    assert prepared["descriptors"]["weight_scale"]["interpret_dtype"] == "fp8_e8m0"
    assert prepared["deployment"]["image_id"].startswith("5461a1a8")
    assert prepared["match"]["source_version"] == "r35/5461a1a8"
    assert rows[1].native_call["call_id"] == call["call_id"]
    assert rows[1].native_occurrence["typed"]["shapes"]["x"] == [1, 16384]
    assert rows[1].native_occurrence["prepare"]["shapes"]["output"] == [1, 6144]
def test_normal_r64_qbmm_o_projection_uses_deployment_image_id():
    import copy
    import os
    from mindie_sim.prediction.piecewise import (
        ImplementationPolicy, OperatorPiecewiseCompiler, PipeSupply,
        RequestGeometry, WorkloadGeometry,
    )
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.prediction.subgraphs.instantiate import FeatureConfig, instantiate_model
    path = Path(os.environ.get(
        "MINDIE_ZERO_SHOT_JSONL",
        "/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl"))
    if not path.is_file():
        pytest.skip("original 731 jsonl unavailable")
    cell = next(c for c in z.load_benchmark_jsonl(path)
                if c.spec.cell_id == "glm53w8a8c8_dp32tp1ep32_on_prefill_1024_c1")
    raw = copy.deepcopy(z._raw_case(cell.spec))
    meta = dict(raw["runtime"]["metadata"])
    meta["image_id"] = "sha256:8d422528ac20a8babcbbf93762cde3b47d4db6c5f7ab777f4f1f65b32b89ab3e"
    meta.pop("mx_quant_source_revision", None)
    raw["runtime"]["metadata"] = meta
    case = parse_case(raw)
    features = FeatureConfig.from_runtime(case.runtime, case.model).project(
        tp=cell.spec.tp, dp=cell.spec.dp, ep=cell.spec.ep, pp=cell.spec.pp,
        cores=64, graph_buckets=cell.spec.graph_buckets)
    instantiated = instantiate_model(case.model, features)
    instance = next(item for layer in instantiated.layers for item in layer.subgraphs
                    if item.kind == "A1" and any(op.name == "o_projection" for op in item.operators))
    compiler = OperatorPiecewiseCompiler(
        PipeSupply.from_hardware(case.machine, dtype="bf16"),
        ImplementationPolicy(cores=64))
    compiled = compiler.compile(instance, feature_metadata=features.metadata)
    evaluated = {}
    for m in (1024, 2048, 2):
        geometry = WorkloadGeometry((RequestGeometry(m, m, phase="prefill"),),
                                    phase="prefill", cohort_batch=1, local_batch=1)
        evaluated[m] = {cost.name: cost for cost in compiled.evaluate(geometry).operators}["o_projection"]
    row = evaluated[1024]
    call = row.native_call
    prepared = row.native_occurrence["prepare"]
    assert row.native_occurrence["charge"] == "call"
    assert call["api"]["entry"] == "torch_npu.npu_quant_matmul"
    assert call["api"]["version"] == "r64/8d422528"
    assert call["source"]["sha256"] == "38de2275cf33ced653b8398e98a07f483489dc8e7353b2b3c238a5ff00782f79"
    assert call["typed"]["shapes"]["weight"] == [16384, 6144]
    assert call["typed"]["shapes"]["weight_scale"] == [256, 6144, 2]
    assert prepared["shapes"]["x"] == [1024, 16384]
    assert prepared["shapes"]["output"] == [1024, 6144]
    assert prepared["shapes"]["pertoken_scale"] == [1024, 256, 2]
    assert prepared["descriptors"]["weight_nz"]["shape"] == [192, 1024, 16, 32]
    assert prepared["descriptors"]["weight_scale"]["dtype"] == "uint8"
    assert prepared["descriptors"]["weight_scale"]["interpret_dtype"] == "fp8_e8m0"
    assert prepared["descriptors"]["weight_scale"]["allocation_shape"] == [6144, 512]
    assert prepared["scale_storage"]["weight_scale"]["allocation_dtype"] == "uint8"
    assert prepared["weight_storage"]["allocation_shape"] == [6144, 16384]
    assert prepared["deployment"]["image_id"].startswith("8d422528")
    assert prepared["match"]["k"] == 16384 and prepared["match"]["n"] == 6144
    for m in (2048, 2):
        item = evaluated[m]
        assert item.native_call["call_id"] == call["call_id"]
        assert item.native_occurrence["typed"]["shapes"]["x"] == [m, 16384]
        assert item.native_occurrence["typed"]["shapes"]["output"] == [m, 6144]
        assert item.native_occurrence["typed"]["shapes"]["pertoken_scale"] == [m, 256, 2]


def _source_rebind_fixture(tmp_path, *, prior_key="deepseek-v4.1-flash", kv=None, mqsmla=True):
    tmp_path.mkdir(parents=True, exist_ok=True)
    model = {"model": {"name": "deepseek-v4.1-flash", "catalog_key": prior_key,
                       "metadata": {"cache_representations": {
                           "window": {"dtype": "fp8_e4m3", "group_size": 32, "scale_dtype": "bf16"},
                           "compressed_kv": {"dtype": "fp4_e2m1", "group_size": 16, "scale_dtype": "bf16"}},
                           "unmodeled_features": ["native mixed FP8/FP4 KV attention cache and compute path"],
                           "degraded_submodules": ["mixed_quant_sparse_flash_mla"]}},
             "machine": {}, "runtime": {"tp": 1, "dp": 2, "ep": 2, "kernels": {"lowerings": {
                 **({"mqsmla_attention": {"implementation": "cannbot_mixed_quant_sparse_flash_mla"}} if mqsmla else {}),
                 "native_fusion": "declared_native_fusion"}}},
             "workload": {"requests": [{"id": "r", "prompt_tokens": 1, "output_tokens": 1}]}}
    case = tmp_path / "case.json"; case.write_text(json.dumps(model))
    source = tmp_path / "weights" / "deepseek-v4.1-flash" / "config.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps({"model_type": "deepseek_v41", "architectures": ["DeepseekV41ForCausalLM"]}))
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    campaign = tmp_path / "out" / "campaign"; campaign.mkdir(parents=True)
    (tmp_path / "cases").mkdir(); (tmp_path / "cases" / "campaign.json").write_text(
        json.dumps({"kv_cache_dtype": kv} if kv else {}))
    spec = z.CellSpec("campaign_dc", "out", "decode", case, "DeepSeek-V4.1-Flash",
                      1024, 2, 8, 1, 2, 2, 1, source_config=source,
                      source_config_sha256=sha, source_deploy_sha256=sha, source_case_dir=campaign)
    return spec


def test_source_rebind_keeps_coupled_cache_declarations_and_kv_override(tmp_path):
    compatible = z._raw_case(_source_rebind_fixture(tmp_path))
    assert compatible["model"]["metadata"]["cache_representations"]["window"]["dtype"] == "fp8_e4m3"
    assert "mqsmla_attention" in compatible["runtime"]["kernels"]["lowerings"]

    requested = z._raw_case(_source_rebind_fixture(tmp_path / "requested", kv="bfloat16"))
    assert requested["model"]["metadata"]["cache_representations"]["window"]["dtype"] == "bf16"
    assert "mqsmla_attention" not in requested["runtime"]["kernels"]["lowerings"]
    declaration = requested["runtime"]["metadata"]["source_cache_declaration"]
    assert declaration["requested_kv_cache_dtype"] == "bfloat16"
    assert declaration["requested_override_applied"] is True

    plain = z._raw_case(_source_rebind_fixture(tmp_path / "plain", kv="bfloat16", mqsmla=False))
    assert plain["model"]["kv_dtype"] == "bf16"
    assert {value["dtype"] for value in plain["model"]["metadata"]["cache_representations"].values()} == {"bf16"}
    assert "mqsmla_attention" not in plain["runtime"]["kernels"]["lowerings"]
    assert plain["runtime"]["metadata"]["source_cache_declaration"]["basis"] == "requested_kv_cache_dtype_applied_without_packed_capability"

    fp8 = z._raw_case(_source_rebind_fixture(tmp_path / "fp8", kv="fp8", mqsmla=False))
    assert (fp8["model"]["metadata"]["cache_representations"]["window"]["dtype"] == "fp8_e4m3"
            and fp8["model"]["metadata"]["cache_representations"]["compressed_kv"]["dtype"] == "fp4_e2m1")

    foreign = z._raw_case(_source_rebind_fixture(tmp_path / "foreign", prior_key="qwen3.8-27b"))
    assert "metadata" not in foreign["model"]
    assert "mqsmla_attention" not in foreign["runtime"]["kernels"]["lowerings"]
    assert foreign["runtime"]["metadata"]["source_cache_declaration"]["basis"].startswith("incompatible_source")


def test_public_consumer_uses_declared_family_role_and_measured_l2_scope():
    base = (z.OperatorRow("router_histogram", "F1", "moe_router", "moe", 99.0, 1,
                          (), "cube", "private", 0, None),)
    def item(family, elapsed, *, role=None, native=None, recipe=None, program="OperatorPlan"):
        data = {"family": family, "elapsed_ms": elapsed, "operator_events": 1,
                "stage": 0, "replica": 0, "layer": 0, "phase": "decode",
                "op_id": f"op.{family}", "recipe": recipe or family, "program": program}
        if role: data["fusion_role"] = role
        if native: data["native_implementation"] = {"native_kind": native}
        return data
    projection = {"operators": {
        "s0:s0.l0.dispatch": item("mc2_protocol", 0.5),
        "s0:s0.l0.router": item("router", 0.2, program="SteadyMatmul"),
        "s0:s0.l0.index_topk": item("topk", 0.1, recipe="index_topk"),
        "s0:s0.l0.router_topk": item("topk", 0.05, recipe="router_topk"),
        "s0:s0.l0.grouped_output_a.quantize": item("quantize", 0.1),
        "s0:s0.l0.compress_norm": item("rmsnorm", 0.3),
        "s0:s0.l0.join": item("elementwise", 0.2, recipe="expert_add"),
        "s0:s0.l0.muls_add": item("elementwise", 0.05, recipe="muls_add"),
        "s0:s0.l0.grouped_gate_up_situ_quant.native": item("native_fusion", 0.3, role="grouped_gate_up_situ_quant"),
        "s0:s0.l0.shared.situ_quant.native": item("native_fusion", 0.1, role="situ_quant"),
        "s0:s0.l0.latent_down": item("projection", 0.3, recipe="latent_projection", native="GroupedMatmul"),
        "s0:s0.l0.latent_up": item("projection", 0.2, recipe="latent_projection", native="GroupedMatmul"),
        "s0:s0.l0.linear_decay_a": item("gemm", 0.1, recipe="linear_decay_a"),
        "s0:s0.l0.attention.sp_gather": item("allgather", 0.2, recipe="ring_allgather"),
        "s0:s0.l0.shared.sp_scatter": item("reduce_scatter", 0.15, recipe="ring_reduce_scatter"),
        "s0:s0.l0.recurrent_scan0": item("recurrent_scan", 0.25, recipe="recurrent_scan0"),
        "s0:s0.l0.attention.hc_pre.native": item("native_fusion", 0.4, role="hc_pre", native="HcPre"),
        "s0:s0.l0.logits": item("logits", 0.6),
        "s0:s0.l0.q_a": item("gemm", 0.7),
    }, "step": {"start_ms": 0.0, "device_end_ms": 3.0, "end_ms": 4.0}}
    out = z._public_consume(projection, base, layers=1, basis="expected_index_mod_dp")
    rows = {row.name: row for row in out["rows"]}
    assert rows["router"].mechanism == "gemm" and "source_owner" not in rows["router"].native_occurrence
    assert rows["index_topk"].mechanism == "indexer" and rows["index_topk"].subgraph == "attention"
    assert rows["router_topk"].mechanism == "moe_router" and rows["router_topk"].subgraph == "moe"
    assert rows["grouped_output_a.quantize"].mechanism == "elementwise_quant"
    assert rows["compress_norm"].mechanism == "norm_residual"
    assert rows["join"].mechanism == "norm_residual"
    assert rows["muls_add"].mechanism == "elementwise_quant"
    assert rows["grouped_gate_up_situ_quant.native"].mechanism == "moe_grouped"
    assert rows["shared.situ_quant.native"].mechanism == "unclassified"
    assert rows["latent_down"].mechanism == "moe_grouped" and rows["latent_down"].subgraph == "moe"
    assert rows["latent_down"].kind != "F3" and rows["latent_down"].native_occurrence["source_role"] == "nonrouted_latent_moe_one_group"
    assert rows["latent_up"].mechanism == "moe_grouped" and rows["latent_up"].native_occurrence["routed_expert"] is False
    assert rows["linear_decay_a"].mechanism == "gemm"
    assert rows["attention.sp_gather"].mechanism == "collective"
    assert rows["shared.sp_scatter"].mechanism == "collective"
    assert rows["recurrent_scan0"].mechanism == "gdn_kda"
    assert rows["attention.hc_pre.native"].mechanism == "hyperconnection"
    assert rows["logits"].mechanism == "gemm" and rows["logits"].subgraph == ""
    assert rows["q_a"].mechanism == "gemm" and rows["q_a"].subgraph == ""
    assert out["subgraphs"] == pytest.approx({"moe": 1.35, "attention": 0.35, "norm_residual": 0.5, "hyperconnection": 0.4})
    assert sum(out["per_layer"].values()) == pytest.approx(4.8)
    assert out["body_ms"] == pytest.approx(3.0) and out["step_ms"] == pytest.approx(4.0)
    assert all(row.native_occurrence["basis"] == "expected_index_mod_dp" for row in out["rows"])
