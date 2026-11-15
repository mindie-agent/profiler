"""C7 modeling inputs, operator observations, and the ideal roofline bound.

[Role]
  Own the explicit Shape/dtype/layout/hardware/workload records consumed by
  ``theoretical_model``, classify observed Ascend operators into deterministic
  modeling families, project/extract a portable ``ModelingInputsBundle``, and
  compute the local single-kernel roofline lower bound without importing
  ``mindie_sim``.

[Invariants]
  * Missing Shape/dtype/layout/hardware/workload inputs return
    ``unmodeled_reason`` with no numeric bound; no placeholder value is made up.
  * The ideal bound uses caller-supplied raw physical peaks only.  It does not
    apply an empirical compute/memory efficiency or an upstream model result.
  * Operator family classification is deterministic token matching; an
    unrecognized operator stays ``"unknown"`` rather than being guessed.
  * Bundle extraction preserves observed names/shapes/dtypes and emits ``None``
    for absent fields; it never invents shapes, dtypes or durations.
  * Native/tensor evidence is recovered at its own level: ordered input/output
    slots and an explicit ABI record are preserved, while a single legacy
    ``shape`` is filled only from exactly one complete input slot.  A C7
    hotspot or native call is never expanded into a guessed model/service case.
  * The bound is a single-kernel roofline lower bound, never a whole-network
    lower bound and never proof that measured time must exceed it.

[Timeouts & Locks]
  Pure computation.  No locks, sleeps, network, subprocesses or caches.  Bundle
  reads/writes are explicit-path, bounded JSON/JSONL operations.

[Side-Effect Policy]
  No import-time I/O or global-state mutation.  ``extract_modeling_inputs``
  reads only an explicit path; ``write_modeling_inputs_bundle`` writes only the
  requested destination, atomically through a temporary file and ``os.replace``.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from .native_tensor_abi import ABI_SCHEMA
from .native_tensor_abi import DTYPES as _NATIVE_DTYPES
from .native_tensor_abi import native_abi_from_slots

from .modeling_inputs_observations import (
    OperatorObservation, _PROVENANCE_KEYS, _normalise_observation_mapping,
    _provenance_annotations, _verified_abi,
)
from .modeling_inputs_roofline import ModelingInputsBundle
from .modeling_inputs_slots import (
    IDEAL_BOUND_FORMULA_VERSION, OPERATOR_FAMILIES, SCHEMA_VERSION, TensorSlot,
    _DTYPE_ALIASES, _DTYPE_BYTES, _EXPLICIT_UNDEFINED_TEXT, _LEGACY_DTYPE_NAMES,
    _MISSING_SLOT, _MISSING_TEXT, _NATIVE_DTYPE_ALIASES, _OPERATOR_PREFIXES,
    _PLACEHOLDER_OPERATORS, _UNDEFINED_TEXT, _abi_content, _canonical_annotations,
    _clean_operator, _clean_text, _coerce_shape, _coerce_slots, _finite,
    _is_explicit_undefined_text, _is_missing_text, _is_undefined_text,
    _legacy_dtype_name, _ms_to_ns, _native_abi_record, _normalise_dtype,
    _normalise_operator_name, _normalise_slot_dtype, _normalise_slot_layout,
    _positional_field, _recanonical_abi, _slot_from_parts, _slot_shape, _split_slots,
    _tensor_slots, _us_to_ns, classify_operator_family,
)

def _record_mapping(record: Any) -> Mapping[str, Any]:
    if isinstance(record, Mapping):
        return record
    values: dict[str, Any] = {}
    for name in (
        "name", "operator_name", "op_name", "kernel_name", "kernel_type", "op_type",
        "native_operator", "family", "shape", "input_shapes", "dtype", "input_dtypes",
        "layout", "input_formats", "output_shapes", "output_dtypes", "output_formats",
        "inputs", "outputs", "native_abi", "context", "duration_ns", "duration", "duration_us",
        "duration_ms", "measured_device_ms_p50", "count", "call_count", "rank",
        "device_id", "stream_id", "task_id",
    ):
        if hasattr(record, name):
            values[name] = getattr(record, name)
    if not values:
        try:
            values.update(vars(record))
        except TypeError:
            pass
    return values

def _payload_records(payload: Any, metadata: dict[str, Any]) -> list[Any]:
    """Select observation records from a C7/native/bundle payload.

    A C7 hotspot list and a native call record are already at the recoverable
    operator/tensor level.  They are not padded with guessed model or service
    fields just because a report contains them.
    """
    if isinstance(payload, Mapping):
        if isinstance(payload.get("observations"), list):
            metadata["source_kind"] = "bundle"
            return list(payload["observations"])
        if isinstance(payload.get("events"), list):
            metadata["source_kind"] = "events"
            return list(payload["events"])
        if isinstance(payload.get("top_hotspot_kernels"), list):
            metadata["source_kind"] = "c7_summary"
            metadata.setdefault("source_schema", payload.get("schema_version"))
            if payload.get("hotspot_grouping") is not None:
                metadata.setdefault("hotspot_grouping", payload.get("hotspot_grouping"))
            return list(payload["top_hotspot_kernels"])
        if isinstance(payload.get("raw_abi"), Mapping) and isinstance(payload.get("raw_operator"), Mapping):
            metadata["source_kind"] = "native_observation"
            return [payload]
        if isinstance(payload.get("first_call"), Mapping):
            metadata["source_kind"] = "native_observation"
            return [payload["first_call"]]
        if isinstance(payload.get("selected_row"), Mapping):
            selected = dict(payload["selected_row"])
            selected.setdefault("source_csv", payload.get("source_csv"))
            selected.setdefault("source_window", payload.get("source_window"))
            selected.setdefault("scope", payload.get("scope"))
            selected.setdefault("schema", payload.get("schema"))
            selected.setdefault("same_shape_distribution", payload.get("same_shape_distribution"))
            selected.setdefault("source_kind", "native_selected_row")
            selected.setdefault(
                "name",
                f"kernel_row:{selected.get('csv_line') or selected.get('task_id') or 'unknown'}",
            )
            metadata["source_kind"] = "native_selected_row"
            return [selected]
        if isinstance(payload.get("entries"), Mapping):
            leaves: list[Mapping[str, Any]] = []

            def walk(node: Any, path: tuple[str, ...]) -> None:
                if isinstance(node, Mapping):
                    if any(key in node for key in ("kernel_type", "kernel_name", "native_operator", "op_type")):
                        item = dict(node)
                        item.setdefault("entry_key", "/".join(path))
                        if path:
                            item.setdefault("model_label", path[0])
                        for key in ("schema", "source", "use"):
                            if payload.get(key) is not None:
                                item.setdefault(key, payload[key])
                        item.setdefault("source_kind", "qualified_abi_entry")
                        leaves.append(item)
                    else:
                        for key, child in node.items():
                            walk(child, path + (str(key),))
                elif isinstance(node, list):
                    for index, child in enumerate(node):
                        walk(child, path + (str(index),))

            walk(payload["entries"], ())
            if leaves:
                metadata["source_kind"] = "native_observation_collection"
                return leaves
    if isinstance(payload, list):
        return payload
    return [payload]

def _read_records(path: Path, metadata: dict[str, Any]) -> Iterable[Any]:
    text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except (TypeError, ValueError):
        metadata["source_kind"] = "jsonl_records"
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except (TypeError, ValueError):
                continue
        return
    yield from _payload_records(payload, metadata)

@dataclass(frozen=True)
class HardwareSpec:
    """User-supplied raw physical peaks for the ideal roofline bound."""

    name: str
    peak_flops_per_s: float
    memory_bandwidth_bytes_per_s: float

    def validation_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not isinstance(self.name, str) or not self.name.strip():
            errors.append("hardware_name")
        if not _finite(self.peak_flops_per_s) or float(self.peak_flops_per_s) <= 0:
            errors.append("hardware_peak_flops_per_s")
        if not _finite(self.memory_bandwidth_bytes_per_s) or float(self.memory_bandwidth_bytes_per_s) <= 0:
            errors.append("hardware_memory_bandwidth_bytes_per_s")
        return tuple(errors)

    def canonical(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "peak_flops_per_s": self.peak_flops_per_s,
            "memory_bandwidth_bytes_per_s": self.memory_bandwidth_bytes_per_s,
        }

@dataclass(frozen=True)
class KernelInputs:
    """All inputs required before a C7 modeling alignment may be attempted."""

    shape: tuple[int, ...] | None = None; dtype: str | None = None; layout: str | None = None
    hardware: HardwareSpec | None = None; op_kind: str | None = None; flops: float | None = None
    memory_bytes: float | None = None; kernel_name: str | None = None; rank: int | None = None
    annotations: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.shape, list):
            object.__setattr__(self, "shape", tuple(self.shape))
        object.__setattr__(self, "annotations", _canonical_annotations(self.annotations))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "KernelInputs":
        hardware = value.get("hardware")
        if isinstance(hardware, Mapping):
            hardware = HardwareSpec(**dict(hardware))
        shape = value.get("shape")
        if isinstance(shape, list):
            shape = tuple(shape)
        return cls(
            shape=shape,
            dtype=value.get("dtype"),
            layout=value.get("layout"),
            hardware=hardware,
            op_kind=value.get("op_kind"),
            flops=value.get("flops"),
            memory_bytes=value.get("memory_bytes", value.get("bytes")),
            kernel_name=value.get("kernel_name"),
            rank=value.get("rank"),
            annotations=value.get("annotations", ()),
        )

    def _shape_error(self) -> str | None:
        if self.shape is None:
            return "missing_shape"
        if not isinstance(self.shape, tuple) or not self.shape:
            return "invalid_shape"
        if any(
            not isinstance(dim, int) or isinstance(dim, bool) or dim < 0
            for dim in self.shape
        ):
            return "invalid_shape"
        return None

    def _dtype_error(self) -> str | None:
        if self.dtype is None or (isinstance(self.dtype, str) and not self.dtype.strip()):
            return "missing_dtype"
        if not isinstance(self.dtype, str):
            return "invalid_dtype"
        normalized = _normalise_dtype(self.dtype)
        if normalized not in _DTYPE_BYTES:
            return f"unsupported_dtype:{normalized}"
        return None

    def _layout_error(self) -> str | None:
        if self.layout is None:
            return "missing_layout"
        if not isinstance(self.layout, str) or not self.layout.strip():
            return "missing_layout"
        return None

    def _hardware_error(self) -> str | None:
        if self.hardware is None:
            return "missing_hardware"
        if not isinstance(self.hardware, HardwareSpec):
            return "invalid_hardware"
        errors = self.hardware.validation_errors()
        if errors:
            return "invalid_hardware:" + ",".join(errors)
        return None

    def _explicit_workload_error(self) -> str | None:
        if self.flops is None and self.memory_bytes is None:
            return None
        if self.flops is None:
            return "missing_flops"
        if self.memory_bytes is None:
            return "missing_memory_bytes"
        if not _finite(self.flops) or float(self.flops) < 0:
            return "invalid_flops"
        if not _finite(self.memory_bytes) or float(self.memory_bytes) < 0:
            return "invalid_memory_bytes"
        return None

    def _workload_error(self) -> str | None:
        explicit = self._explicit_workload_error()
        if explicit is not None:
            return explicit
        if self.flops is not None or self.memory_bytes is not None:
            return None
        if self.op_kind is None or not str(self.op_kind).strip():
            return "missing_workload"
        kind = str(self.op_kind).strip().lower()
        if kind in {"matmul", "gemm", "mm", "bmm"}:
            return None if len(self.shape or ()) in {3, 4} else "invalid_matmul_shape"
        if kind == "addmm":
            return None if len(self.shape or ()) == 3 else "invalid_addmm_shape"
        if kind in {"copy", "memcpy", "clone"}:
            return None
        if kind in {"rmsnorm", "rms_norm"}:
            return None if len(self.shape or ()) >= 1 else "invalid_rmsnorm_shape"
        if kind in {"elementwise", "relu"}:
            return None if len(self.shape or ()) >= 1 else "invalid_elementwise_shape"
        return f"unsupported_op_kind:{kind}"

    def missing_metadata_inputs(self) -> tuple[str, ...]:
        problems = (
            self._shape_error(),
            self._dtype_error(),
            self._layout_error(),
            self._hardware_error(),
        )
        return tuple(item for item in problems if item)

    def missing_inputs(self) -> tuple[str, ...]:
        return self.missing_metadata_inputs() + tuple(
            item for item in (self._workload_error(),) if item
        )

    def workload(self) -> tuple[float, float, str] | None:
        """Return (flops, memory_bytes, source) or None when under-specified."""
        if self.missing_inputs():
            return None
        if self.flops is not None and self.memory_bytes is not None:
            return float(self.flops), float(self.memory_bytes), "explicit"
        assert self.shape is not None and self.dtype is not None
        dtype_bytes = _DTYPE_BYTES[_normalise_dtype(self.dtype)]
        kind = str(self.op_kind).strip().lower()
        if kind in {"matmul", "gemm", "mm", "bmm"}:
            dims = self.shape
            if len(dims) == 3:
                batch, m, k, n = 1, dims[0], dims[1], dims[2]
            else:
                batch, m, k, n = dims
            flops = 2.0 * batch * m * n * k
            memory = (batch * m * k + batch * k * n + batch * m * n) * dtype_bytes
            return float(flops), float(memory), "matmul_contiguous"
        if kind == "addmm":
            m, k, n = self.shape
            flops = 2.0 * m * n * k
            memory = (m * k + n * k + n + m * n) * dtype_bytes
            return float(flops), float(memory), "addmm_transposed_bias"
        if kind in {"copy", "memcpy", "clone"}:
            numel = math.prod(self.shape)
            return 0.0, float(2 * numel * dtype_bytes), "copy_read_write"
        if kind in {"rmsnorm", "rms_norm"}:
            numel = math.prod(self.shape)
            row_width = self.shape[-1]
            return (
                float(5 * numel),
                float((2 * numel + row_width) * dtype_bytes),
                "rmsnorm_gp_5n",
            )
        if kind in {"elementwise", "relu"}:
            numel = math.prod(self.shape)
            return 0.0, float(2 * numel * dtype_bytes), "elementwise_read_write"
        return None

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "shape": list(self.shape) if self.shape is not None else None,
            "dtype": _normalise_dtype(self.dtype) if isinstance(self.dtype, str) else self.dtype,
            "layout": self.layout,
            "hardware": self.hardware.canonical() if isinstance(self.hardware, HardwareSpec) else None,
            "op_kind": self.op_kind,
            "flops": self.flops,
            "memory_bytes": self.memory_bytes,
            "kernel_name": self.kernel_name,
            "rank": self.rank,
            "annotations": [list(item) for item in self.annotations],
        }

    def input_signature(self) -> str:
        payload = json.dumps(
            self.canonical_payload(),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _coerce_inputs(value: KernelInputs | Mapping[str, Any]) -> KernelInputs:
    if isinstance(value, KernelInputs):
        return value
    if isinstance(value, Mapping):
        return KernelInputs.from_mapping(value)
    raise TypeError("inputs must be KernelInputs or a mapping")

@dataclass(frozen=True)
class IdealLowerBound:
    status: str; lower_bound_ms: float | None; compute_ms: float | None
    memory_ms: float | None; bottleneck: str | None; formula_version: str
    assumptions: tuple[str, ...]; missing_inputs: tuple[str, ...]; unmodeled_reason: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "ideal_hardware_lower_bound_ms": self.lower_bound_ms,
            "compute_ms": self.compute_ms,
            "memory_ms": self.memory_ms,
            "bottleneck": self.bottleneck,
            "formula_version": self.formula_version,
            "assumptions": list(self.assumptions),
            "missing_inputs": list(self.missing_inputs),
            "unmodeled_reason": self.unmodeled_reason,
        }

def extract_modeling_inputs(
    source: Any = None,
    *,
    source_name: str | None = None,
) -> ModelingInputsBundle:
    """Extract a modeling-inputs bundle from records or an explicit JSON path.

    C7 summaries (``top_hotspot_kernels``), native call records (``raw_abi`` /
    ``raw_operator``) and JSON/JSONL record streams are accepted.  Extraction
    stops at the native/tensor level actually present in the input; it does not
    infer a complete model or service case.
    """
    if isinstance(source, ModelingInputsBundle):
        return source
    metadata: dict[str, Any] = {
        "extractor": "extract_modeling_inputs",
        "schema_version": SCHEMA_VERSION,
        "source_kind": "records",
        "native_scope": "operator_and_tensor_only",
        "model_or_service_inferred": False,
    }
    records: Iterable[Any]
    resolved_source = source_name
    if source is None:
        metadata["source_kind"] = "empty"
        records = ()
    elif isinstance(source, (str, Path)):
        path = Path(source)
        records = _read_records(path, metadata)
        resolved_source = resolved_source or str(path)
    elif isinstance(source, Mapping):
        if isinstance(source.get("observations"), list):
            return ModelingInputsBundle.from_mapping(source)
        records = _payload_records(source, metadata)
    else:
        try:
            records = iter(source)
        except TypeError:
            records = (source,)
    observations: list[OperatorObservation] = []
    for record in records:
        observations.append(
            record if isinstance(record, OperatorObservation)
            else OperatorObservation.from_mapping(_record_mapping(record))
        )
    return ModelingInputsBundle(
        observations=observations,
        generated_at=datetime.now(timezone.utc).isoformat(),
        source=resolved_source,
        metadata=metadata,
    )

def write_modeling_inputs_bundle(
    bundle: ModelingInputsBundle | Mapping[str, Any] | Iterable[Any],
    destination: str | Path,
    *,
    indent: int = 2,
) -> Path:
    """Atomically write a bundle as UTF-8 JSON and return the written path."""
    if isinstance(bundle, (str, Path)) and not isinstance(destination, (str, Path)):
        bundle, destination = destination, bundle
    if isinstance(bundle, ModelingInputsBundle):
        payload = bundle
    elif isinstance(bundle, Mapping):
        payload = ModelingInputsBundle.from_mapping(bundle)
    else:
        payload = extract_modeling_inputs(bundle)
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload.as_dict(), indent=indent, sort_keys=True) + "\n"
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except TimeoutError:
        raise
    except BaseException:
        try:
            os.unlink(temporary)
        except TimeoutError:
            raise
        except OSError:
            pass
        raise
    return path

def estimate_ideal_hardware_lower_bound(
    inputs: KernelInputs | Mapping[str, Any],
) -> IdealLowerBound:
    """Compute a single-kernel roofline lower bound or state why it is absent."""
    try:
        spec = _coerce_inputs(inputs)
    except (TypeError, ValueError) as exc:
        return IdealLowerBound(
            status="unmodeled",
            lower_bound_ms=None,
            compute_ms=None,
            memory_ms=None,
            bottleneck=None,
            formula_version=IDEAL_BOUND_FORMULA_VERSION,
            assumptions=(),
            missing_inputs=("invalid_inputs",),
            unmodeled_reason=f"invalid_inputs:{type(exc).__name__}",
        )
    missing = spec.missing_inputs()
    if missing:
        return IdealLowerBound(
            status="unmodeled",
            lower_bound_ms=None,
            compute_ms=None,
            memory_ms=None,
            bottleneck=None,
            formula_version=IDEAL_BOUND_FORMULA_VERSION,
            assumptions=(),
            missing_inputs=missing,
            unmodeled_reason="missing_inputs:" + ",".join(missing),
        )
    workload = spec.workload()
    if workload is None:
        return IdealLowerBound(
            status="unmodeled",
            lower_bound_ms=None,
            compute_ms=None,
            memory_ms=None,
            bottleneck=None,
            formula_version=IDEAL_BOUND_FORMULA_VERSION,
            assumptions=(),
            missing_inputs=("missing_workload",),
            unmodeled_reason="missing_inputs:missing_workload",
        )
    assert spec.hardware is not None
    flops, memory_bytes, source = workload
    compute_ms = flops / float(spec.hardware.peak_flops_per_s) * 1000.0
    memory_ms = memory_bytes / float(spec.hardware.memory_bandwidth_bytes_per_s) * 1000.0
    lower_ms = max(compute_ms, memory_ms)
    bottleneck = "memory" if memory_ms > compute_ms else "compute"
    assumptions = [
        f"formula={IDEAL_BOUND_FORMULA_VERSION}",
        "single_kernel_no_launch_dependency_or_cache_cost",
        "peak_compute_and_memory_fully_overlapped",
        "hardware_peaks_are_user_supplied_raw_physical_values",
        f"workload_source={source}",
    ]
    if source in {"matmul_contiguous", "addmm_transposed_bias", "copy_read_write", "rmsnorm_gp_5n", "elementwise_read_write"}:
        assumptions.append("layout_is_treated_as_contiguous_for_byte_count")
    if source == "addmm_transposed_bias":
        assumptions.append("addmm_profile_shape_order_a_mk_b_nk_bias_n")
    if source == "rmsnorm_gp_5n":
        assumptions.append("rmsnorm_gp_ops_from_upstream_cost_utils_5n")
    if source == "elementwise_read_write":
        assumptions.append("elementwise_memory_only_no_compute")
    return IdealLowerBound(
        status="modeled",
        lower_bound_ms=lower_ms,
        compute_ms=compute_ms,
        memory_ms=memory_ms,
        bottleneck=bottleneck,
        formula_version=IDEAL_BOUND_FORMULA_VERSION,
        assumptions=tuple(assumptions),
        missing_inputs=(),
        unmodeled_reason=None,
    )

ideal_hardware_lower_bound = estimate_ideal_hardware_lower_bound

__all__ = [
    "IDEAL_BOUND_FORMULA_VERSION",
    "OPERATOR_FAMILIES",
    "SCHEMA_VERSION",
    "HardwareSpec",
    "IdealLowerBound",
    "KernelInputs",
    "ModelingInputsBundle",
    "OperatorObservation",
    "TensorSlot",
    "classify_operator_family",
    "estimate_ideal_hardware_lower_bound",
    "extract_modeling_inputs",
    "ideal_hardware_lower_bound",
    "write_modeling_inputs_bundle",
]
