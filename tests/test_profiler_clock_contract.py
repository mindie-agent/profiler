"""Clock-contract slice: real source -> normalized row, cross-rank relation.

The counterexample in the design/minimal examples is decisive: subtracting
each rank's earliest event would turn two unrelated local timelines into a
false common origin.  These tests keep local durations usable and require a
sourced reference before any cross-rank span or entry/exit order is reported.
"""

from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.accounting import account_window
from mindie_profiler.cross_rank import (
    attribute_cluster_stragglers_and_links,
    cross_rank_stats,
    cross_rank_union_span,
    evaluate_ep_load_balance,
)
from mindie_profiler.events import (
    ClockDomain,
    Event,
    Observation,
    QueryStats,
    SourceRef,
    Window,
)
from mindie_profiler.normalized import kernel_rows, row_from_event
from mindie_profiler.sources_db import DbSource, probe_db

CAPTURE = Path(__file__).parent / "fixtures/profiler_core/real_glm45"
DB = CAPTURE / "rank_0/ASCEND_PROFILER_OUTPUT/ascend_pytorch_profiler_0.db"
CSV = CAPTURE / "kernel_details_slice.csv"
REAL_WINDOW_NS = (1_763_456_164_890_045_000, 1_763_456_164_895_045_000)


def test_real_db_clock_domain_unit_tick_and_duration_survive_normalization():
    events, stats = DbSource(probe_db(DB)).iter_window(Window(*REAL_WINDOW_NS))
    assert stats.bad_rows == 0 and events

    event = next(item for item in events if item.table == "COMPUTE_TASK_INFO")
    assert event.clock.domain == "db_task_ns"
    assert event.clock.unit == "ns"
    assert event.clock.scale_ns == 1
    # Epoch magnitude is not a synchronization claim.
    assert event.clock.offset_ns is None
    assert event.clock.reference_domain is None
    assert "no cross-rank synchronization anchor" in event.clock.source
    # The raw TASK tick is nanoseconds and is retained unchanged.
    assert event.clock_start_tick == event.start_ns
    assert event.clock_end_tick == event.end_ns
    assert event.source_id.startswith("SRC-")
    assert event.capture_id.startswith("CAP-")
    assert event.table_kind == "COMPUTE_TASK_INFO"
    assert event.field_presence["clock"] is True
    assert event.field_presence["abi"] is True

    row = row_from_event(event)
    assert row.clock == event.clock
    assert row.clock_start_tick == event.start_ns
    assert row.clock_end_tick == event.end_ns
    assert row.start_ns == event.start_ns
    assert row.duration_ns == event.duration_ns
    assert row.reference_interval_ns is None


def test_real_csv_source_declares_unit_without_inventing_a_sync_or_tick():
    row = next(kernel_rows(CSV, rank_id="rank_0", rank_index=0))
    assert row.duration_ns == 1920
    assert row.clock.domain == "kernel_details_csv_us"
    assert row.clock.unit == "us"
    assert row.clock.scale_ns == 1000
    assert row.clock.offset_ns is None
    assert row.clock.reference_domain is None
    # The adapter retains the original microsecond token; it never reconstructs
    # it from the rounded nanosecond value.
    assert row.clock_start_tick == "1763456164890788.360"
    assert row.clock_duration_tick == "1.920"
    assert row.clock_end_tick is None


def test_non_epoch_csv_keeps_source_unit_without_claiming_a_reference(tmp_path):
    with CSV.open(newline="") as handle:
        reader = csv.DictReader(handle)
        raw = next(reader)
        fieldnames = reader.fieldnames
    raw["Start Time(us)"] = "10.000"
    raw["Duration(us)"] = "2.000"
    target = tmp_path / "kernel_details.csv"
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(raw)

    row = next(kernel_rows(target))
    assert row.duration_ns == 2_000
    assert row.clock.unit == "us"
    assert row.clock.scale_ns == 1000
    assert row.clock.offset_ns is None
    assert row.clock.reference_domain is None


def _event(
    rank_id: str,
    domain: str,
    start_us: int,
    duration_us: int,
    *,
    offset_us: int | None,
) -> Event:
    start_ns = start_us * 1000
    end_ns = start_ns + duration_us * 1000
    clock = ClockDomain(
        domain=domain,
        unit="us",
        scale_ns=1000,
        offset_ns=None if offset_us is None else offset_us * 1000,
        reference_domain=None if offset_us is None else "global_ns",
        source="explicit synthetic synchronization anchor; not fitted from durations",
    )
    return Event(
        rank_id=rank_id,
        rank_index=int(rank_id.rsplit("_", 1)[1]),
        name="hcom_allReduce",
        op_type="hcom_allReduce",
        task_type="COMMUNICATION",
        core="COMMUNICATION",
        stream_id="1",
        task_id="1",
        device_id="0",
        start_ns=start_ns,
        end_ns=end_ns,
        source_kind="synthetic_capture",
        table="TASK",
        clock=clock,
        clock_start_tick=start_ns,
        clock_end_tick=end_ns,
        block="Comm",
        is_comm=True,
        wait_status="not_applicable",
        pmu_status="not_applicable",
    )


def _observation(rank_id: str, events: list[Event]) -> Observation:
    start_ns = min(event.start_ns for event in events)
    end_ns = max(event.end_ns for event in events)
    window = Window(start_ns - 1, end_ns + 1, step=1, label="step_1")
    return Observation(
        rank_id=rank_id,
        rank_index=int(rank_id.rsplit("_", 1)[1]),
        window=window,
        accounting=account_window(events, window),
        events=events,
        source=SourceRef(
            rank_id=rank_id,
            rank_index=int(rank_id.rsplit("_", 1)[1]),
            kind="synthetic_capture",
            path="capture.db",
            basename="capture.db",
            sha256=None,
            size_bytes=0,
            schema_version="test",
            schema_variant="test",
        ),
        stats=QueryStats(rank_id=rank_id, window_label="step_1"),
    )


def _observations(mapped: bool) -> tuple[list[Observation], list[Event]]:
    events = [
        _event("rank_0", "D0", 10, 4, offset_us=0),
        # D1's raw local clock is 1000us ahead.  The mapping is an explicit
        # anchor, not a value fitted from these durations.
        _event("rank_1", "D1", 1013, 2, offset_us=-1000 if mapped else None),
    ]
    return [_observation(event.rank_id, [event]) for event in events], events


def test_real_epoch_magnitude_adapters_do_not_imply_a_shared_reference():
    db_events, _ = DbSource(probe_db(DB)).iter_window(Window(*REAL_WINDOW_NS))
    compute_events = [item for item in db_events if item.table == "COMPUTE_TASK_INFO"]
    assert len(compute_events) >= 2
    csv_event = next(kernel_rows(CSV, rank_id="rank_1", rank_index=1)).event

    # Both real sources sit at epoch magnitude, but they come from independent
    # adapters with no synchronization anchor.
    mixed = [
        _observation("rank_0", [compute_events[0]]),
        _observation("rank_1", [csv_event]),
    ]
    span = cross_rank_union_span(mixed)
    assert span["status"] == "unavailable_clock_relation"
    assert span["span_ns"] is None
    assert span["rank_domains"] == {
        "rank_0": ["db_task_ns"],
        "rank_1": ["kernel_details_csv_us"],
    }
    assert compute_events[0].duration_ns > 0
    assert csv_event.duration_ns == 1920

    # Even the same domain label without a reference is only a local unit
    # classification, never a synchronization claim.
    same_domain = [
        _observation("rank_0", [compute_events[0]]),
        _observation("rank_1", [compute_events[1]]),
    ]
    assert cross_rank_union_span(same_domain)["status"] == (
        "unavailable_clock_relation"
    )


def _local_clock() -> ClockDomain:
    return ClockDomain(
        domain="rank_local",
        unit="us",
        scale_ns=1000,
        source="explicit local-rank clock without a synchronization anchor",
    )


def test_duration_skew_and_size_without_transit_stays_clock_unverified():
    no_ref = _local_clock()
    group = {
        "step": 1,
        "collective_op": "hcom_allReduce",
        # Payload size alone must not turn the 20us total duration into a
        # measured 0.8192 GB/s transfer rate.
        "size_bytes": 4096,
        "ranks": [
            {"rank_id": "rank_0", "start_ms": 0.0, "end_ms": 0.020,
             "clock": no_ref},
            {"rank_id": "rank_1", "start_ms": 0.0, "end_ms": 0.005,
             "clock": no_ref},
        ],
    }
    result = attribute_cluster_stragglers_and_links(collective_groups=[group])
    group = result["collectives"][0]
    assert group["clock_relation"] == "unavailable_clock_relation"
    assert group["classification"] == "clock_unverified"
    assert group["duration_skew_ms"] == pytest.approx(0.015)
    assert group["transit_source"] == "min_duration_estimate"
    assert group["effective_bandwidth_gbps"] is None
    assert group["bandwidth_source"] is None
    assert group["transport_anomaly"] is None
    assert result["classification_counts"]["slow_link"] == 0


def test_retransmission_or_measured_bandwidth_still_attributes_link():
    no_ref = _local_clock()
    retry_group = {
        "step": 1,
        "collective_op": "hcom_allReduce",
        "ranks": [
            {"rank_id": "rank_0", "start_ms": 0.0, "end_ms": 0.020,
             "clock": no_ref, "retry": 1},
            {"rank_id": "rank_1", "start_ms": 0.0, "end_ms": 0.005,
             "clock": no_ref},
        ],
    }
    retry = attribute_cluster_stragglers_and_links(
        collective_groups=[retry_group]
    )["collectives"][0]
    assert retry["classification"] == "slow_link"
    assert retry["transport_anomaly"] == "rdma_retransmission"

    bandwidth_group = {
        "step": 2,
        "collective_op": "hcom_allReduce",
        "transport": "RDMA",
        "size_bytes": 1_000_000,
        "ranks": [
            {"rank_id": "rank_0", "start_ms": 0.0, "end_ms": 5.0,
             "transit_ms": 1.0, "clock": no_ref},
            {"rank_id": "rank_1", "start_ms": 0.0, "end_ms": 5.0,
             "transit_ms": 1.0, "clock": no_ref},
        ],
    }
    bandwidth = attribute_cluster_stragglers_and_links(
        collective_groups=[bandwidth_group]
    )["collectives"][0]
    assert bandwidth["classification"] == "slow_link"
    assert bandwidth["transport_anomaly"] == "low_link_bandwidth"


def test_cross_rank_union_span_needs_a_sourced_reference_not_rank_minima():
    unmapped, events = _observations(mapped=False)
    missing = cross_rank_union_span(unmapped)
    assert missing["status"] == "unavailable_clock_relation"
    assert missing["span_ns"] is None and missing["span_ms"] is None
    # Local durations stay valid and are the only timing claim we make.
    assert [event.duration_ns for event in events] == [4_000, 2_000]

    mapped, events = _observations(mapped=True)
    available = cross_rank_union_span(mapped)
    assert available["status"] == "available"
    assert available["reference_domain"] == "global_ns"
    assert available["span_ns"] == 5_000
    assert [event.duration_ns for event in events] == [4_000, 2_000]

    stats = cross_rank_stats(mapped)
    assert stats["cross_rank_union_span"]["span_ns"] == 5_000
    # wall_skew is a p50 over local durations, never a raw cross-domain start.
    assert cross_rank_stats(unmapped)["wall_skew_ms"] is not None


def test_entry_skew_is_withheld_without_clock_relation_but_local_skew_remains():
    unmapped, _events = _observations(mapped=False)
    missing = attribute_cluster_stragglers_and_links(unmapped)
    assert missing["status"] == "clock_relation_unavailable"
    assert missing["primary_classification"] == "clock_unverified"
    group = missing["collectives"][0]
    assert group["clock_relation"] == "unavailable_clock_relation"
    assert group["launch_skew_ms"] is None
    assert group["end_skew_ms"] is None
    assert group["duration_skew_ms"] == pytest.approx(0.002)
    assert missing["findings"][0]["finding_type"] == "cross_rank_clock_relation_unavailable"

    mapped, _events = _observations(mapped=True)
    available = attribute_cluster_stragglers_and_links(mapped)
    group = available["collectives"][0]
    assert group["clock_relation"] == "sourced_reference"
    assert group["clock_reference_domain"] == "global_ns"
    assert group["launch_skew_ms"] == pytest.approx(0.003)
    assert group["end_skew_ms"] == pytest.approx(0.001)
    assert group["duration_skew_ms"] == pytest.approx(0.002)


def test_alltoallv_pairs_bytes_and_transit_per_rank_not_across_ranks():
    no_ref = _local_clock()
    ranks = [
        {"rank_id": "rank_0", "start_ms": 0.0, "end_ms": 1.0,
         "size_bytes": 40_000, "transit_ns": 1_000,
         "transport": "RDMA", "clock": no_ref},
        {"rank_id": "rank_1", "start_ms": 0.0, "end_ms": 1.0,
         "size_bytes": 4_000_000, "transit_ns": 100_000,
         "transport": "RDMA", "clock": no_ref},
    ]
    result = attribute_cluster_stragglers_and_links(
        collective_groups=[{
            "step": 3,
            "collective_op": "hcom_allToAllV",
            "transport": "RDMA",
            "ranks": ranks,
        }]
    )
    group = result["collectives"][0]
    assert group["rank_bandwidths_gbps"] == {
        "rank_0": 40.0,
        "rank_1": 40.0,
    }
    assert group["bandwidth_status"] == "uniform"
    assert group["effective_bandwidth_gbps"] == 40.0
    assert group["rank_link_evidence"] == {"rank_0": None, "rank_1": None}
    assert group["link_bottleneck_rank_ids"] == []
    assert group["transport_anomaly"] is None
    assert group["classification"] == "clock_unverified"

    # Reversing rank order must not change the per-rank pairing or the result.
    reversed_result = attribute_cluster_stragglers_and_links(
        collective_groups=[{
            "step": 3,
            "collective_op": "hcom_allToAllV",
            "transport": "RDMA",
            "ranks": list(reversed(ranks)),
        }]
    )
    reversed_group = reversed_result["collectives"][0]
    assert reversed_group["rank_bandwidths_gbps"] == group["rank_bandwidths_gbps"]
    assert reversed_group["classification"] == "clock_unverified"

    # Only the rank whose own pair is slow is attributed; the other rank stays
    # out even though its local duration is equal.
    slow_rank1 = [dict(item) for item in ranks]
    slow_rank1[1]["transit_ns"] = 200_000  # 20 GB/s, below RDMA floor
    slow = attribute_cluster_stragglers_and_links(
        collective_groups=[{
            "step": 3,
            "collective_op": "hcom_allToAllV",
            "transport": "RDMA",
            "ranks": slow_rank1,
        }]
    )["collectives"][0]
    assert slow["rank_bandwidths_gbps"]["rank_0"] == 40.0
    assert slow["rank_bandwidths_gbps"]["rank_1"] == 20.0
    assert slow["bandwidth_status"] == "per_rank"
    assert slow["effective_bandwidth_gbps"] is None
    assert slow["link_bottleneck_rank_ids"] == ["rank_1"]
    assert slow["classification"] == "slow_link"
    assert slow["transport_anomaly"] == "low_link_bandwidth"


def test_mapped_duration_skew_without_paired_link_evidence_is_unknown():
    events = [
        _event("rank_0", "D0", 0, 20, offset_us=0),
        _event("rank_1", "D1", 0, 5, offset_us=0),
    ]
    result = attribute_cluster_stragglers_and_links(
        [_observation(event.rank_id, [event]) for event in events]
    )
    group = result["collectives"][0]
    assert group["clock_relation"] == "sourced_reference"
    assert group["classification"] == "link_attribution_unknown"
    assert group["link_bottleneck_rank_ids"] == []
    assert group["transport_anomaly"] is None
    assert group["bandwidth_status"] == "unavailable"
    assert result["status"] == "link_attribution_unknown"


def _link_group(rank0_transport, group_transport=None):
    no_ref = _local_clock()
    group = {
        "step": 1,
        "collective_op": "hcom_allToAllV",
        "ranks": [
            {"rank_id": "rank_0", "start_ms": 0.0, "end_ms": 0.020,
             "size_bytes": 16_000, "transit_ns": 1_000,
             "clock": no_ref},
            {"rank_id": "rank_1", "start_ms": 0.0, "end_ms": 0.020,
             "size_bytes": 40_000, "transit_ns": 1_000,
             "transport": "RDMA", "clock": no_ref},
        ],
    }
    if rank0_transport is not None:
        group["ranks"][0]["transport"] = rank0_transport
    if group_transport is not None:
        group["transport"] = group_transport
    return group


def test_missing_or_unknown_transport_keeps_rate_but_not_anomaly():
    def evaluated(group):
        return attribute_cluster_stragglers_and_links(
            collective_groups=[group]
        )["collectives"][0]

    missing = evaluated(_link_group(None))
    assert missing["rank_bandwidths_gbps"] == {"rank_0": 16.0, "rank_1": 40.0}
    assert missing["rank_link_facts"]["rank_0"]["applicable_floor_gbps"] is None
    assert "transport_missing" in missing["rank_link_facts"]["rank_0"]["missing_reasons"]
    assert missing["rank_link_facts"]["rank_1"]["applicable_floor_gbps"] == 21.0
    assert missing["link_bottleneck_rank_ids"] == []
    assert missing["classification"] == "clock_unverified"

    unknown = evaluated(_link_group("NVLINK"))
    assert unknown["rank_bandwidths_gbps"]["rank_0"] == 16.0
    assert unknown["rank_link_facts"]["rank_0"]["applicable_floor_gbps"] is None
    assert any(
        reason.startswith("transport_unrecognized:")
        for reason in unknown["rank_link_facts"]["rank_0"]["missing_reasons"]
    )
    assert unknown["link_bottleneck_rank_ids"] == []

    # 16 GB/s is above the known PCIE floor and below the known RDMA floor.
    pcie = evaluated(_link_group("PCIE"))
    assert pcie["rank_link_facts"]["rank_0"]["applicable_floor_gbps"] == 12.0
    assert pcie["rank_link_evidence"]["rank_0"] is None
    assert pcie["link_bottleneck_rank_ids"] == []

    rdma = evaluated(_link_group("RDMA"))
    assert rdma["rank_link_evidence"]["rank_0"] == "low_bandwidth"
    assert rdma["link_bottleneck_rank_ids"] == ["rank_0"]
    assert rdma["classification"] == "slow_link"

    shared = evaluated(_link_group(None, group_transport="RDMA"))
    assert shared["rank_transport_sources"]["rank_0"] == "group"
    assert shared["rank_link_facts"]["rank_0"]["applicable_floor_gbps"] == 21.0
    assert shared["link_bottleneck_rank_ids"] == ["rank_0"]


def test_slow_link_finding_keeps_per_collective_rank_association():
    G1 = {
        "step": 1,
        "collective_op": "hcom_allToAllV",
        "transport": "RDMA",
        "ranks": [
            {"rank_id": "rank_0", "start_ms": 0.0, "end_ms": 0.020,
             "size_bytes": 40_000, "transit_ns": 2_000, "clock": _local_clock()},
            {"rank_id": "rank_1", "start_ms": 0.0, "end_ms": 0.020,
             "size_bytes": 40_000, "transit_ns": 1_000, "clock": _local_clock()},
        ],
    }
    G2 = {
        "step": 2,
        "collective_op": "hcom_allReduce",
        "transport": "RDMA",
        "ranks": [
            {"rank_id": "rank_0", "start_ms": 0.0, "end_ms": 0.020,
             "size_bytes": 40_000, "transit_ns": 1_000, "clock": _local_clock()},
            {"rank_id": "rank_1", "start_ms": 0.0, "end_ms": 0.020,
             "size_bytes": 40_000, "transit_ns": 1_000, "retry": 1,
             "clock": _local_clock()},
        ],
    }

    def items(groups):
        result = attribute_cluster_stragglers_and_links(collective_groups=groups)
        finding = next(
            f for f in result["findings"]
            if f["finding_type"] == "cluster_slow_communication_link"
        )
        by_step = {item["step"]: item for item in finding["evidence_scope"]["slow_link_evidence"]}
        return result, finding, by_step

    result, finding, by_step = items([G1, G2])
    assert by_step[1]["transport_anomaly"] == "low_link_bandwidth"
    assert by_step[1]["bottleneck_rank_ids"] == ["rank_0"]
    assert by_step[1]["rank_link_evidence"] == {
        "rank_0": "low_bandwidth", "rank_1": None
    }
    assert by_step[2]["transport_anomaly"] == "rdma_retransmission"
    assert by_step[2]["bottleneck_rank_ids"] == ["rank_1"]
    assert by_step[2]["rank_link_evidence"] == {
        "rank_0": None, "rank_1": "retransmission"
    }
    assert result["primary_slow_link_ranks"] == ["rank_0", "rank_1"]
    assert finding["evidence_scope"]["slow_link_rank_union"] == ["rank_0", "rank_1"]

    # Swapping the two groups changes list order, not step/op/rank association.
    _result2, _finding2, by_step_swapped = items([G2, G1])
    assert by_step_swapped[1]["bottleneck_rank_ids"] == ["rank_0"]
    assert by_step_swapped[2]["bottleneck_rank_ids"] == ["rank_1"]


def test_partial_pair_keeps_known_rank_facts_without_borrowing_peers():
    no_ref = _local_clock()
    group = {
        "step": 1,
        "collective_op": "hcom_allToAllV",
        "transport": "RDMA",
        "ranks": [
            {"rank_id": "rank_0", "start_ms": 0.0, "end_ms": 0.020,
             "size_bytes": 16_000, "transit_ns": 1_000,
             "transport": "RDMA", "clock": no_ref},
            {"rank_id": "rank_1", "start_ms": 0.0, "end_ms": 0.020,
             "transit_ns": 1_000, "transport": "RDMA", "clock": no_ref},
        ],
    }
    result = attribute_cluster_stragglers_and_links(
        collective_groups=[group]
    )["collectives"][0]
    assert result["rank_bandwidths_gbps"] == {"rank_0": 16.0, "rank_1": None}
    assert "size_missing" in result["rank_link_facts"]["rank_1"]["missing_reasons"]
    assert result["rank_link_facts"]["rank_1"]["bandwidth_gbps"] is None
    assert result["bandwidth_status"] == "incomplete"
    assert result["effective_bandwidth_gbps"] is None
    assert result["rank_link_evidence"]["rank_0"] == "low_bandwidth"
    assert result["rank_link_evidence"]["rank_1"] is None
    assert result["link_bottleneck_rank_ids"] == ["rank_0"]

    # Retry remains independent even though the other rank has the low rate.
    group["ranks"][1]["size_bytes"] = 40_000
    group["ranks"][1]["retry"] = 1
    with_retry = attribute_cluster_stragglers_and_links(
        collective_groups=[group]
    )["collectives"][0]
    assert with_retry["rank_bandwidths_gbps"] == {
        "rank_0": 16.0,
        "rank_1": 40.0,
    }
    assert with_retry["rank_link_evidence"] == {
        "rank_0": "low_bandwidth",
        "rank_1": "retransmission",
    }
    assert with_retry["link_bottleneck_rank_ids"] == ["rank_0", "rank_1"]


def _mapped_clock(domain: str) -> ClockDomain:
    return ClockDomain(
        domain=domain,
        unit="us",
        scale_ns=1000,
        offset_ns=0,
        reference_domain="global_ns",
        source="explicit synthetic synchronization anchor; not fitted from durations",
    )


def _r5_g1():
    return {
        "step": 1,
        "collective_op": "hcom_allToAllV",
        "transport": "RDMA",
        "ranks": [
            {"rank_id": "rank_0", "start_ms": 0.0, "end_ms": 0.020,
             "size_bytes": 40_000, "transit_ns": 2_000,
             "clock": _mapped_clock("D0")},
            {"rank_id": "rank_1", "start_ms": 0.0, "end_ms": 0.020,
             "size_bytes": 40_000, "transit_ns": 1_000,
             "clock": _mapped_clock("D1")},
        ],
    }


def _r5_g2():
    return {
        "step": 2,
        "collective_op": "hcom_allReduce",
        "transport": "RDMA",
        "ranks": [
            {"rank_id": "rank_0", "start_ms": 0.100, "end_ms": 0.120,
             "size_bytes": 40_000, "transit_ns": 1_000,
             "clock": _mapped_clock("D0")},
            {"rank_id": "rank_1", "start_ms": 0.110, "end_ms": 0.120,
             "size_bytes": 40_000, "transit_ns": 1_000, "retry": 1,
             "clock": _mapped_clock("D1")},
        ],
    }


def test_r5_mixed_group_enters_both_evidence_views():
    result = attribute_cluster_stragglers_and_links(collective_groups=[_r5_g2()])
    group = result["collectives"][0]
    assert group["classification"] == "mixed_straggler_and_link"
    assert group["rank_link_evidence"]["rank_1"] == "retransmission"
    assert group["perpetrator_rank_id"] == "rank_1"

    assert [item["step"] for item in result["slow_rank_evidence"]] == [2]
    assert [item["step"] for item in result["slow_link_evidence"]] == [2]
    assert result["slow_link_rank_union"] == ["rank_1"]
    assert result["primary_slow_link_ranks"] == ["rank_1"]
    finding_types = {item["finding_type"] for item in result["findings"]}
    assert "cluster_slow_rank_straggler" in finding_types
    assert "cluster_slow_communication_link" in finding_types
    link_finding = next(
        item for item in result["findings"]
        if item["finding_type"] == "cluster_slow_communication_link"
    )
    assert link_finding["evidence_scope"]["slow_link_evidence"][0][
        "transport_anomaly"
    ] == "rdma_retransmission"


def test_r5_g1_g2_order_preserves_each_fact_view():
    def evaluate(groups):
        result = attribute_cluster_stragglers_and_links(collective_groups=groups)
        rank_view = {
            (item["step"], item["collective_op"]): item
            for item in result["slow_rank_evidence"]
        }
        link_view = {
            (item["step"], item["collective_op"]): item
            for item in result["slow_link_evidence"]
        }
        return result, rank_view, link_view

    result, rank_view, link_view = evaluate([_r5_g1(), _r5_g2()])
    assert set(rank_view) == {(2, "hcom_allReduce")}
    assert set(link_view) == {(1, "hcom_allToAllV"), (2, "hcom_allReduce")}
    assert link_view[(1, "hcom_allToAllV")]["bottleneck_rank_ids"] == ["rank_0"]
    assert link_view[(2, "hcom_allReduce")]["bottleneck_rank_ids"] == ["rank_1"]
    assert result["slow_link_rank_union"] == ["rank_0", "rank_1"]
    assert result["primary_slow_link_ranks"] == ["rank_0", "rank_1"]
    assert {item["finding_type"] for item in result["findings"]} == {
        "cluster_slow_rank_straggler",
        "cluster_slow_communication_link",
    }

    _result2, rank_view2, link_view2 = evaluate([_r5_g2(), _r5_g1()])
    assert set(rank_view2) == set(rank_view)
    assert set(link_view2) == set(link_view)
    assert link_view2[(1, "hcom_allToAllV")]["bottleneck_rank_ids"] == ["rank_0"]
    assert link_view2[(2, "hcom_allReduce")]["bottleneck_rank_ids"] == ["rank_1"]


def test_r5_pure_slow_rank_and_link_coexist_after_primary_changes():
    pure_slow_rank = {
        "step": 3,
        "collective_op": "hcom_allReduce",
        "transport": "RDMA",
        "ranks": [
            {"rank_id": "rank_0", "start_ms": 0.010, "end_ms": 0.025,
             "size_bytes": 40_000, "transit_ns": 1_000,
             "clock": _mapped_clock("D0")},
            {"rank_id": "rank_1", "start_ms": 0.024, "end_ms": 0.0251,
             "size_bytes": 40_000, "transit_ns": 1_000,
             "clock": _mapped_clock("D1")},
        ],
    }
    result = attribute_cluster_stragglers_and_links(
        collective_groups=[_r5_g1(), pure_slow_rank]
    )
    assert result["collectives"][0]["classification"] == "slow_link"
    assert result["collectives"][1]["classification"] == "slow_rank"
    assert result["primary_classification"] == "slow_rank"
    assert result["slow_link_rank_union"] == ["rank_0"]
    assert result["primary_slow_link_ranks"] == ["rank_0"]
    assert [item["perpetrator_rank_id"] for item in result["slow_rank_evidence"]] == [
        "rank_1"
    ]
    finding_types = {item["finding_type"] for item in result["findings"]}
    assert finding_types == {
        "cluster_slow_rank_straggler",
        "cluster_slow_communication_link",
    }


def test_explicit_ratio_and_validity_mapping_is_opt_in():
    clock = ClockDomain(
        domain="D0",
        unit="ns",
        scale_ns=1,
        offset_ns=100,
        reference_domain="global_ns",
        reference_scale_num=2,
        reference_scale_den=1,
        valid_from_ns=10,
        valid_to_ns=100,
        source="explicit caller mapping with validity; not inferred",
    )
    base = _event("rank_0", "D0", 0, 1, offset_us=0)
    event = replace(base, start_ns=10, end_ns=20, clock=clock)
    assert event.reference_interval_ns() == (120, 140)
    assert clock.to_reference_ns(101) is None
    assert clock.to_reference_ns(9) is None
    assert clock.as_dict()["reference_scale_num"] == 2
    assert clock.as_dict()["valid_to_ns"] == 100


def _ratio_group(scale_num: int):
    return {
        "step": 1,
        "collective_op": "hcom_allReduce",
        "transport": "RDMA",
        "ranks": [
            {"rank_id": "rank_0", "start_ms": 0.0,
             "end_ms": 0.020 / scale_num, "size_bytes": 40_000,
             "transit_ns": 1_000,
             "clock": ClockDomain(
                 domain="D0", unit="us", scale_ns=1000, offset_ns=0,
                 reference_domain="global_ns",
                 reference_scale_num=scale_num, reference_scale_den=1,
                 source="explicit ratio mapping; not inferred",
             )},
            {"rank_id": "rank_1", "start_ms": 0.005 / scale_num,
             "end_ms": 0.020 / scale_num, "size_bytes": 40_000,
             "transit_ns": 1_000,
             "clock": ClockDomain(
                 domain="D1", unit="us", scale_ns=1000, offset_ns=0,
                 reference_domain="global_ns",
                 reference_scale_num=scale_num, reference_scale_den=1,
                 source="explicit ratio mapping; not inferred",
             )},
        ],
    }


def test_ratio_mapping_drives_the_same_reference_view_for_attribution():
    one = attribute_cluster_stragglers_and_links(
        collective_groups=[_ratio_group(1)]
    )["collectives"][0]
    two = attribute_cluster_stragglers_and_links(
        collective_groups=[_ratio_group(2)]
    )["collectives"][0]
    for item in (one, two):
        assert item["clock_relation"] == "sourced_reference"
        assert item["launch_skew_ms"] == pytest.approx(0.005)
        assert item["end_skew_ms"] == pytest.approx(0.0)
        assert item["max_duration_ms"] == pytest.approx(0.020)
        assert item["duration_skew_ms"] == pytest.approx(0.005)
        assert item["duration_domain"] == "reference"
        assert item["classification"] == "link_attribution_unknown"
        assert item["perpetrator_rank_id"] is None
        assert item["link_bottleneck_rank_ids"] == []
    assert one["rank_link_facts"]["rank_0"]["local_duration_ms"] == pytest.approx(0.020)
    assert one["rank_link_facts"]["rank_1"]["local_duration_ms"] == pytest.approx(0.015)
    assert two["rank_link_facts"]["rank_0"]["local_duration_ms"] == pytest.approx(0.010)
    assert two["rank_link_facts"]["rank_1"]["local_duration_ms"] == pytest.approx(0.0075)
    assert two["rank_link_facts"]["rank_0"]["comparison_duration_ms"] == pytest.approx(0.020)
    assert two["rank_link_facts"]["rank_1"]["comparison_duration_ms"] == pytest.approx(0.015)

    result_one = attribute_cluster_stragglers_and_links(
        collective_groups=[_ratio_group(1)]
    )
    result_two = attribute_cluster_stragglers_and_links(
        collective_groups=[_ratio_group(2)]
    )
    for result in (result_one, result_two):
        assert result["slow_rank_evidence"] == []
        assert result["slow_link_evidence"] == []
        assert result["primary_straggler_rank_id"] is None
        assert not any(
            finding["finding_type"] in {
                "cluster_slow_rank_straggler",
                "cluster_slow_communication_link",
            }
            for finding in result["findings"]
        )


def test_ratio_validity_outside_range_falls_back_to_local_facts_only():
    group = _ratio_group(2)
    for rank in group["ranks"]:
        rank["clock"] = replace(
            rank["clock"], valid_from_ns=0, valid_to_ns=8_000
        )
    # rank0 ends at 10000 local ns > 8000, so mapping is unavailable.
    result = attribute_cluster_stragglers_and_links(
        collective_groups=[group]
    )["collectives"][0]
    assert result["clock_relation"] == "unavailable_clock_relation"
    assert result["duration_domain"] == "local"
    assert result["max_duration_ms"] == pytest.approx(0.010)
    assert result["duration_skew_ms"] == pytest.approx(0.0025)
    assert result["rank_link_facts"]["rank_0"]["local_duration_ms"] == pytest.approx(0.010)
    assert result["classification"] == "clock_unverified"


def test_cross_rank_stats_public_entry_uses_ratio_reference_span():
    def event(rank_id, start_us, duration_us):
        base = _event(rank_id, rank_id, start_us, duration_us, offset_us=0)
        return replace(
            base,
            clock=ClockDomain(
                domain=rank_id, unit="us", scale_ns=1000, offset_ns=0,
                reference_domain="global_ns",
                reference_scale_num=2, reference_scale_den=1,
                source="explicit ratio mapping; not inferred",
            ),
        )

    observations = [
        _observation("rank_0", [event("rank_0", 0, 10)]),
        _observation(
            "rank_1",
            [replace(event("rank_1", 2, 8), start_ns=2_500, end_ns=10_000)],
        ),
    ]
    stats = cross_rank_stats(observations)
    assert stats["cross_rank_union_span"]["status"] == "available"
    assert stats["cross_rank_union_span"]["span_ns"] == 20_000
    attribution = stats["straggler_and_link_attribution"]
    assert attribution["collectives"][0]["duration_domain"] == "reference"
    assert attribution["collectives"][0]["classification"] == "link_attribution_unknown"


def _ref_clock(domain: str, scale_num: int) -> ClockDomain:
    return ClockDomain(
        domain=domain,
        unit="ns",
        scale_ns=1,
        offset_ns=0,
        reference_domain="global_ns",
        reference_scale_num=scale_num,
        reference_scale_den=1,
        source="explicit ratio mapping; not inferred",
    )


def _obs_with_window(rank_id, events, window):
    return Observation(
        rank_id=rank_id,
        rank_index=int(rank_id.rsplit("_", 1)[1]),
        window=window,
        accounting=account_window(events, window),
        events=events,
        source=SourceRef(
            rank_id=rank_id,
            rank_index=int(rank_id.rsplit("_", 1)[1]),
            kind="synthetic_capture",
            path="capture.db",
            basename="capture.db",
            sha256=None,
            size_bytes=0,
            schema_version="test",
            schema_variant="test",
        ),
        stats=QueryStats(rank_id=rank_id, window_label=str(window.label)),
    )


def _collective_observation_pair(scale_num: int):
    clock_0 = _ref_clock("D0", 1)
    clock_1 = _ref_clock("D1", scale_num)
    base = _event("rank_0", "D0", 0, 1, offset_us=0)
    rank_0_events = [
        replace(
            base, rank_id="rank_0", rank_index=0, name="compute_0",
            op_type="Compute", task_type="AI_VECTOR_CORE", core="AI_VECTOR_CORE",
            start_ns=0, end_ns=8_000, block="Vector", is_comm=False,
            clock=clock_0,
        ),
        replace(
            base, rank_id="rank_0", rank_index=0, name="hcom_allReduce",
            op_type="hcom_allReduce", task_type="COMMUNICATION",
            core="COMMUNICATION", start_ns=10_000, end_ns=30_000,
            block="Comm", is_comm=True, clock=clock_0,
        ),
    ]
    rank_1_events = [
        replace(
            base, rank_id="rank_1", rank_index=1, name="compute_1",
            op_type="Compute", task_type="AI_VECTOR_CORE", core="AI_VECTOR_CORE",
            start_ns=0, end_ns=15_000 // scale_num, block="Vector",
            is_comm=False, clock=clock_1,
        ),
        replace(
            base, rank_id="rank_1", rank_index=1, name="hcom_allReduce",
            op_type="hcom_allReduce", task_type="COMMUNICATION",
            core="COMMUNICATION", start_ns=20_000 // scale_num,
            end_ns=30_000 // scale_num, block="Comm", is_comm=True,
            clock=clock_1,
        ),
    ]
    return [
        _obs_with_window("rank_0", rank_0_events, Window(0, 30_000, step=1, label="s1")),
        _obs_with_window("rank_1", rank_1_events,
                         Window(0, 30_000 // scale_num, step=1, label="s1")),
    ]


def test_reference_projection_drives_preceding_compute_and_gap():
    rows = {}
    for scale_num in (1, 2):
        result = attribute_cluster_stragglers_and_links(
            observations=_collective_observation_pair(scale_num)
        )
        group = result["collectives"][0]
        rows[scale_num] = group
        assert group["classification"] == "slow_rank"
        assert group["perpetrator_rank_id"] == "rank_1"
        assert group["victim_rank_ids"] == ["rank_0"]
        assert group["straggler_cause"] == "compute_straggler"
        assert group["launch_skew_ms"] == pytest.approx(0.010)
        assert group["end_skew_ms"] == pytest.approx(0.0)
        assert group["max_duration_ms"] == pytest.approx(0.020)
        assert group["duration_skew_ms"] == pytest.approx(0.010)
        assert cross_rank_union_span(_collective_observation_pair(scale_num))["span_ns"] == 30_000
        assert group["preceding_time_domain"] == ["reference"]
        assert group["preceding_compute_ns_by_rank"] == {
            "rank_0": 8_000, "rank_1": 15_000
        }
        assert group["preceding_host_gap_ns_by_rank"] == {
            "rank_0": 2_000, "rank_1": 5_000
        }
        assert group["local_preceding_compute_ns_by_rank"]["rank_0"] == 8_000
        assert group["local_preceding_compute_ns_by_rank"]["rank_1"] == 15_000 // scale_num
        assert group["local_preceding_host_gap_ns_by_rank"]["rank_0"] == 2_000
        assert group["local_preceding_host_gap_ns_by_rank"]["rank_1"] == 5_000 // scale_num
    assert rows[1]["preceding_compute_ns_by_rank"]["rank_1"] == rows[2]["preceding_compute_ns_by_rank"]["rank_1"]
    assert rows[1]["preceding_host_gap_ns_by_rank"]["rank_1"] == rows[2]["preceding_host_gap_ns_by_rank"]["rank_1"]


def _moe_observation_pair(scale_num: int):
    clock_0 = _ref_clock("D0", 1)
    clock_1 = _ref_clock("D1", scale_num)
    base = _event("rank_0", "D0", 0, 1, offset_us=0)
    rank_0 = [
        replace(
            base, rank_id="rank_0", rank_index=0, name="moe_0",
            op_type="GroupedMatmul", start_ns=0, end_ns=20_000,
            block="MoE", is_comm=False, clock=clock_0,
        )
    ]
    rank_1 = [
        replace(
            base, rank_id="rank_1", rank_index=1, name="moe_1",
            op_type="GroupedMatmul", start_ns=0, end_ns=30_000 // scale_num,
            block="MoE", is_comm=False, clock=clock_1,
        )
    ]
    return [
        _obs_with_window("rank_0", rank_0, Window(0, 20_000, step=1, label="s1")),
        _obs_with_window("rank_1", rank_1,
                         Window(0, 30_000 // scale_num, step=1, label="s1")),
    ]


def test_cross_rank_stats_and_ep_use_reference_wall_and_moe_duration():
    local_cv = {}
    for scale_num in (1, 2):
        observations = _moe_observation_pair(scale_num)
        stats = cross_rank_stats(observations)
        assert stats["comparison_domain"] == "global_ns"
        assert stats["wall_skew_ms"] == pytest.approx(0.010)
        assert stats["wall_ratio"] == pytest.approx(1.5)
        assert stats["slowest_rank"]["rank_id"] == "rank_1"
        assert stats["slowest_rank"]["dominant_excess_block"] == "MoE"
        assert stats["slowest_rank"]["dominant_excess_ms"] == pytest.approx(0.010)
        assert stats["cross_rank_union_span"]["span_ns"] == 30_000
        by_rank = {row["rank_id"]: row for row in stats["rank_summaries"]}
        assert by_rank["rank_1"]["wall_ms_p50"] == pytest.approx(0.030)
        assert by_rank["rank_1"]["local_wall_ms_p50"] == pytest.approx(
            0.030 if scale_num == 1 else 0.015
        )
        assert by_rank["rank_1"]["block_union_ms_p50"]["MoE"] == pytest.approx(0.030)
        ep = stats["ep_load_balance"]
        assert ep["duration_domain"] == "global_ns"
        assert ep["duration_cv"] == pytest.approx(0.2)
        local_cv[scale_num] = ep["local_duration_cv"]
        assert ep["local_duration_cv"] == pytest.approx(
            0.2 if scale_num == 1 else 0.142857
        )
    assert local_cv[1] != local_cv[2]


def test_only_preceding_interval_out_of_validity_keeps_collective_without_cause():
    observations = _collective_observation_pair(1)
    rank_1 = observations[1]
    compute = rank_1.events[0]
    comm = rank_1.events[1]
    rank_1.events[:] = [comm, replace(
        compute,
        clock=replace(compute.clock, valid_from_ns=0, valid_to_ns=10_000),
    )]
    rank_1.accounting = account_window(rank_1.events, rank_1.window)
    result = attribute_cluster_stragglers_and_links(observations=observations)
    group = result["collectives"][0]
    assert group["classification"] == "slow_rank"
    assert group["perpetrator_rank_id"] == "rank_1"
    assert group["victim_rank_ids"] == ["rank_0"]
    assert group["straggler_cause"] is None
    assert set(group["preceding_time_domain"]) == {"reference", "unavailable"}
    assert group["preceding_compute_ns_by_rank"]["rank_1"] == 15_000
    assert group["preceding_host_gap_ns_by_rank"]["rank_1"] == 5_000
    assert result["primary_straggler_cause"] is None


def _coverage_event(rank, start, end, *, reference="R", valid=(10, 100), scale=2):
    base = _event(rank, rank, 0, 1, offset_us=0)
    return replace(
        base,
        start_ns=start,
        end_ns=end,
        clock=ClockDomain(
            domain=f"D_{rank}", unit="ns", scale_ns=1,
            offset_ns=(100 if reference is not None else None),
            reference_domain=reference,
            reference_scale_num=(scale if reference is not None else 1),
            reference_scale_den=1, valid_from_ns=valid[0], valid_to_ns=valid[1],
            source="explicit synthetic synchronization anchor",
        ),
    )


def _coverage_obs(rank, start, end, *, window=(0, 200), reference="R",
                  valid=(10, 100), scale=2):
    event = _coverage_event(rank, start, end, reference=reference,
                            valid=valid, scale=scale)
    win = Window(window[0], window[1], step=1, label="coverage")
    return _obs_with_window(rank, [event], win)


def test_union_coverage_counts_and_reference_failure_reasons():
    outside = cross_rank_union_span([
        _coverage_obs("rank_0", 101, 111, window=(100, 120)),
    ])
    assert outside["event_count"] == 1
    assert outside["window_event_count"] == 1
    assert outside["mapped_event_count"] == 0
    assert outside["unmapped_event_count"] == 1
    assert outside["actual_reference_domain"] == "R"
    assert outside["span_ns"] is None
    assert outside["failure_reason"] == "outside_validity"
    assert outside["reference_available"] is False
    assert cross_rank_stats([
        _coverage_obs("rank_0", 101, 111, window=(100, 120)),
    ])["cross_rank_union_span"]["mapped_event_count"] == 0

    clipped = cross_rank_union_span([
        _coverage_obs("rank_0", 90, 110, window=(90, 100)),
    ])
    assert clipped["event_count"] == 1
    assert clipped["mapped_event_count"] == 1
    assert clipped["span_ns"] == 20
    assert clipped["actual_reference_domain"] == "R"
    assert clipped["reason"] is None

    interior = cross_rank_union_span([
        _coverage_obs("rank_0", 10, 20, window=(10, 20)),
    ])
    assert interior["span_ns"] == 20
    assert interior["mapped_endpoint_count"] == 2


def test_union_coverage_reports_partial_mismatch_and_no_mapping():
    partial = cross_rank_union_span([
        _coverage_obs("rank_0", 90, 100, valid=(10, 100)),
        _coverage_obs("rank_1", 90, 100, valid=(10, 20)),
    ])
    assert partial["event_count"] == 2
    assert partial["mapped_event_count"] == 1
    assert partial["unmapped_event_count"] == 1
    assert partial["mapped_rank_count"] == 1
    assert partial["unmapped_rank_ids"] == ["rank_1"]
    assert partial["span_ns"] is None
    assert partial["failure_reason"] == "outside_validity"
    assert partial["reference_available"] is False

    mismatch = cross_rank_union_span([
        _coverage_obs("rank_0", 10, 20, reference="R0"),
        _coverage_obs("rank_1", 10, 20, reference="R1"),
    ])
    assert mismatch["mapped_event_count"] == 2
    assert mismatch["declared_reference_domains"] == ["R0", "R1"]
    assert mismatch["span_ns"] is None
    assert mismatch["failure_reason"] == "reference_domain_mismatch"

    no_mapping = cross_rank_union_span([
        _coverage_obs("rank_0", 10, 20, reference=None),
    ])
    assert no_mapping["event_count"] == 1
    assert no_mapping["mapped_event_count"] == 0
    assert no_mapping["actual_reference_domain"] is None
    assert no_mapping["failure_reason"] == "no_reference_mapping"
    assert no_mapping["span_ns"] is None


def _mixed_validity_collective(swap=False):
    def clock(domain, valid_to):
        return ClockDomain(
            domain=domain, unit="ns", scale_ns=1, offset_ns=0,
            reference_domain="R", valid_from_ns=0, valid_to_ns=valid_to,
            source="explicit validity",
        )
    base = _event("rank_0", "D0", 0, 1, offset_us=0)
    r0_clock = clock("D0", 30_000)
    r1_compute_clock = clock("D1", 10_000)
    r1_comm_clock = clock("D1", 30_000)
    r0 = [
        replace(base, rank_id="rank_0", rank_index=0, name="compute_0",
                op_type="Compute", block="Vector", is_comm=False,
                start_ns=0, end_ns=8_000, clock=r0_clock),
        replace(base, rank_id="rank_0", rank_index=0, name="hcom_allReduce",
                op_type="hcom_allReduce", block="Comm", is_comm=True,
                start_ns=10_000, end_ns=30_000, clock=r0_clock),
    ]
    r1_compute = replace(
        base, rank_id="rank_1", rank_index=1, name="compute_1",
        op_type="Compute", block="Vector", is_comm=False,
        start_ns=0, end_ns=15_000, clock=r1_compute_clock,
    )
    r1_comm = replace(
        base, rank_id="rank_1", rank_index=1, name="hcom_allReduce",
        op_type="hcom_allReduce", block="Comm", is_comm=True,
        start_ns=20_000, end_ns=30_000, clock=r1_comm_clock,
    )
    r1 = [r1_comm, r1_compute] if swap else [r1_compute, r1_comm]
    return [
        _obs_with_window("rank_0", r0, Window(0, 30_000, step=1, label="s1")),
        _obs_with_window("rank_1", r1, Window(0, 30_000, step=1, label="s1")),
    ]


def test_window_relation_is_order_independent_and_preceding_failure_is_local():
    for swap in (False, True):
        result = attribute_cluster_stragglers_and_links(
            observations=_mixed_validity_collective(swap)
        )
        group = result["collectives"][0]
        assert group["classification"] == "slow_rank"
        assert group["perpetrator_rank_id"] == "rank_1"
        assert group["victim_rank_ids"] == ["rank_0"]
        assert group["launch_skew_ms"] == pytest.approx(0.010)
        assert group["end_skew_ms"] == pytest.approx(0.0)
        assert group["max_duration_ms"] == pytest.approx(0.020)
        assert group["duration_skew_ms"] == pytest.approx(0.010)
        assert group["straggler_cause"] is None
        assert result["primary_straggler_cause"] is None
        assert group["local_preceding_compute_ns_by_rank"] == {
            "rank_0": 8_000, "rank_1": 15_000
        }
        assert group["local_preceding_host_gap_ns_by_rank"] == {
            "rank_0": 2_000, "rank_1": 5_000
        }
        assert "unavailable" in group["preceding_time_domain"]


def _multidomain_moe_observations():
    base = _event("rank_0", "D0", 0, 1, offset_us=0)
    r0_clock = ClockDomain(
        domain="D0", unit="ns", scale_ns=1, offset_ns=0,
        reference_domain="R", valid_from_ns=0, valid_to_ns=30_000,
        source="explicit",
    )
    r1_clock = ClockDomain(
        domain="D1", unit="ns", scale_ns=1, offset_ns=0,
        reference_domain="R", reference_scale_num=2,
        valid_from_ns=0, valid_to_ns=15_000, source="explicit",
    )
    r1_aux_clock = replace(r1_clock, domain="D1aux")
    r0 = [replace(base, rank_id="rank_0", rank_index=0, name="moe_0",
                  op_type="GroupedMatmul", block="MoE", is_comm=False,
                  start_ns=0, end_ns=20_000, clock=r0_clock)]
    r1 = [
        replace(base, rank_id="rank_1", rank_index=1, name="moe_1a",
                op_type="GroupedMatmul", block="MoE", is_comm=False,
                start_ns=0, end_ns=15_000, clock=r1_clock),
        replace(base, rank_id="rank_1", rank_index=1, name="moe_1b",
                op_type="GroupedMatmul", block="MoE", is_comm=False,
                start_ns=0, end_ns=15_000, clock=replace(r1_clock, valid_to_ns=30_000)),
        replace(base, rank_id="rank_1", rank_index=1, name="aux_a",
                op_type="GroupedMatmul", block="MoE", is_comm=False,
                start_ns=1_000, end_ns=2_000, clock=r1_aux_clock),
        replace(base, rank_id="rank_1", rank_index=1, name="aux_b",
                op_type="GroupedMatmul", block="MoE", is_comm=False,
                start_ns=1_000, end_ns=2_000, clock=replace(r1_aux_clock, valid_to_ns=30_000)),
    ]
    return [
        _obs_with_window("rank_0", r0, Window(0, 20_000, step=1, label="s1")),
        _obs_with_window("rank_1", r1, Window(0, 15_000, step=1, label="s1")),
    ]


def test_multiple_local_domains_map_to_one_reference_for_wall_and_ep():
    observations = _multidomain_moe_observations()
    stats = cross_rank_stats(observations)
    assert stats["comparison_domain"] == "R"
    assert stats["wall_skew_ms"] == pytest.approx(0.010)
    assert stats["wall_ratio"] == pytest.approx(1.5)
    assert stats["slowest_rank"]["rank_id"] == "rank_1"
    ep = stats["ep_load_balance"]
    assert ep["duration_domain"] == "R"
    assert ep["duration_cv"] == pytest.approx(0.2)
    assert ep["hot_expert_rank_id"] == "rank_1"
    assert ep["local_duration_cv"] == pytest.approx(0.142857)
    assert ep["duration_available"] is True

    partial = _multidomain_moe_observations()
    partial[1].events[2] = replace(
        partial[1].events[2],
        clock=replace(partial[1].events[2].clock, valid_to_ns=0),
    )
    partial[1].accounting = account_window(partial[1].events, partial[1].window)
    partial_stats = cross_rank_stats(partial)
    assert partial_stats["comparison_complete"] is False
    assert partial_stats["ep_load_balance"]["duration_available"] is False
    assert partial_stats["ep_load_balance"]["duration_unmapped_event_count"] == 1
    assert partial_stats["wall_skew_ms"] == pytest.approx(0.010)


def test_explicit_window_clock_and_unclassified_groupedmatmul_fallback():
    identity = ClockDomain(
        domain="W", unit="ns", scale_ns=1, offset_ns=0,
        reference_domain="R", valid_from_ns=10_000, valid_to_ns=30_000,
        source="explicit window clock",
    )
    base = _event("rank_0", "W", 0, 1, offset_us=0)
    clock = ClockDomain(
        domain="W", unit="ns", scale_ns=1, offset_ns=0,
        reference_domain="R", valid_from_ns=10_000, valid_to_ns=30_000,
        source="explicit",
    )
    r0 = [replace(base, rank_id="rank_0", rank_index=0, name="moe_0",
                  op_type="GroupedMatmul", start_ns=20_000, end_ns=25_000,
                  block="Unclassified", is_comm=False, clock=clock)]
    r1 = [
        replace(base, rank_id="rank_1", rank_index=1, name="moe_1a",
                op_type="GroupedMatmul", start_ns=0, end_ns=15_000,
                block="Unclassified", is_comm=False, clock=clock),
        replace(base, rank_id="rank_1", rank_index=1, name="moe_1b",
                op_type="GroupedMatmul", start_ns=0, end_ns=15_000,
                block="Unclassified", is_comm=False, clock=clock),
    ]
    window = Window(10_000, 30_000, step=1, label="window", clock=identity)
    observations = [
        _obs_with_window("rank_0", r0, window),
        _obs_with_window("rank_1", r1, window),
    ]
    union = cross_rank_union_span(observations)
    assert union["status"] == "available"
    assert union["span_ns"] == 20_000
    assert union["mapped_window_endpoint_count"] == 4

    # Separate fallback case: local 20/30us, no tokens, unclassified.
    fb_clock = ClockDomain(
        domain="F", unit="ns", scale_ns=1, offset_ns=0,
        reference_domain="R", valid_from_ns=0, valid_to_ns=30_000,
        source="explicit",
    )
    fb_base = _event("rank_0", "F", 0, 1, offset_us=0)
    fb_obs = [
        _obs_with_window("rank_0", [replace(
            fb_base, rank_id="rank_0", rank_index=0, name="gm_0",
            op_type="GroupedMatmul", start_ns=0, end_ns=20_000,
            block="Unclassified", is_comm=False, clock=fb_clock,
        )], Window(0, 20_000, step=1, label="s1")),
        _obs_with_window("rank_1", [replace(
            fb_base, rank_id="rank_1", rank_index=1, name="gm_1",
            op_type="GroupedMatmul", start_ns=0, end_ns=30_000,
            block="Unclassified", is_comm=False, clock=fb_clock,
        )], Window(0, 30_000, step=1, label="s1")),
    ]
    ep = evaluate_ep_load_balance(fb_obs)
    assert ep["duration_cv"] == pytest.approx(0.2)
    assert ep["straggler_to_median_ratio"] == pytest.approx(1.2)
    assert ep["hot_expert_rank_id"] == "rank_1"
    assert ep["eplb_recommended"] is True
    assert ep["duration_available"] is True
    assert ep["per_rank_moe_compute_ms_p50"]["rank_0"] == pytest.approx(0.020)
    assert ep["per_rank_moe_compute_ms_p50"]["rank_1"] == pytest.approx(0.030)
