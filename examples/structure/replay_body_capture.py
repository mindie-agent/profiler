"""Stream an existing model capture against an independently declared sim case.

[Role] Reproduce body contract coverage without retaining raw event history.
[Invariants] Capture-wide counts are not a phase or layer assignment. The
  declared phase/tokens come from the caller's recipe, never event timing.
[Timeouts & Locks] Each CSV scan has a row/time budget; mapping has an event cap.
[Side-Effect Policy] Read-only captures and case; writes one requested report.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import time

from mindie_profiler.events import Observation, QueryStats, SourceRef, Window
from mindie_profiler.normalized import row_from_event
from mindie_profiler.sources_csv import CsvSource, probe_csv
from mindie_profiler.structure_mapping import StructureMapper
from mindie_profiler.tensor_contracts import (
    NATIVE_BODY_TYPES, observed_contract, observed_contract_diagnostic,
)


def file_hash(path):
    digest = sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replay(capture, case, *, phase, tokens, context=0, sequences=1,
           max_rows=1_000_000, timeout_s=120, mapping_limit=4,
           lowerings=None, lowering_source=None, mapping_output=None):
    from mindie_sim.structure import export_structure

    started = time.perf_counter()
    capture, case = Path(capture).resolve(), Path(case).resolve()
    schema = probe_csv(capture)
    source = CsvSource(schema, rank_id="rank_0", rank_index=0)
    stats = QueryStats("rank_0", "capture_bounds", budget=max_rows)
    start, end = None, None
    for event in source.iter_events(max_rows=max_rows, timeout_s=timeout_s,
                                    stats=stats, strict=True):
        start = event.start_ns if start is None else min(start, event.start_ns)
        end = event.end_ns if end is None else max(end, event.end_ns)
    if start is None:
        raise ValueError("capture contains no positive-duration events")
    if case.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("case exceeds the bounded metadata budget")
    case_data = json.loads(case.read_text())
    declaration_source = {"case_path": str(case), "case_sha256": file_hash(case)}
    if lowerings:
        selected = case_data.setdefault("runtime", {}).setdefault("kernels", {}).setdefault(
            "lowerings", {})
        selected.update(lowerings)
        declaration_source["implementation_overrides"] = dict(lowerings)
        declaration_source["implementation_source"] = lowering_source
        declaration_source["override_basis"] = "caller_declared_implementation_selection"
    declared = export_structure(
        case_data, phase=phase, tokens=tokens,
        context=context, sequences=sequences, scope="model",
        source=declaration_source,
    )
    source_ref = SourceRef(
        rank_id="rank_0", rank_index=0, kind="csv", path=str(capture),
        basename=capture.name, sha256=file_hash(capture),
        size_bytes=capture.stat().st_size, mtime_ns=capture.stat().st_mtime_ns,
        schema_version=schema.schema_version, schema_variant=schema.schema_variant,
        header_sha256=schema.header_sha256, optional_missing=schema.optional_missing,
    )
    observed = Observation(
        "rank_0", 0, Window(start, end, label="complete_capture_mixed_phase_possible"),
        None, [], source_ref, stats,
    )
    mapper = StructureMapper(declared, mapping_limit=mapping_limit, max_events=max_rows)
    body_types = NATIVE_BODY_TYPES | set(mapper.target_index.native_implementations)
    examples = {}
    examples_per_type = Counter()
    example_budget = 4 * len(body_types)

    def events_with_examples():
        for event in source.iter_events(max_rows=max_rows, timeout_s=timeout_s, strict=True):
            if event.op_type in body_types and examples_per_type[event.op_type] < 4:
                row = row_from_event(event)
                contract = observed_contract(row)
                key = (
                    row.kind, contract[0] if contract is not None else None,
                    len(mapper.contracts.get(contract, ())),
                    observed_contract_diagnostic(row)["reason"] if contract is None else None,
                )
                if key not in examples:
                    examples[key] = event
                    examples_per_type[event.op_type] += 1
            yield event

    window = mapper.map_window(observed, events=events_with_examples())
    result = mapper.finish([window])
    if mapping_output is not None:
        Path(mapping_output).write_text(json.dumps(result, indent=2) + "\n")
    # Remap a bounded representative subset through the same matcher. These
    # examples do not enter the complete-window counters a second time.
    sample_mapper = StructureMapper(
        declared, mapping_limit=example_budget, max_events=max(1, example_budget))
    sample_mapper.map_window(observed, events=examples.values())
    body = [row for row in window["operators"] if row["operator_type"] in body_types]
    body_statuses = {
        status: sum(row["status_counts"].get(status, 0) for row in body)
        for status in ("bound", "candidate", "ambiguous", "unmapped")
    }
    return {
        "kind": "historical_full_capture_body_contract_replay",
        "not_new_live_collection": True,
        "source_identity": source_ref.content_identity(),
        "declaration_source": declared["source"],
        "model": declared["model"]["name"],
        "graph_id": declared["graph_id"],
        "declared_execution": declared["execution"],
        "observed_phase": None,
        "capture_bounds_ns": [start, end],
        "raw_rows": stats.rows_read,
        "positive_event_count": result["event_window_count"],
        "status_counts": result["status_counts"],
        "diagnostic_counts": result["diagnostic_counts"],
        "reason_counts": result["reason_counts"],
        "body_contracts": {
            "event_count": sum(row["event_count"] for row in body),
            "contract_available_events": sum(row["contract_available_events"] for row in body),
            "status_counts": body_statuses,
            "operators": body,
        },
        "other_operators": [row for row in window["operators"]
                            if row["operator_type"] not in body_types],
        "declaration_coverage": {
            "node_count": len(declared["nodes"]),
            "contracted_node_count": sum(
                node.get("contract") is not None for node in declared["nodes"]),
            "node_families": dict(Counter(node["family"] for node in declared["nodes"])),
            "subgraph_count": len(declared.get("subgraphs", ())),
            "contracted_subgraph_count": sum(
                row.get("contract") is not None for row in declared.get("subgraphs", ())),
            "subgraph_roles": dict(Counter(
                row["role"] for row in declared.get("subgraphs", ()))),
        },
        "structural_groups": window["structural_groups"],
        "cohorts": window["cohorts"],
        "cohort_event_count": result["cohort_event_window_count"],
        "cohort_excluded_event_counts": window["cohort_excluded_event_counts"],
        "bound_subgraphs": window["subgraphs"],
        "bound_layers": window["layers"],
        "bound_busy_union_ns": window["bound_busy_union_ns"],
        "retained_examples": result["event_mappings"],
        "retained_body_examples": sample_mapper.sample,
        "body_example_selection": (
            "First event per native type, comparison family, candidate count and missing reason; "
            "at most four examples per declared or supported native body type, "
            "separate from complete-window denominators."),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "limitations": [
            "One selected rank is scanned completely; this does not prove other ranks were collected.",
            "The declared execution is one comparison hypothesis, not an inferred event phase.",
            "Tensor candidates do not prove model identity, layer identity or selected scalar flags.",
            "No Host/module occurrence scopes are supplied in this replay; no automatic binding is expected.",
            "Native ABI and active projections have different comparison scopes, preserved per event.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--phase", required=True, choices=("prefill", "decode"))
    parser.add_argument("--tokens", required=True, type=int)
    parser.add_argument("--context", type=int, default=0)
    parser.add_argument("--sequences", type=int, default=1)
    parser.add_argument("--max-rows", type=int, default=1_000_000)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--lowering", action="append", default=[],
                        metavar="SELECTOR=IMPLEMENTATION")
    parser.add_argument("--lowering-source",
                        help="Independent source for the caller's implementation declaration")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mapping-output", type=Path,
                        help="Write the complete mapping for sim cohort comparison")
    args = parser.parse_args()
    lowerings = {}
    for value in args.lowering:
        selector, separator, implementation = value.partition("=")
        if not separator or not selector or not implementation:
            parser.error("--lowering requires SELECTOR=IMPLEMENTATION")
        lowerings[selector] = implementation
    report = replay(
        args.capture, args.case, phase=args.phase, tokens=args.tokens,
        context=args.context, sequences=args.sequences,
        max_rows=args.max_rows, timeout_s=args.timeout,
        lowerings=lowerings, lowering_source=args.lowering_source,
        mapping_output=args.mapping_output,
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in (
        "model", "raw_rows", "positive_event_count", "status_counts", "elapsed_seconds",
    )}))


if __name__ == "__main__":
    main()
