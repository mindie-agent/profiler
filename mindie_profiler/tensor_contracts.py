"""Standalone lazy forwarding shim to ``mindie_profiler.observed_contracts.signatures``.

[Role] Forward every requested name to the local canonical implementation.
[Invariants] Zero ``mindie_sim`` import (``python -I`` clean); public
  and private symbols forward unchanged.
[Timeouts & Locks] One lazy import on first attribute access; no locks.
[Side-Effect Policy] Pure in-memory delegation after the lazy import.
"""
from __future__ import annotations

from importlib import import_module

_TARGET = "mindie_profiler.observed_contracts.signatures"


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(import_module(_TARGET), name)
