"""Clean-Core ``mindie-sim`` Roofline provider and keyed model-input registry.

[Role]
  Turn measured ``Observation`` events into the keyed ``KernelInputs`` registry
  consumed by hotspot enrichment, and price one request through a versioned
  provider whose peaks come from :mod:`mindie_profiler.hardware_presets`.
[Invariants]
  * A registry entry exists only for a fully described ND matrix observation
    whose two inputs and one output close ``(M, K) x (K, N) -> (M, N)`` with a
    single common dtype; every other key stays absent (never fabricated).
  * Conflicting observations of the same ``(rank, block, kernel)`` key remove
    the entry instead of picking one silently.
  * Hardware is resolved per observation dtype; one default BF16 peak is never
    reused for an INT8/FP8/FP4 kernel.
  * The provider returns the request's own ``input_signature`` and non-empty
    assumptions/evidence; its version is a plain semantic version.
[Timeouts & Locks]
  Pure in-memory arithmetic over already-collected observations; no locks or
  device access.
[Side-Effect Policy]
  No I/O and no import of ``torch``/``torch_npu``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .hardware_presets import resolve_hardware_preset
from .modeling_inputs import (
    IDEAL_BOUND_FORMULA_VERSION, KernelInputs, OperatorObservation,
)
from .native_tensor_abi import DTYPES
from .theoretical_model import (
    ProviderIdentity, ProviderPrediction, ProviderUnmodeledError,
)

PROVIDER_NAME = "mindie_sim.clean_core.roofline"
_DECLARED_PIN_VERSION = "0.9.18"
_MATRIX_OP_TYPES = frozenset({"MatMul", "MatMulV2", "MatMulV3", "BatchMatMulV2"})


def sim_version() -> str | None:
    """Return the installed ``mindie_sim`` semantic version without device use."""
    try:
        import mindie_sim
    except ImportError:
        return None
    version = getattr(mindie_sim, "__version__", None)
    return version if isinstance(version, str) and version.strip() else None


@dataclass(frozen=True)
class MindieSimModelingProvider:
    """Roofline provider over the declared hardware peaks for one execution."""

    version: str | None = None

    @property
    def identity(self) -> ProviderIdentity:
        return ProviderIdentity(
            provider_name=PROVIDER_NAME,
            provider_version=self.version or sim_version() or _DECLARED_PIN_VERSION,
        )

    def available(self) -> bool:
        return sim_version() is not None

    def predict(self, request: Any) -> ProviderPrediction:
        inputs = getattr(request, "inputs", None)
        if not isinstance(inputs, KernelInputs):
            raise ProviderUnmodeledError("missing_kernel_inputs")
        hardware = inputs.hardware
        if hardware is None:
            raise ProviderUnmodeledError("missing_hardware")
        workload = inputs.workload()
        if workload is None:
            missing = inputs.missing_inputs()
            raise ProviderUnmodeledError(
                "missing_workload:" + ",".join(missing) if missing else "missing_workload")
        flops, memory_bytes, source = workload
        compute_ms = (flops / float(hardware.peak_flops_per_s)) * 1000.0
        memory_ms = (memory_bytes / float(hardware.memory_bandwidth_bytes_per_s)) * 1000.0
        predicted_ms = max(compute_ms, memory_ms)
        if predicted_ms <= 0:
            raise ProviderUnmodeledError("non_positive_roofline_bound")
        signature = request.input_signature
        assumptions = (
            f"{IDEAL_BOUND_FORMULA_VERSION}: max(flops/peak, bytes/bandwidth) on "
            f"{hardware.name}; dtype={inputs.dtype}; op_kind={inputs.op_kind}; "
            f"workload={source}; no measured efficiency is applied."
        )
        evidence = (
            "provider:mindie_sim_clean_core_roofline",
            f"hardware:{hardware.name}",
            f"peak_flops_per_s:{hardware.peak_flops_per_s}",
            f"memory_bandwidth_bytes_per_s:{hardware.memory_bandwidth_bytes_per_s}",
            f"formula:{IDEAL_BOUND_FORMULA_VERSION}",
            f"workload:{source}",
        )
        return ProviderPrediction(
            predicted_ms=float(predicted_ms),
            model_assumptions=assumptions,
            input_signature=signature,
            evidence=evidence,
        )


def _slot_is_nd_descriptor(slot: Any, rank: int | None = None) -> bool:
    if getattr(slot, "state", None) != "descriptor" or getattr(slot, "layout", None) != "ND":
        return False
    shape = getattr(slot, "shape", None)
    return (
        isinstance(shape, tuple) and (rank is None or len(shape) == rank)
        and all(isinstance(value, int) and not isinstance(value, bool) and value > 0
                for value in shape)
    )


def _candidate_inputs(event: Any, sku: str) -> KernelInputs | None:
    if event.op_type not in _MATRIX_OP_TYPES:
        return None
    row = OperatorObservation.from_mapping({
        "kernel_name": event.name,
        "op_type": event.op_type,
        "input_shapes": event.input_shapes,
        "input_dtypes": event.input_dtypes,
        "input_formats": event.input_formats,
        "output_shapes": event.output_shapes,
        "output_dtypes": event.output_dtypes,
        "output_formats": event.output_formats,
    })
    slots = (*row.inputs, *row.outputs)
    if (
        len(row.inputs) != 2 or len(row.outputs) != 1
        or not all(_slot_is_nd_descriptor(slot, 2) for slot in slots)
    ):
        return None
    a, b, out = slots
    dtypes = {DTYPES.get(slot.dtype, slot.dtype) for slot in slots}
    m, k = a.shape
    out_m, n = out.shape
    if len(dtypes) != 1 or out_m != m or b.shape not in {(k, n), (n, k)}:
        return None
    dtype = next(iter(dtypes))
    if dtype not in {"bf16", "fp16", "fp32", "int8", "fp8_e4m3", "hif8", "fp4_e2m1"}:
        return None
    return KernelInputs(
        shape=(m, k, n), dtype=dtype, layout="ND",
        hardware=resolve_hardware_preset(sku, dtype=dtype),
        op_kind="matmul", kernel_name=event.name, rank=event.rank_index,
    )


def build_model_registry(
    observations: Iterable[Any], sku: str,
) -> dict[tuple[str, str, str], KernelInputs]:
    """Build the keyed ``(rank_id, block, kernel)`` registry from observations."""
    registry: dict[tuple[str, str, str], KernelInputs] = {}
    blocked: set[tuple[str, str, str]] = set()
    for observation in observations:
        for event in getattr(observation, "events", ()) or ():
            key = (event.rank_id, event.block, event.name)
            if key in blocked:
                continue
            try:
                candidate = _candidate_inputs(event, sku)
            except TimeoutError:
                raise
            except Exception:  # unresolved dtype/SKU is a concrete registry gap
                candidate = None
            previous = registry.get(key)
            if candidate is None or (
                previous is not None
                and previous.input_signature() != candidate.input_signature()
            ):
                registry.pop(key, None)
                blocked.add(key)
            else:
                registry[key] = candidate
    return registry


__all__ = [
    "PROVIDER_NAME", "MindieSimModelingProvider", "build_model_registry",
    "sim_version",
]
