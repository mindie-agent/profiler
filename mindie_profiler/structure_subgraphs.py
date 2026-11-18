"""Lazy SSOT forwarding shim for declared composite structure targets.

[Role]
  Forward ``mindie_sim.observed_contracts.targets`` while preserving the
  profiler's ``ProfilerUsageError`` boundary for malformed structure carriers.

[Invariants]
  * Zero top-level ``mindie_sim`` import; raw trace commands stay isolated.
  * ``StructureTargets`` is the canonical simulator class with only its carrier
    failures translated; rows remain attribute-bearing carriers.
  * ``TimeoutError`` propagates untouched from the constructor and ``scope()``.
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

    target = import_module("mindie_sim.observed_contracts.targets")
    if name != "StructureTargets":
        return getattr(target, name)

    from .events import ProfilerUsageError
    from mindie_sim.observed_contracts.errors import StructureTargetError

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
