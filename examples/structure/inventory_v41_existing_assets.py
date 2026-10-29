"""Inventory retained V4.1 assets without treating serving metrics as body spans.

[Role] Record local whole-model and primitive-capture availability and provenance.
[Invariants] Client TPOT and historical step measurements are not body evidence.
  Primitive captures do not prove whole-model layer occurrence or phase identity.
[Timeouts & Locks] Bounded small metadata; SQLite read-only connections use 5s timeout.
[Side-Effect Policy] Reads existing local files; writes one requested manifest only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3


BASE = Path("/Volumes/data/mindie-sim-data/a5")


def identity(path):
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    stat = path.stat()
    return {"path": str(path), "sha256": digest.hexdigest(), "size_bytes": stat.st_size}


def read_json(path):
    if path.stat().st_size > 1024 * 1024:
        raise ValueError(f"inventory_metadata_exceeds_1MiB:{path}")
    return json.loads(path.read_text())


def inventory():
    model_roots = [BASE / "2026-10-24/v41-dp4-small",
                   BASE / "2026-10-25/v41-dp4-16k-aoff", BASE / "2026-10-25/v41-dp4-64k"]
    whole = []
    for root in model_roots:
        files = [path for path in root.rglob("*") if path.is_file()] if root.exists() else []
        profiles = [path for path in files if path.name in {
            "kernel_details.csv", "op_summary.csv", "trace_view.json"} or path.suffix == ".db"]
        clients = []
        for path in sorted(files):
            if path.suffix == ".json" and path.name.startswith("p") and "matrix" in path.parts:
                value = read_json(path)
                clients.append({"source": identity(path), **{key: value.get(key) for key in (
                    "label", "model", "input_len", "output_len", "concurrency", "n_ok", "n_failed")},
                    "metric_scope": "client_serving_benchmark_not_body_forward"})
        whole.append({"root": str(root), "exists": root.exists(), "file_count": len(files),
                      "whole_model_profiling_sources": [identity(path) for path in profiles],
                      "client_runs": clients,
                      "body_forward_evidence": "available_for_review" if profiles else "missing",
                      "reason": "No kernel/event capture exists in this retained tree." if not profiles else None})
    runs = BASE / "2026-10-24/op-sweep/runs"
    families = []
    for name, summary_name in (("prof_mla", "prof_mla.json"), ("prof_dsa", "prof_dsa.json"),
                               ("prof_quant", "prof_quant.json"), ("prof_act", "prof_activation.json"),
                               ("prof_elem", "prof_elementwise.json")):
        summary_path = runs / summary_name
        summary = read_json(summary_path)
        captures = []
        for path in sorted((runs / name).rglob("kernel_details.csv")):
            if path.stat().st_size > 1024 * 1024:
                raise ValueError(f"primitive_inventory_csv_exceeds_1MiB:{path}")
            with path.open(newline="") as source:
                rows = list(csv.DictReader(source))
            database = path.with_name("ascend_pytorch_profiler.db")
            with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5)) as connection:
                tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            cell = path.relative_to(runs / name).parts[0]
            captures.append({"cell": cell, "csv": identity(path), "database": identity(database),
                             "event_rows": len(rows), "kernel_names": dict(Counter(row["Name"] for row in rows)),
                             "has_cann_api": "CANN_API" in tables, "has_pytorch_api": "PYTORCH_API" in tables,
                             "observed_tensor_descriptor_rows": sum(row.get("Input Shapes") not in {None, "", "N/A"} for row in rows),
                             "capture_scope": "primitive_microbenchmark",
                             "declared_cell": summary["cells"][cell]})
        families.append({"family": summary["family"], "source": identity(summary_path),
                         "environment": summary["env"], "captures": captures})
    probe_path = runs / "csa_probe.json"
    probe = read_json(probe_path)
    return {"schema_version": "mindie-retained-v41-assets/1",
            "inventoried_at_utc": datetime.now(timezone.utc).isoformat(),
            "whole_model_trees": whole, "primitive_families": families,
            "csa_probe": {"source": identity(probe_path), "attempts": {
                key: {"ok": value["ok"], "error": value.get("error")}
                for key, value in probe["attempts"].items()}},
            "limitations": ["No whole-model body or per-layer timing is inferred from client or step summaries.",
                            "Primitive CSV tensor descriptors are absent; geometry needs the source-pinned harness declaration.",
                            "Historical CSA failures describe that capture environment, not general A5 capability.",
                            "Engram CPU offload and async settings require the serving deployment declaration.",
                            "This read-only inventory performs no remote action or new profiling collection."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inventory()
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"whole_model_sources": sum(len(row["whole_model_profiling_sources"]) for row in result["whole_model_trees"]),
                      "primitive_captures": sum(len(row["captures"]) for row in result["primitive_families"]),
                      "csa_successful_attempts": sum(row["ok"] for row in result["csa_probe"]["attempts"].values())}))


if __name__ == "__main__":
    main()
