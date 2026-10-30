"""GLM packed-cache ABI correspondence for explicit analytic source programs.

[Role] Match complete retained INT8-528 sparse-MLA buckets to existing Sim ops.
[Invariants] No 672-byte/rope64 kernel is claimed for the observed rope0 ABI.
  Tensor capacities do not prove valid indices, cache contents or tensor aliasing.
  One native batch maps to all declared sequences; references remain conditional.
[Timeouts & Locks] Finite metadata checks only; no locks or subprocesses.
[Side-Effect Policy] Pure selector; no captures, timing fits or Sim mutations.
"""
from glm_native_references import SELECTORS as BASE_SELECTORS, _slot


def packed_sparse(native, local, groups, execution):
    ins, outs = native[2:]
    if (len(ins), len(outs)) != (9, 3):
        raise ValueError("packed_sparse_native_slot_count")
    query, key, value, indices, qrope, krope, table, query_lengths, cache_lengths = ins
    batch, q = execution["sequences"], execution["tokens"]
    if (len(query[0]) != 3 or len(key[0]) != 4 or len(indices[0]) != 3
            or len(table[0]) != 2):
        raise ValueError("packed_sparse_native_rank")
    rows, heads, latent = query[0]
    if (rows != batch*q or latent != 512 or not 1 <= heads <= 16
            or not _slot(query, (rows, heads, latent), "bf16")
            or outs[0] != query or outs[1:] != (((), "fp32", "ND"),)*2
            or key[0][1:] != (128, 1, 528) or key[1:] != ("int8", "ND")
            or value != key or qrope != ((), None, None) or krope != ((), None, None)
            or not _slot(indices, (rows, 1, indices[0][2]), "int32")
            or not _slot(table, (batch, table[0][1]), "int32")
            or not _slot(query_lengths, (batch,), "int32")
            or not _slot(cache_lengths, (batch,), "int32")):
        raise ValueError("packed_sparse_int8_528_rope0_abi")
    targets = [t for t in local if t["family"] == "attention"
               and t["operator"]["metadata"].get("program_kind") == "indexed_attention"]
    if not targets:
        raise ValueError("packed_sparse_declared_program_missing")
    sequences, topks = [], set()
    for target in targets:
        geometry = target["operator"]["metadata"]["indexed_attention_geometry"]
        if ((geometry["heads"], geometry["latent"], geometry["rope"],
             geometry["query_dtype"], geometry["cache_dtype"], geometry["compression_ratio"],
             geometry["window"], geometry["cp"]) != (heads, 512, 0, "bf16", "int8", 1, 0, 1)):
            raise ValueError("packed_sparse_declared_channel_precision")
        sequences.extend(tuple(item) for item in geometry.get(
            "sequences", [(geometry.get("query"), geometry.get("context"))]))
        topks.add(geometry["topk"])
    if sequences != [(q, execution["context"])]*batch:
        raise ValueError("packed_sparse_declared_batch_coverage")
    if len(topks) != 1 or indices[0][2] < next(iter(topks)):
        raise ValueError("packed_sparse_declared_topk_exceeds_index_capacity")
    return "indexed_attention_batch", targets, {
        "kind": "existing_declared_packed_int8_analytic_program",
        "capture_binary_identity": "not_established"}, {
        "boundary_relation": "whole_batch_packed528_int8_analytic_reference",
        "observed_cache_row_bytes": 528, "observed_rope_descriptors": [qrope, krope],
        "observed_sparse_index_capacity": indices[0][2], "declared_topk": next(iter(topks)),
        "declared_sequence_count": batch, "declared_sequence_program_count": len(targets),
        "observed_index_values": None, "observed_sequence_length_values": None,
        "observed_scale_values": None, "observed_key_value_address_alias": None,
        "observed_cache_capacity_is_active_context": False,
        "limitations": [
            "The 528-byte row is compatible with the explicit analytic 512 INT8 + four FP32-scale declaration; scale offsets and values are not captured.",
            "The retained arch22 672-byte/rope64 kernel is not this native rope0 ABI and is not claimed as the captured binary.",
            "Key/value descriptors agree; physical aliasing follows the caller declaration, not observed addresses.",
            "Sparse valid indices, sequence lengths, masks and private dispatch/tiling remain unobserved.",
            "The complete declared batch program set is a conditional service reference, not strict native accuracy."]}


SELECTORS = {**BASE_SELECTORS, "KvQuantSparseFlashAttentionVllm": packed_sparse}
