"""Simulator Case normalization and native operator observation/request bridge (sim_bridge_native_obs).

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

import argparse, csv, hashlib, json, os, re, sys
from fractions import Fraction
from collections.abc import Mapping, Sequence
from typing import Any

from .sim_bridge_case import (
    _T12_CONDITION_KEYS, _native_api_mapping, _native_merge_explicit_invocation,
    _native_request_condition_parts, _qbmm_t12_invocation,
)
from .sim_bridge_observed import _canonical_json, _native_timing_path

def _t12_invocation_from_request(
    request: Mapping[str, Any], *, source_revision: str | None = None,
) -> tuple[dict[str, Any] | None, str | None, dict[str, Any]]:
    """Build one timing-free native operator invocation from an exported request.

    A complete explicit ``t12_invocation``/``invocation`` mapping is preferred
    and merged with request declarations prior to ``mindie-sim`` normalization.
    Otherwise only an explicit API entry plus ordered ABI slots are mapped via
    the declared native spec, without synthesizing a model or quantization.
    """
    parts, request_conditions, sources, conflicts = (
        _native_request_condition_parts(request))
    declared_conditions = dict(request_conditions)
    meta = {
        "sources": sources, "conflicts": conflicts,
        "declared_conditions": declared_conditions,
    }
    explicit = None
    explicit_name = None
    for name in ("t12_invocation", "invocation"):
        candidate = request.get(name)
        if isinstance(candidate, Mapping):
            explicit, explicit_name = candidate, name
            break
    if explicit is not None:
        found = _native_timing_path(explicit, explicit_name or "invocation")
        if found:
            return None, f"t12_invocation_contains_timing:{found}", meta
        invocation, merged_meta = _native_merge_explicit_invocation(
            explicit, parts, request_conditions, sources, conflicts)
        meta = {
            **meta,
            "sources": merged_meta["sources"],
            "conflicts": merged_meta["conflicts"],
        }
        return invocation, None, meta
    boundary = request.get("boundary") if isinstance(
        request.get("boundary"), Mapping) else {}
    if boundary.get("native_operator") == "QuantBatchMatmulV3":
        return _qbmm_t12_invocation(
            request, source_revision=source_revision, parts=parts,
            conditions=request_conditions, sources=sources,
            conflicts=conflicts)
    api = _native_api_mapping(parts.get("api"))
    entry = api.get("entry") or api.get("aclnn_symbol") or request.get("entry")
    if not entry:
        # A timing-free CSV capture names its physical kernel row, not the
        # Python/ACLNN caller.  Resolve that captured operator against the
        # declared ordered-slot catalogue instead of requiring an API entry
        # the capture never retained.
        entry = boundary.get("native_operator") or request.get("native_operator")
    if not entry:
        return None, "t12_invocation_unavailable:api_entry_not_declared", meta
    try:
        from mindie_sim.prediction.piecewise.native_calls import native_abi_spec
        spec = native_abi_spec(entry)
    except TimeoutError:
        raise
    except Exception as exc:
        return None, ("t12_invocation_unavailable:import_or_spec:"
                      + type(exc).__name__ + ":" + str(exc)), meta
    if spec is None:
        return None, "t12_invocation_unavailable:native_abi_spec_not_declared", meta
    if not api.get("entry"):
        # Complete the declared API identity from the ordered-slot spec that
        # the captured kernel name resolved to.
        api = {"namespace": getattr(spec, "namespace", None) or "native",
               "entry": spec.entry,
               "aclnn_symbol": getattr(spec, "aclnn_symbol", None)}
    abi = request.get("abi") if isinstance(request.get("abi"), Mapping) else {}
    input_slots = list(abi.get("inputs") or ())
    output_slots = list(abi.get("outputs") or ())
    declared_inputs = [item for item in spec.tensors
                       if str(item.role) != "output"]
    declared_outputs = [item for item in spec.tensors
                        if str(item.role) == "output"]
    if (len(input_slots) > len(declared_inputs)
            or len(output_slots) > len(declared_outputs)):
        return None, "t12_invocation_unavailable:tensor_slot_count_mismatch", meta
    tensors: dict[str, Any] = {}

    def bind_slot(declared: Any, slot: Any) -> None:
        role = str(declared.role)
        if slot is None:
            # A trailing optional declaration (for example QBMM's bias) has no
            # captured position at all.  It stays an explicit absent slot; it
            # is never filled with a guessed descriptor.
            tensors[declared.name] = {
                "shape": None, "dtype": None,
                "layout": getattr(declared, "layout", None) or "ND",
                "role": role, "optional": True, "present": False,
            }
            return
        if isinstance(slot, Mapping):
            present = slot.get("present", True) is not False
            # ``presence: absent`` is the captured spelling for an explicit
            # undefined optional position.
            if str(slot.get("presence") or "").lower() in {
                    "absent", "not_present"}:
                present = False
            # An empty captured slot whose dtype and layout are both explicitly
            # undefined is an absent optional tensor, not a typed scalar.
            if str(slot.get("quality") or "").strip() == "undefined":
                present = False
            if (not slot.get("shape") and slot.get("dtype") is None
                    and getattr(declared, "optional", False)):
                present = False
            shape = slot.get("shape") if present else None
            dtype = slot.get("dtype") if present else None
            layout = slot.get("layout") if present else None
        else:
            present = True
            shape, dtype, layout = slot
        tensors[declared.name] = {
            "shape": list(shape) if shape is not None else None,
            "dtype": dtype,
            "layout": layout or getattr(declared, "layout", None) or "ND",
            "role": role, "optional": bool(declared.optional),
            "present": present,
        }

    for index, declared in enumerate(declared_inputs):
        if index < len(input_slots):
            bind_slot(declared, input_slots[index])
        elif declared.optional:
            bind_slot(declared, None)
        else:
            return None, "t12_invocation_unavailable:tensor_slot_count_mismatch", meta
    for index, declared in enumerate(declared_outputs):
        if index < len(output_slots):
            bind_slot(declared, output_slots[index])
        elif declared.optional:
            bind_slot(declared, None)
        else:
            return None, "t12_invocation_unavailable:tensor_slot_count_mismatch", meta
    raw_version = parts.get("version")
    version = dict(raw_version) if isinstance(raw_version, Mapping) else (
        {"api": raw_version} if isinstance(raw_version, str) and raw_version else {})
    attrs = dict(parts.get("attrs") or {}) if isinstance(
        parts.get("attrs"), Mapping) else {}
    # Captured kernel CSV rows retain ND tensor shapes/layouts on MatMulV3 /
    # MatMulV2 without the host ACLNN transpose booleans.  When a rank-2 ND
    # operand is square ([M, M] or [K, K] with K == N), both storage orders
    # address the same contiguous [D, D] footprint; bind the undeclared ND
    # storage flag to False instead of leaving the kernel unexecuted.
    if (str(boundary.get("kind") or "") == "kernel"
            and str(api.get("aclnn_symbol") or api.get("entry") or "") in {
                "aclnnMatmul", "torch.matmul", "MatMulV3", "MatMulV2"}):
        x1_slot = tensors.get("x1") or {}
        x2_slot = tensors.get("x2") or {}
        out_slot = tensors.get("output") or {}
        x1_shape = x1_slot.get("shape") if x1_slot.get("present") else None
        x2_shape = x2_slot.get("shape") if x2_slot.get("present") else None
        out_shape = out_slot.get("shape") if out_slot.get("present") else None
        if (isinstance(x1_shape, list) and len(x1_shape) == 2
                and isinstance(x2_shape, list) and len(x2_shape) == 2
                and isinstance(out_shape, list) and len(out_shape) == 2
                and str(x1_slot.get("layout") or "ND").upper() == "ND"
                and str(x2_slot.get("layout") or "ND").upper() == "ND"):
            out_m, out_n = out_shape[0], out_shape[1]
            if ("transpose_x1" not in attrs and x1_shape[0] == out_m
                    and x1_shape[1] == out_m
                    and out_m in (x2_shape[0], x2_shape[1])):
                attrs["transpose_x1"] = False
                sources.setdefault("attrs.transpose_x1", []).append(
                    "kernel_nd_square_storage")
            inferred_k = (
                x1_shape[0] if attrs.get("transpose_x1") is True else
                x1_shape[1] if attrs.get("transpose_x1") is False else
                x1_shape[1] if x1_shape[0] == out_m and x1_shape[1] != out_m else
                x1_shape[0] if x1_shape[1] == out_m and x1_shape[0] != out_m else
                None)
            if ("transpose_x2" not in attrs and inferred_k == out_n
                    and x2_shape[0] == out_n and x2_shape[1] == out_n):
                attrs["transpose_x2"] = False
                sources.setdefault("attrs.transpose_x2", []).append(
                    "kernel_nd_square_storage")
    # Epsilon is a declared condition on the AddRmsNorm call; when it is only
    # present at condition level, pass it to the declared attr slot instead of
    # dropping it.  The original condition stays in the same canonical receipt.
    conditions = dict(request_conditions)
    for key in ("epsilon", "eps", "norm_eps"):
        if key in conditions and key not in attrs:
            attrs[key] = conditions.pop(key)
            sources.setdefault(f"attrs.{key}", [])
            sources[f"attrs.{key}"].append(f"request.conditions.{key}")
    if not getattr(spec, "preserve_extra_conditions", False):
        conditions = {
            key: value for key, value in conditions.items()
            if key in _T12_CONDITION_KEYS
        }
    meta = {"sources": sources, "conflicts": conflicts,
            "declared_conditions": declared_conditions,
            "t12_condition_keys": list(conditions)}
    return {
        "api": api,
        "version": version,
        "tensors": tensors,
        "attrs": attrs,
        "conditions": conditions,
    }, None, meta

def _t12_duration_ms(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        if isinstance(value, str) and "/" in value:
            return float(Fraction(value))
        number = float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    return number

_DTYPE_STORAGE_ALIASES = {"uint8": "fp8_e8m0"}

def _dtype_identity(dtype: Any) -> str:
    text = str(dtype or "").lower()
    return _DTYPE_STORAGE_ALIASES.get(text, text)

def _declared_slot_signature(abi: Mapping[str, Any]) -> list[str]:
    """Ordered present tensor signature (shape, dtype) of one declared ABI."""
    out: list[str] = []
    for direction in ("inputs", "outputs"):
        for slot in abi.get(direction) or ():
            if not isinstance(slot, Mapping) or not slot.get("present"):
                continue
            shape = slot.get("shape")
            if not isinstance(shape, (list, tuple)) or not shape:
                continue
            out.append(_canonical_json([list(shape),
                                        _dtype_identity(slot.get("dtype"))]))
    return out

def _invocation_slots(invocation: Mapping[str, Any]) -> list[str]:
    """Ordered present tensor signature (shape, dtype) of one invocation."""
    out: list[str] = []
    for tensor in (invocation.get("tensors") or {}).values():
        if not isinstance(tensor, Mapping) or tensor.get("present") is False:
            continue
        shape = tensor.get("shape")
        if not isinstance(shape, (list, tuple)) or not shape:
            continue
        out.append(_canonical_json([list(shape),
                                    _dtype_identity(tensor.get("dtype"))]))
    return out

def _slot_shape_equivalent(declared: Any, actual: Any) -> bool:
    """True when two declared slot shapes describe the same physical buffer.

    An ACLNN slot may be declared in either storage order: the captured
    ``QuantBatchMatmulV3`` weight is ``[N, K]`` while the lowered descriptor is
    ``[K, N]``, and its block scale is ``[N, K/64, 2]`` versus
    ``[K/64, N, 2]``.  Those are the same tensor, so the leading two axes may
    be transposed; every other axis (and the dtype) must still agree exactly.
    A different rank or a different trailing extent is a real mismatch.
    """
    left = list(declared or ())
    right = list(actual or ())
    if left == right:
        return True
    if len(left) != len(right):
        return False
    if len(left) == 2:
        return left == [right[1], right[0]]
    if len(left) >= 3:
        return (left[0] == right[1] and left[1] == right[0]
                and left[2:] == right[2:])
    return False

def _slots_equivalent(declared: list, actual: list) -> bool:
    """Ordered slot equivalence under the declared storage-transpose rule."""
    if len(declared) != len(actual):
        return False
    for left, right in zip(declared, actual):
        try:
            lshape, ldtype = json.loads(left)
            rshape, rdtype = json.loads(right)
        except (TypeError, ValueError):
            return False
        if ldtype != rdtype:
            return False
        if not _slot_shape_equivalent(lshape, rshape):
            return False
    return True

def _request_abi_lowered(result: Any, request_abi: Any) -> bool:
    """True when the selected program consumed exactly the declared request ABI.

    The prediction then echoes the request's ordered slot identity (the same
    typed tensors the invocation was normalized from) instead of a compressed
    leaf port view.  Every present request slot and every declared invocation
    tensor must agree on shape and dtype, so a projection or a substitution
    does not qualify.
    """
    if not isinstance(request_abi, Mapping):
        return False
    if str(request_abi.get("status") or "") != "complete":
        return False
    if not request_abi.get("digest") or not request_abi.get("verified"):
        return False
    invocation = getattr(result, "invocation", None)
    if not isinstance(invocation, Mapping):
        return False
    declared = _declared_slot_signature(request_abi)
    actual = _invocation_slots(invocation)
    return bool(declared) and _slots_equivalent(declared, actual)

def _t12_abi(result: Any) -> dict[str, Any] | None:
    """Project the actual declared invocation sequence, not a compressed dict.

    Native binding keeps every declared tensor (including absent optional slots)
    in ``invocation`` and the selected physical views in ``program.physical``.
    Required absent positions are preserved; optional absent slots that were
    not part of the selected binding are not injected into a smaller actual
    ABI (QBMM's optional bias/weight_nz).
    """
    invocation = getattr(result, "invocation", None)
    if not isinstance(invocation, Mapping):
        return None
    declared = invocation.get("tensors")
    if not isinstance(declared, Mapping) or not declared:
        return None
    program = getattr(result, "program", None)
    physical = program.get("physical") if isinstance(program, Mapping) else None
    physical_tensors = physical.get("tensors") if isinstance(physical, Mapping) else None
    physical_tensors = physical_tensors if isinstance(physical_tensors, Mapping) else {}
    binding = getattr(result, "binding", None)
    binding_dict = binding.to_dict() if hasattr(binding, "to_dict") else {}
    kernels = binding_dict.get("kernels") or []
    operator = (kernels[0].get("name") if kernels and isinstance(kernels[0], Mapping)
                else None)
    if not operator:
        spec = getattr(result, "spec", None) or {}
        kernels = spec.get("kernels") or ()
        operator = (kernels[0].get("name") if kernels and isinstance(kernels[0], Mapping)
                    else spec.get("entry"))
    if not operator:
        return None
    inputs, outputs = [], []
    for name, tensor in declared.items():
        if not isinstance(tensor, Mapping):
            return None
        present = tensor.get("present", True) is not False
        if not present and tensor.get("optional") is True:
            continue
        selected = physical_tensors.get(name)
        if isinstance(selected, Mapping):
            views = selected.get("views") if isinstance(selected.get("views"), Mapping) else {}
            device = views.get("device") if isinstance(views.get("device"), Mapping) else {}
            logical = views.get("logical") if isinstance(views.get("logical"), Mapping) else {}
            storage = views.get("storage") if isinstance(views.get("storage"), Mapping) else {}
            interp = views.get("interpretation") if isinstance(views.get("interpretation"), Mapping) else {}
            shape = device.get("shape") or selected.get("shape") or logical.get("shape") or storage.get("shape")
            dtype = (interp.get("dtype") or device.get("dtype") or selected.get("dtype")
                     or logical.get("dtype") or storage.get("dtype"))
            layout = (device.get("layout") or selected.get("layout")
                      or logical.get("layout") or storage.get("layout") or "ND")
        else:
            shape = tensor.get("shape") if present else None
            dtype = tensor.get("dtype") if present else None
            layout = tensor.get("layout") if present else None
        slot = {
            "shape": list(shape) if isinstance(shape, (list, tuple)) else None,
            "dtype": dtype, "layout": layout,
            "present": present,
            "dtype_present": present and bool(dtype),
            "layout_present": present and bool(layout),
        }
        (outputs if tensor.get("role") == "output" else inputs).append(slot)
    from .native_tensor_abi import native_abi_from_slots
    return native_abi_from_slots(operator, inputs, outputs)

def _native_prediction_request_fields(request: Mapping[str, Any]) -> dict[str, Any]:
    """Request-side facts retained on every prediction, modelled or not.

    These are declarations (boundary/occurrence/clock/window and request
    conditions), not observation values.  Actual invocation conditions are
    added separately after native binding returns them.
    """
    timing = request.get("timing")
    timing = timing if isinstance(timing, Mapping) else {}
    return {
        "boundary": dict(request.get("boundary") or {}),
        "occurrence": dict(request.get("occurrence") or {}),
        "clock": dict(request.get("clock") or {}),
        "window_id": request.get("window_id") or timing.get("window_id"),
        "request_conditions": dict(request.get("conditions") or {}),
        "request_condition_sources": dict(request.get("condition_sources") or {}),
        "condition_gaps": list(request.get("condition_gaps") or ()),
        "condition_conflicts": list(request.get("condition_conflicts") or ()),
        "conditions": {},
    }

def _native_json_safe(value: Any) -> Any:
    """Project a receipt onto JSON values without dropping its fields.

    Execution receipts retain typed keys (OccurrenceKey, AllocationKey); their
    canonical spelling is the string form the caller can persist and compare.
    """
    if isinstance(value, Mapping):
        return {str(key): _native_json_safe(item)
                for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_native_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
