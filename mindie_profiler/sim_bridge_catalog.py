"""Simulator Case normalization and native operator observation/request bridge (sim_bridge_catalog).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting simulator case normalization and native operator observation/request bridge.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, os, re, sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from .events import PARSER_VERSION, ProfilerError, ProfilerUsageError

BRIDGE_SCHEMA = "mindie-profiler-sim-bridge/1"

_A2, _A3, _A5 = "Ascend910B4", "Ascend910_9392", "Ascend950DT_9582"

_SKUS = ("Ascend910B1", "Ascend910B2", "Ascend910B2C", "Ascend910B3", "Ascend910B4", "Ascend910B4-1", "Ascend910_9362", "Ascend910_9372", "Ascend910_9381", "Ascend910_9382", "Ascend910_9391", "Ascend910_9392", "Ascend950DT_9581", "Ascend950DT_9582", "Ascend950PR_9579")

_HARDWARE = {"a2": _A2, "910b": _A2, "a3": _A3, "910c": _A3, "a5": _A5, "950": _A5, "950dt": _A5, "950pr": "Ascend950PR_9579", "ascend950pr": "Ascend950PR_9579", "950pr_a5": "Ascend950PR_9579", "ascend950pr_a5": "Ascend950PR_9579", "950dt_a5": _A5, "ascend950dt_a5": _A5, "910_9599": _A5, "ascend910_9599": _A5, **{s.lower(): s for s in _SKUS}, **{s.lower().removeprefix("ascend"): s for s in _SKUS}, **{s.split("_")[1].lower(): s for s in _SKUS if "_" in s}}

_MODEL_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple((re.compile(p, re.I), c) for p, c in ((r"deepseek[\s_.-]*v?2[\s_.-]*lite|dsv2lite", "deepseek-v2-lite"), (r"deepseek[\s_.-]*v?3(?:\.?2)?[\s_.-]*prune|dsv32?prune", "deepseek-v3.2-prune-3l"), (r"deepseek[\s_.-]*v?4\.?1|dsv41|(?<![0-9a-z])v41(?![0-9])", "deepseek-v4.1-flash"), (r"deepseek[\s_.-]*v?4[\s_.-]*pro|dsv4pro", "deepseek-v4-pro-0813"), (r"deepseek[\s_.-]*v?4[\s_.-]*10t|dsv410t", "deepseek-v4-10t"), (r"deepseek[\s_.-]*v?4[\s_.-]*flash|dsv4f|v4flash|(?<![0-9a-z])v4f(?![0-9])", "deepseek-v4-flash"), (r"qwen3\.?5[\s_.-]*27b", "qwen3.5-27b"), (r"qwen3[\s_.-]*[56][\s_.-]*35b[\s_.-]*a3b|qwen3_5_moe_a3b|(?<![0-9a-z])qwen35(?![0-9])", "qwen3.5-35b-a3b"), (r"qwen3\.?5[\s_.-]*moe", "qwen3.5-moe"), (r"qwen3[\s_.-]*30b(?:[\s_.-]*a3b)?|qwen30b(?:a3b)?", "qwen3-30b-a3b"), (r"qwen3\.?6[\s_.-]*27b|(?<![0-9a-z])qwen36(?![0-9])", "qwen3.6-27b"), (r"qwen3\.?8[\s_.-]*2\.?4t", "qwen3.8-2.4t-a95b"), (r"qwen3\.?8[\s_.-]*27b|(?<![0-9a-z])qwen38(?![0-9])", "qwen3.8-27b"), (r"glm[\s_.-]*5\.?3[\s_.-]*flash|glm53[\s_.-]*flash", "glm-5.3-flash"), (r"glm[\s_.-]*5\.?3|(?<![0-9a-z])glm53(?![0-9])", "glm-5.3"), (r"kimi[\s_.-]*k?3[\s_.-]*dspark", "kimi-k3-dspark"), (r"kimi[\s_.-]*(?:k)?3|kimi4|kimi93|(?<![0-9a-z])kimi(?![0-9a-z])", "kimi-k3"), (r"minimax[\s_.-]*m?3|(?<![0-9a-z])minimax(?![0-9a-z])", "minimax-m3"), (r"longcat[\s_.-]*flash[\s_.-]*lite|(?<![0-9a-z])longcat(?![0-9a-z])", "longcat-flash-lite"), (r"bailing[\s_.-]*v?3|(?<![0-9a-z])bailing(?![0-9a-z])", "bailing-v3"), (r"hunyuan[\s_.-]*video[\s_.-]*dit|hunyuan", "hunyuan-video-dit")))

_JSON_NAMES = {"run_meta.json": "run_meta", "benchmark_summary.json": "benchmark_summary", "client_cell.json": "client_cell", "capture.json": "capture", "provenance.json": "provenance", "model_config.json": "model_config", "config.json": "model_config", "summary.json": "report", "attribution.json": "report", "analysis.json": "report", "report.json": "report"}

_CSV_NAMES = ("op_statistic.csv", "kernel_details.csv", "step_trace_time.csv", "api_statistic.csv")

_SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "dist", "build"}

_GEOMETRY: dict[str, dict[str, Any]] = {"bailing-v3": {"catalog_key": "bailing-v3", "hidden_size": 4096, "num_heads": 32, "head_dim": 128, "num_kv_heads": 32, "intermediate_size": 12288, "vocab_size": 151851, "layers": 64, "attention": "kda", "ffn": "moe", "num_experts": 256, "top_k": 8, "moe_intermediate_size": 1536, "mla": {"q_lora_rank": 1536, "kv_lora_rank": 512, "qk_nope_head_dim": 128, "qk_rope_head_dim": 64, "v_head_dim": 128}}, "deepseek-v2-lite": {"catalog_key": "deepseek-v2-lite", "hidden_size": 2048, "num_heads": 16, "head_dim": 128, "num_kv_heads": 16, "intermediate_size": 10944, "vocab_size": 102400, "layers": 27, "attention": "mla", "ffn": "moe", "num_experts": 64, "top_k": 6, "moe_intermediate_size": 1408, "mla": {"q_lora_rank": 0, "kv_lora_rank": 512, "qk_nope_head_dim": 128, "qk_rope_head_dim": 64, "v_head_dim": 128}}, "deepseek-v3.2-prune-3l": {"catalog_key": "deepseek-v3.2-prune-3l", "hidden_size": 7168, "num_heads": 128, "head_dim": 192, "intermediate_size": 18432, "vocab_size": 129280, "layers": 3, "attention": "mla", "ffn": "moe", "num_experts": 256, "top_k": 8, "moe_intermediate_size": 2048, "mla": {"q_lora_rank": 1536, "kv_lora_rank": 512, "qk_nope_head_dim": 128, "qk_rope_head_dim": 64, "v_head_dim": 128}}, "deepseek-v4-10t": {"catalog_key": "deepseek-v4-10t", "hidden_size": 7168, "num_heads": 128, "head_dim": 512, "num_kv_heads": 1, "intermediate_size": 3072, "vocab_size": 129280, "layers": 61, "attention": "mla", "ffn": "moe", "num_experts": 384, "top_k": 6, "moe_intermediate_size": 3072, "mla": {"q_lora_rank": 1536, "kv_lora_rank": 512, "qk_nope_head_dim": 448, "qk_rope_head_dim": 64, "v_head_dim": 512}}, "deepseek-v4-flash": {"catalog_key": "deepseek-v4-flash-0731", "hidden_size": 4096, "num_heads": 64, "head_dim": 512, "num_kv_heads": 1, "intermediate_size": 2048, "vocab_size": 129280, "layers": 43, "attention": "mla", "ffn": "moe", "num_experts": 256, "top_k": 6, "moe_intermediate_size": 2048, "mla": {"q_lora_rank": 1024, "kv_lora_rank": 512, "qk_nope_head_dim": 448, "qk_rope_head_dim": 64, "v_head_dim": 512}}, "deepseek-v4-flash-0731": {"catalog_key": "deepseek-v4-flash-0731", "hidden_size": 4096, "num_heads": 64, "head_dim": 512, "num_kv_heads": 1, "intermediate_size": 2048, "vocab_size": 129280, "layers": 43, "attention": "mla", "ffn": "moe", "num_experts": 256, "top_k": 6, "moe_intermediate_size": 2048, "mla": {"q_lora_rank": 1024, "kv_lora_rank": 512, "qk_nope_head_dim": 448, "qk_rope_head_dim": 64, "v_head_dim": 512}}, "deepseek-v4-pro-0813": {"catalog_key": "deepseek-v4-pro-0813", "hidden_size": 7168, "num_heads": 128, "head_dim": 512, "num_kv_heads": 1, "intermediate_size": 3072, "vocab_size": 129280, "layers": 61, "attention": "mla", "ffn": "moe", "num_experts": 384, "top_k": 6, "moe_intermediate_size": 3072, "mla": {"q_lora_rank": 1536, "kv_lora_rank": 512, "qk_nope_head_dim": 448, "qk_rope_head_dim": 64, "v_head_dim": 512}}, "deepseek-v4.1-flash": {"catalog_key": "deepseek-v4.1-flash", "hidden_size": 5120, "num_heads": 64, "head_dim": 512, "num_kv_heads": 1, "intermediate_size": 2304, "vocab_size": 129280, "layers": 40, "attention": "mla", "ffn": "moe", "num_experts": 384, "top_k": 6, "moe_intermediate_size": 2304, "mla": {"q_lora_rank": 1280, "kv_lora_rank": 512, "qk_nope_head_dim": 448, "qk_rope_head_dim": 64, "v_head_dim": 512}}, "hunyuan-video-dit": {"catalog_key": "hunyuan-video-dit", "hidden_size": 3072, "num_heads": 24, "head_dim": 128, "num_kv_heads": 24, "intermediate_size": 12288, "vocab_size": 32000, "layers": 60, "attention": "projection_only", "ffn": "dense", "num_experts": 0, "top_k": 0, "moe_intermediate_size": 0}, "kimi-k3-dspark": {"catalog_key": "kimi-k3-dspark", "hidden_size": 7168, "num_heads": 64, "head_dim": 64, "num_kv_heads": 16, "intermediate_size": 14336, "vocab_size": 163840, "layers": 5, "attention": "gqa", "ffn": "dense", "num_experts": 0, "top_k": 0, "moe_intermediate_size": 0}, "longcat-flash-lite": {"catalog_key": "longcat-flash-lite", "hidden_size": 3072, "num_heads": 32, "head_dim": 64, "num_kv_heads": 32, "intermediate_size": 6144, "vocab_size": 131072, "layers": 14, "attention": "mla", "ffn": "moe", "num_experts": 256, "top_k": 12, "moe_intermediate_size": 1024, "mla": {"q_lora_rank": 1536, "kv_lora_rank": 512, "qk_nope_head_dim": 128, "qk_rope_head_dim": 64, "v_head_dim": 128}}, "minimax-m3": {"catalog_key": "minimax-m3", "hidden_size": 6144, "num_heads": 64, "head_dim": 128, "num_kv_heads": 8, "intermediate_size": 16384, "vocab_size": 152064, "layers": 60, "attention": "gqa", "ffn": "moe", "num_experts": 64, "top_k": 8, "moe_intermediate_size": 2048}, "qwen3-30b-a3b": {"catalog_key": "qwen3-30b-a3b", "hidden_size": 2048, "num_heads": 32, "head_dim": 128, "num_kv_heads": 4, "intermediate_size": 6144, "vocab_size": 151936, "layers": 48, "attention": "gqa", "ffn": "moe", "num_experts": 128, "top_k": 8, "moe_intermediate_size": 768}, "qwen3.5-35b-a3b": {"catalog_key": "qwen3.5-35b-a3b", "hidden_size": 2048, "num_heads": 16, "head_dim": 256, "num_kv_heads": 2, "intermediate_size": 512, "vocab_size": 248320, "layers": 40, "attention": "gdn", "ffn": "moe", "num_experts": 256, "top_k": 8, "moe_intermediate_size": 512}, "qwen3.5-moe": {"catalog_key": "qwen3.5-moe", "hidden_size": 4096, "num_heads": 32, "head_dim": 128, "num_kv_heads": 4, "intermediate_size": 12288, "vocab_size": 151936, "layers": 64, "attention": "gdn", "ffn": "moe", "num_experts": 128, "top_k": 8, "moe_intermediate_size": 1536}, "qwen3.5-27b": {"catalog_key": "qwen3.6-27b", "hidden_size": 5120, "num_heads": 24, "head_dim": 256, "num_kv_heads": 4, "intermediate_size": 17408, "vocab_size": 248320, "layers": 64, "attention": "gdn", "ffn": "dense", "num_experts": 0, "top_k": 0, "moe_intermediate_size": 0}, "qwen3.6-27b": {"catalog_key": "qwen3.6-27b", "hidden_size": 5120, "num_heads": 24, "head_dim": 256, "num_kv_heads": 4, "intermediate_size": 17408, "vocab_size": 248320, "layers": 64, "attention": "gdn", "ffn": "dense", "num_experts": 0, "top_k": 0, "moe_intermediate_size": 0}, "qwen3.8-2.4t-a95b": {"catalog_key": "qwen3.8-2.4t-a95b", "hidden_size": 8192, "num_heads": 64, "head_dim": 256, "num_kv_heads": 4, "intermediate_size": 2048, "vocab_size": 248320, "layers": 92, "attention": "gdn", "ffn": "moe", "num_experts": 512, "top_k": 10, "moe_intermediate_size": 2048}, "qwen3.8-27b": {"catalog_key": "qwen3.8-27b", "hidden_size": 5120, "num_heads": 24, "head_dim": 256, "num_kv_heads": 4, "intermediate_size": 17408, "vocab_size": 248320, "layers": 64, "attention": "gdn", "ffn": "dense", "num_experts": 0, "top_k": 0, "moe_intermediate_size": 0}, "glm-5.3": {"catalog_key": "glm-5.3", "hidden_size": 6144, "num_heads": 64, "head_dim": 192, "num_kv_heads": 64, "intermediate_size": 12288, "vocab_size": 154880, "layers": 78, "attention": "mla", "ffn": "moe", "num_experts": 256, "top_k": 8, "moe_intermediate_size": 2048, "mla": {"q_lora_rank": 2048, "kv_lora_rank": 512, "qk_nope_head_dim": 192, "qk_rope_head_dim": 64, "v_head_dim": 256}}, "glm-5.3-flash": {"catalog_key": "glm-5.3-flash", "hidden_size": 4096, "num_heads": 64, "head_dim": 256, "num_kv_heads": 64, "intermediate_size": 12288, "vocab_size": 154880, "layers": 45, "attention": "mla", "ffn": "moe", "num_experts": 288, "top_k": 8, "moe_intermediate_size": 2048, "mla": {"q_lora_rank": 1536, "kv_lora_rank": 512, "qk_nope_head_dim": 256, "qk_rope_head_dim": 0, "v_head_dim": 256}}, "kimi-k3": {"catalog_key": "kimi-k3", "hidden_size": 7168, "num_heads": 96, "head_dim": 74, "num_kv_heads": 96, "intermediate_size": 33792, "vocab_size": 163840, "layers": 93, "attention": "mla", "ffn": "moe", "num_experts": 896, "top_k": 16, "moe_intermediate_size": 3072}}

_GENERIC = {"hidden_size": 4096, "num_heads": 32, "head_dim": 128, "num_kv_heads": 8, "intermediate_size": 14336, "vocab_size": 151936, "layers": 32, "attention": "gqa", "ffn": "moe", "num_experts": 64, "top_k": 8, "moe_intermediate_size": 512}

_MAX_POS = {"deepseek-v2-lite": 163840, "deepseek-v3.2-prune-3l": 163840, "qwen3-30b-a3b": 131072, "qwen3.5-27b": 262144, "qwen3.5-35b-a3b": 262144, "qwen3.6-27b": 262144, "qwen3.8-2.4t-a95b": 262144, "qwen3.8-27b": 262144, "deepseek-v4-10t": 1048576, "deepseek-v4-flash": 1048576, "deepseek-v4-flash-0731": 1048576, "deepseek-v4-pro-0813": 1048576, "deepseek-v4.1-flash": 1048576, "glm-5.3": 1048576, "glm-5.3-flash": 1048576, "kimi-k3": 1048576, "kimi-k3-dspark": 1048576}

def _empty_bundle(root: Path | None) -> dict[str, Any]:
    return {"root": root, "json": {}, "env": {}, "cmd": "", "csv": {}, "report": None, "case_record": None, "source_kind": "directory", "source_path": None}

def _walk_err(exc: OSError) -> None:
    if isinstance(exc, TimeoutError): raise exc
    raise ProfilerUsageError(f"cannot scan directory: {exc}") from exc

def _read_json(path: Path) -> Any:
    try:
        if path.stat().st_size > 50 * 1024**2: raise ProfilerUsageError(f"JSON metadata exceeds 50 MiB: {path}")
        with path.open(encoding="utf-8") as stream: return json.load(stream)
    except json.JSONDecodeError as exc: raise ProfilerUsageError(f"invalid JSON in {path}: {exc}") from exc
    except TimeoutError: raise
    except OSError as exc: raise ProfilerUsageError(f"cannot read JSON {path}: {exc}") from exc

def _read_text(path: Path, limit: int = 50 * 1024**2) -> str:
    try:
        if path.stat().st_size > limit: raise ProfilerUsageError(f"text metadata exceeds {limit // 1024**2} MiB: {path}")
        return path.read_text(encoding="utf-8", errors="replace")
    except TimeoutError: raise
    except OSError as exc: raise ProfilerUsageError(f"cannot read text {path}: {exc}") from exc

def _parse_env(text: str) -> dict[str, str]:
    env: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        if line.startswith("export "): line = line[7:].strip()
        key, value = line.split("=", 1)
        if key.strip(): env[key.strip()] = value.strip().strip("'\"")
    return env

def _strip_spec_cmd(cmd: str) -> str: return re.sub(r"--(?:speculative[-_]config|draft[-_]model)(?:=|\s+)(?:'[^']*'|\"[^\"]*\"|\{[^}]*\}|\S+)", "", cmd)

def _runtime_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        low = value.strip().lower()
        if low in {"1", "true", "yes", "on", "enabled"}:
            return True
        if low in {"0", "false", "no", "off", "disabled"}:
            return False
    return None

def _candidate_strings(*values: Any) -> list[str]:
    strings: list[str] = []
    def visit(val: Any, depth: int) -> None:
        if depth > 4 or len(strings) > 256: return
        if isinstance(val, str) and val.strip(): strings.append(val.strip())
        elif isinstance(val, Mapping):
            for k in sorted(val, key=str):
                if str(k) not in {"speculative_config", "draft_model"}: visit(val[k], depth + 1)
        elif isinstance(val, Sequence) and not isinstance(val, (str, bytes)):
            for item in val[:32]: visit(item, depth + 1)
    for v in values: visit(v, 0)
    return strings

def _resolve_hw_token(text: str, *, strict: bool = False) -> str | None:
    lowered = text.strip().lower()
    if found := next((_HARDWARE[k] for k in sorted(_HARDWARE, key=len, reverse=True) if lowered == k or lowered == _HARDWARE[k].lower()), None): return found
    if not strict and (sku_hit := next((s for s in sorted(_SKUS, key=len, reverse=True) if re.search(rf"(?<![0-9a-z]){re.escape(s.lower())}(?![0-9a-z-])", lowered)), None)): return sku_hit
    if m := re.search(r"ascend[\s_-]*(910[\s_-]*[a-z0-9-]+|950[\s_-]*[a-z0-9-]+)", lowered):
        tok = re.sub(r"[\s_-]+", "", m.group(1))
        if tok in {"910ba3", "910ca3"}: return _A3
        if tok == "910ba2": return _A2
        tok_base = re.sub(r"a[235]$", "", tok) if tok.endswith(("950a5", "950dta5", "950pra5")) else tok
        if found := (_HARDWARE.get(tok) or _HARDWARE.get(tok_base) or _HARDWARE.get(re.sub(r"^(910)(\d{4})$", r"\1_\2", tok_base))): return found
        if strict: raise ProfilerUsageError(f"unsupported or unrecognized hardware: {text}")
        return None
    if strict: raise ProfilerUsageError(f"unsupported or unrecognized hardware: {text}")
    m = re.search(r"(?<![0-9a-z])(a[235]|910b[0-9a-z-]*|910c|950(?:dt|pr)?)(?![0-9a-z])", lowered)
    return _HARDWARE[m.group(1)] if (m and m.group(1) in _HARDWARE) else None

def _config_identity(config: Mapping[str, Any]) -> str | None:
    for key in ("_name_or_path", "name", "model_type", "architectures"):
        val = config.get(key)
        if isinstance(val, Sequence) and not isinstance(val, (str, bytes)): val = " ".join(str(x) for x in val)
        if isinstance(val, str) and val.strip(): return val.strip()
    return None

def _match_model(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        low = value.strip().lower()
        return low if low in _GEOMETRY else next((c for p, c in _MODEL_PATTERNS if p.search(value)), None)
    return None

def _normalize_quant(value: Any) -> str | None:
    text = str(value or "").strip().lower().replace("-", "").replace("_", "")
    return next((norm for pat, norm in (("w8a8mxfp8", "w8a8_mxfp8"), ("mxfp8", "mxfp8"), ("w8a8", "w8a8"), ("w4a8", "w4a8"), ("fp8", "fp8"), ("int8", "w8a8"), ("bf16", "bf16"), ("fp16", "fp16")) if pat in text), None)

def _empty_observed() -> dict[str, Any]:
    return {"step_time_ms": None, "tpot_p50_ms": None, "ttft_p50_ms": None, "device_busy_union_ms": None, "device_activity_sum_ms": None, "exposed_comm_ms": None, "device_uncovered_ms": None, "cube_share": None, "vector_share": None, "hccl_share": None, "comm_share": None, "aicpu_share": None, "host_share": None, "attention_share": None, "moe_share": None, "kv_peak_ratio": None, "dominant_bottleneck": None, "top_operators": []}

def _merge_observed(target: dict[str, Any], incoming: Mapping[str, Any]) -> None:
    for key, value in incoming.items():
        if key not in target or value is None: continue
        if key == "top_operators":
            if value and not target.get(key): target[key] = list(value)[:10]
        elif target.get(key) is None: target[key] = value

def _quant_from_operators(values: Sequence[Any]) -> str | None:
    names = " ".join(str(x.get("name") or x.get("op_type") or "") if isinstance(x, Mapping) else str(x) for x in values).lower()
    has_w8 = any(k in names for k in ("quantbatchmatmul", "dynamicquant", "w8a8"))
    if "w4a8" in names: return "w4a8"
    if "mxfp8" in names: return "w8a8_mxfp8" if has_w8 else "mxfp8"
    return "w8a8" if has_w8 else ("fp8" if "fp8" in names else None)

def _try_import(mod_name: str) -> Any:
    try: return __import__(mod_name, fromlist=["compose_case"])
    except ImportError: return None

def _norm_aux_and_fp16(out: dict[str, Any], q_val: str | None, req_layers: int | None = None) -> None:
    if isinstance(out.get("auxiliary"), Mapping):
        out["auxiliary"] = {**out["auxiliary"], "standalone_draft": False}
        for sk in ("mtp", "dspark"):
            if isinstance(out["auxiliary"].get(sk), Mapping) and (t_ids := out["auxiliary"][sk].get("target_layer_ids")):
                n_l = int(req_layers or out.get("layers") or 1)
                if any(int(i) < 0 or int(i) >= n_l for i in t_ids): out["auxiliary"][sk] = {**out["auxiliary"][sk], "target_layer_ids": list(range(max(0, n_l - min(n_l, len(t_ids))), n_l))}
    if q_val == "fp16":
        out.update(weight_dtype="fp16", activation_dtype="fp16", kv_dtype="fp16")
        out.pop("quantization", None)
        if isinstance(out.get("quant"), Mapping): out["quant"] = {**out["quant"], "name": "fp16", "weight_format": "fp16", "native_format": "fp16", "activation_format": "fp16", "expert_weight_format": "fp16", "kv_dtype": "fp16"}

def _strip_timings(value: Any) -> None:
    if isinstance(value, dict):
        for key in list(value):
            if str(key).lower() != "latency_us" and any(t in str(key).lower() for t in ("observed", "latency", "step_time", "tpot", "ttft")): value.pop(key, None)
            else: _strip_timings(value[key])
    elif isinstance(value, list):
        for item in value: _strip_timings(item)

def _parse_case(case: Mapping[str, Any]) -> str | None:
    try: from mindie_sim.prediction.structure import parse_case
    except ImportError: return "mindie_sim unavailable"
    try: parse_case(case); return None
    except TimeoutError: raise
    except Exception as exc: return str(exc)

def _mapping(value: Any) -> dict[str, Any]: return dict(value) if isinstance(value, Mapping) else {}

def _diagnostic_filled_values(facts: Mapping[str, Any], case: Mapping[str, Any], gaps: Sequence[str]) -> dict[str, Any]:
    runtime, workload, model = _mapping(case.get("runtime")), _mapping(facts.get("workload")), _mapping(case.get("model"))
    values: dict[str, Any] = {}
    for gap in gaps:
        if gap.startswith("workload."):
            key = gap.split(".", 1)[1]
            values[gap] = workload.get(key)
        elif gap.startswith("runtime."):
            key = gap.split(".", 1)[1]
            values[gap] = runtime.get(key)
        elif gap == "model.missing":
            values[gap] = {"name": model.get("name"), "layers": model.get("layers")}
        elif gap == "model.generic_geometry":
            values[gap] = {
                "name": model.get("name"), "hidden_size": model.get("hidden_size"),
                "num_heads": model.get("num_heads"), "layers": model.get("layers"),
                "intermediate_size": model.get("intermediate_size"),
                "vocab_size": model.get("vocab_size"),
            }
    return values

def _quantization(override: Any, run_meta: Mapping[str, Any], env: Mapping[str, str], cmd: str, config: Mapping[str, Any], bench: Mapping[str, Any], record: Mapping[str, Any]) -> str | None:
    for exp in (override, record.get("quantization"), record.get("quant"), run_meta.get("quantization"), run_meta.get("quant"), env.get("QUANTIZATION"), env.get("QUANT"), _mapping(bench.get("extra")).get("quantization")):
        if isinstance(exp, str) and exp.strip():
            low = exp.strip().lower()
            if low in {"auto", "ascend"}: continue
            if low in {"none", "unquantized"}: return "bf16"
            if (norm := _normalize_quant(exp)) is None: raise ProfilerUsageError(f"unsupported or unrecognized quantization: {exp}")
            return norm
    vals = (cmd, config.get("quantization"), config.get("quant_method"), run_meta.get("model_name"), run_meta.get("weight_path"), env.get("MODEL_NAME"), env.get("WEIGHT_PATH"))
    return next((f for v in vals if (f := _normalize_quant(v))), None)

def _validate_case(case: Mapping[str, Any]) -> None:
    par, model = _mapping(_mapping(case.get("runtime")).get("parallel")), _mapping(case.get("model"))
    base_g = _GEOMETRY.get(str(_mapping(_mapping(_mapping(case.get("runtime")).get("metadata")).get("profiler_provenance")).get("extracted_model")), {})
    tp, dp, ep, pp, layers = *(int(par.get(k) or 1) for k in ("tp", "dp", "ep", "pp")), int(model.get("layers") or base_g.get("layers") or 1)
    if (tp * dp) % ep != 0: raise ProfilerUsageError(f"invalid simulation case: ep_not_divisor_of_dp_tp_domain:{tp * dp}%{ep}")
    if pp > layers: raise ProfilerUsageError(f"invalid simulation case: pp_exceeds_layers:{pp}>{layers}")
    if ep > 1:
        experts = int(model.get("num_experts") or model.get("n_routed_experts") or base_g.get("num_experts") or 0)
        if (model.get("ffn") or base_g.get("ffn")) != "moe" or experts < 2: raise ProfilerUsageError("invalid simulation case: ep_requires_moe_model")
        if experts % ep != 0: raise ProfilerUsageError(f"invalid simulation case: ep_not_divisor_of_num_experts:{experts}%{ep}")
    if (err := _parse_case(case)) is not None and err != "mindie_sim unavailable": raise ProfilerUsageError(f"invalid simulation case: {err}")

def _first_string(*values: Any) -> str | None: return next((v.strip() for v in values if isinstance(v, str) and v.strip()), None)

def _detect_hardware(override: Any, run_meta: Mapping[str, Any], record: Mapping[str, Any], env: Mapping[str, str], provenance: Mapping[str, Any], cell_tag: str | None, strings: Sequence[str]) -> str:
    if strict_val := _first_string(override, run_meta.get("npu_type"), run_meta.get("hardware"), run_meta.get("chip"), record.get("hw"), env.get("NPU_TYPE")):
        if res := _resolve_hw_token(strict_val, strict=True): return res
    return next((res for text in (run_meta.get("host"), provenance.get("source"), cell_tag, *strings) if isinstance(text, str) and text.strip() and (res := _resolve_hw_token(text, strict=False))), _A3)

def _detect_model(override: Any, run_meta: Mapping[str, Any], record: Mapping[str, Any], env: Mapping[str, str], cmd: str, config: Mapping[str, Any], cell_tag: str | None, strings: Sequence[str]) -> str | None:
    if isinstance(override, str) and override.strip(): return _match_model(override) or override.strip()
    m_srv = re.search(r"(?:vllm\s+serve|--model|--served-model-name|--weight-path)(?:=|\s+)['\"]?([^\s'\"]+)", cmd)
    explicit = (run_meta.get("model_name"), run_meta.get("weight_path"), run_meta.get("architecture_override"), record.get("model_name"), record.get("family"), env.get("MODEL_NAME"), env.get("WEIGHT_PATH"), _config_identity(config), m_srv.group(1) if m_srv else None)
    for value in (*explicit, cmd, cell_tag, *strings):
        found = _match_model(value)
        if found: return found
    return _first_string(*explicit)

def _graph_mode(override: Any, run_meta: Mapping[str, Any], env: Mapping[str, str], cmd: str, report: Mapping[str, Any], bench: Mapping[str, Any], record: Mapping[str, Any]) -> tuple[str, str]:
    raw = _first_string(override, _mapping(report.get("scene")).get("graph_mode"), record.get("graph_mode"), record.get("execution_mode"), run_meta.get("graph_mode"), run_meta.get("execution_mode"), _mapping(bench.get("extra")).get("graph_mode"), _mapping(bench.get("summary")).get("graph_mode"), env.get("GRAPH_MODE"))
    if raw is None and cmd:
        low = re.sub(r"--speculative[-_]config(?:=|\s+)(?:'[^']*'|\"[^\"]*\"|\{[^}]*\}|\S+)", "", cmd.lower())
        if "--enforce-eager" in low or "enforce_eager" in low: raw = "eager"
        elif "piecewise" in low: raw = "piecewise"
        elif any(t in low for t in ("--aclgraph", "torchair", "full_decode_only", "aclgraph")): raw = "aclgraph"
        else:
            m = re.search(r"--graph-mode(?:=|\s+)([a-z0-9_]+)", low)
            raw = m.group(1) if m else None
    if raw is None:
        flags = (record.get("is_eager"), run_meta.get("is_eager"), _mapping(run_meta.get("workload")).get("is_eager"), _mapping(bench.get("extra")).get("is_eager"), env.get("IS_EAGER"), env.get("ENFORCE_EAGER"))
        raw = next(("aclgraph" if (f is False or str(f).strip().lower() in {"false", "0", "no"}) else "eager" for f in flags if f is not None and (isinstance(f, bool) or str(f).strip().lower() in {"false", "0", "no", "true", "1", "yes"})), None)
    text = str(raw or "").strip().lower()
    if "piecewise" in text: return ("piecewise", "piecewise")
    return ("aclgraph_full", "full") if any(t in text for t in ("aclgraph", "torchair", "full_decode", "full")) else ("eager", "none")

def _hccl_mode(override: Any, run_meta: Mapping[str, Any], env: Mapping[str, str], cmd: str, bench: Mapping[str, Any], record: Mapping[str, Any]) -> str:
    raw = override or env.get("HCCL_OP_EXPANSION_MODE")
    if raw is None:
        m = re.search(r"HCCL_OP_EXPANSION_MODE\s*=\s*['\"]?([A-Za-z0-9_]+)", cmd)
        raw = m.group(1) if m else _first_string(record.get("hccl_op_expansion_mode"), run_meta.get("hccl_op_expansion_mode"), _mapping(run_meta.get("env")).get("HCCL_OP_EXPANSION_MODE"), _mapping(bench.get("extra")).get("hccl_op_expansion_mode"))
    text = str(raw or "").strip().lower()
    return "aicpu" if ("aicpu" in text or "ai_cpu" in text or "ai cpu" in text) else "aiv" if ("aiv" in text or "vector" in text) else "unspecified"

def _first_float(*values: Any) -> float | None:
    for v in values:
        if v is not None and not isinstance(v, bool):
            try:
                if (num := float(v)) == num and abs(num) != float("inf"): return num
            except (TypeError, ValueError): pass
    return None

def _attach_metadata(case: dict[str, Any], facts: Mapping[str, Any], observed: Mapping[str, Any], applied: Sequence[str]) -> None:
    runtime, spec_k, acc_len = case["runtime"], facts["structural"].get("spec_tokens"), _first_float(facts.get("mtp_acceptance_length"))
    runtime.update(parallel={k: int(facts["parallel"][k]) for k in ("tp", "dp", "ep", "pp")}, graph_mode=facts["graph_capture_mode"], graph_capture_mode=facts["graph_capture_mode"])
    if facts["graph_capture_mode"] == "full": runtime["graph_capture_keys"] = sorted({*(runtime.get("graph_capture_keys") or ()), 1, 2, 4, 8, 16, 32, 64, 128, 256, max(1, int(runtime.get("max_num_seqs") or 16) * max(1, 1 + int(spec_k or 0)))})
    elif facts["graph_capture_mode"] == "piecewise": runtime.setdefault("piecewise_capture_keys", sorted({1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, int(runtime.get("max_num_batched_tokens") or 8192)}))
    metadata = runtime["metadata"] if isinstance(runtime.get("metadata"), dict) else runtime.setdefault("metadata", {})
    metadata.update(execution_mode=facts["execution_mode"], hccl_op_expansion_mode=facts["hccl_op_expansion_mode"], observed_profile=dict(observed))
    if acc_len is not None and acc_len > 1.0: runtime["mtp_acceptance_length"] = round(float(acc_len), 4)
    if spec_k is not None:
        metadata["spec_tokens"] = int(spec_k)
        if int(spec_k) > 0:
            aux, n_l = _mapping(case["model"].get("auxiliary")), int(case["model"].get("layers") or 1)
            if str(facts.get("model")) == "kimi-k3-dspark" or aux.get("standalone_draft"): raise ProfilerUsageError("invalid simulation case: standalone_draft_requires_target_model")
            mode = "dspark" if (aux.get("dspark") and not aux.get("mtp")) or "dspark" in str(facts.get("model") or "") else "mtp"
            metadata.update(draft_mode=mode, draft_proposal_tokens=int(spec_k))
            if not aux.get("mtp") and not aux.get("dspark"):
                m = case["model"]
                hid, hds, hdim = int(m.get("hidden_size") or 4096), int(m.get("num_heads") or 32), int(m.get("head_dim") or 128)
                kvh = int(m.get("num_kv_heads") or hds)
                case["model"]["auxiliary"] = {**aux, "mtp": {"kind": "mtp", "layers": 1, "hidden_size": hid, "intermediate_size": int(m.get("intermediate_size") or hid), "num_heads": hds, "num_kv_heads": kvh, "head_dim": hdim, "q_width": hds * hdim, "kv_width": 2 * kvh * hdim, "target_layer_ids": [max(0, n_l - 1)]}}
            elif isinstance(aux.get(mode), Mapping) and any(int(i) < 0 or int(i) >= n_l for i in (aux[mode].get("target_layer_ids") or ())):
                raise ProfilerUsageError(f"invalid simulation case: auxiliary_target_layer_out_of_bounds:{list(aux[mode].get('target_layer_ids') or ())}>=layers({n_l})")
    metadata["profiler_provenance"] = {"schema_version": BRIDGE_SCHEMA, "parser_version": PARSER_VERSION, "source_path": facts.get("source_path"), "source_kind": facts.get("source_kind"), "cell_tag": facts.get("cell_tag"), "extracted_hardware": facts["hardware"], "extracted_model": facts.get("model"), "execution_mode": facts["execution_mode"], "hccl_op_expansion_mode": facts["hccl_op_expansion_mode"], "overrides_applied": list(applied), "no_forward_latency_leakage": True}
    metadata["bridge_summary"] = {"system": {"hardware": facts["hardware"], "model": facts.get("model"), "quantization": facts.get("quantization") or _mapping(case["model"].get("quant")).get("name") or case["model"].get("quantization"), "execution_mode": facts["execution_mode"], "hccl_op_expansion_mode": facts["hccl_op_expansion_mode"], "spec_tokens": spec_k}, "parallel": dict(facts["parallel"]), "workload": {key: value for key, value in facts["workload"].items() if not str(key).startswith("_")}}

def _first_int(*values: Any) -> int | None:
    return None if (num := _first_float(*values)) is None else int(num)

def _flatten_record(item: Mapping[str, Any]) -> dict[str, Any]:
    record = {**_mapping(item.get("traits")), **dict(item)}
    if {"machine", "model", "workload"} <= set(item):
        m_hw, m_mod, m_rt, m_wl = _mapping(item.get("machine")), _mapping(item.get("model")), _mapping(item.get("runtime")), _mapping(item.get("workload"))
        m_par, m_meta = _mapping(m_rt.get("parallel")), _mapping(m_rt.get("metadata"))
        reqs = m_wl.get("requests") if isinstance(m_wl.get("requests"), Sequence) and not isinstance(m_wl.get("requests"), (str, bytes)) else []
        req0 = _mapping(reqs[0]) if reqs else {}
        n_exp = _first_int(m_mod.get("num_experts"), m_mod.get("n_routed_experts"))
        top_k = _first_int(m_mod.get("top_k"), m_mod.get("num_experts_per_tok"))
        sim_fields = {"hw": m_hw.get("sku") or m_hw.get("hardware_key") or m_hw.get("name"), "model_name": m_mod.get("catalog_key") or m_mod.get("name"), "tp": m_par.get("tp", m_rt.get("tp")), "dp": m_par.get("dp", m_rt.get("dp")), "ep": m_par.get("ep", m_rt.get("ep")), "pp": m_par.get("pp", m_rt.get("pp")), "concurrency": len(reqs) if reqs else None, "seq_len": req0.get("prompt_tokens"), "decode_steps": req0.get("output_tokens"), "prefix_len": req0.get("prefix_tokens"), "graph_mode": m_meta.get("execution_mode") or m_rt.get("graph_capture_mode") or m_rt.get("graph_mode"), "hccl_op_expansion_mode": m_meta.get("hccl_op_expansion_mode"), "layers": m_mod.get("layers"), "n_routed_experts": n_exp if (n_exp and n_exp > 0) else None, "num_experts_per_tok": top_k if (top_k and top_k > 0) else None, "spec_tokens": _first_int(m_meta.get("spec_tokens"), m_meta.get("draft_proposal_tokens")), "mtp_acceptance_length": _first_float(m_rt.get("mtp_acceptance_length")), "observed_profile": m_meta.get("observed_profile")}
        record.update({k: v for k, v in sim_fields.items() if v is not None})
    if record.get("hardware") and not record.get("hw"): record["hw"] = record["hardware"]
    return record

def _runtime_facts(
    run_meta: Mapping[str, Any], bench: Mapping[str, Any],
    client: Mapping[str, Any], capture: Mapping[str, Any],
    report: Mapping[str, Any], record: Mapping[str, Any],
    env: Mapping[str, str], cmd: str,
) -> dict[str, Any]:
    """Collect only explicitly declared scheduler/runtime facts.

    Values are not guessed from workload shape.  A missing fact stays absent so
    the ordinary export can report a concrete gap instead of a generic default.
    """
    sources: list[Mapping[str, Any]] = []
    for value in (run_meta, bench, client, capture, report, record):
        if isinstance(value, Mapping):
            sources.append(value)
            for nested in ("runtime", "scheduler", "engine"):
                if isinstance(value.get(nested), Mapping):
                    sources.append(value[nested])
    specs = {
        "max_num_seqs": ("max_num_seqs", "max_num_seq", "max_seqs"),
        "max_num_batched_tokens": ("max_num_batched_tokens", "max_batched_tokens"),
        "max_model_len": ("max_model_len", "max_sequence_length", "max_seq_len"),
        "kv_block_size": ("kv_block_size", "block_size", "cache_block_size"),
    }
    result: dict[str, Any] = {}
    for key, names in specs.items():
        value = _first_int(*(source.get(name) for source in sources for name in names))
        if value is None:
            env_names = {"max_num_seqs": ("MAX_NUM_SEQS", "MAX_SEQS"),
                         "max_num_batched_tokens": ("MAX_NUM_BATCHED_TOKENS",),
                         "max_model_len": ("MAX_MODEL_LEN", "MAX_SEQ_LEN"),
                         "kv_block_size": ("KV_BLOCK_SIZE", "BLOCK_SIZE")}[key]
            value = _first_int(*(env.get(name) for name in env_names))
        if value is None:
            flags = {"max_num_seqs": ("max-num-seqs", "max-seqs"),
                     "max_num_batched_tokens": ("max-num-batched-tokens",),
                     "max_model_len": ("max-model-len", "max-seq-len"),
                     "kv_block_size": ("block-size", "kv-block-size")}[key]
            for flag in flags:
                match = re.search(rf"--{re.escape(flag)}(?:=|\s+)(\d+)", cmd)
                if match:
                    value = int(match.group(1))
                    break
        if value is not None:
            result[key] = value
    raw_chunked = next((source.get(name) for source in sources
                        for name in ("enable_chunked_prefill", "chunked_prefill")
                        if isinstance(source.get(name), (bool, str))), None)
    chunked = _runtime_bool(raw_chunked)
    if chunked is None:
        chunked = _runtime_bool(env.get("ENABLE_CHUNKED_PREFILL"))
    if chunked is None:
        if re.search(r"--no-enable-chunked-prefill(?:\s|$)", cmd):
            chunked = False
        elif re.search(r"--enable-chunked-prefill(?:\s|$)", cmd):
            chunked = True
    if chunked is not None:
        result["enable_chunked_prefill"] = chunked
    return result

def _complete_model_config(config: Mapping[str, Any]) -> bool:
    hidden = _first_int(config.get("hidden_size"), config.get("d_model"), config.get("hidden_dim"))
    heads = _first_int(config.get("num_attention_heads"), config.get("num_heads"), config.get("n_heads"))
    layers = _first_int(config.get("num_hidden_layers"), config.get("layers"), config.get("num_layers"))
    intermediate = _first_int(config.get("intermediate_size"), config.get("ffn_intermediate_size"), config.get("ffn_dim"))
    vocab = _first_int(config.get("vocab_size"))
    return all(value is not None and value > 0 for value in (hidden, heads, layers, intermediate, vocab))

def _complete_sim_model(model: Mapping[str, Any]) -> bool:
    if isinstance(model.get("layer_plans"), Sequence) and model.get("layer_plans"):
        return True
    return _complete_model_config(model)

def _model_production_gap(facts: Mapping[str, Any]) -> str | None:
    model = facts.get("model")
    if not isinstance(model, str) or not model:
        return "model.missing"
    if isinstance(facts.get("sim_model"), Mapping) and _complete_sim_model(facts["sim_model"]):
        return None
    if _complete_model_config(_mapping(facts.get("config"))):
        return None
    if model in _GEOMETRY:
        return None
    return "model.generic_geometry"

def _structural_overrides(run_meta: Mapping[str, Any], env: Mapping[str, str], config: Mapping[str, Any], record: Mapping[str, Any], report: Mapping[str, Any], bench: Mapping[str, Any] = {}, client: Mapping[str, Any] = {}, cmd: str = "") -> dict[str, int]:
    b_sum, b_extra = _mapping(bench.get("summary")), _mapping(bench.get("extra"))
    b_design, m_sc = _mapping(b_sum.get("design")) or _mapping(bench.get("design")), re.search(r"--speculative[-_]config(?:=|\s+)(?:'([^']*)'|\"([^\"]*)\"|(\{[^}]*\}))", cmd)
    sc_txt = next((g for g in m_sc.groups() if g is not None), "") if m_sc else ""
    spec_keys = ("spec_tokens", "spec_k", "num_speculative_tokens", "mtp_proposal_tokens")
    cmd_spec = {k: int(m.group(1)) for k in (*spec_keys, "num_nextn_predict_layers", "num_mtp_layers") if (m := re.search(rf'"{k}"\s*:\s*(\d+)', sc_txt))}
    spec_cfgs = tuple(_mapping(x) for x in (_mapping(run_meta.get("recipe")).get("speculative_config"), run_meta.get("speculative_config"), _mapping(b_extra.get("recipe")).get("speculative_config"), b_extra.get("speculative_config"), bench.get("speculative_config"), _mapping(client.get("extra")).get("speculative_config"), cmd_spec) if isinstance(x, Mapping) and x)
    rt_sources = (record, _mapping(run_meta.get("architecture_override")), _mapping(run_meta.get("structure")), _mapping(run_meta.get("workload")), run_meta, _mapping(report.get("scene")), bench, b_sum, b_design, b_extra, client)
    sources = (*rt_sources[:6], config, *rt_sources[6:])
    spec_map = {"layers": (("layers", "num_layers", "n_layers", "num_hidden_layers", "num_layers_per_stage"), ("NUM_LAYERS", "LAYERS", "N_LAYERS")), "n_routed_experts": (("n_routed_experts", "num_routed_experts", "num_experts", "n_experts", "num_local_experts"), ("NUM_EXPERTS", "N_ROUTED_EXPERTS", "NUM_ROUTED_EXPERTS", "N_EXPERTS")), "num_experts_per_tok": (("num_experts_per_tok", "top_k", "moe_top_k", "num_experts_per_token"), ("TOP_K", "NUM_EXPERTS_PER_TOK", "MOE_TOP_K"))}
    result = {f: v for f, (keys, env_keys) in spec_map.items() if (v := _first_int(*(s.get(k) for s in sources for k in keys), *(env.get(k) for k in env_keys))) is not None and v >= 1}
    spec_v = _first_int(*(s.get(k) for s in (*rt_sources[:6], *spec_cfgs) for k in spec_keys), *(env.get(k) for k in ("SPEC_K", "NUM_SPECULATIVE_TOKENS", "MTP_PROPOSAL_TOKENS")), *(s.get(k) for s in rt_sources[6:] for k in spec_keys), *(s.get(k) for s in (*rt_sources, *spec_cfgs) for k in ("num_nextn_predict_layers", "num_mtp_layers")))
    if spec_v is not None and spec_v >= 0: result["spec_tokens"] = spec_v
    return result

def _parallel_overrides(overrides: Mapping[str, Any], run_meta: Mapping[str, Any], env: Mapping[str, str], bench: Mapping[str, Any], client: Mapping[str, Any], report: Mapping[str, Any], cmd: str, cell_tag: str | None, record: Mapping[str, Any]) -> dict[str, int]:
    declared, scene = _mapping(run_meta.get("parallelism")) or _mapping(run_meta.get("parallel")), _mapping(report.get("scene"))
    specs = (("tp", "tensor_parallel_size", ("TP", "TENSOR_PARALLEL_SIZE"), r"--tensor-parallel-size(?:=|\s+)(\d+)"), ("dp", "data_parallel_size", ("DP", "DATA_PARALLEL_SIZE"), r"--data-parallel-size(?:=|\s+)(\d+)"), ("ep", "expert_parallel_size", ("EP", "EXPERT_PARALLEL_SIZE"), r"--expert-parallel-size(?:=|\s+)(\d+)"), ("pp", "pipeline_parallel_size", ("PP", "PIPELINE_PARALLEL_SIZE"), r"--pipeline-parallel-size(?:=|\s+)(\d+)"))
    result: dict[str, int] = {}
    for key, long_key, env_keys, cmd_pattern in specs:
        m_cmd, m_cell = re.search(cmd_pattern, cmd), (re.search(rf"(?<![a-z]){key}[_-]?(\d+)", cell_tag, re.I) if cell_tag else None)
        val = _first_int(overrides.get(key), record.get(key), declared.get(key), declared.get(f"{key}_size"), env.get(env_keys[0]), env.get(env_keys[1]), bench.get(f"{key}_size"), bench.get(f"{key}_parallel_size"), bench.get(long_key), client.get(f"{key}_size"), scene.get(key), int(m_cmd.group(1)) if m_cmd else None, int(m_cell.group(1)) if m_cell else None)
        if val is not None:
            if val < 1: raise ProfilerUsageError(f"invalid simulation case: {key}_out_of_bounds:{val}")
            result[key] = val
    if "--enable-expert-parallel" in cmd and "ep" not in result: result["ep"] = max(1, result.get("tp", 1) * result.get("dp", 1))
    return {k: result.get(k, 1) for k in ("tp", "dp", "ep", "pp")}

def _request_records(
    run_meta: Mapping[str, Any], bench: Mapping[str, Any],
    client: Mapping[str, Any], record: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Preserve real per-request identity/arrival/geometry when declared."""
    candidates = (
        ("client_cell.per_request", client.get("per_request")),
        ("benchmark.requests", bench.get("requests")),
        ("run_meta.workload.requests", _mapping(run_meta.get("workload")).get("requests")),
        ("case.requests", _mapping(record.get("workload")).get("requests")),
        ("record.requests", record.get("requests")),
    )
    for source, value in candidates:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            continue
        rows = [item for item in value if isinstance(item, Mapping)]
        if not rows:
            continue
        result = []
        for index, row in enumerate(rows):
            usage = _mapping(row.get("usage"))
            result.append({
                "request_id": _first_string(row.get("request_id"), row.get("id"),
                                            row.get("request"), f"req-{index}"),
                "arrival_ms": _first_float(row.get("arrival_ms"), row.get("arrival"),
                                           row.get("arrive_ms")),
                "prompt_tokens": _first_int(row.get("prompt_tokens"), row.get("prompt_len"),
                                            row.get("input_len"), row.get("context_tokens"),
                                            usage.get("prompt_tokens")),
                "output_tokens": _first_int(row.get("output_tokens"),
                                             row.get("requested_max_tokens"),
                                             row.get("decode_steps"), row.get("max_tokens"),
                                             row.get("completion_tokens"),
                                             usage.get("completion_tokens")),
                "prefix_tokens": _first_int(row.get("prefix_tokens"), row.get("prefix_len")) or 0,
                "source": source,
            })
        return result
    return []

def _request_gaps(requests: Sequence[Mapping[str, Any]]) -> list[str]:
    gaps: list[str] = []
    for index, request in enumerate(requests):
        if not isinstance(request, Mapping):
            gaps.append(f"workload.requests[{index}]")
            continue
        if not _first_string(request.get("request_id"), request.get("id")):
            gaps.append(f"workload.requests[{index}].request_id")
        for field, aliases in (
            ("prompt_tokens", ("prompt_tokens", "prompt_len", "input_len")),
            ("output_tokens", ("output_tokens", "requested_max_tokens", "decode_steps")),
        ):
            value = _first_int(*(request.get(alias) for alias in aliases))
            if value is None or value < 0:
                gaps.append(f"workload.requests[{index}].{field}")
        if _first_float(request.get("arrival_ms"), request.get("arrival")) is None:
            gaps.append(f"workload.requests[{index}].arrival_ms")
    return gaps

def _case_request_gaps(value: Mapping[str, Any]) -> list[str]:
    workload = _mapping(value.get("workload"))
    requests = workload.get("requests")
    if not isinstance(requests, Sequence) or isinstance(requests, (str, bytes)) or not requests:
        return ["workload.requests"]
    return _request_gaps([item for item in requests if isinstance(item, Mapping)])

def _workload(overrides: Mapping[str, Any], run_meta: Mapping[str, Any], bench: Mapping[str, Any], client: Mapping[str, Any], env: Mapping[str, str], record: Mapping[str, Any], report: Mapping[str, Any], cell_tag: str | None = None) -> dict[str, Any]:
    declared, summary, scene = _mapping(run_meta.get("workload")), _mapping(bench.get("summary")), _mapping(report.get("scene"))
    design, prof_cfg = _mapping(summary.get("design")) or _mapping(bench.get("design")), _mapping(summary.get("profile"))
    reqs = bench.get("requests") if isinstance(bench.get("requests"), Sequence) and not isinstance(bench.get("requests"), (str, bytes)) else (client.get("per_request") if isinstance(client.get("per_request"), Sequence) and not isinstance(client.get("per_request"), (str, bytes)) else ())
    req0 = _mapping(reqs[0]) if reqs else {}
    request_records = _request_records(run_meta, bench, client, record)
    if request_records:
        if overrides.get("batch_size") is not None:
            try:
                request_records = request_records[:max(1, int(overrides["batch_size"]))]
            except (TypeError, ValueError):
                pass
        if overrides.get("seq_len") is not None:
            for row in request_records:
                row["prompt_tokens"] = int(overrides["seq_len"])
        if overrides.get("decode_steps") is not None:
            for row in request_records:
                row["output_tokens"] = int(overrides["decode_steps"])
    request_count = len(request_records) if request_records else (len(reqs) if reqs else None)
    batch = _first_int(overrides.get("batch_size"), declared.get("batch_size"), declared.get("concurrency"), summary.get("concurrency"), bench.get("concurrency"), client.get("concurrency"), scene.get("concurrency"), record.get("concurrency"), request_count, env.get("CONCURRENCY"))
    obs_p = next((x[0] for x in (client.get("observed_prompt_tokens"), bench.get("observed_prompt_tokens")) if isinstance(x, Sequence) and not isinstance(x, (str, bytes)) and x), None)
    pref_suf = next((p + (_first_int(s.get("suffix_len")) or 0) for s in (bench, client) if (p := _first_int(s.get("prefix_len"))) is not None), None)
    seq = _first_int(overrides.get("seq_len"), declared.get("seq_len"), declared.get("prompt_tokens"), declared.get("input_len"), declared.get("context_tokens"), design.get("seq_len"), design.get("prompt_tokens"), design.get("input_len"), bench.get("prompt_tokens"), client.get("prompt_tokens"), bench.get("seq_len"), client.get("seq_len"), bench.get("input_len"), client.get("input_len"), req0.get("prompt_tokens"), _mapping(req0.get("usage")).get("prompt_tokens"), obs_p, pref_suf, record.get("context_tokens"), record.get("seq_len"), scene.get("seq_len"), env.get("INPUT_LEN"))
    out_tot, n_ok = _first_int(summary.get("out_tokens")), _first_int(summary.get("n_ok"), summary.get("concurrency"), batch)
    per_req_out = int(round(out_tot / max(1, n_ok or 1))) if (out_tot is not None and out_tot > 0) else None
    direct_decode = _first_int(overrides.get("decode_steps"), declared.get("decode_steps"), declared.get("output_len"), declared.get("output_tokens"), design.get("decode_steps"), design.get("output_len"), design.get("max_tokens"), prof_cfg.get("profile_max_tokens"), req0.get("requested_max_tokens"), req0.get("completion_tokens"), _mapping(req0.get("usage")).get("completion_tokens"), bench.get("decode_len"), bench.get("output_len"), bench.get("output_tokens"), client.get("decode_len"), client.get("output_len"), client.get("output_tokens"), record.get("decode_steps"), record.get("output_len"), scene.get("decode_steps"), env.get("OUTPUT_LEN"))
    decode = direct_decode if direct_decode is not None else per_req_out
    prefix = _first_int(declared.get("prefix_len"), declared.get("shared_tokens"), design.get("prefix_len"), design.get("shared_tokens"), bench.get("shared_tokens"), client.get("shared_tokens"), bench.get("prefix_tokens"), client.get("prefix_tokens"), record.get("prefix_len"), env.get("PREFIX_LEN"), env.get("SHARED_TOKENS"))
    if prefix is None and (reuse := _first_float(bench.get("prefix_cache_reuse_ratio"), client.get("prefix_cache_reuse_ratio"))) is not None and 0.0 <= reuse <= 1.0:
        prefix = int(round((4096 if seq is None else seq) * reuse))
    phase_cands = (overrides.get("phase"), declared.get("phase"), declared.get("mode"), bench.get("phase"), bench.get("mode"), summary.get("phase"), summary.get("mode"), record.get("phase"), record.get("mode"), scene.get("phase"), scene.get("mode"), env.get("PHASE"), env.get("MODE"))
    raw_phase = _first_string(overrides.get("phase")) or next((s.strip() for s in phase_cands if isinstance(s, str) and s.strip().lower().startswith(("decode", "prefill"))), None) or ("prefill" if (cell_tag and "prefill" in cell_tag.lower()) else "decode")
    phase_low = str(raw_phase).strip().lower()
    phase = "prefill" if phase_low.startswith("prefill") else "decode" if phase_low.startswith("decode") else phase_low
    batch_val, seq_val, dec_val = (1 if batch is None else batch), (4096 if seq is None else seq), (128 if decode is None else decode)
    if batch_val < 1 or batch_val > 4096: raise ProfilerUsageError(f"invalid simulation case: batch_size_out_of_bounds:{batch_val}")
    if seq_val < 1 or dec_val < 1 or (prefix is not None and prefix < 0): raise ProfilerUsageError(f"invalid simulation case: workload_dimensions_out_of_bounds:seq={seq_val},decode={dec_val},prefix={prefix}")
    return {
        "batch_size": batch_val, "seq_len": seq_val,
        "decode_steps": dec_val,
        "prefix_len": 0 if prefix is None else min(prefix, seq_val),
        "phase": phase,
        "_explicit": {
            "batch_size": bool(request_records) or batch is not None,
            "seq_len": bool(request_records) or seq is not None,
            "decode_steps": bool(request_records) or direct_decode is not None,
            "phase": raw_phase is not None,
            "requests": bool(request_records),
        },
        "_requests": request_records,
        "_aggregate": {
            "out_tokens": out_tot, "n_ok": n_ok,
            "per_request_output": per_req_out,
            "decode_from_aggregate": bool(direct_decode is None and per_req_out is not None),
        },
    }

def _extract_facts(bundle: Mapping[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    js = bundle.get("json", {})
    raw_rm, bench, client = _mapping(js.get("run_meta")), _mapping(js.get("benchmark_summary")), _mapping(js.get("client_cell"))
    run_meta = {**{k: v for s in (client, bench) for k, v in s.items() if k not in ("summary", "metrics", "profile")}, **raw_rm}
    raw_cfg = _mapping(js.get("model_config"))
    config = {**_mapping(raw_cfg.get("text_config")), **_mapping(raw_cfg.get("language_config")), **_mapping(raw_cfg.get("llm_config")), **raw_cfg}
    capture, provenance = _mapping(js.get("capture")), _mapping(js.get("provenance"))
    report, record = _mapping(bundle.get("report")), _mapping(bundle.get("case_record"))
    env, cmd = dict(bundle.get("env", {})), str(bundle.get("cmd", ""))
    cmd_main = _strip_spec_cmd(cmd)
    strings = _candidate_strings(run_meta, bench, client, capture, provenance, config, report, record, env, cmd_main, bundle.get("source_path"), bundle.get("root"))
    b_sum = _mapping(bench.get("summary"))
    cell_tag = _first_string(run_meta.get("cell_tag"), run_meta.get("cell"), run_meta.get("tag"), run_meta.get("label"), bench.get("cell"), bench.get("label"), b_sum.get("cell"), b_sum.get("label"), b_sum.get("tag"), client.get("cell"), client.get("label"), record.get("cell"), record.get("label"), record.get("cohort"), _mapping(report.get("scene")).get("label"), provenance.get("run_id"), capture.get("run_id")) or ((Path(str(bundle.get("source_path") or bundle.get("root"))).name or None) if (bundle.get("source_path") or bundle.get("root")) else None)
    execution_mode, graph_capture = _graph_mode(overrides.get("graph_mode"), run_meta, env, cmd_main, report, bench, record)
    acc_len = _first_float(record.get("mtp_acceptance_length"), record.get("acceptance_length"), run_meta.get("mtp_acceptance_length"), _mapping(run_meta.get("workload")).get("mtp_acceptance_length"), _mapping(report.get("scene")).get("mtp_acceptance_length"), bench.get("mtp_acceptance_length"), b_sum.get("mtp_acceptance_length"), env.get("MTP_ACCEPTANCE_LENGTH"))
    return {
        "hardware": _detect_hardware(overrides.get("chip"), run_meta, record, env, provenance, cell_tag, strings),
        "model": _detect_model(overrides.get("model"), run_meta, record, env, cmd_main, config, cell_tag, strings),
        "model_override": bool(overrides.get("model")),
        "sim_model": bundle.get("sim_model"),
        "structural": _structural_overrides(run_meta, env, config, record, report, bench, client, cmd),
        "mtp_acceptance_length": acc_len,
        "parallel": _parallel_overrides(overrides, run_meta, env, bench, client, report, cmd_main, cell_tag, record),
        "execution_mode": execution_mode, "graph_capture_mode": graph_capture,
        "hccl_op_expansion_mode": _hccl_mode(overrides.get("hccl_expansion_mode"), run_meta, env, cmd_main, bench, record),
        "quantization": _quantization(overrides.get("quant"), run_meta, env, cmd_main, config, bench, record),
        "workload": _workload(overrides, run_meta, bench, client, env, record, report, cell_tag),
        "runtime_facts": _runtime_facts(run_meta, bench, client, capture, report, record, env, cmd_main),
        "cell_tag": cell_tag, "source_kind": bundle.get("source_kind") or "mapping",
        "source_path": bundle.get("source_path"), "config": config,
    }

def _has_explicit_config(facts: Mapping[str, Any]) -> bool:
    cfg = _mapping(facts.get("config"))
    return bool(not facts.get("model_override") and "catalog_key" not in cfg and _first_int(cfg.get("hidden_size"), cfg.get("d_model"), cfg.get("hidden_dim")) and _first_int(cfg.get("num_attention_heads"), cfg.get("num_heads"), cfg.get("n_heads")))
