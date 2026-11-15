"""Permanent storage-content and standalone-module regressions for FIX25.

[Role]
  Exercise raw/bound/blocked ingress, helpers, CLI and retrievable MCP scripts.
[Invariants]
  Invalid storage raises bounded usage errors before hashing or publication;
  every ready control loads without hardware and contains only built-in data.
[Timeouts & Locks]
  Subprocesses have a 30-second timeout; no locks or device execution.
[Side-Effect Policy]
  Files are confined to pytest temporary directories; no interpreter limits
  are changed. Caller storage mappings remain untouched.
"""

import ast
import hashlib
import importlib.util
import json
import math
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

from mindie_profiler.__main__ import main as cli_main
from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.op_api_registry import bind_captured_occurrence
from mindie_profiler.repro_metadata import synthesize_metadata, validate_metadata_counts
from mindie_profiler.repro_op import _compact_occurrence, _render, call_mcp_tool
from mindie_profiler.repro_op import generate_single_op_reproducer
from mindie_profiler.repro_preconditions import precondition_problems
from mindie_profiler.repro_values import literal_value, slot_allocations
from mindie_profiler.repro_values import storage_mapping, storage_record, validate_binding_counts
from mindie_profiler.token_budget import estimate_tokens
from nr_s6_support import paged_binding, paged_row
from test_nr_s6_round2_closure import _ready_bindings


class Frozen(Mapping):
    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)


class UnsafeInt(int):
    def __repr__(self):
        raise AssertionError("caller repr must never be evaluated")


def _bad_storage():
    cases = {"key_int": {1: "x", "storage_offset": 0},
             "key_tuple": {("x",): 0}, "key_none": {None: 0},
             "key_bool": {False: 0}, "key_object": {object(): 0}}
    for label, leaf in {"inf": math.inf, "negative_inf": -math.inf, "nan": math.nan,
                        "huge": 10**5000, "bytes": b"x", "set": {1},
                        "function": _bad_storage, "object": object(),
                        "subclass": UnsafeInt(1)}.items():
        cases[label] = {"storage_id": leaf}
        cases["nested_" + label] = {"storage_id": MappingProxyType({"x": (leaf,)})}
        cases["unknown_" + label] = {"unknown": {"x": [leaf]}}
    cases.update({"nested_key": {"storage_id": {"x": [{1: "x"}]}},
                  "unknown_key": {"unknown": {None: "x"}},
                  "id_bool": {"storage_id": True},
                  "alias_bool": {"storage_object_id": False}})
    return cases


def _raw(direction, storage):
    row = paged_row()
    field = direction[:-1]
    row[field + "_shapes"] = [
        dict(shape=json.loads(shape), dtype=row[field + "_dtypes"][i],
             layout=row[field + "_formats"][i])
        for i, shape in enumerate(row[field + "_shapes"])]
    row[field + "_shapes"][0]["storage"] = storage
    return row


def _usage(fn):
    with pytest.raises(ProfilerUsageError) as exc:
        fn()
    assert len(str(exc.value)) < 1500


def _envelope(value):
    wire = json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)
    body = json.dumps({k: v for k, v in value.items() if k != "receipt"},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False)
    assert estimate_tokens(value) <= 250
    if tiktoken is not None:
        for name in ("cl100k_base", "o200k_base"):
            try:
                enc = tiktoken.get_encoding(name)
            except TimeoutError:
                raise
            except Exception:
                break
            assert len(enc.encode(wire, disallowed_special=())) <= estimate_tokens(value) <= 250
            assert len(enc.encode(body, disallowed_special=())) <= value["receipt"]["token_estimate"]
    assert value["receipt"]["within_budget"]


@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("label", sorted(_bad_storage()))
def test_r25_storage_contents_all_helpers(direction, label, tmp_path, monkeypatch):
    limits = sys.get_int_max_str_digits(), sys.getrecursionlimit()
    assert limits[0] == 4300
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    storage = _bad_storage()[label]
    binding = paged_binding()
    occurrence = _compact_occurrence(binding)
    binding[direction][0]["storage"] = storage
    next(a for a in occurrence["allocations"] if a["direction"] == direction[:-1])["storage"] = storage
    for fn in (lambda: storage_mapping(storage),
               lambda: storage_record(binding[direction][0]),
               lambda: validate_binding_counts(binding), lambda: slot_allocations(binding),
               lambda: validate_metadata_counts(occurrence),
               lambda: synthesize_metadata(occurrence),
               lambda: bind_captured_occurrence(_raw(direction, storage))):
        _usage(fn)
    assert precondition_problems(occurrence)
    for status in ("bound", "blocked"):
        binding["status"] = status
        _usage(lambda: _compact_occurrence(binding))
        _usage(lambda: generate_single_op_reproducer(binding, output_dir="caller"))
        envelope = call_mcp_tool("repro_op", {"occurrence": binding, "output_dir": "caller"})
        assert envelope["status"] == "blocked" and "artifact_id" not in envelope
        _envelope(envelope)
    assert not list(tmp_path.iterdir())
    assert limits == (sys.get_int_max_str_digits(), sys.getrecursionlimit())


@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("key", [1, ("x",), None, True], ids=["int", "tuple", "null", "bool"])
@pytest.mark.parametrize("route", ["raw", "bound", "blocked"])
def test_r25_non_string_key_cli_ingress(direction, key, route, tmp_path, monkeypatch, capsys):
    storage = {key: "x", "storage_offset": 0}
    payload = _raw(direction, storage) if route == "raw" else paged_binding()
    if route != "raw":
        payload[direction][0]["storage"] = storage
        payload["status"] = route
    monkeypatch.setattr("mindie_profiler.repro_op.load_cli_json", lambda path: payload)
    for args in (["--dry-run"], ["--output-dir", str(tmp_path / "caller")]):
        assert cli_main(["repro-op", "--row", "virtual.json", *args]) == 2
        output = capsys.readouterr()
        assert "Traceback" not in output.err and len(output.err) < 1500
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("location", ["direct", "nested", "unknown"])
@pytest.mark.parametrize("literal", ["1e309", "-1e309", "NaN", "Infinity", "-Infinity"])
def test_r25_nonfinite_real_cli(direction, location, literal, tmp_path):
    storage = ('{"storage_id":' + literal + '}' if location == "direct" else
               '{"' + ("unknown" if location == "unknown" else "storage_id") +
               '":{"x":[' + literal + ']}}')
    for route in ("raw", "bound", "blocked"):
        payload = _raw(direction, "LITERAL") if route == "raw" else paged_binding()
        if route != "raw":
            payload[direction][0]["storage"] = "LITERAL"
            payload["status"] = route
        path = tmp_path / (route + ".json")
        path.write_text(json.dumps(payload).replace('"LITERAL"', storage))
        for args in (["--dry-run"], ["--output-dir", str(tmp_path / "caller")]):
            run = subprocess.run([sys.executable, "-B", "-m", "mindie_profiler", "repro-op",
                                  "--row", str(path), *args], capture_output=True,
                                 text=True, timeout=30)
            assert run.returncode == 2, run.stderr
            assert "Traceback" not in run.stderr and len(run.stderr) < 1500
    assert not list(tmp_path.glob("caller*"))


@pytest.mark.parametrize("wrapper", ["ops", "kernels", "occurrences", "operator_rows", "operators", "rows"])
@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("literal,expected", [('{"storage_id":1e309}', 2),
    ('{"storage_id":{"x":[-1e309]}}', 2), ('{"storage_id":NaN}', 2),
    ('{"storage_id":"valid"}', 0), ('null', 0), ('{}', 0)])
def test_r25_capture_wrappers(wrapper, direction, literal, expected, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    path = tmp_path / "capture.json"
    path.write_text(json.dumps({wrapper: [_raw(direction, "LITERAL")]}).replace('"LITERAL"', literal))
    for args in (["--dry-run"], ["--output-dir", "caller"]):
        run = subprocess.run([sys.executable, "-B", "-m", "mindie_profiler", "repro-op",
                              "--capture", str(path), "--occurrence-index", "0", *args],
                             capture_output=True, text=True, timeout=30)
        assert run.returncode == expected, run.stderr
        assert "Traceback" not in run.stderr and len(run.stderr) < 1500
    if expected == 0:
        _load_script(tmp_path / "caller/repro.py")
    else:
        assert not list(tmp_path.glob("caller*"))


def _load_script(path):
    spec = importlib.util.spec_from_file_location("r25_standalone", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.OCCURRENCE == literal_value(module.OCCURRENCE)
    tree = ast.parse(path.read_text())
    assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "OCCURRENCE" for t in n.targets))
    assert ast.literal_eval(assignment.value) == module.OCCURRENCE
    run = subprocess.run([sys.executable, "-B", str(path), "--help"],
                         capture_output=True, text=True, timeout=30)
    assert run.returncode == 0 and "usage:" in run.stdout and not run.stderr
    return module.OCCURRENCE


def _valid_storage():
    nested = {"x": (None, False, "id", 7, -1.25, MappingProxyType({"leaf": [1]}))}
    return {"none": None, "empty": {}, "str": {"storage_id": "allocation-id"},
            "template_text": {"storage_id": "__SYNTH_SOURCE__ '__DTYPE_MAP__'\n\x00界"},
            "int": {"storage_id": -7}, "null_id": {"storage_id": None},
            "int_edge": {"storage_id": (1 << 4096) - 1},
            "float_edge": {"storage_id": sys.float_info.max},
            "float_small": {"storage_id": 5e-324},
            "userdict": UserDict({"storage_offset": 0}),
            "proxy": MappingProxyType({"storage_bytes": 16384}),
            "custom": Frozen({"storage_offset": 0}),
            "nested_proxy": {"storage_id": MappingProxyType(nested)},
            "nested_custom": {"storage_id": UserDict({"x": Frozen(nested)})}}


@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("label", sorted(_valid_storage()))
def test_r25_valid_mapping_controls_and_retrieval(direction, label, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    storage = _valid_storage()[label]
    normalized = storage_mapping(storage)
    json.dumps(normalized, sort_keys=True, allow_nan=False)
    bound = paged_binding()
    bound[direction][0]["storage"] = storage
    for route, binding in (("bound", bound), ("raw", bind_captured_occurrence(_raw(direction, storage)))):
        result = generate_single_op_reproducer(binding, output_dir=route)
        assert result["status"] == "ready" and result["syntax_ok"]
        occurrence = _load_script(Path(route) / "repro.py")
        actual = next(a for a in occurrence["allocations"] if a["direction"] == direction[:-1])["storage"]
        assert actual == normalized
        envelope = call_mcp_tool("repro_op", {"occurrence": binding})
        _envelope(envelope)
        assert envelope["status"] == "ready"
        receipt = call_mcp_tool("repro_op", {"resolve_artifact_id": envelope["artifact_id"]})
        _envelope(receipt)
        assert receipt["resolved"] and receipt["retrievable"]
        artifact = Path(receipt["artifact_path"])
        assert "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest() == envelope["artifact_id"]
        assert _load_script(artifact) == occurrence
    assert bound[direction][0]["storage"] is storage
    assert storage_mapping(storage) == normalized


@pytest.mark.parametrize("name", sorted(_ready_bindings()))
def test_r25_every_ready_recipe_loads(name, tmp_path):
    binding = _ready_bindings()[name]
    binding["inputs"][0]["storage"] = {"storage_id": MappingProxyType({"x": ("id", 1)})}
    result = generate_single_op_reproducer(binding)
    assert result["status"] == "ready"
    path = tmp_path / "repro.py"
    path.write_text(result["script"])
    _load_script(path)


@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("key", ["storage_id", "storage_object_id", "offset", "storage_bytes"])
def test_r25_direct_members_and_shadowed_values(direction, key):
    binding = paged_binding()
    record = binding[direction][0]
    record[key] = math.inf
    record["storage"] = {key: 0}
    _usage(lambda: storage_record(record))
    _usage(lambda: validate_binding_counts(binding))
    raw = _raw(direction, {key: 0})
    raw[direction[:-1] + "_shapes"][0][key] = math.inf
    _usage(lambda: bind_captured_occurrence(raw))


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan, object(), b"x", {1}, UnsafeInt(1)],
                         ids=["inf", "negative_inf", "nan", "object", "bytes", "set", "subclass"])
def test_r25_render_defense(value):
    occurrence = _compact_occurrence(paged_binding())
    occurrence["untrusted"] = value
    _usage(lambda: _render(occurrence, warmup=0, iters=5, flush_mb=0, max_cv_pct=5.0, l2_bytes=None))


from mindie_profiler.repro_values import (
    bounded_container_len, bounded_mapping, bounded_sequence, bounded_summary,
    diagnostic_value, validate_container_depth, validate_json_integers,
)


class VirtualWidth(Mapping):
    """Lazy finite or lying mapping with observable protocol callbacks."""

    def __init__(self, declared, count=None, *, fault=None, sentinel=None, leaf=None, reads=None):
        self.declared = declared
        self.count = declared if count is None else count
        self.fault, self.sentinel, self.leaf = fault, sentinel, leaf
        self.reads = reads if reads is not None else {"len": 0, "iter": 0, "key": 0, "value": 0}

    def __len__(self):
        self.reads["len"] += 1
        if self.fault == "len":
            raise self.sentinel
        return self.declared

    def __iter__(self):
        self.reads["iter"] += 1
        if self.fault == "iter":
            raise self.sentinel

        def keys():
            for i in range(self.count):
                self.reads["key"] += 1
                yield str(i)

        return keys()

    def __getitem__(self, key):
        self.reads["value"] += 1
        if self.fault == "getitem":
            raise self.sentinel
        if type(key) is not str or not key.isdecimal() or not 0 <= int(key) < self.count:
            raise KeyError(key)
        return self.leaf


class CountedArray(list):
    def __init__(self, items, reads, declared=None):
        super().__init__(items)
        self.reads, self.declared = reads, declared

    def __len__(self):
        return super().__len__() if self.declared is None else self.declared

    def __iter__(self):
        for item in super().__iter__():
            self.reads["value"] += 1
            yield item


def _width_binding(value, direction="inputs", placement="id"):
    storage = value if placement == "top" else {"storage_id": value}
    binding = paged_binding()
    binding[direction][0]["storage"] = storage
    return binding, storage


@pytest.mark.parametrize("size", [1_000_001, sys.maxsize, sys.maxsize + 1, 1 << 100])
@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("placement", ["top", "id"])
def test_r26_declared_cardinality_before_members(size, direction, placement, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    value = VirtualWidth(size)
    binding, storage = _width_binding(value, direction, placement)
    for call in (lambda: bounded_container_len(value), lambda: bounded_mapping(value),
                 lambda: validate_container_depth(value), lambda: literal_value(value),
                 lambda: validate_json_integers(value), lambda: storage_mapping(storage),
                 lambda: storage_record({"storage": storage}),
                 lambda: storage_record(value), lambda: validate_binding_counts(binding),
                 lambda: bind_captured_occurrence(_raw(direction, storage))):
        _usage(call)
    for status in ("bound", "blocked"):
        binding["status"] = status
        _usage(lambda: generate_single_op_reproducer(binding, output_dir="caller"))
        result = call_mcp_tool("repro_op", {"occurrence": binding, "output_dir": "caller"})
        assert result["status"] == "blocked" and "artifact_id" not in result
        _envelope(result)
    assert value.reads["len"] > 0
    assert {k: v for k, v in value.reads.items() if k != "len"} == {"iter": 0, "key": 0, "value": 0}
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("size", [1_000_001, sys.maxsize, sys.maxsize + 1])
@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("placement", ["top", "id"])
@pytest.mark.parametrize("route", ["raw", "bound", "blocked", "ops", "kernels",
                                   "occurrences", "operator_rows", "operators", "rows"])
def test_r26_cli_cardinality_all_wrappers(size, direction, placement, route,
                                        tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    value = VirtualWidth(size)
    binding, storage = _width_binding(value, direction, placement)
    binding["status"] = "blocked" if route == "blocked" else "bound"
    raw = _raw(direction, storage)
    wrapper = route not in ("raw", "bound", "blocked")
    payload = {route: [None, raw]} if wrapper else raw if route == "raw" else binding
    monkeypatch.setattr("mindie_profiler.repro_op.load_cli_json", lambda path: payload)
    source = ["--capture", "virtual.json", "--occurrence-index", "1"] if wrapper else ["--row", "virtual.json"]
    for args in (["--dry-run"], ["--output-dir", "caller"]):
        assert cli_main(["repro-op", *source, *args]) == 2
        output = capsys.readouterr()
        assert len(output.err) < 1500 and "Traceback" not in output.err
    assert value.reads["iter"] == value.reads["key"] == value.reads["value"] == 0
    assert not list(tmp_path.iterdir())


def _budget_fixture(kind):
    reads = {"len": 0, "iter": 0, "key": 0, "value": 0}
    if kind == "lying_mapping":
        return VirtualWidth(1, sys.maxsize, reads=reads), reads
    if kind == "lying_array":
        return CountedArray(range(1_000_001), reads, declared=1), reads
    if kind == "dict_dag":
        leaf = None
        for _ in range(3):
            leaf = VirtualWidth(1000, leaf=leaf, reads=reads)
        return leaf, reads
    leaf = [] if kind == "empty_dag" else None
    for _ in range(3):
        leaf = CountedArray([leaf] * 1000, reads)
    return leaf, reads


@pytest.mark.parametrize("kind", ["lying_mapping", "lying_array", "list_dag", "dict_dag", "empty_dag"])
@pytest.mark.parametrize("route", ["depth", "literal", "snapshot", "integers", "counts",
                                   "raw", "generator", "blocked_generator", "mcp", "blocked_mcp"])
def test_r26_cumulative_budget_counts_alias_visits(kind, route, tmp_path, monkeypatch):
    value, reads = _budget_fixture(kind)
    binding, storage = _width_binding(value)
    if route.startswith("blocked_"):
        binding["status"] = "blocked"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    calls = {"depth": lambda: validate_container_depth(value),
             "literal": lambda: literal_value(value),
             "integers": lambda: validate_json_integers(value),
             "snapshot": lambda: (bounded_mapping(value) if isinstance(value, Mapping)
                                  else bounded_sequence(value, "array")),
             "counts": lambda: validate_binding_counts(binding),
             "raw": lambda: bind_captured_occurrence(_raw("inputs", storage))}
    if "mcp" in route:
        result = call_mcp_tool("repro_op", {"occurrence": binding, "output_dir": "caller"})
        assert result["status"] == "blocked" and "artifact_id" not in result
        _envelope(result)
    else:
        _usage(calls.get(route, lambda: generate_single_op_reproducer(binding, output_dir="caller")))
    assert 0 < reads["value"] <= 1_000_001
    if route in ("depth", "literal", "integers", "snapshot"):
        if isinstance(value, Mapping):
            assert reads["key"] == 1_000_001
            assert reads["value"] == 1_000_000
        else:
            assert reads["value"] == 1_000_001
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("fault", ["len", "iter", "getitem"])
@pytest.mark.parametrize("route", ["length", "depth", "literal", "snapshot", "integers", "record",
                                   "counts", "raw", "generator", "blocked_generator", "mcp",
                                   "blocked_mcp", "cli", "capture", "summary", "diagnostic"])
def test_r26_timeout_identity(fault, route, tmp_path, monkeypatch):
    sentinel = TimeoutError("container callback deadline")
    value = VirtualWidth(1, fault=fault, sentinel=sentinel)
    binding, storage = _width_binding(value)
    if route.startswith("blocked_"):
        binding["status"] = "blocked"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    calls = {"length": lambda: bounded_container_len(value),
             "depth": lambda: validate_container_depth(value),
             "literal": lambda: literal_value(value), "snapshot": lambda: bounded_mapping(value),
             "integers": lambda: validate_json_integers(value),
             "record": lambda: storage_record({"storage": storage}),
             "counts": lambda: validate_binding_counts(binding),
             "raw": lambda: bind_captured_occurrence(_raw("inputs", storage)),
             "summary": lambda: bounded_summary(value), "diagnostic": lambda: diagnostic_value(value)}
    if route == "length" and fault != "len":
        assert calls[route]() == 1
        return
    if route in ("cli", "capture"):
        payload = {"rows": [_raw("inputs", storage)]} if route == "capture" else binding
        monkeypatch.setattr("mindie_profiler.repro_op.load_cli_json", lambda path: payload)
        call = lambda: cli_main(["repro-op", "--capture" if route == "capture" else "--row",
                                "virtual.json", "--dry-run"])
    elif "mcp" in route:
        call = lambda: call_mcp_tool("repro_op", {"occurrence": binding})
    else:
        call = calls.get(route, lambda: generate_single_op_reproducer(binding, output_dir="caller"))
    with pytest.raises(TimeoutError) as exc:
        call()
    assert exc.value is sentinel
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("size", [1_000_001, sys.maxsize, sys.maxsize + 1, 1 << 100])
def test_r26_diagnostics_and_array_lengths(size):
    mapping = VirtualWidth(size)
    array = CountedArray([None], {"value": 0}, declared=size)
    for value in (mapping, array):
        assert len(bounded_summary(value)) < 160
        assert len(str(diagnostic_value(value))) < 160
    _usage(lambda: bounded_sequence(array, "array"))
    assert mapping.reads["iter"] == mapping.reads["value"] == array.reads["value"] == 0


def test_r26_exact_cumulative_boundary_and_fresh_root_budget():
    value = [None] * 1_000_000
    for _ in range(2):
        validate_container_depth(value)
        assert len(literal_value(value)) == 1_000_000
    for call in (validate_container_depth, literal_value):
        _usage(lambda: call([value]))
    assert (sys.get_int_max_str_digits(), sys.getrecursionlimit()) == (4300, 1000)


@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("placement", ["top", "id"])
def test_r26_small_lazy_mapping_standalone(direction, placement, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    value = VirtualWidth(3)
    binding, storage = _width_binding(value, direction, placement)
    for route, bound in (("bound", binding), ("raw", bind_captured_occurrence(_raw(direction, storage)))):
        result = generate_single_op_reproducer(bound, output_dir=route)
        assert result["status"] == "ready"
        _load_script(Path(result["output_path"]))
        receipt = call_mcp_tool("repro_op", {"occurrence": bound})
        _envelope(receipt)
        assert receipt["status"] == "ready"
        resolved = call_mcp_tool("repro_op", {"resolve_artifact_id": receipt["artifact_id"]})
        assert resolved["resolved"] and resolved["retrievable"]
        _load_script(Path(resolved["artifact_path"]))
    assert binding[direction][0]["storage"] is storage


@pytest.mark.parametrize("kind", ["lying_mapping", "list_dag", "dict_dag"])
@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("route", ["raw", "bound", "blocked", "ops", "kernels",
                                   "occurrences", "operator_rows", "operators", "rows"])
def test_r26_cli_cumulative_budget(kind, direction, route, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    wrapper = route not in ("raw", "bound", "blocked")
    for args in (["--dry-run"], ["--output-dir", "caller"]):
        value, reads = _budget_fixture(kind)
        binding, storage = _width_binding(value, direction)
        binding["status"] = "blocked" if route == "blocked" else "bound"
        raw = _raw(direction, storage)
        payload = {route: [None, raw]} if wrapper else raw if route == "raw" else binding
        monkeypatch.setattr("mindie_profiler.repro_op.load_cli_json", lambda path: payload)
        source = (["--capture", "virtual.json", "--occurrence-index", "1"] if wrapper
                  else ["--row", "virtual.json"])
        assert cli_main(["repro-op", *source, *args]) == 2
        output = capsys.readouterr()
        assert "Traceback" not in output.err and len(output.err) < 1500
        assert 0 < reads["value"] <= 1_000_001
    assert not list(tmp_path.iterdir())




from nr_s6_support import KeyMapping, key_fixture, key_timeout_callback
from mindie_profiler.op_api_registry import call_mcp_tool as registry_mcp
from mindie_profiler.op_abi_binding import bind_resolved_occurrence
from mindie_profiler.op_abi_attributes import attr_issue


@pytest.fixture
def key_deadline():
    import signal
    def expired(signum, frame):
        raise TimeoutError("key validation exceeded test deadline")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 60)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


@pytest.mark.parametrize("kind", ["counted", "billion", "frozenset", "list", "dict", "int", "tuple", "str_subclass"])
@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("placement", ["top", "id", "direct", "attrs"])
def test_r27_key_rejection_before_hash(kind, direction, placement, tmp_path, monkeypatch, capsys, key_deadline):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    key, calls = key_fixture(kind)
    value = KeyMapping(key)
    binding, storage = _width_binding(value, direction, "top" if placement == "top" else "id")
    raw = _raw(direction, storage)
    if placement == "direct":
        binding[direction][0].update(storage_id=value, storage={})
        raw[direction[:-1] + "_shapes"][0].update(storage_id=value, storage={})
    elif placement == "attrs":
        binding["attrs"] = raw["attrs"] = value
    for call in (lambda: literal_value(value), lambda: bounded_mapping(value),
                 lambda: bind_resolved_occurrence(paged_row(), value),
                 lambda: attr_issue("field", "int", 1, value),
                 lambda: storage_mapping(storage), lambda: storage_record({"storage": storage}),
                 lambda: validate_binding_counts(binding), lambda: bind_captured_occurrence(raw)):
        _usage(call)
    for status in ("bound", "blocked"):
        binding["status"] = status
        _usage(lambda: generate_single_op_reproducer(binding, output_dir="caller"))
        for tool in (call_mcp_tool, registry_mcp):
            result = tool("repro_op", {"occurrence": binding})
            assert result["status"] == "blocked" and "artifact_id" not in result
            _envelope(result)
    for route in ("raw", "bound", "blocked", "ops", "kernels", "occurrences", "operator_rows", "operators", "rows"):
        wrapper = route not in ("raw", "bound", "blocked")
        binding["status"] = "blocked" if route == "blocked" else "bound"
        payload = {route: [None, raw]} if wrapper else raw if route == "raw" else binding
        monkeypatch.setattr("mindie_profiler.repro_op.load_cli_json", lambda path: payload)
        source = ["--capture", "virtual.json", "--occurrence-index", "1"] if wrapper else ["--row", "virtual.json"]
        for mode in (["--dry-run"], ["--output-dir", "caller"]):
            assert cli_main(["repro-op", *source, *mode]) == 2
            assert "Traceback" not in capsys.readouterr().err
    assert calls == {"hash": 0, "eq": 0}
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("method", ["hash", "eq"])
@pytest.mark.parametrize("error_type", [TimeoutError, type("KeyDeadline", (TimeoutError,), {})])
@pytest.mark.parametrize("status", ["bound", "blocked"])
def test_r27_reached_key_timeout_identity(method, error_type, status, tmp_path, monkeypatch, key_deadline):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    sentinel = error_type("key callback deadline")
    value = KeyMapping("valid", callback=key_timeout_callback(method, sentinel))
    binding, storage = _width_binding(value)
    binding["status"] = status
    for call in (lambda: bounded_mapping(value), lambda: literal_value(value),
                 lambda: validate_container_depth(value), lambda: diagnostic_value(value),
                 lambda: storage_record({"storage": storage}), lambda: validate_binding_counts(binding),
                 lambda: bind_captured_occurrence(_raw("inputs", storage)),
                 lambda: generate_single_op_reproducer(binding, output_dir="caller"),
                 lambda: call_mcp_tool("repro_op", {"occurrence": binding}),
                 lambda: registry_mcp("repro_op", {"occurrence": binding})):
        with pytest.raises(TimeoutError) as error:
            call()
        assert error.value is sentinel
    for wrapper in ("ops", "kernels", "occurrences", "operator_rows", "operators", "rows"):
        monkeypatch.setattr("mindie_profiler.repro_op.load_cli_json", lambda path: {wrapper: [_raw("inputs", storage)]})
        for mode in (["--dry-run"], ["--output-dir", "caller"]):
            with pytest.raises(TimeoutError) as error:
                cli_main(["repro-op", "--capture", "virtual.json", *mode])
            assert error.value is sentinel
    assert not list(tmp_path.iterdir())
