"""Regression tests for honest in_sample provenance across calibrated cases and cases.json.

[Role] Verify that every calibrated rule and case file modified in v0.5.4 declares
  honest in_sample provenance, preserves prior_frozen_model_sha256 when superseding
  frozen transfer rules, and aligns case-level and cases.json calibration metadata.
[Invariants] No rule modified relative to its frozen predecessor may retain a frozen-*
  rule ID or evaluation_relation != 'in_sample'. Case-level runtime.metadata.calibration
  and cases.json calibration_provenance must agree with rule-level in_sample provenance.
[Timeouts & Locks] Pure local JSON inspection (< 1s); no subprocesses or locks.
[Side-Effect Policy] Read-only validation of examples/structure/cases/*.json and cases.json.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRUCT_DIR = ROOT / "examples" / "structure"

MODIFIED_CASE_FILES = (
    "a3-v41-tp4dp4-128k-source.json",
    "decode-a3_glm53_dc4k_b4.json",
    "decode-a3_glm53_w4a8_tp16_tpot30_c2.json",
    "decode-a3_glm53_w4a8_tp16_tpot50_c2.json",
    "decode-a3_glm53flash_tp16_aclgraph_c8.json",
    "decode-a3_kimi4_tp8_w4a8_c16.json",
    "decode-a5_glm53flash_heldout_c12_p4k.json",
    "decode-a5_glm53flash_heldout_c24_p12k.json",
    "decode-a5_glm53flash_tp8_c16_p4k.json",
    "decode-a5_glm53flash_tp8_c16_p8k.json",
    "decode-a5_glm53flash_tp8_c32_p8k.json",
    "decode-a5_glm53flash_tp8_c4_p8k.json",
    "decode-a5_glm53flash_tp8_c8_p4k.json",
    "decode-a5_kimi_k3_p32768_c1.json",
    "decode-a5_qwen36_highconc_c4.json",
    "decode-a5_qwen36_highconc_c40.json",
    "decode-a5_qwen38_highconc_c32.json",
    "decode-a5_qwen38_highconc_c4.json",
    "decode-glm53flash-a5-tp8-c1.json",
    "decode-glm53flash-a5-tp8-c3.json",
    "decode-qwen35-35b-a3-tp4-c144.json",
    "decode-qwen35-35b-a5-tp4-c4-graph.json",
    "decode-qwen35-397b-a3-tp16-c136.json",
    "decode-qwen35-397b-a3-tp16-c48.json",
    "decode-qwen36-a5-tp2-c1.json",
    "decode-qwen36-a5-tp2-c12.json",
)


def test_modified_case_files_and_registry_declare_consistent_in_sample_provenance():
    assert len(MODIFIED_CASE_FILES) == 26
    insample_prefixed_rules = 0

    for fname in MODIFIED_CASE_FILES:
        path = STRUCT_DIR / "cases" / fname
        doc = json.loads(path.read_text(encoding="utf-8"))
        meta = doc.get("runtime", {}).get("metadata", {})
        if "calibration" in meta:
            cal = meta["calibration"]
            assert cal.get("evaluation_relation") == "in_sample", f"{fname} runtime.metadata.calibration not in_sample"
            assert cal.get("target_timing_used_to_fit") is True, f"{fname} target_timing_used_to_fit must be True"
            assert cal.get("heldout_observed_values_used_in_fit") is True
            assert "frozen_model_sha256" not in cal
            assert cal.get("prior_frozen_model_sha256")
        if "calibration_evidence" in meta:
            assert meta["calibration_evidence"].get("evaluation_relation") == "in_sample"

        regimes = doc.get("runtime", {}).get("kernels", {}).get("service_regimes", [])
        in_sample_rules = [r for r in regimes if (r.get("provenance") or {}).get("heldout_observed_values_used_in_fit") is True]
        assert in_sample_rules, f"{fname} must have at least one rule with heldout_observed_values_used_in_fit=True"
        for rule in in_sample_rules:
            rid = rule.get("id", "")
            prov = rule.get("provenance", {})
            assert not rid.startswith("frozen-"), f"{fname} modified rule {rid} must not use frozen-* prefix"
            assert prov.get("evaluation_relation") == "in_sample", f"{fname}:{rid} evaluation_relation must be in_sample"
            assert "frozen_model_sha256" not in prov, f"{fname}:{rid} must use prior_frozen_model_sha256"
            if rid.startswith("insample-"):
                insample_prefixed_rules += 1
                assert len(prov.get("prior_frozen_model_sha256", "")) == 64

    assert insample_prefixed_rules == 6

    cases_doc = json.loads((STRUCT_DIR / "cases.json").read_text(encoding="utf-8"))
    modified_rels = {f"cases/{name}" for name in MODIFIED_CASE_FILES}
    matched_rows = [
        row for row in cases_doc["cases"]
        if row.get("sim_case_path") in modified_rels or (row.get("model_case") or {}).get("path") in modified_rels
    ]
    assert len(matched_rows) == 35
    for row in matched_rows:
        cid = row["id"]
        assert row.get("calibration", {}).get("evaluation_relation") == "in_sample", f"{cid} calibration not in_sample"
        cp = row.get("calibration_provenance")
        assert isinstance(cp, dict), f"{cid} missing calibration_provenance"
        assert cp.get("evaluation_relation") == "in_sample"
        assert cp.get("heldout_observed_values_used_in_fit") is True
        assert cp.get("modified_in_sample_rule_ids"), f"{cid} missing modified_in_sample_rule_ids"
