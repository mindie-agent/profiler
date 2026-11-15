"""ACLGraph DAG, multi-stream diagnostics, memory-evidence, and MCP contracts.

[Role]
  Exercise all NR-S9 `mindie_profiler` surfaces (`aclgraph_dag`, `aclgraph_schema`,
  `aclgraph_multistream`, `aclgraph_mcp`, and `memory_evidence` service helpers)
  without requiring `mindie_knowledge` in the `profiler` repository test suite.
[Invariants]
  Every MCP response stays <= 250 UTF-8 bytes and <= 250 BPE tokens; invalid
  DAGs and non-boolean flags fail closed.
[Timeouts & Locks]
  Pure in-memory deterministic checks; < 2s runtime.
[Side-Effect Policy]
  Read-only in-memory execution; writes no files.
"""

from __future__ import annotations

import importlib
import inspect
import random
from dataclasses import fields, replace

import pytest

from mindie_profiler import aclgraph_multistream as multistream
from mindie_profiler.aclgraph_mcp import (
    TOOL_SPECS as ACL_SPECS,
    aclgraph_diagnose,
    aclgraph_launch_floor,
    aclgraph_superkernel,
    call_tool as acl_call,
)
from mindie_profiler.aclgraph_multistream import (
    ACLGraphModelError,
    ACLGraphWrapperModel,
    BreakableACLGraphWrapperModel,
    ParallelRegion,
    StreamInterval,
    UpdatableGraphModel,
    check_superkernel_eligibility,
    classify_capture_error,
    diagnose_region,
    effective_launch_floor_us,
)
from mindie_profiler.memory_evidence import region_memory_service
from mindie_sim.opflow.token_budget import envelope_size

BAD_BOOLS = (0, 1, 2, -1, 0.0, 1.0, "", "true", "false", None, [], {}, (True,))


def fork_graph() -> dict:
    return dict(
        name="fork",
        capture_root_stream_id=0,
        nodes=[
            dict(id="fork", stream_id=0, duration_us=2, records=["enter"]),
            dict(id="a", stream_id=1, duration_us=10, waits=["enter"], records=["ae"]),
            dict(id="b", stream_id=2, duration_us=6, waits=["enter"], records=["be"]),
            dict(id="join", stream_id=0, duration_us=3, waits=["ae", "be"]),
        ],
    )


def event_graph(release: float, *, observed: bool = False) -> dict:
    return dict(
        name="event",
        event_causality_observed=observed,
        nodes=[
            dict(id="a", stream_id=0, start_us=0, end_us=10),
            dict(id="b", stream_id=1, start_us=release, end_us=release + 10),
        ],
        events=[dict(id="e", record="a", wait="b")],
    )


def test_aclgraph_mcp_token_budgets_and_compact_identity() -> None:
    assert len(ACL_SPECS) == 4
    acl_calls = [
        (
            "aclgraph_diagnose",
            {
                "region": {
                    "name": "n" * 5000,
                    "branch_a": {"op": "a", "stream_id": 0, "start_us": 0, "end_us": 1},
                    "branch_b": {"op": "b", "stream_id": 0, "start_us": 0, "end_us": 1},
                }
            },
        ),
        (
            "aclgraph_diagnose",
            {
                "region": {
                    "name": "r",
                    "branch_a": {"op": "AllReduce", "stream_id": 0, "start_us": 0, "end_us": 10},
                    "branch_b": {"op": "dispatch", "stream_id": 1, "start_us": 0, "end_us": 10},
                }
            },
        ),
        (
            "aclgraph_sq_budget",
            {"captured_batch_sizes": 8, "subgraphs_per_step": 32, "active_streams_per_graph": 16},
        ),
        ("aclgraph_superkernel", {"static_decode": True}),
        ("aclgraph_launch_floor", {"mode": "full"}),
        ("aclgraph_launch_floor", {"mode": "bad_backend", "superkernel": True}),
        ("missing", {}),
    ]
    for name, arguments in acl_calls:
        result = acl_call(name, arguments)
        size = envelope_size(result)
        assert size["utf8_bytes"] <= 250, (name, size)
        assert size["token_estimate"] <= 250, (name, size)
        assert result.get("err") != "EBUDGET"


def test_aclgraph_draft_evidence_and_mode_order() -> None:
    assert ACLGraphWrapperModel(use_eagle=True).replay_sync_required is True
    assert ACLGraphWrapperModel(use_eagle=True, is_draft_model=True).replay_sync_required is False
    assert UpdatableGraphModel(use_eagle=True).needs_sync is True
    assert UpdatableGraphModel(use_eagle=True, is_draft_model=True).needs_sync is False
    a = StreamInterval("vector_a", 0, 0, 10, aiv_blocks=40, io_bytes=1024)
    b = StreamInterval("vector_b", 1, 20, 30, aiv_blocks=0, io_bytes=1024)
    diag = diagnose_region(ParallelRegion("no_events", a, b, event_pairs=0))
    assert diag.cause != "premature_event_record_wait"
    vectors = diagnose_region(ParallelRegion("two_vectors", a, b, event_pairs=0))
    assert vectors.cause != "hccl_aiv_expansion_steals_vector_cores"
    hccl = diagnose_region(
        ParallelRegion(
            "hccl",
            StreamInterval("AllReduce", 0, 0, 10, aiv_blocks=40, io_bytes=4096),
            StreamInterval("dispatch", 1, 0, 10, aiv_blocks=30, io_bytes=4096),
            aiv_cores=64,
        )
    )
    assert hccl.code == "A3" and "hccl_aiv" in hccl.cause
    assert hccl.evidence_grade in ("supported_hypothesis", "observed", "confirmed")
    dangling = diagnose_region(
        ParallelRegion(
            "dangling",
            a,
            StreamInterval("b", 1, 0, 10, waits_on_capture_root=False),
            capture_root_stream_id=0,
        )
    )
    assert dangling.code == "A5"
    assert effective_launch_floor_us("aclgraph_superkernel") == 0.32
    assert effective_launch_floor_us("superkernel") == 0.32
    with pytest.raises(ACLGraphModelError):
        effective_launch_floor_us("bad_backend", superkernel=True)
    with pytest.raises(ACLGraphModelError):
        effective_launch_floor_us("piecewise", superkernel=True)
    assert classify_capture_error("error 207008 stream resources are insufficient") == "stream_resource_207008"
    assert classify_capture_error("Alloc sq cq fail") == "old_hdk_alloc_sq_cq"


def test_multistream_dag_critical_path_and_root_closure() -> None:
    region = ParallelRegion.from_mapping(fork_graph())
    result = diagnose_region(region)
    assert result.code == "OK"
    assert result.span_us == 15
    assert result.wall_us == 18
    assert result.net_speedup_us == 3
    assert result.details["event_us"] == 3
    assert result.details["event_count"] == 3
    assert result.details["overlap_us"] == 6
    assert result.details["capture_hazards"] == ()
    mcp = aclgraph_diagnose(fork_graph())
    assert mcp["ok"] == 1 and mcp["wall"] == 18 and mcp["net"] == 3


def test_records_waits_and_event_forms_are_equivalent() -> None:
    base = fork_graph()
    variants = []
    for style in ("events", "records"):
        payload = fork_graph()
        for node in payload["nodes"]:
            node.pop("records", None)
            node.pop("waits", None)
        if style == "events":
            payload["events"] = [
                dict(id="enter", record="fork", wait=["a", "b"]),
                dict(id="ae", record="a", wait="join"),
                dict(id="be", record="b", wait="join"),
            ]
        else:
            payload["records"] = [dict(id=e, node=n) for e, n in (("enter", "fork"), ("ae", "a"), ("be", "b"))]
            payload["waits"] = [
                dict(id=e, node=n) for e, n in (("enter", "a"), ("enter", "b"), ("ae", "join"), ("be", "join"))
            ]
        variants.append(payload)
    for payload in variants:
        assert diagnose_region(payload).wall_us == diagnose_region(base).wall_us
        assert diagnose_region(payload).details["edges"] == diagnose_region(base).details["edges"]


@pytest.mark.parametrize(
    "bad",
    [
        "region_key",
        "node_key",
        "missing_record",
        "orphan_record",
        "duplicate_record",
        "duplicate_wait",
        "duplicate_node",
        "dangling",
        "cycle",
        "stream_cycle",
        "event_key",
        "record_key",
        "wait_key",
        "dependency_key",
        "wrong_bool",
        "wrong_sequence",
    ],
)
def test_invalid_graph_evidence_fails_closed(bad: str) -> None:
    g = fork_graph()
    if bad == "region_key":
        g["surprise"] = 1
    if bad == "node_key":
        g["nodes"][0]["surprise"] = 1
    if bad == "missing_record":
        g["nodes"][0]["records"] = []
    if bad == "orphan_record":
        g["nodes"][0]["records"].append("unused")
    if bad == "duplicate_record":
        g["nodes"][1]["records"].append("enter")
    if bad == "duplicate_wait":
        g["nodes"][1]["waits"].append("enter")
    if bad == "duplicate_node":
        g["nodes"].append(g["nodes"][0])
    if bad == "dangling":
        g["dependencies"] = [["absent", "a"]]
    if bad == "cycle":
        g["dependencies"] = [["a", "b"], ["b", "a"]]
    if bad == "stream_cycle":
        g["dependencies"] = [["join", "fork"]]
    if bad == "event_key":
        g["events"] = [dict(id="z", record="fork", wait="a", typo=0)]
    if bad == "record_key":
        g["records"] = [dict(id="z", node="fork", typo=0)]
    if bad == "wait_key":
        g["waits"] = [dict(id="z", node="a", typo=0)]
    if bad == "dependency_key":
        g["dependencies"] = [dict(source="a", target="b", typo=0)]
    if bad == "wrong_bool":
        g["piece_boundary_between"] = "false"
    if bad == "wrong_sequence":
        g["events"] = False
    with pytest.raises(ValueError):
        ParallelRegion.from_mapping(g)
    assert aclgraph_diagnose(g)["ok"] == 0


def test_dependency_serialization_and_release_intervals() -> None:
    g = dict(
        name="serial",
        intervals=[
            dict(id="a", stream_id=0, start_us=20, end_us=23),
            dict(id="b", stream_id=1, start_us=20, end_us=24),
            dict(id="c", stream_id=2, start_us=20, end_us=25),
        ],
        dependencies=[["a", "b"], ["b", "c"]],
    )
    result = diagnose_region(g)
    assert result.span_us == result.wall_us == 12
    assert result.net_speedup_us == result.overlap_pct == 0
    assert result.details["starts_us"] == {"a": 0, "b": 3, "c": 7}


def test_generated_dags_match_independent_longest_paths() -> None:
    rng = random.Random(902)
    for _ in range(60):
        nodes, edges, previous = [], set(), {}
        finish = {}
        for i in range(12):
            stream, duration = rng.randrange(3), rng.randrange(1, 10)
            preds = {j for j in range(i) if rng.random() < 0.12}
            if stream in previous:
                preds.add(previous[stream])
            previous[stream] = i
            edges.update((j, i) for j in preds)
            finish[i] = max((finish[j] for j in preds), default=0) + duration
            nodes.append(dict(id=str(i), stream_id=stream, duration_us=duration))
        result = diagnose_region(
            dict(name="random", nodes=nodes, dependencies=[[str(a), str(b)] for a, b in sorted(edges)])
        )
        assert result.wall_us == max(finish.values())
        assert result.net_speedup_us == sum(x["duration_us"] for x in nodes) - result.wall_us


def test_capture_root_exemption_and_nonroot_join() -> None:
    root = StreamInterval("root", 0, 0, 10, waits_on_capture_root=False, joined_at_exit=False)
    other = StreamInterval("other", 1, 0, 10)
    assert diagnose_region(ParallelRegion("r", root, other, capture_root_stream_id=0)).code != "A5"
    for key in ("waits_on_capture_root", "joined_at_exit"):
        assert (
            diagnose_region(
                ParallelRegion("r", root, replace(other, **{key: False}), capture_root_stream_id=0)
            ).code
            == "A5"
        )
    g = fork_graph()
    g["nodes"][-1]["waits"].remove("be")
    g["nodes"][2].pop("records")
    assert diagnose_region(g).code == "A5"


def test_mixed_memory_and_declared_scopes() -> None:
    a = StreamInterval("a", 0, 0, 10, read_bytes=10**9, write_bytes=10**9)
    b = StreamInterval("b", 1, 0, 10, io_bytes=64)
    service, detail = region_memory_service(a, b, ParallelRegion("r", a, b))
    assert detail["read_service_bytes"] == detail["write_service_bytes"] == 10**9
    assert detail["unknown_direction_bytes"] == 64
    assert service == pytest.approx(812.50004)

    ca = StreamInterval("a", 0, 0, 10, io_bytes=256, read_bytes=256, write_bytes=0, unique_bytes=64)
    cb = StreamInterval("b", 1, 0, 10, read_bytes=0, write_bytes=0, unique_bytes=0)
    diag = diagnose_region(ParallelRegion("cache", ca, cb, event_pairs=0))
    assert diag.details["unique_bytes"] == 64
    assert diag.details["read_service_bytes"] == 256
    assert diag.details["write_service_bytes"] == 0
    legacy = diagnose_region(ParallelRegion("unknown", StreamInterval("a", 0, 0, 10, io_bytes=256), cb, event_pairs=0))
    assert legacy.details["unique_bytes"] is None
    assert legacy.details["memory_evidence"] == "io_total_upper_bound"


@pytest.mark.parametrize("release", [11.5, 20, 100])
@pytest.mark.parametrize("observed", [False, True])
def test_nonbinding_event_does_not_override_release_evidence(release: float, observed: bool) -> None:
    graph = event_graph(release, observed=observed)
    actual = diagnose_region(graph)
    base = diagnose_region(dict(graph, events=[]))
    assert actual.wall_us == base.wall_us == release + 10
    assert actual.details["starts_us"] == base.details["starts_us"]
    assert actual.details["event_us"] == 0
    assert actual.details["cross_stream_event_delays_us"] == {}
    assert actual.cause == "insufficient_trace_evidence_for_event_attribution"
    assert actual.evidence_grade == "observed"
    envelope = aclgraph_diagnose(graph)
    assert envelope["ok"] == 1 and envelope["grade"] == "observed"


@pytest.mark.parametrize("observed", [False, True])
def test_binding_event_requires_causal_evidence_for_confirmation(observed: bool) -> None:
    result = diagnose_region(event_graph(0, observed=observed))
    assert result.wall_us == 21.5 and result.details["event_us"] == 1.5
    assert result.details["cross_stream_event_delays_us"] == {"b": 11.5}
    assert result.cause == "premature_event_record_wait"
    assert result.evidence_grade == ("confirmed" if observed else "supported_hypothesis")


def test_event_binding_off_critical_path_and_same_stream_control() -> None:
    graph = event_graph(0, observed=True)
    graph["nodes"].append(dict(id="long", stream_id=2, start_us=100, end_us=200))
    result = diagnose_region(graph)
    assert result.details["event_us"] == 0
    assert result.details["cross_stream_event_delays_us"] == {"b": 11.5}
    assert result.evidence_grade == "confirmed"
    graph["dependencies"] = [["a", "b"]]
    result = diagnose_region(graph)
    assert result.details["cross_stream_event_delays_us"] == {"b": 1.5}

    local_graph = dict(
        name="local",
        event_causality_observed=True,
        nodes=[
            dict(id="a", stream_id=0, duration_us=10),
            dict(id="b", stream_id=0, duration_us=10),
            dict(id="c", stream_id=1, start_us=30, end_us=40),
        ],
        events=[dict(id="e", record="a", wait="b")],
    )
    local_result = diagnose_region(local_graph)
    assert local_result.details["cross_stream_event_delays_us"] == {}
    assert local_result.cause == "insufficient_trace_evidence_for_event_attribution"


@pytest.mark.parametrize("bad", BAD_BOOLS)
def test_aclgraph_boolean_parameters_and_dataclass_fields_reject_non_bools(bad: object) -> None:
    region = ParallelRegion.from_mapping(event_graph(0))
    records = [
        region,
        region.dag,
        region.dag.nodes[0].interval,
        check_superkernel_eligibility(True),
        ACLGraphWrapperModel(),
        BreakableACLGraphWrapperModel(),
        UpdatableGraphModel(),
    ]
    for record in records:
        for f in fields(record):
            if f.type is bool or f.type == "bool":
                with pytest.raises(ValueError):
                    replace(record, **{f.name: bad})
    for fn, args in (
        (multistream.check_superkernel_eligibility, ()),
        (multistream.effective_launch_floor_us, ("full",)),
        (aclgraph_launch_floor, ()),
        (aclgraph_superkernel, ()),
    ):
        bool_params = [
            p.name
            for p in inspect.signature(fn).parameters.values()
            if "bool" in str(p.annotation) or isinstance(p.default, bool)
        ]
        for flag in bool_params:
            options: dict[str, object] = {flag: bad}
            if fn is multistream.check_superkernel_eligibility:
                options.setdefault("static_decode", True)
            if fn.__module__.endswith("_mcp"):
                res = fn(*args, **options)
                assert res["ok"] == 0 and res["err"] == "EARGS"
            else:
                with pytest.raises(ValueError, match=flag):
                    fn(*args, **options)
