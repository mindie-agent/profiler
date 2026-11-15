"""Public topology, precondition and catalog-page Mapping ingress contracts.

[Role]
  Keep public metadata consumers equivalent across accepted Mapping carriers.
[Invariants]
  Nested read-only data is snapshotted, preserved and validated before use.
[Timeouts & Locks]
  TimeoutError and derived callback instances propagate unchanged.
[Side-Effect Policy]
  Only pytest temporary files may be written; no hardware work is performed.
"""

import json
from collections.abc import Mapping

import pytest

from mindie_profiler import fabric_probe, op_api_paging as paging, op_api_registry as registry
from mindie_profiler.__main__ import main as cli
from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.fabric_probe_fit import fit_calibrated_fabric_profile
from mindie_profiler.repro_op import _compact_occurrence
from mindie_profiler.repro_preconditions import precondition_problems
from nr_s6_support import paged_binding
from test_nr_s6_capture_mapping_metadata import CARRIERS, Deadline, ReadOnly, _wrap
from test_nr_s6_round12 import _reassemble


def _freeze(value, carrier):
    if isinstance(value, dict):
        return _wrap({key: _freeze(item, carrier) for key, item in value.items()}, carrier)
    if isinstance(value, list):
        return [_freeze(item, carrier) for item in value]
    return value


def _fingerprint(value):
    if isinstance(value, Mapping):
        return id(value), [(key, _fingerprint(item)) for key, item in value.items()]
    if isinstance(value, (list, tuple)):
        return id(value), [_fingerprint(item) for item in value]
    return id(value), value


def _topology():
    return {"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1]}]}


@pytest.mark.parametrize("carrier", CARRIERS)
def test_topology_public_and_cli_mapping(carrier, tmp_path, monkeypatch, capsys):
    data = _topology()
    payload = _freeze(data, carrier)
    before = _fingerprint(payload)
    expected = fabric_probe.build_fabric_probe_plan(world_size=2, topology=data)
    assert fabric_probe.build_fabric_probe_plan(world_size=2, topology=payload) == expected
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(fabric_probe, "load_cli_json", lambda path: payload)
    assert cli(["fabric-probe", "--topology", "virtual.json", "--world-size", "2"]) == 0
    captured = capsys.readouterr()
    assert not captured.err and json.loads(captured.out) == expected
    assert _fingerprint(payload) == before
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("carrier", CARRIERS)
def test_preconditions_nested_mapping(carrier):
    occurrence = _compact_occurrence(paged_binding())
    payload = _freeze(occurrence, carrier)
    before = _fingerprint(payload)
    assert precondition_problems(payload) == precondition_problems(occurrence) == []
    assert _fingerprint(payload) == before


@pytest.mark.parametrize("carrier", CARRIERS)
def test_fabric_plan_validation_and_fit_nested_mapping(carrier):
    plan = fabric_probe.build_fabric_probe_plan(world_size=2, topology=_topology())
    payload = _freeze(plan, carrier)
    before = _fingerprint(payload)
    assert fabric_probe.validate_plan(payload) == plan
    script = fabric_probe.emit_fabric_probe_script(payload)["script"]
    namespace = {"__name__": "mapping_plan_control"}
    exec(compile(script, "<probe>", "exec"), namespace)
    samples = [{"status": "aborted", "reason": "control"}]
    expected = fit_calibrated_fabric_profile(plan, samples)
    assert fit_calibrated_fabric_profile(payload, _freeze(samples, carrier)) == expected
    assert _fingerprint(payload) == before


@pytest.mark.parametrize("carrier", CARRIERS)
def test_catalog_pages_nested_mapping(carrier):
    name = "aclnnPagedAttention"
    entry = registry.catalog_entry(name)
    artifact = registry.inspect_op_abi(name)["artifact"]
    payload, reference = _freeze(entry, carrier), _freeze(artifact, carrier)
    before = _fingerprint([payload, reference])[1]
    paging._PAGE_CACHE.clear()
    pages, number = [], 0
    while True:
        page = paging.span_page(name, reference, payload, number)
        pages.append(page)
        if page["next_page"] is None:
            break
        number = page["next_page"]
    assert _reassemble(pages) == entry
    assert _fingerprint([payload, reference])[1] == before


@pytest.mark.parametrize("route", ("topology", "preconditions", "page_entry", "page_artifact",
                                   "plan", "fit"))
@pytest.mark.parametrize("site", ("len", "iter", "getitem"))
@pytest.mark.parametrize("error_type", (TimeoutError, Deadline, TypeError))
def test_public_mapping_callback_errors(route, site, error_type, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sentinel = error_type("metadata callback")
    hits = []

    class Fault(ReadOnly):
        def hit(self, callback):
            if site == callback:
                hits.append(callback)
                raise sentinel

        def __len__(self):
            self.hit("len")
            return super().__len__()

        def __iter__(self):
            self.hit("iter")
            return super().__iter__()

        def __getitem__(self, key):
            self.hit("getitem")
            return super().__getitem__(key)

    if route == "topology":
        call = lambda: fabric_probe.build_fabric_probe_plan(world_size=2, topology=Fault(_topology()))
    elif route == "preconditions":
        call = lambda: precondition_problems(Fault(_compact_occurrence(paged_binding())))
    elif route == "plan":
        call = lambda: fabric_probe.validate_plan(Fault(fabric_probe.build_fabric_probe_plan()))
    elif route == "fit":
        call = lambda: fit_calibrated_fabric_profile(Fault(fabric_probe.build_fabric_probe_plan()), [])
    else:
        entry = registry.catalog_entry("aclnnPagedAttention")
        artifact = registry.inspect_op_abi("aclnnPagedAttention")["artifact"]
        if route == "page_entry":
            entry = Fault(entry)
        else:
            artifact = Fault(artifact)
        call = lambda: paging.span_page("aclnnPagedAttention", artifact, entry)
    if issubclass(error_type, TimeoutError):
        with pytest.raises(TimeoutError) as caught:
            call()
        assert caught.value is sentinel
    elif route == "preconditions":
        assert call()[0]["rule"] == "cardinality"
    else:
        with pytest.raises(ProfilerUsageError):
            call()
    assert hits == [site]
    assert not list(tmp_path.iterdir())
