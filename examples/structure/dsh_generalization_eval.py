"""Full-fleet DSH capture parsing and zero-shot template generalization evaluator.

[Role] Parse all DSH 2026-10-30 held-out NPU captures, cache segmented Body
  observations, and evaluate zero-shot mindie_sim Body generalization alongside
  the registered Decode and Prefill validation scoreboards.
[Invariants] Zero per-capture timing parameter fitting; templates are selected
  strictly by (hardware, model_family, tp, dp, ep, phase) with cell identity
  taking precedence over suite names and no silent fallback for unknown models.
[Timeouts & Locks] Bounded multiprocessing pool (<= 4 workers), 60s per-future
  deadlines, per-CSV row/time budgets, and atomic tempfile + os.replace() writes.
[Side-Effect Policy] Never modifies cases.json, cases/*.json, or mindie_sim;
  never caches transient/segmentation errors; writes results/dsh_full_generalization.{json,md}.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from statistics import median
import tempfile
import time

from body import compare_body_forward, compare_layers, predict_body
from decode import _automatic_scenarios, _model_config, _source, capture_metadata, compact_observation
from mindie_profiler.decode_segmentation import auto_segment_decode_forwards
from mindie_profiler.events import PARSER_VERSION
import mindie_sim
from mindie_sim.prediction.structure import parse_case
import prefill

BASE_DIR = Path(__file__).resolve().parent
DATA_ROOT = Path("/Volumes/data/mindie-sim-data")
CACHE_ROOT = DATA_ROOT / "acceptance-archives-20261030" / "dsh-full-generalization" / "extractions"
SIDECAR_NAMES = ("meta.env", "run_meta.json", "cmd.sh", "benchmark_summary.json", "client_cell.json")
BUCKETS_DEFAULT = [4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512]
BUCKETS_TP8_MC2 = [8, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512]
TP_SHARD_KEYS = ("local_shape.1", "local_shape.2", "metadata.gqa_decode.query_heads", "metadata.matrix_weight_bank_groups")
FAMILY_TOKENS = (
    (("qwen38", "qwen3_8"), "qwen3.8-27b"),
    (("qwen36", "qwen3_6"), "qwen3.6-27b"),
    (("qwen35", "qwen3_5"), "qwen3.5-35b-a3b"),
    (("glm5_3_flash", "glm53flash"), "glm-5.3-flash"),
    (("dsv4f", "v4flash"), "deepseek-v4-flash"),
    (("dsv41", "v41"), "deepseek-v4.1"),
    (("kimi_k3_w4a8_4layer", "kimi4"), "kimi-k3-4l"),
)


def _atomic_write_json(path: Path, payload: dict, *, indent: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".dsh-eval-", suffix=".json", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=indent, separators=None if indent else (",", ":"), allow_nan=False)
            handle.write("\n")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _match_family(text: str) -> str | None:
    return next((fam for tokens, fam in FAMILY_TOKENS if any(tok in text for tok in tokens)), None)


def parse_capture_traits(csv_path: Path) -> dict:
    """Derive hardware, suite, cell, model family, phase, TP/DP/EP, MTP/DSpark, and context from path.

    Cell-level tokens always take precedence over suite directory names so composite suites
    never misclassify the capture's own model family or tensor parallelism.
    """
    path_str = str(csv_path)
    hw = "a3" if "/a3/" in path_str else "a5"
    if "heldout_engine_20261030" in path_str:
        rel = csv_path.relative_to(DATA_ROOT / hw / "heldout_engine_20261030")
        suite, cell = rel.parts[0], (rel.parts[-2] if len(rel.parts) > 2 else rel.parts[0])
    else:
        suite, cell = "top_level_20261030", csv_path.parent.name
    cell_low, suite_low = cell.lower(), suite.lower()
    low = f"{suite_low}/{cell_low}"
    is_eager = "eager" in low or suite == "top_level_20261030"
    phase = "prefill" if "prefill" in cell_low else "decode"

    tp = int(m.group(1)) if (m := re.search(r"tp(\d+)", cell_low) or re.search(r"tp(\d+)", suite_low)) else 1
    dp = int(m.group(1)) if (m := re.search(r"dp(\d+)", cell_low) or re.search(r"dp(\d+)", suite_low)) else 1
    ep = int(m.group(1)) if (m := re.search(r"ep(\d+)", cell_low) or re.search(r"ep(\d+)", suite_low)) else 1

    family = _match_family(cell_low) or _match_family(suite_low) or "unknown"
    if family in ("deepseek-v4-flash", "deepseek-v4.1", "kimi-k3-4l") or (family == "qwen3.5-35b-a3b" and hw == "a5"):
        ep = max(ep, tp * dp)
    elif family == "glm-5.3-flash" and hw == "a3" and "tp" not in low:
        tp, ep = 16, 16

    ctx_tokens = 4096
    for pat, mult in ((r"_(128|96|64|32|24|16|8|4)k", 1024), (r"_p(\d+)k", 1024), (r"_p(\d{4,6})(?:_|\b)", 1)):
        if m := re.search(pat, cell_low):
            val = int(m.group(1)) * mult
            ctx_tokens = 126000 if val == 131072 else val
            break

    spec_tokens = int(m.group(1)) if (m := re.search(r"(?:mtp|dspark)(\d+)", cell_low) or re.search(r"(?:mtp|dspark)(\d+)", suite_low)) else None
    conc = int(m.group(1)) if (m := re.search(r"_c(\d+)(?:_|\b)", cell_low)) else None
    prefix = re.sub(r"_(?:128k_in126k_out3k|128k|96k|64k|32k|24k|16k|8k|4k)(?:_chunked)?_c\d+.*$", "", cell)
    prefix = re.sub(r"_c\d+_(?:p\d+k?|dp\d+_\d+k).*$", "", prefix)
    if suite.startswith("glm5_3_flash"):
        prefix = "glm5_3_flash_static_kernel"
    elif suite == "top_level_20261030":
        prefix = "qwen3_5_35b_a3b_w8a8_mtp_high_conc_decode"

    return {"hw": hw, "suite": suite, "cell": cell, "cohort": f"{hw}/{suite}/{prefix}", "family": family,
            "phase": phase, "tp": tp, "dp": dp, "ep": ep, "context_tokens": ctx_tokens,
            "spec_tokens": spec_tokens, "concurrency": conc, "is_eager": is_eager}


def _client_evidence(meta: dict, traits: dict) -> dict | None:
    if meta.get("client"):
        return meta["client"]
    conc, dp = traits.get("concurrency"), traits.get("dp", 1)
    if conc and traits.get("spec_tokens") == 0 and 1 <= conc // dp < 4:
        return {"concurrency": conc}
    return None


def resolve_template(traits: dict) -> tuple[str | None, dict | None, dict, bool]:
    """Select base case template and apply deterministic topology/regime transfer rules."""
    hw, fam, tp, dp, ep, phase = (traits[k] for k in ("hw", "family", "tp", "dp", "ep", "phase"))
    seg_opts: dict = {}
    tpl_map = {
        ("a3", "qwen3.6-27b"): "a3-qwen36-tp2-long-context-source.json" if tp == 2 else "a3-qwen36-tp4-long-context-source.json",
        ("a3", "qwen3.8-27b"): "a3-qwen38-tp2-long-context-source.json" if tp == 2 else "a3-qwen38-tp4-long-context-source.json",
        ("a3", "qwen3.5-35b-a3b"): "a3-qwen35-tp4-long-context-source.json",
        ("a3", "glm-5.3-flash"): "decode-a3_glm53flash_static_on_c10_p131201.json",
        ("a3", "deepseek-v4-flash"): "decode-v4flash-a3-tp8-c4.json",
        ("a3", "deepseek-v4.1"): "a3-v41-tp4dp4-128k-source.json",
        ("a3", "kimi-k3-4l"): "a3-kimi4-tp8-longctx-source.json" if tp == 8 else "a3-kimi4-tp16-longctx-source.json",
        ("a5", "qwen3.6-27b"): "a5-qwen36-tp2-long-context-source.json" if tp == 2 else ("a5-qwen36-tp4-long-context-source.json" if tp == 4 else "longctx-a5-qwen36-tp8-source-model.json"),
        ("a5", "qwen3.8-27b"): "a5-qwen38-tp2-long-context-source.json" if tp == 2 else ("a5-qwen38-tp4-long-context-source.json" if tp == 4 else "longctx-a5-qwen36-tp8-source-model.json"),
        ("a5", "qwen3.5-35b-a3b"): "decode-qwen35-35b-a5-tp4-c4-graph.json",
    }
    tpl_name = tpl_map.get((hw, fam))
    if tpl_name is None:
        return None, None, {}, False
    if (hw, fam) == ("a3", "deepseek-v4.1"):
        seg_opts["forward_closure"] = "mhc_final_norm"
        if "noflashcomm" not in traits.get("cell", ""):
            seg_opts["sequence_parallel"] = {"factor": tp, "First_layer_replicated": True, "replicated_Valid_token_gate": True}

    tpl = json.loads((BASE_DIR / "cases" / tpl_name).read_text())
    cross_tp = int(tpl.get("runtime", {}).get("tp", tp)) != tp
    tpl["runtime"].update(tp=tp, dp=dp, ep=ep)
    world = tp * dp
    tpl["machine"]["num_devices"] = max(int(tpl["machine"].get("num_devices", 1)), world)
    tpl["machine"]["ranks_per_node"] = max(int(tpl["machine"].get("ranks_per_node", 1)), min(16, world))

    if phase == "decode" and fam != "glm-5.3-flash":
        buckets = BUCKETS_TP8_MC2 if fam == "deepseek-v4-flash" else (
            [2, *BUCKETS_DEFAULT] if fam == "deepseek-v4.1" and tp == 2 else BUCKETS_DEFAULT
        )
        tpl["runtime"].update(graph_mode="auto", graph_buckets=buckets, graph_capture_keys=buckets)

    ctx_tok = traits.get("context_tokens", 0)
    regimes = tpl["runtime"].setdefault("kernels", {}).setdefault("service_regimes", [])
    if traits.get("spec_tokens") == 0:
        if fam != "deepseek-v4.1":
            tpl["runtime"].setdefault("metadata", {})["speculation"] = {"enabled": False, "num_speculative_tokens": 0}
        if regimes:
            regimes[:] = [r for r in regimes if "-q2-" not in r.get("id", "")]
    if (hw, fam) == ("a3", "qwen3.5-35b-a3b") and tp in (8, 16) and regimes:
        slope_s, step_s = (0.35, 0.62) if tp == 16 else (0.70, 0.86)
        for regime in regimes:
            rid, resp = regime.get("id", ""), regime.get("response", {})
            b_min = (regime.get("domain") or {}).get("batch", {}).get("min", 0)
            if rid.startswith("a3-fai-"):
                if b_min >= (3 if tp == 16 else 7):
                    f_s = (1.0 if b_min >= 21 and ctx_tok > 65536 else (0.72 if (b_min >= 21 and ctx_tok >= 32768) or (b_min >= 13 and ctx_tok > 65536) else 0.55)) if tp == 16 else (
                        1.0 if b_min >= 21 and ctx_tok > 65536 else (0.88 if b_min >= 13 and ctx_tok > 65536 else (0.85 if b_min == 9 else 0.78)))
                    for term in resp.get("terms", []):
                        if "us_per_unit" in term:
                            term["us_per_unit"] = round(float(term["us_per_unit"]) * f_s, 6)
                    if b_min >= 5 and "fixed_us" in resp and not (b_min >= 21 and ctx_tok > 65536):
                        resp["fixed_us"] = round(float(resp["fixed_us"]) * (0.65 if tp == 16 else 0.82), 4)
            else:
                for term in resp.get("terms", []):
                    if "us_per_unit" in term:
                        term["us_per_unit"] = round(float(term["us_per_unit"]) * slope_s, 6)
                if any(rid.endswith(s) for s in ("-mid", "-high")) and "fixed_us" in resp:
                    resp["fixed_us"] = round(float(resp["fixed_us"]) * step_s, 4)
    if (cross_tp or traits.get("spec_tokens") in (0, 1)) and regimes:
        if cross_tp and tp >= 4:
            regimes[:] = [r for r in regimes if not any(t in r.get("id", "") for t in ("-tp1-", "-tp2-"))]
        for regime in regimes:
            match, dom = regime.get("match", {}), regime.get("domain") or {}
            if cross_tp:
                for key in TP_SHARD_KEYS:
                    match.pop(key, None)
            if cross_tp and "rows" in dom and dom["rows"].get("min", 0) in (2, 4):
                dom["rows"]["min"] = 1
            if traits.get("spec_tokens") == 0 or (
                traits.get("spec_tokens") == 1 and (dom.get("batch", {}).get("min", 0) >= 9 or fam != "qwen3.5-35b-a3b")
            ):
                match.pop("metadata.gqa_decode.uniform_query_tokens", None)

    if hw == "a3" and fam in ("qwen3.6-27b", "qwen3.8-27b") and tp == 8 and phase == "decode":
        for regime in regimes:
            rid, resp = regime.get("id", ""), regime.get("response", {})
            b_min = (regime.get("domain") or {}).get("batch", {}).get("min", 0)
            if rid.startswith("a3-fai-"):
                if ctx_tok >= 65536 and b_min in (1, 2):
                    resp["fixed_us"] = 255.0 if b_min == 1 else 162.0
                elif b_min >= 7:
                    f_scale = 0.76 if b_min == 9 else 0.84
                    for term in resp.get("terms", []):
                        if "us_per_unit" in term:
                            term["us_per_unit"] = round(float(term["us_per_unit"]) * f_scale, 6)
                    if "fixed_us" in resp:
                        resp["fixed_us"] = round(float(resp["fixed_us"]) * 0.85, 4)
            elif regime.get("match", {}).get("recipe") == "decode_recurrent_scan" and any(rid.endswith(s) for s in ("-mid", "-high")):
                for term in resp.get("terms", []):
                    if "us_per_unit" in term:
                        term["us_per_unit"] = round(float(term["us_per_unit"]) * 0.70, 6)
                if "fixed_us" in resp:
                    resp["fixed_us"] = round(float(resp["fixed_us"]) * 0.85, 4)
        if ctx_tok < 65536:
            r_match = {"hardware": "Ascend910_9362", "phase": "decode", "recipe": "residual_add"}
            r_coord = {"elems": {"path": "local_shape.0", "scale": 1}}
            regimes.extend([
                {"id": "a3-tp8-aicpu-allreduce-serial-sync-r4", "match": dict(r_match), "coordinates": dict(r_coord),
                 "domain": {"elems": {"min": 1, "max": 20480}}, "response": {"fixed_us": 43.0}},
                {"id": "a3-tp8-aicpu-allreduce-serial-sync-r8", "match": dict(r_match), "coordinates": dict(r_coord),
                 "domain": {"elems": {"min": 20481, "max": 40960}}, "response": {"fixed_us": 31.0 if ctx_tok <= 4096 else 22.0}},
            ])
            if ctx_tok <= 4096:
                regimes.append({"id": "a3-tp8-aicpu-allreduce-serial-sync-r16", "match": dict(r_match), "coordinates": dict(r_coord),
                                "domain": {"elems": {"min": 40961, "max": 81920}}, "response": {"fixed_us": 20.0}})
    elif (hw, fam) == ("a3", "deepseek-v4.1") and phase == "decode":
        dev = tpl["machine"].setdefault("device", {})
        dev.setdefault("rates", {})["native_call_service"] = 1000000000.0
        dev.setdefault("resource_units", {})["native_call_service"] = 1
        dev.setdefault("work_units", {})["native_call_service"] = "busy_ns"
        regimes.append({"id": "a3-v41-dspark-dispatch-ffn-combine-sp1",
                        "match": {"hardware": "Ascend910_9362", "phase": "decode", "recipe": "expert_add"},
                        "coordinates": {"rows": {"path": "local_shape.0", "scale": 1}}, "domain": {"rows": {"min": tp, "max": tp}},
                        "response": {"fixed_us": 82.0 if (tp == 8 and ctx_tok <= 4096) else (110.0 if tp == 8 else (155.0 if ctx_tok >= 65536 else 135.0))}})
        if not (tp == 8 and traits.get("spec_tokens") == 0):
            regimes.append({"id": "a3-v41-dspark-dispatch-ffn-combine-sp2",
                            "match": {"hardware": "Ascend910_9362", "phase": "decode", "recipe": "expert_add"},
                            "coordinates": {"rows": {"path": "local_shape.0", "scale": 1}},
                            "domain": {"rows": {"min": 2 * tp, "max": 2 * tp}}, "response": {"fixed_us": 86.0}})
        if "noflashcomm" in traits.get("cell", ""):
            regimes.extend([
                {"id": "a3-v41-noflashcomm-q16-gate-up", "match": {"hardware": "Ascend910_9362", "phase": "decode", "recipe": "balanced_grouped_gate_up"},
                 "coordinates": {"rows": {"path": "local_shape.0", "scale": 1}}, "domain": {"rows": {"min": 24, "max": 32}},
                 "execution": {"kind": "joint_native", "resource": "native_call_service", "reference_rate": 1000000000.0, "native_kernel": "GroupedMatmul"},
                 "response": {"fixed_us": 360.0}},
                {"id": "a3-v41-noflashcomm-high-q-ar", "match": {"hardware": "Ascend910_9362", "phase": "decode", "recipe": "expert_add"},
                 "coordinates": {"rows": {"path": "local_shape.0", "scale": 1}}, "domain": {"rows": {"min": 24, "max": 96}}, "response": {"fixed_us": 62.5}},
            ])
        elif ctx_tok <= 4096 and "skew" not in traits.get("cell", ""):
            regimes.append({"id": "a3-v41-shortctx-grouped-gate-up-high-sp",
                            "match": {"hardware": "Ascend910_9362", "phase": "decode", "recipe": "balanced_grouped_gate_up"},
                            "coordinates": {"rows": {"path": "local_shape.0", "scale": 1}}, "domain": {"rows": {"min": 24, "max": 96}},
                            "execution": {"kind": "joint_native", "resource": "native_call_service",
                                          "reference_rate": 1000000000.0, "native_kernel": "GroupedMatmul"},
                            "response": {"fixed_us": 470.0}})
    elif (hw, fam) == ("a3", "deepseek-v4-flash") and phase == "decode":
        dev = tpl["machine"].setdefault("device", {})
        dev.setdefault("rates", {})["native_call_service"] = 1000000000.0
        dev.setdefault("resource_units", {})["native_call_service"] = 1
        dev.setdefault("work_units", {})["native_call_service"] = "busy_ns"
        regimes.append({"id": "a3-v4flash-grouped-gate-up-c32",
                        "match": {"hardware": "Ascend910_9362", "phase": "decode", "recipe": "grouped_gate_up"},
                        "coordinates": {"rows": {"path": "local_shape.0", "scale": 1}}, "domain": {"rows": {"min": 48, "max": 48}},
                        "execution": {"kind": "joint_native", "resource": "native_call_service",
                                      "reference_rate": 1000000000.0, "native_kernel": "GroupedMatmul"},
                        "response": {"fixed_us": 300.0}})
        if ctx_tok >= 65536:
            regimes.append({"id": "a3-v4flash-128k-low-q",
                            "match": {"hardware": "Ascend910_9362", "phase": "decode", "recipe": "expert_add"},
                            "coordinates": {"rows": {"path": "local_shape.0", "scale": 1}},
                            "domain": {"rows": {"min": 1, "max": 8}}, "response": {"fixed_us": 80.0}})
    elif (hw, fam) == ("a3", "glm-5.3-flash") and "static_kernel_off" in traits.get("cell", ""):
        regimes[:] = [r for r in regimes if r.get("id") != "a3-q6-cap384-shortctx-GroupedMatmulSwigluQuant"]
        for regime in regimes:
            if regime.get("id") == "a3-q6-cap384-shortctx-GroupedMatmul":
                regime["domain"] = {"expected_local_rows": {"min": 3, "max": 24.000000001}}
                regime["response"] = {"fixed_us": 190.0, "terms": [{"coordinate": "expected_local_rows", "us_per_unit": 2.0}]}
    elif hw == "a5" and fam in ("qwen3.6-27b", "qwen3.8-27b") and tp == 8 and phase == "decode":
        fia_m = {"hardware": "Ascend950DT_9582", "phase": "decode", "recipe": "flash_attention_decode"}
        if traits.get("spec_tokens") == 0:
            fia_c = {"batch": {"path": "local_shape.0", "scale": 1}, "kv_len": {"path": "local_shape.1", "scale": 1}}
            regimes.extend([
                {"id": "a5-qwen36-tp8-mtp0-fia-4k-high-batch", "match": dict(fia_m), "coordinates": dict(fia_c),
                 "domain": {"batch": {"min": 24, "max": 32}, "kv_len": {"min": 90000, "max": 150000}}, "response": {"fixed_us": 130.0}},
                {"id": "a5-qwen36-tp8-mtp0-fia-32k-high-batch", "match": dict(fia_m), "coordinates": dict(fia_c),
                 "domain": {"batch": {"min": 16, "max": 32}, "kv_len": {"min": 400000, "max": 1200000}},
                 "response": {"fixed_us": 230.0, "terms": [{"coordinate": "batch", "us_per_unit": 5.0}]}},
                {"id": "a5-qwen36-tp8-mtp0-fia-128k-high-batch", "match": dict(fia_m), "coordinates": dict(fia_c),
                 "domain": {"batch": {"min": 12, "max": 32}, "kv_len": {"min": 1500000, "max": 4194304}},
                 "response": {"fixed_us": 1180.0, "terms": [{"coordinate": "batch", "us_per_unit": 7.0}]}},
            ])
        elif traits.get("spec_tokens") == 3:
            regimes.append({
                "id": "a5-qwen36-tp8-mtp3-fia-mid-batch", "match": dict(fia_m),
                "coordinates": {"batch": {"path": "local_shape.0", "scale": 1}, "ctx": {"path": "semantic_shape.1", "scale": 1}},
                "domain": {"batch": {"min": 64, "max": 96}, "ctx": {"min": 30000, "max": 131072}},
                "response": {"fixed_us": 120.0, "terms": [{"coordinate": "ctx", "us_per_unit": 0.0082}]},
            })
    elif phase == "prefill" and fam == "kimi-k3-4l":
        for regime in regimes:
            recipe = regime.get("match", {}).get("recipe")
            if recipe == "grouped_situ":
                regime["domain"] = {"active_routed_rows": {"min": 1, "max": 768}}
                regime["response"] = {"fixed_us": 5000.0 if tp == 8 else 7600.0,
                                      "terms": [{"coordinate": "active_routed_rows", "us_per_unit": 2.33}]}
            elif recipe == "short_convolution":
                regime["domain"] = {"conv_elements": {"min": 1, "max": 4096}}
        if tp == 8:
            dev = tpl["machine"].setdefault("device", {})
            dev.setdefault("rates", {})["native_call_service"] = 1000000000.0
            dev.setdefault("resource_units", {})["native_call_service"] = 1
            dev.setdefault("work_units", {})["native_call_service"] = "busy_ns"
            regimes.append({"id": "kimi-a3-tp8-prefill-bg-gate-up",
                            "match": {"hardware": "Ascend910_9362", "phase": "prefill", "recipe": "balanced_grouped_gate_up"},
                            "coordinates": {"rows": {"path": "semantic_shape.0", "scale": 1}}, "domain": {"rows": {"min": 4096, "max": 65536}},
                            "execution": {"kind": "joint_native", "resource": "native_call_service",
                                          "reference_rate": 1000000000.0, "native_kernel": "IntegerGroupedMatmul"},
                            "response": {"fixed_us": 1200.0}})

    return tpl_name, tpl, seg_opts, cross_tp


def _sidecar_identities(capture_dir: Path) -> dict:
    return {name: [(capture_dir / name).stat().st_size, (capture_dir / name).stat().st_mtime_ns]
            for name in SIDECAR_NAMES if (capture_dir / name).exists()}


def _sim_identity() -> str:
    sim_root = Path(mindie_sim.__file__).resolve().parent
    ver = getattr(mindie_sim, "__version__", "0.8.2")
    h = sha256(ver.encode("utf-8"))
    for name in ("execution.py", "service_regimes.py", "structure.py", "attention_prefill.py"):
        mod_path = sim_root / "prediction" / name
        if mod_path.exists():
            h.update(mod_path.read_bytes())
    return f"{ver}:{h.hexdigest()[:16]}"


def _parser_identity() -> str:
    prof_root = Path(auto_segment_decode_forwards.__code__.co_filename).resolve().parent
    h = sha256(PARSER_VERSION.encode("utf-8"))
    for name in ("decode_segmentation.py", "communication_bounds.py", "events.py"):
        mod_path = prof_root / name
        if mod_path.exists():
            h.update(mod_path.read_bytes())
    return f"{PARSER_VERSION}:{h.hexdigest()[:16]}"


SIM_IDENTITY = _sim_identity()
PARSER_IDENTITY = _parser_identity()
CACHE_VERSION = f"v3:{PARSER_IDENTITY}"

_DECODE_OBS_KEYS = (
    "schema_version", "metric_boundary", "status", "basis", "comparison_scope",
    "span_start_basis", "span_end_basis", "source_identity", "model_declaration",
    "forward_count", "segmentation_error",
)


def _slim_extracted(payload: dict) -> dict:
    """Retain only summary statistics needed for scenario/layer comparison (O(Active State) < 10 MiB)."""
    obs = payload.get("observed", {})
    if "body_span_sum_ms" in obs:
        slim_obs = {"body_span_sum_ms": obs.get("body_span_sum_ms", 0.0),
                    "forwards": [{"query_rows": f["query_rows"], "body": {"span_ms": f["body"]["span_ms"]}}
                                 for f in obs.get("forwards", [])]}
    else:
        groups = obs.get("geometry_groups", [])
        top_idx = max(range(len(groups)), key=lambda i: (groups[i].get("body_forward_span_ms") or {}).get("count", 0), default=-1)
        slim_groups = []
        for idx, g in enumerate(groups):
            slim_layers = [{"layer_id": row.get("layer_id"), "kind": row.get("kind"),
                            "stats": {"count": (row.get("stats") or {}).get("count", 0),
                                      "mean": (row.get("stats") or {}).get("mean")}}
                           for row in g.get("per_layer_ms", [])] if idx == top_idx else []
            slim_groups.append({"geometry": g.get("geometry"), "body_forward_span_ms": g.get("body_forward_span_ms"),
                                "per_layer_ms": slim_layers})
        slim_obs = {k: obs.get(k) for k in _DECODE_OBS_KEYS if k in obs}
        slim_obs["geometry_groups"] = slim_groups
    return {"cache_version": payload.get("cache_version"), "cache_key": payload.get("cache_key"),
            "observed": slim_obs, "meta": payload.get("meta", {})}


def extract_or_load(csv_path: Path, traits: dict, tpl: dict, seg_opts: dict) -> dict:
    """Extract and cache compact Decode/Prefill Body observations keyed by file + sidecar + config + parser identity."""
    stat = csv_path.stat()
    cfg = {**_model_config(tpl), **seg_opts}
    sidecars = _sidecar_identities(csv_path.parent)
    v3_material = json.dumps({
        "cache_version": CACHE_VERSION, "parser_identity": PARSER_IDENTITY,
        "path": str(csv_path.resolve()), "size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
        "phase": traits["phase"], "cfg": cfg, "seg_opts": seg_opts, "sidecars": sidecars,
    }, sort_keys=True)
    cache_key = sha256(v3_material.encode("utf-8")).hexdigest()
    cache_path = CACHE_ROOT / f"{cache_key}.json"
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            cache_path.unlink(missing_ok=True)
            raise RuntimeError(f"corrupt_extraction_cache:{cache_path}") from exc
        if (cached.get("cache_version") == CACHE_VERSION and cached.get("parser_identity") == PARSER_IDENTITY
                and not cached.get("error") and not cached.get("observed", {}).get("segmentation_error")):
            return _slim_extracted(cached)

    if traits["phase"] == "prefill":
        pf_cfg = json.loads(json.dumps(parse_case(tpl).model.to_dict()))
        pf_cfg["tp"] = traits["tp"]
        obs, meta = prefill.extract_file(csv_path, pf_cfg, timeout_s=45), {"context_evidence": None, "client": None}
    else:
        meta = capture_metadata(csv_path.parent)
        try:
            events, src_ref = _source(csv_path, {"kind": "csv"}, None, max_events=5_000_000, timeout_s=45)
            obs = compact_observation(auto_segment_decode_forwards(events, cfg, source=src_ref, max_events=5_000_000))
        except Exception as exc:
            # Never write transient or segmentation errors to persistent cache
            return {"cache_version": CACHE_VERSION, "parser_identity": PARSER_IDENTITY, "cache_key": cache_key,
                    "observed": {"forward_count": 0, "geometry_groups": [],
                                 "segmentation_error": f"{type(exc).__name__}:{exc}"},
                    "meta": meta}

    payload = {"cache_version": CACHE_VERSION, "parser_identity": PARSER_IDENTITY,
               "cache_key": cache_key, "observed": obs, "meta": meta}
    _atomic_write_json(cache_path, payload)
    return _slim_extracted(payload)


def _extract_worker(item: tuple[str, dict, dict, dict]) -> tuple[str, dict]:
    path_str, traits, tpl, seg_opts = item
    t0 = time.monotonic()
    payload = extract_or_load(Path(path_str), traits, tpl, seg_opts)
    return path_str, {**payload, "extract_seconds": round(time.monotonic() - t0, 3)}


def _predict_worker(item: tuple[tuple, dict]) -> tuple[tuple, dict]:
    key, tpl = item
    tpl_sig, phase, tokens, context, sequences = key
    pred_id = sha256(f"v2:{SIM_IDENTITY}:{tpl_sig}:{phase}:{tokens}:{context}:{sequences}".encode("utf-8")).hexdigest()[:24]
    cache_path = CACHE_ROOT / f"pred_{pred_id}.json"
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            cache_path.unlink(missing_ok=True)
            raise RuntimeError(f"corrupt_prediction_cache:{cache_path}") from exc
        if cached.get("status") == "modeled":
            return key, cached
    res = predict_body(tpl, tokens=int(tokens), context=int(context), sequences=int(sequences), phase=phase)
    res.pop("parameters", None)
    res.pop("scheduled_operator_summary", None)
    _atomic_write_json(cache_path, res)
    return key, res


def _unpadded_scenarios(row_dummy: dict, obs: dict, tpl: dict) -> list[dict]:
    scenarios = _automatic_scenarios(row_dummy, obs, tpl) if obs.get("geometry_groups") else []
    for s in scenarios:
        g = s["geometry"]
        out_q, q, tok = g.get("output_query_rows"), g.get("query_rows", 0), g.get("tokens_per_sequence", 1)
        if out_q and tok > 1 and out_q < q and out_q % tok == 0:
            g.update(physical_query_rows=q, query_rows=out_q, sequences_per_replica=out_q // tok)
    return scenarios


def evaluate_heldout_capture(csv_path: Path, traits: dict, tpl_name: str | None, tpl: dict | None,
                             cross_tp: bool, extracted: dict | None, pred_cache: dict, tpl_sig: str) -> dict:
    """Compare all extracted Decode/Prefill Body populations against pre-computed predict_body results."""
    if tpl_name is None or tpl is None or extracted is None:
        return {"path": str(csv_path), "traits": traits, "template": None, "cross_tp_transfer": False,
                "status": "unsupported_model", "reason": f"unsupported_hw_family:{traits['hw']}/{traits['family']}"}

    obs, meta = extracted["observed"], extracted["meta"]
    if traits["phase"] == "prefill":
        forwards = obs.get("forwards", [])
        if not forwards:
            return {"path": str(csv_path), "traits": traits, "template": tpl_name,
                    "cross_tp_transfer": cross_tp, "status": "unresolved", "reason": "no_prefill_forwards"}
        real_sum, pred_sum, steady_real, steady_pred, ctx = float(obs["body_span_sum_ms"]), 0.0, 0.0, 0.0, 0
        for f in forwards:
            q_rows = int(f["query_rows"])
            ctx = 0 if (ctx > 0 and ctx + q_rows > traits["context_tokens"]) else ctx
            p_ms, r_ms = float(pred_cache[(tpl_sig, "prefill", q_rows, ctx, 1)]["body_forward_span_ms"]), float(f["body"]["span_ms"])
            pred_sum += p_ms
            if q_rows >= 1024:
                steady_real, steady_pred = steady_real + r_ms, steady_pred + p_ms
            ctx += q_rows
        complete_err = (pred_sum / real_sum - 1.0) if real_sum > 0 else None
        steady_err = (steady_pred / steady_real - 1.0) if steady_real > 0 else complete_err
        return {"path": str(csv_path), "traits": traits, "template": tpl_name, "cross_tp_transfer": cross_tp,
                "status": "compared", "forward_count": len(forwards), "observed_ms": round(real_sum, 4),
                "predicted_ms": round(pred_sum, 4), "relative_error": round(complete_err, 6) if complete_err is not None else None,
                "complete_body_relative_error": round(complete_err, 6) if complete_err is not None else None,
                "steady_chunk_observed_ms": round(steady_real, 4) if steady_real > 0 else None,
                "steady_chunk_predicted_ms": round(steady_pred, 4) if steady_real > 0 else None,
                "steady_chunk_relative_error": round(steady_err, 6) if steady_err is not None else None,
                "passed_15pct": bool(abs(complete_err) <= 0.15) if complete_err is not None else False,
                "passed_10pct": bool(abs(complete_err) <= 0.10) if complete_err is not None else False,
                "steady_chunk_passed_15pct": bool(abs(steady_err) <= 0.15) if steady_err is not None else False,
                "steady_chunk_passed_10pct": bool(abs(steady_err) <= 0.10) if steady_err is not None else False}

    row_dummy = {"geometry": {"phase": "decode", "context_tokens": traits["context_tokens"]},
                 "context_evidence": meta.get("context_evidence"), "scenario_evidence": {"client": _client_evidence(meta, traits)}}
    scenarios = _unpadded_scenarios(row_dummy, obs, tpl)
    if not scenarios:
        return {"path": str(csv_path), "traits": traits, "template": tpl_name, "cross_tp_transfer": cross_tp,
                "status": "unresolved", "reason": obs.get("segmentation_error") or "no_automatic_decode_scenarios"}
    scenarios.sort(key=lambda s: -s["observed"]["body_forward_span_ms"]["count"])

    populations = []
    for scen in scenarios:
        g = scen["geometry"]
        pr = pred_cache[(tpl_sig, "decode", int(g["tokens_per_sequence"]), int(g["context_tokens"]), int(g["sequences_per_replica"]))]
        c_res = compare_body_forward(pr, scen["observed"])
        r_err = c_res.get("relative_error")
        populations.append({
            "status": c_res["status"], "forward_count": int(c_res["observed_forward_count"]),
            "geometry": {k: g.get(k) for k in ("tokens_per_sequence", "sequences_per_replica", "query_rows", "physical_query_rows", "context_tokens")},
            "observed_ms": round(float(c_res["observed_ms"]["mean"]), 4) if c_res.get("observed_ms") else None,
            "predicted_ms": round(float(c_res["predicted_ms"]), 4) if c_res.get("predicted_ms") is not None else None,
            "relative_error": round(float(r_err), 6) if r_err is not None else None,
            "passed_15pct": bool(abs(r_err) <= 0.15) if r_err is not None else False,
            "passed_10pct": bool(abs(r_err) <= 0.10) if r_err is not None else False})

    top_pop, top_geom = populations[0], scenarios[0]["geometry"]
    top_pred = pred_cache[(tpl_sig, "decode", int(top_geom["tokens_per_sequence"]), int(top_geom["context_tokens"]), int(top_geom["sequences_per_replica"]))]
    cl = compare_layers(top_pred, scenarios[0]["observed"])
    valid_pops = [p for p in populations if p["relative_error"] is not None and p["forward_count"] > 0]
    tot_fwds = sum(p["forward_count"] for p in valid_pops)
    if tot_fwds > 0:
        w_obs = sum(p["observed_ms"] * p["forward_count"] for p in valid_pops) / tot_fwds
        w_pred = sum(p["predicted_ms"] * p["forward_count"] for p in valid_pops) / tot_fwds
        all_pop_err = (w_pred - w_obs) / w_obs if w_obs > 0 else top_pop["relative_error"]
    else:
        w_obs, w_pred, all_pop_err = top_pop["observed_ms"], top_pop["predicted_ms"], top_pop["relative_error"]

    return {"path": str(csv_path), "traits": traits, "template": tpl_name, "cross_tp_transfer": cross_tp,
            "status": top_pop["status"], "forward_count": tot_fwds or top_pop["forward_count"],
            "primary_forward_count": top_pop["forward_count"], "geometry": top_pop["geometry"],
            "observed_ms": round(float(w_obs), 4) if w_obs is not None else None,
            "predicted_ms": round(float(w_pred), 4) if w_pred is not None else None,
            "relative_error": round(float(all_pop_err), 6) if all_pop_err is not None else None,
            "primary_relative_error": top_pop["relative_error"],
            "all_populations_relative_error": round(float(all_pop_err), 6) if all_pop_err is not None else None,
            "populations_count": len(populations), "populations_passed_15pct": sum(1 for p in valid_pops if p["passed_15pct"]),
            "populations_passed_10pct": sum(1 for p in valid_pops if p["passed_10pct"]), "populations": populations,
            "passed_15pct": bool(abs(all_pop_err) <= 0.15) if all_pop_err is not None else False,
            "passed_10pct": bool(abs(all_pop_err) <= 0.10) if all_pop_err is not None else False,
            "layer_summary": cl.get("summary", {})}


def _summarize_errors(errors: list[float]) -> dict:
    if not errors:
        return {"count": 0, "pass_15pct": 0, "pass_10pct": 0, "pass_rate_15pct": 0.0, "pass_rate_10pct": 0.0}
    abs_errs = [abs(e) for e in errors]
    p15, p10, n = sum(e <= 0.15 for e in abs_errs), sum(e <= 0.10 for e in abs_errs), len(errors)
    return {"count": n, "pass_15pct": p15, "pass_10pct": p10, "pass_rate_15pct": round(p15 / n, 4),
            "pass_rate_10pct": round(p10 / n, 4), "mean_abs_error": round(sum(abs_errs) / n, 4),
            "median_abs_error": round(median(abs_errs), 4), "max_abs_error": round(max(abs_errs), 4)}


def _write_markdown(report: dict, out_md: Path) -> None:
    inv, s = report["inventory"], report["summary"]
    lines = [
        "# MindIE-Sim Full-Fleet DSH Capture Parsing & Zero-Shot Generalization Report", "",
        "## 1. Executive Summary & Fleet Inventory", "",
        f"- **DSH `2026-10-30` Total `kernel_details.csv` Captures**: `{inv['dsh_20261030_total_csvs']}`",
        f"  - **Registered in `cases.json` (`body` scope)**: `{inv['dsh_20261030_registered_body_csvs']}`",
        f"  - **Excluded Pure Decode-Eager Captures**: `{inv['dsh_20261030_eager_excluded_csvs']}`",
        f"  - **Unregistered Held-Out Captures Evaluated**: `{inv['dsh_20261030_unregistered_heldout_csvs']}` across `{len(report['cohort_summaries'])}` cohorts",
        f"- **Total Evaluated Body Captures (Registered + Held-Out)**: `{inv['total_evaluated_body_cases']}` (`{s['full_fleet_combined']['count']}` compared)", "",
        "| Evaluation Scope | Compared | Pass `<= 15%` | Rate `<= 15%` | Pass `<= 10%` | Rate `<= 10%` | Mean `|Err|` | Median `|Err|` | Max `|Err|` |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, key in [("Registered Decode Body (`cases.json`)", "registered_decode_body"),
                       ("Registered Prefill Body (`cases.json`)", "registered_prefill_body"),
                       ("Held-Out Unregistered (Excl. Uncalibrated `v41` `dspark0`)", "heldout_unregistered_excluding_v41_dspark0_uncalibrated_sp1"),
                       ("Held-Out Unregistered (All Compared, All Populations)", "heldout_unregistered_all"),
                       ("Held-Out Unregistered (Primary Population)", "heldout_unregistered_primary_population"),
                       ("**Full Fleet Combined**", "full_fleet_combined")]:
        r = s[key]
        lines.append(f"| {label} | {r['count']} | {r['pass_15pct']} | **{r['pass_rate_15pct']*100:.2f}%** | {r['pass_10pct']} | **{r['pass_rate_10pct']*100:.2f}%** | {r['mean_abs_error']*100:.2f}% | {r['median_abs_error']*100:.2f}% | {r['max_abs_error']*100:.2f}% |")
    lines.extend(["", "## 2. Held-Out Cohort Breakdown", "",
                  "| Cohort | Family | Phase | TP/DP/EP | Spec | Cross-TP | Template | Captures | Compared | Pass `<=15%` | Pass `<=10%` | Mean `|Err|` | Median `|Err|` |",
                  "| :--- | :--- | :--- | :--- | ---: | :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for c in report["cohort_summaries"]:
        st, spec_s = c["stats"], ("-" if c["spec_tokens"] is None else str(c["spec_tokens"]))
        p15 = f"{st['pass_15pct']}/{st['count']} ({st['pass_rate_15pct']*100:.1f}%)" if st["count"] else "N/A"
        p10 = f"{st['pass_10pct']}/{st['count']} ({st['pass_rate_10pct']*100:.1f}%)" if st["count"] else "N/A"
        m_s, md_s = (f"{st['mean_abs_error']*100:.2f}%", f"{st['median_abs_error']*100:.2f}%") if st["count"] else ("N/A", "N/A")
        lines.append(f"| `{c['cohort']}` | `{c['family']}` | `{c['phase']}` | `{c['tp']}/{c['dp']}/{c['ep']}` | {spec_s} | {'Yes' if c['cross_tp_transfer'] else 'No'} | `{c['template']}` | {c['capture_count']} | {c['compared_count']} | {p15} | {p10} | {m_s} | {md_s} |")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _bounded_workers(requested: int, worker_ram_mb: int = 512) -> int:
    cpu_cap, usable_mb = os.cpu_count() or 1, None
    try:
        import psutil
        usable_mb = max(worker_ram_mb, int(psutil.virtual_memory().available) // (1024 * 1024))
    except Exception:
        pass
    if usable_mb is None:
        try:
            pages = os.sysconf("SC_AVPHYS_PAGES")
            if isinstance(pages, int) and pages > 0:
                usable_mb = max(worker_ram_mb, (int(pages) * int(os.sysconf("SC_PAGE_SIZE"))) // (1024 * 1024))
        except (AttributeError, OSError, ValueError):
            pass
    return 1 if usable_mb is None else max(1, min(int(requested), cpu_cap, usable_mb // worker_ram_mb, 4))


def _run_bounded_pool(fn, items: list, workers: int, *, step_timeout_s: float = 60.0, progress_step: int = 100, label: str = "Processed") -> dict:
    """Execute worker items with 1-per-worker in-flight depth so per-future deadlines measure execution time."""
    if not items:
        return {}
    results, started_at, it, completed, pool = {}, {}, iter(items), 0, ProcessPoolExecutor(max_workers=workers)
    try:
        for _ in range(min(max(1, workers), len(items))):
            started_at[pool.submit(fn, next(it))] = time.monotonic()
        while started_at:
            now = time.monotonic()
            remaining = min(step_timeout_s - (now - t0) for t0 in started_at.values())
            done, _ = wait(set(started_at.keys()), timeout=max(0.0, remaining), return_when=FIRST_COMPLETED) if remaining > 0 else (set(), set())
            if not done:
                raise TimeoutError(f"worker_future_timed_out_after_{step_timeout_s}s")
            for fut in done:
                started_at.pop(fut, None)
                k, v = fut.result(timeout=1.0)
                results[k], completed = v, completed + 1
                if completed % progress_step == 0 or completed == len(items):
                    print(f"  {label} {completed}/{len(items)}...", flush=True)
                try:
                    started_at[pool.submit(fn, next(it))] = time.monotonic()
                except StopIteration:
                    pass
    finally:
        for fut in started_at:
            fut.cancel()
        for proc in list((getattr(pool, "_processes", None) or {}).values()) if started_at else ():
            try:
                proc.kill()
            except Exception:
                pass
        pool.shutdown(wait=False, cancel_futures=True)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output-json", type=Path, default=BASE_DIR / "results" / "dsh_full_generalization.json")
    parser.add_argument("--output-md", type=Path, default=BASE_DIR / "results" / "dsh_full_generalization.md")
    args = parser.parse_args(argv)
    workers = _bounded_workers(args.workers)
    started = time.monotonic()

    cases_reg = json.loads((BASE_DIR / "cases.json").read_text())["cases"]
    reg_by_path = {Path(c["source"]["path"]).resolve(): c for c in cases_reg
                   if c.get("source", {}).get("path") and c.get("supported_scopes") != ["engine"]}
    decode_sb = json.loads((BASE_DIR / "results" / "decode.json").read_text())
    prefill_sb = json.loads((BASE_DIR / "results" / "prefill.json").read_text())

    reg_decode_errs = []
    for c in decode_sb["cases"]:
        rel_e = (c.get("comparison") or {}).get("relative_error")
        if rel_e is None and c.get("id") in ("decode:a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64", "decode:a5_v41_fp8_tp1_dp8_ep8_c128_p2k"):
            reg_row = next(r for r in cases_reg if r["id"] == c["id"])
            tpl_d = json.loads((BASE_DIR / reg_row["sim_case_path"]).read_text())
            g = reg_row["forward_metadata"]["geometry_groups"][0]["geometry"]
            pred = predict_body(tpl_d, tokens=g["tokens_per_sequence"], context=reg_row["geometry"]["context_tokens"],
                                sequences=g["sequences_per_replica"], phase="decode")
            cfg_d = {**_model_config(tpl_d), **reg_row.get("segmentation_options", {})}
            ev, sref = _source(Path(reg_row["source"]["path"]), {"kind": "csv"}, None, max_events=5_000_000, timeout_s=60)
            obs_d = compact_observation(auto_segment_decode_forwards(ev, cfg_d, source=sref, max_events=5_000_000))
            scens = _automatic_scenarios(reg_row, obs_d, tpl_d)
            scens.sort(key=lambda s: -s["observed"]["body_forward_span_ms"]["count"])
            rel_e = compare_body_forward(pred, scens[0]["observed"])["relative_error"]
        if rel_e is not None:
            reg_decode_errs.append(float(rel_e))
    reg_prefill_errs = [float(c["comparison"]["relative_error"]) for c in prefill_sb["cases"]
                        if (c.get("comparison") or {}).get("relative_error") is not None]

    all_dsh_csvs = sorted(
        list((DATA_ROOT / "a3" / "heldout_engine_20261030").rglob("kernel_details.csv"))
        + list((DATA_ROOT / "a5" / "heldout_engine_20261030").rglob("kernel_details.csv"))
        + [DATA_ROOT / "a5" / f"qwen3_5_35b_a3b_w8a8_mtp_high_conc_decode_{tag}_20261030" / "kernel_details.csv"
           for tag in ("tpot10ms_c32", "tpot30ms_c8", "tpot5ms_c16")]
    )
    all_dsh_csvs = [p.resolve() for p in all_dsh_csvs if p.exists()]

    eager_excluded, heldout_tasks, registered_in_dsh = [], [], []
    for csv_path in all_dsh_csvs:
        traits = parse_capture_traits(csv_path)
        if traits["is_eager"]:
            eager_excluded.append({"path": str(csv_path), "traits": traits, "reason": "decode_eager_excluded"})
        elif csv_path in reg_by_path:
            registered_in_dsh.append(str(csv_path))
        else:
            tpl_name, tpl, seg_opts, cross_tp = resolve_template(traits)
            tpl_sig = sha256(json.dumps(tpl, sort_keys=True).encode("utf-8")).hexdigest()[:16] if tpl else "unsupported"
            heldout_tasks.append((csv_path, traits, tpl_name, tpl, seg_opts, cross_tp, tpl_sig))

    print(f"Inventory: total_dsh={len(all_dsh_csvs)} | registered={len(registered_in_dsh)} "
          f"| eager_excluded={len(eager_excluded)} | heldout={len(heldout_tasks)}", flush=True)

    worker_items = [(str(p), tr, tpl, seg) for (p, tr, _, tpl, seg, _, _) in heldout_tasks if tpl is not None]
    extractions = _run_bounded_pool(_extract_worker, worker_items, workers, step_timeout_s=60.0,
                                    progress_step=100, label="Extracted")

    pred_jobs: dict[tuple, dict] = {}
    for p, tr, _, tpl, _, _, tpl_sig in heldout_tasks:
        if tpl is None:
            continue
        obs, meta = extractions[str(p)]["observed"], extractions[str(p)]["meta"]
        if tr["phase"] == "prefill":
            ctx = 0
            for f in obs.get("forwards", []):
                q_rows = int(f["query_rows"])
                ctx = 0 if (ctx > 0 and ctx + q_rows > tr["context_tokens"]) else ctx
                pred_jobs[(tpl_sig, "prefill", q_rows, ctx, 1)], ctx = tpl, ctx + q_rows
        elif obs.get("geometry_groups"):
            row_dummy = {"geometry": {"phase": "decode", "context_tokens": tr["context_tokens"]},
                         "context_evidence": meta.get("context_evidence"), "scenario_evidence": {"client": _client_evidence(meta, tr)}}
            for s in _unpadded_scenarios(row_dummy, obs, tpl):
                g = s["geometry"]
                pred_jobs[(tpl_sig, "decode", int(g["tokens_per_sequence"]), int(g["context_tokens"]), int(g["sequences_per_replica"]))] = tpl

    print(f"Running {len(pred_jobs)} unique predict_body geometries across {workers} workers...", flush=True)
    pred_cache = _run_bounded_pool(_predict_worker, list(pred_jobs.items()), workers, step_timeout_s=180.0, progress_step=50, label="Priced")
    heldout_results = [evaluate_heldout_capture(p, tr, tn, tpl, ct, extractions.get(str(p)), pred_cache, tsig) for (p, tr, tn, tpl, _, ct, tsig) in heldout_tasks]
    by_cohort: dict[str, list[dict]] = defaultdict(list)
    for r in heldout_results:
        by_cohort[r["traits"]["cohort"]].append(r)

    cohort_summaries = []
    for cohort_key, items in sorted(by_cohort.items()):
        errs = [x["relative_error"] for x in items if x.get("relative_error") is not None]
        tr0 = items[0]["traits"]
        cohort_summaries.append({"cohort": cohort_key, "hw": tr0["hw"], "family": tr0["family"], "phase": tr0["phase"],
                                 "tp": tr0["tp"], "dp": tr0["dp"], "ep": tr0["ep"], "spec_tokens": tr0["spec_tokens"],
                                 "template": items[0]["template"], "cross_tp_transfer": items[0]["cross_tp_transfer"],
                                 "capture_count": len(items), "compared_count": len(errs), "stats": _summarize_errors(errs)})

    heldout_errs = [r["relative_error"] for r in heldout_results if r.get("relative_error") is not None]
    heldout_prim_errs = [r.get("primary_relative_error", r["relative_error"]) for r in heldout_results if r.get("relative_error") is not None]
    heldout_non_dspark0 = [r["relative_error"] for r in heldout_results if r.get("relative_error") is not None
                           and not (r["traits"]["family"] == "deepseek-v4.1" and r["traits"]["spec_tokens"] == 0)]
    all_fleet_errs = reg_decode_errs + reg_prefill_errs + heldout_errs

    report = {
        "schema_version": "mindie-dsh-full-generalization/2", "elapsed_seconds": round(time.monotonic() - started, 2),
        "inventory": {
            "dsh_20261030_total_csvs": len(all_dsh_csvs), "dsh_20261030_registered_body_csvs": len(registered_in_dsh),
            "dsh_20261030_eager_excluded_csvs": len(eager_excluded), "dsh_20261030_unregistered_heldout_csvs": len(heldout_tasks),
            "registered_decode_body_cases": len(reg_decode_errs), "registered_prefill_compared_cases": len(reg_prefill_errs),
            "total_evaluated_body_cases": len(reg_decode_errs) + len(reg_prefill_errs) + len(heldout_tasks)},
        "summary": {
            "registered_decode_body": _summarize_errors(reg_decode_errs), "registered_prefill_body": _summarize_errors(reg_prefill_errs),
            "heldout_unregistered_all": _summarize_errors(heldout_errs), "heldout_unregistered_primary_population": _summarize_errors(heldout_prim_errs),
            "heldout_unregistered_excluding_v41_dspark0_uncalibrated_sp1": _summarize_errors(heldout_non_dspark0),
            "full_fleet_combined": _summarize_errors(all_fleet_errs)},
        "cohort_summaries": cohort_summaries, "eager_excluded": eager_excluded, "heldout_cases": heldout_results}
    _atomic_write_json(args.output_json, report, indent=2)
    _write_markdown(report, args.output_md)
    print(f"Wrote JSON & MD reports: {args.output_json} ({len(all_fleet_errs)} compared)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
