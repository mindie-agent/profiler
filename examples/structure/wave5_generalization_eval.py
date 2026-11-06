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

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
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
    "input_conditioned_regime_overrides_by_hw": {
        "a2": False,
        "a3": True,
        "a5": False,
    },
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


def _parser_identity() -> str:
    prof_root = Path(decode_segmentation.__file__).resolve().parent
    digest = sha256(PARSER_VERSION.encode("utf-8"))
    for mod_path in (
        prof_root / "decode_segmentation.py",
        prof_root / "communication_bounds.py",
        prof_root / "events.py",
        STRUCT_DIR / "prefill.py",
    ):
        if mod_path.exists():
            digest.update(mod_path.read_bytes())
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
        return {
            "count": 0, "pass_15pct": 0, "pass_10pct": 0,
            "pass_rate_15pct": 0.0, "pass_rate_10pct": 0.0,
            "mean_abs_error": 0.0, "median_abs_error": 0.0, "max_abs_error": 0.0,
        }
    abs_errs = [abs(float(e)) for e in errors]
    n = len(abs_errs)
    p15 = sum(1 for e in abs_errs if e <= 0.15)
    p10 = sum(1 for e in abs_errs if e <= 0.10)
    return {
        "count": n,
        "pass_15pct": p15,
        "pass_10pct": p10,
        "pass_rate_15pct": round(p15 / n, 4),
        "pass_rate_10pct": round(p10 / n, 4),
        "mean_abs_error": round(sum(abs_errs) / n, 4),
        "median_abs_error": round(median(abs_errs), 4),
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
        "path": raw.get("path"),
        "hw": hw,
        "cohort": cohort,
        "cell": tr.get("cell"),
        "family": tr.get("family"),
        "phase": phase,
        "tp": tr.get("tp"),
        "dp": tr.get("dp", 1),
        "ep": tr.get("ep", 1),
        "num_layers": num_layers,
        "num_experts": tr.get("num_experts"),
        "top_k": tr.get("top_k"),
        "spec_tokens": tr.get("spec_tokens", 0),
        "context_tokens": tr.get("context_tokens"),
        "concurrency": tr.get("concurrency"),
        "template": raw.get("template"),
        "status": raw.get("status"),
        "forward_count": raw.get("forward_count"),
        "observed_ms": raw.get("observed_ms"),
        "predicted_ms": raw.get("predicted_ms"),
        "relative_error": raw.get("relative_error"),
        "passed_15pct": bool(raw.get("passed_15pct")),
        "passed_10pct": bool(raw.get("passed_10pct")),
    }
    rec["track"] = _classify_track(rec)
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
    module_dir = str(script.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
    previous_bytecode_setting = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        module = importlib.import_module(script.stem)
    finally:
        sys.dont_write_bytecode = previous_bytecode_setting
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
            subprocess.run([
                sys.executable, str(Path(__file__).resolve()), "--run-chip", hw,
                "--archive-root", str(archive_root), "--workers", str(workers),
                "--output-json", str(reports_root / f"{hw}_wave5_eval.json"),
                "--output-md", str(reports_root / f"{hw}_wave5_eval.md"),
            ], env=env, check=True, timeout=CHIP_TIMEOUT_SECONDS,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    a2_report = json.loads((reports_root / "a2_wave5_eval.json").read_text(encoding="utf-8"))
    a3_report = json.loads((reports_root / "a3_wave5_eval.json").read_text(encoding="utf-8"))
    a5_report = json.loads((reports_root / "a5_wave5_eval.json").read_text(encoding="utf-8"))

    report = aggregate_chip_reports(a2_report, a3_report, a5_report)
    report["elapsed_seconds"] = round(time.monotonic() - started, 2)
    _atomic_write_json(args.output_json, report)
    _atomic_write_text(args.output_md, render_markdown(report))
    s = report["summary"]["wave5_all"]
    print(
        f"Wave 5 Full Generalization: {s['pass_10pct']}/{s['count']} ({s['pass_rate_10pct']*100:.2f}%) <= 10%, "
        f"mean={s['mean_abs_error']*100:.2f}%, median={s['median_abs_error']*100:.2f}%, max={s['max_abs_error']*100:.2f}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
