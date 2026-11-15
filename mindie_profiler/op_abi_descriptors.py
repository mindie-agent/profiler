"""Lossless native descriptor parsing for captured operator occurrences.

[Role]
  Split ``;``/``|``-delimited capture fields without deleting empty positions,
  parse shapes into an explicit state machine, align dtype/layout columns by
  original index and expose the native-tensor slot projection used for
  content-addressed identities.

[Invariants]
  * Empty middle fields are retained as ``absent`` positions.
  * ``absent``, ``undefined``, ``missing``, ``invalid``, ``scalar`` and
    ``tensor`` remain distinct; a negative dimension is never a scalar.
  * ``present=False`` and ``shape_present=False`` on mapping descriptors are
    honored; a hidden shape is never promoted to a tensor.
  * Parallel ``dtype``/``format`` columns are preserved.  A mapping/token count
    disagreement is a ``descriptor_column_mismatch`` issue, never a silent drop.
  * Explicit presence with missing metadata is never optional omission.
  * Captured strides, storage offset/bytes/id and presence flags survive into
    the binding and the allocator.
  * Mixed non-null tokens/mappings stay invalid; null mapping entries are absent.

[Timeouts & Locks]
  Pure in-memory parsing proportional to the number of slots.

[Side-Effect Policy]
  No I/O or mutation of the input row.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .native_tensor_abi import DTYPES
from .repro_values import (
    bounded_container_len,
    bounded_count,
    bounded_mapping,
    bounded_sequence,
    bounded_shape,
    bounded_summary,
    storage_mapping,
    storage_record,
    validate_container_depth,
    validate_json_integers,
)

_UNDEFINED = {"", "NULL", "NONE", "UNDEFINED", "DT_UNDEFINED", "N/A", "NA"}
_EXTRA_DTYPES = {
    "UINT64": "uint64", "DT_UINT64": "uint64",
    "UINT32": "uint32", "DT_UINT32": "uint32",
    "UINT8": "uint8", "DT_UINT8": "uint8",
    "UINT4": "uint4", "DT_UINT4": "uint4",
    "DT_FLOAT8_E5M2": "fp8_e5m2", "FLOAT8_E5M2": "fp8_e5m2",
    "DT_FLOAT8_E4M3": "fp8_e4m3", "DT_HIF8": "hif8",
    "DT_INT4": "int4", "INT4": "int4",
}
_STORAGE_KEYS = (
    "strides", "stride", "storage_offset", "storage_bytes",
    "storage_id", "storage_object_id", "offset",
)


def _text(value: Any) -> str:
    return "" if value is None else value.strip() if isinstance(value, str) else bounded_summary(value)


def _field(row: Any, key: str) -> Any:
    if isinstance(row, Mapping):
        bounded_container_len(row)
        return row.get(key)
    return getattr(row, key, None)


def _split_slots(value: Any) -> list[Any] | None:
    """Split a ``;``/``|`` delimited capture string keeping empty positions."""
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if ";" in text or "|" in text:
            return [part.strip() for part in re.split(r"[;|]", text)]
        return [text]
    if isinstance(value, Mapping):
        return [bounded_mapping(value)]
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return bounded_sequence(value, "descriptor column")
    return [value]


def parse_shape(token: Any) -> tuple[list[int] | None, str]:
    """Parse one shape token into a preserved shape plus an explicit state."""
    validate_json_integers(token)
    if isinstance(token, Mapping):
        if not token.get("shape_present", "shape" in token) or "shape" not in token:
            return None, "missing"
        token = token.get("shape")
    if token is None:
        return None, "missing"
    if isinstance(token, (list, tuple)):
        values = list(bounded_sequence(token, "shape", 32))
        if any(isinstance(item, bool) or not isinstance(item, int) for item in values):
            return None, "invalid"
        for item in values:
            bounded_count(item, "captured shape dimension", -(1 << 62), 1 << 62)
        values = [int(item) for item in values]
        if all(item >= 0 for item in values):
            bounded_shape(values, 1 << 62)
        return (values, "invalid") if any(item < 0 for item in values) else (values, "tensor")
    text = _text(token)
    if text.upper() in _UNDEFINED:
        return None, "missing"
    if text.strip("[]() ") == "":
        return [], "scalar"
    cleaned = text.strip("[](){} ").replace("x", ",")
    try:
        values = [int(part.strip()) for part in cleaned.split(",") if part.strip()]
    except ValueError:
        return None, "invalid"
    if any(item < 0 for item in values):
        return values, "invalid"
    bounded_shape(values, 1 << 62)
    return values, "tensor"


def _norm_dtype(value: Any) -> tuple[str | None, str, bool]:
    raw = _text(value)
    if raw.upper() in _UNDEFINED:
        return None, raw, False
    if raw in DTYPES:
        return DTYPES[raw], raw, True
    if raw.upper() in _EXTRA_DTYPES:
        return _EXTRA_DTYPES[raw.upper()], raw, True
    lowered = raw.lower().replace("-", "_")
    if lowered in DTYPES:
        return DTYPES[lowered], raw, True
    if lowered.upper() in _EXTRA_DTYPES:
        return _EXTRA_DTYPES[lowered.upper()], raw, True
    return None, raw, False


def _storage_of(source: Mapping[str, Any]) -> dict[str, Any]:
    return storage_record(source)


def _raw_slot(
    index: int,
    shape_token: Any,
    dtype_token: Any,
    layout_token: Any,
    *,
    shape_present: bool = True,
    dtype_present: bool = True,
    layout_present: bool = True,
    values: Any = None,
    present: bool = True,
    storage: Mapping[str, Any] | None = None,
    source: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    storage = dict(storage_mapping(storage))
    validate_json_integers((shape_token, dtype_token, layout_token, storage))
    shape, shape_state = parse_shape(shape_token) if shape_present else (None, "missing")
    dtype, dtype_raw, dtype_known = _norm_dtype(dtype_token) if dtype_present else (None, "", False)
    layout_raw = _text(layout_token) if layout_present else ""
    layout = None if layout_raw.upper() in _UNDEFINED else layout_raw
    source_map = bounded_mapping(source) if source is not None else None
    declared = source_map is not None and (
        bool(source_map.get("present") or source_map.get("declared_present"))
        or ("shape_present" in source_map and not source_map["shape_present"])
        or ("shape" not in source_map and bool(source_map or layout))
        or bool(storage)
        or values is not None
    )
    absent = (not present) or (
        not declared
        and (
            (not shape_present and not dtype_present and not layout_present)
            or (
                shape_present
                and not _text(shape_token)
                and not _text(dtype_token)
                and not _text(layout_token)
            )
        )
    )
    if absent:
        state = "absent"
    elif shape_state == "invalid" or (shape is None and shape_present and _text(shape_token)):
        state = "invalid"
    elif shape is None:
        state = "missing"
    elif not dtype_present or not layout_present or dtype is None:
        state = "undefined" if shape == [] and dtype is None and layout is None else "missing"
    elif shape == []:
        state = "scalar"
    else:
        state = "tensor"
    if source_map:
        source_map.update({key: storage[key] for key in _STORAGE_KEYS if key in source_map and key in storage})
        if "storage" in source_map:
            source_map["storage"] = storage_mapping(source_map["storage"])
    record = {
        "position": index,
        "state": state,
        "present": present and state not in {"absent", "undefined"},
        "shape": list(shape) if shape is not None else None,
        "shape_present": bool(present and shape_present and _text(shape_token)),
        "dtype": dtype,
        "dtype_raw": dtype_raw,
        "dtype_known": dtype_known,
        "dtype_present": dtype_present and bool(_text(dtype_token)),
        "layout": layout,
        "layout_raw": layout_raw,
        "layout_present": layout_present and bool(_text(layout_token)),
        "values": values,
        "usable": state in {"scalar", "tensor"},
        "storage": storage,
        "declared_present": bool(present),
        "omitted": not present
        or (not declared and _text(shape_token).upper() in _UNDEFINED and dtype_raw.upper() in _UNDEFINED),
        "descriptor_source": source_map,
    }
    for key, value in storage.items():
        record[key] = value
    return record


def _mapping_columns(
    row: Any, direction: str, count: int
) -> tuple[list[Any], list[Any], list[dict[str, Any]]]:
    """Return parallel dtype/format columns, reporting count disagreements."""
    dtype_tokens = _split_slots(_field(row, f"{direction}_dtypes")) or []
    layout_tokens = _split_slots(_field(row, f"{direction}_formats")) or []
    issues: list[dict[str, Any]] = []
    for name, tokens in (("dtype", dtype_tokens), ("format", layout_tokens)):
        if tokens and len(tokens) != count:
            issues.append(
                {
                    "code": "descriptor_column_mismatch",
                    "direction": direction,
                    "column": name,
                    "shapes": count,
                    "values": len(tokens),
                }
            )
    return dtype_tokens, layout_tokens, issues


def slot_descriptors(row: Any, direction: str) -> dict[str, Any]:
    """Return ``{"present": bool, "slots": [...], "issues": [...]}`` losslessly."""
    validate_container_depth(row)
    raw_shapes = _field(row, f"{direction}_shapes")
    dtype_tokens = _split_slots(_field(row, f"{direction}_dtypes")) or []
    layout_tokens = _split_slots(_field(row, f"{direction}_formats")) or []
    if raw_shapes is None and not dtype_tokens and not layout_tokens:
        return {
            "present": False,
            "slots": [],
            "issues": [{"code": "missing_descriptor_field", "field": f"{direction}_shapes"}],
        }
    shape_tokens = _split_slots(raw_shapes) or []
    mapping_mode = any(isinstance(item, Mapping) for item in shape_tokens)
    if mapping_mode:
        dtype_columns, layout_columns, issues = _mapping_columns(row, direction, len(shape_tokens))
        if not all(isinstance(item, Mapping) or item is None for item in shape_tokens):
            issues = [
                {"code": "descriptor_not_a_mapping", "detail": "mixed mapping/token shape sequence"},
                *issues,
            ]
        slots = []
        count = max(len(shape_tokens), len(dtype_columns), len(layout_columns))
        for index in range(count):
            item = shape_tokens[index] if index < len(shape_tokens) else {}
            invalid_token = item is not None and not isinstance(item, Mapping)
            raw_item = item
            if item is None:
                item = {"present": False}
            elif invalid_token:
                item = {}
            dtype_token = item.get("dtype")
            if dtype_token is None and index < len(dtype_columns):
                dtype_token = dtype_columns[index]
            layout_token = item.get("layout", item.get("format"))
            if layout_token is None and index < len(layout_columns):
                layout_token = layout_columns[index]
            slots.append(
                _raw_slot(
                    index,
                    item.get("shape"),
                    dtype_token,
                    layout_token,
                    shape_present=bool(item.get("shape_present", "shape" in item)),
                    dtype_present="dtype" in item or index < len(dtype_columns),
                    layout_present=("layout" in item or "format" in item or index < len(layout_columns)),
                    values=item.get("values"),
                    present=bool(item.get("present", True)),
                    storage=_storage_of(item),
                    source=item,
                )
            )
            if invalid_token:
                slots[-1].update(
                    state="invalid",
                    present=True,
                    usable=False,
                    omitted=False,
                    raw=bounded_summary(raw_item),
                )
            if index < len(dtype_columns):
                slots[-1]["dtype_column"] = dtype_columns[index]
            if index < len(layout_columns):
                slots[-1]["layout_column"] = layout_columns[index]
        return {"present": True, "slots": slots, "issues": issues}
    count = max(len(shape_tokens), len(dtype_tokens), len(layout_tokens))
    slots = []
    for index in range(count):
        shape_token = shape_tokens[index] if index < len(shape_tokens) else None
        dtype_token = dtype_tokens[index] if index < len(dtype_tokens) else None
        layout_token = layout_tokens[index] if index < len(layout_tokens) else None
        shape_present = index < len(shape_tokens)
        storage = _storage_of(shape_token) if isinstance(shape_token, Mapping) else {}
        slots.append(
            _raw_slot(
                index,
                shape_token,
                dtype_token,
                layout_token,
                shape_present=shape_present,
                dtype_present=index < len(dtype_tokens),
                layout_present=index < len(layout_tokens),
                values=shape_token.get("values") if isinstance(shape_token, Mapping) else None,
                present=True,
                storage=storage,
                source=shape_token if isinstance(shape_token, Mapping) else None,
            )
        )
    _, _, issues = _mapping_columns(row, direction, len(shape_tokens))
    return {"present": True, "slots": slots, "issues": issues}


def _native_slots(slots: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    native: list[dict[str, Any]] = []
    for slot in slots:
        if slot.get("state") == "tensor_list" and slot.get("items"):
            native.extend(_native_slots(slot["items"]))
            continue
        if slot["state"] in {"absent", "omitted", "null"}:
            native.append({"present": False})
        elif slot["state"] == "invalid" and slot.get("shape") is None:
            native.append({"shape": None, "dtype": slot.get("dtype_raw"), "layout": slot.get("layout_raw")})
        else:
            entry: dict[str, Any] = {
                "dtype": slot.get("dtype_raw"),
                "layout": slot.get("layout_raw"),
                "dtype_present": bool(slot.get("dtype_present")),
                "layout_present": bool(slot.get("layout_present")),
            }
            if slot.get("shape_present"):
                entry["shape"] = list(slot.get("shape") or [])
            native.append(entry)
    return native


__all__ = ["_native_slots", "parse_shape", "slot_descriptors"]
