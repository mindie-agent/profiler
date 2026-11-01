"""Unit tests for Wave 5 segmentation anchors (AddRmsNormQuant, SparseFlashAttention/Mla, DP-partner EP prefill) and Wave 5 evaluator contracts.

[Role] Verify that decode_segmentation._norm recognizes AddRmsNormQuant (Qwen3-30B-A3B
  W8A8 fused residual RMSNorm + static quant), prefill.anchor / _attention_query_rows /
  _prefill_head / align recognize SparseFlashAttention/SparseFlashMla chunks and
  DP-partner EP all-to-all prefill segments (while rejecting GQA mismatches or missing
  GroupedMatmul/SwiGlu), and wave5_generalization_eval enforces strict parser_identity
  parity, derives cohort topology from captures, and discloses regime provenance.
[Invariants] No host environment pollution; pure in-memory unit tests (< 2s).
[Timeouts & Locks] Synchronous in-memory checks only.
[Side-Effect Policy] Read-only against repository reports; no filesystem mutations.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "examples" / "structure") not in sys.path:
    sys.path.insert(0, str(ROOT / "examples" / "structure"))

from mindie_profiler.decode_segmentation import _Row, _norm
from mindie_profiler.events import Event, PARSER_VERSION
from mindie_profiler.normalized import shapes
import prefill
import wave5_generalization_eval as wave5_eval


def _row(
    op_type: str,
    input_shapes: str,
    output_shapes: str,
    *,
    start_ns: int = 1_000,
    end_ns: int = 2_000,
) -> _Row:
    ev = Event(
        rank_id="0",
        rank_index=0,
        name=op_type,
        op_type=op_type,
        task_type="AI_VECTOR_CORE",
        core="AI_VECTOR_CORE",
        stream_id="10",
        task_id="20",
        device_id="0",
        start_ns=start_ns,
        end_ns=end_ns,
        source_kind="kernel_details_csv",
        table="csv",
        input_shapes=input_shapes,
        output_shapes=output_shapes,
        input_dtypes="DT_BF16",
        output_dtypes="INT8",
        input_formats="ND",
        output_formats="ND",
        locator={"csv_line": 1, "row": "1"},
    )
    return _Row(ev, shapes(ev.input_shapes), shapes(ev.output_shapes))


def test_add_rms_norm_quant_recognized_only_at_hidden_width() -> None:
    valid = _row("AddRmsNormQuant", "16,2048;16,2048;2048", "16,2048;16,2048")
    wrong_width = _row("AddRmsNormQuant", "16,1024;16,1024;1024", "16,1024;16,1024")
    assert _norm(valid, 2048) is True
    assert _norm(wrong_width, 2048) is False


def test_prefill_sparse_flash_attention_and_mla_anchors() -> None:
    for kind in ("SparseFlashAttention", "SparseFlashMla", "SparseAttnSharedkv"):
        prefill_chunk = _row(kind, "4096,16,512;64,128,1,512", "4096,16,512")
        decode_step = _row(kind, "8,16,512;64,128,1,512", "8,16,512")
        assert prefill.anchor(prefill_chunk) == "mla"
        assert prefill._attention_query_rows(prefill_chunk) == 4096
        assert prefill.anchor(decode_step) is None
        assert prefill._attention_query_rows(decode_step) == 8


def test_dp_partner_prefill_alignment_and_negative_controls() -> None:
    config = {
        "hidden_size": 7168,
        "vocab_size": 129280,
        "tp": 4,
        "layer_plans": [{"attention": "mla", "ffn": "moe"}],
    }
    head_row = _row("Index", "1,7168;1;2;1", "1,7168", start_ns=9_000, end_ns=10_000)
    assert prefill._prefill_head(head_row, config) is True
    assert prefill._prefill_head(_row("Index", "2,7168;1;2;1", "2,7168"), config) is False

    rows = [
        _row("BroadcastTo", "1;1", "4095,512", start_ns=1_000, end_ns=1_500),
        _row("RmsNorm", "1,7168;7168", "1,7168", start_ns=2_000, end_ns=2_500),
        _row("SparseFlashMla", "1,16,512;64,128,1,512", "1,16,512", start_ns=3_000, end_ns=4_000),
        _row("AddRmsNorm", "1,7168;1,7168;7168", "1,7168;1,7168", start_ns=4_500, end_ns=5_000),
        _row("MoeInitRoutingV3", "4096,7168;4096,4", "16384,7168", start_ns=5_200, end_ns=5_600),
        _row("GroupedMatmulSwigluQuant", "16384,7168", "16384,2048", start_ns=5_800, end_ns=6_400),
        _row("GroupedMatmul", "16384,2048", "16384,7168", start_ns=6_500, end_ns=6_900),
        _row("MoeDistributeCombineV2", "16384,7168;4096,4", "1,7168", start_ns=7_000, end_ns=8_000),
        _row("RmsNorm", "1,7168;7168", "1,7168", start_ns=8_200, end_ns=8_600),
        head_row,
    ]
    aligned, err = prefill.align(rows, config, 0)
    assert err is None
    assert aligned is not None
    assert aligned["dp_partner_prefill"] is True
    assert aligned["query_rows"] == 4096
    assert aligned["matched_layer_count"] == 1

    # Negative control 1: changing declared attention from mla to gqa must be rejected
    bad_gqa_cfg = {**config, "layer_plans": [{"attention": "gqa", "ffn": "moe"}]}
    assert prefill.align(rows, bad_gqa_cfg, 0)[0] is None

    # Negative control 2: removing GroupedMatmul/SwiGlu must be rejected
    no_gmm_rows = [r for r in rows if not r.kind.startswith("GroupedMatmul")]
    assert prefill.align(no_gmm_rows, config, 0)[0] is None


def test_wave5_aggregation_derives_topology_and_discloses_provenance() -> None:
    assert PARSER_VERSION == "mindie_profiler/0.5.5"
    assert wave5_eval._bounded_workers(0) == 1
    assert wave5_eval._bounded_workers(3) == 3
    assert wave5_eval._bounded_workers(16) == 4

    synthetic_a2 = {
        "schema_version": "a2/1",
        "parser_identity": wave5_eval.PARSER_IDENTITY,
        "cases": [{
            "path": "/tmp/a2.csv",
            "traits": {
                "hw": "a2", "cohort": "a2/c_decode", "cell": "a2_c1", "family": "qwen3-30b-a3b",
                "phase": "decode", "tp": 4, "dp": 1, "ep": 4, "num_layers": 48, "num_experts": 128,
                "top_k": 8, "spec_tokens": 0, "context_tokens": 4096, "concurrency": 1,
            },
            "template": "t_a2", "status": "compared", "forward_count": 10,
            "observed_ms": 10.0, "predicted_ms": 10.2, "relative_error": 0.02,
            "passed_15pct": True, "passed_10pct": True,
        }],
        "cohort_summaries": [{
            "cohort": "a2/c_decode", "family": "qwen3-30b-a3b", "phase": "decode",
            "capture_count": 1, "compared_count": 1,
            "stats": {"count": 1, "pass_15pct": 1, "pass_10pct": 1, "pass_rate_15pct": 1.0,
                      "pass_rate_10pct": 1.0, "mean_abs_error": 0.02, "median_abs_error": 0.02, "max_abs_error": 0.02},
        }],
    }
    synthetic_a3 = {
        "schema_version": "a3/1",
        "parser_identity": wave5_eval.PARSER_IDENTITY,
        "heldout_cases": [{
            "path": "/tmp/a3.csv",
            "traits": {
                "hw": "a3", "cohort": "a3/c_decode", "cell": "a3_c1", "family": "glm-5.3-flash",
                "phase": "decode", "tp": 8, "dp": 1, "ep": 8, "num_layers": 40, "num_experts": 256,
                "top_k": 8, "spec_tokens": 3, "context_tokens": 196608, "concurrency": 1,
            },
            "template": "t_a3", "status": "compared", "forward_count": 10,
            "observed_ms": 20.0, "predicted_ms": 20.4, "relative_error": 0.02,
            "passed_15pct": True, "passed_10pct": True,
        }],
        "cohort_summaries": [{
            "cohort": "a3/c_decode", "family": "glm-5.3-flash", "phase": "decode",
            "capture_count": 1, "compared_count": 1,
            "stats": {"count": 1, "pass_15pct": 1, "pass_10pct": 1, "pass_rate_15pct": 1.0,
                      "pass_rate_10pct": 1.0, "mean_abs_error": 0.02, "median_abs_error": 0.02, "max_abs_error": 0.02},
        }],
    }
    synthetic_a5 = {
        "schema_version": "a5/1",
        "parser_identity": wave5_eval.PARSER_IDENTITY,
        "captures": [{
            "path": "/tmp/a5.csv",
            "traits": {
                "hw": "a5", "cohort": "a5_qwen36_tp4_mtp3", "cell": "a5_qwen36_tp4_mtp3_prefill_192k_c1",
                "family": "qwen3.6-27b", "phase": "prefill", "tp": 4, "dp": 1, "ep": 1,
                "layers": 64, "num_experts": 256, "top_k": 8, "spec_tokens": 3,
                "context_tokens": 196608, "concurrency": 1,
            },
            "template": "t_a5", "status": "compared", "forward_count": 6,
            "observed_ms": 100.0, "predicted_ms": 101.0, "relative_error": 0.01,
            "passed_15pct": True, "passed_10pct": True,
        }],
        "cohort_phase_summaries": [{
            "cohort": "a5_qwen36_tp4_mtp3", "family": "qwen3.6-27b", "phase": "prefill",
            "layers": 64, "num_experts": 256, "top_k": 8, "spec_tokens": 3,
            "capture_count": 1, "compared_count": 1,
            "stats": {"count": 1, "pass_15pct": 1, "pass_10pct": 1, "pass_rate_15pct": 1.0,
                      "pass_rate_10pct": 1.0, "mean_abs_error": 0.01, "median_abs_error": 0.01, "max_abs_error": 0.01},
        }],
    }

    agg = wave5_eval.aggregate_chip_reports(synthetic_a2, synthetic_a3, synthetic_a5)
    cohorts = {c["cohort"]: c for c in agg["cohort_summaries"]}
    assert cohorts["a5/a5_qwen36_tp4_mtp3_prefill"]["tp"] == 4
    assert cohorts["a5/a5_qwen36_tp4_mtp3_prefill"]["dp"] == 1
    assert cohorts["a5/a5_qwen36_tp4_mtp3_prefill"]["ep"] == 1
    assert cohorts["a5/a5_qwen36_tp4_mtp3_prefill"]["calibration_provenance"]["input_conditioned_regime_overrides"] is False
    assert cohorts["a3/c_decode"]["calibration_provenance"]["input_conditioned_regime_overrides"] is True

    for invalid_a2 in (
        {**synthetic_a2, "parser_identity": "mindie_profiler/0.5.4:deadbeef"},
        {**synthetic_a2, "parser_identity": None},
        {k: v for k, v in synthetic_a2.items() if k != "parser_identity"},
    ):
        try:
            wave5_eval.aggregate_chip_reports(invalid_a2, synthetic_a3, synthetic_a5)
        except ValueError as exc:
            assert "chip_report_parser_identity_mismatch:a2" in str(exc)
        else:
            raise AssertionError("Expected ValueError on missing or stale chip report parser_identity")

    md = wave5_eval.render_markdown(agg)
    assert "`4/1/1`" in md
    assert "in_sample_regime_calibration" in md

    report_path = ROOT / "examples" / "structure" / "results" / "wave5_full_generalization.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["parser_identity"] == wave5_eval.PARSER_IDENTITY
    q36_cohorts = [c for c in report["cohort_summaries"] if "a5_qwen36_tp4_mtp3" in c["cohort"]]
    assert q36_cohorts and all((c["tp"], c["dp"], c["ep"]) == (4, 1, 1) for c in q36_cohorts)
    s = report["summary"]["wave5_all"]
    assert s["count"] == 1653
    assert s["pass_10pct"] == s["count"]
    assert s["pass_rate_10pct"] == 1.0
    assert s["max_abs_error"] <= 0.10


def test_release_workflow_and_notes_point_to_0_5_5() -> None:
    wf = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    notes_path = ROOT / "docs" / "releases" / "profiler-0.5.5.md"
    assert "release-notes-path: docs/releases/profiler-0.5.5.md" in wf
    assert notes_path.is_file()
    assert "# mindie-profiler 0.5.5" in notes_path.read_text(encoding="utf-8")
