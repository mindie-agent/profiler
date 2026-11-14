"""Per-capture prefill scope materialisation for the maintained DSH evaluator.

[Role] Prepare one capture's caller evidence once, apply capture-scoped caller
  then native observations for every retained forward, price each final raw
  under its own identity, and score the same observation partition unchanged.
[Invariants] One prepared scope per capture; explicit scope plans must match the
  observed forward count and every geometry exactly. Predictions are keyed by
  final physical raw, geometry, simulator identity and native identity, never
  by capture path or observation timing.
[Timeouts & Locks] One bounded capture scan per prepared capture; pricing reuses
  the caller's bounded pool. No locks or device work.
[Side-Effect Policy] Read-only capture and cache access; writes only the
  caller-selected prediction cache.
"""
from __future__ import annotations

from collections import defaultdict
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from statistics import median
import time

from runtime_identity import prediction_report_identity
from service_response_acceptance import evaluate_acceptance
from scoped_native_replay import (
    compact_scope_sidecar,
    is_a5_machine,
    prefill_geometries,
    prepare_scoped_replay,
    price_declared_prediction,
    prediction_identity,
    read_prediction_cache,
    resolve_context_offset,
    validate_scope_plan,
)


@dataclass(frozen=True)
class ScopedPrefillJob:
    """One capture's scope evidence and exact observed forward partition."""
    path: str
    template: dict
    extraction_path: str
    expected_extraction: dict
    requested_context: int
    geometries: tuple
    sim_identity: str
    native_identity: str
    cache_root: str
    context_offset: int


def scoped_prefill_worker(job):
    """Prepare one capture once, apply C then B per geometry, price final raws."""
    prepared = prepare_scoped_replay(
        job.template, capture_path=job.path,
        extraction_path=job.extraction_path,
        expected_extraction=job.expected_extraction,
        requested_context=job.requested_context,
        context_offset=job.context_offset, extract_missing=False)
    signatures, sidecar = [], []
    try:
        for geometry in job.geometries:
            tokens, context = int(geometry["tokens"]), int(geometry["context"])
            declared, provenance = prepared.apply(
                job.template, phase="prefill", tokens=tokens, context=context,
                sequences=1)
            key = prediction_identity(
                declared, phase="prefill", tokens=tokens, context=context,
                sequences=1, sim_identity=job.sim_identity,
                native_identity=job.native_identity)
            price_declared_prediction(
                key, declared, phase="prefill", tokens=tokens, context=context,
                sequences=1, cache_root=job.cache_root)
            signatures.append({"tokens": tokens, "context": context,
                               "key": key})
            sidecar.append(compact_scope_sidecar(provenance))
    finally:
        prepared.release()
    return job.path, {"signatures": signatures, "provenance": sidecar,
                      "context_offset": job.context_offset,
                      "geometries": [
                          {"tokens": int(row["tokens"]),
                           "context": int(row["context"])}
                          for row in job.geometries]}


def materialize_scoped_jobs(*, heldout_tasks, extractions, workers,
                            sim_identity, native_identity, cache_root,
                            run_pool):
    """Build and run scoped prefill jobs; return unscoped jobs and predictions.

    This is the actual DSH scheduling branch. The per-capture job carries the
    exact observed geometries (including an inferred A5 offset), so progress
    accounting and worker dispatch use named fields rather than tuple indexes.
    """
    scoped_jobs, unscoped = [], {}
    for p, tr, _, tpl, _, _, tpl_sig in heldout_tasks:
        if tpl is None or tr.get("phase") != "prefill":
            continue
        extracted = extractions[str(p)]
        observed = extracted["observed"]
        offset, _basis = resolve_context_offset(
            observed, requested_context=tr["context_tokens"],
            hardware_a5=is_a5_machine(tpl))
        geometries = prefill_geometries(
            observed, tr["context_tokens"], context_offset=offset)
        expected = {
            "cache_version": extracted.get("cache_version"),
            "parser_identity": extracted.get("parser_identity"),
            "cache_key": extracted.get("cache_key"),
        }
        full_cache_path = extracted.get("full_cache_path")
        if geometries and full_cache_path and all(expected.values()):
            scoped_jobs.append(ScopedPrefillJob(
                path=str(p), template=tpl, extraction_path=full_cache_path,
                expected_extraction=expected,
                requested_context=int(tr["context_tokens"]),
                geometries=tuple(geometries), sim_identity=sim_identity,
                native_identity=native_identity, cache_root=str(cache_root),
                context_offset=offset))
            continue
        for geometry in geometries:
            unscoped[(tpl_sig, "prefill", geometry["tokens"],
                      geometry["context"], 1)] = tpl
    if scoped_jobs:
        print(f"Running {len(scoped_jobs)} scoped prefill captures "
              f"({sum(len(job.geometries) for job in scoped_jobs)} geometries) "
              f"across {workers} workers...", flush=True)
    results = (run_pool(scoped_prefill_worker, scoped_jobs, workers)
               if scoped_jobs else {})
    pred_cache = {}
    for plan in results.values():
        pred_cache.update(load_scoped_predictions(plan, cache_root))
    return unscoped, results, pred_cache


def load_scoped_predictions(plan, cache_root):
    """Load every materialised final-raw prediction; absence is an error."""
    predictions = {}
    for signature in plan.get("signatures") or []:
        key = signature["key"]
        cached = read_prediction_cache(key, cache_root)
        if cached is None:
            raise RuntimeError(f"scoped_prediction_missing:{key}")
        predictions[(key, "prefill", int(signature["tokens"]),
                     int(signature["context"]), 1)] = cached
    return predictions


def score_prefill_capture(csv_path, traits, tpl_name, cross_tp, extracted,
                          pred_cache, tpl_sig, scope_plan=None):
    """Score the unchanged prefill partition against per-geometry predictions."""
    obs = extracted["observed"]
    forwards = obs.get("forwards", [])
    if not forwards:
        return {"path": str(csv_path), "traits": traits, "template": tpl_name,
                "cross_tp_transfer": cross_tp, "status": "unresolved",
                "reason": "no_prefill_forwards"}
    offset = int((scope_plan or {}).get("context_offset", 0))
    geometries = prefill_geometries(
        obs, traits["context_tokens"], context_offset=offset)
    signatures = validate_scope_plan(
        scope_plan, geometries=geometries, forward_count=len(forwards))
    if signatures is not None:
        provenance = scope_plan.get("provenance")
        if not isinstance(provenance, list) or len(provenance) != len(forwards):
            raise ValueError("scoped_plan_provenance_count_mismatch")
        for index, (row, geometry) in enumerate(zip(provenance, geometries)):
            if (row.get("geometry", {}).get("tokens") != geometry["tokens"]
                    or row.get("geometry", {}).get("context") != geometry["context"]):
                raise ValueError(f"scoped_plan_provenance_geometry_mismatch:{index}")
    real_sum, pred_sum, steady_real, steady_pred = float(obs["body_span_sum_ms"]), 0.0, 0.0, 0.0
    ordered_parts = []
    for index, (forward, geometry) in enumerate(zip(forwards, geometries)):
        q_rows, context = geometry["tokens"], geometry["context"]
        key = signatures[index]["key"] if signatures is not None else tpl_sig
        predicted = pred_cache[(key, "prefill", q_rows, context, 1)][
            "body_forward_span_ms"]
        observed = float(forward["body"]["span_ms"])
        pred_sum += float(predicted)
        ordered_parts.append({"observed_ms": observed, "predicted_ms": float(predicted),
                              "count": 1, "id": f"prefill:{index}"})
        if q_rows >= 1024:
            steady_real += observed
            steady_pred += float(predicted)
    complete_err = (pred_sum / real_sum - 1.0) if real_sum > 0 else None
    steady_err = (steady_pred / steady_real - 1.0) if steady_real > 0 else complete_err
    result = {
        "path": str(csv_path), "traits": traits, "template": tpl_name,
        "cross_tp_transfer": cross_tp, "status": "compared",
        "forward_count": len(forwards), "observed_ms": round(real_sum, 4),
        "predicted_ms": round(pred_sum, 4),
        "relative_error": round(complete_err, 6) if complete_err is not None else None,
        "complete_body_relative_error": round(complete_err, 6) if complete_err is not None else None,
        "steady_chunk_observed_ms": round(steady_real, 4) if steady_real > 0 else None,
        "steady_chunk_predicted_ms": round(steady_pred, 4) if steady_pred > 0 else None,
        "steady_chunk_relative_error": round(steady_err, 6) if steady_err is not None else None,
        "passed_15pct": bool(abs(complete_err) <= 0.15) if complete_err is not None else False,
        "passed_10pct": bool(abs(complete_err) <= 0.10) if complete_err is not None else False,
        "steady_chunk_passed_15pct": bool(abs(steady_err) <= 0.15) if steady_err is not None else False,
        "steady_chunk_passed_10pct": bool(abs(steady_err) <= 0.10) if steady_err is not None else False,
        "ordered_parts": ordered_parts,
        "uncancelled_acceptance": evaluate_acceptance(
            ordered_parts, tolerance=0.10, label=str(csv_path)),
    }
    if signatures is not None:
        counts = {}
        for row in scope_plan["provenance"]:
            status = row.get("status") or "unknown"
            counts[status] = counts.get(status, 0) + 1
        result["scoped_native_replay"] = {
            "status_counts": dict(sorted(counts.items())),
            "geometries": scope_plan["provenance"],
        }
    return result


def price_legacy_prediction(item, *, predict_fn, sim_identity,
                            native_identity, cache_root, writer):
    """Retain the original unscoped prediction cache contract.

    Kept separate from final-raw identity so legacy decode/absent-scope jobs
    still reuse exactly the historical cache shape.
    """
    key, template = item
    tpl_sig, phase, tokens, context, sequences = key
    pred_id = sha256(
        f"v3:{sim_identity}:{native_identity}:{tpl_sig}:{phase}:"
        f"{tokens}:{context}:{sequences}".encode("utf-8")).hexdigest()[:24]
    cache_path = Path(cache_root) / f"pred_{pred_id}.json"
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
        except TimeoutError:
            raise
        except json.JSONDecodeError as exc:
            cache_path.unlink(missing_ok=True)
            raise RuntimeError(f"corrupt_prediction_cache:{cache_path}") from exc
        except OSError as exc:
            raise RuntimeError(f"unreadable_prediction_cache:{cache_path}") from exc
        if cached.get("status") == "modeled":
            return key, cached
    result = predict_fn(template, tokens=int(tokens), context=int(context),
                        sequences=int(sequences), phase=phase)
    result.pop("parameters", None)
    result.pop("scheduled_operator_summary", None)
    writer(cache_path, result)
    return key, result


def unpadded_scenarios(row_dummy, obs, tpl, automatic_scenarios):
    """Keep the maintained physical/output row split used by decode scoring."""
    scenarios = (automatic_scenarios(row_dummy, obs, tpl)
                 if obs.get("geometry_groups") else [])
    for scenario in scenarios:
        geometry = scenario["geometry"]
        out_q = geometry.get("output_query_rows")
        rows = geometry.get("query_rows", 0)
        tokens = geometry.get("tokens_per_sequence", 1)
        if out_q and tokens > 1 and out_q < rows and out_q % tokens == 0:
            geometry.update(physical_query_rows=rows, query_rows=out_q,
                            sequences_per_replica=out_q // tokens)
    return scenarios


def summarize_errors(errors: list[float]) -> dict:
    if not errors:
        return {"count": 0, "pass_15pct": 0, "pass_10pct": 0, "pass_rate_15pct": 0.0, "pass_rate_10pct": 0.0}
    abs_errs = [abs(e) for e in errors]
    p15, p10, n = sum(e <= 0.15 for e in abs_errs), sum(e <= 0.10 for e in abs_errs), len(errors)
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


def assemble_dsh_report(
    *,
    elapsed_seconds: float,
    decode_sb: dict,
    prefill_sb: dict,
    sim_identity: str,
    native_identity: str,
    registered_recomputations: dict,
    scoped_results: dict,
    all_dsh_csvs: list,
    registered_in_dsh: list,
    eager_excluded: list,
    heldout_tasks: list,
    reg_decode_errs: list[float],
    reg_prefill_errs: list[float],
    heldout_results: list[dict],
) -> dict:
    by_cohort: dict[str, list[dict]] = defaultdict(list)
    for row in heldout_results:
        by_cohort[row["traits"]["cohort"]].append(row)
    cohort_summaries = []
    for cohort_key, items in sorted(by_cohort.items()):
        errs = [x["relative_error"] for x in items if x.get("relative_error") is not None]
        tr0 = items[0]["traits"]
        cohort_summaries.append({
            "cohort": cohort_key, "hw": tr0["hw"], "family": tr0["family"], "phase": tr0["phase"],
            "tp": tr0["tp"], "dp": tr0["dp"], "ep": tr0["ep"], "spec_tokens": tr0["spec_tokens"],
            "template": items[0]["template"], "cross_tp_transfer": items[0]["cross_tp_transfer"],
            "capture_count": len(items), "compared_count": len(errs), "stats": summarize_errors(errs),
        })
    heldout_errs = [r["relative_error"] for r in heldout_results if r.get("relative_error") is not None]
    heldout_prim_errs = [
        r.get("primary_relative_error", r["relative_error"])
        for r in heldout_results if r.get("relative_error") is not None
    ]
    heldout_non_dspark0 = [
        r["relative_error"] for r in heldout_results
        if r.get("relative_error") is not None
        and not (r["traits"]["family"] == "deepseek-v4.1" and r["traits"]["spec_tokens"] == 0)
    ]
    all_fleet_errs = reg_decode_errs + reg_prefill_errs + heldout_errs
    scoped_status = defaultdict(int)
    scoped_geometries = 0
    for plan in scoped_results.values():
        for row in plan["provenance"]:
            scoped_status[row.get("status") or "unknown"] += 1
            scoped_geometries += 1
    return {
        "schema_version": "mindie-dsh-full-generalization/2",
        "elapsed_seconds": round(elapsed_seconds, 2),
        **prediction_report_identity(
            {"registered_decode": decode_sb, "registered_prefill": prefill_sb, "dsh_predictions": {"sim_identity": sim_identity}},
            sim_identity,
        ),
        "registered_recomputations": registered_recomputations,
        "dsh_native_observation_identity": native_identity,
        "dsh_prediction_arm": "observed_native",
        "dsh_scoped_native_replay": {
            "captures": len(scoped_results),
            "geometries": scoped_geometries,
            "status_counts": dict(sorted(scoped_status.items())),
            "order": "capture_scoped_caller_before_native_observations",
            "archive_template_replacement": False,
            "prediction_identity": "final_physical_raw_plus_geometry_plus_sim_and_native_identity",
            "prepared_state": "one_capture_reused_per_geometry_released_after_jobs_materialized",
        },
        "calibration_provenance": {
            "evaluation_relation": "historical_model_conditioned_regimes_not_certified_heldout",
            "independent_heldout": False,
            "input_conditioned_regime_overrides": True,
            "prior_fit_capture_membership": "not_established",
            "registered_comparisons": "retained_source_reports_except_explicit_missing_case_recomputations",
        },
        "inventory": {
            "dsh_20261030_total_csvs": len(all_dsh_csvs),
            "dsh_20261030_registered_body_csvs": len(registered_in_dsh),
            "dsh_20261030_eager_excluded_csvs": len(eager_excluded),
            "dsh_20261030_unregistered_heldout_csvs": len(heldout_tasks),
            "registered_decode_body_cases": len(reg_decode_errs),
            "registered_prefill_compared_cases": len(reg_prefill_errs),
            "total_evaluated_body_cases": len(reg_decode_errs) + len(reg_prefill_errs) + len(heldout_tasks),
        },
        "summary": {
            "registered_decode_body": summarize_errors(reg_decode_errs),
            "registered_prefill_body": summarize_errors(reg_prefill_errs),
            "heldout_unregistered_all": summarize_errors(heldout_errs),
            "heldout_unregistered_primary_population": summarize_errors(heldout_prim_errs),
            "heldout_unregistered_excluding_v41_dspark0_uncalibrated_sp1": summarize_errors(heldout_non_dspark0),
            "full_fleet_combined": summarize_errors(all_fleet_errs),
        },
        "cohort_summaries": cohort_summaries,
        "eager_excluded": eager_excluded,
        "heldout_cases": heldout_results,
    }


def write_dsh_markdown(report: dict, out_md: Path) -> None:
    inv, s = report["inventory"], report["summary"]
    lines = [
        "# MindIE-Sim Full-Fleet DSH Historical-Template Replay Report", "",
        "Existing template regimes are not certified independent heldout calibration. Registered scoreboard comparisons retain their source runtime metadata; explicit missing-case recomputations are recorded separately from the new DSH predictions.", "",
        f"- **All contributing runtime identities verified against the current runtime**: `{report['sim_identity_matches_current']}`",
        "## 1. Executive Summary & Fleet Inventory", "",
        f"- **DSH `2026-10-30` Total `kernel_details.csv` Captures**: `{inv['dsh_20261030_total_csvs']}`",
        f"  - **Registered in `cases.json` (`body` scope)**: `{inv['dsh_20261030_registered_body_csvs']}`",
        f"  - **Excluded Pure Decode-Eager Captures**: `{inv['dsh_20261030_eager_excluded_csvs']}`",
        f"  - **Unregistered Captures Evaluated**: `{inv['dsh_20261030_unregistered_heldout_csvs']}` across `{len(report['cohort_summaries'])}` cohorts",
        f"- **Total Evaluated Body Captures (Registered + Unregistered)**: `{inv['total_evaluated_body_cases']}` (`{s['full_fleet_combined']['count']}` compared)", "",
        "| Evaluation Scope | Compared | Pass `<= 15%` | Rate `<= 15%` | Pass `<= 10%` | Rate `<= 10%` | Mean `|Err|` | Median `|Err|` | Max `|Err|` |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, key in [
        ("Registered Decode Body (`cases.json`)", "registered_decode_body"),
        ("Registered Prefill Body (`cases.json`)", "registered_prefill_body"),
        ("Unregistered (Excl. Uncalibrated `v41` `dspark0`)", "heldout_unregistered_excluding_v41_dspark0_uncalibrated_sp1"),
        ("Unregistered (All Compared, All Populations)", "heldout_unregistered_all"),
        ("Unregistered (Primary Population)", "heldout_unregistered_primary_population"),
        ("**Full Fleet Combined**", "full_fleet_combined"),
    ]:
        r = s[key]
        lines.append(
            f"| {label} | {r['count']} | {r['pass_15pct']} | **{r['pass_rate_15pct']*100:.2f}%** | "
            f"{r['pass_10pct']} | **{r['pass_rate_10pct']*100:.2f}%** | {r['mean_abs_error']*100:.2f}% | "
            f"{r['median_abs_error']*100:.2f}% | {r['max_abs_error']*100:.2f}% |"
        )
    lines.extend([
        "", "## 2. Unregistered Cohort Breakdown", "",
        "| Cohort | Family | Phase | TP/DP/EP | Spec | Cross-TP | Template | Captures | Compared | Pass `<=15%` | Pass `<=10%` | Mean `|Err|` | Median `|Err|` |",
        "| :--- | :--- | :--- | :---: | ---: | :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for c in report["cohort_summaries"]:
        st, spec_s = c["stats"], ("-" if c["spec_tokens"] is None else str(c["spec_tokens"]))
        p15 = f"{st['pass_15pct']}/{st['count']} ({st['pass_rate_15pct']*100:.1f}%)" if st["count"] else "N/A"
        p10 = f"{st['pass_10pct']}/{st['count']} ({st['pass_rate_10pct']*100:.1f}%)" if st["count"] else "N/A"
        m_s, md_s = (f"{st['mean_abs_error']*100:.2f}%", f"{st['median_abs_error']*100:.2f}%") if st["count"] else ("N/A", "N/A")
        lines.append(
            f"| `{c['cohort']}` | `{c['family']}` | `{c['phase']}` | `{c['tp']}/{c['dp']}/{c['ep']}` | "
            f"{spec_s} | {'Yes' if c['cross_tp_transfer'] else 'No'} | `{c['template']}` | {c['capture_count']} | "
            f"{c['compared_count']} | {p15} | {p10} | {m_s} | {md_s} |"
        )
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def bounded_workers(requested: int, worker_ram_mb: int = 512) -> int:
    cpu_cap, usable_mb = os.cpu_count() or 1, None
    try:
        import psutil
        usable_mb = max(worker_ram_mb, int(psutil.virtual_memory().available) // (1024 * 1024))
    except ImportError:
        pass
    except TimeoutError:
        raise
    except OSError:
        pass
    if usable_mb is None:
        try:
            pages = os.sysconf("SC_AVPHYS_PAGES")
            if isinstance(pages, int) and pages > 0:
                usable_mb = max(worker_ram_mb, (int(pages) * int(os.sysconf("SC_PAGE_SIZE"))) // (1024 * 1024))
        except TimeoutError:
            raise
        except (AttributeError, OSError, ValueError):
            pass
    return 1 if usable_mb is None else max(1, min(int(requested), cpu_cap, usable_mb // worker_ram_mb, 4))


def run_bounded_pool(
    fn,
    items: list,
    workers: int,
    *,
    step_timeout_s: float = 60.0,
    progress_step: int = 100,
    label: str = "Processed",
) -> dict:
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
            done, _ = (
                wait(set(started_at.keys()), timeout=max(0.0, remaining), return_when=FIRST_COMPLETED)
                if remaining > 0
                else (set(), set())
            )
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
            except TimeoutError:
                raise
            except OSError:
                pass
        pool.shutdown(wait=False, cancel_futures=True)
    return results
