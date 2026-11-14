"""R64 sparse FlashAttention MTE1 critical-owner service math and scope guards.

[Role]
  Verify ``sparse_mte1_bytes``, ``summarize_sparse_mte1``, ``analyze_profile``,
  and CLI ``--sparse-geometry`` derive critical-owner MTE1 service rates from
  provenance-backed real R64 ``KvQuantSparseFlashAttention`` Golden Captures
  only when certified R64 source identity and full Q/KV/output tensor signatures
  match the declared ``prefill`` / ``dynamic`` geometry.

[Invariants]
  * Critical-owner QK/PV L1->L0A/L0B closed-form byte math matches exact causal
    tile partitioning (``q_len=1024 -> 93,782,016``, ``q_len=2048 -> 373,948,416``)
    and executes in ``O(q_len)`` time even for ``q_len=32768``.
  * Mismatched Q head/dim (``[1024,8,128]`` vs ``g=64,dq=576``), output dim, or
    KV block size emit ``sparse_mte1_tensor_geometry_mismatch`` and ``[]``.
  * Bare captures, R35 captures, decode/static geometries, and malformed
    ``sparse_geometry`` are guarded with explicit limitations or ``ProfilerUsageError``.

[Timeouts & Locks]
  Closed-form arithmetic and small local Golden Capture CSV/JSON files; zero locks.

[Side-Effect Policy]
  Reads ``tests/fixtures/r64_sfa_service/*`` read-only; writes only inside
  pytest ``tmp_path``.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pytest

from mindie_profiler.__main__ import main as cli_main
from mindie_profiler.analyze import analyze_profile
from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.pmu_derivation import (
    R35_IMAGE_SHA,
    R64_IMAGE_SHA,
    RESOURCE_SERVICE_SCHEMA,
    sparse_mte1_bytes,
)

FIXTURES = Path(__file__).parent / "fixtures" / "r64_sfa_service"
REAL_SFA_CSV = FIXTURES / "kernel_details.csv"
PROVENANCE = FIXTURES / "provenance.json"
TRAIN_GEOMETRY = FIXTURES / "train_geometry.json"
DC_GEOMETRY = FIXTURES / "dc_geometry.json"
R64 = f"sha256:{R64_IMAGE_SHA}"
R35 = f"sha256:{R35_IMAGE_SHA}"


def _write_sfa_csv(
    path: Path,
    *,
    q_shape: str = "1024,64,576",
    k_shape: str = "4080,128,1,656",
    out_shape: str = "1024,64,512",
    out_dtype: str = "DT_BF16",
    op_state: str = "dynamic",
) -> Path:
    header = (
        "Device_id,Model ID,Task ID,Stream ID,Name,Type,OP State,Accelerator Core,"
        "Start Time(us),Duration(us),Wait Time(us),Block Num,Mix Block Num,"
        "Input Shapes,Input Data Types,Input Formats,Output Shapes,Output Data Types,Output Formats,"
        "aicore_time(us),aic_total_cycles,aic_mte1_time(us),aic_mte1_ratio\n"
    )
    rows = [
        f'0,1,10,4,KvQuantSparseFlashAttention,KvQuantSparseFlashAttention,{op_state},MIX_AIC,'
        f'1000.0,802.0,0.0,32,64,"{q_shape};{k_shape}",DT_BF16;DT_FLOAT8_E4M3FN,ND;ND,'
        f'"{out_shape}",{out_dtype},ND,800.0,21900000,270.0,0.336\n',
        f'0,1,11,4,KvQuantSparseFlashAttention,KvQuantSparseFlashAttention,{op_state},MIX_AIC,'
        f'2000.0,804.0,0.0,32,64,"{q_shape};{k_shape}",DT_BF16;DT_FLOAT8_E4M3FN,ND;ND,'
        f'"{out_shape}",{out_dtype},ND,801.0,21950000,270.595,0.335\n',
    ]
    path.write_text(header + "".join(rows), encoding="utf-8")
    return path


def test_sparse_mte1_critical_owner_closed_form_math_and_speed() -> None:
    q1k = sparse_mte1_bytes(
        q_len=1024, context=0, kv_len=1024, causal=True, owners=32, g=64, dq=576, dv=512, s2_tile=128
    )
    assert q1k["critical_qk_pv_bytes"] == 93_782_016
    assert q1k["total_qk_pv_bytes"] == 1_566_572_544
    assert q1k["critical_owner_index"] == 31

    q2k = sparse_mte1_bytes(
        q_len=2048, context=0, kv_len=2048, causal=True, owners=32, g=64, dq=576, dv=512, s2_tile=128
    )
    assert q2k["critical_qk_pv_bytes"] == 373_948_416

    # Non-multiple remainder tile check (selected=130 -> 1 full 128 tile + 1 aligned-to-16 tail tile).
    odd = sparse_mte1_bytes(
        q_len=1, context=129, kv_len=130, causal=False, owners=1, g=64, dq=576, dv=512, s2_tile=128
    )
    expected_full = (2 * 64 * 576 + 2 * 128 * 576) + (2 * 64 * 128 + 2 * 512 * 128)
    expected_tail = (2 * 64 * 576 + 2 * 16 * 576) + (2 * 64 * 16 + 2 * 512 * 16)
    assert odd["critical_qk_pv_bytes"] == expected_full + expected_tail
    assert odd["critical_tiles"] == 2

    # Closed-form O(q_len) arithmetic completes in well under 0.1s even at q_len=32768, s2_tile=1.
    t0 = time.perf_counter()
    big = sparse_mte1_bytes(q_len=32_768, context=0, kv_len=32_768, owners=32, s2_tile=1)
    assert (time.perf_counter() - t0) < 0.25
    assert big["critical_tiles"] > 0


def test_real_r64_sfa_golden_capture_emits_verified_mte1_service() -> None:
    meta = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    assert meta["not_fabricated"] is True
    actual_sha = hashlib.sha256(REAL_SFA_CSV.read_bytes()).hexdigest()
    assert actual_sha == meta["fixture_csv_sha256"]

    geometry = json.loads(TRAIN_GEOMETRY.read_text(encoding="utf-8"))
    report = analyze_profile(
        REAL_SFA_CSV,
        full_range=True,
        source="csv",
        hash_sources=True,
        aic_count=32,
        deployment_image_id=R64,
        sparse_geometry=geometry,
    )
    supply = report["enrichment"]["pmu_observations"]["measured_supply"]
    assert supply["source_identity"]["source_scope"] == "r64"
    records = supply["resource_services"]
    assert len(records) == 1
    record = records[0]
    assert record["schema_version"] == RESOURCE_SERVICE_SCHEMA
    assert record["resource"] == "mte1"
    assert record["native_type"] == "KvQuantSparseFlashAttention"
    assert record["hardware"] == "Ascend950DT_9582"
    assert record["owners"] == 32 and record["mix_block_num"] == 64
    assert record["measured_q_tokens"] == 1024
    assert record["measured_critical_bytes"] == 93_782_016
    assert record["measured_total_bytes"] == 1_566_572_544
    # Static decode row (q=1) is excluded; 3 dynamic q=1024 prefill rows have median 269.564 us!
    assert record["event_count"] == 3
    assert record["median_mte1_us"] == pytest.approx(269.564, rel=1e-9)
    assert record["rate_bytes_per_s"] == pytest.approx(93_782_016 / 269.564e-6, rel=1e-9)

    bare = analyze_profile(
        REAL_SFA_CSV, full_range=True, source="csv", aic_count=32, deployment_image_id=R64
    )
    assert bare["enrichment"]["pmu_observations"]["measured_supply"]["resource_services"] == []


def test_tensor_geometry_mismatch_rejected_explicitly(tmp_path: Path) -> None:
    train_geom = json.loads(TRAIN_GEOMETRY.read_text(encoding="utf-8"))
    for case_name, kwargs in (
        ("wrong_q_heads_dim", {"q_shape": "1024,8,128"}),
        ("wrong_out_dim", {"out_shape": "1024,64,256"}),
        ("wrong_kv_block_size", {"k_shape": "4080,64,1,656"}),
        ("wrong_kv_heads_and_packed_dim", {"k_shape": "4080,128,2,123"}),
        ("insufficient_kv_blocks", {"k_shape": "4,128,1,656"}),
        ("wrong_out_dtype", {"out_dtype": "DT_FLOAT"}),
    ):
        bad_csv = _write_sfa_csv(tmp_path / f"{case_name}.csv", **kwargs)
        supply = analyze_profile(
            bad_csv,
            full_range=True,
            source="csv",
            aic_count=32,
            deployment_image_id=R64,
            sparse_geometry=train_geom,
        )["enrichment"]["pmu_observations"]["measured_supply"]
        assert supply["resource_services"] == [], case_name
        assert "sparse_mte1_tensor_geometry_mismatch" in {
            item["code"] for item in supply["limitations"]
        }, case_name


def test_r35_decode_unmatched_and_malformed_geometry_guards(tmp_path: Path) -> None:
    train_geom = json.loads(TRAIN_GEOMETRY.read_text(encoding="utf-8"))
    dc_geom = json.loads(DC_GEOMETRY.read_text(encoding="utf-8"))

    # R35 same shape -> rejected immediately with sparse_mte1_source_not_r64.
    r35 = analyze_profile(
        REAL_SFA_CSV,
        full_range=True,
        source="csv",
        aic_count=32,
        deployment_image_id=R35,
        sparse_geometry=train_geom,
    )["enrichment"]["pmu_observations"]["measured_supply"]
    assert r35["resource_services"] == []
    assert "sparse_mte1_source_not_r64" in {item["code"] for item in r35["limitations"]}

    # Invalid suffix appended to R64 digest -> rejected as unpinned, never certified R64!
    bogus_digest = analyze_profile(
        REAL_SFA_CSV,
        full_range=True,
        source="csv",
        aic_count=32,
        deployment_image_id=f"{R64}INVALID",
        sparse_geometry=train_geom,
    )["enrichment"]["pmu_observations"]["measured_supply"]
    assert bogus_digest["source_identity"]["source_scope"] == "unpinned"
    assert bogus_digest["resource_services"] == []
    assert "sparse_mte1_source_not_r64" in {item["code"] for item in bogus_digest["limitations"]}

    # Multi-rank captures preserve per-rank medians and provenance without cross-rank mixing!
    multi_root = tmp_path / "two_ranks"
    (multi_root / "rank_0").mkdir(parents=True)
    (multi_root / "rank_1").mkdir(parents=True)
    r0_csv = multi_root / "rank_0" / "kernel_details.csv"
    r1_csv = multi_root / "rank_1" / "kernel_details.csv"
    raw_csv_text = REAL_SFA_CSV.read_text(encoding="utf-8")
    r0_csv.write_text(raw_csv_text, encoding="utf-8")
    r1_csv.write_text(
        raw_csv_text.replace(",269.564,", ",539.128,")
        .replace(",271.055,", ",542.110,")
        .replace(",269.245,", ",538.490,"),
        encoding="utf-8",
    )
    multi_supply = analyze_profile(
        multi_root,
        full_range=True,
        source="csv",
        hash_sources=True,
        aic_count=32,
        deployment_image_id=R64,
        sparse_geometry=train_geom,
    )["enrichment"]["pmu_observations"]["measured_supply"]
    by_rank = {rec["rank_id"]: rec for rec in multi_supply["resource_services"]}
    assert set(by_rank) == {"rank_0", "rank_1"}
    assert by_rank["rank_0"]["median_mte1_us"] == pytest.approx(269.564, rel=1e-9)
    assert by_rank["rank_1"]["median_mte1_us"] == pytest.approx(539.128, rel=1e-9)
    assert Path(by_rank["rank_0"]["source"]).resolve() == r0_csv.resolve()
    assert Path(by_rank["rank_1"]["source"]).resolve() == r1_csv.resolve()
    assert by_rank["rank_0"]["source_sha256"] != by_rank["rank_1"]["source_sha256"]

    # Decode / static geometry -> rejected with sparse_mte1_not_prefill_dynamic.
    dc = analyze_profile(
        REAL_SFA_CSV,
        full_range=True,
        source="csv",
        aic_count=32,
        deployment_image_id=R64,
        sparse_geometry=dc_geom,
    )["enrichment"]["pmu_observations"]["measured_supply"]
    assert dc["resource_services"] == []
    assert "sparse_mte1_not_prefill_dynamic" in {item["code"] for item in dc["limitations"]}

    # Unmatched q_len -> rejected with sparse_mte1_no_matching_events.
    unmatched = analyze_profile(
        REAL_SFA_CSV,
        full_range=True,
        source="csv",
        aic_count=32,
        deployment_image_id=R64,
        sparse_geometry={**train_geom, "q_len": 2048, "kv_len": 2048},
    )["enrichment"]["pmu_observations"]["measured_supply"]
    assert unmatched["resource_services"] == []
    assert "sparse_mte1_no_matching_events" in {item["code"] for item in unmatched["limitations"]}

    # Malformed or absurdly huge sparse_geometry -> raises ProfilerUsageError.
    for bad_geom in (
        {**train_geom, "q_len": "not-an-int"},
        {**train_geom, "q_len": 10_000_000, "kv_len": 10_000_000},
    ):
        with pytest.raises(ProfilerUsageError, match="sparse_geometry"):
            analyze_profile(
                REAL_SFA_CSV,
                full_range=True,
                source="csv",
                aic_count=32,
                deployment_image_id=R64,
                sparse_geometry=bad_geom,
            )

    # CLI --sparse-geometry end-to-end check on real R64 Golden Capture CSV.
    out_path = tmp_path / "sparse_c7.json"
    rc = cli_main(
        [
            "analyze",
            "--root",
            str(REAL_SFA_CSV),
            "--full-range",
            "--source",
            "csv",
            "--aic-count",
            "32",
            "--deployment-image-id",
            R64,
            "--sparse-geometry",
            str(TRAIN_GEOMETRY),
            "--output",
            str(out_path),
        ]
    )
    assert rc == 0
    cli_payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert (
        len(
            cli_payload["enrichment"]["pmu_observations"]["measured_supply"][
                "resource_services"
            ]
        )
        == 1
    )


def test_summarize_sparse_mte1_streams_bounded_and_guards_missing_or_static_events(
    tmp_path: Path,
) -> None:
    from mindie_profiler.measured_supply import deployment_source_identity
    from mindie_profiler.pmu_derivation import summarize_sparse_mte1

    train_geom = json.loads(TRAIN_GEOMETRY.read_text(encoding="utf-8"))
    r64_id = deployment_source_identity(R64, basis="cli_flag")

    def _valid_event(idx: int, *, op_state: str = "dynamic", parsed: bool = True) -> dict:
        ev = {
            "native_type": "KvQuantSparseFlashAttention",
            "op_state": op_state,
            "rank_id": "rank_0",
            "rank_index": 0,
            "device_id": "0",
            "source": "/cap/rank_0/kernel_details.csv",
            "source_sha256": None,
            "source_schema": "csv",
            "q_tokens": 1024,
            "block_num": 32,
            "mix_block_num": 64,
            "elapsed_us": 800.0,
            "mte1_us": 270.0 + (idx % 3) * 0.1,
            "mte1_ratio": 0.336,
        }
        if parsed:
            ev.update(
                {
                    "tensor_geometry_parsed": True,
                    "dtype": "bf16",
                    "output_dtype": "bf16",
                    "q_shape": (1024, 64, 576),
                    "k_shape": (4080, 128, 1, 656),
                    "out_shape": (1024, 64, 512),
                    "input_dtypes_slots": ("bf16", "fp8_e4m3"),
                }
            )
        return ev

    # 1. Streaming 2,000-element generator caps retained samples at 512 and emits limitation.
    stream_lims: list[dict] = []
    streamed = summarize_sparse_mte1(
        (_valid_event(i) for i in range(2000)),
        source_identity=r64_id,
        sparse_geometry=train_geom,
        limitations=stream_lims,
    )
    assert len(streamed) == 1
    assert streamed[0]["event_count"] == 512
    assert "sparse_mte1_samples_capped" in {item["code"] for item in stream_lims}

    # 2. 600 static events preceding 3 dynamic events do NOT starve dynamic eligibility!
    mixed_lims: list[dict] = []
    mixed_events = [_valid_event(i, op_state="static") for i in range(600)] + [
        _valid_event(i, op_state="dynamic") for i in range(3)
    ]
    mixed = summarize_sparse_mte1(
        mixed_events,
        source_identity=r64_id,
        sparse_geometry=train_geom,
        limitations=mixed_lims,
    )
    assert len(mixed) == 1
    assert mixed[0]["event_count"] == 3
    assert "sparse_mte1_samples_capped" not in {item["code"] for item in mixed_lims}

    # 3. Missing tensor shapes/descriptors never fall back to True!
    unparsed_lims: list[dict] = []
    unparsed = summarize_sparse_mte1(
        [_valid_event(0, parsed=False), _valid_event(1, parsed=False)],
        source_identity=r64_id,
        sparse_geometry=train_geom,
        limitations=unparsed_lims,
    )
    assert unparsed == []
    assert "sparse_mte1_tensor_geometry_mismatch" in {
        item["code"] for item in unparsed_lims
    }

    # 4. Distinct kernel KvQuantSparseFlashAttentionVllm is NEVER relabeled to KvQuantSparseFlashAttention!
    vllm_csv = tmp_path / "vllm_sfa.csv"
    vllm_csv.write_text(
        REAL_SFA_CSV.read_text(encoding="utf-8").replace(
            "KvQuantSparseFlashAttention", "KvQuantSparseFlashAttentionVllm"
        ),
        encoding="utf-8",
    )
    vllm_rep = analyze_profile(
        vllm_csv,
        full_range=True,
        source="csv",
        aic_count=32,
        deployment_image_id=R64,
        sparse_geometry=train_geom,
    )
    vllm_supply = vllm_rep["enrichment"]["pmu_observations"]["measured_supply"]
    assert vllm_supply["resource_services"] == []
    assert "sparse_mte1_no_matching_events" in {
        item["code"] for item in vllm_supply["limitations"]
    }

    # 5. Truncated Input Data Types missing FP8 KV evidence is rejected explicitly!
    no_kv_dt_csv = tmp_path / "no_kv_dt.csv"
    no_kv_dt_csv.write_text(
        REAL_SFA_CSV.read_text(encoding="utf-8").replace(
            "DT_BF16;DT_FLOAT8_E4M3FN;DT_FLOAT8_E4M3FN;INT32;DT_UNDEFINED;DT_UNDEFINED;INT32;INT32;INT32",
            "DT_BF16",
        ),
        encoding="utf-8",
    )
    no_kv_rep = analyze_profile(
        no_kv_dt_csv,
        full_range=True,
        source="csv",
        aic_count=32,
        deployment_image_id=R64,
        sparse_geometry=train_geom,
    )
    no_kv_supply = no_kv_rep["enrichment"]["pmu_observations"]["measured_supply"]
    assert no_kv_supply["resource_services"] == []
    assert "sparse_mte1_tensor_geometry_mismatch" in {
        item["code"] for item in no_kv_supply["limitations"]
    }


def test_overlapping_windows_deduplicate_sparse_and_matrix_pmu_supply() -> None:
    from mindie_profiler.events import Window
    from mindie_profiler.sources_csv import CsvSource, probe_csv

    train_geom = json.loads(TRAIN_GEOMETRY.read_text(encoding="utf-8"))
    sfa_events = list(
        CsvSource(probe_csv(REAL_SFA_CSV), rank_id="rank_0", rank_index=0).iter_events(
            max_rows=100, timeout_s=3.0
        )
    )
    whole = Window(
        min(e.start_ns for e in sfa_events),
        max(e.end_ns for e in sfa_events),
        label="all",
    )
    last = max(sfa_events, key=lambda e: e.start_ns)
    clipped_last = Window(
        last.start_ns + (last.end_ns - last.start_ns) // 2,
        last.end_ns,
        label="clipped_last",
    )
    overlapping = [
        whole,
        *(Window(last.start_ns - i, last.end_ns + i, label=f"w{i}") for i in range(1, 5)),
    ]
    for windows in ([whole], overlapping, [clipped_last, whole], [whole, clipped_last]):
        rep = analyze_profile(
            REAL_SFA_CSV,
            windows=windows,
            source="csv",
            aic_count=32,
            deployment_image_id=R64,
            sparse_geometry=train_geom,
        )
        pmu = rep["enrichment"]["pmu_observations"]
        assert pmu["counts"]["bound_event_count"] == 4
        assert pmu["counts"]["clipped_bound_event_count"] == 0
        assert len(pmu["bound_events"]) == 4
        svc = pmu["measured_supply"]["resource_services"][0]
        assert svc["event_count"] == 3
        assert svc["median_mte1_us"] == pytest.approx(269.564, rel=1e-9)
        assert svc["rate_bytes_per_s"] == pytest.approx(93_782_016 / 269.564e-6, rel=1e-9)

    qbmm_csv = Path(__file__).parent / "fixtures" / "r64_qbmm_dual_load" / "kernel_details.csv"
    qbmm_events = list(
        CsvSource(probe_csv(qbmm_csv), rank_id="rank_0", rank_index=0).iter_events(
            max_rows=100, timeout_s=3.0
        )
    )
    q_whole = Window(
        min(e.start_ns for e in qbmm_events),
        max(e.end_ns for e in qbmm_events),
        label="q_all",
    )
    q_last = max(qbmm_events, key=lambda e: e.start_ns)
    q_base = analyze_profile(
        qbmm_csv, windows=[q_whole], source="csv", aic_count=32, deployment_image_id=R64
    )["enrichment"]["pmu_observations"]
    q_over = analyze_profile(
        qbmm_csv,
        windows=[q_whole, Window(q_last.start_ns - 5, q_last.end_ns + 5, label="q_dup")],
        source="csv",
        aic_count=32,
        deployment_image_id=R64,
    )["enrichment"]["pmu_observations"]
    assert q_over["counts"] == q_base["counts"]
    assert q_over["measured_supply"]["pair"] == q_base["measured_supply"]["pair"]


def test_pmu_enrichment_scales_past_250k_events_and_deduplicates_serialized_records() -> None:
    from mindie_profiler.accounting import account_window
    from mindie_profiler.enrichment_anomaly import pmu_summary
    from mindie_profiler.events import Event, Observation, QueryStats, SourceRef, Window
    from mindie_profiler.measured_supply import measured_supply_event_record
    from mindie_profiler.measured_supply_summary import (
        PmuEventDeduplicator,
        summarize_measured_supply,
    )
    from mindie_profiler.sources_csv import CsvSource, probe_csv

    src = SourceRef("rank_0", 0, "db", "/mem/p.db", "p.db", None, 1, "v1", "db", 1)
    comm_events = [
        Event(
            rank_id="rank_0", rank_index=0, name="hcom_allReduce_", op_type="hcom_allReduce_",
            task_type="COMMUNICATION", core="COMMUNICATION", stream_id="5", task_id=str(i),
            device_id="0", start_ns=i * 10 + 1, end_ns=i * 10 + 9,
            source_kind="db", table="COMMUNICATION_OP", pmu_status="not_applicable",
        )
        for i in range(250_005)
    ]
    win = Window(0, 250_005 * 10 + 10, step=1)
    obs = Observation(
        "rank_0", 0, win,
        account_window(comm_events[:1], win),
        comm_events, src, QueryStats("rank_0", "1"),
    )
    dedup_probe = PmuEventDeduplicator([obs])
    assert dedup_probe._obs_locator == {}
    summary = pmu_summary([obs], physical_owners=32)
    assert summary["counts"]["not_applicable_event_count"] == 250_005

    # Serialized measured_supply_event_record dicts place observation_id inside provenance:
    # overlapping windows over the same physical QBMM event must deduplicate to event_count=1.
    qbmm_csv = Path(__file__).parent / "fixtures" / "r64_qbmm_dual_load" / "kernel_details.csv"
    q_ev = next(
        iter(
            CsvSource(probe_csv(qbmm_csv), rank_id="rank_0", rank_index=0).iter_events(
                max_rows=10, timeout_s=3.0
            )
        )
    )
    win_a = Window(q_ev.start_ns - 10, q_ev.end_ns + 10, label="wa")
    win_b = Window(q_ev.start_ns - 20, q_ev.end_ns + 20, label="wb")
    obs_a = Observation(
        "rank_0", 0, win_a, account_window([q_ev], win_a), [q_ev], src, QueryStats("rank_0", "wa")
    )
    obs_b = Observation(
        "rank_0", 0, win_b, account_window([q_ev], win_b), [q_ev], src, QueryStats("rank_0", "wb")
    )
    r64_ident = {"source_scope": "r64", "image_digest": R64_IMAGE_SHA}
    rec_a = measured_supply_event_record(obs_a, q_ev, r64_ident, physical_owners=32)
    rec_b = measured_supply_event_record(obs_b, q_ev, r64_ident, physical_owners=32)
    assert "observation_id" not in rec_a and rec_a["provenance"]["observation_id"] != rec_b["provenance"]["observation_id"]
    deduped = summarize_measured_supply([rec_a, rec_b], physical_owners=32, source_identity=r64_ident)
    assert deduped["candidates"][0]["event_count"] == 1
