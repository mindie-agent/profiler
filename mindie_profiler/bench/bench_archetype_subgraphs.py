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
  * A collective inside the declared S0 timed window or splitting a local chain
    is refused; single-rank S0 cuts supply preallocated boundary tensors.
  * ``host_fallback`` fails closed unless ``--allow-cpu-smoke`` is explicitly
    requested; missing kernels attach ``mindie-unmodeled-structure-hint/1``.
  * Every case keeps its frozen ``train``/``heldout`` split.

[Timeouts & Locks]
  No locks.  Process-group initialization uses an explicit finite timeout and
  the caller's container budget bounds the launch.

[Side-Effect Policy]
  Reads the plan and writes only the requested ``--out`` JSON/observations; the
  S1 arm owns one HCCL process group and destroys it in ``finally``.
"""

from __future__ import annotations

import argparse, importlib, json, os, sys
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from ..events import ProfilerUsageError
from .abi import portable_receipt, resolve_allowed_phy_ids
from .observations import ObservationJournal
from .operators import (
    BenchUnmodeledOperatorError, COLLECTIVE_OPS, OPERATOR_BUILDERS,
    _bind_collective, build_operator_enqueue, device_of, resolve_op,
    supports_cold_ring, torch_dtype,
)
from .profiles import profile_section
from .subgraph_runtime import (
    DEFAULT_OBSERVATION_BOUNDARY, TorchJointRuntime, _emit_case_observations,
)
from .timing import (
    HOST_FALLBACK, EventTimer, MeasurementProtocol, TorchTimingRuntime, case_over_budget,
)

_CFG = profile_section("subgraph")

PLAN_SCHEMA = "mindie-bench-subgraph-plan/1"
RUN_SCHEMA = "mindie-bench-subgraph-run/1"
NODE_SCHEMA = "mindie-bench-subgraph-node/1"
STAGES = ("s0_local", "s1_joint")
EXECUTION_MODES = ("eager", "aclgraph")
EDGE_KINDS = ("stream", "wait", "data")
NODE_KINDS = ("operator", "collective", "boundary")
MAX_PLAN_BYTES = int(_CFG["max_plan_bytes"])
MAX_CASES = int(_CFG["max_cases"])
MAX_NODES = int(_CFG["max_nodes"])
MAX_EDGES = int(_CFG["max_edges"])
MAX_WORLD = int(_CFG["max_world"])
BOUNDARY_BYTES = int(_CFG["boundary_bytes"])
_FP32_BYTES = int(_CFG["float32_element_bytes"])
_ALLCLOSE_TOL = float(_CFG["allclose_tol"])
_REASON_LIMIT = int(_CFG["max_reason_chars"])
_EXIT_ERR = int(_CFG["exit_error"])
_EXIT_UNAVAIL = int(_CFG["exit_torch_unavailable"])
FLOAT32_NAME = "float32"


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProfilerUsageError(reason)


def _bounded(value: Any, reason: str, limit: int) -> None:
    _require(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 0 <= int(value) <= limit,
        reason,
    )


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
        _require(
            isinstance(edges, list) and len(edges) <= MAX_EDGES,
            "bench_subgraph_edges_invalid",
        )
        for node in nodes:
            if not isinstance(node, Mapping):
                raise ProfilerUsageError("bench_subgraph_node_invalid")
            if str(node.get("kind") or "operator") not in NODE_KINDS:
                raise ProfilerUsageError(
                    f"bench_subgraph_node_kind_invalid: {node.get('kind')!r}"
                )
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
    return str(node.get("kind")) == "collective" or str(node.get("op")) in COLLECTIVE_OPS


def _adjacency(
    case: Mapping[str, Any],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
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
            raise ProfilerUsageError(
                f"bench_collective_inside_timed_window: {node.get('node_id')}"
            )
    timed_nodes = [dict(node) for node in ordered if not is_collective(node)]
    if included:
        timed_nodes = [
            dict(node)
            for node in ordered
            if str(node.get("node_id")) in included and not is_collective(node)
        ]
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


def _data_upstream(case: Mapping[str, Any]) -> dict[str, list[str]]:
    upstream: dict[str, list[str]] = {}
    for edge in case.get("edges") or ():
        if str(edge.get("kind") or "data") == "data":
            upstream.setdefault(str(edge["to"]), []).append(str(edge["from"]))
    return upstream


def _detach(value: Any) -> Any:
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
                self.torch, node, self.context, hot=hot
            )
        return self.built[key]

    def launch(
        self, node: Mapping[str, Any], upstream: Sequence[Any] = (), *, hot: bool = False
    ) -> Any:
        node_id = str(node.get("node_id"))
        self.context["_node_inputs"] = list(upstream)
        try:
            output = self.build(node, hot=hot)()
        finally:
            self.context.pop("_node_inputs", None)
        self.outputs[node_id] = output
        return output

    def upstream(self, node_ids: Iterable[str]) -> list[Any]:
        return [self.outputs[node_id] for node_id in node_ids if node_id in self.outputs]

    def supply_boundary(self, node: Mapping[str, Any]) -> Any:
        shape = node.get("shape") if isinstance(node.get("shape"), Mapping) else {}
        nbytes = int(node.get("nbytes") or shape.get("bytes") or BOUNDARY_BYTES)
        elements = max(1, nbytes // _FP32_BYTES)
        tensor = self.torch.zeros(
            elements,
            dtype=getattr(self.torch, FLOAT32_NAME, None),
            device=device_of(self.context),
        )
        self.outputs[str(node.get("node_id"))] = tensor
        return tensor

    def reset(self) -> None:
        self.built.clear()
        self.outputs.clear()
        self.context.pop("_node_inputs", None)


def _dist_ready(context: Mapping[str, Any] | None) -> bool:
    return bool(
        isinstance(context, Mapping)
        and context.get("dist") is not None
        and context.get("dist_initialized")
    )


def _upstream(
    executor: Any, node_id: str, upstream: Mapping[str, list[str]]
) -> list[Any]:
    getter = getattr(executor, "upstream", None)
    return getter(upstream.get(node_id, ())) if callable(getter) else []


def _launch(
    executor: Any, node: Mapping[str, Any], upstream: Sequence[Any], *, hot: bool = False
) -> Any:
    if hot:
        return executor.launch(node, upstream, hot=True)
    return executor.launch(node, upstream) if upstream else executor.launch(node)


def _run_pre(
    executor: Any, pre: Sequence[Mapping[str, Any]], upstream: Mapping[str, list[str]]
) -> list[str]:
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


def execute_local_case(
    executor: OperatorExecutor, case: Mapping[str, Any], protocol: MeasurementProtocol
) -> dict[str, Any]:
    """Run one S0 case: cut collectives pre/post, time only the local chain."""
    ordered = topological_order(case)
    cut = plan_timed_cut(case, ordered)
    upstream = _data_upstream(case)
    executed_pre = _run_pre(executor, cut["pre"], upstream)
    synchronize = getattr(getattr(executor.torch, "npu", None), "synchronize", None)
    if callable(synchronize):
        synchronize()
    ctx = getattr(executor, "context", None) or {}
    ring = ctx.get("ring")
    ring_ready = bool(
        ring is not None
        and getattr(ring, "allocated", False)
        and any(supports_cold_ring(node) for node in cut["timed"])
    )
    timed_nodes = [
        dict(node, cold_ring=True) if ring_ready and supports_cold_ring(node) else node
        for node in cut["timed"]
    ]

    def enqueue() -> Any:
        result = None
        for node in timed_nodes:
            node_id = str(node.get("node_id"))
            result = _launch(executor, node, _upstream(executor, node_id, upstream))
        return result

    run_kwargs: dict[str, Any] = {
        "case_id": str(case.get("case_id")),
        "kind": "operator",
        "nbytes": int(case.get("work_bytes") or 0),
    }
    if ring_ready:
        run_kwargs["cold_ring"] = ring
        run_kwargs["hot_enqueue"] = lambda: [
            _launch(executor, node, _upstream(executor, str(node.get("node_id")), upstream), hot=True)
            for node in timed_nodes
        ]
    timing = protocol.run(enqueue, **run_kwargs)
    if not ctx.get("allow_cpu_smoke") and (
        timing.get("timer_source") == "perf_counter_host_fallback"
        or HOST_FALLBACK in (timing.get("modes") or {})
    ):
        raise ProfilerUsageError("bench_host_fallback_forbidden")
    executed_post = _run_pre(executor, cut["post"], upstream)
    return {
        "case_id": str(case.get("case_id")),
        "status": "ok",
        "split": str(case.get("split") or "train"),
        "archetype": case.get("archetype"),
        "timed_nodes": [str(node.get("node_id")) for node in cut["timed"]],
        "cut_nodes": executed_pre + executed_post,
        "pre_nodes": executed_pre,
        "post_nodes": executed_post,
        "single_rank_boundary_tensors": bool(
            cut["pre"] and not _dist_ready(getattr(executor, "context", None))
        ),
        "timing": timing,
        "minimum_ms": timing["minimum_ms"],
        "startup_ms": 0.0,
    }


def _joint_split(
    case: Mapping[str, Any], ordered: Sequence[Mapping[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    include = {
        str(item) for item in ((case.get("timed_boundary") or {}).get("include") or ())
    }
    if not include:
        return [], [dict(node) for node in ordered]
    return (
        [dict(node) for node in ordered if str(node.get("node_id")) not in include],
        [dict(node) for node in ordered if str(node.get("node_id")) in include],
    )


def _same_outputs(left: Any, right: Any, torch: Any) -> bool | None:
    if left is None and right is None:
        return True
    allclose = getattr(torch, "allclose", None)
    try:
        return (
            bool(allclose(left, right, rtol=_ALLCLOSE_TOL, atol=_ALLCLOSE_TOL))
            if callable(allclose)
            else bool(left == right)
        )
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


def execute_joint_case(
    executor: OperatorExecutor,
    case: Mapping[str, Any],
    protocol: MeasurementProtocol,
    runtime: Any,
    *,
    execution_modes: Any = None,
    blocker: Any = None,
    blocker_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one S1 case eagerly, then as a captured graph, and compare."""
    modes = _normalized_modes(execution_modes)
    ordered = topological_order(case)
    pre, timed = _joint_split(case, ordered)
    upstream = _data_upstream(case)
    run_kwargs: dict[str, Any] = {}
    if blocker is not None:
        run_kwargs.update({"blocker": blocker, "blocker_receipt": blocker_receipt})
    for node in pre:
        node_id = str(node.get("node_id"))
        _launch(executor, node, _upstream(executor, node_id, upstream))
    runtime.synchronize()

    def launch_all() -> list[Any]:
        return [
            _launch(executor, node, _upstream(executor, str(node.get("node_id")), upstream))
            for node in timed
        ]

    eager_outputs = [_detach(value) for value in launch_all()]
    eager = protocol.run(
        launch_all, case_id=f"{case.get('case_id')}.eager", kind="operator", **run_kwargs
    )
    ctx = getattr(executor, "context", None) or {}
    if not ctx.get("allow_cpu_smoke") and (
        eager.get("timer_source") == "perf_counter_host_fallback"
        or HOST_FALLBACK in (eager.get("modes") or {})
    ):
        raise ProfilerUsageError("bench_host_fallback_forbidden")
    graph = None
    capture_receipt: dict[str, Any] = {"status": "skipped", "mode": "eager"}
    qualified = True
    agreement = None
    if "aclgraph" in modes:
        captured, capture_receipt = runtime.capture(
            launch_all, f"{case.get('case_id')}.aclgraph"
        )
        replay_outputs = runtime.replay(captured) if captured is not None else None
        if isinstance(replay_outputs, (list, tuple)) and (
            len(eager_outputs) == len(replay_outputs)
        ):
            agreement = all(
                _same_outputs(left, right, executor.torch)
                for left, right in zip(eager_outputs, replay_outputs)
            )
        else:
            agreement = False
        qualified = bool(captured is not None and agreement is True)
        if captured is not None:
            graph = protocol.run(
                lambda: runtime.replay(captured),
                case_id=f"{case.get('case_id')}.aclgraph",
                kind="operator",
                **run_kwargs,
            )
    return {
        "case_id": str(case.get("case_id")),
        "status": "ok" if qualified else "unqualified",
        "split": str(case.get("split") or "train"),
        "execution_modes": modes,
        "timed_nodes": [str(node.get("node_id")) for node in timed],
        "cut_nodes": [str(node.get("node_id")) for node in pre],
        "environment_mode": "separate_contexts",
        "eager": eager,
        "aclgraph": graph,
        "capture": capture_receipt,
        "outputs_agree": agreement,
        "qualified": qualified,
        "minimum_ms": eager["minimum_ms"],
        "startup_ms": 0.0,
    }


def _skipped_stage(case: Mapping[str, Any], stage: str) -> dict[str, Any]:
    return {
        "case_id": str(case.get("case_id")),
        "status": "skipped_stage",
        "reason": f"case belongs to {stage}",
        "split": str(case.get("split") or "train"),
    }


def run_plan(
    plan: Mapping[str, Any],
    *,
    runtime: Any = None,
    protocol: MeasurementProtocol | None = None,
    executor: OperatorExecutor | None = None,
    observations: Any = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Execute every planned case for the plan's stage with per-case scoping."""
    stage = str(plan["stage"])
    cases = list(plan["cases"])
    records: list[dict[str, Any]] = []
    journal = (
        None
        if observations is None
        else observations
        if hasattr(observations, "append")
        else ObservationJournal(observations)
    )
    context = (getattr(executor, "context", None) or {}) if executor is not None else {}
    identity = run_id or plan.get("plan_id") or "subgraph"
    for case in cases:
        if stage == "s0_local" and (
            case.get("stage") == "s1_joint" or case.get("kind") == "fabric"
        ):
            records.append(_skipped_stage(case, "s1_joint"))
            continue
        reset = getattr(executor, "reset", None)
        if callable(reset):
            reset()
        if case_over_budget(case, context.get("budget")):
            records.append(
                {
                    "case_id": str(case.get("case_id")),
                    "status": "over_budget",
                    "split": str(case.get("split") or "train"),
                }
            )
            continue
        try:
            if stage == "s0_local":
                record = execute_local_case(executor, case, protocol)
            else:
                record = execute_joint_case(
                    executor,
                    case,
                    protocol,
                    runtime,
                    execution_modes=plan.get("execution_modes") or ["eager"],
                    blocker=context.get("blocker"),
                    blocker_receipt=context.get("blocker_receipt"),
                )
        except TimeoutError:
            raise
        except ProfilerUsageError as exc:
            record = {
                "case_id": str(case.get("case_id")),
                "status": "unsupported_binding",
                "reason": str(exc),
            }
            if isinstance(exc, BenchUnmodeledOperatorError):
                record["unmodeled_hint"] = dict(exc.payload)
        records.append(record)
        _emit_case_observations(journal, plan, case, record, identity, stage)
    ok = all(record["status"] in {"ok", "skipped_stage"} for record in records)
    return {
        "schema": RUN_SCHEMA,
        "status": "ok" if ok else "partial",
        "stage": stage,
        "plan_id": plan.get("plan_id"),
        "case_count": len(cases),
        "records": records,
    }


def _subgraph_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler bench subgraph",
        description="Replay exported S0 local chains or S1 joined subgraphs.",
        allow_abbrev=False,
    )
    parser.add_argument("--plan", required=True, help="exported subgraph plan JSON")
    parser.add_argument("--stage", default=None, choices=STAGES, help="override plan stage")
    parser.add_argument(
        "--execution-mode", action="append", default=None, choices=EXECUTION_MODES
    )
    parser.add_argument("--allowed-phy-ids", default=None, help="physical die allowlist")
    parser.add_argument(
        "--allow-cpu-smoke",
        action="store_true",
        help="permit host-clock smoke runs without device events",
    )
    parser.add_argument("--observations", default=None, help="append observation rows here")
    parser.add_argument("--out", "--output", dest="output", default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _rank_environment(plan: Mapping[str, Any]) -> tuple[int, int]:
    plan_rank = plan.get("rank")
    rank = int(os.environ.get("RANK", str(plan_rank if plan_rank is not None else 0)))
    world = int(os.environ.get("WORLD_SIZE", str(plan.get("world_size") or 1)))
    return rank, world


def _rank_mismatch(plan: Mapping[str, Any], rank: int, world: int) -> bool:
    if plan.get("rank") is not None:
        return (int(plan["rank"]), int(plan.get("world_size") or 1)) != (rank, world)
    return (
        str(plan.get("stage")) == "s1_joint"
        and int(plan.get("world_size") or 1) > 1
        and int(plan.get("world_size") or 1) != world
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _subgraph_parser().parse_args(list(argv or ()))
    plan = load_plan(args.plan)
    if args.stage:
        plan["stage"] = args.stage
    plan["execution_modes"] = list(
        args.execution_mode or list(plan.get("execution_modes") or ["eager"])
    )
    rank, world = _rank_environment(plan)
    if _rank_mismatch(plan, rank, world):
        _emit(
            {
                "schema": RUN_SCHEMA,
                "status": "rank_mismatch",
                "plan": [plan.get("rank"), plan.get("world_size")],
                "environment": [rank, world],
            },
            args.output,
        )
        return _EXIT_ERR
    summary = {
        "schema": RUN_SCHEMA,
        "status": "dry_run",
        "plan_id": plan.get("plan_id"),
        "stage": plan["stage"],
        "execution_modes": plan["execution_modes"],
        "case_count": len(plan["cases"]),
        "cases": [
            {
                "case_id": case.get("case_id"),
                "split": case.get("split", "train"),
                "archetype": case.get("archetype"),
                "nodes": [str(node.get("node_id")) for node in case["nodes"]],
            }
            for case in plan["cases"]
        ],
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
        _emit(
            {"schema": RUN_SCHEMA, "status": "torch_npu_unavailable", "reason": str(exc)[:_REASON_LIMIT]},
            args.output,
        )
        return _EXIT_UNAVAIL
    from .timing import admit_context, close_context

    journal = ObservationJournal(args.observations) if args.observations else None
    context = admit_context(
        torch=torch,
        torch_npu=torch_npu,
        allowed_phy_ids=resolve_allowed_phy_ids(args.allowed_phy_ids),
        l2_bytes=None,
        allocate=False,
        allow_cpu_smoke=bool(args.allow_cpu_smoke),
    )
    context.update({"rank": rank, "world_size": world})
    try:
        runtime = TorchJointRuntime(
            torch, rank=rank, world_size=world, parallel=plan.get("parallel")
        )
        runtime.init_process_group()
        context.update(
            {
                "dist": runtime.dist,
                "groups": runtime.groups,
                "dist_initialized": runtime.initialized,
            }
        )
        executor = OperatorExecutor(torch, context)
        try:
            result = run_plan(
                plan,
                runtime=runtime,
                protocol=context["protocol"],
                executor=executor,
                observations=journal,
                run_id=str(plan.get("plan_id") or "subgraph"),
            )
        finally:
            reset = getattr(executor, "reset", None)
            if callable(reset):
                reset()
            runtime.close()
    finally:
        close_context(context)
    output = f"{args.output}.rank{rank}.json" if args.output and world > 1 else args.output
    _emit(portable_receipt(result, home=os.environ.get("HOME")), output)
    return 0 if result["status"] == "ok" else _EXIT_ERR


def _emit(payload: Mapping[str, Any], output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(text, encoding="utf-8", newline="\n")
        os.replace(temporary, target)
        print(json.dumps({"output": str(target), "status": payload.get("status")}, sort_keys=True))
        return
    sys.stdout.write(text)


__all__ = [
    "COLLECTIVE_OPS", "_bind_collective", "EDGE_KINDS", "EXECUTION_MODES",
    "EventTimer", "NODE_SCHEMA", "OPERATOR_BUILDERS", "OperatorExecutor",
    "PLAN_SCHEMA", "RUN_SCHEMA", "STAGES", "TorchJointRuntime",
    "TorchTimingRuntime", "build_operator_enqueue", "device_of",
    "execute_joint_case", "execute_local_case", "load_plan", "main",
    "plan_timed_cut", "resolve_op", "run_plan", "split_timed", "torch_dtype",
    "topological_order", "validate_plan",
]
