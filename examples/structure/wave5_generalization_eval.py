"""Unified Wave 5 multi-chip (A2 + A3 + A5) ultra-long-context and synthetic-expert MoE evaluator.

[Role] Aggregate or re-execute the Wave 5 (2026-10-31) evaluations across Ascend
  910B4 (A2), Ascend 910_9392 (A3), and Ascend 910_9599 (A5) covering 4K..400K
  ultra-long-context trajectories, reduced-expert real checkpoints (DeepSeek-V2-Lite,
  DeepSeek-V3.2-Prune-3L, Qwen3-30B-A3B), and synthetic L=8, E in {16, 32, 48, 64},
  K in {2, 4, 6, 8} MoE topologies.
[Invariants] Observed body_forward_span_ms hardware measurements are never trimmed
  or mutated. Service-regime calibration provenance (including A3 input-conditioned
  cohort:context_tokens:concurrency overrides vs A2/A5 cohort-phase templates) is
  explicitly disclosed in JSON and Markdown reports.
[Timeouts & Locks] Sequential offline CPU chip runs allow 3600s each (10800s
  total), with bounded worker pools (<= 4 workers, default 3) and archived
  per-future deadlines. Outputs use atomic tempfile + os.replace().
[Side-Effect Policy] Writes reports and fresh chip caches beside the requested
  output. Historical archives, source cases and captures stay read-only.
"""
from __future__ import annotations
from service_response_acceptance import evaluate_acceptance

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import argparse
from functools import partial
from hashlib import sha256
import importlib
import json
import multiprocessing
import os
from pathlib import Path
from statistics import median
import subprocess
import sys
import tempfile
import time

from mindie_profiler import decode_segmentation
from mindie_profiler.events import PARSER_VERSION
import mindie_sim
from runtime_identity import simulator_identity
from wave5_regime_import import import_a3_regime_catalog
from native_observations import native_observation_identity, predict_body as native_predict_body
from capture_policy import import_capture_policy
from scoped_native_replay import (
    compact_scope_sidecar, load_verified_extraction, prefill_geometries,
    prediction_identity, prepare_scoped_replay, price_declared_prediction)
from dsh_scoped_prefill import load_scoped_predictions, score_prefill_capture

STRUCT_DIR = Path(__file__).resolve().parent
DEFAULT_ARCHIVE_ROOT = Path("/Volumes/data/mindie-sim-data/acceptance-archives-20261030/wave5-eval")
DEFAULT_OUT_JSON = STRUCT_DIR / "results" / "wave5_full_generalization.json"
DEFAULT_OUT_MD = STRUCT_DIR / "results" / "wave5_full_generalization.md"
MAX_WORKERS = 4
CHIP_TIMEOUT_SECONDS = 3600

CALIBRATION_PROVENANCE = {
    "evaluation_relation": "in_sample_regime_calibration",
    "target_timing_used_to_fit": True,
    "heldout_observed_values_used_in_fit": True,
    "observed_spans_untrimmed": True,
    "input_conditioned_regime_overrides_by_hw": {"a2": False, "a3": True, "a5": False},
    "calibration_scope": (
        "In-sample service_regimes calibration on Wave 5 (heldout_engine_20261031) "
        "captures across A2, A3, and A5. A2 and A5 select regimes strictly by "
        "cohort-phase architecture/parallelism; A3 additionally includes "
        "(cohort, context_tokens, concurrency)-conditioned regime overrides in "
        "a3/templates/_regime_catalog.json."
    ),
}


def _bounded_workers(value: int) -> int:
    return max(1, min(int(value), MAX_WORKERS))


_PARSER_SOURCES = ("decode_segmentation.py", "decode_active_event.py", "communication_bounds.py", "events.py", "prefill.py")


def _parser_identity(prof_root: Path | None = None, struct_dir: Path | None = None) -> str:
    prof_root = prof_root or Path(decode_segmentation.__file__).resolve().parent
    struct_dir = struct_dir or STRUCT_DIR
    digest = sha256(PARSER_VERSION.encode("utf-8"))
    for name in _PARSER_SOURCES:
        mod_path = (struct_dir if name == "prefill.py" else prof_root) / name
        payload = mod_path.read_bytes()
        if not payload:
            raise ValueError(f"parser source is empty: {mod_path}")
        digest.update(payload)
    return f"{PARSER_VERSION}:{digest.hexdigest()[:16]}"


def _sim_identity() -> str:
    return simulator_identity(mindie_sim)


PARSER_IDENTITY = _parser_identity()
SIM_IDENTITY = _sim_identity()
NATIVE_OBSERVATION_IDENTITY = native_observation_identity()


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".wave5-eval-", suffix=path.suffix, dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _atomic_write_json(path: Path, payload: dict) -> None:
    _atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def _summarize_errors(errors: list[float]) -> dict:
    if not errors:
        return {"count": 0, "pass_15pct": 0, "pass_10pct": 0, "pass_rate_15pct": 0.0,
                "pass_rate_10pct": 0.0, "mean_abs_error": 0.0, "median_abs_error": 0.0, "max_abs_error": 0.0}
    abs_errs = [abs(float(e)) for e in errors]
    n, p15, p10 = len(abs_errs), sum(1 for e in abs_errs if e <= 0.15), sum(1 for e in abs_errs if e <= 0.10)
    return {
        "count": n, "pass_15pct": p15, "pass_10pct": p10,
        "pass_rate_15pct": round(p15 / n, 4), "pass_rate_10pct": round(p10 / n, 4),
        "mean_abs_error": round(sum(abs_errs) / n, 4), "median_abs_error": round(median(abs_errs), 4),
        "max_abs_error": round(max(abs_errs), 4),
    }


def _classify_track(case_rec: dict) -> str:
    family = str(case_rec.get("family") or "").lower()
    cohort = str(case_rec.get("cohort") or "").lower()
    if family.startswith("synth-") or "synth_" in cohort:
        return "synthetic_moe_l8"
    if any(k in family for k in ("v2-lite", "v3.2-prune", "30b-a3b")) or any(
        k in cohort for k in ("real_dsv2lite", "real_dsv32prune", "real_qwen30b", "qwen30ba3b")
    ):
        return "reduced_expert_real_checkpoints"
    return "ultra_long_context_real_checkpoints"


def _normalize_case(hw: str, raw: dict) -> dict:
    tr = raw.get("traits", {})
    num_layers = tr.get("num_layers") if tr.get("num_layers") is not None else tr.get("layers")
    cohort = str(tr.get("cohort") or "")
    phase = str(tr.get("phase") or "")
    if hw == "a5" and cohort and not cohort.endswith(f"_{phase}"):
        cohort = f"a5/{cohort}_{phase}"
    rec = {
        "path": raw.get("path"), "hw": hw, "cohort": cohort, "cell": tr.get("cell"),
        "family": tr.get("family"), "phase": phase, "tp": tr.get("tp"), "dp": tr.get("dp", 1),
        "ep": tr.get("ep", 1), "num_layers": num_layers, "num_experts": tr.get("num_experts"),
        "top_k": tr.get("top_k"), "spec_tokens": tr.get("spec_tokens", 0),
        "context_tokens": tr.get("context_tokens"), "concurrency": tr.get("concurrency"),
        "template": raw.get("template"), "status": raw.get("status"),
        "forward_count": raw.get("forward_count"), "observed_ms": raw.get("observed_ms"),
        "predicted_ms": raw.get("predicted_ms"), "relative_error": raw.get("relative_error"),
        "passed_15pct": bool(raw.get("passed_15pct")), "passed_10pct": bool(raw.get("passed_10pct")),
    }
    rec["track"] = _classify_track(rec)
    if raw.get("ordered_parts"):
        ordered_parts = [dict(part) for part in raw["ordered_parts"]]
    else:
        populations = raw.get("populations") or []
        ordered_parts = [{"observed_ms": p.get("observed_ms"),
                          "predicted_ms": (p.get("predicted_ms")
                                           if p.get("relative_error") is not None
                                           and p.get("status") in (None, "compared", "completed", "ok")
                                           else None),
                          "status": p.get("status"),
                          "count": p.get("forward_count", 1),
                          "id": p.get("geometry")}
                         for p in populations
                         if isinstance(p, dict)
                         and int(p.get("forward_count") or 0) > 0]
    if ordered_parts:
        rec["ordered_parts"] = ordered_parts
        rec["uncancelled_acceptance"] = (
            dict(raw["uncancelled_acceptance"])
            if isinstance(raw.get("uncancelled_acceptance"), dict)
            else evaluate_acceptance(ordered_parts, tolerance=0.10, label=rec.get("cell"))
        )
    elif isinstance(raw.get("uncancelled_acceptance"), dict):
        rec["uncancelled_acceptance"] = dict(raw["uncancelled_acceptance"])
    return rec


def _normalize_cohort(hw: str, raw: dict, cohort_cases: list[dict]) -> dict:
    phase = str(raw.get("phase") or "")
    cohort = str(raw.get("cohort") or "")
    if hw == "a5" and cohort and not cohort.endswith(f"_{phase}"):
        cohort = f"a5/{cohort}_{phase}"
    first_case = cohort_cases[0] if cohort_cases else {}
    num_layers = raw.get("num_layers") if raw.get("num_layers") is not None else raw.get("layers")
    if num_layers is None:
        num_layers = first_case.get("num_layers")
    tp = raw.get("tp") if raw.get("tp") is not None else first_case.get("tp")
    dp = raw.get("dp") if raw.get("dp") is not None else first_case.get("dp")
    ep = raw.get("ep") if raw.get("ep") is not None else first_case.get("ep")
    return {
        "cohort": cohort,
        "hw": hw,
        "family": raw.get("family") or first_case.get("family"),
        "phase": phase,
        "tp": tp,
        "dp": dp,
        "ep": ep,
        "num_layers": num_layers,
        "num_experts": raw.get("num_experts") if raw.get("num_experts") is not None else first_case.get("num_experts"),
        "top_k": raw.get("top_k") if raw.get("top_k") is not None else first_case.get("top_k"),
        "spec_tokens": raw.get("spec_tokens") if raw.get("spec_tokens") is not None else first_case.get("spec_tokens", 0),
        "capture_count": int(raw.get("capture_count", len(cohort_cases))),
        "compared_count": int(raw.get("compared_count", len(cohort_cases))),
        "stats": raw.get("stats", {}),
        "calibration_provenance": {
            "evaluation_relation": "in_sample_regime_calibration",
            "target_timing_used_to_fit": True,
            "heldout_observed_values_used_in_fit": True,
            "observed_spans_untrimmed": True,
            "input_conditioned_regime_overrides": (hw == "a3"),
        },
    }


def aggregate_chip_reports(a2_report: dict, a3_report: dict, a5_report: dict) -> dict:
    chip_map = {
        "a2": (a2_report, a2_report.get("cases", []), a2_report.get("cohort_summaries", [])),
        "a3": (a3_report, a3_report.get("heldout_cases", []), a3_report.get("cohort_summaries", [])),
        "a5": (a5_report, a5_report.get("captures", []), a5_report.get("cohort_phase_summaries", [])),
    }
    all_cases: list[dict] = []
    all_cohorts: list[dict] = []
    chip_identities: dict[str, dict] = {}
    for hw, (rep, raw_cases, raw_cohorts) in chip_map.items():
        rep_parser = rep.get("parser_identity")
        if not isinstance(rep_parser, str) or rep_parser != PARSER_IDENTITY:
            raise ValueError(
                f"chip_report_parser_identity_mismatch:{hw}:{rep_parser}!={PARSER_IDENTITY}"
            )
        chip_identities[hw] = {
            "schema_version": rep.get("schema_version"),
            "parser_identity": rep_parser,
            "sim_identity": rep.get("sim_identity"),
            "sim_identity_status": (
                "missing" if rep.get("sim_identity") is None else
                "matches_current" if rep["sim_identity"] == SIM_IDENTITY else "differs_from_current"
            ),
            "input_provenance": rep.get("input_provenance"),
        }
        norm_cases = [_normalize_case(hw, c) for c in raw_cases]
        by_cohort: dict[str, list[dict]] = defaultdict(list)
        for nc in norm_cases:
            by_cohort[nc["cohort"]].append(nc)
        all_cases.extend(norm_cases)
        for rc in raw_cohorts:
            phase = str(rc.get("phase") or "")
            c_key = str(rc.get("cohort") or "")
            if hw == "a5" and c_key and not c_key.endswith(f"_{phase}"):
                c_key = f"a5/{c_key}_{phase}"
            all_cohorts.append(_normalize_cohort(hw, rc, by_cohort.get(c_key, [])))

    def _errs(pred) -> list[float]:
        return [float(c["relative_error"]) for c in all_cases if c.get("relative_error") is not None and pred(c)]

    summary = {
        "wave5_all": _summarize_errors(_errs(lambda _: True)),
        "by_hardware": {
            "a2_ascend910b4": _summarize_errors(_errs(lambda c: c["hw"] == "a2")),
            "a3_ascend910_9392": _summarize_errors(_errs(lambda c: c["hw"] == "a3")),
            "a5_ascend910_9599": _summarize_errors(_errs(lambda c: c["hw"] == "a5")),
        },
        "by_phase": {
            "decode": _summarize_errors(_errs(lambda c: c["phase"] == "decode")),
            "prefill": _summarize_errors(_errs(lambda c: c["phase"] == "prefill")),
        },
        "by_track": {
            "ultra_long_context_real_checkpoints": _summarize_errors(
                _errs(lambda c: c["track"] == "ultra_long_context_real_checkpoints")
            ),
            "reduced_expert_real_checkpoints": _summarize_errors(
                _errs(lambda c: c["track"] == "reduced_expert_real_checkpoints")
            ),
            "synthetic_moe_l8": _summarize_errors(
                _errs(lambda c: c["track"] == "synthetic_moe_l8")
            ),
        },
        "ultra_long_192k_to_400k": _summarize_errors(
            _errs(lambda c: int(c.get("context_tokens") or 0) >= 196608)
        ),
    }
    current_sim = all(row["sim_identity_status"] == "matches_current"
                      for row in chip_identities.values())
    return {
        "schema_version": "mindie-wave5-full-generalization/1",
        "parser_identity": PARSER_IDENTITY,
        "sim_identity": SIM_IDENTITY if current_sim else None,
        "evaluator_sim_identity": SIM_IDENTITY,
        "sim_identity_matches_current": current_sim,
        "chip_report_identities": chip_identities,
        "calibration_provenance": CALIBRATION_PROVENANCE,
        "inventory": {
            "total_csvs": len(all_cases),
            "compared_csvs": summary["wave5_all"]["count"],
            "a2_csvs": summary["by_hardware"]["a2_ascend910b4"]["count"],
            "a3_csvs": summary["by_hardware"]["a3_ascend910_9392"]["count"],
            "a5_csvs": summary["by_hardware"]["a5_ascend910_9599"]["count"],
            "cohort_phase_count": len(all_cohorts),
        },
        "summary": summary,
        "cohort_summaries": all_cohorts,
        "cases": all_cases,
    }


def render_markdown(report: dict) -> str:
    inv = report["inventory"]
    s = report["summary"]
    prov = report["calibration_provenance"]
    lines = [
        "# MindIE-Sim & MindIE-Profiler Wave 5 (`2026-10-31`) Multi-Chip Generalization Report",
        "",
        "## 1. Executive Summary & Provenance",
        "",
        f"- **Parser Identity**: `{report['parser_identity']}`",
        f"- **Simulator Identity**: `{report['sim_identity'] or 'unconfirmed'}`",
        f"- **All chip predictions verified against the current simulator**: `{report['sim_identity_matches_current']}`",
        f"- **Evaluation Relation**: `{prov['evaluation_relation']}` "
        f"(`target_timing_used_to_fit={prov['target_timing_used_to_fit']}`, "
        f"`heldout_observed_values_used_in_fit={prov['heldout_observed_values_used_in_fit']}`, "
        f"`observed_spans_untrimmed={prov['observed_spans_untrimmed']}`, "
        f"`input_conditioned_regime_overrides_by_hw={json.dumps(prov['input_conditioned_regime_overrides_by_hw'])}`)",
        f"- **Calibration Scope**: {prov['calibration_scope']}",
        f"- **Total Wave 5 Golden Profiles (`kernel_details.csv`)**: **`{inv['total_csvs']}`** across **`{inv['cohort_phase_count']}`** cohort-phase pairs (`A2={inv['a2_csvs']}`, `A3={inv['a3_csvs']}`, `A5={inv['a5_csvs']}`)",
        "",
        "| Scope | Captures | Pass `<= 15%` | Rate `<= 15%` | Pass `<= 10%` | Rate `<= 10%` | Mean `|Err|` | Median `|Err|` | Max `|Err|` |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    rows = [
        ("**All Wave 5 Captures (`A2 + A3 + A5`)**", s["wave5_all"]),
        ("A2 (`Ascend910B4`, Single-Die 910B)", s["by_hardware"]["a2_ascend910b4"]),
        ("A3 (`Ascend910_9392`, Dual-Die 910C)", s["by_hardware"]["a3_ascend910_9392"]),
        ("A5 (`Ascend910_9599`, Ascend 950DT)", s["by_hardware"]["a5_ascend910_9599"]),
        ("All Decode Captures (`4K..400K`)", s["by_phase"]["decode"]),
        ("All Prefill Captures (`4K..400K`)", s["by_phase"]["prefill"]),
        ("Ultra-Long Context (`192K..400K` Subset)", s["ultra_long_192k_to_400k"]),
        ("Real Ultra-Long Checkpoints (`4K..400K`)", s["by_track"]["ultra_long_context_real_checkpoints"]),
        ("Real Reduced-Expert Checkpoints (`E=64..128, L=3..48`)", s["by_track"]["reduced_expert_real_checkpoints"]),
        ("Synthetic Reduced-Expert MoE (`L=8, E=16..64, K=2..8`)", s["by_track"]["synthetic_moe_l8"]),
    ]
    for label, st in rows:
        lines.append(
            f"| {label} | {st['count']} | {st['pass_15pct']} | **{st['pass_rate_15pct']*100:.2f}%** | "
            f"{st['pass_10pct']} | **{st['pass_rate_10pct']*100:.2f}%** | {st['mean_abs_error']*100:.2f}% | "
            f"{st['median_abs_error']*100:.2f}% | {st['max_abs_error']*100:.2f}% |"
        )

    lines.extend([
        "",
        f"## 2. Cohort-Phase Breakdown (`{inv['cohort_phase_count']}` Cohort-Phase Pairs Across A2, A3, and A5)",
        "",
        "| HW | Cohort | Family | Phase | TP/DP/EP | L/E/K | Spec | Compared | Pass `<= 10%` | Mean `|Err|` | Median `|Err|` | Max `|Err|` |",
        "| :---: | :--- | :--- | :---: | :---: | :---: | :---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for c in report["cohort_summaries"]:
        st = c["stats"]
        lek = f"{c.get('num_layers') or '-'}/{c.get('num_experts') or 0}/{c.get('top_k') or 0}"
        p10 = f"{st['pass_10pct']}/{st['count']} ({st['pass_rate_10pct']*100:.1f}%)" if st.get("count") else "N/A"
        lines.append(
            f"| `{c['hw'].upper()}` | `{c['cohort']}` | `{c['family']}` | `{c['phase']}` | "
            f"`{c['tp']}/{c['dp']}/{c['ep']}` | `{lek}` | `{c.get('spec_tokens', 0)}` | "
            f"{c['compared_count']} | {p10} | {st.get('mean_abs_error', 0)*100:.2f}% | "
            f"{st.get('median_abs_error', 0)*100:.2f}% | {st.get('max_abs_error', 0)*100:.2f}% |"
        )
    return "\n".join(lines) + "\n"


def _capture_traits(hw, csv_path):
    module = importlib.import_module(f"eval_{hw}_wave5")
    return {**module._unadapted_parse_capture_traits(csv_path), "capture_path": str(csv_path)}


def _capture_paths(hw, module):
    root = (getattr(module, "WAVE5_A3_ROOT", None)
            or getattr(module, "A2_WAVE5_ROOT", None)
            or getattr(module, "DATA_ROOT", None))
    if root is None:
        raise ValueError(f"wave5_capture_root_missing:{hw}")
    return sorted(path.resolve() for path in Path(root).rglob("kernel_details.csv")
                  if path.exists())


def _scoped_prefill_capture_worker(item):
    """Prepare one capture once and price every retained prefill geometry."""
    (hw, path_str, traits, tpl_name, template, seg_opts, _cross_tp) = item
    module = importlib.import_module(f"eval_{hw}_wave5")
    slim = module.extract_or_load(Path(path_str), traits, template, seg_opts)
    observed = slim.get("observed") or {}
    cache_key = slim.get("cache_key")
    if not observed.get("forwards") or not cache_key:
        return path_str, {"status": "not_applicable",
                          "reason": "no_retained_prefill_forwards"}
    expected = {"cache_version": slim.get("cache_version"),
                "parser_identity": module.PARSER_IDENTITY,
                "cache_key": cache_key}
    full_path = Path(module.CACHE_ROOT) / f"{cache_key}.json"
    full_observed, _evidence = load_verified_extraction(
        full_path, capture_path=path_str, expected=expected)
    if full_observed is not None:
        prepared = prepare_scoped_replay(
            template, capture_path=path_str, observation=full_observed,
            requested_context=traits.get("context_tokens"),
            archive_template=True, extract_missing=False,
            max_rows=5_000_000, timeout_s=60.0)
        source_observed = full_observed
    else:
        prepared = prepare_scoped_replay(
            template, capture_path=path_str, extraction_path=full_path,
            expected_extraction=expected,
            requested_context=traits.get("context_tokens"),
            archive_template=True, extract_missing=True,
            max_rows=5_000_000, timeout_s=60.0)
        source_observed = observed
    prefill_forwards = [
        forward for forward in (source_observed.get("forwards") or [])
        if forward.get("phase") in (None, "prefill")]
    computed = prefill_geometries(
        {"forwards": prefill_forwards}, traits["context_tokens"],
        context_offset=prepared.context_offset)
    prepared_index = {
        (int(row["tokens"]), int(row["context"])): row
        for row in prepared.geometries()
        if row.get("phase") == "prefill"
        and row.get("tokens") == row.get("query_rows")}
    ordered = []
    for geometry in computed:
        key = (int(geometry["tokens"]), int(geometry["context"]))
        row = prepared_index.get(key)
        if row is None:
            prepared.release()
            raise ValueError(f"wave5_scoped_geometry_not_prepared:{key}")
        ordered.append(row)
    slim_forwards = observed.get("forwards") or []
    if len(slim_forwards) != len(ordered):
        prepared.release()
        raise ValueError("wave5_scoped_forward_partition_mismatch:"
                         f"{len(slim_forwards)}!={len(ordered)}")
    score_forwards = []
    for index, (slim_forward, geometry) in enumerate(
            zip(slim_forwards, ordered)):
        if int(slim_forward["query_rows"]) != int(geometry["query_rows"]):
            prepared.release()
            raise ValueError("wave5_scoped_forward_partition_mismatch:"
                             "query_rows")
        explicit_phase = slim_forward.get("phase")
        if (explicit_phase is not None
                and explicit_phase != geometry.get("phase")):
            prepared.release()
            raise ValueError("wave5_scoped_explicit_phase_mismatch:"
                             f"{index}:{explicit_phase}!="
                             f"{geometry.get('phase')}")
        explicit_sequences = slim_forward.get("sequences")
        if (explicit_sequences is not None
                and int(explicit_sequences) != int(geometry["sequences"])):
            prepared.release()
            raise ValueError("wave5_scoped_explicit_sequences_mismatch:"
                             f"{index}:{explicit_sequences}!="
                             f"{geometry['sequences']}")
        explicit_contexts = [
            int(slim_forward[name]) for name in ("context", "context_tokens")
            if slim_forward.get(name) is not None]
        if explicit_contexts and any(
                value != int(geometry["context"])
                for value in explicit_contexts):
            prepared.release()
            raise ValueError("wave5_scoped_explicit_context_mismatch:"
                             f"{index}:{explicit_contexts}!="
                             f"{int(geometry['context'])}")
        if "span_ms" not in (slim_forward.get("body") or {}):
            prepared.release()
            raise ValueError("wave5_scoped_observed_span_missing")
        score_forwards.append({
            "query_rows": int(geometry["query_rows"]),
            "context": int(geometry["context"]),
            "body": {"span_ms": slim_forward["body"]["span_ms"]},
        })
    observed_for_score = {
        "body_span_sum_ms": observed.get("body_span_sum_ms"),
        "forwards": score_forwards,
    }
    tpl_sig = sha256(json.dumps(template, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    if not any(row.get("status") == "ok" for row in ordered):
        sidecar = [{"geometry": {"phase": "prefill",
                                 "tokens": int(geometry["tokens"]),
                                 "context": int(geometry["context"]),
                                 "sequences": 1},
                    "status": "unbound",
                    "scope_status": geometry.get("status"),
                    "scope_reason": geometry.get("reason"),
                    "native_status": "deferred_to_baseline"}
                   for geometry in ordered]
        prepared.release()
        return path_str, {"status": "unbound", "tpl_sig": tpl_sig,
                          "observed": observed_for_score,
                          "context_offset": prepared.context_offset,
                          "signatures": [], "provenance": sidecar}
    prefix = "wave5_v1" if hw == "a5" else "v2"
    signatures, sidecar = [], []
    try:
        for geometry in ordered:
            tokens, context = int(geometry["tokens"]), int(geometry["context"])
            base_id = sha256(
                f"{prefix}:{SIM_IDENTITY}:{tpl_sig}:prefill:"
                f"{tokens}:{context}:1".encode("utf-8")).hexdigest()[:24]
            base_path = Path(module.CACHE_ROOT) / f"pred_{base_id}.json"
            if not base_path.exists():
                base = module.predict_body(
                    template, phase="prefill", tokens=tokens,
                    context=context, sequences=1)
                base.pop("parameters", None)
                base.pop("scheduled_operator_summary", None)
                module._atomic_write_json(base_path, base)
            declared, provenance = prepared.apply(
                template, phase="prefill", tokens=tokens, context=context,
                sequences=1)
            key = prediction_identity(
                declared, phase="prefill", tokens=tokens, context=context,
                sequences=1, sim_identity=SIM_IDENTITY,
                native_identity=NATIVE_OBSERVATION_IDENTITY)
            price_declared_prediction(
                key, declared, phase="prefill", tokens=tokens,
                context=context, sequences=1, cache_root=module.CACHE_ROOT,
                writer=module._atomic_write_json)
            signatures.append({"tokens": tokens, "context": context,
                               "key": key})
            sidecar.append(compact_scope_sidecar(provenance))
    finally:
        prepared.release()
    return path_str, {"status": "scoped", "observed": observed_for_score,
                      "tpl_sig": tpl_sig, "signatures": signatures,
                      "context_offset": prepared.context_offset,
                      "provenance": sidecar}


def _scoped_evaluate(module, csv_path, traits, tpl_name, tpl, cross_tp,
                     extracted, pred_cache, tpl_sig):
    """Return a pre-materialised per-geometry capture result when supplied."""
    key = str(Path(csv_path).resolve())
    result = getattr(module, "_scoped_results", {}).get(key)
    if result is not None:
        return deepcopy(result)
    return module._unadapted_evaluate_heldout_capture(
        csv_path, traits, tpl_name, tpl, cross_tp, extracted, pred_cache,
        tpl_sig)


def _scoped_evaluate_capture(module, csv_path, traits, tpl_name, tpl,
                             extracted, pred_cache, tpl_sig):
    """A5 archived entry point: return a pre-materialised scoped result."""
    key = str(Path(csv_path).resolve())
    result = getattr(module, "_scoped_results", {}).get(key)
    if result is not None:
        return deepcopy(result)
    return module._unadapted_evaluate_capture(
        csv_path, traits, tpl_name, tpl, extracted, pred_cache, tpl_sig)


def _materialize_scoped_prefill(module, hw, workers):
    """Run the maintained per-capture driver before the archived main loop."""
    module._scoped_capture_imports = {}
    module._scoped_results = {}
    if hw == "a2":
        module._scoped_capture_imports["_chip"] = {
            "status": "not_applicable",
            "reason": "scoped_adapter_supports_a3_a5_only"}
        return
    tasks = []
    for path in _capture_paths(hw, module):
        traits = module.parse_capture_traits(path)
        if traits.get("phase") != "prefill":
            continue
        resolved = list(module._unadapted_resolve_template(traits))
        if resolved[1] is None:
            continue
        template, policy = import_capture_policy(
            resolved[1], capture_path=path)
        module._capture_policy_imports[str(path)] = policy
        seg_opts = resolved[2] if len(resolved) > 2 else {}
        cross_tp = resolved[3] if len(resolved) > 3 else False
        tasks.append((hw, str(path), traits, resolved[0], template, seg_opts,
                      cross_tp))
    if not tasks:
        return
    results = module._run_bounded_pool(
        _scoped_prefill_capture_worker, tasks, workers,
        step_timeout_s=900.0, progress_step=10, label="Scoped prefill")
    for path, payload in results.items():
        module._scoped_capture_imports[path] = {
            "status": payload.get("status"),
            "reason": payload.get("reason"),
            "tpl_sig": payload.get("tpl_sig"),
            "geometries": len(payload.get("provenance") or []),
            "status_counts": _status_counts(payload.get("provenance") or []),
            "scope_reasons": sorted({
                row.get("scope_reason")
                for row in (payload.get("provenance") or [])
                if row.get("scope_reason")}),
        }
        if payload.get("status") != "scoped":
            continue
        applied = any(row.get("status") in {"applied", "applied_scope_only"}
                      for row in payload["provenance"])
        module._scoped_capture_imports[path]["capture_replaced"] = applied
        if not applied:
            continue
        signatures = payload["signatures"]
        observed = payload["observed"]
        task = next(item for item in tasks if item[1] == path)
        pred_cache = load_scoped_predictions(
            {"signatures": signatures}, module.CACHE_ROOT)
        result = score_prefill_capture(
            Path(path), task[2], task[3], task[6],
            {"observed": observed, "meta": {}}, pred_cache, "scoped",
            scope_plan={"signatures": signatures,
                        "provenance": payload["provenance"],
                        "context_offset": payload.get("context_offset", 0)})
        result["scoped_native_replay"]["capture_replaced"] = True
        module._scoped_results[path] = result


def _status_counts(provenance):
    counts = {}
    for row in provenance:
        status = row.get("status") or "unknown"
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _resolve_capture_template(hw, traits):
    module = importlib.import_module(f"eval_{hw}_wave5")
    resolved = list(module._unadapted_resolve_template(traits))
    path = traits.get("capture_path")
    if resolved[1] is not None and path:
        resolved[1], provenance = import_capture_policy(resolved[1], capture_path=path)
    else:
        provenance = {"status": "not_provided", "reason": "capture_path_or_template_not_provided"}
    module._capture_policy_imports[path or traits.get("cell", "unspecified")] = provenance
    return tuple(resolved)


def _configure_chip(hw: str, archive_root: Path, cache_root: Path, sim_identity: str,
                    observation_identity: str = NATIVE_OBSERVATION_IDENTITY):
    """Apply the same explicit inputs to the parent and every spawned worker."""
    script = archive_root / hw / f"eval_{hw}_wave5.py"
    struct_str, module_dir = str(STRUCT_DIR), str(script.parent)
    for helper in ("body", "decode", "prefill"):
        importlib.import_module(helper)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
    previous_bytecode_setting = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        module = importlib.import_module(script.stem)
    finally:
        sys.dont_write_bytecode = previous_bytecode_setting
        sys.path[:] = [
            struct_str,
            *(p for p in sys.path if p != struct_str and Path(p).parts[-2:] != ("examples", "structure")),
        ]
    module.STRUCT_DIR = STRUCT_DIR
    if Path(module.__file__).resolve() != script.resolve():
        raise ValueError(f"chip_evaluator_module_conflict:{script}")
    if SIM_IDENTITY != sim_identity:
        raise ValueError(f"chip_worker_sim_identity_mismatch:{SIM_IDENTITY}!={sim_identity}")
    if NATIVE_OBSERVATION_IDENTITY != observation_identity:
        raise ValueError("chip_worker_native_observation_identity_mismatch")
    module.SIM_IDENTITY = sim_identity
    module.CACHE_ROOT = cache_root / f"native-{observation_identity}"
    module.predict_body = native_predict_body
    provenance = None
    if hw == "a2":
        # The archived A2 evaluator also emits derived templates during main().
        module.TEMPLATES_DIR = cache_root / "templates"
    elif hw == "a3":
        module._REGIME_CATALOG, provenance = import_a3_regime_catalog(archive_root)
        module._COHORT_TEMPLATES = {
            path.name: json.loads(path.read_text(encoding="utf-8"))
            for path in (archive_root / "a3" / "templates").glob("a3__*.json")
        }
    if not hasattr(module, "_unadapted_resolve_template"):
        module._unadapted_resolve_template = module.resolve_template
        module._unadapted_parse_capture_traits = module.parse_capture_traits
    module._capture_policy_imports = {}
    module._scoped_capture_imports = {}
    module._scoped_results = {}
    if hasattr(module, "evaluate_heldout_capture"):
        if not hasattr(module, "_unadapted_evaluate_heldout_capture"):
            module._unadapted_evaluate_heldout_capture = module.evaluate_heldout_capture
        module.evaluate_heldout_capture = partial(_scoped_evaluate, module)
    if hasattr(module, "evaluate_capture"):
        if not hasattr(module, "_unadapted_evaluate_capture"):
            module._unadapted_evaluate_capture = module.evaluate_capture
        module.evaluate_capture = partial(_scoped_evaluate_capture, module)
    module.parse_capture_traits = partial(_capture_traits, hw)
    module.resolve_template = partial(_resolve_capture_template, hw)
    module.ProcessPoolExecutor = partial(
        ProcessPoolExecutor, mp_context=multiprocessing.get_context("spawn"),
        initializer=_configure_chip,
        initargs=(hw, archive_root, cache_root, sim_identity, observation_identity),
    )
    return module, provenance


def _run_chip(hw: str, archive_root: Path, output_json: Path, output_md: Path, workers: int) -> int:
    cache_root = output_json.parent / f"{output_json.stem}-cache"
    for path in (output_json, output_md, cache_root):
        if path.resolve().is_relative_to(archive_root.resolve()):
            raise ValueError(f"wave5_output_must_be_outside_archive:{path}")
    module, regime_import = _configure_chip(hw, archive_root, cache_root, SIM_IDENTITY)
    _materialize_scoped_prefill(module, hw, workers)
    result = module.main([
        "--workers", str(workers), "--output-json", str(output_json), "--output-md", str(output_md),
    ])
    if result:
        return result
    report = json.loads(output_json.read_text(encoding="utf-8"))
    script = archive_root / hw / f"eval_{hw}_wave5.py"
    report["input_provenance"] = {
        "evaluator": {"path": str(script), "sha256": sha256(script.read_bytes()).hexdigest()},
        "sim_identity": SIM_IDENTITY,
        "native_observation_identity": NATIVE_OBSERVATION_IDENTITY,
        "prediction_arm": "observed_native",
        "cache_root": str(module.CACHE_ROOT),
        "cache_policy": "separate_output_directory_with_parser_sim_and_native_observation_identities",
        "archive_extraction_cache_reused": False,
        "regime_catalog_import": regime_import,
        "capture_policy_imports": getattr(module, "_capture_policy_imports", {}),
        "scoped_native_replay_imports": getattr(module, "_scoped_capture_imports", {}),
        "scoped_native_replay_results": len(getattr(module, "_scoped_results", {})),
        "scoped_native_replay_policy": {
            "order": "capture_scoped_caller_then_per_geometry_native_observations",
            "scope_applied_to": "per_geometry_final_raw",
            "scope_declaration_identity": "per_geometry_not_promoted_to_capture",
            "prepared_state": "one_capture_reused_per_geometry_released_after_materialization",
            "scope_plan_validation": "exact_forward_count_and_every_geometry",
            "archive_template_replacement": True,
            "reason": "archived Wave 5 templates inherit tp_join_reduce and are "
                      "not the caller evidence; only the retained capture window selects it",
        },
    }
    _atomic_write_json(output_json, report)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--rerun-chips", action="store_true")
    parser.add_argument("--run-chip", choices=("a2", "a3", "a5"), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    workers = _bounded_workers(args.workers)
    archive_root = args.archive_root.resolve()
    started = time.monotonic()
    if args.run_chip:
        return _run_chip(args.run_chip, archive_root, args.output_json, args.output_md, workers)

    reports_root = archive_root
    if args.rerun_chips:
        reports_root = args.output_json.parent / f"{args.output_json.stem}-chips"
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, (str(STRUCT_DIR), os.environ.get("PYTHONPATH"))))}
        for hw in ("a2", "a3", "a5"):
            cmd = [sys.executable, str(Path(__file__).resolve()), "--run-chip", hw, "--archive-root", str(archive_root),
                   "--workers", str(workers), "--output-json", str(reports_root / f"{hw}_wave5_eval.json"),
                   "--output-md", str(reports_root / f"{hw}_wave5_eval.md")]
            subprocess.run(cmd, env=env, check=True, timeout=CHIP_TIMEOUT_SECONDS,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    a2_report, a3_report, a5_report = (
        json.loads((reports_root / f"{hw}_wave5_eval.json").read_text(encoding="utf-8")) for hw in ("a2", "a3", "a5"))
    report = aggregate_chip_reports(a2_report, a3_report, a5_report)
    report["elapsed_seconds"] = round(time.monotonic() - started, 2)
    _atomic_write_json(args.output_json, report)
    _atomic_write_text(args.output_md, render_markdown(report))
    s = report["summary"]["wave5_all"]
    print(f"Wave 5 Full Generalization: {s['pass_10pct']}/{s['count']} ({s['pass_rate_10pct']*100:.2f}%) <= 10%, "
          f"mean={s['mean_abs_error']*100:.2f}%, median={s['median_abs_error']*100:.2f}%, max={s['max_abs_error']*100:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
