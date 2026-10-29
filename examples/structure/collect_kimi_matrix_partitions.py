"""Retain complete MatMulV3 ABI partitions inside previously accepted Kimi bodies.

[Role] Fill the saved two-example evidence gap with one targeted local CSV pass.
[Invariants] Accepted windows and geometry are reused exactly; no new bodies,
  layer-order guesses, timing-based role assignment, or changed Body statistics.
  Native ABI and topology region are retained even when semantic role is unknown.
[Timeouts & Locks] One bounded body buffer; one source at a time; no locks.
[Side-Effect Policy] Read local captures and declarations, write new evidence only.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import resource
import sys
import time

from mindie_profiler.decode_segmentation import _align, _anchor, _model, _norm, _norm_start, _Row
from mindie_profiler.events import Observation, QueryStats, SourceRef, Window
from mindie_profiler.normalized import kernel_rows, row_from_event, shapes
from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_sim.prediction.structure import parse_case
from mindie_sim.structure import export_structure
from replay_body_operator_families import RoleMapper, declared_role, duration_stats, identity, read, runtime_identity, write
from diagnose_kimi_family_gap import canonical


def selected_geometry(value):
    return tuple(value[k] for k in ("tokens_per_sequence", "sequences_per_replica", "query_rows"))


def extract(actual_path, case_dir, output):
    started = time.perf_counter(); runtime_before = runtime_identity()
    actual = read(actual_path); actual_pin = identity(actual_path)
    body_pin = actual["body_acceptance_identity"]
    if identity(body_pin["path"]) != body_pin:
        raise ValueError("retained_body_artifact_changed")
    prior = read(body_pin["path"])
    source = actual["source_identity"]; path = Path(source["path"])
    source_now = identity(path)
    if any(source_now[k] != source[k] for k in ("path", "sha256", "size_bytes")):
        raise ValueError("source_identity_changed")
    stat_before = path.stat()
    case_path = case_dir / Path(actual["case_identity"]["path"]).name
    case_pin = identity(case_path); case = parse_case(read(case_path))
    config = _model({**case.model.to_dict(), "tp": case.runtime.parallel.tp, **prior.get("segmentation_options", {})})
    geo = actual["geometry"]; key = selected_geometry(geo)
    expected = [f for f in prior["forwards"] if selected_geometry(f["geometry"]) == key]
    if len(expected) != actual["forward_count"]:
        raise ValueError("selected_forward_count_changed")
    manifest = export_structure(case, phase="decode", tokens=geo["tokens_per_sequence"],
        sequences=geo["sequences_per_replica"], context=actual["conditional_context_tokens"], scope="body")
    mapper = RoleMapper(manifest, mapping_limit=0, max_events=1_000_000, phase="decode")
    ref = SourceRef("rank_0", 0, "csv", str(path), path.name, source["sha256"], source["size_bytes"],
        source["schema_version"], "retained_complete_body_targeted_matrix_pass", mtime_ns=source.get("mtime_ns"))
    observation = Observation("rank_0", 0, Window(expected[0]["start_ns"], expected[-1]["end_ns"]),
        None, [], ref, QueryStats("rank_0", "retained_complete_body_targeted_matrix_pass"))
    partitions, total, buffer, counts = {}, Counter(), [], Counter()
    cursor = 0

    def close(window, rows):
        aligned, failure = _align(rows, config, cursor)
        if failure or any(aligned[field] != window[field] for field in
                          ("start_ns", "end_ns", "head_start_ns", "head_end_ns", "query_rows", "device_id")):
            raise ValueError(f"retained_window_topology_drift:{window['forward_id']}:{failure}")
        layers = [stage for stage in aligned["stages"] if stage["layer_id"] is not None]
        starts = [layer["start_ns"] for layer in layers]
        boundaries = {}
        for layer in layers:
            local = [r for r in rows if layer["start_ns"] <= r.event.start_ns < layer["evidence"]["successor_boundary_start_ns"]]
            anchor = next(r for r in local if _anchor(r, config))
            norm_index = next(i for i,r in enumerate(local) if r.event.start_ns > anchor.event.start_ns and _norm(r, config["hidden_size"]))
            boundaries[layer["layer_id"]] = anchor.event.start_ns, local[_norm_start(local, norm_index, config["hidden_size"])].event.start_ns
        ordinal = Counter()
        for row in rows:
            event = row.event
            if event.op_type != "MatMulV3" or not window["start_ns"] <= event.start_ns < window["end_ns"] or event.end_ns > window["end_ns"]:
                continue
            layer = layers[bisect_right(starts, event.start_ns)-1]
            anchor, ffn = boundaries[layer["layer_id"]]
            block = "ffn" if event.start_ns >= ffn else "attention"
            phase = "ffn" if block == "ffn" else "before_attention_anchor" if event.start_ns < anchor else "after_attention_anchor"
            ordinal[layer["layer_id"], phase] += 1
            mapper.layer, mapper.block = layer["layer_id"], block
            _, _, candidates, _, _, contract, _ = mapper.match(event, observation)
            roles = sorted({declared_role(mapper.targets[c]) for c in candidates})
            abi = native_tensor_contract(row_from_event(event))
            group_key = canonical((abi, layer["attention"], phase, ordinal[layer["layer_id"], phase], roles))
            group = partitions.setdefault(group_key, {"native_abi": abi, "contract": contract,
                "attention_kind": layer["attention"], "topology_region": phase,
                "matrix_ordinal_in_region": ordinal[layer["layer_id"], phase],
                "declared_roles": roles, "role_basis": "exact_tensor_contract_conditioned_on_verified_whole_layer" if roles else "native_abi_and_whole_layer_region_only",
                "duration_ns_counter": Counter(), "layer_counts": Counter(), "forward_counts": Counter(), "examples": []})
            group["duration_ns_counter"][event.duration_ns] += 1
            group["layer_counts"][layer["layer_id"]] += 1
            group["forward_counts"][window["forward_id"]] += 1
            total[event.duration_ns] += 1
            if len(group["examples"]) < 2:
                group["examples"].append({"locator": event.locator, "layer_id": layer["layer_id"],
                    "forward_id": window["forward_id"], "start_ns": event.start_ns, "end_ns": event.end_ns})

    previous_start = None
    for kernel in kernel_rows(path, rank_id="rank_0", rank_index=0, max_rows=5_000_000, timeout_s=180):
        event = kernel.event; counts["parsed_kernel_rows"] += 1
        if previous_start is not None and event.start_ns < previous_start:
            raise ValueError("targeted_window_pass_requires_chronological_events")
        previous_start = event.start_ns
        while cursor < len(expected) and event.start_ns > expected[cursor]["head_start_ns"]:
            close(expected[cursor], buffer); buffer = []; cursor += 1
        if cursor == len(expected):
            break
        if expected[cursor]["start_ns"] <= event.start_ns <= expected[cursor]["head_start_ns"]:
            buffer.append(_Row(event, shapes(event.input_shapes), shapes(event.output_shapes)))
            if len(buffer) > 100_000:
                raise MemoryError("body_buffer_limit_exceeded")
    if cursor < len(expected):
        close(expected[cursor], buffer); cursor += 1
    if cursor != len(expected):
        raise ValueError("retained_windows_not_all_read")
    saved = Counter()
    for family in actual["families"]:
        if family["native_operator_type"] == "MatMulV3":
            saved.update(dict(family["duration_ns_counter"]))
    if saved != total:
        raise ValueError("targeted_MatMul_population_differs_from_saved_complete_histogram")
    result_groups = []
    for group in partitions.values():
        hist = group["duration_ns_counter"]
        result_groups.append({**group, "duration_ns_counter": sorted(hist.items()),
            "layer_counts": dict(group["layer_counts"]), "forward_counts": dict(group["forward_counts"]),
            "observed_us": duration_stats(hist, 1000),
            "observed_activity_ms_per_forward": sum(ns*n for ns,n in hist.items()) / 1e6 / len(expected)})
    if runtime_identity() != runtime_before or identity(case_path) != case_pin:
        raise ValueError("targeted_pass_runtime_or_case_changed")
    if (path.stat().st_size,path.stat().st_mtime_ns) != (stat_before.st_size,stat_before.st_mtime_ns):
        raise ValueError("source_changed_during_targeted_pass")
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    if rss > 512 * 1024**2: raise MemoryError("targeted_pass_exceeds_512MiB")
    result = {"schema_version": "mindie-kimi-matrix-partitions/1", "source_case_id": actual["source_case_id"],
        "source_identity": source, "actual_identity": actual_pin, "body_acceptance_identity": body_pin,
        "case_identity": case_pin, "runtime_source_identity": runtime_before,
        "geometry": geo, "forward_count": len(expected), "matrix_event_count": sum(total.values()),
        "saved_matrix_histogram_exactly_equal": True,
        "partitions": sorted(result_groups, key=lambda g:-g["observed_activity_ms_per_forward"]),
        "execution": {**counts, "raw_targeted_scans": 1, "source_hash_reads": 1,
            "scan_end": "after_last_selected_body_head; remainder_not_parsed", "elapsed_seconds": time.perf_counter()-started,
            "maximum_resident_set_size_bytes": rss},
        "interpretation": "Full ABI partitions inside existing accepted windows; topology-conditional roles do not assert Host identity. Unknown fused projections require independent source correspondence."}
    out = output / (actual["source_case_id"] + "-matrix-partitions.json")
    write(out, result)
    print(json.dumps({"case": actual["source_case_id"], "forwards":len(expected), "events":sum(total.values()),
        "partitions":len(result_groups),"elapsed_s":result["execution"]["elapsed_seconds"],"rss":rss}),flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual", type=Path, action="append", default=[])
    parser.add_argument("--case-dir", type=Path)
    parser.add_argument("--summarize", action="store_true")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    if args.summarize:
        cases = []
        for path in sorted(args.output_dir.glob("*-matrix-partitions.json")):
            data = read(path)
            if not data["saved_matrix_histogram_exactly_equal"] or sum(
                g["observed_us"]["count"] for g in data["partitions"]) != data["matrix_event_count"]:
                raise ValueError("partition_total_drift")
            cases.append({"case_id":data["source_case_id"], "artifact_identity":identity(path),
                **{k:data[k] for k in ("source_identity","body_acceptance_identity","case_identity","geometry","execution")},
                "forwards":data["forward_count"], "matrix_events":data["matrix_event_count"],
                "partitions":len(data["partitions"]),
                "runtime_file_map_sha256":sha256(canonical(data["runtime_source_identity"]).encode()).hexdigest()})
        summary = {"sources":len(cases), "forwards":sum(c["forwards"] for c in cases),
            "matrix_events":sum(c["matrix_events"] for c in cases),
            "native_abi_topology_partitions":sum(c["partitions"] for c in cases),
            "all_saved_histograms_exactly_equal":True, "raw_targeted_scans":len(cases), "source_hash_reads":len(cases),
            "total_elapsed_s":sum(c["execution"]["elapsed_seconds"] for c in cases),
            "max_source_rss_bytes":max(c["execution"]["maximum_resident_set_size_bytes"] for c in cases)}
        write(args.output_dir/"kimi-matrix-partition-receipt.json", {
            "schema_version":"mindie-kimi-targeted-matrix-receipt/1", "cases":cases,"summary":summary,
            "interpretation":"Existing complete windows only; targeted native-family evidence, no new collection or changed Body statistics. Source roles remain conditional."})
        print(json.dumps(summary)); return
    if not args.actual or not args.case_dir:
        parser.error("targeted extraction requires actual inputs and source case directory")
    for path in args.actual:
        extract(path,args.case_dir,args.output_dir)


if __name__ == "__main__":
    main()
