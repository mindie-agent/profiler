"""Ten-archetype subgraph replay: S0 local chains and S1 joined collectives.

[Role]
  Load the exported ``mindie-bench-subgraph-plan/1`` plan, build every operator
  from its declared binding through ``bench.operators``, execute S0 local
  chains with collectives cut outside the timed window, and execute S1
  ``torchrun`` joined subgraphs in eager and ACLGraph replay with output
  agreement checks.

[Invariants]
  * Dispatch is by declared binding/builder, never by archetype, model id or
    case id; the ten archetype names are reporting labels only.
  * A collective inside the declared timed window is refused.  In S0 a
    collective with both a timed ancestor and a timed descendant splits the
    local chain and is refused; a leading collective is cut pre-window and a
    trailing collective post-window, never hoisted ahead of its producer.
  * A single-rank S0 cut supplies preallocated boundary tensors instead of
    calling an uninitialized ``torch.distributed``.
  * In S1 collectives stay inside the joined timed graph unless explicitly
    excluded by ``timed_boundary["include"]``.
  * Every case gets a fresh operator scope; no ``node_id`` state leaks.
  * A captured arm is compared with the eager arm before its timing is
    reported; a mismatched or uncaptured graph is ``unqualified``.
  * Every case keeps its frozen ``train``/``heldout`` split.

[Timeouts & Locks]
  No locks.  Process-group initialization uses an explicit finite timeout and
  the caller's container budget bounds the launch.

[Side-Effect Policy]
  Reads the plan and writes only the requested ``--out`` JSON/observations; the
  S1 arm owns one HCCL process group and destroys it in ``finally``.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from ..events import ProfilerUsageError
from .abi import portable_receipt, resolve_allowed_phy_ids
from .observations import (
    ObservationJournal, case_complete_row, observation_row,
)
from .operators import (
    COLLECTIVE_OPS, OPERATOR_BUILDERS, _bind_collective, build_operator_enqueue,
    device_of, resolve_op, supports_cold_ring, torch_dtype,
)
from .timing import (
    EventTimer, MeasurementProtocol, TorchTimingRuntime, case_over_budget,
)

PLAN_SCHEMA = "mindie-bench-subgraph-plan/1"
RUN_SCHEMA = "mindie-bench-subgraph-run/1"
NODE_SCHEMA = "mindie-bench-subgraph-node/1"
STAGES = ("s0_local", "s1_joint")
EXECUTION_MODES = ("eager", "aclgraph")
EDGE_KINDS = ("stream", "wait", "data")
NODE_KINDS = ("operator", "collective", "boundary")
MAX_PLAN_BYTES = 48 * 1024 * 1024
MAX_CASES = 4096
MAX_NODES = 8192
MAX_EDGES = 65536
MAX_WORLD = 4096
DEFAULT_OBSERVATION_BOUNDARY = "device_kernel"
BOUNDARY_BYTES = 4096
FLOAT32_NAME = "float32"


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProfilerUsageError(reason)


def _bounded(value: Any, reason: str, limit: int) -> None:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool)
             and 0 <= int(value) <= limit, reason)


def load_plan(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    try:
        if target.stat().st_size > MAX_PLAN_BYTES:
            raise ProfilerUsageError("bench_subgraph_plan_too_large")
        payload = json.loads(target.read_text(encoding="utf-8"))
    except TimeoutError:
        raise
    except (OSError, ValueError, UnicodeError) as exc:
        raise ProfilerUsageError(f"bench_subgraph_plan_invalid: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ProfilerUsageError("bench_subgraph_plan_invalid: expected an object")
    return validate_plan(payload)


def validate_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    plan = dict(plan)
    if plan.get("schema") != PLAN_SCHEMA:
        raise ProfilerUsageError(f"bench_subgraph_plan_schema: expected {PLAN_SCHEMA}")
    stage = str(plan.get("stage") or "")
    if stage not in STAGES:
        raise ProfilerUsageError(f"bench_subgraph_stage_invalid: {stage!r}")
    if plan.get("rank") is not None:
        _bounded(plan["rank"], "bench_subgraph_rank_invalid", MAX_WORLD - 1)
    world = plan.get("world_size", 1)
    _bounded(world, "bench_subgraph_world_invalid", MAX_WORLD)
    _require(int(world) >= 1, "bench_subgraph_world_invalid")
    modes = plan.get("execution_modes") or ["eager"]
    if any(str(mode) not in EXECUTION_MODES for mode in modes):
        raise ProfilerUsageError("bench_subgraph_execution_mode_invalid")
    cases = plan.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ProfilerUsageError("bench_subgraph_cases_missing")
    _require(len(cases) <= MAX_CASES, "bench_subgraph_cases_too_many")
    normalized = []
    for case in cases:
        if not isinstance(case, Mapping):
            raise ProfilerUsageError("bench_subgraph_case_invalid")
        nodes = case.get("nodes") or []
        if not isinstance(nodes, list) or not nodes:
            raise ProfilerUsageError("bench_subgraph_nodes_missing")
        _require(len(nodes) <= MAX_NODES, "bench_subgraph_nodes_too_many")
        edges = case.get("edges") or []
        _require(isinstance(edges, list) and len(edges) <= MAX_EDGES,
                 "bench_subgraph_edges_invalid")
        for node in nodes:
            if not isinstance(node, Mapping):
                raise ProfilerUsageError("bench_subgraph_node_invalid")
            if str(node.get("kind") or "operator") not in NODE_KINDS:
                raise ProfilerUsageError(
                    f"bench_subgraph_node_kind_invalid: {node.get('kind')!r}")
        for edge in edges:
            if not isinstance(edge, Mapping) or "from" not in edge or "to" not in edge:
                raise ProfilerUsageError("bench_subgraph_edge_invalid")
            if str(edge.get("kind") or "data") not in EDGE_KINDS:
                raise ProfilerUsageError("bench_subgraph_edge_kind_invalid")
        normalized.append(dict(case))
    plan["cases"] = normalized
    return plan


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
    return (str(node.get("kind")) == "collective"
            or str(node.get("op")) in COLLECTIVE_OPS)


def _adjacency(case: Mapping[str, Any]) -> tuple[dict[str, set[str]],
                                                dict[str, set[str]]]:
    descendants: dict[str, set[str]] = {
        str(node.get("node_id")): set() for node in case.get("nodes") or ()}
    ancestors: dict[str, set[str]] = {node_id: set() for node_id in descendants}
    for edge in case.get("edges") or ():
        source, target = str(edge["from"]), str(edge["to"])
        descendants[source].add(target)
        ancestors[target].add(source)
    return descendants, ancestors


def plan_timed_cut(case: Mapping[str, Any],
                   ordered: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Cut S0 collectives without hoisting any of them ahead of a producer."""
    boundary = case.get("timed_boundary") or {}
    included = {str(item) for item in boundary.get("include") or ()}
    descendants, ancestors = _adjacency(case)
    for node in ordered:
        if is_collective(node) and str(node.get("node_id")) in included:
            raise ProfilerUsageError(
                f"bench_collective_inside_timed_window: {node.get('node_id')}")
    timed_nodes = [dict(node) for node in ordered
                   if not is_collective(node)]
    if included:
        timed_nodes = [dict(node) for node in ordered
                       if str(node.get("node_id")) in included
                       and not is_collective(node)]
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
                "timed ancestor and a timed descendant")
        (post if has_ancestor else pre).append(dict(node))
    return {"pre": pre, "timed": timed_nodes, "post": post,
            "include": sorted(included)}


def split_timed(case: Mapping[str, Any], ordered: Sequence[Mapping[str, Any]]
                ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Compatibility view: pre-window and timed nodes (post-window omitted)."""
    cut = plan_timed_cut(case, ordered)
    return cut["pre"], cut["timed"]


def _data_upstream(case: Mapping[str, Any]) -> dict[str, list[str]]:
    upstream: dict[str, list[str]] = {}
    for edge in case.get("edges") or ():
        if str(edge.get("kind") or "data") == "data":
            upstream.setdefault(str(edge["to"]), []).append(str(edge["from"]))
    return upstream


def _detach(torch: Any, value: Any) -> Any:
    """Clone/detach eager outputs so graph capture cannot alias their storage."""
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


class OperatorExecutor:
    """Per-case operator closure scope with data-edge output passing."""

    def __init__(self, torch: Any, context: Mapping[str, Any]) -> None:
        self.torch = torch
        self.context = context
        self.built: dict[tuple[str, bool], Callable[[], Any]] = {}
        self.outputs: dict[str, Any] = {}

    def build(self, node: Mapping[str, Any], *, hot: bool = False) -> Callable[[], Any]:
        node_id = str(node.get("node_id"))
        key = (node_id, bool(hot))
        if key not in self.built:
            self.built[key] = build_operator_enqueue(
                self.torch, node, self.context, hot=hot)
        return self.built[key]

    def launch(self, node: Mapping[str, Any],
               upstream: Sequence[Any] = ()) -> Any:
        node_id = str(node.get("node_id"))
        self.context["_node_inputs"] = list(upstream)
        try:
            output = self.build(node)()
        finally:
            self.context.pop("_node_inputs", None)
        self.outputs[node_id] = output
        return output

    def upstream(self, node_ids: Iterable[str]) -> list[Any]:
        return [self.outputs[node_id] for node_id in node_ids
                if node_id in self.outputs]

    def supply_boundary(self, node: Mapping[str, Any]) -> Any:
        """Preallocated stand-in for a collective cut outside a dist context."""
        shape = node.get("shape") if isinstance(node.get("shape"), Mapping) else {}
        nbytes = int(node.get("nbytes") or shape.get("bytes") or BOUNDARY_BYTES)
        elements = max(1, nbytes // 4)
        tensor = self.torch.zeros(elements, dtype=getattr(self.torch, FLOAT32_NAME, None),
                                  device=device_of(self.context))
        self.outputs[str(node.get("node_id"))] = tensor
        return tensor

    def reset(self) -> None:
        self.built.clear()
        self.outputs.clear()
        self.context.pop("_node_inputs", None)


def _dist_ready(context: Mapping[str, Any] | None) -> bool:
    if not isinstance(context, Mapping):
        return False
    return bool(context.get("dist") is not None and context.get("dist_initialized"))


def _upstream(executor: Any, node_id: str,
              upstream: Mapping[str, list[str]]) -> list[Any]:
    getter = getattr(executor, "upstream", None)
    return getter(upstream.get(node_id, ())) if callable(getter) else []


def _launch(executor: Any, node: Mapping[str, Any],
            upstream: Sequence[Any]) -> Any:
    """Call a real two-argument executor or a minimal one-argument fake."""
    return (executor.launch(node, upstream) if upstream
            else executor.launch(node))


def _run_pre(executor: Any, pre: Sequence[Mapping[str, Any]],
             upstream: Mapping[str, list[str]]) -> list[str]:
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


def execute_local_case(executor: OperatorExecutor, case: Mapping[str, Any],
                       protocol: MeasurementProtocol) -> dict[str, Any]:
    """Run one S0 case: cut collectives pre/post, time only the local chain."""
    ordered = topological_order(case)
    cut = plan_timed_cut(case, ordered)
    upstream = _data_upstream(case)
    executed_pre = _run_pre(executor, cut["pre"], upstream)
    synchronize = getattr(getattr(executor.torch, "npu", None), "synchronize", None)
    if callable(synchronize):
        synchronize()

    def enqueue():
        result = None
        for node in cut["timed"]:
            node_id = str(node.get("node_id"))
            result = _launch(executor, node,
                             _upstream(executor, node_id, upstream))
        return result

    run_kwargs: dict[str, Any] = {
        "case_id": str(case.get("case_id")), "kind": "operator",
        "nbytes": int(case.get("work_bytes") or 0)}
    ring = (getattr(executor, "context", {}) or {}).get("ring")
    if ring is not None and supports_cold_ring(case):
        run_kwargs["cold_ring"] = ring
        run_kwargs["hot_enqueue"] = build_operator_enqueue(
            executor.torch, dict(case, cold_ring=True), executor.context, hot=True)
    timing = protocol.run(enqueue, **run_kwargs)
    executed_post = _run_pre(executor, cut["post"], upstream)
    return {"case_id": str(case.get("case_id")), "status": "ok",
            "split": str(case.get("split") or "train"),
            "archetype": case.get("archetype"),
            "timed_nodes": [str(node.get("node_id")) for node in cut["timed"]],
            "cut_nodes": executed_pre + executed_post,
            "pre_nodes": executed_pre, "post_nodes": executed_post,
            "single_rank_boundary_tensors": bool(
                cut["pre"] and not _dist_ready(getattr(executor, "context", None))),
            "timing": timing, "minimum_ms": timing["minimum_ms"],
            "startup_ms": 0.0}


def _joint_split(case: Mapping[str, Any], ordered: Sequence[Mapping[str, Any]]
                 ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    include = {str(item) for item in
               ((case.get("timed_boundary") or {}).get("include") or ())}
    if not include:
        return [], [dict(node) for node in ordered]
    return ([dict(node) for node in ordered
             if str(node.get("node_id")) not in include],
            [dict(node) for node in ordered
             if str(node.get("node_id")) in include])


def _same_outputs(left: Any, right: Any, torch: Any) -> bool | None:
    if left is None and right is None:
        return True
    allclose = getattr(torch, "allclose", None)
    try:
        return (bool(allclose(left, right, rtol=1e-2, atol=1e-2))
                if callable(allclose) else bool(left == right))
    except TimeoutError:
        raise
    except Exception:
        return None


def _normalized_modes(modes: Any) -> list[str]:
    if not modes:
        return list(EXECUTION_MODES)
    values = [str(mode) for mode in modes]
    if any(mode not in EXECUTION_MODES for mode in values):
        raise ProfilerUsageError("bench_subgraph_execution_mode_invalid")
    return values


def execute_joint_case(executor: OperatorExecutor, case: Mapping[str, Any],
                       protocol: MeasurementProtocol, runtime: Any,
                       *, execution_modes: Any = None,
                       blocker: Any = None,
                       blocker_receipt: Mapping[str, Any] | None = None
                       ) -> dict[str, Any]:
    """Run one S1 case eagerly, then as a captured graph, and compare."""
    modes = _normalized_modes(execution_modes)
    ordered = topological_order(case)
    pre, timed = _joint_split(case, ordered)
    upstream = _data_upstream(case)
    run_kwargs: dict[str, Any] = {}
    if blocker is not None:
        run_kwargs.update({"blocker": blocker,
                           "blocker_receipt": blocker_receipt})
    for node in pre:
        node_id = str(node.get("node_id"))
        _launch(executor, node, _upstream(executor, node_id, upstream))
    runtime.synchronize()

    def launch_all():
        return [_launch(executor, node,
                        _upstream(executor, str(node.get("node_id")), upstream))
                for node in timed]

    eager_outputs = [_detach(executor.torch, value) for value in launch_all()]
    eager = protocol.run(lambda: launch_all(),
                         case_id=f"{case.get('case_id')}.eager",
                         kind="operator", **run_kwargs)
    graph = None
    capture_receipt: dict[str, Any] = {"status": "skipped", "mode": "eager"}
    qualified = True
    agreement = None
    if "aclgraph" in modes:
        captured, capture_receipt = runtime.capture(
            launch_all, f"{case.get('case_id')}.aclgraph")
        replay_outputs = runtime.replay(captured) if captured is not None else None
        if isinstance(replay_outputs, (list, tuple)) and (
                len(eager_outputs) == len(replay_outputs)):
            agreement = all(_same_outputs(left, right, executor.torch)
                            for left, right in zip(eager_outputs, replay_outputs))
        else:
            agreement = False
        qualified = bool(captured is not None and agreement is True)
        if captured is not None:
            graph = protocol.run(lambda: runtime.replay(captured),
                                 case_id=f"{case.get('case_id')}.aclgraph",
                                 kind="operator", **run_kwargs)
    return {"case_id": str(case.get("case_id")),
            "status": "ok" if qualified else "unqualified",
            "split": str(case.get("split") or "train"),
            "execution_modes": modes,
            "timed_nodes": [str(node.get("node_id")) for node in timed],
            "cut_nodes": [str(node.get("node_id")) for node in pre],
            "environment_mode": "separate_contexts",
            "eager": eager, "aclgraph": graph,
            "capture": capture_receipt, "outputs_agree": agreement,
            "qualified": qualified,
            "minimum_ms": eager["minimum_ms"], "startup_ms": 0.0}


class TorchJointRuntime:
    """HCCL group construction plus ACLGraph capture/replay adapter."""

    def __init__(self, torch: Any, *, rank: int = 0, world_size: int = 1,
                 parallel: Mapping[str, Any] | None = None,
                 timeout_s: float = 300.0) -> None:
        self.torch = torch
        self.rank = int(rank)
        self.world_size = int(world_size)
        self.parallel = dict(parallel or {})
        self.timeout_s = float(timeout_s)
        self.groups: dict[str, Any] = {}
        self.initialized = False
        self.dist = None

    def init_process_group(self) -> dict[str, Any]:
        """Initialize HCCL once and create the declared axis groups in order."""
        self.dist = importlib.import_module("torch.distributed")
        if self.world_size > 1:
            from datetime import timedelta

            self.dist.init_process_group("hccl", rank=self.rank,
                                         world_size=self.world_size,
                                         timeout=timedelta(seconds=self.timeout_s))
            self.initialized = True
        for axis in sorted(("tp", "ep", "sp", "mc2")):
            declared = self.parallel.get(axis)
            if isinstance(declared, bool):
                if not declared:
                    continue
                size = max(int(self.parallel.get("tp") or 1),
                           int(self.parallel.get("ep") or 1))
            else:
                size = int(declared or 1)
            if size <= 1:
                continue
            self.groups[axis] = self.dist.new_group(
                list(range(min(size, self.world_size))))
        return {"world_size": self.world_size, "rank": self.rank,
                "groups": sorted(self.groups), "initialized": self.initialized}

    def close(self) -> None:
        if self.initialized and self.dist is not None:
            self.dist.destroy_process_group()
            self.initialized = False

    def synchronize(self) -> None:
        sync = getattr(self.torch.npu, "synchronize", None)
        if callable(sync):
            sync()

    def capture(self, call: Callable[[], Any], case_id: str) -> tuple[Any, dict[str, Any]]:
        factory = getattr(self.torch.npu, "NPUGraph", None)
        if not callable(factory):
            return None, {"status": "unsupported_binding",
                          "reason": "torch.npu.NPUGraph unavailable"}
        graph = factory()
        context = getattr(self.torch.npu, "graph", None)
        if not callable(context):
            return None, {"status": "unsupported_binding",
                          "reason": "torch.npu.graph unavailable"}
        with context(graph):
            outputs = call()
        return (graph, outputs), {"status": "captured", "case_id": case_id,
                                  "mode": "aclgraph"}

    def replay(self, captured: Any) -> Any:
        if not isinstance(captured, tuple) or len(captured) != 2:
            return None
        graph, outputs = captured
        replay = getattr(graph, "replay", None)
        if callable(replay):
            replay()
        return outputs


def _skipped_stage(case: Mapping[str, Any], stage: str) -> dict[str, Any]:
    return {"case_id": str(case.get("case_id")), "status": "skipped_stage",
            "reason": f"case belongs to {stage}", "split": str(
                case.get("split") or "train")}


def run_plan(plan: Mapping[str, Any], *, runtime: Any = None,
             protocol: MeasurementProtocol | None = None,
             executor: OperatorExecutor | None = None,
             observations: Any = None, run_id: str | None = None) -> dict[str, Any]:
    """Execute every planned case for the plan's stage with per-case scoping."""
    stage = str(plan["stage"])
    cases = list(plan["cases"])
    records: list[dict[str, Any]] = []
    journal = (None if observations is None else observations
               if hasattr(observations, "append")
               else ObservationJournal(observations))
    context = (getattr(executor, "context", None) or {}) if executor is not None else {}
    identity = run_id or plan.get("plan_id") or "subgraph"
    for case in cases:
        if stage == "s0_local" and (case.get("stage") == "s1_joint"
                                    or case.get("kind") == "fabric"):
            records.append(_skipped_stage(case, "s1_joint"))
            continue
        skipped = None
        reset = getattr(executor, "reset", None)
        if callable(reset):
            reset()
        if case_over_budget(case, context.get("budget")):
            skipped = {"case_id": str(case.get("case_id")),
                       "status": "over_budget", "split": str(
                           case.get("split") or "train")}
            records.append(skipped)
            continue
        try:
            if stage == "s0_local":
                record = execute_local_case(executor, case, protocol)
            else:
                record = execute_joint_case(
                    executor, case, protocol, runtime,
                    execution_modes=plan.get("execution_modes") or ["eager"],
                    blocker=context.get("blocker"),
                    blocker_receipt=context.get("blocker_receipt"))
        except TimeoutError:
            raise
        except ProfilerUsageError as exc:
            record = {"case_id": str(case.get("case_id")),
                      "status": "unsupported_binding", "reason": str(exc)}
        records.append(record)
        _emit_case_observations(journal, plan, case, record, identity, stage)
    ok = all(record["status"] in {"ok", "skipped_stage"} for record in records)
    return {"schema": RUN_SCHEMA, "status": "ok" if ok else "partial",
            "stage": stage, "plan_id": plan.get("plan_id"),
            "case_count": len(cases), "records": records}


def _timing_rows(timing: Mapping[str, Any]) -> Iterable[tuple[str, int, int,
                                                               float]]:
    modes = timing.get("modes") if isinstance(timing.get("modes"), Mapping) else {}
    for mode, summary in modes.items():
        for trial in (summary or {}).get("trials") or ():
            for index, value in enumerate(trial.get("repeats_us") or ()):
                yield str(mode), int(trial.get("trial") or 0), index, float(value)


def _emit_case_observations(journal: Any, plan: Mapping[str, Any],
                            case: Mapping[str, Any], record: Mapping[str, Any],
                            run_id: str, stage: str) -> None:
    if journal is None or record.get("status") not in {"ok", "unqualified"}:
        return
    timing = record.get("timing") or record.get("eager") or {}
    if not isinstance(timing, Mapping):
        return
    split = str(case.get("split") or "train")
    boundary = str(case.get("boundary") or DEFAULT_OBSERVATION_BOUNDARY)
    identities = (case.get("identities")
                  if isinstance(case.get("identities"), Mapping) else {})
    service = identities.get("service")
    facets = ("work", "resource", "work_unit", "active_units")
    capabilities = ({key: service.get(key) for key in facets}
                    if isinstance(service, Mapping) else (
                        {"work": timing.get("minimum_ms"),
                         "resource": case.get("resource"),
                         "work_unit": case.get("work_unit"),
                         "active_units": case.get("active_units")}
                        if case.get("work_unit") else {}))
    for mode, trial, repeat_index, repeat_us in _timing_rows(timing):
        row = observation_row(
            plan_id=plan.get("plan_id"), case=case, run_id=f"{run_id}.{mode}.t{trial}", split=split,
            boundary=boundary, timing_mode=mode,
            residency=str(case.get("residency") or "device"),
            trial=trial, repeat_index=repeat_index, rank=case.get("rank"),
            duration_ms=repeat_us / 1000.0,
            source=f"capture://bench-subgraph/{case.get('case_id')}/{mode}."
                   f"{trial}.{repeat_index}",
            validated=bool(record.get("validated", True)),
            qualified=bool(record.get("qualified", True)),
            level=str(case.get("level") or "subgraph"),
            phase=case.get("phase"), execution={"mode": mode, "stage": stage},
            work_bytes=case.get("work_bytes"), key=identities.get("primitive_key"),
            identity_override=identities.get("accuracy_identity"),
            service_identity=(service.get("identity")
                              if isinstance(service, Mapping) else None),
            **capabilities)
        journal.append(row)
    journal.append(case_complete_row(
        plan_id=plan.get("plan_id"), case_id=case.get("case_id"),
        run_id=run_id, status=str(record.get("status")), split=split,
        summary={"stage": stage, "timed_nodes": record.get("timed_nodes")}))


def _subgraph_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler bench subgraph",
        description="Replay exported S0 local chains or S1 joined subgraphs.",
        allow_abbrev=False)
    parser.add_argument("--plan", required=True, help="exported subgraph plan JSON")
    parser.add_argument("--stage", default=None, choices=STAGES, help="override the plan stage")
    parser.add_argument("--execution-mode", action="append", default=None,
                        choices=EXECUTION_MODES, help="restrict modes (repeatable)")
    parser.add_argument("--allowed-phy-ids", default=None,
                        help="physical die allowlist, e.g. '12..15'")
    parser.add_argument("--observations", default=None,
                        help="append mindie-bench-observation/1 rows here")
    parser.add_argument("--out", "--output", dest="output", default=None,
                        help="write JSON here (atomic); otherwise print to stdout")
    parser.add_argument("--dry-run", action="store_true",
                        help="validate and summarize the plan without importing torch")
    return parser


def _rank_environment(plan: Mapping[str, Any]) -> tuple[int, int]:
    plan_rank = plan.get("rank")
    rank = int(os.environ.get("RANK", str(plan_rank if plan_rank is not None else 0)))
    world = int(os.environ.get("WORLD_SIZE", str(plan.get("world_size") or 1)))
    return rank, world


def _rank_mismatch(plan: Mapping[str, Any], rank: int, world: int) -> bool:
    if plan.get("rank") is not None:
        return (int(plan["rank"]), int(plan.get("world_size") or 1)) != (rank, world)
    return (str(plan.get("stage")) == "s1_joint"
            and int(plan.get("world_size") or 1) > 1
            and int(plan.get("world_size") or 1) != world)


def main(argv: Sequence[str] | None = None) -> int:
    args = _subgraph_parser().parse_args(list(argv or ()))
    plan = load_plan(args.plan)
    if args.stage:
        plan["stage"] = args.stage
    modes = args.execution_mode or list(plan.get("execution_modes") or ["eager"])
    plan["execution_modes"] = list(modes)
    rank, world = _rank_environment(plan)
    if _rank_mismatch(plan, rank, world):
        _emit({"schema": RUN_SCHEMA, "status": "rank_mismatch",
               "plan": [plan.get("rank"), plan.get("world_size")],
               "environment": [rank, world]}, args.output)
        return 2
    summary = {
        "schema": RUN_SCHEMA, "status": "dry_run", "plan_id": plan.get("plan_id"),
        "stage": plan["stage"], "execution_modes": plan["execution_modes"],
        "case_count": len(plan["cases"]),
        "cases": [{"case_id": case.get("case_id"), "split": case.get("split", "train"),
                   "archetype": case.get("archetype"),
                   "nodes": [str(node.get("node_id")) for node in case["nodes"]]}
                  for case in plan["cases"]],
    }
    if args.dry_run:
        _emit(portable_receipt(summary, home=os.environ.get("HOME")), args.output)
        return 0
    try:
        import torch
        import torch_npu  # noqa: F401
    except TimeoutError:
        raise
    except Exception as exc:
        _emit({"schema": RUN_SCHEMA, "status": "torch_npu_unavailable",
               "reason": str(exc)[:400]}, args.output)
        return 3
    from .timing import admit_context, close_context

    journal = ObservationJournal(args.observations) if args.observations else None
    context = admit_context(
        torch=torch, torch_npu=torch_npu,
        allowed_phy_ids=resolve_allowed_phy_ids(args.allowed_phy_ids),
        l2_bytes=None, allocate=False)
    context.update({"rank": rank, "world_size": world})
    try:
        runtime = TorchJointRuntime(torch, rank=rank, world_size=world,
                                    parallel=plan.get("parallel"))
        runtime.init_process_group()
        context.update({"dist": runtime.dist, "groups": runtime.groups,
                        "dist_initialized": runtime.initialized})
        executor = OperatorExecutor(torch, context)
        try:
            result = run_plan(plan, runtime=runtime, protocol=context["protocol"],
                              executor=executor, observations=journal,
                              run_id=str(plan.get("plan_id") or "subgraph"))
        finally:
            reset = getattr(executor, "reset", None)
            if callable(reset):
                reset()
            runtime.close()
    finally:
        close_context(context)
    output = args.output
    if output and world > 1:
        output = f"{output}.rank{rank}.json"
    _emit(portable_receipt(result, home=os.environ.get("HOME")), output)
    return 0 if result["status"] == "ok" else 2


def _emit(payload: Mapping[str, Any], output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(text, encoding="utf-8", newline="\n")
        os.replace(temporary, target)
        print(json.dumps({"output": str(target), "status": payload.get("status")},
                         sort_keys=True))
        return
    import sys

    sys.stdout.write(text)


__all__ = [
    "COLLECTIVE_OPS", "_bind_collective", "EDGE_KINDS", "EXECUTION_MODES", "NODE_SCHEMA",
    "OPERATOR_BUILDERS", "OperatorExecutor", "PLAN_SCHEMA", "RUN_SCHEMA",
    "STAGES", "TorchJointRuntime", "build_operator_enqueue", "device_of",
    "execute_joint_case", "execute_local_case", "load_plan", "main",
    "plan_timed_cut", "resolve_op", "run_plan", "split_timed", "torch_dtype",
    "topological_order", "validate_plan", "EventTimer", "TorchTimingRuntime",
]
