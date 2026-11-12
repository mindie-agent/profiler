"""Shared native owner-program schedule survives the concurrent Engine."""
import json
import os
from dataclasses import replace
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
PROFILER = HERE.parent
SIM = PROFILER.parent / "sim"
CELLS = Path(os.environ.get(
    "MINDIE_TEST_ORIGINAL_CELLS",
    "/private/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl"))


def _z():
    if str(PROFILER / "examples" / "structure") not in sys.path:
        sys.path.insert(0, str(PROFILER / "examples" / "structure"))
    os.environ.setdefault("MINDIE_PROFILER_SOURCE", str(PROFILER))
    os.environ.setdefault("MINDIE_SIM_SOURCE", str(SIM))
    os.environ.setdefault("MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT",
                          "/private/tmp/mindie-7337-20261111-1457/header-provenance")
    import zero_shot_piecewise_validation as z
    return z


def _conv():
    from mindie_sim.prediction.piecewise import composition as cc
    from mindie_sim.prediction.piecewise.compiler import CompiledOperator
    z = _z()
    cell = None
    for line in CELLS.open("rb"):
        raw = json.loads(line)
        if raw.get("cell_id") == "qwen38_27b_dp4tp2_prefill_1024_c2":
            cell = z.cell_from_dict(raw).spec
            break
    if cell is None:
        pytest.skip("Qwen38 original cell unavailable")
    z.predict_cell(cell)
    compiled = z._COMPILED_MODELS[cell.dataset, z._structure_fingerprint(cell)]
    geometry, state = z._geometry(cell, cell.phase), compiled[5]
    supply = compiled[2]
    sub, op = next((sub, op) for sub in compiled[3].values()
                   for op in sub.operators if op.name == "conv")
    cost = op.evaluate(geometry, state)

    def rescore(new_supply):
        ctx = CompiledOperator(
            op.operator, new_supply, op.policy, kind=op.kind, layer=op.layer,
            domain=op.domain, siblings=op.siblings, variant=op.variant,
            feature_metadata=getattr(op, "feature_metadata", ()))
        return ctx.evaluate(geometry, state), cc.operator_segment(
            ctx.evaluate(geometry, state), new_supply)

    return cost, supply, cc.operator_segment(cost, supply), rescore, cc


@pytest.mark.skipif(not CELLS.is_file(), reason="original cells unavailable")
def test_native_conv_real_program_solo_duration_and_register_work():
    cost, supply, segment, _rescore, cc = _conv()
    assert cost.native_program is not None
    assert cost.native_schedule is None
    assert cost.native_program.fidelity == "native_program"
    assert cost.native_program.duration == cost.duration_ms
    assert segment.native_program is cost.native_program
    assert segment.native_stages == ()
    exported = dict(cost.stage_work[0])
    work = dict(cost.work)
    for register in ("reg_issue_slots", "reg_data_writes", "reg_ub_accesses",
                     "reg_alu_lanes", "reg_ub_stores"):
        assert exported[register] == work[register] > 0
    one = cc.run_engine_work({}, supply, chains={"conv": [segment]})
    assert float(one.makespan_ms) == pytest.approx(
        float(cost.duration_ms), rel=0, abs=1e-12)
    assert dict(one.summary).get("completed_tasks", 0) >= 7500
    envelope = cc.contention_envelope({}, supply, chains={"conv": [segment]})
    assert float(envelope.makespan_ms) == pytest.approx(
        float(cost.duration_ms), rel=0, abs=1e-12)
    assert float(envelope.isolated_max_ms) == pytest.approx(
        float(cost.duration_ms), rel=0, abs=1e-12)
    assert envelope.lower_bound_ms <= envelope.makespan_ms
    shared = cc.contention_envelope({}, supply, chains={
        "left": [segment], "right": [segment]})
    assert "vector" in shared.shared_pipes and "hbm" in shared.shared_pipes
    assert shared.lower_bound_ms <= shared.makespan_ms


@pytest.mark.skipif(not CELLS.is_file(), reason="original cells unavailable")
def test_native_conv_resource_sensitivity_and_per_core_scaling():
    cost, supply, segment, rescore, cc = _conv()
    one = cc.run_engine_work({}, supply, chains={"conv": [segment]})
    rates = dict(supply.rates)
    slower = replace(supply, rates=tuple(
        (name, value * 0.25 if name == "reg_data_writes" else value)
        for name, value in supply.rates))
    reg_cost, reg_seg = rescore(slower)
    reg_one = cc.run_engine_work({}, slower, chains={"conv": [reg_seg]})
    assert float(reg_one.makespan_ms) == pytest.approx(
        float(reg_cost.duration_ms), rel=0, abs=1e-9)
    assert reg_one.makespan_ms > one.makespan_ms

    units = dict(supply.resource_units)
    assert units.get("vector", 1) > 1
    half = replace(supply, resource_units=tuple(
        (name, max(1, value // 2) if name == "vector" else value)
        for name, value in supply.resource_units))
    core_cost, core_seg = rescore(half)
    core_one = cc.run_engine_work({}, half, chains={"conv": [core_seg]})
    assert float(core_one.makespan_ms) == pytest.approx(
        float(core_cost.duration_ms), rel=0, abs=1e-9)
    assert core_one.makespan_ms != one.makespan_ms
    assert abs(float(core_one.makespan_ms) - float(one.makespan_ms)) > 1e-6


@pytest.mark.skipif(not CELLS.is_file(), reason="original cells unavailable")
def test_typed_two_branch_join_dependencies_contention_and_no_overlap():
    from mindie_sim.prediction.engine import Engine, Resource
    from mindie_sim.prediction.piecewise.composition import (
        NativeTask, OperatorSegment,
    )
    cost, supply, segment, _rescore, cc = _conv()
    single = cc.run_engine_work({}, supply, chains={"left": [segment]})
    both = cc.run_engine_work({}, supply, chains={
        "left": [segment], "right": [segment]})
    disabled = cc.run_engine_work({}, supply, chains={
        "left": [segment], "right": []})
    serial = cc.run_engine_work({}, supply, chains={
        "left": [segment, segment]})
    units = dict(supply.resource_units)
    control = Engine(
        [Resource(name, float(value), "work", "fair",
                  int(units.get(name, 1))) for name, value in supply.rates],
        pools=dict(supply.buffers), pool_units=dict(supply.pool_units))
    ready = control.submit("ready", release=0)
    left = cost.native_program.start(control, "native:left", ready)
    right = cost.native_program.start(control, "native:right", ready)
    control.advance(until=(left, right), first=False)
    control_two = max(left.time, right.time)
    assert float(both.makespan_ms) == pytest.approx(
        control_two, rel=1e-12, abs=1e-9)
    assert max(float(v) for _k, v in both.branches) == pytest.approx(
        control_two, rel=1e-12, abs=1e-9)
    assert disabled.makespan_ms == single.makespan_ms
    assert dict(disabled.branches)["right"] == 0
    assert serial.makespan_ms == pytest.approx(
        2 * float(cost.duration_ms), rel=1e-12, abs=1e-9)

    limited = replace(supply, rates=tuple(
        (name, 50_000_000.0 if name == "vector" else value)
        for name, value in supply.rates))
    limited_one = cc.run_engine_work(
        {}, limited, chains={"left": [segment]})
    limited_both = cc.run_engine_work(
        {}, limited, chains={"left": [segment], "right": [segment]})
    assert limited_both.makespan_ms > limited_one.makespan_ms

    hbm = OperatorSegment(stages=(), native_stages=(
        (NativeTask("hbm", 1_000_000_000),),))
    mte3 = OperatorSegment(stages=(), native_stages=(
        (NativeTask("mte3", 1_000_000_000),),))
    overlap = cc.run_engine_work(
        {}, supply, chains={"hbm": [hbm], "mte3": [mte3]})
    only_hbm = cc.run_engine_work({}, supply, chains={"hbm": [hbm]})
    only_mte3 = cc.run_engine_work({}, supply, chains={"mte3": [mte3]})
    assert overlap.makespan_ms == pytest.approx(
        max(only_hbm.makespan_ms, only_mte3.makespan_ms), rel=1e-12)
