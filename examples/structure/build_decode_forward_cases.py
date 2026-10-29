"""Build a local multi-model source index for structure-guided Decode replay.

[Role] Pair retained captures with existing Sim model declarations and request facts.
[Invariants] No manual layer/Forward boundaries; automatic alignment owns inference.
  Request input length is not the exact changing KV length of each Forward.
[Timeouts & Locks] Streaming source hashes, metadata <=5 MiB; no locks or devices.
[Side-Effect Policy] Writes the local source manifest; no remote collection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _hash(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _read(path):
    if path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError(f"metadata exceeds 5 MiB: {path}")
    return json.loads(path.read_text())


def build(data_root, sim_root, output):
    cases = []
    # These are retained campaign coordinates, never operator-shape-derived models.
    campaigns = [
        ("a3_qwen35", "a3/2026-10-23/qwen35-gdn", "qwen35-a3-tp4.json",
         ["p_4096_c1", "p_4096_c2", "p_4096_c4", "p_4096_c8", "p_16384_c1", "p_16384_c4"]),
        ("a3_qwen36", "a3/2026-10-23/qwen36-rows", "qwen36-a3-tp4.json",
         ["p_4096_c1", "p_4096_c4", "p_16384_c1", "p_16384_c4"]),
        ("a5_qwen38", "a5/2026-10-24/qwen38-c8", "qwen38-a5.json",
         ["p8192_c1", "p8192_c2", "p8192_c4", "p8192_c8", "p32768_c1", "p32768_c8"]),
        ("a3_glm53", "a3/2026-10-23/glm53-attn", "glm53-a3-w4a8.json",
         ["dc4k_b1", "dc4k_b2", "dc4k_b4", "dc4k_b8", "dc16k_b1"]),
    ]
    for key, campaign, model, labels in campaigns:
        root = data_root / campaign
        for label in labels:
            if key == "a3_glm53":
                source = root / "raw/kernels" / f"{label}.csv.gz"
                client = root / "raw" / f"{label}.json"
            elif key == "a5_qwen38":
                source = root / "raw/prof" / label / "kernel_details.csv"
                client = root / "raw/prof_meta" / f"{label}.json"
            else:
                matches = list((root / "prof" / label).rglob("kernel_details.csv"))
                if len(matches) != 1:
                    raise ValueError(f"ambiguous capture for {key}/{label}: {matches}")
                source = matches[0]
                client = root / "raw" / f"{label}.json"
            raw = _read(client)
            cases.append(_case(key + "_" + label, source, sim_root / "examples/cases" / model,
                               {"client": {"path": str(client), "sha256": _hash(client),
                                           "input_len": raw["input_len"],
                                           "concurrency": raw["concurrency"],
                                           "token_exact": raw.get("token_exact")},
                                "capture_mode": raw.get("mode", "profiled_campaign"),
                                "prefix_hit_100_percent": "not_verified",
                                "forced_load_balancing": "not_verified",
                                "acceptance_0_8": "not_verified", "dspark": "not_verified"}))
    graph_manifest = output.parent / "decode-forward-cases.json"
    if graph_manifest.exists():
        for case in _read(graph_manifest)["cases"]:
            if case["case_id"].startswith("a5_qwen36_"):
                case["sim_case_path"] = str(sim_root / "examples/cases/qwen36-a5.json")
                case["segmentation"] = "auto_structure_guided"
                case["unresolved_reasons"] = []
                case["model_declaration"] = {
                    "path": case["sim_case_path"], "sha256": _hash(Path(case["sim_case_path"])),
                    "basis": "existing_sim_catalog_and_capture_server_model_identity"}
                cases.append(case)
    kimi_receipt = output.parent / "fusion-cohort-a5_kimi_k3_decode-reference.json"
    kimi = _read(kimi_receipt)
    source = Path(kimi["source_identity"]["path"])
    if _hash(source) != kimi["source_identity"]["sha256"]:
        raise ValueError("Kimi retained source differs from completed cohort receipt")
    cases.append(_case("a5_kimi_k3_p32768_c1", source,
                       sim_root / "examples/cases/kimi-k3-a5.json", {
                           "historical_capture_provenance": str(output.parent / "model-evidence-inventory.md"),
                           "source_archive": str(data_root / "a5/2026-10-23/kimi-k3-longctx/k3lc-os1.tgz"),
                           "source_member": "raw/prof-export/op_summary_20261023053244.csv",
                           "historical_model_quantization_metadata": "incomplete",
                           "request_input_len": 32768, "request_concurrency": 1,
                           "dp_replica_placement": "single_rank_capture_not_all_dp_replicas",
                           "forced_load_balancing": "not_verified", "acceptance_0_8": "not_verified",
                           "dspark": "not_verified", "prefix_hit_100_percent": "not_verified"}))
    result = {"schema_version": "mindie-decode-forward-replay/1", "cases": cases,
              "segmentation": "auto_structure_guided", "not_new_live_collection": True,
              "notes": ["Model topology comes from Sim; observed timings never change its structure.",
                        "Forward/layer boundaries are inferred by declared topology and tensor contracts, not Host annotations.",
                        "Per-forward geometry and retained/rejected windows are reported by automatic replay."]}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return {"cases": len(cases), "output": str(output)}


def _case(case_id, source, model, scenario):
    return {
        "case_id": case_id, "source": {"path": str(source), "size_bytes": source.stat().st_size,
                                        "sha256": _hash(source)},
        "sim_case_path": str(model), "boundaries_path": None,
        "segmentation": "auto_structure_guided",
        "model_declaration": {"path": str(model), "sha256": _hash(model),
                              "basis": "existing_sim_catalog_and_capture_campaign_identity"},
        "geometry": {"phase": "decode", "tokens_per_sequence": None, "context_tokens": None,
                     "sequences_per_replica": None, "participating_replicas": None},
        "scenario_evidence": scenario, "unresolved_reasons": [],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("/Volumes/data/mindie-sim-data"))
    parser.add_argument("--sim-root", type=Path, default=Path("/Users/maoxx241/code/sim-rewrite-20261027"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("acceptance-20261029") / "decode-forward-auto-cases.json")
    args = parser.parse_args()
    print(json.dumps(build(args.data_root, args.sim_root, args.output)))
