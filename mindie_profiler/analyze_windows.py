"""Native step-window discovery, ``--auto-step`` selection and bounded rank fan-out.

[Role]
  Resolve per-rank explicit ``Window`` objects from native ``STEP_TIME`` /
  ``ProfilerStep#`` markers (or a single-clock ``step_trace_time.csv``), select
  post-warmup steady steps, format actionable missing-window errors, and run a
  bounded thread pool over already-discovered rank sources.
[Invariants]
  * Every selected rank carries the same original step IDs; no shared Rank-0
    timestamp is ever applied to another rank's local clock.
  * Step IDs and labels are preserved, never renumbered; matching IDs alone do
    not declare cross-rank clock alignment.
  * Selection only runs when the caller passed ``auto_step=True``; otherwise the
    explicit-window usage error is unchanged and contains ``explicit``.
  * Zero native markers raise a usage error with copy-pasteable commands; they
    never invent a window.
[Timeouts & Locks]
  Each rank probe is bounded by ``timeout_s`` (SQLite progress handler or CSV
  row budget); the fan-out pool is bounded by ``jobs`` and holds no locks.
[Side-Effect Policy]
  Read-only SQLite/CSV access; no filesystem writes or device context.
"""
from __future__ import annotations

import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from .events import ProfilerUsageError, Window
from .inventory import inventory_profile
from .scene_detector import STEADY, SteadyStateConfig, StepSample, detect_steady_window

MAX_AUTO_STEPS = 8
STEADY_TOLERANCE = 0.10
_AUTO_PROBE_TIMEOUT_S = 1.0
_STEP_COLUMNS = ("Step ID", "Step", "step_id", "step")
_STAGE_COLUMNS = ("Stage(us)", "Stage", "Stage Time(us)", "Stage(us)")


def _resolve_jobs(jobs: int | None, count: int) -> int:
    if jobs is None:
        return 1 if count <= 1 else max(1, min(count, os.cpu_count() or 4, 8))
    if isinstance(jobs, bool) or not isinstance(jobs, int) or jobs < 1:
        raise ProfilerUsageError("jobs must be a positive integer")
    return jobs


def _native_windows_for_source(source: Any, *, timeout_s: float) -> tuple[list[dict[str, Any]], str]:
    if getattr(source, "kind", None) == "db" and getattr(source, "db_path", None):
        inventory = inventory_profile(source.db_path, timeout_s=timeout_s)
        rank = (inventory.get("ranks") or [{}])[0]
        return list(rank.get("native_step_windows") or ()), "STEP_TIME"
    rank_dir = Path(getattr(source, "rank_dir", "") or "")
    path = rank_dir / "step_trace_time.csv"
    if not path.is_file():
        return [], "step_trace_time.csv"
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader):
                if index >= 20_000:
                    break
                step_text = next((row[name].strip() for name in _STEP_COLUMNS
                                  if isinstance(row.get(name), str) and row[name].strip()), None)
                stage = next((row[name].strip() for name in _STAGE_COLUMNS
                              if isinstance(row.get(name), str) and row[name].strip()), None)
                if step_text is None or stage is None:
                    continue
                try:
                    step, span_us = int(float(step_text)), float(stage)
                except ValueError:
                    continue
                if span_us <= 0:
                    continue
                rows.append({"source_table": "step_trace_time.csv", "step": step,
                             "name": f"Step#{step}", "start_ns": int(step * 1_000_000),
                             "end_ns": int(step * 1_000_000 + span_us * 1000.0),
                             "duration_ms": round(span_us / 1000.0, 6)})
    except TimeoutError:
        raise
    except OSError as exc:
        raise ProfilerUsageError(f"cannot read step_trace_time.csv: {exc}") from exc
    return rows, "step_trace_time.csv"


def _steps_by_id(windows: Iterable[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    selected: dict[int, dict[str, Any]] = {}
    for item in windows:
        step = item.get("step")
        if not isinstance(step, int) or isinstance(step, bool):
            continue
        start_ns, end_ns = item.get("start_ns"), item.get("end_ns")
        if not isinstance(start_ns, int) or not isinstance(end_ns, int) or end_ns <= start_ns:
            continue
        current = selected.get(step)
        if current is None or (current.get("source_table") != "STEP_TIME"
                               and item.get("source_table") == "STEP_TIME"):
            selected[step] = dict(item)
    return selected


def select_steps(
    steps: dict[int, dict[str, Any]], *, max_steps: int = MAX_AUTO_STEPS,
) -> tuple[list[int], str, list[int], list[dict[str, Any]]]:
    """Select post-warmup steady step IDs and explain the selection basis."""
    ordered = sorted(steps)
    if not ordered:
        return [], "", [], []
    limitations: list[dict[str, Any]] = []
    if len(ordered) >= 4:
        samples = [
            StepSample(step=step, wall_ms=float(
                (steps[step]["end_ns"] - steps[step]["start_ns"]) / 1_000_000.0))
            for step in ordered if step != ordered[0]
        ]
        steady = detect_steady_window(
            samples, config=SteadyStateConfig(
                relative_tolerance=STEADY_TOLERANCE, min_steady_steps=3))
        if steady.status == STEADY and steady.steady_steps:
            chosen = [step for step in ordered if step in set(steady.steady_steps)][:max_steps]
            if chosen:
                warmup = [step for step in ordered if step < min(chosen)]
                return chosen, "native_step_auto_steady", warmup, limitations
    if len(ordered) >= 2:
        chosen = ordered[1:1 + max_steps]
        return chosen, "native_step_auto_post_warmup", [ordered[0]], limitations
    limitations.append({
        "severity": "medium",
        "code": "single_native_step_warmup_unexcluded",
        "message": "Only one native step exists; warmup cannot be distinguished from steady state.",
    })
    return ordered[:1], "native_step_auto_single", [], limitations


def resolve_auto_step_windows(
    root: str | Path, sources: Sequence[Any], *,
    max_steps: int = MAX_AUTO_STEPS, timeout_s: float = 5.0,
) -> tuple[dict[str, list[Window]], dict[str, Any]]:
    """Resolve one local-clock window list per rank for common native step IDs."""
    if not sources:
        raise ProfilerUsageError("auto-step requires at least one discovered rank source")
    per_rank: dict[str, dict[int, dict[str, Any]]] = {}
    table_by_rank: dict[str, str] = {}
    deadline = time.perf_counter() + max(0.1, float(timeout_s)) * max(1, len(sources))
    for source in sources:
        if time.perf_counter() > deadline:
            raise ProfilerUsageError("auto-step native marker discovery exceeded the query budget")
        windows, table = _native_windows_for_source(
            source, timeout_s=max(0.1, float(timeout_s)))
        per_rank[source.rank_id] = _steps_by_id(windows)
        table_by_rank[source.rank_id] = table
    common = set.intersection(*(set(items) for items in per_rank.values())) if per_rank else set()
    if not common:
        missing = ", ".join(
            f"{rank}={sorted(items)}" for rank, items in sorted(per_rank.items()))
        raise ProfilerUsageError(
            "auto-step found no common native STEP_TIME/ProfilerStep# step IDs across "
            f"selected ranks ({missing}). Pass --step-window STEP=START:END with local "
            "timestamps, or --full-range for the whole capture.")
    representative = per_rank[sources[0].rank_id]
    chosen, basis, warmup, limitations = select_steps(
        {step: representative[step] for step in common}, max_steps=max_steps)
    coverage_gap = {
        rank: sorted(common - set(items)) for rank, items in per_rank.items()
        if common - set(items)
    }
    if coverage_gap:
        raise ProfilerUsageError(
            "auto-step rank coverage is incomplete for the selected steps: "
            + ", ".join(f"{rank}=missing{steps}" for rank, steps in sorted(coverage_gap.items()))
            + "; pass explicit per-rank --step-window bounds instead.")
    windows_by_rank: dict[str, list[Window]] = {}
    for source in sources:
        rank_windows: list[Window] = []
        for step in chosen:
            item = per_rank[source.rank_id][step]
            rank_windows.append(Window(
                start_ns=int(item["start_ns"]), end_ns=int(item["end_ns"]),
                step=int(step), label=f"step={int(step)}",
                source=str(item.get("source_table") or "STEP_TIME"),
                clock=None,
            ))
        windows_by_rank[source.rank_id] = rank_windows
    provenance = {
        "mode": "auto_step",
        "selection_basis": basis,
        "source_table": table_by_rank.get(sources[0].rank_id),
        "source_tables": dict(sorted(table_by_rank.items())),
        "selected_steps": list(chosen),
        "warmup_excluded_steps": list(warmup),
        "native_step_count": len(common),
        "rank_count": len(sources),
        "window_scope": "per_rank_local_clock",
        "clock_alignment_declared": False,
        "limitations": limitations,
    }
    return windows_by_rank, provenance


def _discovered_steps(root: Path, ranks: Sequence[str] | None, timeout_s: float) -> tuple[list[int], dict[int, dict[str, Any]], str]:
    try:
        inventory = inventory_profile(root, timeout_s=timeout_s)
    except TimeoutError:
        raise
    except Exception:
        return [], {}, ""
    rank_rows = list(inventory.get("ranks") or ())
    if ranks:
        wanted = {str(item) for item in ranks}
        rank_rows = [row for row in rank_rows if str(row.get("rank_id")) in wanted] or rank_rows
    merged: dict[int, dict[str, Any]] = {}
    for row in rank_rows:
        for step, item in _steps_by_id(row.get("native_step_windows") or ()).items():
            merged.setdefault(step, item)
    return sorted(merged), merged, str(inventory.get("root") or root)


def format_missing_window_error(
    root: str | Path, ranks: Sequence[str] | None = None, *, timeout_s: float = _AUTO_PROBE_TIMEOUT_S,
) -> str:
    """Actionable usage error: discovered steps plus exact copy-pasteable commands."""
    path = Path(root).expanduser()
    head = ("analyze requires an explicit window selection (--auto-step, "
            "--step-window STEP=START:END, --steps-file, --window START:END, "
            "or --full-range).")
    try:
        steps, by_id, resolved_root = _discovered_steps(
            path, ranks, max(0.1, float(timeout_s)))
    except TimeoutError:
        raise
    except Exception:
        steps, by_id, resolved_root = [], {}, str(path)
    if not steps:
        return (
            f"{head}\nNo native STEP_TIME / ProfilerStep# markers were found in {path}.\n"
            f"  Whole capture: mindie-profiler analyze --root {path} --full-range\n"
            f"  Explicit span: mindie-profiler analyze --root {path} --window START:END --unit us"
        )
    chosen, _, _, _ = select_steps(by_id)
    steady = chosen or steps[:1]
    span = by_id[steady[0]]
    commands = [
        f"  Recommended steady-state: mindie-profiler analyze --root {path} --auto-step",
        (f"  Explicit step window:     mindie-profiler analyze --root {path} "
         f"--step-window {steady[0]}={span['start_ns']}:{span['end_ns']} --unit ns"),
        f"  Whole capture (w/ warmup): mindie-profiler analyze --root {path} --full-range",
    ]
    return (
        f"{head}\nDiscovered {len(steps)} native steps ({steps[0]}..{steps[-1]}; "
        f"post-warmup steady candidates: {steady[0]}..{steady[-1]}) in {resolved_root}:\n"
        + "\n".join(commands)
    )


def collect_rank_observations_parallel(
    sources: Sequence[Any],
    windows_by_rank: dict[str, list[Window]] | None,
    *,
    reader: Callable[[Any, list[Window] | None], Any],
    jobs: int | None = None,
) -> list[Any]:
    """Read each rank with its own local windows and deterministic ordering."""
    return parallel_map(
        sources,
        lambda item: reader(
            item, windows_by_rank.get(item.rank_id) if windows_by_rank else None),
        jobs=jobs,
    )


def parallel_map(items: Sequence[Any], worker: Callable[[Any], Any], *, jobs: int | None = None) -> list[Any]:
    """Run ``worker`` over items with deterministic ordering and bounded threads."""
    resolved = _resolve_jobs(jobs, len(items))
    if resolved <= 1 or len(items) <= 1:
        return [worker(item) for item in items]
    with ThreadPoolExecutor(max_workers=resolved) as pool:
        return list(pool.map(worker, items))


__all__ = [
    "MAX_AUTO_STEPS", "collect_rank_observations_parallel",
    "format_missing_window_error", "parallel_map",
    "resolve_auto_step_windows", "select_steps",
]
