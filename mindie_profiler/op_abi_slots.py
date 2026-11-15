"""Descriptor slots, dtype mapping, catalog specs and kernel classification.

[Role]
  Preserve captured slot identity (shape, dtype, layout, values) losslessly and
  positionally, map every declared dtype spelling to the engine's canonical
  storage type, resolve the real operator ABI catalog entry, and classify native
  kernel names into formula families.  Split from ``op_abi_bridge`` and
  ``op_abi_geometry`` so each module stays inspectable and under the size cap.

[Invariants]
  * Empty/malformed positional slots are retained; they are never deleted and
    later slots never shift left.  ``valid`` is false unless shape and dtype
    are both present and non-negative.
  * ``absent``/``undefined``/``missing``/``invalid`` slots are never promoted to
    tensors; a non-empty unknown dtype spelling raises ``AbiError``.
  * A shape is never guessed from an anonymous positional token: layout comes
    from the declared format, then from an explicit rank rule.
  * The resolved catalog entry is the real ``op_api_catalog.json`` contract; a
    declared fallback is explicit in ``source`` and never claims catalog
    provenance.
  * Classification is deterministic and independent of insertion order.
  * Mixed descriptors and column count conflicts reject before geometry runs.

[Timeouts & Locks]
  Pure in-memory parsing proportional to the slot count; one cached catalog read.

[Side-Effect Policy]
  No I/O beyond the immutable catalog load and no mutation of the input row.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from mindie_profiler.op_abi_descriptors import _EXTRA_DTYPES, slot_descriptors
from mindie_profiler.native_tensor_abi import DTYPES

from mindie_sim.op_formulas import FormulaValidationError
from mindie_sim.op_formulas.primitives import strict_int


class AbiError(FormulaValidationError):
    """Structured ABI rejection carrying a stable code."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


@dataclass(frozen=True)
class Slot:
    """One positional descriptor slot, including its rejection state."""

    name: str
    shape: tuple[int, ...] | None
    dtype: str | None
    layout: str
    values: Any = None
    state: str = "tensor"
    valid: bool = True
    raw_shape: str | None = None
    omitted: bool = False  # Explicit absence, not malformed/partial metadata.

    @property
    def rank(self) -> int:
        return 0 if self.shape is None else len(self.shape)

    @property
    def dims(self) -> tuple[int, ...]:
        if not self.valid or self.shape is None:
            raise AbiError("invalid_tensor_slot", self.name)
        return self.shape


_ATTN_LAYOUTS = {"BSND", "BNSD", "TND", "BSH", "SBH", "NSD", "ND"}


def _map_dtype(raw: Any) -> str | None:
    text = "" if raw is None else str(raw).strip()
    if not text or text.upper() in {"NULL", "NONE", "UNDEFINED", "DT_UNDEFINED",
                                    "N/A", "NA"}:
        return None
    if text in DTYPES:
        mapped = DTYPES[text]
    elif text in _EXTRA_DTYPES:
        mapped = _EXTRA_DTYPES[text]
    elif text.lower() in DTYPES:
        mapped = DTYPES[text.lower()]
    elif text.lower() in _EXTRA_DTYPES:
        mapped = _EXTRA_DTYPES[text.lower()]
    else:
        raise AbiError("unknown_dtype", repr(text))
    return mapped


def _aliases(row: Mapping[str, Any], direction: str) -> dict[str, Any]:
    """Add the dtype/format column spellings the captured CSV actually uses."""
    out = dict(row)
    pairs = (
        (f"{direction}_dtypes", (f"{direction}_data_types", f"{direction}_dtype")),
        (f"{direction}_formats", (f"{direction}_format",)),
    )
    for canonical, sources in pairs:
        if out.get(canonical) not in (None, ""):
            continue
        for source in sources:
            if out.get(source) not in (None, ""):
                out[canonical] = out[source]
                break
    return out


def _layout_of(raw: Any, rank: int) -> str:
    text = str(raw or "").strip().upper()
    cleaned = text.replace("_NZ", "")
    for candidate in ("BSND", "BNSD", "TND", "BSH", "SBH", "NSD", "NCHW", "ND"):
        if cleaned.startswith(candidate):
            return candidate
    if rank == 4:
        return "BSND"
    if rank == 3:
        return "TND"
    return "ND"


def _raw_layout(raw: Any) -> str:
    return str(raw or "").strip().upper().replace("_NZ", "")


def slot_records(row: Mapping[str, Any], direction: str) -> list[Slot]:
    """Return every positional slot, preserving invalid and empty entries."""
    source = _aliases(row, direction)
    descriptor = slot_descriptors(source, direction)
    out: list[Slot] = []
    if not descriptor.get("present"):
        return out
    for index, slot in enumerate(descriptor.get("slots", [])):
        state = str(slot.get("state") or "missing")
        raw_shape = slot.get("shape")
        source_obj = slot.get("descriptor_source") or {}
        name = str(slot.get("name") or source_obj.get("name")
                   or f"{direction}[{index}]")
        layout = _raw_layout(slot.get("layout_raw"))
        rank = 0 if raw_shape is None else len(raw_shape)
        if not layout:
            layout = _layout_of("", rank)
        raw_dtype = str(slot.get("dtype_raw") or "").strip()
        if (slot.get("dtype_present") and not slot.get("dtype_known")
                and raw_dtype.upper() not in {
                    "", "NULL", "NONE", "UNDEFINED", "DT_UNDEFINED", "N/A",
                    "NA"}):
            raise AbiError("unknown_dtype", repr(raw_dtype))
        dtype = None
        if state not in {"absent", "missing", "undefined", "invalid"}:
            dtype = _map_dtype(slot.get("dtype_raw"))
        shape: tuple[int, ...] | None = None
        shape_ok = raw_shape is not None
        if shape_ok:
            try:
                shape = tuple(strict_int(dim, "shape dim", minimum=0)
                              for dim in raw_shape)
            except FormulaValidationError:
                shape_ok = False
        valid = bool(state in {"tensor", "scalar"} and shape_ok
                     and dtype is not None)
        if not valid and state in {"tensor", "scalar"}:
            state = "invalid"
        out.append(Slot(name=name, shape=shape, dtype=dtype, layout=layout,
                        values=slot.get("values"), state=state, valid=valid,
                        raw_shape=None if raw_shape is None else str(raw_shape),
                        omitted=bool(slot.get("omitted"))))
    # Structural errors reject before geometry can select a compact layout.
    # Inspect every dtype first, including invalid tokens and trailing slots.
    for issue in descriptor.get("issues", []):
        if issue["code"] == "descriptor_not_a_mapping":
            raise AbiError(issue["code"], f"{direction}: {issue['detail']}")
        if issue["code"] == "descriptor_column_mismatch":
            raise AbiError(issue["code"], f"{direction}: {issue['column']} "
                           f"{issue['values']} != shapes {issue['shapes']}")
    return out


_CATALOG_CANDIDATES: dict[str, tuple[str, ...]] = {
    "flash_attention": ("aclnnFusedInferAttentionScoreV3",
                        "aclnnFlashAttentionVarLenScore"),
    "paged_attention": ("aclnnPagedAttention",),
    "matmul": ("aclnnMatmul",),
    "batch_matmul": ("aclnnMatmul",),
    "quant_batch_matmul": ("QuantBatchMatmulV3", "aclnnQuantMatmulV4"),
    "grouped_matmul": ("aclnnGroupedMatmulV4",),
    "moe_distribute_dispatch": ("MoeDistributeDispatchV3",),
    "moe_distribute_combine": ("MoeDistributeCombineV3",),
    "chunk_kda": ("ChunkGatedDeltaRule",),
    "recurrent_kda": ("FusedRecurrentGatedDeltaRule",),
    "causal_conv1d": ("CausalConv1d",),
    "rms_norm": ("aclnnRmsNorm",),
    "add_rms_norm": ("aclnnAddRmsNorm",),
    "qk_rms_norm": ("aclnnRmsNorm",),
    "swiglu": ("aclnnSwiGlu",),
    "silu_and_mul": ("aclnnSwiGlu",),
    "dynamic_quant": ("aclnnDynamicQuant",),
    "lightning_indexer": ("QuantLightningIndexer",),
    "moe_gating": ("MoeGatingTopKSoftmax",),
    "init_routing": ("MoeInitRoutingV2",),
    "finalize": ("MoeFinalizeRoutingV2",),
    "mla_prolog": ("MlaPrologV2",),
}

_COLLECTIVE_ENTRIES = {
    "all_reduce": "HcclAllReduce",
    "all_gather": "HcclAllGather",
    "reduce_scatter": "HcclReduceScatter",
    "all_to_all": "HcclAlltoAllV",
    "broadcast": "HcclAllReduce",
}

_FALLBACK_PADDING = {
    "attention": {
        "mode": "masked_varlen", "layout_attr": "input_layout",
        "layouts": {
            "TND": {"token_axis": 0, "seq_axis": 0,
                    "seq_encoding": "cumsum", "leading_zero": True},
            "BSND": {"batch_axis": 0, "seq_axis": 1, "per_batch": True,
                     "seq_encoding": "lengths"},
            "BNSD": {"batch_axis": 0, "seq_axis": 2, "per_batch": True,
                     "seq_encoding": "lengths"},
        },
        "query_arg": "actual_seq_lengths",
        "kv_arg": "actual_seq_lengths_kv", "default_layout": "TND",
    },
    "full": {"mode": "full_padded_tensor"},
}


def _resolve_entry(catalog_name: str) -> dict[str, Any] | None:
    try:
        from mindie_profiler.op_api_registry import catalog_entry
        return catalog_entry(catalog_name)
    except TimeoutError:
        raise
    except Exception:  # noqa: BLE001 - catalog absence is a declared fallback
        return None


def resolve_op_spec(operator: str, name: str = "") -> dict[str, Any]:
    """Resolve the real catalog entry (or an explicit declared fallback)."""
    candidates = list(_CATALOG_CANDIDATES.get(operator, ()))
    if operator == "collective":
        lowered = name.lower().replace("_", "")
        for key, entry_name in _COLLECTIVE_ENTRIES.items():
            if key.replace("_", "") in lowered:
                candidates = [entry_name]
                break
    for candidate in candidates:
        entry = _resolve_entry(candidate)
        if entry is not None:
            slots = entry.get("c_abi_slots") or {}
            return {
                "catalog_name": candidate, "entry": entry,
                "input_slots": list(slots.get("input_slots") or ()),
                "output_slots": list(slots.get("output_slots") or ()),
                "source": "catalog",
            }
    family = ("attention" if operator in {
        "flash_attention", "paged_attention", "sparse_flash_mla",
        "lightning_indexer"} else "full")
    return {
        "catalog_name": None,
        "entry": {"padding_semantics": _FALLBACK_PADDING[family]},
        "input_slots": [], "output_slots": [],
        "source": "declared_fallback",
    }


def apply_spec_names(slots: Sequence[Slot], names: Sequence[str]) -> list[Slot]:
    """Assign declared catalog slot names by original position (never reorder)."""
    out: list[Slot] = []
    for index, slot in enumerate(slots):
        if index < len(names) and names[index]:
            out.append(Slot(name=str(names[index]), shape=slot.shape,
                            dtype=slot.dtype, layout=slot.layout,
                            values=slot.values, state=slot.state,
                            valid=slot.valid, raw_shape=slot.raw_shape,
                            omitted=slot.omitted))
        else:
            out.append(slot)
    return out


def classify(name: str, row: Mapping[str, Any]) -> str | None:
    """Deterministic kernel-name classifier (native aclnn spellings included)."""
    text = "".join(char for char in str(name).lower() if char.isalnum())
    if "kdarecoverssm" in text:
        # Commit must win over the generic recover spelling.
        return ("kda_recover_ssm_commit" if "commit" in text
                else "kda_recover_ssm_verify")
    # The captured kernel's own Type is authoritative.  ``InplaceCopy_Slice``
    # is a different, unsupported API and stays explicitly unclassified.
    kernel_type = str(row.get("type") or row.get("Type") or "").strip().lower()
    if kernel_type == "slice":
        return None if "inplacecopy" in text else "slice"
    if "groupedmatmul" in text or "groupedgemm" in text:
        return "grouped_matmul"
    if "quantbatchmatmul" in text or "quantmatmul" in text:
        return "quant_batch_matmul"
    if "batchmatmul" in text:
        return "batch_matmul"
    if "moedistributedispatch" in text:
        return "moe_distribute_dispatch"
    if "moedistributecombine" in text:
        return "moe_distribute_combine"
    if "lightningindexer" in text:
        return "lightning_indexer"
    if "sparseflashmla" in text:
        return "sparse_flash_mla"
    if "chunkkda" in text or "chunkgateddeltarule" in text:
        return "chunk_kda"
    if "fusedrecurrentgdn" in text or "fusedrecurrentgateddeltarule" in text \
            or "recurrentkda" in text:
        return "recurrent_kda"
    if "causalconv1d" in text or "conv1d" in text:
        return "causal_conv1d"
    if "fusedinferattention" in text or "flashattention" in text:
        return "flash_attention"
    if "pagedattention" in text:
        return "paged_attention"
    if "addrmsnorm" in text:
        return "add_rms_norm"
    if "qkrmsnorm" in text:
        return "qk_rms_norm"
    if "rmsnorm" in text:
        return "rms_norm"
    if "matmul" in text or "gemm" in text:
        return "matmul"
    if "allreduce" in text or "allgather" in text or "reducescatter" in text:
        return "collective"
    if "alltoall" in text:
        return "collective"
    if "broadcast" in text:
        return "collective"
    if "geglu" in text:
        return "geglu"
    if "siluandmul" in text or "swiglu" in text:
        return "swiglu"
    if "silu" in text or "swish" in text:
        return "silu_and_mul"
    if text in {"mul", "add"} or text.endswith("mul") or text.endswith("add"):
        return "swiglu"
    if "rotary" in text or "rope" in text:
        return "rotary_position_embedding"
    if "dynamicquant" in text:
        return "dynamic_quant"
    if "topksoftmax" in text or "gating" in text:
        return "moe_gating_topk_softmax"
    return None


__all__ = [
    "AbiError", "Slot", "apply_spec_names", "classify", "resolve_op_spec",
    "slot_records",
]
