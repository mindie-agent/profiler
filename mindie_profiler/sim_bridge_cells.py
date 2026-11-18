"""Declared zero-shot cells and their canonical public forecast projection.

[Role]
  Parse retained benchmark rows into immutable ``CellSpec`` geometry and price
  them only through the canonical ``mindie_sim`` serving entry point.
[Invariants]
  No measured field enters the spec; missing cases and simulator rejections
  remain explicit notes.  No private service, PP or compiled-cell price cache
  exists here.
[Timeouts & Locks]
  Bounded local reads and deterministic arithmetic; no locks.
[Side-Effect Policy]
  Read-only; the caller owns any output file.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
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
            "dataset": self.dataset, "model_case": str(self.model_case or ""),
            "model_label": self.model_label, "phase": self.phase,
            "prompt_tokens": self.prompt_tokens, "concurrency": self.concurrency,
            "max_tokens": self.max_tokens, "tp": self.tp, "dp": self.dp,
            "ep": self.ep, "pp": self.pp,
            "graph_buckets": list(self.graph_buckets),
            "graph_bucket": self.graph_bucket, "notes": list(self.notes),
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
        return (self.dataset, hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest())


def structure_fingerprint(spec: CellSpec) -> str:
    """Deterministic source/geometry identity for a declared cell."""
    payload = {
        "cell_id": spec.cell_id, "phase": spec.phase,
        "model_case": str(spec.model_case or ""), "model_label": spec.model_label,
        "prompt_tokens": spec.prompt_tokens, "concurrency": spec.concurrency,
        "max_tokens": spec.max_tokens, "tp": spec.tp, "dp": spec.dp,
        "ep": spec.ep, "pp": spec.pp, "graph_buckets": list(spec.graph_buckets),
        "graph_bucket": spec.graph_bucket, "notes": list(spec.notes),
        "source_config": str(spec.source_config or ""),
        "source_config_sha256": spec.source_config_sha256,
        "source_deploy_sha256": spec.source_deploy_sha256,
        "source_file_sha256": spec.source_file_sha256,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def cell_from_dict(raw: Mapping[str, Any]) -> Any:
    """Parse a retained benchmark row into a declared cell record."""
    from types import SimpleNamespace
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
        tp=int(record.get("tp") or 1), dp=int(record.get("dp") or 1),
        ep=int(record.get("ep") or 1), pp=int(record.get("pp") or 1),
        graph_buckets=tuple(int(item) for item in record.get("graph_buckets") or ()),
        graph_bucket=int(record.get("graph_bucket") or 0),
        notes=tuple(dict.fromkeys(str(item) for item in record.get("notes") or ())),
        sequences_per_replica=int(record.get("sequences_per_replica") or 0),
        tokens_per_sequence=int(record.get("tokens_per_sequence") or 0),
        synthetic_layers=int(record.get("synthetic_layers") or 0),
        synthetic_experts=int(record.get("synthetic_experts") or 0),
        synthetic_topk=int(record.get("synthetic_topk") or 0),
        source_config=(Path(str(record.get("source_config")))
                       if record.get("source_config") else None),
        source_config_sha256=str(record.get("source_config_sha256") or ""),
        source_deploy_sha256=str(record.get("source_deploy_sha256") or ""),
        source_weight_dir=(Path(str(record["source_weight_dir"]))
                           if record.get("source_weight_dir") else None),
        source_case_dir=(Path(str(record["source_case_dir"]))
                         if record.get("source_case_dir") else None),
        source_header_archive=(Path(str(record["source_header_archive"]))
                               if record.get("source_header_archive") else None),
        require_source=bool(record.get("require_source")),
        source_reject_reason=str(record.get("source_reject_reason") or ""),
        source_file_sha256=str(record.get("source_file_sha256") or ""),
        source_origin=str(record.get("source_origin") or ""),
    )
    trace = raw.get("trace") if isinstance(raw.get("trace"), Mapping) else None
    return SimpleNamespace(
        spec=spec, kernel_paths=(), trace=trace, success=bool(raw.get("success", True)),
        failure=str(raw.get("failure") or ""), ttft_ms=raw.get("ttft_ms"),
        tpot_ms=raw.get("tpot_ms"), step_trace_ms=raw.get("step_trace_ms"),
        decode_steps=int(raw.get("decode_steps") or 1),
        trace_quality=str(raw.get("trace_quality") or "ok"),
    )


def raw_case_for_cell(spec: CellSpec) -> dict[str, Any]:
    """Apply one cell's declared workload and parallel geometry to its template.

    The template case file is only a structure declaration.  Requested
    concurrency, prompt/output tokens, ``tp``/``dp``/``ep``/``pp`` axes and
    graph buckets are applied before ``parse_case`` so the price belongs to the
    requested cell instead of the template's own geometry.  Canonical
    validation still rejects an incompatible declaration.
    """
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


def predict_cell(spec: CellSpec, **_: Any) -> dict[str, Any]:
    """Price one declared cell through the canonical serving entry point.

    A failed or incomplete simulator evaluation never becomes a formal
    zero-time point: timing fields stay ``None`` and ``formal_point`` is false.
    """
    base = {
        "cell_id": spec.cell_id, "model_label": spec.model_label, "layers": 0,
        "per_layer": {}, "subgraphs": {}, "body_ms": None, "ttft_ms": None,
        "dual_moe_ms": None, "rows": (), "notes": (), "decode_body_ms": None,
        "prefill_body_ms": None, "formal_point": False, "partial_targets": (),
        "native_status": {}, "step_ms": None, "public_basis": "canonical_predict",
        "public_events": 0, "source_binding": dict(spec.source_binding or {}),
        "routing_status": "canonical_serving",
    }
    if spec.model_case is None or not Path(spec.model_case).is_file():
        return {**base, "notes": ("no_model_case",)}
    try:
        import mindie_sim
        from mindie_sim.prediction.structure import parse_case

        raw = raw_case_for_cell(spec)
        case = parse_case(raw)
        report = mindie_sim.predict(case, scope="serving", trace_limit=0, event_limit=8)
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
        **base, "layers": layers,
        "ttft_ms": _canonical_metric(metrics, "ttft_ms"),
        "step_ms": _canonical_metric(metrics, "tpot_ms"),
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
    return {"status": "unavailable", "reason": "canonical_forecast_not_retained",
            "cell_id": str(row.get("cell_id") or "")}


def source_declarations(row: Mapping[str, Any]) -> tuple[Any, ...]:
    """Retained declaration keys from one benchmark row."""
    value = row.get("source_declarations") or row.get("declarations") or ()
    return tuple(value) if isinstance(value, (list, tuple)) else ()


