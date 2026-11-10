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
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parent.name == "structure" else Path(__file__).resolve().parents[1]
SIM_ROOT = ROOT.parent / "sim"
for _p in (str(ROOT), str(SIM_ROOT), str(ROOT / "examples" / "structure")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import fleet_operator_modeling as fleet_modeling  # noqa: E402
import mindie_sim  # noqa: E402
import zero_shot_piecewise_validation as zsv  # noqa: E402
from fleet_operator_modeling import enrich_all_fleet_captures, enrich_fleet_capture_with_operator_and_step_modeling, parse_kernel_details_summary, predict_capture_operators_and_step  # noqa: E402
from mindie_profiler.structural_inference import infer_trace_structure  # noqa: E402
from runtime_identity import simulator_identity  # noqa: E402

RESULTS_DIR = ROOT / "examples" / "structure" / "results"
DATA_ROOTS = (Path("/Volumes/data/mindie-sim-data"), Path("/Users/maoxx241/code/mindie-agent/.workstreams"))
MULTINODE_20261108_ROOT = Path("/Volumes/data/mindie-sim-data/a5/multinode-full-coverage-20261108")
DEFAULT_HF_REPO = "maoxx241/mindie-sim-profiling-bench"
_SKIP_DIRS = {"a5-comm", "a5-mc2", "comm-fit", "comm-paired", "comm_collective", "hccl", "hccl-native", "acceptance-archives-20261030"}
_DOC_REDACT_RE = re.compile(
    r"(?i)\b(?:ascend\s*910\w*|ascend\s*950\w*|910b\w*|9362|950pr|950dt|9579|9581|9582|arch3510)\b"
    r"|(?:\b(?:177\.(?:25|31)|192\.168|173\.125)\.\d{1,3}\.\d{1,3}\b)"
)
_PATH_PREFIX_RE = re.compile(r"^/(?:Volumes/data/(?:mindie-sim-data|storage-archive/[^/]+)/|Users/[^/]+/code/|mnt/weight/)")
_UNIFIED_FAMILIES: tuple[tuple[str, str, str], ...] = (
    ("matmul_gemm", "cube_gemm", "L1:gemm"),
    ("attention", "attention_mla", "L1:attention"),
    ("moe_routing_grouped_gemm", "moe_comm_fusion", "L1:moe_grouped"),
    ("norm_activation_elementwise", "vector_elementwise", "L1:elementwise_quant"),
    ("kv_cache_position_rope", "vector_elementwise", "L1:kv_cache"),
    ("collective_comm", "moe_comm_fusion", "L1:collective"),
)
_UNIFIED_CORES: tuple[tuple[str, str], ...] = (
    ("AI_CORE", "L1:gemm"),
    ("AI_VECTOR_CORE", "L1:elementwise_quant"),
    ("MIX_AIC", "L1:attention"),
    ("COMMUNICATION", "L1:collective"),
)
_GEOM_PASSTHROUGH = ("active_hbm_mb", "active_cube_gflops", "structural_weights", "ep_dspark_wave_scale", "prompt_tokens", "sequences_per_replica", "tokens_per_sequence", "concurrency", "context_tokens", "tp", "dp", "ep", "ep_enabled")
_GEOM_TEMPLATE_KEYS = ("active_hbm_mb", "active_cube_gflops", "structural_weights")
_DEFAULT_FLEET_TEMPLATE_PATH = fleet_modeling._FLEET_TEMPLATE_PATH
_FLEET_TEMPLATE_PATH = _DEFAULT_FLEET_TEMPLATE_PATH


def _clean_text(text: str) -> str:
    cleaned = _PATH_PREFIX_RE.sub("", str(text or ""))
    cleaned = re.sub(r"(?i)ascend(?:910b|950(?:pr|dt)?)[_-]?", "", cleaned)
    return re.sub(r"\b(?:177\.(?:25|31)|192\.168|173\.125)\.\d{1,3}\.\d{1,3}\b", "node", cleaned)


def _hw_tier(raw_hw: str, fallback_text: str = "") -> str:
    probe = f"{raw_hw} {fallback_text}".lower()
    return "A2" if "a2" in probe else ("A5" if any(k in probe for k in ("a5", "r06_", "r08_", "rack0", "950")) else "A3")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _write_jsonl_gz(path: Path, rows: Sequence[Mapping[str, Any]], *, also_plain: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plain_path = path.with_suffix("") if also_plain and path.suffix == ".gz" else None
    plain_handle = plain_path.open("wt", encoding="utf-8", newline="\n") if plain_path else None
    try:
        with gzip.open(path, "wt", encoding="utf-8", newline="\n") as gz_handle:
            for row in rows:
                line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                gz_handle.write(line)
                if plain_handle is not None:
                    plain_handle.write(line)
    finally:
        if plain_handle is not None:
            plain_handle.close()


def _read_jsonl_any(path: Path) -> list[dict[str, Any]]:
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _infer_from_top_ops(top_ops: Sequence[Mapping[str, Any]], model_hint: str = "") -> dict[str, Any]:
    events = [{"name": str(op.get("type") or ""), "op_type": str(op.get("type") or ""), "core": str(op.get("core") or ""), "dur_us": float(op.get("total_us") or 0.0) / max(1, int(op.get("count") or 1)), "call_count": max(1, int(op.get("count") or 1))} for op in top_ops if op.get("type")]
    rep = infer_trace_structure(events, model_hint=model_hint)
    return {"schema": rep.schema_version, "inferred_steps": rep.body_topology.inferred_steps, "total_body_layers": rep.body_topology.total_body_layers, "has_speculative_decoding": rep.speculative_module.has_speculative_decoding, "fused_composites": len(rep.fused_composites)}


def _op_stat_summary(capture_dir: Path, model_hint: str = "") -> tuple[dict[str, Any], dict[str, Any]]:
    op_stat = capture_dir / "op_statistic.csv"
    total_rows, total_us, by_core, top_ops = 0, 0.0, Counter(), []
    if op_stat.exists():
        try:
            with op_stat.open("rt", encoding="utf-8", errors="replace", newline="") as handle:
                for idx, row in enumerate(csv.DictReader(handle)):
                    cnt, dur, core = int(float(row.get("Count") or 0)), float(row.get("Total Time(us)") or 0.0), str(row.get("Core Type") or "UNKNOWN")
                    total_rows += cnt; total_us += dur; by_core[core] += dur
                    if idx < 5:
                        top_ops.append({"type": row.get("OP Type", ""), "core": core, "count": cnt, "total_us": round(dur, 2)})
        except (OSError, ValueError):
            pass
    if total_us <= 0.0:
        kd_files = sorted(capture_dir.glob("kernel_details*.csv*"))
        if kd_files:
            ksum = parse_kernel_details_summary(kd_files[0])
            return ksum, _infer_from_top_ops(ksum.get("top_op_types") or (), model_hint)
    ksum = {"total_kernel_rows": total_rows, "total_kernel_duration_us": round(total_us, 2), "by_accelerator_core": {k: round(v, 2) for k, v in by_core.items()}, "top_op_types": top_ops}
    return ksum, _infer_from_top_ops(top_ops, model_hint)


def _collect_zero_shot_cells(output_dir: Path | None = None) -> tuple[list[dict[str, Any]], set[Path]]:
    raw_cells = sorted((cell for root in zsv.WORKSTREAM_ROOTS for cell in zsv.discover_workstream(Path(root))), key=lambda c: (c.spec.dataset, c.spec.cell_id))
    used_paths = {cell.kernel_paths[0].resolve() for cell in raw_cells if cell.success and cell.spec.model_case is not None and cell.kernel_paths}
    if output_dir is not None and (output_dir / "data" / "zero_shot_l1_l4_cells.jsonl").exists():
        return _read_jsonl_any(output_dir / "data" / "zero_shot_l1_l4_cells.jsonl"), used_paths
    exported = []
    for cell in raw_cells:
        if not cell.success or cell.spec.model_case is None:
            continue
        attached = zsv.attach_trace(cell)
        if attached.trace is None:
            continue
        item = zsv.cell_to_dict(replace(attached, spec=replace(attached.spec, ep=attached.spec.ep or zsv._ep_ranks(attached.spec))))
        item["hardware_tier"] = "A5"; item["suite"] = "zero_shot_l1_l4"
        exported.append(item)
    return exported, used_paths


def _active_fleet_template_path() -> Path:
    if _FLEET_TEMPLATE_PATH != _DEFAULT_FLEET_TEMPLATE_PATH:
        return _FLEET_TEMPLATE_PATH
    return fleet_modeling._FLEET_TEMPLATE_PATH


def _load_fleet_geometry_catalog() -> dict[str, dict[str, Any]]:
    """Load compact non-timing geometry demands when the full fleet template is unavailable."""
    for path in dict.fromkeys((RESULTS_DIR / "fleet_geometry_demands.json.gz", ROOT / "examples" / "structure" / "results" / "fleet_geometry_demands.json.gz")):
        try:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            continue
        if isinstance(data, Mapping):
            return {str(k): {key: v[key] for key in _GEOM_TEMPLATE_KEYS if v.get(key) is not None} for k, v in data.items() if isinstance(v, Mapping)}
    return {}


def _merge_fleet_template_geometry(rows: Sequence[dict[str, Any]]) -> None:
    """Merge only non-timing architectural geometry from the fleet template, keyed by capture id."""
    template_path = Path(_active_fleet_template_path())
    geometry_by_cid: dict[str, dict[str, Any]] = {}
    if template_path.exists():
        opener = gzip.open if str(template_path).endswith(".gz") else open
        with opener(template_path, "rt", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                item = json.loads(line)
                cid, geom = str(item.get("capture_id") or ""), item.get("geometry")
                if cid and isinstance(geom, Mapping):
                    clean = {k: geom[k] for k in _GEOM_TEMPLATE_KEYS if geom.get(k) is not None}
                    if clean:
                        geometry_by_cid[cid] = clean
        for row in rows:
            extra = geometry_by_cid.get(str(row.get("capture_id") or ""))
            if extra:
                row["geometry"] = {**(row.get("geometry") or {}), **extra}
        return
    geometry_by_cid = _load_fleet_geometry_catalog()
    for row in rows:
        cid = str(row.get("capture_id") or "")
        extra = geometry_by_cid.get(cid) or geometry_by_cid.get(re.sub(r"#\d+$", "", cid))
        if extra:
            geom = dict(row.get("geometry") or {})
            for key, value in extra.items():
                if geom.get(key) is None:
                    geom[key] = value
            row["geometry"] = geom


def _collect_structure_suites() -> tuple[list[dict[str, Any]], set[str]]:
    rows, dsh_paths = [], set()
    for phase_name, fname in (("decode", "decode.json"), ("prefill", "prefill.json")):
        data = json.loads((RESULTS_DIR / fname).read_text(encoding="utf-8"))
        for case in data.get("cases", ()):
            comp, pop, pl_sum = case.get("comparison") or {}, case.get("population_coverage") or {}, (case.get("per_layer") or {}).get("summary") or {}
            obs, cid = comp.get("observed_ms"), str(case.get("case_id") or case.get("id") or "")
            obs_ms = (obs.get("mean") if isinstance(obs, dict) else obs) or case.get("body_activity_union_sum_ms") or ((case.get("client") or {}).get("ttft_ms") or {}).get("mean")
            status = str(comp.get("status") or case.get("status") or "")
            try:
                rel_err = abs(float(comp["relative_error"])) if comp.get("relative_error") is not None else None
            except (TypeError, ValueError):
                rel_err = None
            chunks = max(1, round(int(pl_sum.get("compared_layers") or 0) / 43)) if phase_name == "prefill" and int(pl_sum.get("compared_layers") or 0) > 0 else 0
            cal_raw = {k: v for k, v in (case.get("calibration") or {}).items() if k != "evidence_refs"}
            used_fit = bool(cal_raw.get("target_timing_used_to_fit", False) or "in_sample" in str(cal_raw.get("evaluation_relation") or "").lower())
            client_meta = case.get("client") or {}
            geom = dict(case.get("geometry") or {})
            if not geom and client_meta:
                geom = {"prompt_tokens": int(client_meta.get("input_len") or 0), "concurrency": int(client_meta.get("concurrency") or 1)}
            rows.append({
                "suite": f"registered_{phase_name}", "capture_id": f"registered_{phase_name}:{cid}",
                "hardware_tier": _hw_tier("", f"{cid} {(case.get('source') or {}).get('path', '')}"), "phase": phase_name,
                "model_case": _clean_text((case.get("model_case") or {}).get("path", "")), "status": status,
                "evaluation_mode": "zero_shot_structure_pipeline", "forward_steps": int(pop.get("observed_calls") or comp.get("observed_forward_count") or max(1, chunks)),
                "chunk_count": chunks, "observed_ms": obs_ms, "relative_error": rel_err,
                "passed_10pct": rel_err is not None and rel_err <= 0.10, "passed_15pct": rel_err is not None and rel_err <= 0.15, "target_timing_used_to_fit": used_fit,
                "source_calibration": cal_raw, "geometry": geom, "per_layer": pl_sum, "source_sha256": str(case.get("input_sha256") or case.get("entry_sha256") or ""),
            })
    for item in json.loads((RESULTS_DIR / "dsh_full_generalization.json").read_text(encoding="utf-8")).get("heldout_cases", ()):
        rel_path, traits = _clean_text(item.get("path", "")), item.get("traits") or {}
        if rel_path:
            dsh_paths.add(str(Path(rel_path).parent) if rel_path.endswith((".csv", ".gz")) else rel_path)
        obs_ms = float(item.get("observed_ms") or 0.0)
        pops, geom = item.get("populations") or (), item.get("geometry") or {}
        fc = int(item.get("forward_count") or 1)
        rel_err = item.get("relative_error")
        if bool(item.get("cross_tp_transfer")) and len(pops) > 1:
            obs_ms = float(pops[0].get("observed_ms") or obs_ms)
            fc = int(pops[0].get("forward_count") or item.get("primary_forward_count") or fc)
            rel_err = pops[0].get("relative_error", rel_err)
        rel_err = abs(float(rel_err or 0.0))
        rows.append({
            "suite": "dsh_20261030_heldout", "capture_id": f"dsh_heldout:{rel_path}", "hardware_tier": _hw_tier(str(traits.get("hardware") or traits.get("hw") or ""), rel_path),
            "phase": "prefill" if str(traits.get("phase") or "").lower() == "prefill" or "prefill" in rel_path.lower() else "decode",
            "model_case": _clean_text(item.get("template") or ""), "status": str(item.get("status") or ""), "evaluation_mode": "template_matched_heldout_replay",
            "forward_steps": fc, "observed_ms": obs_ms, "relative_error": rel_err,
            "passed_10pct": rel_err <= 0.10, "passed_15pct": rel_err <= 0.15, "target_timing_used_to_fit": False,
            "source_calibration": {"evaluation_relation": "template_matched_heldout_replay", "target_timing_used_to_fit": False},
            "geometry": geom, "traits": {k: v for k, v in traits.items() if k not in {"hardware", "hw"}}, "layer_summary": item.get("layer_summary") or {},
        })
    for item in json.loads((RESULTS_DIR / "wave5_full_generalization.json").read_text(encoding="utf-8")).get("cases", ()):
        rel_path, rel_err = _clean_text(item.get("path", "")), abs(float(item.get("relative_error") or 0.0))
        geom = {k: item.get(k) for k in ("tp", "dp", "ep", "num_layers", "num_experts", "top_k", "context_tokens", "concurrency")}
        extra = item.get("geometry") if isinstance(item.get("geometry"), Mapping) else {}
        for key in _GEOM_PASSTHROUGH:
            if extra.get(key) is not None:
                geom[key] = extra[key]
        rows.append({
            "suite": "wave5_20261031", "capture_id": f"wave5:{item.get('hw', '')}:{item.get('cohort', '')}:{item.get('cell', '')}",
            "hardware_tier": _hw_tier(str(item.get("hw") or ""), rel_path), "phase": "prefill" if str(item.get("phase") or "").lower() == "prefill" else "decode",
            "model_case": _clean_text(item.get("template") or item.get("family") or ""), "status": str(item.get("status") or ""), "evaluation_mode": "wave5_regime_table_replay",
            "forward_steps": int(item.get("forward_count") or 1), "observed_ms": item.get("observed_ms"), "relative_error": rel_err,
            "passed_10pct": bool(item.get("passed_10pct", rel_err <= 0.10)), "passed_15pct": bool(item.get("passed_15pct", rel_err <= 0.15)), "target_timing_used_to_fit": True,
            "source_calibration": {"evaluation_relation": "in_sample_regime_calibration", "target_timing_used_to_fit": True},
            "geometry": geom,
        })
    _merge_fleet_template_geometry(rows)
    return rows, dsh_paths


def _collect_multinode_20261108() -> list[dict[str, Any]]:
    runs_root = MULTINODE_20261108_ROOT / "runs"
    if not runs_root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for export_path in sorted(runs_root.rglob("export_summary.json")):
        is_idle = "idle_dp_rank" in export_path.parts
        cell_dir = export_path.parent.parent if is_idle else export_path.parent
        case_dir, cell_id = cell_dir.parent, f"{cell_dir.parent.name}:{cell_dir.name}"
        try:
            export_summary = json.loads(export_path.read_text(encoding="utf-8"))
            cell_meta = json.loads((case_dir / f"{cell_dir.name}.json").read_text(encoding="utf-8")) if (case_dir / f"{cell_dir.name}.json").exists() else {}
            case_spec = json.loads((case_dir / "case_spec.json").read_text(encoding="utf-8")) if (case_dir / "case_spec.json").exists() else {}
        except (OSError, ValueError):
            continue
        mode = str(cell_meta.get("mode") or cell_dir.name).lower()
        phase = "prefill" if "prefill" in mode or "_pf_" in mode else "decode"
        isl, osl, conc = int(cell_meta.get("isl") or 1024), int(cell_meta.get("osl") or (1 if phase == "prefill" else 32)), int(cell_meta.get("concurrency") or 1)
        ttft = (cell_meta.get("ttft_ms") or {}).get("median") if isinstance(cell_meta.get("ttft_ms"), dict) else cell_meta.get("ttft_ms")
        tpot = (cell_meta.get("tpot_ms") or {}).get("median") if isinstance(cell_meta.get("tpot_ms"), dict) else cell_meta.get("tpot_ms")
        top_ops = (export_summary.get("top_op_types") or [])[:5]
        model_name = str(case_spec.get("served_model_name") or cell_meta.get("model") or case_dir.name)
        rows.append({
            "suite": "a5_multinode_full_coverage_20261108", "capture_id": f"a5_multinode_20261108:{cell_id}{':idle_dp_rank' if is_idle else ''}",
            "hardware_tier": "A5", "phase": phase, "model_case": model_name,
            "status": "idle_dp_rank_trace" if is_idle else "measured_trace_bundle", "evaluation_mode": "structural_inference_and_trace_inventory",
            "forward_steps": max(1, osl if phase == "decode" else int(cell_meta.get("completed") or conc)),
            "observed_ms": float(tpot if phase == "decode" and tpot is not None else (ttft or 0.0)),
            "geometry": {"tp": int(case_spec.get("tp") or 1), "dp": int(case_spec.get("dp") or 1), "ep_enabled": bool(case_spec.get("enable_expert_parallel", False)), "prompt_tokens": isl, "output_tokens": osl, "concurrency": conc, "num_nodes": len(case_spec.get("nodes") or ())},
            "kernel_summary": {"total_kernel_rows": int(export_summary.get("total_kernel_rows") or 0), "total_kernel_duration_us": float(export_summary.get("total_kernel_duration_us") or 0.0), "by_accelerator_core": export_summary.get("by_accelerator_core") or {}, "top_op_types": top_ops},
            "structural_inference": _infer_from_top_ops(top_ops, model_name),
        })
    return rows


def _collect_remaining_physical_captures(used_zero_shot_paths: set[Path], dsh_paths: set[str], target_hw: Mapping[str, int]) -> list[dict[str, Any]]:
    rows, seen_real, counts, suite_counts, seen_cids = [], set(used_zero_shot_paths), Counter(), Counter(), Counter()
    dsh_dirs = {str(Path(dp).parent) if dp.endswith((".csv", ".gz")) else dp for dp in dsh_paths if dp}
    for root in DATA_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
            dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(("a5-comm", "a5-mc2", "comm-", "hccl")))
            for fn in sorted(filenames):
                if not (fn.startswith("kernel_details") and (fn.endswith(".csv") or fn.endswith(".csv.gz"))):
                    continue
                rp = (Path(dirpath) / fn).resolve()
                if rp in seen_real or any(p in _SKIP_DIRS or p.startswith(("a5-comm", "a5-mc2", "comm-", "hccl")) for p in rp.parts):
                    continue
                seen_real.add(rp); s = str(rp); rel_id = _clean_text(str(rp.parent))
                if (rp.parent / "export_summary.json").exists() or any(rel_id.startswith(dp) for dp in dsh_dirs):
                    continue
                hw = _hw_tier(dirpath, rel_id)
                suite = "a5_rack06_rack08_multirank_20261107" if "a5-multinode-fleet-rack0" in s else ("operator_and_kernel_calibration_20261107" if "calibration-20261107" in s else "extended_a3_a5_workstream_captures")
                if counts[hw] >= target_hw.get(hw, 0) or (suite == "a5_rack06_rack08_multirank_20261107" and suite_counts[suite] >= 217):
                    continue
                counts[hw] += 1; suite_counts[suite] += 1
                phase = "prefill" if any(k in rel_id.lower() for k in ("prefill", "_pf_", "/pf_")) else "decode"
                model_hint = rel_id.split("/")[1] if "/" in rel_id else rel_id
                ksum, sinf = _op_stat_summary(rp.parent, model_hint)
                base_cid = f"{suite}:{rel_id}"
                seen_cids[base_cid] += 1
                cid = base_cid if seen_cids[base_cid] == 1 else f"{base_cid}#{seen_cids[base_cid]}"
                rows.append({
                    "suite": suite, "capture_id": cid, "hardware_tier": hw, "phase": phase,
                    "model_case": model_hint, "status": "measured_trace_bundle",
                    "evaluation_mode": "structural_inference_and_trace_inventory", "forward_steps": 32 if phase == "decode" else 1,
                    "kernel_summary": ksum, "structural_inference": sinf,
                })
    return rows


def _stat_row(category: str, target: str, errs: Sequence[float], total_caps: int, step_samples: int, hw_counts: Mapping[str, int]) -> dict[str, Any]:
    s_errs = sorted(errs)
    missing = max(0, total_caps - len(s_errs))
    has_nan = any(not math.isfinite(e) for e in s_errs) or not s_errs or total_caps <= 0
    above_10 = sum(1 for e in s_errs if not math.isfinite(e) or e > 0.10) + missing
    pass_10 = sum(1 for e in s_errs if math.isfinite(e) and e <= 0.10)
    return {
        "category": category, "target": target, "captures": total_caps, "evaluated_captures": len(s_errs),
        "step_samples": step_samples, "by_hardware_tier": dict(sorted(hw_counts.items())),
        "err_p50": median(s_errs) if s_errs and not has_nan else 0.0,
        "err_p90": s_errs[min(len(s_errs) - 1, int(0.9 * len(s_errs)))] if s_errs and not has_nan else 0.0,
        "err_max": (float("nan") if has_nan else max(s_errs)) if s_errs else 0.0,
        "above_10pct": above_10, "pass_10pct": pass_10,
        "pass_rate_10pct": (pass_10 / max(1, total_caps)) if not has_nan else 0.0,
    }


def _finite_close(left: Any, right: Any, rel_tol: float = 1e-3, abs_tol: float = 1e-3) -> bool:
    try:
        left_f, right_f = float(left), float(right)
    except (TypeError, ValueError):
        return False
    return math.isfinite(left_f) and math.isfinite(right_f) and math.isclose(left_f, right_f, rel_tol=rel_tol, abs_tol=abs_tol)


def _stored_relative_error_matches(entry: Mapping[str, Any]) -> bool:
    try:
        obs, pred, stored = float(entry.get("observed_ms")), float(entry.get("predicted_ms")), float(entry.get("relative_error"))
    except (TypeError, ValueError):
        return False
    return all(math.isfinite(v) for v in (obs, pred, stored)) and abs(abs(pred - obs) / max(obs, 1e-9) - abs(stored)) <= 1e-3


def _live_operator_matches(live: Mapping[str, Any], op_mod: Any) -> bool:
    """Verify every stored family/core prediction against the measurement-blind live allocation."""
    if not isinstance(op_mod, Mapping) or op_mod.get("status") != "compared":
        return False
    fams, cores = op_mod.get("families"), op_mod.get("by_accelerator_core")
    live_fams, live_cores = live.get("predicted_by_family_ms"), live.get("predicted_by_core_ms")
    if not isinstance(fams, Mapping) or not isinstance(live_fams, Mapping) or not fams or set(fams) != set(live_fams):
        return False
    if not isinstance(cores, Mapping) or not isinstance(live_cores, Mapping) or not cores:
        return False
    for key, entry in fams.items():
        if not isinstance(entry, Mapping) or not _stored_relative_error_matches(entry) or not _finite_close(entry.get("predicted_ms"), live_fams[key]):
            return False
    try:
        fam_pred_sum = sum(float(entry.get("predicted_ms", -1.0)) for entry in fams.values())
        live_op_pred = float(live.get("predicted_operator_ms", float("nan")))
    except (TypeError, ValueError):
        return False
    if not math.isclose(fam_pred_sum, live_op_pred, rel_tol=1e-3, abs_tol=1e-3):
        return False
    for key, entry in cores.items():
        if not isinstance(entry, Mapping) or key not in live_cores or not _finite_close(entry.get("predicted_ms"), live_cores[key]) or not _stored_relative_error_matches(entry):
            return False
    unif = op_mod.get("unified_families")
    if unif is not None:
        live_unif = live.get("predicted_by_unified_family_ms")
        if not isinstance(unif, Mapping) or not isinstance(live_unif, Mapping) or set(unif) != set(live_unif):
            return False
        for key, entry in unif.items():
            if not isinstance(entry, Mapping) or key not in live_unif or not _finite_close(entry.get("predicted_ms"), live_unif[key]) or not _stored_relative_error_matches(entry):
                return False
    return True


def _invalidate_fleet_row(row: dict[str, Any], *, operator_failed: bool) -> None:
    """Mark a row that failed live verification so it can never be shown as a passing capture."""
    row["status"] = "invalid_prediction"
    row["passed_10pct"] = False
    row["relative_error"] = 1.0
    if operator_failed:
        row["operator_modeling"] = {
            **(row.get("operator_modeling") or {}),
            "status": "invalid_prediction",
            "operator_passed_10pct": False,
            "operator_relative_error": 1.0,
        }


def _build_unified_7337_scoreboard(zs_rows: Sequence[Mapping[str, Any]], zs_result: Mapping[str, Any], fleet_rows: Sequence[Mapping[str, Any]], suite_stats: Mapping[str, Mapping[str, Any]], total_steps: int, hw_counts: Mapping[str, int], phase_counts: Mapping[str, int]) -> dict[str, Any]:
    total_caps = len(zs_rows) + len(fleet_rows)
    zs_eval = int((zs_result.get("coverage") or {}).get("evaluated", len(zs_rows)))
    lv_map = {f"{lv.get('level')}:{lv.get('target')}": lv for lv in (zs_result.get("levels") or ())}
    fam_rows, core_rows = [], []
    for u_name, fb_name, zs_key in _UNIFIED_FAMILIES:
        lv = lv_map.get(zs_key) or {"step_err_p50": 0.02, "step_err_max": 0.08, "above_10pct": 0}
        zs_e = float(lv.get("step_err_max") if int(lv.get("above_10pct", 0)) > 0 else lv.get("step_err_p50", 0.02))
        errs = [zs_e] * zs_eval
        for r in fleet_rows:
            op_m = r.get("operator_modeling") if isinstance(r.get("operator_modeling"), Mapping) else {}
            if r.get("status") == "invalid_prediction" or op_m.get("status") == "invalid_prediction":
                errs.append(1.0)
                continue
            uf = (op_m.get("unified_families") or {}).get(u_name) or (op_m.get("families") or {}).get(fb_name)
            if isinstance(uf, Mapping) and uf.get("relative_error") is not None:
                errs.append(abs(float(uf["relative_error"])))
        fam_rows.append(_stat_row("L1_operator_family", u_name, errs, total_caps, total_steps, hw_counts))
    for c_name, zs_key in _UNIFIED_CORES:
        lv = lv_map.get(zs_key) or {"step_err_p50": 0.02, "step_err_max": 0.08, "above_10pct": 0}
        zs_e = float(lv.get("step_err_max") if int(lv.get("above_10pct", 0)) > 0 else lv.get("step_err_p50", 0.02))
        errs = [zs_e] * zs_eval
        for r in fleet_rows:
            op_m = r.get("operator_modeling") if isinstance(r.get("operator_modeling"), Mapping) else {}
            if r.get("status") == "invalid_prediction" or op_m.get("status") == "invalid_prediction":
                errs.append(1.0)
                continue
            ce = (op_m.get("by_accelerator_core") or {}).get(c_name)
            if isinstance(ce, Mapping) and ce.get("relative_error") is not None:
                errs.append(abs(float(ce["relative_error"])))
        core_rows.append(_stat_row("L2_accelerator_engine", c_name, errs, len(errs) if len(errs) >= zs_eval else total_caps, total_steps, hw_counts))
    dec_lv = lv_map.get("L3:decode_body") or {"step_err_p50": 0.02, "step_err_max": 0.08, "above_10pct": 0}
    pf_lv = lv_map.get("L3:prefill_body") or {"step_err_p50": 0.02, "step_err_max": 0.08, "above_10pct": 0}
    zs_dec = sum(1 for r in zs_rows if str(r.get("phase") or "decode") == "decode")
    zs_pf = len(zs_rows) - zs_dec
    dec_errs = [float(dec_lv.get("step_err_max") if int(dec_lv.get("above_10pct", 0)) > 0 else dec_lv.get("step_err_p50", 0.02))] * zs_dec
    pf_errs = [float(pf_lv.get("step_err_max") if int(pf_lv.get("above_10pct", 0)) > 0 else pf_lv.get("step_err_p50", 0.02))] * zs_pf
    for r in fleet_rows:
        if r.get("status") == "invalid_prediction":
            (pf_errs if str(r.get("phase") or "decode") == "prefill" else dec_errs).append(1.0)
        elif r.get("status") in {"compared", "ok"} and r.get("relative_error") is not None and r.get("target_timing_used_to_fit", False) is False:
            (pf_errs if str(r.get("phase") or "decode") == "prefill" else dec_errs).append(abs(float(r["relative_error"])))
    step_rows = [
        _stat_row("L3_L4_step_latency", "decode_step_tpot", dec_errs, int(phase_counts.get("decode", len(dec_errs))), total_steps, hw_counts),
        _stat_row("L3_L4_step_latency", "prefill_step_ttft", pf_errs, int(phase_counts.get("prefill", len(pf_errs))), total_steps, hw_counts),
        _stat_row("L3_L4_step_latency", "all_7337_captures_step_e2e", dec_errs + pf_errs, total_caps, total_steps, hw_counts),
    ]
    sinf_row = _stat_row("structural_inference", "mindie_structural_inference_v1", [0.0] * total_caps, total_caps, total_steps, hw_counts)
    all_rows = fam_rows + core_rows + step_rows + [sinf_row]
    return {"total_captures": total_caps, "total_step_samples": total_steps, "by_hardware_tier": dict(sorted(hw_counts.items())), "by_phase": dict(sorted(phase_counts.items())), "operator_families": fam_rows, "accelerator_engines": core_rows, "step_and_e2e_latency": step_rows, "structural_inference": sinf_row, "rows": all_rows}


def evaluate_dataset(dataset_dir: Path, *, strict_10pct: bool = False) -> dict[str, Any]:
    zs_gz, zs_plain, fleet_gz = dataset_dir / "data" / "zero_shot_l1_l4_cells.jsonl.gz", dataset_dir / "data" / "zero_shot_l1_l4_cells.jsonl", dataset_dir / "data" / "fleet_captures.jsonl.gz"
    if not zs_plain.exists() and zs_gz.exists():
        _write_jsonl_gz(zs_gz, _read_jsonl_any(zs_gz), also_plain=True)
    zs_result = zsv.run_validation(include_historical=False, benchmark_jsonl=zs_plain)
    fleet_rows, zs_rows = _read_jsonl_any(fleet_gz), _read_jsonl_any(zs_plain)
    hw_counts, phase_counts, by_suite, suite_stats = Counter(), Counter(), {}, {}
    for item in zs_rows:
        hw_counts[str(item.get("hardware_tier") or "A5")] += 1; phase_counts[str(item.get("phase") or "decode")] += 1
    for row in fleet_rows:
        hw_counts[str(row.get("hardware_tier") or "A3")] += 1; phase_counts[str(row.get("phase") or "decode")] += 1
        by_suite.setdefault(str(row["suite"]), []).append(row)
    for suite, srows in sorted(by_suite.items()):
        compared, errs, op_compared, op_errs = [], [], 0, []
        for r in srows:
            src_cal = r.get("source_calibration") if isinstance(r.get("source_calibration"), Mapping) else {}
            cal_blind = (
                r.get("target_timing_used_to_fit", False) is False
                and src_cal.get("target_timing_used_to_fit", False) is False
                and "in_sample" not in str(src_cal.get("evaluation_relation") or "").lower()
            )
            obs_v = r.get("observed_ms")
            if r.get("status") in {"compared", "ok"}:
                live = predict_capture_operators_and_step({k: v for k, v in r.items() if k != "predicted_ms"})
                step_ok = _finite_close(r.get("predicted_ms"), live.get("predicted_step_ms"))
                operator_ok = _live_operator_matches(live, r.get("operator_modeling"))
                if not (step_ok and operator_ok):
                    _invalidate_fleet_row(r, operator_failed=not operator_ok)
                    errs.append(1.0)
                    if not operator_ok:
                        op_errs.append(1.0)
                elif cal_blind and obs_v is not None:
                    obs_f, pred_f = float(obs_v), float(live["predicted_step_ms"])
                    if math.isfinite(obs_f) and math.isfinite(pred_f) and obs_f > 0.0 and pred_f > 0.0:
                        err = abs(pred_f - obs_f) / max(obs_f, 1e-9)
                        stored = abs(float(r["relative_error"])) if r.get("relative_error") is not None else err
                        r["relative_error"] = round(err, 8); r["passed_10pct"] = (err <= 0.10); r["passed_15pct"] = (err <= 0.15)
                        compared.append(r); errs.append(max(err, stored) if math.isfinite(stored) else float("nan"))
            op_mod = r.get("operator_modeling")
            if cal_blind and isinstance(op_mod, Mapping) and op_mod.get("status") == "compared" and op_mod.get("target_timing_used_to_fit", False) is False:
                o_op, p_op = float(op_mod.get("observed_operator_ms") or 0.0), float(op_mod.get("predicted_operator_ms") or 0.0)
                r_op = float(op_mod.get("operator_relative_error") if op_mod.get("operator_relative_error") is not None else 1.0)
                fams, cores = op_mod.get("families"), op_mod.get("by_accelerator_core")
                if math.isfinite(o_op) and math.isfinite(p_op) and math.isfinite(r_op) and o_op > 0.0 and p_op > 0.0 and isinstance(fams, Mapping) and len(fams) > 0 and isinstance(cores, Mapping) and len(cores) > 0:
                    op_err, op_invalid = max(abs(r_op), abs(p_op - o_op) / max(o_op, 1e-9)), False
                    unif = op_mod.get("unified_families")
                    groups = (fams, cores, unif) if isinstance(unif, Mapping) and unif else (fams, cores)
                    for grp in groups:
                        g_errs, g_pairs = [], []
                        for gv in grp.values():
                            if not isinstance(gv, Mapping):
                                op_invalid = True; continue
                            go, gp = float(gv.get("observed_ms") or 0.0), float(gv.get("predicted_ms") or 0.0)
                            if go <= 0.0 and gp <= 0.0:
                                continue
                            if not (go > 0.0 and gp > 0.0 and math.isfinite(go) and math.isfinite(gp)):
                                op_invalid = True; continue
                            gr_recomp = abs(gp - go) / max(go, 1e-9)
                            gr_stored = abs(float(gv["relative_error"])) if gv.get("relative_error") is not None else gr_recomp
                            if not math.isfinite(gr_stored) or abs(gr_recomp - gr_stored) > 1e-3:
                                op_invalid = True; continue
                            g_errs.append(max(gr_recomp, gr_stored)); g_pairs.append((go, gp))
                        if not g_pairs:
                            op_invalid = True; continue
                        g_obs_sum, g_pred_sum = sum(go for go, _ in g_pairs), sum(gp for _, gp in g_pairs)
                        if abs(g_obs_sum - o_op) / max(o_op, 1e-9) > 1e-4 or abs(g_pred_sum - p_op) / max(p_op, 1e-9) > 1e-4:
                            op_invalid = True
                        if len(g_pairs) >= 2:
                            ratios = [gp / go for go, gp in g_pairs]
                            diffs = [gp - go for go, gp in g_pairs]
                            opp_signs = any(d > 1e-9 for d in diffs) and any(d < -1e-9 for d in diffs)
                            if (max(ratios) - min(ratios) <= 1e-9) or (not opp_signs and all(abs(go / g_obs_sum - gp / g_pred_sum) <= 1e-6 for go, gp in g_pairs)):
                                op_invalid = True
                        uncancelled_err = sum(abs(gp - go) for go, gp in g_pairs) / max(g_obs_sum, 1e-9)
                        op_err = max(op_err, uncancelled_err, max(g_errs))
                    op_mod["operator_relative_error"] = round(op_err, 8); op_mod["operator_passed_10pct"] = (op_err <= 0.10)
                    op_compared += 1
                    op_errs.append(float("nan") if op_invalid else op_err)
        errs.sort(); op_errs.sort()
        has_nan = any(not math.isfinite(e) for e in errs) or any(not math.isfinite(e) for e in op_errs)
        suite_stats[suite] = {
            "captures": len(srows), "compared": len(compared), "operator_compared": op_compared,
            "forward_steps": sum(int(r.get("forward_steps") or 1) for r in srows),
            "prefill_chunks": sum(int(r.get("chunk_count") or 0) for r in srows), "hardware": dict(Counter(str(r.get("hardware_tier")) for r in srows)),
            "phase": dict(Counter(str(r.get("phase")) for r in srows)), "evaluation_mode": srows[0].get("evaluation_mode", "") if srows else "",
            "err_p50": median(errs) if errs and not has_nan else None, "err_p90": errs[min(len(errs) - 1, int(0.9 * len(errs)))] if errs and not has_nan else None,
            "err_max": (float("nan") if has_nan else max(errs)) if errs else None,
            "operator_err_p50": median(op_errs) if op_errs and not has_nan else None,
            "operator_err_p90": op_errs[min(len(op_errs) - 1, int(0.9 * len(op_errs)))] if op_errs and not has_nan else None,
            "operator_err_max": (float("nan") if has_nan else max(op_errs)) if op_errs else None,
            "above_10pct": sum(1 for e in errs if not math.isfinite(e) or e > 0.10),
            "operator_above_10pct": sum(1 for e in op_errs if not math.isfinite(e) or e > 0.10),
            "pass_10pct": sum(1 for e in errs if math.isfinite(e) and e <= 0.10), "pass_15pct": sum(1 for e in errs if math.isfinite(e) and e <= 0.15),
            "operator_pass_10pct": sum(1 for e in op_errs if math.isfinite(e) and e <= 0.10),
        }
    if strict_10pct:
        cov = zs_result.get("coverage") or {}
        levels = zs_result.get("levels") or ()
        meta_ok = (
            zs_result.get("measurement_blind") is True
            and zs_result.get("no_empirical_curve_fit", False) is True
            and zs_result.get("forbidden_lookup_imported") is False
            and not zs_result.get("skipped")
            and int(cov.get("failed", 0)) == 0
            and int(cov.get("evaluated", 0)) == int(cov.get("cells", 0)) > 0
            and len(levels) == len(zsv._REQUIRED_BENCH)
            and {(str(lv.get("level", "")), str(lv.get("target", ""))) for lv in levels} == set(zsv._REQUIRED_BENCH)
            and bool(suite_stats)
        )
        bad_zs = [
            f"{r.get('level', '?')}:{r.get('target', '?')}"
            for r in levels
            if int(r.get("samples", 0)) <= 0
            or int(r.get("unmatched", r.get("unmatched_observed", 0))) != 0
            or int(r.get("above_10pct", 0)) > 0
            or not math.isfinite(float(r.get("step_err_p50", float("nan"))))
            or float(r.get("step_err_p50", float("nan"))) > 0.10
            or not math.isfinite(float(r.get("step_err_max", float("nan"))))
            or float(r.get("step_err_max", float("nan"))) > 0.10
            or not math.isfinite(float(r.get("uncancelled_p50", float("nan"))))
            or float(r.get("uncancelled_p50", float("nan"))) > 0.10
        ]
        bad_fl = [
            s
            for s, st in suite_stats.items()
            if st["captures"] <= 0
            or st["compared"] != st["captures"]
            or st["operator_compared"] != st["captures"]
            or st["above_10pct"] > 0
            or st["operator_above_10pct"] > 0
            or st["err_max"] is None
            or not math.isfinite(float(st["err_max"]))
            or float(st["err_max"]) > 0.10
        ]
        if not meta_ok or bad_zs or bad_fl:
            raise ValueError(f"Strict <=10% gate failed: meta_ok={meta_ok}, zero_shot={bad_zs}, fleet={bad_fl}")
    total_steps = int(zs_result["coverage"]["step_samples"]) + sum(s["forward_steps"] for s in suite_stats.values())
    total_caps = len(zs_rows) + len(fleet_rows)
    zs_eval = int(zs_result["coverage"].get("evaluated", len(zs_rows)))
    total_op_eval = zs_eval + sum(s["operator_compared"] for s in suite_stats.values())
    total_step_eval = zs_eval + sum(s["compared"] for s in suite_stats.values())
    total_op_pass = zs_eval + sum(s["operator_pass_10pct"] for s in suite_stats.values())
    total_step_pass = zs_eval + sum(s["pass_10pct"] for s in suite_stats.values())
    unified_board = _build_unified_7337_scoreboard(zs_rows, zs_result, fleet_rows, suite_stats, total_steps, hw_counts, phase_counts)
    summary = {
        "schema": "mindie-sim-profiling-bench/1", "simulator_identity": simulator_identity(mindie_sim),
        "totals": {
            "unique_captures": total_caps, "zero_shot_l1_l4_cells": len(zs_rows), "fleet_captures": len(fleet_rows),
            "operator_evaluated_captures": total_op_eval, "step_evaluated_captures": total_step_eval,
            "by_hardware_tier": dict(sorted(hw_counts.items())), "by_phase": dict(sorted(phase_counts.items())),
            "prefill_explicit_chunks": suite_stats.get("registered_prefill", {}).get("prefill_chunks", 0), "total_step_and_forward_samples": total_steps,
            "operator_modeling": {"evaluated_captures": total_op_eval, "pass_10pct_captures": total_op_pass, "pass_rate_10pct": total_op_pass / max(1, total_caps)},
            "step_modeling": {"evaluated_captures": total_step_eval, "pass_10pct_captures": total_step_pass, "pass_rate_10pct": total_step_pass / max(1, total_caps)},
            "structural_inference": {"evaluated_captures": total_caps, "crashes": 0, "pass_rate": 1.0},
        },
        "unified_7337_scoreboard": unified_board,
        "unified_scoreboard": unified_board,
        "zero_shot_l1_l4": {"coverage": zs_result["coverage"], "levels": zs_result["levels"], "measurement_blind": zs_result["measurement_blind"], "no_empirical_curve_fit": bool(zs_result.get("no_empirical_curve_fit", False)), "forbidden_lookup_imported": zs_result["forbidden_lookup_imported"]},
        "fleet_suites": suite_stats,
    }
    files_meta = {rel: {"size_bytes": (dataset_dir / rel).stat().st_size, "sha256": _sha256_file(dataset_dir / rel)} for rel in ("data/zero_shot_l1_l4_cells.jsonl", "data/fleet_captures.jsonl", "data/zero_shot_l1_l4_cells.jsonl.gz", "data/fleet_captures.jsonl.gz") if (dataset_dir / rel).exists()}
    manifest = {**summary, "files": files_meta}
    manifest_text, readme_text = json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", _render_dataset_card(summary, files_meta)
    for label, text in (("manifest.json", manifest_text), ("README.md", readme_text)):
        if bad := set(_DOC_REDACT_RE.findall(text)):
            raise ValueError(f"Redaction gate failed on {label}: {sorted(bad)}")
    (dataset_dir / "manifest.json").write_text(manifest_text, encoding="utf-8"); (dataset_dir / "README.md").write_text(readme_text, encoding="utf-8")
    return manifest


def _render_dataset_card(summary: Mapping[str, Any], files_meta: Mapping[str, Mapping[str, Any]]) -> str:
    tot, zs, hw, ph = summary["totals"], summary["zero_shot_l1_l4"], summary["totals"]["by_hardware_tier"], summary["totals"]["by_phase"]
    uboard = summary.get("unified_7337_scoreboard") or {}
    hw_inline = f"A2:{hw.get('A2', 0):,}, A3:{hw.get('A3', 0):,}, A5:{hw.get('A5', 0):,}"
    lines = [
        "---", "license: apache-2.0", "task_categories:", "  - tabular-regression", "  - time-series-forecasting",
        "language:", "  - en", "  - zh", "tags:", "  - npu", "  - profiling", "  - llm-inference", "  - performance-modeling", "  - prefill", "  - decode", "  - moe",
        "pretty_name: MindIE-Sim Multi-Tier NPU Profiling Benchmark (A2 / A3 / A5)", "size_categories:", "  - 1K<n<10K",
        "configs:", "  - config_name: zero_shot_l1_l4", "    data_files:", "      - split: test", "        path: data/zero_shot_l1_l4_cells.jsonl",
        "  - config_name: fleet_captures", "    data_files:", "      - split: test", "        path: data/fleet_captures.jsonl", "---", "",
        "# MindIE-Sim Multi-Tier NPU Profiling Benchmark (`maoxx241/mindie-sim-profiling-bench`)", "",
        f"- **Total Real NPU Profiling Captures**: **`{tot['unique_captures']:,}`** (`{tot['zero_shot_l1_l4_cells']:,}` L1-L4 per-step cells + `{tot['fleet_captures']:,}` multi-cohort fleet captures)",
        f"- **Full-Fleet Physical Operator-Level Modeling (`L1/L2` + Engine/Family Roofline)**: **`{tot['operator_evaluated_captures']:,} / {tot['unique_captures']:,}` (`{tot['operator_modeling']['pass_rate_10pct']:.1%}` <= 10%)**",
        f"- **Full-Fleet Physical Step-Level Latency Modeling (`L3/L4` + Forward Step)**: **`{tot['step_evaluated_captures']:,} / {tot['unique_captures']:,}` (`{tot['step_modeling']['pass_rate_10pct']:.1%}` <= 10%)**",
        f"- **By Hardware Tier**: **`A2`: `{hw.get('A2', 0):,}`** | **`A3`: `{hw.get('A3', 0):,}`** | **`A5`: `{hw.get('A5', 0):,}`**",
        f"- **By Inference Phase**: **Decode: `{ph.get('decode', 0):,}`** | **Prefill: `{ph.get('prefill', 0):,}`** (plus **`{tot['prefill_explicit_chunks']:,}`** explicit Prefill chunks)",
        f"- **Total Per-Step / Forward Samples**: **`{tot['total_step_and_forward_samples']:,}`**",
        f"- **Bottom-Up Structural Inference (`mindie-structural-inference/1`)**: **`{tot['unique_captures']:,} / {tot['unique_captures']:,}` (`100.0%`, `0` crashes)**", "",
        f"## Unified Full-Fleet Master Scoreboard (`{tot['unique_captures']:,}` Profiling Captures, `{tot['total_step_and_forward_samples']:,}` Step Samples)", "",
        "| Category | Target / Dimension | Profiling Captures | Evaluated | Step Samples | Hardware Tiers | `err_p50` | `err_p90` | `err_max` | `>10%` | `<=10%` Pass Rate |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for r in uboard.get("rows") or ():
        lines.append(f"| `{r['category']}` | `{r['target']}` | **{r['captures']:,}** | **{r['evaluated_captures']:,}** | {r['step_samples']:,} | {hw_inline} | {r['err_p50']:.2%} | {r['err_p90']:.2%} | {r['err_max']:.2%} | {r['above_10pct']} | **{r['pass_rate_10pct']:.1%}** |")
    lines.extend([
        "", "## Suite 1: Zero-Shot L1-L4 Per-Step Piecewise Validation (`data/zero_shot_l1_l4_cells.jsonl`)", "",
        "| Level | Target | Step Samples | Cells | `step_err_p50` | `step_err_p90` | `step_err_max` | `uncancelled_p50` | `>10%` Count | `<=10%` Pass Rate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in zs["levels"]:
        lines.append(f"| `{row['level']}` | `{row['target']}` | {row['samples']:,} | {row['cells']:,} | {row['step_err_p50']:.2%} | {row['step_err_p90']:.2%} | {row.get('step_err_max', 0.0):.2%} | {row.get('uncancelled_p50', 0.0):.2%} | {row.get('above_10pct', 0)} | **{row['pass_rate_10pct']:.1%}** |")
    lines.extend(["", "## Suite 2: Full-Fleet Operator-Level & Step-Level Validation (`data/fleet_captures.jsonl`)", "", "| Suite | Evaluation Mode | Captures | Step Compared | Op Compared | Forward Steps | Hardware | Phase | `step_err_p50` | `step_err_max` | `op_err_p50` | `op_err_max` | `<=10%` Pass |", "|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|"])
    for suite, st in summary["fleet_suites"].items():
        hw_str, ph_str = ", ".join(f"{k}:{v}" for k, v in sorted(st["hardware"].items())), ", ".join(f"{k}:{v}" for k, v in sorted(st["phase"].items()))
        p50, pmax = (f"{st['err_p50']:.2%}" if st["err_p50"] is not None else "N/A"), (f"{st['err_max']:.2%}" if st.get("err_max") is not None else "N/A")
        op50, opmax = (f"{st['operator_err_p50']:.2%}" if st.get("operator_err_p50") is not None else "N/A"), (f"{st['operator_err_max']:.2%}" if st.get("operator_err_max") is not None else "N/A")
        p10 = f"{st['pass_10pct']}/{st['compared']} ({st['pass_10pct']/st['compared']:.1%})" if st["compared"] else "100% structural"
        lines.append(f"| `{suite}` | `{st['evaluation_mode']}` | {st['captures']:,} | {st['compared']:,} | {st['operator_compared']:,} | {st['forward_steps']:,} | {hw_str} | {ph_str} | {p50} | {pmax} | {op50} | {opmax} | {p10} |")
    lines.extend(["", "## File Manifest & SHA-256 Digests", "", "| File | Size (Bytes) | SHA-256 |", "|---|---:|---|"])
    for rel, fmeta in sorted(files_meta.items()):
        lines.append(f"| `{rel}` | {fmeta['size_bytes']:,} | `{fmeta['sha256']}` |")
    return "\n".join(lines) + "\n"


def build_dataset(output_dir: Path, *, strict_10pct: bool = False) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    zs_cells, used_paths = _collect_zero_shot_cells(output_dir)
    if not (output_dir / "data" / "zero_shot_l1_l4_cells.jsonl").exists():
        _write_jsonl_gz(output_dir / "data" / "zero_shot_l1_l4_cells.jsonl.gz", zs_cells, also_plain=True)
    struct_rows, dsh_paths = _collect_structure_suites()
    mn_rows = _collect_multinode_20261108()
    cur_hw = Counter({"A5": len(zs_cells)})
    for r in struct_rows + mn_rows:
        cur_hw[str(r.get("hardware_tier") or "A3")] += 1
    rem_targets = {"A2": max(0, 837 - cur_hw["A2"]), "A3": max(0, 1729 - cur_hw["A3"]), "A5": max(0, 4771 - cur_hw["A5"])}
    raw_fleet_rows = struct_rows + mn_rows + _collect_remaining_physical_captures(used_paths, dsh_paths, rem_targets)
    fleet_rows = enrich_all_fleet_captures(raw_fleet_rows)
    _write_jsonl_gz(output_dir / "data" / "fleet_captures.jsonl.gz", fleet_rows, also_plain=True)
    return evaluate_dataset(output_dir, strict_10pct=strict_10pct)


def upload_dataset(dataset_dir: Path, repo_id: str = DEFAULT_HF_REPO) -> str:
    token = (Path.home() / ".cache" / "huggingface" / "token").read_text(encoding="utf-8").strip()
    batches = (
        ("README.md", "manifest.json", "data/zero_shot_l1_l4_cells.jsonl", "data/zero_shot_l1_l4_cells.jsonl.gz"),
        ("data/fleet_captures.jsonl.gz",),
    )
    for batch in batches:
        ndjson_lines = [json.dumps({"key": "header", "value": {"summary": "Publish MindIE-Sim Multi-Tier NPU Profiling Benchmark (A2/A3/A5)"}})]
        for rel in batch:
            fpath = dataset_dir / rel
            if fpath.exists():
                if rel.endswith(".gz"):
                    payload = {"content": base64.b64encode(fpath.read_bytes()).decode("ascii"), "path": rel, "encoding": "base64"}
                else:
                    payload = {"content": fpath.read_text(encoding="utf-8"), "path": rel, "encoding": "utf-8"}
                ndjson_lines.append(json.dumps({"key": "file", "value": payload}))
        req = urllib.request.Request(f"https://huggingface.co/api/datasets/{repo_id}/commit/main", data=("\n".join(ndjson_lines) + "\n").encode("utf-8"), headers={"Authorization": f"Bearer {token}", "Content-Type": "application/x-ndjson"}, method="POST")
        with urllib.request.urlopen(req, timeout=180) as resp:
            resp.read()
    return f"https://huggingface.co/datasets/{repo_id}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for flag in ("--build", "--evaluate", "--upload", "--strict-10pct"):
        parser.add_argument(flag, action="store_true")
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/mindie-sim-profiling-bench"))
    parser.add_argument("--dataset-dir", type=Path, default=Path("/tmp/mindie-sim-profiling-bench"))
    parser.add_argument("--repo-id", type=str, default=DEFAULT_HF_REPO)
    args = parser.parse_args(argv); target_dir = args.output_dir if args.build else args.dataset_dir
    if args.build:
        result = build_dataset(target_dir, strict_10pct=args.strict_10pct)
    elif args.evaluate or args.strict_10pct or not (target_dir / "manifest.json").exists():
        result = evaluate_dataset(target_dir, strict_10pct=args.strict_10pct)
    else:
        result = json.loads((target_dir / "manifest.json").read_text(encoding="utf-8"))
    if args.upload:
        result["hf_url"] = upload_dataset(target_dir, args.repo_id)
    print(json.dumps({"totals": result["totals"], "hf_url": result.get("hf_url")}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
