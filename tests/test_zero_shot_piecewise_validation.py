"""Contract and behaviour tests for the zero-shot piecewise validation lane.

[Role]
  Verify the measurement-blind four-level validator, streamed kernel
  aggregation, physical diagnosis taxonomy, observed-boundary bindings, and
  public consumer projections over synthetic A5 fleet cells.

[Invariants]
  * Tests never feed a measured latency into ``predict_cell``.
  * Trace step recovery and DP local-batch geometry stay on the measured side.
  * The synthetic workstream resolves repository structural cases while owning
    all measured JSON/CSV inputs inside ``tmp_path``.

[Timeouts & Locks]
  Bounded local files and deterministic structural predictions. No network,
  device, subprocess, sleep or lock is used.

[Side-Effect Policy]
  All generated inputs live under pytest ``tmp_path``; repository files are
  read-only and the validator writes only to captured stdout in tests.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip("mindie_sim")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
import zero_shot_piecewise_validation as z  # noqa: E402

MODEL_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen38_highconc_c4.json"
QWEN36_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen36_highconc_c4.json"
GLM51_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_glm51_mxfp4_dp16tp1ep16_pf1k.json"
V41_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json"


@pytest.fixture(scope="module")
def compact_cases(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    base_dir = tmp_path_factory.mktemp("zspv_cases")
    out: dict[str, Path] = {}
    for key, src in (
        ("qwen38", MODEL_CASE),
        ("qwen36", QWEN36_CASE),
        ("glm51", GLM51_CASE),
        ("v41", V41_CASE),
    ):
        n = 12 if key == "glm51" else (8 if key == "v41" else 4)
        doc = json.loads(src.read_text(encoding="utf-8"))
        doc["model"]["layers"] = n
        if "body_layers" in doc["model"]:
            doc["model"]["body_layers"] = n
        if "layer_plans" in doc["model"]:
            doc["model"]["layer_plans"] = list(doc["model"]["layer_plans"])[:n]
        tc = (doc["model"].get("hf_config") or {}).get("text_config")
        if key == "v41" and isinstance(tc, dict):
            tc["num_hidden_layers"] = n
            if "compress_ratios" in tc:
                tc["compress_ratios"] = list(tc["compress_ratios"])[:n] + [0, 0, 0]
            tc["kv_source_layer_ids"] = [2]
            tc["index_source_layer_ids"] = [2]
            tc["candidate_source_layer_id"] = 2
            tc["engram_layer_ids"] = [1]
            if "engram_num_embeddings" in tc:
                tc["engram_num_embeddings"] = list(tc["engram_num_embeddings"])[:1]
            tc["dspark_target_layer_ids"] = [5, 6, 7]
        dst = base_dir / f"compact_{key}.json"
        dst.write_text(json.dumps(doc), encoding="utf-8")
        out[key] = dst
    return out


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


def make_corpus(tmp_path: Path, *, model_case: Path | None = None):
    root = tmp_path / "out"
    case_root = root / "case"
    write_measured(
        case_root / "measured" / "case_dc_1k_c1.json",
        model_case=str(model_case or MODEL_CASE),
    )
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
# Classification and streamed loading


@pytest.mark.parametrize(("name", "kind", "expected"), (
    ("aclnnMatmul_MatMulV3Common", "MatMulV3", "gemm"),
    ("KvQuantSparseFlashAttention", "KvQuantSparseFlashAttention", "attention"),
    ("QuantLightningIndexer", "QuantLightningIndexer", "indexer"),
    ("aclnnGroupedMatmulV4_GroupedMatmul", "GroupedMatmul", "moe_grouped"),
    ("MoeDistributeDispatchV3", "MoeDistributeDispatchV3", "collective"),
    ("aclnnRecurrentKda_RecurrentKda", "RecurrentKda", "kda_linear_attn"),
    ("aclnnRecurrentGatedDeltaRule_RecurrentGatedDeltaRule", "RecurrentGatedDeltaRule", "gdn_linear_attn"),
    ("_kda_state_copy_kernel", "", "kda_linear_attn"),
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
    ("CausalConv1d", "CausalConv1d", "gdn_linear_attn"),
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


def test_structural_prediction_exposes_guards_pipes_and_all_levels(compact_cases):
    spec = z.CellSpec("qwen38", "unit", "decode", compact_cases["qwen38"], "Qwen3.8-27B",
                      128, 2, 1, 4, 1, 1, 1, (1, 2, 4, 8), 2)
    first = z.predict_cell(spec)
    second = z.predict_cell(spec)
    assert first == second
    assert first.layers == 4
    for mechanism in ("gemm", "attention", "gdn_linear_attn"):
        assert first.per_layer.get(mechanism, 0.0) > 0
    assert first.body_ms > 0 and first.ttft_ms and first.ttft_ms > first.body_ms
    assert first.rows and all(row.guard_text and (row.dominant_pipe or row.name == "prepare") for row in first.rows)
    assert any(row.segment >= 0 for row in first.rows)
    assert "index_scale_dtype_none_priced_as_1_byte_e8m0" in first.notes
    assert not any(note.startswith("V0:") for note in first.notes)
    assert not any(row.kind == "V0" for row in first.rows)


def test_selected_fusions_publish_one_parent_and_uncharged_members_and_row_for_owner(compact_cases):
    spec = z.CellSpec("glm51_dp16tp1ep16_pf_1k_c2", "unit", "prefill", compact_cases["glm51"],
                      "GLM-5.1/W4A4C8", 256, 2, 1, 1, 2, 2, 1, (1, 2, 4, 8, 16, 32, 64))
    pred = z.predict_cell(spec)
    owners = [row for row in pred.rows
              if (row.native_occurrence or {}).get("membership") == "selected_fused_owner"]
    assert len({row.name for row in owners}) >= 2
    assert all((row.native_occurrence or {}).get("charge") == "call" for row in owners)
    children = [row for row in pred.rows
                if (row.native_occurrence or {}).get("membership") == "consumed_by_selected_fusion"]
    assert children and all((row.native_occurrence or {}).get("charge") == "none" for row in children)
    assert all(row.native_occurrence.get("timing_owner") in {x.name for x in owners} for row in children)
    row = z._row_for(pred.rows, "gemm")
    assert row is not None
    assert (row.native_occurrence or {}).get("charge") != "none"


def test_dp_cohort_is_split_into_one_local_batch_per_replica(compact_cases):
    spec = z.CellSpec("dp", "unit", "decode", compact_cases["qwen38"], "Qwen3.8-27B",
                      4096, 4, 1, 4, 4, 1, 1, (1, 2, 4, 8), 4, synthetic_layers=2)
    assert z._local_batch(spec) == 1
    assert z._local_batch(replace(spec, concurrency=10, dp=4)) == 3
    assert z._local_batch(replace(spec, concurrency=7, dp=8)) == 1
    assert z._geometry(spec, "decode").batch == 1
    assert z._geometry(replace(spec, phase="prefill"), "prefill").batch == 1
    clustered = z.predict_cell(replace(spec, dp=1))
    per_replica = z.predict_cell(spec)
    assert per_replica.per_layer["attention"] < clustered.per_layer["attention"]


def test_observed_block_table_batch_wins_over_the_declared_ceiling(compact_cases):
    spec = z.CellSpec("dp_obs", "unit", "decode", compact_cases["qwen38"], "Qwen3.8-27B",
                      256, 8, 1, 4, 4, 1, 1, (1, 2, 4, 8), 8, synthetic_layers=2)
    observed = replace(spec, sequences_per_replica=5)
    batch, is_observed, basis = z._local_batch_binding(observed)
    assert (batch, is_observed, basis) == (
        5, True, "observed_block_table_sequences_per_replica")
    assert z._local_batch(observed) == 5
    assert z._geometry(observed, "decode").batch == 5
    fallback, is_fallback, fallback_basis = z._local_batch_binding(
        replace(spec, concurrency=10, dp=4))
    assert (fallback, is_fallback, fallback_basis) == (
        3, False, "declared_upper_bound_ceil_concurrency_over_dp")
    prediction = z.predict_cell(observed)
    assert "local_batch:5" in prediction.notes
    assert "local_batch_observed:1" in prediction.notes
    assert "local_batch_basis:observed_block_table_sequences_per_replica" in prediction.notes
    assert "local_batch_observed:0" not in prediction.notes


def test_inactive_draft_is_skipped_and_output_uses_selected_rows(compact_cases):
    draft = z.predict_cell(z.CellSpec("draft", "unit", "decode", compact_cases["v41"], "DeepSeek-V4.1",
                                      256, 2, 2, 1, 2, 2, 1, (4,), 4))
    assert draft.rows and not any(row.kind == "spec_decode" for row in draft.rows)
    assert not any(note.startswith("spec_decode:") for note in draft.notes)
    small = z.predict_cell(z.CellSpec("small", "unit", "prefill", compact_cases["qwen38"], "Qwen3.8-27B",
                                      64, 2, 1, 4, 1, 1, 1, (1, 2, 4, 8), synthetic_layers=2))
    large = z.predict_cell(z.CellSpec("large", "unit", "prefill", compact_cases["qwen38"], "Qwen3.8-27B",
                                      8192, 2, 1, 4, 1, 1, 1, (1, 2, 4, 8), synthetic_layers=2))
    small_o0 = sum(row.total_ms for row in small.rows if row.kind == "lm_head_sampler")
    large_o0 = sum(row.total_ms for row in large.rows if row.kind == "lm_head_sampler")
    assert small_o0 < large_o0 < 2.0 * small_o0
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
    for name in ("hc_projection", "hc_project", "inv_rms"):
        assert z.operator_mechanism(SimpleNamespace(name=name, family="gemm", kind="gemm"), "R0") == "hyperconnection"
    assert z.subgraph_family("R0") == "hyperconnection"
    assert z.operator_mechanism(SimpleNamespace(name="score", family="gemm"), "R1") == "gemm"
    for name, family in (("softmax_mix", "elementwise"), ("cast", "copy"), ("slot_push", "copy")):
        assert z.operator_mechanism(SimpleNamespace(name=name, family=family), "R1") == "norm_residual"
    assert z.subgraph_family("R1") == "attention"
    for name in ("expert_gate_up", "expert_activation", "expert_down"):
        cost = SimpleNamespace(name=name, family="grouped_gemm")
        assert z.operator_mechanism(cost, "F3") == "moe_grouped"
    assert z.operator_mechanism(SimpleNamespace(name="expert_activation", family="elementwise"), "F3") == "activation"
    assert z.operator_mechanism(SimpleNamespace(name="etp_allreduce", family="collective"), "F3") == "collective"
    assert z.operator_mechanism(SimpleNamespace(name="quantize", family="elementwise"), "F2") == "elementwise_quant"
    assert z.operator_mechanism(SimpleNamespace(name="dispatch", family="transport"), "F2") == "collective"
    assert z.operator_mechanism(SimpleNamespace(name="cp_gather", family="collective"), "I1") == "collective"
    assert z.operator_mechanism(SimpleNamespace(name="index_score", family="indexer"), "I1") == "indexer"
    assert z.operator_mechanism(SimpleNamespace(name="tp_allreduce", family="collective"), "F4") == "collective"
    assert z.operator_mechanism(SimpleNamespace(name="shared_activation", family="elementwise"), "F4") == "activation"
    assert z.operator_mechanism(SimpleNamespace(name="shared_gate_up", family="gemm"), "F4") == "gemm"
    for kind in ("A0", "A1", "A2"):
        assert z.operator_mechanism(SimpleNamespace(name="o_proj_transpose", family="copy"), kind) == "elementwise_quant"
        assert z.operator_mechanism(SimpleNamespace(name="dcp_lse_merge", family="elementwise"), kind) == "elementwise_quant"
        for name in ("dcp_allgather", "o_proj_allgather", "tp_allreduce"):
            assert z.operator_mechanism(SimpleNamespace(name=name, family="collective"), kind) == "collective"
    assert z.subgraph_family("gdn_linear_attn") == "attention"
    assert z.subgraph_family("kda_linear_attn") == "attention"
    assert z.classify_kernel("aclnnContiguous_SliceAiCore_Slice", "Slice") == "elementwise_quant"
    assert z.classify_kernel("ZerosLike", "ZerosLike") == "elementwise_quant"
    for name in ("beta_slice", "alpha_slice", "qkv_slice", "q_slice", "k_slice", "v_slice", "z_slice", "core_zeros"):
        assert z.operator_mechanism(SimpleNamespace(name=name, family="copy"), "gdn_linear_attn") == "elementwise_quant"
    assert z.operator_mechanism(SimpleNamespace(name="q_l2norm", family="elementwise"), "gdn_linear_attn") == "gdn_linear_attn"
    assert z.operator_mechanism(SimpleNamespace(name="prepare", family="elementwise"), "gdn_linear_attn") == "elementwise_quant"
    assert z.operator_mechanism(SimpleNamespace(name="gated_delta", family="recurrent"), "gdn_linear_attn") == "gdn_linear_attn"
    assert z.operator_mechanism(SimpleNamespace(name="kda_recurrent", family="recurrent"), "kda_linear_attn") == "kda_linear_attn"
    assert z.operator_mechanism(SimpleNamespace(name="prepare", family="elementwise"), "kda_linear_attn") == "elementwise_quant"


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
    assert z._case_layers(replace(base, model_case=glm53_case, model_label=glm53_label, notes=glm53_notes)) == 45
    assert z._case_layers(replace(base, model_case=glm51_case, model_label=glm51_label, notes=glm51_notes)) == 78


def test_glm51_stale_glm53_declaration_uses_source_case_not_template(compact_cases):
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
    pred = z.predict_cell(replace(cell.spec, model_case=compact_cases["glm51"],
                                  source_config=None, source_config_sha256="",
                                  source_case_dir=None, require_source=False))
    assert pred.layers == 12 and pred.body_ms > 0.0
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


def test_historical_inventory_covers_profiles_fixtures_and_registry():
    entries = z.load_historical_inventory()
    kinds = {item["kind"] for item in entries}
    assert {"profile_source", "fixture", "case_registry"}.issubset(kinds)
    assert all(isinstance(item["exists"], bool) for item in entries)
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
    from mindie_sim.prediction.structure import parse_case

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
        assert mc is not None and "structural_proxy" not in notes
        parsed = parse_case(z._raw_case(z.CellSpec(tag, "a5", "decode", mc, ml, 512, 4, 8, 4, 1, 4, 1, notes=notes)))
        assert parsed.model.layers > 0


def test_l1_l3_comparisons_invariant_under_ttft_tpot_perturbation(tmp_path, compact_cases):
    qwen38 = compact_cases["qwen38"]
    dc_rows = (("MlaPrologV3", "MlaPrologV3", 60000.0), ("_categorical_sample_kernel", "x", 10.0)) + tuple(it for _ in range(3) for it in (("MlaPrologV3", "MlaPrologV3", 20000.0), ("AddRmsNormBias", "AddRmsNormBias", 5000.0), ("_prepare_dflash_inputs", "x", 5.0), ("_categorical_sample_kernel", "x", 10.0)))
    dc_csv, pf_csv = tmp_path / "dc.csv", tmp_path / "pf.csv"
    write_kernel_csv(dc_csv, rows=dc_rows)
    write_kernel_csv(pf_csv, rows=KERNEL_ROWS)
    for phase, csv_p in (("decode", dc_csv), ("prefill", pf_csv)):
        spec = z.CellSpec(f"inv_{phase}", "unit", phase, qwen38, "Qwen3.8-27B", 128, 2, 1, 4, 1, 1, 1, synthetic_layers=2)
        pred = z.predict_cell(spec)
        c1 = z.attach_trace(z.MeasuredCell(spec, (csv_p,), None, 120.0, 15.0, None, 4 if phase == "decode" else 1, True))
        c2 = z.attach_trace(z.MeasuredCell(spec, (csv_p,), None, 9999.0, 888.0, None, 4 if phase == "decode" else 1, True))
        assert (c1.decode_steps, c1.step_trace_ms, c1.trace_quality) == (c2.decode_steps, c2.step_trace_ms, c2.trace_quality)
        l13_a = [item for item in z.compare_cell(c1, pred) if item.level in {"L1", "L2", "L3"}]
        l13_b = [item for item in z.compare_cell(c2, pred) if item.level in {"L1", "L2", "L3"}]
        assert l13_a and l13_a == l13_b
    jsonl = tmp_path / "bench.jsonl"
    jsonl.write_text(json.dumps({**z.cell_to_dict(z.attach_trace(z.MeasuredCell(z.CellSpec("inv_dc", "unit", "decode", qwen38, "Qwen3.8-27B", 128, 2, 1, 4, 1, 1, 1, synthetic_layers=2), (dc_csv,), None, 120.0, 15.0, None, 4, True))), "model_case": str(qwen38)}) + "\n", encoding="utf-8")
    res = z.run_validation(benchmark_jsonl=jsonl, include_historical=False)
    assert "_prepare_dflash_inputs" in res["unresolved_kernels"] and res["agent_decisions"] and z.main(["--benchmark-jsonl", str(jsonl), "--no-historical", "--json"]) == 1


def test_public_rows_expose_native_call_occurrence_and_exact_coverage(compact_cases):
    spec = z.CellSpec("native", "unit", "decode", compact_cases["qwen38"], "Qwen3.8-27B",
                      128, 2, 1, 4, 1, 1, 1, (1, 2, 4, 8), 2)
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
                  if (row.native_occurrence or {}).get("membership") != "consumed_by_selected_fusion"
                  and (row.native_occurrence or {}).get("membership") != "consumed_by_selected_native_call"
                  and (row.native_occurrence or {}).get("charge") != "member")
    attribution = sum(row.count for row in prediction.rows
                      if (row.native_occurrence or {}).get("membership") == "consumed_by_selected_fusion")
    assert coverage["denominator"]["emitted_operators"] == emitted
    assert coverage["totals"]["attribution_occurrences"] == attribution
    assert (coverage["totals"]["bound_occurrences"]
            + coverage["totals"]["unresolved_occurrences"]) == emitted
    assert coverage["totals"]["unique_calls"] == len(coverage["unique_calls"])
    assert 0 < coverage["totals"]["unique_calls"] <= len({
        row.native_call["call_id"] for row in bound})


def test_public_qwen36_prefill_gdn_prepare_descriptors_and_owner(compact_cases):
    spec = z.CellSpec("gdn", "unit", "prefill", compact_cases["qwen36"], "Qwen3.6-27B",
                      256, 1, 1, 2, 1, 1, 1)
    prediction = z.predict_cell(spec)
    rows = {row.name: row for row in prediction.rows}
    prepare, delta = rows["prepare"], rows["gated_delta"]
    assert prepare.count == delta.count == 3
    assert prepare.native_call["call_id"] == delta.native_call["call_id"]
    assert prepare.native_occurrence["charge"] == "member"
    assert delta.native_occurrence["charge"] == "call"
    call = delta.native_call
    assert call["api"]["aclnn_symbol"] == "aclnnChunkGatedDeltaRuleFwd"
    assert call["evidence"]["aclnn_symbol"] == "source_declared"
    assert "aclnn_symbol_unresolved" not in call["unresolved"]
    assert call["typed"]["shapes"]["q"] == [8, 128]
    occurrence = delta.native_occurrence
    assert occurrence["typed"]["shapes"]["q"] == [1, 256, 8, 128]
    assert occurrence["typed"]["shapes"]["v"] == [1, 256, 24, 128]
    assert occurrence["typed"]["shapes"]["o"] == [1, 256, 24, 128]
    prepared = occurrence["prepare"]
    assert prepared["arguments"]["cu_seqlens"] == [0, 256]
    assert prepared["arguments"]["chunks"] == 4
    assert prepared["named_arguments"]["layout"] == "BSND"
    assert prepared["named_arguments"]["scale"] == 128 ** -0.5
    assert prepared["descriptors"]["initial_state"]["shape"] == [1, 24, 128, 128]
    assert prepared["descriptors"]["o"]["role"] == "output"
    assert set(prepared["outputs"]) == {"o", "final_state", "g_cumsum", "A",
                                       "q_hat", "k_hat", "q_rstd", "k_rstd"}
    assert set(prepared["disabled_outputs"]) == {"beta_eff", "h"}
    assert prepared["output_slots"]["g_cumsum"]["acl_slot"] == "gCumsumOutOptional"
    assert prepared["descriptors"]["A"]["shape"] == [1, 24, 256, 64]
    assert prepared["descriptors"]["q_rstd"]["shape"] == [1, 8, 256]
    assert sum(item["count"] for item in prepared["physical_presentations"]) == 7
    assert prepared["allocation"] == "not_performed"
    assert occurrence["prepare_args"]["shapes"]["q"] == [1, 256, 8, 128]
    independent = {row.name: row for row in z.predict_cell(
        replace(spec, prompt_tokens=128)).rows}
    independent_delta = independent["gated_delta"]
    assert independent_delta.native_call["call_id"] == call["call_id"]
    assert independent_delta.native_occurrence["typed"]["shapes"]["q"] == [1, 128, 8, 128]
    assert independent_delta.native_occurrence["prepare"]["arguments"]["cu_seqlens"] == [0, 128]
    batched = {row.name: row for row in z.predict_cell(
        replace(spec, concurrency=2)).rows}
    batched_delta = batched["gated_delta"]
    assert batched_delta.native_call["call_id"] == call["call_id"]
    assert batched_delta.native_occurrence["prepare"]["arguments"]["cu_seqlens"] == [0, 256, 512]
    assert batched_delta.native_occurrence["prepare"]["descriptors"]["initial_state"]["shape"] == [2, 24, 128, 128]
    decode = {row.name: row for row in z.predict_cell(
        replace(spec, phase="decode", prompt_tokens=128, max_tokens=1)).rows}
    assert decode["gated_delta"].native_call["api"]["entry"] == "RecurrentGatedDeltaRule"
    assert "prepare" not in decode["gated_delta"].native_occurrence


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
    case = tmp_path / "case.json"
    case.write_text(json.dumps(model))
    source = tmp_path / "weights" / "deepseek-v4.1-flash" / "config.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps({"model_type": "deepseek_v41", "architectures": ["DeepseekV41ForCausalLM"]}))
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    campaign = tmp_path / "out" / "campaign"
    campaign.mkdir(parents=True)
    (tmp_path / "cases").mkdir()
    (tmp_path / "cases" / "campaign.json").write_text(
        json.dumps({"kv_cache_dtype": kv} if kv else {}))
    return z.CellSpec("campaign_dc", "out", "decode", case, "DeepSeek-V4.1-Flash",
                      1024, 2, 8, 1, 2, 2, 1, source_config=source,
                      source_config_sha256=sha, source_deploy_sha256=sha, source_case_dir=campaign)


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
        if role:
            data["fusion_role"] = role
        if native:
            data["native_implementation"] = {"native_kind": native}
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
    assert rows["recurrent_scan0"].mechanism == "gdn_linear_attn"
    assert rows["attention.hc_pre.native"].mechanism == "hyperconnection"
    assert rows["logits"].mechanism == "gemm" and rows["logits"].subgraph == ""
    assert rows["q_a"].mechanism == "gemm" and rows["q_a"].subgraph == ""
    assert out["subgraphs"] == pytest.approx({"moe": 1.35, "attention": 0.35, "norm_residual": 0.5, "hyperconnection": 0.4})
    assert sum(out["per_layer"].values()) == pytest.approx(4.8)
    assert out["body_ms"] == pytest.approx(3.0) and out["step_ms"] == pytest.approx(4.0)
    assert all(row.native_occurrence["basis"] == "expected_index_mod_dp" for row in out["rows"])


def test_topology_cache_respects_ordered_catalog_precedence():
    glm53_flash = ROOT / "examples" / "structure" / "cases" / "decode-a5_glm53flash_tp8_c4_p8k.json"
    base = z.CellSpec("cat-order", "unit", "decode", glm53_flash, "GLM-5.3-Flash",
                      1024, 1, 8, 8, 1, 1, 1)
    first = replace(base, notes=("override_model", "catalog:deepseek-v3.2-prune-3l", "catalog:glm-5.1"))
    second = replace(base, notes=("override_model", "catalog:glm-5.1", "catalog:deepseek-v3.2-prune-3l"))
    z._CASE_LAYERS.clear()
    z._CASE_MOE.clear()
    try:
        first_layers = z._case_layers(first)
        second_warm = z._case_layers(second)
        first_moe = z._case_has_moe(first)
        second_moe_warm = z._case_has_moe(second)
        assert z._model_topology_fingerprint(first) != z._model_topology_fingerprint(second)
        z._CASE_LAYERS.clear()
        z._CASE_MOE.clear()
        second_cold = z._case_layers(second)
        second_moe_cold = z._case_has_moe(second)
        assert first_layers == 3
        assert second_warm == second_cold == 78
        assert first_moe is True
        assert second_moe_warm == second_moe_cold is True
    finally:
        z._CASE_LAYERS.clear()
        z._CASE_MOE.clear()


def test_topology_cache_revalidates_declared_source_digest(tmp_path):
    source = tmp_path / "hf-config.json"
    config = {
        "model_type": "llama",
        "hidden_size": 64,
        "num_attention_heads": 4,
        "num_key_value_heads": 2,
        "num_hidden_layers": 3,
        "intermediate_size": 128,
        "vocab_size": 128,
    }
    source.write_text(json.dumps(config), encoding="utf-8")
    pinned = z.CellSpec(
        "digest-check", "unit", "decode", MODEL_CASE, "Qwen3.8-27B",
        1024, 2, 8, 4, 1, 1, 1,
        source_config=source,
        source_config_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    )
    unpinned = replace(pinned, source_config_sha256="")
    z._CASE_LAYERS.clear()
    z._CASE_MOE.clear()
    try:
        assert z._case_layers(pinned) == 3
        assert z._case_has_moe(pinned) is False
        config["num_hidden_layers"] = 7
        source.write_text(json.dumps(config), encoding="utf-8")
        warm_layers = z._case_layers(pinned)
        warm_moe = z._case_has_moe(pinned)
        unpinned_warm = z._case_layers(unpinned)
        z._CASE_LAYERS.clear()
        z._CASE_MOE.clear()
        cold_layers = z._case_layers(pinned)
        cold_moe = z._case_has_moe(pinned)
        unpinned_cold = z._case_layers(unpinned)
        assert warm_layers == cold_layers == 0
        assert warm_moe == cold_moe is False
        assert unpinned_warm == unpinned_cold == 7
    finally:
        z._CASE_LAYERS.clear()
        z._CASE_MOE.clear()


def test_moe_zero_ep_resolves_without_recursion():
    spec = z.CellSpec("moe-ep0", "unit", "decode", GLM51_CASE, "GLM-5.1/W4A4C8",
                      1024, 2, 8, 1, 8, 0, 1)
    z._CASE_LAYERS.clear()
    z._CASE_MOE.clear()
    try:
        assert z._case_has_moe(spec) is True
        assert z._ep_ranks(spec) == 8
        assert len(z._structure_fingerprint(spec)) == 64
        dense = z.CellSpec("dense-ep0", "unit", "decode", MODEL_CASE, "Qwen3.8-27B",
                           1024, 2, 8, 4, 2, 0, 1)
        assert z._case_has_moe(dense) is False
        assert z._ep_ranks(dense) == 1
    finally:
        z._CASE_LAYERS.clear()
        z._CASE_MOE.clear()
