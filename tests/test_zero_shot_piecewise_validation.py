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
import json
import math
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
        assert len(lines) < 800, (path.name, len(lines))
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
    assert first.rows and all(row.guard_text and row.dominant_pipe for row in first.rows)
    assert any(row.segment >= 0 for row in first.rows)
    assert "index_scale_dtype_none_priced_as_1_byte_e8m0" in first.notes
    assert not any(note.startswith("V0:") for note in first.notes)
    assert not any(row.kind == "V0" for row in first.rows)

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
    assert small_o0 == pytest.approx(large_o0)
    assert large_o0 < 20.0

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
    assert {"decode_step_trace", "decode_step_tpot"}.isdisjoint({item.target for item in z.compare_cell(blob, pred)})
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
    assert window.decode_steps == 1 and window.trace.by_name.get("HcPre", 0.0) == 0.0
    assert window.trace.segments == ()
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

def test_glm53_and_glm53_flash_resolve_to_distinct_model_structures():
    flash_case, flash_label, _ = z.resolve_model("glm53flash_tp8_c4")
    glm53_case, glm53_label, _ = z.resolve_model("glm53_dp16tp1ep16")
    glm51_case, glm51_label, _ = z.resolve_model("glm51_dp16tp1ep16")
    assert flash_label == "GLM-5.3-Flash"
    assert glm53_label == "GLM-5.3/W8A8-MXFP8"
    assert glm51_label == "GLM-5.1/W4A4C8"
    base = z.CellSpec("x", "u", "decode", flash_case, flash_label, 1024, 1, 8, 8, 1, 1, 1)
    assert z._case_layers(base) == 45
    assert z._case_layers(replace(base, model_case=glm53_case, model_label=glm53_label)) == 78
    assert z._case_layers(replace(base, model_case=glm51_case, model_label=glm51_label)) == 78

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
    assert {"gemm", "attention", "decode_step_trace", "decode_step_tpot",
            "prefill_step_ttft"}.issubset(targets)
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
                   "Decode 单步耗时", "Prefill 单步耗时",
                   "Unmodeled Operation / Boundary Mismatch (未建模算子或边界偏差)",
                   "Fusion Boundary Mismatch (算子融合边界偏差)",
                   "Collective Communication Skew / Latency (集合通信慢卡倾斜或握手延迟)",
                   "Tile / Core Wave Quantization (分块与核波次量化效应)",
                   "Memory Alignment Amplification (访存粒度对齐放大)"):
        assert marker in summary, marker

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
    case, label, _ = z.resolve_model("dsv41_kvbf16")
    spec = z.CellSpec("kv", "unit", "decode", case, label, 128, 4, 8, 1, 8, 8, 1)
    assert "quant" not in z._raw_case(spec).get("model", {})
    from mindie_sim.prediction.structure import parse_case
    parsed = parse_case(z._raw_case(spec))
    fp8 = replace(parsed.model, kv_dtype="fp8_e4m3", quant=replace(parsed.model.quant, kv_dtype="fp8_e4m3"))
    forced, _notes = z._model_for_instantiation(fp8, spec)
    assert forced.kv_dtype == "bf16" and forced.quant.kv_dtype == "bf16"
    kept, _notes = z._model_for_instantiation(fp8, replace(spec, model_label="DeepSeek-V4.1-Flash"))
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
    assert z.predict_cell(replace(s1, cell_id="qwen38_pd_64k_p8k_c8", prompt_tokens=65536, concurrency=8)).ttft_ms < 0.35 * z.predict_cell(replace(s1, cell_id="qwen38_dc_64k_p8k_c8", prompt_tokens=65536, concurrency=8)).ttft_ms
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
