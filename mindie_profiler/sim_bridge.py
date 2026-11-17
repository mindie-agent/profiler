"""Bridge measured MindIE profiler captures into schema-valid mindie-sim Cases.

[Role] Deterministically normalize a benchmark cell capture, a profiler capture,
  a C7 summary/attribution report, or an archived case record into the five-key
  ``mindie-sim`` Case contract with post-simulation observed metadata.  The same
  reader also exports complete native events and timing-free prediction requests.
[Invariants] Top-level keys are ``machine``, ``model``, ``workload``, ``runtime``
  and ``slo``; observed timings stay in ``runtime.metadata.observed_profile``;
  missing measurements stay ``None``; extraction is order-independent.
[Timeouts & Locks] Bounded metadata reads and streaming CSV scans; no locks/I/O side effects.
[Side-Effect Policy] Export helpers read only; callers write the requested JSON.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, os, re, sys
from fractions import Fraction
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from .events import PARSER_VERSION, ProfilerError, ProfilerUsageError, remote_guide_hint
from .profiler_configs import DEFAULT_SIM_BRIDGE_POLICY, SimBridgeBottleneckPolicy

from .sim_bridge_case import (
    _NATIVE_EXECUTION_CORES, _T12_CONDITION_KEYS, _native_api_mapping,
    _native_capture_selection, _native_conditions, _native_merge_explicit_invocation,
    _native_operator_identity, _native_request_condition_parts, _native_request_identity,
    _qbmm_t12_invocation, native_prediction_requests,
)
from .sim_bridge_catalog import (
    BRIDGE_SCHEMA, _A2, _A3, _A5, _CSV_NAMES, _GENERIC, _GEOMETRY, _HARDWARE,
    _JSON_NAMES, _MAX_POS, _MODEL_PATTERNS, _SKIP_DIRS, _SKUS, _attach_metadata,
    _candidate_strings, _case_request_gaps, _complete_model_config, _complete_sim_model,
    _config_identity, _detect_hardware, _detect_model, _diagnostic_filled_values,
    _empty_bundle, _empty_observed, _extract_facts, _first_float, _first_int,
    _first_string, _flatten_record, _graph_mode, _has_explicit_config, _hccl_mode,
    _mapping, _match_model, _merge_observed, _model_production_gap, _norm_aux_and_fp16,
    _normalize_quant, _parallel_overrides, _parse_case, _parse_env,
    _quant_from_operators, _quantization, _read_json, _read_text, _request_gaps,
    _request_records, _resolve_hw_token, _runtime_bool, _runtime_facts, _strip_spec_cmd,
    _strip_timings, _structural_overrides, _try_import, _validate_case, _walk_err,
    _workload,
)
from .sim_bridge_native_obs import (
    _DTYPE_STORAGE_ALIASES, _declared_slot_signature, _dtype_identity,
    _invocation_slots, _native_json_safe, _native_prediction_request_fields,
    _request_abi_lowered, _slot_shape_equivalent, _slots_equivalent, _t12_abi,
    _t12_duration_ms, _t12_invocation_from_request,
)
from .sim_bridge_observed import (
    NATIVE_OBSERVATION_SCHEMA, NATIVE_REQUEST_SCHEMA, _NATIVE_TIMING_KEYS,
    _RUNTIME_FACT_KEYS, _build_case, _bundle_from_mapping, _canonical_json,
    _compose_case, _csv_path, _extract_observed, _fallback_case, _fallback_model,
    _finalize_observed, _find_case_record, _find_kv_ratio, _full_explicit_case,
    _is_attention, _is_c7_report, _is_comm, _is_moe, _iter_csv, _looks_like_case_record,
    _native_timing_path, _normalize_operators, _observed_from_api,
    _observed_from_benchmark, _observed_from_op_csv, _observed_from_report,
    _observed_from_step_trace, _pct, _production_gaps, _quant_from_kernel_file, _ratio,
    _row_duration_us, _row_text, _share_from_names, _stat_median,
)
from .sim_bridge_predict import predict_native_requests

def _sha256_text(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()

def export_native_observations(
    input_path: str | Path,
    *,
    conditions: Mapping[str, Any] | None = None,
    hardware: str | None = None,
    phase: str | None = None,
    model: str | None = None,
    quant: str | None = None,
    deployment_image_id: str | None = None,
    execution: Mapping[str, Any] | None = None,
    rank: str | int | None = None,
    max_events: int = 100_000,
    timeout_s: float = 30.0,
    include_hash: bool = False,
    output: str | Path | None = None,
) -> dict[str, Any]:
    """Export complete native events from one real ``kernel_details.csv``.

    The event tensor ABI, raw task/stream locator, local duration and causal
    stream order are retained.  The API-call expansion, cross-domain clock
    mapping and fused semantic membership are *not* invented: each remains an
    explicit missing/undeclared field.  Conditions come only from the caller.

    A request identity excludes every timing field.  Repeated events with the
    same ABI/conditions share a ``request_id`` and can be priced once by an
    independent native entry; their individual durations remain observations.
    """
    if not isinstance(max_events, int) or isinstance(max_events, bool) or max_events < 1:
        raise ProfilerUsageError("native max_events must be a positive integer")
    from .normalized import kernel_rows
    from .sources_csv import probe_csv

    rank_value_arg = (None if rank is None or not str(rank).strip()
                      else str(rank).strip())
    path, source_discovery = _native_capture_selection(
        input_path, rank=rank_value_arg)
    schema = probe_csv(path)
    condition_values, condition_sources, condition_gaps, condition_conflicts = (
        _native_conditions(
            conditions, hardware=hardware, phase=phase, model=model, quant=quant,
            deployment_image_id=deployment_image_id, execution=execution))
    rank_value = (None if rank is None or not str(rank).strip()
                  else str(rank).strip())
    from .native_tensor_abi import (
        native_abi_from_slots, native_abi_record, native_tensor_contract,
    )
    source_identity = {
        "kind": "kernel_details_csv", "path": str(path), "basename": path.name,
        "schema_version": schema.schema_version,
        "size_bytes": path.stat().st_size,
        "mtime_ns": path.stat().st_mtime_ns,
        "sha256": _sha256_text(path) if include_hash else None,
        "sha256_scope": "raw_file_bytes" if include_hash else None,
        "source_discovery": source_discovery,
    }
    rows = []
    truncated = False
    for index, row in enumerate(kernel_rows(
        path, rank_id="" if rank_value is None else rank_value,
        max_rows=max_events + 2, timeout_s=timeout_s,
    )):
        if index >= max_events:
            truncated = True
            break
        event = row.event
        locator = dict(event.locator or {})
        operator, type_issue = _native_operator_identity(row, event)
        contract = native_tensor_contract(row)
        if operator is not None:
            abi = native_abi_record(row, kind=operator)
        elif contract is not None:
            abi = native_abi_from_slots(
                None, contract[2], contract[3], strict_operator=False)
        else:
            abi = native_abi_record(row)
        if type_issue:
            abi = {
                **abi, "native_operator": None,
                "issues": [
                    *abi.get("issues", ()),
                    {"slot": "native_operator", "reason": type_issue},
                ],
            }
        device = str(event.device_id or "").strip()
        stream = str(event.stream_id or "").strip()
        stream_missing = not stream
        stream_key = stream or f"missing-stream@{locator.get('row_index')}"
        device_missing = not device
        device_key = device or f"missing-device@{locator.get('row_index')}"
        clock_domain = (
            f"rank:{rank_value}/" if rank_value is not None else ""
        ) + f"device:{device_key}:stream:{stream_key}"
        clock = {
            "domain": clock_domain, "unit": "ns", "source_unit": "us",
            "scale_ns": 1000, "reference_domain": None, "offset_ns": None,
            "comparable": False,
            "source": "kernel_details.csv start/duration converted to ns once; "
                      "no cross-domain synchronization anchor retained",
        }
        ambiguity = []
        if type_issue:
            ambiguity.append({"slot": "native_operator", "reason": type_issue})
        if device_missing:
            ambiguity.append({"slot": "occurrence.device_id",
                              "reason": "missing_device_id"})
        ambiguity.extend(abi.get("issues", ()))
        if operator is None:
            status = ("candidate" if abi.get("inputs") or abi.get("outputs")
                      else "unidentified")
            basis = ("native_type_unresolved_slots_preserved"
                     if abi.get("inputs") or abi.get("outputs")
                     else "no_native_tensor_abi")
        elif device_missing:
            status, basis = "candidate", "device_scope_not_declared"
        elif abi.get("status") == "complete" and abi.get("verified"):
            status, basis = "confirmed", "complete_ordered_tensor_slots_and_device"
        else:
            status, basis = "candidate", "partial_native_tensor_abi"
        boundary = {
            "kind": "kernel",
            "native_operator": operator,
            "raw_kind": str(row.kind or ""),
            "raw_core": str(row.core or event.core or ""),
            "scope": ("one_complete_kernel_event" if status == "confirmed"
                      else "local_kernel_event_scope_incomplete"),
            "expansion": "single_kernel_row",
            "expansion_status": "api_call_not_retained_in_kernel_details_csv",
            "raw_kernel_name": row.name,
            "raw_task_type": event.task_type,
            "occurrence_scope": {
                "rank_declared": rank_value is not None,
                "device_declared": not device_missing,
                "stream_declared": not stream_missing,
                "native_type_declared": operator is not None,
            },
            "fusion": {
                "status": "not_evidenced", "members": [], "member_count": 1,
                "allocation": "none",
                "basis": "kernel_details_csv_has_no_semantic_subgraph_membership",
            },
        }
        occurrence = {
            "event_id": event.event_id,
            "rank": rank_value,
            "device_id": device or None,
            "stream_id": stream or None,
            "task_id": str(event.task_id or ""),
            "start_ns": int(row.start_ns),
            "end_ns": int(row.end_ns),
            "locator": locator,
            "core": event.core,
            "task_type": event.task_type,
            "op_state": event.op_state,
        }
        duration_ns = int(row.duration_ns)
        counters = {
            str(key): float(value) for key, value in dict(row.counters_us).items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        rows.append({
            "row": row,
            "domain_key": (rank_value, device_key, stream_key, clock_domain),
            "stream_missing": stream_missing,
            "boundary": boundary, "abi": abi, "occurrence": occurrence,
            "clock": clock,
            "timing": {
                "duration_ns": duration_ns,
                "duration_ms": duration_ns / 1_000_000.0,
                "source_field": "Duration(us)", "source_unit": "us",
                "canonical_unit": "ns", "complete_in_window": True,
                "window_id": None,
            },
            "structure": {"status": status, "basis": basis,
                          "ambiguity": ambiguity},
            "evidence": {
                "pipe_times_us": counters,
                "block_num": row.blocks,
                "mix_block_num": event.mix_block_dim,
                "pmu_status": event.pmu_status,
                "wait_status": event.wait_status,
            },
            "source": {
                "path": str(path), "row_index": locator.get("row_index"),
                "source_discovery": source_discovery,
                "csv_line": locator.get("csv_line"),
                "schema_version": schema.schema_version,
            },
        })
    if not rows:
        return {
            "schema": NATIVE_OBSERVATION_SCHEMA, "source_identity": source_identity,
            "source_discovery": source_discovery,
            "conditions": {
                "declared": condition_values,
                "sources": condition_sources,
                "gaps": condition_gaps,
                "conflicts": condition_conflicts,
            },
            "window": {"kind": "per_domain", "count": 0,
                       "clock_comparable_across_domains": False},
            "windows": [], "observations": [], "truncated": truncated,
            "counts": {"events": 0, "confirmed": 0, "candidate": 0,
                       "unidentified": 0, "requests": 0, "windows": 0,
                       "devices": 0, "missing_device_id": 0,
                       "missing_native_type": 0, "missing_stream_id": 0},
            "limitations": ["no_complete_kernel_event_in_input"],
        }
    rows.sort(key=lambda item: (
        str(item["domain_key"][0]), str(item["domain_key"][1]),
        str(item["domain_key"][2]), item["occurrence"]["start_ns"],
        item["occurrence"]["end_ns"], item["occurrence"]["task_id"],
    ))
    domain_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for item in rows:
        domain_groups.setdefault(item["domain_key"], []).append(item)
    windows = []
    observations = []
    for domain_key, group in domain_groups.items():
        group.sort(key=lambda item: (
            item["occurrence"]["start_ns"], item["occurrence"]["end_ns"],
            item["occurrence"]["task_id"], item["occurrence"]["event_id"]))
        start_ns = min(item["occurrence"]["start_ns"] for item in group)
        end_ns = max(item["occurrence"]["end_ns"] for item in group)
        seed = {
            "source": source_identity["path"],
            "size_bytes": source_identity["size_bytes"],
            "mtime_ns": source_identity["mtime_ns"],
            "domain_key": [str(value) for value in domain_key],
            "start_ns": start_ns, "end_ns": end_ns, "count": len(group),
        }
        window_id = "window:" + _sha256_json(seed)[:24]
        window = {
            "id": window_id,
            "kind": ("truncated_local_domain_range" if truncated
                     else "local_domain_range"),
            "rank": domain_key[0], "device_id": (
                None if str(domain_key[1]).startswith("missing-device@")
                else domain_key[1]),
            "stream_id": (None if str(domain_key[2]).startswith("missing-stream@")
                          else domain_key[2]),
            "clock_domain": domain_key[3],
            "start_ns": start_ns, "end_ns": end_ns,
            "duration_ms": (end_ns - start_ns) / 1_000_000.0,
            "event_count": len(group),
            "clock_comparable_across_domains": False,
            "source": "kernel_details.csv local clock/device/stream range",
        }
        if str(domain_key[1]).startswith("missing-device@"):
            window["device_scope"] = "not_declared"
        if str(domain_key[2]).startswith("missing-stream@"):
            window["stream_scope"] = "not_declared"
            window["window_scope"] = "event_local_no_stream"
        windows.append(window)
        for ordinal, item in enumerate(group):
            occurrence = item["occurrence"]
            timing = item["timing"]
            timing["window_id"] = window_id
            timing["window"] = {
                "id": window_id, "clock_domain": domain_key[3],
                "start_ns": start_ns, "end_ns": end_ns,
                "duration_ms": window["duration_ms"],
                "local_event_start_ns": occurrence["start_ns"],
                "local_event_end_ns": occurrence["end_ns"],
            }
            if item["stream_missing"]:
                item["causality"] = {
                    "domain_key": [str(value) for value in domain_key],
                    "stream_ordinal": None,
                    "basis": "stream_identity_missing_no_causal_edge",
                    "dependencies_established": False,
                    "predecessor_event_id": None,
                    "successor_event_id": None,
                }
            else:
                item["causality"] = {
                    "domain_key": [str(value) for value in domain_key],
                    "stream_ordinal": ordinal,
                    "basis": "same_rank_device_stream_clock_start_end_order",
                    "dependencies_established": True,
                    "predecessor_event_id": (
                        group[ordinal - 1]["occurrence"]["event_id"]
                        if ordinal else None),
                    "successor_event_id": (
                        group[ordinal + 1]["occurrence"]["event_id"]
                        if ordinal + 1 < len(group) else None),
                }
        observations.extend(group)
    for item in observations:
        request_identity = _native_request_identity(
            item["boundary"], item["abi"], condition_values,
            item["occurrence"], item["clock"], item["timing"]["window_id"],
            condition_gaps=condition_gaps,
            condition_conflicts=condition_conflicts)
        request_id = "request:" + _sha256_json(request_identity)[:24]
        observation_id = "observation:" + _sha256_json({
            "request_id": request_id, "event_id": item["occurrence"]["event_id"],
            "start_ns": item["occurrence"]["start_ns"],
            "end_ns": item["occurrence"]["end_ns"],
            "locator": item["occurrence"]["locator"],
        })[:24]
        item.pop("row", None)
        item.update({
            "schema": "mindie-profiler-native-observation/1",
            "observation_id": observation_id, "request_id": request_id,
            "request_identity": request_identity,
            "conditions": condition_values,
            "condition_sources": condition_sources,
            "condition_gaps": condition_gaps,
            "condition_conflicts": condition_conflicts,
            "fusion": item["boundary"]["fusion"],
        })
    observations.sort(key=lambda item: (
        str(item["occurrence"].get("rank")), str(item["domain_key"][1]),
        str(item["occurrence"].get("stream_id")),
        item["occurrence"]["start_ns"], item["occurrence"]["end_ns"],
        item["occurrence"]["task_id"], item["observation_id"],
    ))
    id_by_event = {
        item["occurrence"]["event_id"]: item["observation_id"]
        for item in observations
    }
    for item in observations:
        causality = item["causality"]
        causality["stream_predecessor"] = id_by_event.get(
            causality.pop("predecessor_event_id", None))
        causality["stream_successor"] = id_by_event.get(
            causality.pop("successor_event_id", None))
    statuses = [item["structure"]["status"] for item in observations]
    missing_device_id = sum(
        1 for item in observations if item["occurrence"]["device_id"] is None)
    missing_native_type = sum(
        1 for item in observations if item["boundary"]["native_operator"] is None)
    missing_stream_id = sum(
        1 for item in observations if item["occurrence"]["stream_id"] is None)
    devices = sorted({
        item["occurrence"]["device_id"] for item in observations
        if item["occurrence"]["device_id"] is not None
    })
    report = {
        "schema": NATIVE_OBSERVATION_SCHEMA,
        "source_identity": source_identity,
        "source_discovery": source_discovery,
        "conditions": {
            "declared": condition_values,
            "sources": condition_sources,
            "gaps": condition_gaps,
            "conflicts": condition_conflicts,
        },
        "window": {
            "kind": "per_domain", "count": len(windows),
            "clock_comparable_across_domains": False,
            "windows": windows,
        },
        "windows": windows,
        "observations": observations,
        "truncated": truncated,
        "counts": {
            "events": len(observations),
            "confirmed": statuses.count("confirmed"),
            "candidate": statuses.count("candidate"),
            "unidentified": statuses.count("unidentified"),
            "requests": len({item["request_id"] for item in observations}),
            "windows": len(windows),
            "devices": len(devices),
            "missing_device_id": missing_device_id,
            "missing_native_type": missing_native_type,
            "missing_stream_id": missing_stream_id,
        },
        "limitations": [
            "api_call_expansion_not_retained_in_kernel_details_csv",
            "cross_domain_clock_not_mapped",
            "per_domain_local_windows_not_a_global_span",
            "causality_within_same_rank_device_stream_clock_only",
            "fusion_membership_not_declared_by_capture",
            *([] if not missing_device_id else [
                "missing_device_id_preserved_as_candidate_scope"]),
            *([] if not missing_native_type else [
                "native_type_missing_preserved_as_candidate"]),
            *([] if not missing_stream_id else [
                "missing_stream_id_no_causal_edges"]),
            *([] if not truncated else ["event_budget_truncated"]),
        ],
    }
    if output is not None:
        from .report import write_report
        write_report(report, output)
    return report

def _attach_rank_selection(case: dict[str, Any], bundle: Mapping[str, Any]) -> None:
    selection = bundle.get("rank_selection")
    if not isinstance(selection, Mapping):
        return
    runtime = case.get("runtime")
    if not isinstance(runtime, dict):
        return
    metadata = runtime.get("metadata")
    if not isinstance(metadata, dict):
        metadata = runtime["metadata"] = {}
    provenance = metadata.get("profiler_provenance")
    if not isinstance(provenance, dict):
        provenance = metadata["profiler_provenance"] = {}
    provenance["rank_selection"] = dict(selection)


def select_case_rank(root: str | Path, rank: str | int = "auto") -> tuple[Any, dict[str, Any]]:
    """Select one Case measurement rank without changing native-export strictness."""
    from .segment import discover_rank_sources, resolve_ranks

    sources = discover_rank_sources(root, source="auto")
    if not sources:
        raise ProfilerUsageError("export-sim-case: no profiling rank sources")
    ordered = sorted(
        sources,
        key=lambda item: (
            item.rank_index is None,
            item.rank_index if item.rank_index is not None else 0,
            item.rank_id,
        ),
    )
    selected = ordered[0] if str(rank) == "auto" else resolve_ranks(sources, [rank])[0]
    return selected, {
        "selected_rank": selected.rank_id,
        "available_ranks": [item.rank_id for item in ordered],
        "selection_basis": "auto_lowest_numeric_rank" if str(rank) == "auto" else "explicit",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mindie-profiler export-sim-case", description="Export a measured capture/report as a mindie-sim Case with observed profile metadata.", allow_abbrev=False)
    parser.add_argument("input_path", nargs="?", default=None, help="capture directory, report JSON, or metadata JSON")
    parser.add_argument("--capture-dir", "--input", "--root", dest="input_option", default=None, help="capture directory or JSON input")
    parser.add_argument("--chip", "--hardware", dest="chip", default=None, help="explicit Ascend SKU override (e.g. Ascend910B4, Ascend910_9392)")
    for flag in ("tp", "dp", "ep", "pp"): parser.add_argument(f"--{flag}", type=int, default=None, help=f"explicit {flag.upper()} parallelism degree override")
    for flags, dest, label in ((("--batch-size", "--concurrency"), "batch_size", "batch size / concurrency"), (("--seq-len", "--prompt-tokens"), "seq_len", "input sequence / prompt token length"), (("--decode-steps", "--output-tokens"), "decode_steps", "decode step / output token count")): parser.add_argument(*flags, dest=dest, type=int, default=None, help=f"explicit {label} override")
    for flag in ("model", "phase", "quant", "graph-mode", "hccl-expansion-mode"): parser.add_argument(f"--{flag}", default=None, help=f"explicit {flag.replace('-', ' ')} override")
    parser.add_argument("--rank", default="auto",
                        help="rank id/index for Case measurement files, or 'auto' (lowest numeric rank)")
    parser.add_argument("--max-num-seqs", type=int, default=None, help="runtime.max_num_seqs")
    parser.add_argument("--max-num-batched-tokens", type=int, default=None,
                        help="runtime.max_num_batched_tokens")
    parser.add_argument("--max-model-len", type=int, default=None, help="runtime.max_model_len")
    parser.add_argument("--kv-block-size", type=int, default=None, help="runtime.kv_block_size")
    parser.add_argument("--enable-chunked-prefill", action=argparse.BooleanOptionalAction,
                        default=None, help="runtime.enable_chunked_prefill")
    parser.add_argument("--async-scheduling", action=argparse.BooleanOptionalAction,
                        default=None, help="runtime.async_scheduling")
    parser.add_argument("--cp", type=int, default=None, help="context-parallel degree override")
    parser.add_argument("--diagnostic", action="store_true",
                        help="legacy descriptive export; fills defaults only when explicitly requested")
    parser.add_argument("--output", "-o", default=None, help="write exported mindie-sim Case JSON to path (prints summary receipt)")
    return parser

def _iter_files(root: Path, max_depth: int = 4, max_files: int = 4096) -> list[Path]:
    found: list[Path] = []
    for current, dirs, names in os.walk(root, onerror=_walk_err):
        depth = len(Path(current).relative_to(root).parts)
        dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS and depth < max_depth)
        for name in sorted(names):
            found.append(Path(current) / name)
            if len(found) >= max_files: return found
    return sorted(found, key=lambda item: (len(item.relative_to(root).parts), str(item)))

def _bundle_from_dir(root: Path, *, rank: str | int = "auto") -> dict[str, Any]:
    bundle = {**_empty_bundle(root), "source_path": str(root)}
    selected = None
    selection = None
    if root.is_dir():
        try:
            selected, selection = select_case_rank(root, rank)
        except ProfilerUsageError:
            selected, selection = None, None
    if selected is not None:
        bundle["rank_selection"] = selection
        bundle["selected_rank"] = selected.rank_id
        measurement_root = Path(selected.rank_dir).resolve()
    else:
        measurement_root = root.resolve()
    files = _iter_files(root)
    for path in files:
        name = path.name.lower()
        resolved = path.resolve()
        measurement_file = (
            name in _CSV_NAMES
            or (name.startswith(("ascend_pytorch_profiler", "msprof")) and name.endswith(".db"))
            or (name.startswith("trace_view") and name.endswith(".json"))
        )
        if measurement_file and measurement_root not in resolved.parents and resolved != measurement_root:
            continue
        if name in _JSON_NAMES:
            payload, key = _read_json(path), _JSON_NAMES[name]
            if key == "report" and _is_c7_report(payload): bundle["report"] = payload
            elif key != "report" and key not in bundle["json"]: bundle["json"][key] = payload
            if key == "run_meta" and isinstance(payload, Mapping) and isinstance(payload.get("env"), Mapping):
                bundle["env"].update({str(k): str(v) for k, v in payload["env"].items()})
        elif name == "meta.env": bundle["env"].update(_parse_env(_read_text(path)))
        elif name == "cmd.sh": bundle["cmd"] = _read_text(path)
        elif name in _CSV_NAMES and name not in bundle["csv"]: bundle["csv"][name] = path
    if bundle["report"] is None: bundle["report"] = next((p for p in bundle["json"].values() if _is_c7_report(p)), None)
    has_kernel_csv = any(
        name == "kernel_details.csv" or name.startswith("op_summary_")
        for name in bundle["csv"]
    )
    if (selected is not None and getattr(selected, "kind", None) == "db"
            and getattr(selected, "db_path", None) and not has_kernel_csv
            and bundle["report"] is None):
        from .sim_bridge_observed import _db_observed_profile

        try:
            bundle["db_observed"] = _db_observed_profile(Path(selected.db_path))
        except TimeoutError:
            raise
        except ProfilerError as exc:
            bundle["db_observed_error"] = str(exc)
    has_wave = bool({"run_meta", "benchmark_summary", "client_cell"} & bundle["json"].keys() or bundle["env"] or bundle["cmd"] or {"op_statistic.csv", "step_trace_time.csv", "api_statistic.csv"} & bundle["csv"].keys())
    has_prof = bool({"capture", "provenance"} & bundle["json"].keys() or "kernel_details.csv" in bundle["csv"] or any(("ascend_pytorch_profiler" in p.name and p.suffix == ".db") or any(part.startswith("rank_") for part in p.parts) for p in files))
    bundle["source_kind"] = ("capture_directory" if (has_wave and has_prof) else "wave5_capture" if has_wave else "profiler_capture" if has_prof else "directory")
    bundle["case_record"] = _find_case_record(bundle)
    return bundle

def _load_input(source: str | Path | Mapping[str, Any], *, rank: str | int = "auto") -> dict[str, Any]:
    if isinstance(source, Mapping): return _bundle_from_mapping(dict(source), None)
    try: path = Path(source).expanduser().resolve()
    except TimeoutError: raise
    except OSError as exc: raise ProfilerUsageError(f"cannot resolve input: {exc}") from exc
    if path.is_dir(): return _bundle_from_dir(path, rank=rank)
    if not path.is_file(): raise ProfilerUsageError(f"input does not exist: {path}")
    suffix = path.suffix.lower()
    if suffix == ".json": return _bundle_from_mapping(_read_json(path), path)
    if suffix == ".db":
        bundle = {**_empty_bundle(path.parent), "source_path": str(path),
                  "source_kind": "profiler_capture"}
        from .sim_bridge_observed import _db_observed_profile
        bundle["db_observed"] = _db_observed_profile(path)
        try:
            selected, selection = select_case_rank(path, rank)
            bundle["rank_selection"] = selection
            bundle["selected_rank"] = selected.rank_id
        except ProfilerUsageError:
            pass
        return bundle
    if suffix in {".csv", ".gz"}:
        bundle = {**_empty_bundle(path.parent), "source_path": str(path),
                  "source_kind": "profiler_capture"}
        bundle["csv"][path.name] = path
        return bundle
    if suffix in {".env", ".sh", ".txt"}:
        text, bundle = _read_text(path), {**_empty_bundle(path.parent), "source_kind": "metadata_file"}
        if suffix == ".env": bundle.update(env=_parse_env(text), text=text)
        else: bundle["cmd"] = text
        return bundle
    raise ProfilerUsageError(f"unsupported input file type: {path.suffix or path.name}")

def export_sim_case(input_path: str | Path | Mapping[str, Any], *, chip: str | None = None, model: str | None = None, tp: int | None = None, dp: int | None = None, ep: int | None = None, pp: int | None = None, cp: int | None = None, batch_size: int | None = None, seq_len: int | None = None, decode_steps: int | None = None, phase: str | None = None, quant: str | None = None, graph_mode: str | None = None, hccl_expansion_mode: str | None = None, rank: str | int = "auto", runtime_overrides: Mapping[str, Any] | None = None, output: str | Path | None = None, diagnostic: bool = False) -> dict[str, Any]:
    """Export a production simulation Case only from complete request facts.

    ``diagnostic=True`` is the explicit legacy/descriptive mode: it preserves
    the old defaulted Case, lists every filled default and sets
    ``production_prediction=false``.  The ordinary path raises a concrete gap
    instead of emitting a schema-valid guess.
    """
    overrides = {"chip": chip, "model": model, "tp": tp, "dp": dp, "ep": ep, "pp": pp, "cp": cp, "batch_size": batch_size, "seq_len": seq_len, "decode_steps": decode_steps, "phase": phase, "quant": quant, "graph_mode": graph_mode, "hccl_expansion_mode": hccl_expansion_mode}
    from .sim_bridge_observed import _RUNTIME_OVERRIDE_KEYS

    runtime_values = {
        key: value for key, value in (runtime_overrides or {}).items()
        if key in _RUNTIME_OVERRIDE_KEYS and value is not None
    }
    applied = sorted(k for k, v in overrides.items() if v is not None and v != "")
    applied.extend(f"runtime.{key}" for key in sorted(runtime_values))
    bundle = _load_input(input_path, rank=rank)
    explicit = bundle.get("explicit_case")
    if isinstance(explicit, Mapping) and not applied:
        case = json.loads(json.dumps(explicit))
        _attach_rank_selection(case, bundle)
        if output is not None:
            from .report import write_report
            write_report(case, output)
        return case
    candidate = bundle.get("explicit_case_candidate")
    candidate_gaps = (_case_request_gaps(candidate)
                      if isinstance(candidate, Mapping) else [])
    if candidate_gaps and not diagnostic:
        error = ProfilerUsageError(
            "sim_case_incomplete:" + ";".join(candidate_gaps))
        error.gaps = candidate_gaps
        raise error
    facts = _extract_facts(bundle, overrides)
    facts["runtime_facts"].update(runtime_values)
    observed = _extract_observed(bundle, facts)
    case = _build_case(facts, observed, applied)
    _attach_rank_selection(case, bundle)
    gaps = _production_gaps(facts, case)
    if gaps:
        if not diagnostic:
            error = ProfilerUsageError("sim_case_incomplete:" + ";".join(gaps))
            error.gaps = gaps
            raise error
        metadata = case["runtime"].setdefault("metadata", {})
        metadata["production_prediction"] = False
        metadata["diagnostic_mode"] = True
        metadata["diagnostic_gaps"] = list(gaps)
        metadata["diagnostic_filled_values"] = _diagnostic_filled_values(facts, case, gaps)
        aggregate = _mapping(_mapping(facts.get("workload")).get("_aggregate"))
        if aggregate.get("out_tokens") is not None or aggregate.get("n_ok") is not None:
            metadata["diagnostic_aggregate"] = {
                "out_tokens": aggregate.get("out_tokens"),
                "n_ok": aggregate.get("n_ok"),
                "per_request_output": aggregate.get("per_request_output"),
                "decode_from_aggregate": aggregate.get("decode_from_aggregate"),
            }
    if output is not None:
        from .report import write_report
        write_report(case, output)
    return case

def main(argv: Sequence[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    args = _parser().parse_args(raw[1:] if (raw and raw[0] == "export-sim-case") else raw)
    if not (source := args.input_option or args.input_path):
        print("mindie-profiler export-sim-case: an input path or --capture-dir is required", file=sys.stderr); return 2
    runtime_overrides = {
        "max_num_seqs": args.max_num_seqs,
        "max_num_batched_tokens": args.max_num_batched_tokens,
        "max_model_len": args.max_model_len,
        "kv_block_size": args.kv_block_size,
        "enable_chunked_prefill": args.enable_chunked_prefill,
        "async_scheduling": args.async_scheduling,
    }
    try: case = export_sim_case(source, chip=args.chip, model=args.model, tp=args.tp, dp=args.dp, ep=args.ep, pp=args.pp, cp=args.cp, batch_size=args.batch_size, seq_len=args.seq_len, decode_steps=args.decode_steps, phase=args.phase, quant=args.quant, graph_mode=args.graph_mode, hccl_expansion_mode=args.hccl_expansion_mode, rank=args.rank, runtime_overrides=runtime_overrides, output=args.output, diagnostic=args.diagnostic)
    except TimeoutError: raise
    except (ProfilerError, OSError, ValueError) as exc:
        print(f"mindie-profiler export-sim-case: {remote_guide_hint(exc)}", file=sys.stderr); return 2
    metadata = _mapping(_mapping(case.get("runtime")).get("metadata"))
    prov = _mapping(metadata.get("profiler_provenance"))
    summary = {"output": args.output, "schema_version": BRIDGE_SCHEMA,
               "source_kind": prov.get("source_kind"), "cell_tag": prov.get("cell_tag"),
               "hardware": prov.get("extracted_hardware"), "model": prov.get("extracted_model"),
               "production_prediction": metadata.get("production_prediction", True)}
    if metadata.get("diagnostic_gaps"):
        summary["diagnostic_gaps"] = metadata["diagnostic_gaps"]
    print(json.dumps(summary if args.output else case, ensure_ascii=False, indent=None if args.output else 2, sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())
