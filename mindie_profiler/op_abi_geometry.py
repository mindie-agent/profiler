"""Catalog-qualified geometry and parameter derivation for the ABI bridge.

[Role]
  Turn preserved positional ``Slot`` records plus the resolved catalog entry
  into strict ``mindie_sim.op_formulas`` parameters.  Attention and matrix
  geometry live in dedicated submodules; this module owns linear-attention
  state ownership, vector/quant/collective/routing geometry and the public
  re-exports consumed by ``op_abi_bridge``.

[Invariants]
  * Mandatory positional slots are validated in place; a missing, empty or
    malformed mandatory slot raises ``AbiError`` with a stable code.
  * ``initial_state``/``final_state`` owners, heads, Dk/Dv and floating dtype
    are cross-checked against Q/K/V; the declared state dtype drives bytes.
  * Collective ``world_size`` must be a positive integer; native AllGather and
    ReduceScatter reconcile their local/gathered output volumes exactly.
  * The real catalog padding contract is applied to the captured slots with
    ``compute_padding`` and ``operator_charge``; no synthetic shape is built.

[Timeouts & Locks]
  Pure in-memory arithmetic proportional to declared slots; no I/O.

[Side-Effect Policy]
  No mutation of the input row or slots; returns fresh params/flags mappings.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from mindie_profiler.op_abi_geometry_common import (
    _attr_values, _capture_ints, _encoding, _int_attr, _lengths, _present,
    _paired_lengths, _strict_int_attr,
    require_dtype, require_float_dtype, require_output, require_slot,
)
from mindie_profiler.op_abi_geometry_vector import rms_params, swiglu_params
from mindie_profiler.op_abi_geometry_matrix import grouped_params, matmul_params
from mindie_profiler.op_abi_attention import _causal, attention_params
from mindie_profiler.op_abi_slots import AbiError, Slot

from mindie_sim.op_formulas.hardware import dtype_bytes
from mindie_sim.op_formulas.errors import FormulaValidationError
from mindie_sim.op_formulas.ops_comm import mc2_ownership
from mindie_sim.op_formulas.primitives import strict_int, strict_state_dtype


def _find_state(slots: Sequence[Slot],
                preferred: tuple[str, ...] = (),
                index: int | None = None,
                fallback: bool = True) -> Slot | None:
    """Locate a state slot by name/position before validating its rank.

    A supplied rank-3 or malformed state must reach ``_state_axes`` and be
    rejected; it must never be filtered out and silently replaced by the
    final/default state.
    """
    for name in preferred:
        for slot in slots:
            if slot.name.lower() == name:
                return slot
    if index is not None:
        return slots[index] if index < len(slots) else None
    if fallback:
        for slot in slots:
            if slot.valid and "state" in slot.name.lower():
                return slot
        for slot in slots:
            if slot.valid and slot.rank == 4:
                return slot
    return None


def _state_axes(state: Slot, heads: int, head_dim: int, head_dim_v: int,
                what: str) -> tuple[int, str]:
    if state.rank != 4:
        raise AbiError(f"{what}_rank", f"{state.shape}")
    owners, state_heads, state_dk, state_dv = state.shape
    if state_heads != heads:
        raise AbiError(f"{what}_head_mismatch",
                       f"state heads {state_heads} != Q heads {heads}")
    if state_dk != head_dim:
        raise AbiError(f"{what}_dk_mismatch",
                       f"state Dk {state_dk} != Q Dk {head_dim}")
    if state_dv != head_dim_v:
        raise AbiError(f"{what}_dv_mismatch",
                       f"state Dv {state_dv} != V Dv {head_dim_v}")
    dtype = require_float_dtype(state, what)
    strict_state_dtype(dtype, f"{what}_dtype")
    return int(owners), dtype


def _rate_shape(slot: Slot, tokens: int, heads: int, head_dim: int,
                what: str, prefix: tuple[int, ...] | None = None) -> tuple[int, str]:
    if not slot.valid or slot.shape is None:
        raise AbiError(f"{what}_invalid", f"{slot.shape}")
    dtype = require_float_dtype(slot, what)
    dims = tuple(slot.dims)
    scalar = (tokens, heads) if prefix is None else prefix + (heads,)
    if dims in {scalar, scalar + (head_dim,)}:
        return int(math.prod(dims)), dtype
    raise AbiError(f"{what}_axes", f"{dims} vs {scalar}")


def chunk_params(row: Mapping[str, Any], inputs: Sequence[Slot],
                 outputs: Sequence[Slot]
                 ) -> tuple[dict[str, Any], dict[str, Any]]:
    q = require_slot(inputs, 0, "q")
    k = require_slot(inputs, 1, "k")
    v = require_slot(inputs, 2, "v")
    if q.rank != 3 or k.rank != 3 or v.rank != 3:
        raise AbiError("chunk_rank", f"{q.shape} {k.shape} {v.shape}")
    tokens, heads, head_dim = q.shape
    if tuple(k.shape) != (tokens, heads, head_dim):
        raise AbiError("chunk_k_mismatch", f"K {k.shape} vs Q {q.shape}")
    if v.shape[:2] != (tokens, heads):
        raise AbiError("chunk_v_mismatch", f"V {v.shape} vs Q {q.shape}")
    q_dtype = require_float_dtype(q, "q")
    if require_float_dtype(k, "k") != q_dtype \
            or require_float_dtype(v, "v") != q_dtype:
        raise AbiError("chunk_dtype_mismatch", f"{q.dtype}/{k.dtype}/{v.dtype}")
    head_dim_v = int(v.shape[-1])
    beta = require_slot(inputs, 3, "beta")
    gate = require_slot(inputs, 4, "g")
    beta_elems, beta_dtype = _rate_shape(beta, tokens, heads, head_dim, "beta")
    gate_elems, gate_dtype = _rate_shape(gate, tokens, heads, head_dim, "gate")
    initial = _find_state(inputs, ("initial_state",), 5, fallback=False)
    final = _find_state(outputs, ("final_state",), 1, fallback=False)
    states = []
    for label, slot in (("initial_state", initial), ("final_state", final)):
        if slot is None or not _present(slot):
            continue
        if not slot.valid or slot.shape is None:
            raise AbiError(f"chunk_state_{label}", f"{slot.shape}")
        sequences, state_dtype = _state_axes(slot, heads, head_dim,
                                             head_dim_v, "chunk_state")
        states.append((slot, sequences, state_dtype))
    if len(states) == 2:
        left, right = states[0][0], states[1][0]
        if tuple(left.shape) != tuple(right.shape) or left.dtype != right.dtype:
            raise AbiError("chunk_state_mismatch",
                           f"{left.shape}/{left.dtype} vs "
                           f"{right.shape}/{right.dtype}")
    sequences = states[0][1] if states else 1
    state_dtype = states[0][2] if states else "fp32"
    out = require_output(outputs, "chunk output")
    if out.rank != 3 or tuple(out.dims) != (tokens, heads, head_dim_v):
        raise AbiError("chunk_output_shape",
                       f"{out.shape} != {(tokens, heads, head_dim_v)}")
    out_dtype = require_float_dtype(out, "chunk output")
    raw = _attr_values(row, inputs, ("actual_seq_lengths", "actual_seq_lens",
                                     "cu_seqlens"))
    encoding = _encoding(row, "BSND")
    lens = (_lengths(raw, encoding=encoding, total=tokens,
                     expected=sequences, label="sequence")
            if raw is not None else None)
    params = {
        "tokens": tokens, "heads": heads, "head_dim": head_dim,
        "batch": sequences, "dtype": q_dtype, "out_dtype": out_dtype,
        "state_dtype": state_dtype,
        "beta_elems": beta_elems, "beta_dtype": beta_dtype,
        "gate_elems": gate_elems, "gate_dtype": gate_dtype,
    }
    if head_dim_v is not None:
        params["head_dim_v"] = head_dim_v
    if lens is not None:
        params["actual_seq_lens"] = list(lens)
    return params, {}


def recurrent_params(row: Mapping[str, Any], inputs: Sequence[Slot],
                     outputs: Sequence[Slot]
                     ) -> tuple[dict[str, Any], dict[str, Any]]:
    q, k, v = [require_slot(inputs, i, name)
               for i, name in enumerate(("q", "k", "v"))]
    if q.rank not in {3, 4} or k.shape != q.shape:
        raise AbiError("recurrent_qk_shape", f"{q.shape}/{k.shape}")
    prefix, heads, head_dim = q.dims[:-2], q.dims[-2], q.dims[-1]
    tokens, slots = prefix[0], prefix[1] if len(prefix) == 2 else 1
    if v.rank != q.rank or v.dims[:-1] != q.dims[:-1]:
        raise AbiError("recurrent_v_shape", f"{v.shape} vs {q.shape}")
    head_dim_v = v.dims[-1]
    q_dtype = require_float_dtype(q, "q")
    for slot, name in ((k, "k"), (v, "v")):
        if require_float_dtype(slot, name) != q_dtype:
            raise AbiError("recurrent_dtype_mismatch", name)
    gate = require_slot(inputs, 3, "gate")
    beta = require_slot(inputs, 4, "beta")
    gate_elems, gate_dtype = _rate_shape(gate, tokens, heads, head_dim, "gate", prefix)
    beta_elems, beta_dtype = _rate_shape(beta, tokens, heads, head_dim, "beta", prefix)
    state = _find_state(inputs, ("initial_state",), 5, fallback=False)
    if not _present(state) or not state.valid or state.shape is None:
        raise AbiError("missing_tensor_slot", "recurrent initial_state")
    owners, state_dtype = _state_axes(state, heads, head_dim, head_dim_v, "recurrent_state")
    if owners != tokens:
        raise AbiError("recurrent_state_ownership", f"{owners} != {tokens}")
    final = _find_state(outputs, ("final_state",), 1, fallback=False)
    if _present(final):
        if not final.valid or final.shape != state.shape:
            raise AbiError("recurrent_state_shape", f"{final.shape} vs {state.shape}")
        if _state_axes(final, heads, head_dim, head_dim_v, "final_state") != (owners, state_dtype):
            raise AbiError("recurrent_state_dtype", f"{final.dtype} vs {state_dtype}")
    out = require_output(outputs, "recurrent output")
    if out.shape != v.shape:
        raise AbiError("recurrent_output_shape", f"{out.shape} vs {v.shape}")
    out_dtype = require_float_dtype(out, "recurrent output")
    spec = _int_attr(row, ("spec_slots", "num_spec_tokens", "num_accepted_tokens"), slots)
    if spec != slots:
        raise AbiError("recurrent_spec_slots", f"{spec} != shaped slots {slots}")
    return ({"tokens": tokens, "heads": heads, "head_dim": head_dim,
             "head_dim_v": head_dim_v, "batch": tokens, "spec_slots": slots,
             "dtype": q_dtype, "out_dtype": out_dtype, "state_dtype": state_dtype,
             "beta_elems": beta_elems, "beta_dtype": beta_dtype,
             "gate_elems": gate_elems, "gate_dtype": gate_dtype}, {})


def recover_params(row: Mapping[str, Any], operator: str,
                   inputs: Sequence[Slot], outputs: Sequence[Slot]
                   ) -> tuple[dict[str, Any], dict[str, Any]]:
    compact = require_slot(inputs, 0, "compact record")
    states = []
    for label, candidates, index in (("initial_state", inputs, 1),
                                      ("final_state", outputs, 0)):
        slot = _find_state(candidates, (label,), index, fallback=False)
        if not _present(slot):
            continue
        if not slot.valid or slot.rank != 4:
            raise AbiError("recover_state_rank", f"{label}: {slot.shape}")
        require_float_dtype(slot, label)
        states.append(slot)
    if len(states) == 2 and (states[0].shape != states[1].shape
                            or states[0].dtype != states[1].dtype):
        raise AbiError("recover_state_mismatch", "initial/final state disagree")
    state = states[0] if states else None
    if state is not None:
        batch, heads, head_dim, head_dim_v = state.shape
        state_dtype = require_dtype(state, "state")
    else:
        if compact.rank < 2:
            raise AbiError("recover_rank", f"{compact.shape}")
        batch = compact.shape[0]
        heads = compact.shape[-2] if compact.rank >= 3 else 1
        head_dim = compact.shape[-1]
        head_dim_v = head_dim
        state_dtype = "fp32"
    slots = compact.shape[1] if compact.rank == 4 else 1
    params = {
        "tokens": int(batch), "heads": int(heads),
        "head_dim": int(head_dim), "head_dim_v": int(head_dim_v),
        "spec_slots": max(1, int(slots)), "phase": operator.rsplit("_", 1)[-1],
        "dtype": require_dtype(compact, "compact record"),
        "state_dtype": state_dtype,
    }
    if operator.endswith("commit"):
        params["accepted_tokens"] = max(1, int(slots))
    return params, {}


def conv_params(row: Mapping[str, Any], inputs: Sequence[Slot],
                outputs: Sequence[Slot]) -> tuple[dict[str, Any], dict[str, Any]]:
    x = require_slot(inputs, 0, "x")
    if x.rank < 1:
        raise AbiError("conv_rank", f"{x.shape}")
    tokens = int(x.shape[0]) if x.rank > 1 else 1
    channels = int(x.shape[-1])
    width = _int_attr(row, ("width", "kernel_size"), 4) or 4
    mode = _int_attr(row, ("run_mode", "runMode"), None)
    if mode is None:
        mode = 1 if tokens <= 1 else 0
    params = {"tokens": max(1, tokens), "channels": channels, "width": width,
              "run_mode": mode, "dtype": require_dtype(x, "x")}
    batch = _int_attr(row, ("batch", "B", "num_sequences"), None)
    if batch is not None:
        params["batch"] = batch
    return params, {}


def slice_params(inputs: Sequence[Slot], outputs: Sequence[Slot]
                 ) -> tuple[dict[str, Any], dict[str, Any]]:
    """Pure data-copy/view slice: bytes only, zero activation Vector work."""
    x = require_slot(inputs, 0, "x")
    out = require_output(outputs, "slice output")
    if x.rank < 1 or x.rank != out.rank:
        raise AbiError("slice_rank", f"{x.shape} -> {out.shape}")
    if tuple(x.dims[:-1]) != tuple(out.dims[:-1]):
        raise AbiError("slice_prefix_mismatch", f"{x.shape} -> {out.shape}")
    if out.dims[-1] > x.dims[-1]:
        raise AbiError("slice_width", f"{x.shape} -> {out.shape}")
    dtype = require_dtype(x, "x")
    if require_dtype(out, "output") != dtype:
        raise AbiError("slice_dtype_mismatch",
                       f"{dtype} vs {out.dtype}")
    rows = math.prod(x.dims[:-1]) if x.rank > 1 else 1
    return ({"rows": max(1, rows), "in_hidden": x.dims[-1],
             "out_hidden": out.dims[-1], "dtype": dtype}, {})


def rope_params(inputs: Sequence[Slot]) -> tuple[dict[str, Any], dict[str, Any]]:
    x = require_slot(inputs, 0, "x")
    return ({"tokens": max(1, x.dims[0] if x.rank > 1 else 1),
             "heads": max(1, x.dims[-2] if x.rank > 1 else 1),
             "head_dim": x.dims[-1], "dtype": require_dtype(x, "x")}, {})


def quant_params(inputs: Sequence[Slot]) -> tuple[dict[str, Any], dict[str, Any]]:
    x = require_slot(inputs, 0, "x")
    rows = math.prod(x.dims[:-1])
    params = {"rows": max(1, rows), "hidden": x.dims[-1],
              "dtype": require_dtype(x, "x")}
    for slot in inputs[1:]:
        if slot.valid and "smooth" in slot.name.lower():
            params["has_smooth_scales"] = True
            params["smooth_scale_bytes"] = math.prod(slot.dims) * (
                4 if slot.dtype == "fp32" else 2)
            break
    return params, {}


def routing_params(row: Mapping[str, Any], inputs: Sequence[Slot],
                   outputs: Sequence[Slot]) -> tuple[dict[str, Any], dict[str, Any]]:
    logits = require_slot(inputs, 0, "logits")
    if logits.rank < 2:
        raise AbiError("routing_rank", f"{logits.shape}")
    topk = (_int_attr(row, ("topk", "k"), None)
            or (outputs[0].dims[-1] if outputs and outputs[0].valid else 8))
    params = {"tokens": logits.dims[0] if logits.rank > 2 else logits.dims[0],
              "experts": logits.dims[-1], "hidden": logits.dims[-1],
              "topk": max(1, int(topk)), "dtype": require_dtype(logits, "logits")}
    return params, {}


def indexer_params(row: Mapping[str, Any], inputs: Sequence[Slot],
                   outputs: Sequence[Slot], sparse: bool
                   ) -> tuple[dict[str, Any], dict[str, Any]]:
    q = require_slot(inputs, 0, "q")
    key = require_slot(inputs, 1, "key")
    if q.rank < 2 or key.rank < 2:
        raise AbiError("indexer_rank", f"{q.shape} / {key.shape}")
    tokens = int(q.dims[0])
    heads = int(q.dims[-2]) if q.rank >= 2 else 1
    dim = int(q.dims[-1])
    kv_len = int(key.dims[0])
    topk = _int_attr(row, ("topk",), None)
    topk = 2048 if topk is None else topk
    if topk <= 0:
        raise AbiError("invalid_topk", f"topk={topk}")
    dtype = require_dtype(q, "q")
    q_raw = _attr_values(row, inputs, ("actual_seq_lengths_query",
                                       "actual_seq_lengths_q", "actual_seq_lens_q",
                                       "actual_seq_lengths", "actual_seq_lens"))
    kv_raw = _attr_values(row, inputs, ("actual_seq_lengths_kv",
                                        "actual_seq_lens_kv", "actual_seq_lengths_key"))
    encoding = _encoding(row, "TND")
    q_lens, kv_lens, batch = _paired_lengths(
        row, q_raw, kv_raw, encoding=encoding, total_q=tokens, total_kv=None)
    if q_lens is not None and sum(q_lens) != tokens:
        raise AbiError("indexer_length_arity",
                       f"sum(q_lens)={sum(q_lens)} != tokens={tokens}")
    if kv_lens is None and q_lens is not None:
        kv_lens = tuple([kv_len] * len(q_lens))
    params = {"tokens": max(1, tokens), "heads": max(1, heads),
              "head_dim": dim, "kv_len": max(1, kv_len),
              "topk": topk, "dtype": dtype,
              "causal": _causal(row)}
    if batch is not None:
        params["batch"] = batch
    offset = _int_attr(row, ("causal_offset", "pos_offset"), None)
    if offset is not None:
        if offset < 0:
            raise AbiError("invalid_causal_offset", f"{offset}")
        params["causal_offset"] = offset
    if q_lens is not None:
        params["actual_seq_lens_q"] = list(q_lens)
    if kv_lens is not None:
        params["actual_seq_lens_kv"] = list(kv_lens)
    if not sparse:
        params["index_heads"] = params.pop("heads")
        params["index_dim"] = params.pop("head_dim")
        params.pop("head_dim", None)
    return params, {}


def collective_params(row: Mapping[str, Any], name: str,
                      inputs: Sequence[Slot],
                      outputs: Sequence[Slot] = ()
                      ) -> tuple[dict[str, Any], dict[str, Any]]:
    lowered = name.lower().replace("_", "")
    if "allgather" in lowered:
        operator = "hccl_all_gather"
    elif "reducescatter" in lowered:
        operator = "hccl_reduce_scatter"
    elif "alltoall" in lowered:
        operator = "hccl_all_to_all"
    elif "broadcast" in lowered:
        operator = "hccl_broadcast"
    else:
        operator = "hccl_all_reduce"
    dtype = "bf16"
    size = None
    elems = None
    if inputs:
        slot = require_slot(inputs, 0, "collective input")
        dtype = require_dtype(slot, "collective tensor")
        elems = math.prod(slot.dims)
        size = elems * dtype_bytes(dtype)
    elif row.get("size_bytes") not in (None, ""):
        size = _int_attr(row, ("size_bytes",), None)
        dtype = str(row.get("dtype") or "bf16")
    if not size:
        raise AbiError("collective_size", name)
    world = _int_attr(row, ("world_size", "ws"), 8)
    if world is None:
        world = 8
    if world <= 0:
        raise AbiError("invalid_world_size", str(world))
    out = require_output(outputs, "collective output") if inputs else None
    if not inputs and outputs:
        raise AbiError("collective_size_only", "size-only interface has no descriptors")
    if out is not None and require_dtype(out, "collective output") != dtype:
        raise AbiError("collective_dtype_mismatch", f"{dtype} vs {out.dtype}")
    send_raw = row.get("send_counts")
    recv_raw = row.get("recv_counts")
    split = operator == "hccl_all_to_all" and (
        send_raw not in (None, "") or recv_raw not in (None, ""))
    if split:
        if send_raw in (None, "") or recv_raw in (None, ""):
            raise AbiError("all_to_all_v_counts",
                           "send_counts and recv_counts must be supplied together")
        send = _capture_ints(send_raw, "send_counts")
        recv = _capture_ints(recv_raw, "recv_counts")
        if len(send) != world or len(recv) != world:
            raise AbiError("all_to_all_v_counts",
                           f"split lengths {len(send)}/{len(recv)} != {world}")
        if elems is None or out is None:
            raise AbiError("all_to_all_v_counts",
                           "local input/output tensors are required")
        out_elems = math.prod(out.dims) if out.dims else 1
        if sum(send) != elems:
            raise AbiError("all_to_all_v_input",
                           f"sum(send_counts)={sum(send)} != {elems}")
        if sum(recv) != out_elems:
            raise AbiError("all_to_all_v_output",
                           f"sum(recv_counts)={sum(recv)} != {out_elems}")
        rank = _int_attr(row, ("self_rank", "rank"), None)
        if rank is not None and rank < world and send[rank] != recv[rank]:
            raise AbiError("all_to_all_v_self",
                           f"rank {rank}: send {send[rank]} != recv {recv[rank]}")
        size = sum(send) * dtype_bytes(dtype)
    elif out is not None and elems is not None:
        out_dtype = dtype
        out_elems = math.prod(out.dims) if out.dims else 1
        if operator == "hccl_all_gather":
            if world > 1 and out_elems != elems * world:
                raise AbiError("all_gather_volume",
                               f"{out_elems} != {elems} * {world}")
            if world == 1 and out_elems != elems:
                raise AbiError("all_gather_volume",
                               f"{out_elems} != {elems}")
            size = out_elems * dtype_bytes(out_dtype)
        elif operator == "hccl_reduce_scatter":
            if world > 1 and elems != out_elems * world:
                raise AbiError("reduce_scatter_volume",
                               f"{out_elems} * {world} != {elems}")
            if world == 1 and out_elems != elems:
                raise AbiError("reduce_scatter_volume",
                               f"{out_elems} != {elems}")
        elif tuple(out.dims) != tuple(inputs[0].dims):
            raise AbiError("collective_output_shape",
                           f"{out.shape} != {inputs[0].shape}")
    params = {"size_bytes": int(size), "world_size": int(world),
              "algorithm": "ring", "dtype": dtype}
    if operator == "hccl_all_to_all" and split:
        params["send_counts"] = list(_capture_ints(send_raw, "send_counts"))
        params["recv_counts"] = list(_capture_ints(recv_raw, "recv_counts"))
        rank = _int_attr(row, ("self_rank", "rank"), None)
        if rank is not None:
            params["self_rank"] = rank
    return operator, params


def _mc2_routing(inputs: Sequence[Slot], tokens: int, topk: int | None,
                 dispatch: bool) -> tuple[int, bool]:
    """Captured comm/x/IDs/.../scales positions; compact controls omit metadata."""
    ids = require_slot(inputs, 2, "expertIds")
    if ids.rank != 2 or ids.dims[0] != tokens or ids.dims[1] < 1:
        raise AbiError("mc2_buffer_shape", f"expertIds {ids.shape}, T={tokens}")
    if require_dtype(ids, "expertIds") != "int32":
        raise AbiError("mc2_index_dtype", f"expertIds: {ids.dtype}")
    if topk is not None and topk != ids.dims[1]:
        raise AbiError("mc2_topk_shape", f"{topk} != {ids.dims[1]}")
    topk = ids.dims[1]
    # Three/four-slot controls imply FP32 weights. The retained five-slot
    # compact form puts weights at 4; full captures always put them at 5.
    index = 5 if len(inputs) >= 6 else 4
    if len(inputs) <= index:
        return topk, True
    if dispatch and inputs[index].omitted:
        return topk, False
    scales = require_slot(inputs, index, "expertScales")
    if scales.rank != 2 or scales.dims != (tokens, topk):
        raise AbiError("mc2_buffer_shape", f"expertScales {scales.shape}, T/K={tokens}/{topk}")
    # V3 docs and capture producers use FP32 route weights, INT32 IDs.
    if require_dtype(scales, "expertScales") != "fp32":
        raise AbiError("mc2_scale_dtype", f"expertScales: {scales.dtype}")
    return topk, True


def mc2_params(row: Mapping[str, Any], operator: str,
               inputs: Sequence[Slot], outputs: Sequence[Slot]
               ) -> tuple[dict[str, Any], dict[str, Any]]:
    aliases = {
        "routed_rows": ("routed_rows",),
        "local_rows": ("local_rows", "local_routed_rows", "local"),
        "remote_routed_rows": ("remote_routed_rows", "remote_rows", "remote"),
        "sent_rows": ("sent_rows", "sent_routed_rows", "sent"),
        "received_rows": ("received_rows", "received_routed_rows", "received"),
        "experts_total": ("experts_total", "E", "e", "experts", "num_experts"),
        "experts_local": ("experts_local", "E_local", "e_local"),
        "topk": ("topk", "K", "k"), "ep": ("ep", "ep_world_size", "world_size"),
        "tokens": ("tokens", "T", "t"), "hidden": ("hidden", "H", "h"),
    }
    declared = {}
    for key, names in aliases.items():
        minimum = 1 if key in {"experts_total", "topk", "ep", "tokens", "hidden"} else 0
        value = _strict_int_attr(row, names, minimum=minimum)
        if value is not None:
            declared[key] = value
    if len(inputs) < 2:
        raise AbiError("missing_tensor_slot", "MC2 activation")
    x = require_slot(inputs, 1, "activation")
    if x.rank < 2:
        raise AbiError("mc2_rank", f"activation {x.shape}")
    hidden, in_tokens = x.dims[-1], x.dims[-2]
    out = require_output(outputs, "MC2 output")
    if out.rank != 2 or x.rank != 2 or out.dims[-1] != hidden:
        raise AbiError("mc2_buffer_shape", f"{x.shape} -> {out.shape}")
    out_tokens = out.dims[-2]
    expanded = out_tokens if operator.endswith("dispatch") else in_tokens
    tokens = in_tokens if operator.endswith("dispatch") else out_tokens
    if tokens < 1 or hidden < 1 or expanded < 0:
        raise AbiError("mc2_buffer_shape", f"{x.shape} -> {out.shape}")
    in_dtype = require_dtype(x, "activation")
    out_dtype = require_dtype(out, "MC2 output")
    if in_dtype not in {"fp16", "bf16", "fp32"} or out_dtype not in {"fp16", "bf16", "fp32"}:
        raise AbiError("mc2_dtype", f"{in_dtype} -> {out_dtype}")
    if in_dtype != out_dtype:
        raise AbiError("mc2_dtype_mismatch", f"{in_dtype} -> {out_dtype}")
    for key, shaped in (("tokens", tokens), ("hidden", hidden)):
        if key in declared and declared[key] != shaped:
            raise AbiError("mc2_buffer_shape", f"{key}={declared[key]} != {shaped}")
    routed = declared.get("routed_rows")
    topk, has_scales = _mc2_routing(
        inputs, tokens, declared.get("topk"), operator.endswith("dispatch"))
    ep = declared.get("ep")
    e_total, e_local = declared.get("experts_total"), declared.get("experts_local")
    if ep is None and e_total is not None and e_local is not None and e_local > 0:
        if e_total % e_local == 0:
            ep = e_total // e_local
    if ep is None:
        # Legacy captures expose global capacity T*K*EP. A buffer filled by
        # nondefault arrivals cannot establish topology; a larger integral
        # capacity retains the captured global-capacity interpretation.
        nominal = tokens * topk
        if routed is not None and routed != tokens * topk and (
                expanded <= routed or expanded % nominal):
            raise AbiError("mc2_ep_ambiguous", "nondefault arrivals require EP or expert counts")
        ep = max(1, int(round(expanded / nominal)))
    if e_total is None:
        e_total = 64
        for slot in inputs:
            if slot.valid and slot.rank == 1 and 0 < slot.dims[0] <= 4096 \
                    and slot.dims[0] >= ep and slot.dims[0] % ep == 0:
                e_total = int(slot.dims[0])
                break
    if e_local is None:
        e_local = max(1, e_total // ep)
    try:
        effective_routed, _, _, _ = mc2_ownership(
            tokens, ep, e_total, e_local, topk, operator.rsplit("_", 1)[-1],
            routed, declared.get("remote_routed_rows"), declared.get("sent_rows"),
            declared.get("received_rows"), declared.get("local_rows"))
    except FormulaValidationError as exc:
        raise AbiError("mc2_ownership", str(exc)) from exc
    if effective_routed > expanded:
        raise AbiError("mc2_buffer_capacity", f"routed_rows={effective_routed} > {expanded}")
    return ({
        "tokens": tokens, "hidden": hidden,
        "experts_total": e_total, "experts_local": e_local,
        "topk": topk, "ep": ep, "dtype": in_dtype,
        "use_measured_fit": False, **declared,
        **({"has_scales": False} if not has_scales else {}),
    }, {})


def embedding_params(operator: str, inputs: Sequence[Slot], outputs: Sequence[Slot]
                     ) -> tuple[dict[str, Any], dict[str, Any]]:
    x = require_slot(inputs, 0, "x")
    if operator in {"embedding", "vocab_parallel_embedding"}:
        table = require_slot(inputs, 1, "weight")
        return ({"tokens": max(1, x.dims[0]), "hidden": table.dims[-1],
                 "vocab": table.dims[0], "dtype": require_dtype(x, "x")}, {})
    if operator in {"argmax", "top_p_sample"}:
        return ({"tokens": max(1, x.dims[-2] if x.rank >= 2 else 1),
                 "vocab": x.dims[-1], "logits_dtype": require_dtype(x, "logits")},
                {})
    return ({"tokens": max(1, x.dims[-2] if x.rank >= 2 else 1),
             "hidden": x.dims[-1], "vocab": 1, "dtype": require_dtype(x, "x")},
            {})


__all__ = [
    "attention_params", "chunk_params", "collective_params", "conv_params",
    "embedding_params", "grouped_params", "indexer_params", "matmul_params",
    "mc2_params", "quant_params", "recover_params", "recurrent_params",
    "require_dtype", "require_output", "require_slot", "rms_params",
    "rope_params", "routing_params", "slice_params", "swiglu_params",
]
