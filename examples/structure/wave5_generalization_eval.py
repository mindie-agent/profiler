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
[Timeouts & Locks] Subprocess chip runs use bounded worker pools (<= 4 workers,
  default 3) and explicit timeouts; outputs use atomic tempfile + os.replace().
[Side-Effect Policy] Writes wave5_full_generalization.{json,md}; does not mutate
  cases.json, cases/*.json, or dsh_generalization_eval.py.
"""
from __future__ import annotations

from collections import defaultdict
import argparse
from hashlib import sha256
import json
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

STRUCT_DIR = Path(__file__).resolve().parent
DEFAULT_ARCHIVE_ROOT = Path("/Volumes/data/mindie-sim-data/acceptance-archives-20261030/wave5-eval")
DEFAULT_OUT_JSON = STRUCT_DIR / "results" / "wave5_full_generalization.json"
DEFAULT_OUT_MD = STRUCT_DIR / "results" / "wave5_full_generalization.md"
MAX_WORKERS = 4

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
    sim_root = Path(mindie_sim.__file__).resolve().parent
    ver = getattr(mindie_sim, "__version__", "0.8.2")
    digest = sha256(ver.encode("utf-8"))
    for name in ("execution.py", "service_regimes.py", "structure.py", "attention_prefill.py"):
        mod_path = sim_root / "prediction" / name
        if mod_path.exists():
            digest.update(mod_path.read_bytes())
    return f"mindie_sim/{ver}:{digest.hexdigest()[:16]}"


PARSER_IDENTITY = _parser_identity()
SIM_IDENTITY = _sim_identity()


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
            "sim_identity": rep.get("sim_identity", SIM_IDENTITY),
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
    return {
        "schema_version": "mindie-wave5-full-generalization/1",
        "parser_identity": PARSER_IDENTITY,
        "sim_identity": SIM_IDENTITY,
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
        f"- **Simulator Identity**: `{report['sim_identity']}`",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--rerun-chips", action="store_true")
    args = parser.parse_args(argv)

    workers = _bounded_workers(args.workers)
    archive_root = args.archive_root.resolve()
    started = time.monotonic()

    if args.rerun_chips:
        env = {**os.environ, "PYTHONPATH": str(STRUCT_DIR)}
        for hw in ("a2", "a3", "a5"):
            script = archive_root / hw / f"eval_{hw}_wave5.py"
            subprocess.run([sys.executable, str(script), "--workers", str(workers)], env=env, check=True, timeout=600)

    a2_report = json.loads((archive_root / "a2_wave5_eval.json").read_text(encoding="utf-8"))
    a3_report = json.loads((archive_root / "a3_wave5_eval.json").read_text(encoding="utf-8"))
    a5_report = json.loads((archive_root / "a5_wave5_eval.json").read_text(encoding="utf-8"))

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
