"""Lazy SSOT forwarding shim to ``mindie_sim.observed_contracts.router_contracts``.

[Role] Forward every requested name to the single canonical implementation.
[Invariants] Zero top-level ``mindie_sim`` import (``python -I`` clean); public
  and private symbols forward unchanged; no local schema or fallback copy.
[Timeouts & Locks] One lazy import on first attribute access; no locks.
[Side-Effect Policy] Pure in-memory delegation after the lazy import.
"""
from __future__ import annotations

from importlib import import_module

_TARGET = "mindie_sim.observed_contracts.router_contracts"


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(import_module(_TARGET), name)
