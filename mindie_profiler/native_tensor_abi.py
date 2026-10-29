"""Strict projections of the tensor descriptors recorded by native profilers.

[Role] Preserve ordered shape, dtype and storage-format slots for native ABIs.
[Invariants] Explicit undefined slots and typed empty shapes remain distinct.
  Tensor descriptors do not identify scalar arguments, tensor values or a model
  occurrence. Missing fields never become a guessed shape or layout.
[Timeouts & Locks] Pure in-memory work proportional to the number of tensor slots.
[Side-Effect Policy] No I/O, hardware context or simulation imports.
"""
from __future__ import annotations


DTYPES = {
    "DT_BF16": "bf16", "DT_FLOAT16": "fp16", "FLOAT": "fp32", "INT8": "int8",
    "INT64": "int64", "INT32": "int32", "BOOL": "bool", "DT_UNDEFINED": None,
    "DT_FLOAT8_E4M3FN": "fp8_e4m3", "DT_FLOAT8_E8M0": "fp8_e8m0",
    "BF16": "bf16", "FP16": "fp16", "DT_FLOAT": "fp32",
    "bf16": "bf16", "fp16": "fp16", "fp32": "fp32",
    "int8": "int8", "int64": "int64", "int32": "int32", "bool": "bool",
    "FLOAT16": "fp16", "DT_INT8": "int8", "DT_INT32": "int32",
    "DT_INT64": "int64", "DT_UINT1": "uint1", "UNDEFINED": None,
}
_MISSING = {"", "N/A", "NULL", "UNDEFINED", "DT_UNDEFINED"}
_EMPTY_DTYPES = {"UNDEFINED", "DT_UNDEFINED"}
_EMPTY_FORMATS = {"NULL", "UNDEFINED"}


def native_contract_issue(row):
    """Return a concrete missing/unsupported descriptor reason, or None."""
    for direction in ("input", "output"):
        shapes = getattr(row, f"{direction}_shapes")
        if shapes is None or not shapes:
            return {
                "category": "capture_metadata_missing", "reason": "missing_tensor_metadata",
                "detail": "Native tensor ABI requires captured input and output descriptors.",
                "missing_fields": [f"{direction}_shapes"], "operator_type": row.kind,
            }
        dtypes = getattr(row, f"{direction}_dtypes")
        formats = getattr(row, f"{direction}_formats")
        if len(shapes) != len(dtypes) or len(shapes) != len(formats):
            return {
                "category": "capture_metadata_missing", "reason": "incomplete_native_tensor_slots",
                "detail": "Native shape, dtype and format arrays must describe the same ordered slots.",
                "direction": direction, "slot_counts": {
                    "shapes": len(shapes), "dtypes": len(dtypes), "formats": len(formats)},
                "operator_type": row.kind,
            }
        for index, (shape, dtype, layout) in enumerate(zip(shapes, dtypes, formats)):
            if any(not isinstance(value, int) or value < 0 for value in shape):
                return {
                    "category": "capture_metadata_missing", "reason": "unknown_tensor_dimensions",
                    "detail": "Negative or noninteger native dimensions cannot establish geometry.",
                    "direction": direction, "slot": index, "operator_type": row.kind,
                }
            if not shape and dtype in _EMPTY_DTYPES and layout in _EMPTY_FORMATS:
                continue
            missing = [field for field, value in (("dtype", dtype), ("format", layout))
                       if value in _MISSING]
            if missing:
                return {
                    "category": "capture_metadata_missing", "reason": "missing_tensor_metadata",
                    "detail": "Only explicitly undefined empty slots may omit dtype and format.",
                    "missing_fields": [f"{direction}[{index}].{field}" for field in missing],
                    "operator_type": row.kind,
                }
    return None


def native_tensor_contract(row, *, kind=None):
    """Return full native tensor slots; unknown nonempty dtype names stay literal."""
    if native_contract_issue(row) is not None:
        return None
    sides = []
    for direction in ("input", "output"):
        slots = []
        for shape, dtype, layout in zip(
            getattr(row, f"{direction}_shapes"), getattr(row, f"{direction}_dtypes"),
            getattr(row, f"{direction}_formats"),
        ):
            empty = not shape and dtype in _EMPTY_DTYPES and layout in _EMPTY_FORMATS
            slots.append((tuple(shape), None if empty else DTYPES.get(dtype, dtype),
                          None if empty else layout))
        sides.append(tuple(slots))
    return ("native_tensor_abi", kind or row.kind, *sides)


def native_tensor_diagnostic(row):
    return native_contract_issue(row) or {
        "category": "tensor_contract_available", "reason": "observed_tensor_contract_available",
        "detail": "All captured native tensor slots are preserved; scalar values and dispatch are not.",
        "operator_type": row.kind,
    }
