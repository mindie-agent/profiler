"""Shared low-level slot, attribute and padding helpers for the ABI bridge.

[Role]
  Hold the generic positional-slot accessors, capture-attribute decoders,
  sequence-length decoder adapter and real catalog padding charge used by both
  the attention/GEMM geometry module and the state/collective geometry module.

[Invariants]
  * A missing, empty or malformed mandatory slot raises a stable ``AbiError``.
  * Attribute decoders reject bools-as-integers and unknown encodings.
  * Sequence lengths are decoded by the shared
    ``mindie_sim.op_formulas.primitives.decode_sequence_lengths`` contract.
  * Padding always calls the real ``compute_padding``/``operator_charge``
    contract on the captured slots; no synthetic tensor shape is invented.

[Timeouts & Locks]
  Pure in-memory arithmetic proportional to declared slots; no I/O.

[Side-Effect Policy]
  No mutation of the input row or slots; returns fresh mappings/tuples.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from mindie_profiler.op_abi_padding import compute_padding, operator_charge
from mindie_profiler.op_abi_slots import AbiError, Slot

from mindie_sim.op_formulas.hardware import dtype_bytes
from mindie_sim.op_formulas.primitives import decode_sequence_lengths, strict_int

_ENCODING_KEYS = ("actual_seq_lengths_type", "offset_encoding", "seq_encoding")


def require_slot(slots: Sequence[Slot], index: int, what: str) -> Slot:
    """Return one valid mandatory positional slot or fail closed."""
    if index >= len(slots):
        raise AbiError("missing_tensor_slot", f"{what} at position {index}")
    slot = slots[index]
    if not slot.valid or slot.shape is None:
        raise AbiError("invalid_tensor_slot",
                       f"{what} at position {index}: state={slot.state}")
    return slot


def require_dtype(slot: Slot, what: str) -> str:
    if not slot.dtype:
        raise AbiError("unknown_dtype", f"{what} has no declared dtype")
    dtype_bytes(slot.dtype)
    return slot.dtype


def _present(slot: Slot | None) -> bool:
    """True when a descriptor slot is supplied (not omitted/null)."""
    return slot is not None and slot.state not in {
        "omitted", "absent", "undefined", "null"}


_FLOATING_DTYPES = frozenset({"bf16", "fp16", "fp32", "hf32", "tf32"})


def require_float_dtype(slot: Slot, what: str) -> str:
    """A real-valued operand; integer storage is not a floating tensor."""
    dtype = require_dtype(slot, what)
    if dtype not in _FLOATING_DTYPES:
        raise AbiError("non_floating_dtype", f"{what}: {dtype}")
    return dtype


def require_output(outputs: Sequence[Slot], what: str = "output") -> Slot:
    if not outputs:
        raise AbiError("missing_tensor_slot", what)
    return require_slot(outputs, 0, what)


def _capture_ints(values: Any, label: str) -> tuple[int, ...]:
    """Decode comma/space-separated capture integers or a strict JSON list."""
    if isinstance(values, str):
        parts = [part for part in re.split(r"[,;\s]+", values.strip()) if part]
        if not parts:
            raise AbiError(f"{label}_not_numeric", repr(values))
        out = []
        for part in parts:
            if not re.fullmatch(r"-?\d+", part):
                raise AbiError(f"{label}_invalid_element", repr(part))
            out.append(int(part))
        return tuple(out)
    return tuple(strict_int(item, label) for item in values)


def _bool_attr(row: Mapping[str, Any], keys: Sequence[str]) -> bool:
    for key in keys:
        value = row.get(key)
        if value in (None, ""):
            continue
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"1", "true", "yes"}:
            return True
        if text in {"0", "false", "no"}:
            return False
        raise AbiError("invalid_boolean_attribute", f"{key}={value!r}")
    return False


def _int_attr(row: Mapping[str, Any], keys: Sequence[str],
              default: int | None = None) -> int | None:
    for key in keys:
        value = row.get(key)
        if value in (None, ""):
            continue
        if isinstance(value, bool):
            raise AbiError("invalid_integer_attribute", f"{key}={value!r}")
        try:
            return int(str(value).strip())
        except (TypeError, ValueError) as exc:
            raise AbiError("invalid_integer_attribute", f"{key}={value!r}") from exc
    return default


def _strict_int_attr(row: Mapping[str, Any], keys: Sequence[str], *,
                     minimum: int = 0) -> int | None:
    """Read every supplied alias, preserving zero and rejecting contradictions."""
    result = None
    sources = [row] + [row[key] for key in ("attrs", "attributes")
                       if isinstance(row.get(key), Mapping)]
    for source in sources:
        for key in keys:
            value = source.get(key)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise AbiError("invalid_integer_attribute", f"{key}={value!r}")
            if result is not None and result != value:
                raise AbiError("conflicting_integer_attribute", f"{keys}: {result}/{value}")
            result = value
    return result


def _paired_lengths(row: Mapping[str, Any], q_raw: Any, kv_raw: Any, *,
                    encoding: str, total_q: int, total_kv: int | None,
                    expected: int | None = None
                    ) -> tuple[tuple[int, ...] | None, tuple[int, ...] | None, int | None]:
    """Reconcile owners before deciding whether either leading zero is a sentinel.

    Two equally ambiguous zero-prefixed vectors retain the legacy sentinel
    convention; an explicit batch or an unambiguous partner determines owners.
    """
    batch = _strict_int_attr(row, ("batch", "B", "b", "num_sequences"), minimum=1)
    if batch is not None and expected is not None and batch != expected:
        raise AbiError("sequence_batch_mismatch", f"{batch} != {expected}")
    batch = expected if batch is None else batch
    if batch is None and q_raw is not None and kv_raw is not None:
        candidates = []
        for raw in (q_raw, kv_raw):
            try:
                values = _capture_ints(raw, "sequence")
            except (TypeError, ValueError) as exc:
                raise AbiError("invalid_sequence_lengths", "sequence vector") from exc
            counts = {len(values)}
            if encoding == "cumsum" and len(values) > 1 and values[0] == 0:
                counts.add(len(values) - 1)
            candidates.append(counts)
        common = (candidates[0] & candidates[1]) - {0}
        if not common:
            raise AbiError("qkv_length_arity", "no shared Q/KV owner count")
        batch = min(common)
    q_lens = _lengths(q_raw, encoding=encoding, total=total_q,
                       expected=batch, label="sequence_q")
    if batch is None and q_lens is not None:
        batch = len(q_lens)
    kv_lens = _lengths(kv_raw, encoding=encoding, total=total_kv,
                        expected=batch, label="sequence_kv")
    return q_lens, kv_lens, batch


def _encoding(row: Mapping[str, Any], layout: str) -> str:
    for key in _ENCODING_KEYS:
        value = row.get(key)
        if value in (None, ""):
            continue
        text = str(value).strip().lower()
        if text in {"cumsum", "cumulative", "prefix", "0"}:
            return "cumsum"
        if text in {"lengths", "length", "per_sequence", "per_seq", "1"}:
            return "lengths"
        raise AbiError("unknown_sequence_encoding", repr(value))
    return "cumsum" if layout == "TND" else "lengths"


def _attr_values(row: Mapping[str, Any], slots: Sequence[Slot],
                 keys: Sequence[str]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    for slot in slots:
        if slot.valid and slot.values is not None:
            low = slot.name.lower()
            if any(key in low for key in keys):
                return slot.values
    return None


def _padding_vector(lengths: Sequence[int], layout: str) -> list[int]:
    if layout != "TND":
        return list(lengths)
    running, out = 0, []
    for value in lengths:
        running += int(value)
        out.append(running)
    return out


def _lengths(values: Any, *, encoding: str, total: int | None,
             expected: int | None, label: str) -> tuple[int, ...] | None:
    if values is None:
        return None
    try:
        raw = list(_capture_ints(values, label))
        lengths = decode_sequence_lengths(raw, encoding=encoding,
                                          total_tokens=total,
                                          expected_count=expected, label=label)
    except AbiError:
        raise
    except TimeoutError:
        raise
    except Exception as exc:  # noqa: BLE001 - convert to a stable ABI code
        raise AbiError("invalid_sequence_lengths",
                       f"{label}: {type(exc).__name__}") from exc
    return lengths


def _padding_view(entry: Mapping[str, Any], inputs: Sequence[Slot],
                  attrs: Mapping[str, Any]
                  ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Present a layout-equivalent batched view to the padding contract.

    The catalog may declare only ``BSND``/``BSH`` padding semantics while the
    ABI also accepts the axis-permuted ``BNSD``/``SBH`` layouts.  Those layouts
    own exactly the same batch and sequence extents, so transpose the captured
    shape into the declared axis order instead of rejecting a legal layout or
    guessing a different bucket.
    """
    spec = entry.get("padding_semantics") or {}
    layouts = spec.get("layouts") or {}
    layout = str(attrs.get("layout") or "").strip().upper()
    mapping = {"BNSD": "BSND", "SBH": "BSH", "NSD": "BSND"}
    target = mapping.get(layout)
    use_view = bool(target and target in layouts and layout not in layouts)
    records = []
    for slot in inputs:
        shape = list(slot.shape) if slot.shape is not None else None
        if use_view and shape is not None:
            if layout == "BNSD" and len(shape) == 4:
                shape = [shape[0], shape[2], shape[1], shape[3]]
            elif layout == "SBH" and len(shape) == 3:
                shape = [shape[1], shape[0], shape[2]]
        records.append({"name": slot.name, "present": bool(slot.valid),
                        "shape": shape, "values": slot.values})
    view_attrs = dict(attrs)
    if use_view:
        view_attrs["layout"] = target
    return records, view_attrs


def _charge(entry: Mapping[str, Any], inputs: Sequence[Slot],
            attrs: Mapping[str, Any]) -> dict[str, Any]:
    """Apply the real catalog padding contract to real captured slots."""
    records, view_attrs = _padding_view(entry, inputs, attrs)
    resolved = compute_padding(entry, records, view_attrs, device="generic")
    if not resolved.get("valid"):
        codes = ",".join(item.get("code", "invalid")
                         for item in resolved.get("violations", []))
        raise AbiError("invalid_padding_contract", codes)
    charged = operator_charge(entry, bucket=int(resolved["bucket_tokens"]),
                              logical=int(resolved["logical_tokens"]),
                              attrs=view_attrs)
    return {**resolved, **charged}




__all__ = [
    "_attr_values", "_bool_attr", "_capture_ints", "_charge", "_encoding",
    "_int_attr", "_lengths", "_padding_vector", "_present", "require_dtype",
    "_paired_lengths", "_strict_int_attr", "require_float_dtype", "require_output", "require_slot",
]
