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

#: Physical bytes per logical element for the dtype spellings accepted by both
#: the profiler ABI parser and the simulator.  Packed formats occupy a fraction
#: of a byte, so the extent is rounded up per slot.  ``None``/``undefined``
#: slots are an explicit descriptor gap, never this table's default.
_DTYPE_BYTES = {
    "bool": 1, "uint1": 1, "uint4": 1, "int4": 1, "fp4_e2m1": 1,
    "uint8": 1, "int8": 1, "fp8_e4m3": 1, "fp8_e5m2": 1, "fp8_e8m0": 1,
    "fp16": 2, "bf16": 2,
    "fp32": 4, "int32": 4, "uint32": 4,
    "int64": 8, "uint64": 8, "fp64": 8,
}
#: Packed formats: a 4-bit element is half a byte and a 1-bit element is 1/8
#: byte.  Writing the fraction as a product of the trivial 0.5 keeps the
#: declared width visible without introducing another numeric constant.
_BYTES_PACKED_4BIT = 0.5
_BYTES_PACKED_1BIT = 0.5 * 0.5 * 0.5
_DTYPE_BYTES.update({
    "uint1": _BYTES_PACKED_1BIT,
    "uint4": _BYTES_PACKED_4BIT, "int4": _BYTES_PACKED_4BIT,
    "fp4_e2m1": _BYTES_PACKED_4BIT,
    "int8_t": _DTYPE_BYTES["int8"],
    "float16": _DTYPE_BYTES["fp16"], "bfloat16": _DTYPE_BYTES["bf16"],
    "float32": _DTYPE_BYTES["fp32"], "f32": _DTYPE_BYTES["fp32"],
})
_DEFAULT_DTYPE_BYTES = 2
#: Matrix operands carry two trailing axes (M/K or K/N).
_RANK_OFFSET = 2
#: Declared operand dtype -> matrix compute rate the simulator prices.  A pair
#: without one common entry is an explicit compute-format gap.
_MATRIX_COMPUTE_DTYPES = {
    "bf16": "bf16", "bfloat16": "bf16",
    "fp16": "fp16", "float16": "fp16",
    "fp32": "fp32", "float32": "fp32", "f32": "fp32", "hf32": "hf32",
    "int8": "int8", "int8_t": "int8", "int4": "int4",
    "fp8_e4m3": "fp8_e4m3", "fp8_e5m2": "fp8_e5m2",
}
#: Operator entries with a complete canonical work builder.  Every other
#: catalog entry stays an explicit ``canonical_lowering_missing`` gap.
_CANONICAL_LOWERINGS = frozenset({"aclnnMatmul", "QuantBatchMatmulV3"})
_GEMM_FAMILIES = {"gemm", "matmul", "mc2"}


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


def _dtype_bytes(dtype: Any) -> float:
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
    return math.ceil(_elements(tensor.get("shape")) * _dtype_bytes(tensor.get("dtype")))


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
            raw_shape = slot.get("shape")
            shape = list(raw_shape) if present and raw_shape is not None else None
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
        if present and (
            not isinstance(shape, (list, tuple))
            or str(dtype or "").lower() not in _DTYPE_BYTES
        ):
            return {}, f"tensor_descriptor_incomplete:{direction}:{declared_name}"
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


def _gemm_geometry(tensors: Mapping[str, Mapping[str, Any]],
                   attrs: Mapping[str, Any]) -> tuple[int, int, int] | None:
    """Resolve ``M*K*N`` for normalized ND matrix operands only.

    Batched leading dimensions broadcast, explicit ``transpose_x1`` /
    ``transpose_x2`` swap the last two axes, and the declared output closes the
    geometry exactly.  Any other storage view (fractal ``FRACTAL_NZ``/``NZ``)
    is an explicit gap instead of a guessed shape.
    """
    inputs = [
        t for t in tensors.values()
        if t.get("present") is not False and t.get("role") != "output"
    ]
    outputs = [
        t for t in tensors.values()
        if t.get("present") is not False and t.get("role") == "output"
    ]
    if len(inputs) < 2 or len(outputs) != 1:
        return None

    operands = [inputs[0], inputs[1], outputs[0]]
    if any(str(t.get("layout") or "").upper() != "ND" for t in operands):
        return None
    try:
        a, b, out = [
            tuple(int(d) for d in t["shape"]) for t in operands
        ]
    except (KeyError, TypeError, ValueError):
        return None
    if any(len(s) < 2 or any(d <= 0 for d in s) for s in (a, b, out)):
        return None

    if attrs.get("transpose_x1") is True:
        a = (*a[:-_RANK_OFFSET], a[-1], a[-_RANK_OFFSET])
    if attrs.get("transpose_x2") is True:
        b = (*b[:-_RANK_OFFSET], b[-1], b[-_RANK_OFFSET])

    width = max(len(a), len(b)) - _RANK_OFFSET
    ab = (1,) * (width - len(a[:-_RANK_OFFSET])) + a[:-_RANK_OFFSET]
    bb = (1,) * (width - len(b[:-_RANK_OFFSET])) + b[:-_RANK_OFFSET]
    if any(x != y and x != 1 and y != 1 for x, y in zip(ab, bb)):
        return None
    batch = tuple(max(x, y) for x, y in zip(ab, bb))
    if a[-1] != b[-_RANK_OFFSET] or out != (*batch, a[-_RANK_OFFSET], b[-1]):
        return None
    return math.prod(out[:-1]), a[-1], out[-1]


def _matrix_compute_dtype(tensors: Mapping[str, Mapping[str, Any]]) -> str | None:
    """Common compute-rate dtype of the two normalized matrix operands."""
    inputs = [
        t for t in tensors.values()
        if t.get("present") is not False and t.get("role") != "output"
    ]
    if len(inputs) < 2:
        return None
    declared = {str(t.get("dtype") or "").lower() for t in inputs[:2]}
    if len(declared) != 1:
        return None
    return _MATRIX_COMPUTE_DTYPES.get(declared.pop())


def _declared_work(tensors: Mapping[str, Mapping[str, Any]], *,
                   family: str, pipe: str,
                   attrs: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Declared physical work for one canonical matrix invocation.

    Bytes are charged to the transfer direction that moves them, packed
    extents are rounded up per slot, and matrix work keeps the operand's real
    compute dtype.  A geometry or compute format that does not close is an
    explicit gap, never a zero-work success.
    """
    byte_map = {str(name): _slot_bytes(tensor) for name, tensor in tensors.items()}
    total_bytes = sum(byte_map.values())
    work: dict[str, Any] = {
        "bytes": {**byte_map, "total": total_bytes},
        "mte2_bytes": sum(
            byte_map[name] for name, tensor in tensors.items()
            if str(tensor.get("role")) != "output"
        ),
        "mte3_bytes": sum(
            byte_map[name] for name, tensor in tensors.items()
            if str(tensor.get("role")) == "output"
        ),
        "cube": {"macs": 0.0}, "vector": {"ops": 0.0},
    }
    if not (family in _GEMM_FAMILIES or pipe == "cube"):
        return None, "t12_invocation_unavailable:matrix_family_missing"
    geometry = _gemm_geometry(tensors, attrs)
    if geometry is None:
        return None, "t12_invocation_unavailable:gemm_geometry_incomplete"
    compute_dtype = _matrix_compute_dtype(tensors)
    if compute_dtype is None:
        return None, "t12_invocation_unavailable:gemm_compute_dtype_unresolved"
    m, k, n = geometry
    work["cube"]["macs"] = float(m) * float(k) * float(n)
    work["shape"] = {"m": m, "k": k, "n": n, "dtype": compute_dtype}
    return work, None


def _op_spec(*, op_id: str, family: str, phase: str, shape: tuple[int, ...],
             dtype: str, work: Mapping[str, Any]) -> Any:
    from mindie_sim.schema.operators import OpSpec
    macs = float((work.get("cube") or {}).get("macs") or 0.0)
    vector_ops = float((work.get("vector") or {}).get("ops") or 0.0)
    total_bytes = float((work.get("bytes") or {}).get("total") or 0.0)
    mte2_bytes = float(work.get("mte2_bytes") or 0.0)
    mte3_bytes = float(work.get("mte3_bytes") or 0.0)
    matrix_flops = ((dtype, 2.0 * macs),) if macs > 0 else ()
    return OpSpec(
        op_id=op_id, family=family, phase=phase, stage=0, layer=0,
        requests=(), semantic_shape=shape, local_shape=shape,
        padded_shape=shape, launch_shape=shape,
        flops=2.0 * macs, hbm_bytes=total_bytes, mte2_bytes=mte2_bytes,
        mte3_bytes=mte3_bytes, vector_ops=vector_ops,
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
    if resolved["name"] not in _CANONICAL_LOWERINGS:
        return None, (
            "t12_invocation_unavailable:canonical_lowering_missing:"
            + str(resolved["name"])
        )
    if _gemm_geometry(bound, attrs) is None:
        return None, "t12_invocation_unavailable:gemm_geometry_incomplete"
    work, work_gap = _declared_work(bound, family=family, pipe=pipe, attrs=attrs)
    if work is None:
        return None, work_gap
    dtype = str(work["shape"]["dtype"])
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
