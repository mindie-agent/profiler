"""Small shared I/O helpers for offline evaluation caches and reports.

[Role] Write JSON reports/cache entries atomically and fingerprint optional
  capture sidecars without consuming a private key.
[Invariants] Temporary files stay beside the destination and are removed on
  failure; a report is replaced only after its full content is flushed.
[Timeouts & Locks] No locks or timers; callers bound their own work.
[Side-Effect Policy] Writes only the caller-selected destination path.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile


def atomic_write_json(path, payload, *, indent=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".eval-", suffix=".json",
                                    dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=indent,
                      separators=None if indent else (",", ":"),
                      allow_nan=False)
            handle.write("\n")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def sidecar_identities(capture_dir, names):
    directory = Path(capture_dir)
    return {
        name: [(directory / name).stat().st_size,
               (directory / name).stat().st_mtime_ns]
        for name in names if (directory / name).exists()
    }
