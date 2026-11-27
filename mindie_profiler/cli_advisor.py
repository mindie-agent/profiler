"""Product advisor commands: ``version``, ``doctor`` and ``remote-guide``.

[Role]
  Publish machine-readable package/environment readiness and the exact
  in-place remote workflow for multi-GB Ascend captures, plus confined bundle
  staging for a remote host.
[Invariants]
  * No command imports ``torch``/``torch_npu`` or initializes a CANN context.
  * ``remote-guide`` never recommends copying raw ``msprof`` directories and
    emits the complete C16 ``export-sim-case`` argv (phase and runtime facts).
  * ``--stage-dir`` refuses ``/``, ``$HOME``, the current directory and the
    package/repository source; only an owned leaf is created and populated.
[Timeouts & Locks]
  Bounded local metadata reads only; no locks, network or subprocesses.
[Side-Effect Policy]
  ``doctor``/``version`` write nothing; ``remote-guide`` writes only the
  explicitly requested confined stage directory.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any, Sequence

from . import __version__
from .events import ProfilerUsageError

PACKAGE_NAME = "mindie-profiler"


def _json_print(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _host_ram_gib() -> float | None:
    try:
        if sys.platform.startswith("linux"):
            for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                if line.startswith("MemTotal:"):
                    return round(int(line.split()[1]) / 1024.0 / 1024.0, 3)
        value = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        return round(float(value) / 1024.0**3, 3)
    except TimeoutError:
        raise
    except (OSError, ValueError, AttributeError):
        return None


def _catalog_facts() -> dict[str, Any]:
    try:
        from .op_api_registry import operator_names

        names = operator_names()
        return {"present": True, "operator_count": len(names)}
    except TimeoutError:
        raise
    except Exception as exc:  # missing/invalid packaged catalog is degraded
        return {"present": False, "operator_count": 0, "error": type(exc).__name__}


def _sim_facts() -> dict[str, Any]:
    import importlib.util

    try:
        spec = importlib.util.find_spec("mindie_sim")
    except (ModuleNotFoundError, ValueError):
        spec = None
    if spec is None:
        return {
            "installed": False,
            "optional": True,
            "version": None,
            "structure_api_ready": False,
            "cohort_comparison_ready": False,
        }
    try:
        from importlib import metadata as importlib_metadata

        ver = importlib_metadata.version("mindie-sim")
    except TimeoutError:
        raise
    except Exception:
        ver = None
    return {
        "installed": True,
        "optional": True,
        "version": ver,
        "structure_api_ready": importlib.util.find_spec("mindie_sim.structure") is not None,
        "cohort_comparison_ready": importlib.util.find_spec("mindie_sim.cohort_accuracy") is not None,
    }


def _ijson_facts() -> dict[str, Any]:
    try:
        import ijson
    except ImportError:
        return {"installed": False, "backend": None}
    return {"installed": True, "backend": getattr(ijson, "backend", None)}


def version_report() -> dict[str, Any]:
    return {
        "package": PACKAGE_NAME,
        "version": __version__,
        "python": platform.python_version(),
    }


def doctor_report() -> dict[str, Any]:
    cpu_count = os.cpu_count()
    ram = _host_ram_gib()
    catalog = _catalog_facts()
    sim = _sim_facts()
    ijson_facts = _ijson_facts()
    sqlite_ok = tuple(int(part) for part in sqlite3.sqlite_version.split(".")) >= (3, 31, 0)
    advisory = None
    if (cpu_count or 1) <= 4 or (ram is not None and ram < 8.0):
        advisory = (
            "This host is small for multi-rank analysis: run inventory/analyze/"
            "export-sim-case in place on the remote Ascend host via remote-dev "
            "with --jobs auto, and keep multi-GB captures on their source host.")
    status = "ok" if catalog["present"] and sqlite_ok else "degraded"
    return {
        "status": status,
        "package": PACKAGE_NAME,
        "version": __version__,
        "python_version": platform.python_version(),
        "sqlite_version": sqlite3.sqlite_version,
        "sqlite_cte_ready": sqlite_ok,
        "cpu_count": cpu_count,
        "host_ram_gib": ram,
        "ijson_backend": ijson_facts,
        "op_api_catalog": catalog,
        "mindie_sim_bridge": sim,
        "cann_msprof_cli": {"msprof_on_path": bool(shutil.which("msprof"))},
        "recommended_jobs": max(1, min(8, cpu_count or 4)),
        "compute_placement_advisory": advisory,
        "device_context": "none: offline analysis never initializes NPU runtime",
    }


def _protected_stage_roots() -> list[tuple[Path, bool]]:
    cwd = Path.cwd().resolve()
    return [
        (Path("/").resolve(), False),
        (Path.home().resolve(), False),
        (cwd, True),
        (Path(__file__).resolve().parent, True),
        (cwd / "mindie_profiler", True),
    ]


def _validate_stage_dir(value: str) -> Path:
    candidate = Path(value).expanduser().resolve()
    for protected, subtree in _protected_stage_roots():
        if candidate == protected or (subtree and protected in candidate.parents):
            raise ProfilerUsageError(
                f"refusing to stage into a protected root: {candidate}")
    if candidate.suffix == ".py":
        raise ProfilerUsageError(f"refusing to stage onto a Python source file: {candidate}")
    if candidate.exists() and not candidate.is_dir():
        raise ProfilerUsageError(f"stage directory is not a directory: {candidate}")
    return candidate


def _stage_bundle(stage_dir: str) -> dict[str, Any]:
    target = _validate_stage_dir(stage_dir)
    package = Path(__file__).resolve().parent
    destination = target / "mindie_profiler"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "knowledge").mkdir(parents=True, exist_ok=True)
    copied = 0
    for source in sorted(package.glob("*.py")):
        shutil.copy2(source, destination / source.name)
        copied += 1
    for name in ("op_api_catalog.json",):
        source = package / name
        if source.is_file():
            shutil.copy2(source, destination / name)
            copied += 1
    for source in sorted((package / "knowledge").glob("*.json")):
        shutil.copy2(source, destination / "knowledge" / source.name)
        copied += 1
    for pattern in ("_cann9_capture_*.c", "_cann9_capture_*.h"):
        for source in sorted(package.glob(pattern)):
            shutil.copy2(source, destination / source.name)
            copied += 1
    return {"stage_dir": str(target), "destination": str(destination), "files": copied}


def _export_argv(root: str, model: str, hardware: str, sequences: int) -> list[str]:
    return [
        "export-sim-case", root, "--rank", "auto",
        "--model", model, "--hardware", hardware, "--tp", "8",
        "--phase", "decode",
        "--concurrency", str(sequences), "--prompt-tokens", "4096", "--output-tokens", "128",
        "--max-num-seqs", str(sequences), "--max-num-batched-tokens", "32",
        "--max-model-len", "8192", "--kv-block-size", "128",
        "--enable-chunked-prefill", "--output", "/tmp/sim_case.json",
    ]


def remote_guide_report(
    root: str, *, stage_dir: str | None = None, ranks: int = 8,
    model: str = "qwen3.5-35b-a3b", hardware: str = "a3",
) -> dict[str, Any]:
    staged = _stage_bundle(stage_dir) if stage_dir else None
    sequence_count = max(1, int(ranks))
    inventory = ["inventory", "--root", root, "--jobs", "auto",
                 "--output", "/tmp/prof_inventory.json"]
    analyze = ["analyze", "--root", root, "--auto-step", "--jobs", "auto",
               "--hardware", hardware, "--output", "/tmp/prof_summary.json"]
    export = _export_argv(root, model, hardware, sequence_count)
    structure = ["structure", "/tmp/sim_case.json", "--phase", "decode", "--tokens", "1",
                 "--sequences", str(sequence_count), "--context", "4096",
                 "--output", "/tmp/structure.json"]
    closed_loop = ["analyze", "--root", root, "--auto-step", "--structure",
                   "/tmp/structure.json", "--sim-case", "/tmp/sim_case.json",
                   "--phase", "decode", "--tokens", "1", "--sequences",
                   str(sequence_count), "--context", "4096",
                   "--output", "/tmp/closed_loop.json"]
    return {
        "status": "ok",
        "bundle_staged": bool(staged),
        "stage": staged,
        "remote_profiler_execution_guide": {
            "anti_pattern_warning": (
                "NEVER copy raw multi-GB msprof / ASCEND_PROFILER_OUTPUT directories "
                "over SCP/SFTP. Always run inventory, analyze, and export-sim-case "
                "IN-PLACE on the remote Ascend host/container and transfer only the "
                "resulting KB-sized JSON summaries."),
            "step_1_discover_and_inventory_in_place": {
                "tool": "mcp__mindie-tools__remote-dev__remote_bash",
                "argv": inventory,
                "command": "mindie-profiler " + " ".join(inventory),
            },
            "step_2_steady_state_analyze_in_place": {
                "tool": "mcp__mindie-tools__remote-dev__remote_bash",
                "argv": analyze,
                "command": "mindie-profiler " + " ".join(analyze),
            },
            "step_3_export_sim_case_in_place": {
                "tool": "mcp__mindie-tools__remote-dev__remote_bash",
                "argv": export,
                "command": "mindie-profiler " + " ".join(export),
            },
            "step_4_closed_loop_sim_predict_and_cohort_compare": {
                "forward": [
                    "mindie-sim predict /tmp/sim_case.json",
                    "mindie-sim efficiency /tmp/sim_case.json",
                ],
                "reverse_structure": {
                    "argv": structure,
                    "command": "mindie-sim " + " ".join(structure),
                },
                "reverse_analyze": {
                    "argv": closed_loop,
                    "command": "mindie-profiler " + " ".join(closed_loop),
                },
                "transfer": "pull only /tmp/sim_case.json (< 30 KB) with remote_read/scp",
            },
            "compute_placement": (
                "Run heavy multi-SKU sweeps with --jobs auto on the remote multi-core "
                "host; retain large profiling captures on their source host."),
        },
    }


def version_main(argv: Sequence[str] | None = None) -> int:
    raw = list(argv or ())
    report = version_report()
    if "--json" in raw:
        _json_print(report)
    else:
        print(f"{PACKAGE_NAME} {__version__}")
    return 0


def doctor_main(argv: Sequence[str] | None = None) -> int:
    _json_print(doctor_report())
    return 0


def remote_guide_main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="mindie-profiler remote-guide",
        description="Print in-place remote profiling guidance; never copy raw captures.")
    parser.add_argument("--root", required=True, help="remote capture directory")
    parser.add_argument("--stage-dir", default=None, help="confined local bundle directory")
    parser.add_argument("--ranks", type=int, default=8, help="declared sequence/rank count")
    parser.add_argument("--model", default="qwen3.5-35b-a3b", help="declared catalog model")
    parser.add_argument("--hardware", default="a3", help="declared Ascend SKU/alias")
    args = parser.parse_args(list(argv or ()))
    return _emit_guide(args)


def _emit_guide(args: Any) -> int:
    _json_print(remote_guide_report(
        args.root, stage_dir=args.stage_dir, ranks=args.ranks,
        model=args.model, hardware=args.hardware))
    return 0


__all__ = [
    "doctor_main", "doctor_report", "remote_guide_main", "remote_guide_report",
    "version_main", "version_report",
]
