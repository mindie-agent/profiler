"""CAModel export arithmetic and CLI contracts; no hardware accuracy claims.

Instruction fields follow PyPTO's clean_sim_trace.py at 9f3ca53526bc31ccf7b7ec42064f4449f9db1acf.
Synthetic interval cases below are independent arithmetic oracles, not captures.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from mindie_profiler.camodel import summarize_camodel
from mindie_profiler.events import ProfilerQueryError, ProfilerUsageError


def _plan():
    return {
        "timestamp_unit": "us",
        "context": {"soc_version": "Ascend910_9362", "simulator_version": "test-oracle", "kernel": "example"},
        "stages": {"load": {"pid": "group0.cubecore0", "tids": ["MTE2", "MTE2#1"], "windows": [[0, 8], [10, 20]]}},
    }


def _event(start, duration, **fields):
    return {"name": "LOAD_A", "ph": "X", "pid": "group0.cubecore0", "tid": "MTE2", "ts": start, "dur": duration, **fields}


def test_overlapping_sublanes_sync_and_other_core_do_not_inflate_service():
    # Unsorted [0,1] U [.5,1.5] = 1.5us, second invocation 2us;
    # median per invocation = 1.75us, not the sum of overlapping instructions.
    events = [_event(.5, 1, tid="MTE2#1"), _event(0, 1), _event(10, 2),
              _event(0, 90, pid="group0.cubecore1"), _event(1.5, 5, name="WAIT_FLAG"),
              _event(0, 8, name="SET_FLAG", ph="B"), _event(0, 0, ph="M")]
    result = summarize_camodel(events, _plan(), source="oracle")
    assert result["durations_ns"]["load"] == 1750
    assert result["evidence"]["stages"]["load"]["samples"][0] == {
        "active_ns": 1500, "summed_instruction_ns": 2000, "span_ns": 1500, "instruction_count": 2,
    }
    assert result["evidence"]["selected_intervals"] == 3
    assert result["evidence"]["source_class"] == "simulated"


def test_cycles_and_large_absolute_timestamps_preserve_fractional_service():
    plan = _plan()
    plan.update(timestamp_unit="cycles", clock_mhz=1250)
    plan["stages"]["load"]["windows"] = [[10**16, 10**16 + 10]]
    result = summarize_camodel([_event(10**16, 1.5)], plan, source="oracle")
    assert result["durations_ns"]["load"] == pytest.approx(1.2)


def test_cut_empty_or_double_assigned_invocations_are_not_exported():
    plan = _plan()
    with pytest.raises(ProfilerUsageError, match="cuts instruction"):
        summarize_camodel([_event(7, 2)], plan, source="oracle")
    with pytest.raises(ProfilerUsageError, match="invocation 1 has no"):
        summarize_camodel([_event(0, 1)], plan, source="oracle")
    plan["stages"]["other"] = copy.deepcopy(plan["stages"]["load"])
    with pytest.raises(ProfilerUsageError, match="assigned to both"):
        summarize_camodel([_event(0, 1)], plan, source="oracle")


def test_interval_budget_is_an_error_instead_of_truncated_cost():
    with pytest.raises(ProfilerQueryError, match="exceed cap"):
        summarize_camodel([_event(0, 1), _event(10, 1)], _plan(), source="oracle", max_intervals=1)


def test_cli_streams_export_and_preserves_output_when_trace_is_malformed(tmp_path, capsys):
    from mindie_profiler.__main__ import main

    examples = Path(__file__).resolve().parents[1] / "examples" / "camodel"
    trace = tmp_path / "trace.json"
    trace.write_text((examples / "trace.example.json").read_text(), encoding="utf-8")
    output = tmp_path / "durations.json"
    args = ["camodel", "--trace", str(trace), "--plan", str(examples / "plan.example.json"), "--output", str(output)]
    assert main(args) == 0
    artifact = json.loads(output.read_text())
    # displayTimeUnit=ns must not override the declared raw us timestamp unit.
    assert artifact["durations_ns"] == {"load": 1750, "compute": 5000}
    before = output.read_bytes()
    trace.write_text(trace.read_text().rstrip()[:-1] + ",broken", encoding="utf-8")
    assert main(args) == 2
    assert output.read_bytes() == before
    assert "invalid JSON trace" in capsys.readouterr().err
