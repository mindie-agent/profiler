"""Read-only structural metadata, native records and explicit binding evidence.

[Role]
  Exercise structure consumers and measured event mapping with Mapping carriers.
[Invariants]
  Native records and explicit evidence are retained without changing caller data.
[Timeouts & Locks]
  Protocol deadlines propagate by exact instance identity; no waits or locks.
[Side-Effect Policy]
  In-memory metadata only; no device access or publication.
"""

from types import SimpleNamespace

import pytest

from mindie_profiler.events import Event, ProfilerUsageError, SourceRef, Window
from mindie_profiler.structure_mapping import StructureMapper, _seal_digest, read_metadata
from mindie_profiler.structure_subgraphs import StructureTargets
from mapping_fixtures import CARRIERS, Deadline, ReadOnly
from test_public_mapping_parity import _fingerprint, _freeze


def _structure():
    structure = {"schema_version": "mindie-model-structure/1",
                 "nodes": [{"node_id": "n", "replica": "0", "stage": "0",
                            "phase": "decode", "layer": 0}], "subgraphs": []}
    structure["graph_id"] = _seal_digest(structure)
    structure["native_calls"] = [{"node_id": "n", "call_id": "native-call",
                                  "api": {"entry": "PagedAttention"},
                                  "kernels": [{"name": "paged_kernel"}],
                                  "observed_aliases": [{"compute_name": "observed_kernel"}]}]
    return structure


def _bindings(structure, event_id="event"):
    return {"schema_version": "mindie-profile-bindings/1",
            "graph_id": structure["graph_id"],
            "events": [{"event_id": event_id, "node_ids": ["n"],
                        "evidence": {"source": "capture"}}]}


def _event(locator=None):
    return Event(rank_id="0", rank_index=0, name="measured", op_type="PagedAttention",
                 task_type="compute", core="AI_CORE", stream_id="0", task_id="1",
                 device_id="0", start_ns=10, end_ns=30, source_kind="csv", table="kernels",
                 locator={} if locator is None else locator)


@pytest.mark.parametrize("carrier", CARRIERS)
def test_structural_records_and_measured_mapping(carrier):
    locator = _freeze({"layout": "kernel_details", "metadata": {"line": 1}}, carrier)
    prior_locator = _fingerprint(locator)
    event = _event(locator)
    assert type(event.locator) is dict and event.locator is not locator
    assert event.locator == {"layout": "kernel_details", "metadata": {"line": 1}}
    assert _fingerprint(locator) == prior_locator
    source = SourceRef("0", 0, "csv", "capture.csv", "capture.csv", None, 0, "1", "test")
    observation = SimpleNamespace(rank_id="0", rank_index=0, window=Window(0, 100),
                                  events=[event], source=source)
    structure = _structure()
    bindings = _bindings(structure, event.event_id)
    payload, evidence = _freeze(structure, carrier), _freeze(bindings, carrier)
    before = _fingerprint([payload, evidence])[1]
    mapper = StructureMapper(payload, bindings=evidence)
    assert mapper.target_index.native_bindings["n"]["call_id"] == "native-call"
    assert mapper.target_index.native_call_kernels["paged_kernel"] == ["n"]
    assert "observed_kernel" in mapper.target_index.native_call_alias_names
    result = mapper.finish([mapper.map_window(observation)])
    control = StructureMapper(structure, bindings=bindings)
    assert result == control.finish([control.map_window(observation)])
    assert result["status"] == "mapped" and result["event_window_count"] == 1
    assert result["windows"][0]["bound_busy_union_ns"] == 20
    assert not result["unused_explicit_event_ids"]
    assert _fingerprint([payload, evidence])[1] == before


@pytest.mark.parametrize("carrier", CARRIERS)
def test_direct_structure_targets_mapping(carrier):
    structure = _structure()
    nodes = {row["node_id"]: row for row in structure["nodes"]}
    payload = _freeze([nodes, [], structure["native_calls"]], carrier)
    before = _fingerprint(payload)
    targets = StructureTargets(*payload)
    details = targets.describe_implementation("PagedAttention", ["n"])
    assert details["native_call"]["kernels"] == ["paged_kernel"]
    assert details["native_call"]["call_id"] == "native-call"
    assert _fingerprint(payload) == before


@pytest.mark.parametrize("route", ("metadata", "bindings", "native_calls", "event_locator"))
@pytest.mark.parametrize("site", ("len", "iter", "getitem"))
@pytest.mark.parametrize("error_type", (TimeoutError, Deadline, TypeError))
def test_structure_callback_errors(route, site, error_type, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sentinel = error_type("structure callback")
    reached = []

    class Fault(ReadOnly):
        def hit(self, callback):
            if callback == site:
                reached.append(callback)
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

    structure = _structure()
    if route == "metadata":
        call = lambda: read_metadata(Fault(structure), "mindie-model-structure/1")
    elif route == "bindings":
        call = lambda: StructureMapper(structure, bindings=Fault(_bindings(structure)))
    elif route == "event_locator":
        call = lambda: _event(Fault({"layout": "captured"}))
    else:
        nodes = {row["node_id"]: row for row in structure["nodes"]}
        call = lambda: StructureTargets(nodes, [], [Fault(structure["native_calls"][0])])
    if issubclass(error_type, TimeoutError):
        with pytest.raises(TimeoutError) as caught:
            call()
        assert caught.value is sentinel
    else:
        with pytest.raises(ProfilerUsageError):
            call()
    assert reached == [site]
    assert not list(tmp_path.iterdir())
