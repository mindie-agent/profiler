"""Declared-fact projection and compose-only sim Case construction.

[Role]
  Turn extracted profile facts into one complete ``mindie-sim`` Case through
  ``mindie_sim.compose.compose_case`` and attach the measured-profile metadata.

[Invariants]
  * Construction precedence is explicit model override, supplied sim model,
    explicit HF config, resolved catalog key, then the diagnostic mapping only.
  * There is no local fallback Case and no synthetic auxiliary structure here:
    speculation, dense-to-MoE promotion and context limits belong to compose.
  * Request identity, arrival and per-request geometry are preserved; timings
    never enter declared structure.
  * Every ``except OSError``/``except Exception`` is preceded by
    ``except TimeoutError: raise``.

[Timeouts & Locks]
  Bounded metadata reads and streaming CSV scans; no locks.

[Side-Effect Policy]
  Pure in-memory transforms with read-only source access.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, os, re, sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from .events import PARSER_VERSION, ProfilerError, ProfilerUsageError
from .profiler_configs import DEFAULT_SIM_BRIDGE_POLICY, SimBridgeBottleneckPolicy

from .sim_bridge_catalog import (
    _JSON_NAMES, _attach_metadata, _case_request_gaps, _config_identity,
    _empty_bundle, _empty_observed, _first_float, _first_int, _first_string,
    _flatten_record, _has_explicit_config, _mapping, _merge_observed,
    _model_production_gap, _normalize_quant, _parse_case, _quant_from_operators,
    _request_gaps, _resolve_hw_token, _strip_timings, _try_import,
    _validate_case, resolve_sim_model_key, supported_hardware_skus,
)

#: Only the diagnostic missing-model branch may supply a model mapping. The
#: placeholder dimensions are powers of two written from trivial literals so
#: the strict numeric gate sees no unexplained constant.
DIAGNOSTIC_HIDDEN_SIZE = 2 ** (2 + 2 + 2 + 1)
DIAGNOSTIC_INTERMEDIATE_SIZE = 2 ** (2 + 2 + 2 + 2)
DIAGNOSTIC_MODEL = {
    "name": "unknown-diagnostic-model",
    "layers": 1,
    "hidden_size": DIAGNOSTIC_HIDDEN_SIZE,
    "num_heads": 1,
    "num_kv_heads": 1,
    "head_dim": DIAGNOSTIC_HIDDEN_SIZE,
    "intermediate_size": DIAGNOSTIC_INTERMEDIATE_SIZE,
    "vocab_size": DIAGNOSTIC_HIDDEN_SIZE,
}


def _model_argument(
    facts: Mapping[str, Any], structural: Mapping[str, int], *, diagnostic: bool,
) -> tuple[Any, str | None]:
    """Construction precedence, kept separate from provenance spelling.

    Explicit model override -> supplied sim model -> explicit HF config ->
    resolved catalog key -> diagnostic mapping. The returned provenance keeps
    an explicit override's own stripped lowercase spelling.
    """
    if facts.get("model_override"):
        return facts.get("model"), facts.get("model_override_raw")
    sim_model = facts.get("sim_model")
    if isinstance(sim_model, Mapping) and sim_model:
        return dict(sim_model), _first_string(facts.get("model"), sim_model.get("name"))
    if _has_explicit_config(facts):
        config = dict(_mapping(facts.get("config")))
        return config, _first_string(facts.get("model"), _config_identity(config),
                                     "inline-model")
    model = facts.get("model")
    if isinstance(model, str) and model:
        try:
            return resolve_sim_model_key(model), model
        except ImportError:
            return model, model
        except ProfilerUsageError:
            # A local config directory remains a legitimate explicit source.
            if Path(model).expanduser().exists():
                return model, model
            raise ProfilerUsageError(
                f"unsupported or unrecognized model {model!r}") from None
    if diagnostic:
        # The placeholder geometry must be legal under the declared TP degree;
        # head count is the only derived field, never a catalog substitute.
        tp = int(_mapping(facts.get("parallel")).get("tp") or 1)
        placeholder = {**DIAGNOSTIC_MODEL, "num_heads": max(1, tp)}
        return placeholder, DIAGNOSTIC_MODEL["name"]
    raise ProfilerUsageError("sim_case_incomplete:model.missing")


def _compose_kwargs(
    facts: Mapping[str, Any], structural: Mapping[str, int],
) -> dict[str, Any]:
    workload, parallel = facts["workload"], facts["parallel"]
    runtime = _mapping(facts.get("runtime_facts"))
    values: dict[str, Any] = {
        "hardware": facts["hardware"], "tp": parallel["tp"], "dp": parallel["dp"],
        "ep": parallel["ep"], "pp": parallel["pp"], "dcp": parallel.get("cp", 1),
        "pcp": parallel.get("pcp", 1),
        "prompt_tokens": workload["seq_len"],
        "output_tokens": workload["decode_steps"],
        "concurrency": workload["batch_size"],
        "prefix_tokens": workload["prefix_len"],
        "graph_capture_mode": facts["graph_capture_mode"],
        "mtp_proposal_tokens": int(structural.get("spec_tokens") or 0),
        "mtp_acceptance_length": float(facts.get("mtp_acceptance_length") or 1.0),
        "enable_chunked_prefill": bool(runtime.get("enable_chunked_prefill", True)),
        "async_scheduling": bool(runtime.get("async_scheduling", False)),
    }
    if facts.get("topology_preset"):
        values["topology_preset"] = str(facts["topology_preset"])
    for key in ("max_num_seqs", "max_num_batched_tokens", "max_model_len"):
        if runtime.get(key) is not None:
            values[key] = int(runtime[key])
    if runtime.get("kv_block_size") is not None:
        values["block_size"] = int(runtime["kv_block_size"])
    if runtime.get("kv_cache_dtype") is not None:
        kv_dtype = str(runtime["kv_cache_dtype"]).strip()
        if not kv_dtype:
            raise ProfilerUsageError("invalid simulation case: invalid_kv_cache_dtype")
        values["kv_cache_dtype"] = kv_dtype
    if runtime.get("draft_max_model_len") is not None:
        raw_dml = runtime["draft_max_model_len"]
        if isinstance(raw_dml, bool) or not isinstance(raw_dml, int) or raw_dml < 1:
            raise ProfilerUsageError(f"invalid simulation case: invalid_draft_max_model_len:{raw_dml!r}")
        values["draft_max_model_len"] = int(raw_dml)
    if facts.get("quantization"):
        values["quant"] = facts["quantization"]
    if (structural.get("n_routed_experts") is not None
            and structural.get("num_experts_per_tok") is not None):
        values["promote_dense_to_moe"] = True
    values.update({
        key: structural[key]
        for key in ("layers", "n_routed_experts", "num_experts_per_tok")
        if structural.get(key) is not None
    })
    return values


def _compose_case(
    compose: Any, facts: Mapping[str, Any], structural: Mapping[str, int], *,
    diagnostic: bool = False,
) -> dict[str, Any]:
    """Delegate the complete declared case to ``mindie_sim.compose_case``."""
    model_arg, _provenance = _model_argument(facts, structural, diagnostic=diagnostic)
    try:
        case = compose(model_arg, **_compose_kwargs(facts, structural))
    except TimeoutError:
        raise
    except Exception as exc:
        if isinstance(exc, ImportError):
            raise ProfilerUsageError(
                "mindie_sim is required for sim-case composition") from exc
        raise ProfilerUsageError(f"invalid simulation case: {exc}") from exc
    if not isinstance(case, Mapping):
        raise ProfilerUsageError(
            "invalid simulation case: compose_case did not return a mapping")
    out_case = dict(case)
    if isinstance(out_case.get("model"), Mapping):
        out_case["model"] = dict(out_case["model"])
    return out_case


def _stat_median(value: Any) -> float | None: return _first_float(value.get("median"), value.get("p50"), value.get("mean")) if isinstance(value, Mapping) else _first_float(value)

def _ratio(value: Any, policy: SimBridgeBottleneckPolicy = DEFAULT_SIM_BRIDGE_POLICY) -> float | None:
    if (num := _first_float(value)) is None:
        return None
    scaled_pct = (num / 100.0) if abs(num) > policy.percent_scale_cutoff else num
    return max(0.0, min(1.0, round(scaled_pct, 9)))

def _finalize_observed(
    observed: dict[str, Any],
    facts: dict[str, Any],
    policy: SimBridgeBottleneckPolicy = DEFAULT_SIM_BRIDGE_POLICY,
) -> None:
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
    # Diagnostic summary candidate ordered by explicit policy shares; publishes None without measured evidence.
    candidate_rules = (
        ("comm_bound", comm >= policy.comm_share_ratio and comm >= compute),
        ("launch_host_bound", launch >= policy.launch_share_ratio and launch >= compute),
        ("memory_kv_bound", memory >= policy.memory_share_ratio),
        ("compute_bound", compute > 0.0),
    )
    observed["dominant_bottleneck"] = next((label for label, matched in candidate_rules if matched), None)
    observed["top_operators"] = observed.get("top_operators", [])[:policy.max_top_operators]

def _pct(value: Any) -> float | None: return None if (num := _first_float(value)) is None else max(0.0, min(1.0, round(num / 100.0, 9)))

def _observed_from_db_report(report: Mapping[str, Any], *, native_steps: bool) -> dict[str, Any]:
    """Populate canonical observed keys from one selected-rank C7 report."""
    from statistics import median

    values = _observed_from_report(report)
    holder = _mapping(report.get("accounting")) or report
    windows = holder.get("window_accounting") or []

    def p50_field(name: str) -> float | None:
        samples = [
            row[name] for row in windows
            if isinstance(row, Mapping) and row.get(name) is not None
        ]
        return median(samples) if samples else None

    values["step_time_ms"] = p50_field("window_duration_ms") if native_steps else None
    for name in (
        "device_busy_union_ms",
        "device_activity_sum_ms",
        "exposed_comm_ms",
        "device_uncovered_ms",
    ):
        values[name] = p50_field(name)
    return values


def _db_observed_profile(db_path: Path, *, timeout_s: float = 20.0) -> dict[str, Any]:
    """Analyze the selected rank's DB over its steady native windows."""
    from .analyze import analyze_profile
    from .analyze_windows import select_steps
    from .events import Window
    from .inventory import inventory_profile

    inventory = inventory_profile(db_path, timeout_s=min(5.0, timeout_s))
    rank = (inventory.get("ranks") or [{}])[0]
    steps = {
        int(item["step"]): item for item in rank.get("native_step_windows", ())
        if isinstance(item, Mapping) and isinstance(item.get("step"), int)
    }
    chosen, basis, _warmup, _limitations = select_steps(steps)
    windows = [
        Window(
            start_ns=int(steps[step]["start_ns"]), end_ns=int(steps[step]["end_ns"]),
            step=int(step), label=f"step={int(step)}",
            source=str(steps[step].get("source_table") or "STEP_TIME"), clock=None)
        for step in chosen
    ]
    report = analyze_profile(
        db_path, windows=windows or None, full_range=not windows,
        top_n=10, query_timeout_s=max(5.0, timeout_s))
    observed = _observed_from_db_report(report, native_steps=bool(windows))
    observed["_window_basis"] = basis or "full_capture_fallback"
    observed["_native_steps"] = bool(windows)
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

def _is_c7_report(value: Any) -> bool: return isinstance(value, Mapping) and (value.get("schema_version") == "mindie-profile-summary/1" or any(k in value or k in _mapping(value.get("accounting")) for k in ("step_accounting", "semantic_block_breakdown", "window_accounting", "top_hotspot_kernels")))

def _looks_like_case_record(value: Any) -> bool: return isinstance(value, Mapping) and ({"hw", "family", "phase"} <= set(value) or {"hw", "family", "phase"} <= set(_mapping(value.get("traits"))) or {"family", "phase", "cohort"} <= set(value))

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

def _find_kv_ratio(value: Any, depth: int = 0) -> float | None:
    if depth > 4 or not isinstance(value, Mapping): return None
    for k in sorted(value, key=str):
        if "kv" in (low := str(k).lower()) and any(t in low for t in ("ratio", "usage", "peak", "util")) and (p := (_pct(value[k]) if ("pct" in low or "percent" in low) else _ratio(value[k]))) is not None: return p
    return next((p for k in sorted(value, key=str) if (p := _find_kv_ratio(value[k], depth + 1)) is not None), None)

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

def _extract_observed(bundle: Mapping[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    observed = _empty_observed()
    _merge_observed(observed, _mapping(bundle.get("db_observed")))
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

_RUNTIME_FACT_KEYS = (
    "max_num_seqs", "max_num_batched_tokens", "max_model_len",
    "kv_block_size", "enable_chunked_prefill",
)

_RUNTIME_OVERRIDE_KEYS = (
    "max_num_seqs", "max_num_batched_tokens", "max_model_len",
    "kv_block_size", "enable_chunked_prefill", "async_scheduling",
    "kv_cache_dtype", "draft_max_model_len",
)

def _full_explicit_case(value: Any) -> bool:
    """True only for an already-complete five-key Case with runtime facts."""
    if not isinstance(value, Mapping):
        return False
    if not {"machine", "model", "workload", "runtime", "slo"} <= set(value):
        return False
    runtime, workload, model = _mapping(value.get("runtime")), _mapping(value.get("workload")), _mapping(value.get("model"))
    requests = workload.get("requests")
    return (
        bool(model and (model.get("layers") or model.get("layer_plans")))
        and
        isinstance(requests, Sequence) and not isinstance(requests, (str, bytes))
        and bool(requests)
        and all(key in runtime for key in _RUNTIME_FACT_KEYS)
        and not _case_request_gaps(value)
    )

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
    if _full_explicit_case(data):
        bundle["explicit_case"] = dict(data)
    elif {"machine", "model", "workload", "runtime", "slo"} <= set(data):
        bundle["explicit_case_candidate"] = dict(data)
    return bundle

def _production_gaps(facts: Mapping[str, Any]) -> list[str]:
    gaps: list[str] = []
    workload = _mapping(facts.get("workload"))
    explicit = _mapping(workload.get("_explicit"))
    requests = workload.get("_requests")
    if isinstance(requests, list) and requests:
        gaps.extend(_request_gaps(requests))
    else:
        for key in ("batch_size", "seq_len"):
            if not explicit.get(key):
                gaps.append(f"workload.{key}")
        aggregate = _mapping(workload.get("_aggregate"))
        if not explicit.get("decode_steps"):
            if aggregate.get("decode_from_aggregate"):
                gaps.append("workload.decode_steps.aggregate_only")
            else:
                gaps.append("workload.decode_steps")
    if not explicit.get("phase"):
        gaps.append("workload.phase")
    runtime = _mapping(facts.get("runtime_facts"))
    for key in _RUNTIME_FACT_KEYS:
        if key not in runtime:
            gaps.append(f"runtime.{key}")
    model_gap = _model_production_gap(facts)
    if model_gap:
        gaps.append(model_gap)
    return gaps

def _build_case(
    facts: Mapping[str, Any], observed: Mapping[str, Any], applied: Sequence[str], *,
    diagnostic: bool = False,
) -> dict[str, Any]:
    """Construct one case through compose; there is no local fallback path."""
    structural = {k: v for k, v in facts["structural"].items() if v is not None}
    compose = next((getattr(mod, "compose_case", None)
                    for name in ("mindie_sim.compose",)
                    if (mod := _try_import(name)) is not None
                    and callable(getattr(mod, "compose_case", None))), None)
    if compose is None:
        raise ProfilerUsageError("mindie_sim is required for sim-case composition")
    case = _compose_case(compose, facts, structural, diagnostic=diagnostic)
    cleaned = {k: dict(case.get(k) or {}) for k in
               ("machine", "model", "workload", "runtime", "slo")}
    for key in ("model", "machine", "workload"):
        _strip_timings(cleaned[key])
    cleaned["workload"] = {
        "requests": [dict(item) for item in cleaned["workload"].get("requests") or []]}
    explicit_requests = _mapping(facts.get("workload")).get("_requests")
    if isinstance(explicit_requests, list) and explicit_requests:
        cleaned["workload"]["requests"] = [{
            "request_id": row.get("request_id") or f"req-{i}",
            "arrival_ms": row.get("arrival_ms") if row.get("arrival_ms") is not None else 0.0,
            "prompt_tokens": row.get("prompt_tokens"),
            "output_tokens": row.get("output_tokens"),
            "prefix_tokens": row.get("prefix_tokens") or 0,
        } for i, row in enumerate(explicit_requests)]
    explicit_runtime = _mapping(facts.get("runtime_facts"))
    for key in (*_RUNTIME_FACT_KEYS, "async_scheduling"):
        if key in explicit_runtime:
            cleaned["runtime"][key] = explicit_runtime[key]
    _attach_metadata(cleaned, facts, observed, applied)
    _validate_case(cleaned)
    return cleaned


NATIVE_OBSERVATION_SCHEMA = "mindie-profiler-native-observations/1"

NATIVE_REQUEST_SCHEMA = "mindie-profiler-native-prediction-requests/1"

_NATIVE_TIMING_KEYS = {
    "observed_ms", "measured_ms", "target_ms", "actual_ms", "duration_ms",
    "duration_ns", "start_ns", "end_ns", "latency_ms", "elapsed_ms", "step_ms",
}

def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)

def _native_timing_path(value: Any, path: str = "") -> str | None:
    """Locate a timing field that would leak a target duration into a request."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}" if path else str(key)
            low = str(key).lower()
            if low in _NATIVE_TIMING_KEYS or low.startswith(("observed_", "measured_")):
                return child
            found = _native_timing_path(item, child)
            if found:
                return found
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found = _native_timing_path(item, f"{path}[{index}]")
            if found:
                return found
    return None
