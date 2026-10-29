"""Show real matrix-contract ambiguity and whole-model topology conditioning.

[Role] Inspect two retained first-Forward GDN/GQA layer pairs against Sim structure.
[Invariants] Tensor equality alone cannot identify a layer; topology-conditioned
  candidates remain inferred, never Host/module annotations. No costs are fitted.
[Timeouts & Locks] Read bounded CSV prefixes, one metadata-only graph at a time.
[Side-Effect Policy] Local read-only captures; write compact evidence JSON/Markdown.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from mindie_profiler.normalized import kernel_rows
from mindie_profiler.tensor_contracts import observed_contract
from mindie_sim.structure import export_structure


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(base, case_dir, output):
    cases = []
    for model, tp in (("qwen36", 8), ("qwen38", 4)):
        extracted = base / f"auto-forward-a5_{model}_highconc_c4.json"
        observed = json.loads(extracted.read_text())
        case_path = case_dir / f"{model}-a5-tp{tp}-c4.json"
        structure = export_structure(json.loads(case_path.read_text()), phase="decode",
                                     tokens=4, sequences=4, context=4104)
        declarations = [{key: row[key] for key in ("node_id", "op_id", "layer", "family",
                         "block", "role", "recipe", "deps", "contract", "lineage")}
                        for row in structure["nodes"] if row["layer"] in (0, 3)
                        and row.get("contract") and row["contract"][0] == "matrix"]
        scopes = [next(row for row in observed["per_layer_ms"] if row["layer_id"] == layer)["samples"][0]
                  for layer in (0, 3)]
        limit = max(scope["evidence"]["successor_locator"]["csv_line"] for scope in scopes) + 3
        matrices, examined = [], 0
        for row in kernel_rows(observed["source_identity"]["path"], timeout_s=30):
            examined += 1
            if row.line > limit:
                break
            contract = observed_contract(row)
            if not contract or contract[0] != "matrix":
                continue
            scope = next((scope for scope in scopes if scope["start_ns"] <= row.start_ns
                          < scope["evidence"]["successor_boundary_start_ns"]), None)
            if scope is None:
                continue
            contract = json.loads(json.dumps(contract))
            candidates = [node for node in declarations if node["contract"] == contract]
            conditioned = [node for node in candidates if node["layer"] == scope["layer_id"]]
            matrices.append({"locator": row.event.locator, "event_id": row.event_id,
                             "type": row.kind, "start_ns": row.start_ns, "end_ns": row.end_ns,
                             "contract": contract, "scope_layer_id": scope["layer_id"],
                             "scope_basis": observed["basis"],
                             "tensor_only_candidates": [node["node_id"] for node in candidates],
                             "topology_conditioned_candidates": [node["node_id"] for node in conditioned],
                             "declared_roles": [node["recipe"] for node in conditioned]})
        cases.append({"case_path": str(case_path), "case_sha256": sha(case_path),
                      "graph_id": structure["graph_id"], "model_declaration": observed["model_declaration"],
                      "extraction": {"path": str(extracted), "sha256": sha(extracted)},
                      "source_identity": observed["source_identity"], "bounded_rows_examined": examined,
                      "declared_matrix_nodes": declarations, "layer_scopes": scopes, "matrix_rows": matrices})
    rows = [row for case in cases for row in case["matrix_rows"]]
    result = {"schema_version": "mindie-body-matrix-role-evidence/1",
              "basis": "tensor_contract_plus_previously_verified_whole_model_topology",
              "not_host_binding": True, "duration_used_for_candidate_selection": False,
              "scope_assignment": "observed occurrence inside previously topology-verified layer boundaries",
              "selected_layers": [0, 3], "cases": cases,
              "summary": {"matrix_occurrences": len(rows),
                          "tensor_only_ambiguous": sum(len(row["tensor_only_candidates"]) > 1 for row in rows),
                          "topology_conditioned_unique": sum(len(row["topology_conditioned_candidates"]) == 1 for row in rows)}}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    lines = ["# 矩阵角色：从完整模型到局部契约", "",
             "复用已有完整 Forward 的层窗口，仅读取两份 c4 CSV 的前缀；Sim 导出没有执行成本模型。",
             "模型层身份来自完整 64 层序列的条件推断，不能宣称 Host/module 绑定。", "",
             "| 模型 / 层 | CSV line | 实测类型 | M,N,K | 仅 tensor 候选数 | 拓扑条件后角色 |",
             "|---|---:|---|---|---:|---|"]
    for case in cases:
        for row in case["matrix_rows"]:
            lines.append(f"| {case['model_declaration']['name']} / {row['scope_layer_id']} | "
                         f"{row['locator']['csv_line']} | {row['type']} | {row['contract'][1]} | "
                         f"{len(row['tensor_only_candidates'])} | {', '.join(row['declared_roles']) or 'unresolved'} |")
    lines += ["", "Qwen3.6 的 GDN qkvz 与 GQA qkv 契约完全相同；FFN gate_up/down 在两类层中也重复。",
              "因此先验证完整层计划，再在当前层的候选子图内对账。FFN 角色与所在层的 attention 类型分开保留；不把 GDN/GQA 层里的 FFN 计为 attention。", ""]
    output.with_suffix(".md").write_text("\n".join(lines))
    return result["summary"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    base = Path(__file__).with_name("acceptance-20261030-high-concurrency")
    parser.add_argument("--base", type=Path, default=base)
    parser.add_argument("--case-dir", type=Path, default=Path("/Users/maoxx241/code/sim-rewrite-20261027/examples/cases/high-concurrency-20261030/source-gdn"))
    parser.add_argument("--output", type=Path, default=base / "matrix-role-evidence.json")
    args = parser.parse_args()
    print(json.dumps(inspect(args.base, args.case_dir, args.output)))
