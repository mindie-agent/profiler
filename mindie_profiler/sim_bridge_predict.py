"""Simulator Case normalization and native operator observation/request bridge (sim_bridge_predict).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting simulator case normalization and native operator observation/request bridge.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import Any

from .events import PARSER_VERSION, ProfilerError, ProfilerUsageError
from .native_abi_model import build_plan

from .sim_bridge_native_obs import (
    _native_json_safe, _native_prediction_request_fields,
    _t12_abi, _t12_duration_ms, _t12_invocation_from_request,
)
from .sim_bridge_observed import _canonical_json, _native_timing_path

def _canonical_environment(hardware: Any) -> tuple[Any, str | None]:
    """Build one canonical execution environment from supplied declarations."""
    from mindie_sim.public import ExecutionEnvironment

    if isinstance(hardware, ExecutionEnvironment):
        return hardware, None
    from mindie_sim.schema.hardware import Hardware

    if isinstance(hardware, Hardware):
        return ExecutionEnvironment.from_hardware(hardware), None
    if isinstance(hardware, Mapping):
        raw = dict(hardware)
        if isinstance(raw.get("machine"), Mapping):
            raw = dict(raw["machine"])
        try:
            return ExecutionEnvironment.from_hardware(
                Hardware.from_mapping(raw)), None
        except TimeoutError:
            raise
        except Exception as exc:  # noqa: BLE001 - concrete environment gap
            return None, "t12_environment_unavailable:" + type(exc).__name__ + ":" + str(exc)
    if isinstance(hardware, str) and hardware.strip():
        from mindie_sim.backends import materialize

        sku = hardware.strip()
        failures: list[str] = []
        for backend in ("ascend", "nvidia"):
            try:
                machine = Hardware.from_mapping(materialize(
                    {"backend": backend, "sku": sku, "num_devices": 1}))
                return ExecutionEnvironment.from_hardware(machine), None
            except TimeoutError:
                raise
            except Exception as exc:  # noqa: BLE001 - try the next backend
                failures.append(backend + ":" + type(exc).__name__)
        return None, "t12_environment_unavailable:" + ",".join(failures)
    return None, "t12_environment_unavailable:hardware_not_declared"


def _binding_state(plan: Any) -> tuple[bool, str | None]:
    """Resolve the canonical source binding receipt, never a version label.

    The generic ``OpSpec`` path carries declared API/version facts but no
    ``{repository, revision, relative_path, source_sha256}`` receipt, so the
    binding stays explicitly unestablished.  ``plan.version`` is preserved
    verbatim in the invocation receipt; it is never hashed into a pretended
    source identity.
    """
    del plan
    return False, None


def _canonical_result(plan: Any, report: Mapping[str, Any] | None, *,
                      duration: float | None, execute: bool) -> Any:
    """Project one canonical call report onto the retained prediction receipt."""
    bound, gap = _binding_state(plan)
    payload = _canonical_json({
        "operator": plan.operator,
        "slots": [
            [tensor.get("shape"), tensor.get("dtype"), tensor.get("layout"),
             bool(tensor.get("present", True))]
            for tensor in plan.tensors.values()
        ],
        "api": plan.api, "attrs": plan.attrs,
    })
    call_id = "native:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
    kernel = {"name": plan.operator}
    binding = {
        "call_id": call_id,
        "api": dict(plan.api),
        "typed": {
            "source": None,
            "kernels": [kernel],
            "variant": plan.conditions.get("variant"),
            "relation": "declared_native_call",
            "shapes": {
                str(name): list(tensor.get("shape"))
                for name, tensor in plan.tensors.items()
                if tensor.get("present") is not False
                and isinstance(tensor.get("shape"), (list, tuple))
            },
        },
        "unresolved": list(plan.unresolved)
        + (["attributable_source_reference_unresolved"] if not bound else []),
    }
    physical = {"tensors": plan.tensors}
    program = {
        "caller_plan": {"variant": plan.conditions.get("variant")},
        "physical": physical,
    }
    environment = {
        "basis": "canonical_declared_call", "arch": plan.family,
        "dtype": next((str(t.get("dtype")) for t in plan.tensors.values()
                       if t.get("dtype")), ""),
        "policy": "simulate_native_call",
    }
    payload_dict = {
        "status": "predicted" if gap is None else "unmodeled",
        "reasons": [gap] if gap is not None else [],
        "binding_bound": bound,
        "invocation": {
            "api": dict(plan.api), "version": dict(plan.version),
            "tensors": plan.tensors, "attrs": dict(plan.attrs),
            "conditions": dict(plan.conditions),
        },
        "program": program,
        "binding": binding,
        "environment": environment,
        "spec": {"entry": plan.operator, "kernels": [kernel]},
        "prediction": {
            "duration_ms": duration,
            "work": plan.work,
        },
        "execution_receipt": None,
        "execution_handle_available": False,
        "canonical": {
            "entry": "mindie_sim.simulate_native_call",
            "executed": bool(execute),
            "report": dict(report) if isinstance(report, Mapping) else None,
        },
    }
    return SimpleNamespace(
        status=payload_dict["status"], reasons=payload_dict["reasons"],
        binding_bound=bool(bound), invocation=payload_dict["invocation"],
        program=program, binding=SimpleNamespace(to_dict=lambda: dict(binding)),
        environment=environment, spec=payload_dict["spec"],
        prediction=payload_dict["prediction"],
        to_dict=lambda: dict(payload_dict),
    )


def _simulate_canonical(environment: Any, plan: Any, *, execute: bool) -> tuple[Any, float | None]:
    """Run one declared call through the canonical simulator entry point."""
    if not execute:
        return _canonical_result(plan, None, duration=None, execute=False), None
    from mindie_sim import simulate_native_call

    report = simulate_native_call(environment, plan.ops)
    duration = _t12_duration_ms(report.get("duration_ms"))
    return _canonical_result(plan, report, duration=duration,
                             execute=True), duration


def predict_native_requests(
    requests: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    *,
    hardware: Any = None,
    supply: Any = None,
    policy: Any = None,
    phase: str | None = None,
    source_revision: str | None = None,
    execution: Any = None,
    execute: bool | None = None,
    blocking: bool = True,
) -> dict[str, Any]:
    """Run timing-free requests through ``mindie-sim`` native binding and execution.

    This is the production bridge: an explicit native invocation (or an explicit
    API entry plus ordered ABI slots) is normalized by ``mindie-sim``, the
    selected binding/program is returned, and any unmodeled request remains an
    explicit gap.  When ``execute`` is ``None`` and a hardware/supply/execution
    provider is supplied, the CPU engine evaluates physical duration; callers
    requesting work-only projection pass ``execute=False``.  No duration, model
    Case, default quantization, or observation identity is fabricated.
    """
    if execute is None:
        execute = bool(hardware is not None or supply is not None
                       or execution is not None)
    rows = (list(requests.get("requests", ())) if isinstance(requests, Mapping)
            else list(requests))
    environment, environment_gap = _canonical_environment(hardware)
    predictions = []
    for request in rows:
        if not isinstance(request, Mapping):
            raise ProfilerUsageError("native prediction request must be a mapping")
        request_id = request.get("request_id")
        leak = _native_timing_path(request, "request")
        if leak:
            predictions.append({
                "prediction_id": "t12:" + str(request_id or "unidentified"),
                "request_id": request_id, "status": "unmodeled",
                "reason": "t12_request_contains_timing:" + leak,
                "duration_ms": None,
                "evidence": ["timing-free request rejected before T12 binding"],
                "t12": {"status": "not_invoked", "reason": "request_timing_present"},
                **_native_prediction_request_fields(request),
            })
            continue
        invocation, gap, invocation_meta = _t12_invocation_from_request(
            request, source_revision=source_revision)
        if invocation is None:
            predictions.append({
                "prediction_id": "t12:" + str(request_id or "unidentified"),
                "request_id": request_id, "status": "unmodeled",
                "reason": gap, "duration_ms": None,
                "evidence": ["T12 invocation not constructible without explicit ABI/dispatch facts"],
                "t12": {"status": "not_invoked", "reason": gap},
                **_native_prediction_request_fields(request),
            })
            continue
        boundary = request.get("boundary") if isinstance(
            request.get("boundary"), Mapping) else {}
        plan, plan_gap = build_plan(
            invocation,
            native_operator=boundary.get("native_operator")
            or request.get("native_operator"),
            phase=phase, cann_version=(invocation.get("version") or {}).get("api"))
        if plan is None:
            predictions.append({
                "prediction_id": "t12:" + str(request_id or "unidentified"),
                "request_id": request_id, "status": "unmodeled",
                "reason": plan_gap, "duration_ms": None,
                "evidence": ["canonical ABI normalization preserved an explicit gap"],
                "t12": {"status": "not_invoked", "reason": plan_gap},
                **_native_prediction_request_fields(request),
            })
            continue
        if environment is None:
            predictions.append({
                "prediction_id": "t12:" + str(request_id or "unidentified"),
                "request_id": request_id, "status": "unmodeled",
                "reason": environment_gap, "duration_ms": None,
                "evidence": ["canonical ExecutionEnvironment not constructible"],
                "t12": {"status": "environment_unavailable"},
                **_native_prediction_request_fields(request),
            })
            continue
        try:
            result, duration = _simulate_canonical(
                environment, plan, execute=bool(execute))
        except TimeoutError:
            raise
        except Exception as exc:  # preserve a concrete provider gap
            predictions.append({
                "prediction_id": "t12:" + str(request_id or "unidentified"),
                "request_id": request_id, "status": "unmodeled",
                "reason": "t12_exception:" + type(exc).__name__ + ":" + str(exc),
                "duration_ms": None,
                "evidence": ["canonical simulate_native_call raised; no observation used"],
                "t12": {"status": "exception", "exception": type(exc).__name__},
                **_native_prediction_request_fields(request),
            })
            continue
        prediction_payload = result.prediction or {}
        if result.status == "predicted" and duration is not None:
            status = "modeled"
        elif result.status == "predicted":
            status = "modeled_work_only"
        else:
            status = "unmodeled"
        payload = result.to_dict()
        invocation = result.invocation or {}
        result_environment = result.environment or {}
        binding_payload = payload.get("binding") or {}
        typed = binding_payload.get("typed") or {}
        actual_conditions: dict[str, Any] = {}
        actual_condition_sources: dict[str, list[str]] = {}
        actual_condition_conflicts = list(invocation_meta.get("conflicts") or ())

        def add_actual(key: str, value: Any, source: str) -> None:
            key = str(key)
            if key in actual_conditions:
                if _canonical_json(actual_conditions[key]) != _canonical_json(value):
                    actual_condition_conflicts.append({
                        "field": key,
                        "values": [actual_conditions[key], value],
                        "sources": [*actual_condition_sources.get(key, ()), source],
                    })
                actual_condition_sources.setdefault(key, []).append(source)
                return
            actual_conditions[key] = value
            actual_condition_sources.setdefault(key, []).append(source)

        for key, value in dict(invocation.get("conditions") or {}).items():
            add_actual(key, value, "t12.invocation.conditions")
        for name in ("api", "version", "attrs"):
            value = invocation.get(name)
            if isinstance(value, Mapping):
                add_actual(name, dict(value), "t12.invocation." + name)
        image_id = (invocation.get("version") or {}).get("image_id")
        if image_id:
            add_actual("deployment_image_id", image_id,
                       "t12.invocation.version.image_id")
        add_actual("implementation", {
            "api": binding_payload.get("api"),
            "source": typed.get("source"),
            "kernels": typed.get("kernels"),
            "variant": typed.get("variant"),
            "relation": typed.get("relation"),
        }, "t12.binding.implementation")
        add_actual("execution", {
            "basis": result_environment.get("basis"),
            "arch": result_environment.get("arch"),
            "dtype": result_environment.get("dtype"),
            "policy": result_environment.get("policy"),
        }, "t12.environment.execution")
        actual_hardware = result_environment.get("hardware") or hardware
        if actual_hardware:
            add_actual(
                "hardware",
                actual_hardware if isinstance(actual_hardware, str)
                else getattr(actual_hardware, "hardware_key", None)
                or getattr(getattr(actual_hardware, "machine", None), "sku", None),
                "t12.environment.hardware" if result_environment.get("hardware")
                else "predict.argument.hardware")
        actual_phase = result_environment.get("phase") or phase
        if actual_phase:
            add_actual("phase", actual_phase, "t12.environment.phase"
                       if result_environment.get("phase") else "predict.argument.phase")
        declared_conditions = dict(request.get("conditions") or {})
        actual_condition_gaps = []
        for key, value in declared_conditions.items():
            if key not in actual_conditions:
                actual_condition_gaps.append({
                    "field": str(key),
                    "reason": "not_consumed_by_t12_invocation",
                })
        actual_condition_sources = {
            key: list(dict.fromkeys(labels))
            for key, labels in actual_condition_sources.items()
        }
        deduped_conflicts: dict[tuple[str, str], dict[str, Any]] = {}
        for row in actual_condition_conflicts:
            field = str(row.get("field"))
            deduped_conflicts[(field, _canonical_json(row.get("values")))] = {
                "field": field,
                "values": list(row.get("values") or ()),
                "sources": [str(item) for item in row.get("sources") or ()],
            }
        actual_condition_conflicts = [
            deduped_conflicts[key] for key in sorted(deduped_conflicts)
        ]
        declared_keys = set(request.get("conditions") or ())
        actual_keys = set(invocation_meta.get("t12_condition_keys") or ())
        actual_keys.update({"api", "version", "attrs", "hardware", "phase"})
        if (invocation.get("version") or {}).get("image_id"):
            actual_keys.add("deployment_image_id")
        condition_scope = {
            key: ("actual" if key in actual_keys else "declaration")
            for key in declared_keys
        }
        request_software = request.get("software")
        request_runtime = request.get("runtime")
        runner_source = request.get("runner_source", request.get("producer"))
        source_domains = {
            "request_version": dict(request.get("version") or {}),
            "request_software": dict(request_software)
            if isinstance(request_software, Mapping) else {},
            "request_runtime": dict(request_runtime)
            if isinstance(request_runtime, Mapping) else {},
            "runner_source": dict(runner_source)
            if isinstance(runner_source, Mapping) else {},
            "t12_invocation_version": dict(invocation.get("version") or {}),
            "t12_invocation_conditions": dict(invocation.get("conditions") or {}),
            "t12_environment": dict(result_environment),
            "t12_binding_source": typed.get("source"),
        }
        abi_for_eligibility = _t12_abi(result) if result.status == "predicted" else None
        request_abi = request.get("abi")
        same_abi = bool(
            isinstance(request_abi, Mapping)
            and request_abi.get("verified")
            and abi_for_eligibility
            and request_abi.get("digest")
            == abi_for_eligibility.get("digest")
        )
        if result.status == "predicted" and same_abi:
            # Exact verified digest agreement: the declared request ABI is the
            # actual normalized ABI.  The duration remains independently
            # computed by the simulator.
            abi_for_eligibility = dict(request_abi)
            abi_for_eligibility["digest_source"] = (
                "declared_request_slots_lowered_by_selected_program")
        prediction = {
            "prediction_id": "t12:" + str(request_id or payload.get("spec", {}).get("entry", "native")),
            "request_id": request_id,
            "status": status,
            "duration_ms": duration,
            "duration_available": duration is not None,
            "work": prediction_payload.get("work"),
            "boundary": dict(request.get("boundary") or {}),
            "occurrence": dict(request.get("occurrence") or {}),
            "clock": dict(request.get("clock") or {}),
            "window_id": request.get("window_id")
            or (request.get("timing") or {}).get("window_id"),
            "conditions": actual_conditions,
            "condition_sources": actual_condition_sources,
            "condition_gaps": actual_condition_gaps,
            "condition_conflicts": actual_condition_conflicts,
            "condition_scope": condition_scope,
            "request_conditions": dict(request.get("conditions") or {}),
            "request_condition_sources": dict(
                request.get("condition_sources") or {}),
            "source_domains": source_domains,
            "eligibility": {
                "cpu_mechanism": result.status == "predicted",
                "selected_plan": bool(payload.get("program")),
                "timed_pairing": duration is not None,
                "capture_pairing": same_abi,
            },
            "abi": abi_for_eligibility,
            "evidence": [
                "mindie_sim.simulate_native_call",
                "binding_bound=" + str(bool(getattr(result, "binding_bound", False))),
                "request_contains_no_observed_duration",
                *(["actual_submission_receipt"]
                  if payload.get("execution_receipt") else []),
            ],
            "submitted": bool(payload.get("execution_handle_available")),
            "actual_execution": _native_json_safe(payload.get("execution_receipt")),
            "t12": {
                "status": payload.get("status"),
                "binding_bound": bool(getattr(result, "binding_bound", False)),
                "reasons": list(payload.get("reasons") or ()),
                "binding": payload.get("binding"),
                "occurrence": payload.get("occurrence"),
                "program": payload.get("program"),
                "replay_minimal": payload.get("replay_minimal"),
                "environment": payload.get("environment"),
                "source_establishment": payload.get("source_establishment"),
                "invocation": payload.get("invocation"),
                "actual_conditions": actual_conditions,
            },
        }
        if status == "modeled_work_only":
            prediction["reason"] = "t12_timing_free_work_only_no_duration"
        elif status != "modeled":
            prediction["reason"] = "t12_" + str(result.status) + (
                ":" + ";".join(result.reasons) if result.reasons else "")
        predictions.append(prediction)
    statuses = {}
    for prediction in predictions:
        statuses[prediction["status"]] = statuses.get(prediction["status"], 0) + 1
    submitted = sum(1 for item in predictions if item.get("submitted"))
    # Explicit aggregate: every supplied timing-free request must have reached
    # a selected physical program and a concrete duration.  A work-only or
    # unmodeled row makes this false; the per-row reason remains authoritative.
    all_modeled = bool(predictions) and all(
        item.get("status") == "modeled"
        and item.get("duration_ms") is not None
        for item in predictions)
    return _native_json_safe({
        "schema": "mindie-profiler-t12-native-predictions/1",
        "predictions": predictions,
        "all_modeled": all_modeled,
        "execution": {
            "requested": bool(execute),
            "caller_execution": execution is not None,
            "blocking": bool(blocking),
            "submitted": submitted,
        },
        "counts": {"requests": len(rows), "predictions": len(predictions),
                   "submitted": submitted,
                   **{f"status_{key}": value for key, value in statuses.items()}},
        "non_claims": [
            "no_model_case_constructed",
            "no_default_model_or_quantization",
            "no_observation_identity_used_as_prediction",
            "t12_gap_preserved_when_native_binding_not_implemented",
            "cpu_prediction_only_not_device_execution",
        ],
    })
