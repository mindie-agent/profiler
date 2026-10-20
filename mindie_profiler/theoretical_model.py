"""Alias ``mindie_profiler.theoretical_model`` to standalone ``mindie_sim.theoretical_model``.

[Role]
  Zero-duplication module alias so callers importing ``mindie_profiler.theoretical_model``
  share the exact module object from ``mindie_sim.theoretical_model``.

[Invariants]
  * ``mindie_sim.theoretical_model`` is the single source of truth.

[Timeouts & Locks]
  Pure module alias; no I/O or locks.

[Side-Effect Policy]
  None.
"""
from __future__ import annotations

import sys

from mindie_sim import theoretical_model as _impl
from mindie_sim.theoretical_model import *  # noqa: F401,F403

sys.modules[__name__] = _impl
