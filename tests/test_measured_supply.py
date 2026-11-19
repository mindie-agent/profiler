"""R64 QBMM dual-load measured supply, R35/bare boundaries, and status provenance.

[Role]
  Verify ``derive_measured_supply``, ``build_dual_load_service``,
  ``MatrixSupplyAccumulator``, ``analyze_profile``, and ``mindie-profiler analyze``
  derive pure active-pipe matrix supply from retained Golden Captures without
  inventing simulator execution policies, while rejecting >2D batched tensors,
  enforcing bounded memory, and reporting conflicting/absent provenance honestly.

[Invariants]
  * ``rate_flops_per_s`` uses issued active-pipe work over ``aic_mac_time``,
    never end-to-end kernel elapsed duration, and emits pure
    ``mindie-profiler-dual-load/1`` observations (no ``service_regime``).
  * Only 2D ``[M, K] -> [M, N]`` matrix shapes are certified; >2D batched
    tensors stay ``unknown`` (``non_2d_matrix_shape_unsupported``).
  * Declared ``--aic-count`` propagates to both ``bound_events`` and aggregated
    ``candidates`` without stale ``physical_owners_not_declared`` flags.
  * ``analyze_profile`` never calls ``tempfile.gettempdir()``, stops at the
    capture boundary, and flags conflicting ``status.json`` vs CLI image digests.

[Timeouts & Locks]
  Local retained two-row Golden Capture CSV and ``tmp_path`` JSON files only;
  no devices, sleeps, or locks.

[Side-Effect Policy]
  Reads ``tests/fixtures/r64_qbmm_dual_load/kernel_details.csv`` read-only;
  writes only inside pytest ``tmp_path``.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from mindie_profiler.__main__ import main as cli_main
from mindie_profiler.analyze import analyze_profile
from mindie_profiler.measured_supply import MatrixSupplyAccumulator
from mindie_profiler.pmu_derivation import (
    DUAL_LOAD_SCHEMA,
    MEASURED_SUPPLY_SCHEMA,
    R35_IMAGE_SHA,
    R64_IMAGE_SHA,
    build_dual_load_service,
    derive_measured_supply,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "r64_qbmm_dual_load"
FIXTURE = FIXTURE_DIR / "kernel_details.csv"
PROVENANCE = FIXTURE_DIR / "provenance.json"
R64 = f"sha256:{R64_IMAGE_SHA}"
R35 = f"sha256:{R35_IMAGE_SHA}"


def _report(path: Path, deployment_image_id: str | None = None) -> dict:
    return analyze_profile(
        path,
        full_range=True,
        source="csv",
        top_n=2,
        aic_count=32,
        deployment_image_id=deployment_image_id,
    )


def _pair(report: dict) -> dict:
    supply = report["enrichment"]["pmu_observations"]["measured_supply"]
    assert supply["schema_version"] == MEASURED_SUPPLY_SCHEMA
    assert supply["status"] == "measured_pair"
    return supply["pair"]


def test_real_fixture_separates_full_grid_from_tail_by_raw_counters() -> None:
    meta = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    assert meta["not_fabricated"] is True
    report = _report(FIXTURE, R64)
    pmu_obs = report["enrichment"]["pmu_observations"]
    # Declared aic_count=32 propagates cleanly to bound_events and candidates.
    for bound in pmu_obs["bound_events"]:
        ms = bound["measured_supply"]
        assert ms["physical_owners"] == 32
        assert "physical_owners_not_declared" not in ms["missing"]
        assert ms["counter_status"] == "present"
    for cand in pmu_obs["measured_supply"]["candidates"]:
        assert cand["physical_owners"] == 32
        assert "physical_owners_not_declared" not in cand["missing"]
        assert cand["counter_status"] == "present"

    pair = _pair(report)
    assert pair["schema_version"] == DUAL_LOAD_SCHEMA
    assert "service_regime" not in pair
    assert pair["provenance"]["execution_policy_emitted"] is False
    assert pair["provenance"]["not_end_to_end_kernel_latency"] is True
    assert [load["id"] for load in pair["loads"]] == ["saturated", "underfilled"]
    assert pair["identity"]["issue_rule"]["m_alignment"] == 16

    full, tail = pair["saturated"], pair["underfilled"]
    assert pair["identity"]["native_type"] == "QuantBatchMatmulV3"
    assert pair["identity"]["dtype"] == "fp8_e4m3"
    assert (pair["identity"]["n"], pair["identity"]["k"]) == (6144, 16384)
    assert (full["active_owners"], tail["active_owners"]) == (32, 24)
    assert (full["m"], tail["m"]) == (1024, 1)
    assert full["saturated"] is True
    assert tail["saturated"] is False
    assert full["mac_ratio"] > 0.9 > tail["mac_ratio"]
    assert full["limited_by"] == "aic_mac_ratio"
    assert tail["limited_by"] == "aic_mte2_ratio"
    assert full["rate_flops_per_s"] > tail["rate_flops_per_s"]
    assert full["logical_flops"] == full["issued_flops"] == 206_158_430_208
    assert tail["logical_flops"] == 201_326_592
    assert tail["issued_flops"] == 3_221_225_472
    assert full["rate_flops_per_s"] == pytest.approx(
        full["issued_flops"] / (full["pipe_times_ns"]["aic_mac_time"] * 1e-9)
    )
    assert tail["rate_flops_per_s"] == pytest.approx(
        tail["issued_flops"] / (tail["pipe_times_ns"]["aic_mac_time"] * 1e-9)
    )
    assert tail["effective_rate_flops_per_s"] != pytest.approx(tail["rate_flops_per_s"])
    assert 0.2 < pair["service_ratio"]["underfilled_over_saturated"] < 0.35


def test_missing_counters_and_batched_3d_shapes_stay_unknown() -> None:
    record = derive_measured_supply(
        {"aic_total_time": 100.0},
        input_shapes="not-a-shape",
        input_dtypes="DT_FLOAT8_E4M3FN",
        output_shapes='"1,6144"',
        output_dtypes="DT_BF16",
        block_num=None,
        complete_in_window=True,
        duration_ns=10_000,
    )
    assert record["status"] == "unknown"
    assert record["rate_flops_per_s"] is None
    assert "input_matrix_shape_not_parsed" in record["missing"]
    assert "block_num_missing" in record["missing"]
    assert "aic_mac_time_missing" in record["missing"]

    # Batched 3D [2,3,4] x [2,4,5] -> [2,3,5] must NEVER compute 2D 36 FLOPs as measured!
    batched = derive_measured_supply(
        {"aic_mac_time": 1000.0, "aic_mac_ratio": 0.95},
        input_shapes="2,3,4;2,4,5",
        input_dtypes="DT_BF16;DT_BF16",
        output_shapes="2,3,5",
        output_dtypes="DT_BF16",
        block_num=32,
        physical_owners=32,
        complete_in_window=True,
    )
    assert batched["status"] == "unknown"
    assert batched["logical_flops"] is None
    assert batched["rate_flops_per_s"] is None
    assert "non_2d_matrix_shape_unsupported" in batched["missing"]


def test_accumulator_noop_without_owners_and_caps_samples() -> None:
    noop = MatrixSupplyAccumulator(physical_owners=None)
    sample = derive_measured_supply(
        {"aic_mac_time": 1000.0, "aic_mac_ratio": 0.95},
        input_shapes="16,32;32,64",
        input_dtypes="DT_BF16;DT_BF16",
        output_shapes="16,64",
        output_dtypes="DT_BF16",
        block_num=32,
        physical_owners=32,
        complete_in_window=True,
        native_type="MatMulV2",
    )
    for _ in range(1_000):
        noop.add_record(sample)
    assert noop.conditions == {}

    bounded = MatrixSupplyAccumulator(
        physical_owners=32, max_conditions=2, max_samples_per_condition=4
    )
    for _ in range(10):
        bounded.add_record(sample)
    assert len(bounded.conditions) == 1
    assert bounded.capped_samples == 6


def test_physical_capacity_must_be_declared_and_non_saturated_full_rejected() -> None:
    report = analyze_profile(FIXTURE, full_range=True, source="csv", top_n=2)
    supply = report["enrichment"]["pmu_observations"]["measured_supply"]
    assert supply["status"] == "not_available"
    assert supply["pair"] is None
    assert "measured_supply_physical_owners_not_declared" in {
        item["code"] for item in supply["limitations"]
    }

    pair = _pair(_report(FIXTURE, R64))
    full = dict(pair["saturated"], mac_ratio=0.4)
    tail = dict(pair["underfilled"])
    with pytest.raises(ValueError, match="measured_supply_saturated_mac_ratio_below_threshold"):
        build_dual_load_service(full, tail, physical_owners=32)


def test_r35_and_bare_csv_keep_generic_measurements_without_r64_issue_rule() -> None:
    r35_supply = _report(FIXTURE, R35)["enrichment"]["pmu_observations"]["measured_supply"]
    assert r35_supply["status"] == "not_available"
    assert r35_supply["pair"] is None
    assert r35_supply["source_identity"]["source_scope"] == "r35"
    assert r35_supply["candidate_conditions"] > 0
    assert all(item.get("issue_rule") is None for item in r35_supply["candidates"])
    assert all(
        item.get("issued_flops") == item.get("logical_flops")
        for item in r35_supply["candidates"]
        if item.get("status") == "measured"
    )

    bare_supply = _report(FIXTURE)["enrichment"]["pmu_observations"]["measured_supply"]
    assert bare_supply["status"] == "not_available"
    assert bare_supply["pair"] is None
    assert bare_supply["source_identity"]["source_scope"] == "absent"
    assert bare_supply["candidate_conditions"] > 0
    assert all(item.get("issue_rule") is None for item in bare_supply["candidates"])


def test_status_json_boundary_conflict_and_readonly_tmpdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Works even when TMPDIR/TEMP/TMP point to a non-existent / unwritable path!
    for env_key in ("TMPDIR", "TEMP", "TMP"):
        monkeypatch.setenv(env_key, str(tmp_path / "no_writable_tmp_dir"))

    # 1. Valid parent status.json inside capture hierarchy resolves R64 automatically.
    valid_case = tmp_path / "valid_case"
    rank_dir = valid_case / "pf_1k_c1" / "rank_0"
    rank_dir.mkdir(parents=True)
    shutil.copy2(FIXTURE, rank_dir / "kernel_details.csv")
    (valid_case / "status.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "prepare": [{"node": "10.0.0.1", "created": True, "image_id": R64}],
            }
        ),
        encoding="utf-8",
    )
    valid_report = analyze_profile(rank_dir, full_range=True, source="csv", aic_count=32)
    assert valid_report["enrichment"]["deployment_source"]["source_scope"] == "r64"
    assert (
        valid_report["enrichment"]["pmu_observations"]["measured_supply"]["status"]
        == "measured_pair"
    )

    # 2. Conflicting explicit --deployment-image-id vs status.json is NEVER silently overridden!
    conflict = analyze_profile(
        rank_dir, full_range=True, source="csv", aic_count=32, deployment_image_id=R35
    )
    assert conflict["enrichment"]["deployment_source"]["source_scope"] == "conflicting"
    assert "conflicting_deployment_image_identity" in {
        item["code"] for item in conflict["limitations"]
    }
    assert conflict["enrichment"]["pmu_observations"]["measured_supply"]["pair"] is None

    # 3. Unrelated outer directory status.json does NOT contaminate an anonymous copied bundle!
    outer = tmp_path / "archive_root"
    copied = outer / "copied_bundle"
    copied.mkdir(parents=True)
    (outer / "status.json").write_text(
        json.dumps({"prepare": [{"created": True, "image_id": R64}]}),
        encoding="utf-8",
    )
    shutil.copy2(FIXTURE, copied / "kernel_details.csv")
    copied_report = analyze_profile(copied, full_range=True, source="csv", aic_count=32)
    assert copied_report["enrichment"]["deployment_source"]["source_scope"] == "absent"

    # 4. Malformed status.json records invalid_capture_status limitation.
    bad_case = tmp_path / "bad_case"
    bad_rank = bad_case / "rank_0"
    bad_rank.mkdir(parents=True)
    shutil.copy2(FIXTURE, bad_rank / "kernel_details.csv")
    (bad_case / "status.json").write_text("{corrupt", encoding="utf-8")
    bad_report = analyze_profile(bad_rank, full_range=True, source="csv", aic_count=32)
    assert "invalid_capture_status" in {item["code"] for item in bad_report["limitations"]}

    # 5. Conflicting prepare digests record ambiguous_capture_prepare limitation.
    amb_case = tmp_path / "amb_case"
    amb_rank = amb_case / "rank_0"
    amb_rank.mkdir(parents=True)
    shutil.copy2(FIXTURE, amb_rank / "kernel_details.csv")
    (amb_case / "status.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "prepare": [
                    {"node": "10.0.0.1", "created": True, "image_id": R64},
                    {"node": "10.0.0.2", "created": True, "image_id": R35},
                ],
            }
        ),
        encoding="utf-8",
    )
    amb_report = analyze_profile(amb_rank, full_range=True, source="csv", aic_count=32)
    assert "ambiguous_capture_prepare" in {item["code"] for item in amb_report["limitations"]}


def test_cli_analyze_flags_emit_measured_supply(tmp_path: Path) -> None:
    out_path = tmp_path / "c7.json"
    rc = cli_main(
        [
            "analyze",
            "--root",
            str(FIXTURE),
            "--full-range",
            "--source",
            "csv",
            "--aic-count",
            "32",
            "--deployment-image-id",
            R64,
            "--output",
            str(out_path),
        ]
    )
    assert rc == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert (
        payload["enrichment"]["pmu_observations"]["measured_supply"]["status"]
        == "measured_pair"
    )


def test_non_matrix_op_dtype_aliases_and_tilde_root_status_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 1. Non-matrix operator (e.g. SwiGLU) is never misclassified as GEMM 2*M*K*N FLOPs!
    non_matrix = derive_measured_supply(
        {"aic_mac_time": 8.0, "aic_mac_ratio": 0.8},
        native_type="SwiGLU",
        native_call="aclnnSwiGlu",
        input_shapes="64,2048;2048,6144",
        output_shapes="64,6144",
        input_dtypes="DT_BF16;DT_BF16",
        output_dtypes="DT_BF16",
        duration_ns=10_000,
        block_num=32,
        physical_owners=32,
        complete_in_window=True,
    )
    assert non_matrix["status"] == "not_applicable"
    assert non_matrix["logical_flops"] is None
    assert non_matrix["issued_flops"] is None
    assert "not_matrix_operator" in non_matrix["missing"]

    # 2. DT_FLOAT / FLOAT aliases normalize cleanly to fp32 matching mindie-sim v0.9.11.
    fp32_mm = derive_measured_supply(
        {"aic_mac_time": 8.0, "aic_mac_ratio": 0.8},
        native_type="MatMul",
        native_call="aclnnMm",
        input_shapes="64,256;256,512",
        output_shapes="64,512",
        input_dtypes="DT_FLOAT;FLOAT",
        output_dtypes="DT_FLOAT",
        duration_ns=10_000,
        block_num=32,
        physical_owners=32,
        complete_in_window=True,
    )
    assert fp32_mm["status"] == "measured"
    assert fp32_mm["dtype"] == "fp32"
    assert fp32_mm["output_dtype"] == "fp32"

    # 3. Tilde (~) root preserves status.json deployment provenance identically to absolute path.
    fake_home = tmp_path / "isolated_home"
    bundle = fake_home / "cap_bundle"
    rank_dir = bundle / "rank_0"
    rank_dir.mkdir(parents=True)
    shutil.copy2(FIXTURE, rank_dir / "kernel_details.csv")
    (bundle / "status.json").write_text(
        json.dumps({"prepare": [{"created": True, "image_id": R64}]}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    tilde_report = analyze_profile(
        "~/cap_bundle/rank_0", full_range=True, source="csv", aic_count=32
    )
    assert tilde_report["enrichment"]["deployment_source"]["source_scope"] == "r64"
    assert (
        tilde_report["enrichment"]["pmu_observations"]["measured_supply"]["status"]
        == "measured_pair"
    )

    # 4. Missing weight shape or BF16 weight dtype NEVER certifies R64 16x tile issue rule!
    from mindie_profiler.measured_supply import deployment_source_identity
    from mindie_profiler.pmu_derivation import summarize_measured_supply

    r64_id = deployment_source_identity(R64, basis="cli_flag")
    missing_weight = derive_measured_supply(
        {"aic_mac_time": 12947.0, "aic_mac_ratio": 0.376},
        native_type="QuantBatchMatmulV3",
        native_call="aclnnQuantMatmulWeightNz_QuantBatchMatmulV3_QuantBatchMatmulV3",
        input_shapes="1,16384",
        input_dtypes="DT_FLOAT8_E4M3FN",
        input_formats="ND;FRACTAL_NZ;ND;ND",
        output_shapes="1,6144",
        output_dtypes="DT_BF16",
        output_formats="ND",
        duration_ns=34_665,
        block_num=24,
        physical_owners=32,
        complete_in_window=True,
        source_identity=r64_id,
    )
    assert missing_weight["status"] == "unknown"
    assert missing_weight["issue"] is None
    assert "weight_matrix_shape_not_parsed" in missing_weight["missing"]

    bf16_weight = derive_measured_supply(
        {"aic_mac_time": 12947.0, "aic_mac_ratio": 0.376},
        native_type="QuantBatchMatmulV3",
        native_call="aclnnQuantMatmulWeightNz_QuantBatchMatmulV3_QuantBatchMatmulV3",
        input_shapes="1,16384;192,1024,16,32;256,6144,2;1,256,2",
        input_dtypes="DT_FLOAT8_E4M3FN;DT_BF16;DT_FLOAT8_E8M0;DT_FLOAT8_E8M0",
        input_formats="ND;FRACTAL_NZ;ND;ND",
        output_shapes="1,6144",
        output_dtypes="DT_BF16",
        output_formats="ND",
        duration_ns=34_665,
        block_num=24,
        physical_owners=32,
        complete_in_window=True,
        source_identity=r64_id,
    )
    assert bf16_weight["issue"] is None
    assert bf16_weight["issued_flops"] == bf16_weight["logical_flops"] == 201_326_592

    # 5. Invalid popular lower-owner candidate (mac_ratio=0.95) does NOT suppress a valid pair!
    base_events = [
        item["measured_supply"]
        for item in _report(FIXTURE, R64)["enrichment"]["pmu_observations"]["bound_events"]
    ]
    bad_popular_tail = {
        **base_events[0],
        "m": 2,
        "logical_flops": 402_653_184,
        "issued_flops": 3_221_225_472,
        "mac_ratio": 0.95,
        "pipe_ratios": {**base_events[0]["pipe_ratios"], "aic_mac_ratio": 0.95},
        "saturated": False,
    }
    resilient = summarize_measured_supply(
        [*base_events, bad_popular_tail, bad_popular_tail],
        physical_owners=32,
        source_identity=r64_id,
    )
    assert resilient["status"] == "measured_pair"
    assert resilient["pair"] is not None

    # 6. Public build_dual_load_service enforces complete_in_window exclusion directly!
    valid_pair = resilient["pair"]
    clipped_sat = {**valid_pair["saturated"], "complete_in_window": False}
    clipped_tail = {**valid_pair["underfilled"], "complete_in_window": False}
    with pytest.raises(ValueError, match="measured_supply_saturated_incomplete_in_window"):
        build_dual_load_service(clipped_sat, valid_pair["underfilled"], physical_owners=32)
    with pytest.raises(ValueError, match="measured_supply_underfilled_incomplete_in_window"):
        build_dual_load_service(valid_pair["saturated"], clipped_tail, physical_owners=32)


def _qbmm_evidence(**overrides):
    from mindie_profiler.measured_supply_rules import ISSUE_LAWS

    law = ISSUE_LAWS[0]
    return {
        "kernel_source_sha256": law["kernel_source"]["sha256"],
        "kernel_revision": law["kernel_source"]["revision"],
        "wrapper_source_sha256": law["wrapper_source"]["sha256"],
        "wrapper_revision": law["wrapper_source"]["revision"],
        "native_type": law["native_type"],
        **overrides,
    }


def _qbmm_supply(source_identity, *, m: int = 1):
    return derive_measured_supply(
        {"aic_mac_time": 1000.0, "aic_mac_ratio": 0.95},
        input_shapes=f"{m},32;2,1,16,16;1,16,1;1,16,1",
        input_dtypes="DT_FLOAT8_E4M3FN;DT_FLOAT8_E4M3FN;DT_FLOAT8_E8M0;DT_FLOAT8_E8M0",
        input_formats="ND;FRACTAL_NZ;ND;ND",
        output_shapes=f"{m},16",
        output_dtypes="DT_BF16",
        output_formats="ND",
        native_type="QuantBatchMatmulV3",
        block_num=32,
        physical_owners=32,
        complete_in_window=True,
        source_identity=source_identity,
    )


def test_issue_law_certifies_from_implementation_evidence_without_digest() -> None:
    from mindie_profiler.measured_supply import deployment_source_identity
    from mindie_profiler.measured_supply_rules import ISSUE_LAWS, verified_implementation

    law = ISSUE_LAWS[0]
    source = deployment_source_identity(
        None, basis="implementation", implementation=_qbmm_evidence()
    )
    assert source["source_scope"] == "r64"
    assert source["implementation_verified"] is True
    assert source["law_id"] == law["law_id"]
    nested = verified_implementation(
        {
            "native_type": law["native_type"],
            "kernel_source": law["kernel_source"],
            "wrapper_source": law["wrapper_source"],
        }
    )
    assert nested is not None and nested["implementation_verified"] is True
    record = _qbmm_supply(source)
    assert record["status"] == "measured"
    assert record["work_basis"] == "issued_2_align_m_k_n_flops"
    assert record["issue"] is not None and record["issued_flops"] is not None
    assert record["issued_flops"] == 16 * record["logical_flops"]


def test_mismatching_implementation_keeps_logical_work_basis() -> None:
    from mindie_profiler.measured_supply import deployment_source_identity

    source = deployment_source_identity(
        None,
        basis="implementation",
        implementation=_qbmm_evidence(wrapper_source_sha256="0" * 64),
    )
    assert source["implementation_verified"] is False
    record = _qbmm_supply(source)
    assert record["issue"] is None
    assert record["work_basis"] == "logical_2_m_n_k_flops_no_issue_rule"
    assert record["issued_flops"] == record["logical_flops"] == 1024


def test_legacy_digest_only_certifies_and_unknown_digest_is_unpinned() -> None:
    from mindie_profiler.measured_supply import deployment_source_identity

    legacy = deployment_source_identity(R64, basis="cli_flag")
    assert legacy["source_scope"] == "r64"
    assert legacy["implementation_verified"] is False
    assert legacy["law_id"] is not None
    assert _qbmm_supply(legacy)["issue"] is not None
    unknown = deployment_source_identity("sha256:" + "0" * 64, implementation=None)
    assert unknown["source_scope"] == "unpinned"
    assert unknown["image_digest"] == "0" * 64
    foreign = deployment_source_identity(
        "sha256:" + "a" * 64, implementation=_qbmm_evidence()
    )
    assert foreign["source_scope"] == "r64"
    assert _qbmm_supply(foreign)["issue"] is not None


def test_conflicting_digest_and_implementation_never_certifies() -> None:
    from mindie_profiler.measured_supply import deployment_source_identity

    # Matching implementation evidence wins the scope label, but a digest pinned
    # to another known scope still blocks issued-work certification.
    wrong_image = deployment_source_identity(
        R35, basis="implementation", implementation=_qbmm_evidence()
    )
    assert wrong_image["source_scope"] == "r64"
    assert wrong_image["implementation_verified"] is True
    assert _qbmm_supply(wrong_image)["issue"] is None

    bad_impl = deployment_source_identity(
        R64,
        basis="implementation",
        implementation=_qbmm_evidence(wrapper_source_sha256="f" * 64),
    )
    assert bad_impl["source_scope"] == "conflicting"
    assert _qbmm_supply(bad_impl)["issue"] is None


def test_verified_identity_carries_hashes_and_spoofed_flag_is_not_certified() -> None:
    from mindie_profiler.measured_supply import deployment_source_identity
    from mindie_profiler.measured_supply_rules import ISSUE_LAWS, certify_issue_law

    law = ISSUE_LAWS[0]
    source = deployment_source_identity(
        None, basis="implementation", implementation=_qbmm_evidence())
    assert set(source) >= {
        "kernel_source_sha256", "kernel_revision", "wrapper_source_sha256",
        "wrapper_revision", "native_type"}
    assert source["kernel_source_sha256"] == law["kernel_source"]["sha256"]
    assert source["wrapper_source_sha256"] == law["wrapper_source"]["sha256"]
    assert source["native_type"] == law["native_type"]

    def technical(source_identity):
        return certify_issue_law(
            "QuantBatchMatmulV3", "fp8_e4m3", "bf16", 16, 32,
            input_shapes_slots=((16, 32), (2, 1, 16, 16), (1, 16, 16),
                                (1, 16, 16)),
            input_dtypes_slots=("fp8_e4m3", "fp8_e4m3", "fp8_e8m0", "fp8_e8m0"),
            input_formats="ND;FRACTAL_NZ;ND;ND", output_formats="ND",
            source=source_identity)

    assert technical(source) is not None
    spoof = {"implementation_verified": True, "law_id": law["law_id"],
             "image_digest": None}
    assert technical(spoof) is None
    tampered = dict(source, wrapper_source_sha256="0" * 64)
    assert technical(tampered) is None


def test_cross_image_dual_load_pairs_on_canonical_law_identity() -> None:
    pair = _pair(_report(FIXTURE, R64))
    saturated = dict(pair["saturated"])
    underfilled = dict(pair["underfilled"])
    saturated["issue"] = {
        **saturated["issue"], "deployment_image_id": "a" * 64,
        "source_scope": "r64", "source_basis": "first_image"}
    underfilled["issue"] = {
        **underfilled["issue"], "deployment_image_id": "b" * 64,
        "source_scope": "r64", "source_basis": "second_image"}
    service = build_dual_load_service(saturated, underfilled, physical_owners=32)
    assert service["schema_version"] == DUAL_LOAD_SCHEMA
    assert service["service_ratio"]["underfilled_over_saturated"] > 0
    mismatched = dict(underfilled)
    mismatched["issue"] = {**underfilled["issue"], "m_alignment": 8}
    with pytest.raises(ValueError, match="measured_supply_issue_rule_mismatch"):
        build_dual_load_service(saturated, mismatched, physical_owners=32)


def test_incompatible_scale_and_weight_descriptors_never_certify_issue_law() -> None:
    from mindie_profiler.measured_supply import deployment_source_identity
    from mindie_profiler.measured_supply_rules import certify_issue_law

    legacy = deployment_source_identity(R64, basis="cli_flag")

    def supply(shapes: str) -> dict:
        return derive_measured_supply(
            {"aic_mac_time": 1000.0, "aic_mac_ratio": 0.95},
            input_shapes=shapes,
            input_dtypes=(
                "DT_FLOAT8_E4M3FN;DT_FLOAT8_E4M3FN;"
                "DT_FLOAT8_E8M0;DT_FLOAT8_E8M0"),
            input_formats="ND;FRACTAL_NZ;ND;ND",
            output_shapes="1,16",
            output_dtypes="DT_BF16",
            output_formats="ND",
            native_type="QuantBatchMatmulV3",
            block_num=32,
            physical_owners=32,
            complete_in_window=True,
            source_identity=legacy,
        )

    valid = supply("1,32;2,1,16,16;1,16,1;1,16,1")
    assert valid["issue"] is not None
    assert valid["issued_flops"] == 16 * valid["logical_flops"]

    bad_scales = supply("1,32;2,1,16,16;999,999;999,999")
    assert bad_scales["issue"] is None
    assert bad_scales["work_basis"] == "logical_2_m_n_k_flops_no_issue_rule"
    assert bad_scales["logical_flops"] == bad_scales["issued_flops"] == 1024

    bad_weight = certify_issue_law(
        "QuantBatchMatmulV3", "fp8_e4m3", "bf16", 16, 32,
        input_shapes_slots=((1, 32), (2, 1, 16, 17), (1, 16, 1), (1, 16, 1)),
        input_dtypes_slots=("fp8_e4m3", "fp8_e4m3", "fp8_e8m0", "fp8_e8m0"),
        input_formats="ND;FRACTAL_NZ;ND;ND", output_formats="ND", source=legacy)
    assert bad_weight is None

    bad_scale_blocks = certify_issue_law(
        "QuantBatchMatmulV3", "fp8_e4m3", "bf16", 16, 64,
        input_shapes_slots=((1, 64), (4, 1, 16, 16), (16, 3), (1, 2)),
        input_dtypes_slots=("fp8_e4m3", "fp8_e4m3", "fp8_e8m0", "fp8_e8m0"),
        input_formats="ND;FRACTAL_NZ;ND;ND", output_formats="ND", source=legacy)
    assert bad_scale_blocks is None


def test_mixed_digest_and_implementation_evidence_pair_on_law_identity() -> None:
    from mindie_profiler.measured_supply import deployment_source_identity
    from mindie_profiler.measured_supply_rules import certify_issue_law

    pair = _pair(_report(FIXTURE, R64))
    saturated = dict(pair["saturated"])
    underfilled = dict(pair["underfilled"])
    assert saturated["issue"]["implementation_verified"] is False
    assert underfilled["issue"]["implementation_verified"] is False

    source = deployment_source_identity(
        None, basis="implementation", implementation=_qbmm_evidence())
    verified_issue = certify_issue_law(
        "QuantBatchMatmulV3", "fp8_e4m3", "bf16", 6144, 16384,
        input_shapes_slots=(
            (1, 16384), (192, 1024, 16, 32), (256, 6144, 2), (1, 256, 2)),
        input_dtypes_slots=("fp8_e4m3", "fp8_e4m3", "fp8_e8m0", "fp8_e8m0"),
        input_formats="ND;FRACTAL_NZ;ND;ND", output_formats="ND", source=source)
    assert verified_issue is not None
    assert verified_issue["implementation_verified"] is True
    underfilled["issue"] = verified_issue

    mixed = build_dual_load_service(saturated, underfilled, physical_owners=32)
    assert mixed["service_ratio"] == pair["service_ratio"]

    tampered = dict(underfilled)
    tampered["issue"] = {**verified_issue, "m_alignment": 8}
    with pytest.raises(ValueError, match="measured_supply_issue_rule_mismatch"):
        build_dual_load_service(saturated, tampered, physical_owners=32)


def test_analyze_profile_accepts_implementation_evidence_from_argument_and_status(
    tmp_path: Path,
) -> None:
    rank_dir = tmp_path / "impl_rank"
    rank_dir.mkdir()
    shutil.copy2(FIXTURE, rank_dir / "kernel_details.csv")
    report = analyze_profile(
        rank_dir, full_range=True, source="csv", aic_count=32,
        implementation_evidence=_qbmm_evidence())
    deployment = report["enrichment"]["deployment_source"]
    assert deployment["source_scope"] == "r64"
    assert deployment["implementation_verified"] is True
    assert (
        report["enrichment"]["pmu_observations"]["measured_supply"]["status"]
        == "measured_pair"
    )

    bundle = tmp_path / "impl_bundle"
    status_rank = bundle / "rank_0"
    status_rank.mkdir(parents=True)
    shutil.copy2(FIXTURE, status_rank / "kernel_details.csv")
    (bundle / "status.json").write_text(
        json.dumps({
            "prepare": [{"created": True, "image_id": R64}],
            "implementation": _qbmm_evidence(),
        }),
        encoding="utf-8",
    )
    status_report = analyze_profile(
        status_rank, full_range=True, source="csv", aic_count=32)
    status_deployment = status_report["enrichment"]["deployment_source"]
    assert status_deployment["source_scope"] == "r64"
    assert status_deployment["implementation_verified"] is True
    assert (
        status_report["enrichment"]["pmu_observations"]["measured_supply"]["status"]
        == "measured_pair"
    )


def test_doubled_weight_scale_k_blocks_does_not_certify_issue_law() -> None:
    from mindie_profiler.measured_supply import deployment_source_identity

    source = deployment_source_identity(
        None, basis="implementation", implementation=_qbmm_evidence()
    )
    doubled = derive_measured_supply(
        {"aic_mac_time": 12947.0, "aic_mac_ratio": 0.376},
        native_type="QuantBatchMatmulV3",
        native_call="aclnnQuantMatmulWeightNz_QuantBatchMatmulV3_QuantBatchMatmulV3",
        input_shapes="1,16384;192,1024,16,32;512,6144,2;1,256,2",
        input_dtypes="DT_FLOAT8_E4M3FN;DT_FLOAT8_E4M3FN;DT_FLOAT8_E8M0;DT_FLOAT8_E8M0",
        input_formats="ND;FRACTAL_NZ;ND;ND",
        output_shapes="1,6144",
        output_dtypes="DT_BF16",
        output_formats="ND",
        duration_ns=34_665,
        block_num=24,
        physical_owners=32,
        complete_in_window=True,
        source_identity=source,
    )
    assert doubled["issue"] is None
    assert doubled["issued_flops"] == doubled["logical_flops"] == 201_326_592
