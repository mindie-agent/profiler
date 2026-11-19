"""HCCL joint-subgraph runtime and observation emission helpers.

[Role]
  Own ``TorchJointRuntime`` (HCCL axis-group construction and ``NPUGraph``
  capture/replay) and ``_emit_case_observations`` for ``bench subgraph``,
  keeping ``bench_archetype_subgraphs`` concise and strictly under 800 lines.

[Invariants]
  * Axis groups are created in deterministic sorted order (``ep``, ``mc2``,
    ``sp``, ``tp``) with an explicit finite timeout.
  * Observations are emitted only for ``ok`` or ``unqualified`` cases and
    preserve frozen ``train``/``heldout`` splits and plan identities.

[Timeouts & Locks]
  Process-group initialization uses ``timeout_s``; no host locks.

[Side-Effect Policy]
  Creates/destroys one HCCL process group when ``world_size > 1`` and appends
  JSONL rows to the caller-supplied ``ObservationJournal``.
"""

from __future__ import annotations

import importlib
from typing import Any, Callable, Iterable, Mapping

from .observations import case_complete_row, observation_row
from .profiles import profile_section

_CFG = profile_section("subgraph")
DEFAULT_OBSERVATION_BOUNDARY = "device_kernel"
_PG_TIMEOUT_S = float(_CFG["process_group_timeout_s"])


class TorchJointRuntime:
    """HCCL group construction plus ACLGraph capture/replay adapter."""

    def __init__(
        self,
        torch: Any,
        *,
        rank: int = 0,
        world_size: int = 1,
        parallel: Mapping[str, Any] | None = None,
        timeout_s: float = _PG_TIMEOUT_S,
    ) -> None:
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

            self.dist.init_process_group(
                "hccl",
                rank=self.rank,
                world_size=self.world_size,
                timeout=timedelta(seconds=self.timeout_s),
            )
            self.initialized = True
        for axis in sorted(("tp", "ep", "sp", "mc2")):
            declared = self.parallel.get(axis)
            if isinstance(declared, bool):
                if not declared:
                    continue
                size = max(
                    int(self.parallel.get("tp") or 1), int(self.parallel.get("ep") or 1)
                )
            else:
                size = int(declared or 1)
            if size <= 1:
                continue
            self.groups[axis] = self.dist.new_group(
                list(range(min(size, self.world_size)))
            )
        return {
            "world_size": self.world_size,
            "rank": self.rank,
            "groups": sorted(self.groups),
            "initialized": self.initialized,
        }

    def close(self) -> None:
        if self.initialized and self.dist is not None:
            self.dist.destroy_process_group()
            self.initialized = False

    def synchronize(self) -> None:
        sync = getattr(self.torch.npu, "synchronize", None)
        if callable(sync):
            sync()

    def capture(
        self, call: Callable[[], Any], case_id: str
    ) -> tuple[Any, dict[str, Any]]:
        factory = getattr(self.torch.npu, "NPUGraph", None)
        if not callable(factory):
            return None, {
                "status": "unsupported_binding",
                "reason": "torch.npu.NPUGraph unavailable",
            }
        graph = factory()
        graph_ctx = getattr(self.torch.npu, "graph", None)
        if not callable(graph_ctx):
            return None, {
                "status": "unsupported_binding",
                "reason": "torch.npu.graph unavailable",
            }
        with graph_ctx(graph):
            outputs = call()
        return (graph, outputs), {"status": "captured", "case_id": case_id, "mode": "aclgraph"}

    def replay(self, captured: Any) -> Any:
        if not isinstance(captured, tuple) or len(captured) != 2:
            return None
        graph, outputs = captured
        replay = getattr(graph, "replay", None)
        if callable(replay):
            replay()
        return outputs


def _timing_rows(timing: Mapping[str, Any]) -> Iterable[tuple[str, int, int, float]]:
    modes = timing.get("modes") if isinstance(timing.get("modes"), Mapping) else {}
    for mode, summary in modes.items():
        for trial in (summary or {}).get("trials") or ():
            for idx, val in enumerate(trial.get("repeats_us") or ()):
                yield str(mode), int(trial.get("trial") or 0), idx, float(val)


def _emit_case_observations(
    journal: Any,
    plan: Mapping[str, Any],
    case: Mapping[str, Any],
    record: Mapping[str, Any],
    run_id: str,
    stage: str,
) -> None:
    if journal is None or record.get("status") not in {"ok", "unqualified"}:
        return
    timing = record.get("timing") or record.get("eager") or {}
    if not isinstance(timing, Mapping):
        return
    split = str(case.get("split") or "train")
    boundary = str(case.get("boundary") or DEFAULT_OBSERVATION_BOUNDARY)
    identities = (
        case.get("identities") if isinstance(case.get("identities"), Mapping) else {}
    )
    service = identities.get("service")
    facets = ("work", "resource", "work_unit", "active_units")
    capabilities = (
        {key: service.get(key) for key in facets}
        if isinstance(service, Mapping)
        else (
            {
                "work": timing.get("minimum_ms"),
                "resource": case.get("resource"),
                "work_unit": case.get("work_unit"),
                "active_units": case.get("active_units"),
            }
            if case.get("work_unit")
            else {}
        )
    )
    for mode, trial, repeat_index, repeat_us in _timing_rows(timing):
        duration_ms = repeat_us / 1000.0
        row = observation_row(
            plan_id=plan.get("plan_id"),
            case=case,
            run_id=f"{run_id}.{mode}.t{trial}",
            split=split,
            boundary=boundary,
            timing_mode=mode,
            residency=str(case.get("residency") or "device"),
            trial=trial,
            repeat_index=repeat_index,
            rank=case.get("rank"),
            duration_ms=duration_ms,
            source=f"capture://bench-subgraph/{case.get('case_id')}/{mode}.{trial}.{repeat_index}",
            validated=bool(record.get("validated", True)),
            qualified=bool(record.get("qualified", True)),
            level=str(case.get("level") or "subgraph"),
            phase=case.get("phase"),
            execution={"mode": mode, "stage": stage},
            work_bytes=case.get("work_bytes"),
            key=identities.get("primitive_key"),
            identity_override=identities.get("accuracy_identity"),
            service_identity=(
                service.get("identity") if isinstance(service, Mapping) else None
            ),
            **capabilities,
        )
        journal.append(row)
    journal.append(
        case_complete_row(
            plan_id=plan.get("plan_id"),
            case_id=case.get("case_id"),
            run_id=run_id,
            status=str(record.get("status")),
            split=split,
            summary={"stage": stage, "timed_nodes": record.get("timed_nodes")},
        )
    )


__all__ = [
    "DEFAULT_OBSERVATION_BOUNDARY",
    "TorchJointRuntime",
    "_emit_case_observations",
    "_timing_rows",
]
