"""Strict native attention axis, layout, dtype and required-slot validation.

[Role]
  Decode native ``FusedInferAttentionScore``-family descriptors into the shared
  attention formula parameters.  Every Q/K/V/Out axis is validated before a
  card can be certified; the row-level ``input_layout`` attribute must agree
  with the declared tensor formats and all four operands must share a supported
  dtype.

[Invariants]
  * Q/K/V/Out are all mandatory; an absent, empty or malformed slot fails closed.
  * ``K.heads == V.heads``, ``Q.heads % K.heads == 0``, ``K.seq == V.seq`` and
    ``V.dim`` owns ``head_dim_v``.
  * Out batch/sequence/heads match Q and ``Out.dim == head_dim_v``.
  * Mixed Q/K/V/Out dtypes are rejected: the formula cannot represent them.
  * Unknown or contradictory layout attributes raise a stable ``AbiError``.

[Timeouts & Locks]
  Pure in-memory arithmetic proportional to declared slots; no I/O.

[Side-Effect Policy]
  No mutation of the input row or slots; returns fresh params/flags mappings.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from mindie_profiler.op_abi_geometry_common import (
    _attr_values, _bool_attr, _encoding, _int_attr, _paired_lengths, _padding_vector,
    require_dtype, require_output, require_slot,
)
from mindie_profiler.op_abi_slots import AbiError, Slot

_ATTN_LAYOUTS = {"BSND", "BNSD", "TND", "BSH", "SBH", "NSD", "ND"}

_Q_KEYS = ("actual_seq_lengths_q", "actual_seq_lens_q", "actual_seq_qlen",
           "actual_seq_lengths", "actual_seq_lens", "seq_lens_q", "seq_lens")
_KV_KEYS = ("actual_seq_lengths_kv", "actual_seq_lens_kv", "actual_seq_kvlen",
            "seq_lens_kv")


def _attn_shape(slot: Slot, head_num: int | None, what: str,
                layout_hint: str | None = None) -> dict[str, Any]:
    shape = slot.dims
    raw = str(slot.layout or "").strip().upper()
    if raw and raw not in _ATTN_LAYOUTS:
        raise AbiError("unknown_attention_layout", raw)
    hint = str(layout_hint or "").strip().upper()
    if hint in {"", "ND"}:
        hint = ""
    hint_rank_ok = (hint in {"BSND", "BNSD"} and len(shape) == 4) or (
        hint in {"TND", "BSH", "SBH", "NSD"} and len(shape) == 3)
    if hint and hint_rank_ok and raw not in {"", "ND"} and raw != hint:
        raise AbiError("contradictory_attention_layout",
                       f"{what}: tensor format={raw} but input_layout={hint}")
    if raw in {"", "ND"} and hint_rank_ok:
        # A physical ``ND`` descriptor is not an assertion about axis order:
        # the row's semantic layout owns the axes when the rank is compatible.
        layout = hint
    else:
        layout = raw if raw not in {"", "ND"} else (
            "BSND" if len(shape) == 4 else "TND" if len(shape) == 3 else "ND")
    if layout == "BSND" and len(shape) == 4:
        return {"batch": shape[0], "seq": shape[1], "heads": shape[2],
                "dim": shape[3], "layout": layout}
    if layout == "BNSD" and len(shape) == 4:
        return {"batch": shape[0], "seq": shape[2], "heads": shape[1],
                "dim": shape[3], "layout": layout}
    if layout == "TND" and len(shape) == 3:
        return {"batch": 1, "seq": shape[0], "heads": shape[1],
                "dim": shape[2], "layout": layout}
    if layout == "BSH" and len(shape) == 3:
        if head_num and shape[2] % head_num == 0:
            return {"batch": shape[0], "seq": shape[1], "heads": head_num,
                    "dim": shape[2] // head_num, "layout": layout}
        return {"batch": shape[0], "seq": shape[1], "heads": shape[2],
                "dim": None, "layout": layout}
    if layout == "SBH" and len(shape) == 3:
        if head_num and shape[2] % head_num == 0:
            return {"batch": shape[1], "seq": shape[0], "heads": head_num,
                    "dim": shape[2] // head_num, "layout": layout}
        return {"batch": shape[1], "seq": shape[0], "heads": shape[2],
                "dim": None, "layout": layout}
    if layout == "NSD" and len(shape) == 3:
        heads = head_num or 1
        if shape[2] % heads:
            raise AbiError("qk_head_dim_mismatch", f"{what} {shape}")
        return {"batch": shape[0], "seq": shape[1], "heads": heads,
                "dim": shape[2] // heads, "layout": layout}
    raise AbiError("unsupported_attention_layout",
                   f"{raw} rank {len(shape)} shape {shape}")


def _causal(row: Mapping[str, Any]) -> bool:
    if "causal" in row and row.get("causal") not in (None, ""):
        return _bool_attr(row, ("causal",))
    sparse = _int_attr(row, ("sparse_mode", "sparseMode"), None)
    if sparse in {2, 3, 4}:
        return True
    nxt = _int_attr(row, ("next_tokens", "next_tockens"), None)
    return nxt == 0


def _row_layout(row: Mapping[str, Any], tensor_layout: str) -> str:
    """Validate the row's declared ``input_layout`` against tensor formats."""
    declared = row.get("input_layout")
    if declared in (None, ""):
        return tensor_layout
    text = str(declared).strip().upper()
    if text == "ND":
        return tensor_layout
    if text not in _ATTN_LAYOUTS:
        raise AbiError("unknown_attention_layout", text)
    if text != tensor_layout:
        raise AbiError("contradictory_attention_layout",
                       f"input_layout={text} but tensor format={tensor_layout}")
    return tensor_layout


def _require_same_dtype(slots: Sequence[Slot], what: str) -> str:
    dtype = require_dtype(slots[0], what)
    for index, slot in enumerate(slots[1:], start=1):
        other = require_dtype(slot, f"{what}[{index}]")
        if other != dtype:
            raise AbiError("unsupported_mixed_dtype",
                           f"{what}: {dtype} vs slot {index} {other}")
    return dtype


def attention_params(row: Mapping[str, Any], operator: str,
                     inputs: Sequence[Slot], outputs: Sequence[Slot]
                     ) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate strict Q/K/V/Out ownership and derive attention parameters."""
    q = require_slot(inputs, 0, "query")
    k = require_slot(inputs, 1, "key")
    v = require_slot(inputs, 2, "value")
    head_num = _int_attr(row, ("head_num", "num_heads"), None)
    kv_heads = _int_attr(row, ("num_key_value_heads", "num_kv_heads", "hkv"),
                         None)
    semantic = row.get("input_layout")
    q_info = _attn_shape(q, head_num, "query", semantic)
    k_info = _attn_shape(k, kv_heads if kv_heads is not None else head_num,
                         "key", semantic)
    v_info = _attn_shape(v, kv_heads if kv_heads is not None else head_num,
                         "value", semantic)
    layout = q_info["layout"]
    layout = _row_layout(row, layout)
    if k_info["layout"] != layout or v_info["layout"] != layout:
        raise AbiError("mixed_attention_layout",
                       f"{layout}/{k_info['layout']}/{v_info['layout']}")
    if layout != "TND" and not (
            q_info["batch"] == k_info["batch"] == v_info["batch"]):
        raise AbiError("qkv_batch_mismatch",
                       f"Q {q_info['batch']} K {k_info['batch']} "
                       f"V {v_info['batch']}")
    if k_info["seq"] != v_info["seq"]:
        raise AbiError("kv_sequence_mismatch",
                       f"K {k_info['seq']} != V {v_info['seq']}")
    hq, hkv = q_info["heads"], k_info["heads"]
    if kv_heads is not None and hkv != kv_heads:
        raise AbiError("kv_head_mismatch",
                       f"declared {kv_heads} K heads vs shaped {hkv}")
    if head_num is not None and hq != head_num:
        raise AbiError("q_head_mismatch",
                       f"declared {head_num} Q heads vs shaped {hq}")
    if v_info["heads"] != hkv:
        raise AbiError("kv_head_mismatch",
                       f"K heads {hkv} != V heads {v_info['heads']}")
    if not (hq >= hkv >= 1) or hq % hkv:
        raise AbiError("head_ownership", f"hq={hq} hkv={hkv}")
    head_dim = q_info["dim"]
    if head_dim is None:
        raise AbiError("missing_head_dim", f"query shape {q.shape}")
    if k_info["dim"] is not None and k_info["dim"] != head_dim:
        raise AbiError("qk_head_dim_mismatch", f"{head_dim} != {k_info['dim']}")
    if v_info["dim"] is None:
        raise AbiError("missing_head_dim", f"value shape {v.shape}")
    head_dim_v = v_info["dim"]

    out = require_output(outputs, "attention output")
    out_info = _attn_shape(out, head_num, "output", layout)
    if out_info["layout"] != layout:
        raise AbiError("mixed_attention_layout", f"out {out_info['layout']}")
    if out_info["batch"] != q_info["batch"]:
        raise AbiError("qkv_batch_mismatch",
                       f"Out {out_info['batch']} != Q {q_info['batch']}")
    if out_info["seq"] != q_info["seq"]:
        raise AbiError("output_sequence_mismatch",
                       f"Out {out_info['seq']} != Q {q_info['seq']}")
    if out_info["heads"] != hq:
        raise AbiError("output_head_mismatch",
                       f"Out heads {out_info['heads']} != Q heads {hq}")
    if out_info["dim"] != head_dim_v:
        raise AbiError("output_head_dim_mismatch",
                       f"Out {out_info['dim']} vs V {head_dim_v}")
    dtype = _require_same_dtype((q, k, v, out), "attention_dtype")

    encoding = _encoding(row, layout)
    batch = q_info["batch"] if layout != "TND" else 1
    total_q = q_info["seq"] if layout == "TND" else batch * q_info["seq"]
    total_kv = k_info["seq"] if layout == "TND" else batch * k_info["seq"]
    q_raw = _attr_values(row, inputs, _Q_KEYS)
    kv_raw = _attr_values(row, inputs, _KV_KEYS)
    q_lens, kv_lens, owners = _paired_lengths(
        row, q_raw, kv_raw, encoding=encoding, total_q=total_q,
        total_kv=total_kv, expected=None if layout == "TND" else batch)
    if layout == "TND":
        batch = owners if owners is not None else 1
        if kv_lens is not None and len(kv_lens) != batch:
            raise AbiError("qkv_length_arity",
                           f"{len(q_lens or ())} Q lengths != {len(kv_lens)}")
        storage_q, storage_kv = q_info["seq"], k_info["seq"]
    else:
        storage_q, storage_kv = batch * q_info["seq"], batch * k_info["seq"]
    padding_skipped = bool(
        (q_lens is not None and sum(q_lens) < storage_q)
        or (kv_lens is not None and sum(kv_lens) < storage_kv))
    mask = None
    mask_dtype = "uint8"
    for slot in inputs:
        low = slot.name.lower()
        if slot.valid and ("mask" in low) and "padding" not in low:
            mask = slot
            break
    if mask is not None and mask.dtype in {"fp16", "bf16", "fp32"}:
        mask_dtype = mask.dtype
    params = {
        "q_len": q_info["seq"], "kv_len": k_info["seq"], "hq": hq,
        "hkv": hkv, "head_dim": head_dim, "head_dim_v": head_dim_v,
        "batch": max(1, batch),
        "phase": "decode" if (max(q_lens) if q_lens else q_info["seq"]) <= 4
        else "prefill",
        "layout": layout, "dtype": dtype,
        "paged": "paged" in operator,
        "storage_q": max(1, storage_q), "storage_kv": max(1, storage_kv),
        "padding_skipped": padding_skipped,
        "causal": _causal(row),
    }
    offset = _int_attr(row, ("causal_offset", "pos_offset"), None)
    if offset is not None:
        if offset < 0:
            raise AbiError("invalid_causal_offset", f"{offset}")
        params["causal_offset"] = offset
    if q_lens is not None:
        params["actual_seq_lens_q"] = list(q_lens)
    if kv_lens is not None:
        params["actual_seq_lens_kv"] = list(kv_lens)
    if mask is not None:
        params["attn_mask_shape"] = list(mask.dims)
        params["mask_dtype"] = mask_dtype
    padding_attrs: dict[str, Any] = {"layout": layout}
    if q_lens is not None:
        q_padding = _padding_vector(q_lens, layout)
        padding_attrs["actual_seq_q_len"] = q_padding
        padding_attrs["actual_seq_lengths"] = q_padding
        padding_attrs["actual_seq_lengths_q"] = q_padding
    if kv_lens is not None:
        kv_padding = _padding_vector(kv_lens, layout)
        padding_attrs["actual_seq_kv_len"] = kv_padding
        padding_attrs["actual_seq_lengths_kv"] = kv_padding
    if mask is not None:
        padding_attrs["atten_mask"] = True
    flags: dict[str, Any] = {}
    if q_info["seq"] > 8 and q_lens is None:
        flags["unfiltered_padding_shape_bound"] = True
    if "fused" in str(row.get("name", "")).lower():
        flags["async_overlap_shadowed"] = True
    return params, {"flags": flags, "padding_attrs": padding_attrs}


__all__ = ["attention_params"]
