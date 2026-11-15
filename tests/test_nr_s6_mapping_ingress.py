"""Mapping key work budgets and read-only reproducer request carriers.

[Role]
  Exercise dictionary-backed mappings through traversal, diagnostics and ingress.
[Invariants]
  Over-budget keys are rejected before hashing or publication. Valid requests
  preserve caller data, generate standalone scripts and resolve bounded receipts.
[Timeouts & Locks]
  Callback deadlines propagate by identity; script help has a 30-second deadline.
[Side-Effect Policy]
  Writes only pytest temporary artifacts; no device work or interpreter changes.
"""

import copy
import hashlib
import json
import subprocess
import sys
from collections import UserDict
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import pytest
try:
    import tiktoken
except ImportError:
    tiktoken = None

from mindie_profiler import op_api_registry as registry, repro_op as op
from mindie_profiler import repro_values as values
from mindie_profiler.__main__ import main as cli
from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.token_budget import estimate_tokens
from nr_s6_support import KeyMapping, key_timeout_callback, paged_binding
from test_nr_s6_round25 import _raw


class ReadOnly(Mapping):
    def __init__(self, data):
        self.data = data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]


def _wrap(data, carrier):
    if carrier == "dict":
        return data
    if carrier == "custom":
        return ReadOnly(data)
    if carrier == "proxy":
        return MappingProxyType(data)
    view = UserDict()
    view.data = data
    return MappingProxyType(view) if carrier == "proxy_userdict" else view


@pytest.fixture(scope="module")
def counted_key():
    calls = [0]

    class Leaf(int):
        def __hash__(self):
            calls[0] += 1
            return int.__hash__(self)

    key = Leaf(7)
    for _ in range(3):
        key = (key,) * 101
    data = {key: None}
    assert calls[0] == 101 ** 3
    return data, calls


def _bounded(envelope):
    wire = json.dumps(envelope, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)
    body = json.dumps({k: v for k, v in envelope.items() if k != "receipt"},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert estimate_tokens(envelope) <= 250
    if tiktoken is not None:
        for name in ("cl100k_base", "o200k_base"):
            try:
                encoder = tiktoken.get_encoding(name)
            except TimeoutError:
                raise
            except Exception:
                break
            assert len(encoder.encode(wire, disallowed_special=())) <= estimate_tokens(envelope) <= 250
            assert len(encoder.encode(body, disallowed_special=())) <= envelope["receipt"]["token_estimate"]
    assert envelope["receipt"]["within_budget"]


def _load_help(path):
    source = path.read_bytes()
    namespace = {"__name__": "standalone_mapping_control"}
    exec(compile(source, str(path), "exec"), namespace)
    run = subprocess.run([sys.executable, "-B", str(path), "--help"],
                         capture_output=True, text=True, timeout=30)
    assert run.returncode == 0 and "usage:" in run.stdout and not run.stderr
    return namespace


@pytest.mark.parametrize("carrier", ["dict", "userdict", "proxy_userdict", "custom"])
@pytest.mark.parametrize("route", ["validate_container_depth", "validate_json_integers",
                                  "bounded_summary", "diagnostic_value",
                                  "bounded_mapping", "literal_value"])
def test_mapping_key_budget_before_lookup(carrier, route, counted_key):
    data, calls = counted_key
    view = _wrap(data, carrier)
    calls[0] = 0
    fn = getattr(values, route)
    if route in ("bounded_summary", "diagnostic_value"):
        result = fn(view)
        if carrier != "dict":
            limit = "size" if route == "bounded_summary" else "diagnostic"
            assert result == f"<container exceeds {limit} limit>"
    else:
        with pytest.raises(ProfilerUsageError):
            fn(view)
    assert calls[0] == 0
    assert next(iter(view)) is next(iter(data))


@pytest.mark.parametrize("carrier", ["dict", "userdict", "proxy_userdict", "custom"])
def test_small_tuple_keys_preserve_traversal_and_projection(carrier):
    key = ((("leaf",),),)
    data = {key: [1, {"ok": True}]}
    view = _wrap(data, carrier)
    for fn in (values.validate_container_depth, values.validate_json_integers):
        assert fn(view) is None
    for fn in (values.bounded_summary, values.diagnostic_value):
        assert fn(view) == fn(data)
    for fn in (values.bounded_mapping, values.literal_value):
        with pytest.raises(ProfilerUsageError, match="plain strings"):
            fn(view)


@pytest.mark.parametrize("carrier", ["userdict", "proxy_userdict", "custom"])
@pytest.mark.parametrize("direction", ["inputs", "outputs"])
def test_counted_keys_all_reproducer_ingress(carrier, direction, counted_key,
                                           tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    data, calls = counted_key
    view = _wrap(data, carrier)
    binding = paged_binding()
    binding[direction][0]["storage"] = {"storage_id": view}
    raw = _raw(direction, {"storage_id": view})
    calls[0] = 0
    for blocked in (False, True):
        binding["status"] = "blocked" if blocked else "ready"
        with pytest.raises(ProfilerUsageError):
            op.generate_single_op_reproducer(binding, output_dir="caller")
        for tool in (registry.call_mcp_tool, op.call_mcp_tool):
            for args in ({"occurrence": binding}, view):
                envelope = tool("repro_op", args)
                assert envelope["status"] == "blocked"
                assert "artifact_id" not in envelope
                _bounded(envelope)
        for payload in (raw, binding):
            monkeypatch.setattr(op, "load_cli_json", lambda path: payload)
            for mode in (["--dry-run"], ["--output-dir", "caller"]):
                assert cli(["repro-op", "--row", "virtual.json", *mode]) == 2
                assert "Traceback" not in capsys.readouterr().err
    for wrapper in ("ops", "kernels", "occurrences", "operator_rows", "operators", "rows"):
        payload = {wrapper: [raw]}
        monkeypatch.setattr(op, "load_cli_json", lambda path: payload)
        for mode in (["--dry-run"], ["--output-dir", "caller"]):
            assert cli(["repro-op", "--capture", "virtual.json", *mode]) == 2
            assert "Traceback" not in capsys.readouterr().err
    assert calls[0] == 0
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("carrier", ["dict", "userdict", "proxy", "custom"])
@pytest.mark.parametrize("tool", [registry.call_mcp_tool, op.call_mcp_tool])
def test_mapping_arguments_generate_and_resolve(carrier, tool, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    binding = paged_binding()
    before = copy.deepcopy(binding)
    nested = _wrap(binding, carrier)
    args = _wrap({"occurrence": nested, "output_dir": "out"}, carrier)
    result = tool("repro_op", args)
    assert result["status"] == "ready"
    _bounded(result)
    path = Path(result["artifact_path"])
    assert "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() == result["artifact_id"]
    namespace = _load_help(path)
    # Exercise embedded dependencies as well as module loading and --help.
    small = _wrap({((("leaf",),),): None}, carrier)
    for name in ("validate_container_depth", "validate_json_integers", "bounded_summary"):
        assert namespace[name](small) == getattr(values, name)(small)
    assert namespace["bounded_mapping"](_wrap({"x": [1]}, carrier)) == {"x": [1]}
    request = _wrap({"resolve_artifact_id": result["artifact_id"]}, carrier)
    resolved = tool("repro_op", request)
    assert resolved["resolved"] is True and resolved["retrievable"] is True
    assert Path(resolved["artifact_path"]).read_bytes() == path.read_bytes()
    assert Path(resolved["manifest_path"]).read_bytes() == Path(result["manifest_path"]).read_bytes()
    _bounded(resolved)
    assert binding == before and args["occurrence"] is nested
    assert dict(request) == {"resolve_artifact_id": result["artifact_id"]}
    assert list(args) == ["occurrence", "output_dir"]


@pytest.mark.parametrize("tool", [registry.call_mcp_tool, op.call_mcp_tool])
@pytest.mark.parametrize("arguments", [None, [], "text", 1, {}, {"occurrence": []}])
def test_malformed_mapping_arguments_are_bounded(tool, arguments, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    envelope = tool("repro_op", arguments)
    assert envelope["status"] == "blocked"
    if arguments is not None and not isinstance(arguments, Mapping):
        assert envelope["reason"] == "repro_op arguments must be an object"
    _bounded(envelope)
    assert not list(tmp_path.iterdir())


class Deadline(TimeoutError):
    pass


@pytest.mark.parametrize("site", ["len", "iter", "getitem", "hash", "eq"])
@pytest.mark.parametrize("error_type", [TimeoutError, Deadline])
@pytest.mark.parametrize("resolution", [False, True])
def test_outer_mapping_callback_timeout_identity(site, error_type, resolution,
                                                tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    sentinel = error_type("mapping deadline")
    key = "resolve_artifact_id" if resolution else "occurrence"
    item = "sha256:" + "0" * 64 if resolution else paged_binding()

    class Fault(ReadOnly):
        def __len__(self):
            if site == "len":
                raise sentinel
            return super().__len__()

        def __iter__(self):
            if site == "iter":
                raise sentinel
            return super().__iter__()

        def __getitem__(self, name):
            if site == "getitem":
                raise sentinel
            key_timeout_callback(site, sentinel)()
            return super().__getitem__(name)

    for tool in (registry.call_mcp_tool, op.call_mcp_tool):
        with pytest.raises(TimeoutError) as caught:
            tool("repro_op", Fault({key: item}))
        assert caught.value is sentinel
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("total", [1_000_000, 1_000_001])
def test_key_subtree_uses_one_shared_budget(total):
    calls = [0]
    key = (None,) * 499_999

    def lookup():
        calls[0] += 1

    for fn in (values.validate_container_depth, values.validate_json_integers):
        calls[0] = 0
        view = KeyMapping(key, [None] * (total - 500_000), callback=lookup)
        if total == 1_000_000:
            assert fn(view) is None
        else:
            with pytest.raises(ProfilerUsageError, match="traversal"):
                fn(view)
        assert calls[0] == 1


def test_over_budget_entry_is_not_read():
    reads = []

    class ExtraEntry(ReadOnly):
        def __len__(self):
            return 1

        def __getitem__(self, key):
            reads.append(key)
            return super().__getitem__(key)

    view = ExtraEntry({"a": None, "b": None})
    with pytest.raises(ProfilerUsageError, match="members"):
        values.bounded_mapping(view, high=1)
    assert reads == ["a"]
    reads.clear()
    with pytest.raises(ProfilerUsageError, match="traversal"):
        list(values._bounded_members(view, [1_000_000], string_keys=True))
    assert reads == []


@pytest.mark.parametrize("route", ["validate_container_depth", "validate_json_integers",
                                  "bounded_summary", "diagnostic_value"])
def test_key_validation_precedes_hash_timeout(route):
    sentinel = Deadline("tuple leaf hash deadline")
    calls = [0]
    armed = [False]

    class Leaf(int):
        def __hash__(self):
            calls[0] += 1
            if armed[0]:
                raise sentinel
            return int.__hash__(self)

    view = _wrap({(((Leaf(1),),),): None}, "userdict")
    calls[0], armed[0] = 0, True
    with pytest.raises(TimeoutError) as caught:
        getattr(values, route)(view)
    assert caught.value is sentinel and calls[0] == 1


@pytest.mark.parametrize("carrier,hashes", [("dict", 0), ("userdict", 2),
                                          ("proxy_userdict", 2), ("custom", 1)])
def test_small_key_validation_has_no_hashes(carrier, hashes):
    calls = [0]

    class Leaf(int):
        def __hash__(self):
            calls[0] += 1
            return int.__hash__(self)

    view = _wrap({(((Leaf(7),),),): None}, carrier)
    for fn in (values.validate_container_depth, values.validate_json_integers,
               values.bounded_summary, values.diagnostic_value):
        calls[0] = 0
        fn(view)
        assert calls[0] == hashes


@pytest.mark.parametrize("carrier", ["dict", "userdict", "proxy_userdict", "custom"])
def test_valid_mapping_cli_and_generator_controls(carrier, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    data = {"leaf": [None, 1, "value"]}
    view = _wrap(data, carrier)
    assert values.bounded_mapping(view) == values.literal_value(view) == data
    binding = paged_binding()
    binding["inputs"][0]["storage"] = {"storage_id": view}
    raw = _raw("inputs", {"storage_id": view})
    result = op.generate_single_op_reproducer(binding, output_dir="generated")
    assert result["status"] == "ready"
    _load_help(Path(result["output_path"]))
    for index, (source, payload) in enumerate((("--row", raw), ("--row", binding),
                                              ("--capture", _wrap({"ops": [raw]}, carrier)))):
        monkeypatch.setattr(op, "load_cli_json", lambda path: payload)
        for mode in (["--dry-run"], ["--output-dir", f"out{index}"]):
            assert cli(["repro-op", source, "virtual.json", *mode]) == 0
            assert not capsys.readouterr().err
        _load_help(Path(f"out{index}/repro.py"))
    assert dict(view) == {"leaf": [None, 1, "value"]}


@pytest.mark.parametrize("depth", [63, 64])
def test_key_depth_checked_before_lookup(depth):
    key, reads = None, []
    for _ in range(depth):
        key = (key,)
    for fn in (values.validate_container_depth, values.validate_json_integers):
        reads.clear()
        view = KeyMapping(key, callback=lambda: reads.append(True))
        if depth == 64:
            with pytest.raises(ProfilerUsageError, match="nesting"):
                fn(view)
            assert not reads
        else:
            assert fn(view) is None
            assert reads == [True]
