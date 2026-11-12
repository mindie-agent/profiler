import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples" / "structure"))
import hf_source_slices as s


def _obs(sha, key, relation="in_sample_regime_calibration", fit=True, receipt="r1", path="raw.csv"):
    frames = [{"phase": "prefill", "rank_id": "0", "device_id": "4", "forward_id": "f0-" + key[:4],
               "start_ns": 100, "end_ns": 300}]
    return {"measurements": {"per_forward_window": {
        "status": "measured", "raw_digest_verified": True, "raw_sha256": sha, "source_sha256": sha,
        "raw_path": path, "window_source": receipt, "boundary": "per_forward_window_source_receipt",
        "source_scope_id": sha + ":" + key, "receipt_sha256": "r" * 64,
        "keyset": {"keyset_sha256": key, "windows_integer_ns_sha256": key, "integer_ns_complete": True},
        "evaluation": {"source_declaration": {"source_file_sha256": "s" * 64,
            "evaluation_relation": relation, "target_timing_used_to_fit": fit,
            "source_path_listed": True}, "blind_claim_status": "not_blind_source_target_fit"},
        "frame_identifiers": frames}}}


def _row(cid, relation="zero_shot_piecewise_recomputed", fit=False):
    return {"capture_id": cid, "suite": "extended_a3_a5_workstream_captures",
            "source_calibration": {"evaluation_relation": relation, "target_timing_used_to_fit": fit}}


def test_lone_extended_alias_keeps_source_fit_without_sibling():
    sha, key = "a" * 64, "b" * 64
    rec = s.slice_record(_row("ext-alone"), _obs(sha, key))
    info = s.disclose_source_slices([rec])["by_id"]["ext-alone"]
    assert info["evaluation_relation"] == "in_sample_regime_calibration"
    assert info["target_timing_used_to_fit"] is True
    assert info["inherited"] is False
    item = {"capture_id": "ext-alone", "evaluation_relation": "zero_shot_piecewise_recomputed",
            "target_timing_used_to_fit": False, "coverage_only": False}
    s.apply_slice_disclosure(item, info, coverage_only=lambda rel, role: True)
    assert item["evaluation_relation"] == "in_sample_regime_calibration"
    assert item["target_timing_used_to_fit"] is True
    assert item["coverage_only"] is True


def test_pair_preserves_each_declared_relation_and_no_hidden_population():
    sha, key = "a" * 64, "b" * 64
    ext = s.slice_record(_row("ext"), _obs(sha, key))
    wave = s.slice_record(_row("wave", "regime_table_replay", True), _obs(sha, key, receipt="r2"))
    report = s.disclose_source_slices([ext, wave])
    assert report["cohort"]["measured_ids"] == 2
    assert report["cohort"]["unique_physical_series"] == 1
    assert report["alias_groups"][0]["capture_ids"] == ["ext", "wave"]
    assert report["by_id"]["ext"]["evaluation_relation"] == "in_sample_regime_calibration"
    assert report["by_id"]["wave"]["evaluation_relation"] == "regime_table_replay"
    assert report["alias_groups"][0]["conflict"] is True


def test_adjacent_negative_and_duplicate_path_do_not_alias():
    a = s.slice_record(_row("ext"), _obs("a" * 64, "b" * 64))
    other = s.slice_record(_row("other"), _obs("c" * 64, "d" * 64, receipt="r2",
                                                     relation="zero_shot_piecewise_recomputed", fit=False))
    dup_path = s.slice_record(_row("dup"), _obs("a" * 64, "e" * 64, receipt="r3", path="raw.csv",
                                                         relation="zero_shot_piecewise_recomputed", fit=False))
    report = s.disclose_source_slices([a, other, dup_path])
    assert report["cohort"]["unique_physical_series"] == 3
    assert report["cohort"]["alias_groups"] == 0
    assert report["by_id"]["other"]["evaluation_relation"] is None
    assert report["by_id"]["dup"]["evaluation_relation"] is None


def test_receipt_path_is_not_identity_but_raw_sha_and_scope_are():
    sha, key = "a" * 64, "b" * 64
    one = s.slice_record(_row("one"), _obs(sha, key, receipt="r1"))
    two = s.slice_record(_row("two"), _obs(sha, key, receipt="r2"))
    report = s.disclose_source_slices([one, two])
    assert report["cohort"]["unique_physical_series"] == 1
    assert report["cohort"]["alias_groups"] == 1
