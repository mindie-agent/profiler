"""Lossless catalog-qualified ABI bridge from captured descriptors to params.

[Role]
  Combine ``op_abi_descriptors`` (positional slot preservation),
  ``op_abi_slots`` (dtype/layout mapping, catalog resolution, classification)
  and ``op_abi_geometry`` (axis/ownership validation and parameter derivation)
  into one fail-closed request builder.  The real catalog padding contract is
  then applied to the real captured slots via ``compute_padding`` and
  ``operator_charge``.  Native sequence-length aliases and cumulative offsets
  share ``decode_sequence_lengths`` with the direct formula path.

[Invariants]
  * Positional identity is preserved: an empty/malformed mandatory slot is
    rejected; later slots never shift left.
  * Q/K/V, GEMM axes/broadcast prefixes, grouped K/N, collective byte sizes and
    linear-attention state owners are validated from declared descriptors.
  * Unknown dtypes, layouts, quant modes and sequence encodings are rejected
    with a stable ``invalid_abi`` code; nothing is guessed or clamped.
  * No synthetic placeholder shape is passed to the padding machinery.

[Timeouts & Locks]
  Pure in-memory parsing proportional to the descriptor count; no I/O.

[Side-Effect Policy]
  No mutation of the input row; returns a fresh params mapping.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from mindie_profiler.op_abi_geometry import (
    attention_params, chunk_params, collective_params, conv_params,
    embedding_params, grouped_params, indexer_params, matmul_params, mc2_params,
    quant_params, recover_params, recurrent_params, require_output, rms_params,
    rope_params, routing_params, slice_params, swiglu_params,
)
from mindie_profiler.op_abi_slots import (
    AbiError, Slot, apply_spec_names, classify, resolve_op_spec, slot_records,
)

from mindie_sim.op_formulas.primitives import strict_mapping


def _reject(row: Mapping[str, Any]) -> None:
    if row.get("accepted") is False:
        raise AbiError("rejected_capture_row",
                       str(row.get("error") or "capture marked not accepted")[:160])
    if row.get("error") not in (None, ""):
        raise AbiError("rejected_capture_row", str(row.get("error"))[:160])


def _explicit(row: Mapping[str, Any]) -> tuple[str, dict[str, Any],
                                                dict[str, Any]] | None:
    explicit = row.get("formula")
    if isinstance(explicit, str):
        try:
            explicit = json.loads(explicit)
        except (TypeError, ValueError):
            explicit = None
    if isinstance(explicit, Mapping) and explicit.get("operator"):
        params = (strict_mapping(explicit["params"], "formula.params")
                  if explicit.get("params") is not None else {})
        return str(explicit["operator"]), dict(params), dict(row.get("flags") or {})
    raw_params = row.get("params")
    if isinstance(raw_params, Mapping):
        operator = row.get("operator") or row.get("type")
        if not operator:
            raise AbiError("missing_operator", "params without operator")
        return str(operator), dict(raw_params), dict(row.get("flags") or {})
    return None


def _charge(entry: Mapping[str, Any], inputs: Sequence[Slot],
            attrs: Mapping[str, Any]) -> dict[str, Any]:
    from mindie_profiler.op_abi_geometry_common import _charge as charge

    return charge(entry, inputs, attrs)


def _collective_row(row: Mapping[str, Any], name: str
                    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
    inputs = slot_records(row, "input")
    outputs = slot_records(row, "output")
    operator, params = collective_params(row, name, inputs, outputs)
    spec = resolve_op_spec(operator, name)
    _charge(spec["entry"], inputs, {})
    return operator, params, {}


def _dispatch(operator: str, row: Mapping[str, Any], inputs: Sequence[Slot],
              outputs: Sequence[Slot]
              ) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if operator in {"matmul", "batch_matmul", "quant_batch_matmul"}:
        canonical = ("quant_batch_matmul" if operator == "quant_batch_matmul"
                     else "matmul")
        return canonical, *matmul_params(row, operator, inputs, outputs)
    if operator == "grouped_matmul":
        return operator, *grouped_params(row, inputs, outputs)
    if operator in {"moe_distribute_dispatch", "moe_distribute_combine"}:
        return operator, *mc2_params(row, operator, inputs, outputs)
    if operator in {"flash_attention", "paged_attention"}:
        return operator, *attention_params(row, operator, inputs, outputs)
    if operator in {"rms_norm", "add_rms_norm", "qk_rms_norm"}:
        return operator, *rms_params(operator, inputs, outputs)
    if operator in {"swiglu", "silu_and_mul", "geglu"}:
        return operator, *swiglu_params(operator, inputs, outputs, row)
    if operator == "slice":
        return operator, *slice_params(inputs, outputs)
    if operator == "rotary_position_embedding":
        return operator, *rope_params(inputs)
    if operator == "dynamic_quant":
        return operator, *quant_params(inputs)
    if operator == "moe_gating":
        return "moe_gating_topk_softmax", *routing_params(row, inputs, outputs)
    if operator == "lightning_indexer":
        return operator, *indexer_params(row, inputs, outputs, sparse=False)
    if operator == "sparse_flash_mla":
        return operator, *indexer_params(row, inputs, outputs, sparse=True)
    if operator == "chunk_kda":
        return operator, *chunk_params(row, inputs, outputs)
    if operator == "recurrent_kda":
        return operator, *recurrent_params(row, inputs, outputs)
    if operator in {"kda_recover_ssm_verify", "kda_recover_ssm_commit"}:
        return operator, *recover_params(row, operator, inputs, outputs)
    if operator == "causal_conv1d":
        return operator, *conv_params(row, inputs, outputs)
    if operator in {"embedding", "vocab_parallel_embedding", "lm_head",
                    "argmax", "top_p_sample"}:
        return operator, *embedding_params(operator, inputs, outputs)
    raise AbiError("unsupported_formula_family", operator)


def infer_request(row: Mapping[str, Any]) -> tuple[str, dict[str, Any],
                                                  dict[str, Any]]:
    """Infer ``(operator, params, flags)`` from one normalized profiler row."""
    _reject(row)
    explicit = _explicit(row)
    if explicit is not None:
        operator, params, flags = explicit
        return operator, dict(params), flags
    name = str(row.get("name") or row.get("type") or row.get("op_type") or "")
    operator = classify(name, row)
    if operator is None:
        raise AbiError("unclassified_kernel", name)
    if operator == "collective":
        return _collective_row(row, name)
    spec = resolve_op_spec(operator, name)
    inputs = apply_spec_names(slot_records(row, "input"), spec["input_slots"])
    outputs = apply_spec_names(slot_records(row, "output"), spec["output_slots"])
    if not inputs:
        raise AbiError("missing_input_shapes", name)
    canonical, params, extras = _dispatch(operator, row, inputs, outputs)
    if canonical in {"matmul", "quant_batch_matmul", "grouped_matmul"}:
        require_output(outputs, f"{canonical} output")
    attrs = dict(extras.get("padding_attrs") or {})
    if "layout" not in attrs and params.get("layout"):
        attrs["layout"] = params["layout"]
    charged = _charge(spec["entry"], inputs, attrs)
    flags = dict(extras.get("flags") or {})
    if charged.get("padded_tokens"):
        flags.setdefault("padding_qualified", True)
    return canonical, params, flags


__all__ = ["AbiError", "Slot", "classify", "infer_request", "slot_records"]
