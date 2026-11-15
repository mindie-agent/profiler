"""Command-line entry for comparing two exported profile runs.

[Role]
Read C7 summaries or analyze two local roots with their own explicit step
windows, then produce the same comparison receipt as the Python API.
[Invariants]
Each run owns its timestamps and scene metadata. A missing workload identity
or incompatible measurement remains not_comparable in the receipt.  A receipt
whose declared p50 contradicts its own window rows is still emitted, but the
process exits 4 instead of reporting a clean success.
[Timeouts & Locks]
The analyzer applies its per-query budgets. No lock or network request is used.
[Side-Effect Policy]
Read source artifacts in place; atomically write only the requested output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .analyze import analyze_profile
from .compare import compare_profiles
from .module_trace import build_module_table
from .events import ProfilerError, ProfilerUsageError
from .report import write_report
from .segment import load_steps_file


def _json_object(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProfilerUsageError(f"{path}: expected a JSON object")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler compare",
        description="Compare C7 summaries or two roots with separate step and scene files.",
        allow_abbrev=False,
    )
    for side in ("baseline", "candidate"):
        source = parser.add_mutually_exclusive_group(required=True)
        source.add_argument(f"--{side}-summary", help="existing C7 JSON summary")
        source.add_argument(f"--{side}-root", help="profiling root, DB, or kernel_details.csv")
        parser.add_argument(f"--{side}-steps-file", help="explicit step timestamps for this run")
        parser.add_argument(f"--{side}-scene-file", help="scene metadata, including input_signature")
        parser.add_argument(f"--{side}-structure-file", help="actual operator/module structure JSON")
    parser.add_argument("--rank", action="append", default=None, help="rank filter for both roots")
    parser.add_argument("--source", choices=("auto", "db", "csv"), default="auto", help="preferred event source when analyzing raw roots (default: auto)")
    parser.add_argument("--unit", choices=("us", "ns", "ms"), default="us", help="timestamp unit for explicit steps files (default: us)")
    parser.add_argument("--max-rows", type=int, default=1_000_000, help="per-run event row cap when analyzing raw roots (default: 1000000)")
    parser.add_argument("--query-timeout-s", type=float, default=20.0, help="per-query SQLite deadline in seconds (default: 20.0)")
    parser.add_argument("--csv-timeout-s", type=float, default=30.0, help="per-file CSV scan deadline in seconds (default: 30.0)")
    parser.add_argument("--output", help="atomically write comparison JSON")
    return parser


def _file_ref(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    source = Path(path).expanduser()
    if not source.is_file():
        return {"path": str(source), "sha256": None, "size_bytes": None}
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(source),
        "sha256": digest.hexdigest(),
        "size_bytes": source.stat().st_size,
    }


def _input_evidence(args: argparse.Namespace, side: str, report: dict) -> dict[str, Any]:
    """Retain the raw inputs that produced this side of the comparison."""

    summary = getattr(args, f"{side}_summary")
    root = getattr(args, f"{side}_root")
    identity = report.get("source_identity") if isinstance(report.get("source_identity"), dict) else {}
    sources = identity.get("sources") if isinstance(identity.get("sources"), list) else []
    return {
        "kind": "summary" if summary else "root",
        "summary": _file_ref(summary),
        "root": str(Path(root).expanduser()) if root else None,
        "steps_file": _file_ref(getattr(args, f"{side}_steps_file")),
        "scene_file": _file_ref(getattr(args, f"{side}_scene_file")),
        "structure_file": _file_ref(getattr(args, f"{side}_structure_file")),
        "scene": dict(report.get("scene") or {}) if isinstance(report.get("scene"), dict) else {},
        "source_identity": {
            "source_kind": identity.get("source_kind"),
            "parser_version": identity.get("parser_version"),
            "exporter_schema_version": identity.get("exporter_schema_version"),
            "sources": [
                {
                    key: item.get(key)
                    for key in (
                        "rank_id", "kind", "basename", "path", "sha256",
                        "size_bytes", "mtime_ns", "schema_version",
                    )
                }
                for item in sources if isinstance(item, dict)
            ],
        },
    }


def _structure_object(path: str) -> dict:
    value = _json_object(path)
    structure = value.get("structure") if isinstance(value.get("structure"), dict) else value
    if not isinstance(structure, dict):
        raise ProfilerUsageError(f"{path}: expected a structure object")
    return structure


def _read_side(args: argparse.Namespace, side: str) -> dict:
    summary = getattr(args, f"{side}_summary")
    steps = getattr(args, f"{side}_steps_file")
    scene = getattr(args, f"{side}_scene_file")
    structure_file = getattr(args, f"{side}_structure_file")
    if summary:
        if steps or scene:
            raise ProfilerUsageError(f"--{side}-summary already contains its step and scene evidence")
        report = _json_object(summary)
    else:
        if not steps:
            raise ProfilerUsageError(f"--{side}-root requires --{side}-steps-file")
        report = analyze_profile(
            getattr(args, f"{side}_root"),
            ranks=args.rank,
            windows=load_steps_file(steps, unit=args.unit),
            source=args.source,
            scene=_json_object(scene) if scene else None,
            max_rows=args.max_rows,
            query_timeout_s=args.query_timeout_s,
            csv_timeout_s=args.csv_timeout_s,
        )
    if structure_file:
        report["structure"] = _structure_object(structure_file)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        baseline = _read_side(args, "baseline")
        candidate = _read_side(args, "candidate")
        result = compare_profiles(
            baseline, candidate, require_binding=True, require_input_identity=True,
        )
        baseline_structure = baseline.get("structure")
        candidate_structure = candidate.get("structure")
        if isinstance(baseline_structure, dict) and isinstance(candidate_structure, dict):
            module_table = build_module_table(baseline_structure, candidate_structure)
            # Keep the table visible even when the structure files contain no
            # modules; silently omitting it would turn a missing mapping into a
            # clean-looking comparison.
            result.setdefault("tables", {})["modules"] = module_table
            result["module_scope"] = module_table["scope"]
            if module_table["status"] != "comparable":
                result.setdefault("limitations", []).append({
                    "code": "module_table_not_comparable",
                    "message": "module structure table is present but not fully comparable",
                    "source": "module_table",
                    "details": {
                        "status": module_table["status"],
                        "module_count": len(module_table["modules"]),
                    },
                })
                if result.get("comparable"):
                    result["partial"] = True
                    if result.get("status") == "comparable":
                        result["status"] = "comparable_with_limitations"
        result["input_evidence"] = {
            "baseline": _input_evidence(args, "baseline", baseline),
            "candidate": _input_evidence(args, "candidate", candidate),
        }
        result["generated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if args.output:
            write_report(result, args.output)
            print(json.dumps({"output": args.output, "status": result["status"]}))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except TimeoutError:
        raise
    except (ProfilerError, OSError, ValueError) as exc:
        print(f"mindie-profiler compare: {exc}", file=sys.stderr)
        return 2
    if not result.get("comparable"):
        return 3
    if result.get("applicability", {}).get("report_integrity") == "failed":
        return 4
    return 0
