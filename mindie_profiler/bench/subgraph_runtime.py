"""HCCL joint-subgraph runtime, dataflow execution and observation emission.

[Role]
  Own ``TorchJointRuntime`` (HCCL axis/subgroup construction and ``NPUGraph``
  capture/replay), the ``OperatorExecutor`` dataflow scope, the S0/S1
  topological cut helpers, and ``_emit_case_observations`` for
  ``bench subgraph``, keeping ``bench_archetype_subgraphs`` under 800 lines.

[Invariants]
  * Axis and declared subgroup sets are created in deterministic sorted order
    with contiguous rank chunks; every rank calls ``new_group`` for every chunk
    and a failure destroys the process group before re-raising.
  * Excluded S1 nodes that depend on a timed node follow it into ``post``;
    excluded nodes with no timed dependency stay in ``pre``.
  * Boundary nodes pass upstream tensors through verbatim and never enter the
    cold-ring path; a builder is rebuilt when its upstream tensor changes.
  * Observations preserve frozen ``train``/``heldout`` splits, plan identities,
    per-mode qualification and graph arm/execution separation.

[Timeouts & Locks]
  Process-group initialization uses ``timeout_s``; no host locks.

[Side-Effect Policy]
  Creates/destroys one HCCL process group when ``world_size > 1`` and appends
  JSONL rows to the caller-supplied ``ObservationJournal``.
"""

from __future__ import annotations

import importlib
from typing import Any, Callable, Iterable, Mapping, Sequence

from ..events import ProfilerUsageError
from .observations import case_complete_row, observation_row, timing_rows
from .operators import (
    COLLECTIVE_OPS, ELEMENT_BYTES, build_operator_enqueue, device_of,
    supports_cold_ring, torch_dtype,
)
from .profiles import profile_section

_CFG = profile_section("subgraph")
DEFAULT_OBSERVATION_BOUNDARY = "device_kernel"
EXECUTION_MODES = ("eager", "aclgraph")
DEFAULT_EXECUTION_MODES = tuple(str(m) for m in (_CFG.get("default_execution_modes") or EXECUTION_MODES))
DECODE_GRAPH_POLICY = str(_CFG.get("decode_graph_policy") or "FULL_DECODE_ONLY")
BOUNDARY_BYTES = int(_CFG["boundary_bytes"])
_PG_TIMEOUT_S = float(_CFG["process_group_timeout_s"])
_ALLCLOSE_TOL = float(_CFG["allclose_tol"])
_REASON_LIMIT = int(_CFG["max_reason_chars"])
FLOAT32_NAME = "float32"
INTRA_NODE_HCCS_ROUTE = "intra_node_hccs"
INTRA_NODE_HCCS_GROUP_SIZE = 2 * 2
CANONICAL_ROUTE_GROUP_SIZES = {"intra_package_die": 2, "intra_package_sio": 2}
_GRAPH_BOUNDARY_BUILDER = "graph_boundary"

def _rank_count(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not value.is_integer():
        return None
    return int(value) if int(value) > 1 else None

def _rank_sequence(value: Any) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        return ()
    ranks = {int(item) for item in value if isinstance(item, int) and not isinstance(item, bool)}
    return tuple(sorted(ranks))

def _axis_group_sizes(parallel: Mapping[str, Any] | None) -> dict[str, int]:
    declared_all = dict(parallel or {})
    sizes: dict[str, int] = {}
    for axis in sorted(("tp", "ep", "sp", "mc2")):
        declared = declared_all.get(axis)
        if isinstance(declared, bool):
            if not declared:
                continue
            size = max(int(declared_all.get("tp") or 1), int(declared_all.get("ep") or 1))
        else:
            size = int(declared or 1)
        if size > 1:
            sizes[axis] = size
    return sizes

def _route_group_size(route: str, world_size: int) -> int | None:
    if route == INTRA_NODE_HCCS_ROUTE:
        return min(int(world_size), INTRA_NODE_HCCS_GROUP_SIZE)
    return CANONICAL_ROUTE_GROUP_SIZES.get(route)

def _case_group_sizes(cases: Sequence[Mapping[str, Any]], world_size: int) -> set[tuple[str, int]]:
    sizes: set[tuple[str, int]] = set()
    for case in cases:
        if not isinstance(case, Mapping):
            continue
        if isinstance(case.get("parallel"), Mapping):
            sizes.update(_axis_group_sizes(case["parallel"]).items())
        for node in case.get("nodes") or ():
            if not isinstance(node, Mapping):
                continue
            name = node.get("group") or node.get("route")
            if not name or _rank_sequence(node.get("group_ranks")) or _rank_sequence(node.get("participants")):
                continue
            participants = node.get("participants")
            size = (_rank_count(node.get("group_size"))
                    or (_rank_count(len(participants)) if isinstance(participants, (list, tuple, set, frozenset)) else _rank_count(participants))
                    or _route_group_size(str(node.get("route") or ""), world_size))
            if size is not None and 1 < size <= world_size:
                sizes.add((str(name), int(size)))
    return sizes

def _explicit_group_specs(cases: Sequence[Mapping[str, Any]]) -> list[tuple[str, tuple[int, ...], bool]]:
    specs: set[tuple[str, tuple[int, ...], bool]] = set()
    for case in cases:
        if not isinstance(case, Mapping):
            continue
        case_ranks = _rank_sequence(case.get("group_ranks")) or _rank_sequence(case.get("participants"))
        if case_ranks:
            specs.add((str(case.get("group") or case.get("case_id") or "group"), case_ranks, False))
        for node in case.get("nodes") or ():
            if not isinstance(node, Mapping):
                continue
            ranks = _rank_sequence(node.get("group_ranks")) or _rank_sequence(node.get("participants"))
            if ranks:
                name = str(node.get("group") or node.get("route") or node.get("node_id") or "group")
                specs.add((name, ranks, not bool(case_ranks)))
    return sorted(specs)

def _cosets_for_ranks(ranks: tuple[int, ...], world_size: int, *, spmd: bool) -> list[list[int]]:
    count = len(ranks)
    if count < 2 or any(rank < 0 or rank >= world_size for rank in ranks):
        return []
    stride = ranks[1] - ranks[0]
    span = count * stride
    if (spmd and ranks[0] == 0 and stride > 0 and span <= world_size and world_size % span == 0
            and all(ranks[idx] == idx * stride for idx in range(count))):
        return [[base + lane + idx * stride for idx in range(count)]
                for base in range(0, world_size, span) for lane in range(stride)]
    return [list(ranks)]

def _partition_chunks(world_size: int, group_size: int) -> list[list[int]]:
    return [list(range(start, min(start + group_size, world_size))) for start in range(0, world_size, group_size)]

class TorchJointRuntime:
    """HCCL group construction plus ACLGraph capture/replay adapter."""

    def __init__(self, torch: Any, *, rank: int = 0, world_size: int = 1,
                 parallel: Mapping[str, Any] | None = None, cases: Sequence[Mapping[str, Any]] = (),
                 timeout_s: float = _PG_TIMEOUT_S) -> None:
        self.torch, self.rank, self.world_size = torch, int(rank), int(world_size)
        self.parallel, self.cases, self.timeout_s = dict(parallel or {}), tuple(cases), float(timeout_s)
        self.groups: dict[str, Any] = {}
        self.initialized, self.dist = False, None

    def _create_groups(self) -> None:
        pairs = set(_axis_group_sizes(self.parallel).items()) | _case_group_sizes(self.cases, self.world_size)
        for name, size in sorted(pairs):
            if not 1 < size <= self.world_size:
                continue
            for chunk in _partition_chunks(self.world_size, size):
                if len(chunk) < 2:
                    continue
                group = self.dist.new_group(chunk)
                if self.rank in chunk:
                    self.groups[f"{name}:{size}"] = group
                    self.groups.setdefault(name, group)
        explicit_cache: dict[tuple[int, ...], Any] = {}
        for name, ranks, spmd in _explicit_group_specs(self.cases):
            template_sig = ",".join(str(r) for r in ranks)
            for coset in _cosets_for_ranks(ranks, self.world_size, spmd=spmd):
                key = tuple(coset)
                if key not in explicit_cache:
                    explicit_cache[key] = self.dist.new_group(coset)
                group = explicit_cache[key]
                if self.rank in coset:
                    coset_sig = ",".join(str(r) for r in coset)
                    self.groups[f"{name}@{template_sig}"] = group
                    self.groups[f"{name}@{coset_sig}"] = group
                    self.groups.setdefault(f"{name}:{len(coset)}", group)
                    self.groups.setdefault(name, group)

    def init_process_group(self) -> dict[str, Any]:
        """Initialize HCCL once and create every declared subgroup in order."""
        self.dist = importlib.import_module("torch.distributed")
        if self.world_size > 1:
            from datetime import timedelta

            self.dist.init_process_group(
                "hccl", rank=self.rank, world_size=self.world_size,
                timeout=timedelta(seconds=self.timeout_s),
            )
            self.initialized = True
        try:
            if self.world_size > 1:
                self._create_groups()
        except BaseException:
            self.close()
            raise
        return {
            "world_size": self.world_size, "rank": self.rank,
            "groups": sorted(self.groups), "initialized": self.initialized,
        }

    def close(self) -> None:
        if self.initialized and self.dist is not None:
            self.dist.destroy_process_group()
            self.initialized = False
        self.groups.clear()

    def synchronize(self) -> None:
        sync = getattr(self.torch.npu, "synchronize", None)
        if callable(sync):
            sync()

    @property
    def graph_available(self) -> bool:
        npu = getattr(self.torch, "npu", None)
        return callable(getattr(npu, "NPUGraph", None)) and callable(getattr(npu, "graph", None))

    def capture(self, call: Callable[[], Any], case_id: str) -> tuple[Any, dict[str, Any]]:
        factory = getattr(self.torch.npu, "NPUGraph", None)
        if not callable(factory):
            return None, {"status": "unsupported_binding", "reason": "torch.npu.NPUGraph unavailable"}
        graph = factory()
        graph_ctx = getattr(self.torch.npu, "graph", None)
        if not callable(graph_ctx):
            return None, {"status": "unsupported_binding", "reason": "torch.npu.graph unavailable"}
        try:
            with graph_ctx(graph):
                outputs = call()
        except TimeoutError:
            raise
        except Exception as exc:
            return None, {"status": "capture_failed", "case_id": case_id,
                          "mode": "aclgraph", "reason": str(exc)[:_REASON_LIMIT]}
        return (graph, outputs), {"status": "captured", "case_id": case_id, "mode": "aclgraph"}

    def replay(self, captured: Any) -> Any:
        if not isinstance(captured, tuple) or len(captured) != 2:
            return None
        graph, outputs = captured
        replay = getattr(graph, "replay", None)
        if callable(replay):
            replay()
        return outputs

def topological_order(case: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Kahn order over stream/wait/data edges; cycles are a hard error."""
    nodes = list(case.get("nodes") or ())
    by_id = {str(node.get("node_id")): node for node in nodes}
    indegree = {node_id: 0 for node_id in by_id}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in by_id}
    for edge in case.get("edges") or ():
        source, target = str(edge["from"]), str(edge["to"])
        if source not in by_id or target not in by_id:
            raise ProfilerUsageError("bench_subgraph_edge_unknown_node")
        outgoing[source].append(target)
        indegree[target] += 1
    ready = [node_id for node_id in by_id if indegree[node_id] == 0]
    ordered: list[dict[str, Any]] = []
    while ready:
        node_id = ready.pop(0)
        ordered.append(by_id[node_id])
        for target in outgoing[node_id]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    if len(ordered) != len(by_id):
        raise ProfilerUsageError("bench_subgraph_cycle_detected")
    return ordered

def is_collective(node: Mapping[str, Any]) -> bool:
    return str(node.get("kind")) == "collective" or str(node.get("op")) in COLLECTIVE_OPS

def _adjacency(case: Mapping[str, Any]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    descendants: dict[str, set[str]] = {
        str(node.get("node_id")): set() for node in case.get("nodes") or ()
    }
    ancestors: dict[str, set[str]] = {node_id: set() for node_id in descendants}
    for edge in case.get("edges") or ():
        source, target = str(edge["from"]), str(edge["to"])
        descendants[source].add(target)
        ancestors[target].add(source)
    return descendants, ancestors

def plan_timed_cut(
    case: Mapping[str, Any], ordered: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Cut S0 collectives without hoisting any of them ahead of a producer."""
    boundary = case.get("timed_boundary") or {}
    included = {str(item) for item in boundary.get("include") or ()}
    descendants, ancestors = _adjacency(case)
    for node in ordered:
        if is_collective(node) and str(node.get("node_id")) in included:
            raise ProfilerUsageError(f"bench_collective_inside_timed_window: {node.get('node_id')}")
    timed_nodes = [dict(node) for node in ordered if not is_collective(node)]
    if included:
        timed_nodes = [dict(node) for node in ordered
                       if str(node.get("node_id")) in included and not is_collective(node)]
    timed_ids = {str(node.get("node_id")) for node in timed_nodes}
    if not timed_nodes:
        raise ProfilerUsageError("bench_subgraph_timed_window_empty")
    pre: list[dict[str, Any]] = []
    post: list[dict[str, Any]] = []
    for node in ordered:
        node_id = str(node.get("node_id"))
        if node_id in timed_ids or not is_collective(node):
            continue
        has_ancestor = bool(ancestors[node_id] & timed_ids)
        has_descendant = bool(descendants[node_id] & timed_ids)
        if has_ancestor and has_descendant:
            raise ProfilerUsageError(
                f"bench_collective_splits_local_chain: {node_id} has both a "
                "timed ancestor and a timed descendant"
            )
        (post if has_ancestor else pre).append(dict(node))
    return {"pre": pre, "timed": timed_nodes, "post": post, "include": sorted(included)}

def split_timed(
    case: Mapping[str, Any], ordered: Sequence[Mapping[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cut = plan_timed_cut(case, ordered)
    return cut["pre"], cut["timed"]

def _reachable(edges: Mapping[str, set[str]], roots: Iterable[str]) -> set[str]:
    seen, pending = set(), list(roots)
    while pending:
        for nxt in edges.get(pending.pop(), ()):
            if nxt not in seen:
                seen.add(nxt)
                pending.append(nxt)
    return seen

def _joint_split(
    case: Mapping[str, Any], ordered: Sequence[Mapping[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Split S1 nodes into ``pre`` / ``timed`` / ``post`` around the timed set."""
    include = {str(item) for item in ((case.get("timed_boundary") or {}).get("include") or ())}
    if not include:
        return [], [dict(node) for node in ordered], []
    timed = [dict(node) for node in ordered if str(node.get("node_id")) in include]
    timed_ids = {str(node.get("node_id")) for node in timed}
    adj_down, adj_up = _adjacency(case)
    descendants, ancestors = _reachable(adj_down, timed_ids), _reachable(adj_up, timed_ids)
    pre: list[dict[str, Any]] = []
    post: list[dict[str, Any]] = []
    for node in ordered:
        node_id = str(node.get("node_id"))
        if node_id in timed_ids:
            continue
        if node_id in descendants and node_id in ancestors:
            raise ProfilerUsageError(f"bench_subgraph_non_convex_cut:{node_id}")
        (post if node_id in descendants else pre).append(dict(node))
    return pre, timed, post

def _data_upstream(case: Mapping[str, Any]) -> dict[str, list[str]]:
    upstream: dict[str, list[str]] = {}
    for edge in case.get("edges") or ():
        if str(edge.get("kind") or "data") == "data":
            upstream.setdefault(str(edge["to"]), []).append(str(edge["from"]))
    return upstream

def _detach(value: Any) -> Any:
    if isinstance(value, tuple):
        return tuple(_detach(item) for item in value)
    if isinstance(value, list):
        return [_detach(item) for item in value]
    detach = getattr(value, "detach", None)
    if not callable(detach):
        return value
    try:
        detached = detach()
    except TimeoutError:
        raise
    except Exception:
        return value
    clone = getattr(detached, "clone", None)
    if callable(clone):
        try:
            return clone()
        except TimeoutError:
            raise
        except Exception:
            return detached
    return detached

def _output_snapshot(executor: Any, nodes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    outputs = getattr(executor, "outputs", None)
    if not isinstance(outputs, Mapping):
        return {}
    return {str(node.get("node_id")): _detach(outputs.get(str(node.get("node_id"))))
            for node in nodes}

def _same_shape_dtype(left: Any, right: Any) -> bool:
    for attr in ("shape", "dtype"):
        left_value, right_value = getattr(left, attr, None), getattr(right, attr, None)
        if left_value is None or right_value is None:
            continue
        try:
            if tuple(left_value) != tuple(right_value):
                return False
        except TypeError:
            if left_value != right_value:
                return False
    return True

def _same_outputs(left: Any, right: Any, torch: Any) -> bool | None:
    if left is None and right is None:
        return None
    if (left is None) != (right is None):
        return False
    if isinstance(left, (tuple, list)) or isinstance(right, (tuple, list)):
        if not (isinstance(left, (tuple, list)) and isinstance(right, (tuple, list))):
            return False
        if len(left) != len(right):
            return False
        results = [_same_outputs(a, b, torch) for a, b in zip(left, right)]
        if any(result is False for result in results):
            return False
        return True if any(result is True for result in results) else None
    if not _same_shape_dtype(left, right):
        return False
    allclose = getattr(torch, "allclose", None)
    try:
        if callable(allclose):
            return bool(allclose(left, right, rtol=_ALLCLOSE_TOL, atol=_ALLCLOSE_TOL))
        return bool(left == right)
    except TimeoutError:
        raise
    except Exception:
        return False

def _cold_ring_capable(node: Mapping[str, Any]) -> bool:
    if str(node.get("kind")) == "boundary" or str(node.get("builder")) == _GRAPH_BOUNDARY_BUILDER:
        return False
    return supports_cold_ring(node)

class OperatorExecutor:
    """Per-case operator closure scope with data-edge output passing."""

    def __init__(self, torch: Any, context: Mapping[str, Any]) -> None:
        self.torch = torch
        self.context = context
        self.built: dict[tuple[str, bool], Callable[[], Any]] = {}
        self.outputs: dict[str, Any] = {}
        self._live_inputs: dict[str, Any] = {"tensors": ()}
        if isinstance(self.context, dict):
            self.context["_live_inputs"] = self._live_inputs
            self.context["_hot_arena"] = {"sub_offset": 0}

    def begin_case(self, case: Mapping[str, Any]) -> None:
        self.context["_case_meta"] = {
            "model_id": case.get("model_id"), "layer_idx": case.get("layer_idx", -1),
            "phase": case.get("phase"), "batch": case.get("batch"),
        }

    def build(self, node: Mapping[str, Any], *, hot: bool = False) -> Callable[[], Any]:
        node_id = str(node.get("node_id") or "")
        key = (node_id, bool(hot))
        if key not in self.built:
            prev = self.context.get("_active_node_id")
            self.context["_active_node_id"] = node_id
            try:
                self.built[key] = build_operator_enqueue(self.torch, node, self.context, hot=hot)
            finally:
                self.context.pop("_active_node_id", None) if prev is None else self.context.__setitem__("_active_node_id", prev)
        return self.built[key]

    def launch(self, node: Mapping[str, Any], upstream: Sequence[Any] = (), *, hot: bool = False) -> Any:
        node_id = str(node.get("node_id"))
        inputs = list(upstream)
        if str(node.get("kind")) == "boundary" or str(node.get("builder")) == _GRAPH_BOUNDARY_BUILDER:
            self.outputs[node_id] = inputs[0] if inputs else None
            return self.outputs[node_id]
        self._live_inputs["tensors"] = tuple(inputs)
        try:
            output = self.build(node, hot=hot)()
        finally:
            self._live_inputs["tensors"] = ()
        self.outputs[node_id] = output
        return output

    def upstream(self, node_ids: Iterable[str]) -> list[Any]:
        return [self.outputs[node_id] for node_id in node_ids if node_id in self.outputs]

    def supply_boundary(self, node: Mapping[str, Any]) -> Any:
        name = str(node.get("dtype") or "bf16")
        dtype = (torch_dtype(self.torch, name)
                 or getattr(self.torch, "bfloat16", None)
                 or getattr(self.torch, FLOAT32_NAME, None))
        shape = node.get("shape") if isinstance(node.get("shape"), Mapping) else {}
        tokens, width = shape.get("tokens"), shape.get("width")
        m, n, k = shape.get("m"), shape.get("n"), shape.get("k")
        dims: tuple[int, ...] | None = None
        if _positive_dim(tokens) and _positive_dim(width):
            dims = (int(tokens), int(width))
        elif _positive_dim(m) and _positive_dim(k):
            dims = (int(m), int(k))
        elif _positive_dim(m) and _positive_dim(n):
            dims = (int(m), int(n))
        element = int(ELEMENT_BYTES.get(name, 2))
        if dims is None:
            nbytes = next((value for value in (
                node.get("nbytes"), node.get("bytes"), shape.get("bytes"), shape.get("nbytes"),
            ) if _positive_dim(value)), None)
            dims = (max(1, int(nbytes) // element) if nbytes else max(1, BOUNDARY_BYTES // element),)
        tensor = self.torch.zeros(*dims, dtype=dtype, device=device_of(self.context))
        self.outputs[str(node.get("node_id"))] = tensor
        return tensor

    def reset(self) -> None:
        self.built.clear()
        self.outputs.clear()
        ring = self.context.get("ring") if isinstance(self.context, dict) else None
        allocated = getattr(ring, "allocated_bytes", 0) if getattr(ring, "allocated", False) else 0
        if isinstance(self.context, dict):
            self.context["_byte_ledger"] = {"peak_bytes": int(allocated or 0)}
            self.context["_hot_arena"] = {"sub_offset": 0}
        self.context.pop("_case_meta", None)

def _positive_dim(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0

def _dist_ready(context: Mapping[str, Any] | None) -> bool:
    return bool(isinstance(context, Mapping) and context.get("dist") is not None
                and context.get("dist_initialized"))

def _upstream(executor: Any, node_id: str, upstream: Mapping[str, list[str]]) -> list[Any]:
    producers = upstream.get(node_id, ())
    outputs = getattr(executor, "outputs", None)
    if producers and isinstance(outputs, Mapping):
        if any(producer not in outputs for producer in producers):
            raise ProfilerUsageError(f"bench_subgraph_missing_upstream:{node_id}")
    getter = getattr(executor, "upstream", None)
    return getter(producers) if callable(getter) else []

def _launch(executor: Any, node: Mapping[str, Any], upstream: Sequence[Any], *, hot: bool = False) -> Any:
    if hot:
        return executor.launch(node, upstream, hot=True)
    return executor.launch(node, upstream) if upstream else executor.launch(node)

def _run_pre(executor: Any, pre: Sequence[Mapping[str, Any]], upstream: Mapping[str, list[str]]) -> list[str]:
    executed: list[str] = []
    for node in pre:
        node_id = str(node.get("node_id"))
        supply = getattr(executor, "supply_boundary", None)
        if _dist_ready(getattr(executor, "context", None)) or not callable(supply):
            _launch(executor, node, _upstream(executor, node_id, upstream))
        else:
            supply(node)
        executed.append(node_id)
    return executed

def _begin_case(executor: Any, case: Mapping[str, Any]) -> None:
    begin = getattr(executor, "begin_case", None)
    if callable(begin):
        begin(case)

def _normalized_modes(modes: Any) -> list[str]:
    if not modes:
        return list(DEFAULT_EXECUTION_MODES)
    values = [str(mode) for mode in modes]
    if any(mode not in EXECUTION_MODES for mode in values):
        raise ProfilerUsageError("bench_subgraph_execution_mode_invalid")
    return values

def resolve_case_execution_modes(case: Mapping[str, Any], plan_modes: Any = None) -> list[str]:
    """Enforce ``FULL_DECODE_ONLY``: prefill and fabric run eager; decode includes aclgraph."""
    if case.get("execution_modes"):
        return _normalized_modes(case["execution_modes"])
    modes = _normalized_modes(plan_modes)
    eager_only = str(case.get("phase") or "").strip().lower() == "prefill" or str(case.get("kind") or "") == "fabric"
    return ["eager"] if eager_only and "eager" in modes else modes

def _check_host_fallback(timing: Mapping[str, Any] | None, ctx: Mapping[str, Any]) -> None:
    if timing and not ctx.get("allow_cpu_smoke") and (
        timing.get("timer_source") == "perf_counter_host_fallback" or "host_fallback" in (timing.get("modes") or {})
    ):
        raise ProfilerUsageError("bench_host_fallback_forbidden")

def _make_probe_reducer(runtime: Any, executor: Any) -> Callable[[float], float] | None:
    dist = getattr(runtime, "dist", None)
    red = getattr(getattr(dist, "ReduceOp", None), "MAX", None)
    if not (getattr(runtime, "initialized", False) and dist is not None and red is not None and callable(getattr(executor.torch, "tensor", None))):
        return None
    def _reduce(val: float) -> float:
        buf = executor.torch.tensor([float(val)], dtype=getattr(executor.torch, FLOAT32_NAME, None), device=device_of(getattr(executor, "context", {})))
        dist.all_reduce(buf, op=red)
        item = getattr(buf, "item", None)
        return float(item()) if callable(item) else float(val)
    return _reduce

def _capture_and_time_graph(
    executor: Any, runtime: Any, protocol: Any, case: Mapping[str, Any],
    timed: Sequence[Mapping[str, Any]], launch_fn: Callable[[], list[Any]],
    ref_outputs: list[Any], ref_snapshot: dict[str, Any], run_kwargs: Mapping[str, Any],
) -> tuple[Any, dict[str, Any], bool, bool]:
    node_ids = [str(node.get("node_id")) for node in timed]
    captured, receipt = runtime.capture(launch_fn, f"{case.get('case_id')}.aclgraph")
    replay_outputs = runtime.replay(captured) if captured is not None else None
    capture_snapshot = _output_snapshot(executor, timed)
    comparisons: list[bool | None] = []
    if isinstance(replay_outputs, (list, tuple)) and len(ref_outputs) == len(replay_outputs):
        comparisons = [_same_outputs(a, b, executor.torch) for a, b in zip(ref_outputs, replay_outputs)]
        if comparisons and all(item is None for item in comparisons):
            comparisons = [_same_outputs(ref_snapshot.get(nid), capture_snapshot.get(nid), executor.torch) for nid in node_ids]
    agree = bool(any(item is True for item in comparisons) and not any(item is False for item in comparisons))
    ref_outputs.clear()
    ref_snapshot.clear()
    del replay_outputs, capture_snapshot
    graph = protocol.run(lambda: runtime.replay(captured), case_id=f"{case.get('case_id')}.aclgraph", **run_kwargs) if captured is not None else None
    ok = bool(captured is not None and agree and (not isinstance(graph, Mapping) or graph.get("qualified", True)))
    return graph, {**dict(receipt), "policy": DECODE_GRAPH_POLICY}, agree, ok

def execute_local_case(
    executor: OperatorExecutor, case: Mapping[str, Any], protocol: Any,
    *, runtime: Any = None, execution_modes: Any = None,
) -> dict[str, Any]:
    """Run one S0 case: prefill in eager, decode with optional FULL_DECODE_ONLY aclgraph."""
    _begin_case(executor, case)
    modes = resolve_case_execution_modes(case, execution_modes)
    ordered = topological_order(case)
    cut, upstream = plan_timed_cut(case, ordered), _data_upstream(case)
    executed_pre = _run_pre(executor, cut["pre"], upstream)
    synchronize = getattr(getattr(executor.torch, "npu", None), "synchronize", None)
    if callable(synchronize):
        synchronize()
    ctx = getattr(executor, "context", None) or {}
    ring = ctx.get("ring")
    ring_ready = bool(ring is not None and getattr(ring, "allocated", False) and any(_cold_ring_capable(n) for n in cut["timed"]))
    timed_nodes = [dict(n, cold_ring=True) if ring_ready and _cold_ring_capable(n) else n for n in cut["timed"]]
    base_kwargs: dict[str, Any] = {"kind": "operator", "nbytes": int(case.get("work_bytes") or 0)}
    if ctx.get("blocker") is not None:
        base_kwargs.update({"blocker": ctx["blocker"], "blocker_receipt": ctx.get("blocker_receipt")})
    timing = None
    if "eager" in modes:
        eager_kw: dict[str, Any] = {"case_id": str(case.get("case_id")), **base_kwargs}
        if ring_ready:
            eager_kw["cold_ring"] = ring
            eager_kw["hot_enqueue"] = lambda: [_launch(executor, n, _upstream(executor, str(n.get("node_id")), upstream), hot=True) for n in timed_nodes]
        timing = protocol.run(lambda: [_launch(executor, n, _upstream(executor, str(n.get("node_id")), upstream)) for n in timed_nodes][-1], **eager_kw)
        _check_host_fallback(timing, ctx)
    npu = getattr(executor.torch, "npu", None)
    graph_rt = (runtime if (runtime is not None and (not isinstance(runtime, TorchJointRuntime) or runtime.graph_available))
                else (TorchJointRuntime(executor.torch) if callable(getattr(npu, "NPUGraph", None)) and callable(getattr(npu, "graph", None)) else None))
    aclgraph, capture_receipt, agree, graph_ran, graph_ok = None, {"status": "skipped", "mode": "eager", "policy": DECODE_GRAPH_POLICY}, None, False, True
    if "aclgraph" in modes and graph_rt is not None:
        graph_ran, use_hot = True, isinstance(executor, OperatorExecutor)
        launch_static = lambda: [_launch(executor, n, _upstream(executor, str(n.get("node_id")), upstream), hot=use_hot) for n in cut["timed"]]
        ref_out, ref_snap = [_detach(v) for v in launch_static()], _output_snapshot(executor, cut["timed"])
        graph_rt.synchronize()
        aclgraph, capture_receipt, agree, graph_ok = _capture_and_time_graph(executor, graph_rt, protocol, case, cut["timed"], launch_static, ref_out, ref_snap, base_kwargs)
        _check_host_fallback(aclgraph, ctx)
    elif "aclgraph" in modes and timing is None:
        graph_ran, graph_ok, capture_receipt = True, False, {"status": "unsupported_binding", "mode": "aclgraph", "policy": DECODE_GRAPH_POLICY}
    executed_post = _run_pre(executor, cut["post"], upstream)
    primary = timing if timing is not None else (aclgraph or {"minimum_ms": 0.0, "qualified": False})
    eager_q = bool(timing.get("qualified", False) and timing.get("timer_source") != "perf_counter_host_fallback") if timing is not None else True
    eager_status_ok = bool(timing.get("qualified", True)) if isinstance(timing, Mapping) else True
    status_ok = eager_status_ok and (not graph_ran or graph_ok)
    out: dict[str, Any] = {
        "case_id": str(case.get("case_id")), "status": "ok" if status_ok else "unqualified",
        "split": str(case.get("split") or "train"), "archetype": case.get("archetype"),
        "execution_modes": modes, "graph_policy": DECODE_GRAPH_POLICY, "eager_ran": timing is not None,
        "timed_nodes": [str(node.get("node_id")) for node in cut["timed"]],
        "cut_nodes": executed_pre + executed_post, "pre_nodes": executed_pre, "post_nodes": executed_post,
        "single_rank_boundary_tensors": bool(cut["pre"] and not _dist_ready(getattr(executor, "context", None))),
        "timing": primary, "capture": capture_receipt, "minimum_ms": primary["minimum_ms"], "startup_ms": 0.0,
        "validated": True, "qualified": bool((eager_q if timing is not None else bool((aclgraph or {}).get("qualified", False))) and graph_ok) if graph_ran else eager_q,
    }
    if graph_ran:
        out.update({"aclgraph": aclgraph, "outputs_agree": agree})
    return out

def execute_joint_case(
    executor: OperatorExecutor, case: Mapping[str, Any], protocol: Any, runtime: Any,
    *, execution_modes: Any = None, blocker: Any = None,
    blocker_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one S1 case: prefill in eager, decode in eager + FULL_DECODE_ONLY aclgraph."""
    _begin_case(executor, case)
    modes = resolve_case_execution_modes(case, execution_modes)
    ordered = topological_order(case)
    pre, timed, post = _joint_split(case, ordered)
    upstream = _data_upstream(case)
    has_collective = any(is_collective(node) for node in timed)
    run_kwargs: dict[str, Any] = {
        "kind": "collective" if has_collective else "operator",
        "nbytes": int(case.get("work_bytes") or max((int(node.get("nbytes") or 0) for node in timed), default=0)),
    }
    if blocker is not None:
        run_kwargs.update({"blocker": blocker, "blocker_receipt": blocker_receipt})
    reducer = _make_probe_reducer(runtime, executor)
    if reducer is not None:
        run_kwargs["probe_reduce"] = reducer
    for node in pre:
        _launch(executor, node, _upstream(executor, str(node.get("node_id")), upstream))
    runtime.synchronize()
    node_ids, use_hot = [str(node.get("node_id")) for node in timed], isinstance(executor, OperatorExecutor)
    launch_all = lambda: [_launch(executor, node, _upstream(executor, str(node.get("node_id")), upstream)) for node in timed]
    launch_static = lambda: [_launch(executor, node, _upstream(executor, str(node.get("node_id")), upstream), hot=use_hot) for node in timed]
    eager_outputs, eager_snapshot = [_detach(value) for value in launch_static()], _output_snapshot(executor, timed)
    ctx = getattr(executor, "context", None) or {}
    eager = protocol.run(launch_all, case_id=f"{case.get('case_id')}.eager", **run_kwargs) if "eager" in modes else None
    _check_host_fallback(eager, ctx)
    eager_q = bool(eager.get("qualified", True)) if isinstance(eager, Mapping) else True
    graph, capture_receipt, agreement, graph_ok = None, {"status": "skipped", "mode": "eager", "policy": DECODE_GRAPH_POLICY}, None, True
    if "aclgraph" in modes:
        graph, capture_receipt, agreement, graph_ok = _capture_and_time_graph(
            executor, runtime, protocol, case, timed, launch_static, eager_outputs, eager_snapshot, run_kwargs
        )
        _check_host_fallback(graph, ctx)
    else:
        eager_outputs.clear()
        eager_snapshot.clear()
    qualified = bool(eager_q and graph_ok)
    executed_post = [str(node.get("node_id")) for node in post if (_launch(executor, node, _upstream(executor, str(node.get("node_id")), upstream)), True)[1]]
    primary = eager if eager is not None else (graph or {"minimum_ms": 0.0})
    return {
        "case_id": str(case.get("case_id")), "status": "ok" if qualified else "unqualified",
        "split": str(case.get("split") or "train"), "execution_modes": modes,
        "graph_policy": DECODE_GRAPH_POLICY, "timed_nodes": node_ids,
        "cut_nodes": [str(node.get("node_id")) for node in pre] + [str(node.get("node_id")) for node in post],
        "pre_nodes": [str(node.get("node_id")) for node in pre], "post_nodes": executed_post,
        "environment_mode": "separate_contexts", "eager": eager, "aclgraph": graph,
        "capture": capture_receipt, "outputs_agree": agreement, "qualified": qualified,
        "minimum_ms": primary["minimum_ms"], "startup_ms": 0.0,
    }

def _case_boundary(case: Mapping[str, Any], identities: Mapping[str, Any]) -> str:
    accuracy = identities.get("accuracy_identity")
    declared = accuracy.get("boundary") if isinstance(accuracy, Mapping) else None
    timing = case.get("timing")
    timed = timing.get("boundary") if isinstance(timing, Mapping) else None
    return str(declared or timed or case.get("boundary") or DEFAULT_OBSERVATION_BOUNDARY)

def _row_qualified(record: Mapping[str, Any], graph: str | None, mode_qualified: bool) -> bool:
    if graph == "aclgraph":
        return bool(record.get("qualified") and record.get("outputs_agree") and mode_qualified)
    if graph == "eager":
        return bool(mode_qualified)
    return bool(record.get("validated", True)) and bool(mode_qualified)

def _emit_case_observations(
    journal: Any, plan: Mapping[str, Any], case: Mapping[str, Any],
    record: Mapping[str, Any], run_id: str, stage: str, *, rank: Any = None,
) -> None:
    if journal is None or record.get("status") not in {"ok", "unqualified"}:
        return
    split = str(case.get("split") or "train")
    identities = case.get("identities") if isinstance(case.get("identities"), Mapping) else {}
    boundary = _case_boundary(case, identities)
    row_rank = case.get("rank") if case.get("rank") is not None else rank
    plan_hw = plan.get("hardware")
    hw = (case.get("hardware") or case.get("sku") or plan.get("sku")
          or (plan_hw.get("sku") if isinstance(plan_hw, Mapping) else plan_hw) or plan.get("plan_id") or "subgraph")
    nodes = [n for n in (case.get("nodes") or ()) if isinstance(n, Mapping)]
    n0 = nodes[0] if nodes else {}
    obs_case = {**case, "hardware": hw,
                "implementation": case.get("implementation") or n0.get("implementation") or n0.get("builder") or n0.get("op") or case.get("archetype") or "subgraph",
                "dtype": case.get("dtype") or n0.get("dtype") or "bf16"}
    service = identities.get("service")
    mixed = service.get("mixed_domains") if isinstance(service, Mapping) and "mixed_domains" in service else case.get("mixed_domains")
    wb = case.get("work_bytes") if case.get("work_bytes") is not None else case.get("fabric_bytes")
    facets, base_timing = ("work", "resource", "work_unit", "active_units"), (None if record.get("eager_ran") is False else record.get("timing"))
    arms = [(a, t, g) for a, t, g in (("base", base_timing, None), ("base", record.get("eager"), "eager"), ("aclgraph", record.get("aclgraph"), "aclgraph")) if isinstance(t, Mapping)]
    for arm, arm_timing, graph in arms:
        capabilities = ({key: service.get(key) for key in facets} if isinstance(service, Mapping)
                        else ({"work": arm_timing.get("minimum_ms"), "resource": case.get("resource"),
                               "work_unit": case.get("work_unit"), "active_units": case.get("active_units")}
                              if case.get("work_unit") else {}))
        for mode, mode_qualified, trial, repeat_index, repeat_us in timing_rows(arm_timing):
            execution: dict[str, Any] = {"mode": mode, "stage": stage, **({"graph": graph} if graph is not None else {})}
            journal.append(observation_row(
                plan_id=plan.get("plan_id"), case=obs_case, run_id=f"{run_id}.{arm}.{mode}.t{trial}",
                split=split, boundary=boundary, timing_mode=mode, residency=str(case.get("residency") or "device"),
                trial=trial, repeat_index=repeat_index, rank=row_rank, duration_ms=float(repeat_us) / 1000.0,
                source=f"capture://bench-subgraph/{case.get('case_id')}/{arm}.{mode}.{trial}.{repeat_index}",
                arm=arm, validated=bool(record.get("validated", True)), qualified=_row_qualified(record, graph, mode_qualified),
                level=str(case.get("level") or "subgraph"), phase=case.get("phase"), execution=execution,
                work_bytes=wb, mixed_domains=mixed, route=case.get("route"), key=identities.get("primitive_key"),
                identity_override=identities.get("accuracy_identity"),
                service_identity=(service.get("identity") if isinstance(service, Mapping) else None), **capabilities,
            ))
    summary: dict[str, Any] = {"stage": stage, "timed_nodes": record.get("timed_nodes"), "outputs_agree": record.get("outputs_agree"),
                               **({"mixed_domains": bool(mixed)} if mixed is not None else {}),
                               **({"work_bytes": int(wb)} if int(wb or 0) > 0 else {})}
    journal.append(case_complete_row(plan_id=plan.get("plan_id"), case_id=case.get("case_id"), run_id=run_id, status=str(record.get("status")), split=split, summary=summary))


__all__ = [
    "BOUNDARY_BYTES", "CANONICAL_ROUTE_GROUP_SIZES", "DECODE_GRAPH_POLICY", "DEFAULT_EXECUTION_MODES",
    "DEFAULT_OBSERVATION_BOUNDARY", "EXECUTION_MODES", "FLOAT32_NAME", "INTRA_NODE_HCCS_GROUP_SIZE",
    "INTRA_NODE_HCCS_ROUTE", "OperatorExecutor", "TorchJointRuntime", "_adjacency", "_cold_ring_capable",
    "_data_upstream", "_detach", "_dist_ready", "_emit_case_observations", "_joint_split", "_launch",
    "_normalized_modes", "_output_snapshot", "_run_pre", "_same_outputs", "_upstream", "execute_joint_case",
    "execute_local_case", "is_collective", "plan_timed_cut", "resolve_case_execution_modes",
    "split_timed", "timing_rows", "topological_order",
]
