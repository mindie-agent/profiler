"""Import-stable command-line entry point for ``mindie_profiler``.

[Role]
  Expose the same ``main`` callable as ``mindie_profiler.__main__`` so console
  scripts and callers can import ``mindie_profiler.cli:main`` without importing
  the ``__main__`` module as a side effect.

[Invariants]
  * ``main`` is the single implementation in ``__main__``; this module does not
    duplicate argument parsing or command dispatch.
  * Importing this module performs no I/O and does not execute the CLI.

[Timeouts & Locks]
  No locks or timers; bounded work is owned by the dispatched subcommand.

[Side-Effect Policy]
  Import is side-effect free.  Calling ``main`` writes only the explicitly
  requested output and delegates all reads to the selected subcommand.
"""
from __future__ import annotations

from .__main__ import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
