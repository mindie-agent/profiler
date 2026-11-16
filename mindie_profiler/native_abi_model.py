"""Canonical captured-ABI normalization into declared simulator calls.

[Role]
  Resolve one captured native operator against the retained profiler ABI
  catalog, bind its ordered tensor slots without renaming or dropping a
  dimension, and build the declared ``OpSpec`` work that the canonical
  ``mindie_sim`` operator/call entry points price.

[Invariants]
  * An unknown operator or an incomplete slot sequence stays an explicit
    ``unmodeled`` gap; no model case, quantization or duration is invented.
  * Names, shapes, dtypes, layouts, transposes, scales and outputs are
    preserved; only the ordered storage view is shared with the observation.
  * Work is derived from declared geometry and dtype sizes, never from an
    observed duration or a captured timestamp.
  * Shared conditions are only filtered when the caller asks for an explicit
    condition whitelist; the default keeps every declaration.

[Timeouts & Locks]
  Pure in-memory metadata arithmetic; no I/O, device access or locks.

[Side-Effect Policy]
  No I/O and no simulator mutation; returns immutable plan data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .op_api_registry import catalog_operator

#: Bytes per element for the dtype spellings accepted by both the profiler ABI
#: parser and the simulator.  ``None``/``undefined`` slots are not present.
_DTYPE_BYTES = {
    "bool": 1, "uint1": 1, "uint4": 1, "int4": 1, "fp4_e2m1": 1,
    "uint8": 1, "int8": 1, "fp8_e4m3": 1, "fp8_e5m2": 1, "fp8_e8m0": 1,
    "fp16": 2, "bf16": 2,
    "fp32": 4, "int32": 4, "uint32": 4,
    "int64": 8, "uint64": 8, "fp64": 8,
}
_DEFAULT_DTYPE_BYTES = 2
_GEMM_FAMILIES = {"gemm", "matmul", "mc2"}
_VECTOR_FAMILIES = {"norm", "activation", "elementwise", "rope", "quant", "vector"}
_ATTENTION_FAMILIES = {"attention", "indexer", "mla"}


@dataclass(frozen=True)
class NativeCallPlan:
    """One normalized invocation plus the declared physical work."""

    operator: str
    family: str
    pipe: str
    api: dict[str, Any]
    version: dict[str, Any]
    tensors: dict[str, dict[str, Any]]
    attrs: dict[str, Any]
    conditions: dict[str, Any]
    ops: tuple[Any, ...]
    work: dict[str, Any]
    unresolved: tuple[str, ...] = ()
    catalog_state: str = ""

    def abi_slots(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Ordered present input/output descriptors used for the ABI digest."""
        inputs: list[dict[str, Any]] = []
        outputs: list[dict[str, Any]] = []
        for tensor in self.tensors.values():
            if not isinstance(tensor, Mapping):
                continue
            present = tensor.get("present", True) is not False
            slot = {
                "shape": list(tensor["shape"]) if present and tensor.get("shape") is not None else None,
                "dtype": tensor.get("dtype") if present else None,
                "layout": (tensor.get("layout") or "ND") if present else None,
            }
            if str(tensor.get("role")) == "output":
                outputs.append(slot)
            else:
                inputs.append(slot)
        return inputs, outputs

    def work_bytes(self) -> dict[str, int]:
        return dict(self.work.get("bytes") or {})


def _dtype_bytes(dtype: Any) -> int:
    return _DTYPE_BYTES.get(str(dtype or "").lower(), _DEFAULT_DTYPE_BYTES)


def _elements(shape: Any) -> int:
    if not isinstance(shape, (list, tuple)) or not shape:
        return 0
    total = 1
    for dim in shape:
        try:
            value = int(dim)
        except (TypeError, ValueError):
            return 0
        if value <= 0:
            return 0
        total *= value
    return total


def _slot_bytes(tensor: Mapping[str, Any]) -> int:
    if tensor.get("present") is False:
        return 0
    return _elements(tensor.get("shape")) * _dtype_bytes(tensor.get("dtype"))


def _as_float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def _catalog_names(entry: Any, native_operator: Any) -> list[str]:
    names: list[str] = []
    for value in (entry, native_operator):
        text = str(value or "").strip()
        if text and text not in names:
            names.append(text)
    expanded: list[str] = []
    for name in names:
        for candidate in (name, f"aclnn{name}"):
            if candidate not in expanded:
                expanded.append(candidate)
        if name.lower().startswith("aclnn") and name[5:] not in expanded:
            expanded.append(name[5:])
        if "." in name:
            tail = name.rsplit(".", 1)[-1]
            for candidate in (tail, f"aclnn{tail}"):
                if candidate not in expanded:
                    expanded.append(candidate)
    return expanded


def resolve_catalog_entry(entry: Any, native_operator: Any = None,
                          *, cann_version: str | None = None) -> dict[str, Any] | None:
    """Resolve one declared/captured operator against the retained catalog.

    The pinned catalog is the authoritative descriptor source.  An exact name
    or declared alias is required; an unqualified operator returns ``None`` so
    the caller can publish a concrete unmodeled gap.
    """
    for name in _catalog_names(entry, native_operator):
        report = catalog_operator(name, cann_version=cann_version)
        if report is None:
            continue
        resolved = report.get("entry")
        if isinstance(resolved, Mapping) and resolved:
            return {
                "name": report.get("name") or name,
                "entry": dict(resolved),
                "state": str(report.get("signature_status") or report.get("qualification_state") or ""),
                "match": str(report.get("match") or ""),
            }
    return None


def _declared_slot_specs(entry: Mapping[str, Any]) -> tuple[list[dict], list[dict]]:
    slots = entry.get("c_abi_slots") if isinstance(entry.get("c_abi_slots"), Mapping) else {}
    specs = slots.get("slot_specs") if isinstance(slots.get("slot_specs"), Mapping) else {}
    inputs = [dict(item) for item in specs.get("inputs") or () if isinstance(item, Mapping)]
    outputs = [dict(item) for item in specs.get("outputs") or () if isinstance(item, Mapping)]
    return inputs, outputs


def _fallback_slots(tensors: Mapping[str, Any]) -> tuple[list[dict], list[dict]]:
    inputs: list[dict] = []
    outputs: list[dict] = []
    for name, tensor in tensors.items():
        if not isinstance(tensor, Mapping):
            continue
        spec = {
            "name": str(name), "role": str(tensor.get("role") or "input"),
            "optional": bool(tensor.get("optional", False)),
        }
        (outputs if spec["role"] == "output" else inputs).append(spec)
    return inputs, outputs


def _bind_slots(declared: Sequence[Mapping[str, Any]], actual: Sequence[Any],
                *, direction: str, names: Sequence[str] | None = None,
                ) -> tuple[dict[str, dict[str, Any]], str | None]:
    """Bind ordered actual slots to declared descriptors without dropping one.

    An exact declared name wins; every remaining position is assigned in
    declaration order.  This keeps semantic names (for example QBMM
    ``pertoken_scale``) on their declared slot while still accepting captures
    that only retained positional descriptors.
    """
    if len(actual) > len(declared):
        return {}, f"tensor_slot_count_mismatch:{direction}:surplus"
    is_output = direction == "outputs"
    actual_names = [str(item) for item in (names or ())]
    unused = [(actual_names[pos] if pos < len(actual_names) else "", actual[pos])
              for pos in range(len(actual))]
    chosen: dict[int, tuple[str, Any]] = {}
    for index, spec in enumerate(declared):
        declared_name = str(spec.get("name") or spec.get("c_name") or "")
        if not declared_name:
            continue
        for position, (name, slot) in enumerate(unused):
            if name == declared_name:
                chosen[index] = (name, slot)
                unused.pop(position)
                break
    bound: dict[str, dict[str, Any]] = {}
    for index, spec in enumerate(declared):
        declared_name = str(spec.get("name") or spec.get("c_name")
                             or f"{direction}[{index}]")
        if index in chosen:
            name, slot = chosen[index]
        elif unused:
            name, slot = unused.pop(0)
        elif spec.get("optional"):
            name, slot = declared_name, None
        else:
            return {}, f"tensor_slot_count_mismatch:{direction}:missing"
        role = "output" if is_output else str(spec.get("role") or "input")
        present = True
        if isinstance(slot, Mapping):
            present = slot.get("present", True) is not False
            if str(slot.get("presence") or "").lower() in {"absent", "not_present"}:
                present = False
            if str(slot.get("quality") or "").strip() == "undefined":
                present = False
            shape = list(slot.get("shape") or ()) if present else None
            dtype = slot.get("dtype") if present else None
            layout = (slot.get("layout") or "ND") if present else None
        elif slot is not None:
            shape = list(slot)
            dtype = None
            layout = "ND"
        else:
            shape = dtype = layout = None
            present = False
        if not present and not spec.get("optional"):
            return {}, f"tensor_slot_count_mismatch:{direction}:required_absent"
        if name in bound:
            return {}, f"tensor_slot_count_mismatch:{direction}:duplicate_name"
        bound[name] = {
            "name": name, "shape": shape, "dtype": dtype, "layout": layout,
            "role": role, "present": present,
            "optional": bool(spec.get("optional", False)),
            "dtype_present": present and bool(dtype),
            "layout_present": present and bool(layout),
        }
    return bound, None


def _primary_shape(tensors: Mapping[str, Mapping[str, Any]]) -> tuple[int, ...]:
    for tensor in tensors.values():
        if str(tensor.get("role")) == "output" and tensor.get("present") is not False:
            shape = tensor.get("shape")
            if isinstance(shape, (list, tuple)) and shape:
                return tuple(int(dim) for dim in shape)
    for tensor in tensors.values():
        shape = tensor.get("shape")
        if isinstance(shape, (list, tuple)) and shape:
            return tuple(int(dim) for dim in shape)
    return (1,)


def _gemm_geometry(tensors: Mapping[str, Mapping[str, Any]]) -> tuple[int, int, int] | None:
    x_shape = out_shape = None
    weight_shape = None
    for name, tensor in tensors.items():
        if str(tensor.get("role")) == "output":
            out_shape = tensor.get("shape")
            continue
        lowered = str(name).lower()
        if "weight" in lowered or "x2" in lowered:
            weight_shape = tensor.get("shape")
        elif x_shape is None and tensor.get("present") is not False:
            x_shape = tensor.get("shape")
    if not x_shape or not out_shape:
        return None
    try:
        m = int(x_shape[0]) if len(x_shape) >= 2 else 1
        k = int(x_shape[-1])
        n = int(out_shape[-1])
    except (TypeError, ValueError):
        return None
    if m <= 0 or k <= 0 or n <= 0:
        return None
    if weight_shape and len(weight_shape) == 2:
        # ND weight may be stored [K, N] or [N, K]; the output closes the
        # orientation exactly, so a disagreeing pair stays unmodeled.
        if int(weight_shape[0]) == k:
            pass
        elif int(weight_shape[1]) == k:
            pass
        else:
            return None
    return m, k, n


def _declared_work(tensors: Mapping[str, Mapping[str, Any]], *,
                   family: str, pipe: str) -> dict[str, Any]:
    byte_map = {str(name): _slot_bytes(tensor) for name, tensor in tensors.items()}
    total_bytes = sum(byte_map.values())
    elements = sum(_elements(tensor.get("shape")) for tensor in tensors.values()
                   if tensor.get("present") is not False)
    dtype = next((str(tensor.get("dtype")) for tensor in tensors.values()
                  if tensor.get("dtype")), "bf16")
    work: dict[str, Any] = {
        "bytes": {**byte_map, "total": total_bytes},
        "cube": {"macs": 0.0}, "vector": {"ops": 0.0},
    }
    if family in _GEMM_FAMILIES or pipe == "cube":
        geometry = _gemm_geometry(tensors)
        if geometry is not None:
            m, k, n = geometry
            work["cube"]["macs"] = float(m) * float(k) * float(n)
            work["shape"] = {"m": m, "k": k, "n": n, "dtype": dtype}
    elif family in _ATTENTION_FAMILIES or pipe == "aic_aiv_fused":
        # Attention work is declared as query-token scaled score work only when
        # the geometry closes; no measured span enters the declaration.
        work["vector"]["ops"] = float(elements)
    else:
        work["vector"]["ops"] = float(elements)
    return work


def _op_spec(*, op_id: str, family: str, phase: str, shape: tuple[int, ...],
             dtype: str, work: Mapping[str, Any]) -> Any:
    from mindie_sim.schema.operators import OpSpec
    macs = float((work.get("cube") or {}).get("macs") or 0.0)
    vector_ops = float((work.get("vector") or {}).get("ops") or 0.0)
    total_bytes = float((work.get("bytes") or {}).get("total") or 0.0)
    matrix_flops = (("bf16", 2.0 * macs),) if macs > 0 else ()
    return OpSpec(
        op_id=op_id, family=family, phase=phase, stage=0, layer=0,
        requests=(), semantic_shape=shape, local_shape=shape,
        padded_shape=shape, launch_shape=shape,
        flops=2.0 * macs, hbm_bytes=total_bytes, mte2_bytes=total_bytes,
        mte3_bytes=total_bytes, vector_ops=vector_ops,
        dtype=dtype, matrix_flops=matrix_flops,
        metadata=(("native_abi", True),),
    )


def build_plan(invocation: Mapping[str, Any], *,
               native_operator: Any = None, phase: str | None = None,
               cann_version: str | None = None) -> tuple[NativeCallPlan | None, str | None]:
    """Normalize one invocation into a declared call plan.

    The invocation keeps its declared API/version/attrs/conditions and ordered
    tensors.  Missing descriptors and slot conflicts are returned as a concrete
    ``t12_invocation_unavailable:*`` reason; nothing is fabricated.
    """
    if not isinstance(invocation, Mapping):
        return None, "t12_invocation_unavailable:not_a_mapping"
    tensors = invocation.get("tensors")
    if not isinstance(tensors, Mapping) or not tensors:
        return None, "t12_invocation_unavailable:tensor_slots_missing"
    api = dict(invocation.get("api") or {})
    version = dict(invocation.get("version") or {})
    attrs = dict(invocation.get("attrs") or {})
    conditions = dict(invocation.get("conditions") or {})
    resolved = resolve_catalog_entry(
        api.get("entry") or api.get("aclnn_symbol") or native_operator,
        native_operator, cann_version=cann_version)
    if resolved is None:
        return None, "t12_invocation_unavailable:operator_not_in_catalogue"
    entry = resolved["entry"]
    declared_inputs, declared_outputs = _declared_slot_specs(entry)
    if not declared_inputs and not declared_outputs:
        declared_inputs, declared_outputs = _fallback_slots(tensors)
    ordered = list(tensors.items())
    actual_inputs = [tensor for _, tensor in ordered
                     if str((tensor or {}).get("role")) != "output"]
    actual_outputs = [tensor for _, tensor in ordered
                      if str((tensor or {}).get("role")) == "output"]
    input_names = [str(name) for name, tensor in ordered
                   if str((tensor or {}).get("role")) != "output"]
    output_names = [str(name) for name, tensor in ordered
                    if str((tensor or {}).get("role")) == "output"]
    bound_inputs, reason = _bind_slots(
        declared_inputs, actual_inputs, direction="inputs", names=input_names)
    if reason:
        return None, f"t12_invocation_unavailable:{reason}"
    bound_outputs, reason = _bind_slots(
        declared_outputs, actual_outputs, direction="outputs", names=output_names)
    if reason:
        return None, f"t12_invocation_unavailable:{reason}"
    bound: dict[str, Any] = {**bound_inputs, **bound_outputs}
    family = str(entry.get("family") or "native")
    pipe = str(entry.get("pipe") or "")
    work = _declared_work(bound, family=family, pipe=pipe)
    dtype = next((str(tensor.get("dtype")) for tensor in bound.values()
                  if tensor.get("dtype")), "bf16")
    spec_phase = str(phase or conditions.get("phase") or "decode")
    operator = str(entry.get("name") or resolved["name"] or
                   api.get("entry") or native_operator or "native")
    try:
        op = _op_spec(op_id="native/0", family=family, phase=spec_phase,
                      shape=_primary_shape(bound), dtype=dtype, work=work)
    except TimeoutError:
        raise
    except Exception as exc:  # canonical schema rejection stays a gap
        return None, ("t12_invocation_unavailable:op_spec:"
                      + type(exc).__name__ + ":" + str(exc))
    unresolved: list[str] = []
    if resolved.get("state") and resolved["state"] != "pinned":
        unresolved.append("abi_signature_" + str(resolved["state"]))
    return NativeCallPlan(
        operator=operator, family=family, pipe=pipe, api=api, version=version,
        tensors=bound, attrs=attrs, conditions=conditions, ops=(op,),
        work=work, unresolved=tuple(unresolved),
        catalog_state=str(resolved.get("state") or ""),
    ), None


def catalog_spec(entry: Any, native_operator: Any = None,
                 *, cann_version: str | None = None) -> dict[str, Any] | None:
    """Public descriptor view used by the request normalizer."""
    return resolve_catalog_entry(entry, native_operator, cann_version=cann_version)
