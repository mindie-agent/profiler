"""A worker's high-water mark excludes its launcher's previous memory use."""
import json
import os
from pathlib import Path
import subprocess
import sys


def test_peak_rss_tracks_the_current_executable_and_survives_memory_release():
    flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("fixtures") / "process_memory_probe.py"),
         "parent"], capture_output=True, text=True, timeout=20, check=True, **flags)
    report = json.loads(result.stdout)
    child = report["child"]
    assert child["initial"] < report["parent_peak"] - 64 * 1024 ** 2
    assert child["allocated"] >= child["initial"] + 8 * 1024 ** 2
    # Linux batches RSS accounting asynchronously; verify that freeing the
    # allocation retains its peak, without requiring byte-identical snapshots.
    assert child["released"] >= child["initial"] + 8 * 1024 ** 2
