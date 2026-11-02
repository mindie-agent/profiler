"""P2 framework-log memory fact parsing.

[Role]
  Extract documented vLLM/Ascend startup-log memory facts for P2 attribution,
  preserving the log's explicit GB/GiB units and Available-vs-Current KV
  semantics.

[Invariants]
  * Available KV cache memory is a budget; Current KV cache memory is the
    actual allocation and is parsed separately.
  * GB is decimal 1e9 and GiB is binary 1024^3; units are never guessed from
    magnitude.
  * Only explicit log facts become values; missing lines stay absent.
  * Raw matched text and source lines are retained for precision/audit.

[Timeouts & Locks]
  Pure string parsing over supplied bounded log text.

[Side-Effect Policy]
  No I/O or mutation.
"""

from __future__ import annotations

import re
from typing import Any, Mapping
from .memory_units import _is_number, to_bytes

_WEIGHT_RE = re.compile(r"Loading model weights took\s+([\d.]+)\s*(GB|GiB)")
_KV_AVAIL_RE = re.compile(r"Available KV cache memory:\s+([\d.]+)\s*(GB|GiB)")
_KV_CURRENT_RE = re.compile(r"Current KV cache memory:\s+([\d.]+)\s*(GB|GiB)")
_KV_TOKENS_RE = re.compile(r"(?:GPU|NPU) KV cache size:\s+([\d,]+)\s*tokens")
_GRAPH_RE = re.compile(r"Graph capturing finished in\s+(\d+)\s*secs,\s*took\s+([\d.]+)\s*(GB|GiB)")
_GPU_UTIL_RE = re.compile(r"gpu_memory_utilization['\"]?\s*[:=]\s*([\d.]+)")
_STARTUP_RE = re.compile(r"Free memory on device\s*\(([\d.]+)/([\d.]+)\s*(GB|GiB)\)")
_DESIRED_RE = re.compile(r"Desired GPU memory utilization is\s*\(([\d.]+),\s*([\d.]+)\s*(GB|GiB)\)")
_USAGE_RE = re.compile(
    r"Actual usage:\s*([\d.]+)\s*(GB|GiB) for weights,\s*"
    r"([\d.]+)\s*(GB|GiB) for peak activation,\s*"
    r"([\d.]+)\s*(GB|GiB) for non-torch memory,\s*"
    r"([\d.]+)\s*(GB|GiB) for NPU graph memory"
)
_KV_MEMORY_RE = re.compile(r"--kv-cache-memory=(\d+)`?\s*\(([\d.]+)\s*(GB|GiB)\)")
_WARMUP_RE = re.compile(
    r"After warmup: torch reserved memory\s+([\d.]+)\s*(GB|GiB),\s*"
    r"torch allocated memory\s+([\d.]+)\s*(GB|GiB)"
)
_XTENSOR_PAGES_RE = re.compile(
    r"shared_vmm_allocator:\s*allocated_pages=(\d+),\s*high_watermark_pages=(\d+),\s*"
    r"total_pages=(\d+)(?:,\s*page_size=(\d+))?"
)
_XTENSOR_KV_RE = re.compile(
    r"xTensor\s+KV\s+cache:\s*used=([\d.]+)\s*(GB|GiB),\s*peak=([\d.]+)\s*(GB|GiB)"
    r"(?:,\s*reserved=([\d.]+)\s*(GB|GiB))?"
)
_PROFILE_MANAGER_STEP_RE = re.compile(
    r"ProfileManager:\s*step=(\d+)"
    r"(?:\s+mode=([A-Za-z0-9_-]+))?"
    r"(?:\s+batch_size=(\d+))?"
    r"(?:\s+token_latency_ms=([\d.]+))?"
    r"\s+step_latency_ms=([\d.]+)"
)
_DIT_CACHE_RE = re.compile(
    r"(?:DiTCache|Cache-DiT|TaylorSeer|TeaCache):\s*total_steps=(\d+),\s*"
    r"computed_steps=(\d+),\s*cached_steps=(\d+)(?:,\s*(?:hit_rate|cache_hit_ratio)=([\d.]+))?",
    re.IGNORECASE,
)
_VAE_PEAK_RE = re.compile(
    r"(?:VAE\s+Peak\s+Memory:\s*([\d.]+)\s*(GB|GiB|MB|MiB)|"
    r"vae_peak_mb=([\d.]+)(?:,\s*vae_tiles=(\d+))?)",
    re.IGNORECASE,
)
_MINDIE_SD_MEM_RE = re.compile(
    r"MindIE-SD\s+NPU\s+Memory:\s*allocated=([\d.]+)\s*(GB|GiB|MB|MiB),\s*"
    r"reserved=([\d.]+)\s*(GB|GiB|MB|MiB)",
    re.IGNORECASE,
)


def _suffix(unit: str) -> str:
    return "gib" if unit == "GiB" else "gb"


def _set(info: dict[str, Any], key: str, value: float, unit: str, raw: str) -> None:
    info[key] = value
    info.setdefault("units", {})[key] = unit
    info.setdefault("raw", {})[key] = f"{raw} {unit}"


def parse_vllm_logs(log_text: str) -> dict[str, Any]:
    """Extract explicit P2 memory facts, preserving units and raw text."""
    info: dict[str, Any] = {}
    graphs: list[tuple[float, str]] = []
    source_lines: list[str] = []

    def note(line: str) -> None:
        stripped = line.strip()
        if stripped and stripped not in source_lines:
            source_lines.append(stripped)

    for line in str(log_text).splitlines():
        match = _WEIGHT_RE.search(line)
        if match:
            unit = match.group(2)
            _set(info, f"weights_{_suffix(unit)}", float(match.group(1)), unit, match.group(1))
            info["weights_unit"] = unit
            note(line)
        match = _KV_AVAIL_RE.search(line)
        if match:
            unit = match.group(2)
            _set(info, f"kv_cache_available_{_suffix(unit)}", float(match.group(1)), unit, match.group(1))
            info["kv_cache_available_is_budget"] = True
            note(line)
        match = _KV_CURRENT_RE.search(line)
        if match:
            unit = match.group(2)
            _set(info, f"kv_cache_current_{_suffix(unit)}", float(match.group(1)), unit, match.group(1))
            info["kv_cache_current_is_actual"] = True
            note(line)
        match = _KV_TOKENS_RE.search(line)
        if match:
            info["kv_cache_tokens"] = int(match.group(1).replace(",", ""))
            note(line)
        match = _GRAPH_RE.search(line)
        if match:
            graphs.append((float(match.group(2)), match.group(3)))
            note(line)
        match = _GPU_UTIL_RE.search(line)
        if match:
            info["gpu_memory_utilization"] = float(match.group(1))
            note(line)
        match = _STARTUP_RE.search(line)
        if match:
            unit = match.group(3)
            suffix = _suffix(unit)
            _set(info, f"startup_free_{suffix}", float(match.group(1)), unit, match.group(1))
            _set(info, f"startup_total_{suffix}", float(match.group(2)), unit, match.group(2))
            note(line)
        match = _DESIRED_RE.search(line)
        if match:
            info["desired_gpu_memory_utilization"] = float(match.group(1))
            unit = match.group(3)
            _set(info, f"desired_budget_{_suffix(unit)}", float(match.group(2)), unit, match.group(2))
            note(line)
        match = _USAGE_RE.search(line)
        if match:
            unit_1, unit_2, unit_3, unit_4 = match.group(2), match.group(4), match.group(6), match.group(8)
            if unit_1 == unit_2 == unit_3 == unit_4:
                suffix = _suffix(unit_1)
                _set(info, f"weights_usage_{suffix}", float(match.group(1)), unit_1, match.group(1))
                _set(info, f"peak_activation_{suffix}", float(match.group(3)), unit_2, match.group(3))
                _set(info, f"non_torch_memory_{suffix}", float(match.group(5)), unit_3, match.group(5))
                _set(info, f"npu_graph_memory_{suffix}", float(match.group(7)), unit_4, match.group(7))
            note(line)
        for match in _KV_MEMORY_RE.finditer(line):
            info.setdefault("kv_cache_memory_recommendations", []).append({
                "bytes": int(match.group(1)),
                "value": float(match.group(2)),
                "unit": match.group(3),
            })
            note(line)
        match = _WARMUP_RE.search(line)
        if match:
            unit_1, unit_2 = match.group(2), match.group(4)
            _set(info, f"torch_reserved_{_suffix(unit_1)}", float(match.group(1)), unit_1, match.group(1))
            _set(info, f"torch_allocated_{_suffix(unit_2)}", float(match.group(3)), unit_2, match.group(3))
            note(line)
        match = _XTENSOR_PAGES_RE.search(line)
        if match:
            info["xtensor_allocated_pages"] = int(match.group(1))
            info["xtensor_high_watermark_pages"] = int(match.group(2))
            info["xtensor_total_pages"] = int(match.group(3))
            if match.group(4) is not None:
                page_bytes = int(match.group(4))
                info["xtensor_page_size_bytes"] = page_bytes
                info["xtensor_high_watermark_bytes"] = info["xtensor_high_watermark_pages"] * page_bytes
            note(line)
        match = _XTENSOR_KV_RE.search(line)
        if match:
            used_val, used_unit = float(match.group(1)), match.group(2)
            peak_val, peak_unit = float(match.group(3)), match.group(4)
            _set(info, f"xtensor_kv_used_{_suffix(used_unit)}", used_val, used_unit, match.group(1))
            _set(info, f"xtensor_kv_peak_{_suffix(peak_unit)}", peak_val, peak_unit, match.group(3))
            if match.group(5) is not None and match.group(6) is not None:
                res_val, res_unit = float(match.group(5)), match.group(6)
                _set(info, f"xtensor_kv_reserved_{_suffix(res_unit)}", res_val, res_unit, match.group(5))
            note(line)
        match = _PROFILE_MANAGER_STEP_RE.search(line)
        if match:
            step_entry: dict[str, Any] = {
                "step": int(match.group(1)),
                "mode": match.group(2),
                "batch_size": int(match.group(3)) if match.group(3) is not None else None,
                "token_latency_ms": float(match.group(4)) if match.group(4) is not None else None,
                "step_latency_ms": float(match.group(5)),
            }
            info.setdefault("profile_manager_steps", []).append(step_entry)
            note(line)

    pm_steps = info.get("profile_manager_steps")
    if isinstance(pm_steps, list) and pm_steps:
        latencies = [float(item["step_latency_ms"]) for item in pm_steps]
        info["profile_manager_step_count"] = len(latencies)
        info["profile_manager_mean_step_latency_ms"] = sum(latencies) / len(latencies)
        info["profile_manager_max_step_latency_ms"] = max(latencies)

    if graphs:
        max_value, max_unit = max(graphs, key=lambda item: item[0])
        _set(info, f"graph_capture_{_suffix(max_unit)}", max_value, max_unit, str(max_value))
        info["graph_capture_count"] = len(graphs)
    recommendations = info.get("kv_cache_memory_recommendations")
    if isinstance(recommendations, list) and recommendations:
        info["kv_cache_memory_fit_bytes"] = recommendations[0]["bytes"]
        info["kv_cache_memory_fit_value"] = recommendations[0]["value"]
        info["kv_cache_memory_fit_unit"] = recommendations[0]["unit"]
        if len(recommendations) > 1:
            info["kv_cache_memory_full_bytes"] = recommendations[1]["bytes"]
            info["kv_cache_memory_full_value"] = recommendations[1]["value"]
            info["kv_cache_memory_full_unit"] = recommendations[1]["unit"]
    if source_lines:
        info["source_lines"] = source_lines
    return info


def parse_xllm_logs(log_text: str) -> dict[str, Any]:
    """Extract xLLM xTensor (shared_vmm_allocator) watermarks and ProfileManager step latencies."""
    return parse_vllm_logs(log_text)


def parse_mindie_sd_logs(log_text: str) -> dict[str, Any]:
    """Extract MindIE-SD DiTCache step metrics, 3D Causal VAE peak memory, and NPU memory watermarks."""
    info: dict[str, Any] = {"source": "mindie_sd_log", "framework": "mindie-sd"}
    for line in str(log_text).splitlines():
        m_cache = _DIT_CACHE_RE.search(line)
        if m_cache:
            total, computed, cached = int(m_cache.group(1)), int(m_cache.group(2)), int(m_cache.group(3))
            info["total_steps"] = total
            info["computed_steps"] = computed
            info["cached_steps"] = cached
            info["cache_hit_ratio"] = (
                float(m_cache.group(4)) if m_cache.group(4) is not None else (float(cached) / float(total) if total > 0 else 0.0)
            )
        m_vae = _VAE_PEAK_RE.search(line)
        if m_vae:
            if m_vae.group(1) is not None and m_vae.group(2) is not None:
                val, unit = float(m_vae.group(1)), m_vae.group(2)
                info["vae_peak_bytes"] = to_bytes(val, unit)
            elif m_vae.group(3) is not None:
                val = float(m_vae.group(3))
                info["vae_peak_mb"] = val
                info["vae_peak_bytes"] = to_bytes(val, "MB")
                if m_vae.group(4) is not None:
                    info["vae_tiles"] = int(m_vae.group(4))
        m_mem = _MINDIE_SD_MEM_RE.search(line)
        if m_mem:
            alloc_val, alloc_unit = float(m_mem.group(1)), m_mem.group(2)
            res_val, res_unit = float(m_mem.group(3)), m_mem.group(4)
            info["allocated_bytes"] = to_bytes(alloc_val, alloc_unit)
            info["reserved_bytes"] = to_bytes(res_val, res_unit)
    return info


def resolve_kv_log_measurement(info: Mapping[str, Any]) -> tuple[float, str, Any, str, str] | None:
    """Resolve P2 KV / state cache (bytes, unit, raw, source_kind, ref) across vLLM, xLLM, and MindIE-SD logs."""
    for key, unit, kind, ref in (
        ("kv_cache_current_bytes", "B", "vllm_log", "vllm log: Current KV cache memory"),
        ("kv_cache_current_gib", "GiB", "vllm_log", "vllm log: Current KV cache memory"),
        ("kv_cache_current_gb", "GB", "vllm_log", "vllm log: Current KV cache memory"),
        ("kv_cache_bytes", "B", "vllm_log", "vllm log: kv_cache_bytes"),
        ("xtensor_kv_used_bytes", "B", "xllm_xtensor_log", "xllm log: xTensor KV cache"),
        ("xtensor_kv_used_gib", "GiB", "xllm_xtensor_log", "xllm log: xTensor KV cache"),
        ("xtensor_kv_used_gb", "GB", "xllm_xtensor_log", "xllm log: xTensor KV cache"),
        ("xtensor_kv_peak_bytes", "B", "xllm_xtensor_log", "xllm log: xTensor KV cache"),
        ("xtensor_kv_peak_gib", "GiB", "xllm_xtensor_log", "xllm log: xTensor KV cache"),
        ("xtensor_kv_peak_gb", "GB", "xllm_xtensor_log", "xllm log: xTensor KV cache"),
        ("xtensor_high_watermark_bytes", "B", "xllm_xtensor_log", "xllm log: shared_vmm_allocator"),
        ("vae_peak_bytes", "B", "mindie_sd_log", "mindie-sd log: VAE Peak Memory"),
        ("allocated_bytes", "B", "mindie_sd_log", "mindie-sd log: MindIE-SD NPU Memory"),
    ):
        raw = info.get(key)
        if _is_number(raw):
            byte_val = float(raw) if unit == "B" else to_bytes(raw, unit)
            return byte_val, unit, raw, kind, ref
    return None


__all__ = ["parse_mindie_sd_logs", "parse_vllm_logs", "parse_xllm_logs", "resolve_kv_log_measurement"]
