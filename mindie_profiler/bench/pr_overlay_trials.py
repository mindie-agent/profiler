"""ABBA trial execution helpers for the ephemeral PR-overlay A/B harness.

[Role]
  Run one ABBA schedule across the ``base``/``pr`` overlay arms, pair the
  per-trial arm durations, and execute a child command in its own per-arm
  process.  ``pr_overlay`` re-exports these names as its public facade.

[Invariants]
  * A child exit status other than zero is never reported as success; when the
    child prints a JSON receipt, its device-timed ``duration_ms`` /
    ``minimum_ms`` and explicit ``outputs_ok`` / ``validated`` are honoured.
  * ``status`` is ``completed`` only for a full, failure-free schedule with at
    least one eligible pair; otherwise it is ``partial`` or ``failed``.
  * ``TimeoutError`` is always raised, never downgraded to a failed arm.

[Timeouts & Locks]
  Child commands are bounded by ``timeout_s`` (default ``GIT_TIMEOUT_SECONDS``);
  an expired child is killed and reaped before ``TimeoutError`` is raised.
  No locks are held.

[Side-Effect Policy]
  Runs caller-provided child processes under the supplied per-arm environment;
  writes no files and mutates no global state.
"""

from __future__ import annotations

import json
import math
import os
import shlex
import subprocess
import time
from statistics import median
from typing import Any, Mapping, Sequence


def _overlay():
    """Import the facade lazily so the re-export cycle stays one-directional."""
    from . import pr_overlay
    return pr_overlay


def _distribution(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "median_ms": None, "min_ms": None, "max_ms": None}
    return {"count": len(values), "median_ms": float(median(values)), "min_ms": min(values), "max_ms": max(values)}


def pair_differences(trials: Sequence[Mapping[str, Any]], *, warmup: int = 0) -> dict[str, Any]:
    """Pair base/pr durations per trial and report signed PR-minus-base deltas."""
    arms = _overlay()._ARMS
    if isinstance(warmup, bool) or not isinstance(warmup, int) or warmup < 0:
        raise ValueError("warmup must be a non-negative integer")
    grouped: dict[int, dict[str, list[dict[str, Any]]]] = {}
    for raw in trials:
        if not isinstance(raw, Mapping):
            raise ValueError(f"trial record must be a mapping, got {type(raw).__name__}")
        trial, arm, duration = raw.get("trial"), raw.get("arm"), raw.get("duration_ms")
        if isinstance(trial, bool) or not isinstance(trial, int):
            raise ValueError(f"trial record needs an integer trial, got {trial!r}")
        if arm not in arms:
            raise ValueError(f"trial record arm must be one of {arms}, got {arm!r}")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            raise ValueError(f"duration_ms must be numeric, got {duration!r}")
        value = float(duration)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"duration_ms must be finite/non-negative, got {duration!r}")
        sequence = raw.get("sequence")
        if sequence is not None and (isinstance(sequence, bool) or not isinstance(sequence, int)):
            raise ValueError(f"sequence must be an integer or None, got {sequence!r}")
        grouped.setdefault(trial, {"base": [], "pr": []})[arm].append(
            {"duration_ms": value, "sequence": sequence,
             "outputs_ok": raw.get("outputs_ok")}
        )
    trial_numbers = sorted(grouped)
    skipped = set(trial_numbers[:warmup])
    pairs: list[dict[str, Any]] = []
    deltas: list[float] = []
    relatives: list[float] = []
    base_values: list[float] = []
    pr_values: list[float] = []
    excluded: list[dict[str, Any]] = []
    counts = {"faster": 0, "slower": 0, "equal": 0}
    for trial in trial_numbers:
        if trial in skipped:
            continue
        base_records, pr_records = grouped[trial]["base"], grouped[trial]["pr"]
        sequence = next((record["sequence"] for record in base_records + pr_records
                         if record["sequence"] is not None), trial)
        if len(base_records) == 1 and len(pr_records) == 1:
            base_ms, pr_ms = base_records[0]["duration_ms"], pr_records[0]["duration_ms"]
            if (base_records[0].get("outputs_ok") is False
                    or pr_records[0].get("outputs_ok") is False):
                pair = {"trial": trial, "sequence": sequence,
                        "status": "excluded_output_mismatch",
                        "base_ms": base_ms, "pr_ms": pr_ms, "delta_ms": None,
                        "relative": None, "direction": None,
                        "outputs_ok": False}
                pairs.append(pair)
                excluded.append(pair)
                continue
            delta = pr_ms - base_ms
            relative = delta / base_ms if base_ms != 0 else None
            direction = "faster" if delta < 0 else "slower" if delta > 0 else "equal"
            counts[direction] += 1
            deltas.append(delta)
            if relative is not None:
                relatives.append(relative)
            base_values.append(base_ms)
            pr_values.append(pr_ms)
            pairs.append({
                "trial": trial, "sequence": sequence, "status": "paired",
                "base_ms": base_ms, "pr_ms": pr_ms, "delta_ms": delta,
                "relative": relative, "direction": direction,
            })
        else:
            flags = (("missing base arm", not base_records),
                     ("missing pr arm", not pr_records),
                     ("duplicate base arm records", len(base_records) > 1),
                     ("duplicate pr arm records", len(pr_records) > 1))
            reasons = [label for label, present in flags if present]
            pairs.append({
                "trial": trial, "sequence": sequence, "status": "unpaired",
                "reason": "; ".join(reasons),
                "base_ms": base_records[0]["duration_ms"] if len(base_records) == 1 else None,
                "pr_ms": pr_records[0]["duration_ms"] if len(pr_records) == 1 else None,
                "base_records": len(base_records), "pr_records": len(pr_records),
                "delta_ms": None, "relative": None, "direction": None,
            })
    return {
        "pairs": pairs,
        "unpaired": [pair for pair in pairs if pair["status"] == "unpaired"],
        "excluded": excluded,
        "excluded_output_mismatch_count": len(excluded),
        "eligible_pairs": len(deltas),
        "excluded_pairs": len(excluded),
        "paired_median_delta_ms": float(median(deltas)) if deltas else None,
        "paired_median_relative": float(median(relatives)) if relatives else None,
        "direction_counts": counts,
        "between_arm_distribution": {
            "base": _distribution(base_values),
            "pr": _distribution(pr_values),
            "delta_ms": _distribution(deltas),
        },
        "warmup": warmup,
        "excluded_trials": sorted(skipped),
    }


def run_paired_trials(plan: Mapping[str, Any], trial_runner: Any, *,
                      trials: int = 2) -> dict[str, Any]:
    """Run an ABBA schedule, stopping at the first arm failure.

    ``trial_runner(arm=, tree=, pythonpath=, env=, sequence=, trial=)`` returns
    ``duration_ms`` and optionally ``outputs_ok``.  Each arm runs in its own
    process context, so ``environment_mode`` is ``"separate_contexts"``.
    """
    overlay = _overlay()
    if not isinstance(plan, Mapping):
        raise ValueError("plan must be a mapping")
    raw_arms = plan.get("arms")
    if not isinstance(raw_arms, Mapping):
        raise ValueError("plan must contain an 'arms' mapping")
    arms = {}
    for arm in overlay._ARMS:
        payload = raw_arms.get(arm)
        if not isinstance(payload, Mapping):
            raise ValueError(f"plan is missing the {arm!r} arm")
        tree = payload.get("tree")
        pythonpath = payload.get("pythonpath", tree)
        if (not isinstance(tree, str) or not os.path.isabs(tree)
                or not isinstance(pythonpath, str) or not os.path.isabs(pythonpath)):
            raise ValueError(f"plan arm {arm!r} needs absolute tree/pythonpath values")
        arms[arm] = {"tree": tree, "pythonpath": pythonpath}
    overlay_id = overlay._token(plan.get("overlay_id") or "overlay", "overlay_id")
    schedule = overlay.abba_schedule(trials)
    classification = plan.get("classification")
    if (isinstance(classification, Mapping)
            and classification.get("verdict") == "native_rebuild_required"):
        raise ValueError("plan classification is 'native_rebuild_required'; source overlay "
                         "cannot preserve the installed compiled extensions")
    base_dir = plan.get("root")
    if base_dir is not None and not isinstance(base_dir, (str, os.PathLike)):
        raise ValueError("plan root must be a path")
    notes = ["environment_mode=separate_contexts: base and pr package revisions run in "
             "isolated processes with per-arm Triton/vLLM/extension caches"]
    records: list[dict[str, Any]] = []
    failure = ""
    for sequence, order in enumerate(schedule):
        trial_number = sequence + 1
        for arm in order:
            env = overlay.cache_environment(arm, overlay_id, base_dir=base_dir)
            try:
                outcome = trial_runner(arm=arm, tree=arms[arm]["tree"],
                                       pythonpath=arms[arm]["pythonpath"], env=env,
                                       sequence=sequence, trial=trial_number)
            except TimeoutError:
                raise
            except Exception as exc:
                failure = (f"trial {trial_number} sequence {sequence} arm {arm} failed: "
                           f"{type(exc).__name__}: {overlay._bounded(exc, overlay.MAX_STDERR_CHARS)}")
                break
            if not isinstance(outcome, Mapping):
                failure = (f"trial {trial_number} sequence {sequence} arm {arm} returned "
                           f"{type(outcome).__name__}, not a mapping")
                break
            duration = outcome.get("duration_ms")
            if (isinstance(duration, bool) or not isinstance(duration, (int, float))
                    or not math.isfinite(float(duration)) or float(duration) < 0):
                failure = (f"trial {trial_number} sequence {sequence} arm {arm} returned "
                           f"an invalid duration_ms={duration!r}")
                break
            record = {"trial": trial_number, "arm": arm,
                      "duration_ms": float(duration), "sequence": sequence}
            for key in ("outputs_ok", "wall_duration_ms", "returncode"):
                if key in outcome:
                    record[key] = outcome[key]
            records.append(record)
        if failure:
            break
    if failure:
        notes.append(failure)
    if not records:
        notes.append("no arm completed; differences are empty and unpaired")
    differences = pair_differences(records)
    if trials > 0 and differences["eligible_pairs"] == 0:
        status = "failed"
    elif failure or differences["excluded_pairs"] > 0 or len(records) < 2 * trials:
        status = "partial"
    else:
        status = "completed"
    return {"schema": overlay.TRIALS_SCHEMA, "status": status, "records": records,
            "differences": differences, "environment_mode": "separate_contexts",
            "notes": notes}


def _extract_receipt_fields(value: Mapping[str, Any]) -> tuple[float | None, Any]:
    verdict = value.get("outputs_ok", value.get("validated"))
    for key in ("duration_ms", "minimum_ms"):
        duration = value.get(key)
        if (isinstance(duration, (int, float)) and not isinstance(duration, bool)
                and math.isfinite(float(duration)) and float(duration) >= 0):
            return float(duration), verdict
    return None, verdict


def _parse_receipt(stdout: bytes) -> tuple[float | None, Any]:
    """Parse trailing compact or multiline JSON receipt into device ms and verdict."""
    text = stdout.decode("utf-8", "surrogateescape").strip()
    if not text:
        return None, None
    try:
        whole = json.loads(text)
    except ValueError:
        whole = None
    if isinstance(whole, Mapping):
        return _extract_receipt_fields(whole)
    decoder = json.JSONDecoder()
    pos = text.rfind("{")
    while pos >= 0:
        try:
            obj, end = decoder.raw_decode(text, pos)
        except ValueError:
            pos = text.rfind("{", 0, pos)
            continue
        if isinstance(obj, Mapping) and not text[end:].strip():
            return _extract_receipt_fields(obj)
        pos = text.rfind("{", 0, pos)
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, Mapping):
            return _extract_receipt_fields(value)
    return None, None


def subprocess_trial_runner(command: str, *, timeout_s: float | None = None):
    """Run one ABBA arm in its own process with the per-arm cache environment."""
    overlay = _overlay()
    argv = (command if isinstance(command, (list, tuple))
            else [part for part in shlex.split(str(command)) if part])
    if not argv:
        raise ValueError("trial command must be non-empty")
    limit = overlay.GIT_TIMEOUT_SECONDS if timeout_s is None else timeout_s

    def runner(*, arm: str, tree: str, pythonpath: str, env: Mapping[str, str],
               sequence: int, trial: int) -> dict[str, Any]:
        child_env = {**os.environ, **dict(env), "PYTHONPATH": pythonpath}
        started = time.perf_counter()
        proc = subprocess.Popen(
            list(argv), cwd=tree, env=child_env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = proc.communicate(timeout=limit)
        except subprocess.TimeoutExpired as exc:
            proc.kill()
            proc.communicate()
            raise TimeoutError(
                f"trial {trial} arm {arm} exceeded the {limit:.0f}s limit") from exc
        wall_duration_ms = (time.perf_counter() - started) * 1000.0
        device_ms, receipt_outputs = _parse_receipt(stdout)
        return {
            "duration_ms": device_ms if device_ms is not None else wall_duration_ms,
            "wall_duration_ms": wall_duration_ms,
            "returncode": proc.returncode,
            "outputs_ok": proc.returncode == 0 and receipt_outputs is not False,
            "stderr": overlay._bounded(stderr.decode("utf-8", "surrogateescape"),
                                       overlay.MAX_STDERR_CHARS),
        }

    return runner
