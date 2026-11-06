"""Retained Kimi HCCL responses bind only their declared source transport.

[Role] Execute retained TP8/TP16 native collective groups and identity controls.
[Invariants] Existing response knots stay inclusive; changed links or parallel
  decomposition must execute their analytic source DAG without that response.
[Timeouts & Locks] Four-layer graph construction, one collective per CPU run.
[Side-Effect Policy] Read-only retained cases; no capture reads or remote work.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from mindie_sim import graph_costs, target_operators
from mindie_sim.prediction.structure import parse_case


CASES = Path(__file__).resolve().parents[1] / "examples" / "structure" / "cases"


def _case(tp):
    return json.loads((CASES / f"a3-kimi4-tp{tp}-longctx-source.json").read_text())


def _collective(raw, collective):
    ops = target_operators(raw, phase="decode", tokens=1, context=126000, sequences=1)
    entry = next(op for op in ops if op.recipe == "hccl_entry"
                 and dict(op.metadata)["hccl_selection"]["collective"] == collective)
    group = dict(entry.metadata)["hccl_source_group"]
    return tuple(op for op in ops if dict(op.metadata).get("hccl_source_group") == group)


def _execute(raw, ops):
    members = {op.op_id for op in ops}
    inputs = {dep: 7 for op in ops for dep in op.deps if dep not in members}
    return graph_costs(raw, ops, external_inputs=inputs, input_ready_ms=7,
                       replay_scope="full", isolated=False, trace_limit=10000)


@pytest.mark.parametrize("tp", (8, 16))
@pytest.mark.parametrize("collective", ("allgather", "reduce_scatter"))
def test_retained_collective_response_executes_once_at_the_native_boundary(tp, collective):
    raw = _case(tp)
    rule = next(row for row in raw["runtime"]["kernels"]["service_regimes"]
                if row["id"] == f"kimi-a3-tp{tp}-hccl-{collective}")
    report = _execute(raw, _collective(raw, collective))
    selected, = report["parameters"]["service_regimes"]
    assert selected["id"] == rule["id"]
    assert selected["queries"] == {"observable_response": 1}
    assert report["duration_ms"] == pytest.approx(rule["response"]["knots"][0][1] / 1000)
    assert sum(row["task"].endswith(":minimum") for row in report["events"]) == 1
    assert all(row["start_ms"] >= 7 for row in report["events"] if row["demand"])
    assert report["execution"]["live_tasks"] == report["execution"]["live_programs"] == 0


@pytest.mark.parametrize("tp", (8, 16))
@pytest.mark.parametrize("changed_axis", ("link", "parallel"))
def test_changed_transport_keeps_strict_matching_and_the_analytic_source_program(tp, changed_axis):
    changed = _case(tp)
    if changed_axis == "link":
        changed["machine"]["links"] = [link.to_dict() for link in parse_case(changed).machine.links]
        changed["machine"]["links"][0]["capacity_bytes_per_ms"] *= 2
    else:
        changed["runtime"].update(tp=tp // 2, ep=tp // 2)
    ops = _collective(changed, "allgather")
    unmatched = _execute(changed, ops)
    control = deepcopy(changed)
    control["runtime"]["kernels"].pop("service_regimes")
    analytic = _execute(control, ops)
    selected, = unmatched["parameters"]["service_regimes"]
    assert selected["queries"] == {"physical_identity_mismatch": 1}
    assert selected["mismatched_axes"] == {"transport": 1}
    assert unmatched["duration_ms"] == analytic["duration_ms"]
    assert unmatched["events"] == analytic["events"]
    assert unmatched["execution"] == analytic["execution"]
