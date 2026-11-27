"""Lazy forwarding shim for standalone composite structure targets.

[Role]
  Forward ``mindie_profiler.observed_contracts.vocabulary`` while preserving
  the profiler's ``ProfilerUsageError`` boundary for malformed carriers.

[Invariants]
  * Zero ``mindie_sim`` import; operates 100% standalone.
  * ``StructureTargets`` translates ``StructureTargetError`` to
    ``ProfilerUsageError`` while propagating ``TimeoutError`` untouched.
  * Every other symbol forwards unchanged; dunder names raise ``AttributeError``.

[Timeouts & Locks]
  One lazy import on first attribute access; no waits or locks.

[Side-Effect Policy]
  Pure in-memory delegation after the lazy import.
"""
from __future__ import annotations

from importlib import import_module


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)

    target = import_module("mindie_profiler.observed_contracts.vocabulary")
    if name != "StructureTargets":
        return getattr(target, name)

    from .events import ProfilerUsageError
    from .observed_contracts.vocabulary import StructureTargetError

    class StructureTargets(target.StructureTargets):
        def __init__(self, *args, **kwargs):
            try:
                super().__init__(*args, **kwargs)
            except TimeoutError:
                raise
            except StructureTargetError as exc:
                raise ProfilerUsageError(str(exc)) from exc

        def scope(self, row):
            try:
                return super().scope(row)
            except TimeoutError:
                raise
            except StructureTargetError as exc:
                raise ProfilerUsageError(str(exc)) from exc

    globals()[name] = StructureTargets
    return StructureTargets
