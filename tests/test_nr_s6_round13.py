"""Round-13/14/15 closure: TimeoutError identity and lifecycle cleanup.

[Role]
  Pin public timeout identity, checked predicates, writer rollback and
  multi-child reaping with transient or persistent method faults.

[Invariants]
  * Every injected ``TimeoutError`` instance is re-raised unchanged; it is never
    translated to ``ProfilerUsageError``, ``delivery_failed``,
    ``delivery_blocked``, ``status="ready"``, ``None`` or a fallback root.
  * A timed-out write leaves no open descriptor, no temporary and no half pair;
    the same fault-free request then succeeds.
  * A timeout during termination or abort-file inspection still reaps every
    owned child before the identical sentinel escapes.

[Timeouts & Locks]
  In-process monkeypatching plus short-lived real Python children; no device,
  thread, network or NPU work.

[Side-Effect Policy]
  Writes only relative roots under pytest's temporary directory and restores
  every patched environment variable, module attribute or child object.
"""

from __future__ import annotations

import contextlib
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

from mindie_profiler import op_api_registry as registry
from mindie_profiler import repro_atomic_io as atomic_io
from mindie_profiler import repro_storage as storage
from mindie_profiler.fabric_probe import supervise_probe_processes
from mindie_profiler.repro_op import (
    call_mcp_tool as repro_mcp, generate_single_op_reproducer,
)
from mindie_sim import diff_trace
from mindie_sim.diff_trace import call_mcp_tool as diff_mcp
from nr_s6_support import paged_binding

def test_r13_registry_mcp_re_raises_catalog_stat_timeout():
    catalog = registry._catalog_path()
    sentinel = TimeoutError("R13 catalog stat timeout")
    original = Path.stat

    def stat_timeout(self, *args, **kwargs):
        if self == catalog:
            raise sentinel
        return original(self, *args, **kwargs)

    with patch.object(Path, "stat", stat_timeout):
        with pytest.raises(TimeoutError) as caught:
            registry.call_mcp_tool("inspect_op_abi", {"op_name": "aclnnSwiGlu"})
    assert caught.value is sentinel

def test_r13_registry_mcp_re_raises_catalog_read_text_timeout():
    catalog = registry._catalog_path()
    sentinel = TimeoutError("R13 catalog read timeout")
    original = Path.read_text
    registry._catalog_index.cache_clear()

    def read_timeout(self, *args, **kwargs):
        if self == catalog:
            raise sentinel
        return original(self, *args, **kwargs)

    try:
        with patch.object(Path, "read_text", read_timeout):
            with pytest.raises(TimeoutError) as caught:
                registry.call_mcp_tool(
                    "inspect_op_abi", {"op_name": "aclnnSwiGlu"})
        assert caught.value is sentinel
    finally:
        registry._catalog_index.cache_clear()

def test_r13_repro_op_re_raises_anchor_stat_timeout(monkeypatch, tmp_path):
    binding = paged_binding()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "r13_anchor")
    sentinel = TimeoutError("R13 anchor stat timeout")
    original = os.stat

    def stat_timeout(path, *args, **kwargs):
        if isinstance(path, (str, bytes, os.PathLike)) \
                and os.fspath(path) == os.sep:
            raise sentinel
        return original(path, *args, **kwargs)

    with patch.object(os, "stat", stat_timeout):
        with pytest.raises(TimeoutError) as caught:
            repro_mcp("repro_op", {"occurrence": binding, "iters": 4101})
    assert caught.value is sentinel

def test_r13_repro_op_re_raises_predictable_temp_lstat_timeout(
        monkeypatch, tmp_path):
    binding = paged_binding()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "r13_temps")
    sentinel = TimeoutError("R13 predictable temp lstat timeout")
    original = os.lstat
    hits = []

    def lstat_timeout(path, *args, **kwargs):
        if isinstance(path, (str, bytes, os.PathLike)) \
                and os.fspath(path).endswith(os.sep + "index.json.tmp"):
            hits.append(os.fspath(path))
            raise sentinel
        return original(path, *args, **kwargs)

    with patch.object(os, "lstat", lstat_timeout):
        with pytest.raises(TimeoutError) as caught:
            repro_mcp("repro_op", {"occurrence": binding, "iters": 4102})
    assert caught.value is sentinel
    assert hits

@pytest.mark.parametrize("resolver", [
    storage._resolved,
    storage._resolved_target,
    atomic_io._resolved_loose,
])
def test_r13_path_resolvers_re_raise_resolve_timeout(resolver):
    sentinel = TimeoutError("R13 resolve timeout")

    def resolve_timeout(self, *args, **kwargs):
        raise sentinel

    with patch.object(Path, "resolve", resolve_timeout):
        with pytest.raises(TimeoutError) as caught:
            resolver(Path("r13_path/timeout"))
    assert caught.value is sentinel

def test_r13_diff_root_re_raises_short_root_timeout(monkeypatch):
    sentinel = TimeoutError("R13 short-root timeout")

    def raising():
        raise sentinel

    monkeypatch.setattr(storage, "short_root", raising)
    with pytest.raises(TimeoutError) as caught:
        diff_trace._diff_root()
    assert caught.value is sentinel

def test_r13_diff_mcp_re_raises_short_root_timeout(monkeypatch):
    sentinel = TimeoutError("R13 diff root timeout")

    def raising():
        raise sentinel

    trace = {"total_ms": 4, "ops": [{"name": "T", "duration_ms": 4}]}
    monkeypatch.setattr(storage, "short_root", raising)
    with pytest.raises(TimeoutError) as caught:
        diff_mcp({"predicted": trace, "captured": trace})
    assert caught.value is sentinel

# ---------------------------------------------------------------- Round 14
def _fsync_harness(leaf, sentinel):
    """Patch os.open/os.fsync and track the production temporary descriptor."""
    tracked, hits = {}, []
    original_open, original_fsync = os.open, os.fsync

    def tracked_open(path, flags, *args, **kwargs):
        descriptor = original_open(path, flags, *args, **kwargs)
        name = os.fsdecode(path) if isinstance(
            path, (str, bytes, os.PathLike)) else ""
        if flags & os.O_WRONLY and ("." + leaf + ".") in name:
            tracked[descriptor] = name
        return descriptor

    def fsync_timeout(descriptor):
        if descriptor in tracked:
            hits.append(descriptor)
            raise sentinel
        return original_fsync(descriptor)

    return tracked, hits, tracked_open, fsync_timeout

def _assert_descriptors_and_temporaries_gone(tracked):
    for descriptor, temporary in tracked.items():
        with pytest.raises(OSError) as caught:
            os.fstat(descriptor)
        assert caught.value.errno == errno.EBADF
        assert atomic_io.path_exists(Path(temporary)) is False

def _sleeper(seconds):
    return subprocess.Popen(
        [sys.executable, "-B", "-c",
         f"import time; time.sleep({seconds})"])

def _reap_children(children):
    for child in children:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=5)

def test_r14_checked_predicates_re_raise_timeout_and_report_absence(tmp_path):
    missing = tmp_path / "missing"
    assert atomic_io.stat_or_none(missing) is None
    assert atomic_io.lstat_or_none(missing) is None
    assert atomic_io.path_exists(missing) is False
    assert atomic_io.path_lexists(missing) is False
    assert atomic_io.path_is_dir(missing) is False
    assert atomic_io.path_is_file(missing) is False
    assert atomic_io.path_is_symlink(missing) is False
    regular = tmp_path / "regular"
    regular.write_text("x", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(regular)
    assert atomic_io.path_exists(regular) is True
    assert atomic_io.path_is_file(regular) is True
    assert atomic_io.path_is_dir(regular) is False
    assert atomic_io.path_is_dir(tmp_path) is True
    assert atomic_io.path_is_symlink(link) is True
    assert atomic_io.path_is_file(link) is True
    sentinel = TimeoutError("R14 checked stat timeout")
    original_stat, original_lstat = os.stat, os.lstat

    def stat_timeout(path, *args, **kwargs):
        if Path(path) == missing:
            raise sentinel
        return original_stat(path, *args, **kwargs)

    def lstat_timeout(path, *args, **kwargs):
        if Path(path) == missing:
            raise sentinel
        return original_lstat(path, *args, **kwargs)

    with patch.object(os, "stat", stat_timeout):
        for helper in (atomic_io.stat_or_none, atomic_io.path_exists):
            with pytest.raises(TimeoutError) as caught:
                helper(missing)
            assert caught.value is sentinel
    with patch.object(os, "lstat", lstat_timeout):
        for helper in (atomic_io.lstat_or_none, atomic_io.path_lexists,
                       atomic_io.path_is_symlink):
            with pytest.raises(TimeoutError) as caught:
                helper(missing)
            assert caught.value is sentinel

@pytest.mark.parametrize("helper_name", ["_has_pair", "_slot_state"])
def test_r14_repro_mcp_checked_predicate_re_raises_public_timeout(
        helper_name, monkeypatch, tmp_path):
    binding = paged_binding()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "r14pred_seed")
    assert generate_single_op_reproducer(
        binding, iters=4300, stage=True)["status"] == "ready"
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "r14pred_" + helper_name)
    helper = getattr(storage, helper_name)
    sentinel = TimeoutError("R14 predicate " + helper_name)
    original = os.lstat
    hits = []

    def lstat_timeout(path, *args, **kwargs):
        frame = sys._getframe(1)
        codes = []
        for _ in range(4):
            if frame is None:
                break
            codes.append(frame.f_code)
            frame = frame.f_back
        if (atomic_io.lstat_or_none.__code__ in codes
                and helper.__code__ in codes
                and str(path).endswith("/repro.py")):
            hits.append(str(path))
            raise sentinel
        return original(path, *args, **kwargs)

    with patch.object(os, "lstat", lstat_timeout):
        with pytest.raises(TimeoutError) as caught:
            repro_mcp("repro_op", {"occurrence": binding, "iters": 4301})
    assert caught.value is sentinel
    assert hits

@pytest.mark.parametrize("leaf", ["repro.py", "manifest.json"])
def test_r14_writer_fsync_timeout_cleans_up_and_retries(
        leaf, monkeypatch, tmp_path):
    binding = paged_binding()
    monkeypatch.chdir(tmp_path)
    root = "r14write_" + leaf.split(".")[0]
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", root)
    sentinel = TimeoutError("R14 fsync " + leaf)
    tracked, hits, tracked_open, fsync_timeout = _fsync_harness(leaf, sentinel)
    with patch.object(os, "open", tracked_open), \
            patch.object(os, "fsync", fsync_timeout):
        with pytest.raises(TimeoutError) as caught:
            repro_mcp("repro_op", {"occurrence": binding, "iters": 4302})
    assert caught.value is sentinel
    assert hits
    _assert_descriptors_and_temporaries_gone(tracked)
    assert not any(".tmp" in path.name for path in Path(root).rglob("*"))
    retry = repro_mcp("repro_op", {"occurrence": binding, "iters": 4302})
    assert retry["status"] == "ready"

def test_r14_diff_writer_fsync_timeout_cleans_up_and_retries(
        monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    root = "r14write_diff"
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", root)
    trace = {"total_ms": 2, "ops": [{"name": "R14", "duration_ms": 2}]}
    sentinel = TimeoutError("R14 fsync diff.json")
    tracked, hits, tracked_open, fsync_timeout = _fsync_harness(
        "diff.json", sentinel)
    with patch.object(os, "open", tracked_open), \
            patch.object(os, "fsync", fsync_timeout):
        with pytest.raises(TimeoutError) as caught:
            diff_mcp({"predicted": trace, "captured": trace})
    assert caught.value is sentinel
    assert hits
    _assert_descriptors_and_temporaries_gone(tracked)
    assert not any(".tmp" in path.name for path in Path(root).rglob("*"))
    retry = diff_mcp({"predicted": trace, "captured": trace})
    assert retry["persisted"] is True
    assert retry["retrievable"] is True

@pytest.mark.parametrize("mode", [
    "poll_once", "terminate_persistent", "kill_once", "wait_once",
    "poll_persistent", "kill_persistent", "terminate_then_poll_once",
    "terminate_then_kill_once", "terminate_then_wait_once",
])
def test_r15_supervisor_reaps_before_primary_escapes_with_shared_budget(mode):
    code = ('import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); '
            'print("ready", flush=True); time.sleep(30)')
    children = [subprocess.Popen([sys.executable, "-B", "-c", code],
                                stdout=subprocess.PIPE, text=True) for _ in range(2)]
    primary, secondary = TimeoutError(mode), TimeoutError("cleanup " + mode)
    hits, cleanup_hits, killed = [], [], []
    original = {name: getattr(children[0], name)
                for name in ("poll", "terminate", "kill", "wait")}

    def hook(name, *args, **kwargs):
        fault = mode.split("_")[0]
        if name == fault and (not hits or "persistent" in mode):
            hits.append(name)
            raise primary
        if (mode.startswith("terminate_then_") and hits
                and name == mode.split("_")[2] and not cleanup_hits):
            cleanup_hits.append(name)
            raise secondary
        result = original[name](*args, **kwargs)
        if name == "kill":
            killed.append(True)
        if mode == "wait_once" and name == "poll" and killed and not hits:
            return None  # Reach the normal wait boundary even after a fast reap.
        return result

    try:
        for child in children:
            assert child.stdout.readline().strip() == "ready"
        with contextlib.ExitStack() as stack:
            for name in original:
                stack.enter_context(patch.object(children[0], name,
                    lambda *a, _name=name, **kw: hook(_name, *a, **kw)))
            started = time.monotonic()
            with pytest.raises(TimeoutError) as caught:
                supervise_probe_processes(children, wall_budget_s=.12,
                                          poll_interval_s=.002)
            elapsed = time.monotonic() - started
            codes = [child.returncode for child in children]
        assert elapsed <= .25
        assert hits and caught.value is primary
        assert codes == [-9, -9]  # Before any harness poll/wait or rescue.
        if mode.startswith("terminate_then_"):
            assert cleanup_hits
        for child in children:
            with pytest.raises(ProcessLookupError):
                os.kill(child.pid, 0)
    finally:
        _reap_children(children)
        for child in children:
            child.stdout.close()

def test_r14_supervisor_abort_stat_timeout_reaps_every_child(tmp_path):
    abort = tmp_path / "abort.json"
    abort.write_text(json.dumps(
        {"kind": "abort", "error": "R14 peer abort"}) + "\n",
        encoding="utf-8")
    children = [_sleeper(1), _sleeper(1)]
    sentinel = TimeoutError("R14 supervisor abort stat timeout")
    original = os.stat

    def stat_timeout(path, *args, **kwargs):
        if not isinstance(path, int) and os.fsdecode(path) == str(abort):
            raise sentinel
        return original(path, *args, **kwargs)

    try:
        with patch.object(os, "stat", stat_timeout):
            with pytest.raises(TimeoutError) as caught:
                supervise_probe_processes(
                    children, abort_file=abort, wall_budget_s=1.0,
                    poll_interval_s=0.005)
        assert caught.value is sentinel
        assert all(child.poll() is not None for child in children)
    finally:
        _reap_children(children)

def test_r14_diff_checked_predicates_re_raise_timeout(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "r14diff_pred")
    trace = {"total_ms": 2, "ops": [{"name": "R14", "duration_ms": 2}]}
    lexists_sentinel = TimeoutError("R14 diff lexists timeout")
    original_lstat = os.lstat

    def lstat_timeout(path, *args, **kwargs):
        frame = sys._getframe(1)
        codes = []
        for _ in range(4):
            if frame is None:
                break
            codes.append(frame.f_code)
            frame = frame.f_back
        if (atomic_io.lstat_or_none.__code__ in codes
                and "/diff/" in str(path)):
            raise lexists_sentinel
        return original_lstat(path, *args, **kwargs)

    with patch.object(os, "lstat", lstat_timeout):
        with pytest.raises(TimeoutError) as caught:
            diff_mcp({"predicted": trace, "captured": trace})
    assert caught.value is lexists_sentinel
    isdir_sentinel = TimeoutError("R14 diff is_dir timeout")
    original_stat = os.stat

    def stat_timeout(path, *args, **kwargs):
        frame = sys._getframe(1)
        codes = []
        for _ in range(4):
            if frame is None:
                break
            codes.append(frame.f_code)
            frame = frame.f_back
        if (atomic_io.stat_or_none.__code__ in codes
                and "/diff/" in str(path)):
            raise isdir_sentinel
        return original_stat(path, *args, **kwargs)

    with patch.object(atomic_io, "validate_directory", lambda *a, **k: False):
        with patch.object(os, "stat", stat_timeout):
            with pytest.raises(TimeoutError) as caught:
                diff_trace.resolve_diff_artifact("sha256:" + "a" * 64)
    assert caught.value is isdir_sentinel


@pytest.mark.parametrize("status", ["bound", "blocked"])
@pytest.mark.parametrize("issues", [True, False, 10**5000, 0, "bad", {"code": "bad"}],
    ids=["true", "false", "huge", "zero", "string", "mapping"])
def test_r23_issues_container(status, issues, tmp_path, monkeypatch):
    from mindie_profiler.events import ProfilerUsageError
    from mindie_profiler.token_budget import estimate_tokens
    monkeypatch.chdir(tmp_path)
    binding = paged_binding()
    binding.update(status=status, issues=issues)
    with pytest.raises(ProfilerUsageError, match="issues must be an array"):
        generate_single_op_reproducer(binding)
    result = repro_mcp("repro_op", {"occurrence": binding})
    assert result["status"] == "blocked" and "issues must be an array" in result["reason"]
    assert estimate_tokens(result) <= 250


@pytest.mark.parametrize("storage_value", [True, "bad", [1, 2], None, 0, 10**5000],
    ids=["bool", "string", "array", "none", "zero", "huge"])
def test_r23_storage_container(storage_value):
    from mindie_profiler.events import ProfilerUsageError
    from nr_s6_support import paged_row
    row = paged_row()
    row["input_shapes"] = [dict(shape=json.loads(shape), dtype=row["input_dtypes"][i],
        layout=row["input_formats"][i], storage={}) for i, shape in enumerate(row["input_shapes"])]
    assert generate_single_op_reproducer(registry.bind_captured_occurrence(row))["status"] == "ready"
    row["input_shapes"][0]["storage"] = storage_value
    if storage_value is None:
        # FIX24: explicit null consistently denotes absent storage at all ingress routes.
        assert generate_single_op_reproducer(registry.bind_captured_occurrence(row))["status"] == "ready"
        return
    with pytest.raises(ProfilerUsageError, match="storage must be an object"):
        registry.bind_captured_occurrence(row)


@pytest.mark.parametrize("boundary", ["row", "capture", "topology", "samples_json", "samples_jsonl"])
@pytest.mark.parametrize("object_nesting", [False, True])
def test_r23_deep_json_cli(tmp_path, boundary, object_nesting):
    prefix, suffix = ('{"x":', '}') if object_nesting else ('[', ']')
    text = prefix * 1200 + '0' + suffix * 1200
    data, topo = tmp_path / "deep.json", tmp_path / "topology.json"
    topo.write_text(json.dumps({"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1], "protocol": "HCCS"}]}))
    data.write_text(('{"kind":"abort"}\n' if boundary == "samples_jsonl" else '') + text)
    if boundary in ("row", "capture"):
        args = ["repro-op", "--" + boundary, str(data), "--dry-run"]
    else:
        args = ["fabric-probe", "--world-size", "2", "--ranks-per-node", "2", "--topology",
                str(data if boundary == "topology" else topo)]
        if boundary != "topology":
            args += ["--samples", str(data)]
    result = subprocess.run([sys.executable, "-B", "-m", "mindie_profiler", *args],
        text=True, capture_output=True, timeout=30)
    assert result.returncode in (2, 4) and "Traceback" not in result.stderr
    assert len(result.stderr) < 1500 and "nesting" in result.stderr
    assert sys.get_int_max_str_digits() == 4300


@pytest.mark.parametrize("cyclic", [False, True])
def test_r23_programmatic_depth(cyclic, tmp_path, monkeypatch):
    from mindie_profiler.events import ProfilerUsageError
    from mindie_profiler.repro_values import decode_bounded_json, validate_container_depth
    from mindie_profiler.repro_metadata import synthesize_metadata
    from mindie_profiler.repro_preconditions import precondition_problems
    from mindie_profiler.repro_op import extract_raw_rows
    from mindie_profiler.fabric_probe import build_fabric_probe_plan
    from mindie_profiler.fabric_probe_fit import parse_fabric_probe_samples, fit_calibrated_fabric_profile
    from mindie_profiler.token_budget import estimate_tokens
    monkeypatch.chdir(tmp_path)
    deep = []
    if cyclic:
        deep.append(deep)
    else:
        for _ in range(1200):
            deep = [deep]
    binding = paged_binding()
    binding["unknown"] = deep
    calls = [lambda: generate_single_op_reproducer(binding), lambda: extract_raw_rows(deep),
        lambda: registry.bind_captured_occurrence({"input_shapes": deep}),
        lambda: parse_fabric_probe_samples(deep), lambda: build_fabric_probe_plan(topology={"unknown": deep}),
        lambda: fit_calibrated_fabric_profile({"unknown": deep}, []),
        lambda: synthesize_metadata({"allocations": [], "unknown": deep})]
    for call in calls:
        with pytest.raises(ProfilerUsageError, match="nesting"):
            call()
    assert precondition_problems({"attrs": {"unknown": deep}})
    result = repro_mcp("repro_op", {"occurrence": binding})
    assert result["status"] == "blocked" and estimate_tokens(result) <= 250
    limit, recursion_limit = sys.get_int_max_str_digits(), sys.getrecursionlimit()
    validate_container_depth(decode_bounded_json('[' * 64 + '0' + ']' * 64))
    with pytest.raises(ProfilerUsageError, match="nesting"):
        decode_bounded_json('[' * 65 + '0' + ']' * 65)
    assert decode_bounded_json(json.dumps('[' * 1200 + '\\"' + ']' * 1200)).startswith('[')
    assert (limit, recursion_limit) == (4300, sys.getrecursionlimit())


@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("label", ["true", "false", "text", "array", "zero", "huge", "float", "set", "tuple", "deep"])
def test_r24_bound_storage_ingress(direction, label, tmp_path, monkeypatch):
    import sys
    from mindie_profiler.token_budget import estimate_tokens
    from nr_s6_support import paged_binding
    from mindie_profiler.events import ProfilerUsageError
    from mindie_profiler.repro_op import _compact_occurrence
    from mindie_profiler.repro_values import storage_record, slot_allocations, validate_binding_counts
    from mindie_profiler.repro_metadata import synthesize_metadata
    from mindie_profiler.repro_preconditions import precondition_problems
    assert sys.get_int_max_str_digits() == 4300
    deep = 0
    for _ in range(1200):
        deep = {"nested": deep}
    value = {"true": True, "false": False, "text": "bad", "array": [1, 2], "zero": 0,
        "huge": 10**5000, "float": 1.5, "set": {1, 2}, "tuple": (("strides", [1]),), "deep": deep}[label]
    binding = paged_binding()
    occurrence = _compact_occurrence(binding)
    target = binding[direction][0]
    target["storage"] = value
    next(a for a in occurrence["allocations"] if a["direction"] == direction[:-1])["storage"] = value
    for fn in (lambda: storage_record(target), lambda: slot_allocations(binding),
               lambda: validate_binding_counts(binding), lambda: synthesize_metadata(occurrence),
               lambda: generate_single_op_reproducer(binding)):
        with pytest.raises(ProfilerUsageError) as caught:
            fn()
        assert len(str(caught.value)) < 200
    assert precondition_problems(occurrence)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "r24storage")
    for status in ("bound", "blocked"):
        binding["status"] = status
        result = repro_mcp("repro_op", {"occurrence": binding})
        assert result["status"] == "blocked" and estimate_tokens(result) <= 250
        json.dumps(result, allow_nan=False)
    assert sys.get_int_max_str_digits() == 4300


@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("mode", ["omitted", "none", "mapping"])
def test_r24_absent_storage_consistency(direction, mode):
    from nr_s6_support import paged_binding, paged_row
    from mindie_profiler.repro_op import _compact_occurrence
    from mindie_profiler.repro_metadata import synthesize_metadata
    binding = paged_binding()
    if mode == "omitted":
        binding[direction][0].pop("storage", None)
    else:
        binding[direction][0]["storage"] = None if mode == "none" else {}
    occurrence = _compact_occurrence(binding)
    assert synthesize_metadata(occurrence)["checks"]["metadata_installable"]
    assert generate_single_op_reproducer(binding)["status"] == "ready"
    row = paged_row()
    field = direction[:-1]
    row[field + "_shapes"] = [dict(shape=json.loads(s), dtype=row[field + "_dtypes"][i],
        layout=row[field + "_formats"][i]) for i, s in enumerate(row[field + "_shapes"])]
    if mode != "omitted":
        row[field + "_shapes"][0]["storage"] = None if mode == "none" else {}
    assert generate_single_op_reproducer(registry.bind_captured_occurrence(row))["status"] == "ready"


@pytest.mark.parametrize("direction", ["inputs", "outputs"])
@pytest.mark.parametrize("value", [True, False, "bad", [1, 2], 0, 1.5])
def test_r24_bound_storage_cli(direction, value, tmp_path):
    import subprocess
    import sys
    from nr_s6_support import paged_binding
    binding = paged_binding()
    binding[direction][0]["storage"] = value
    row = tmp_path / "bound.json"
    row.write_text(json.dumps(binding, allow_nan=False))
    run = subprocess.run([sys.executable, "-B", "-m", "mindie_profiler", "repro-op", "--row", str(row),
        "--dry-run"], capture_output=True, text=True, timeout=30)
    assert run.returncode == 2 and "Traceback" not in run.stderr and len(run.stderr) < 1500
