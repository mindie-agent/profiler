"""CLI for offline captured-kernel inventory.

[Role] Load an explicit source manifest and invoke the streaming inventory.
[Invariants] Errors remain nonzero; existing captures are never modified.
[Timeouts & Locks] Per-source budget is passed to the importer; no device work.
[Side-Effect Policy] Writes only --output-dir; reads only declared inputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .events import ProfilerUsageError
from .kernel_inventory import build_inventory


def main(argv=None):
    parser = argparse.ArgumentParser(prog="mindie-profiler kernels")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-timeout-s", type=float, default=300)
    args = parser.parse_args(argv)
    path = Path(args.manifest)
    if path.stat().st_size > 1024 * 1024:
        raise ProfilerUsageError("kernel manifest exceeds 1 MiB")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProfilerUsageError(f"invalid kernel manifest: {exc}") from exc
    summary = build_inventory(manifest, args.output_dir, timeout_s=args.source_timeout_s)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 2 if summary["failures"] else 0
