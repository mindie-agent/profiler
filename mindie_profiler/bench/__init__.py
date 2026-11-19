"""Standalone device benchmark suite: ABI, SKU, subgraph and PR overlay A/B.

[Role]
  Dispatch the four ``bench`` subcommands.  ``abi`` admits one die and inspects
  the installed operator surface, ``sku`` runs the five S0 domains, ``subgraph``
  replays exported S0/S1 plans, and ``pr-ab`` runs an ephemeral PR overlay
  A/B on a serving checkout.  The package is importable and runnable inside an
  A2/A3 container with no ``mindie-sim`` installation.

[Invariants]
  * Importing ``mindie_profiler.bench`` imports neither ``torch``, ``torch_npu``
    nor ``mindie_sim``; each subcommand imports its own runtime lazily.
  * A missing runtime is an explicit ``torch_npu_unavailable`` status with a
    non-zero exit code, never a silent fallback to modeled numbers.
  * Every subcommand accepts an explicit output path and writes atomically.

[Timeouts & Locks]
  Delegated to each subcommand; the package layer starts no thread and takes no
  lock.

[Side-Effect Policy]
  Delegated to each subcommand.  This module only parses ``argv``.
"""

from __future__ import annotations

import sys
from typing import Sequence

BENCH_SCHEMA = "mindie-bench/1"
SUBCOMMANDS = ("abi", "sku", "subgraph", "pr-ab")
SUBCOMMAND_SUMMARIES = {
    "abi": "bind LOCAL_RANK, verify the physical die, inspect operator ABIs",
    "sku": "run the five-domain SKU microbench on one admitted die",
    "subgraph": "replay exported S0 local chains or S1 joined subgraphs",
    "pr-ab": "materialise base/PR overlay worktrees and run ABBA paired trials",
}

_DISPATCH = {
    "abi": (".abi", "main"),
    "sku": (".bench_sku_microbench", "main"),
    "subgraph": (".bench_archetype_subgraphs", "main"),
    "pr-ab": (".pr_overlay", "main"),
}


def usage() -> str:
    lines = ["usage: mindie-profiler bench <command> [options]", "", "commands:"]
    for name in SUBCOMMANDS:
        lines.append(f"  {name:<10} {SUBCOMMAND_SUMMARIES[name]}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw or raw[0] in {"-h", "--help"}:
        print(usage())
        return 0 if raw else 2
    if raw[0] in {"-V", "--version"}:
        from .. import __version__

        print(f"mindie-profiler bench {__version__}")
        return 0
    command = raw[0]
    if command not in SUBCOMMANDS:
        print(f"mindie_profiler bench: unknown command {command!r} "
              f"(choose from {', '.join(SUBCOMMANDS)})", file=sys.stderr)
        return 2
    from importlib import import_module

    module_name, entry = _DISPATCH[command]
    module = import_module(module_name, __name__)
    return int(getattr(module, entry)(raw[1:]))


__all__ = ["BENCH_SCHEMA", "SUBCOMMANDS", "SUBCOMMAND_SUMMARIES", "main", "usage"]


if __name__ == "__main__":
    raise SystemExit(main())
