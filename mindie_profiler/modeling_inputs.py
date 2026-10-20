"""Alias ``mindie_profiler.modeling_inputs`` to standalone ``mindie_sim.modeling_inputs``.

[Role]
  Zero-duplication module alias so callers importing ``mindie_profiler.modeling_inputs``
  share the exact module object from ``mindie_sim.modeling_inputs``.

[Invariants]
  * ``mindie_sim.modeling_inputs`` is the single source of truth.

[Timeouts & Locks]
  Pure module alias; no I/O or locks.

[Side-Effect Policy]
  None.
"""
from __future__ import annotations

import sys

from mindie_sim import modeling_inputs as _impl
from mindie_sim.modeling_inputs import *  # noqa: F401,F403

sys.modules[__name__] = _impl
