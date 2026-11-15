"""Validated stream/event DAG and critical-path accounting.

[Role]
Reconstruct stream program order, node dependencies and event record/wait
edges, then solve earliest starts and whole-graph wall time topologically.
[Invariants]
Node/event IDs are unique; every wait has exactly one producer and every
record has a consumer. Edge cost is charged only along the critical path.
Explicit start times are release lower bounds, not permission to violate edges.
[Timeouts & Locks]
At most 10000 nodes and 100000 edges; finite traversal and sorting; no locks or I/O.
[Side-Effect Policy]
Pure in-memory records; no capture, replay or filesystem operations.
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Mapping

from .aclgraph_schema import ACLGraphModelError, StreamInterval, _num
from .profiler_configs import DEFAULT_ACLGRAPH_LAUNCH_CONFIG

EVENT_US = DEFAULT_ACLGRAPH_LAUNCH_CONFIG.event_sync_us


def _mapping(value, allowed, required=()):
    if not isinstance(value, Mapping):
        raise ACLGraphModelError("graph record must be a mapping")
    if set(value) - set(allowed) or set(required) - set(value):
        raise ACLGraphModelError("unknown or missing graph record fields")
    return dict(value)


def _ident(value):
    if not isinstance(value, str) or not value:
        raise ACLGraphModelError("node/event ID must be a nonempty string")
    return value


def _sequence(value):
    if not isinstance(value, (list, tuple)):
        raise ACLGraphModelError("graph records must be a list or tuple")
    return value


def _ids(value):
    return (_ident(value),) if isinstance(value, str) else tuple(map(_ident, _sequence(value)))


@dataclass(frozen=True)
class DAGNode:
    id: str
    interval: StreamInterval
    dependencies: tuple = ()
    records: tuple = ()
    waits: tuple = ()

    @classmethod
    def from_mapping(cls, payload):
        keys = set(StreamInterval.__dataclass_fields__) | {"id", "duration_us", "dependencies", "records", "waits"}
        data = _mapping(payload, keys, ("id", "stream_id"))
        ident = _ident(data.pop("id"))
        deps, records, waits = (_ids(data.pop(key, ())) for key in ("dependencies", "records", "waits"))
        duration = data.pop("duration_us", None)
        if duration is None and not {"start_us", "end_us"} <= data.keys():
            raise ACLGraphModelError("node requires duration_us or start_us/end_us")
        data.setdefault("start_us", 0)
        if duration is not None:
            duration = _num("duration_us", duration)
            end = data["start_us"] + duration
            if "end_us" in data and data["end_us"] != end:
                raise ACLGraphModelError("node duration conflicts with interval")
            data["end_us"] = end
        data.setdefault("op", ident)
        # Explicit graphs prove fork/join by edges unless a caller declares flags.
        data.setdefault("waits_on_capture_root", False)
        data.setdefault("joined_at_exit", False)
        return cls(ident, StreamInterval.from_mapping(data), deps, records, waits)


@dataclass(frozen=True)
class DAGResult:
    nodes: tuple
    order: tuple
    edges: tuple
    starts: Mapping
    finishes: Mapping
    critical_path_us: float
    event_wall_us: float
    serial_us: float
    overlap_us: float
    overlap_pct: float
    event_cost_us: float
    event_count: int
    capture_hazards: tuple
    explicit: bool
    event_delays_us: Mapping

    def __post_init__(self) -> None:
        if not isinstance(self.explicit, bool):
            raise ACLGraphModelError("explicit must be bool")

    def details(self):
        return {"node_count": len(self.nodes), "edge_count": len(self.edges),
                "topological_order": self.order, "edges": self.edges,
                "starts_us": dict(self.starts), "finishes_us": dict(self.finishes),
                "critical_path_us": self.critical_path_us, "event_wall_us": self.event_wall_us,
                "serial_work_us": self.serial_us, "overlap_us": self.overlap_us,
                "event_us": self.event_cost_us, "event_count": self.event_count,
                "cross_stream_event_delays_us": dict(self.event_delays_us),
                "capture_hazards": self.capture_hazards, "accounting": "validated_stream_event_dag"}


def reconstruct_dag(region):
    """Accept one graph vocabulary; list order establishes per-stream order.

    nodes/intervals contain {id, stream_id, duration_us} or timestamp intervals.
    dependencies are [producer, consumer] pairs (or {source,target}). Events
    are {id,record,wait}; wait may be one ID or a list. Equivalently records and
    waits contain {id,node}, or node-local records/waits list event IDs.
    Legacy branch pairs use op as ID when unique, otherwise branch_a/branch_b.
    """
    if region.nodes and region.intervals:
        raise ACLGraphModelError("use either nodes or intervals")
    explicit_nodes = bool(region.nodes or region.intervals)
    explicit = bool(explicit_nodes or region.events or region.records or region.waits or region.dependencies)
    if explicit_nodes:
        raw = _sequence(region.nodes or region.intervals)
        if len(raw) > DEFAULT_ACLGRAPH_LAUNCH_CONFIG.max_dag_nodes:
            raise ACLGraphModelError("graph node budget exceeded")
        nodes = tuple(DAGNode.from_mapping(x) for x in raw)
    else:
        branches = (region.branch_a, region.branch_b)
        unique = branches[0].op != branches[1].op
        nodes = tuple(DAGNode(_ident(x.op if unique else f"branch_{'ab'[i]}"), x)
                      for i, x in enumerate(branches))
    by_id = {node.id: node for node in nodes}
    if len(by_id) != len(nodes) or not nodes:
        raise ACLGraphModelError("duplicate or empty node graph")
    edges, event_edges = set(), set()

    def edge(source, target, event=False):
        if source not in by_id or target not in by_id or source == target:
            raise ACLGraphModelError("dangling or self-dependent graph edge")
        edges.add((source, target))
        if len(edges) > DEFAULT_ACLGRAPH_LAUNCH_CONFIG.max_dag_edges:
            raise ACLGraphModelError("graph edge budget exceeded")
        if event:
            event_edges.add((source, target))

    last = {}
    for node in nodes:
        stream = node.interval.stream_id
        if stream in last:
            edge(last[stream], node.id)
        last[stream] = node.id
        for dep in node.dependencies:
            edge(dep, node.id)
    if region.piece_boundary_between and region.graph_mode in ("piecewise", "full_and_piecewise"):
        if explicit_nodes:
            raise ACLGraphModelError("multi-node piece boundaries require explicit dependency edges")
        edge(nodes[0].id, nodes[1].id)
    for dep in _sequence(region.dependencies):
        if isinstance(dep, Mapping):
            row = _mapping(dep, ("source", "target"), ("source", "target"))
            edge(_ident(row["source"]), _ident(row["target"]))
        else:
            if len(_sequence(dep)) != 2:
                raise ACLGraphModelError("dependency requires two node IDs")
            edge(*map(_ident, dep))
    producers, consumers = {}, defaultdict(set)

    def record(ident, node):
        ident, node = _ident(ident), _ident(node)
        if ident in producers or node not in by_id:
            raise ACLGraphModelError("duplicate or dangling event record")
        producers[ident] = node

    def wait(ident, node):
        ident, node = _ident(ident), _ident(node)
        if node not in by_id or node in consumers[ident]:
            raise ACLGraphModelError("duplicate or dangling event wait")
        consumers[ident].add(node)

    for node in nodes:
        for ident in node.records:
            record(ident, node.id)
        for ident in node.waits:
            wait(ident, node.id)
    for row in _sequence(region.events):
        row = _mapping(row, ("id", "record", "wait"), ("id", "record", "wait"))
        record(row["id"], row["record"])
        for node in _ids(row["wait"]):
            wait(row["id"], node)
    for key, fn in (("records", record), ("waits", wait)):
        for row in _sequence(getattr(region, key)):
            row = _mapping(row, ("id", "node"), ("id", "node"))
            fn(row["id"], row["node"])
    if set(producers) != set(consumers):
        raise ACLGraphModelError("event requires a recorded producer and at least one wait")
    ordinary_edges = set(edges)
    for ident, source in producers.items():
        for target in consumers[ident]:
            edge(source, target, True)
    cross_events = {(s, t) for s, t in event_edges
                    if by_id[s].interval.stream_id != by_id[t].interval.stream_id}
    preds, succs = defaultdict(set), defaultdict(set)
    for source, target in edges:
        preds[target].add(source)
        succs[source].add(target)
    degrees = {key: len(preds[key]) for key in by_id}
    ready = deque(node.id for node in nodes if not degrees[node.id])
    order = []
    while ready:
        key = ready.popleft()
        order.append(key)
        for child in sorted(succs[key]):
            degrees[child] -= 1
            if degrees[child] == 0:
                ready.append(child)
    if len(order) != len(nodes):
        raise ACLGraphModelError("dependency cycle in stream/event DAG")
    origin = min(node.interval.start_us for node in nodes)

    def solve(with_events, *, without_cross_events=False):
        starts, finishes = {}, {}
        for key in order:
            interval = by_id[key].interval
            arrivals = [interval.start_us - origin]
            for p in preds[key]:
                removed = without_cross_events and (p, key) in cross_events
                if removed and (p, key) not in ordinary_edges:
                    continue
                delay = EVENT_US if with_events and (p, key) in event_edges and not removed else 0
                arrivals.append(finishes[p] + delay)
            start = max(arrivals)
            starts[key], finishes[key] = start, start + interval.duration_us
        return starts, finishes, max(finishes.values())

    _, _, critical = solve(False)
    starts, finishes, wall = solve(True)
    # Remove cross-stream events, retaining independent dependencies and stream
    # order. Consumer delays also detect binding events off the critical path.
    event_delays = {}
    if cross_events:
        without, _, _ = solve(True, without_cross_events=True)
        event_delays = {t: starts[t] - without[t] for _, t in sorted(cross_events)
                        if starts[t] > without[t]}
    if not explicit:
        wall += region.event_pairs * EVENT_US
    busy = sum(node.interval.duration_us for node in nodes)
    stream_busy = defaultdict(float)
    for node in nodes:
        stream_busy[node.interval.stream_id] += node.interval.duration_us
    saved = max(0.0, busy - critical)
    possible = busy - max(stream_busy.values())
    pct = 100 * saved / possible if possible > 0 else 0.0
    root = region.capture_root_stream_id
    root_nodes = [node.id for node in nodes if node.interval.stream_id == root]
    if root is not None and not root_nodes:
        raise ACLGraphModelError("capture root stream is absent from graph")
    entered, joined = set(), set()
    if root_nodes:
        for key in order:
            if key == root_nodes[0] or preds[key] & entered:
                entered.add(key)
        for key in reversed(order):
            if key == root_nodes[-1] or succs[key] & joined:
                joined.add(key)
    hazards = []
    for node in nodes:
        x = node.interval
        check_root = x.stream_id != root and (root is not None or not explicit_nodes)
        # ABI: ACLGraph capture records tasks for replay; cross-stream dependencies and capture boundaries must survive partitioning or fusion.
        if check_root and (not (x.waits_on_capture_root or node.id in entered)
                           or not (x.joined_at_exit or node.id in joined)):
            hazards.append(node.id)
        elif x.aliases_buffer and not x.events_ordered:
            hazards.append(node.id)
    return DAGResult(nodes, tuple(order), tuple(sorted(edges)), starts, finishes,
                     critical, wall, busy, saved, pct, wall-critical,
                     len(producers) if explicit else region.event_pairs, tuple(hazards), explicit,
                     event_delays)


def peak_resources(dag):
    """Concurrent resource demand on the solved timeline, not sum of all nodes."""
    changes = defaultdict(lambda: [0, 0])
    for node in dag.nodes:
        start, end = dag.starts[node.id], dag.finishes[node.id]
        if start == end:
            continue
        for j, count in enumerate((node.interval.aic_blocks, node.interval.aiv_blocks)):
            changes[start][j] += count
            changes[end][j] -= count
    peak, current = [0, 0], [0, 0]
    for time in sorted(changes):
        for j in range(2):
            current[j] += changes[time][j]
            peak[j] = max(peak[j], current[j])
    return tuple(peak)
