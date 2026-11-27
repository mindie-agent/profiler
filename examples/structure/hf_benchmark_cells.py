"""Example-local zero-shot cell declarations and canonical ``mindie_sim`` pricing.

[Role]
  Own the example-only ``CellSpec`` parser, template workload/parallel projection,
  and canonical ``mindie_sim.predict`` cell helper consumed exclusively by
  ``examples/structure/hf_*`` and ``examples/structure/zero_shot_public_consumer``.
[Invariants]
  No measured field enters ``CellSpec``; simulator failures stay explicit notes
  with ``formal_point=False`` and ``None`` timing fields (never fabricated zeros).
[Timeouts & Locks]
  Bounded local reads and deterministic arithmetic; propagates ``TimeoutError``.
[Side-Effect Policy]
  Read-only; callers own any output files.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping


@dataclass(frozen=True)
class CellSpec:
    """Declared geometry for one retained zero-shot cell (no timing input)."""

    cell_id: str = ""
    dataset: str = ""
    phase: str = "decode"
    model_case: Path | None = None
    model_label: str = ""
    prompt_tokens: int = 1
    concurrency: int = 1
    max_tokens: int = 1
    tp: int = 1
    dp: int = 1
    ep: int = 1
    pp: int = 1
    graph_buckets: tuple[int, ...] = ()
    graph_bucket: int = 0
    notes: tuple[str, ...] = ()
    sequences_per_replica: int = 0
    tokens_per_sequence: int = 0
    synthetic_layers: int = 0
    synthetic_experts: int = 0
    synthetic_topk: int = 0
    source_config: Path | None = None
    source_config_sha256: str = ""
    source_deploy_sha256: str = ""
    source_weight_dir: Path | None = None
    source_case_dir: Path | None = None
    source_header_archive: Path | None = None
    require_source: bool = False
    source_reject_reason: str = ""
    source_file_sha256: str = ""
    source_origin: str = ""
    source_binding: Mapping[str, Any] = field(default_factory=dict, compare=False, repr=False)

    def prediction_key(self) -> tuple:
        payload = {
            "dataset": self.dataset,
            "model_case": str(self.model_case or ""),
            "model_label": self.model_label,
            "phase": self.phase,
            "prompt_tokens": self.prompt_tokens,
            "concurrency": self.concurrency,
            "max_tokens": self.max_tokens,
            "tp": self.tp,
            "dp": self.dp,
            "ep": self.ep,
            "pp": self.pp,
            "graph_buckets": list(self.graph_buckets),
            "graph_bucket": self.graph_bucket,
            "notes": list(self.notes),
            "sequences_per_replica": self.sequences_per_replica,
            "tokens_per_sequence": self.tokens_per_sequence,
            "synthetic_layers": self.synthetic_layers,
            "synthetic_experts": self.synthetic_experts,
            "synthetic_topk": self.synthetic_topk,
            "source_config": str(self.source_config or ""),
            "source_config_sha256": self.source_config_sha256,
            "source_deploy_sha256": self.source_deploy_sha256,
            "source_file_sha256": self.source_file_sha256,
            "source_origin": self.source_origin,
            "structure": structure_fingerprint(self),
        }
        return (
            self.dataset,
            hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest(),
        )


def structure_fingerprint(spec: CellSpec) -> str:
    """Deterministic source/geometry identity for a declared cell."""
    payload = {
        "cell_id": spec.cell_id,
        "phase": spec.phase,
        "model_case": str(spec.model_case or ""),
        "model_label": spec.model_label,
        "prompt_tokens": spec.prompt_tokens,
        "concurrency": spec.concurrency,
        "max_tokens": spec.max_tokens,
        "tp": spec.tp,
        "dp": spec.dp,
        "ep": spec.ep,
        "pp": spec.pp,
        "graph_buckets": list(spec.graph_buckets),
        "graph_bucket": spec.graph_bucket,
        "notes": list(spec.notes),
        "source_config": str(spec.source_config or ""),
        "source_config_sha256": spec.source_config_sha256,
        "source_deploy_sha256": spec.source_deploy_sha256,
        "source_file_sha256": spec.source_file_sha256,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def cell_from_dict(raw: Mapping[str, Any]) -> Any:
    """Parse a retained benchmark row into a declared cell record."""
    record = raw.get("spec") if isinstance(raw.get("spec"), Mapping) else raw
    model_case = record.get("model_case")
    model_case = Path(str(model_case)) if model_case else None
    spec = CellSpec(
        cell_id=str(record.get("cell_id") or ""),
        dataset=str(record.get("dataset") or ""),
        phase=str(record.get("phase") or "decode"),
        model_case=model_case,
        model_label=str(record.get("model_label") or ""),
        prompt_tokens=int(record.get("prompt_tokens") or 1),
        concurrency=int(record.get("concurrency") or 1),
        max_tokens=int(record.get("max_tokens") or 1),
        tp=int(record.get("tp") or 1),
        dp=int(record.get("dp") or 1),
        ep=int(record.get("ep") or 1),
        pp=int(record.get("pp") or 1),
        graph_buckets=tuple(int(item) for item in record.get("graph_buckets") or ()),
        graph_bucket=int(record.get("graph_bucket") or 0),
        notes=tuple(dict.fromkeys(str(item) for item in record.get("notes") or ())),
        sequences_per_replica=int(record.get("sequences_per_replica") or 0),
        tokens_per_sequence=int(record.get("tokens_per_sequence") or 0),
        synthetic_layers=int(record.get("synthetic_layers") or 0),
        synthetic_experts=int(record.get("synthetic_experts") or 0),
        synthetic_topk=int(record.get("synthetic_topk") or 0),
        source_config=Path(str(record["source_config"])) if record.get("source_config") else None,
        source_config_sha256=str(record.get("source_config_sha256") or ""),
        source_deploy_sha256=str(record.get("source_deploy_sha256") or ""),
        source_weight_dir=(
            Path(str(record["source_weight_dir"])) if record.get("source_weight_dir") else None
        ),
        source_case_dir=(
            Path(str(record["source_case_dir"])) if record.get("source_case_dir") else None
        ),
        source_header_archive=(
            Path(str(record["source_header_archive"]))
            if record.get("source_header_archive")
            else None
        ),
        require_source=bool(record.get("require_source")),
        source_reject_reason=str(record.get("source_reject_reason") or ""),
        source_file_sha256=str(record.get("source_file_sha256") or ""),
        source_origin=str(record.get("source_origin") or ""),
    )
    trace = raw.get("trace") if isinstance(raw.get("trace"), Mapping) else None
    return SimpleNamespace(
        spec=spec,
        kernel_paths=(),
        trace=trace,
        success=bool(raw.get("success", True)),
        failure=str(raw.get("failure") or ""),
        ttft_ms=raw.get("ttft_ms"),
        tpot_ms=raw.get("tpot_ms"),
        step_trace_ms=raw.get("step_trace_ms"),
        decode_steps=int(raw.get("decode_steps") or 1),
        trace_quality=str(raw.get("trace_quality") or "ok"),
    )


def raw_case_for_cell(spec: CellSpec) -> dict[str, Any]:
    """Apply one cell's declared workload and parallel geometry to its template."""
    if spec.model_case is None:
        raise ValueError("cell_model_case_missing")
    raw = json.loads(Path(spec.model_case).read_text(encoding="utf-8"))
    runtime = dict(raw.get("runtime") or {})
    parallel = dict(runtime.get("parallel") or {})
    for axis in ("tp", "dp", "ep", "pp"):
        runtime.pop(axis, None)
        parallel[axis] = int(getattr(spec, axis))
    runtime["parallel"] = parallel
    if spec.graph_buckets:
        runtime["graph_buckets"] = list(spec.graph_buckets)
    raw["runtime"] = runtime
    raw["workload"] = {
        "num_requests": int(spec.concurrency),
        "prompt_tokens": int(spec.prompt_tokens),
        "output_tokens": int(spec.max_tokens),
        "arrival_interval_ms": 0,
        "synthetic": True,
    }
    return raw


def _canonical_metric(metrics: Mapping[str, Any], key: str) -> float | None:
    value = metrics.get(key)
    if isinstance(value, Mapping):
        for name in ("p50", "mean", "max"):
            candidate = value.get(name)
            if isinstance(candidate, (int, float)) and math.isfinite(float(candidate)):
                return float(candidate)
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


_PREDICT_EVENT_LIMIT = 2 * 2 * 2


def _finite_nonneg(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        val = float(value)
        if math.isfinite(val) and val >= 0.0:
            return val
    return None


def _iteration_step_ms(
    report: Mapping[str, Any],
    observed_steps: Mapping[str, list[float]],
    *,
    phase: str,
) -> float | None:
    """Derive actual per-step iteration latency (ms/step), never per-token TPOT."""
    target_mode = "prefill" if str(phase or "").strip().lower() == "prefill" else "decode"
    modes = (target_mode, "mixed")
    for mode in modes:
        acc = observed_steps.get(mode)
        if acc is not None and acc[1] > 0.0:
            return acc[0] / acc[1]
    traces = report.get("traces")
    if isinstance(traces, (list, tuple)):
        for mode in modes:
            samples: list[float] = []
            for row in traces:
                if not isinstance(row, Mapping):
                    continue
                if str(row.get("mode") or "").strip().lower() != mode:
                    continue
                dur = _finite_nonneg(row.get("duration_ms"))
                if dur is None:
                    start = _finite_nonneg(row.get("start_ms"))
                    end = _finite_nonneg(row.get("end_ms"))
                    if start is not None and end is not None and end >= start:
                        dur = end - start
                if dur is not None:
                    samples.append(dur)
            if samples:
                return sum(samples) / float(len(samples))
    execution = report.get("execution")
    step_summary = execution.get("step_summary") if isinstance(execution, Mapping) else None
    groups = step_summary.get("groups") if isinstance(step_summary, Mapping) else None
    if isinstance(groups, (list, tuple)):
        for mode in modes:
            total_steps = 0
            total_ms = 0.0
            for group in groups:
                if not isinstance(group, Mapping):
                    continue
                if str(group.get("mode") or "").strip().lower() != mode:
                    continue
                steps = group.get("steps")
                dur_map = group.get("duration_ms")
                dur_sum = (
                    _finite_nonneg(dur_map.get("sum")) if isinstance(dur_map, Mapping) else None
                )
                if type(steps) is int and steps > 0 and dur_sum is not None:
                    total_steps += steps
                    total_ms += dur_sum
            if total_steps > 0:
                return total_ms / float(total_steps)
    return None


def predict_cell(spec: CellSpec, **_: Any) -> dict[str, Any]:
    """Price one declared cell through the canonical ``mindie_sim.predict`` entry point."""
    base = {
        "cell_id": spec.cell_id,
        "model_label": spec.model_label,
        "layers": 0,
        "per_layer": {},
        "subgraphs": {},
        "body_ms": None,
        "ttft_ms": None,
        "tpot_ms": None,
        "dual_moe_ms": None,
        "rows": (),
        "notes": (),
        "decode_body_ms": None,
        "prefill_body_ms": None,
        "formal_point": False,
        "partial_targets": (),
        "native_status": {},
        "step_ms": None,
        "public_basis": "canonical_predict",
        "public_events": 0,
        "source_binding": dict(spec.source_binding or {}),
        "routing_status": "canonical_serving",
    }
    if spec.model_case is None or not Path(spec.model_case).is_file():
        return {**base, "notes": ("no_model_case",)}
    observed_steps: dict[str, list[float]] = {}

    def _observe_step(step: Any) -> None:
        mode = str(getattr(step, "mode", "") or "").strip().lower()
        completion = getattr(step, "completion", None)
        end_ms = _finite_nonneg(getattr(completion, "time", None))
        start_ms = _finite_nonneg(getattr(step, "start_ms", None))
        if mode and end_ms is not None and start_ms is not None and end_ms >= start_ms:
            acc = observed_steps.setdefault(mode, [0.0, 0.0])
            acc[0] += end_ms - start_ms
            acc[1] += 1.0

    try:
        import mindie_sim
        from mindie_sim.prediction.structure import parse_case

        raw = raw_case_for_cell(spec)
        case = parse_case(raw)
        try:
            report = mindie_sim.predict(
                case,
                scope="serving",
                trace_limit=0,
                event_limit=_PREDICT_EVENT_LIMIT,
                observer=_observe_step,
            )
        except TypeError as exc:
            if "observer" not in str(exc):
                raise
            report = mindie_sim.predict(
                case, scope="serving", trace_limit=0, event_limit=_PREDICT_EVENT_LIMIT
            )
    except TimeoutError:
        raise
    except Exception as exc:  # noqa: BLE001 - declared serving gap
        return {
            **base,
            "error": {
                "code": "canonical_predict_error",
                "type": type(exc).__name__,
                "message": str(exc),
            },
            "notes": (f"canonical_predict_error:{type(exc).__name__}:{exc}",),
        }
    metrics = report.get("metrics") if isinstance(report.get("metrics"), Mapping) else {}
    layers = int(getattr(case.model, "layers", 0) or 0)
    body_ms = _canonical_metric(metrics, "e2e_ms")
    prefill_ms = _canonical_metric(metrics, "prefill_ms")
    decode_ms = _canonical_metric(metrics, "decode_ms")
    formal = body_ms is not None
    result = {
        **base,
        "layers": layers,
        "ttft_ms": _canonical_metric(metrics, "ttft_ms"),
        "tpot_ms": _canonical_metric(metrics, "tpot_ms"),
        "step_ms": _iteration_step_ms(report, observed_steps, phase=spec.phase),
        "body_ms": body_ms if formal else None,
        "prefill_body_ms": prefill_ms if formal else None,
        "decode_body_ms": decode_ms if formal else None,
        "formal_point": formal,
        "notes": (f"canonical_status:{report.get('status')}",),
    }
    if not formal:
        result["error"] = {
            "code": "canonical_predict_no_timing",
            "status": report.get("status"),
            "message": "sim returned no usable e2e timing metric",
        }
    return result


def forecast_cell(row: Mapping[str, Any], *, declarations: Any = ()) -> dict[str, Any]:
    """Canonical declared-cell forecast projection (no private service pricing)."""
    del declarations
    return {
        "status": "unavailable",
        "reason": "canonical_forecast_not_retained",
        "cell_id": str(row.get("cell_id") or ""),
    }


def source_declarations(row: Mapping[str, Any]) -> tuple[Any, ...]:
    """Retained declaration keys from one benchmark row."""
    value = row.get("source_declarations") or row.get("declarations") or ()
    return tuple(value) if isinstance(value, (list, tuple)) else ()
