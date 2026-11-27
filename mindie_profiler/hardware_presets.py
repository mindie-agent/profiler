"""Standalone Ascend hardware peaks and topology resolved from packaged presets.

[Role]
  Resolve a hardware alias or exact Ascend SKU into ``HardwareSpec`` peaks for
  one execution dtype, and expose the declared chip topology (AIC/AIV, dies,
  clock, L2, HBM, Cube/Vector rates) for ACLGraph region defaults and roofline
  bounds with zero ``mindie-sim`` dependency.

[Invariants]
  * All numeric SKU specifications live declaratively in
    ``mindie_profiler/knowledge/ascend_hardware_presets.json``.
  * Only compute peaks declared by the preset are exposed; unsupported dtypes
    or unknown SKUs raise ``ProfilerUsageError`` instead of fabricating peaks.
  * Importing this module performs no disk read and no device work; presets
    load lazily via ``@lru_cache``.
  * ``SUPPORTED_SKUS`` is materialized on first access.

[Timeouts & Locks]
  One bounded packaged JSON read on first lookup; no locks, subprocesses, or
  network access.

[Side-Effect Policy]
  Pure in-memory resolution; no filesystem writes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Mapping

from .events import ProfilerUsageError
from .modeling_inputs import HardwareSpec

#: Lossless dtype spelling aliases -> canonical operand dtype name.
_DTYPE_PEAK_KEYS = {
    "bf16": "bf16", "bfloat16": "bf16",
    "fp16": "fp16", "float16": "fp16", "half": "fp16",
    "fp32": "fp32", "float32": "fp32", "float": "fp32",
    "hf32": "hf32", "int8": "int8", "uint8": "int8",
    "fp8": "fp8_e4m3", "fp8_e4m3": "fp8_e4m3", "fp8_e4m3fn": "fp8_e4m3",
    "float8_e4m3fn": "fp8_e4m3", "mxfp8": "fp8_e4m3", "w8a8_mxfp8": "fp8_e4m3",
    "fp8_e5m2": "fp8_e5m2", "float8_e5m2": "fp8_e5m2",
    "hif8": "hif8", "hifloat8": "hif8",
    "fp4": "fp4_e2m1", "fp4_e2m1": "fp4_e2m1", "float4_e2m1": "fp4_e2m1",
    "mxfp4": "fp4_e2m1", "w4a8_mxfp4": "fp4_e2m1",
    "int4": "int4", "uint4": "int4", "w4a4": "int4",
}
#: One TFLOPS expressed in FLOPS; unit tokens stay explicit for numeric hygiene.
FLOPS_PER_TFLOPS = 1000000000 * 1000
_PRESETS_PATH = Path(__file__).resolve().parent / "knowledge" / "ascend_hardware_presets.json"


@lru_cache(maxsize=1)
def _preset_payload() -> Mapping[str, Any]:
    return json.loads(_PRESETS_PATH.read_text(encoding="utf-8"))


def _profiles() -> Mapping[str, Mapping[str, Any]]:
    return _preset_payload()["skus"]


def hardware_aliases() -> Mapping[str, str]:
    """Return canonical lowercase hardware alias -> SKU mapping."""
    return _preset_payload()["aliases"]


def hardware_topology_aliases() -> Mapping[str, tuple[str, str]]:
    """Return canonical lowercase topology alias -> ``(sku, preset)`` mapping."""
    return {
        str(alias): (str(pair[0]), str(pair[1]))
        for alias, pair in _preset_payload()["topology_aliases"].items()
    }


def supported_hardware_skus() -> tuple[str, ...]:
    """Exact declared Ascend SKU tuple from packaged presets."""
    return tuple(sorted(_profiles()))


def __getattr__(name: str) -> Any:
    """Materialize ``SUPPORTED_SKUS`` on first access."""
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
    source: str = "mindie_profiler.knowledge.ascend_hardware_presets"
    assumptions: tuple[str, ...] = ()


def _topology_from_profile(sku: str, profile: Mapping[str, Any]) -> ChipTopologySpec:
    peaks = {
        str(k): float(v)
        for k, v in (profile.get("compute_peaks") or {}).items()
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0
    }
    return ChipTopologySpec(
        sku=sku,
        arch=str(profile.get("architecture") or "unknown"),
        aic_cores=int(profile.get("aic_cores") or 0),
        aiv_cores=int(profile.get("aiv_cores") or 0),
        dies_per_package=int(profile.get("dies_per_package") or 1),
        clock_mhz=float(profile.get("clock_mhz") or 0.0),
        l2_bytes_per_die=int(profile.get("l2_bytes_per_die") or 0),
        hbm_gbps=float(profile.get("hbm_bytes_per_s") or 0.0) / 1000000000,
        cube_tflops_by_dtype={k: v / FLOPS_PER_TFLOPS for k, v in peaks.items()},
        vector_tflops_bf16=float(profile.get("vector_ops_per_s") or 0.0) / FLOPS_PER_TFLOPS,
        assumptions=(),
    )


def resolve_hardware_sku(sku_or_alias: str) -> str:
    """Resolve one alias/SKU to an exact declared Ascend profile name."""
    if not isinstance(sku_or_alias, str) or not sku_or_alias.strip():
        raise ProfilerUsageError(
            "hardware SKU is required (a2, a3, a5, or an exact Ascend SKU)")
    raw = sku_or_alias.strip()
    profs = _profiles()
    if raw in profs:
        return raw
    low = raw.lower()
    aliases = hardware_aliases()
    if low in aliases:
        return aliases[low]
    folded = low.replace("_", "-")
    if folded in aliases:
        return aliases[folded]
    underscored = low.replace("-", "_")
    if underscored in aliases:
        return aliases[underscored]
    by_lower = {sku.lower(): sku for sku in profs}
    for cand in (low, f"ascend{low}", underscored, f"ascend{underscored}"):
        if cand in by_lower:
            return by_lower[cand]
    raise ProfilerUsageError(
        f"unsupported or unrecognized hardware: {sku_or_alias}; "
        f"supported={','.join(supported_hardware_skus())}")


def resolve_chip_topology(sku_or_alias: str) -> ChipTopologySpec:
    """Return AIC/AIV/die/clock/L2/HBM/Vector topology for one declared SKU."""
    sku = resolve_hardware_sku(sku_or_alias)
    return _topology_from_profile(sku, _profiles()[sku])


def efficiency_tolerances() -> tuple[float, float]:
    """Return declarative ``(cube_sum_rel_tol, cube_sum_abs_tol)`` from packaged presets."""
    tol = _preset_payload().get("efficiency_tolerances") or {}
    return float(tol["cube_sum_rel_tol"]), float(tol["cube_sum_abs_tol"])


def resolve_hardware_peaks(sku_or_alias: str) -> dict[str, Any]:
    """Return declared SI compute/vector/HBM peaks for subgraph efficiency math."""
    sku = resolve_hardware_sku(sku_or_alias)
    profile = _profiles()[sku]
    return {
        "compute_peaks": {str(k): float(v) for k, v in (profile.get("compute_peaks") or {}).items()},
        "vector_peak_ops_per_s": float(profile.get("vector_ops_per_s") or 0.0),
        "hbm_peak_bytes_per_s": float(profile.get("hbm_bytes_per_s") or 0.0),
    }


def resolve_hardware_preset(sku_or_alias: str, *, dtype: str = "bf16") -> HardwareSpec:
    """Return the compute/HBM peaks for one SKU and one execution dtype."""
    sku = resolve_hardware_sku(sku_or_alias)
    profile = _profiles()[sku]
    folded = str(dtype or "bf16").strip().lower().replace("-", "_")
    key = _DTYPE_PEAK_KEYS.get(folded, folded)
    peaks = profile.get("compute_peaks") or {}
    if key not in peaks:
        raise ProfilerUsageError(
            f"hardware_compute_dtype_unsupported:{sku}:{dtype}:missing_peak:{key}")
    return HardwareSpec(
        name=sku,
        peak_flops_per_s=float(peaks[key]),
        memory_bandwidth_bytes_per_s=float(profile["hbm_bytes_per_s"]),
    )
