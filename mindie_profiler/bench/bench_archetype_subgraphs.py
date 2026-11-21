"""Ten-archetype subgraph replay: S0 local chains and S1 joined collectives.

[Role]
  Load the exported ``mindie-bench-subgraph-plan/1`` plan, validate its case,
  node and edge contract, execute S0 local chains with collectives cut outside
  the timed window, and execute S1 ``torchrun`` joined subgraphs in eager and
  ACLGraph replay with output agreement checks.  Topological cut, dataflow
  execution and observation helpers live in ``bench.subgraph_runtime`` and are
  re-exported here for the CLI contract.

[Invariants]
  * Dispatch is by declared binding/builder, never by archetype, model id or
    case id; the ten archetype names are reporting labels only.
  * A collective inside the declared S0 timed window or splitting a local chain
    is refused; single-rank S0 cuts supply preallocated boundary tensors.
  * ``host_fallback`` fails closed unless ``--allow-cpu-smoke`` is explicitly
    requested; missing kernels attach ``mindie-unmodeled-structure-hint/1``.
  * Every case keeps its frozen ``train``/``heldout`` split, and every
    execution of the same plan gets a unique run id for conflict-free packets.

[Timeouts & Locks]
  No locks.  Process-group initialization uses an explicit finite timeout and
  the caller's container budget bounds the launch.

[Side-Effect Policy]
  Reads the plan and writes only the requested ``--out`` JSON/observations; the
  S1 arm owns one HCCL process group and destroys it in ``finally``.
"""

from __future__ import annotations

import argparse, json, os, sys, uuid
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..events import ProfilerUsageError
from .abi import portable_receipt, resolve_allowed_phy_ids
from .observations import ObservationJournal
from .operators import (
    BenchUnmodeledOperatorError, COLLECTIVE_OPS, OPERATOR_BUILDERS,
    _bind_collective, build_operator_enqueue, device_of, resolve_op,
    torch_dtype,
)
from .profiles import profile_section
from .subgraph_runtime import (
    DECODE_GRAPH_POLICY, DEFAULT_EXECUTION_MODES, DEFAULT_OBSERVATION_BOUNDARY,
    OperatorExecutor, TorchJointRuntime,
    _adjacency, _cold_ring_capable, _data_upstream, _detach, _dist_ready,
    _emit_case_observations, _joint_split, _launch, _normalized_modes,
    _output_snapshot, _run_pre, _same_outputs, _upstream, execute_joint_case,
    execute_local_case, is_collective, plan_timed_cut,
    resolve_case_execution_modes, split_timed, topological_order,
)
from .timing import (
    EventTimer, MeasurementProtocol, MIB, TorchTimingRuntime, _positive_int,
    calibrate_blocker, case_over_budget,
)
from .timing_ring import make_blocker_unit_op, resolve_l2_bytes

_CFG = profile_section("subgraph")
_TIMING_CFG = profile_section("timing")

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
_REASON_LIMIT = int(_CFG["max_reason_chars"])
_EXIT_ERR = int(_CFG["exit_error"])
_EXIT_UNAVAIL = int(_CFG["exit_torch_unavailable"])
_RUN_SUFFIX_CHARS = 2 * 2 * 2


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProfilerUsageError(reason)


def _bounded(value: Any, reason: str, limit: int) -> None:
    _require(
        isinstance(value, (int, float)) and not isinstance(value, bool)
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
    modes = plan.get("execution_modes") or list(DEFAULT_EXECUTION_MODES)
    if any(str(mode) not in EXECUTION_MODES for mode in modes):
        raise ProfilerUsageError("bench_subgraph_execution_mode_invalid")
    plan["execution_modes"] = [str(mode) for mode in modes]
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


def _new_run_id(plan: Mapping[str, Any]) -> str:
    return f"{plan.get('plan_id') or 'subgraph'}-{uuid.uuid4().hex[:_RUN_SUFFIX_CHARS]}"


def _participant_ranks(case: Mapping[str, Any]) -> set[int] | None:
    ranks = case.get("group_ranks")
    if not isinstance(ranks, (list, tuple, set, frozenset)):
        ranks = case.get("participants")
    if not isinstance(ranks, (list, tuple, set, frozenset)):
        return None
    values = {int(item) for item in ranks
              if isinstance(item, int) and not isinstance(item, bool)}
    return values or None


def _participates(case: Mapping[str, Any], rank: Any) -> bool:
    ranks = _participant_ranks(case)
    if ranks is None or rank is None:
        return True
    return int(rank) in ranks


def _skipped_stage(case: Mapping[str, Any], stage: str) -> dict[str, Any]:
    return {
        "case_id": str(case.get("case_id")),
        "status": "skipped_stage",
        "reason": f"case belongs to {stage}",
        "split": str(case.get("split") or "train"),
    }


def _blocker_prefix(unit_op: Any, repeats: int) -> Any:
    def arm() -> None:
        for _ in range(int(repeats)):
            unit_op()

    return arm


def _calibrate_context_blocker(context: dict[str, Any], *, auto_unit_op: bool = False) -> None:
    if context.get("blocker") is not None or context.get("allow_cpu_smoke"):
        return
    runtime = context.get("runtime")
    if runtime is None or not getattr(runtime, "available", False):
        return
    unit_op = context.get("blocker_unit_op")
    if not callable(unit_op):
        torch = context.get("torch")
        if not auto_unit_op or torch is None:
            return
        if not (callable(getattr(torch, "randn", None)) and (callable(getattr(torch, "mm", None)) or callable(getattr(torch, "matmul", None)))):
            return
        ordinal = int((context.get("device") or {}).get("ordinal") or 0)
        unit_op = make_blocker_unit_op(torch, ordinal)
        context["blocker_unit_op"] = unit_op
    calibrated = calibrate_blocker(runtime, unit_op)
    context["blocker_receipt"] = calibrated.receipt()
    if calibrated.repeats:
        context["blocker"] = _blocker_prefix(unit_op, calibrated.repeats)


def _case_attempted_shape(case: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Assemble attempted geometry from the case/primary node plus builder-recorded shape."""
    shape: dict[str, Any] = {}
    case_shape = case.get("shape")
    if isinstance(case_shape, Mapping):
        shape.update(dict(case_shape))
    else:
        nodes = [n for n in (case.get("nodes") or ()) if isinstance(n, Mapping)]
        include = {str(item) for item in ((case.get("timed_boundary") or {}).get("include") or ())}
        primary = next((n for n in nodes if str(n.get("node_id")) in include), nodes[0] if nodes else None)
        if isinstance(primary, Mapping) and isinstance(primary.get("shape"), Mapping):
            shape.update(dict(primary["shape"]))
    recorded = context.get("_actual_shape") if isinstance(context, Mapping) else None
    if isinstance(recorded, Mapping) and recorded:
        shape.update(dict(recorded))
    return shape


def _skipped_non_participant(case: Mapping[str, Any], rank: Any) -> dict[str, Any]:
    return {
        "case_id": str(case.get("case_id")),
        "status": "skipped_non_participant",
        "reason": f"rank {rank} is not in the declared participant set",
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
        None if observations is None
        else observations if hasattr(observations, "append")
        else ObservationJournal(observations)
    )
    context = (getattr(executor, "context", None) or {}) if executor is not None else {}
    if isinstance(context, dict):
        _calibrate_context_blocker(context, auto_unit_op=True)
    context_rank = context.get("rank")
    identity = run_id or _new_run_id(plan)
    for case in cases:
        if stage == "s0_local" and (
            case.get("stage") == "s1_joint" or case.get("kind") == "fabric"
        ):
            records.append(_skipped_stage(case, "s1_joint"))
            continue
        if stage == "s1_joint" and not _participates(case, context_rank):
            records.append(_skipped_non_participant(case, context_rank))
            continue
        reset = getattr(executor, "reset", None)
        if callable(reset):
            reset()
        if case_over_budget(case, context.get("budget")):
            records.append({
                "case_id": str(case.get("case_id")),
                "status": "over_budget",
                "split": str(case.get("split") or "train"),
            })
            continue
        plan_modes = plan.get("execution_modes") or list(DEFAULT_EXECUTION_MODES)
        if isinstance(context, dict):
            context["_actual_shape"] = {}
        try:
            if stage == "s0_local":
                record = execute_local_case(
                    executor, case, protocol, runtime=runtime, execution_modes=plan_modes,
                )
            else:
                record = execute_joint_case(
                    executor, case, protocol, runtime,
                    execution_modes=plan_modes,
                    blocker=context.get("blocker"),
                    blocker_receipt=context.get("blocker_receipt"),
                )
            if "actual_shape" not in record:
                attempted = _case_attempted_shape(case, context)
                if attempted:
                    record["actual_shape"] = attempted
        except TimeoutError:
            raise
        except Exception as exc:
            attempted = _case_attempted_shape(case, context)
            if isinstance(exc, ProfilerUsageError):
                record = {
                    "case_id": str(case.get("case_id")),
                    "status": "unsupported_binding",
                    "reason": str(exc),
                    "split": str(case.get("split") or "train"),
                }
                if isinstance(exc, BenchUnmodeledOperatorError):
                    record["unmodeled_hint"] = dict(exc.payload)
            else:
                record = {
                    "case_id": str(case.get("case_id")),
                    "status": "failed",
                    "reason": str(exc)[:_REASON_LIMIT],
                    "split": str(case.get("split") or "train"),
                }
            if attempted:
                record["actual_shape"] = attempted
        records.append(record)
        _emit_case_observations(
            journal, plan, case, record, identity, stage, rank=context_rank
        )
    ok = all(
        record["status"] in {"ok", "skipped_stage", "skipped_non_participant"}
        for record in records
    )
    return {
        "schema": RUN_SCHEMA,
        "status": "ok" if ok else "partial",
        "stage": stage,
        "plan_id": plan.get("plan_id"),
        "run_id": identity,
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
    parser.add_argument("--execution-mode", action="append", default=None,
                        choices=EXECUTION_MODES)
    parser.add_argument("--allowed-phy-ids", default=None, help="physical die allowlist")
    parser.add_argument("--l2-mib", type=float, default=None,
                        help="explicit L2 size for the ColdRing (MiB)")
    parser.add_argument("--allow-cpu-smoke", action="store_true",
                        help="permit host-clock smoke runs without device events")
    parser.add_argument("--observations", default=None,
                        help="append observation rows here")
    parser.add_argument("--out", "--output", dest="output", default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _resolve_l2_bytes(args: argparse.Namespace, plan: Mapping[str, Any]) -> int | None:
    if args.l2_mib is not None:
        return int(args.l2_mib * MIB)
    declared = _positive_int(plan.get("l2_bytes"))
    if declared is not None:
        return declared
    hw = plan.get("hardware")
    if isinstance(hw, Mapping):
        declared = _positive_int(hw.get("l2_bytes_per_die")) or _positive_int(hw.get("l2_bytes"))
        if declared is not None:
            return declared
    meta = plan.get("hardware_meta")
    if isinstance(meta, Mapping):
        declared = _positive_int(meta.get("l2_bytes"))
        if declared is not None:
            return declared
    table = _TIMING_CFG.get("sku_l2_bytes")
    if not isinstance(table, Mapping):
        return None
    sku = str(
        plan.get("sku")
        or (hw.get("sku") if isinstance(hw, Mapping) else plan.get("hardware"))
        or ""
    )
    return _positive_int(table.get(sku))


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
        args.execution_mode or list(plan.get("execution_modes") or DEFAULT_EXECUTION_MODES)
    )
    rank, world = _rank_environment(plan)
    if _rank_mismatch(plan, rank, world):
        _emit({
            "schema": RUN_SCHEMA, "status": "rank_mismatch",
            "plan": [plan.get("rank"), plan.get("world_size")],
            "environment": [rank, world],
        }, args.output)
        return _EXIT_ERR
    summary = {
        "schema": RUN_SCHEMA, "status": "dry_run", "plan_id": plan.get("plan_id"),
        "stage": plan["stage"], "execution_modes": plan["execution_modes"],
        "graph_policy": DECODE_GRAPH_POLICY,
        "case_count": len(plan["cases"]),
        "cases": [
            {"case_id": case.get("case_id"), "split": case.get("split", "train"),
             "phase": case.get("phase"), "archetype": case.get("archetype"),
             "execution_modes": resolve_case_execution_modes(case, plan["execution_modes"]),
             "nodes": [str(node.get("node_id")) for node in case["nodes"]]}
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
        _emit({"schema": RUN_SCHEMA, "status": "torch_npu_unavailable",
               "reason": str(exc)[:_REASON_LIMIT]}, args.output)
        return _EXIT_UNAVAIL
    from .timing import admit_context, close_context

    journal = ObservationJournal(args.observations) if args.observations else None
    l2_bytes = _resolve_l2_bytes(args, plan)
    if l2_bytes is None and not args.allow_cpu_smoke:
        l2_bytes = resolve_l2_bytes(
            None, sku=str(plan.get("sku") or ""), torch_npu=torch_npu
        )
    context = admit_context(
        torch=torch, torch_npu=torch_npu,
        allowed_phy_ids=resolve_allowed_phy_ids(args.allowed_phy_ids),
        l2_bytes=l2_bytes,
        allocate=bool(l2_bytes is not None and not args.allow_cpu_smoke),
        allow_cpu_smoke=bool(args.allow_cpu_smoke),
    )
    context.update({"rank": rank, "world_size": world})
    _calibrate_context_blocker(context, auto_unit_op=True)
    try:
        runtime = TorchJointRuntime(
            torch, rank=rank, world_size=world,
            parallel=plan.get("parallel"), cases=plan["cases"],
        )
        runtime.init_process_group()
        context.update({
            "dist": runtime.dist, "groups": runtime.groups,
            "dist_initialized": runtime.initialized,
        })
        executor = OperatorExecutor(torch, context)
        try:
            result = run_plan(
                plan, runtime=runtime, protocol=context["protocol"],
                executor=executor, observations=journal,
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
        print(json.dumps({"output": str(target), "status": payload.get("status")},
                         sort_keys=True))
        return
    sys.stdout.write(text)


__all__ = [
    "COLLECTIVE_OPS", "_adjacency", "_bind_collective", "_cold_ring_capable",
    "_data_upstream", "_detach", "_dist_ready", "_emit_case_observations",
    "_joint_split", "_launch", "_normalized_modes", "_output_snapshot",
    "_run_pre", "_same_outputs", "_upstream", "DEFAULT_OBSERVATION_BOUNDARY",
    "EDGE_KINDS", "EXECUTION_MODES", "EventTimer", "NODE_KINDS", "NODE_SCHEMA",
    "OPERATOR_BUILDERS", "OperatorExecutor", "PLAN_SCHEMA", "RUN_SCHEMA",
    "STAGES", "TorchJointRuntime", "TorchTimingRuntime", "build_operator_enqueue",
    "device_of", "execute_joint_case", "execute_local_case", "is_collective",
    "load_plan", "main", "plan_timed_cut", "resolve_op", "run_plan",
    "split_timed", "topological_order", "torch_dtype", "validate_plan",
]
