"""[Role] Read the operating system's process memory accounting.
[Invariants] Peak RSS is an OS high-water mark, never current RSS mislabeled peak.
  Platform-specific units are decoded without restricting execution placement.
[Timeouts & Locks] Local process counters only; no locks or subprocesses.
[Side-Effect Policy] Read-only. No device or model initialization.
"""
from __future__ import annotations

import sys


def peak_rss_bytes() -> int:
    try:
        import resource
    except ImportError:
        import psutil

        info = psutil.Process().memory_info()
        return int(info.peak_wset)
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # getrusage specifies bytes on macOS and KiB on other supported Unix hosts.
    return int(value if sys.platform == "darwin" else value * 1024)
