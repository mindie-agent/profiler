"""Capture read/join for original zero-shot client sources.

[Role] Build producer-declared ordinals independent of measured outcomes, then
  join optional observed TTFT/streams into evaluation rows.  Source parsing and
  model types stay in zero_shot_client_source; projection stays separate.

[Invariants] Declarations depend only on producer cmd/measured declaration
  geometry.  Missing outcomes leave declared_count visible and are not
  conflicts.  Orphan measured values stay in the evaluation capture.

[Side-Effect Policy] Read-only source reads.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from zero_shot_client_source import (
    DEFAULT_PRODUCER_SEED,
    DEFAULT_SOURCE_ROOTS,
    SCHEMA_VERSION,
    ClientCapture,
    ClientDeclaration,
    ClientRequest,
    ClientStream,
    _BOUNDARIES,
    _UNITS,
    _float,
    _int,
    _join_streams,
    _measured_index,
    _producer_info,
    _rank_sources,
    _secondary_declaration,
    iter_original_rows_with_sha,
)


def _build_declarations(*, cell_id: str, phase: str, producer: Mapping[str, Any],
                        mode_boundary: str | None, context: Mapping[str, Any],
                        launch: Mapping[str, Any], document: Mapping[str, Any],
                        mix_count: int | None) -> tuple[tuple[ClientDeclaration, ...],
                                                       int | None, str, str]:
    """Enumerate producer-declared ordinals from cmd/measured declaration geometry only."""
    cmd = launch.get("cmd_args") or {}
    measured_count = _int(document.get("concurrency"))
    cmd_count = _int(cmd.get("concurrency"))
    if cmd_count is not None and cmd_count > 0:
        concurrency, count_source = cmd_count, "producer_cmd_concurrency"
    elif measured_count is not None and measured_count > 0:
        concurrency, count_source = measured_count, "measured_record_concurrency"
    else:
        return (), None, "declaration_unknown_missing_concurrency", "none"
    prompt = _int(cmd.get("prompt-tokens"))
    if prompt is None:
        prompt = _int(document.get("prompt_tokens"))
    shared = _int(cmd.get("shared-tokens"))
    if shared is None:
        shared = _int(document.get("shared_tokens"))
    max_tokens = _int(cmd.get("max-tokens"))
    if max_tokens is None:
        max_tokens = _int(document.get("max_tokens"))
    mix = _int(cmd.get("mix-count"))
    if mix is None:
        mix = _int(document.get("mix_count")) or 0
    mix_prompt = _int(cmd.get("mix-prompt-tokens"))
    if mix_prompt is None:
        mix_prompt = _int(document.get("mix_prompt_tokens"))
    if prompt is None:
        return (), concurrency, "declaration_unknown_missing_prompt", count_source
    if shared is None:
        shared = max(0, prompt - 128)
    if max_tokens is None:
        max_tokens = 128
    mix = max(0, min(mix, concurrency))
    base_count = concurrency - mix
    if mix and mix_prompt is None:
        mix_prompt = prompt
    mshared = max(0, (mix_prompt or 0) - 128)
    mfresh = max(0, (mix_prompt or 0) - mshared)
    seed = _int(launch.get("seed_effective"))
    if seed is None:
        seed = DEFAULT_PRODUCER_SEED
    cohort = ("singleton94" if phase == "prefill" and concurrency == 1
              else "other637")
    declarations: list[ClientDeclaration] = []
    for ordinal in range(concurrency):
        if ordinal < base_count:
            q, s, f = prompt, shared, max(0, prompt - shared)
            cls, mix_index = "base", None
            prompt_seed = seed + ordinal + 1
            seed_basis = f"base_prompt_seed=seed+{ordinal}+1;request_body_seed=1234+ordinal"
        else:
            mix_index = ordinal - base_count
            q, s, f = mix_prompt or prompt, mshared, mfresh
            cls = "mixed_tail"
            prompt_seed = seed + 7001 + mix_index
            seed_basis = (f"mixed_prompt_seed=seed+7001+{mix_index};"
                          "request_body_seed=1234+ordinal")
        declarations.append(ClientDeclaration(
            key=(f"{cell_id}|ordinal={ordinal}|ctx={context.get('started')}"
                 f"|C={concurrency}|p={q}|o={max_tokens}|mix={cls}"
                 f"|rack={producer.get('rack')}"),
            cell_id=cell_id, phase=phase, cohort=cohort,
            producer=str(producer.get("producer_variant")),
            rack=str(producer.get("rack")), ordinal=ordinal,
            concurrency=concurrency, prompt_tokens=q, shared_tokens=s,
            fresh_tokens=f, mix_class=cls, mix_index=mix_index, mix_count=mix,
            prompt_seed=prompt_seed, request_seed=1234 + ordinal,
            seed_basis=seed_basis, max_tokens=max_tokens,
            chunk_budget=launch.get("server_chunk_budget"),
            graph_mode=launch.get("graph_mode"),
            graph_capture_sizes=launch.get("graph_capture_sizes"),
            mixed_prompt=bool(mix), mode_boundary=mode_boundary,
            declaration_source=count_source, declaration_status="declared",
            conditions={
                "started": context.get("started"),
                "started_scope": "cell_utc",
                "per_request_start": "not_exported",
                "ttft_boundary": producer.get("ttft_boundary"),
                "e2e_boundary": producer.get("e2e_boundary"),
            }))
    return tuple(declarations), concurrency, "declared", count_source


def client_capture(row: Mapping[str, Any], *,
                   roots: Sequence[Path | str] | None = None,
                   index: Mapping[str, tuple[Path, ...]] | None = None,
                   include_rank_hashes: bool = False,
                   row_sha256: str | None = None) -> ClientCapture:
    """Read one original cell's retained client record and classify it."""
    cell_id = str(row.get("cell_id") or "")
    row_phase = str(row.get("phase") or "")
    phase = row_phase
    original_row_sha = row_sha256 or hashlib.sha256(
        json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    original_row_basis = "exact_line_with_newline" if row_sha256 else "canonical_json"
    root_names = tuple(str(Path(item).resolve())
                       for item in (roots or DEFAULT_SOURCE_ROOTS))
    measured_index = index or _measured_index(root_names)
    paths = measured_index.get(cell_id, ())
    limits = (
        "streams are producer-sorted by ttft_s, not launch order",
        "no client request id is exported; launch ordinal only by exact TTFT value match",
        "TTFT/e2e/ITL are client SSE boundaries, not device-forward spans",
        "cell aggregates and measure_window_s are not request L4 values",
    )
    if not paths:
        return ClientCapture(
            cell_id=cell_id, phase=phase, status="missing",
            reason="measured_client_json_absent", measured_path="",
            measured_sha256=None, size_bytes=0, tag=None, mode=None,
            started=None, bases=(), concurrency=None, prompt_tokens=None,
            shared_tokens=None, fresh_tokens=None, max_tokens=None,
            success=None, failed=None, warmup_requests=None, warmup_ok=None,
            warmup=(), start_profile=(), stop_profile=(),
            start_profile_s=None, measure_window_s=None,
            first_token_latencies_s=(), requests=(), cell_aggregate={},
            conflicts=(), out_of_domain=("missing_source",),
            request_id_status="not_exported", rank_sources=(),
            hardware_families=(), service_association="unresolved",
            units=dict(_UNITS), boundaries=dict(_BOUNDARIES),
            limitations=limits + ("cell retained in denominator",))
    if len(paths) > 1:
        return ClientCapture(
            cell_id=cell_id, phase=phase, status="conflict",
            reason="duplicate_measured_tag", measured_path=";".join(map(str, paths)),
            measured_sha256=None, size_bytes=0, tag=None, mode=None,
            started=None, bases=(), concurrency=None, prompt_tokens=None,
            shared_tokens=None, fresh_tokens=None, max_tokens=None,
            success=None, failed=None, warmup_requests=None, warmup_ok=None,
            warmup=(), start_profile=(), stop_profile=(),
            start_profile_s=None, measure_window_s=None,
            first_token_latencies_s=(), requests=(), cell_aggregate={},
            conflicts=("duplicate_measured_tag",),
            out_of_domain=("source_identity_conflict",),
            request_id_status="not_exported", rank_sources=(),
            hardware_families=(), service_association="unresolved",
            units=dict(_UNITS), boundaries=dict(_BOUNDARIES),
            limitations=limits)
    path = paths[0]
    try:
        raw_bytes = path.read_bytes()
        document = json.loads(raw_bytes)
    except (OSError, ValueError) as exc:
        return ClientCapture(
            cell_id=cell_id, phase=phase, status="conflict",
            reason=f"measured_client_json_unreadable:{type(exc).__name__}",
            measured_path=str(path), measured_sha256=None,
            size_bytes=path.stat().st_size if path.exists() else 0,
            tag=None, mode=None, started=None, bases=(), concurrency=None,
            prompt_tokens=None, shared_tokens=None, fresh_tokens=None,
            max_tokens=None, success=None, failed=None, warmup_requests=None,
            warmup_ok=None, warmup=(), start_profile=(), stop_profile=(),
            start_profile_s=None, measure_window_s=None,
            first_token_latencies_s=(), requests=(), cell_aggregate={},
            conflicts=("measured_client_json_unreadable",),
            out_of_domain=("source_identity_conflict",),
            request_id_status="not_exported", rank_sources=(),
            hardware_families=(), service_association="unresolved",
            units=dict(_UNITS), boundaries=dict(_BOUNDARIES),
            limitations=limits)
    measured_sha = hashlib.sha256(raw_bytes).hexdigest()
    launch = _secondary_declaration(cell_id, phase, path, document, root_names)
    streams = [item for item in (document.get("streams") or ())
               if isinstance(item, Mapping)]
    first = tuple(document.get("first_token_latencies_s") or ())
    concurrency = _int(document.get("concurrency"))
    success = _int(document.get("success"))
    failed = _int(document.get("failed"))
    mode = str(document.get("mode") or "")
    conflicts: list[str] = []
    out_of_domain: list[str] = []
    source_conflicts: list[dict[str, Any]] = []
    if str(document.get("tag") or "") != cell_id:
        conflicts.append("measured_tag_mismatch")
    cmd = launch.get("cmd_args") or {}
    launch_pairs = (("mode", mode), ("concurrency", concurrency),
                    ("prompt-tokens", _int(document.get("prompt_tokens"))),
                    ("max-tokens", _int(document.get("max_tokens"))),
                    ("shared-tokens", _int(document.get("shared_tokens"))),
                    ("warmup", _int(document.get("warmup_requests"))))
    for names, actual in [((key,), actual) for key, actual in launch_pairs]:
        key = names[0]
        declared_value = cmd.get(key)
        if declared_value is None or actual is None:
            continue
        if str(declared_value) != str(actual):
            conflicts.append(f"launch_{key.replace('-', '_')}_mismatch")
    if streams and concurrency != len(streams):
        conflicts.append("concurrency_stream_count_mismatch")
    if streams and (success != len(streams) or failed != 0):
        conflicts.append("success_failed_stream_mismatch")
    ok_count = sum(1 for item in streams if item.get("ok") is True)
    if streams and ok_count != len(streams):
        conflicts.append("failed_stream_present")
    for stream in streams:
        ttft = _float(stream.get("ttft_s"))
        e2e = _float(stream.get("e2e_s"))
        completion = _int(stream.get("completion_tokens"))
        chunks = _int(stream.get("chunks"))
        if ttft is None or e2e is None:
            conflicts.append("request_boundary_absent")
        elif e2e + 1e-9 < ttft:
            conflicts.append("e2e_before_ttft")
        if completion is None or chunks is None:
            conflicts.append("request_token_count_absent")
        if ttft is not None and completion is not None:
            tpot = (e2e - ttft) / max(1, completion - 1) if e2e is not None else None
        else:
            tpot = None
    producer = _producer_info(path)
    if mode == "profile_pd":
        declared_phase = "decode"
        mode_boundary = "profile_pd_mixed"
    elif mode in ("profile_decode", "profile_prefill"):
        declared_phase = "decode" if mode == "profile_decode" else "prefill"
        mode_boundary = "profile_single_phase"
    else:
        declared_phase = phase
        mode_boundary = "unknown_mode"
        conflicts.append("unknown_mode")
    if declared_phase not in ("prefill", "decode"):
        conflicts.append("unknown_measured_phase")
    if row_phase and row_phase != declared_phase:
        source_conflicts.append({"field": "phase", "supplied": row_phase,
                                 "measured": declared_phase,
                                 "source": "row_phase_override"})
    phase = declared_phase if declared_phase in ("prefill", "decode") else row_phase
    for field, supplied, actual in (
            ("concurrency", row.get("concurrency"), concurrency),
            ("prompt_tokens", row.get("prompt_tokens"),
             _int(document.get("prompt_tokens"))),
            ("max_tokens", row.get("max_tokens"), _int(document.get("max_tokens")))):
        if supplied is None or actual is None:
            continue
        if str(supplied) != str(actual):
            source_conflicts.append({"field": field, "supplied": supplied,
                                     "measured": actual,
                                     "source": "row_override"})
    if concurrency is not None and len(first) != concurrency:
        conflicts.append("first_token_latencies_length_mismatch")
    launch_positive = [float(item) for item in first
                       if isinstance(item, (int, float)) and item > 0]
    stream_ttfts = [item.get("ttft_s") for item in streams
                    if isinstance(item.get("ttft_s"), (int, float))]
    if len(launch_positive) == len(first) == len(stream_ttfts):
        if sorted(round(item, 6) for item in launch_positive) != sorted(
                round(float(item), 6) for item in stream_ttfts):
            conflicts.append("launch_stream_ttft_multiset_mismatch")
    ordinals, stream_rows, join_conflicts = _join_streams(first, streams)
    conflicts.extend(join_conflicts)
    for stream in streams:
        itl = stream.get("itl_mean_s")
        chunks = _int(stream.get("chunks"))
        if chunks is not None and ((itl is None) != (chunks < 2)):
            conflicts.append("itl_presence_chunk_boundary_conflict")
    mix_count = _int(document.get("mix_count"))
    mix_prompt_tokens = document.get("mix_prompt_tokens")
    context = {
        "started": document.get("started"), "mode": mode,
        "concurrency": concurrency, "prompt_tokens": _int(document.get("prompt_tokens")),
        "shared_tokens": _int(document.get("shared_tokens")),
        "fresh_tokens": _int(document.get("fresh_tokens")),
        "max_tokens": _int(document.get("max_tokens")),
        "bases": tuple(str(item) for item in document.get("bases") or ()),
        "seed_effective": launch.get("seed_effective"),
        "seed_basis": launch.get("seed_basis"),
        "mix_count": mix_count,
        "mix_prompt_tokens": mix_prompt_tokens,
        "rack": producer.get("rack"),
    }
    declarations, declared_count, declaration_status, declaration_source = _build_declarations(
        cell_id=cell_id, phase=phase, producer=producer,
        mode_boundary=mode_boundary, context=context, launch=launch,
        document=document, mix_count=mix_count)
    mix = max(0, min(mix_count or 0, concurrency or 0))
    base_count = max(0, (concurrency or 0) - mix)
    base_prompt = _int(document.get("prompt_tokens"))
    base_shared = (_int(document.get("shared_tokens"))
                   if _int(document.get("shared_tokens")) is not None
                   else max(0, (base_prompt or 0) - 128))
    if not base_shared:
        base_shared = max(0, (base_prompt or 0) - 128)
    base_fresh = max(0, (base_prompt or 0) - base_shared)
    mix_prompt = (_int(mix_prompt_tokens) if mix_prompt_tokens is not None
                  else base_prompt)
    mix_shared = max(0, (mix_prompt or 0) - 128)
    mix_fresh = max(0, (mix_prompt or 0) - mix_shared)
    context["base_count"] = base_count
    context["mix_prompt_tokens_effective"] = mix_prompt
    seed_effective = launch.get("seed_effective", DEFAULT_PRODUCER_SEED)
    requests = []
    for row in ordinals:
        ordinal = int(row["launch_ordinal"])
        stream = (streams[row["stream_rank"]]
                  if row["stream_rank"] is not None else None)
        ttft = row["ttft_s"]
        if stream is not None:
            e2e = _float(stream.get("e2e_s"))
            completion = _int(stream.get("completion_tokens"))
            chunks = _int(stream.get("chunks"))
            tpot = ((e2e - ttft) / max(1, completion - 1)
                    if e2e is not None and ttft is not None and completion is not None
                    else None)
            itl_valid = chunks is not None and chunks >= 2
            token_chunk_aligned = (completion is not None and chunks is not None
                                   and completion == chunks)
            ok = stream.get("ok") is True
            itl_mean = _float(stream.get("itl_mean_s"))
            itl_p50 = _float(stream.get("itl_p50_s"))
        else:
            e2e = completion = chunks = tpot = None
            itl_mean = itl_p50 = None
            itl_valid = token_chunk_aligned = None
            ok = None
        request_seed = 1234 + ordinal
        if ordinal < base_count:
            mix_class = "base"
            mix_index = None
            request_prompt = base_prompt
            request_shared = base_shared
            request_fresh = base_fresh
            prompt_seed = seed_effective + ordinal + 1
            seed_basis = (f"base_prompt_seed=seed+{ordinal}+1;"
                          "request_body_seed=1234+ordinal")
        else:
            mix_class = "mixed_tail"
            mix_index = ordinal - base_count
            request_prompt = mix_prompt
            request_shared = mix_shared
            request_fresh = mix_fresh
            prompt_seed = seed_effective + 7001 + mix_index
            seed_basis = (f"mixed_prompt_seed=seed+7001+{mix_index};"
                          "request_body_seed=1234+ordinal")
        key = (f"{cell_id}|ordinal={ordinal}"
               f"|ctx={context['started']}|C={concurrency}|p={request_prompt}"
               f"|o={context['max_tokens']}|mix={mix_class}|rack={producer.get('rack')}")
        requests.append(ClientRequest(
            key=key, client_id=str(document.get("tag") or cell_id),
            cell_id=cell_id, phase=phase,
            producer=str(producer.get("producer_variant")),
            rack=str(producer.get("rack")), launch_ordinal=ordinal,
            raw_ttft_s=row["raw_ttft_s"], ttft_s=ttft,
            ttft_boundary=str(producer.get("ttft_boundary")),
            stream_join_status=row["join_status"],
            stream_rank=row["stream_rank"],
            candidate_stream_ranks=tuple(row["candidate_stream_ranks"]),
            ok=ok, e2e_s=e2e,
            e2e_truncation_possible=(completion is not None
                                     and context["max_tokens"] is not None
                                     and completion < context["max_tokens"]),
            itl_mean_s=itl_mean, itl_p50_s=itl_p50,
            tpot_derived_s=tpot, completion_tokens=completion, chunks=chunks,
            itl_valid=itl_valid, token_chunk_aligned=token_chunk_aligned,
            request_seed=request_seed,
            prompt_seed=prompt_seed,
            prompt_tokens=request_prompt,
            shared_tokens=request_shared,
            fresh_tokens=request_fresh,
            mix_class=mix_class,
            mix_index=mix_index,
            mix_count=mix,
            seed_basis=seed_basis,
            capture_context=context, source_sha256=measured_sha,
            measured_path=str(path), original_row_sha256=original_row_sha,
            original_row_sha_basis=original_row_basis))
    streams_out = []
    for row in stream_rows:
        stream = streams[row["stream_rank"]]
        completion = _int(stream.get("completion_tokens"))
        chunks = _int(stream.get("chunks"))
        streams_out.append(ClientStream(
            cell_id=cell_id, stream_rank=row["stream_rank"],
            ttft_s=_float(stream.get("ttft_s")),
            e2e_s=_float(stream.get("e2e_s")),
            e2e_truncation_possible=(completion is not None
                                     and context["max_tokens"] is not None
                                     and completion < context["max_tokens"]),
            completion_tokens=completion, chunks=chunks,
            itl_mean_s=_float(stream.get("itl_mean_s")),
            itl_p50_s=_float(stream.get("itl_p50_s")),
            ok=stream.get("ok") is True,
            joined_ordinal=row["joined_ordinal"],
            join_status=row["join_status"],
            candidate_ordinals=tuple(row["candidate_ordinals"]),
            token_chunk_aligned=(completion is not None and chunks is not None
                                 and completion == chunks),
            itl_valid=chunks is not None and chunks >= 2,
            boundaries=dict(_BOUNDARIES)))
    if conflicts:
        status = "conflict"
    elif source_conflicts:
        status = "source_conflict"
    elif not streams and not first and declarations:
        status = "outcome_missing"
    elif not first and streams:
        status = "outcome_ttft_missing"
    elif not streams and first:
        status = "outcome_stream_missing"
    elif not declarations:
        status = "declaration_unknown"
    elif any(not item.ok for item in streams_out):
        status = "partial"
    else:
        status = "acquired"
    missing_ordinals = tuple(
        ordinal for ordinal in range(declared_count or 0)
        if ordinal not in {item.launch_ordinal for item in requests})
    orphan_ttfts = tuple(item.ttft_s for item in requests
                         if declared_count is not None
                         and item.launch_ordinal >= declared_count)
    orphan_stream_ranks = tuple(
        row["stream_rank"] for row in stream_rows
        if row["join_status"] == "no_launch_match")
    if not streams and not first:
        outcome_status = "missing"
    elif not first:
        outcome_status = "ttft_missing"
    elif not streams:
        outcome_status = "streams_missing"
    elif missing_ordinals or orphan_ttfts or orphan_stream_ranks:
        outcome_status = "partitioned"
    else:
        outcome_status = "complete"
    if any(item.stream_join_status == "ambiguous_duplicate_rounded_ttft"
           for item in requests):
        out_of_domain.append("observed_stream_metadata_ambiguous")
    if any(item.itl_mean_s is None and item.completion_tokens is not None
           and item.completion_tokens > 1 for item in requests):
        out_of_domain.append("itl_absent_with_completion_gt1")
    if any(item.token_chunk_aligned is False for item in requests):
        out_of_domain.append("itl_chunk_boundary_only")
    if phase == "decode" and any(
            item.completion_tokens is not None and context["max_tokens"] is not None
            and item.completion_tokens < context["max_tokens"] for item in requests):
        out_of_domain.append("decode_completion_truncated_by_profile_stop")
    if mode == "profile_pd" or mix_count:
        out_of_domain.append("profile_pd_mixed_prompt")
    if source_conflicts:
        out_of_domain.append("row_override_source_conflict")
    request_id_status = ("ordinal_ttft_keyed"
                         if len(requests) == concurrency and not join_conflicts
                         else "partial_ordinal_ttft")
    rank_sources, families = _rank_sources(cell_id, root_names,
                                           include_hashes=include_rank_hashes)
    aggregate = {name: document.get(name) for name in (
        "ttft_mean_s", "ttft_p50_s", "tpot_mean_s", "tpot_p50_s",
        "window_s", "out_tokens_total", "out_tokens_per_s")}
    association = ("service_cell_level" if rank_sources
                   else "rank_source_unresolved")
    if phase == "prefill" and concurrency == 1 and failed == 0 and success == 1:
        subset = "singleton_94"
    else:
        subset = "other_637"
    out_of_domain.append("subset:" + subset)
    return ClientCapture(
        cell_id=cell_id, phase=phase, status=status, reason=None,
        measured_path=str(path), measured_sha256=measured_sha,
        size_bytes=len(raw_bytes), tag=document.get("tag"), mode=mode,
        mode_boundary=mode_boundary, started=document.get("started"),
        bases=tuple(str(item) for item in document.get("bases") or ()),
        concurrency=concurrency, prompt_tokens=_int(document.get("prompt_tokens")),
        shared_tokens=_int(document.get("shared_tokens")),
        fresh_tokens=_int(document.get("fresh_tokens")),
        max_tokens=_int(document.get("max_tokens")), success=success,
        failed=failed, warmup_requests=_int(document.get("warmup_requests")),
        warmup_ok=_int(document.get("warmup_ok")),
        warmup=tuple(item for item in document.get("warmup") or ()
                     if isinstance(item, Mapping)),
        start_profile=tuple(document.get("start_profile") or ()),
        stop_profile=tuple(document.get("stop_profile") or ()),
        start_profile_s=_float(document.get("start_profile_s")),
        measure_window_s=_float(document.get("measure_window_s")),
        first_token_latencies_s=first, requests=tuple(requests),
        cell_aggregate=aggregate, conflicts=tuple(sorted(set(conflicts))),
        out_of_domain=tuple(sorted(set(out_of_domain))),
        request_id_status=request_id_status, rank_sources=rank_sources,
        hardware_families=families, service_association=association,
        units=dict(_UNITS), boundaries=dict(_BOUNDARIES), limitations=limits,
        original_row_sha256=original_row_sha,
        original_row_sha_basis=original_row_basis,
        launch_declaration=launch, producer=producer,
        streams=tuple(streams_out), mixed_prompt=bool(mix_count),
        mix_count=mix_count, mix_prompt_tokens=mix_prompt_tokens,
        full_join_count=sum(1 for item in requests
                            if item.stream_join_status == "exact_unique_rounded_ttft"),
        ambiguous_join_count=sum(1 for item in requests
                                 if item.stream_join_status == "ambiguous_duplicate_rounded_ttft"),
        status_cell={"started": launch.get("status_cell_started"),
                     "finished": launch.get("status_cell_finished"),
                     "captured": launch.get("status_cell_captured")},
        source_conflicts=tuple(source_conflicts),
        declarations=declarations, declared_count=declared_count,
        declaration_status=declaration_status,
        declaration_source=declaration_source,
        missing_ordinals=missing_ordinals, orphan_ttfts=orphan_ttfts,
        orphan_stream_ranks=orphan_stream_ranks,
        outcome_status=outcome_status)


def iter_client_captures(rows: Iterable[Mapping[str, Any]], *,
                         roots: Sequence[Path | str] | None = None,
                         include_rank_hashes: bool = False) -> Iterator[ClientCapture]:
    root_names = tuple(str(Path(item).resolve())
                       for item in (roots or DEFAULT_SOURCE_ROOTS))
    index = _measured_index(root_names)
    for row in rows:
        yield client_capture(row, roots=root_names, index=index,
                             include_rank_hashes=include_rank_hashes)


def iter_client_captures_from_jsonl(path: Path | str, *,
                                   roots: Sequence[Path | str] | None = None,
                                   include_rank_hashes: bool = False
                                   ) -> Iterator[ClientCapture]:
    root_names = tuple(str(Path(item).resolve())
                       for item in (roots or DEFAULT_SOURCE_ROOTS))
    index = _measured_index(root_names)
    for row, row_sha in iter_original_rows_with_sha(path):
        yield client_capture(row, roots=root_names, index=index,
                             include_rank_hashes=include_rank_hashes,
                             row_sha256=row_sha)


def iter_client_requests(rows: Iterable[Mapping[str, Any]], *,
                         roots: Sequence[Path | str] | None = None) -> Iterator[ClientRequest]:
    for capture in iter_client_captures(rows, roots=roots):
        for request in capture.requests:
            yield request
