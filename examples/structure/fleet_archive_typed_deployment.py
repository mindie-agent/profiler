"""Bind a grouped caller from same-run typed operator connections.

The connection is shape plus dtype on one device stream. The successor is
the next matching consumer inside one contiguous source segment. A routing
or collective name on any stream ends that segment, and a same-stream
grouped matmul that is not the accepted consumer ends it too. An intervening
op is kept only when it does not consume the tensor and is not one of those
barriers. Each consumer is bound by its source-row index, so an equal
earlier op is not reused. A graph-capture mode, a suite name, a path, a
duration, and a requested row capacity do not select the caller. An INT32
input slot is not a returned INT32 tensor.

The matching INT8 x INT8 W8 path is the ordinary ``gemm_op``: BF16 store,
internal INT32 accumulator, contract
``int32_cast_row_scale_column_scale_output_cast``, then a separate BF16
SwiGLU and DynamicQuantV2. That path is already built when
``grouped_int8_caller`` is absent. ``ascend_grouped_int32_dequant_swiglu``
is removed only when this unfused chain is witnessed and the INT32 dequant
graph is not. A witnessed INT32 return, GroupedDequantSwiglu, or
arch35_full_load keeps that caller. ``vllm_ascend_mc2_unfused_w8a8`` is
another owner's binder and is left in place.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Mapping

from fleet_archive_producer_reader import _MATRIX_ROW_CAP, _shape_slots

_INT32_CALLER = "ascend_grouped_int32_dequant_swiglu"
_MC2_CALLER = "vllm_ascend_mc2_unfused_w8a8"
_CONTRACT = "int32_cast_row_scale_column_scale_output_cast"


def _canon(dtype: str) -> str:
    text = str(dtype or "").strip().upper().replace("DT_", "")
    if text in {"BFLOAT16", "BF16"}:
        return "BF16"
    if text in {"FLOAT", "FP32", "FLOAT32"}:
        return "FP32"
    if text in {"FLOAT16", "FP16", "HALF"}:
        return "FP16"
    if text == "INT8":
        return "INT8"
    if text == "INT32":
        return "INT32"
    return text


def _kind(name: str, op_type: str) -> str:
    low = f"{name} {op_type}".lower()
    if "arch35_full_load" in low:
        return "arch35_full_load"
    if "dequantswiglu" in low or "groupedmatmulswigluquant" in low or "gmmswigluquant" in low:
        return "dequant_swiglu"
    if "groupedmatmul" in low:
        return "grouped"
    if "swiglu" in low:
        return "swiglu"
    if "dynamicquantv2" in low or "dynamicquant" in low:
        return "dynamic_quant"
    return ""


def _rank2(slot: Any) -> tuple[int, int] | None:
    if isinstance(slot, tuple) and len(slot) == 2 and all(type(item) is int for item in slot):
        return slot
    return None


def _tensor(shapes: list | None, dtypes: list | None) -> tuple[tuple[int, int], str] | None:
    if not shapes or not dtypes:
        return None
    shape = _rank2(shapes[0])
    if shape is None or not dtypes[0]:
        return None
    return shape, _canon(dtypes[0])


def _bf16_gmm(op: Mapping[str, Any]) -> bool:
    if op["kind"] != "grouped":
        return False
    incoming = _tensor(op["inputs"], op["input_dtypes"])
    outgoing = _tensor(op["outputs"], op["output_dtypes"])
    dtypes = [_canon(item) for item in op["input_dtypes"]]
    return bool(
        incoming and outgoing
        and incoming[1] == "INT8" and outgoing[1] == "BF16"
        and len(dtypes) >= 2 and dtypes[1] == "INT8" and "BF16" in dtypes
    )


def _scale_dtypes(op: Mapping[str, Any]) -> list[str]:
    found: list[str] = []
    for raw in op["input_dtypes"]:
        if _canon(raw) in {"BF16", "FP32"} and raw not in found:
            found.append(raw)
    return found


def _barrier_name(name: str, op_type: str) -> bool:
    """Routing and collective names end a segment on every stream."""
    text = f"{name} {op_type}".lower().replace("_", "").replace(" ", "")
    return any(token in text for token in (
        "moeinitrouting", "moefinalizerouting", "moegatingtopk",
        "moetokenpermute", "moetokenunpermute",
        "hccl", "hcom", "alltoall", "allgather", "allreduce", "reducescatter",
    ))


def _successor(ops: list[dict[str, Any]], index: int, tensor: tuple[tuple[int, int], str],
               predicate) -> int | None:
    """Return the source-list index of the next accepted consumer.

    A matching first input that fails the role predicate blocks the segment.
    Search never restarts from an equal earlier dict.
    """
    source = ops[index]
    for cursor in range(index + 1, len(ops)):
        later = ops[cursor]
        if later["barrier"]:
            return None
        same = later["device"] == source["device"] and later["stream"] == source["stream"]
        incoming = _tensor(later["inputs"], later["input_dtypes"]) if later["inputs"] else None
        if same and later["kind"] == "grouped":
            if incoming == tensor and predicate(later):
                return cursor
            return None
        if not same:
            continue
        if incoming == tensor:
            if predicate(later):
                return cursor
            return None
    return None


def _swiglu(op: Mapping[str, Any], tensor: tuple[tuple[int, int], str]) -> bool:
    if op["kind"] != "swiglu":
        return False
    incoming = _tensor(op["inputs"], op["input_dtypes"])
    outgoing = _tensor(op["outputs"], op["output_dtypes"])
    if incoming != tensor or outgoing is None or outgoing[1] != "BF16":
        return False
    return outgoing[0][0] == incoming[0][0] and outgoing[0][1] * 2 == incoming[0][1]


def _dynamic_quant(op: Mapping[str, Any], tensor: tuple[tuple[int, int], str]) -> bool:
    label = f"{op['name']} {op['type']}"
    if op["kind"] != "dynamic_quant" or "DynamicQuantV2" not in label:
        return False
    incoming = _tensor(op["inputs"], op["input_dtypes"])
    outgoing = _tensor(op["outputs"], op["output_dtypes"])
    if incoming != tensor or outgoing is None or outgoing[0] != incoming[0] or outgoing[1] != "INT8":
        return False
    return "FP32" in {_canon(item) for item in op["output_dtypes"][1:]}


def _down(op: Mapping[str, Any], tensor: tuple[tuple[int, int], str]) -> bool:
    incoming = _tensor(op["inputs"], op["input_dtypes"])
    outgoing = _tensor(op["outputs"], op["output_dtypes"])
    return bool(
        _bf16_gmm(op) and incoming == tensor and outgoing is not None
        and outgoing[0][0] == incoming[0][0]
    )


def witness_typed_expert_chain(source: Path, *, row_cap: int = _MATRIX_ROW_CAP) -> dict[str, Any]:
    """Read one kernel CSV. Absence after a cap is not a certified miss."""
    witness: dict[str, Any] = {
        "opened": False, "rows_seen": 0, "capped": False,
        "reason": None, "chains": [], "int32_returned_grouped_matmul": 0,
        "dequant_swiglu_ops": 0, "arch35_full_load_ops": 0,
    }
    if not isinstance(source, Path) or not source.is_file() or source.name.endswith(".gz"):
        witness["reason"] = "source_not_read"
        return witness
    try:
        with source.open(newline="", encoding="utf-8", errors="replace") as handle:
            reader = csv.DictReader(handle)
            names = reader.fieldnames or []
            required = ("Name", "Input Shapes", "Input Data Types", "Output Shapes", "Output Data Types")
            if any(column not in names for column in required):
                witness["reason"] = "dtype_columns_absent"
                return witness
            witness["opened"] = True
            ops: list[dict[str, Any]] = []
            for index, row in enumerate(reader):
                if index >= row_cap:
                    witness["capped"] = True
                    break
                witness["rows_seen"] = index + 1
                name = row.get("Name") or ""
                op_type = row.get("Type") or ""
                barrier = _barrier_name(name, op_type)
                inputs = _shape_slots(row.get("Input Shapes") or "", True)
                outputs = _shape_slots(row.get("Output Shapes") or "", True)
                input_dtypes = _shape_slots(row.get("Input Data Types") or "", False)
                output_dtypes = _shape_slots(row.get("Output Data Types") or "", False)
                parsed = inputs is not None and outputs is not None and input_dtypes is not None and output_dtypes is not None
                if not parsed and not barrier:
                    continue
                ops.append({
                    "kind": _kind(name, op_type) if parsed else "",
                    "name": name, "type": op_type, "barrier": barrier, "row_index": index,
                    "device": str(row.get("Device_id") or ""),
                    "stream": str(row.get("Stream ID") or ""),
                    "inputs": inputs or [], "outputs": outputs or [],
                    "input_dtypes": [str(item) for item in input_dtypes] if parsed else [],
                    "output_dtypes": [str(item) for item in output_dtypes] if parsed else [],
                })
    except OSError:
        witness["opened"] = False
        witness["reason"] = "source_not_read"
        return witness
    chains: list[dict[str, Any]] = []
    for index, op in enumerate(ops):
        if op["kind"] == "dequant_swiglu":
            witness["dequant_swiglu_ops"] += 1
        elif op["kind"] == "arch35_full_load":
            witness["arch35_full_load_ops"] += 1
        outgoing = _tensor(op["outputs"], op["output_dtypes"])
        if op["kind"] == "grouped" and outgoing is not None and outgoing[1] == "INT32":
            witness["int32_returned_grouped_matmul"] += 1
        if not _bf16_gmm(op) or outgoing is None or op["barrier"]:
            continue

        def accept_swiglu(item, _tensor=outgoing):
            return _swiglu(item, _tensor)

        swiglu_at = _successor(ops, index, outgoing, accept_swiglu)
        if swiglu_at is None:
            continue
        swiglu = ops[swiglu_at]
        swiglu_out = _tensor(swiglu["outputs"], swiglu["output_dtypes"])
        if swiglu_out is None:
            continue

        def accept_quant(item, _tensor=swiglu_out):
            return _dynamic_quant(item, _tensor)

        quant_at = _successor(ops, swiglu_at, swiglu_out, accept_quant)
        if quant_at is None:
            continue
        quant = ops[quant_at]
        quant_out = _tensor(quant["outputs"], quant["output_dtypes"])
        if quant_out is None:
            continue

        def accept_down(item, _tensor=quant_out):
            return _down(item, _tensor)

        down_at = _successor(ops, quant_at, quant_out, accept_down)
        if down_at is None:
            continue
        down = ops[down_at]
        read_rows = quant_out[0][0]
        returned_rows = _tensor(down["outputs"], down["output_dtypes"])[0][0]
        chains.append({
            "read_rows": read_rows,
            "returned_rows": returned_rows,
            "scale_dtypes": _scale_dtypes(down),
            "device": down["device"],
            "stream": down["stream"],
            "source_indices": [op["row_index"], swiglu["row_index"], quant["row_index"], down["row_index"]],
        })
    witness["chains"] = chains
    return witness


def _public_chain(witness: Mapping[str, Any], *, bound: str | None) -> dict[str, Any]:
    chains = list(witness.get("chains") or [])
    returned = sorted({int(item["returned_rows"]) for item in chains})
    read = sorted({int(item["read_rows"]) for item in chains})
    scales: list[str] = []
    for item in chains:
        for dtype in item.get("scale_dtypes") or []:
            if dtype not in scales:
                scales.append(dtype)
    int32 = bool(
        witness.get("int32_returned_grouped_matmul")
        or witness.get("dequant_swiglu_ops")
        or witness.get("arch35_full_load_ops")
    )
    if chains and int32:
        kind = "bf16_unfused_and_int32_dequant"
    elif int32:
        kind = "int32_dequant_swiglu"
    else:
        kind = "int8_bf16_w8_gmm_swiglu_dynamic_quant"
    return {
        "kind": kind,
        "bound_implementation": bound,
        "matrix_output_contract": _CONTRACT if bound == "gemm_op" else None,
        "output_format": "bf16" if chains else None,
        "swiglu": "bf16" if chains else None,
        "activation_quant": "DynamicQuantV2" if chains else None,
        "gates": len(chains),
        "downs": len(chains),
        "down_returned_rows": returned,
        "down_read_rows": read,
        "down_scale_dtypes": scales,
        "int32_dequant_graph": int32,
        "int32_returned_grouped_matmul": int(witness.get("int32_returned_grouped_matmul") or 0),
        "dequant_swiglu_ops": int(witness.get("dequant_swiglu_ops") or 0),
        "arch35_full_load_ops": int(witness.get("arch35_full_load_ops") or 0),
        "witness_rows_seen": int(witness.get("rows_seen") or 0),
        "witness_capped": bool(witness.get("capped")),
        "chain_source_indices": [list(item["source_indices"]) for item in chains if item.get("source_indices")],
    }


def _caller(runtime: Mapping[str, Any]) -> dict[str, Any] | None:
    kernels = runtime.get("kernels") if isinstance(runtime, Mapping) else None
    lowerings = kernels.get("lowerings") if isinstance(kernels, dict) else None
    caller = lowerings.get("grouped_int8_caller") if isinstance(lowerings, dict) else None
    return caller if isinstance(caller, dict) else None


def bind_witnessed_expert_caller(runtime: dict, model: Any, source: Path,
                                 replaced: list[dict[str, Any]], diagnostics: list[str]) -> None:
    """Drop the unselected INT32 caller, or keep a real INT32 dequant graph."""
    if not isinstance(runtime, dict):
        return
    witness = witness_typed_expert_chain(source)
    chains = list(witness.get("chains") or [])
    int32 = bool(
        witness.get("int32_returned_grouped_matmul")
        or witness.get("dequant_swiglu_ops")
        or witness.get("arch35_full_load_ops")
    )
    caller = _caller(runtime)
    if not chains and not int32:
        if witness.get("capped") and caller is not None:
            diagnostics.append("typed_expert_chain_not_certified:witness_capped")
        return
    bound = "gemm_op" if chains and not int32 else None
    public = _public_chain(witness, bound=bound)
    if isinstance(model, dict) and isinstance(model.get("metadata"), dict):
        model["metadata"]["typed_expert_chain"] = public
    if int32:
        diagnostics.append("typed_expert_chain:int32_dequant_graph_preserved")
        if chains:
            diagnostics.append("typed_expert_chain:bf16_and_int32_graphs_both_witnessed")
        return
    if caller is None:
        diagnostics.append("typed_expert_chain:gemm_op_int8_bf16_already_selected")
        return
    implementation = str(caller.get("implementation") or "")
    if implementation == _MC2_CALLER:
        diagnostics.append("typed_expert_chain:mc2_unfused_binder_not_owned_here")
        return
    if implementation != _INT32_CALLER:
        diagnostics.append(f"typed_expert_chain:grouped_int8_caller_left:{implementation or 'absent_name'}")
        return
    lowerings = runtime["kernels"]["lowerings"]
    removed = lowerings.pop("grouped_int8_caller")
    rows = ",".join(str(item) for item in public["down_returned_rows"])
    replaced.append({
        "grouped_int8_caller": removed,
        "bound_implementation": "gemm_op",
        "matrix_output_contract": _CONTRACT,
        "output_format": "bf16",
        "swiglu": "bf16",
        "activation_quant": "DynamicQuantV2",
        "down_returned_rows": public["down_returned_rows"],
        "down_read_rows": public["down_read_rows"],
        "down_scale_dtypes": public["down_scale_dtypes"],
        "reason": "witnessed_unfused_int8_bf16_gmm_not_int32_dequant",
    })
    diagnostics.append(f"typed_expert_chain:int8_bf16_w8_gmm_swiglu_dynamic_quant:down_rows={rows}")
