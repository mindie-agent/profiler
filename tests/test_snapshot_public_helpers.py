"""Metadata snapshot coverage for direct public JSON helpers.

[Role]
  Verify the remaining publication, identity and token helper boundaries.
[Invariants]
  Nested mappings and tuple arrays behave like dict/list values. Validation
  precedes publication and hashing, and caller input is never mutated.
[Timeouts & Locks]
  Original callback TimeoutError instances pass through without replacement.
[Side-Effect Policy]
  Files are created only inside pytest temporary directories; no device access.
"""

import json
from collections import Counter, UserDict
from collections.abc import Sequence
from pathlib import Path
from types import MappingProxyType

import pytest

from mindie_profiler import token_budget as tokens
from mindie_profiler.events import ProfilerUsageError, composite_event_identity
from mindie_profiler.fabric_probe_fit import parse_fabric_probe_samples
from mindie_profiler.repro_snapshot import snapshot
from mindie_profiler.repro_storage import stage_artifacts
from mapping_fixtures import (
    CountedTuple, Deadline, HELPERS, ReadOnly, WideMapping, freeze, plain,
)


def identity(locator):
    return composite_event_identity(rank_id="rank", rank_index=0, source_kind="trace",
        table="kernels", device_id="0", stream_id="0", task_id="0",
        start_ns=0, end_ns=1, locator=locator)


PUBLIC = (
    (tokens.serialize, {"metadata": [{"source": "capture"}]}),
    (tokens.estimate_tokens, {"evidence": [{"source": "capture"}]}),
    (tokens.receipt, {"status": "ready", "metadata": [{"source": "capture"}]}),
    (tokens.bounded_envelope, {"status": "blocked", "issues": [{"code": "invalid_request"}]}),
    (tokens.truncate_lists, {"metadata": [{"source": "capture"}]}),
    (tokens.omit_unrepresentable_paths, {"status": "ready", "metadata": [{"source": "capture"}]}),
    (identity, {"metadata": [{"source": "capture"}]}),
    (parse_fabric_probe_samples, {"samples": [{"bytes": 8, "latency_us": 1,
        "validated": True, "metadata": [{"evidence": {"source": "probe"}}]}]}),
)


@pytest.mark.parametrize("function,value", PUBLIC, ids=[f.__name__ for f, _ in PUBLIC])
@pytest.mark.parametrize("carrier", (UserDict, MappingProxyType, ReadOnly))
def test_public_json_helpers_keep_nested_mapping_and_tuple_parity(function, value, carrier):
    tracked = []
    wrapped = freeze(value, carrier, CountedTuple, tracked)
    assert function(wrapped) == function(value)
    assert plain(wrapped) == value
    for item in tracked:
        if isinstance(item, ReadOnly):
            assert item.iterations == 1
            assert item.reads == Counter({key: 1 for key in item.data})
        elif isinstance(item, CountedTuple):
            assert item.iterations == 1 and item.reads == len(item)


@pytest.mark.parametrize("carrier", (UserDict, MappingProxyType, ReadOnly))
def test_direct_manifest_stage_snapshots_before_encoding(carrier, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    manifest = {"schema": "test", "metadata": [{"evidence": {"source": "capture"}}]}
    wrapped = freeze(manifest, carrier, tuple)
    result = stage_artifacts("print('snapshot')\n", wrapped, output_dir="caller")
    assert result["status"] == "delivered"
    assert json.loads(Path(result["manifest_path"]).read_text()) == manifest
    assert plain(wrapped) == manifest


@pytest.mark.parametrize("function,value", PUBLIC, ids=[f.__name__ for f, _ in PUBLIC])
def test_public_json_helpers_reject_declared_width_before_reads(function, value):
    wide = WideMapping(value)
    with pytest.raises(ProfilerUsageError):
        function(wide)
    assert not wide.reads and wide.iterations == 0


def test_manifest_rejection_cannot_publish(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", "cas")
    with pytest.raises(ProfilerUsageError):
        stage_artifacts("pass\n", {"metadata": WideMapping({"a": 1})}, output_dir="caller")
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("function,arguments", HELPERS, ids=[f.__name__ for f, _ in HELPERS])
@pytest.mark.parametrize("error_type", (TimeoutError, Deadline))
def test_direct_diff_helper_timeout_identity(function, arguments, error_type):
    sentinel = error_type("direct helper deadline")
    hits = []

    class Fault(ReadOnly):
        def __len__(self):
            hits.append("len")
            raise sentinel

    supplied = dict(arguments)
    field = next(key for key, value in supplied.items() if isinstance(value, (dict, list)))
    supplied[field] = Fault({"evidence": 1})
    with pytest.raises(TimeoutError) as error:
        function(**supplied)
    assert error.value is sentinel and hits == ["len"]


@pytest.mark.parametrize("function,value", PUBLIC, ids=[f.__name__ for f, _ in PUBLIC])
@pytest.mark.parametrize("error_type", (TimeoutError, Deadline))
def test_public_json_helper_timeout_identity(function, value, error_type):
    sentinel = error_type("metadata deadline")

    class Fault(ReadOnly):
        def __iter__(self):
            raise sentinel

    with pytest.raises(TimeoutError) as error:
        function(Fault(value))
    assert error.value is sentinel


def test_unsupported_sequence_fails_without_member_access():
    class Unbounded(Sequence):
        def __len__(self):
            return 1_000_001

        def __getitem__(self, index):
            raise AssertionError("unsupported sequence was traversed")

    with pytest.raises(ProfilerUsageError):
        snapshot({"rows": Unbounded()})


def test_shared_subtree_keeps_budget_without_rereading_members():
    leaf = ReadOnly({"evidence": [0] * 1000})
    tree = [[leaf] * 1000] * 1000
    with pytest.raises(ProfilerUsageError):
        snapshot(tree)
    assert leaf.iterations == 1 and leaf.reads == Counter(evidence=1)


def test_shared_subtree_keeps_depth_budget():
    leaf = ReadOnly({"evidence": 1})
    nested = leaf
    for _ in range(63):
        nested = [nested]
    with pytest.raises(ProfilerUsageError):
        snapshot([leaf, nested])
    assert leaf.iterations == 1 and leaf.reads == Counter(evidence=1)


def test_snapshot_retains_ephemeral_member_owners():
    class Ephemeral(ReadOnly):
        def __getitem__(self, key):
            return {"index": int(key)}

    result = snapshot(Ephemeral({str(index): None for index in range(1000)}))
    assert result == {str(index): {"index": index} for index in range(1000)}
