"""Per-launch client TTFT forecast from blind declarations and actual model source.

[Role]
  Turn P8 producer-declared launch ordinals (base/mixed Q, seeds, shared/fresh,
  max_tokens, chunk budget) plus B's actual compiled model/source body into one
  forecast per ordinal.  H2's FCFS/round-robin chunked-prefill recipe provides
  ordinal finishes; observed TTFT is joined only after the forecast is frozen.

[Invariants]
  * Forecast inputs are P8 declarations and validated model/source/topology.
    No observed TTFT, stream chunk timing, e2e, ITL or cell aggregate enters.
  * Body price is B's actual single-chunk `predict_chunk(spec, q, kv_end)`
    primitive on the same model/source: query tokens plus explicit absolute
    context end, matching H2's `body_one(chunk, kv_context)` contract.  No
    whole-request prefix difference or F(total)-F(prev) subtraction is used.
  * H2 returns original launch-order finishes.  Scheduling is labelled as the
    declared FCFS/round-robin model condition, never as an observed vLLM
    scheduler.
  * Host/transport overhead is not synthesized.  If no independent value is
    supplied it is 0 ms with `host_overhead_status="absent_assumed_zero"`; the
    forecast is still published and is not called measured TTFT.
  * Actual values are joined only by `evaluate_cell`; missing outcomes stay
    visible as null actual/error and never change the forecast.

[Timeouts & Locks] Pure local arithmetic and bounded model reads; per-cell
  chunk/body caches are O(active requests/chunks) and local to one call.

[Side-Effect Policy] Read-only.  No network, NPU, subprocess, Git or writes.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

P9_SCHEMA = "mindie-profiler-request-ttft-prediction/1"
P12_SCHEMA = "mindie-profiler-request-ttft-view/1"
DEFAULT_HOST_OVERHEAD_MS = 0.0


def _int(value: Any) -> int | None:
    try:
        out = int(value)
    except (TypeError, ValueError):
        return None
    return out


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number >= 0.0 else None


def _declarations(row: Mapping[str, Any], *, roots: Sequence[Path | str] | None = None,
                  declarations: Sequence[Any] | None = None) -> list[Any]:
    if declarations is not None:
        return list(declarations)
    from zero_shot_client_capture import client_capture
    capture = client_capture(row, roots=roots)
    return list(capture.declarations)


def _spec(row: Mapping[str, Any]) -> Any:
    import zero_shot_piecewise_validation as zsv
    return zsv.cell_from_dict(row).spec


def _prefill_spec(spec: Any, kv_end: int) -> Any:
    return replace(spec, phase="prefill", prompt_tokens=int(kv_end),
                   concurrency=1, max_tokens=1, sequences_per_replica=1,
                   tokens_per_sequence=0)


def _chunk_body(spec: Any, q_len: int, kv_end: int) -> float:
    """Actual single-chunk body (q, context_before/end); never a prefix difference."""
    from zero_shot_chunk_pricing import predict_chunk
    prediction = predict_chunk(_prefill_spec(spec, kv_end), int(q_len), int(kv_end),
                               sequences=1)
    body = _finite(getattr(prediction, "prefill_body_ms", None))
    if body is None or body <= 0.0:
        raise RuntimeError("chunk_body_source_unavailable")
    return body


def _own_body(spec: Any, prompt: int, budget: int,
              body_one: Any) -> float:
    """Sum actual causal chunk bodies for one request under the declared budget."""
    done = 0
    total = 0.0
    budget = max(1, int(budget))
    prompt = max(1, int(prompt))
    while done < prompt:
        take = min(budget, prompt - done)
        done += take
        total += body_one(take, done)
    return total


def _expected_key(cell_id: str, ordinal: int, started: Any, concurrency: int,
                  prompt: int, max_tokens: Any, mix_class: Any, rack: Any) -> str:
    return (f"{cell_id}|ordinal={ordinal}|ctx={started}|C={concurrency}|"
            f"p={prompt}|o={max_tokens}|mix={mix_class}|rack={rack}")


def _declaration_view(item: Any) -> dict[str, Any]:
    if isinstance(item, Mapping):
        return dict(item)
    if hasattr(item, "as_dict"):
        out = dict(item.as_dict())
        if not out.get("key"):
            out["key"] = getattr(item, "key", None)
        return out
    return {
        "ordinal": getattr(item, "ordinal", None),
        "prompt_tokens": getattr(item, "prompt_tokens", None),
        "shared_tokens": getattr(item, "shared_tokens", None),
        "fresh_tokens": getattr(item, "fresh_tokens", None),
        "prompt_seed": getattr(item, "prompt_seed", None),
        "request_seed": getattr(item, "request_seed", None),
        "mix_class": getattr(item, "mix_class", None),
        "mix_index": getattr(item, "mix_index", None),
        "max_tokens": getattr(item, "max_tokens", None),
        "chunk_budget": getattr(item, "chunk_budget", None),
        "key": getattr(item, "key", None),
    }


def _canonical_declarations(identity: Any) -> list[dict[str, Any]]:
    items = []
    for declaration in sorted(identity.declarations, key=lambda item: item.ordinal):
        item = dict(declaration.as_dict())
        item["key"] = declaration.key
        item["ordinal"] = declaration.ordinal
        items.append(item)
    return items


def _normalize_declarations(identity: Any, declarations: Sequence[Any] | None,
                            row: Mapping[str, Any]) -> tuple[list[dict[str, Any]] | None,
                                                            str | None, tuple[str, ...]]:
    canonical = _canonical_declarations(identity)
    if not canonical:
        return None, "declarations_absent", ()
    if declarations is None:
        declarations = canonical
    parsed: dict[int, dict[str, Any]] = {}
    for raw in declarations:
        item = _declaration_view(raw)
        ordinal = item.get("ordinal")
        if ordinal is None and item.get("key"):
            import re
            match = re.search(r"\|ordinal=(\d+)\|", str(item["key"]))
            ordinal = int(match.group(1)) if match else None
        if ordinal is None or not isinstance(ordinal, int) or ordinal < 0:
            return None, "declaration_ordinal_missing", ()
        if ordinal in parsed:
            return None, "declaration_ordinal_mismatch", ()
        parsed[ordinal] = item
    if sorted(parsed) != list(range(len(canonical))):
        return None, "declaration_ordinal_mismatch", ()
    normalized: list[dict[str, Any]] = []
    counterfactual: set[str] = set()
    budgets: set[int] = set()
    for ordinal, src in enumerate(canonical):
        inp = parsed[ordinal]
        conditions = inp.get("conditions") if isinstance(inp.get("conditions"), Mapping) else {}
        conditions = {**src.get("conditions", {}), **conditions}
        key = inp.get("key") or src.get("key")
        prompt = inp.get("prompt_tokens", src.get("prompt_tokens"))
        max_tokens = inp.get("max_tokens", src.get("max_tokens"))
        rack = inp.get("rack", src.get("rack"))
        producer = inp.get("producer", src.get("producer"))
        if inp.get("cell_id", src.get("cell_id")) != src.get("cell_id"):
            return None, "declaration_cell_mismatch", ()
        if inp.get("ordinal", ordinal) != ordinal:
            return None, "declaration_ordinal_mismatch", ()
        if rack != src.get("rack"):
            return None, "declaration_rack_mismatch", ()
        if producer not in (None, src.get("producer")):
            return None, "declaration_producer_mismatch", ()
        if conditions.get("started") != src.get("conditions", {}).get("started"):
            return None, "declaration_clock_mismatch", ()
        if conditions.get("ttft_boundary") != src.get("conditions", {}).get("ttft_boundary"):
            return None, "declaration_boundary_mismatch", ()
        if str(inp.get("phase", src.get("phase"))) != str(src.get("phase")):
            return None, "declaration_phase_mismatch", ()
        expected = _expected_key(src.get("cell_id"), ordinal, conditions.get("started"),
                                 len(canonical), prompt, max_tokens,
                                 inp.get("mix_class", src.get("mix_class")), rack)
        if key != expected:
            return None, "declaration_key_mismatch", ()
        budget = inp.get("chunk_budget", src.get("chunk_budget"))
        budget_int = int(budget) if budget is not None else None
        if budget_int:
            budgets.add(budget_int)
        for field in ("prompt_tokens", "max_tokens", "shared_tokens", "fresh_tokens",
                      "mix_class", "mix_index", "mix_count", "chunk_budget"):
            if field in inp and inp.get(field) != src.get(field):
                counterfactual.add(field)
        merged = {**src, **inp, "key": key, "ordinal": ordinal,
                  "conditions": conditions, "rack": rack,
                  "producer": producer, "chunk_budget": budget}
        normalized.append(merged)
    if len(budgets) > 1:
        return None, "declaration_budget_inconsistent", ()
    # A top-level row declaration that disagrees with the retained source cannot
    # be graded against that source, even if its child declarations are clean.
    for field in ("prompt_tokens", "concurrency", "max_tokens", "phase"):
        if field in row and row.get(field) is not None:
            source_value = canonical[0].get(field)
            if source_value is not None and str(row.get(field)) != str(source_value):
                return None, f"row_{field}_mismatch", ()
    return normalized, None, tuple(sorted(counterfactual))


def source_declarations(row: Mapping[str, Any], *,
                       roots: Sequence[Path | str] | None = None
                       ) -> list[dict[str, Any]]:
    """Authoritative P8 declaration mappings including ClientDeclaration.key."""
    from zero_shot_client_capture import client_capture
    return _canonical_declarations(client_capture(row, roots=roots))


def forecast_view(row: Mapping[str, Any], *,
                  roots: Sequence[Path | str] | None = None
                  ) -> dict[str, Any]:
    """CG5-facing view preserving key/actual; no dropped semantic key."""
    evaluated = evaluate_cell(row, roots=roots)
    return {
        "schema": P12_SCHEMA,
        "cell": evaluated.get("cell", {}),
        "requests": [
            {key: item.get(key) for key in (
                "key", "semantic_key", "semantic_key_status", "ordinal",
                "launch_ordinal", "prompt_tokens", "chunk_budget",
                "predicted_ms", "actual_ms", "signed_error", "unsigned_error",
                "join_status", "grade_eligible", "diagnostic_eligible",
                "counterfactual_fields", "score_scope", "scenario",
                "scheduler_condition", "model_condition", "admission",
                "conditions", "producer", "rack")}
            for item in evaluated.get("requests", [])
        ],
        "summary": evaluated.get("summary", {}),
        "status": evaluated.get("status"),
        "reason": evaluated.get("reason"),
    }


def forecast_cell(row: Mapping[str, Any], *,
                  declarations: Sequence[Any] | None = None,
                  roots: Sequence[Path | str] | None = None,
                  host_overhead_ms: float = DEFAULT_HOST_OVERHEAD_MS,
                  scheduler: str = "h2_legacy",
                  max_num_seqs: int | None = None,
                  arrival_order: Sequence[int] | None = None
                  ) -> dict[str, Any]:
    """Blind forecast only.  Return one row per producer-declared ordinal."""
    cell_id = str(row.get("cell_id") or "")
    from zero_shot_client_capture import client_capture
    identity = client_capture(row, roots=roots)
    declared, normalize_error, counterfactual_fields = _normalize_declarations(
        identity, declarations, row)
    base = {"schema": P9_SCHEMA, "cell_id": cell_id, "status": "unavailable",
            "reason": None, "requests": [], "cell": {}, "summary": {}}
    if normalize_error:
        return {**base, "reason": normalize_error}
    if not declared:
        return {**base, "reason": "declarations_absent"}
    try:
        spec = _spec(row)
    except Exception as exc:  # model/source parsing only; no measurement
        return {**base, "reason": f"spec_unavailable:{type(exc).__name__}:{exc}"}
    if getattr(spec, "source_reject_reason", ""):
        return {**base, "reason": f"source_rejected:{spec.source_reject_reason}"}
    if getattr(spec, "model_case", None) is None or not Path(spec.model_case).is_file():
        return {**base, "reason": "model_source_absent"}
    try:
        chunk_budget = next((int(item["chunk_budget"]) for item in declared
                             if item.get("chunk_budget")), None)
        if not chunk_budget:
            import zero_shot_piecewise_validation as zsv
            chunk_budget = zsv._max_batched_tokens(spec) or 8192
        prompts = [max(1, int(item.get("prompt_tokens") or 0)) for item in declared]
        if any(item.get("prompt_tokens") is None for item in declared):
            return {**base, "reason": "declaration_prompt_absent"}
        h3_meta: dict[str, Any] = {}
        h3_requests: dict[int, Any] = {}
        h3_own: dict[int, float] = defaultdict(float)
        h3_steps = 0
        h3_batch_calls: list[int] = []
        if scheduler in {"h3_open", "h3"}:
            try:
                from mindie_sim.prediction.piecewise.open_prefill_scheduler import (
                    chunked_prefill_open_scheduler_ttft_ms,
                )
                from zero_shot_chunk_pricing import predict_chunk_batch
            except ImportError as exc:
                return {**base, "reason": f"h3_or_kb_adapter_unavailable:{exc}"}
            configured_seqs = max_num_seqs
            if configured_seqs is None:
                configured_seqs = _int(identity.launch_declaration.get(
                    "server_max_num_seqs"))
            if not configured_seqs or configured_seqs <= 0:
                return {**base, "reason": "max_num_seqs_source_absent"}

            def body_batch(requests: Sequence[Mapping[str, Any]]) -> float:
                h3_batch_calls.append(len(requests))
                priced = predict_chunk_batch(spec, list(requests), sequences=1)
                for key, value in (priced.get("per_request_ms") or {}).items():
                    if isinstance(key, int):
                        h3_own[key] += float(value)
                return float(priced["total_ms"])

            result = chunked_prefill_open_scheduler_ttft_ms(
                prompts, dp=max(1, int(spec.dp)),
                max_batched_tokens=int(chunk_budget),
                max_num_seqs=int(configured_seqs),
                arrival_order=arrival_order, body_batch=body_batch,
                max_tokens=[max(1, int(item.get("max_tokens") or 1))
                            for item in declared],
                scheduler="vllm_v0_27_open_fcfs")
            finishes = tuple(float(item) for item in result)
            mean_finish = float(result.mean_ttft_ms)
            h3_meta = dict(result.metadata)
            h3_steps = len(result.steps)
            h3_requests = {item.ordinal: item for item in result.requests}
        elif scheduler == "h2_legacy":
            from mindie_sim.prediction.piecewise.service_span import (
                chunked_prefill_request_ttft_ms,
            )
            from mindie_sim.prediction.piecewise.service_span import (
                chunked_prefill_mean_ttft_ms,
            )
            cache: dict[tuple[int, int], float] = {}

            def body_one(chunk: int, kv_context: int) -> float:
                key = (int(chunk), int(kv_context))
                if key not in cache:
                    cache[key] = _chunk_body(spec, key[0], key[1])
                return cache[key]

            finishes = chunked_prefill_request_ttft_ms(
                prompts, dp=max(1, int(spec.dp)), max_batched_tokens=int(chunk_budget),
                body_one=body_one)
            mean_finish = chunked_prefill_mean_ttft_ms(
                prompts, dp=max(1, int(spec.dp)), max_batched_tokens=int(chunk_budget),
                body_one=body_one)
        else:
            return {**base, "reason": f"scheduler_condition_unsupported:{scheduler}"}
    except Exception as exc:
        return {**base, "reason": f"body_or_schedule_unavailable:{type(exc).__name__}:{exc}"}
    overhead = _finite(host_overhead_ms)
    if overhead is None:
        return {**base, "reason": "host_overhead_invalid"}
    host_status = "absent_assumed_zero" if overhead == 0.0 else "declared"
    counterfactual_fields = list(counterfactual_fields)
    if overhead != 0.0:
        counterfactual_fields.append("host_overhead_ms")
    grade_eligible = not bool(counterfactual_fields)
    scenario = ("original" if not counterfactual_fields else
                "host_overhead_scenario" if counterfactual_fields == ["host_overhead_ms"]
                else "physical_counterfactual")
    rows = []
    is_h3 = bool(h3_meta)
    for ordinal, (item, prompt, finish) in enumerate(zip(declared, prompts, finishes)):
        if is_h3:
            own_body = float(h3_own.get(ordinal, 0.0))
            queue = max(0.0, float(finish) - own_body)
            request_result = h3_requests.get(ordinal)
            rank = int(getattr(request_result, "rank", ordinal % max(1, int(spec.dp))))
            prior_on_rank = max(0, len(getattr(request_result, "batches", ()) or ()) - 1)
        else:
            own_body = _own_body(spec, prompt, int(chunk_budget), body_one)
            queue = max(0.0, float(finish) - own_body)
            rank = ordinal % max(1, int(spec.dp))
            prior_on_rank = sum(1 for earlier in range(ordinal) if earlier % max(1, int(spec.dp)) == rank)
        predicted = float(finish) + overhead
        diagnostic_eligible = is_h3 and not bool(counterfactual_fields) and overhead == 0.0
        row_grade = grade_eligible and not is_h3
        row_scenario = ("conditional_batch_model" if is_h3 and overhead == 0.0 else
                        "conditional_batch_model_with_host_scenario" if is_h3 else
                        scenario)
        rows.append({
            "key": item.get("key") or f"{cell_id}|ordinal={ordinal}",
            "semantic_key": item.get("key"),
            "semantic_key_status": "verified",
            "cell_id": cell_id, "phase": spec.phase,
            "concurrency": len(declared),
            "rack": item.get("rack"), "producer": item.get("producer"),
            "producer_sha256": identity.producer.get("producer_sha256"),
            "source_row_sha256": identity.original_row_sha256,
            "conditions": dict(item.get("conditions") or {}),
            "ordinal": ordinal, "launch_ordinal": ordinal,
            "absolute_finish_ms": (float(getattr(request_result, "finish_ms", finish))
                                   if is_h3 else None),
            "termination_condition": (h3_meta.get("termination_condition") if is_h3 else None),
            "route_condition": (h3_meta.get("route_condition") if is_h3 else None),
            "arrival_condition": (h3_meta.get("arrival_condition") if is_h3 else None),
            "prompt_tokens": prompt,
            "shared_tokens": item.get("shared_tokens"),
            "fresh_tokens": item.get("fresh_tokens"),
            "mix_class": item.get("mix_class"), "mix_index": item.get("mix_index"),
            "prompt_seed": item.get("prompt_seed"), "request_seed": item.get("request_seed"),
            "max_tokens": item.get("max_tokens"),
            "chunk_budget": int(chunk_budget),
            "dp": int(spec.dp), "tp": int(spec.tp), "ep": int(spec.ep), "pp": int(spec.pp),
            "rank_assignment": rank, "rank_queue_index": prior_on_rank,
            "own_body_ms": own_body, "queue_wait_ms": queue,
            "device_queue_finish_ms": float(finish),
            "host_overhead_ms": overhead, "host_overhead_status": host_status,
            "host_overhead_grade_eligible": overhead == 0.0,
            "predicted_ms": predicted,
            "grade_eligible": row_grade,
            "diagnostic_eligible": diagnostic_eligible,
            "counterfactual_fields": counterfactual_fields,
            "scenario": row_scenario,
            "score_scope": ("conditional_batch_model" if is_h3 else "original"),
            "prediction_boundary": "client_send_to_first_sse",
            "device_boundary": "chunked_prefill_fcfs_device_queue",
            "boundary_status": "assumed_zero_host_transport" if overhead == 0.0 else "declared_host_overhead",
            "scheduler_condition": (h3_meta.get("scheduler") if is_h3 else
                                    "round_robin_fcfs_model"),
            "model_condition": bool(is_h3),
            "admission": dict(h3_meta.get("admission") or {}) if is_h3 else {},
            "batch_condition": (h3_meta.get("max_num_seqs_condition") if is_h3 else
                                "per_rank_serial_fcfs; no concurrent batching assumed"),
            "actual_scheduler_observed": False,
            "source": ("P8_blind_declaration+KB_predict_chunk_batch+H3_open_fcfs"
                       if is_h3 else
                       "P8_blind_declaration+B_predict_cell+H2_ordinal_recipe"),
            "trained_vs_blind": "blind",
            "actual_ms": None, "signed_error": None, "unsigned_error": None,
        })
    mean_pred = sum(item["predicted_ms"] for item in rows) / max(1, len(rows))
    return {
        "schema": P9_SCHEMA, "cell_id": cell_id, "status": "forecast",
        "reason": None,
        "cell": {
            "cell_id": cell_id, "phase": spec.phase,
            "model_label": spec.model_label, "model_case": str(spec.model_case),
            "source_config_sha256": spec.source_config_sha256,
            "source_deploy_sha256": spec.source_deploy_sha256,
            "dp": int(spec.dp), "tp": int(spec.tp), "ep": int(spec.ep), "pp": int(spec.pp),
            "chunk_budget": int(chunk_budget), "chunk_budget_source": "declaration" if any(
                item.get("chunk_budget") for item in declared) else "case_model",
            "declared_ordinals": len(rows),
            "scheduling_model": ("vllm_v1_open_fcfs_model_condition" if is_h3
                                 else "round_robin_fcfs"),
            "scheduler_condition": (h3_meta.get("scheduler") if is_h3 else
                                    "model_condition_not_observed_vllm_scheduler"),
            "model_condition": bool(is_h3),
            "admission": dict(h3_meta.get("admission") or {}) if is_h3 else {},
            "h3_steps": h3_steps,
            "h3_body_calls": list(h3_batch_calls),
            "absolute_finishes_ms": (list(h3_meta.get("absolute_finishes_ms") or ())
                                     if is_h3 else None),
            "termination_condition": (h3_meta.get("termination_condition") if is_h3 else None),
            "declared_max_tokens": [item.get("max_tokens") for item in declared],
            "declared_min_tokens": None,
            "stop_conditions": [],
            "route_condition": (h3_meta.get("route_condition") if is_h3 else None),
            "arrival_condition": (h3_meta.get("arrival_condition") if is_h3 else None),
            "source_vllm_version_observed": (h3_meta.get("source_vllm_version_observed")
                                             if is_h3 else None),
            "source_vllm_version_read": (h3_meta.get("source_vllm_version_read")
                                         if is_h3 else None),
            "actual_scheduler_observed": False,
            "batch_condition": (h3_meta.get("max_num_seqs_condition") if is_h3 else
                                "per_rank_serial_fcfs; no concurrent batching assumed"),
            "client_boundary": next((item.get("conditions", {}).get("ttft_boundary")
                                     for item in declared
                                     if isinstance(item.get("conditions"), Mapping)), None),
            "host_overhead_ms": overhead, "host_overhead_status": host_status,
            "host_overhead_grade_eligible": overhead == 0.0,
            "target_boundary": "client_send_to_first_sse",
            "rack": next((item.get("rack") for item in declared if item.get("rack")), None),
            "producer_sha256": identity.producer.get("producer_sha256"),
            "source_row_sha256": identity.original_row_sha256,
            "identity_started": identity.started,
            "producer_boundary": identity.producer.get("ttft_boundary"),
            "mean_finish_ms": mean_finish,
            "mean_forecast_ms": mean_pred,
            "grade_eligible": bool(grade_eligible and not is_h3),
            "diagnostic_eligible": bool(is_h3 and not counterfactual_fields
                                        and overhead == 0.0),
            "score_scope": ("conditional_batch_model" if is_h3 else "original"),
            "counterfactual_fields": counterfactual_fields,
            "scenario": ("conditional_batch_model" if is_h3 else scenario),
        },
        "summary": {
            "declared": len(rows), "observed": 0, "missing": len(rows),
            "mean_forecast_ms": mean_pred, "mean_device_queue_finish_ms": mean_finish,
            "mean_preserved": abs(mean_finish - mean_pred) <= 1e-9,
            "host_overhead_status": host_status,
            "host_overhead_grade_eligible": overhead == 0.0,
            "grade_eligible": bool(grade_eligible and not is_h3),
            "diagnostic_eligible": bool(is_h3 and not counterfactual_fields
                                        and overhead == 0.0),
            "score_scope": ("conditional_batch_model" if is_h3 else "original"),
            "scenario": ("conditional_batch_model" if is_h3 else scenario),
        },
        "requests": rows,
    }


def evaluate_cell(row: Mapping[str, Any], *,
                  declarations: Sequence[Any] | None = None,
                  roots: Sequence[Path | str] | None = None,
                  host_overhead_ms: float = DEFAULT_HOST_OVERHEAD_MS,
                  scheduler: str = "h2_legacy",
                  max_num_seqs: int | None = None,
                  arrival_order: Sequence[int] | None = None
                  ) -> dict[str, Any]:
    """Freeze forecast first, then join observed ordinal TTFT for evaluation."""
    forecast = forecast_cell(row, declarations=declarations, roots=roots,
                             host_overhead_ms=host_overhead_ms, scheduler=scheduler,
                             max_num_seqs=max_num_seqs, arrival_order=arrival_order)
    if forecast.get("status") != "forecast":
        return forecast
    from zero_shot_client_capture import client_capture
    capture = client_capture(row, roots=roots)
    identity_ok = (capture.producer.get("producer_sha256")
                   == forecast["cell"].get("producer_sha256")
                   and capture.original_row_sha256
                   == forecast["cell"].get("source_row_sha256"))
    actual = {item.key: item for item in capture.requests
              if item.ttft_s is not None}
    requests = []
    for item in forecast["requests"]:
        observed_item = actual.get(item.get("semantic_key"))
        join_status = "no_observed"
        observed = None
        if not identity_ok:
            join_status = "identity_mismatch"
        elif not item.get("grade_eligible", True) and not item.get("diagnostic_eligible", False):
            join_status = "counterfactual_no_grade"
        elif observed_item is not None:
            key_ok = (observed_item.key == item.get("semantic_key")
                      and observed_item.launch_ordinal == item.get("launch_ordinal")
                      and observed_item.capture_context.get("started")
                      == (item.get("conditions") or {}).get("started")
                      and observed_item.producer == item.get("producer")
                      and observed_item.rack == item.get("rack"))
            if key_ok:
                observed = observed_item.ttft_s * 1000.0
                join_status = ("conditional_model_diagnostic"
                               if item.get("score_scope") == "conditional_batch_model"
                               else "exact_key_identity_ordinal_clock")
            else:
                join_status = "key_or_identity_mismatch"
        signed = None if observed is None else (item["predicted_ms"] - observed) / observed if observed > 0 else None
        requests.append({**item, "actual_ms": observed, "signed_error": signed,
                         "unsigned_error": None if signed is None else abs(signed),
                         "join_status": join_status})
    observed_rows = [item for item in requests if item["actual_ms"] is not None]
    forecast["requests"] = requests
    forecast["summary"] = {
        **forecast["summary"],
        "observed": len(observed_rows), "missing": len(requests) - len(observed_rows),
        "mean_actual_ms": (sum(item["actual_ms"] for item in observed_rows) /
                           len(observed_rows) if observed_rows else None),
        "mean_unsigned_error": (sum(item["unsigned_error"] for item in observed_rows) /
                                len(observed_rows) if observed_rows else None),
        "max_unsigned_error": (max(item["unsigned_error"] for item in observed_rows)
                               if observed_rows else None),
        "joined": len(observed_rows),
        "strict_graded": sum(1 for item in observed_rows
                             if item["join_status"] == "exact_key_identity_ordinal_clock"),
        "diagnostic_observed": sum(1 for item in observed_rows
                                   if item["join_status"] == "conditional_model_diagnostic"),
        "score_scope": forecast["cell"].get("score_scope", "original"),
        "join_mismatches": sum(1 for item in requests
                               if item["join_status"] in {
                                   "identity_mismatch", "key_or_identity_mismatch"}),
        "trained_vs_blind": "blind forecast; actuals joined after freeze",
    }
    return forecast


def iter_forecasts(rows: Iterable[Mapping[str, Any]], *,
                   roots: Sequence[Path | str] | None = None,
                   evaluate: bool = False) -> Iterable[dict[str, Any]]:
    for row in rows:
        yield (evaluate_cell if evaluate else forecast_cell)(row, roots=roots)


__all__ = ["P9_SCHEMA", "P12_SCHEMA", "source_declarations", "forecast_view",
           "forecast_cell", "evaluate_cell", "iter_forecasts"]


def _main() -> int:
    import argparse
    import json
    from pathlib import Path as _Path
    parser = argparse.ArgumentParser(description="P14/P15 per-launch TTFT forecast")
    parser.add_argument("--cell-id", required=True)
    parser.add_argument("--rows", default="/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl")
    parser.add_argument("--scheduler", default="h2_legacy",
                        choices=("h2_legacy", "h3_open"))
    parser.add_argument("--max-num-seqs", type=int, default=None)
    parser.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    row = next(item for item in map(json.loads, _Path(args.rows).open())
               if item.get("cell_id") == args.cell_id)
    fn = evaluate_cell if args.evaluate else forecast_cell
    result = fn(row, scheduler=args.scheduler, max_num_seqs=args.max_num_seqs)
    print(json.dumps(result, indent=1, default=str))
    return 0 if result.get("status") == "forecast" else 1


if __name__ == "__main__":
    raise SystemExit(_main())
