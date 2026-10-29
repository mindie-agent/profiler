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
import re
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


def source_contract(family, cell):
    """Describe the retained harness call, never manufacture observed tensors."""
    scripts = BASE / "2026-10-24/op-sweep/scripts"
    files = {"prof_mla": "bench_mla.py", "prof_dsa": "bench_dsa.py",
             "prof_quant": "bench_quant.py", "prof_act": "bench_activation.py",
             "prof_elem": "bench_elementwise.py"}
    declared = {"dtype": "bfloat16"}
    if family in {"prof_mla", "prof_dsa"}:
        phase, axis, size, kv = re.fullmatch(r"(decode|prefill)_([bq])(\d+)_kv(\d+)", cell).groups()
        batch, query = (int(size), 1) if axis == "b" else (1, int(size))
        declared.update(phase=phase, batch=batch, query_tokens=query, active_kv=int(kv),
                        query_heads=128, kv_heads=1, qk_dim=576, value_dim=512)
        if family == "prof_mla":
            declared.update(api="npu_fusion_attention", layout="BNSD" if phase == "decode" else "TND",
                            sparse_mode=3, inner_precise=0,
                            operation_boundary="dense MLA attention only; not CSA or an entire attention block")
        else:
            declared.update(api="npu_sparse_flash_attention", layout_query="TND", layout_kv="PA_BSND",
                            nonrope_dim=512, rope_dim=64, page_block_size=128, selected_indices=2048,
                            sparse_block_size=1, sparse_mode=3, attention_mode=2,
                            operation_boundary="Sparse attention only; index generation is outside profiling")
    elif family == "prof_quant":
        values = {key: int(value) for key, value in re.findall(r"(?:^|_)([mnk])(\d+)", cell)}
        declared.update(values)
        declared["output_dtype"] = "bfloat16"
        if cell.startswith("mxfp8_"):
            declared.update(api="npu_quant_matmul", dtype="float8_e4m3fn",
                            scale_dtype="float8_e8m0fnu", group_sizes=[1, 1, 32],
                            weight_layout="K,N transposed contiguous; scale[K/64,N,2]",
                            operation_boundary="MXFP8 matmul only; input/weight quantization occurs before profiling")
        else:
            declared.update(api="npu_anti_mx_quant", dtype="FP4_source_enum_296", src_type=296, dst_type=15, axis=-1,
                            operation_boundary="FP4 dequantization only; not FP4 GEMM")
    elif family == "prof_act":
        declared.update(tokens=16384, intermediate=17408, variant=cell.rsplit("_t", 1)[0],
                        fused_input_shape=[16384, 34816] if cell.startswith("swiglu_fused") else None,
                        split_input_shape=[16384, 17408] if not cell.startswith("swiglu_fused") else None,
                        gelu_approximate="tanh", operation_boundary="Activation primitive; hidden-size labels do not change this input shape")
    else:
        values = {
            "rms_norm_t16384_h7168": {"api": "npu_rms_norm", "shape": [16384, 7168], "epsilon": 1e-6},
            "rope_t16384_h7168": {"api": "npu_apply_rotary_pos_emb", "q": [1, 16384, 56, 128],
                                    "k": [1, 16384, 8, 128], "cos_sin": [1, 16384, 1, 128],
                                    "layout": "BSND", "rotary_mode": "half"},
            "softmax_t16384_v248320": {"api": "torch.softmax", "shape": [16384, 248320], "axis": -1},
            "top_k_top_p_t4096_v248320": {"api": "npu_top_k_top_p", "shape": [4096, 248320], "k": 50, "p": 0.9},
        }
        declared.update(values[cell])
    return {"status": "conditional_source_declared_contract", "harness": identity(scripts / files[family]),
            "execution_time_harness_hash_attested": False, "observed_tensor_contract": None,
            "declared": declared,
            "limitations": ["Retained harness and named capture cell agree, but capture metadata does not attest the producer source hash.",
                            "Absent observed descriptors remain absent; this is a primitive latency reference, not model-layer binding."]}


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
            repeats = summary["cells"][cell]["reps"]
            activity_us = sum(float(row["Duration(us)"].strip()) for row in rows) / repeats
            if abs(activity_us - summary["cells"][cell]["kernel_us_per_repeat"]) > 0.0051:
                raise ValueError(f"primitive_summary_activity_differs:{cell}")
            captures.append({"cell": cell, "csv": identity(path), "database": identity(database),
                             "event_rows": len(rows), "kernel_names": dict(Counter(row["Name"] for row in rows)),
                             "has_cann_api": "CANN_API" in tables, "has_pytorch_api": "PYTORCH_API" in tables,
                             "observed_tensor_descriptor_rows": sum(row.get("Input Shapes") not in {None, "", "N/A"} for row in rows),
                             "capture_scope": "primitive_microbenchmark",
                             "measured_kernel_activity_us_per_invocation": activity_us,
                             "activity_basis": "sum of raw kernel duration divided by retained invocation count; not a whole-model or multistream wall span",
                             "declared_cell": summary["cells"][cell],
                             "source_contract": source_contract(name, cell)})
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
    lines = ["# V4.1 retained primitive references", "",
             "These local microbenchmarks provide source-declared conditional geometry, not model-layer binding. Tensor descriptors and execution-time harness hashes were not captured. The JSON pins the retained source and raw CSV identities.", "",
             "Measured activity is the raw kernel-duration sum divided by invocation count; it is not a whole-model or multistream wall span. DSA excludes index generation, FP4 measures dequantization only, and dense attention is not CSA. Different source geometries cannot be treated as exact matches to the current V4.1 body declaration.", "",
             "| Family | Primitive | Invocations | Kernel events | Actual activity us/call | Source declaration |",
             "|---|---|---:|---:|---:|---|"]
    for family in result["primitive_families"]:
        for row in family["captures"]:
            declared = json.dumps(row["source_contract"]["declared"], sort_keys=True, separators=(",", ":"))
            lines.append(f"| {family['family']} | {row['cell']} | {row['declared_cell']['reps']} | "
                         f"{row['event_rows']} | {row['measured_kernel_activity_us_per_invocation']:.3f} | `{declared}` |")
    lines.extend(["", "All 8 retained CSA probes failed in that recorded environment and provide no successful latency. The retained whole-model trees contain no kernel capture; neither fact establishes a general hardware limitation.", ""])
    args.output.with_suffix(".md").write_text("\n".join(lines))
    print(json.dumps({"whole_model_sources": sum(len(row["whole_model_profiling_sources"]) for row in result["whole_model_trees"]),
                      "primitive_captures": sum(len(row["captures"]) for row in result["primitive_families"]),
                      "csa_successful_attempts": sum(row["ok"] for row in result["csa_probe"]["attempts"].values())}))


if __name__ == "__main__":
    main()
