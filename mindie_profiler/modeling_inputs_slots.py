"""Per-operator ABI observation bundles and ideal hardware Roofline bounds (modeling_inputs_slots).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting per-operator abi observation bundles and ideal hardware roofline bounds.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from .native_tensor_abi import DTYPES as _NATIVE_DTYPES
from .native_tensor_abi import native_abi_from_slots

IDEAL_BOUND_FORMULA_VERSION = "roofline-max-v1"

SCHEMA_VERSION = "mindie-modeling-inputs/1"

OPERATOR_FAMILIES: dict[str, tuple[str, ...]] = {
    "matmul": ("matmul", "batchmatmul", "batch_matmul", "bmm", "gemm", "mm", "addmm",
               "linear", "fusedmatmul", "groupedmatmul", "quantmatmul",
               "quantgroupmatmul", "groupmatmul", "quantbatchmatmul",
               "matmulallreduce", "allgathermatmul", "matmulreducescatter"),
    "communication": ("hccl", "hcom", "allreduce", "allgather", "alltoall",
                      "reducescatter", "broadcast", "send", "recv", "barrier"),
    "rmsnorm": ("rmsnorm", "rms_norm", "rms norm", "layernorm", "layer_norm",
                "l2norm", "l2_norm", "normalization"),
    "elementwise": ("elementwise", "element_wise", "relu", "gelu", "silu", "swish",
                    "sigmoid", "tanh", "add", "sub", "mul", "div", "exp", "log", "sqrt",
                    "rsqrt", "abs", "neg", "cast", "clamp", "activation", "softmax",
                    "dropout", "where", "select"),
    "copy": ("copy", "memcpy", "clone", "contiguous", "transpose", "permute",
             "reshape", "view", "concat", "slice", "pad", "gather", "scatter", "datacopypad"),
    "reduction": ("reduce", "reduction", "sum", "mean", "max", "min", "argmax", "argmin", "norm"),
    "mla_attention": ("mqsmla", "pamlaattention", "sparseflashmla", "flashmla",
                      "mlaprolog", "mla"),
    "linear_attention": ("chunkgateddeltarule", "recurrentgateddeltarule",
                         "gateddeltarule", "chunkkda", "recurrentkda", "kda"),
    "mhc": ("hcpre", "hcpost", "hyperconnection"),
    "attn_res": ("attnresfwd", "attnres"),
}

_OPERATOR_PREFIXES = ("aclnn", "aclop", "aic", "aiv", "mix", "op")

_DTYPE_BYTES: dict[str, int | float] = {
    "fp4": 0.5, "fp4_e2m1": 0.5, "float4_e2m1": 0.5, "float4_e2m1fn": 0.5, "mxfp4": 0.5,
    "int4": 0.5, "uint4": 0.5,
    "fp8": 1, "fp8_e4m3": 1, "fp8_e4m3fn": 1, "float8_e4m3fn": 1,
    "fp8_e5m2": 1, "float8_e5m2": 1, "fp8_e8m0": 1, "float8_e8m0": 1, "e8m0": 1,
    "hif8": 1, "hifloat8": 1,
    "int8": 1, "uint8": 1, "bool": 1,
    "fp16": 2, "float16": 2, "bf16": 2, "bfloat16": 2, "int16": 2, "uint16": 2,
    "fp32": 4, "float": 4, "float32": 4, "int32": 4, "uint32": 4,
    "fp64": 8, "double": 8, "float64": 8, "int64": 8, "uint64": 8,
}

_DTYPE_ALIASES = {
    "fp16": "float16",
    "half": "float16",
    "bf16": "bfloat16",
    "fp32": "float32",
    "float": "float32",
    "fp64": "float64",
    "double": "float64",
    "i8": "int8",
    "u8": "uint8",
    "i16": "int16",
    "i32": "int32",
    "i64": "int64",
    "dt_bf16": "bfloat16",
    "dt_float16": "float16",
    "dt_float32": "float32",
    "dt_float": "float32",
    "dt_int8": "int8",
    "fp4_e2m1fn": "fp4_e2m1",
    "float4_e2m1fn": "float4_e2m1",
    "w4a4": "fp4_e2m1",
    "w4a4_mxfp4": "mxfp4",
    "dt_hifloat8": "hif8",
    "dt_float8_e4m3fn": "fp8_e4m3fn",
    "dt_float8_e5m2": "fp8_e5m2",
    "dt_float8_e8m0": "fp8_e8m0",
    "dt_float4_e2m1": "fp4_e2m1",
    "dt_int4": "int4",
    "dt_uint4": "uint4",
}

_NATIVE_DTYPE_ALIASES = {
    str(key).strip().lower(): value for key, value in _NATIVE_DTYPES.items() if value
}

_MISSING_TEXT = {"n/a", "na", "none", "-"}

_EXPLICIT_UNDEFINED_TEXT = {"dt_undefined", "undefined", "null"}

_UNDEFINED_TEXT = _MISSING_TEXT | _EXPLICIT_UNDEFINED_TEXT | {""}

_PLACEHOLDER_OPERATORS = {"<missing>", "unknown", "n/a", "na", "none", "null", "-"}

_LEGACY_DTYPE_NAMES = {
    "bf16": "bfloat16", "fp16": "float16", "fp32": "float32",
    "fp64": "float64", "fp8_e4m3": "fp8_e4m3", "fp8_e8m0": "fp8_e8m0",
}

def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))

def _normalise_dtype(dtype: str) -> str:
    key = dtype.strip().lower().replace("-", "_").replace(" ", "_")
    return _DTYPE_ALIASES.get(key) or _NATIVE_DTYPE_ALIASES.get(key) or key

def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    return text

def _is_undefined_text(value: Any) -> bool:
    return _clean_text(value).lower() in _UNDEFINED_TEXT

def _is_missing_text(value: Any) -> bool:
    return _clean_text(value).lower() in _MISSING_TEXT

def _is_explicit_undefined_text(value: Any) -> bool:
    return _clean_text(value).lower() in _EXPLICIT_UNDEFINED_TEXT

def _legacy_dtype_name(value: str | None) -> str | None:
    if value is None:
        return None
    return _LEGACY_DTYPE_NAMES.get(value, value)

def _clean_operator(value: Any) -> str | None:
    text = _clean_text(value)
    return None if text.lower() in _PLACEHOLDER_OPERATORS else text

def _normalise_slot_dtype(value: Any) -> str | None:
    """Return the canonical native dtype spelling owned by ``native_tensor_abi``.

    ``DT_BF16``/``bf16`` remain ``bf16`` so ``native_abi_from_slots`` sees the
    same token it would receive from a native row.  The long legacy roofline
    spelling is derived only in ``OperatorObservation.dtype``.  Unknown names
    stay literal; missing/``N/A`` and explicit undefined carry their own
    presence state in the caller.
    """
    text = _clean_text(value)
    if not text or _is_missing_text(text) or _is_explicit_undefined_text(text) or ";" in text:
        return None
    for key in (text, text.upper(), text.lower()):
        if key in _NATIVE_DTYPES:
            return _NATIVE_DTYPES[key]
    return text

def _normalise_slot_layout(value: Any) -> str | None:
    text = _clean_text(value)
    if not text or _is_missing_text(text) or _is_explicit_undefined_text(text) or ";" in text:
        return None
    return text

def _ms_to_ns(value: Any) -> int | None:
    if not _finite(value):
        return None
    return max(0, int(round(float(value) * 1_000_000.0)))

def _us_to_ns(value: Any) -> int | None:
    if not _finite(value):
        return None
    return max(0, int(round(float(value) * 1_000.0)))

def _canonical_annotations(value: Any) -> tuple[tuple[str, str], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return tuple(sorted((str(k), str(v)) for k, v in value.items()))
    return tuple(sorted((str(k), str(v)) for k, v in value))

def _normalise_operator_name(name: str) -> str:
    text = str(name or "").strip().lower()
    if "::" in text:
        text = text.rsplit("::", 1)[-1]
    text = "".join(char for char in text if char.isalnum())
    for prefix in _OPERATOR_PREFIXES:
        if text.startswith(prefix) and len(text) > len(prefix):
            text = text[len(prefix):]
            break
    return text

def classify_operator_family(operator_name: str) -> str:
    """Return the deterministic modeling family for an operator name."""
    normalised = _normalise_operator_name(operator_name)
    if not normalised:
        return "unknown"
    for family, tokens in OPERATOR_FAMILIES.items():
        for token in tokens:
            candidate = "".join(char for char in token.lower() if char.isalnum())
            if candidate and (normalised == candidate or candidate in normalised):
                return family
    return "unknown"

def _coerce_shape(value: Any) -> tuple[int, ...] | None:
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return (value,) if value >= 0 else None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except (TypeError, ValueError):
            parsed = None
        if parsed is not None and parsed != value:
            return _coerce_shape(parsed)
        text = text.replace("x", ",").replace("×", ",").replace(" ", ",")
        parts = [part for part in text.replace("[", "").replace("]", "").split(",") if part]
        if not parts:
            return None
        try:
            return tuple(int(part) for part in parts)
        except (TypeError, ValueError):
            return None
    if isinstance(value, (list, tuple)):
        try:
            dims = tuple(int(dim) for dim in value)
        except (TypeError, ValueError):
            return None
        return dims or None
    return None

def _positional_field(value: Any) -> bool:
    """Whether a dtype/layout field describes an ordered slot list.

    A bare ``"bf16"`` beside an explicit legacy ``shape`` is a scalar summary,
    not a positional slot array.  A semicolon string or a sequence is ordered.
    """
    if value is None:
        return False
    if isinstance(value, (list, tuple)):
        return True
    return isinstance(value, str) and ";" in value

def _split_slots(value: Any) -> tuple[Any, ...] | None:
    """Split one C7/native tensor field into positional slots.

    ``None`` means the whole field is explicitly unavailable; an empty string
    inside a semicolon list remains an explicit empty slot.  A flat integer
    sequence is one legacy shape, while a sequence of sequences/dicts/strings
    is an ordered slot list.
    """
    if value is None:
        return None
    if isinstance(value, str):
        text = _clean_text(value)
        if _is_undefined_text(text):
            return None
        if ";" in text:
            return tuple(_clean_text(part) for part in text.split(";"))
        return (text,)
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, (list, tuple)):
        if not value:
            return ()
        if all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value):
            return (tuple(value),)
        return tuple(value)
    return (value,)

_MISSING_SLOT = object()

def _slot_shape(value: Any) -> tuple[int, ...] | None:
    """Return a slot shape, preserving ``()`` as an explicit empty shape."""
    if value is None:
        return None
    if isinstance(value, str):
        text = _clean_text(value)
        if not text:
            return ()
        if text in {"[]", "()"}:
            return ()
        if _is_missing_text(text):
            return _MISSING_SLOT
        if _is_explicit_undefined_text(text):
            return None
        return _coerce_shape(text)
    if isinstance(value, (list, tuple)):
        if not value:
            return ()
        return _coerce_shape(value)
    return None

@dataclass(frozen=True)
class TensorSlot:
    """One ordered native tensor descriptor with original tokens and presence.

    ``shape=None`` means the position exists but its shape was not observed.
    ``shape=()`` is an explicit empty shape: it is a typed scalar only when
    dtype/layout are present and nonblank.  Blank/absent dtype/layout stay
    incomplete; only present ``DT_UNDEFINED``/``NULL``/null fields are explicit
    undefined.  ``native_tensor_abi`` owns canonical dtype normalization and
    slot qualification; this adapter only preserves the source facts.
    """

    shape: tuple[int, ...] | None = None
    dtype: str | None = None
    layout: str | None = None
    present: bool = True
    shape_present: bool = True
    dtype_present: bool = True
    layout_present: bool = True

    def __post_init__(self) -> None:
        shape = self.shape
        if isinstance(shape, list):
            shape = tuple(shape)
        if shape is not None:
            if not isinstance(shape, tuple) or any(
                not isinstance(dim, int) or isinstance(dim, bool) or dim < 0 for dim in shape
            ):
                raise ValueError("tensor slot shape must be non-negative integer dimensions")
        object.__setattr__(self, "shape", shape)
        object.__setattr__(self, "dtype", None if self.dtype is None else str(self.dtype))
        object.__setattr__(self, "layout", None if self.layout is None else str(self.layout))
        object.__setattr__(self, "present", bool(self.present))
        object.__setattr__(self, "shape_present", bool(self.shape_present))
        object.__setattr__(self, "dtype_present", bool(self.dtype_present))
        object.__setattr__(self, "layout_present", bool(self.layout_present))

    @property
    def state(self) -> str:
        if not self.present:
            return "absent"
        if self.shape is None:
            return "unknown"
        dtype_blank = not self.dtype_present or _clean_text(self.dtype) == ""
        layout_blank = not self.layout_present or _clean_text(self.layout) == ""
        dtype_undefined = self.dtype_present and (
            self.dtype is None or _is_explicit_undefined_text(self.dtype)
        )
        layout_undefined = self.layout_present and (
            self.layout is None or _is_explicit_undefined_text(self.layout)
        )
        if not self.shape:
            if dtype_undefined and layout_undefined:
                return "explicit_undefined"
            if not dtype_blank and not layout_blank and not dtype_undefined and not layout_undefined:
                return "scalar"
            return "incomplete"
        if not dtype_blank and not layout_blank and not dtype_undefined and not layout_undefined:
            return "descriptor"
        return "incomplete"

    @classmethod
    def from_mapping(cls, value: Any) -> "TensorSlot":
        if isinstance(value, TensorSlot):
            return value
        if not isinstance(value, Mapping):
            raise TypeError("tensor slot must be a mapping or TensorSlot")
        shape = value.get("shape")
        shape_present = (
            bool(value["shape_present"]) if "shape_present" in value else "shape" in value
        )
        if isinstance(shape, str):
            if _is_missing_text(shape):
                shape_present = False
            parsed = _slot_shape(shape)
            shape = None if parsed is _MISSING_SLOT else parsed
        elif isinstance(shape, list):
            shape = tuple(shape)
        if not shape_present:
            shape = None
        dtype = value.get("dtype")
        layout = value.get("layout", value.get("format"))
        dtype_present = (
            bool(value["dtype_present"]) if "dtype_present" in value else "dtype" in value
        )
        layout_present = (
            bool(value["layout_present"]) if "layout_present" in value
            else "layout" in value or "format" in value
        )
        if _is_missing_text(dtype):
            dtype_present = False
        if _is_missing_text(layout):
            layout_present = False
        if not dtype_present:
            dtype = None
        if not layout_present:
            layout = None
        present = bool(value["present"]) if "present" in value else True
        return cls(
            present=present,
            shape=shape,
            dtype=None if dtype is None else str(dtype),
            layout=None if layout is None else str(layout),
            shape_present=shape_present,
            dtype_present=dtype_present,
            layout_present=layout_present,
        )

    def abi_slot(self) -> dict[str, Any]:
        slot: dict[str, Any] = {
            "present": self.present,
            "dtype": self.dtype,
            "layout": self.layout,
            "dtype_present": self.dtype_present,
            "layout_present": self.layout_present,
        }
        if self.shape_present:
            slot["shape"] = None if self.shape is None else list(self.shape)
        return slot

    def as_dict(self) -> dict[str, Any]:
        return {
            "shape": list(self.shape) if self.shape is not None else None,
            "dtype": self.dtype,
            "layout": self.layout,
            "state": self.state,
            "present": self.present,
            "shape_present": self.shape_present,
            "dtype_present": self.dtype_present,
            "layout_present": self.layout_present,
        }

    to_dict = as_dict

def _slot_from_parts(
    shape_value: Any,
    dtype_value: Any,
    layout_value: Any,
    *,
    shape_present: bool = True,
    dtype_present: bool = True,
    layout_present: bool = True,
    present: bool = True,
) -> "TensorSlot":
    if shape_value is _MISSING_SLOT or _is_missing_text(shape_value):
        shape = None
        shape_present = False
    else:
        shape = _slot_shape(shape_value)
        if shape is _MISSING_SLOT:
            shape = None
            shape_present = False
    if dtype_value is _MISSING_SLOT or _is_missing_text(dtype_value):
        dtype = None
        dtype_present = False
    else:
        dtype = None if dtype_value is None else str(dtype_value)
    if layout_value is _MISSING_SLOT or _is_missing_text(layout_value):
        layout = None
        layout_present = False
    else:
        layout = None if layout_value is None else str(layout_value)
    dtype_undefined = dtype_present and (
        dtype is None or _is_explicit_undefined_text(dtype)
    )
    layout_undefined = layout_present and (
        layout is None or _is_explicit_undefined_text(layout)
    )
    if (
        shape is None
        and shape_present
        and dtype_undefined
        and layout_undefined
    ):
        # A positional null/DT_UNDEFINED/NULL slot is explicitly undefined.
        # An empty shape with absent/blank dtype/layout stays incomplete.
        shape = ()
    return TensorSlot(
        present=present,
        shape=shape,
        dtype=dtype,
        layout=layout,
        shape_present=shape_present,
        dtype_present=dtype_present,
        layout_present=layout_present,
    )

def _tensor_slots(shapes: Any, dtypes: Any, layouts: Any) -> tuple["TensorSlot", ...]:
    """Build ordered slots without padding or collapsing positional fields."""
    shape_parts = _split_slots(shapes)
    dtype_parts = _split_slots(dtypes)
    layout_parts = _split_slots(layouts)
    counts = [len(part) for part in (shape_parts, dtype_parts, layout_parts) if part is not None]
    count = max(counts) if counts else 0
    slots: list[TensorSlot] = []
    for index in range(count):
        shape_present = shape_parts is not None and index < len(shape_parts)
        dtype_present = dtype_parts is not None and index < len(dtype_parts)
        layout_present = layout_parts is not None and index < len(layout_parts)
        shape = shape_parts[index] if shape_present else _MISSING_SLOT
        dtype = dtype_parts[index] if dtype_present else _MISSING_SLOT
        layout = layout_parts[index] if layout_present else _MISSING_SLOT
        slots.append(_slot_from_parts(
            shape, dtype, layout,
            shape_present=shape_present,
            dtype_present=dtype_present,
            layout_present=layout_present,
        ))
    return tuple(slots)

def _coerce_slots(value: Any) -> tuple[TensorSlot, ...]:
    if value is None:
        return ()
    if isinstance(value, TensorSlot):
        return (value,)
    if isinstance(value, Mapping):
        return (TensorSlot.from_mapping(value),)
    if isinstance(value, str):
        return _tensor_slots(value, None, None)
    try:
        items = tuple(value)
    except TypeError:
        return ()
    return tuple(
        item if isinstance(item, TensorSlot) else TensorSlot.from_mapping(item)
        for item in items
    )

def _native_abi_record(
    operator: str | None,
    inputs: tuple[TensorSlot, ...],
    outputs: tuple[TensorSlot, ...],
) -> dict[str, Any] | None:
    """Hand ordered raw slots to ``native_tensor_abi`` for canonical qualification.

    No local cleaning, slot deletion, or digest shortcut occurs here.
    Qualification returns ``complete`` with a verified digest, or an
    ``incomplete``/``conflict`` record retaining every supplied slot position."""
    if not operator:
        return None
    return native_abi_from_slots(
        operator,
        [slot.abi_slot() for slot in inputs],
        [slot.abi_slot() for slot in outputs],
    )

def _recanonical_abi(record: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(record, Mapping):
        return None
    operator = record.get("native_operator")
    if not isinstance(operator, str) or not operator.strip():
        return None
    return native_abi_from_slots(
        operator,
        record.get("inputs") or (),
        record.get("outputs") or (),
    )

def _abi_content(record: Mapping[str, Any] | None) -> tuple[Any, ...] | None:
    if not isinstance(record, Mapping):
        return None

    def side(name: str) -> tuple[Any, ...]:
        slots = record.get(name)
        if not isinstance(slots, list):
            return ()
        return tuple(
            (
                bool(slot.get("present", True)),
                tuple(slot.get("shape") or ()),
                slot.get("dtype"),
                slot.get("layout"),
            )
            for slot in slots
            if isinstance(slot, Mapping)
        )

    return (record.get("native_operator"), side("inputs"), side("outputs"))
