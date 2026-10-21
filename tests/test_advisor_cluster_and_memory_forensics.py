"""Tier 0 unit tests for Ascend Advisor rules, cluster slow-rank/slow-link + EP balance, and memory forensics."""

from __future__ import annotations

import pytest

from mindie_profiler import (
    ADVISOR_SCHEMA,
    MEMORY_FORENSICS_SCHEMA,
    Event,
    SourceRef,
    Window,
    analyze_memory_inefficiencies,
    attribute_cluster_stragglers_and_links,
    cross_rank_stats,
    detect_step_monotonic_leaks,
    evaluate_advisor_rules,
    evaluate_ep_load_balance,
    run_memory_forensics,
    scan_aicpu_fallbacks,
    scan_alignment_and_mte_contention,
    scan_fusible_operator_sequences,
    scan_host_sync_and_gc_freezes,
)
from mindie_profiler.accounting import account_window
from mindie_profiler.enrichment import enrich_report
from mindie_profiler.events import Observation, QueryStats
from mindie_profiler.memory_profile import attribute_memory


def _make_event(
    start_us: float,
    end_us: float,
    name: str,
    op_type: str,
    *,
    rank_id: str = "rank_0",
    rank_index: int = 0,
    core: str = "AI_VECTOR_CORE",
    task_type: str | None = None,
    stream_id: str = "1",
    task_id: str = "1",
    block: str = "Norm_Act_Elem",
    is_comm: bool = False,
    is_aicpu: bool = False,
    input_shapes: str | None = '"128,4096"',
    input_dtypes: str | None = "FP16",
    pmu: dict[str, float | None] | None = None,
    bound_family: str = "vector",
) -> Event:
    tt = task_type or core
    return Event(
        rank_id=rank_id,
        rank_index=rank_index,
        name=name,
        op_type=op_type,
        task_type=tt,
        core=core,
        stream_id=stream_id,
        task_id=task_id,
        device_id=rank_index,
        start_ns=int(round(start_us * 1000.0)),
        end_ns=int(round(end_us * 1000.0)),
        source_kind="db",
        table="TASK",
        block=block,
        mapping_rule="test",
        execution_engine="aicpu" if is_aicpu else ("comm" if is_comm else "aiv"),
        bound_family=bound_family,
        is_comm=is_comm,
        is_aicpu=is_aicpu,
        input_shapes=input_shapes,
        input_dtypes=input_dtypes,
        input_formats="ND",
        wait_ns=0,
        wait_status="measured",
        pmu=pmu or {},
        pmu_status="measured" if pmu else "unavailable",
        pmu_kind="ratio" if pmu else "none",
    )


def _make_observation(
    rank_id: str,
    rank_index: int,
    step: int,
    start_us: float,
    end_us: float,
    events: list[Event],
) -> Observation:
    window = Window(
        start_ns=int(round(start_us * 1000.0)),
        end_ns=int(round(end_us * 1000.0)),
        step=step,
        label=f"step_{step}",
    )
    accounting = account_window(events, window)
    return Observation(
        rank_id=rank_id,
        rank_index=rank_index,
        window=window,
        source=SourceRef(
            rank_id=rank_id,
            rank_index=rank_index,
            kind="db",
            path="memory.db",
            basename="memory.db",
            sha256="0" * 64,
            size_bytes=4096,
            schema_version="1.2.0",
            schema_variant="torch_npu_db",
        ),
        events=tuple(events),
        accounting=accounting,
        stats=QueryStats(rank_id=rank_id, window_label=f"step_{step}"),
    )


def test_advisor_aicpu_fallbacks_and_cast_storms():
    events = [
        _make_event(0, 35, "aclnnNonZero", "NonZero", core="AI_CPU", is_aicpu=True, input_dtypes="BOOL"),
        _make_event(40, 85, "aclnnIndexPut", "IndexPut", core="AI_CPU", is_aicpu=True, input_dtypes="DT_DOUBLE"),
        _make_event(90, 120, "aclnnTopK", "TopKV2", core="AI_CPU", is_aicpu=True, input_dtypes="FP64"),
        _make_event(130, 145, "aclnnCast1", "Cast", core="AI_VECTOR_CORE"),
        _make_event(150, 165, "aclnnTransData1", "TransData", core="AI_VECTOR_CORE"),
        _make_event(170, 185, "aclnnCast2", "Cast", core="AI_VECTOR_CORE"),
        _make_event(190, 205, "aclnnTranspose1", "Transpose", core="AI_VECTOR_CORE"),
    ]
    res = scan_aicpu_fallbacks(events=events)
    assert res["status"] == "detected"
    assert res["aicpu_event_count"] == 3
    assert res["aicpu_total_ms"] == pytest.approx(0.110)
    assert res["double_dtype_fallback_count"] == 2
    assert res["cast_transdata_storm_count"] == 4
    codes = {m["pattern_code"] for m in res["matches"]}
    assert "aicpu_nonzero_dynamic_mask" in codes
    assert "aicpu_index_scatter_gather" in codes
    assert "aicpu_topk_sort_fallback" in codes
    assert "cast_transdata_storm" in codes


def test_advisor_alignment_and_multi_stream_mte_contention():
    events = [
        # 512B SDMA unaligned communication (1500 bytes > 512 and 1500 % 512 != 0)
        {
            "rank_id": "rank_0",
            "step": None,
            "name": "hcom_allReduce_",
            "op_type": "hcom_allReduce_",
            "task_type": "COMMUNICATION",
            "stream_id": "2",
            "task_id": "10",
            "start_us": 10.0,
            "duration_us": 50.0,
            "is_comm": True,
            "size_bytes": 1500,
        },
        # Cube MatMul overlapping on stream 1 with unaligned shape [17, 300] and high mte2_ratio
        _make_event(
            15.0,
            55.0,
            "aclnnMatMul",
            "MatMulV2",
            core="AI_CORE",
            stream_id="1",
            task_id="11",
            block="Linear_Cube",
            input_shapes='"17,300;300,4096"',
            input_dtypes="FP16",
            pmu={"mte2_ratio": 0.62, "mac_ratio": 0.21},
            bound_family="cube",
        ),
        # Concurrent Vector kernel on stream 3 overlapping stream 1 with high mte2_ratio
        _make_event(
            20.0,
            45.0,
            "aclnnRmsNorm",
            "RmsNorm",
            core="AI_VECTOR_CORE",
            stream_id="3",
            task_id="12",
            input_shapes='"15,15"',  # 225 * 2 = 450B -> 450 % 32 != 0 (32B UB violation)
            input_dtypes="FP16",
            pmu={"mte2_ratio": 0.58},
            bound_family="memory",
        ),
    ]
    obs = _make_observation("rank_0", 0, 1, 0.0, 100.0, [_make_event(15.0, 55.0, "aclnnMatMul", "MatMulV2", core="AI_CORE", stream_id="1", input_shapes='"17,300;300,4096"', pmu={"mte2_ratio": 0.62})])
    assert obs.accounting.available

    res = scan_alignment_and_mte_contention(events=events)
    assert res["status"] == "detected"
    assert res["alignment_violation_count"] == 3
    all_rules = {code for v in res["alignment_violations"] for code in v["rule_codes"]}
    assert "sdma_512b_unaligned" in all_rules
    assert "cube_fractal_16_unaligned" in all_rules
    assert "ub_32b_unaligned" in all_rules
    assert res["mte_contention_count"] >= 2
    contention_types = {w["contention_type"] for w in res["mte_contention_windows"]}
    assert "sdma_compute_mte_contention" in contention_types
    assert "multi_stream_cube_vector_mte_contention" in contention_types


def test_advisor_host_sync_and_gc_freezes():
    # Two kernels separated by a 25ms (25,000 us) uncovered gap with zero host ACL dispatch
    events = [
        _make_event(0.0, 100.0, "aclnnMatMul", "MatMulV2", stream_id="1", task_id="1"),
        _make_event(25_100.0, 25_200.0, "aclnnRmsNorm", "RmsNorm", stream_id="1", task_id="2"),
    ]
    obs = _make_observation("rank_0", 0, 2, 0.0, 26_000.0, events)
    host_events = [
        {"rank_id": "rank_0", "step": 2, "name": "NodeLaunch", "start_us": 0.0, "duration_us": 10.0},
        {"rank_id": "rank_0", "step": 2, "name": "aclrtSynchronizeStream", "start_us": 10.0, "duration_us": 90.0},
        {"rank_id": "rank_0", "step": 2, "name": "NodeLaunch", "start_us": 25_090.0, "duration_us": 8.0},
        {"rank_id": "rank_0", "step": 2, "name": "aclrtSynchronizeStream", "start_us": 25_100.0, "duration_us": 100.0},
        {"rank_id": "rank_0", "step": 2, "name": "aten::item", "start_us": 25_210.0, "duration_us": 30.0},
    ]
    res = scan_host_sync_and_gc_freezes([obs], host_events=host_events, gc_gap_threshold_ms=10.0)
    assert res["status"] == "detected"
    assert res["forced_sync_count"] == 3
    assert res["ascend_launch_blocking_suspected"] is True
    assert res["node_launch_sync_co_occurrence_ratio"] == pytest.approx(1.0)
    assert res["gc_freeze_count"] == 1
    assert res["gc_freezes"][0]["freeze_type"] == "suspected_python_gc_or_gil_freeze"
    assert res["gc_freezes"][0]["gap_ms"] == pytest.approx(25.0)
    assert res["gc_freezes"][0]["acl_busy_ratio"] < 0.01


def test_advisor_fusible_operator_sequences_and_barrier_respect():
    events = [
        # 1. Add + RmsNorm + DynamicQuant -> torch_npu.npu_add_rms_norm_quant
        _make_event(10.0, 20.0, "aclnnAdd", "Add", stream_id="1", task_id="1"),
        _make_event(22.0, 38.0, "aclnnRmsNorm", "RmsNorm", stream_id="1", task_id="2"),
        _make_event(40.0, 50.0, "aclnnDynamicQuant", "DynamicQuant", stream_id="1", task_id="3"),
        # 2. Slice + SiLU + Mul -> torch_npu.npu_swiglu
        _make_event(60.0, 68.0, "aclnnSlice", "Slice", stream_id="1", task_id="4"),
        _make_event(70.0, 82.0, "aclnnSilu", "Swish", stream_id="1", task_id="5"),
        _make_event(84.0, 94.0, "aclnnMul", "Mul", stream_id="1", task_id="6"),
        # 3. RoPE chain: Mul + Slice + Neg + Concat + Mul + Add -> torch_npu.npu_rotary_mul
        _make_event(100.0, 106.0, "aclnnMul", "Mul", stream_id="1", task_id="7"),
        _make_event(107.0, 111.0, "aclnnSlice", "Slice", stream_id="1", task_id="8"),
        _make_event(112.0, 116.0, "aclnnNeg", "Neg", stream_id="1", task_id="9"),
        _make_event(117.0, 122.0, "aclnnConcat", "Concat", stream_id="1", task_id="10"),
        _make_event(123.0, 129.0, "aclnnMul", "Mul", stream_id="1", task_id="11"),
        _make_event(130.0, 136.0, "aclnnAdd", "Add", stream_id="1", task_id="12"),
        # 4. MoE routing: TopK + Scatter + Gather -> npu_moe_gating_top_k_softmax + npu_moe_token_permute
        _make_event(150.0, 165.0, "aclnnTopK", "TopK", stream_id="1", task_id="13"),
        _make_event(167.0, 180.0, "aclnnScatter", "Scatter", stream_id="1", task_id="14"),
        _make_event(182.0, 195.0, "aclnnGather", "GatherV2", stream_id="1", task_id="15"),
        # 5. Barrier check: Add followed by COMMUNICATION followed by RmsNorm must NOT fuse
        _make_event(210.0, 220.0, "aclnnAdd", "Add", stream_id="1", task_id="16"),
        _make_event(221.0, 230.0, "hcom_allReduce_", "hcom_allReduce_", stream_id="1", task_id="17", is_comm=True, block="Comm"),
        _make_event(231.0, 240.0, "aclnnRmsNorm", "RmsNorm", stream_id="1", task_id="18"),
    ]
    obs = _make_observation("rank_0", 0, 4, 0.0, 300.0, events)
    res = scan_fusible_operator_sequences([obs])
    assert res["status"] == "detected"
    assert res["total_matched_sequences"] == 4
    by_code = {c["pattern_code"]: c for c in res["candidates"]}
    assert set(by_code) == {
        "add_rms_norm_dynamic_quant",
        "swiglu_slice_chain",
        "rotary_pos_emb_decomposed",
        "moe_routing_topk_permute",
    }
    assert by_code["add_rms_norm_dynamic_quant"]["replacement_api"] == "torch_npu.npu_add_rms_norm_quant"
    assert by_code["add_rms_norm_dynamic_quant"]["total_launch_gap_ms"] == pytest.approx(0.004)
    assert by_code["add_rms_norm_dynamic_quant"]["estimated_savings_ms"] > 0.015

    # Full enrich_report integration
    report = {"top_hotspot_kernels": [], "findings": [], "limitations": []}
    enriched = enrich_report(report, observations=[obs], requested_steps=[4])
    assert enriched["enrichment"]["advisor_rules"]["schema_version"] == ADVISOR_SCHEMA
    assert any(f["finding_type"] == "advisor_fusible_operator_sequence" for f in enriched["findings"])


def test_cluster_slow_rank_vs_slow_link_orthogonal_attribution():
    # Case 1: Slow Rank (Compute Straggler on rank_3 delays collective entry; ranks 0..2 wait)
    slow_rank_collectives = [
        {
            "step": 4,
            "collective_op": "hcom_allReduce",
            "ranks": [
                {"rank_id": "rank_0", "start_ms": 10.0, "end_ms": 25.0, "preceding_compute_ms": 9.5, "preceding_host_gap_ms": 0.5},
                {"rank_id": "rank_1", "start_ms": 10.2, "end_ms": 25.05, "preceding_compute_ms": 9.7, "preceding_host_gap_ms": 0.5},
                {"rank_id": "rank_2", "start_ms": 10.1, "end_ms": 25.02, "preceding_compute_ms": 9.6, "preceding_host_gap_ms": 0.5},
                {"rank_id": "rank_3", "start_ms": 24.0, "end_ms": 25.10, "preceding_compute_ms": 23.4, "preceding_host_gap_ms": 0.6},
            ],
        }
    ]
    sr = attribute_cluster_stragglers_and_links(collective_groups=slow_rank_collectives)
    assert sr["status"] == "detected"
    assert sr["primary_classification"] == "slow_rank"
    assert sr["primary_straggler_rank_id"] == "rank_3"
    assert sr["primary_straggler_cause"] == "compute_straggler"
    assert sr["primary_victim_rank_ids"] == ["rank_0", "rank_1", "rank_2"]
    assert sr["collectives"][0]["launch_skew_ms"] == pytest.approx(14.0)
    assert sr["collectives"][0]["end_skew_ms"] == pytest.approx(0.1)
    assert sr["collectives"][0]["transit_duration_ms"] == pytest.approx(1.1)

    # Case 2: Slow Rank caused by Host Dispatch Straggler
    host_straggler_collectives = [
        {
            "step": 5,
            "collective_op": "hcom_allGather",
            "ranks": [
                {"rank_id": "rank_0", "start_ms": 8.0, "end_ms": 20.0, "preceding_compute_ms": 7.5, "preceding_host_gap_ms": 0.5},
                {"rank_id": "rank_1", "start_ms": 19.0, "end_ms": 20.1, "preceding_compute_ms": 7.6, "preceding_host_gap_ms": 11.4},
            ],
        }
    ]
    hs = attribute_cluster_stragglers_and_links(collective_groups=host_straggler_collectives)
    assert hs["primary_classification"] == "slow_rank"
    assert hs["primary_straggler_rank_id"] == "rank_1"
    assert hs["primary_straggler_cause"] == "host_dispatch_straggler"
    assert hs["primary_victim_rank_ids"] == ["rank_0"]

    # Case 3: Slow Link (Simultaneous entry, large transit / degraded RDMA bandwidth & completion skew)
    slow_link_collectives = [
        {
            "step": 6,
            "collective_op": "hcom_allToAll",
            "transport": "RDMA",
            "size_bytes": 64 * 1024 * 1024,  # 67.1 MB
            "ranks": [
                {"rank_id": "rank_0", "start_ms": 10.0, "end_ms": 14.0},
                {"rank_id": "rank_1", "start_ms": 10.1, "end_ms": 14.1},
                {"rank_id": "rank_2", "start_ms": 10.1, "end_ms": 28.0},
                {"rank_id": "rank_3", "start_ms": 10.2, "end_ms": 28.2, "retry": 2},
            ],
        }
    ]
    sl = attribute_cluster_stragglers_and_links(collective_groups=slow_link_collectives)
    assert sl["status"] == "detected"
    assert sl["primary_classification"] == "slow_link"
    assert sl["primary_straggler_rank_id"] is None
    assert "rank_3" in sl["primary_slow_link_ranks"]
    assert sl["collectives"][0]["transport_anomaly"] == "rdma_retransmission"


def test_cluster_moe_ep_load_balance_and_comm_masking():
    # Build 4 rank observations with GroupedMatmul routed token shapes and dual-stream comm masking
    obs_list: list[Observation] = []
    routed_tokens_by_rank = [512, 520, 496, 1536]
    moe_dur_us_by_rank = [120.0, 125.0, 118.0, 340.0]

    for rank_idx, (tokens, moe_dur) in enumerate(zip(routed_tokens_by_rank, moe_dur_us_by_rank)):
        rk = f"rank_{rank_idx}"
        evs = [
            _make_event(
                0.0,
                moe_dur,
                "aclnnGroupedMatmul",
                "GroupedMatmul",
                rank_id=rk,
                rank_index=rank_idx,
                core="AI_CORE",
                stream_id="1",
                task_id="1",
                block="MoE",
                input_shapes=f'"{tokens},4096;4096,11008"',
                bound_family="cube",
            ),
            # Communication on stream 2 partially masked by GroupedMatmul on stream 1
            _make_event(
                20.0,
                100.0,
                "hcom_allToAll_",
                "hcom_allToAll_",
                rank_id=rk,
                rank_index=rank_idx,
                core="COMMUNICATION",
                stream_id="2",
                task_id="2",
                block="Comm",
                is_comm=True,
                input_shapes="",
            ),
        ]
        obs_list.append(_make_observation(rk, rank_idx, 4, 0.0, 400.0, evs))

    ep = evaluate_ep_load_balance(obs_list)
    assert ep["status"] == "imbalanced"
    assert ep["rank_count_evaluated"] == 4
    assert ep["tokens_max"] == 1536.0
    assert ep["tokens_min"] == 496.0
    assert ep["tokens_diff"] == 1040.0
    assert ep["hot_expert_rank_id"] == "rank_3"
    assert ep["cold_expert_rank_id"] == "rank_2"
    assert ep["ep_imbalance_cv"] > 0.50
    assert ep["straggler_to_median_ratio"] == pytest.approx(1536.0 / 516.0, rel=1e-4)
    assert ep["eplb_recommended"] is True
    assert ep["dual_stream_overlap_active"] is True
    assert ep["comm_masking_ratio_p50"] == pytest.approx(1.0)

    stats = cross_rank_stats(obs_list)
    assert "straggler_and_link_attribution" in stats
    assert stats["ep_load_balance"]["eplb_recommended"] is True


def test_memory_inefficiency_four_canonical_patterns():
    blocks = [
        # Freed block between A's malloc and A's first access -> triggers early_allocation
        {
            "block_id": "blk_freed_early",
            "addr": "0x1000",
            "op_name": "aclnnAdd",
            "size_bytes": 16 * 1024 * 1024,
            "malloc_api_id": 5,
            "first_access_api_id": 8,
            "last_access_api_id": 20,
            "free_api_id": 25,
            "alloc_ms": 0.5,
            "first_use_ms": 0.8,
            "last_use_ms": 2.0,
            "free_ms": 2.5,
            "step": 1,
        },
        # 1. early_allocation: allocated at api 10 (1.0ms), first accessed at api 60 (9.0ms) after blk_freed_early freed at 25
        {
            "block_id": "blk_early_alloc",
            "addr": "0x2000",
            "op_name": "aclnnMatMul",
            "size_bytes": 64 * 1024 * 1024,
            "malloc_api_id": 10,
            "first_access_api_id": 60,
            "last_access_api_id": 70,
            "free_api_id": 75,
            "alloc_ms": 1.0,
            "first_use_ms": 9.0,
            "last_use_ms": 10.5,
            "free_ms": 11.0,
            "step": 1,
        },
        # 2. late_deallocation: last accessed at api 80 (12.0ms), freed at api 160 (24.0ms) across streams while blk_next allocates at 100
        {
            "block_id": "blk_late_free",
            "addr": "0x3000",
            "op_name": "aclnnFlashAttention",
            "size_bytes": 128 * 1024 * 1024,
            "stream_id": "1",
            "free_stream_id": "2",
            "malloc_api_id": 72,
            "first_access_api_id": 74,
            "last_access_api_id": 80,
            "free_api_id": 160,
            "alloc_ms": 10.8,
            "first_use_ms": 11.0,
            "last_use_ms": 12.0,
            "free_ms": 24.0,
            "step": 1,
        },
        # 3. temporary_buffer_spike (temporary_idleness + workspace tag)
        {
            "block_id": "blk_temp_idle",
            "addr": "0x4000",
            "op_name": "aclnnGroupedMatmulWorkspace",
            "tag": "workspace",
            "size_bytes": 256 * 1024 * 1024,
            "malloc_api_id": 100,
            "first_access_api_id": 102,
            "last_access_api_id": 4200,
            "free_api_id": 4205,
            "max_access_interval": 4000,
            "alloc_ms": 14.0,
            "first_use_ms": 14.2,
            "last_use_ms": 40.0,
            "free_ms": 40.5,
            "max_idle_gap_ms": 22.0,
            "step": 1,
        },
    ]
    snapshots = [
        # 4. allocator_fragmentation: 10 GiB allocated, 14 GiB reserved (28.57% fragmentation) + 12.5 GiB transient peak
        {
            "step": 1,
            "allocated_bytes": 10 * (1024 ** 3),
            "peak_allocated_bytes": 12.5 * (1024 ** 3),
            "reserved_bytes": 14 * (1024 ** 3),
            "peak_op": "lm_head_logits",
        }
    ]
    res = analyze_memory_inefficiencies(blocks, allocator_snapshots=snapshots)
    assert res["status"] == "detected"
    assert res["early_allocation_count"] == 1
    assert res["early_allocations"][0]["block_id"] == "blk_early_alloc"
    assert res["late_deallocation_count"] == 1
    assert res["late_deallocations"][0]["block_id"] == "blk_late_free"
    assert res["late_deallocations"][0]["cross_stream_retention"] is True
    assert res["temporary_buffer_spike_count"] == 2
    assert res["allocator_fragmentation_count"] == 1
    assert res["allocator_fragmentation"][0]["severity"] == "high"
    assert res["expandable_segments_recommended"] is True
    assert res["max_fragmentation_ratio"] == pytest.approx(4.0 / 14.0, rel=1e-4)


def test_memory_step_monotonic_leak_vs_warmup_bucket_growth():
    gib = float(1024 ** 3)
    mib = float(1024 ** 2)

    # Case A: Warmup jump at step 0->1 + reserved bucket step-up at step 2, but allocated returns to 12 GiB baseline
    warmup_and_bucket_steps = [
        {"step": 0, "allocated_bytes": 8.0 * gib, "reserved_bytes": 9.0 * gib, "phase": "warmup"},
        {"step": 1, "allocated_bytes": 12.0 * gib, "reserved_bytes": 14.0 * gib, "phase": "decode"},
        {"step": 2, "allocated_bytes": 12.05 * gib, "reserved_bytes": 16.0 * gib, "phase": "decode"},
        {"step": 3, "allocated_bytes": 12.0 * gib, "reserved_bytes": 16.0 * gib, "phase": "decode"},
        {"step": 4, "allocated_bytes": 12.0 * gib, "reserved_bytes": 16.0 * gib, "phase": "decode"},
    ]
    non_leak = detect_step_monotonic_leaks(warmup_and_bucket_steps)
    assert non_leak["leak_detected"] is False
    assert non_leak["classification"] == "warmup_or_bucket_reservation_growth"
    assert non_leak["warmup_growth_bytes"] == pytest.approx(4.0 * gib)
    assert non_leak["total_post_warmup_growth_bytes"] == pytest.approx(0.0)

    # Case B: True post-warmup step_monotonic_leak (+32 MiB every decode step) with leaked HAL & shadow PTA blocks
    monotonic_leak_steps = [
        {"step": 0, "allocated_bytes": 8.0 * gib, "reserved_bytes": 9.0 * gib, "phase": "warmup"},
        {"step": 1, "allocated_bytes": 12.0 * gib, "reserved_bytes": 14.0 * gib, "phase": "decode"},
        {"step": 2, "allocated_bytes": 12.0 * gib + 32 * mib, "reserved_bytes": 14.0 * gib, "phase": "decode"},
        {"step": 3, "allocated_bytes": 12.0 * gib + 64 * mib, "reserved_bytes": 14.0 * gib, "phase": "decode"},
        {"step": 4, "allocated_bytes": 12.0 * gib + 96 * mib, "reserved_bytes": 14.5 * gib, "phase": "decode"},
    ]
    leaked_blocks = [
        {"block_id": "pta_leak_1", "addr": "0xaaaa", "op_name": "kv_step_meta", "size_bytes": 32 * mib, "attr": "PTA", "shadow": True, "step": 2},
        {"block_id": "hal_leak_1", "addr": "0xbbbb", "op_name": "halMalloc", "size_bytes": 16 * mib, "attr": "HAL", "unfreed": True, "step": 3},
    ]
    leak_res = detect_step_monotonic_leaks(monotonic_leak_steps, memory_blocks=leaked_blocks)
    assert leak_res["status"] == "detected"
    assert leak_res["leak_detected"] is True
    assert leak_res["classification"] == "step_monotonic_leak"
    assert leak_res["total_post_warmup_growth_bytes"] == pytest.approx(96 * mib)
    assert leak_res["leak_rate_bytes_per_step"] == pytest.approx(32 * mib)
    assert len(leak_res["leaked_block_candidates"]) == 2
    layers = {c["leak_layer"] for c in leak_res["leaked_block_candidates"]}
    assert layers == {"PTA", "HAL"}

    # Verify attribute_memory integration
    manifest = {
        "baseline_hbm": {"0": 1024},
        "after_ready_hbm": {"0": 13312},
        "after_infer_hbm": {"0": 15360},
        "step_snapshots": monotonic_leak_steps,
        "memory_blocks": leaked_blocks,
    }
    mem_report = attribute_memory(manifest)
    assert mem_report["memory_forensics"]["schema_version"] == MEMORY_FORENSICS_SCHEMA
    assert mem_report["memory_forensics"]["step_leak_analysis"]["leak_detected"] is True
