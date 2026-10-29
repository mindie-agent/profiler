"""Historical capture branches through the ordinary streaming replay.

These tests supply an explicit implementation declaration and no occurrence
bindings. Matching a fusion's active tensors must not manufacture layer timing.
"""
from hashlib import sha256
from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"
LOWERINGS = {"mla_prolog": "vllm_ascend_mla_prolog_v3"}


def replay(capture, case_name):
    structure = pytest.importorskip("mindie_sim.structure")
    case = Path(structure.__file__).resolve().parents[1] / "examples/cases" / f"{case_name}.json"
    if not case.exists():
        pytest.skip("the companion sim source checkout and independent cases are required")
    original = case.read_bytes()
    run = runpy.run_path(str(ROOT / "examples/structure/replay_body_capture.py"))["replay"]
    report = run(
        FIXTURES / capture, case, phase="decode", tokens=1, context=4096,
        lowerings=LOWERINGS,
        lowering_source={"kind": "explicit_test_implementation_declaration"},
        mapping_limit=0,
    )
    assert case.read_bytes() == original
    assert report["declaration_source"]["case_sha256"] == sha256(original).hexdigest()
    assert report["declaration_source"]["implementation_overrides"] == LOWERINGS
    assert report["declared_execution"]["software"]["kernels"]["lowerings"] == LOWERINGS
    assert report["observed_phase"] is None
    assert report["retained_examples"] == []
    assert report["bound_layers"] == report["bound_subgraphs"] == []
    assert report["bound_busy_union_ns"] == 0
    assert sum(report["status_counts"].values()) == report["positive_event_count"]
    operators = report["body_contracts"]["operators"] + report["other_operators"]
    assert sum(row["event_count"] for row in operators) == report["positive_event_count"]
    return report


def test_glm_decode_stream_keeps_both_real_prolog_output_branches():
    report = replay("attention_cache_contracts/a3_glm53_decode.csv", "glm53-a3-w4a8")
    assert report["positive_event_count"] == 3
    examples = report["retained_body_examples"]
    prologs = [row for row in examples if row["operator_type"] == "MlaPrologV3"]
    assert len(prologs) == 2
    assert {row["candidate_count"] for row in prologs} == {21, 57}
    assert all(row["status"] == "ambiguous" for row in prologs)
    assert all(row["observed_native_tensor_abi"][1] == "MlaPrologV3" for row in prologs)
    assert prologs[0]["observed_contract"] != prologs[1]["observed_contract"]
    assert not (
        set(prologs[0]["candidate_subgraph_ids"]) & set(prologs[1]["candidate_subgraph_ids"])
    )
    groups = report["structural_groups"]
    assert sum(row["event_count"] for row in groups) == 3
    assert all(not row["occurrence_binding_implied"] for row in groups)


def test_kimi_mixed_capture_retains_prefill_rows_under_decode_declaration():
    report = replay("body_attention/kimi_a5_full_model.csv", "kimi-k3-a5")
    assert report["positive_event_count"] == 8
    examples = {row["operator_type"]: row for row in report["retained_body_examples"]}
    prolog = examples["MlaPrologV3"]
    # The independent case keeps dense attention BF16; its routed-expert MXFP
    # declaration cannot be reused to invent FP8 attention projection weights.
    assert prolog["status"] == "unmapped"
    assert prolog["candidate_count"] == 0
    assert prolog["diagnostic"]["category"] == "declared_structure_mismatch"
    assert prolog["observed_contract"][2] == ((1, 7168), "fp8_e4m3", "ND")
    assert prolog["observed_native_tensor_abi"][2][0][0] == (1, 1, 7168)
    assert examples["layer_norm_gated_fwd_kernel"]["status"] == "unmapped"
    assert examples["ScatterPaKvCache"]["status"] == "unmapped"
    assert examples["FusedInferAttentionScore"]["status"] == "unmapped"
    assert report["status_counts"]["unmapped"] > 0
