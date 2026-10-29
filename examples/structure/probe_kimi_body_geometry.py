"""Inspect one complete Decode candidate per existing Kimi capture.

[Role] Expose valid-head versus physically padded body tensor evidence.
[Invariants] Reuse Sim's layer plan and profiler's exact current head/alignment
  rules. A diagnostic candidate does not become a scored Forward or deployment.
[Timeouts & Locks] At most 50,000 rows per source; each scan has a 30s budget.
[Side-Effect Policy] Read retained local CSVs and write one diagnostic JSON.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from math import prod
from pathlib import Path

import mindie_profiler.decode_segmentation as segmentation
from mindie_profiler.decode_segmentation import _Row, _align, _anchor, _head, _model, _PREFILL_ANCHORS
from mindie_profiler.normalized import kernel_rows


def probe(path, config):
    active, consumed = [], 0
    for row in kernel_rows(path, rank_id="rank_0", max_rows=50_000, timeout_s=30):
        consumed += 1
        if row.duration_ns <= 0:
            continue
        current = _Row(row.event, row.input_shapes, row.output_shapes)
        active.append(current)
        if not _head(current, config):
            continue
        kinds = Counter(item.kind for item in active)
        anchors = [(item, _anchor(item, config)) for item in active if _anchor(item, config)]
        if len(anchors) != config["layers"] or any(kinds[name] for name in _PREFILL_ANCHORS):
            active = []
            continue
        result, anomaly = _align(active, config, 0)
        evidence, seen, samples = [], set(), Counter()
        selected = {"AttnResFwd", "RecurrentKda", "SparseFlashAttention", "SparseFlashMla",
                    "FusedInferAttentionScore", "KvQuantSparseFlashAttention", "DynamicQuant",
                    "QuantBatchMatmulV3", "QuantBatchMatmulV4", "MatMulV3"}
        selected.update(item.kind for item, _ in anchors)
        for item in [*active, current]:
            if item.kind not in selected and item is not current:
                continue
            signature = (item.kind, item.inputs, item.outputs)
            if signature in seen or (samples[item.kind] >= 6 and item is not current):
                continue
            seen.add(signature)
            samples[item.kind] += 1
            evidence.append({"kind": item.kind, "inputs": item.inputs, "outputs": item.outputs,
                             "input_dtypes": item.event.input_dtypes,
                             "locator": item.event.locator, "is_head": _head(item, config)})
        head = {"inputs": current.inputs, "outputs": current.outputs, "locator": current.event.locator}
        recurrent_rows = sorted({prod(item.inputs[3][:2]) for item, _ in anchors
                                 if item.kind == "RecurrentKda" and len(item.inputs[3]) == 4})
        return {"status": "complete_topology_candidate", "scanned_rows": consumed,
                "candidate_event_count": len(active), "anchors": dict(Counter(kind for _, kind in anchors)),
                "candidate_first_locator": active[0].event.locator, "head": head,
                "head_query_rows": current.inputs[0][0], "kda_physical_query_rows": recurrent_rows,
                "current_alignment_status": "accepted" if result else "rejected",
                "current_alignment_anomaly": anomaly, "geometry": result.get("geometry") if result else None,
                "tensor_evidence": evidence}
    return {"status": "no_complete_decode_candidate_in_scan", "scanned_rows": consumed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-case", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from mindie_sim.prediction.structure import parse_case

    declared = parse_case(json.loads(args.model_case.read_text()))
    config = declared.model.to_dict()
    config["tp"] = 8
    config = _model(config)
    rows = []
    for concurrency in (1, 2, 4, 8, 16, 32):
        root = Path(f"/Volumes/data/mindie-sim-data/a5/kimi_k3_tp8_high_conc_decode_c{concurrency}_p4k_20261030")
        path = root / "kernel_details.csv"
        stat = path.stat()
        result = probe(path, config)
        rows.append({"case_id": root.name, "source": {"path": str(path), "size_bytes": stat.st_size,
                     "mtime_ns": stat.st_mtime_ns, "identity_basis": "path/stat diagnostic; full SHA supplied by inventory"},
                     **result})
        print(json.dumps({"case_id": root.name, "rows": result["scanned_rows"],
                          "head_m": result.get("head_query_rows"), "body_m": result.get("kda_physical_query_rows"),
                          "alignment": result.get("current_alignment_status"),
                          "reason": (result.get("current_alignment_anomaly") or {}).get("reason")}), flush=True)
    args.output.write_text(json.dumps({"schema_version": "mindie-kimi-geometry-probe/1",
        "not_a_new_capture": True, "not_a_body_accuracy_report": True,
        "model_structure_template": {"path": str(args.model_case.resolve()),
                                     "sha256": sha256(args.model_case.read_bytes()).hexdigest(),
                                     "role": "layer plan only; does not assert template DP4 deployment"},
        "alignment_core_identity": {"path": str(Path(segmentation.__file__).resolve()),
                                    "sha256": sha256(Path(segmentation.__file__).read_bytes()).hexdigest()},
        "declared_attention_layers": dict(Counter(plan["attention"] for plan in config["layer_plans"])),
        "cases": rows}, indent=2) + "\n")


if __name__ == "__main__":
    main()
