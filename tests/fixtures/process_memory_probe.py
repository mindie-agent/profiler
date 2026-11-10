"""Exercise OS peak accounting across a real parent/exec boundary."""
import json
import os
from pathlib import Path
import subprocess
import sys

from mindie_profiler.process_memory import peak_rss_bytes


def committed_memory(mebibytes):
    value = bytearray(mebibytes * 1024 ** 2)
    value[::4096] = b"x" * (len(value) // 4096)
    return value


if __name__ == "__main__":
    if sys.argv[1] == "parent":
        retained = committed_memory(96)
        flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        child = subprocess.run(
            [sys.executable, str(Path(__file__)), "child"], capture_output=True,
            text=True, timeout=10, check=True, **flags)
        print(json.dumps(dict(parent_peak=peak_rss_bytes(), child=json.loads(child.stdout))))
    else:
        initial = peak_rss_bytes()
        retained = committed_memory(16)
        allocated = peak_rss_bytes()
        del retained
        print(json.dumps(dict(initial=initial, allocated=allocated,
                              released=peak_rss_bytes())))
