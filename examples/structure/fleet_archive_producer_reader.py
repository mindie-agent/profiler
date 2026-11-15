"""Streamed attention identities and closed prefill steps.

Query length is a tensor axis. A paged leading axis is cache capacity, not
logical K. Context 0 is a dense key axis that equals the new query, an explicit
prefix-caching disable on the recorded launch, or neither. A missing flag,
a designed prefix, and a summary cached-token field are not that proof.
"""
from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

_MAX_SHAPE_BYTES = 8 * 1024 * 1024
_MAX_IDENTITIES = 256
_MAX_RUNS = 64
_MATRIX_ROW_CAP = 2500
_ACTIVE_LAYOUTS = frozenset((
    "attention_active_qkv", "attention_paged_active_qkv", "attention_paged_mla_qk_rope",
))


def _note_shape_scan(source: Path, shapes: dict[str, Any] | None, frames: list[dict[str, Any]],
                     binding: Mapping[str, Any], notes: list[str]) -> None:
    """The 8MiB leading-integer scan stays blind. A streamed ABI either maps or says so."""
    if binding.get("overflow"):
        notes.append("attention_identity_bound_exceeded")
        return
    unidentified = int(binding.get("layout_not_identified") or 0)
    if unidentified and binding.get("identities") and not binding.get("overflow"):
        notes.append(f"fia_rows_layout_not_identified_{unidentified}")
    if shapes is not None or frames:
        return
    if binding.get("opened") and binding.get("fia_rows"):
        notes.append("attention_shapes_streamed_abi_not_identified")
        return
    if binding.get("opened") and not binding.get("fia_rows"):
        notes.append("no_fused_infer_attention_rows")
        return
    if source.is_file() and source.stat().st_size > _MAX_SHAPE_BYTES:
        notes.append("attention_shapes_not_scanned_source_larger_than_8mib")


def _shape_slots(text: str, numeric: bool) -> list | None:
    found: list = []
    for part in (text or "").strip().strip('"').split(";"):
        part = part.strip().strip('"')
        if not part:
            found.append(() if numeric else "")
            continue
        if not numeric:
            found.append(part)
            continue
        pieces = [item.strip() for item in part.split(",")]
        if any(not piece.isdigit() for piece in pieces):
            return None
        found.append(tuple(int(piece) for piece in pieces))
    return found


def _kernel_family(name: str) -> str:
    if "GroupedMatmul" in name:
        return "grouped"
    if "Matmul" in name or "MatMul" in name:
        return "matmul"
    if "MoeGatingTopK" in name:
        return "gating"
    if "MoeTokenPermute" in name:
        return "permute"
    return ""


def _rank2(slot: Any) -> tuple[int, int] | None:
    if isinstance(slot, tuple) and len(slot) == 2 and all(isinstance(item, int) and not isinstance(item, bool) for item in slot):
        return slot
    return None


def witness_launch_matrices(source: Path, *, row_cap: int = _MATRIX_ROW_CAP) -> dict[str, Any]:
    """Same-run matmul and routed shapes, bounded by row_cap.

    Widths are only numbers that appear on those contracts. A missing column
    or a cap with no contracts is an empty witness, not a catalog width.
    """
    witness: dict[str, Any] = {
        "opened": False, "rows_seen": 0, "capped": False,
        "matmul_kn": [], "grouped_kn": [], "expert_axes": [], "topk_axes": [],
        "gating_topk": [], "permute_widths": [],
    }
    if not isinstance(source, Path) or not source.is_file() or source.name.endswith(".gz"):
        return witness
    matmul: set[tuple[int, int]] = set()
    grouped: set[tuple[int, int]] = set()
    experts: set[int] = set()
    topk: set[int] = set()
    gating_topk: set[int] = set()
    permute: set[int] = set()
    try:
        with source.open(newline="", encoding="utf-8", errors="replace") as handle:
            reader = csv.DictReader(handle)
            names = reader.fieldnames or []
            if "Name" not in names or "Input Shapes" not in names:
                return witness
            witness["opened"] = True
            for index, row in enumerate(reader):
                if index >= row_cap:
                    witness["capped"] = True
                    break
                witness["rows_seen"] = index + 1
                family = _kernel_family(row.get("Name") or "")
                if not family:
                    continue
                inputs = _shape_slots(row.get("Input Shapes") or "", True)
                outputs = _shape_slots(row.get("Output Shapes") or "", True)
                if inputs is None:
                    continue
                if family == "gating" and inputs:
                    gate = _rank2(inputs[0])
                    if gate is not None and gate[1] >= 1:
                        experts.add(gate[1])
                    if outputs and gate is not None:
                        for slot in outputs:
                            chosen = _rank2(slot)
                            if chosen is not None and chosen[1] >= 1 and chosen[1] != gate[1]:
                                gating_topk.add(chosen[1])
                    continue
                if family == "permute" and len(inputs) >= 2:
                    hidden = _rank2(inputs[0])
                    index_slot = _rank2(inputs[1])
                    if hidden is not None and hidden[1] >= 1:
                        permute.add(hidden[1])
                    if index_slot is not None and index_slot[1] >= 1:
                        topk.add(index_slot[1])
                    continue
                if not inputs:
                    continue
                left = _rank2(inputs[0])
                if left is None:
                    continue
                if family == "matmul":
                    if len(inputs) < 2 or outputs is None or not outputs:
                        continue
                    right = _rank2(inputs[1])
                    out = _rank2(outputs[0])
                    if right is None or out is None or left[1] != right[1] or out != (left[0], right[0]):
                        continue
                    if left[1] >= 1 and right[0] >= 1:
                        matmul.add((left[1], right[0]))
                    continue
                if family == "grouped":
                    if outputs is None or not outputs:
                        continue
                    out = _rank2(outputs[0])
                    if out is None or out[0] != left[0] or left[1] < 1 or out[1] < 1:
                        continue
                    grouped.add((left[1], out[1]))
    except OSError:
        witness["opened"] = False
        return witness
    witness["matmul_kn"] = [list(item) for item in sorted(matmul)]
    witness["grouped_kn"] = [list(item) for item in sorted(grouped)]
    witness["expert_axes"] = sorted(experts)
    witness["topk_axes"] = sorted(topk)
    witness["gating_topk"] = sorted(gating_topk)
    witness["permute_widths"] = sorted(permute)
    return witness


def _clock_class(stamp: float, window: Mapping[str, Any] | None) -> str:
    if not isinstance(window, Mapping):
        return "profile_window_absent"
    start, stop = window.get("start_profile_epoch"), window.get("stop_profile_epoch")
    if not isinstance(start, (int, float)) or not isinstance(stop, (int, float)):
        return "profile_window_absent"
    seconds = stamp / 1_000_000.0
    if seconds < start:
        return "before_profile_window"
    if seconds > stop:
        return "after_profile_window"
    return "inside_profile_window"


def _table_shape(label: str, inputs: tuple) -> tuple:
    if label == "attention_paged_mla_qk_rope":
        index = 4 if len(inputs) == 7 else 14
    elif label == "attention_paged_active_qkv":
        index = 6 if len(inputs) == 7 else 14
    else:
        return ()
    if index >= len(inputs) or not isinstance(inputs[index], tuple):
        return ()
    return inputs[index]


def _layout_axes(label: str, inputs: tuple) -> dict[str, Any] | None:
    """Query axis from a contract that already separated pages from tokens."""
    query = inputs[0] if inputs else ()
    key = inputs[1] if len(inputs) > 1 else ()
    value = inputs[2] if len(inputs) > 2 else ()
    if label == "attention_paged_mla_qk_rope" and len(query) == 4 and len(key) == 4:
        table = _table_shape(label, inputs)
        return {
            "query_rows": query[2], "query_batch": query[0], "sequences_per_replica": query[0],
            "query_shape": list(query), "key_shape": list(key), "value_shape": list(value),
            "cache_capacity_pages": key[0], "cache_block_size": key[2], "cache_kv_heads": key[1],
            "cache_packed_width": None, "block_table_shape": list(table),
            "key_tensor_tokens": None,
        }
    if label == "attention_paged_active_qkv" and len(query) == 3 and len(key) == 3:
        table = _table_shape(label, inputs)
        return {
            "query_rows": query[0], "query_batch": None, "sequences_per_replica": None,
            "query_shape": list(query), "key_shape": list(key), "value_shape": list(value),
            "cache_capacity_pages": key[0], "cache_block_size": key[1], "cache_kv_heads": None,
            "cache_packed_width": key[2], "block_table_shape": list(table),
            "key_tensor_tokens": None,
        }
    if label == "attention_active_qkv" and len(query) == 3 and len(key) == 3:
        return {
            "query_rows": query[0], "query_batch": None, "sequences_per_replica": None,
            "query_shape": list(query), "key_shape": list(key), "value_shape": list(value),
            "cache_capacity_pages": None, "cache_block_size": None, "cache_kv_heads": key[1],
            "cache_packed_width": None, "block_table_shape": None,
            "key_tensor_tokens": key[0],
        }
    return None


def _observe_task(item: dict[str, Any], task: Any, layers: int | None) -> None:
    if item.get("cycle_failed") or not isinstance(layers, int) or layers < 1 or task in (None, ""):
        item["cycle_failed"] = True
        return
    seen: list[str] = item["cycle_ids"]
    text = str(task)
    if len(seen) < layers:
        seen.append(text)
        return
    if text != seen[(item["observed_call_count"] - 1) % layers]:
        item["cycle_failed"] = True
        item["cycle_ids"] = []


def _mark_break(binding: dict[str, Any]) -> None:
    if binding.get("run_overflow"):
        return
    runs: list[dict[str, Any]] = binding["runs"]
    if runs and runs[-1].get("break"):
        return
    if len(runs) >= _MAX_RUNS:
        binding["run_overflow"] = True
        return
    runs.append({"break": True})


def _record_run(binding: dict[str, Any], identity_index: int) -> None:
    if binding.get("run_overflow"):
        return
    runs: list[dict[str, Any]] = binding["runs"]
    if runs and not runs[-1].get("break") and runs[-1].get("identity_index") == identity_index:
        runs[-1]["calls"] += 1
        return
    if len(runs) >= _MAX_RUNS:
        binding["run_overflow"] = True
        return
    runs.append({"identity_index": identity_index, "calls": 1})


def _stream_attention_binding(path: Path, window: Mapping[str, Any] | None, layers: int | None) -> dict[str, Any]:
    """One pass. Retain distinct ABI identities, not a row per kernel call."""
    binding: dict[str, Any] = {
        "opened": False, "fia_rows": 0, "layout_not_identified": 0, "identities": [],
        "overflow": False, "max_identities": _MAX_IDENTITIES, "runs": [], "run_overflow": False,
    }
    if not path.is_file() or path.name.endswith(".gz"):
        return binding
    from mindie_profiler.body_attention_contracts import observed_attention_contract

    index: dict[tuple, dict[str, Any]] = {}
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            reader = csv.DictReader(handle)
            names = reader.fieldnames or []
            if "Name" not in names or "Input Shapes" not in names:
                return binding
            binding["opened"] = True
            for row in reader:
                name = row.get("Name") or ""
                if "FusedInferAttentionScore" not in name or "Slice" in name or "AttentionUpdate" in name:
                    continue
                binding["fia_rows"] += 1
                inputs = _shape_slots(row.get("Input Shapes") or "", True)
                outputs = _shape_slots(row.get("Output Shapes") or "", True)
                dtypes = _shape_slots(row.get("Input Data Types") or "", False)
                formats = _shape_slots(row.get("Input Formats") or "", False)
                out_dtypes = _shape_slots(row.get("Output Data Types") or "", False)
                out_formats = _shape_slots(row.get("Output Formats") or "", False)
                if None in (inputs, outputs, dtypes, formats, out_dtypes, out_formats):
                    binding["layout_not_identified"] += 1
                    _mark_break(binding)
                    continue
                kind = row.get("Type") or "FusedInferAttentionScore"
                if kind != "FusedInferAttentionScore":
                    binding["layout_not_identified"] += 1
                    _mark_break(binding)
                    continue
                contract = observed_attention_contract(SimpleNamespace(
                    kind=kind, input_shapes=inputs, input_dtypes=dtypes, input_formats=formats,
                    output_shapes=outputs, output_dtypes=out_dtypes, output_formats=out_formats,
                ))
                label = contract[0] if isinstance(contract, tuple) else ""
                axes = _layout_axes(label, tuple(inputs)) if label in _ACTIVE_LAYOUTS else None
                if axes is None or not isinstance(axes.get("query_rows"), int) or axes["query_rows"] < 1:
                    binding["layout_not_identified"] += 1
                    _mark_break(binding)
                    continue
                try:
                    stamp = float(row.get("Start Time(us)") or 0)
                except (TypeError, ValueError):
                    stamp = None
                device = str(row.get("Device_id") or "") or None
                key = (label, tuple(inputs), tuple(outputs), device)
                item = index.get(key)
                if item is None:
                    if len(index) >= _MAX_IDENTITIES:
                        binding["overflow"] = True
                        _mark_break(binding)
                        continue
                    absolute_window = (
                        window if isinstance(window, Mapping)
                        and isinstance(window.get("start_profile_epoch"), (int, float))
                        and isinstance(window.get("stop_profile_epoch"), (int, float))
                        else None
                    )
                    clock = {name: 0 for name in (
                        "before_profile_window", "inside_profile_window", "after_profile_window",
                    )} if absolute_window is not None else {"profile_window_absent": 0}
                    item = {
                        **axes, "layout": label, "device_id": device, "observed_call_count": 0,
                        "clock": clock, "clock_unparsed": 0, "cycle_ids": [], "cycle_failed": False,
                        "output_shape": list(outputs[0]) if outputs else [],
                        "input_shapes": [list(part) for part in inputs],
                        "identity_index": len(binding["identities"]),
                    }
                    index[key] = item
                    binding["identities"].append(item)
                item["observed_call_count"] += 1
                if stamp is None:
                    item["clock_unparsed"] += 1
                else:
                    item["clock"][_clock_class(stamp, absolute_window)] += 1
                _observe_task(item, row.get("Task ID"), layers)
                _record_run(binding, int(item["identity_index"]))
    except OSError:
        return binding
    binding["num_layers"] = layers
    return binding


def _layer_cycle(item: Mapping[str, Any], layers: int | None) -> dict[str, Any]:
    count = int(item.get("observed_call_count") or 0)
    proven = (
        not item.get("cycle_failed") and isinstance(layers, int) and layers >= 1
        and count >= layers and count % layers == 0 and len(item.get("cycle_ids") or ()) == layers
    )
    if not isinstance(layers, int):
        return {"source": "num_layers_not_in_same_run_documents", "proven": False}
    record = {"source": "kernel_task_id_file_order", "num_layers": layers, "proven": proven}
    if proven:
        record["closure_count"] = count // layers
    return record


def _declaration_frames(binding: Mapping[str, Any], phase: str) -> list[dict[str, Any]]:
    """One frame per distinct tensor identity. Call multiplicity is not copied out."""
    frames = []
    phase_name = phase or None
    layers = binding.get("num_layers")
    for item in binding.get("identities") or ():
        query = item.get("query_rows")
        if not isinstance(query, int) or isinstance(query, bool) or query < 1:
            continue
        frame = {
            "schedule_role": "model_argument_identity",
            "forward_id": None,
            "phase": phase_name,
            "query_rows": query,
            "context_tokens": None,
            "logical_context_tokens": None,
            "device_id": item.get("device_id"),
            "rank_id": None,
            "basis": f"{item.get('layout')}_query_axis_cache_capacity_is_not_logical_k",
            "layout": item.get("layout"),
            "query_shape": item.get("query_shape"),
            "key_shape": item.get("key_shape"),
            "value_shape": item.get("value_shape"),
            "output_shape": item.get("output_shape"),
            "input_shapes": item.get("input_shapes"),
            "query_batch": item.get("query_batch"),
            "cache_capacity_pages": item.get("cache_capacity_pages"),
            "cache_block_size": item.get("cache_block_size"),
            "cache_kv_heads": item.get("cache_kv_heads"),
            "cache_packed_width": item.get("cache_packed_width"),
            "block_table_shape": item.get("block_table_shape"),
            "block_table_columns_are_capacity": bool(item.get("block_table_shape")),
            "key_tensor_tokens": item.get("key_tensor_tokens"),
            "observed_call_count": item.get("observed_call_count"),
            "clock_class_counts": dict(item.get("clock") or {}),
            "clock_unparsed": item.get("clock_unparsed") or 0,
            "layer_cycle": _layer_cycle(item, layers if isinstance(layers, int) else None),
        }
        if isinstance(item.get("sequences_per_replica"), int) and not isinstance(item.get("sequences_per_replica"), bool):
            frame["sequences_per_replica"] = item["sequences_per_replica"]
        frames.append(frame)
    return frames


def _shapes_from_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    queries: list[int] = []
    pages: list[int] = []
    for item in binding.get("identities") or ():
        query = item.get("query_rows")
        if isinstance(query, int) and query not in queries:
            queries.append(query)
        page = item.get("cache_capacity_pages")
        if isinstance(page, int) and page not in pages:
            pages.append(page)
    return {
        "basis": "fia_native_tensor_abi_streamed",
        "query_rows": queries,
        "uniform_query_rows": queries[0] if len(queries) == 1 else None,
        "logical_kv_rows": None,
        "cache_capacity_pages": pages,
        "cache_capacity_is_not_logical_k": True,
        "fia_rows": binding.get("fia_rows"),
        "fia_rows_layout_not_identified": binding.get("layout_not_identified"),
        "identity_count": len(binding.get("identities") or ()),
        "stream_bound": {"max_identities": binding.get("max_identities"), "overflow": False},
    }


def _once(notes: list[str], text: str) -> None:
    if text not in notes:
        notes.append(text)


def _positive(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def _match_window(windows: Sequence[Mapping[str, Any]] | None, query: int, device: Any, phase: str) -> Mapping[str, Any] | None:
    """One receipt window with the same query, device, and phase. Empty rank is not filled in."""
    if not windows or device in (None, ""):
        return None
    hits = []
    for window in windows:
        if not isinstance(window, Mapping):
            continue
        if window.get("query_rows") != query:
            continue
        if str(window.get("device_id") or "") != str(device):
            continue
        declared = str(window.get("phase") or phase).lower()
        if declared != phase:
            continue
        if window.get("forward_id") in (None, ""):
            continue
        hits.append(window)
    if len(hits) != 1:
        return None
    return hits[0]


def _closed_prefill_steps(binding: Mapping[str, Any] | None, *, phase: str, prompt: int | None,
                          windows: Sequence[Mapping[str, Any]] | None, prefix_caching: bool | None,
                          notes: list[str], sequence_proof: str | None = None) -> list[dict[str, Any]]:
    """Full q and KV-end for a prefill whose tensor or explicit disable closes the context.

    File order is the run list. A later paged query may use the prior closed KV
    end. Its page count and block table stay capacity.
    """
    if phase != "prefill" or not isinstance(binding, Mapping):
        return []
    declared_prompt = _positive(prompt)
    if declared_prompt is None:
        return []
    if binding.get("overflow") or binding.get("run_overflow"):
        _once(notes, "prefill_attention_run_order_not_bounded")
        return []
    identities = list(binding.get("identities") or ())
    runs = list(binding.get("runs") or ())
    if not runs:
        return []
    steps: list[dict[str, Any]] = []
    cursor = 0
    chain_open = True
    for run in runs:
        if not isinstance(run, Mapping) or run.get("break") or not chain_open:
            chain_open = False
            continue
        index = run.get("identity_index")
        if not isinstance(index, int) or isinstance(index, bool) or index < 0 or index >= len(identities):
            chain_open = False
            continue
        item = identities[index]
        query = _positive(item.get("query_rows"))
        layout = item.get("layout")
        key_tokens = item.get("key_tensor_tokens")
        device = item.get("device_id")
        if query is None or layout not in _ACTIVE_LAYOUTS:
            chain_open = False
            continue
        context = None
        basis = None
        if layout == "attention_active_qkv" and isinstance(key_tokens, int) and not isinstance(key_tokens, bool) and key_tokens >= query:
            physical = key_tokens - query
            if physical != cursor:
                _once(notes, "prefill_dense_key_disagrees_with_running_kv_end")
                chain_open = False
                continue
            context = physical
            basis = "dense_key_token_axis_equals_new_query" if physical == 0 else "dense_key_token_axis_includes_prior_kv"
        elif (
            prefix_caching is False and cursor == 0 and layout == "attention_paged_active_qkv"
            and item.get("key_tensor_tokens") is None
        ):
            context = 0
            basis = "launch_prefix_caching_explicitly_disabled"
        elif (
            layout == "attention_paged_active_qkv" and item.get("key_tensor_tokens") is None and cursor > 0
        ):
            context = cursor
            basis = "prior_closed_kv_end_file_order_paged_capacity_not_context"
        else:
            _once(notes, "prefill_chunk_context_not_physical")
            chain_open = False
            continue
        window = _match_window(windows, query, device, phase)
        if window is None:
            _once(notes, "prefill_receipt_device_forward_link_absent")
            chain_open = False
            continue
        rank = window.get("rank_id")
        if rank in (None, ""):
            rank = None
            _once(notes, "receipt_rank_id_empty_device_forward_linked")
        if item.get("cache_capacity_pages") is not None:
            _once(notes, "paged_cache_capacity_not_used_as_context")
        steps.append({
            "schedule_role": "prefill_physical_step",
            "forward_id": window.get("forward_id"),
            "phase": phase,
            "query_rows": query,
            "context_tokens": context,
            "logical_context_tokens": context,
            "kv_end": context + query,
            "device_id": device,
            "rank_id": rank,
            "basis": basis,
            "layout": layout,
            "query_shape": item.get("query_shape"),
            "key_shape": item.get("key_shape"),
            "key_tensor_tokens": key_tokens if isinstance(key_tokens, int) and not isinstance(key_tokens, bool) else None,
            "cache_capacity_pages": item.get("cache_capacity_pages"),
            "cache_block_size": item.get("cache_block_size"),
            "block_table_shape": item.get("block_table_shape"),
            "block_table_columns_are_capacity": bool(item.get("block_table_shape")),
            "cache_capacity_is_not_logical_k": item.get("cache_capacity_pages") is not None,
            "observed_call_count": run.get("calls"),
        })
        cursor = context + query
    if not steps:
        return []
    if windows and len(steps) == len(windows):
        if any(step["query_rows"] != window.get("query_rows") for step, window in zip(steps, windows) if isinstance(window, Mapping)):
            _once(notes, "prefill_file_order_disagrees_with_receipt_window_order")
            return []
    admitted = sum(step["query_rows"] for step in steps)
    if admitted != declared_prompt:
        _once(notes, "prefill_admitted_query_sum_is_not_declared_prompt")
    if prefix_caching is True and any(step["context_tokens"] == 0 for step in steps):
        _once(notes, "prefix_caching_enabled_context_taken_from_key_or_prior_kv")
    if sequence_proof:
        devices = {step.get("device_id") for step in steps if step.get("device_id") not in (None, "")}
        if len(devices) == 1:
            for step in steps:
                step["sequences_per_replica"] = 1
                step["sequences_basis"] = sequence_proof + "_single_device"
        else:
            _once(notes, "sequences_not_deduced_across_devices")
    return steps
