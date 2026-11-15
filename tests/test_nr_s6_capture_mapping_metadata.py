"""Capture envelope metadata parity across mutable and read-only carriers.

[Role]
  Exercise capture wrappers, version aliases and immutable raw-row UID selection.
[Invariants]
  One bounded ingress snapshot supplies rows and metadata without caller mutation.
  Rejected inputs publish nothing; list and tuple captures remain supported.
[Timeouts & Locks]
  Callback timeouts propagate by exact identity; script help is bounded to 30 s.
[Side-Effect Policy]
  Files are confined to pytest temporary directories; no device work is performed.
"""

import copy
import hashlib
import json
import subprocess
import sys
from collections import Counter, UserDict
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import pytest

from mindie_profiler import repro_op as op
from mindie_profiler.__main__ import main as cli
from nr_s6_support import paged_row


WRAPPERS = ("ops", "kernels", "occurrences", "operator_rows", "operators", "rows")
CARRIERS = ("dict", "userdict", "proxy", "readonly")


class ReadOnly(Mapping):
    def __init__(self, data):
        self.data = data
        self.iterations = 0
        self.reads = Counter()

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        self.iterations += 1
        return iter(self.data)

    def __getitem__(self, key):
        self.reads[key] += 1
        return self.data[key]


def _wrap(data, carrier):
    return {"dict": dict, "userdict": UserDict, "proxy": MappingProxyType,
            "readonly": ReadOnly}[carrier](data)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")


def _call(payload, mode, monkeypatch, capsys, *selectors):
    monkeypatch.setattr(op, "load_cli_json", lambda path: payload)
    flags = ["--dry-run"] if mode == "dry" else ["--output-dir", "out"]
    rc = cli(["repro-op", "--capture", "virtual.json", *selectors, *flags])
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


_VERIFIED_AFFIXES: set[tuple[str, str]] = set()
_OCC_PREFIX = "\nOCCURRENCE = "
_OCC_SUFFIX = '\n\nclass ProfilerUsageError(ValueError):\n    """Invalid standalone resource request."""'


def _ready(result, mode, index, tmp_path):
    import ast
    rc, stdout, stderr = result
    assert rc == 0 and not stderr, (rc, stdout, stderr)
    receipt = json.loads(stdout)
    if mode == "dry":
        assert receipt["occurrence_index"] == index
        assert receipt["repro_status"] == "ready" and not receipt["failed_checks"]
        assert not list(tmp_path.iterdir())
    else:
        assert receipt["status"] == "ready"
        manifest = json.loads(Path("out/manifest.json").read_text())
        assert manifest["cann_version"] == "8.0"
        path = Path("out/repro.py")
        raw_bytes = path.read_bytes()
        source_text = raw_bytes.decode("utf-8")
        p_idx = source_text.find(_OCC_PREFIX)
        s_idx = source_text.rfind(_OCC_SUFFIX)
        affix = (source_text[:p_idx], source_text[s_idx:]) if p_idx >= 0 and s_idx > p_idx else None
        if affix is not None and affix in _VERIFIED_AFFIXES:
            ast.literal_eval(source_text[p_idx + len(_OCC_PREFIX):s_idx])
            return
        namespace = {"__name__": "capture_metadata_control"}
        exec(compile(raw_bytes, str(path), "exec"), namespace)
        run = subprocess.run([sys.executable, "-B", str(path), "--help"],
                             capture_output=True, text=True, timeout=30)
        assert run.returncode == 0 and "usage:" in run.stdout and not run.stderr
        if affix is not None:
            _VERIFIED_AFFIXES.add(affix)


def _once(view):
    assert view.iterations == 1
    assert view.reads == Counter({key: 1 for key in view.data})


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("version_key", ("cann_version", "cann_release"))
@pytest.mark.parametrize("run_key", ("run_id", "capture_id"))
@pytest.mark.parametrize("carrier", CARRIERS)
@pytest.mark.parametrize("mode", ("dry", "caller"))
def test_capture_envelope_version_and_derived_uid(wrapper, version_key, run_key,
                                                 carrier, mode, tmp_path,
                                                 monkeypatch, capsys):
    row = paged_row(rank=3, step=7, stream=2, abi_sha256="captured-abi")
    row.pop("cann_version")
    before = copy.deepcopy(row)
    nested = ReadOnly(row)
    rows = [None, {"op_type": "host_launch"}, nested]
    data = {wrapper: rows, version_key: "8.0", run_key: "capture-metadata"}
    payload = _wrap(data, carrier)
    uid = op._row_uid("capture-metadata", row, 2)
    _ready(_call(payload, mode, monkeypatch, capsys, "--op-uid", uid), mode, 2, tmp_path)
    _once(nested)
    if carrier == "readonly":
        _once(payload)
    assert row == before and data[wrapper] is rows and rows[2] is nested
    assert payload[wrapper] is rows and dict(payload) == data
    assert "cann_version" not in row and "op_uid" not in row


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("version_key", ("cann_version", "cann_release"))
@pytest.mark.parametrize("carrier", CARRIERS)
@pytest.mark.parametrize("mode", ("dry", "caller"))
def test_capture_version_only_envelope(wrapper, version_key, carrier, mode,
                                       tmp_path, monkeypatch, capsys):
    row = paged_row()
    row.pop("cann_version")
    data = {wrapper: [row], version_key: "8.0"}
    before = copy.deepcopy(data)
    payload = _wrap(data, carrier)
    _ready(_call(payload, mode, monkeypatch, capsys), mode, 0, tmp_path)
    assert data == before and payload[wrapper][0] is row


@pytest.mark.parametrize("sequence", (list, tuple))
@pytest.mark.parametrize("carrier", CARRIERS)
@pytest.mark.parametrize("mode", ("dry", "caller"))
def test_sequence_capture_controls(sequence, carrier, mode, tmp_path, monkeypatch, capsys):
    row = paged_row()
    before = copy.deepcopy(row)
    nested = _wrap(row, carrier)
    payload = sequence([nested])
    uid = op._row_uid("run", row, 0)
    _ready(_call(payload, mode, monkeypatch, capsys, "--op-uid", uid), mode, 0, tmp_path)
    assert row == before and payload[0] is nested


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("carrier", CARRIERS)
def test_public_extractor_snapshots_mapping_and_tuple_rows(wrapper, carrier):
    row = paged_row()
    before = copy.deepcopy(row)
    view = ReadOnly(row)
    payload = _wrap({wrapper: (None, {"op_type": "host"}, view)}, carrier)
    rows = op.extract_raw_rows(payload)
    assert rows == [{}, {"op_type": "host"}, before]
    _once(view)
    rows[2]["attrs"]["num_heads"] = 1
    assert row == before


@pytest.mark.parametrize("carrier", CARRIERS)
@pytest.mark.parametrize("mode", ("dry", "caller"))
@pytest.mark.parametrize("fault", ("key", "deep", "wide", "version", "uid", "mismatch"))
def test_rejected_capture_does_not_publish(carrier, mode, fault, tmp_path,
                                          monkeypatch, capsys):
    row = paged_row()
    row.pop("cann_version")
    data = {"rows": [None, row], "cann_release": "8.0", "capture_id": "source"}
    uid = op._row_uid("source", row, 1)
    selectors = ["--op-uid", uid]
    if fault == "key":
        data[("bad",)] = None
    elif fault == "deep":
        value = []
        for _ in range(64):
            value = [value]
        data["extra"] = value
    elif fault == "wide":
        class Wide(ReadOnly):
            def __len__(self):
                return 1_000_001

            def __iter__(self):
                pytest.fail("over-budget capture must be rejected before iteration")

        data["extra"] = Wide({})
    elif fault == "version":
        data["cann_release"] = "unsupported"
    elif fault == "uid":
        selectors = ["--op-uid", op._row_uid("other-source", row, 1)]
    else:
        data["rows"][0] = paged_row()
        selectors += ["--occurrence-index", "0"]
    payload = _wrap(data, carrier)
    rc, out, err = _call(payload, mode, monkeypatch, capsys, *selectors)
    assert rc == (4 if fault == "version" else 2)
    assert "Traceback" not in out + err
    assert not list(tmp_path.iterdir())
    assert payload["rows"] is data["rows"] and data["rows"][1] is row


class Deadline(TimeoutError):
    pass


@pytest.mark.parametrize("mode", ("dry", "caller"))
@pytest.mark.parametrize("site", ("len", "iter", "getitem", "cann_version", "run_id"))
@pytest.mark.parametrize("error_type", (TimeoutError, Deadline, TypeError))
@pytest.mark.parametrize("placement", ("envelope", "nested"))
def test_capture_callback_errors(mode, site, error_type, placement,
                                 tmp_path, monkeypatch, capsys):
    sentinel = error_type("capture callback")
    reached = []

    class Fault(ReadOnly):
        def fail(self, callback):
            if site == callback:
                reached.append(callback)
                raise sentinel

        def __len__(self):
            self.fail("len")
            return super().__len__()

        def __iter__(self):
            self.fail("iter")
            return super().__iter__()

        def __getitem__(self, key):
            self.fail("getitem")
            self.fail(key)
            return super().__getitem__(key)

    data = {"ops": [paged_row()], "cann_version": "8.0", "run_id": "source"}
    payload = Fault(data)
    if placement == "nested":
        payload = MappingProxyType({**data, "extra": payload})
    if issubclass(error_type, TimeoutError):
        with pytest.raises(TimeoutError) as caught:
            _call(payload, mode, monkeypatch, capsys)
        assert caught.value is sentinel
    else:
        rc, out, err = _call(payload, mode, monkeypatch, capsys)
        assert rc == 2 and "Traceback" not in out + err
    assert reached == [site]
    assert not list(tmp_path.iterdir())
