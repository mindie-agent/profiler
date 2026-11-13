"""CLI entry point for ``mindie-profiler capture`` (CANN 9.x native collector).

[Role]
  Parse CLI options for launch, standby-prepare, and live-attach steady-state
  NPU captures and emit ``mindie-native-capture/1`` JSON receipts.

[Invariants]
  * Returns exit code 0 only when ``status`` is ``completed`` or
    ``standby_ready``; returns 1 on runtime capture failure and 2 on usage
    errors.
  * Target command arguments after ``--`` are passed verbatim without shell
    interpolation.

[Timeouts & Locks]
  Delegates strict ``outer >= sum(inner) + grace`` budgets to ``native_capture``.

[Side-Effect Policy]
  Writes session outputs under ``--output-dir`` and optional ``--output`` JSON.
"""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .events import ProfilerUsageError
from .native_capture import capture_profile, prepare_standby_session
from .native_capture_shm import AICORE_METRICS_MAP
from .report import write_report


def build_capture_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler capture",
        description=(
            "CANN 9.x framework-agnostic steady-state NPU collector "
            "(Gear 1: MSPTI fast summary; Gear 2: sniper aclprof + C7 report)."
        ),
        allow_abbrev=False,
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--attach",
        dest="attach_session_id",
        default=None,
        help="attach to an existing STANDBY /dev/shm session id",
    )
    mode_group.add_argument(
        "--prepare-session",
        dest="prepare_session_id",
        default=None,
        help="create a persistent STANDBY /dev/shm session and print preload env JSON",
    )
    parser.add_argument(
        "--gear",
        choices=("fast", "deep"),
        default="fast",
        help="capture gear: 'fast' (MSPTI, zero msprof) or 'deep' (sniper aclprof + C7)",
    )
    parser.add_argument("--cann-root", default=None, help="explicit CANN 9.x root path")
    parser.add_argument("--output-dir", default=None, help="directory for worker/PROF artifacts")
    parser.add_argument("--output", "-o", default=None, help="write JSON receipt here (atomic)")
    parser.add_argument("--shm-dir", default=None, help="override /dev/shm directory")
    parser.add_argument("--cache-root", default=None, help="override compiled shim cache directory")
    parser.add_argument("--min-warmup-steps", type=int, default=5, help="minimum warmup steps before gate")
    parser.add_argument("--steady-window-steps", type=int, default=5, help="consecutive steps in CV gate window")
    parser.add_argument("--steps", dest="target_capture_steps", type=int, default=10, help="steady steps to capture")
    parser.add_argument("--max-cv-pct", type=float, default=15.0, help="maximum step-duration CV%% for gate lock")
    parser.add_argument("--replays-per-step", type=int, default=1, help="NPUGraph replays per logical model step")
    parser.add_argument(
        "--allow-alloc-churn",
        dest="require_zero_alloc_steps",
        action="store_false",
        help="allow aclrtMalloc calls inside steady gate window",
    )
    parser.add_argument("--min-step-interval-us", type=float, default=50.0, help="minimum eager sync interval in us")
    parser.add_argument("--expected-workers", type=int, default=1, help="number of NPU workers to coordinate")
    parser.add_argument("--coordinated", action="store_true", default=None, help="force coordinated /dev/shm barrier")
    parser.add_argument(
        "--aicore-metrics",
        choices=tuple(sorted(AICORE_METRICS_MAP)),
        default="pipe_utilization",
        help="Gear-2 AICore PMU metric group",
    )
    parser.add_argument(
        "--terminate-after-capture",
        action="store_true",
        help="send SIGTERM to launched command immediately once all workers finish capturing",
    )
    parser.add_argument("--warmup-timeout-s", type=float, default=120.0)
    parser.add_argument("--capture-timeout-s", type=float, default=60.0)
    parser.add_argument("--export-timeout-s", type=float, default=90.0)
    parser.add_argument("--cleanup-grace-s", type=float, default=10.0)
    parser.add_argument("--outer-timeout-s", type=float, default=None)
    parser.add_argument("--top", type=int, default=12, help="hotspot rows retained per worker")
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="target command after '--' (launch mode)",
    )
    return parser


def main(argv: Sequence[str]) -> int:
    args = build_capture_parser().parse_args(list(argv))
    cmd = list(args.command or [])
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]

    if args.prepare_session_id:
        if cmd:
            raise ProfilerUsageError("--prepare-session does not accept a target command")
        if not args.output_dir:
            raise ProfilerUsageError("--prepare-session requires --output-dir")
        payload = prepare_standby_session(
            args.prepare_session_id,
            output_dir=args.output_dir,
            gear=args.gear,
            cann_root=args.cann_root,
            shm_dir=args.shm_dir,
            cache_root=args.cache_root,
        )
        if args.output:
            write_report(payload, args.output)
            print(
                json.dumps(
                    {"output": args.output, "status": payload["status"], "session_id": payload["session_id"]},
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.attach_session_id and cmd:
        raise ProfilerUsageError("--attach cannot be combined with a target command")
    if not args.attach_session_id and not cmd:
        raise ProfilerUsageError(
            "capture requires either '-- <command...>' (launch mode), '--attach <id>', or '--prepare-session <id>'"
        )

    report = capture_profile(
        command=cmd if cmd else None,
        attach_session_id=args.attach_session_id,
        output_dir=args.output_dir,
        output=args.output,
        gear=args.gear,
        cann_root=args.cann_root,
        shm_dir=args.shm_dir,
        cache_root=args.cache_root,
        min_warmup_steps=args.min_warmup_steps,
        steady_window_steps=args.steady_window_steps,
        target_capture_steps=args.target_capture_steps,
        max_cv_pct=args.max_cv_pct,
        replays_per_step=args.replays_per_step,
        require_zero_alloc_steps=bool(args.require_zero_alloc_steps),
        min_step_interval_us=args.min_step_interval_us,
        expected_workers=args.expected_workers,
        coordinated=args.coordinated,
        aicore_metrics=args.aicore_metrics,
        terminate_after_capture=bool(args.terminate_after_capture),
        warmup_timeout_s=args.warmup_timeout_s,
        capture_timeout_s=args.capture_timeout_s,
        export_timeout_s=args.export_timeout_s,
        cleanup_grace_s=args.cleanup_grace_s,
        outer_timeout_s=args.outer_timeout_s,
        top_n=args.top,
    )
    if args.output:
        print(
            json.dumps(
                {
                    "output": args.output,
                    "schema_version": report["schema_version"],
                    "status": report["status"],
                    "gear": report["gear"],
                    "worker_count": report["worker_count"],
                    "transient_contaminated": report["transient_contaminated"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "completed" else 1
