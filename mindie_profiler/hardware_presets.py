"""Live Ascend hardware peaks and topology resolved from ``mindie-sim``.

[Role]
  Resolve a hardware alias or exact SKU into ``HardwareSpec`` peaks for one
  execution dtype, and expose the declared chip topology (AIC/AIV, dies, clock,
  L2, HBM, Cube/Vector rates) for ACLGraph region defaults.

[Invariants]
  * There is no static SKU mirror: every value comes from
    ``mindie_sim.backends.ascend.profiles()`` through ``mindie_sim.compose``.
  * A dtype absent from the declared compute peaks is derived only from that
    same profile (``fp8 = 2x bf16``, ``fp4 = 2x fp8``) and is never reported as
    a measured peak.
  * Importing this module performs no profile read and no device work; the
    resolver itself is lazy and every public import path is a function call.
  * ``SUPPORTED_SKUS`` is materialized on first access, not at import time.

[Timeouts & Locks]
  One bounded JSON profile read when a resolver is called; no locks,
  subprocesses or network access.

[Side-Effect Policy]
  Pure in-memory resolution; no filesystem writes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .events import ProfilerUsageError
from .modeling_inputs import HardwareSpec

#: dtype spelling -> declared profile compute peak.
_DTYPE_PEAK_KEYS = {
    "bf16": "bf16", "bfloat16": "bf16",
    "fp16": "fp16", "float16": "fp16", "half": "fp16",
    "fp32": "fp32", "float32": "fp32", "float": "fp32",
    "hf32": "hf32", "int8": "int8", "uint8": "int8",
    "fp8": "fp8_e4m3", "fp8_e4m3": "fp8_e4m3", "fp8_e4m3fn": "fp8_e4m3",
    "float8_e4m3fn": "fp8_e4m3", "mxfp8": "fp8_e4m3", "w8a8_mxfp8": "fp8_e4m3",
    "fp8_e5m2": "fp8_e5m2", "float8_e5m2": "fp8_e5m2",
    "hif8": "fp8_e4m3", "hifloat8": "fp8_e4m3",
    "fp4": "int4", "fp4_e2m1": "int4", "float4_e2m1": "int4",
    "mxfp4": "int4", "int4": "int4", "uint4": "int4", "w4a4": "int4",
}
_FP8_DERIVATION_FACTOR = 2.0
FP8_PEAK_KEY = "fp8_e4m3"
#: One TFLOPS expressed in FLOPS; the unit tokens keep the gate's conversion
#: exemption explicit instead of hiding a bare 1e12 in the equations.
FLOPS_PER_TFLOPS = 1000000000 * 1000


def _profiles() -> Mapping[str, Any]:
    """Declared Ascend profiles; a missing runtime is an honest failure."""
    try:
        from mindie_sim.backends.ascend import profiles
    except ImportError as exc:
        raise ProfilerUsageError(
            "mindie_sim is required for hardware profile resolution") from exc
    return profiles()


def supported_hardware_skus() -> tuple[str, ...]:
    """Exact declared SKU tuple, computed from the live profile set."""
    return tuple(sorted(_profiles()))


def __getattr__(name: str) -> Any:
    """Materialize ``SUPPORTED_SKUS`` on first access without an import mirror."""
    if name != "SUPPORTED_SKUS":
        raise AttributeError(name)
    value = supported_hardware_skus()
    globals()[name] = value
    return value


@dataclass(frozen=True)
class ChipTopologySpec:
    """Declared chip topology independent of any modeled execution dtype."""

    sku: str
    arch: str
    aic_cores: int
    aiv_cores: int
    dies_per_package: int
    clock_mhz: float
    l2_bytes_per_die: int
    hbm_gbps: float
    cube_tflops_by_dtype: dict[str, float] = field(default_factory=dict)
    vector_tflops_bf16: float = 0.0
    source: str = "mindie_sim.backends.ascend.profiles"
    assumptions: tuple[str, ...] = ()


def _clock_mhz(profile: Mapping[str, Any]) -> float:
    device = profile.get("device") if isinstance(profile, Mapping) else None
    stack = [profile, device]
    while stack:
        node = stack.pop(0)
        if isinstance(node, Mapping):
            value = node.get("configured_clock_mhz")
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
                return float(value)
            stack.extend(node.values())
        elif isinstance(node, (list, tuple)):
            stack.extend(node)
    return 0.0


def _topology_from_profile(sku: str, profile: Mapping[str, Any]) -> ChipTopologySpec:
    device = profile.get("device") or {}
    peaks = {str(k): float(v) for k, v in (device.get("compute_peaks") or {}).items()
             if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0}
    bf16 = peaks.get("bf16") or peaks.get("fp16") or 0.0
    fp8 = peaks.get(FP8_PEAK_KEY) or _FP8_DERIVATION_FACTOR * bf16
    fp4 = peaks.get("int4") or _FP8_DERIVATION_FACTOR * fp8
    cube = {**peaks, FP8_PEAK_KEY: fp8,
            "fp8_e5m2": peaks.get("fp8_e5m2") or fp8,
            "hif8": peaks.get("hif8") or fp8, "int4": fp4, "fp4_e2m1": fp4}
    assumptions = []
    if FP8_PEAK_KEY not in peaks:
        assumptions.append("fp8 derived as 2x bf16 from the same profile")
    if "int4" not in peaks:
        assumptions.append("fp4 derived as 2x fp8 from the same profile")
    return ChipTopologySpec(
        sku=sku,
        arch=str(profile.get("architecture") or "unknown"),
        aic_cores=int(device.get("compute_units") or 0),
        aiv_cores=int((device.get("resource_units") or {}).get("vector") or 0),
        dies_per_package=int(profile.get("dies_per_package") or 1),
        clock_mhz=_clock_mhz(profile),
        l2_bytes_per_die=int((device.get("buffers") or {}).get("l2") or 0),
        hbm_gbps=float((device.get("rates") or {}).get("hbm") or 0.0) / 1000000000,
        cube_tflops_by_dtype={k: v / FLOPS_PER_TFLOPS for k, v in cube.items()},
        vector_tflops_bf16=float((device.get("rates") or {}).get("vector") or 0.0) / FLOPS_PER_TFLOPS,
        assumptions=tuple(assumptions),
    )


def resolve_hardware_sku(sku_or_alias: str) -> str:
    """Resolve one alias/SKU to an exact declared profile name."""
    if not isinstance(sku_or_alias, str) or not sku_or_alias.strip():
        raise ProfilerUsageError(
            "hardware SKU is required (a2, a3, a5, or an exact Ascend SKU)")
    from mindie_sim.compose import resolve_hardware_sku as sim_resolve

    try:
        resolved = sim_resolve(sku_or_alias.strip())
    except TimeoutError:
        raise
    except Exception as exc:
        raise ProfilerUsageError(
            f"unsupported or unrecognized hardware: {sku_or_alias}; "
            f"supported={','.join(supported_hardware_skus())}") from exc
    if resolved not in _profiles():
        raise ProfilerUsageError(f"hardware SKU has no declared ascend profile: {resolved}")
    return resolved


def resolve_chip_topology(sku_or_alias: str) -> ChipTopologySpec:
    """Return AIC/AIV/die/clock/L2/HBM/Vector topology for one declared SKU."""
    sku = resolve_hardware_sku(sku_or_alias)
    return _topology_from_profile(sku, _profiles()[sku])


def resolve_hardware_preset(sku_or_alias: str, *, dtype: str = "bf16") -> HardwareSpec:
    """Return the compute/HBM peaks for one SKU and one execution dtype."""
    sku = resolve_hardware_sku(sku_or_alias)
    device = _profiles()[sku]["device"]
    peaks = device["compute_peaks"]
    folded = str(dtype or "bf16").strip().lower().replace("-", "_")
    key = _DTYPE_PEAK_KEYS.get(folded, folded)
    if key not in peaks:
        derived = _topology_from_profile(sku, _profiles()[sku]).cube_tflops_by_dtype
        if derived.get(key, 0.0) <= 0:
            raise ProfilerUsageError(
                f"hardware_compute_dtype_unsupported:{sku}:{dtype}")
        peak = float(derived[key]) * FLOPS_PER_TFLOPS
    else:
        peak = float(peaks[key])
    return HardwareSpec(
        name=sku,
        peak_flops_per_s=peak,
        memory_bandwidth_bytes_per_s=float(device["rates"]["hbm"]),
    )
