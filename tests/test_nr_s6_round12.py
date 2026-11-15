"""Round-12 ABI/storage and Round-15 writer ownership regressions.

[Role]
  Exercise the four Round-12 findings at their public boundaries: every MCP
  catalog-span continuation page for all 32 entries, the full direct C ABI
  card by name and by span, the deliberate path-omission transition through
  final MCP resolution/generation, and explicit index-persistence failure.
  Also pin post-rename rollback and reader/writer cleanup exception identity.

[Invariants]
  * Every page is receipted, has ``estimate <= 250`` and ``estimate >= real``
    under both shipped tiktoken encodings, and reconstructs the full entry.
  * The direct card exposes catalog-identical ``c_abi_slots`` and
    ``slot_specs`` for both name and span inspection.
  * Unrepresentable paths leave no path key and keep
    ``artifact_path_omitted=True`` through the final MCP wrapper.
  * Malformed or protected ``index.json`` yields an explicit
    ``delivery_failed``/``index_persistence_failed`` result and never
    overwrites the protected bytes.

[Timeouts & Locks]
  In-process filesystem writes under ``tmp_path``; no device or subprocess work.

[Side-Effect Policy]
  Writes only relative roots created under pytest's temporary directory.
"""

from __future__ import annotations

import json
import contextlib
import errno
import os
from pathlib import Path
from mindie_profiler import repro_atomic_io as checked_io
from mindie_profiler import repro_storage as storage
from unittest.mock import patch

import pytest

from mindie_profiler.op_api_registry import (
    call_mcp_tool as registry_mcp, inspect_op_abi, load_catalog,
)
from mindie_profiler.repro_op import (
    call_mcp_tool as repro_mcp, generate_single_op_reproducer,
)
from mindie_profiler.repro_storage import resolve_repro_artifact
from mindie_profiler.token_budget import bounded_envelope, estimate_tokens
from mindie_sim.diff_trace import call_mcp_tool as diff_mcp
from nr_s6_support import paged_binding


def _compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def _encoders():
    tiktoken = pytest.importorskip("tiktoken")
    return [tiktoken.get_encoding(name)
            for name in ("cl100k_base", "o200k_base")]


def _real(value, encoders):
    text = _compact(value)
    return max(len(encoder.encode(text, disallowed_special=()))
               for encoder in encoders)


def _assign(root, path, value):
    if not path:
        if isinstance(value, dict):
            root.update(value)
        return
    node = root
    for position, token in enumerate(path[:-1]):
        following = path[position + 1]
        if isinstance(token, int):
            while len(node) <= token:
                node.append(None)
            if node[token] is None:
                node[token] = [] if isinstance(following, int) else {}
            node = node[token]
        else:
            child = node.get(token)
            if not isinstance(child, (dict, list)):
                child = [] if isinstance(following, int) else {}
                node[token] = child
            node = child
    last = path[-1]
    if isinstance(last, int):
        while len(node) <= last:
            node.append(None)
        node[last] = value
    else:
        node[last] = value


def _reassemble(pages):
    root = {}
    segments = {}
    for page in pages:
        for unit in page["items"]:
            path, value = unit[0], unit[1]
            if len(unit) == 3:
                segments.setdefault(tuple(path), {})[unit[2]] = value
            else:
                _assign(root, path, value)
    for path, parts in segments.items():
        _assign(root, list(path),
                "".join(parts[offset] for offset in sorted(parts)))
    return root


def _pages(name, artifact):
    page = registry_mcp("inspect_op_abi", {
        "span": artifact["span"],
        "catalog_sha256_16": artifact["catalog_sha256_16"]})
    pages = []
    while True:
        pages.append(page)
        if page["next_page"] is None:
            return pages
        assert page["next_page"] == page["page"] + 1
        page = registry_mcp("inspect_op_abi", {
            "span": artifact["span"],
            "catalog_sha256_16": artifact["catalog_sha256_16"],
            "page": page["next_page"]})


def test_r12_mcp_span_pages_are_bounded_receipted_and_lossless():
    encoders = _encoders()
    document = load_catalog()
    total = 0
    for name, entry in document["operators"].items():
        compact = registry_mcp("inspect_op_abi", {"op_name": name})
        artifact = compact["artifact"]
        pages = _pages(name, artifact)
        assert pages[0]["api"] == name
        for page in pages:
            assert page["schema"] == "mindie-op-abi-card/2"
            assert page["next"] == page["next_page"] == page["cursor"]
            assert page["artifact"] == artifact
            assert "receipt" in page
            assert page["receipt"]["within_budget"] is True
            assert page["receipt"]["tokenizer"] == "b3"
            estimate = estimate_tokens(page)
            real = _real(page, encoders)
            assert estimate <= 250
            assert real <= 250
            assert estimate >= real
            assert page["receipt"]["token_estimate"] == estimate_tokens(
                {key: value for key, value in page.items() if key != "receipt"})
        assert _reassemble(pages) == entry
        total += len(pages)
    assert total > 32


def test_r12_direct_card_exposes_catalog_c_abi_slots_and_slot_specs():
    for name, entry in load_catalog()["operators"].items():
        named = inspect_op_abi(name)
        span = named["artifact"]
        via_span = inspect_op_abi(
            span=span["span"],
            catalog_sha256_16=span["catalog_sha256_16"])
        for card in (named["card"], via_span["card"]):
            assert card["c_abi_slots"] == entry["c_abi_slots"]
            assert card["slot_specs"] == entry["c_abi_slots"]["slot_specs"]
            assert [item.get("declared_type") for item in
                    card["c_abi_slots"]["parameters"]][:1] == [
                item.get("declared_type") for item in
                entry["c_abi_slots"]["parameters"]][:1]
            for key in ("api", "abi_id", "inputs", "outputs", "attrs",
                        "recipe", "padding_semantics", "qualification"):
                assert key in card
        assert named["card"]["c_abi_slots"] == via_span["card"]["c_abi_slots"]
        assert named["receipt"]["within_budget"] is True


def test_r12_path_transition_deletes_keys_and_keeps_marker(monkeypatch,
                                                           tmp_path):
    long_path = "/tmp/" + "x" * 4096 + "/repro.py"
    envelope = bounded_envelope({
        "schema": "s", "status": "ready", "artifact_path": long_path,
        "manifest_path": long_path.replace("repro.py", "manifest.json"),
        "retrievable": True, "resolved": True,
        "artifact": {"retrievable": True}}, limit=250)
    assert envelope["status"] == "delivery_blocked"
    assert envelope["error"] == "artifact_paths_not_representable"
    assert envelope["artifact_path_omitted"] is True
    assert "artifact_path" not in envelope
    assert "manifest_path" not in envelope
    assert envelope["retrievable"] is False
    assert estimate_tokens(envelope) <= 250

    monkeypatch.chdir(tmp_path)
    root = Path("r" * 48)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", str(root))
    generated = generate_single_op_reproducer(
        paged_binding(), iters=403, stage=True)
    assert generated["status"] == "ready"
    assert resolve_repro_artifact(generated["sha256"])["resolved"] is True
    resolved = repro_mcp("repro_op",
                         {"resolve_artifact_id": generated["sha256"]})
    assert resolved["status"] == "delivery_blocked"
    assert resolved["error"] == "artifact_paths_not_representable"
    assert resolved["artifact_path_omitted"] is True
    assert resolved["resolved"] is False
    assert resolved["retrievable"] is False
    assert "artifact_path" not in resolved
    assert "manifest_path" not in resolved
    assert estimate_tokens(resolved) <= 250
    wrapped = repro_mcp("repro_op", {"occurrence": paged_binding(),
                                     "iters": 5})
    assert wrapped["status"] == "delivery_blocked"
    assert wrapped["artifact_path_omitted"] is True
    assert "artifact_path" not in wrapped
    assert "manifest_path" not in wrapped


def test_r12_index_failure_is_explicit_and_protected_bytes_survive(
        monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    trace = {"total_ms": 2, "ops": [{"name": "A", "duration_ms": 2}]}
    # Positive control: three ordinary handles are all in the persisted index.
    normal = Path("normal")
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", str(normal))
    handles = []
    for iters in (5, 7, 9):
        result = repro_mcp("repro_op", {"occurrence": paged_binding(),
                                        "iters": iters})
        assert result["status"] == "ready"
        handles.append(result["artifact_id"])
    index = json.loads((normal / "index.json").read_text())
    assert set(handles) <= set(index)

    for mode in ("invalid_json", "symlink", "directory", "hardlink_script",
                 "hardlink_manifest", "hardlink_diff"):
        root = Path("idx_" + mode)
        monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", str(root))
        first = generate_single_op_reproducer(
            paged_binding(), iters=320, stage=True)
        assert first["status"] == "ready"
        assert first["index_persisted"] is True
        index_path = root / "index.json"
        index_path.unlink()
        target = None
        if mode == "invalid_json":
            index_path.write_text("{")
        elif mode == "directory":
            index_path.mkdir()
        else:
            key = ("short_manifest_path" if mode == "hardlink_manifest"
                   else "short_artifact_path")
            target = Path(first["storage"][key])
            if mode == "hardlink_diff":
                diff = diff_mcp({"predicted": trace, "captured": trace})
                target = Path(diff["artifact_path"])
            if mode == "symlink":
                index_path.symlink_to(target)
            else:
                os.link(target, index_path)
        before = target.read_bytes() if target else None
        second = generate_single_op_reproducer(
            paged_binding(), iters=321, stage=True)
        third = generate_single_op_reproducer(
            paged_binding(), iters=322, stage=True)
        for result in (second, third):
            assert result["status"] == "delivery_failed"
            assert result["error"] == "index_persistence_failed"
            assert result["index_persisted"] is False
            assert result["index_warning"] == "index_persistence_failed"
            assert result["storage"]["status"] == "delivery_failed"
        assert resolve_repro_artifact(first["sha256"])["resolved"] is True
        assert resolve_repro_artifact(second["sha256"])["resolved"] is True
        if mode == "invalid_json":
            assert index_path.read_text() == "{"
        elif mode == "directory":
            assert checked_io.path_is_dir(index_path)
        else:
            assert target is not None
            assert checked_io.path_is_symlink(index_path) or index_path.stat().st_nlink > 1
            assert target.read_bytes() == before
        wrapped = repro_mcp("repro_op", {"occurrence": paged_binding(),
                                         "iters": 323})
        assert wrapped["status"] == "delivery_failed"
        assert wrapped["error"] == "index_persistence_failed"
        assert wrapped["index_persisted"] is False
        assert wrapped["index_warning"] == "index_persistence_failed"
        assert wrapped["receipt"]["within_budget"] is True
        assert estimate_tokens(wrapped) <= 250


@pytest.mark.parametrize("leaf", ["repro.py", "manifest.json"])
@pytest.mark.parametrize("fault", [
    "read_temp", "read_dest", "close_temp", "close_dest", "dual_temp", "dual_dest",
    "fsync_close", "fsync_unlink", "fsync_lstat", "pair_unlink", "pair_lstat",
])
def test_r15_writer_rollback_reader_identity_and_retry(leaf, fault, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    binding = paged_binding()
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "history")
    old = generate_single_op_reproducer(binding, iters=5100, stage=True)
    historical = {Path(old["storage"][key]): Path(old["storage"][key]).read_bytes()
                  for key in ("short_artifact_path", "short_manifest_path")}
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "fresh")
    primary, secondary = TimeoutError(fault), TimeoutError("cleanup " + fault)
    original = {name: getattr(os, name)
                for name in ("open", "fstat", "read", "close", "fsync", "unlink", "lstat")}
    fds, hits = {}, []

    def opened(path, flags, *args, **kwargs):
        fd = original["open"](path, flags, *args, **kwargs)
        st = original["fstat"](fd)
        fds[fd] = (Path(path), flags, (st.st_dev, st.st_ino))
        return fd

    def syscall(name, arg, *args, **kwargs):
        path, flags, _ = fds.get(arg, (Path("absent"), 0, None)) if isinstance(
            arg, int) else (Path(arg), 0, None)
        path = Path(os.path.abspath(path))
        selected = (tmp_path / "fresh") in path.parents
        temp = path.name.startswith("." + leaf + ".")
        dest = path.name == leaf
        reader = not flags & os.O_WRONLY and selected
        phase = temp if fault.endswith("temp") else dest
        if not hits and selected and (
                (name == "fsync" and fault.startswith("fsync_") and temp)
                or (reader and phase and name == "read" and fault.startswith(("read_", "dual_")))
                or (reader and phase and name == "close" and fault.startswith("close_"))):
            hits.append("primary")
            raise primary
        cleanup = ("close" if fault.startswith("dual_") else fault.split("_")[-1])
        if (hits == ["primary"] and selected and name == cleanup
                and (temp or dest) and fault.startswith(("dual_", "fsync_", "pair_"))):
            hits.append("secondary")
            raise secondary
        return original[name](arg, *args, **kwargs)

    verify = storage._verify_pair_bytes

    def pair_check(*args, **kwargs):
        if fault.startswith("pair_") and not hits:
            hits.append("primary")
            raise primary
        return verify(*args, **kwargs)

    request = {"occurrence": binding, "iters": 5101}
    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(os, "open", opened))
        stack.enter_context(patch.object(storage, "_verify_pair_bytes", pair_check))
        for name in ("read", "close", "fsync", "unlink", "lstat"):
            stack.enter_context(patch.object(os, name,
                lambda arg, *a, _name=name, **kw: syscall(_name, arg, *a, **kw)))
        with pytest.raises(TimeoutError) as caught:
            repro_mcp("repro_op", request)
    assert hits and caught.value is primary
    if fault.startswith(("dual_", "fsync_", "pair_")):
        assert hits == ["primary", "secondary"]
    for fd in fds:
        with pytest.raises(OSError) as closed:
            original["fstat"](fd)
        assert closed.value.errno == errno.EBADF
    assert not any(checked_io.path_is_file(p) for p in Path("fresh").rglob("*"))
    assert {p: p.read_bytes() for p in historical} == historical
    assert resolve_repro_artifact(old["sha256"])["resolved"] is True
    assert repro_mcp("repro_op", request)["status"] == "ready"


@pytest.mark.parametrize("kind", ["protected", "replaced", "symlink"])
def test_r15_rollback_never_unlinks_an_unowned_inode(kind, tmp_path):
    target, replacement = tmp_path / "leaf", tmp_path / "replacement"
    target.write_bytes(b"owned")
    installed = checked_io.inode_of(target)
    replacement.write_bytes(b"protected")
    protected = {checked_io.inode_of(replacement)}
    if kind == "protected":
        protected.add(installed)
    elif kind == "replaced":
        os.replace(replacement, target)
    else:
        target.unlink()
        target.symlink_to(replacement)
    before = target.read_bytes()
    checked_io._unlink_owned_path(target, installed, protected=protected)
    assert target.read_bytes() == before


@pytest.mark.parametrize("operation", ["close", "unlink"])
def test_r15_cleanup_retries_keep_first_fault_even_after_kernel_success(operation, tmp_path):
    path = tmp_path / "owned"
    fd = os.open(path, os.O_CREAT | os.O_WRONLY, 0o600)
    sentinel, hits = TimeoutError("after kernel success"), []
    original = getattr(os, operation)

    def completed_then_timeout(arg):
        hits.append(arg)
        original(arg)
        raise sentinel

    if operation == "unlink":
        os.close(fd)
    with patch.object(os, operation, completed_then_timeout):
        with pytest.raises(TimeoutError) as caught:
            if operation == "close":
                checked_io._close_owned_fd(fd, active_exc=None)
            else:
                checked_io._unlink_owned_path(path, checked_io.inode_of(path))
    assert caught.value is sentinel
    with pytest.raises(OSError) as closed:
        os.fstat(fd)
    assert closed.value.errno == errno.EBADF
    if operation == "unlink":
        assert checked_io.lstat_or_none(path) is None
    assert len(hits) == 1  # A completed raw close loses its receipt; never retry blindly.


def test_r15_reader_close_is_primary_inside_a_callers_exception_handler(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "handled")
    primary, hits = TimeoutError("reader close"), []
    original_open, original_close = os.open, os.close
    readers = set()

    def opened(path, flags, *args, **kwargs):
        fd = original_open(path, flags, *args, **kwargs)
        if not flags & os.O_WRONLY and Path(path).name == "repro.py":
            readers.add(fd)
        return fd

    def close(fd):
        if fd in readers and not hits:
            hits.append(fd)
            raise primary
        return original_close(fd)

    request = {"occurrence": paged_binding(), "iters": 5102}
    try:
        raise ValueError("already handled by caller")
    except ValueError:
        with patch.object(os, "open", opened), patch.object(os, "close", close):
            with pytest.raises(TimeoutError) as caught:
                repro_mcp("repro_op", request)
        assert caught.value is primary and hits
    assert not any(checked_io.path_is_file(p) for p in Path("handled").rglob("*"))
    for fd in readers:
        with pytest.raises(OSError):
            os.fstat(fd)
    assert repro_mcp("repro_op", request)["status"] == "ready"


@pytest.mark.parametrize("latency", [1e-300, 1e-305, 1e-308, 1e-309, 1e-310, 1e-312, 1e-320, 5e-324])
@pytest.mark.parametrize("parsed", [False, True])
def test_r23_tiny_latency_rejected(latency, parsed):
    from mindie_profiler.events import ProfilerUsageError
    from mindie_profiler.fabric_probe import build_fabric_probe_plan
    from mindie_profiler.fabric_probe_fit import parse_fabric_probe_samples, fit_calibrated_fabric_profile
    plan = build_fabric_probe_plan(world_size=2, ranks_per_node=2,
        topology={"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1], "protocol": "HCCS"}]})
    samples = [dict(tier="intra_node_hccs", op="all_reduce", bytes=b, latency_us=1.,
        rank=0, group_size=2, group_ranks=[0, 1], protocol="HCCS", validated=True) for b in (4096, 8192)]
    if parsed:
        samples = parse_fabric_probe_samples(samples)
    for i, sample in enumerate(samples):
        sample["latency_us"] = latency * (i + 1)
    for call in (lambda: parse_fabric_probe_samples(samples), lambda: fit_calibrated_fabric_profile(plan, samples)):
        with pytest.raises(ProfilerUsageError, match="latency_us"):
            call()


@pytest.mark.parametrize("jsonl", [False, True])
@pytest.mark.parametrize("ratio", [False, True])
def test_r23_fit_cli_rejects_nonfinite_derivation(tmp_path, jsonl, ratio):
    import subprocess
    import sys
    from mindie_profiler.events import ProfilerUsageError
    from mindie_profiler.fabric_probe import build_fabric_probe_plan
    from mindie_profiler.fabric_probe_fit import fit_calibrated_fabric_profile
    topology = {"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1], "protocol": "HCCS"}]}
    plan = build_fabric_probe_plan(world_size=2, ranks_per_node=2, topology=topology)
    samples = [dict(tier="intra_node_hccs", op="all_reduce", bytes=b, latency_us=latency,
        rank=0, group_size=2, group_ranks=[0, 1], protocol="HCCS", validated=True, regime=regime)
        for b in (4096, 8192) for regime, latency in
        (("isolated", 1e-300), ("loaded", 1e12)) if ratio or regime == "isolated"]
    with pytest.raises(ProfilerUsageError):
        fit_calibrated_fabric_profile(plan, samples)
    topo, data = tmp_path / "topology.json", tmp_path / "samples.json"
    topo.write_text(json.dumps(topology))
    data.write_text("\n".join(map(json.dumps, samples)) if jsonl else json.dumps(samples))
    run = subprocess.run([sys.executable, "-B", "-m", "mindie_profiler", "fabric-probe",
        "--world-size", "2", "--ranks-per-node", "2", "--topology", str(topo), "--samples", str(data)],
        text=True, capture_output=True, timeout=30)
    assert run.returncode in (2, 4) and "Traceback" not in run.stderr
    assert "Infinity" not in run.stdout and "NaN" not in run.stdout
    # Both endpoints of the supported interval retain finite strict JSON output.
    for i, sample in enumerate(samples):
        sample["latency_us"] = 1e-6 if sample["regime"] == "isolated" else 1e12
    result = fit_calibrated_fabric_profile(plan, samples)
    assert result["status"] == "calibrated" and result["usable_for_link_override"]
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("parsed", [False, True])
@pytest.mark.parametrize("ratio", [False, True])
def test_r24_published_positive_fit(parsed, ratio, tmp_path):
    import math
    import subprocess
    import sys
    from mindie_profiler.fabric_probe import build_fabric_probe_plan
    from mindie_profiler.fabric_probe_fit import parse_fabric_probe_samples, fit_calibrated_fabric_profile
    assert sys.get_int_max_str_digits() == 4300
    topology = {"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1], "protocol": "HCCS"}]}
    plan = build_fabric_probe_plan(world_size=2, ranks_per_node=2, topology=topology)
    samples = [dict(tier="intra_node_hccs", op="all_reduce", bytes=b,
        latency_us=(1e12 if regime == "isolated" else 1e-6) if ratio else (i + 1) * 1e11,
        rank=0, group_size=2, group_ranks=[0, 1], protocol="HCCS", validated=True, regime=regime)
        for i, b in enumerate((4096, 8192)) for regime in (("isolated", "loaded") if ratio else ("isolated",))]
    if parsed:
        samples = parse_fabric_probe_samples(samples)
    profiles = [json.loads(json.dumps(fit_calibrated_fabric_profile(plan, samples), allow_nan=False))]
    topo = tmp_path / "topology.json"
    topo.write_text(json.dumps(topology))
    for fmt in ("json", "jsonl"):
        data = tmp_path / ("samples." + fmt)
        data.write_text(json.dumps(samples, allow_nan=False) if fmt == "json" else
            "\n".join(json.dumps(s, allow_nan=False) for s in samples) + "\n")
        run = subprocess.run([sys.executable, "-B", "-m", "mindie_profiler", "fabric-probe", "--world-size", "2",
            "--ranks-per-node", "2", "--topology", str(topo), "--samples", str(data)],
            text=True, capture_output=True, timeout=30)
        assert run.returncode == 0 and not run.stderr and "NaN" not in run.stdout and "Infinity" not in run.stdout
        profiles.append(json.loads(run.stdout))
    for profile in profiles:
        assert profile["status"] == "calibrated" and profile["usable_for_link_override"]
        block = profile["tiers"]["intra_node_hccs"]["operations"]["all_reduce"]
        if ratio:
            assert block["congestion_factor"] > 0 and math.isclose(block["congestion_factor"], 1e-18, rel_tol=1e-12)
        else:
            fit = block["conditions"][0]
            assert fit["bandwidth_gbps"] > 0 and math.isclose(fit["bandwidth_gbps"], 4.096e-11, rel_tol=1e-12)
            assert math.isclose(fit["bandwidth_gbps"] * fit["beta_ns_per_byte"], 1., rel_tol=1e-12)
    assert sys.get_int_max_str_digits() == 4300


@pytest.mark.parametrize("field,value", [("bandwidth_gbps", 0.), ("bandwidth_gbps", -1.),
    ("bandwidth_gbps", 2.), ("congestion_factor", 0.), ("congestion_factor", -1.), ("congestion_factor", 2.)])
def test_r24_published_fit_rejects_unsuitable_values(field, value):
    from mindie_profiler.events import ProfilerUsageError
    from mindie_profiler.fabric_probe_fit import _published_profile
    profile = {"alpha_us": 0., "beta_ns_per_byte": 1., "bandwidth_gbps": 1., "congestion_factor": 1.,
        "congestion_evidence": {"bytes": 4096, "isolated": {"alpha_us": 0., "beta_ns_per_byte": 1.},
            "loaded": {"alpha_us": 0., "beta_ns_per_byte": 1.}}}
    profile[field] = value
    with pytest.raises(ProfilerUsageError, match="published fabric"):
        _published_profile(profile)




from nr_s6_support import KeyMapping, key_fixture, paged_row
from mindie_profiler.repro_values import bounded_mapping, bounded_sequence, diagnostic_value, validate_container_depth


@pytest.mark.parametrize("kind", ["counted", "billion", "list", "dict", "frozenset", "str_subclass"])
def test_r27_diagnostic_key_projection(kind):
    key, calls = key_fixture(kind)
    result = diagnostic_value(KeyMapping(key))
    if kind in ("counted", "billion"):
        assert result == "<container exceeds diagnostic limit>"
    else:
        assert isinstance(result, dict) and all(type(k) is str for k in result)
    assert len(json.dumps(result)) < 1024
    assert calls == {"hash": 0, "eq": 0}


@pytest.mark.parametrize("kind", ["counted", "billion"])
def test_r27_key_dag_traversal(kind):
    from mindie_profiler.events import ProfilerUsageError
    from mindie_profiler.repro_values import validate_json_integers
    key, calls = key_fixture(kind)
    for validate in (validate_container_depth, validate_json_integers):
        with pytest.raises(ProfilerUsageError, match="traversal"):
            validate(KeyMapping(key))
    assert calls == {"hash": 0, "eq": 0}


@pytest.mark.parametrize("kind", ["list", "tuple", "mapping", "set", "frozenset"])
def test_r27_container_key_depth(kind):
    from mindie_profiler.events import ProfilerUsageError
    key = 0
    for _ in range(64):
        key = [key] if kind == "list" else {"key": key} if kind == "mapping" else (key,)
    if kind in ("set", "frozenset"):
        key = {key} if kind == "set" else frozenset((key,))
    with pytest.raises(ProfilerUsageError, match="nesting"):
        validate_container_depth(KeyMapping(key))


def test_r27_key_and_value_share_one_budget():
    from mindie_profiler.events import ProfilerUsageError
    with pytest.raises(ProfilerUsageError, match="traversal"):
        validate_container_depth(KeyMapping((None,) * 500_000, [None] * 500_000))


@pytest.mark.parametrize("kind", ["list", "dict"])
def test_r27_unhashable_mapping_protocol(kind):
    from mindie_profiler.events import ProfilerUsageError
    key, _ = key_fixture(kind)
    value = KeyMapping(key, callback=lambda: hash(key))
    with pytest.raises(ProfilerUsageError):
        validate_container_depth(value)
    assert isinstance(diagnostic_value(value), str)
    with pytest.raises(ProfilerUsageError):
        bounded_mapping(value)


@pytest.mark.parametrize("kind", ["counted", "billion", "frozenset", "list", "dict", "str_subclass", "int", "tuple"])
def test_r27_outer_mapping_keys(kind, tmp_path, monkeypatch, capsys):
    from mindie_profiler.events import ProfilerUsageError
    from mindie_profiler.__main__ import main as cli
    from mindie_profiler.op_api_registry import bind_captured_occurrence, call_mcp_tool as registry_tool
    from mindie_profiler.repro_op import call_mcp_tool, generate_single_op_reproducer
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    key, calls = key_fixture(kind)
    binding = KeyMapping(key, prefix=paged_binding())
    raw = KeyMapping(key, prefix=paged_row())
    for call in (lambda: bind_captured_occurrence(raw), lambda: generate_single_op_reproducer(binding, output_dir="caller")):
        with pytest.raises(ProfilerUsageError):
            call()
    for tool in (call_mcp_tool, registry_tool):
        for args in (KeyMapping(key, prefix={"occurrence": paged_binding()}), {"occurrence": binding}):
            result = tool("repro_op", args)
            assert result["status"] == "blocked" and "artifact_id" not in result
    for wrapper in ("ops", "kernels", "occurrences", "operator_rows", "operators", "rows"):
        payload = KeyMapping(key, prefix={wrapper: [paged_row()]})
        monkeypatch.setattr("mindie_profiler.repro_op.load_cli_json", lambda path: payload)
        for mode in (["--dry-run"], ["--output-dir", "caller"]):
            assert cli(["repro-op", "--capture", "virtual.json", *mode]) == 2
            assert "Traceback" not in capsys.readouterr().err
    assert calls == {"hash": 0, "eq": 0}
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("key", ["", "1", "null", "界", "__hash__"])
def test_r27_exact_string_key_controls(key, tmp_path, monkeypatch, capsys):
    from mindie_profiler.repro_op import call_mcp_tool, generate_single_op_reproducer
    from mindie_profiler.op_api_registry import bind_captured_occurrence
    from test_nr_s6_round25 import _raw, _load_script, _envelope
    from mindie_profiler.__main__ import main as cli
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    value = KeyMapping(key, [None, {"leaf": [1, "x"]}])
    assert bounded_mapping(value) == {key: [None, {"leaf": [1, "x"]}]}
    assert bounded_sequence([value], "array") == [{key: [None, {"leaf": [1, "x"]}]}]
    for direction in ("inputs", "outputs"):
        binding = paged_binding()
        binding[direction][0]["storage"] = {"storage_id": value}
        for index, bound in enumerate((binding, bind_captured_occurrence(_raw(direction, {"storage_id": value})))):
            result = generate_single_op_reproducer(bound, output_dir=f"caller_{direction}_{index}")
            assert result["status"] == "ready"
            _load_script(Path(result["output_path"]))
            envelope = call_mcp_tool("repro_op", {"occurrence": bound})
            _envelope(envelope)
            assert envelope["status"] == "ready"
    for wrapper in ("ops", "kernels", "occurrences", "operator_rows", "operators", "rows"):
        payload = KeyMapping(key, prefix={wrapper: [paged_row()]})
        monkeypatch.setattr("mindie_profiler.repro_op.load_cli_json", lambda path: payload)
        for mode in (["--dry-run"], ["--output-dir", f"capture_{wrapper}"]):
            assert cli(["repro-op", "--capture", "virtual.json", *mode]) == 0
            assert not capsys.readouterr().err
