"""Normal caller projection for original client-request sources.

[Role] P6/P7 declarations and human-readable summaries over the source module;
  no raw measurements in the blind declaration path.

[Invariants] P7 is per launch ordinal and carries only causal source geometry.
  P6 adds observed TTFT/stream metadata for the evaluator.  The source module
  owns parsing and identity; this module owns projection.

[Side-Effect Policy] Pure reads over source records; CLI prints JSON.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from zero_shot_client_source import (
    DEFAULT_SOURCE_ROOTS,
    P6_SCHEMA,
    P7_SCHEMA,
    SCHEMA_VERSION,
    _BOUNDARIES,
    _UNITS,
    ClientCapture,
    ClientRequest,
    ClientStream,
    iter_original_rows,
    iter_original_rows_with_sha,
)
from zero_shot_client_capture import (
    client_capture,
    iter_client_captures,
    iter_client_captures_from_jsonl,
    iter_client_requests,
)


def prediction_declaration(capture: ClientCapture) -> dict[str, Any]:
    """Cell-level blind declaration with actual base/mixed prompt classes."""
    launch = capture.launch_declaration or {}
    return {
            "cell_id": capture.cell_id, "phase": capture.phase,
            "concurrency": capture.concurrency, "prompt_tokens": capture.prompt_tokens,
            "shared_tokens": capture.shared_tokens, "fresh_tokens": capture.fresh_tokens,
            "max_tokens": capture.max_tokens,
            "seed_effective": launch.get("seed_effective"),
            "seed_basis": launch.get("seed_basis"),
            "server_chunk_budget": launch.get("server_chunk_budget"),
            "server_max_num_seqs": launch.get("server_max_num_seqs"),
            "rack": capture.producer.get("rack"),
            "producer_sha256": capture.producer.get("producer_sha256"),
            "producer_variant": capture.producer.get("producer_variant"),
            "mixed_prompt": capture.mixed_prompt,
            "mix_count": capture.mix_count,
            "declared_count": capture.declared_count,
            "declaration_status": capture.declaration_status,
            "declaration_source": capture.declaration_source,
            "prompt_classes": {
                cls: next(({
                    "prompt_tokens": item.prompt_tokens,
                    "shared_tokens": item.shared_tokens,
                    "fresh_tokens": item.fresh_tokens,
                    "prompt_seed": item.prompt_seed,
                } for item in capture.declarations if item.mix_class == cls), None)
                for cls in ("base", "mixed_tail")
            },
            "request_id_status": capture.request_id_status,
            "strict_boundary": "per_request_client_ttft",
        }


def p6_interface(capture: ClientCapture) -> dict[str, Any]:
    """Normal caller interface: one stable shape, conditions not forked states."""
    return {
            "schema": P6_SCHEMA,
            "cell": {
                "cell_id": capture.cell_id, "phase": capture.phase,
                "cohort": ("singleton94" if "subset:singleton_94" in capture.out_of_domain
                           else "other637"),
                "rack": capture.producer.get("rack"),
                "producer_sha256": capture.producer.get("producer_sha256"),
                "producer_variant": capture.producer.get("producer_variant"),
                "mode": capture.mode, "mode_boundary": capture.mode_boundary,
                "started": capture.started, "started_scope": "cell_utc",
                "concurrency": capture.concurrency, "prompt_tokens": capture.prompt_tokens,
                "shared_tokens": capture.shared_tokens, "fresh_tokens": capture.fresh_tokens,
                "max_tokens": capture.max_tokens, "mixed_prompt": capture.mixed_prompt,
                "mix_count": capture.mix_count,
                "mix_prompt_tokens": capture.mix_prompt_tokens,
                "base_requests": max(0, (capture.concurrency or 0) - (capture.mix_count or 0)),
                "graph_mode": capture.launch_declaration.get("graph_mode"),
                "graph_capture_sizes": capture.launch_declaration.get("graph_capture_sizes"),
                "source_token_geometry": capture.launch_declaration.get(
                    "source_token_geometry"),
                "seed_effective": capture.launch_declaration.get("seed_effective"),
                "seed_basis": capture.launch_declaration.get("seed_basis"),
                "server_chunk_budget": capture.launch_declaration.get("server_chunk_budget"),
                "server_max_num_seqs": capture.launch_declaration.get("server_max_num_seqs"),
                "status": capture.status,
                "source_conflicts": [dict(item) for item in capture.source_conflicts],
                "declared_count": capture.declared_count,
                "observed_count": len(capture.requests),
                "missing_ordinals": list(capture.missing_ordinals),
                "orphan_ttfts": list(capture.orphan_ttfts),
                "orphan_stream_ranks": list(capture.orphan_stream_ranks),
                "outcome_status": capture.outcome_status,
                "declaration_status": capture.declaration_status,
                "declaration_source": capture.declaration_source,
                "declared_ordinals": [item.ordinal for item in capture.declarations],
            },
            "requests": [{
                "key": item.key, "launch_ordinal": item.launch_ordinal,
                "ttft_s": item.ttft_s, "ttft_boundary": item.ttft_boundary,
                "stream_join_status": item.stream_join_status,
                "stream_rank": item.stream_rank,
                "candidate_stream_ranks": list(item.candidate_stream_ranks),
                "observed_stream": None if item.stream_rank is None else {
                    "e2e_s": item.e2e_s,
                    "e2e_boundary": capture.producer.get("e2e_boundary"),
                    "e2e_truncation_possible": item.e2e_truncation_possible,
                    "completion_tokens": item.completion_tokens,
                    "chunks": item.chunks, "itl_mean_s": item.itl_mean_s,
                    "itl_valid": item.itl_valid,
                    "token_chunk_aligned": item.token_chunk_aligned,
                },
                "request_seed": item.request_seed, "prompt_seed": item.prompt_seed,
                "token_geometry": {
                    "prompt_tokens": item.prompt_tokens,
                    "shared_tokens": item.shared_tokens,
                    "fresh_tokens": item.fresh_tokens,
                    "prompt_seed": item.prompt_seed,
                    "mix_class": item.mix_class,
                    "mix_index": item.mix_index,
                    "mix_count": item.mix_count,
                },
            } for item in capture.requests],
            "invariants": {
                "ordinal_uniqueness": "declared ordinal from producer cmd/cell; observed "
                                      "TTFT keys when first_token_latencies_s exists",
                "ttft_rounding": "producer round(raw,6)",
                "stream_join": "exact rounded equality; ambiguous leaves observed_stream null",
                "e2e_boundary": capture.producer.get("e2e_boundary"),
                "itl_boundary": "chunk arrival; token_chunk_aligned required for token ITL",
                "finish_token_boundary": "not_exported; rack06 empty-choice sentinel is not a "
                                        "finish-token timestamp and is not comparable to a "
                                        "predictor time-to-finish-token",
            },
        }


def iter_p6_requests(rows: Iterable[Mapping[str, Any]], *,
                     roots: Sequence[Path | str] | None = None
                     ) -> Iterator[dict[str, Any]]:
    """Normal caller P6 interface, one row per launch-ordinal TTFT key."""
    for capture in iter_client_captures(rows, roots=roots):
        interface = p6_interface(capture)
        for request in interface["requests"]:
            yield {"schema": P6_SCHEMA, "cell": interface["cell"],
                   **request, "invariants": interface["invariants"]}


def iter_prediction_declarations(rows: Iterable[Mapping[str, Any]], *,
                                 roots: Sequence[Path | str] | None = None
                                 ) -> Iterator[dict[str, Any]]:
    """Producer-declared ordinal only; independent of measured TTFT/streams."""
    for capture in iter_client_captures(rows, roots=roots):
        for declaration in capture.declarations:
            yield declaration.as_dict()


def summarize_client_requests(rows: Iterable[Mapping[str, Any]], *,
                              roots: Sequence[Path | str] | None = None) -> dict[str, Any]:
    cells: Counter[str] = Counter()
    phases: Counter[str] = Counter()
    conc: Counter[int] = Counter()
    request_id_status: Counter[str] = Counter()
    join_status: Counter[str] = Counter()
    itl_reason: Counter[str] = Counter()
    out_of_domain: Counter[str] = Counter()
    conflicts: Counter[str] = Counter()
    hardware: Counter[str] = Counter()
    racks: Counter[str] = Counter()
    producer_shas: Counter[str] = Counter()
    chunk_budgets: Counter[str] = Counter()
    seed_bases: Counter[str] = Counter()
    launch_sha: Counter[str] = Counter()
    graph_source: Counter[str] = Counter()
    graph_modes: Counter[str] = Counter()
    graph_sizes: Counter[str] = Counter()
    ttft_boundaries: Counter[str] = Counter()
    producer_variants: Counter[str] = Counter()
    total_requests = 0
    total_streams = 0
    cohort_cells: Counter[str] = Counter()
    cohort_requests: Counter[str] = Counter()
    cohort_full: Counter[str] = Counter()
    cohort_amb: Counter[str] = Counter()
    observed_ok = observed_failed = observed_unknown = 0
    c1 = c_gt1 = singleton94 = mixed = 0
    completion_ne_chunks = completion_lt_max = no_itl_completion_gt1 = 0
    explicit_request_ids = 0
    source_conflict_fields: Counter[str] = Counter()
    declaration_status: Counter[str] = Counter()
    outcome_status: Counter[str] = Counter()
    mix_classes: Counter[str] = Counter()
    prompt_geometry: Counter[str] = Counter()
    for capture in iter_client_captures(rows, roots=roots):
        cells[capture.status] += 1
        phases[f"{capture.phase}:{capture.status}"] += 1
        if capture.concurrency is not None:
            conc[capture.concurrency] += 1
        if capture.concurrency == 1:
            c1 += 1
        elif capture.concurrency and capture.concurrency > 1:
            c_gt1 += 1
        cohort = ("singleton94" if "subset:singleton_94" in capture.out_of_domain
                  else "other637")
        cohort_cells[cohort] += 1
        cohort_requests[cohort] += len(capture.requests)
        cohort_full[cohort] += sum(
            1 for item in capture.requests
            if item.stream_join_status == "exact_unique_rounded_ttft")
        cohort_amb[cohort] += sum(
            1 for item in capture.requests
            if item.stream_join_status == "ambiguous_duplicate_rounded_ttft")
        if cohort == "singleton94":
            singleton94 += 1
        if capture.mixed_prompt or capture.mode == "profile_pd":
            mixed += 1
        if capture.hardware_families:
            hardware.update(capture.hardware_families)
        racks[str(capture.producer.get("rack"))] += 1
        producer_shas[str(capture.producer.get("producer_sha256"))] += 1
        request_id_status[capture.request_id_status] += 1
        launch = capture.launch_declaration or {}
        for key in ("cmd_sha256", "case_sha256", "status_sha256"):
            if launch.get(key):
                launch_sha[key] += 1
        if launch.get("server_chunk_budget") is not None:
            chunk_budgets[str(launch.get("server_chunk_budget"))] += 1
        seed_bases[str(launch.get("seed_basis"))] += 1
        graph_source[str(launch.get("graph_source"))] += 1
        graph_modes[str(launch.get("graph_mode"))] += 1
        sizes = launch.get("graph_capture_sizes")
        graph_sizes[str(sizes) if sizes else "absent"] += 1
        ttft_boundaries[str(capture.producer.get("ttft_boundary"))] += 1
        producer_variants[str(capture.producer.get("producer_variant"))] += 1
        conflicts.update(capture.conflicts)
        declaration_status[capture.declaration_status] += 1
        outcome_status[capture.outcome_status] += 1
        for item in capture.source_conflicts:
            source_conflict_fields[str(item.get("field"))] += 1
        out_of_domain.update(item for item in capture.out_of_domain
                             if not item.startswith("subset:"))
        total_requests += len(capture.requests)
        total_streams += len(capture.streams)
        for request in capture.requests:
            mix_classes[request.mix_class] += 1
            prompt_geometry[f"{request.mix_class}:Q{request.prompt_tokens}:"
                            f"S{request.shared_tokens}"] += 1
            join_status[request.stream_join_status] += 1
            if request.ok is True:
                observed_ok += 1
            elif request.ok is False:
                observed_failed += 1
            else:
                observed_unknown += 1
            explicit_request_ids += 0
        for stream in capture.streams:
            if stream.completion_tokens is not None and stream.chunks is not None:
                completion_ne_chunks += stream.completion_tokens != stream.chunks
            if (stream.completion_tokens is not None and capture.max_tokens is not None
                    and stream.completion_tokens < capture.max_tokens):
                completion_lt_max += 1
            if stream.itl_mean_s is None:
                itl_reason["itl_absent"] += 1
                if stream.completion_tokens is not None and stream.completion_tokens > 1:
                    no_itl_completion_gt1 += 1
                    itl_reason["itl_absent_completion_gt1_chunks_lt_2"] += 1
            if stream.itl_valid is False:
                itl_reason["itl_invalid_chunk_boundary"] += 1
            if stream.token_chunk_aligned is False:
                itl_reason["token_chunk_mismatch"] += 1
    return {
        "schema_version": SCHEMA_VERSION,
        "cells": sum(cells.values()),
        "cell_status": {key: cells.get(key, 0) for key in (
            "acquired", "source_conflict", "outcome_missing", "outcome_ttft_missing",
            "outcome_stream_missing", "declaration_unknown", "partial", "empty",
            "missing", "conflict")},
        "cell_phase_status": dict(sorted(phases.items())),
        "concurrency_cells": {str(key): value for key, value in sorted(conc.items())},
        "c1_cells": c1,
        "c_gt1_cells": c_gt1,
        "singleton_94_cells": singleton94,
        "other_637_cells": sum(cells.values()) - singleton94,
        "cohorts": {
            "singleton94": {"cells": cohort_cells.get("singleton94", 0),
                            "requests": cohort_requests.get("singleton94", 0),
                            "full_joins": cohort_full.get("singleton94", 0),
                            "ambiguous_joins": cohort_amb.get("singleton94", 0)},
            "other637": {"cells": cohort_cells.get("other637", 0),
                         "requests": cohort_requests.get("other637", 0),
                         "full_joins": cohort_full.get("other637", 0),
                         "ambiguous_joins": cohort_amb.get("other637", 0)},
        },
        "mixed_prompt_cells": mixed,
        "mixed_tail_requests": mix_classes.get("mixed_tail", 0),
        "base_requests": mix_classes.get("base", 0),
        "request_mix_classes": dict(sorted(mix_classes.items())),
        "prompt_geometry": dict(sorted(prompt_geometry.items())),
        "source_conflicts": dict(sorted(source_conflict_fields.items())),
        "requests": total_requests,
        "declarations": sum(len(capture.declarations) for capture in
                            iter_client_captures(rows, roots=roots)),
        "streams": total_streams,
        "declaration_status": dict(sorted(declaration_status.items())),
        "outcome_status": dict(sorted(outcome_status.items())),
        "missing_ordinals": sum(len(capture.missing_ordinals) for capture in
                                iter_client_captures(rows, roots=roots)),
        "orphan_ttfts": sum(len(capture.orphan_ttfts) for capture in
                            iter_client_captures(rows, roots=roots)),
        "orphan_stream_ranks": sum(len(capture.orphan_stream_ranks) for capture in
                                   iter_client_captures(rows, roots=roots)),
        "request_observed": {"ok": observed_ok, "failed": observed_failed,
                             "unknown": observed_unknown},
        "request_id_status": dict(sorted(request_id_status.items())),
        "stream_join_status": dict(sorted(join_status.items())),
        "full_stream_joins": join_status.get("exact_unique_rounded_ttft", 0),
        "ambiguous_stream_joins": join_status.get("ambiguous_duplicate_rounded_ttft", 0),
        "no_stream_match": join_status.get("no_rounded_stream_match", 0),
        "itl": dict(sorted(itl_reason.items())),
        "completion_ne_chunks": completion_ne_chunks,
        "completion_lt_configured_max": completion_lt_max,
        "no_itl_with_completion_gt1": no_itl_completion_gt1,
        "explicit_request_id_fields": explicit_request_ids,
        "conflicts": dict(sorted(conflicts.items())),
        "out_of_domain": dict(sorted(out_of_domain.items())),
        "hardware_families": dict(sorted(hardware.items())),
        "racks": dict(sorted(racks.items())),
        "producer_sha256": dict(sorted(producer_shas.items())),
        "launch": {
            "cmd_sha_present": launch_sha.get("cmd_sha256", 0),
            "case_sha_present": launch_sha.get("case_sha256", 0),
            "status_sha_present": launch_sha.get("status_sha256", 0),
            "server_chunk_budget_cells": dict(sorted(chunk_budgets.items())),
            "seed_basis_cells": dict(sorted(seed_bases.items())),
            "declared_num_requests": total_requests,
            "graph_source_cells": dict(sorted(graph_source.items())),
            "graph_modes": dict(sorted(graph_modes.items())),
            "graph_capture_sizes_cells": dict(sorted(graph_sizes.items())),
            "ttft_boundary_cells": dict(sorted(ttft_boundaries.items())),
            "producer_variants": dict(sorted(producer_variants.items())),
        },
        "recommended_integration": {
            "p6_schema": P6_SCHEMA,
            "smallest_coherent_cohort": "C1 requests: 168 cells/168 ordinal TTFT keys "
                                        "(94 prefill singleton separate + 74 decode C1)",
            "request_key": "cell_id + launch_ordinal + capture context (rack included)",
            "target_boundary": "per-ordinal client TTFT; e2e only when observed_stream "
                               "exactly joins; ITL only when chunks>=2",
            "c_gt1": "6,652 ordinal TTFT keys remain fully usable; only 2 observed-stream "
                     "metadata joins are ambiguous in one cell. No scheduler/queue inference.",
            "forbidden": "cell ttft_mean_s/tpot_mean_s/window_s/measure_window_s are aggregates; "
                         "no inferred active membership, token/chunk conflation, or synthetic fallback",
        },
        "units": dict(_UNITS),
        "boundaries": dict(_BOUNDARIES),
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", required=True)
    parser.add_argument("--roots", nargs="*", default=None)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--example", default=None)
    parser.add_argument("--hash-ranks", action="store_true")
    args = parser.parse_args()
    rows = list(iter_original_rows(args.rows))
    if args.summary:
        print(json.dumps(summarize_client_requests(rows, roots=args.roots), indent=1))
    if args.example:
        capture = next(item for item in iter_client_captures_from_jsonl(
            args.rows, roots=args.roots,
            include_rank_hashes=args.hash_ranks) if item.cell_id == args.example)
        print(json.dumps(capture.as_dict(), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
