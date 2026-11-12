"""Launch-script and cmd.sh fields for an archive producer.

Graph capture mode is copied onto the runtime later. It is not a grouped
GEMM caller selector.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

from fleet_archive_sources import as_int, capture_sizes, sha256

_LAUNCH: dict[str, dict[str, Any]] = {}

_SERVER = re.compile(r'start_server\s+"([^"]+)"\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(true|false)')
_MATRIX = re.compile(r'run_matrix_for_cfg\s+"([^"]+)"\s+(\d+)\s+"([^"]+)"')

def _parse_env(text: str) -> dict[str, str]:
    data = {}
    for line in text.splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _prefix_caching_declared(text: str) -> bool | None:
    """Explicit disable is false. Absence of either flag is unknown, not cached zero."""
    disabled = "--no-enable-prefix-caching" in text
    enabled = "--enable-prefix-caching" in text.replace("--no-enable-prefix-caching", "")
    if disabled and enabled:
        return None
    if disabled:
        return False
    if enabled:
        return True
    return None


def _parse_cmd(text: str) -> dict[str, Any]:
    def opt(flag: str) -> str | None:
        match = re.search(rf"--{flag}(?:\s+|=)(\S+)", text)
        return match.group(1) if match else None
    graph = re.search(r'"cudagraph_mode"\s*:\s*"([^"]+)"', text)
    gpu = opt("gpu-memory-utilization")
    return {
        "tp": as_int(opt("tensor-parallel-size")), "dp": as_int(opt("data-parallel-size")),
        "max_model_len": as_int(opt("max-model-len")), "max_num_seqs": as_int(opt("max-num-seqs")),
        "max_num_batched_tokens": as_int(opt("max-num-batched-tokens")), "block_size": as_int(opt("block-size")),
        "gpu_memory_utilization": float(gpu) if gpu and re.fullmatch(r"[0-9.]+", gpu) else None,
        "graph_capture_mode": graph.group(1) if graph else None, "graph_capture_sizes": capture_sizes(text),
        "enable_chunked_prefill": True if "--enable-chunked-prefill" in text else None,
        "enable_prefix_caching": _prefix_caching_declared(text),
    }


def _script_literals(text: str) -> dict[str, Any]:
    def grab(pattern: str, cast=int):
        match = re.search(pattern, text)
        if not match:
            return None
        try:
            return cast(match.group(1))
        except ValueError:
            return None
    plain = text.replace("\\", "")
    ep = re.search(r"EP(\d+)\s+spec_k=", plain)
    graph = re.search(r'"cudagraph_mode"\s*:\s*"([^"]+)"', plain)
    gpu = grab(r"--gpu-memory-utilization\s+([0-9.]+)", float)
    return {
        "max_model_len": grab(r"--max-model-len\s+(\d+)"), "block_size": grab(r"--block-size\s+(\d+)"),
        "gpu_memory_utilization": gpu, "graph_capture_mode": graph.group(1) if graph else None, "graph_capture_sizes": capture_sizes(plain),
        "enable_prefix_caching": _prefix_caching_declared(plain),
        "enable_chunked_prefill": True if "--enable-chunked-prefill" in plain else None,
        "ep": int(ep.group(1)) if ep else None,
        "speculative_branch_gt_zero": '[ "$spec_k" -gt 0 ]' in plain,
        "shared_expert_dp": True if re.search(r'"enable_shared_expert_dp"\s*:\s*true', plain) else None,
        "force_eplb": True if re.search(r'"enable_force_eplb"\s*:\s*true', plain) else None,
        "fused_mc2": 1 if re.search(r'"enable_fused_mc2"\s*:\s*1', plain) else None,
        "engram_layer_ids_empty": True if re.search(r'"engram_layer_ids"\s*:\s*\[\s*\]', plain) else None,
    }


def _launch_table(path: Path) -> dict[str, Any]:
    key = str(path)
    cached = _LAUNCH.get(key)
    if cached is not None:
        return cached
    text = path.read_text(encoding="utf-8", errors="replace")
    literals = _script_literals(text)
    conc_match = re.search(r"for c in ([0-9 ]+);", text)
    concs = [int(item) for item in conc_match.group(1).split()] if conc_match else []
    current = None
    cells: dict[str, Any] = {}
    for line in text.splitlines():
        server = _SERVER.search(line)
        if server:
            current = server.groups()
            continue
        matrix = _MATRIX.search(line)
        if not matrix or current is None:
            continue
        cfg, _spec_k, specs = matrix.groups()
        tag_name, tp, dp, spec_k, max_seqs, max_batched, flash = current
        for spec in specs.split():
            parts = spec.split(":")
            if len(parts) != 6:
                continue
            plen, ilen, label, olen, delay, dur = parts
            for conc in concs:
                cells[f"{cfg}_decode_{label}_c{conc}"] = {
                    "script": str(path), "server_tag": tag_name, "matrix_tag": cfg,
                    "tp": int(tp), "dp": int(dp), "spec_k": int(spec_k),
                    "max_num_seqs": int(max_seqs), "max_num_batched_tokens": int(max_batched),
                    "flashcomm": flash == "true", "prefix_len": int(plen), "input_len": int(ilen),
                    "label": label, "output_len": int(olen), "profile_delay_s": float(delay), "profile_dur_s": float(dur),
                    "speculative_config_emitted": bool(literals["speculative_branch_gt_zero"] and int(spec_k) > 0),
                    **{name: literals[name] for name in ("max_model_len", "block_size", "gpu_memory_utilization", "graph_capture_mode", "enable_prefix_caching", "enable_chunked_prefill", "ep", "shared_expert_dp", "force_eplb", "fused_mc2", "engram_layer_ids_empty")},
                }
    _LAUNCH[key] = cells
    return cells


def _match_launch(source: Path, scripts: list[Path], cmd: Any, conflicts: list[str], sources: list[dict[str, Any]]) -> dict | None:
    cell = source.parent.name
    found = []
    for script in scripts:
        table = _launch_table(script)
        if cell in table:
            found.append(table[cell])
            sources.append({"role": "launch_script", "path": str(script), "sha256": sha256(script), "size_bytes": script.stat().st_size, "matched_cell": cell})
    launch = dict(found[0]) if found else None
    if len(found) > 1 and any(item != found[0] for item in found[1:]):
        conflicts.append("conflict:launch_scripts_disagree")
        launch = None
    if isinstance(cmd, Mapping):
        if launch is None:
            launch = {"script": None, "label": None, **{key: cmd.get(key) for key in ("tp", "dp", "max_model_len", "max_num_seqs", "max_num_batched_tokens", "block_size", "gpu_memory_utilization", "graph_capture_mode", "graph_capture_sizes", "enable_chunked_prefill", "enable_prefix_caching")}}
        else:
            for key in ("tp", "dp", "max_model_len", "max_num_seqs", "max_num_batched_tokens", "graph_capture_mode"):
                if cmd.get(key) is not None and launch.get(key) is not None and cmd.get(key) != launch.get(key):
                    conflicts.append(f"conflict:launch_{key}:{cmd.get(key)}!={launch.get(key)}")
    return launch


def _merge_spec(launch: dict | None, documents: Mapping[str, Any], conflicts: list[str]) -> dict | None:
    votes = []
    if isinstance(launch, dict) and as_int(launch.get("spec_k")) is not None:
        votes.append(("launch", as_int(launch.get("spec_k"))))
    env = documents.get("meta_env") if isinstance(documents.get("meta_env"), Mapping) else {}
    if as_int(env.get("SPEC_K")) is not None:
        votes.append(("meta_env", as_int(env.get("SPEC_K"))))
    run = documents.get("run_meta") if isinstance(documents.get("run_meta"), Mapping) else {}
    arch = run.get("architecture_override") if isinstance(run.get("architecture_override"), Mapping) else {}
    if as_int(arch.get("spec_k")) is not None:
        votes.append(("run_meta", as_int(arch.get("spec_k"))))
    unique = {value for _, value in votes if value is not None}
    if len(unique) > 1:
        conflicts.append("conflict:spec_k:" + ",".join(f"{name}={value}" for name, value in votes))
        return launch
    if len(unique) != 1:
        return launch
    spec_k = next(iter(unique))
    if not isinstance(launch, dict):
        return {"spec_k": spec_k, "speculative_config_emitted": False}
    if launch.get("spec_k") is None:
        merged = dict(launch)
        merged["spec_k"] = spec_k
        merged["speculative_config_emitted"] = False
        return merged
    return launch



def clear_launch_cache() -> None:
    _LAUNCH.clear()
