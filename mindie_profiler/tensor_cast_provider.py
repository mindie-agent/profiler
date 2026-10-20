"""Alias ``mindie_profiler.tensor_cast_provider`` to standalone ``mindie_sim.tensor_cast_provider``.

[Role]
  Zero-duplication module alias so callers importing ``mindie_profiler.tensor_cast_provider``
  share the exact module object from ``mindie_sim.tensor_cast_provider``.

[Invariants]
  * ``mindie_sim.tensor_cast_provider`` is the single source of truth.

[Timeouts & Locks]
  Pure module alias; no I/O or locks.

[Side-Effect Policy]
  None.
"""
from __future__ import annotations

import sys

from mindie_sim import tensor_cast_provider as _impl
from mindie_sim.tensor_cast_provider import *  # noqa: F401,F403

if __name__ == "__main__":
    raise SystemExit(_impl.main(sys.argv[1:]))

sys.modules[__name__] = _impl
