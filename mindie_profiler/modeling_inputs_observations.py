"""Per-operator ABI observation bundles and ideal hardware Roofline bounds (modeling_inputs_observations).

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

from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from .native_tensor_abi import ABI_SCHEMA

from .modeling_inputs_slots import (
    TensorSlot, _abi_content, _canonical_annotations, _clean_operator, _clean_text,
    _coerce_shape, _coerce_slots, _legacy_dtype_name, _ms_to_ns, _native_abi_record,
    _normalise_slot_dtype, _normalise_slot_layout, _positional_field, _recanonical_abi,
    _tensor_slots, _us_to_ns, classify_operator_family,
)

def _verified_abi(
    provided: Mapping[str, Any] | None,
    computed: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Recompute canonical ABI slot content and preserve any unresolved conflict.

    The supplied digest is evidence, never authority.  Canonical dtype aliases
    and slot content come from ``native_tensor_abi``; a raw spelling difference
    is not a content conflict, whereas a shape/layout/order/presence change is.
    """
    if provided is None:
        return None if computed is None else dict(computed)
    provided = dict(provided)
    declared_value = provided.get("declared_digest")
    if declared_value is None:
        digest_value = str(provided.get("digest") or "").strip().lower()
        computed_value = str(provided.get("computed_digest") or "").strip().lower()
        declared_value = digest_value if digest_value and digest_value != computed_value else ""
    declared_digest = str(declared_value or "").strip().lower()
    provided_canon = _recanonical_abi(provided)
    if computed is None:
        return {
            **provided,
            "status": "conflict",
            "digest": None,
            "verified": False,
            "declared_digest": declared_digest or None,
            "computed_digest": None,
            "issues": [
                *(provided.get("issues") or ()),
                {"slot": "abi", "reason": "abi_not_verifiable_without_typed_slots"},
            ],
            "provided": provided,
        }
    computed = dict(computed)
    computed_digest = str(computed.get("computed_digest") or computed.get("digest") or "").strip().lower()
    if declared_digest and not computed.get("verified"):
        return {
            **computed,
            "status": "conflict",
            "digest": None,
            "verified": False,
            "declared_digest": declared_digest,
            "computed_digest": computed_digest or None,
            "issues": [
                *(computed.get("issues") or ()),
                {"slot": "abi", "reason": "declared_digest_not_verified",
                 "declared_digest": declared_digest,
                 "computed_digest": computed_digest or None},
            ],
            "provided": provided,
        }
    content_equal = _abi_content(provided_canon) == _abi_content(computed)
    if str(provided.get("status") or "") != "conflict" and content_equal:
        if declared_digest and computed_digest and declared_digest != computed_digest:
            return {
                **computed,
                "status": "conflict",
                "digest": None,
                "verified": False,
                "declared_digest": declared_digest,
                "computed_digest": computed_digest,
                "issues": [
                    *(computed.get("issues") or ()),
                    {"slot": "abi", "reason": "declared_digest_mismatch",
                     "declared_digest": declared_digest,
                     "computed_digest": computed_digest},
                ],
                "provided": provided,
            }
        result = dict(computed)
        result["declared_digest"] = declared_digest or None
        result["computed_digest"] = computed_digest or None
        return result
    return {
        **computed,
        "status": "conflict",
        "digest": None,
        "verified": False,
        "declared_digest": declared_digest or None,
        "computed_digest": computed_digest or None,
        "issues": [
            *(computed.get("issues") or ()),
            {"slot": "abi", "reason": "abi_content_conflict",
             "declared_digest": declared_digest or None,
             "computed_digest": computed_digest or None,
             "provided_status": provided.get("status")},
        ],
        "provided": provided,
    }

_PROVENANCE_KEYS = (
    "case_id", "cohort_id", "native_operator_type", "api", "implementation",
    "hardware", "semantic_block", "representative_window", "share_basis",
    "distribution_basis", "rank_id", "source_path", "evidence_path",
    "selection", "execution_engine", "bound_family",
    "measured_device_ms_p50", "measured_device_ms_total", "call_count",
    "complete_call_count", "clipped_event_count", "csv_line", "scope",
    "entry_key", "model_label", "source_csv_path", "source_csv_sha256",
    "source_sha256",
)

def _provenance_annotations(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value[key]
        for key in _PROVENANCE_KEYS
        if value.get(key) is not None and not isinstance(value.get(key), (Mapping, list, tuple))
    }

def _normalise_observation_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    """Recover one native/tensor observation from C7, native or bundle records.

    The mapping is only normalised, never expanded into a model or service case:
    a C7 hotspot, a native operator call and a tensor descriptor stay at their
    own level.  Raw ABI/operator containers are unpacked into typed fields and
    provenance annotations instead of being stringified as opaque blobs.
    """
    data = dict(value)
    native = data.pop("native", None)
    if isinstance(native, Mapping):
        native_abi = native.get("abi")
        if native.get("operator"):
            data.setdefault("native_operator", native.get("operator"))
            data.setdefault(
                "native_operator_source",
                native.get("operator_source") or "bundle.native.operator",
            )
        elif isinstance(native_abi, Mapping) and native_abi.get("native_operator"):
            data.setdefault("native_operator", native_abi.get("native_operator"))
            data.setdefault("native_operator_source", "bundle.native.abi.native_operator")
        explicit_type = (
            _clean_operator(data.get("kernel_type"))
            or _clean_operator(data.get("op_type"))
            or _clean_operator(data.get("native_operator_type"))
        )
        if (
            native.get("operator")
            and explicit_type
            and _clean_operator(native.get("operator")) != explicit_type
        ):
            data.setdefault(
                "native_operator_conflict",
                f"{native.get('operator')}!={explicit_type}",
            )
        if native.get("inputs") is not None:
            data.setdefault("inputs", native.get("inputs"))
        elif isinstance(native_abi, Mapping) and native_abi.get("inputs") is not None:
            data.setdefault("inputs", native_abi.get("inputs"))
        if native.get("outputs") is not None:
            data.setdefault("outputs", native.get("outputs"))
        elif isinstance(native_abi, Mapping) and native_abi.get("outputs") is not None:
            data.setdefault("outputs", native_abi.get("outputs"))
        if native_abi is not None:
            data.setdefault("native_abi", native_abi)
    for alias, target in (("input_slots", "inputs"), ("output_slots", "outputs")):
        if data.get(target) is None and data.get(alias) is not None:
            data[target] = data.pop(alias)
    raw_abi = data.pop("raw_abi", None)
    if isinstance(raw_abi, Mapping):
        for key in ("input_shapes", "input_dtypes", "input_formats",
                    "output_shapes", "output_dtypes", "output_formats"):
            if data.get(key) is None and raw_abi.get(key) is not None:
                data[key] = raw_abi[key]
        if data.get("inputs") is None and raw_abi.get("inputs") is not None:
            data["inputs"] = raw_abi["inputs"]
        if data.get("outputs") is None and raw_abi.get("outputs") is not None:
            data["outputs"] = raw_abi["outputs"]
        if data.get("native_abi") is None and raw_abi.get("schema") == ABI_SCHEMA:
            data["native_abi"] = raw_abi
    top_abi = data.get("native_abi")
    if isinstance(top_abi, Mapping):
        if data.get("inputs") is None and top_abi.get("inputs") is not None:
            data["inputs"] = top_abi.get("inputs")
        if data.get("outputs") is None and top_abi.get("outputs") is not None:
            data["outputs"] = top_abi.get("outputs")
        if data.get("native_operator") is None and top_abi.get("native_operator"):
            data["native_operator"] = top_abi.get("native_operator")
    raw_operator = data.pop("raw_operator", None)
    if isinstance(raw_operator, Mapping):
        data.setdefault("kernel_type", raw_operator.get("type"))
        data.setdefault("kernel_name", raw_operator.get("name"))
        data.setdefault("device_id", raw_operator.get("device_id"))
        data.setdefault("stream_id", raw_operator.get("stream_id"))
        data.setdefault("task_id", raw_operator.get("task_id"))
        if raw_operator.get("type"):
            data.setdefault("native_operator_source", "raw_operator.type")
    if not data.get("native_operator_source"):
        for key in ("native_operator_source", "native_operator_type_source"):
            if data.get(key):
                data["native_operator_source"] = data[key]
                break
    if not data.get("native_operator"):
        for key in ("native_operator_type", "kernel_type", "op_type"):
            candidate = _clean_operator(data.get(key))
            if candidate:
                data["native_operator"] = candidate
                data.setdefault("native_operator_source", key)
                break
    # A kernel display name is never promoted to a native operator type.
    if data.get("duration_ns") is None:
        if data.get("measured_device_ms_p50") is not None:
            data["duration_ns"] = _ms_to_ns(data.get("measured_device_ms_p50"))
            data.setdefault("duration_basis", "measured_device_ms_p50")
        elif data.get("duration_us") is not None:
            data["duration_ns"] = _us_to_ns(data.get("duration_us"))
            data.setdefault("duration_basis", "duration_us")
        elif data.get("duration_ms") is not None:
            data["duration_ns"] = _ms_to_ns(data.get("duration_ms"))
            data.setdefault("duration_basis", "duration_ms")
        elif isinstance(data.get("clock"), Mapping) and data["clock"].get("duration_us") is not None:
            data["duration_ns"] = _us_to_ns(data["clock"].get("duration_us"))
            data.setdefault("duration_basis", "clock.duration_us")
        elif isinstance(data.get("observation_window"), Mapping) and data["observation_window"].get("call_duration_us") is not None:
            data["duration_ns"] = _us_to_ns(data["observation_window"].get("call_duration_us"))
            data.setdefault("duration_basis", "observation_window.call_duration_us")
    if data.get("count") is None and data.get("call_count") is not None:
        data["count"] = data.get("call_count")
    source_csv = data.get("source_csv")
    if isinstance(source_csv, Mapping):
        if source_csv.get("path"):
            data.setdefault("source_csv_path", source_csv.get("path"))
        if source_csv.get("sha256"):
            data.setdefault("source_csv_sha256", source_csv.get("sha256"))
    source_ref = data.get("source")
    if isinstance(source_ref, Mapping):
        if source_ref.get("path"):
            data.setdefault("source_path", source_ref.get("path"))
        if source_ref.get("sha256"):
            data.setdefault("source_sha256", source_ref.get("sha256"))
    context = data.get("context")
    if not isinstance(context, Mapping):
        context = {}
        for key in (
            "clock", "observation_window", "step_state", "ambiguities", "runtime",
            "hardware", "deployment", "kv_view", "control_flags", "geometry",
            "source_csv", "source_window", "scope", "schema",
            "same_shape_distribution", "entry_key", "model_label", "source",
            "use", "source_kind",
        ):
            if data.get(key) is not None:
                context[key] = data[key]
    if context:
        data["context"] = dict(context)
        for key in (
            "clock", "observation_window", "step_state", "ambiguities", "runtime",
            "hardware", "deployment", "kv_view", "control_flags", "geometry",
            "source_csv", "source_window", "scope", "schema",
            "same_shape_distribution", "entry_key", "model_label", "source",
            "use", "source_kind",
        ):
            data.pop(key, None)
    if not any(_clean_text(data.get(key)) for key in (
        "name", "operator_name", "operator", "op_name", "kernel_name", "op_type", "kernel_type",
    )):
        if data.get("native_operator"):
            data["name"] = data["native_operator"]
        elif data.get("csv_line") is not None:
            data["name"] = f"kernel_row:{data.get('csv_line')}"
        elif data.get("entry_key"):
            data["name"] = str(data["entry_key"])
    if data.get("native_operator") and not data.get("native_operator_source"):
        data["native_operator_source"] = "provided"
    provenance = _provenance_annotations(data)
    if provenance:
        annotations = data.get("annotations")
        merged = dict(annotations) if isinstance(annotations, Mapping) else dict(
            _canonical_annotations(annotations or ())
        )
        merged.update(provenance)
        data["annotations"] = merged
    return data

@dataclass(frozen=True, init=False)
class OperatorObservation:
    """One observed operator occurrence with optional native/tensor evidence.

    ``shape``/``dtype``/``layout`` remain the legacy single-tensor view.  They
    are populated only when exactly one complete input slot is present; the
    ordered native slots live in ``inputs``/``outputs`` so multi-input kernels
    are never collapsed to the first shape.
    """

    name: str; family: str; shape: tuple[int, ...] | None; dtype: str | None
    layout: str | None; duration_ns: int | None; count: int; rank: int | None
    device_id: str | None; stream_id: str | None; task_id: str | None
    native_operator: str | None; native_operator_source: str | None
    inputs: tuple[TensorSlot, ...]
    outputs: tuple[TensorSlot, ...]; native_abi: dict[str, Any] | None
    context: dict[str, Any] | None
    annotations: tuple[tuple[str, str], ...]

    def __init__(
        self, name: str | None = None, family: str | None = None, shape: Any = None,
        dtype: str | None = None, layout: str | None = None, duration_ns: int | None = None,
        count: int = 1, rank: int | None = None, device_id: str | int | None = None,
        stream_id: str | int | None = None, task_id: str | int | None = None, annotations: Any = (),
        *, operator_name: str | None = None, operator: str | None = None, op_name: str | None = None,
        kernel_name: str | None = None, op_type: str | None = None, kernel_type: str | None = None,
        native_operator: str | None = None, native_operator_source: str | None = None,
        input_shapes: Any = None, input_dtypes: Any = None,
        input_formats: Any = None, output_shapes: Any = None, output_dtypes: Any = None,
        output_formats: Any = None, inputs: Any = None, outputs: Any = None,
        native_abi: Mapping[str, Any] | None = None, context: Mapping[str, Any] | None = None,
        duration: Any = None, duration_us: Any = None, duration_ms: Any = None,
        measured_device_ms_p50: Any = None, call_count: Any = None,
        extra: Mapping[str, Any] | None = None, **kwargs: Any,
    ) -> None:
        observed_name = name or operator_name or operator or op_name or kernel_name or op_type or kernel_type or native_operator or ""
        if not isinstance(observed_name, str) or not observed_name.strip():
            raise ValueError("operator observation requires a non-empty name")
        observed_native_operator = _clean_operator(native_operator or kernel_type)
        if not observed_native_operator:
            observed_native_operator = None
        observed_operator_source = native_operator_source
        if observed_native_operator and not observed_operator_source:
            observed_operator_source = "kernel_type" if kernel_type else "provided"
        elif not observed_native_operator:
            observed_operator_source = None
        tensor_fields = any(
            value is not None for value in (
                input_shapes, input_dtypes, input_formats,
                output_shapes, output_dtypes, output_formats,
            )
        ) or bool(inputs) or bool(outputs) or native_abi is not None
        if inputs is not None:
            slot_inputs = _coerce_slots(inputs)
        elif (
            input_shapes is not None
            or _positional_field(input_dtypes)
            or _positional_field(input_formats)
        ):
            slot_inputs = _tensor_slots(input_shapes, input_dtypes, input_formats)
        elif shape is not None and any(
            value is not None for value in (dtype, input_dtypes, layout, input_formats)
        ):
            slot_inputs = (
                TensorSlot(
                    shape=_coerce_shape(shape),
                    dtype=dtype if dtype is not None else input_dtypes,
                    layout=layout if layout is not None else input_formats,
                ),
            )
        else:
            slot_inputs = ()
        if outputs is not None:
            slot_outputs = _coerce_slots(outputs)
        elif (
            output_shapes is not None
            or _positional_field(output_dtypes)
            or _positional_field(output_formats)
        ):
            slot_outputs = _tensor_slots(output_shapes, output_dtypes, output_formats)
        else:
            slot_outputs = ()
        single = slot_inputs[0] if len(slot_inputs) == 1 else None
        if shape is not None:
            observed_shape = _coerce_shape(shape)
            observed_dtype = (
                _legacy_dtype_name(_normalise_slot_dtype(dtype)) if dtype is not None
                else (_legacy_dtype_name(_normalise_slot_dtype(single.dtype)) if single is not None else None)
            )
            observed_layout = (
                _normalise_slot_layout(layout) if layout is not None
                else (single.layout if single is not None else None)
            )
        else:
            observed_shape = single.shape if single is not None and single.state != "explicit_undefined" else None
            observed_dtype = _legacy_dtype_name(_normalise_slot_dtype(single.dtype)) if single is not None else None
            observed_layout = single.layout if single is not None else None
            if dtype is not None:
                observed_dtype = _legacy_dtype_name(_normalise_slot_dtype(dtype))
            if layout is not None:
                observed_layout = _normalise_slot_layout(layout)
        if duration_ns is not None:
            observed_duration = duration_ns
        elif duration_us is not None:
            observed_duration = _us_to_ns(duration_us)
        elif duration_ms is not None:
            observed_duration = _ms_to_ns(duration_ms)
        elif measured_device_ms_p50 is not None:
            observed_duration = _ms_to_ns(measured_device_ms_p50)
        else:
            observed_duration = duration
        if observed_duration is not None:
            try:
                observed_duration = max(0, int(observed_duration))
            except (TypeError, ValueError):
                observed_duration = None
        if call_count is not None and count == 1:
            count = call_count
        try:
            observed_count = max(0, int(count))
        except (TypeError, ValueError):
            observed_count = 0
        try:
            observed_rank = None if rank is None else int(rank)
        except (TypeError, ValueError):
            observed_rank = None
        resolved_family = family or classify_operator_family(observed_name)
        provided_abi = dict(native_abi) if isinstance(native_abi, Mapping) else None
        computed_abi = (
            _native_abi_record(observed_native_operator, slot_inputs, slot_outputs)
            if (tensor_fields and observed_native_operator) else None
        )
        native_abi = _verified_abi(provided_abi, computed_abi)
        identity_status = (
            "typed" if observed_native_operator
            else "missing_operator_type"
            if (slot_inputs or slot_outputs or observed_duration is not None)
            else "absent"
        )
        merged = dict(extra or {})
        merged.update(kwargs)
        for key, value in (
            ("operator_name", operator_name), ("op_name", op_name),
            ("kernel_name", kernel_name), ("op_type", op_type),
            ("kernel_type", kernel_type), ("native_operator", observed_native_operator),
        ):
            if value is not None and key not in merged:
                merged[key] = value
        if annotations:
            merged.update(dict(_canonical_annotations(annotations)))
        if identity_status == "missing_operator_type":
            merged.setdefault("native_identity_gap", "missing_operator_type")
        object.__setattr__(self, "name", observed_name.strip())
        object.__setattr__(self, "family", str(resolved_family).strip().lower() or "unknown")
        object.__setattr__(self, "shape", observed_shape)
        object.__setattr__(self, "dtype", observed_dtype)
        object.__setattr__(self, "layout", observed_layout)
        object.__setattr__(self, "duration_ns", observed_duration)
        object.__setattr__(self, "count", observed_count)
        object.__setattr__(self, "rank", observed_rank)
        object.__setattr__(self, "device_id", None if device_id is None else str(device_id))
        object.__setattr__(self, "stream_id", None if stream_id is None else str(stream_id))
        object.__setattr__(self, "task_id", None if task_id is None else str(task_id))
        object.__setattr__(self, "native_operator", observed_native_operator)
        object.__setattr__(self, "native_operator_source", observed_operator_source)
        object.__setattr__(self, "inputs", tuple(slot_inputs))
        object.__setattr__(self, "outputs", tuple(slot_outputs))
        object.__setattr__(self, "native_abi", None if native_abi is None else dict(native_abi))
        object.__setattr__(self, "context", None if context is None else dict(context))
        object.__setattr__(self, "annotations", tuple(sorted((str(k), str(v)) for k, v in merged.items())))

    @property
    def operator_name(self) -> str: return self.name

    @property
    def op_name(self) -> str: return self.name

    @property
    def kernel_name(self) -> str: return self.name

    @property
    def input_shapes(self) -> tuple[int, ...] | None: return self.shape

    @property
    def input_dtypes(self) -> str | None: return self.dtype

    @property
    def input_formats(self) -> str | None: return self.layout

    @property
    def input_slots(self) -> tuple[TensorSlot, ...]: return self.inputs

    @property
    def output_slots(self) -> tuple[TensorSlot, ...]: return self.outputs

    @property
    def native_identity_status(self) -> str:
        if self.native_operator:
            return "typed"
        if self.inputs or self.outputs or self.duration_ns is not None:
            return "missing_operator_type"
        return "absent"

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "OperatorObservation":
        if not isinstance(value, Mapping):
            raise TypeError("operator observation must be a mapping")
        return cls(**_normalise_observation_mapping(value))

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name, "operator_name": self.name, "family": self.family,
            "shape": list(self.shape) if self.shape is not None else None,
            "dtype": self.dtype, "layout": self.layout, "duration_ns": self.duration_ns,
            "count": self.count, "rank": self.rank, "device_id": self.device_id,
            "stream_id": self.stream_id, "task_id": self.task_id,
            "annotations": [list(item) for item in self.annotations],
        }
        if self.native_operator or self.inputs or self.outputs or self.native_abi or self.duration_ns is not None:
            payload["native"] = {
                "display_name": self.name,
                "operator": self.native_operator,
                "operator_source": self.native_operator_source,
                "identity_status": self.native_identity_status,
                "inputs": [slot.as_dict() for slot in self.inputs],
                "outputs": [slot.as_dict() for slot in self.outputs],
                "abi": None if self.native_abi is None else dict(self.native_abi),
            }
        if self.context:
            payload["context"] = dict(self.context)
        return payload

    to_dict = as_dict
