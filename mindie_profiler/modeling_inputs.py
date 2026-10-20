"""C7 modeling inputs, operator observations, and the ideal roofline bound.

[Role]
  Own the explicit Shape/dtype/layout/hardware/workload records consumed by
  ``theoretical_model``, classify observed Ascend operators into deterministic
  modeling families, project/extract a portable ``ModelingInputsBundle``, and
  compute the local single-kernel roofline lower bound.  It carries a fully
  self-contained fallback and imports ``mindie_sim`` only when already installed.

[Invariants]
  * Missing Shape/dtype/layout/hardware/workload inputs return
    ``unmodeled_reason`` with no numeric bound; no placeholder value is made up.
  * The ideal bound uses caller-supplied raw physical peaks only.  It does not
    apply an empirical compute/memory efficiency or an upstream model result.
  * Operator family classification is deterministic token matching; an
    unrecognized operator stays ``"unknown"`` rather than being guessed.
  * Bundle extraction preserves observed names/shapes/dtypes and emits ``None``
    for absent fields; it never invents shapes, dtypes or durations.
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

try:  # Prefer the shared implementation when mindie-sim is installed.
    from mindie_sim import modeling_inputs as _sim_modeling_inputs
except (ImportError, ModuleNotFoundError):  # Isolated mindie-profiler install.
    _sim_modeling_inputs = None

IDEAL_BOUND_FORMULA_VERSION = "roofline-max-v1"
SCHEMA_VERSION = "mindie-modeling-inputs/1"

# Stable family catalogue consumed by the simulator.  Tokens are compared
# against the normalized operator name; order resolves overlap (for example
# GroupedMatmulAllReduce is a matmul before it is a communication op).
OPERATOR_FAMILIES: dict[str, tuple[str, ...]] = {
    "matmul": ("matmul", "batchmatmul", "batch_matmul", "bmm", "gemm", "mm", "addmm",
               "linear", "fusedmatmul", "groupedmatmul", "quantmatmul",
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
}

_OPERATOR_PREFIXES = ("aclnn", "aclop", "aic", "aiv", "mix", "op")

_DTYPE_BYTES = {
    "float16": 2,
    "bfloat16": 2,
    "float32": 4,
    "float64": 8,
    "int8": 1,
    "uint8": 1,
    "int16": 2,
    "int32": 4,
    "int64": 8,
    "bool": 1,
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
}


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _normalise_dtype(dtype: str) -> str:
    key = dtype.strip().lower().replace("-", "_").replace(" ", "_")
    return _DTYPE_ALIASES.get(key, key)


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


@dataclass(frozen=True, init=False)
class OperatorObservation:
    """One observed operator occurrence with optional modeling metadata."""

    name: str; family: str; shape: tuple[int, ...] | None; dtype: str | None
    layout: str | None; duration_ns: int | None; count: int; rank: int | None
    device_id: str | None; stream_id: str | None; task_id: str | None
    annotations: tuple[tuple[str, str], ...]

    def __init__(
        self, name: str | None = None, family: str | None = None, shape: Any = None,
        dtype: str | None = None, layout: str | None = None, duration_ns: int | None = None,
        count: int = 1, rank: int | None = None, device_id: str | int | None = None,
        stream_id: str | int | None = None, task_id: str | int | None = None, annotations: Any = (),
        *, operator_name: str | None = None, operator: str | None = None, op_name: str | None = None,
        kernel_name: str | None = None, op_type: str | None = None, input_shapes: Any = None,
        input_dtypes: Any = None, input_formats: Any = None, duration: Any = None,
        extra: Mapping[str, Any] | None = None, **kwargs: Any,
    ) -> None:
        observed_name = name or operator_name or operator or op_name or kernel_name or op_type or ""
        if not isinstance(observed_name, str) or not observed_name.strip():
            raise ValueError("operator observation requires a non-empty name")
        observed_shape = _coerce_shape(shape if shape is not None else input_shapes)
        observed_dtype = dtype if dtype is not None else input_dtypes
        if isinstance(observed_dtype, str) and observed_dtype.strip():
            observed_dtype = _normalise_dtype(observed_dtype)
        else:
            observed_dtype = None
        observed_layout = layout if layout is not None else input_formats
        observed_layout = observed_layout.strip() if isinstance(observed_layout, str) and observed_layout.strip() else None
        observed_duration = duration_ns if duration_ns is not None else duration
        if observed_duration is not None:
            try:
                observed_duration = max(0, int(observed_duration))
            except (TypeError, ValueError):
                observed_duration = None
        try:
            observed_count = max(0, int(count))
        except (TypeError, ValueError):
            observed_count = 0
        try:
            observed_rank = None if rank is None else int(rank)
        except (TypeError, ValueError):
            observed_rank = None
        resolved_family = family or classify_operator_family(observed_name)
        merged = dict(extra or {})
        merged.update(kwargs)
        for key, value in (
            ("operator_name", operator_name), ("op_name", op_name),
            ("kernel_name", kernel_name), ("op_type", op_type),
        ):
            if value is not None and key not in merged:
                merged[key] = value
        if annotations:
            merged.update(dict(_canonical_annotations(annotations)))
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

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "OperatorObservation":
        if not isinstance(value, Mapping):
            raise TypeError("operator observation must be a mapping")
        return cls(**dict(value))

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "operator_name": self.name, "family": self.family,
                "shape": list(self.shape) if self.shape is not None else None,
                "dtype": self.dtype, "layout": self.layout, "duration_ns": self.duration_ns,
                "count": self.count, "rank": self.rank, "device_id": self.device_id,
                "stream_id": self.stream_id, "task_id": self.task_id,
                "annotations": [list(item) for item in self.annotations]}

    to_dict = as_dict


@dataclass(frozen=True, init=False)
class ModelingInputsBundle:
    """Portable collection of operator observations consumed by a simulator."""

    schema_version: str; observations: tuple[OperatorObservation, ...]
    generated_at: str | None; source: str | None; metadata: dict[str, Any]

    def __init__(self, observations: Iterable[OperatorObservation | Mapping[str, Any]] = (),
                 *, schema_version: str = SCHEMA_VERSION, generated_at: str | None = None,
                 source: str | None = None, metadata: Mapping[str, Any] | None = None) -> None:
        normalized: list[OperatorObservation] = []
        for item in observations:
            if isinstance(item, OperatorObservation):
                normalized.append(item)
            elif isinstance(item, Mapping):
                normalized.append(OperatorObservation.from_mapping(item))
            else:
                raise TypeError("observations must contain OperatorObservation or mappings")
        object.__setattr__(self, "schema_version", str(schema_version))
        object.__setattr__(self, "observations", tuple(normalized))
        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ModelingInputsBundle":
        if not isinstance(value, Mapping):
            raise TypeError("modeling inputs bundle must be a mapping")
        return cls(
            observations=value.get("observations", ()),
            schema_version=value.get("schema_version", SCHEMA_VERSION),
            generated_at=value.get("generated_at"),
            source=value.get("source"),
            metadata=value.get("metadata"),
        )

    from_dict = from_mapping

    def as_dict(self) -> dict[str, Any]:
        family_counts: dict[str, int] = {}
        for observation in self.observations:
            family_counts[observation.family] = family_counts.get(observation.family, 0) + 1
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source": self.source,
            "observation_count": len(self.observations),
            "families": dict(sorted(family_counts.items())),
            "observations": [observation.as_dict() for observation in self.observations],
            "metadata": dict(self.metadata),
        }

    to_dict = as_dict

    def __len__(self) -> int:
        return len(self.observations)

    def __iter__(self):
        return iter(self.observations)

    def __getitem__(self, key: str) -> Any:
        return self.as_dict()[key]


def _record_mapping(record: Any) -> Mapping[str, Any]:
    if isinstance(record, Mapping):
        return record
    values: dict[str, Any] = {}
    for name in ("name", "operator_name", "op_name", "kernel_name", "op_type", "family",
                 "shape", "input_shapes", "dtype", "input_dtypes", "layout", "input_formats",
                 "duration_ns", "duration", "count", "rank", "device_id", "stream_id", "task_id"):
        if hasattr(record, name):
            values[name] = getattr(record, name)
    if not values:
        try:
            values.update(vars(record))
        except TypeError:
            pass
    return values


def _read_records(path: Path) -> Iterable[Any]:
    text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except (TypeError, ValueError):
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except (TypeError, ValueError):
                continue
        return
    if isinstance(payload, Mapping) and isinstance(payload.get("observations"), list):
        yield from payload["observations"]
    elif isinstance(payload, Mapping) and isinstance(payload.get("events"), list):
        yield from payload["events"]
    elif isinstance(payload, list):
        yield from payload
    else:
        yield payload


def extract_modeling_inputs(
    source: Any = None,
    *,
    source_name: str | None = None,
) -> ModelingInputsBundle:
    """Extract a modeling-inputs bundle from records or an explicit JSON path."""
    if isinstance(source, ModelingInputsBundle):
        return source
    records: Iterable[Any]
    resolved_source = source_name
    if source is None:
        records = ()
    elif isinstance(source, (str, Path)):
        path = Path(source)
        records = _read_records(path)
        resolved_source = resolved_source or str(path)
    elif isinstance(source, Mapping):
        if isinstance(source.get("observations"), list):
            return ModelingInputsBundle.from_mapping(source)
        records = (source,)
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
        metadata={"extractor": "extract_modeling_inputs", "schema_version": SCHEMA_VERSION},
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
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return path


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

if _sim_modeling_inputs is not None:
    # Share the installed mindie-sim roofline types/formula when available.
    IDEAL_BOUND_FORMULA_VERSION = getattr(_sim_modeling_inputs, "IDEAL_BOUND_FORMULA_VERSION", IDEAL_BOUND_FORMULA_VERSION)
    HardwareSpec = getattr(_sim_modeling_inputs, "HardwareSpec", HardwareSpec)
    KernelInputs = getattr(_sim_modeling_inputs, "KernelInputs", KernelInputs)
    IdealLowerBound = getattr(_sim_modeling_inputs, "IdealLowerBound", IdealLowerBound)
    estimate_ideal_hardware_lower_bound = getattr(_sim_modeling_inputs, "estimate_ideal_hardware_lower_bound", estimate_ideal_hardware_lower_bound)

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
    "classify_operator_family",
    "estimate_ideal_hardware_lower_bound",
    "extract_modeling_inputs",
    "ideal_hardware_lower_bound",
    "write_modeling_inputs_bundle",
]
