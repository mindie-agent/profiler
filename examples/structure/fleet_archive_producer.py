"""Producer workload files for archive cases. Path labels are not token lengths."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping

from fleet_archive_launch import (
    _launch_table,
    _match_launch,
    _merge_spec,
    _parse_cmd,
    _parse_env,
    clear_launch_cache,
)
from fleet_archive_producer_reader import (
    _MAX_SHAPE_BYTES,
    _closed_prefill_steps,
    _declaration_frames,
    _note_shape_scan,
    _shapes_from_binding,
    _stream_attention_binding,
)
from fleet_archive_sources import (
    agreed_receipt_windows, annotate_public_frames, as_int, device_inventory, sha256,
)

_ATTENTION = "FusedInferAttentionScore_FusedInferAttentionScore"
_PRODUCER: dict[str, dict[str, Any]] = {}


def clear_producer_caches() -> None:
    clear_launch_cache()
    _PRODUCER.clear()


def producer_declaration(source: Path, projections: list[Mapping[str, Any]], phase: str | None = None) -> dict[str, Any]:
    key = str(source)
    cached = _PRODUCER.get(key)
    if cached is not None:
        return cached
    conflicts: list[str] = []
    notes: list[str] = []
    sources: list[dict[str, Any]] = []
    client, evidence = _agreed_receipt_context(projections, conflicts)
    files = _producer_files(source)
    documents = _load_producer_documents(files, evidence, conflicts, sources)
    launch = _match_launch(source, files.get("launch_scripts") or [], documents.get("cmd"), conflicts, sources)
    launch = _merge_spec(launch, documents, conflicts)
    usage = documents.get("usage")
    requests = _request_rows(usage)
    votes_prompt = _prompt_votes(client, evidence, documents, launch, requests)
    if _exporter_output_placeholder(client, evidence):
        notes.append("receipt_client_output_tokens_placeholder:192:eval_a5_wave5.extract_or_load")
        client = {key: value for key, value in client.items() if key != "output_tokens"}
    votes_output = _output_votes(client, documents, launch, requests)
    prompt, prompt_conflict = _vote("prompt_tokens", votes_prompt)
    output, output_conflict = _vote("output_tokens", votes_output)
    for item in (prompt_conflict, output_conflict):
        if item:
            conflicts.append(item)
    prefix = _prefix(documents, launch, notes)
    token_exact, exact_conflict = _token_exact(evidence, documents)
    if exact_conflict:
        conflicts.append(exact_conflict)
    concurrency = _concurrency(client, documents, requests)
    window = _profile_window(documents)
    captured = _chunk_window(requests, window, notes)
    binding = _stream_attention_binding(source, window, _layer_count(documents))
    if binding.get("identities") and not binding.get("overflow"):
        shapes = _shapes_from_binding(binding)
    else:
        shapes = _attention_shapes(source)
    frames, executed_graph, receipt_windows, window_fields = annotate_public_frames(_physical_frames(
        source, projections, documents, requests, launch, prefix, prompt, concurrency, window, notes, phase, binding,
    ), projections, launch, notes)
    _note_shape_scan(source, shapes, frames, binding, notes)
    declared = {
        "prompt_tokens": prompt, "output_tokens": output, "concurrency": concurrency,
        "token_exact": token_exact, "requests": [{key: item.get(key) for key in (
            "idx", "lane", "request_id", "source", "prompt_tokens", "output_tokens",
            "prompt_ids_len", "completion_tokens", "ok", "chunk_count", "chunk_timebase",
            "t_start_epoch", "t_end_rel_s", "lane_is_physical_rank",
        ) if key in item} for item in requests] if requests else [],
        "prefix": prefix, "context_evidence": evidence, "client": client, "launch": launch,
        "profile_window": window, "captured_window": captured, "attention_shapes": shapes,
        "frames": frames, "executed_graph": executed_graph, "receipt_windows": receipt_windows,
        "window_fields": window_fields, "batch": _batch(concurrency, documents), "npu": _npu(documents), "sources": sources,
        "window_timebase": window.get("timebase") if isinstance(window, Mapping) else None,
        "window_origin": window.get("origin") if isinstance(window, Mapping) else None,
        "window_valid": window.get("window_valid") if isinstance(window, Mapping) else None,
        "inflight_at_start": window.get("inflight_at_start") if isinstance(window, Mapping) else None,
        "inflight_at_stop": window.get("inflight_at_stop") if isinstance(window, Mapping) else None,
        "client_lane_is_not_physical_rank": True,
        "request_context_bounds": _request_context_bounds(requests) or None,
        "conflicts": conflicts, "notes": notes,
    }
    _PRODUCER[key] = declared
    return declared


def _agree_field(items: list[Mapping[str, Any]], key: str, conflicts: list[str], label: str):
    values = [item.get(key) for item in items if key in item and item.get(key) is not None]
    unique = []
    for value in values:
        if value not in unique:
            unique.append(value)
    if len(unique) > 1:
        conflicts.append(f"conflict:{label}:{key}:" + ",".join(str(value) for value in unique))
        return None
    return unique[0] if unique else None


def _agreed_receipt_context(projections: list[Mapping[str, Any]], conflicts: list[str]) -> tuple[dict, dict]:
    clients = [item.get("client") or {} for item in projections if item.get("client")]
    evidences = [item.get("context_evidence") or {} for item in projections if item.get("context_evidence")]
    client = {}
    for key in ("input_len", "concurrency", "output_tokens"):
        value = _agree_field(clients, key, conflicts, "receipt_client")
        if value is not None:
            client[key] = value
    evidence = {}
    for key in ("representative_tokens", "lower_bound_tokens", "upper_bound_tokens", "requested_prefix_tokens", "requested_suffix_tokens", "basis", "per_step_context_observed", "client_token_exact", "source_path", "source_sha256", "source_size", "limitation"):
        value = _agree_field(evidences, key, conflicts, "receipt_context_evidence")
        if value is not None or any(key in item and item.get(key) is None for item in evidences):
            if value is not None:
                evidence[key] = value
            elif key in ("requested_prefix_tokens", "requested_suffix_tokens") and any(key in item for item in evidences):
                evidence[key] = None
    return client, evidence


def _producer_files(source: Path) -> dict[str, Any]:
    found: dict[str, Any] = {}
    directory = source.parent
    for name, role in (
        ("benchmark_summary.json", "benchmark_summary"), ("client_cell.json", "client_cell"),
        ("run_meta.json", "run_meta"), ("meta.env", "meta_env"), ("cmd.sh", "cmd"),
    ):
        path = directory / name
        if path.is_file():
            found[role] = path
    scripts: list[Path] = []
    if directory.parent.name == "prof":
        campaign = directory.parent.parent
        cellset = campaign / "raw" / f"cellset_{directory.name}.json"
        if cellset.is_file():
            found["cellset"] = cellset
        for name in ("run_wave234_v2.sh", "run_wave23.sh"):
            script = campaign / name
            if script.is_file():
                scripts.append(script)
    if scripts:
        found["launch_scripts"] = scripts
    return found


def _load_json(path: Path) -> dict | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return document if isinstance(document, dict) else None


def _load_producer_documents(files: Mapping[str, Any], evidence: Mapping[str, Any], conflicts: list[str], sources: list[dict[str, Any]]) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for role in ("benchmark_summary", "client_cell", "cellset", "run_meta"):
        path = files.get(role)
        if isinstance(path, Path):
            document = _load_json(path)
            if document is not None:
                loaded[role] = document
                sources.append({"role": role, "path": str(path), "sha256": sha256(path), "size_bytes": path.stat().st_size})
    pointed = evidence.get("source_path")
    digest = evidence.get("source_sha256")
    if isinstance(pointed, str) and Path(pointed).is_file():
        actual = sha256(Path(pointed))
        if isinstance(digest, str) and actual != digest:
            conflicts.append(f"conflict:context_evidence_source_sha_mismatch:{actual}!={digest}")
        else:
            document = _load_json(Path(pointed))
            if document is not None:
                loaded["evidence_source"] = document
                sources.append({"role": "context_evidence_source", "path": pointed, "sha256": actual, "size_bytes": Path(pointed).stat().st_size})
    env_path = files.get("meta_env")
    if isinstance(env_path, Path):
        loaded["meta_env"] = _parse_env(env_path.read_text(encoding="utf-8", errors="replace"))
        sources.append({"role": "meta_env", "path": str(env_path), "sha256": sha256(env_path), "size_bytes": env_path.stat().st_size})
    cmd_path = files.get("cmd")
    if isinstance(cmd_path, Path):
        loaded["cmd"] = _parse_cmd(cmd_path.read_text(encoding="utf-8", errors="replace"))
        sources.append({"role": "cmd", "path": str(cmd_path), "sha256": sha256(cmd_path), "size_bytes": cmd_path.stat().st_size})
    loaded["usage"] = _pick_usage(files, loaded)
    return loaded


def _pick_usage(files: Mapping[str, Any], loaded: Mapping[str, Any]) -> dict | None:
    for key in ("evidence_source", "benchmark_summary", "client_cell"):
        document = loaded.get(key)
        if isinstance(document, Mapping) and (
                isinstance(document.get("requests"), list) or isinstance(document.get("per_request"), list)):
            return dict(document)
    cellset = loaded.get("cellset")
    cellset_path = files.get("cellset")
    if isinstance(cellset, Mapping) and isinstance(cellset_path, Path):
        cells = cellset.get("cells") if isinstance(cellset.get("cells"), list) else []
        name = cells[0].get("cell") if cells and isinstance(cells[0], Mapping) else None
        if isinstance(name, str):
            path = cellset_path.parent / f"{name}.json"
            document = _load_json(path) if path.is_file() else None
            if isinstance(document, Mapping) and (
                    isinstance(document.get("requests"), list) or isinstance(document.get("per_request"), list)):
                return dict(document)
    return None


def _summary(document: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        return {}
    summary = document.get("summary")
    if isinstance(summary, Mapping):
        return dict(summary)
    return {}


def _request_rows(usage: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Normalize retained `requests` or declarative client `per_request` rows.

    A client lane is request identity, never a physical rank. Absolute chunk
    epochs and request-relative intervals keep their own timebase; the window
    matcher compares them only when both origins agree.
    """
    if not isinstance(usage, Mapping):
        return []
    raw = usage.get("requests")
    source = "requests"
    if not isinstance(raw, list) or not raw:
        raw = usage.get("per_request")
        source = "per_request"
    if not isinstance(raw, list):
        return []
    rows = []
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            continue
        body = item.get("usage") if isinstance(item.get("usage"), Mapping) else {}
        prompt = as_int(item.get("prompt_tokens"))
        if prompt is None:
            prompt = as_int(item.get("prompt_ids_len"))
        if prompt is None:
            prompt = as_int(body.get("prompt_tokens"))
        output = as_int(item.get("completion_tokens"))
        if output is None:
            output = as_int(body.get("completion_tokens"))
        epochs = item.get("chunk_epochs") if isinstance(item.get("chunk_epochs"), list) else []
        intervals = item.get("itl_ms") if isinstance(item.get("itl_ms"), list) else []
        intervals = [float(value) for value in intervals if isinstance(value, (int, float))]
        count = as_int(item.get("n_text_chunks"))
        if count is None:
            count = len(epochs) if epochs else (len(intervals) + 1 if intervals else None)
        chunk_epochs = [float(value) for value in epochs if isinstance(value, (int, float))]
        ttft = item.get("ttft_ms") if isinstance(item.get("ttft_ms"), (int, float)) else item.get("ttft_s")
        if isinstance(ttft, (int, float)):
            ttft_ms = float(ttft) * 1000.0 if item.get("ttft_s") is not None else float(ttft)
        else:
            ttft_ms = None
        offsets: list[float] = []
        if not chunk_epochs and intervals and ttft_ms is not None:
            offsets = [ttft_ms / 1000.0]
            for value in intervals:
                offsets.append(offsets[-1] + value / 1000.0)
        lane = as_int(item.get("lane"))
        idx = item.get("idx")
        if idx is None:
            idx = lane if lane is not None else index
        row = {
            "idx": idx, "lane": lane, "source": source,
            "request_id": lane if lane is not None else idx,
            "lane_is_physical_rank": False,
            "prompt_tokens": prompt, "output_tokens": output,
            "prompt_ids_len": as_int(item.get("prompt_ids_len")),
            "completion_tokens": as_int(item.get("completion_tokens")),
            "ok": item.get("ok") is True,
            "status": item.get("status"),
            "chunk_count": count,
            "chunk_epochs": chunk_epochs,
            "chunk_intervals_ms": intervals,
            "chunk_offsets_s": offsets,
            "chunk_timebase": "absolute_epoch" if chunk_epochs else ("request_start_relative" if offsets else None),
            "t_start_epoch": float(item["t_start_epoch"]) if isinstance(item.get("t_start_epoch"), (int, float)) else None,
            "t_end_rel_s": float(item["t_end_rel_s"]) if isinstance(item.get("t_end_rel_s"), (int, float)) else None,
            "ttft_ms": ttft_ms,
        }
        if prompt is None:
            row.pop("prompt_tokens")
        if output is None:
            row.pop("output_tokens")
        rows.append(row)
    return rows


def _request_context_bounds(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Request envelope, not an exact per-window logical-K claim."""
    rows = []
    for item in requests:
        prompt = item.get("prompt_tokens")
        output = item.get("output_tokens")
        if not isinstance(prompt, int) or isinstance(prompt, bool) or prompt < 0:
            continue
        upper = prompt + output if isinstance(output, int) and not isinstance(output, bool) and output >= 0 else None
        rows.append({
            "idx": item.get("idx"), "lane": item.get("lane"), "source": item.get("source"),
            "lower_tokens": prompt, "upper_tokens": upper,
            "basis": "prompt_tokens+completion_tokens", "exact_per_window": False,
            "lane_is_physical_rank": False,
        })
    return rows


def _design(document: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        return {}
    design = document.get("design")
    if isinstance(design, Mapping):
        return dict(design)
    summary = _summary(document)
    nested = summary.get("design")
    return dict(nested) if isinstance(nested, Mapping) else {}


def _prompt_votes(client, evidence, documents, launch, requests) -> list[tuple[str, int]]:
    votes: list[tuple[str, int]] = []
    if as_int(client.get("input_len")) is not None:
        votes.append(("receipt_client", as_int(client.get("input_len"))))
    if as_int(evidence.get("representative_tokens")) is not None and evidence.get("basis") == "retained_request_prompt_usage":
        votes.append(("receipt_representative", as_int(evidence.get("representative_tokens"))))
    for role in ("cellset", "usage", "evidence_source", "benchmark_summary", "client_cell"):
        number = as_int(_design(documents.get(role)).get("prompt_tokens"))
        if number is not None:
            votes.append((role, number))
    prompts = {item["prompt_tokens"] for item in requests if isinstance(item.get("prompt_tokens"), int)}
    if len(prompts) == 1:
        votes.append(("usage_requests", next(iter(prompts))))
    env = documents.get("meta_env") if isinstance(documents.get("meta_env"), Mapping) else {}
    if as_int(env.get("INPUT_LEN")) is not None:
        votes.append(("meta_env", as_int(env.get("INPUT_LEN"))))
    run = documents.get("run_meta") if isinstance(documents.get("run_meta"), Mapping) else {}
    workload = run.get("workload") if isinstance(run.get("workload"), Mapping) else {}
    if as_int(workload.get("input_len")) is not None:
        votes.append(("run_meta", as_int(workload.get("input_len"))))
    if isinstance(launch, Mapping) and as_int(launch.get("input_len")) is not None:
        votes.append(("launch", as_int(launch.get("input_len"))))
    return [(name, value) for name, value in votes if value is not None]


def _output_votes(client, documents, launch, requests) -> list[tuple[str, int]]:
    votes: list[tuple[str, int]] = []
    if as_int(client.get("output_tokens")) is not None:
        votes.append(("receipt_client", as_int(client.get("output_tokens"))))
    for role in ("cellset", "usage"):
        number = as_int(_design(documents.get(role)).get("max_tokens"))
        if number is not None:
            votes.append((role, number))
    outputs = {item["output_tokens"] for item in requests if isinstance(item.get("output_tokens"), int)}
    if len(outputs) == 1:
        votes.append(("usage_requests", next(iter(outputs))))
    env = documents.get("meta_env") if isinstance(documents.get("meta_env"), Mapping) else {}
    if as_int(env.get("OUTPUT_LEN")) is not None:
        votes.append(("meta_env", as_int(env.get("OUTPUT_LEN"))))
    run = documents.get("run_meta") if isinstance(documents.get("run_meta"), Mapping) else {}
    workload = run.get("workload") if isinstance(run.get("workload"), Mapping) else {}
    if as_int(workload.get("output_len")) is not None:
        votes.append(("run_meta", as_int(workload.get("output_len"))))
    if isinstance(launch, Mapping) and as_int(launch.get("output_len")) is not None:
        votes.append(("launch", as_int(launch.get("output_len"))))
    return [(name, value) for name, value in votes if value is not None]


def _exporter_output_placeholder(client: Mapping[str, Any], evidence: Mapping[str, Any]) -> bool:
    return as_int(client.get("output_tokens")) == 192 and evidence.get("basis") == "run_meta_workload_input_len"


def _npu(documents: Mapping[str, Any]) -> dict[str, Any]:
    return device_inventory(documents)


def _vote(label: str, votes: list[tuple[str, int]]) -> tuple[int | None, str | None]:
    present = [(name, value) for name, value in votes if value is not None]
    unique = {value for _, value in present}
    if len(unique) > 1:
        return None, "conflict:" + label + ":" + ",".join(f"{name}={value}" for name, value in present)
    if len(unique) == 1:
        return next(iter(unique)), None
    return None, None


def _prefix_block(document: Mapping[str, Any] | None) -> dict[str, Any]:
    summary = _summary(document)
    prefix = summary.get("prefix") if isinstance(summary.get("prefix"), Mapping) else {}
    if prefix:
        return dict(prefix)
    cells = document.get("cells") if isinstance(document, Mapping) and isinstance(document.get("cells"), list) else []
    if cells and isinstance(cells[0], Mapping) and isinstance(cells[0].get("prefix"), Mapping):
        return dict(cells[0]["prefix"])
    return {}


def _prefix(documents: Mapping[str, Any], launch: Mapping[str, Any] | None, notes: list[str]) -> dict[str, Any]:
    observed = None
    for role in ("usage", "evidence_source", "benchmark_summary", "client_cell", "cellset"):
        block = _prefix_block(documents.get(role))
        cached = as_int(block.get("cached_tokens"))
        if cached is None:
            continue
        if observed is None:
            observed = cached
        elif observed != cached:
            notes.append(f"prefix_cache_disagrees:{observed}!={cached}")
    designed_rows: list[dict[str, Any]] = []
    for role in ("cellset", "usage"):
        number = as_int(_design(documents.get(role)).get("shared_tokens"))
        if number is not None:
            designed_rows.append({"source": f"{role}.design.shared_tokens", "tokens": number})
    env = documents.get("meta_env") if isinstance(documents.get("meta_env"), Mapping) else {}
    if as_int(env.get("PREFIX_LEN")) is not None:
        designed_rows.append({"source": "meta.env:PREFIX_LEN", "tokens": as_int(env.get("PREFIX_LEN"))})
    run = documents.get("run_meta") if isinstance(documents.get("run_meta"), Mapping) else {}
    workload = run.get("workload") if isinstance(run.get("workload"), Mapping) else {}
    if as_int(workload.get("prefix_len")) is not None:
        designed_rows.append({"source": "run_meta.workload.prefix_len", "tokens": as_int(workload.get("prefix_len"))})
    if isinstance(launch, Mapping) and as_int(launch.get("prefix_len")) is not None:
        designed_rows.append({"source": "launch.prefix_len", "tokens": as_int(launch.get("prefix_len"))})
    designed = [item["tokens"] for item in designed_rows]
    designed_value = designed[0] if designed and len(set(designed)) == 1 else None
    if len(set(designed)) > 1:
        notes.append("designed_prefix_sources_disagree")
    if isinstance(observed, int) and isinstance(designed_value, int) and observed != designed_value:
        notes.append("designed_shared_tokens_not_observed_cache")
    block = _prefix_block(documents.get("usage") or documents.get("cellset"))
    return {
        "observed_cached_tokens": observed, "observed_hits": as_int(block.get("hits")),
        "observed_queries": as_int(block.get("queries")), "designed_prefix_tokens": designed_value,
        "designed_prefix_by_source": designed_rows or None,
        "designed_shared_not_applied_as_cache": bool(isinstance(observed, int) and isinstance(designed_value, int) and observed != designed_value),
    }


def _token_exact(evidence: Mapping[str, Any], documents: Mapping[str, Any]) -> tuple[bool | None, str | None]:
    flags = []
    if isinstance(evidence.get("client_token_exact"), bool):
        flags.append(("receipt", evidence["client_token_exact"]))
    for role in ("usage", "cellset", "benchmark_summary", "client_cell"):
        document = documents.get(role)
        summary = _summary(document)
        if not summary and role == "cellset" and isinstance(documents.get(role), Mapping):
            cells = documents[role].get("cells") if isinstance(documents[role].get("cells"), list) else []
            summary = cells[0] if cells and isinstance(cells[0], Mapping) else {}
        if isinstance(summary.get("token_exact"), bool):
            flags.append((role, summary["token_exact"]))
        if isinstance(document, Mapping) and isinstance(document.get("token_exact"), bool):
            flags.append((f"{role}.top_level", document["token_exact"]))
    values = {item for _, item in flags}
    if len(values) > 1:
        return None, "conflict:token_exact:" + ",".join(f"{name}={value}" for name, value in flags)
    return (next(iter(values)), None) if values else (None, None)


def _concurrency(client: Mapping[str, Any], documents: Mapping[str, Any], requests: list[dict[str, Any]]) -> int | None:
    votes = []
    if as_int(client.get("concurrency")) is not None:
        votes.append(as_int(client.get("concurrency")))
    for role in ("usage", "cellset"):
        document = documents.get(role)
        summary = _summary(document)
        if role == "cellset" and isinstance(document, Mapping):
            cells = document.get("cells") if isinstance(document.get("cells"), list) else []
            if cells and isinstance(cells[0], Mapping) and as_int(cells[0].get("concurrency")) is not None:
                votes.append(as_int(cells[0].get("concurrency")))
        if as_int(summary.get("concurrency")) is not None:
            votes.append(as_int(summary.get("concurrency")))
    env = documents.get("meta_env") if isinstance(documents.get("meta_env"), Mapping) else {}
    if as_int(env.get("CONCURRENCY")) is not None:
        votes.append(as_int(env.get("CONCURRENCY")))
    run = documents.get("run_meta") if isinstance(documents.get("run_meta"), Mapping) else {}
    workload = run.get("workload") if isinstance(run.get("workload"), Mapping) else {}
    if as_int(workload.get("concurrency")) is not None:
        votes.append(as_int(workload.get("concurrency")))
    if requests:
        votes.append(len(requests))
    unique = {item for item in votes if item is not None}
    return next(iter(unique)) if len(unique) == 1 else None


def _batch(concurrency: int | None, documents: Mapping[str, Any]) -> dict[str, Any]:
    running = None
    inflight_start = None
    inflight_stop = None
    for role in ("usage", "cellset"):
        document = documents.get(role)
        summary = _summary(document)
        if role == "cellset" and isinstance(document, Mapping):
            cells = document.get("cells") if isinstance(document.get("cells"), list) else []
            if cells and isinstance(cells[0], Mapping):
                running = as_int(cells[0].get("max_running")) if running is None else running
        if running is None:
            running = as_int(summary.get("max_running"))
        if isinstance(document, Mapping):
            block = document.get("profile_window") if isinstance(document.get("profile_window"), Mapping) else {}
            inflight_start = as_int(block.get("inflight_at_start")) if inflight_start is None else inflight_start
            inflight_stop = as_int(block.get("inflight_at_stop")) if inflight_stop is None else inflight_stop
            profile = summary.get("profile") if isinstance(summary.get("profile"), Mapping) else {}
            inflight_start = as_int(profile.get("inflight_at_start")) if inflight_start is None else inflight_start
            inflight_stop = as_int(profile.get("inflight_at_stop")) if inflight_stop is None else inflight_stop
    return {"global_concurrency": concurrency, "max_running": running,
            "inflight_at_start": inflight_start, "inflight_at_stop": inflight_stop,
            "client_lane_is_not_physical_rank": True,
            "basis": "concurrency_max_running_and_local_batch_are_distinct"}


def _profile_window(documents: Mapping[str, Any]) -> dict[str, Any] | None:
    """Normalize an absolute epoch window or a declarative relative window.

    The returned origin is explicit so a relative client window is never
    silently compared with absolute request epochs.
    """
    for role in ("cellset", "usage", "benchmark_summary", "client_cell", "run_meta"):
        document = documents.get(role)
        if not isinstance(document, Mapping):
            continue
        label = "client_cell" if isinstance(document.get("per_request"), list) else role
        profile = None
        if role == "cellset":
            cells = document.get("cells") if isinstance(document.get("cells"), list) else []
            profile = cells[0].get("profile") if cells and isinstance(cells[0], Mapping) else None
        elif role == "run_meta":
            metrics = document.get("metrics") if isinstance(document.get("metrics"), Mapping) else {}
            summary = metrics.get("summary") if isinstance(metrics.get("summary"), Mapping) else {}
            profile = summary.get("profile")
        else:
            profile = _summary(document).get("profile")
        if isinstance(profile, Mapping):
            start, stop = profile.get("start_profile_epoch"), profile.get("stop_profile_epoch")
            if isinstance(start, (int, float)) and isinstance(stop, (int, float)):
                return {
                    "start_profile_epoch": start, "stop_profile_epoch": stop,
                    "timebase": "absolute_epoch", "origin": "absolute_epoch",
                    "source": label, "window_valid": profile.get("window_valid"),
                    "inflight_at_start": profile.get("inflight_at_start"),
                    "inflight_at_stop": profile.get("inflight_at_stop"),
                }
        block = document.get("profile_window")
        if not isinstance(block, Mapping):
            continue
        start, stop = block.get("t_start_profile_req"), block.get("t_stop_profile_done")
        if isinstance(start, (int, float)) and isinstance(stop, (int, float)):
            return {
                "start_rel_s": start, "stop_rel_s": stop,
                "timebase": "relative", "origin": "client_start_relative",
                "source": f"{label}.profile_window",
                "window_valid": block.get("window_valid"),
                "inflight_at_start": block.get("inflight_at_start"),
                "inflight_at_stop": block.get("inflight_at_stop"),
                "engine_window_s": block.get("engine_window_s"),
                "metrics_interval_s": block.get("metrics_interval_s"),
                "start_status": block.get("start_status"),
                "stop_status": block.get("stop_status"),
            }
    return None


def _chunk_window(requests: list[dict[str, Any]], window: Mapping[str, Any] | None, notes: list[str]) -> dict[str, Any] | None:
    if not requests:
        return None
    counts = [item["chunk_count"] for item in requests]
    outputs = [item["output_tokens"] for item in requests if isinstance(item.get("output_tokens"), int)]
    if counts and outputs and any(count != output for count, output in zip(counts, outputs)):
        notes.append("client_chunks_are_not_sequence_tokens")
    rows = []
    timebase = None
    origin = None
    if isinstance(window, Mapping):
        timebase = window.get("timebase")
        origin = window.get("origin")
        if timebase == "absolute_epoch" and isinstance(window.get("start_profile_epoch"), (int, float)):
            start, stop = window["start_profile_epoch"], window["stop_profile_epoch"]
            for item in requests:
                epochs = item.get("chunk_epochs") or []
                inside = [index for index, epoch in enumerate(epochs) if start <= epoch <= stop]
                rows.append({"idx": item.get("idx"), "lane": item.get("lane"),
                             "chunk_count": item["chunk_count"],
                             "in_window_first": inside[0] if inside else None,
                             "in_window_last": inside[-1] if inside else None,
                             "in_window_count": len(inside)})
        elif timebase == "relative" and isinstance(window.get("start_rel_s"), (int, float)):
            start, stop = window["start_rel_s"], window["stop_rel_s"]
            for item in requests:
                offsets = item.get("chunk_offsets_s") or []
                match = item.get("chunk_timebase") == origin
                inside = [index for index, offset in enumerate(offsets) if start <= offset <= stop] if match else []
                rows.append({"idx": item.get("idx"), "lane": item.get("lane"),
                             "chunk_count": item["chunk_count"],
                             "in_window_first": inside[0] if inside else None,
                             "in_window_last": inside[-1] if inside else None,
                             "in_window_count": len(inside) if match else None,
                             "window_match": "same_origin" if match else "timebase_origin_not_equal"})
    return {
        "chunks_are_not_sequence_tokens": True,
        "window_source": window.get("source") if isinstance(window, Mapping) else None,
        "window_timebase": timebase,
        "window_origin": origin,
        "window_valid": window.get("window_valid") if isinstance(window, Mapping) else None,
        "inflight_at_start": window.get("inflight_at_start") if isinstance(window, Mapping) else None,
        "inflight_at_stop": window.get("inflight_at_stop") if isinstance(window, Mapping) else None,
        "requests": rows,
    }


def _attention_shapes(path: Path) -> dict[str, Any] | None:
    if not path.is_file() or path.name.endswith(".gz") or path.stat().st_size > _MAX_SHAPE_BYTES:
        return None
    rows = []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or "Name" not in reader.fieldnames or "Input Shapes" not in reader.fieldnames:
                return None
            for row in reader:
                if _ATTENTION not in (row.get("Name") or ""):
                    continue
                try:
                    stamp = float(row.get("Start Time(us)") or 0)
                except ValueError:
                    stamp = 0.0
                rows.append((stamp, row.get("Input Shapes") or ""))
    except OSError:
        return None
    seen_q: list[int] = []
    seen_kv: list[int] = []
    for _, shapes in sorted(rows):
        leadings = _leadings(shapes)
        if not leadings:
            continue
        if leadings[0] not in seen_q:
            seen_q.append(leadings[0])
        for value in leadings[1:]:
            if value != leadings[0] and value not in seen_kv:
                seen_kv.append(value)
    if not seen_q:
        return None
    return {"query_rows": seen_q, "kv_rows": seen_kv, "uniform_query_rows": seen_q[0] if len(seen_q) == 1 else None,
            "basis": "kernel_attention_input_shapes_time_ordered"}


def _phase_of(projections: list[Mapping[str, Any]], fallback: str | None = None) -> str:
    found = list(dict.fromkeys(str(item["phase"]).lower() for item in projections if item.get("phase")))
    if len(found) == 1:
        return found[0]
    return str(fallback or "").lower() if not found else ""

def _layer_count(documents: Mapping[str, Any]) -> int | None:
    votes = []
    env = documents.get("meta_env") if isinstance(documents.get("meta_env"), Mapping) else {}
    if as_int(env.get("NUM_LAYERS")) is not None:
        votes.append(as_int(env.get("NUM_LAYERS")))
    run = documents.get("run_meta") if isinstance(documents.get("run_meta"), Mapping) else {}
    arch = run.get("architecture_override") if isinstance(run.get("architecture_override"), Mapping) else {}
    if as_int(arch.get("num_hidden_layers")) is not None:
        votes.append(as_int(arch.get("num_hidden_layers")))
    unique = {item for item in votes if item is not None}
    return next(iter(unique)) if len(unique) == 1 else None


def _leadings(shapes: str) -> list[int]:
    found = []
    for part in shapes.strip().strip('"').split(";"):
        pieces = [piece.strip() for piece in part.split(",") if piece.strip()]
        if len(pieces) >= 3 and pieces[0].isdigit():
            found.append(int(pieces[0]))
    return found


def _scan_kernel(path: Path) -> dict[str, Any] | None:
    if not path.is_file() or path.name.endswith(".gz"):
        return None
    zeros: list[tuple[float, int]] = []
    fia: list[dict[str, Any]] = []
    argmax = 0
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or "Name" not in reader.fieldnames or "Input Shapes" not in reader.fieldnames:
                return None
            for row in reader:
                name = row.get("Name") or ""
                shapes = row.get("Input Shapes") or ""
                try:
                    stamp = float(row.get("Start Time(us)") or 0)
                except ValueError:
                    stamp = 0.0
                if "ZerosLike" in name:
                    token = shapes.strip().strip('"')
                    if token.isdigit():
                        zeros.append((stamp, int(token)))
                elif "FusedInferAttentionScore" in name and "Slice" not in name and "AttentionUpdate" not in name:
                    lead = _leadings(shapes)
                    if lead:
                        distinct = [value for value in lead[1:] if value != lead[0]]
                        fia.append({"t": stamp, "q": lead[0], "kv": distinct[0] if distinct else None,
                                    "device_id": str(row.get("Device_id") or "") or None})
                elif "ArgMax" in name:
                    argmax += 1
    except OSError:
        return None
    devices = {item["device_id"] for item in fia if item.get("device_id")}
    return {"zeros": [item[1] for item in sorted(zeros)], "zero_times": sorted(zeros),
            "fia": sorted(fia, key=lambda item: item["t"]), "argmax": argmax,
            "device_id": next(iter(devices)) if len(devices) == 1 else None}


def _frame(phase: str, forward_id: int, query: int, context: int, device: str | None, basis: str) -> dict[str, Any]:
    return {"forward_id": forward_id, "phase": phase, "query_rows": query, "context_tokens": context,
            "device_id": device, "rank_id": None, "basis": basis}


def _prefill_frames(path: Path, prompt: int | None, cached: int | None,
                    documents: Mapping[str, Any], notes: list[str]) -> list[dict[str, Any]]:
    if not isinstance(prompt, int) or prompt < 1 or not isinstance(cached, int) or cached < 0:
        return []
    markers = _scan_kernel(path)
    if not markers:
        return []
    device = markers["device_id"]
    spans = _prefill_spans(markers, prompt, cached, notes)
    if spans:
        return [_frame("prefill", index, query, context, device, "prefill_zeroslike_spans_sum_to_prompt")
                for index, (query, context) in enumerate(spans)]
    queries = [item["q"] for item in markers["fia"]]
    layers = _layer_count(documents)
    if queries and all(value == prompt for value in queries) and (len(queries) == 1 or layers == len(queries)):
        return [_frame("prefill", 0, prompt, cached, device, "producer_initial_cache_and_uniform_attention_query")]
    return []


def _prefill_spans(markers: Mapping[str, Any], prompt: int, cached: int, notes: list[str]) -> list[tuple[int, int]] | None:
    zeros = markers["zero_times"]
    queries = [item[1] for item in zeros]
    if not queries or sum(queries) != prompt or any(item < 1 for item in queries):
        return None
    assigned: list[list[dict[str, Any]]] = [[] for _ in queries]
    cursor = -1
    events = [("z", item[0], index) for index, item in enumerate(zeros)]
    events.extend(("f", item["t"], item) for item in markers["fia"])
    for kind, _stamp, payload in sorted(events, key=lambda item: item[1]):
        if kind == "z":
            cursor = int(payload)
            continue
        if cursor < 0:
            notes.append("prefill_attention_before_chunk_marker")
            return None
        assigned[cursor].append(payload)
    spans = []
    done = cached
    for index, query in enumerate(queries):
        for item in assigned[index]:
            if item["q"] != query:
                notes.append("prefill_attention_query_disagrees_with_chunk_marker")
                return None
            kv = item.get("kv")
            if isinstance(kv, int) and kv not in (query, done, done + query):
                notes.append(f"prefill_attention_kv_{kv}_disagrees_with_context_{done}")
                return None
        spans.append((query, done))
        done += query
    return spans


def _decode_tail_frames(path: Path, requests: list[dict[str, Any]], launch: Mapping[str, Any] | None,
                        concurrency: int | None, window: Mapping[str, Any] | None,
                        documents: Mapping[str, Any], notes: list[str]) -> list[dict[str, Any]]:
    spec = as_int(launch.get("spec_k")) if isinstance(launch, Mapping) else None
    if spec != 0 or concurrency != 1 or not isinstance(window, Mapping):
        return []
    if len(requests) != 1 or requests[0].get("ok") is not True:
        return []
    request = requests[0]
    prompt, output = request.get("prompt_tokens"), request.get("output_tokens")
    epochs = request.get("chunk_epochs") or []
    if not isinstance(prompt, int) or not isinstance(output, int) or output < 2 or len(epochs) != output:
        return []
    if request.get("chunk_count") != output:
        return []
    start, stop = window.get("start_profile_epoch"), window.get("stop_profile_epoch")
    if not isinstance(start, (int, float)) or not isinstance(stop, (int, float)):
        return []
    if not (epochs[-1] <= stop and epochs[0] < start) or any(item > stop for item in epochs):
        return []
    layers = _layer_count(documents)
    markers = _scan_kernel(path)
    if not isinstance(layers, int) or layers < 1 or not markers or not markers["fia"]:
        return []
    if any(item["q"] != 1 for item in markers["fia"]) or len(markers["fia"]) % layers:
        notes.append("decode_tail_not_confirmed")
        return []
    count = len(markers["fia"]) // layers
    if markers["argmax"] != count or not (1 <= count < output):
        notes.append("decode_tail_not_confirmed")
        return []
    inside = sum(1 for item in epochs if start <= item <= stop)
    if not (count <= inside <= count + 1):
        notes.append("decode_tail_not_confirmed")
        return []
    base = output - count
    return [_frame("decode", base + step, 1, prompt + base + step - 1, markers["device_id"],
                   "decode_tail_layer_closures_match_completion_suffix")
            | {"output_ordinal": base + step + 1, "captured_ordinal": step} for step in range(count)]


def _one_request_sequence_proof(requests: list[dict[str, Any]], concurrency: int | None,
                                max_running: Any) -> str | None:
    """One request on one later-checked device. Heads and max_num_seqs are not a batch."""
    ok = [item for item in requests if item.get("ok") is True]
    if len(ok) != 1 or concurrency != 1:
        return None
    running = as_int(max_running)
    if max_running is not None and running != 1:
        return None
    if running == 1:
        return "one_ok_request_concurrency_one_max_running_one"
    return "one_ok_request_concurrency_one"


def _physical_frames(source: Path, projections: list[Mapping[str, Any]], documents: Mapping[str, Any],
                     requests: list[dict[str, Any]], launch: Mapping[str, Any] | None, prefix: Mapping[str, Any],
                     prompt: int | None, concurrency: int | None, window: Mapping[str, Any] | None,
                     notes: list[str], phase: str | None = None, binding: Mapping[str, Any] | None = None,
                     ) -> list[dict[str, Any]]:
    phase = _phase_of(projections, phase)
    stepped: list[dict[str, Any]] = []
    if phase == "prefill":
        cached = prefix.get("observed_cached_tokens") if isinstance(prefix, Mapping) else None
        stepped = _prefill_frames(source, prompt, cached, documents, notes)
    elif phase == "decode":
        stepped = _decode_tail_frames(source, requests, launch, concurrency, window, documents, notes)
    if not stepped and phase == "prefill":
        windows, _window_note = agreed_receipt_windows(projections)
        caching = launch.get("enable_prefix_caching") if isinstance(launch, Mapping) else None
        running = _batch(concurrency, documents).get("max_running")
        proof = _one_request_sequence_proof(requests, concurrency, running)
        stepped = _closed_prefill_steps(
            binding, phase=phase, prompt=prompt, windows=windows,
            prefix_caching=caching if isinstance(caching, bool) else None, notes=notes,
            sequence_proof=proof,
        )
    if stepped:
        return stepped
    if binding and binding.get("identities") and not binding.get("overflow"):
        return _declaration_frames(binding, phase)
    return []
