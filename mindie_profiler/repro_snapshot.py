"""Bounded, detached container inputs for public JSON metadata.

[Role]
  Snapshot Mapping and list/tuple inputs before attribution or publication.

[Invariants]
  Keys are plain strings before lookup/hash; declared widths, expanded member
  counts and nesting are bounded by one million, one million and 64. Shared
  containers are read once but charged at every occurrence in the expanded
  tree. Only finite JSON leaves enter JSON metadata. Caller objects remain
  untouched. Internal snapshot implementations never reopen public ingress.

[Timeouts & Locks]
  No locks. Caller TimeoutError instances, including subclasses, pass through.

[Side-Effect Policy]
  Pure in-memory copying and validation; no publication or global limit changes.
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import wraps
from inspect import signature

from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.repro_values import _bounded_members, literal_value


def snapshot(value, *, _sets=()):
    """Normalize one input tree with single reads and an expanded-tree budget."""
    budget, memo, active = [0], {}, set()

    def copy(item, depth):
        if not (isinstance(item, (Mapping, list, tuple))
                or (id(item) in _sets and isinstance(item, (set, frozenset)))):
            return literal_value(item), 0
        if depth >= 64:
            raise ProfilerUsageError("input container nesting exceeds 64 levels")
        identity = id(item)
        if identity in active:
            raise ProfilerUsageError("input containers must not contain cycles")
        if identity in memo:
            _owner, result, cost, height = memo[identity]
            if depth + height > 64 or budget[0] + cost > 1_000_000:
                raise ProfilerUsageError("expanded container budget exceeded")
            budget[0] += cost
            return result, height
        active.add(identity)
        begin, height = budget[0], 1
        mapping = isinstance(item, Mapping)
        result = {} if mapping else []
        for key, member in _bounded_members(
                item, budget, 1_000_000 - begin, string_keys=True):
            child, child_height = copy(member, depth + 1)
            height = max(height, child_height + 1)
            if mapping:
                result[key] = child
            else:
                result.append(child)
        active.remove(identity)
        memo[identity] = item, result, budget[0] - begin, height
        return result, height

    try:
        return copy(value, 0)[0]
    except ProfilerUsageError:
        raise
    except TimeoutError:
        raise
    except Exception as exc:
        raise ProfilerUsageError("invalid input container protocol") from exc


def snapshot_call(function, *fields, set_fields=()):
    """Wrap a public helper; internal callers use its private implementation.

    All selected arguments share one snapshot budget and alias memo. Binding
    inspects only the function signature, never caller container members.
    """
    parameters = signature(function)

    @wraps(function)
    def public(*args, **kwargs):
        bound = parameters.bind(*args, **kwargs)
        values = snapshot({name: bound.arguments[name] for name in fields
                           if name in bound.arguments}, _sets={
                               id(bound.arguments[name]) for name in set_fields
                               if name in bound.arguments})
        bound.arguments.update(values)
        try:
            return function(*bound.args, **bound.kwargs)
        except TimeoutError:
            raise
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
            raise ProfilerUsageError("invalid container input") from exc

    return public
