"""Out-of-the-box Ascend hardware peaks for the ideal Roofline bound.

[Role]
  Resolve a name-free hardware alias (``a2``/``a3``/``a5``/``dav_3510``) or an
  exact SKU into ``HardwareSpec`` peaks for one execution dtype and expose the
  independent chip topology (AIC/AIV, dies, clock, L2, HBM, Cube/Vector rates).
[Invariants]
  * Only the 15 SKUs declared by ``mindie_sim.backends.ascend.profiles()`` are
    resolvable; no synthetic SKU or alias may supply missing hardware math.
  * A dtype without a declared profile peak is derived from the documented
    doubling (fp8 = 2x bf16, fp4 = 2x fp8) and records that derivation; it is
    never silently reported as a measured peak.
  * Importing this module never initializes a device context or loads torch_npu.
[Timeouts & Locks]
  One bounded JSON profile read (when ``mindie_sim`` is installed) or an
  in-memory static mirror; no locks, subprocesses or network access.
[Side-Effect Policy]
  Pure in-memory resolution; no filesystem writes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .events import ProfilerUsageError
from .modeling_inputs import HardwareSpec

_ARCH_ALIASES = {
    "a2": "Ascend910B4", "910b": "Ascend910B4", "dav_2201": "Ascend910B4",
    "a3": "Ascend910_9392", "910c": "Ascend910_9392", "dav_2202": "Ascend910_9392",
    "a5": "Ascend950DT_9582", "950": "Ascend950DT_9582",
    "950dt": "Ascend950DT_9582", "950pr": "Ascend950PR_9579",
    "dav_3510": "Ascend950DT_9582", "arch35": "Ascend950DT_9582",
    "arch3510": "Ascend950DT_9582",
}

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

# Static mirror of the 15 public ``ascend.json`` profiles: (arch, aic, aiv,
# dies, clock_mhz, l2_bytes, hbm_bytes_s, vector_ops_s, peaks).
_STATIC: dict[str, tuple[Any, ...]] = {
    "Ascend910B1": ("A2", 24, 48, 1, 1850.0, 201326592, 1.8e12, 2.8416e12,
                    {"bf16": 3.637248e14, "fp16": 3.637248e14, "fp32": 9.09312e13,
                     "hf32": 1.818624e14, "int8": 7.274496e14, "int4": 1.4548992e15}),
    "Ascend910B2": ("A2", 24, 48, 1, 1800.0, 201326592, 1.8e12, 2.7648e12,
                    {"bf16": 3.538944e14, "fp16": 3.538944e14, "fp32": 8.84736e13,
                     "hf32": 1.769472e14, "int8": 7.077888e14, "int4": 1.4155776e15}),
    "Ascend910B2C": ("A2", 24, 48, 1, 1800.0, 201326592, 1.8e12, 2.7648e12,
                     {"bf16": 3.538944e14, "fp16": 3.538944e14, "fp32": 8.84736e13,
                      "hf32": 1.769472e14, "int8": 7.077888e14, "int4": 1.4155776e15}),
    "Ascend910B3": ("A2", 20, 40, 1, 1800.0, 201326592, 1.6e12, 2.304e12,
                    {"bf16": 2.94912e14, "fp16": 2.94912e14, "fp32": 7.3728e13,
                     "hf32": 1.47456e14, "int8": 5.89824e14, "int4": 1.179648e15}),
    "Ascend910B4": ("A2", 20, 40, 1, 1500.0, 100663296, 8.0e11, 1.92e12,
                    {"bf16": 2.4576e14, "fp16": 2.4576e14, "fp32": 6.144e13,
                     "hf32": 1.2288e14, "int8": 4.9152e14, "int4": 9.8304e14}),
    "Ascend910B4-1": ("A2", 20, 40, 1, 1650.0, 100663296, 1.2e12, 2.112e12,
                      {"bf16": 2.70336e14, "fp16": 2.70336e14, "fp32": 6.7584e13,
                       "hf32": 1.35168e14, "int8": 5.40672e14, "int4": 1.081344e15}),
    "Ascend910_9362": ("A3", 20, 40, 2, 1650.0, 176160768, 1.2e12, 2.112e12,
                       {"bf16": 2.70336e14, "fp16": 2.70336e14, "fp32": 6.7584e13,
                        "hf32": 1.35168e14, "int8": 5.40672e14, "int4": 1.081344e15}),
    "Ascend910_9372": ("A3", 20, 40, 2, 1650.0, 201326592, 1.4e12, 2.112e12,
                       {"bf16": 2.70336e14, "fp16": 2.70336e14, "fp32": 6.7584e13,
                        "hf32": 1.35168e14, "int8": 5.40672e14, "int4": 1.081344e15}),
    "Ascend910_9381": ("A3", 20, 40, 2, 1800.0, 201326592, 1.6e12, 2.304e12,
                       {"bf16": 2.94912e14, "fp16": 2.94912e14, "fp32": 7.3728e13,
                        "hf32": 1.47456e14, "int8": 5.89824e14, "int4": 1.179648e15}),
    "Ascend910_9382": ("A3", 20, 40, 2, 1650.0, 201326592, 1.6e12, 2.112e12,
                       {"bf16": 2.70336e14, "fp16": 2.70336e14, "fp32": 6.7584e13,
                        "hf32": 1.35168e14, "int8": 5.40672e14, "int4": 1.081344e15}),
    "Ascend910_9391": ("A3", 24, 48, 2, 1850.0, 201326592, 1.6e12, 2.8416e12,
                       {"bf16": 3.637248e14, "fp16": 3.637248e14, "fp32": 9.09312e13,
                        "hf32": 1.818624e14, "int8": 7.274496e14, "int4": 1.4548992e15}),
    "Ascend910_9392": ("A3", 24, 48, 2, 1800.0, 201326592, 1.6e12, 2.7648e12,
                       {"bf16": 3.538944e14, "fp16": 3.538944e14, "fp32": 8.84736e13,
                        "hf32": 1.769472e14, "int8": 7.077888e14, "int4": 1.4155776e15}),
    "Ascend950DT_9581": ("A5", 32, 64, 1, 1650.0, 134217728, 4.0e12, 6.7584e12,
                         {"bf16": 4.325376e14, "fp16": 4.325376e14, "fp32": 2.70336e13,
                          "hf32": 2.162688e14, "int8": 8.650752e14,
                          "fp8_e4m3": 8.650752e14, "fp8_e5m2": 8.650752e14}),
    "Ascend950DT_9582": ("A5", 32, 64, 1, 1650.0, 134217728, 4.0e12, 6.7584e12,
                         {"bf16": 4.325376e14, "fp16": 4.325376e14, "fp32": 2.70336e13,
                          "hf32": 2.162688e14, "int8": 8.650752e14,
                          "fp8_e4m3": 8.650752e14, "fp8_e5m2": 8.650752e14}),
    "Ascend950PR_9579": ("A5", 32, 64, 1, 1650.0, 134217728, 1.6e12, 6.7584e12,
                         {"bf16": 4.325376e14, "fp16": 4.325376e14, "fp32": 2.70336e13,
                          "hf32": 2.162688e14, "int8": 8.650752e14,
                          "fp8_e4m3": 8.650752e14, "fp8_e5m2": 8.650752e14}),
}
SUPPORTED_SKUS = tuple(sorted(_STATIC))


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
    source: str = "static_mirror"
    assumptions: tuple[str, ...] = ()


def _profiles() -> Mapping[str, Any] | None:
    try:
        from mindie_sim.backends.ascend import profiles
    except ImportError:
        return None
    try:
        return profiles()
    except TimeoutError:
        raise
    except Exception:  # installed but unreadable: static mirror stays authoritative
        return None


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
    fp8 = peaks.get("fp8_e4m3") or 2.0 * bf16
    fp4 = peaks.get("int4") or 2.0 * fp8
    cube = {**peaks, "fp8_e4m3": fp8, "fp8_e5m2": peaks.get("fp8_e5m2") or fp8,
            "hif8": fp8, "int4": fp4, "fp4_e2m1": fp4}
    return ChipTopologySpec(
        sku=sku,
        arch=str(profile.get("architecture") or "unknown"),
        aic_cores=int(device.get("compute_units") or 0),
        aiv_cores=int((device.get("resource_units") or {}).get("vector") or 0),
        dies_per_package=int(profile.get("dies_per_package") or 1),
        clock_mhz=_clock_mhz(profile),
        l2_bytes_per_die=int((device.get("buffers") or {}).get("l2") or 0),
        hbm_gbps=float((device.get("rates") or {}).get("hbm") or 0.0) / 1e9,
        cube_tflops_by_dtype={k: v / 1e12 for k, v in cube.items()},
        vector_tflops_bf16=float((device.get("rates") or {}).get("vector") or 0.0) / 1e12,
        source="mindie_sim.backends.ascend.profiles",
        assumptions=(),
    )


def _static_topology(sku: str) -> ChipTopologySpec:
    arch, aic, aiv, dies, clock, l2, hbm, vector, peaks = _STATIC[sku]
    bf16 = peaks.get("bf16") or 0.0
    fp8 = peaks.get("fp8_e4m3") or 2.0 * bf16
    fp4 = peaks.get("int4") or 2.0 * fp8
    cube = {**peaks, "fp8_e4m3": fp8, "fp8_e5m2": peaks.get("fp8_e5m2") or fp8,
            "hif8": fp8, "int4": fp4, "fp4_e2m1": fp4}
    return ChipTopologySpec(
        sku=sku, arch=arch, aic_cores=aic, aiv_cores=aiv, dies_per_package=dies,
        clock_mhz=clock, l2_bytes_per_die=l2, hbm_gbps=hbm / 1e9,
        cube_tflops_by_dtype={k: v / 1e12 for k, v in cube.items()},
        vector_tflops_bf16=vector / 1e12, source="static_mirror",
        assumptions=(
            "static mirror of the 15 public ascend.json profiles",
            "fp8 derived as 2x bf16 when the profile declares no fp8 peak",
            "fp4 derived as 2x fp8 (or the declared int4 peak)",
        ),
    )


def resolve_hardware_sku(sku_or_alias: str) -> str:
    """Resolve one alias/SKU to an exact declared 15-SKU profile name."""
    if not isinstance(sku_or_alias, str) or not sku_or_alias.strip():
        raise ProfilerUsageError("hardware SKU is required (a2, a3, a5, or an exact Ascend SKU)")
    raw = sku_or_alias.strip()
    folded = raw.lower()
    if folded in _ARCH_ALIASES:
        return _ARCH_ALIASES[folded]
    for sku in SUPPORTED_SKUS:
        if sku.lower() == folded:
            return sku
    try:
        from mindie_sim.compose import resolve_hardware_sku as sim_resolve
    except ImportError:
        sim_resolve = None
    try:
        resolved = sim_resolve(raw) if sim_resolve is not None else raw
    except TimeoutError:
        raise
    except Exception as exc:
        raise ProfilerUsageError(
            f"unsupported or unrecognized hardware: {sku_or_alias}; "
            f"supported={','.join(SUPPORTED_SKUS)}") from exc
    if resolved not in _STATIC:
        raise ProfilerUsageError(f"hardware SKU has no declared ascend profile: {resolved}")
    return resolved


def resolve_chip_topology(sku_or_alias: str) -> ChipTopologySpec:
    """Return AIC/AIV/dead/clock/L2/HBM/Vector topology for one declared SKU."""
    sku = resolve_hardware_sku(sku_or_alias)
    profiles = _profiles()
    if profiles and sku in profiles:
        return _topology_from_profile(sku, profiles[sku])
    return _static_topology(sku)


def resolve_hardware_preset(sku_or_alias: str, *, dtype: str = "bf16") -> HardwareSpec:
    """Return the compute/HBM peaks for one SKU and one execution dtype."""
    topology = resolve_chip_topology(sku_or_alias)
    folded = str(dtype or "bf16").strip().lower().replace("-", "_")
    key = _DTYPE_PEAK_KEYS.get(folded)
    if key is None:
        raise ProfilerUsageError(
            f"unsupported modeling dtype: {dtype}; supported={','.join(sorted(_DTYPE_PEAK_KEYS))}")
    peak = topology.cube_tflops_by_dtype.get(key)
    if peak is None or peak <= 0:
        peak = topology.cube_tflops_by_dtype.get("bf16") or 0.0
    if peak <= 0 or topology.hbm_gbps <= 0:
        raise ProfilerUsageError(f"hardware profile has no positive peak: {topology.sku}")
    return HardwareSpec(
        name=topology.sku,
        peak_flops_per_s=float(peak) * 1e12,
        memory_bandwidth_bytes_per_s=float(topology.hbm_gbps) * 1e9,
    )
