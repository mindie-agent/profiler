"""Public diff container parity and rejection boundaries.

[Role]
  Retain nested metadata and occurrence evidence across Python, MCP and CLI.
[Invariants]
  All six wrappers preserve tuple/list parity, raw positions, identities and
  commands. Caller members are read once; rejected inputs publish nothing.
[Timeouts & Locks]
  Callback deadlines retain exact identity; CLI subprocesses have 30 s limits.
[Side-Effect Policy]
  Artifacts and input files are confined to pytest temporary directories.
"""

import copy
import json
import subprocess
import sys
from collections import Counter, UserDict
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch

import pytest

from mindie_profiler.events import ProfilerUsageError
from mindie_sim import diff_trace as diff
from mindie_sim import diff_trace_replay as engine
from mindie_sim import diff_trace_release as release


WRAPPERS = ("ops", "kernels", "occurrences", "operator_rows", "operators", "rows")
ROUTES = ("api", "engine", "mcp", "cli")


class ReadOnly(Mapping):
    def __init__(self, data):
        self.data, self.reads, self.iterations = data, Counter(), 0

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        self.iterations += 1
        return iter(self.data)

    def __getitem__(self, key):
        self.reads[key] += 1
        return self.data[key]


class CountedList(list):
    def __iter__(self):
        self.iterations = getattr(self, "iterations", 0) + 1
        for item in super().__iter__():
            self.reads = getattr(self, "reads", 0) + 1
            yield item


class CountedTuple(tuple):
    __iter__ = CountedList.__iter__

    def __iter__(self):
        self.iterations = getattr(self, "iterations", 0) + 1
        for item in tuple.__iter__(self):
            self.reads = getattr(self, "reads", 0) + 1
            yield item


def freeze(value, carrier, sequence, tracked=None):
    if isinstance(value, dict):
        result = carrier({key: freeze(item, carrier, sequence, tracked)
                          for key, item in value.items()})
    elif isinstance(value, (list, tuple)):
        result = sequence(freeze(item, carrier, sequence, tracked) for item in value)
    else:
        return value
    if tracked is not None:
        tracked.append(result)
    return result


def plain(value):
    if isinstance(value, ReadOnly):
        return plain(value.data)
    if isinstance(value, Mapping):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        iterator = list.__iter__(value) if isinstance(value, list) else tuple.__iter__(value)
        return [plain(item) for item in iterator]
    return value


def packets(wrapper="ops", run_key="run_id"):
    predicted = {"total_ms": 1, wrapper: [None, {"placeholder": True},
                 {"name": "Matmul", "start_ms": 0, "duration_ms": 1,
                  "metadata": {"evidence": [{"source": "predicted"}]}}]}
    captured = copy.deepcopy(predicted)
    captured.update(total_ms=2, cann_release="8.0")
    captured[run_key] = "container-run"
    captured[wrapper][2]["duration_ms"] = 2
    captured["alignment"] = {"coverage_complete": True, "evidence": {
        "source": "capture", "raw_indices": [2], "metadata": [{"tag": "kept"}]}}
    return predicted, captured


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")


def invoke(route, predicted, captured):
    if route == "api":
        return diff.attribute_diff(predicted, captured)
    if route == "engine":
        return engine.attribute_diff(predicted, captured)
    if route == "mcp":
        envelope = diff.call_mcp_tool(ReadOnly({"predicted": predicted, "captured": captured}))
        if envelope["status"] == "invalid_request":
            return envelope
        assert envelope["retrievable"] and envelope["persisted"]
        assert diff.resolve_diff_artifact(envelope["artifact_id"])["resolved"]
        return json.loads(Path(envelope["artifact_path"]).read_text())
    with patch.object(diff, "load_cli_json", side_effect=[predicted, captured]):
        rc = diff.main(["--predicted", "p.json", "--captured", "c.json",
                        "--output", "caller.json"])
    assert rc == 0
    return json.loads(Path("caller.json").read_text())


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("carrier", (dict, UserDict, MappingProxyType, ReadOnly))
@pytest.mark.parametrize("sequence", (list, tuple))
@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("run_key", ("run_id", "capture_id"))
def test_diff_nested_metadata_and_row_parity(wrapper, carrier, sequence, route, run_key):
    predicted, captured = packets(wrapper, run_key)
    expected = diff.attribute_diff(predicted, captured)
    pp, cc = freeze(predicted, carrier, sequence), freeze(captured, carrier, sequence)
    result = invoke(route, pp, cc)
    assert json.loads(json.dumps(result)) == expected
    assert plain(pp) == predicted and plain(cc) == captured
    assert result["status"] == "reconciled"
    assert result["coverage"]["matched_ops"] == 1
    offender, = result["kernel_roofline_and_clock"]["top_offenders"]
    assert offender["raw_op_index"] == 2
    assert offender["selector"]["run_id"] == "container-run"
    assert "--occurrence-index 2" in offender["repro_command"]
    assert "--version 8.0" in offender["repro_command"]


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("sequence", (list, tuple))
def test_diff_real_file_cli(wrapper, sequence, capsys):
    predicted, captured = packets(wrapper)
    predicted[wrapper], captured[wrapper] = sequence(predicted[wrapper]), sequence(captured[wrapper])
    Path("p.json").write_text(json.dumps(predicted))
    Path("c.json").write_text(json.dumps(captured))
    if wrapper == "ops" and sequence is list:
        run = subprocess.run([sys.executable, "-B", "-m", "mindie_sim", "diff-trace",
                              "--predicted", "p.json", "--captured", "c.json"],
                             capture_output=True, text=True, timeout=30)
        rc, stdout, stderr = run.returncode, run.stdout, run.stderr
    else:
        rc = diff.main(["--predicted", "p.json", "--captured", "c.json"])
        io = capsys.readouterr()
        stdout, stderr = io.out, io.err
    assert rc == 0 and not stderr
    assert json.loads(stdout) == diff.attribute_diff(predicted, captured)


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("sequence", (CountedList, CountedTuple))
@pytest.mark.parametrize("shared", (False, True))
def test_diff_single_pass_including_shared_subtrees(route, sequence, shared):
    predicted, captured = packets()
    tracked = []
    pp = freeze(predicted, ReadOnly, sequence, tracked)
    cc = pp if shared else freeze(captured, ReadOnly, sequence, tracked)
    before = plain([pp, cc])
    invoke(route, pp, cc)
    assert plain([pp, cc]) == before
    for item in tracked:
        assert item.iterations == 1
        if isinstance(item, ReadOnly):
            assert item.reads == Counter({key: 1 for key in item.data})
        else:
            assert item.reads == len(item)


class WideMapping(ReadOnly):
    def __len__(self):
        return 1_000_001


class WideList(CountedList):
    def __len__(self):
        return 1_000_001


class WideTuple(CountedTuple):
    def __len__(self):
        return 1_000_001


def invalid_case(kind):
    if kind == "mapping":
        return WideMapping({"metadata": 1})
    if kind in ("list", "tuple"):
        return (WideList if kind == "list" else WideTuple)([1])
    if kind == "key":
        class Key(str):
            def __hash__(self):
                raise AssertionError("invalid key was hashed")

        class Keys(ReadOnly):
            def __iter__(self):
                yield Key("metadata")

        return Keys({"metadata": 1})
    if kind == "cycle":
        value = []
        value.append(value)
        return value
    if kind == "depth":
        value = 0
        for _ in range(65):
            value = [value]
        return value
    if kind == "dag":
        value = [0] * 1000
        return [[value] * 1000] * 1000
    return {"huge": 10**5000, "nan": float("nan"), "object": object(),
            "set": {1}}[kind]


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("kind", ("mapping", "list", "tuple", "key", "cycle",
                                   "depth", "dag", "huge", "nan", "object", "set"))
def test_diff_rejection_precedes_publication(route, kind, tmp_path):
    predicted, captured = packets()
    bad = invalid_case(kind)
    captured["alignment"]["evidence"] = bad
    Path("caller.json").write_text("existing caller bytes\n")
    if route == "mcp":
        result = invoke(route, predicted, captured)
        assert result["status"] == "invalid_request" and not result["persisted"]
    elif route == "cli":
        with pytest.raises(SystemExit) as error:
            invoke(route, predicted, captured)
        assert error.value.code == 2
    else:
        with pytest.raises(ProfilerUsageError):
            invoke(route, predicted, captured)
    assert [path.name for path in tmp_path.iterdir()] == ["caller.json"]
    assert Path("caller.json").read_text() == "existing caller bytes\n"
    if kind in ("mapping", "key"):
        assert not bad.reads
    if kind in ("mapping", "list", "tuple"):
        assert not getattr(bad, "iterations", 0)


class Deadline(TimeoutError):
    pass


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("boundary", ("length", "iterate", "lookup", "sequence"))
@pytest.mark.parametrize("error_type", (TimeoutError, Deadline))
def test_diff_exact_callback_timeout(route, boundary, error_type, tmp_path):
    sentinel, hits = error_type("container deadline"), []

    class Fault(ReadOnly):
        def __len__(self):
            if boundary == "length":
                hits.append(boundary)
                raise sentinel
            return super().__len__()

        def __iter__(self):
            if boundary == "iterate":
                hits.append(boundary)
                raise sentinel
            return super().__iter__()

        def __getitem__(self, key):
            if boundary == "lookup":
                hits.append(boundary)
                raise sentinel
            return super().__getitem__(key)

    class FaultSequence(list):
        def __iter__(self):
            hits.append(boundary)
            raise sentinel

    predicted, captured = packets()
    captured["alignment"] = (FaultSequence([1]) if boundary == "sequence"
                             else Fault({"evidence": {"source": "capture"}}))
    with pytest.raises(TimeoutError) as error:
        invoke(route, predicted, captured)
    assert error.value is sentinel and hits == [boundary]
    assert not list(tmp_path.iterdir())


HELPERS = (
    (engine.normalize_ops, {"packet": packets()[1]}),
    (engine.op_name, {"op": {"name": "A"}}),
    (engine.duration, {"op": {"duration_ms": 2}}),
    (engine.start, {"op": {"start_ms": 1}}),
    (engine.is_collective, {"op": {"kind": "collective"}}),
    (engine.is_host, {"op": {"kind": "host"}}),
    (engine.is_fallback, {"op": {"fallback": True}}),
    (release.normalize_gaps, {"packet": {"gaps": [{"duration_ms": 1}]}}),
    (release.window_of, {"packet": packets()[1], "ops": []}),
    (release.captured_total_explicit, {"packet": packets()[1]}),
    (release.terminal_gap_evidence, {"packet": {"gaps": [{"start_ms": 1,
        "duration_ms": 1}]}, "window": [0, 2], "op_end": 1}),
    (release.launch_cost, {"packet": {"launch_count": 1}, "launch_overhead_us": 0}),
    (release.release_delays, {"captured": [{"start": 1, "duration": 1, "stream": 0}],
        "gaps": [], "origin": 0, "deps": [[]]}),
    (release.tail_gap, {"gaps": [{"start": 1, "duration": 1}],
        "window": [0, 2], "op_end": 1}),
    (release.gap_evidence, {"gaps": [{"start": 1, "duration": 1}], "window": [0, 2],
        "replay_starts": [0], "durations": [1], "exclude_ends": [0]}),
    (release.op_uid, {"run_id": "run", "op": {"rank": 0, "step": 0,
        "stream": 0, "raw_op_index": 2, "abi_digest": "abi"}}),
    (release.union, {"intervals": [[0, 1], [1, 2]], "window": [0, 2]}),
    (release.total, {"intervals": [[0, 1]]}),
    (release.complement, {"busy": [[0, 1]], "window": [0, 2]}),
    (release.intersect, {"left": [[0, 1]], "right": [[0, 2]]}),
    (engine.replay, {"ops": [{"key": "a", "stream": 0, "start": 0}],
        "durations": [1], "window": [0, 1]}),
    (engine.match_key, {"op": {"step": 0, "rank": 0, "stream": 0,
        "key": "a", "stream_occurrence_index": 0}}),
    (diff.effective_operator_rows, {"op_name": "aclnnSwiGlu", "bucket_tokens": 2,
        "logical_tokens": 1, "bound_args": {"metadata": {"evidence": [1]}}}),
    (diff.pad_aware_operator_cost, {"op_name": "aclnnSwiGlu", "duration_ms": 1,
        "bucket_tokens": 2, "logical_tokens": 1, "bound_args": {"metadata": [1]}}),
)


@pytest.mark.parametrize("function,arguments", HELPERS, ids=[f.__name__ for f, _ in HELPERS])
def test_direct_diff_helpers_snapshot_once(function, arguments):
    expected = function(**arguments)
    tracked = []
    wrapped = {key: freeze(value, ReadOnly, CountedTuple, tracked)
               for key, value in arguments.items()}
    result = function(**wrapped)
    assert json.loads(json.dumps(result)) == json.loads(json.dumps(expected))
    for value in tracked:
        assert value.iterations == 1
        if isinstance(value, ReadOnly):
            assert value.reads == Counter({key: 1 for key in value.data})
        else:
            assert getattr(value, "reads", 0) == len(value)
