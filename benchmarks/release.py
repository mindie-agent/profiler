"""[Role] Release entry point for the profiler analysis-and-attribution benchmark.
[Invariants] Delegate to ``benchmarks/profiler.py`` unchanged; never import a sibling project.
[Timeouts & Locks] Inherit the bounded finite iterations defined by ``profiler.py``.
[Side-Effect Policy] Delegate the single result-JSON write to ``benchmarks/profiler.py``.
"""
from pathlib import Path
import runpy

BENCHMARK = Path(__file__).with_name("profiler.py")


def main() -> None:
    runpy.run_path(str(BENCHMARK), run_name="__main__")


if __name__ == "__main__":
    main()
