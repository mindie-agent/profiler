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

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

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
