"""Bridge measured MindIE profiler captures into schema-valid mindie-sim Cases.

[Role] Deterministically normalize a Wave 5 benchmark capture, a profiler capture,
  a C7 summary/attribution report, or a Wave 5 case record into the five-key
  ``mindie-sim`` Case contract with post-simulation observed metadata.
[Invariants] Top-level keys are ``machine``, ``model``, ``workload``, ``runtime``
  and ``slo``; observed timings stay in ``runtime.metadata.observed_profile``;
  missing measurements stay ``None``; extraction is order-independent.
[Timeouts & Locks] Bounded metadata reads and streaming CSV scans; no locks/I/O side effects.
[Side-Effect Policy] ``export_sim_case`` reads only; CLI writes ``--output`` atomically.
"""
from __future__ import annotations
import argparse, csv, json, os, re, sys
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
def export_sim_case(input_path: str | Path | Mapping[str, Any], *, chip: str | None = None, model: str | None = None, tp: int | None = None, dp: int | None = None, ep: int | None = None, pp: int | None = None, batch_size: int | None = None, seq_len: int | None = None, decode_steps: int | None = None, phase: str | None = None, quant: str | None = None, graph_mode: str | None = None, hccl_expansion_mode: str | None = None, output: str | Path | None = None) -> dict[str, Any]:
    """Export ``input_path`` as a schema-valid simulation Case dictionary."""
    overrides = {"chip": chip, "model": model, "tp": tp, "dp": dp, "ep": ep, "pp": pp, "batch_size": batch_size, "seq_len": seq_len, "decode_steps": decode_steps, "phase": phase, "quant": quant, "graph_mode": graph_mode, "hccl_expansion_mode": hccl_expansion_mode}
    applied = sorted(k for k, v in overrides.items() if v is not None and v != "")
    bundle = _load_input(input_path)
    facts = _extract_facts(bundle, overrides)
    observed = _extract_observed(bundle, facts)
    case = _build_case(facts, observed, applied)
    if output is not None:
        from .report import write_report
        write_report(case, output)
    return case
def _load_input(source: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(source, Mapping): return _bundle_from_mapping(dict(source), None)
    try: path = Path(source).expanduser().resolve()
    except TimeoutError: raise
    except OSError as exc: raise ProfilerUsageError(f"cannot resolve input: {exc}") from exc
    if path.is_dir(): return _bundle_from_dir(path)
    if not path.is_file(): raise ProfilerUsageError(f"input does not exist: {path}")
    suffix = path.suffix.lower()
    if suffix == ".json": return _bundle_from_mapping(_read_json(path), path)
    if suffix in {".env", ".sh", ".txt"}:
        text, bundle = _read_text(path), {**_empty_bundle(path.parent), "source_kind": "metadata_file"}
        if suffix == ".env": bundle.update(env=_parse_env(text), text=text)
        else: bundle["cmd"] = text
        return bundle
    raise ProfilerUsageError(f"unsupported input file type: {path.suffix or path.name}")
def _empty_bundle(root: Path | None) -> dict[str, Any]:
    return {"root": root, "json": {}, "env": {}, "cmd": "", "csv": {}, "report": None, "case_record": None, "source_kind": "directory", "source_path": None}
def _bundle_from_dir(root: Path) -> dict[str, Any]:
    bundle = {**_empty_bundle(root), "source_path": str(root)}
    files = _iter_files(root)
    for path in files:
        name = path.name.lower()
        if name in _JSON_NAMES:
            payload, key = _read_json(path), _JSON_NAMES[name]
            if key == "report" and _is_c7_report(payload): bundle["report"] = payload
            elif key != "report" and key not in bundle["json"]: bundle["json"][key] = payload
            if key == "run_meta" and isinstance(payload, Mapping) and isinstance(payload.get("env"), Mapping):
                bundle["env"].update({str(k): str(v) for k, v in payload["env"].items()})
        elif name == "meta.env": bundle["env"].update(_parse_env(_read_text(path)))
        elif name == "cmd.sh": bundle["cmd"] = _read_text(path)
        elif name in _CSV_NAMES and name not in bundle["csv"]: bundle["csv"][name] = path
    if bundle["report"] is None: bundle["report"] = next((p for p in bundle["json"].values() if _is_c7_report(p)), None)
    has_wave = bool({"run_meta", "benchmark_summary", "client_cell"} & bundle["json"].keys() or bundle["env"] or bundle["cmd"] or {"op_statistic.csv", "step_trace_time.csv", "api_statistic.csv"} & bundle["csv"].keys())
    has_prof = bool({"capture", "provenance"} & bundle["json"].keys() or "kernel_details.csv" in bundle["csv"] or any(("ascend_pytorch_profiler" in p.name and p.suffix == ".db") or any(part.startswith("rank_") for part in p.parts) for p in files))
    bundle["source_kind"] = ("capture_directory" if (has_wave and has_prof) else "wave5_capture" if has_wave else "profiler_capture" if has_prof else "directory")
    bundle["case_record"] = _find_case_record(bundle)
    return bundle
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
def _bundle_from_mapping(payload: Mapping[str, Any], path: Path | None) -> dict[str, Any]:
    bundle = _empty_bundle(path.parent if path is not None else None)
    bundle["source_path"] = str(path) if path is not None else None
    data = dict(payload)
    for key in ("run_meta", "benchmark_summary", "client_cell", "capture", "provenance"):
        if isinstance(data.get(key), Mapping): bundle["json"][key] = dict(data[key])
    cfg = data.get("model_config") or data.get("config")
    if isinstance(cfg, Mapping): bundle["json"]["model_config"] = dict(cfg)
    is_sim = isinstance(data, Mapping) and {"machine", "model", "workload"} <= set(data)
    if is_sim and isinstance(data.get("model"), Mapping):
        sm = {k: (dict(v) if isinstance(v, Mapping) else v) for k, v in data["model"].items() if k not in ("n_routed_experts", "num_experts_per_tok", "model_type")}
        if "num_experts" not in sm and data["model"].get("n_routed_experts") is not None: sm["num_experts"] = data["model"]["n_routed_experts"]
        if "top_k" not in sm and data["model"].get("num_experts_per_tok") is not None: sm["top_k"] = data["model"]["num_experts_per_tok"]
        bundle["sim_model"] = sm
    elif not is_sim and "model_config" not in bundle["json"] and any(k in data or k in _mapping(data.get("text_config")) for k in ("hidden_size", "num_attention_heads", "num_hidden_layers", "kv_lora_rank")):
        bundle["json"]["model_config"] = dict(data)
    if _is_c7_report(data): bundle["report"], bundle["source_kind"] = data, "c7_report"
    elif is_sim or _looks_like_case_record(data):
        bundle["case_record"] = _flatten_record(data)
        bundle["source_kind"] = "sim_case" if is_sim else "wave5_case_record"
    elif path is not None and path.name.lower() == "run_meta.json":
        bundle["json"]["run_meta"], bundle["source_kind"] = {**data, **bundle["json"].get("run_meta", {})}, "run_meta"
    elif (path is not None and ("client_cell" in path.name.lower() or "client-cell" in path.name.lower())) or (any(k in data for k in ("step_ms_client", "tokens_per_step_client", "cell_metrics")) and not any(k in data for k in ("kernel_stats", "tpot_client_ms", "step_time_client_ms", "top_operators"))):
        bundle["json"]["client_cell"], bundle["source_kind"] = {**data, **bundle["json"].get("client_cell", {})}, "client_cell"
    elif (path is not None and path.name.lower() == "benchmark_summary.json") or any(k in data for k in ("kernel_stats", "tpot_client_ms", "tpot_tok_ms", "step_time_client_ms", "step_ms", "ttft_ms", "tensor_parallel_size", "step_time_ms", "top_operators")) or (isinstance(data.get("summary"), Mapping) and any(k in data["summary"] for k in ("concurrency", "cell", "design", "tpot_p50_ms", "tpot_true_p50_ms", "ttft_p50_ms", "step_from_metrics_ms"))):
        bundle["json"]["benchmark_summary"], bundle["source_kind"] = {**data, **bundle["json"].get("benchmark_summary", {})}, "benchmark_summary"
    elif any(k in data for k in ("per_request", "profile_window")):
        bundle["json"]["client_cell"], bundle["source_kind"] = {**data, **bundle["json"].get("client_cell", {})}, "client_cell"
    elif any(k in data for k in ("npu_type", "model_name", "parallelism", "weight_path", "architecture_override")):
        bundle["json"]["run_meta"], bundle["source_kind"] = {**data, **bundle["json"].get("run_meta", {})}, "run_meta"
    elif "run_meta" in bundle["json"] or "benchmark_summary" in bundle["json"]:
        bundle["source_kind"] = "benchmark_summary" if "benchmark_summary" in bundle["json"] and "run_meta" not in bundle["json"] else "run_meta"
    elif path is not None:
        name = path.name.lower()
        if name in _JSON_NAMES and _JSON_NAMES[name] != "report":
            bundle["json"][_JSON_NAMES[name]] = {**data, **bundle["json"].get(_JSON_NAMES[name], {})}
            bundle["source_kind"] = _JSON_NAMES[name]
        elif name in {"summary.json", "attribution.json"}: bundle["source_kind"] = "c7_report"
        else: bundle["json"]["run_meta"], bundle["source_kind"] = data, "metadata_json"
    else: bundle["case_record"], bundle["source_kind"] = _flatten_record(data), "mapping"
    for env_src in (_mapping(bundle["json"].get("run_meta")).get("env"), data.get("env")):
        if isinstance(env_src, Mapping): bundle["env"].update({str(k): str(v) for k, v in env_src.items()})
    if bundle["case_record"] is None: bundle["case_record"] = _find_case_record(bundle)
    return bundle
def _find_case_record(bundle: Mapping[str, Any]) -> dict[str, Any] | None:
    for value in (bundle.get("report"), *bundle.get("json", {}).values()):
        if not isinstance(value, Mapping): continue
        if _looks_like_case_record(value): return _flatten_record(value)
        for key in ("cases", "captures", "heldout_cases"):
            items = value.get(key)
            if isinstance(items, Sequence) and not isinstance(items, (str, bytes)):
                for item in items:
                    if isinstance(item, Mapping) and _looks_like_case_record(item): return _flatten_record(item)
    return None
def _walk_err(exc: OSError) -> None:
    if isinstance(exc, TimeoutError): raise exc
    raise ProfilerUsageError(f"cannot scan directory: {exc}") from exc
def _iter_files(root: Path, max_depth: int = 4, max_files: int = 4096) -> list[Path]:
    found: list[Path] = []
    for current, dirs, names in os.walk(root, onerror=_walk_err):
        depth = len(Path(current).relative_to(root).parts)
        dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS and depth < max_depth)
        for name in sorted(names):
            found.append(Path(current) / name)
            if len(found) >= max_files: return found
    return sorted(found, key=lambda item: (len(item.relative_to(root).parts), str(item)))
def _read_json(path: Path) -> Any:
    try:
        if path.stat().st_size > 50 * 1024**2: raise ProfilerUsageError(f"JSON metadata exceeds 50 MiB: {path}")
        with path.open(encoding="utf-8") as stream: return json.load(stream)
    except TimeoutError: raise
    except json.JSONDecodeError as exc: raise ProfilerUsageError(f"invalid JSON in {path}: {exc}") from exc
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
    return {"hardware": _detect_hardware(overrides.get("chip"), run_meta, record, env, provenance, cell_tag, strings), "model": _detect_model(overrides.get("model"), run_meta, record, env, cmd_main, config, cell_tag, strings), "model_override": bool(overrides.get("model")), "sim_model": bundle.get("sim_model"), "structural": _structural_overrides(run_meta, env, config, record, report, bench, client, cmd), "mtp_acceptance_length": acc_len, "parallel": _parallel_overrides(overrides, run_meta, env, bench, client, report, cmd_main, cell_tag, record), "execution_mode": execution_mode, "graph_capture_mode": graph_capture, "hccl_op_expansion_mode": _hccl_mode(overrides.get("hccl_expansion_mode"), run_meta, env, cmd_main, bench, record), "quantization": _quantization(overrides.get("quant"), run_meta, env, cmd_main, config, bench, record), "workload": _workload(overrides, run_meta, bench, client, env, record, report, cell_tag), "cell_tag": cell_tag, "source_kind": bundle.get("source_kind") or "mapping", "source_path": bundle.get("source_path"), "config": config}
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
def _detect_hardware(override: Any, run_meta: Mapping[str, Any], record: Mapping[str, Any], env: Mapping[str, str], provenance: Mapping[str, Any], cell_tag: str | None, strings: Sequence[str]) -> str:
    if strict_val := _first_string(override, run_meta.get("npu_type"), run_meta.get("hardware"), run_meta.get("chip"), record.get("hw"), env.get("NPU_TYPE")):
        if res := _resolve_hw_token(strict_val, strict=True): return res
    return next((res for text in (run_meta.get("host"), provenance.get("source"), cell_tag, *strings) if isinstance(text, str) and text.strip() and (res := _resolve_hw_token(text, strict=False))), _A3)
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
def _detect_model(override: Any, run_meta: Mapping[str, Any], record: Mapping[str, Any], env: Mapping[str, str], cmd: str, config: Mapping[str, Any], cell_tag: str | None, strings: Sequence[str]) -> str | None:
    if isinstance(override, str) and override.strip(): return _match_model(override) or override.strip()
    m_srv = re.search(r"(?:vllm\s+serve|--model|--served-model-name|--weight-path)(?:=|\s+)['\"]?([^\s'\"]+)", cmd)
    explicit = (run_meta.get("model_name"), run_meta.get("weight_path"), run_meta.get("architecture_override"), record.get("model_name"), record.get("family"), env.get("MODEL_NAME"), env.get("WEIGHT_PATH"), _config_identity(config), m_srv.group(1) if m_srv else None)
    for value in (*explicit, cmd, cell_tag, *strings):
        found = _match_model(value)
        if found: return found
    return _first_string(*explicit)
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
def _normalize_quant(value: Any) -> str | None:
    text = str(value or "").strip().lower().replace("-", "").replace("_", "")
    return next((norm for pat, norm in (("w8a8mxfp8", "w8a8_mxfp8"), ("mxfp8", "mxfp8"), ("w8a8", "w8a8"), ("w4a8", "w4a8"), ("fp8", "fp8"), ("int8", "w8a8"), ("bf16", "bf16"), ("fp16", "fp16")) if pat in text), None)
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
def _workload(overrides: Mapping[str, Any], run_meta: Mapping[str, Any], bench: Mapping[str, Any], client: Mapping[str, Any], env: Mapping[str, str], record: Mapping[str, Any], report: Mapping[str, Any], cell_tag: str | None = None) -> dict[str, Any]:
    declared, summary, scene = _mapping(run_meta.get("workload")), _mapping(bench.get("summary")), _mapping(report.get("scene"))
    design, prof_cfg = _mapping(summary.get("design")) or _mapping(bench.get("design")), _mapping(summary.get("profile"))
    reqs = bench.get("requests") if isinstance(bench.get("requests"), Sequence) and not isinstance(bench.get("requests"), (str, bytes)) else (client.get("per_request") if isinstance(client.get("per_request"), Sequence) and not isinstance(client.get("per_request"), (str, bytes)) else ())
    req0 = _mapping(reqs[0]) if reqs else {}
    batch = _first_int(overrides.get("batch_size"), declared.get("batch_size"), declared.get("concurrency"), summary.get("concurrency"), bench.get("concurrency"), client.get("concurrency"), scene.get("concurrency"), record.get("concurrency"), env.get("CONCURRENCY"))
    obs_p = next((x[0] for x in (client.get("observed_prompt_tokens"), bench.get("observed_prompt_tokens")) if isinstance(x, Sequence) and not isinstance(x, (str, bytes)) and x), None)
    pref_suf = next((p + (_first_int(s.get("suffix_len")) or 0) for s in (bench, client) if (p := _first_int(s.get("prefix_len"))) is not None), None)
    seq = _first_int(overrides.get("seq_len"), declared.get("seq_len"), declared.get("prompt_tokens"), declared.get("input_len"), declared.get("context_tokens"), design.get("seq_len"), design.get("prompt_tokens"), design.get("input_len"), bench.get("prompt_tokens"), client.get("prompt_tokens"), bench.get("seq_len"), client.get("seq_len"), bench.get("input_len"), client.get("input_len"), req0.get("prompt_tokens"), _mapping(req0.get("usage")).get("prompt_tokens"), obs_p, pref_suf, record.get("context_tokens"), record.get("seq_len"), scene.get("seq_len"), env.get("INPUT_LEN"))
    out_tot, n_ok = _first_int(summary.get("out_tokens")), _first_int(summary.get("n_ok"), summary.get("concurrency"), batch)
    per_req_out = int(round(out_tot / max(1, n_ok or 1))) if (out_tot is not None and out_tot > 0) else None
    decode = _first_int(overrides.get("decode_steps"), declared.get("decode_steps"), declared.get("output_len"), declared.get("output_tokens"), design.get("decode_steps"), design.get("output_len"), design.get("max_tokens"), prof_cfg.get("profile_max_tokens"), req0.get("requested_max_tokens"), req0.get("completion_tokens"), _mapping(req0.get("usage")).get("completion_tokens"), bench.get("decode_len"), bench.get("output_len"), bench.get("output_tokens"), client.get("decode_len"), client.get("output_len"), client.get("output_tokens"), per_req_out, record.get("decode_steps"), record.get("output_len"), scene.get("decode_steps"), env.get("OUTPUT_LEN"))
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
    return {"batch_size": batch_val, "seq_len": seq_val, "decode_steps": dec_val, "prefix_len": 0 if prefix is None else min(prefix, seq_val), "phase": phase}
def _empty_observed() -> dict[str, Any]:
    return {"step_time_ms": None, "tpot_p50_ms": None, "ttft_p50_ms": None, "device_busy_union_ms": None, "device_activity_sum_ms": None, "exposed_comm_ms": None, "device_uncovered_ms": None, "cube_share": None, "vector_share": None, "hccl_share": None, "comm_share": None, "aicpu_share": None, "host_share": None, "attention_share": None, "moe_share": None, "kv_peak_ratio": None, "dominant_bottleneck": "compute_bound", "top_operators": []}
def _merge_observed(target: dict[str, Any], incoming: Mapping[str, Any]) -> None:
    for key, value in incoming.items():
        if key not in target or value is None: continue
        if key == "top_operators":
            if value and not target.get(key): target[key] = list(value)[:10]
        elif target.get(key) is None: target[key] = value
def _extract_observed(bundle: Mapping[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    observed = _empty_observed()
    js = bundle.get("json", {})
    run_meta = _mapping(js.get("run_meta"))
    bench = _mapping(js.get("benchmark_summary")) or _mapping(run_meta.get("metrics"))
    client, capture = _mapping(js.get("client_cell")), _mapping(js.get("capture"))
    report, record = _mapping(bundle.get("report")), _mapping(bundle.get("case_record"))
    _merge_observed(observed, _observed_from_report(report))
    _merge_observed(observed, _observed_from_benchmark(bench))
    if facts.get("hccl_op_expansion_mode") == "unspecified":
        for op in (bench.get("top_operators") or _mapping(bench.get("kernel_stats")).get("top_operators_by_device_time") or ()):
            if isinstance(op, Mapping) and _is_comm(op.get("op_type") or op.get("name")):
                cu = str(op.get("core_type") or op.get("accelerator_core") or op.get("core") or "").upper()
                if "CPU" in cu: facts["hccl_op_expansion_mode"] = "aicpu"; break
                if "VECTOR" in cu or "AIV" in cu: facts["hccl_op_expansion_mode"] = "aiv"; break
    if not facts.get("quantization") and not facts.get("sim_model"): facts["quantization"] = _quant_from_operators(observed.get("top_operators", []))
    _merge_observed(observed, {"step_time_ms": _stat_median(client.get("step_ms_client")) or _stat_median(client.get("step_ms")), "tpot_p50_ms": _stat_median(client.get("tpot_ms")) or _stat_median(client.get("tpot_tok_ms")), "ttft_p50_ms": _stat_median(client.get("ttft_ms"))} if client else {})
    _merge_observed(observed, {"step_time_ms": _first_float(record.get("observed_ms"), record.get("step_time_ms")), "tpot_p50_ms": _first_float(record.get("tpot_p50_ms"), record.get("tpot_ms")), "ttft_p50_ms": _first_float(record.get("ttft_p50_ms"), record.get("ttft_ms")), "device_busy_union_ms": _first_float(record.get("device_busy_union_ms")), "device_activity_sum_ms": _first_float(record.get("device_activity_sum_ms")), "exposed_comm_ms": _first_float(record.get("exposed_comm_ms")), "device_uncovered_ms": _first_float(record.get("device_uncovered_ms"))} if record else {})
    active = _mapping(_mapping(capture.get("steps")).get("active"))
    _merge_observed(observed, {"step_time_ms": _first_float(active.get("mean_ms"), active.get("min_ms")), "tpot_p50_ms": _first_float(capture.get("tpot_p50_ms")), "ttft_p50_ms": _first_float(capture.get("ttft_p50_ms"))} if capture else {})
    for obs_meta in (_mapping(run_meta.get("observed_profile")), _mapping(run_meta.get("observed")), _mapping(record.get("observed_profile"))):
        if obs_meta: _merge_observed(observed, {k: obs_meta.get(k) for k in observed if k in obs_meta})
    step_trace = _csv_path(bundle, "step_trace_time.csv")
    trace_obs = _observed_from_step_trace(step_trace) if step_trace else {}
    if trace_obs: _merge_observed(observed, trace_obs)
    scanned_kernel = False
    for csv_name in ("op_statistic.csv", "kernel_details.csv"):
        cpath = _csv_path(bundle, csv_name)
        if cpath and (not observed["top_operators"] or observed["device_activity_sum_ms"] is None or facts.get("hccl_op_expansion_mode") == "unspecified" or any(observed[k] is None for k in ("cube_share", "vector_share"))):
            if csv_name == "kernel_details.csv": scanned_kernel = True
            obs_c, hccl_c, quant_c = _observed_from_op_csv(cpath)
            _merge_observed(observed, obs_c)
            if facts.get("hccl_op_expansion_mode") == "unspecified" and hccl_c != "unspecified": facts["hccl_op_expansion_mode"] = hccl_c
            if not facts.get("quantization") and quant_c: facts["quantization"] = quant_c
    if not facts.get("quantization") and not scanned_kernel and _csv_path(bundle, "kernel_details.csv"): facts["quantization"] = _quant_from_kernel_file(_csv_path(bundle, "kernel_details.csv"))  # type: ignore[arg-type]
    if observed["host_share"] is None and _csv_path(bundle, "api_statistic.csv"):
        win_s = _first_float(_mapping(_mapping(_mapping(bench.get("summary")).get("profile"))).get("window_s"), _mapping(client.get("profile_window")).get("engine_window_s"), _mapping(run_meta.get("profile")).get("window_s"), run_meta.get("window_s"))
        busy, uncov = observed.get("device_busy_union_ms"), observed.get("device_uncovered_ms")
        ref_step = observed.get("step_time_ms") or ((busy + (uncov or 0.0)) if busy is not None else None) or observed.get("device_activity_sum_ms")
        n_steps = _first_int(trace_obs.get("_steps"), _mapping(_mapping(client.get("profile_window")).get("metrics")).get("steps_in_window"), _mapping(bench.get("summary")).get("scheduler_steps"), active.get("count"))
        win_ms = (win_s * 1000.0 if (win_s and win_s > 0) else None) or _first_float(trace_obs.get("_win_ms")) or ((n_steps * ref_step) if (n_steps and ref_step) else None)
        _merge_observed(observed, _observed_from_api(_csv_path(bundle, "api_statistic.csv"), win_ms, ref_step))  # type: ignore[arg-type]
    _finalize_observed(observed, facts)
    return observed
def _observed_from_report(report: Mapping[str, Any]) -> dict[str, Any]:
    if not report: return {}
    acct_holder = _mapping(report.get("accounting")) if isinstance(report.get("accounting"), Mapping) else report
    acc, windows = _mapping(acct_holder.get("step_accounting")), acct_holder.get("window_accounting")
    win = _mapping(windows[0]) if isinstance(windows, Sequence) and not isinstance(windows, (str, bytes)) and windows else _mapping(windows)
    values: dict[str, Any] = {"step_time_ms": _first_float(acc.get("step_time_ms"), acc.get("step_ms"), acc.get("step_time_ms_p50"), acc.get("step_ms_p50")), "device_busy_union_ms": _first_float(acc.get("device_busy_union_ms_p50"), acc.get("busy_union_ms_p50"), acc.get("device_busy_union_ms"), win.get("device_busy_union_ms_p50"), win.get("busy_union_ms_p50"), win.get("device_busy_union_ms"), win.get("busy_union_ms")), "device_activity_sum_ms": _first_float(acc.get("device_activity_sum_ms_p50"), acc.get("kernel_sum_ms_p50"), acc.get("device_activity_sum_ms"), win.get("device_activity_sum_ms_p50"), win.get("kernel_sum_ms_p50"), win.get("device_activity_sum_ms"), win.get("kernel_sum_ms")), "exposed_comm_ms": _first_float(acc.get("exposed_comm_ms_p50"), acc.get("exposed_comm_ms"), win.get("exposed_comm_ms_p50"), win.get("exposed_comm_ms")), "device_uncovered_ms": _first_float(acc.get("device_uncovered_ms_p50"), acc.get("host_gap_ms_p50"), acc.get("device_uncovered_ms"), win.get("device_uncovered_ms_p50"), win.get("host_gap_ms_p50"), win.get("device_uncovered_ms"), win.get("host_gap_ms")), "aicpu_share": _ratio(_first_float(acc.get("aicpu_exposed_ratio"), acc.get("aicpu_exposed_ratio_p50"), acc.get("aicpu_share"), win.get("aicpu_exposed_ratio_p50"), win.get("aicpu_exposed_ratio"), win.get("aicpu_share"))), "host_share": _ratio(_first_float(acc.get("underfeed_bubble_ratio"), acc.get("underfeed_bubble_ratio_p50"), acc.get("host_share"), win.get("underfeed_bubble_ratio_p50"), win.get("underfeed_bubble_ratio"), win.get("host_share")))}
    block_map = {"Attention": "attention_share", "MoE": "moe_share", "Comm": "comm_share", "Communication": "comm_share", "HCCL": "comm_share", "Cube": "cube_share", "Cube_Core": "cube_share", "Vector": "vector_share", "Vector_Core": "vector_share", "Host_Gap": "host_share", "Host": "host_share", "AICPU": "aicpu_share", "AI_CPU": "aicpu_share"}
    blocks = report.get("semantic_block_breakdown")
    if isinstance(blocks, Sequence) and not isinstance(blocks, (str, bytes)):
        for item in blocks:
            if isinstance(item, Mapping) and str(item.get("block") or "") in block_map:
                val = _pct(item.get("share_of_busy_pct")) if item.get("share_of_busy_pct") is not None else _ratio(item.get("share"))
                target = block_map[str(item.get("block"))]
                if val is not None and values.get(target) is None: values[target] = val
        if values.get("comm_share") is not None and values.get("hccl_share") is None: values["hccl_share"] = values["comm_share"]
    hotspots = report.get("top_hotspot_kernels")
    if isinstance(hotspots, Sequence) and hotspots:
        rows, denom_ms = [], _first_float(values.get("device_activity_sum_ms"), values.get("device_busy_union_ms"))
        for item in hotspots:
            if not isinstance(item, Mapping) or len(rows) >= 10: continue
            sh = _pct(item.get("share_of_busy_pct")) if item.get("share_of_busy_pct") is not None else _ratio(item.get("share"))
            if sh is None and denom_ms and denom_ms > 0 and (dur_ms := _first_float(item.get("measured_device_ms_total"), item.get("measured_device_ms_p50"))) is not None:
                sh = _ratio(dur_ms / denom_ms)
            name = item.get("kernel_name") or item.get("op_type") or item.get("name")
            rows.append({"name": name, "op_type": name, "count": _first_int(item.get("call_count")), "total_time_ms": _first_float(item.get("measured_device_ms_total")), "avg_time_ms": _first_float(item.get("measured_device_ms_p50")), "share": sh})
        values["top_operators"] = rows
    for key in ("tpot_p50_ms", "ttft_p50_ms"):
        val = _first_float(report.get(key), _mapping(report.get("summary")).get(key))
        if val is not None: values[key] = val
    return values
def _observed_from_benchmark(bench: Mapping[str, Any]) -> dict[str, Any]:
    if not bench: return {}
    kernel, summary = _mapping(bench.get("kernel_stats")), _mapping(bench.get("summary"))
    device_us = _first_float(kernel.get("total_device_time_us"), bench.get("total_device_time_us"))
    values: dict[str, Any] = {"step_time_ms": _stat_median(bench.get("step_time_client_ms")) or _stat_median(bench.get("step_ms_client")) or _stat_median(bench.get("step_ms")) or _first_float(bench.get("step_time_ms"), summary.get("step_from_metrics_ms"), summary.get("step_time_ms")), "tpot_p50_ms": _stat_median(bench.get("tpot_client_ms")) or _stat_median(bench.get("tpot_tok_ms")) or _stat_median(bench.get("tpot_ms")) or _first_float(bench.get("tpot_measured_ms"), summary.get("tpot_true_p50_ms"), summary.get("tpot_p50_ms"), summary.get("itl_mean_p50_ms")), "ttft_p50_ms": _stat_median(bench.get("ttft_ms")) or _first_float(_mapping(bench.get("ttft_ms")).get("mean"), summary.get("ttft_p50_ms")), "device_activity_sum_ms": None if device_us is None else round(device_us / 1000.0, 6)}
    core = _mapping(kernel.get("by_accelerator_core"))
    if core:
        has_us = any(_first_float(_mapping(r).get("total_us")) is not None for r in core.values())
        field = "total_us" if has_us else "pct_of_device_time"
        total = sum(_first_float(_mapping(r).get(field)) or 0.0 for r in core.values())
        if total > 0:
            aic = (_first_float(_mapping(core.get("MIX_AIC")).get(field)) or 0.0) + (_first_float(_mapping(core.get("AI_CORE")).get(field)) or 0.0)
            aiv = (_first_float(_mapping(core.get("AI_VECTOR_CORE")).get(field)) or 0.0) + (_first_float(_mapping(core.get("MIX_AIV")).get(field)) or 0.0)
            comm_val, aicpu_val = _first_float(_mapping(core.get("COMMUNICATION")).get(field)) or 0.0, _first_float(_mapping(core.get("AI_CPU")).get(field)) or 0.0
            values["cube_share"], values["vector_share"] = (_ratio(aic / total) if has_us else _pct(aic)), (_ratio(aiv / total) if has_us else _pct(aiv))
            values["hccl_share"] = values["comm_share"] = _ratio(comm_val / total) if has_us else _pct(comm_val)
            values["aicpu_share"] = _ratio(aicpu_val / total) if has_us else _pct(aicpu_val)
    operators = bench.get("top_operators") or kernel.get("top_operators_by_device_time") or []
    if isinstance(operators, Sequence): values["top_operators"] = _normalize_operators(operators)
    if values.get("hccl_share") is None and values.get("top_operators"): values["hccl_share"] = values["comm_share"] = _share_from_names(values["top_operators"], _is_comm)
    if values.get("attention_share") is None and values.get("top_operators"):
        values["attention_share"], values["moe_share"] = _share_from_names(values["top_operators"], _is_attention), _share_from_names(values["top_operators"], _is_moe)
    kv = _find_kv_ratio(bench)
    if kv is not None: values["kv_peak_ratio"] = kv
    return {k: v for k, v in values.items() if v is not None}
def _observed_from_step_trace(path: Path) -> dict[str, Any]:
    cols = {"comp": ("Computing", "Computing(us)", "Computing Time(us)"), "comm": ("Communication", "Communication(us)"), "exp": ("Communication(Not Overlapped)", "Communication(Not Overlapped)(us)"), "over": ("Overlapped", "Overlapped(us)"), "free": ("Free", "Free(us)"), "stage": ("Stage", "Stage(us)")}
    by_dev: dict[str, dict[str, dict[str, float | None]]] = {}
    has_explicit_step = False
    for row in _iter_csv(path):
        dev = _row_text(row, ("Device_id", "device_id", "Rank ID", "rank_id")) or "0"
        raw_step = _row_text(row, ("Step ID", "Step", "step_id", "step"))
        if raw_step is not None: has_explicit_step = True
        sums = by_dev.setdefault(dev, {}).setdefault(raw_step or "_window", dict.fromkeys(cols))
        for k, keys in cols.items():
            val = _first_float(*(row.get(c) for c in keys))
            if val is not None: sums[k] = (sums[k] or 0.0) + val
    if not by_dev: return {}
    steps = list(by_dev[sorted(by_dev)[0]].values())
    def med_vals(items: Sequence[float | None]) -> float | None:
        vals = sorted(v for v in items if v is not None)
        return None if not vals else vals[len(vals) // 2] if len(vals) % 2 else (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2.0
    act_list = [((s["comp"] + s["comm"]) / 1000.0 if (s["comp"] is not None and s["comm"] is not None) else None) for s in steps]
    busy_list = [(((s["comp"] + s["exp"]) / 1000.0) if (s["comp"] is not None and s["exp"] is not None) else ((s["comp"] + s["comm"] - s["over"]) / 1000.0) if (s["comp"] is not None and s["comm"] is not None and s["over"] is not None) else ((s["stage"] - s["free"]) / 1000.0) if (s["stage"] is not None and s["free"] is not None) else a) for s, a in zip(steps, act_list)]
    act, busy = med_vals(act_list), med_vals(busy_list)
    exp, free, stage = med_vals([s["exp"] for s in steps]), med_vals([s["free"] for s in steps]), med_vals([s["stage"] for s in steps])
    if all(v is None for v in (act, busy, exp, free, stage)): return {}
    win_vals = [((s["stage"] / 1000.0) if s["stage"] is not None else ((b + (s["free"] / 1000.0 if s["free"] is not None else 0.0)) if b is not None else None)) for s, b in zip(steps, busy_list)]
    win_ms = sum(v for v in win_vals if v is not None) if any(v is not None for v in win_vals) else None
    return {"step_time_ms": (stage / 1000.0 if (has_explicit_step and stage is not None) else None), "device_busy_union_ms": busy, "device_activity_sum_ms": act if act is not None else busy, "exposed_comm_ms": None if exp is None else exp / 1000.0, "device_uncovered_ms": None if free is None else free / 1000.0, "_steps": len(steps) if has_explicit_step else 1, "_win_ms": win_ms}
def _observed_from_op_csv(path: Path) -> tuple[dict[str, Any], str, str | None]:
    total, by_core, by_op, has_cpu, comm_vec, q_tags = 0.0, {}, {}, False, False, set()
    for row in _iter_csv(path):
        name = _row_text(row, ("OP Type", "Op Type", "Name", "Kernel Name", "op_type")) or "unknown"
        core = _row_text(row, ("Core Type", "Accelerator Core", "Task Type", "core")) or "unknown"
        if q_hit := _quant_from_operators([name]): q_tags.add(q_hit)
        core_up = core.upper()
        if _is_comm(name) and "CPU" in core_up: has_cpu = True
        if _is_comm(name) and ("VECTOR" in core_up or "AIV" in core_up): comm_vec = True
        val = _row_duration_us(row)
        if val is None: continue
        total += val
        by_core[core] = by_core.get(core, 0.0) + val
        if (name, core) in by_op or len(by_op) < 4096:
            rec = by_op.setdefault((name, core), {"name": name, "op_type": name, "count": 0, "total_us": 0.0})
            rec["count"] += _first_int(row.get("Count"), row.get("count")) or 1
            rec["total_us"] += val
    hccl_mode, quant = ("aicpu" if has_cpu else "aiv" if comm_vec else "unspecified"), _quant_from_operators(tuple(q_tags))
    if total <= 0: return {}, hccl_mode, quant
    operators = [{"name": r["name"], "op_type": r["op_type"], "count": r["count"], "total_time_ms": round(r["total_us"] / 1000.0, 6), "share": _ratio(r["total_us"] / total)} for r in by_op.values()]
    operators.sort(key=lambda x: (x["total_time_ms"] or 0.0, str(x.get("name"))), reverse=True)
    hccl = _ratio((by_core.get("COMMUNICATION", 0.0) + by_core.get("HCCL", 0.0)) / total) or _share_from_names(operators, _is_comm)
    obs = {"device_activity_sum_ms": total / 1000.0, "cube_share": _ratio((by_core.get("AI_CORE", 0.0) + by_core.get("MIX_AIC", 0.0)) / total), "vector_share": _ratio((by_core.get("AI_VECTOR_CORE", 0.0) + by_core.get("MIX_AIV", 0.0)) / total), "hccl_share": hccl, "comm_share": hccl, "aicpu_share": _ratio(by_core.get("AI_CPU", 0.0) / total), "attention_share": _share_from_names(operators, _is_attention), "moe_share": _share_from_names(operators, _is_moe), "top_operators": operators[:10]}
    return obs, hccl_mode, quant
def _quant_from_operators(values: Sequence[Any]) -> str | None:
    names = " ".join(str(x.get("name") or x.get("op_type") or "") if isinstance(x, Mapping) else str(x) for x in values).lower()
    has_w8 = any(k in names for k in ("quantbatchmatmul", "dynamicquant", "w8a8"))
    if "w4a8" in names: return "w4a8"
    if "mxfp8" in names: return "w8a8_mxfp8" if has_w8 else "mxfp8"
    return "w8a8" if has_w8 else ("fp8" if "fp8" in names else None)
def _quant_from_kernel_file(path: Path) -> str | None:
    q_tags: set[str] = set()
    for idx, row in enumerate(_iter_csv(path)):
        if idx >= 200_000: break
        if q_hit := _quant_from_operators([_row_text(row, ("Name", "Kernel Name", "OP Type", "op_type"))]): q_tags.add(q_hit)
    return _quant_from_operators(tuple(q_tags))
def _observed_from_api(path: Path, cap_ms: float | None, step_ms: float | None = None) -> dict[str, Any]:
    by_dev, max_cnt = {}, 1
    for row in _iter_csv(path):
        if "synchronize" in (_row_text(row, ("API Name", "Name", "api_name")) or "").lower(): continue
        dev = _row_text(row, ("Device_id", "device_id", "Rank ID", "rank_id")) or "0"
        us = _first_float(row.get("Total Time(us)"), row.get("Time(us)"), row.get("Duration(us)"), row.get("Duration"))
        if us is None and (ms := _first_float(row.get("Total Time(ms)"), row.get("Time(ms)"), row.get("Duration(ms)"))) is not None: us = ms * 1000.0
        if us is not None: by_dev[dev] = by_dev.get(dev, 0.0) + us
        if (cnt := _first_int(row.get("Count"), row.get("count"))) and cnt > max_cnt: max_cnt = cnt
    ref = cap_ms if (cap_ms and cap_ms > 0) else (step_ms if max_cnt <= 1 else None)
    return {"host_share": _ratio(min(by_dev[sorted(by_dev)[0]] / 1000.0 / ref, 1.0))} if (by_dev and ref and ref > 0) else {}
def _finalize_observed(observed: dict[str, Any], facts: dict[str, Any]) -> None:
    busy, exp = observed.get("device_busy_union_ms"), observed.get("exposed_comm_ms")
    exp_ratio = _ratio(exp / busy) if (exp is not None and busy and busy > 0) else None
    if exp_ratio is not None and (observed.get("comm_share") is None or exp_ratio > float(observed["comm_share"])):
        observed["comm_share"] = exp_ratio
    if observed.get("hccl_share") is None: observed["hccl_share"] = observed.get("comm_share")
    if observed.get("comm_share") is None: observed["comm_share"] = observed.get("hccl_share")
    comm = max(_ratio(observed.get("comm_share")) or 0.0, _ratio(observed.get("hccl_share")) or 0.0)
    launch = max(_ratio(observed.get("aicpu_share")) or 0.0, _ratio(observed.get("host_share")) or 0.0)
    memory = _ratio(observed.get("kv_peak_ratio")) or 0.0
    compute = max(_ratio(observed.get(k)) or 0.0 for k in ("cube_share", "vector_share", "attention_share", "moe_share"))
    observed["dominant_bottleneck"] = ("comm_bound" if (comm >= 0.35 and comm >= compute) else "launch_host_bound" if (launch >= 0.3 and launch >= compute) else "memory_kv_bound" if memory >= 0.85 else "compute_bound")
    observed["top_operators"] = observed.get("top_operators", [])[:10]
def _build_case(facts: Mapping[str, Any], observed: Mapping[str, Any], applied: Sequence[str]) -> dict[str, Any]:
    structural, cfg = {k: v for k, v in facts["structural"].items() if v is not None}, _mapping(facts.get("config"))
    mpe = _MAX_POS.get(str(facts.get("model"))) if facts.get("model_override") else _first_int(cfg.get("max_position_embeddings"), None if _has_explicit_config(facts) else _MAX_POS.get(str(facts.get("model"))))
    req_len = int(facts["workload"]["seq_len"]) + int(facts["workload"]["decode_steps"]) + max(0, int(structural.get("spec_tokens") or 0))
    if mpe and req_len > mpe: raise ProfilerUsageError(f"invalid simulation case: workload_exceeds_model_max_position_embeddings:{req_len}>{mpe}")
    compose = next((getattr(mod, "compose_case", None) for name in ("mindie_sim.compose.compose_case", "mindie_sim.compose", "mindie_sim") if (mod := _try_import(name)) is not None and callable(getattr(mod, "compose_case", None))), None)
    case = (_compose_case(compose, facts, structural) if compose is not None else None) or _fallback_case(facts, structural)
    cleaned = {k: dict(case.get(k) or {}) for k in ("machine", "model", "workload", "runtime", "slo")}
    for k in ("model", "machine", "workload"): _strip_timings(cleaned[k])
    cleaned["workload"] = {"requests": [dict(item) for item in cleaned["workload"].get("requests") or []]}
    _attach_metadata(cleaned, facts, observed, applied)
    _validate_case(cleaned)
    return cleaned
def _try_import(mod_name: str) -> Any:
    try: return __import__(mod_name, fromlist=["compose_case"])
    except ImportError: return None
def _has_explicit_config(facts: Mapping[str, Any]) -> bool:
    cfg = _mapping(facts.get("config"))
    return bool(not facts.get("model_override") and "catalog_key" not in cfg and _first_int(cfg.get("hidden_size"), cfg.get("d_model"), cfg.get("hidden_dim")) and _first_int(cfg.get("num_attention_heads"), cfg.get("num_heads"), cfg.get("n_heads")))
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
def _compose_case(compose: Any, facts: Mapping[str, Any], structural: Mapping[str, int]) -> dict[str, Any] | None:
    workload, parallel, q_val = facts["workload"], facts["parallel"], facts.get("quantization")
    base_kw: dict[str, Any] = {"hardware": facts["hardware"], "tp": parallel["tp"], "dp": parallel["dp"], "ep": parallel["ep"], "pp": parallel["pp"], "prompt_tokens": workload["seq_len"], "output_tokens": workload["decode_steps"], "concurrency": workload["batch_size"], "prefix_tokens": workload["prefix_len"], "graph_capture_mode": facts["graph_capture_mode"], **({"quant": "bf16" if q_val == "fp16" else q_val} if q_val else {})}
    struct_kw = {k: structural[k] for k in ("layers", "n_routed_experts", "num_experts_per_tok") if structural.get(k) is not None}
    base_g = _GEOMETRY.get(str(facts.get("model")), {})
    cat_key, ext_struct = base_g.get("catalog_key"), (base_g.get("ffn") == "dense" and bool((structural.get("n_routed_experts") or 0) > 0)) or bool(base_g.get("layers") and (structural.get("layers") or 0) > int(base_g["layers"]))
    sim_m = facts.get("sim_model") if (isinstance(facts.get("sim_model"), Mapping) and not facts.get("model_override")) else None
    fb_mod = _fallback_model(facts, structural)
    fb_ok = bool(fb_mod.get("layer_plans"))
    attempts: list[tuple[Any, dict[str, Any]]] = [*([(fb_mod, base_kw)] if (sim_m and fb_ok) else []), *([] if (sim_m or ext_struct or _has_explicit_config(facts) or not isinstance(cat_key, str) or not cat_key) else [(cat_key, {**base_kw, **struct_kw})]), *([(fb_mod, base_kw)] if fb_ok else [])]
    for idx, (candidate, kw) in enumerate(attempts):
        try: case = compose(candidate, **kw)
        except TimeoutError: raise
        except Exception as exc:
            if idx < len(attempts) - 1 and any(t in str(exc) for t in ("model_catalog_unknown", "unknown_model", "invalid_model_identifier", "extended_catalog_requires_explicit_layer_plans", "draft_structure_required")): continue
            raise ProfilerUsageError(f"invalid simulation case: {exc}") from exc
        if isinstance(case, Mapping):
            out_case = dict(case)
            if isinstance(out_case.get("model"), Mapping):
                out_case["model"] = dict(out_case["model"])
                _norm_aux_and_fp16(out_case["model"], q_val, structural.get("layers"))
            if _parse_case(out_case) is None: return out_case
    return None
def _fallback_case(facts: Mapping[str, Any], structural: Mapping[str, int]) -> dict[str, Any]:
    parallel, workload = facts["parallel"], facts["workload"]
    world = max(1, parallel["tp"] * parallel["dp"] * parallel["pp"])
    machine = {"backend": "ascend", "sku": facts["hardware"], "num_devices": world, "ranks_per_node": min(world, 16 if str(facts["hardware"]).startswith("Ascend910_93") else 8)}
    runtime = {"parallel": dict(parallel), "graph_mode": facts["graph_capture_mode"], "graph_capture_mode": facts["graph_capture_mode"], "max_num_seqs": max(workload["batch_size"], 16), "max_num_batched_tokens": max(workload["seq_len"] * workload["batch_size"], 8192), "max_model_len": max(32768, workload["seq_len"] + workload["decode_steps"] + 1), "kv_block_size": 128, "enable_chunked_prefill": True, "metadata": {}}
    requests = [{"request_id": f"req-{i}", "arrival_ms": 0.0, "prompt_tokens": workload["seq_len"], "output_tokens": workload["decode_steps"], "prefix_tokens": workload["prefix_len"]} for i in range(workload["batch_size"])]
    return {"machine": machine, "model": _fallback_model(facts, structural), "workload": {"requests": requests}, "runtime": runtime, "slo": {"ttft_ms": 5000.0, "tpot_ms": 50.0}}
def _fallback_model(facts: Mapping[str, Any], structural: Mapping[str, int]) -> dict[str, Any]:
    canonical, config, q_val = facts.get("model"), _mapping(facts.get("config")), facts.get("quantization")
    q_preset = "bf16" if q_val == "fp16" else q_val
    if isinstance(facts.get("sim_model"), Mapping) and not facts.get("model_override"):
        out = dict(facts["sim_model"])
        if "layer_plans" not in out:
            if structural.get("layers") is not None: out["layers"] = structural["layers"]
            if (structural.get("n_routed_experts") or 0) > 0: out.update(num_experts=structural["n_routed_experts"], ffn="moe")
            if (structural.get("num_experts_per_tok") or 0) > 0: out["top_k"] = structural["num_experts_per_tok"]
        cur_q = _normalize_quant(out.get("quantization") or _mapping(out.get("quant")).get("name") or out.get("weight_dtype"))
        if q_val and q_val != cur_q:
            if q_val == "fp16": _norm_aux_and_fp16(out, q_val, structural.get("layers"))
            else:
                try:
                    from dataclasses import asdict
                    from mindie_sim.prediction.structure import ModelSpec
                    from mindie_sim.schema.serialization import apply_model_overrides
                    clean_m = {k: v for k, v in out.items() if k not in ("n_routed_experts", "num_experts_per_tok", "quantization", "quant", "model_type")}
                    ms = apply_model_overrides(ModelSpec.from_mapping(clean_m), {"quantization": q_preset})
                    out = asdict(ms) if "layer_plans" in out else {**clean_m, "quantization": ms.quantization, "weight_dtype": ms.weight_dtype, "activation_dtype": ms.activation_dtype, "kv_dtype": ms.kv_dtype, **({"quant": asdict(ms.quant)} if ms.quant else {})}
                except TimeoutError: raise
                except ImportError as exc:
                    if "layer_plans" in out: raise ProfilerUsageError("invalid simulation case: mindie_sim required for explicit layer_plans quant override") from exc
                    out["quantization"] = q_preset
                except Exception as exc: raise ProfilerUsageError(f"invalid simulation case: {exc}") from exc
        return out
    if canonical is not None and str(canonical) not in _GEOMETRY and not _has_explicit_config(facts): raise ProfilerUsageError(f"unsupported or unrecognized model: {canonical}")
    geometry = dict(_GEOMETRY.get(str(canonical), _GENERIC))
    if _has_explicit_config(facts):
        try:
            from dataclasses import asdict
            from mindie_sim.catalog.specs import build_model_spec
            from mindie_sim.schema.serialization import override_catalog, apply_model_overrides
            spec = build_model_spec(str(canonical or _config_identity(config) or "inline-model"), config)
            ov = {k: v for k, v in (("layers", structural.get("layers")), ("num_experts", structural.get("n_routed_experts")), ("top_k", structural.get("num_experts_per_tok")), ("quantization", q_preset)) if v is not None}
            out = asdict(apply_model_overrides(override_catalog(spec, ov), ov) if ov else spec)
            _norm_aux_and_fp16(out, q_val, structural.get("layers"))
            return out
        except TimeoutError: raise
        except ImportError: pass
        except Exception as exc:
            if "model_config_dimension_required" not in str(exc): raise ProfilerUsageError(f"invalid simulation case: {exc}") from exc
        hidden, heads = _first_int(config.get("hidden_size"), config.get("d_model"), config.get("hidden_dim")) or 4096, _first_int(config.get("num_attention_heads"), config.get("num_heads"), config.get("n_heads")) or 32
        identity, mla_cfg, base_mla = str(_config_identity(config) or "").lower(), _mapping(config.get("mla")), _mapping(geometry.get("mla"))
        kv_lora = _first_int(mla_cfg.get("kv_lora_rank"), config.get("kv_lora_rank"))
        is_mla = bool(kv_lora or "mla" in identity or "deepseek" in identity)
        mla = {"q_lora_rank": _first_int(mla_cfg.get("q_lora_rank"), config.get("q_lora_rank"), base_mla.get("q_lora_rank")) or 0, "kv_lora_rank": kv_lora or _first_int(base_mla.get("kv_lora_rank")) or 512, "qk_nope_head_dim": _first_int(mla_cfg.get("qk_nope_head_dim"), config.get("qk_nope_head_dim"), base_mla.get("qk_nope_head_dim")) or 128, "qk_rope_head_dim": _first_int(mla_cfg.get("qk_rope_head_dim"), config.get("qk_rope_head_dim"), base_mla.get("qk_rope_head_dim")) or 64, "v_head_dim": _first_int(mla_cfg.get("v_head_dim"), config.get("v_head_dim"), base_mla.get("v_head_dim")) or 128}
        h_dim = (mla["qk_nope_head_dim"] + mla["qk_rope_head_dim"]) if is_mla else (_first_int(config.get("head_dim"), config.get("d_head")) or (hidden // heads if hidden % heads == 0 else 128))
        explicit: dict[str, Any] = {"hidden_size": hidden, "num_heads": heads, "head_dim": h_dim, "num_kv_heads": _first_int(config.get("num_key_value_heads"), config.get("num_kv_heads"), config.get("n_kv_heads")) or heads, "attention": "mla" if is_mla else "gqa", **({"mla": mla} if is_mla else {})}
        for target, keys in (("layers", ("layers", "num_hidden_layers", "num_layers")), ("intermediate_size", ("intermediate_size", "ffn_intermediate_size", "ffn_dim")), ("vocab_size", ("vocab_size",)), ("num_experts", ("n_routed_experts", "num_routed_experts", "num_experts", "n_experts")), ("top_k", ("num_experts_per_tok", "top_k", "moe_top_k")), ("moe_intermediate_size", ("moe_intermediate_size", "moe_inter_dim")), ("num_shared_experts", ("n_shared_experts", "num_shared_experts"))):
            if (val := _first_int(*(config.get(k) for k in keys))) is not None: explicit[target] = val
        explicit["ffn"] = "moe" if (explicit.get("num_experts") or 0) > 0 else "dense"
        if explicit["ffn"] == "dense": explicit.update(num_experts=0, top_k=0, moe_intermediate_size=0)
        if q_cfg := _normalize_quant(config.get("quantization") or config.get("quant_method")): explicit["quantization"] = q_cfg
        geometry = {**_GENERIC, **explicit}
    base_layers, dense_to_moe = int(geometry.get("layers") or 0), geometry.get("ffn") == "dense" and bool((structural.get("n_routed_experts") or 0) > 0)
    ext_struct = dense_to_moe or bool(base_layers and (structural.get("layers") or 0) > base_layers)
    if "catalog_key" in geometry:
        try:
            from dataclasses import asdict
            from mindie_sim.prediction.structure import ModelSpec
            spec_in = {"catalog_key": geometry["catalog_key"], "name": str(canonical or geometry["catalog_key"]), **({"quantization": q_preset} if q_preset else {}), **({} if ext_struct else {k: v for k, v in (("layers", structural.get("layers")), ("num_experts", structural.get("n_routed_experts")), ("top_k", structural.get("num_experts_per_tok"))) if v is not None})}
            out = {**asdict(ModelSpec.from_mapping(spec_in)), "name": str(canonical or geometry["catalog_key"])}
            _norm_aux_and_fp16(out, q_val, structural.get("layers"))
            if ext_struct:
                plans = list(out.get("layer_plans") or [])
                if (req_l := structural.get("layers")) is not None and plans:
                    plans = plans[:req_l] if req_l <= len(plans) else [*plans, *({**plans[-1], "index": i, "native_layer_id": i} for i in range(len(plans), req_l))]
                    out.update(layers=req_l, body_layers=req_l, layer_plans=plans)
                if (exp := structural.get("n_routed_experts") or 0) > 0:
                    top_k, moe_inter = int(structural.get("num_experts_per_tok") or out.get("top_k") or 8), int(out.get("moe_intermediate_size") or 512)
                    out.update(ffn="moe", num_experts=exp, top_k=top_k, moe_intermediate_size=moe_inter)
                    for lp in plans: lp.update(ffn="moe", num_experts=exp, top_k=top_k, moe_intermediate_size=moe_inter)
            if isinstance(out.get("quant"), Mapping) and "950" not in str(facts.get("hardware") or "") and not q_val and "fp8" in str(out["quant"].get("activation_format", "")):
                out["quant"] = {**out["quant"], "weight_format": "int8", "activation_format": "int8", "expert_weight_format": "int8"}
                out["weight_dtype"] = "int8"
            return out
        except TimeoutError: raise
        except ImportError: pass
        except Exception as exc:
            if "model_catalog_unknown" not in str(exc): raise ProfilerUsageError(f"invalid simulation case: {exc}") from exc
    cat_key = geometry.pop("catalog_key", None)
    if structural.get("layers") is not None: geometry["layers"] = structural["layers"]
    if (structural.get("n_routed_experts") or 0) > 0:
        geometry["num_experts"], geometry["ffn"] = structural["n_routed_experts"], "moe"
        if not geometry.get("moe_intermediate_size"): geometry["moe_intermediate_size"] = 512
    if (structural.get("num_experts_per_tok") or 0) > 0: geometry["top_k"] = structural["num_experts_per_tok"]
    if q_val == "fp16": _norm_aux_and_fp16(geometry, q_val)
    elif q_val: geometry.update(quantization=q_val, **({"weight_dtype": "bf16"} if q_val == "bf16" else {}))
    if canonical: geometry.setdefault("name", str(canonical))
    if geometry.get("attention") not in {"gqa", "mla"}:
        if not cat_key or ext_struct or q_val == "fp16" or (facts["structural"].get("spec_tokens") or 0) > 0: raise ProfilerUsageError(f"invalid simulation case: mindie_sim required for {canonical or geometry.get('attention')}")
        return {"catalog_key": cat_key, "name": str(canonical or cat_key), "layers": int(geometry["layers"]), **({"quantization": q_val} if q_val else {}), **{k: v for k, v in (("num_experts", structural.get("n_routed_experts")), ("top_k", structural.get("num_experts_per_tok"))) if v is not None}}
    return geometry
def _strip_timings(value: Any) -> None:
    if isinstance(value, dict):
        for key in list(value):
            if str(key).lower() != "latency_us" and any(t in str(key).lower() for t in ("observed", "latency", "step_time", "tpot", "ttft")): value.pop(key, None)
            else: _strip_timings(value[key])
    elif isinstance(value, list):
        for item in value: _strip_timings(item)
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
    metadata["bridge_summary"] = {"system": {"hardware": facts["hardware"], "model": facts.get("model"), "quantization": facts.get("quantization") or _mapping(case["model"].get("quant")).get("name") or case["model"].get("quantization"), "execution_mode": facts["execution_mode"], "hccl_op_expansion_mode": facts["hccl_op_expansion_mode"], "spec_tokens": spec_k}, "parallel": dict(facts["parallel"]), "workload": dict(facts["workload"])}
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
def _parse_case(case: Mapping[str, Any]) -> str | None:
    try: from mindie_sim.prediction.structure import parse_case
    except ImportError: return "mindie_sim unavailable"
    try: parse_case(case); return None
    except TimeoutError: raise
    except Exception as exc: return str(exc)
def _mapping(value: Any) -> dict[str, Any]: return dict(value) if isinstance(value, Mapping) else {}
def _first_string(*values: Any) -> str | None: return next((v.strip() for v in values if isinstance(v, str) and v.strip()), None)
def _first_int(*values: Any) -> int | None:
    return None if (num := _first_float(*values)) is None else int(num)
def _first_float(*values: Any) -> float | None:
    for v in values:
        if v is not None and not isinstance(v, bool):
            try:
                if (num := float(v)) == num and abs(num) != float("inf"): return num
            except (TypeError, ValueError): pass
    return None
def _stat_median(value: Any) -> float | None: return _first_float(value.get("median"), value.get("p50"), value.get("mean")) if isinstance(value, Mapping) else _first_float(value)
def _ratio(value: Any) -> float | None: return None if (num := _first_float(value)) is None else max(0.0, min(1.0, round(num / 100.0 if abs(num) > 1.5 else num, 9)))
def _pct(value: Any) -> float | None: return None if (num := _first_float(value)) is None else max(0.0, min(1.0, round(num / 100.0, 9)))
def _is_c7_report(value: Any) -> bool: return isinstance(value, Mapping) and (value.get("schema_version") == "mindie-profile-summary/1" or any(k in value or k in _mapping(value.get("accounting")) for k in ("step_accounting", "semantic_block_breakdown", "window_accounting", "top_hotspot_kernels")))
def _looks_like_case_record(value: Any) -> bool: return isinstance(value, Mapping) and ({"hw", "family", "phase"} <= set(value) or {"hw", "family", "phase"} <= set(_mapping(value.get("traits"))) or {"family", "phase", "cohort"} <= set(value))
def _csv_path(bundle: Mapping[str, Any], name: str) -> Path | None: return path if isinstance(path := _mapping(bundle.get("csv")).get(name), Path) and path.is_file() else None
def _iter_csv(path: Path, max_rows: int = 2_000_000) -> Any:
    try:
        with path.open(encoding="utf-8", errors="replace", newline="") as stream:
            for idx, row in enumerate(csv.DictReader(stream)):
                if idx >= max_rows: raise ProfilerUsageError(f"CSV row count exceeds {max_rows} limit: {path}")
                yield {(k or "").strip(): v for k, v in row.items()}
    except TimeoutError: raise
    except OSError as exc: raise ProfilerUsageError(f"cannot read CSV {path}: {exc}") from exc
def _row_text(row: Mapping[str, Any], keys: Sequence[str]) -> str | None: return next((row[k].strip() for k in keys if isinstance(row.get(k), str) and row[k].strip() and row[k].strip() != "N/A"), None)
def _row_duration_us(row: Mapping[str, Any]) -> float | None:
    if (us := _first_float(*(row.get(k) for k in ("Total Time(us)", "Duration(us)", "Duration")))) is not None: return us
    return None if (ms := _first_float(*(row.get(k) for k in ("Total Time(ms)", "Duration(ms)")))) is None else ms * 1000.0
def _normalize_operators(items: Sequence[Any]) -> list[dict[str, Any]]:
    rows = []
    for item in items[:10]:
        if not isinstance(item, Mapping): continue
        name, total_us, total_ms, avg_us = item.get("op_type") or item.get("name") or item.get("kernel_name"), _first_float(item.get("total_us")), _first_float(item.get("total_time_ms")), _first_float(item.get("avg_us"))
        rows.append({"name": name, "op_type": name, "count": _first_int(item.get("count"), item.get("call_count")), "total_time_ms": (total_us / 1000.0 if (total_ms is None and total_us is not None) else total_ms), "avg_time_ms": None if avg_us is None else avg_us / 1000.0, "share": _pct(item.get("pct_of_device_time")) if item.get("pct_of_device_time") is not None else _ratio(item.get("share"))})
    return rows
def _share_from_names(operators: Sequence[Mapping[str, Any]], predicate: Any) -> float | None:
    if not (shares := [s for x in operators if (s := _first_float(x.get("share"))) is not None]): return None
    total, matched = sum(shares), sum(_first_float(x.get("share")) or 0.0 for x in operators if predicate(x.get("name")))
    return _ratio(matched / total if total > 1.000001 else matched)
def _is_comm(name: Any) -> bool: return any(k in str(name or "").lower() for k in ("hccl", "hcom", "allreduce", "allgather", "reducescatter", "alltoall", "broadcast", "sendrecv"))
def _is_attention(name: Any) -> bool: return any(k in str(name or "").lower() for k in ("attention", "flashattention", "mla", "gdn", "kda", "paged", "sparseflash", "lightningindex", "qkv", "causalconv", "sharedkv"))
def _is_moe(name: Any) -> bool: return any(k in str(name or "").lower() for k in ("moe", "expert", "groupedmatmul", "gmm", "dispatch", "combine", "gating", "router", "topk", "swiglu"))
def _find_kv_ratio(value: Any, depth: int = 0) -> float | None:
    if depth > 4 or not isinstance(value, Mapping): return None
    for k in sorted(value, key=str):
        if "kv" in (low := str(k).lower()) and any(t in low for t in ("ratio", "usage", "peak", "util")) and (p := (_pct(value[k]) if ("pct" in low or "percent" in low) else _ratio(value[k]))) is not None: return p
    return next((p for k in sorted(value, key=str) if (p := _find_kv_ratio(value[k], depth + 1)) is not None), None)
def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mindie-profiler export-sim-case", description="Export a measured capture/report as a mindie-sim Case with observed profile metadata.", allow_abbrev=False)
    parser.add_argument("input_path", nargs="?", default=None, help="capture directory, report JSON, or metadata JSON")
    parser.add_argument("--capture-dir", "--input", "--root", dest="input_option", default=None, help="capture directory or JSON input")
    parser.add_argument("--chip", "--hardware", dest="chip", default=None)
    for flag in ("tp", "dp", "ep", "pp"): parser.add_argument(f"--{flag}", type=int, default=None)
    for flags, dest in ((("--batch-size", "--concurrency"), "batch_size"), (("--seq-len", "--prompt-tokens"), "seq_len"), (("--decode-steps", "--output-tokens"), "decode_steps")): parser.add_argument(*flags, dest=dest, type=int, default=None)
    for flag in ("model", "phase", "quant", "graph-mode", "hccl-expansion-mode"): parser.add_argument(f"--{flag}", default=None)
    parser.add_argument("--output", "-o", default=None)
    return parser
def main(argv: Sequence[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    args = _parser().parse_args(raw[1:] if (raw and raw[0] == "export-sim-case") else raw)
    if not (source := args.input_option or args.input_path):
        print("mindie-profiler export-sim-case: an input path or --capture-dir is required", file=sys.stderr); return 2
    try: case = export_sim_case(source, chip=args.chip, model=args.model, tp=args.tp, dp=args.dp, ep=args.ep, pp=args.pp, batch_size=args.batch_size, seq_len=args.seq_len, decode_steps=args.decode_steps, phase=args.phase, quant=args.quant, graph_mode=args.graph_mode, hccl_expansion_mode=args.hccl_expansion_mode, output=args.output)
    except TimeoutError: raise
    except (ProfilerError, OSError, ValueError) as exc:
        print(f"mindie-profiler export-sim-case: {exc}", file=sys.stderr); return 2
    prov = case["runtime"]["metadata"]["profiler_provenance"]
    summary = {"output": args.output, "schema_version": BRIDGE_SCHEMA, "source_kind": prov["source_kind"], "cell_tag": prov["cell_tag"], "hardware": prov["extracted_hardware"], "model": prov["extracted_model"]}
    print(json.dumps(summary if args.output else case, ensure_ascii=False, indent=None if args.output else 2, sort_keys=True))
    return 0
if __name__ == "__main__": raise SystemExit(main())
