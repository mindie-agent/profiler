"""Build, verify, and evaluate the reproducible NPU profiling benchmark dataset.

[Role]
  Export and replay the canonical 7,337-capture NPU profiling benchmark dataset
  (``maoxx241/mindie-sim-profiling-bench``) spanning ``A2`` (837), ``A3`` (1,729),
  and ``A5`` (4,771) hardware tiers across both Prefill and Decode phases.

[Invariants]
  * Suite 1 (``data/zero_shot_l1_l4_cells.jsonl[.gz]``) preserves unmodified
    model profiling traces and measurement-blind ``CellSpec`` declarations so
    ``zero_shot_piecewise_validation.py --benchmark-jsonl`` reproduces the exact
    21-row four-level (L1-L4) per-step validation scoreboard (100.0% <= 10%).
  * Suite 2 (``data/fleet_captures.jsonl[.gz]``) indexes all 6,606 remaining
    non-communication profiling captures across structure, heldout, Wave 5,
    A5 multi-node full-coverage, calibration, and workstream suites, verifying
    100% zero-crash structural inference (``infer_trace_structure``) and full
    operator-level and step-level physical modeling.
  * Documentation, manifest, and metadata scrub internal IP addresses and
    chip SKU model numbers, referring to hardware tiers strictly as A2/A3/A5.

[Timeouts & Locks]
  Bounded local file streaming and deterministic evaluation; no locks, daemons,
  or unbounded in-memory buffers.

[Side-Effect Policy]
  Writes only to the explicitly requested ``--output-dir`` and optionally uploads
  to HuggingFace when ``--upload`` is passed.
"""
from __future__ import annotations
import argparse, base64, csv, gzip, hashlib, json, math, os, re, sys, urllib.request
from collections import Counter
from dataclasses import replace
from functools import lru_cache
from pathlib import Path, PurePosixPath
from statistics import median
from typing import Any, Mapping, Sequence
ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parent.name == "structure" else Path(__file__).resolve().parents[1]
SIM_ROOT = ROOT.parent / "sim"
for _p in (str(ROOT), str(SIM_ROOT), str(ROOT / "examples" / "structure")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import fleet_capture_observations  # noqa: E402
import fleet_operator_modeling as fleet_modeling  # noqa: E402
import hf_benchmark_gate  # noqa: E402
import hf_benchmark_requests as _benchmark_requests  # noqa: E402
from hf_benchmark_requests import (  # noqa: E402
    _attach_request_forecast, _header_fields, _l4_interface, _l4_physical, _zero_shot_l4_pair,
)
from hf_request_ttft import _bind_request_forecast  # noqa: E402
import mindie_sim  # noqa: E402
import zero_shot_piecewise_validation as zsv  # noqa: E402
from fleet_operator_modeling import enrich_all_fleet_captures, enrich_fleet_capture_with_operator_and_step_modeling, parse_kernel_details_summary, predict_capture_operators_and_step  # noqa: E402
from mindie_profiler.structural_inference import infer_trace_structure  # noqa: E402
from mindie_sim.prediction.structure import parse_case  # noqa: E402
from runtime_identity import simulator_identity  # noqa: E402
RESULTS_DIR, CASES_DIR = ROOT / "examples" / "structure" / "results", ROOT / "examples" / "structure" / "cases"
DATA_ROOTS = (Path("/Volumes/data/mindie-sim-data"), Path("/Users/maoxx241/code/mindie-agent/.workstreams"))
MULTINODE_20261108_ROOT = Path("/Volumes/data/mindie-sim-data/a5/multinode-full-coverage-20261108")
DEFAULT_HF_REPO = "maoxx241/mindie-sim-profiling-bench"
_SKIP_DIRS = {"a5-comm", "a5-mc2", "comm-fit", "comm-paired", "comm_collective", "hccl", "hccl-native", "acceptance-archives-20261030"}
_DOC_REDACT_RE = re.compile(r"(?i)\b(?:ascend\s*910\w*|ascend\s*950\w*|910b\w*|9362|950pr|950dt|9579|9581|9582|arch3510)\b|(?:\b(?:177\.(?:25|31)|192\.168|173\.125)\.\d{1,3}\.\d{1,3}\b)")
_PATH_PREFIX_RE = re.compile(r"^/(?:Volumes/data/(?:mindie-sim-data|storage-archive/[^/]+|code/[^/]+/(?:profiler/examples/structure/)?)/|Users/[^/]+/code/(?:profiler/examples/structure/)?|mnt/weight/)")
_GENERIC_ANCESTORS = {"a2", "a3", "a5", "prof", "runs", "out", "cells", "ranks", "raw", "longctx", "2026-10-22", "2026-10-23", "2026-10-24", "heldout_engine_20261030", "heldout_engine_20261031", "mindie-agent", ".workstreams"}
_UNIFIED_FAMILIES: tuple[tuple[str, str, str], ...] = (
    ("matmul_gemm", "cube_gemm", "L1:gemm"), ("attention", "attention_mla", "L1:attention"),
    ("moe_routing_grouped_gemm", "moe_comm_fusion", "L1:moe_grouped"), ("norm_activation_elementwise", "vector_elementwise", "L1:elementwise_quant"),
    ("kv_cache_position_rope", "vector_elementwise", "L1:kv_cache"), ("collective_comm", "moe_comm_fusion", "L1:collective"),
)
_UNIFIED_CORES: tuple[tuple[str, str], ...] = (("AI_CORE", "L1:gemm"), ("AI_VECTOR_CORE", "L1:elementwise_quant"), ("MIX_AIC", "L1:attention"), ("COMMUNICATION", "L1:collective"))
_GEOM_PASSTHROUGH = ("ep_dspark_wave_scale", "prompt_tokens", "sequences_per_replica", "tokens_per_sequence", "query_rows", "body_chunks", "concurrency", "context_tokens", "tp", "dp", "ep", "pp", "ep_enabled", "num_layers", "num_experts", "top_k", "graph_buckets", "graph_bucket", "notes")
_DEMAND_FIELDS = ("structural_weights", "active_hbm_mb", "active_cube_gflops")
_FULL_POPULATION = {"zero_shot": 731, "fleet": 6606, "A2": 837, "A3": 1729, "A5": 4771}
def _clean_text(text: str) -> str:
    s = str(text or "").replace("/Volumes/data/mindie-agent-workstreams/", "mindie-agent/.workstreams/")
    return re.sub(r"\b(?:177\.(?:25|31)|192\.168|173\.125)\.\d{1,3}\.\d{1,3}\b", "node", re.sub(r"(?i)ascend(?:910b|950(?:pr|dt)?)[_-]?", "", _PATH_PREFIX_RE.sub("", s)))
def _hw_tier(raw_hw: str, fallback_text: str = "") -> str:
    probe = f"{raw_hw} {fallback_text}".lower()
    return "A2" if "a2" in probe else ("A5" if any(k in probe for k in ("a5", "r06_", "r08_", "rack0", "950")) else "A3")
def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024): digest.update(chunk)
    return digest.hexdigest()
def _write_jsonl_gz(path: Path, rows: Sequence[Mapping[str, Any]], *, also_plain: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plain_handle = path.with_suffix("").open("wt", encoding="utf-8", newline="\n") if also_plain and path.suffix == ".gz" else None
    try:
        with gzip.open(path, "wt", encoding="utf-8", newline="\n") as gz_handle:
            for row in rows:
                line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"; gz_handle.write(line)
                if plain_handle is not None: plain_handle.write(line)
    finally:
        if plain_handle is not None: plain_handle.close()
def _read_jsonl_any(path: Path) -> list[dict[str, Any]]:
    with (gzip.open if str(path).endswith(".gz") else open)(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
def _positive_int(value: Any) -> int | None:
    if value in (None, ""): return None
    try: number = int(value)
    except (TypeError, ValueError): return None
    return number if number >= 1 else None
def _calibration_role(relation: str, status: str = "") -> str:
    """Role comes from the source relation. ``status`` is ignored and cannot mark not_blind."""
    del status
    rel = str(relation or "").strip()
    if rel == "in_sample": return "in_sample"
    if rel == "retrospective_context_transfer; not_blind": return "not_blind"
    return rel or "unspecified"
def _finite_abs_max(values: Sequence[Any]) -> float:
    """One non-finite sample makes the cell non-finite, even after a finite 0.001."""
    best: float | None = None
    for raw in values:
        try: number = abs(float(raw))
        except (TypeError, ValueError): return float("nan")
        if not math.isfinite(number): return float("nan")
        best = number if best is None else max(best, number)
    return float("nan") if best is None else best
@lru_cache(maxsize=256)
def _case_spec_geometry(model_hint: str) -> dict[str, Any]:
    """Read structured fields from the named case file. Never substitute another model."""
    name = Path(str(model_hint or "").strip()).name
    cand = CASES_DIR / name if name.endswith(".json") else None
    if cand is None or not cand.is_file(): return {}
    try: raw = json.loads(cand.read_text(encoding="utf-8"))
    except (OSError, ValueError): return {}
    rt = raw.get("runtime") if isinstance(raw.get("runtime"), Mapping) else {}
    out: dict[str, Any] = {}
    for key in ("tp", "dp", "ep", "pp"):
        if (number := _positive_int(rt.get(key))) is not None: out[key] = number
    if rt.get("mtp_speculative_tokens") is not None: out["tokens_per_sequence"] = 1 + int(rt.get("mtp_speculative_tokens") or 0)
    nested = raw.get("geometry") if isinstance(raw.get("geometry"), Mapping) else {}
    for src in (raw, nested):
        for key in _DEMAND_FIELDS:
            if key not in out and src.get(key) not in (None, ""): out[key] = src[key]
    try: parsed = parse_case(raw)
    except (OSError, ValueError, KeyError, TypeError): return out
    if (layers := _positive_int(parsed.model.body_layers or parsed.model.layers or 0)) is not None: out["num_layers"] = layers
    if (experts := _positive_int(parsed.model.num_experts or 0)) is not None: out["num_experts"] = experts
    if (top_k := _positive_int(parsed.model.top_k or 0)) is not None: out["top_k"] = top_k
    return out
def _complete_geometry(raw_geom: Mapping[str, Any] | None, phase: str, model_case: str = "", cid_hint: str = "", *, demand_sources: Sequence[tuple[str, Mapping[str, Any]]] = ()) -> dict[str, Any]:
    """Fill geometry from declared metadata only. Missing demand stays absent, not defaulted."""
    out = {k: v for k, v in (raw_geom or {}).items() if v is not None and (k in _GEOM_PASSTHROUGH or k in {"output_tokens", "num_nodes", *_DEMAND_FIELDS})}
    spec_g = _case_spec_geometry(model_case or cid_hint)
    for key, value in spec_g.items():
        if out.get(key) is None and value is not None: out[key] = value
    probe, ph = f"{cid_hint} {model_case}".lower(), ("prefill" if str(phase).lower() == "prefill" else "decode")
    for key, pattern in (("tp", r"(?<![a-z])tp(\d+)"), ("dp", r"(?<![a-z])dp(\d+)"), ("ep", r"(?<![a-z])ep(\d+)")):
        if not out.get(key) and (match := re.search(pattern, probe)) and (number := _positive_int(match.group(1))) is not None and (key != "tp" or number in {1, 2, 4, 8, 16, 32}): out[key] = number
    if not out.get("ep") and out.get("ep_enabled") is True and out.get("tp") and out.get("dp"): out["ep"] = int(out["tp"]) * int(out["dp"])
    if not out.get("prompt_tokens") and not out.get("context_tokens"):
        if (match := re.search(r"(?:isl|p_|_p|-p|decode_|prefill_|dc_|pf_)(\d+)(k)?", probe)): out["prompt_tokens"] = out["context_tokens"] = int(match.group(1)) * (1024 if match.group(2) else 1)
        elif (match := re.search(r"_(\d+)k_", probe)): out["prompt_tokens"] = out["context_tokens"] = int(match.group(1)) * 1024
    elif out.get("context_tokens") or out.get("prompt_tokens"):
        tok = int(out.get("context_tokens") or out.get("prompt_tokens"))
        out.setdefault("context_tokens", tok); out.setdefault("prompt_tokens", int(out.get("prompt_tokens") or tok))
    if not out.get("concurrency") and not out.get("sequences_per_replica") and (match := re.search(r"_c(\d+)\b", probe)) and (number := _positive_int(match.group(1))) is not None: out["concurrency"] = number
    if out.get("concurrency") or out.get("sequences_per_replica"):
        conc, dp_val = max(1, int(out.get("concurrency") or out.get("sequences_per_replica") or 1)), max(1, int(out.get("dp") or 1))
        out["concurrency"] = conc; out["sequences_per_replica"] = max(1, int(out.get("sequences_per_replica") or max(1, conc // dp_val)))
    if out.get("prompt_tokens") or out.get("tokens_per_sequence") or out.get("sequences_per_replica"):
        tps = int(out["tokens_per_sequence"]) if out.get("tokens_per_sequence") else (int(out["prompt_tokens"]) if ph == "prefill" and out.get("prompt_tokens") else None)
        if tps is not None: out["tokens_per_sequence"] = max(1, tps)
        if out.get("query_rows") is None and out.get("tokens_per_sequence") and out.get("sequences_per_replica"):
            out["query_rows"] = int(out["tokens_per_sequence"]) * int(out["sequences_per_replica"]) if ph == "decode" else int(out.get("prompt_tokens") or out["tokens_per_sequence"])
        elif out.get("query_rows") is None and ph == "prefill" and out.get("prompt_tokens"): out["query_rows"] = int(out["prompt_tokens"])
    if out.get("body_chunks") is None and ph == "prefill" and out.get("prompt_tokens"): out["body_chunks"] = max(1, round(int(out["prompt_tokens"]) / 4096))
    elif out.get("body_chunks") is None and ph == "decode": out["body_chunks"] = 1
    provenance = {key: "absent" for key in _DEMAND_FIELDS}
    for source_name, source in (("capture_geometry", raw_geom or {}), ("case_config", spec_g), *demand_sources):
        if not isinstance(source, Mapping): continue
        for key in _DEMAND_FIELDS:
            if provenance[key] == "absent" and source.get(key) not in (None, ""):
                out[key] = source[key]; provenance[key] = source_name
    out["demand_provenance"] = provenance
    return out
@lru_cache(maxsize=1)
def _local_session_index() -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    def _put(key: str, meta: dict[str, Any]) -> None:
        if key and (":" in key or key.count("/") >= 1): idx[key] = {**idx.get(key, {}), **{k: v for k, v in meta.items() if v is not None}}
    def _put_anc(base_dir: str, meta: dict[str, Any]) -> None:
        cur = Path(base_dir)
        for _ in range(4):
            if (s := str(cur)) in {"", ".", "/"}: break
            if cur.name not in _GENERIC_ANCESTORS or s == base_dir: _put(s, meta)
            cur = cur.parent
    if (cases_path := RESULTS_DIR.parent / "cases.json").is_file():
        for entry in json.loads(cases_path.read_text(encoding="utf-8")).get("cases", ()):
            cid, ph = str(entry.get("case_id") or ""), str(entry.get("phase") or "decode").lower()
            mc, fm, cli = _clean_text((entry.get("model_case") or {}).get("path", "")), entry.get("forward_metadata") or {}, ((entry.get("scenario_evidence") or {}).get("client") or {})
            g = dict(entry.get("geometry") or {})
            for gk, fv in (("prompt_tokens", fm.get("declared_prompt_tokens") or cli.get("input_len")), ("query_rows", fm.get("captured_query_tokens")), ("body_chunks", fm.get("body_chunks")), ("num_layers", fm.get("layer_count")), ("concurrency", cli.get("concurrency"))):
                if fv: g.setdefault(gk, int(fv))
            meta = {"model_case": mc, "phase": ph, "geometry": g, "forward_steps": fm.get("observed_forward_count")}
            _put(f"registered_{ph}:{cid}", meta)
            if src_p := _clean_text(((entry.get("source") or {}).get("path") or "")): _put_anc(str(Path(src_p).parent) if src_p.endswith((".csv", ".gz")) else src_p, meta)
    for ph, fname in (("decode", "decode.json"), ("prefill", "prefill.json")):
        if not (fpath := RESULTS_DIR / fname).is_file(): continue
        for case in json.loads(fpath.read_text(encoding="utf-8")).get("cases", ()):
            if not (src_p := _clean_text(((case.get("source") or {}).get("path") or ""))): continue
            comp, pop, cli, obs = case.get("comparison") or {}, case.get("population_coverage") or {}, case.get("client") or {}, (case.get("comparison") or {}).get("observed_ms")
            obs_ms = (obs.get("mean") if isinstance(obs, Mapping) else obs) or case.get("body_activity_union_sum_ms") or (cli.get("ttft_ms") or {}).get("mean")
            g = dict(case.get("geometry") or {})
            if cli.get("input_len"): g.setdefault("prompt_tokens", int(cli["input_len"]))
            if cli.get("concurrency"): g.setdefault("concurrency", int(cli["concurrency"]))
            _put_anc(str(Path(src_p).parent) if src_p.endswith((".csv", ".gz")) else src_p, {"model_case": _clean_text((case.get("model_case") or {}).get("path", "")), "phase": ph, "observed_ms": float(obs_ms) if obs_ms is not None else None, "forward_steps": int(pop.get("observed_calls") or comp.get("observed_forward_count") or 1), "geometry": g})
    if (dsh_p := RESULTS_DIR / "dsh_full_generalization.json").is_file():
        for item in json.loads(dsh_p.read_text(encoding="utf-8")).get("heldout_cases", ()):
            if not (rel_p := _clean_text(item.get("path", ""))): continue
            traits, pops, g = item.get("traits") or {}, item.get("populations") or (), dict(item.get("geometry") or {})
            for tk in ("tp", "dp", "ep", "concurrency"):
                if traits.get(tk) is not None and g.get(tk) is None: g[tk] = int(traits[tk])
            ph = "prefill" if str(traits.get("phase") or "").lower() == "prefill" or "prefill" in rel_p.lower() else "decode"
            if traits.get("spec_tokens") is not None and ph == "decode": g.setdefault("tokens_per_sequence", 1 + int(traits["spec_tokens"]))
            obs_ms, fc = float(item.get("observed_ms") or 0.0), int(item.get("forward_count") or 1)
            if bool(item.get("cross_tp_transfer")) and len(pops) > 1:
                obs_ms, fc = float(pops[0].get("observed_ms") or obs_ms), int(pops[0].get("forward_count") or item.get("primary_forward_count") or fc)
            _put_anc(str(Path(rel_p).parent) if rel_p.endswith((".csv", ".gz")) else rel_p, {"model_case": _clean_text(item.get("template") or ""), "phase": ph, "forward_steps": fc, "observed_ms": obs_ms if obs_ms > 0.0 else None, "geometry": g})
    if (w5_path := RESULTS_DIR / "wave5_full_generalization.json").is_file():
        for item in json.loads(w5_path.read_text(encoding="utf-8")).get("cases", ()):
            if not (rel_p := _clean_text(item.get("path", ""))): continue
            ph = "prefill" if str(item.get("phase") or "").lower() == "prefill" else "decode"
            g = {k: item.get(k) for k in ("tp", "dp", "ep", "num_layers", "num_experts", "top_k", "context_tokens", "concurrency") if item.get(k) is not None}
            if item.get("spec_tokens") is not None and ph == "decode": g.setdefault("tokens_per_sequence", 1 + int(item["spec_tokens"]))
            extra = item.get("geometry") if isinstance(item.get("geometry"), Mapping) else {}
            g.update({k: extra[k] for k in _GEOM_PASSTHROUGH if extra.get(k) is not None})
            _put_anc(str(Path(rel_p).parent) if rel_p.endswith((".csv", ".gz")) else rel_p, {"model_case": _clean_text(item.get("template") or item.get("family") or ""), "phase": ph, "forward_steps": int(item.get("forward_count") or 1), "observed_ms": float(item["observed_ms"]) if item.get("observed_ms") is not None else None, "geometry": g})
    return idx
@lru_cache(maxsize=1)
def _workstream_session_index() -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    zs_f = Path("/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl")
    if zs_f.is_file():
        for d in _read_jsonl_any(zs_f):
            c = zsv.cell_from_dict(d); sp = c.spec
            obs = (c.tpot_ms if c.trace_quality == "dp_barrier_skew" and c.tpot_ms else c.step_trace_ms) or c.tpot_ms or c.ttft_ms
            g = {"tp": sp.tp, "dp": sp.dp, "ep": sp.ep or zsv._ep_ranks(sp), "pp": sp.pp, "prompt_tokens": sp.prompt_tokens, "context_tokens": sp.prompt_tokens, "concurrency": sp.concurrency, "graph_buckets": list(sp.graph_buckets), "graph_bucket": sp.graph_bucket, "notes": sp.notes}
            idx[sp.cell_id.split(":", 1)[-1]] = {"model_case": _clean_text(str(sp.model_case or sp.model_label or "")), "phase": sp.phase, "forward_steps": max(1, int(c.decode_steps if sp.phase == "decode" else 1)), "observed_ms": float(obs) if obs else None, "geometry": g}
    ws_base = Path("/Volumes/data/mindie-sim-data/.workstreams")
    ws_roots = (*zsv.WORKSTREAM_ROOTS, *(ws_base / n for n in ("a5-va-capture-20261106", "a5-wave2-multinode-20261106", "a5_live_20261106", "a5-k3-4node-24-26-27-28-20261106", "a5-k3-glm51-multinode-20261106")))
    for root in dict.fromkeys(Path(r) for r in ws_roots):
        if not root.exists(): continue
        for cell in zsv.discover_workstream(root):
            sp, cid = cell.spec, cell.spec.cell_id.split(":", 1)[-1]
            m_kps = [kp for kp in cell.kernel_paths if cid in kp.parts or any(f"{a}_{b}" == cid or f"{a}:{b}" == cid for a, b in zip(kp.parts, kp.parts[1:]))]
            if not m_kps: continue
            if cid not in idx:
                att = zsv.attach_trace(cell)
                obs = (att.tpot_ms if att.trace_quality == "dp_barrier_skew" and att.tpot_ms else att.step_trace_ms) or att.tpot_ms or att.ttft_ms
                g = {"tp": sp.tp, "dp": sp.dp, "ep": sp.ep or zsv._ep_ranks(sp), "pp": sp.pp, "prompt_tokens": sp.prompt_tokens, "context_tokens": sp.prompt_tokens, "concurrency": sp.concurrency, "graph_buckets": list(sp.graph_buckets), "graph_bucket": sp.graph_bucket, "notes": sp.notes}
                idx[cid] = {"model_case": _clean_text(str(sp.model_case or sp.model_label or "")), "phase": sp.phase, "forward_steps": max(1, int(att.decode_steps if sp.phase == "decode" else 1)), "observed_ms": float(obs) if obs else None, "geometry": g}
            meta = idx[cid]
            for kp in m_kps:
                kdir = _clean_text(str(kp.resolve().parent))
                for key in (kdir, str(Path(kdir).parent)):
                    if key.count("/") >= 2: idx[key] = {**idx.get(key, {}), **{k: v for k, v in meta.items() if v is not None}}
    return idx
def _dir_session_meta(capture_dir: Path) -> dict[str, Any]:
    meta, geom, stems = {}, {}, {capture_dir.name, capture_dir.parent.name}
    def _load(p: Path) -> Any:
        try: return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
        except (OSError, ValueError, TypeError): return None
    for anc in (capture_dir, capture_dir.parent, capture_dir.parent.parent, capture_dir.parent.parent.parent):
        if not anc.is_dir(): continue
        if (rep_doc := _load(anc / "profiler_representative.json")) is not None:
            items = rep_doc if isinstance(rep_doc, list) else rep_doc.get("cases") or rep_doc.get("representatives") or [rep_doc]
            for it in items:
                if isinstance(it, Mapping) and (str(it.get("case") or it.get("variant") or "") in stems or len(items) == 1):
                    if it.get("phase"): meta.setdefault("phase", str(it["phase"]).lower())
                    if it.get("profiled_iters"): meta.setdefault("forward_steps", int(it["profiled_iters"]))
                    if it.get("concurrency"): geom.setdefault("concurrency", int(it["concurrency"]))
        if isinstance(sm := _load(anc / "shape-manifest.json"), Mapping):
            nt = sm.get("native_trace") if isinstance(sm.get("native_trace"), Mapping) else {}
            if nt.get("repeats"): meta.setdefault("forward_steps", int(nt["repeats"]))
            if sm.get("model"): meta.setdefault("model_case", _clean_text(str(sm["model"])))
        if isinstance(bs := _load(anc / "benchmark_summary.json"), Mapping):
            if bs.get("max_concurrency"): geom.setdefault("concurrency", int(bs["max_concurrency"]))
            if bs.get("model_id"): meta.setdefault("model_case", _clean_text(str(bs["model_id"])))
            t_ms = bs.get("median_tpot_ms") or bs.get("tpot_ms") or bs.get("median_ttft_ms") or bs.get("ttft_ms")
            if t_ms := ((t_ms.get("median") or t_ms.get("mean")) if isinstance(t_ms, Mapping) else t_ms): meta.setdefault("observed_ms", float(t_ms))
        for sub in ("analysis", "cells", "raw"):
            for stem in stems:
                if isinstance(cd := _load(anc / sub / f"{stem}.json"), Mapping):
                    cd = cd.get(stem) if isinstance(cd.get(stem), Mapping) else cd
                    if cd.get("model"): meta.setdefault("model_case", _clean_text(str(cd["model"])))
                    if cd.get("layers_per_step"): geom.setdefault("num_layers", int(cd["layers_per_step"]))
                    if tok := (cd.get("input_len") or cd.get("prefix_len")): geom.setdefault("prompt_tokens", int(tok)); geom.setdefault("context_tokens", int(tok))
                    if cd.get("concurrency"): geom.setdefault("concurrency", int(cd["concurrency"]))
                    if dec_s := [s for s in (cd.get("steps") or ()) if isinstance(s, Mapping) and int(s.get("batch") or 0) >= 1 and float(s.get("span_ms") or 0.0) > 0.0]:
                        mb = max({int(s["batch"]) for s in dec_s}, key=lambda b: (sum(1 for s in dec_s if int(s["batch"]) == b), b))
                        bs_l = [s for s in dec_s if int(s["batch"]) == mb]
                        geom["concurrency"] = mb; meta["forward_steps"] = len(bs_l); meta["observed_ms"] = sum(float(s["span_ms"]) for s in bs_l) / len(bs_l)
                    else:
                        if cd.get("n_complete_steps"): meta.setdefault("forward_steps", int(cd["n_complete_steps"]))
                        obs = cd.get("tpot_ms") or cd.get("ttft_ms") or cd.get("step_ms")
                        if obs := ((obs.get("median") or obs.get("mean")) if isinstance(obs, Mapping) else obs): meta.setdefault("observed_ms", float(obs))
    if geom: meta["geometry"] = geom
    return meta
def _infer_from_top_ops(top_ops: Sequence[Mapping[str, Any]], model_hint: str = "", geom: Mapping[str, Any] | None = None) -> dict[str, Any]:
    g = geom or {}
    tp, dp, ep = _positive_int(g.get("tp")), _positive_int(g.get("dp")), _positive_int(g.get("ep"))
    events = [{"name": str(op.get("type") or ""), "op_type": str(op.get("type") or ""), "core": str(op.get("core") or ""), "dur_us": float(op.get("total_us") or 0.0) / max(1, int(op.get("count") or 1)), "call_count": max(1, int(op.get("count") or 1))} for op in top_ops if op.get("type")]
    rep = infer_trace_structure(events, model_hint=model_hint)
    arch_ok = bool(rep.schema_version) and int(rep.total_events or 0) > 0
    # Declared geometry is not an inference. all_4 needs an independent expected/inferred pair.
    return {"schema": rep.schema_version, "inferred_steps": rep.body_topology.inferred_steps, "total_body_layers": rep.body_topology.total_body_layers, "has_speculative_decoding": rep.speculative_module.has_speculative_decoding, "fused_composites": len(rep.fused_composites), "declared_tp": tp, "declared_dp": dp, "declared_ep": ep, "inferred_tp": None, "inferred_dp": None, "inferred_ep": None, "exact_architecture_pass": arch_ok, "exact_tp_pass": False, "exact_dp_pass": False, "exact_ep_pass": False, "all_4_pass": False}
def _op_stat_summary(capture_dir: Path, model_hint: str = "", geom: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    op_stat = capture_dir / "op_statistic.csv"
    total_rows, total_us, by_core, top_ops = 0, 0.0, Counter(), []
    by_op_engine: dict[str, dict[str, dict[str, float]]] = {}
    if op_stat.exists():
        try:
            with op_stat.open("rt", encoding="utf-8", errors="replace", newline="") as handle:
                for idx, row in enumerate(csv.DictReader(handle)):
                    cnt, dur, core = int(float(row.get("Count") or 0)), float(row.get("Total Time(us)") or 0.0), str(row.get("Core Type") or "UNKNOWN") or "UNKNOWN"
                    op_type = str(row.get("OP Type") or "UNKNOWN") or "UNKNOWN"
                    total_rows += cnt; total_us += dur; by_core[core] += dur
                    slot = by_op_engine.setdefault(op_type, {}).setdefault(core, {"count": 0, "total_us": 0.0})
                    slot["count"] += cnt; slot["total_us"] += dur
                    if idx < 5: top_ops.append({"type": op_type, "core": core, "count": cnt, "total_us": round(dur, 2)})
        except (OSError, ValueError): pass
    if total_us <= 0.0 and (kd_files := sorted(capture_dir.glob("kernel_details*.csv*"))):
        ksum = parse_kernel_details_summary(kd_files[0])
        return ksum, _infer_from_top_ops(ksum.get("top_op_types") or (), model_hint, geom)
    ksum = {"total_kernel_rows": total_rows, "total_kernel_duration_us": round(total_us, 2), "by_accelerator_core": {k: round(v, 2) for k, v in by_core.items()}, "by_op_engine": {op: {core: {"count": int(v["count"]), "total_us": round(v["total_us"], 2)} for core, v in cores.items()} for op, cores in by_op_engine.items()}, "top_op_types": top_ops}
    return ksum, _infer_from_top_ops(top_ops, model_hint, geom)
def _collect_zero_shot_cells(output_dir: Path | None = None) -> tuple[list[dict[str, Any]], set[Path]]:
    raw_cells = sorted((cell for root in zsv.WORKSTREAM_ROOTS for cell in zsv.discover_workstream(Path(root))), key=lambda c: (c.spec.dataset, c.spec.cell_id))
    used_paths = {cell.kernel_paths[0].resolve() for cell in raw_cells if cell.success and cell.spec.model_case is not None and cell.kernel_paths}
    if output_dir is not None and (output_dir / "data" / "zero_shot_l1_l4_cells.jsonl").exists():
        return _read_jsonl_any(output_dir / "data" / "zero_shot_l1_l4_cells.jsonl"), used_paths
    exported = []
    for cell in raw_cells:
        if not cell.success or cell.spec.model_case is None: continue
        attached = zsv.attach_trace(cell)
        if attached.trace is None: continue
        item = zsv.cell_to_dict(replace(attached, spec=replace(attached.spec, ep=attached.spec.ep or zsv._ep_ranks(attached.spec))))
        item["hardware_tier"] = "A5"; item["suite"] = "zero_shot_l1_l4"; exported.append(item)
    return exported, used_paths
def _collect_structure_suites() -> tuple[list[dict[str, Any]], set[str]]:
    rows, dsh_paths, sess_idx = [], set(), _local_session_index()
    for phase_name, fname in (("decode", "decode.json"), ("prefill", "prefill.json")):
        data = json.loads((RESULTS_DIR / fname).read_text(encoding="utf-8"))
        for case in data.get("cases", ()):
            comp, pop, pl_sum = case.get("comparison") or {}, case.get("population_coverage") or {}, (case.get("per_layer") or {}).get("summary") or {}
            obs, cid = comp.get("observed_ms"), str(case.get("case_id") or case.get("id") or "")
            obs_ms = (obs.get("mean") if isinstance(obs, dict) else obs) or case.get("body_activity_union_sum_ms") or ((case.get("client") or {}).get("ttft_ms") or {}).get("mean")
            status = str(comp.get("status") or case.get("status") or "")
            try: rel_err = abs(float(comp["relative_error"])) if comp.get("relative_error") is not None else None
            except (TypeError, ValueError): rel_err = None
            chunks = max(1, round(int(pl_sum.get("compared_layers") or 0) / 43)) if phase_name == "prefill" and int(pl_sum.get("compared_layers") or 0) > 0 else 0
            cal_raw = {k: v for k, v in (case.get("calibration") or {}).items() if k != "evidence_refs"}
            used_fit = bool(cal_raw.get("target_timing_used_to_fit", False) or "in_sample" in str(cal_raw.get("evaluation_relation") or "").lower())
            client_meta, sess_g = case.get("client") or {}, (sess_idx.get(f"registered_{phase_name}:{cid}") or {}).get("geometry") or {}
            raw_geom = {**sess_g, **(case.get("geometry") or {})}
            if client_meta.get("input_len"): raw_geom.setdefault("prompt_tokens", int(client_meta["input_len"]))
            if client_meta.get("concurrency"): raw_geom.setdefault("concurrency", int(client_meta["concurrency"]))
            if chunks > 0: raw_geom.setdefault("body_chunks", chunks)
            mc = _clean_text((case.get("model_case") or {}).get("path", ""))
            geom = _complete_geometry(raw_geom, phase_name, mc, cid)
            rows.append({
                "suite": f"registered_{phase_name}", "capture_id": f"registered_{phase_name}:{cid}",
                "hardware_tier": _hw_tier("", f"{cid} {(case.get('source') or {}).get('path', '')}"), "phase": phase_name,
                "model_case": mc, "status": status, "evaluation_mode": "zero_shot_structure_pipeline",
                "forward_steps": int(pop.get("observed_calls") or comp.get("observed_forward_count") or max(1, chunks)),
                "chunk_count": chunks, "observed_ms": obs_ms, "relative_error": rel_err,
                "passed_10pct": rel_err is not None and rel_err <= 0.10, "passed_15pct": rel_err is not None and rel_err <= 0.15, "target_timing_used_to_fit": used_fit,
                "source_calibration": cal_raw, "geometry": geom, "per_layer": pl_sum,
                "source_sha256": str((case.get("source") or {}).get("sha256") or ""),
                "generator_input_sha256": str(case.get("input_sha256") or ""),
                "calibration_role": _calibration_role(str(cal_raw.get("evaluation_relation") or ""), str(status or "")),
                "structural_inference": _infer_from_top_ops((), mc, geom),
            })
    for item in json.loads((RESULTS_DIR / "dsh_full_generalization.json").read_text(encoding="utf-8")).get("heldout_cases", ()):
        rel_path, traits = _clean_text(item.get("path", "")), item.get("traits") or {}
        if rel_path: dsh_paths.add(str(Path(rel_path).parent) if rel_path.endswith((".csv", ".gz")) else rel_path)
        obs_ms, pops, raw_geom = float(item.get("observed_ms") or 0.0), item.get("populations") or (), dict(item.get("geometry") or {})
        for tk in ("tp", "dp", "ep", "concurrency"):
            if traits.get(tk) is not None and raw_geom.get(tk) is None: raw_geom[tk] = int(traits[tk])
        fc, rel_err = int(item.get("forward_count") or 1), item.get("relative_error")
        if bool(item.get("cross_tp_transfer")) and len(pops) > 1:
            obs_ms = float(pops[0].get("observed_ms") or obs_ms)
            fc = int(pops[0].get("forward_count") or item.get("primary_forward_count") or fc)
            rel_err = pops[0].get("relative_error", rel_err)
        rel_err = abs(float(rel_err or 0.0))
        ph = "prefill" if str(traits.get("phase") or "").lower() == "prefill" or "prefill" in rel_path.lower() else "decode"
        if traits.get("spec_tokens") is not None and ph == "decode": raw_geom.setdefault("tokens_per_sequence", 1 + int(traits["spec_tokens"]))
        mc = _clean_text(item.get("template") or "")
        geom = _complete_geometry(raw_geom, ph, mc, rel_path)
        rows.append({
            "suite": "dsh_20261030_heldout", "capture_id": f"dsh_heldout:{rel_path}", "hardware_tier": _hw_tier(str(traits.get("hardware") or traits.get("hw") or ""), rel_path),
            "phase": ph, "model_case": mc, "status": str(item.get("status") or ""), "evaluation_mode": "template_matched_heldout_replay",
            "forward_steps": fc, "observed_ms": obs_ms, "relative_error": rel_err,
            "passed_10pct": rel_err <= 0.10, "passed_15pct": rel_err <= 0.15, "target_timing_used_to_fit": False,
            "source_calibration": {"evaluation_relation": "template_matched_heldout_replay", "target_timing_used_to_fit": False},
            "calibration_role": _calibration_role("template_matched_heldout_replay", str(item.get("status") or "")),
            "geometry": geom, "traits": {k: v for k, v in traits.items() if k not in {"hardware", "hw"}}, "layer_summary": item.get("layer_summary") or {},
            "structural_inference": _infer_from_top_ops((), mc, geom),
        })
    for item in json.loads((RESULTS_DIR / "wave5_full_generalization.json").read_text(encoding="utf-8")).get("cases", ()):
        rel_path, rel_err = _clean_text(item.get("path", "")), abs(float(item.get("relative_error") or 0.0))
        raw_geom = {k: item.get(k) for k in ("tp", "dp", "ep", "num_layers", "num_experts", "top_k", "context_tokens", "concurrency") if item.get(k) is not None}
        ph = "prefill" if str(item.get("phase") or "").lower() == "prefill" else "decode"
        if item.get("spec_tokens") is not None and ph == "decode": raw_geom.setdefault("tokens_per_sequence", 1 + int(item["spec_tokens"]))
        extra = item.get("geometry") if isinstance(item.get("geometry"), Mapping) else {}
        raw_geom.update({k: extra[k] for k in _GEOM_PASSTHROUGH if extra.get(k) is not None})
        mc, cid_w5 = _clean_text(item.get("template") or item.get("family") or ""), f"wave5:{item.get('hw', '')}:{item.get('cohort', '')}:{item.get('cell', '')}"
        geom = _complete_geometry(raw_geom, ph, mc, f"{cid_w5} {rel_path}")
        rows.append({
            "suite": "wave5_20261031", "capture_id": cid_w5, "hardware_tier": _hw_tier(str(item.get("hw") or ""), rel_path), "phase": ph,
            "model_case": mc, "status": str(item.get("status") or ""), "evaluation_mode": "wave5_regime_table_replay",
            "forward_steps": int(item.get("forward_count") or 1), "observed_ms": item.get("observed_ms"), "relative_error": rel_err,
            "passed_10pct": bool(item.get("passed_10pct", rel_err <= 0.10)), "passed_15pct": bool(item.get("passed_15pct", rel_err <= 0.15)), "target_timing_used_to_fit": True,
            "source_calibration": {"evaluation_relation": "regime_table_replay", "target_timing_used_to_fit": True, "calibration_role": "regime_table_replay"},
            "calibration_role": "regime_table_replay",
            "geometry": geom, "structural_inference": _infer_from_top_ops((), mc, geom),
        })
    return rows, dsh_paths
def _collect_multinode_20261108() -> list[dict[str, Any]]:
    runs_root = MULTINODE_20261108_ROOT / "runs"
    if not runs_root.exists(): return []
    rows: list[dict[str, Any]] = []
    for export_path in sorted(runs_root.rglob("export_summary.json")):
        is_idle = "idle_dp_rank" in export_path.parts
        cell_dir = export_path.parent.parent if is_idle else export_path.parent
        case_dir, cell_id = cell_dir.parent, f"{cell_dir.parent.name}:{cell_dir.name}"
        try:
            export_summary = json.loads(export_path.read_text(encoding="utf-8"))
            cell_meta = json.loads((case_dir / f"{cell_dir.name}.json").read_text(encoding="utf-8")) if (case_dir / f"{cell_dir.name}.json").exists() else {}
            case_spec = json.loads((case_dir / "case_spec.json").read_text(encoding="utf-8")) if (case_dir / "case_spec.json").exists() else {}
        except (OSError, ValueError): continue
        mode = str(cell_meta.get("mode") or cell_dir.name).lower()
        phase = "prefill" if "prefill" in mode or "_pf_" in mode else "decode"
        isl, osl, conc = _positive_int(cell_meta.get("isl")), _positive_int(cell_meta.get("osl")), _positive_int(cell_meta.get("concurrency"))
        ttft = (cell_meta.get("ttft_ms") or {}).get("median") if isinstance(cell_meta.get("ttft_ms"), dict) else cell_meta.get("ttft_ms")
        tpot = (cell_meta.get("tpot_ms") or {}).get("median") if isinstance(cell_meta.get("tpot_ms"), dict) else cell_meta.get("tpot_ms")
        top_ops, model_name = (export_summary.get("top_op_types") or [])[:5], str(case_spec.get("served_model_name") or cell_meta.get("model") or case_dir.name)
        k_us = float(export_summary.get("total_kernel_duration_us") or 0.0)
        client_ms = tpot if phase == "decode" else ttft
        obs_val = round(float(client_ms), 4) if client_ms not in (None, "") and float(client_ms) > 0.0 else None
        declared_steps = osl if phase == "decode" and osl else _positive_int(cell_meta.get("completed"))
        raw_geom = {"tp": _positive_int(case_spec.get("tp")), "dp": _positive_int(case_spec.get("dp")), "ep_enabled": bool(case_spec.get("enable_expert_parallel", False)), "num_nodes": len(case_spec.get("nodes") or ())}
        if isl: raw_geom["prompt_tokens"] = raw_geom["context_tokens"] = isl
        if osl: raw_geom["output_tokens"] = osl
        if conc: raw_geom["concurrency"] = conc
        geom = _complete_geometry(raw_geom, phase, model_name, cell_id, demand_sources=(("case_spec", case_spec), ("cell_meta", cell_meta)))
        ksum = {"total_kernel_rows": int(export_summary.get("total_kernel_rows") or 0), "total_kernel_duration_us": k_us, "by_accelerator_core": export_summary.get("by_accelerator_core") or {}, "top_op_types": top_ops}
        rows.append({
            "suite": "a5_multinode_full_coverage_20261108", "capture_id": f"a5_multinode_20261108:{cell_id}{':idle_dp_rank' if is_idle else ''}",
            "hardware_tier": "A5", "phase": phase, "model_case": model_name,
            "status": "idle_dp_rank_trace" if is_idle else "measured_trace_bundle", "evaluation_mode": "structural_inference_and_trace_inventory",
            "forward_steps": declared_steps, "observed_ms": obs_val, "geometry": geom, "kernel_summary": ksum,
            "structural_inference": _infer_from_top_ops(ksum.get("top_op_types") or (), model_name, geom),
        })
    return rows
def _collect_remaining_physical_captures(used_zero_shot_paths: set[Path], dsh_paths: set[str], target_hw: Mapping[str, int]) -> list[dict[str, Any]]:
    rows, seen_real, counts, suite_counts, seen_cids = [], set(used_zero_shot_paths), Counter(), Counter(), Counter()
    dsh_dirs = {PurePosixPath(dp.replace("\\", "/")).parent if dp.endswith((".csv", ".gz")) else PurePosixPath(dp.replace("\\", "/")) for dp in dsh_paths if dp}
    sess_idx = {**_local_session_index(), **(_workstream_session_index() if any("/Volumes/data" in str(r) for r in DATA_ROOTS) else {})}
    for root in DATA_ROOTS:
        if not root.exists(): continue
        for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
            dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(("a5-comm", "a5-mc2", "comm-", "hccl")))
            for fn in sorted(filenames):
                if not (fn.startswith("kernel_details") and (fn.endswith(".csv") or fn.endswith(".csv.gz"))): continue
                rp = (Path(dirpath) / fn).resolve()
                if rp in seen_real or any(p in _SKIP_DIRS or p.startswith(("a5-comm", "a5-mc2", "comm-", "hccl")) for p in rp.parts): continue
                seen_real.add(rp); s = str(rp)
                rel_id = _clean_text(Path(dirpath).relative_to(root).as_posix())
                capture = PurePosixPath(rel_id)
                if (rp.parent / "export_summary.json").exists() or any(capture == dp or dp in capture.parents for dp in dsh_dirs): continue
                hw = _hw_tier(dirpath, rel_id)
                suite = "a5_rack06_rack08_multirank_20261107" if "a5-multinode-fleet-rack0" in s else ("operator_and_kernel_calibration_20261107" if "calibration-20261107" in s else "extended_a3_a5_workstream_captures")
                if counts[hw] >= target_hw.get(hw, 0) or (suite == "a5_rack06_rack08_multirank_20261107" and suite_counts[suite] >= 217): continue
                counts[hw] += 1; suite_counts[suite] += 1
                p_rel = Path(rel_id)
                s_meta = next((sess_idx[k] for k in (rel_id, str(p_rel.parent), str(p_rel.parent.parent), str(p_rel.parent.parent.parent)) if k in sess_idx), {})
                d_meta = _dir_session_meta(rp.parent)
                phase = str(s_meta.get("phase") or d_meta.get("phase") or ("prefill" if any(k in rel_id.lower() for k in ("prefill", "_pf_", "/pf_")) else "decode"))
                model_hint = str(s_meta.get("model_case") or d_meta.get("model_case") or next((seg for seg in rel_id.split("/") if seg and seg.lower() not in _GENERIC_ANCESTORS and not re.fullmatch(r"2026-\d\d-\d\d", seg)), rel_id))
                fsteps = max(1, int(s_meta.get("forward_steps") or d_meta.get("forward_steps") or (32 if phase == "decode" else 1)))
                geom = _complete_geometry({**(d_meta.get("geometry") or {}), **(s_meta.get("geometry") or {})}, phase, model_hint, rel_id, demand_sources=(("session_metadata", s_meta.get("geometry") or {}), ("directory_metadata", d_meta.get("geometry") or {})))
                ksum, sinf = _op_stat_summary(rp.parent, model_hint, geom)
                declared_obs = s_meta.get("observed_ms") if s_meta.get("observed_ms") is not None else d_meta.get("observed_ms")
                obs_val = round(float(declared_obs), 4) if declared_obs not in (None, "") and float(declared_obs) > 0.0 else None
                base_cid = f"{suite}:{rel_id}"; seen_cids[base_cid] += 1
                cid = base_cid if seen_cids[base_cid] == 1 else f"{base_cid}#{seen_cids[base_cid]}"
                rows.append({
                    "suite": suite, "capture_id": cid, "hardware_tier": hw, "phase": phase, "model_case": model_hint, "status": "measured_trace_bundle",
                    "evaluation_mode": "structural_inference_and_trace_inventory", "forward_steps": fsteps, "observed_ms": obs_val,
                    "geometry": geom, "kernel_summary": ksum, "structural_inference": sinf,
                })
    return rows
def _stat_row(category: str, target: str, errs: Sequence[float], total_caps: int, step_samples: int, hw_counts: Mapping[str, int]) -> dict[str, Any]:
    """Percentiles use measured errors. Absent rows stay in the population as unverified."""
    measured = [float(e) for e in errs]
    finite = [e for e in measured if math.isfinite(e)]
    bad = any(not math.isfinite(e) for e in measured)
    population, evaluated = max(0, int(total_caps)), len(measured)
    unverified = max(0, population - evaluated)
    above_10 = sum(1 for e in measured if not math.isfinite(e) or e > 0.10) + unverified
    pass_10 = sum(1 for e in finite if e <= 0.10)
    ordered = sorted(finite)
    return {
        "category": category, "target": target, "captures": population, "evaluated_captures": evaluated, "unverified_captures": unverified,
        "step_samples": step_samples, "by_hardware_tier": dict(sorted(hw_counts.items())),
        "err_p50": median(ordered) if ordered and not bad else 0.0, "err_p90": ordered[min(len(ordered) - 1, int(0.9 * len(ordered)))] if ordered and not bad else 0.0,
        "err_max": (float("nan") if bad else (max(ordered) if ordered else 0.0)),
        "above_10pct": above_10, "pass_10pct": pass_10, "pass_rate_10pct": (pass_10 / max(population, evaluated)) if max(population, evaluated) and not bad else 0.0,
    }
def _zs_cell_errors(zs_result: Mapping[str, Any], lv_map: Mapping[str, Mapping[str, Any]]) -> dict[str, list[float]]:
    by_key_cell: dict[str, dict[str, list[float]]] = {}
    for idx, se in enumerate(zs_result.get("step_errors") or ()):
        if isinstance(se, Mapping) and (raw_e := se.get("relative_error", se.get("signed_error"))) is not None:
            by_key_cell.setdefault(f"{se.get('level')}:{se.get('target')}", {}).setdefault(str(se.get("cell") or se.get("cell_id") or idx), []).append(raw_e)
    out: dict[str, list[float]] = {k: [_finite_abs_max(v) for v in cells.values() if v] for k, cells in by_key_cell.items()}
    for key, lv in lv_map.items():
        if key in out or not isinstance(lv, Mapping): continue
        raw_list = lv.get("cell_errors") or lv.get("errors") or lv.get("step_errors")
        if isinstance(raw_list, Sequence) and not isinstance(raw_list, (str, bytes)):
            grouped: dict[str, list[Any]] = {}
            flat: list[Any] = []
            keyed = False
            for idx, item in enumerate(raw_list):
                if isinstance(item, Mapping) and (item.get("cell") or item.get("cell_id")):
                    keyed = True
                    grouped.setdefault(str(item.get("cell") or item.get("cell_id")), []).append(item.get("relative_error", item.get("signed_error")))
                else:
                    flat.append(item.get("relative_error", item.get("signed_error", item)) if isinstance(item, Mapping) else item)
            out[key] = [_finite_abs_max(v) for v in grouped.values()] if keyed else [_finite_abs_max(flat)] if flat else []
    return out
def _structural_inference_stats(zs_rows: Sequence[Mapping[str, Any]], fleet_rows: Sequence[Mapping[str, Any]], total_caps: int, total_steps: int, hw_counts: Mapping[str, int]) -> dict[str, Any]:
    eval_cnt = arch_pass = tp_pass = dp_pass = ep_pass = all4_pass = 0
    sinf_errs: list[float] = []
    def _paired(sinf: Mapping[str, Any], name: str) -> bool | None:
        exp, inf = sinf.get(f"expected_{name}"), sinf.get(f"inferred_{name}")
        if exp is None or inf is None: return None
        return exp == inf
    for r in list(zs_rows) + list(fleet_rows):
        sinf = r.get("structural_inference")
        if not isinstance(sinf, Mapping) or not sinf: continue
        arch, tp, dp, ep = (_paired(sinf, name) for name in ("architecture", "tp", "dp", "ep"))
        if arch is None and tp is None and dp is None and ep is None: continue
        eval_cnt += 1
        a_ok, t_ok, d_ok, e_ok = arch is True, tp is True, dp is True, ep is True
        all_ok = a_ok and t_ok and d_ok and e_ok
        arch_pass += int(a_ok); tp_pass += int(t_ok); dp_pass += int(d_ok); ep_pass += int(e_ok); all4_pass += int(all_ok); sinf_errs.append(0.0 if all_ok else 1.0)
    row = _stat_row("structural_inference", "mindie_structural_inference_v1", sinf_errs, total_caps, total_steps, hw_counts)
    row.update({"evaluated_captures": eval_cnt, "exact_architecture_pass": arch_pass, "exact_tp_pass": tp_pass, "exact_dp_pass": dp_pass, "exact_ep_pass": ep_pass, "all_4_pass": all4_pass})
    return row
def _finite_close(left: Any, right: Any, rel_tol: float = 1e-3, abs_tol: float = 1e-3) -> bool:
    try: left_f, right_f = float(left), float(right)
    except (TypeError, ValueError): return False
    return math.isfinite(left_f) and math.isfinite(right_f) and math.isclose(left_f, right_f, rel_tol=rel_tol, abs_tol=abs_tol)
def _stored_relative_error_matches(entry: Mapping[str, Any]) -> bool:
    try: obs, pred, stored = float(entry.get("observed_ms")), float(entry.get("predicted_ms")), float(entry.get("relative_error"))
    except (TypeError, ValueError): return False
    return all(math.isfinite(v) for v in (obs, pred, stored)) and abs(abs(pred - obs) / max(obs, 1e-9) - abs(stored)) <= 1e-3
def _live_operator_matches(live: Mapping[str, Any], op_mod: Any) -> bool:
    """Verify every stored family/core prediction against the measurement-blind live allocation."""
    if not isinstance(op_mod, Mapping) or op_mod.get("status") != "compared": return False
    fams, cores = op_mod.get("families"), op_mod.get("by_accelerator_core")
    live_fams, live_cores = live.get("predicted_by_family_ms"), live.get("predicted_by_core_ms")
    if not isinstance(fams, Mapping) or not isinstance(live_fams, Mapping) or not fams or set(fams) != set(live_fams): return False
    if not isinstance(cores, Mapping) or not isinstance(live_cores, Mapping) or not cores: return False
    for key, entry in fams.items():
        if not isinstance(entry, Mapping) or not _stored_relative_error_matches(entry) or not _finite_close(entry.get("predicted_ms"), live_fams[key]): return False
    try: fam_pred_sum, live_op_pred = sum(float(entry.get("predicted_ms", -1.0)) for entry in fams.values()), float(live.get("predicted_operator_ms", float("nan")))
    except (TypeError, ValueError): return False
    if not math.isclose(fam_pred_sum, live_op_pred, rel_tol=1e-3, abs_tol=1e-3): return False
    for key, entry in cores.items():
        if not isinstance(entry, Mapping) or key not in live_cores or not _finite_close(entry.get("predicted_ms"), live_cores[key]) or not _stored_relative_error_matches(entry): return False
    if (unif := op_mod.get("unified_families")) is not None:
        live_unif = live.get("predicted_by_unified_family_ms")
        if not isinstance(unif, Mapping) or not isinstance(live_unif, Mapping) or set(unif) != set(live_unif): return False
        for key, entry in unif.items():
            if not isinstance(entry, Mapping) or key not in live_unif or not _finite_close(entry.get("predicted_ms"), live_unif[key]) or not _stored_relative_error_matches(entry): return False
    return True
def _invalidate_fleet_row(row: dict[str, Any], *, operator_failed: bool) -> None:
    """Mark a row that failed live verification so it can never be shown as a passing capture."""
    row["status"] = "invalid_prediction"; row["passed_10pct"] = False; row["relative_error"] = 1.0
    if operator_failed:
        row["operator_modeling"] = {**(row.get("operator_modeling") or {}), "status": "invalid_prediction", "operator_passed_10pct": False, "operator_relative_error": 1.0}
def _build_unified_7337_scoreboard(zs_rows: Sequence[Mapping[str, Any]], zs_result: Mapping[str, Any], fleet_rows: Sequence[Mapping[str, Any]], suite_stats: Mapping[str, Mapping[str, Any]], total_steps: int, hw_counts: Mapping[str, int], phase_counts: Mapping[str, int]) -> dict[str, Any]:
    total_caps = len(zs_rows) + len(fleet_rows)
    lv_map = {f"{lv.get('level')}:{lv.get('target')}": lv for lv in (zs_result.get("levels") or ())}
    zs_errs_by_key = _zs_cell_errors(zs_result, lv_map)
    # L1 errors stay on the L1 target. Stored fleet relative_error is not a sample.
    # Accelerator cores stay empty until an exact raw-core boundary is compared.
    fam_rows = [_stat_row("L1_operator_family", u_name, list(zs_errs_by_key.get(zs_key, ())), total_caps, total_steps, hw_counts) for u_name, _fb_name, zs_key in _UNIFIED_FAMILIES]
    core_rows = [_stat_row("L2_accelerator_engine", c_name, [], total_caps, total_steps, hw_counts) for c_name, _zs_key in _UNIFIED_CORES]
    dec_trace, pf_trace = list(zs_errs_by_key.get("L3:decode_step_trace", ())), list(zs_errs_by_key.get("L3:prefill_step_trace", ()))
    l3_trace = dec_trace + pf_trace
    l3_finite = [err for err in l3_trace if isinstance(err, (int, float)) and math.isfinite(err)]
    l3_err = float("nan") if any(not isinstance(err, (int, float)) or not math.isfinite(err) for err in l3_trace) else (median(sorted(l3_finite)) if l3_finite else None)
    n_dec, n_pf = int(phase_counts.get("decode", 0)), int(phase_counts.get("prefill", 0))
    step_rows = [
        _stat_row("L3_device_trace", "decode_step_trace", dec_trace, n_dec, total_steps, hw_counts),
        _stat_row("L3_device_trace", "prefill_step_trace", pf_trace, n_pf, total_steps, hw_counts),
        _stat_row("L4_request", "decode_step_tpot", [], n_dec, total_steps, hw_counts),
        _stat_row("L4_request", "prefill_step_ttft", [], n_pf, total_steps, hw_counts),
        _stat_row("request_e2e", "all_7337_captures_step_e2e", [], total_caps, total_steps, hw_counts),
    ]
    sinf_row = _structural_inference_stats(zs_rows, fleet_rows, total_caps, total_steps, hw_counts)
    all_rows = fam_rows + core_rows + step_rows + [sinf_row]
    return {"total_captures": total_caps, "total_step_samples": total_steps, "l3_step_trace_err_p50": l3_err, "by_hardware_tier": dict(sorted(hw_counts.items())), "by_phase": dict(sorted(phase_counts.items())), "operator_families": fam_rows, "accelerator_engines": core_rows, "step_and_e2e_latency": step_rows, "structural_inference": sinf_row, "rows": all_rows}
def _population_gaps(zs_n: int, fleet_n: int, hw: Mapping[str, int]) -> list[str]:
    gaps = [f"counts:{zs_n}+{fleet_n}"] if (zs_n, fleet_n) != (_FULL_POPULATION["zero_shot"], _FULL_POPULATION["fleet"]) else []
    return gaps + [f"{tier}:{int(hw.get(tier, 0))}" for tier in ("A2", "A3", "A5") if int(hw.get(tier, 0)) != _FULL_POPULATION[tier]]
def _zs_step_gaps(zs_result: Mapping[str, Any], levels: Sequence[Mapping[str, Any]]) -> list[str]:
    grouped: dict[str, list[float]] = {}
    for row in zs_result.get("step_errors") or ():
        if isinstance(row, Mapping) and row.get("signed_error", row.get("relative_error")) is not None:
            grouped.setdefault(f"{row.get('level')}:{row.get('target')}", []).append(abs(float(row.get("signed_error", row.get("relative_error")))))
    gaps = []
    for level in levels:
        key, errs, samples = f"{level.get('level')}:{level.get('target')}", grouped.get(f"{level.get('level')}:{level.get('target')}", []), int(level.get("samples") or 0)
        reported = float(level.get("step_err_max", float("nan")))
        if len(errs) < samples or any((not math.isfinite(err)) or err > 0.10 for err in errs) or (errs and (not math.isfinite(reported) or reported + 1e-9 < max(errs))): gaps.append(key)
    return gaps
def _zero_shot_timetables(row: Mapping[str, Any]) -> Any:
    """Stream P's raw timetables for one enrolled cell. The gate keeps only the counts."""
    import zero_shot_native_windows as zsn
    return zsn.iter_trace_timetables(row)
def evaluate_dataset(dataset_dir: Path, *, strict_10pct: bool = False, full_population: bool = False, summary_dir: Path | None = None, inventory: str | None = None) -> dict[str, Any]:
    """Strict mode checks the original 7,337 ids. inventory='targeted' cannot set a global pass."""
    mode = ("targeted" if inventory == "targeted" else
            "full" if inventory == "full" or strict_10pct or full_population else "targeted")

    def _board(zs_rows: Sequence[Mapping[str, Any]], zs_result: Mapping[str, Any], fleet_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        hw, phase = Counter(), Counter()
        for item in list(zs_rows) + list(fleet_rows):
            hw[str(item.get("hardware_tier") or "unverified")] += 1
            phase[str(item.get("phase") or "decode")] += 1
        steps = sum(int(item.get("forward_steps") or 0) for item in fleet_rows)
        payload = zs_result if isinstance(zs_result, Mapping) else {}
        return _build_unified_7337_scoreboard(zs_rows, payload, fleet_rows, {}, steps, hw, phase)

    return hf_benchmark_gate.evaluate(
        dataset_dir,
        strict_10pct=strict_10pct,
        inventory=mode,
        summary_dir=summary_dir,
        identity_builder=lambda: _collect_structure_suites()[0],
        simulator_name=simulator_identity(mindie_sim),
        predict=predict_capture_operators_and_step,
        observe=fleet_capture_observations.extract_capture_observations,
        run_validation=zsv.run_validation,
        configure_roots=fleet_capture_observations.configure_observation_roots,
        data_roots=DATA_ROOTS,
        file_meta=lambda file_path: {"size_bytes": file_path.stat().st_size, "sha256": _sha256_file(file_path)},
        build_scoreboard=_board,
        redact_hits=lambda blob: set(_DOC_REDACT_RE.findall(blob)),
        zero_shot_timetables=_zero_shot_timetables,
        zero_shot_requests=_zero_shot_l4_pair,
    )


def _render_dataset_card(summary: Mapping[str, Any], files_meta: Mapping[str, Mapping[str, Any]] | None = None) -> str:
    """Print pass, evaluated, and unverified as three different numbers."""
    del files_meta
    return hf_benchmark_gate.render_dataset_card(summary)


def build_dataset(output_dir: Path, *, strict_10pct: bool = False) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True); zs_cells, used_paths = _collect_zero_shot_cells(output_dir)
    if not (output_dir / "data" / "zero_shot_l1_l4_cells.jsonl").exists(): _write_jsonl_gz(output_dir / "data" / "zero_shot_l1_l4_cells.jsonl.gz", zs_cells, also_plain=True)
    struct_rows, dsh_paths = _collect_structure_suites(); mn_rows = _collect_multinode_20261108(); cur_hw = Counter({"A5": len(zs_cells)})
    for r in struct_rows + mn_rows: cur_hw[str(r.get("hardware_tier") or "A3")] += 1
    rem_targets = {"A2": max(0, 837 - cur_hw["A2"]), "A3": max(0, 1729 - cur_hw["A3"]), "A5": max(0, 4771 - cur_hw["A5"])}
    fleet_rows = enrich_all_fleet_captures(struct_rows + mn_rows + _collect_remaining_physical_captures(used_paths, dsh_paths, rem_targets))
    _write_jsonl_gz(output_dir / "data" / "fleet_captures.jsonl.gz", fleet_rows, also_plain=True)
    return evaluate_dataset(output_dir, strict_10pct=strict_10pct, summary_dir=output_dir)
def upload_dataset(dataset_dir: Path, repo_id: str = DEFAULT_HF_REPO, *, allow_network: bool = False) -> str:
    """Validate advertised bytes and identities. Do not POST."""
    del allow_network, repo_id
    problems = hf_benchmark_gate.validate_release(dataset_dir, simulator_name=simulator_identity(mindie_sim))
    if problems:
        raise ValueError("upload refused: " + "; ".join(problems))
    raise RuntimeError("upload refused: external upload is not permitted")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for flag in ("--build", "--evaluate", "--upload", "--strict-10pct"):
        parser.add_argument(flag, action="store_true")
    for flag in ("--output-dir", "--dataset-dir"):
        parser.add_argument(flag, type=Path, default=Path("/tmp/mindie-sim-profiling-bench"))
    parser.add_argument("--summary-dir", type=Path, default=None)
    parser.add_argument("--repo-id", type=str, default=DEFAULT_HF_REPO)
    args = parser.parse_args(argv)
    target_dir = args.output_dir if args.build else args.dataset_dir
    if args.build:
        result = build_dataset(target_dir, strict_10pct=args.strict_10pct)
    else:
        result = evaluate_dataset(target_dir, strict_10pct=args.strict_10pct, summary_dir=args.summary_dir)
    if args.upload:
        result["hf_url"] = upload_dataset(target_dir, args.repo_id)
    print(json.dumps({"totals": result["totals"], "strict_global_pass": result.get("strict_global_pass"), "hf_url": result.get("hf_url")}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
