"""Retained Mapping-carrier and callback fixtures for the keeper suites.

[Role]
  Expose the read-only, counted and timeout-observable containers that the
  retained mapping, snapshot and lookup-contract suites exercise, plus the
  profiler-owned helpers they count reads through.
[Invariants]
  A fixture iterates its payload once and looks each mapping member up once;
  unsupported keys are never hashed during construction.
[Timeouts & Locks]
  ``Deadline`` is an exact ``TimeoutError`` subclass; no waits or locks.
[Side-Effect Policy]
  Pure in-memory helpers; callers own temporary paths.
"""

from __future__ import annotations

import json
from collections import Counter, UserDict
from collections.abc import Mapping
from types import MappingProxyType

from mindie_profiler import repro_values, token_budget

from native_abi_fixtures import paged_row


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


class CountedList(list):
    def __iter__(self):
        self.iterations = getattr(self, "iterations", 0) + 1
        for item in super().__iter__():
            self.reads = getattr(self, "reads", 0) + 1
            yield item


class CountedTuple(tuple):
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


class WideMapping(ReadOnly):
    def __len__(self):
        return 1_000_001


class WideList(CountedList):
    def __len__(self):
        return 1_000_001


class WideTuple(CountedTuple):
    def __len__(self):
        return 1_000_001


class Deadline(TimeoutError):
    pass


class KeyMapping(Mapping):
    """Expose keys without hashing them when the mapping is constructed."""

    def __init__(self, key, value=None, prefix=None, callback=None):
        self.key, self.value = key, value
        self.prefix = {} if prefix is None else prefix
        self.callback = callback
        self.reads = 0

    def __len__(self):
        return len(self.prefix) + 1

    def __iter__(self):
        yield from self.prefix
        yield self.key

    def __getitem__(self, key):
        self.reads += 1
        if self.callback is not None:
            self.callback()
        if key is self.key:
            return self.value
        if type(key) is str and key in self.prefix:
            return self.prefix[key]
        if key == self.key:
            return self.value
        raise KeyError(key)


def key_fixture(kind):
    """Return an unsupported key and observable hash/equality counters."""
    calls = {"hash": 0, "eq": 0}

    class CountedInt(int):
        def __hash__(self):
            calls["hash"] += 1
            return int.__hash__(self)

    class CustomString(str):
        def __hash__(self):
            calls["hash"] += 1
            raise AssertionError("unsupported key hash was reached")

        def __eq__(self, other):
            calls["eq"] += 1
            raise AssertionError("unsupported key equality was reached")

    if kind in ("counted", "billion"):
        key = CountedInt(7) if kind == "counted" else "leaf"
        for _ in range(3):
            key = (key,) * (101 if kind == "counted" else 1000)
    elif kind == "frozenset":
        key = frozenset((tuple(range(1000)),))
        for _ in range(3):
            key = frozenset((key,))
    else:
        key = {"list": [1], "dict": {"leaf": 1}, "int": 1,
               "tuple": (1,), "str_subclass": CustomString("field")}[kind]
    return key, calls


def key_timeout_callback(method, sentinel):
    """Reach a key callback through an accepted string-key mapping lookup."""
    class CallbackKey:
        def __hash__(self):
            if method == "hash":
                raise sentinel
            return 0

        def __eq__(self, other):
            raise sentinel

    key = CallbackKey()
    if method == "hash":
        return lambda: {key: None}
    data = {key: None}
    return lambda: data[CallbackKey()]


def _raw(direction, storage):
    row = paged_row()
    field = direction[:-1]
    row[field + "_shapes"] = [
        dict(shape=json.loads(shape), dtype=row[field + "_dtypes"][i],
             layout=row[field + "_formats"][i])
        for i, shape in enumerate(row[field + "_shapes"])]
    row[field + "_shapes"][0]["storage"] = storage
    return row


# Profiler-owned helpers that snapshot each declared member exactly once.  The
# retired diff-replay wrappers are intentionally absent: this keeper only counts
# generic ingress reads, not a deleted simulator subsystem.
HELPERS = (
    (token_budget.serialize, {"value": [1, 2, 3]}),
    (token_budget.estimate_tokens, {"value": [1, 2, 3]}),
    (token_budget.within_budget, {"value": [1, 2, 3], "limit": 5000}),
    (repro_values.bounded_mapping, {"value": {"a": 1, "b": 2}}),
    (repro_values.validate_container_depth, {"value": {"a": 1, "b": 2}}),
    (repro_values.validate_json_integers, {"value": {"a": 1}}),
)
