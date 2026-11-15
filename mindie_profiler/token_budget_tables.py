"""Static calibrated protocol vocabulary tables for BPE token upper bounds.

[Role]
  Store pre-verified ``cl100k_base`` and ``o200k_base`` token maxima for finite
  MCP protocol keys, schemas, status codes, issue identifiers and operator names.

[Invariants]
  * Every entry is a fixed protocol literal; caller-supplied strings and paths
    never consult these tables directly without exact-match gating.
  * Whitelists and field-projection sets remain immutable ``frozenset``/``tuple``
    collections.

[Timeouts & Locks]
  Import-time constant construction only; no I/O or locks.

[Side-Effect Policy]
  Pure constant tables; no external state.
"""

from __future__ import annotations

_KEY_TABLE = (
    "abi_id:4 aliases:3 api:3 artifact:3 artifact_id:4 artifact_path:4"
    " artifact_path_omitted:7 attr_slots:4 attrs:3 basis:3 buckets:4 bytes:3"
    " c_abi_slots:6 c_name:4 call:3 capture_path:4 capture_verified:4 cat:3"
    " catalog_sha256:5 catalog_sha256_16:7 charges:3 charges_count:4 checks_ok:4 code:3"
    " complete:3 conditional:3 constraints:3 detail:3 details:3 diff_schema:4"
    " digest:3 dtype:3 dtypes:4 effective_tokens:4 end:3 entry:3"
    " error:3 evidence:4 family:3 fidelity:4 flatten_adapter:4 inline_script_omitted:7"
    " input_slots:4 inputs:3 issue_count:4 issues:3 issues_omitted:6 issues_truncated_count:6"
    " index_persisted:6 index_warning:4 items:3 keyword:3 kind:3 layout:3 layouts:3 level:3"
    " limitation:4 line_count:4 manifest_path:4 manifest_sha256:5 message:3 metadata:3"
    " next_page:4 page:3"
    " mutable:3 mutable_aliases:5 name:3 notes:3 observed_ms:5 op:3"
    " op_name:4 optional:3 output_buffers:4 output_slots:4 outputs:3 padding:3"
    " padding_charges_count:6 padding_semantics:5 padding_valid:4 parameters:3 params:3 persisted:4"
    " pinned:4 pipe:3 positional:4 preconditions:4 predicted_ms:5 protected_artifact_target:6"
    " qualification:3 qualification_state:4 rank:3 reason:3 receipt:3 recipe:3"
    " reconciled:5 release_basis:4 repro_recipe:5 repro_sha256:6 repro_status:5 repro_supported:5"
    " required:3 resolved:3 retrievable:5 return_indices:4 returns:3 role:3"
    " schema:3 schema_pinned:5 script:3 script_path:4 script_sha256:5 sha256:4"
    " shape:3 signature:3 signature_status:4 slot:3 slot_specs:4 sources:3"
    " span:3 start:3 status:3 status_code:4 supported:3 surface:3"
    " surface_kind:4 symbol:3 tag:3 tags:3 tensor_specs:4 token_estimate:5"
    " token_limit:4 tokenizer:4 undefined_means_null:6 unsupported_reason:4 valid:3 verified:3"
    " verified_against_capture:6 version_qualified:5 version_supported:4 versions:3 within_budget:4"
)
_VALUE_TABLE = (
    "aclnn_c_api:7 argument_kind_mismatch:6 artifact_digest_mismatch:6 artifact_directory_conflict:6"
    " artifact_identity_truncated:6 artifact_integrity_mismatch:7 artifact_not_found:5 artifact_not_retrievable:7"
    " artifact_paths_not_representable:8 artifact_persistence_failed:6 artifact_write_failed:5 blocked:3"
    " b3:4 bpe/2:6 bpe/3:6 catalog_span:4 colliding_output_paths:6"
    " delivered:4 delivery_blocked:5 delivery_failed:4 descriptor_column_mismatch:6"
    " descriptor_incomplete:5 descriptor_invalid:4 descriptor_not_a_mapping:6 dtype_not_declared:6"
    " dtype_unknown:4 effective_tokens_exceeds_bucket:8 effective_tokens_invalid:5 envelope_budget_exceeded:7"
    " expert_ids_invalid:5 expert_ids_negative:5 failed:3 full_padded_tensor:6"
    " grouped_prefix:4 hccl_collective:6 incomplete:3 integrity_mismatch:6"
    " invalid_array_length:5 invalid_array_order:5 invalid_array_range:5 invalid_artifact_id:6"
    " invalid_attribute_range:5 invalid_attribute_type:5 invalid_attribute_value:5 invalid_occurrence_issue:6"
    " index_persistence_failed:6 invalid_request:4 layout_not_declared:6 masked_varlen:5 mindie-bounded-envelope/1:9"
    " mindie-diff-trace-mcp/1:12 mindie-mcp-envelope/1:9 mindie-op-abi-card/2:10 mindie-op-api-catalog/2:10"
    " mindie-repro-artifact-resolution/1:11 mindie-single-op-repro-manifest/1:12 mindie-single-op-repro/2:10 missing_descriptor_field:5"
    " ready_index_unconfirmed:6"
    " not_found:4 ok:3 output_dir_conflicts_with_registered_artifact:10 padding_validation_failed:5"
    " protected_artifact_target:6 ready:3 reconciled:5 required_positional_absent:7"
    " required_slot_null:5 required_slot_omitted:7 resolved:3 routed_rows_exceed_bucket:8"
    " selector_mismatch:5 span_deficit:5 surplus_slots:5 tensor_list_item_invalid:6"
    " tensor_list_lengths_invalid:6 torch_npu_op:6 unexpected_input_slots:5 unexpected_output_slots:5"
    " unknown_operator_semantics:6 unspecified:4 vllm_ascend_op:9"
)
_KEY_TOKENS = {key: int(count) for key, count in
               (pair.rsplit(":", 1) for pair in _KEY_TABLE.split())}
_VALUE_TOKENS = {value: int(count) for value, count in
                 (pair.rsplit(":", 1) for pair in _VALUE_TABLE.split())}

_ISSUE_CODES = frozenset("""
argument_kind_mismatch artifact_digest_mismatch artifact_directory_conflict
artifact_identity_truncated artifact_integrity_mismatch artifact_not_found
artifact_not_retrievable artifact_paths_not_representable
artifact_persistence_failed artifact_write_failed colliding_output_paths
descriptor_column_mismatch descriptor_incomplete descriptor_invalid
descriptor_not_a_mapping dtype_not_declared dtype_unknown
effective_tokens_exceeds_bucket effective_tokens_invalid
expert_ids_invalid expert_ids_negative invalid_array_length
invalid_array_order invalid_array_range invalid_attribute_range
invalid_attribute_type invalid_attribute_value invalid_occurrence_issue
invalid_request invalid_artifact_id layout_not_declared
missing_descriptor_field output_dir_conflicts_with_registered_artifact
padding_validation_failed protected_artifact_target
required_positional_absent required_slot_null required_slot_omitted
routed_rows_exceed_bucket selector_mismatch span_deficit surplus_slots
tensor_list_item_invalid tensor_list_lengths_invalid
unexpected_input_slots unexpected_output_slots unknown_operator_semantics
unspecified
""".split())

_CORE_STRING_KEYS = frozenset({
    "schema", "status", "error", "artifact_id", "repro_sha256",
    "script_sha256", "manifest_sha256", "digest", "sha256",
    "artifact_path", "manifest_path", "script_path", "capture_path",
    "index_warning",
})
_PATH_KEYS = frozenset({"artifact_path", "manifest_path", "script_path"})
_FLAG_KEYS = frozenset({
    "reconciled", "persisted", "retrievable", "within_budget", "resolved",
    "protected_artifact_target", "artifact_path_omitted",
    "inline_script_omitted", "padding_valid", "checks_ok", "syntax_ok",
    "run_evidence_blocked", "usable_for_link_override", "complete",
    "schema_pinned", "capture_verified", "version_qualified",
    "version_supported", "repro_supported", "index_persisted",
})
_KNOWN_KEYS = frozenset({
    "schema", "status", "error", "artifact_id", "repro_sha256",
    "script_sha256", "manifest_sha256", "artifact_path", "manifest_path",
    "script_path", "retrievable", "persisted", "reconciled", "resolved",
    "issues", "receipt", "issue_count", "issues_truncated_count",
    "issues_omitted", "artifact_path_omitted", "protected_artifact_target",
    "artifact", "padding", "padding_valid", "padding_charges_count",
    "reason", "detail", "details", "code", "name", "slot", "valid",
    "charges", "charges_count", "effective_tokens", "version_qualified",
    "version_supported", "inline_script_omitted", "bytes", "kind", "span",
    "api", "fidelity", "line_count", "checks_ok", "metadata", "buckets",
    "observed_ms", "predicted_ms", "diff_schema", "abi_id", "signature",
    "schema_pinned", "capture_verified", "qualification_state",
    "qualification", "release_basis", "complete", "repro_supported",
    "repro_status", "surface", "pipe", "versions", "pinned", "inputs",
    "outputs", "attrs", "recipe", "catalog_sha256_16", "catalog_sha256",
    "constraints", "entry", "cursor", "items", "page", "next", "next_page",
    "index_persisted",
    "index_warning",
})
_OPTIONAL_DROP = (
    "reason", "fidelity", "line_count", "checks_ok", "metadata",
    "buckets", "observed_ms", "predicted_ms", "details", "detail",
    "padding_charges_count", "issue_count", "issues_truncated_count",
    "release_basis", "qualification_state", "padding",
)
_ARTIFACT_KEYS = frozenset({
    "sha256", "bytes", "retrievable", "inline_script_omitted", "kind",
    "span", "catalog_sha256_16", "catalog_sha256",
})
_PADDING_KEYS = frozenset({"valid", "charges", "charges_count"})
_CHARGE_KEYS = frozenset({
    "effective_tokens", "version_qualified", "version_supported",
})
_SCHEMA_WHITELIST = frozenset({
    "mindie-single-op-repro/2", "mindie-op-abi-card/2",
    "mindie-repro-artifact-resolution/1", "mindie-diff-trace-mcp/1",
    "mindie-bounded-envelope/1", "mindie-mcp-envelope/1",
    "mindie-single-op-repro-manifest/1", "mindie-op-api-catalog/2",
})
_STATUS_WHITELIST = frozenset({
    "ready", "blocked", "delivered", "delivery_blocked", "delivery_failed",
    "invalid_request", "resolved", "not_found", "integrity_mismatch",
    "reconciled", "incomplete", "failed", "ok", "partial", "exists",
    "artifact_not_found", "artifact_integrity_mismatch",
    "ready_index_unconfirmed",
})


_PATH_SUFFIX_TOKENS = {"/repro.py": 3, "/manifest.json": 3, "/diff.json": 3}

KNOWN_TOKEN_COUNTS: dict[str, int] = {
    "mindie-op-formula-mcp/1": 9, "clean": 1, "unmeasured": 3,
    "bound_violation": 4, "violations_detected": 4, "invalid_input": 2,
    "invalid_abi": 3, "invalid_request": 2, "unmodeled": 3, "ok": 1,
    "cross_op_l2_hit": 5, "unfiltered_padding_shape_bound": 5,
    "async_overlap_shadowed": 4, "wrong_sku_spec": 4, "schema": 1,
    "status": 1, "operator": 1, "family": 1, "variant": 1, "canonical_op": 2,
    "raw_op_preview": 3, "t_floor_us": 3, "t_ref_us": 3, "measured_us": 3,
    "sol_floor_pct": 3, "ref_ratio": 2, "bottleneck_pipe": 4,
    "structural_gap_us": 4, "impl_headroom_us": 4, "bound_violation_warning": 5,
    "root_cause_candidates": 4, "total_rows": 2, "modeled_rows": 3,
    "unmodeled_rows": 4, "invalid_rows": 2, "violation_count": 3,
    "clean_rows": 2, "codes_truncated": 3, "total_code_count": 3,
    "worst_ratio": 3, "root_cause_codes": 4, "sample_rows": 2,
    "sample_rows_returned": 4, "rows_omitted": 4, "rows": 1, "receipt": 1,
    "tokenizer": 2, "token_estimate": 3, "token_limit": 2, "within_budget": 2,
    "reason": 1, "code": 1, "usage": 1, "alg_flops": 3,
    "cube_flops_tiled": 5, "compulsory_gm_bytes": 6, "granule_gm_bytes": 5,
    "alg_flops_expr": 4, "error": 1, "mindie-bpe-upper/2": 7, "true": 1,
    "false": 1, "null": 1, "aclnnFlashAttentionScore": 6,
    # Canonical operator / stable-code literals (max over both encoders).
    "add_rms_norm": 4, "argmax": 2, "causal_conv1d": 5,
    "chunk_gated_delta_rule": 5, "chunk_kda": 3, "composite_chain": 3,
    "dequant_swiglu_quant": 6, "dynamic_quant": 2, "embedding": 1,
    "flash_attention": 2, "fused_infer_attention_score": 6,
    "fused_recurrent_gdn": 6, "geglu": 3, "grouped_matmul": 4,
    "hccl_all_gather": 5, "hccl_all_reduce": 4, "hccl_all_to_all": 5,
    "hccl_broadcast": 4, "hccl_reduce_scatter": 5,
    "incre_flash_attention": 4, "kda_recover_ssm_commit": 7,
    "kda_recover_ssm_verify": 7, "lightning_indexer": 4, "lm_head": 2,
    "logits_matmul": 4, "matmul": 2, "mla_prolog": 4,
    "moe_distribute_combine": 6, "moe_distribute_dispatch": 5,
    "moe_finalize_routing": 5, "moe_gating_topk_softmax": 8,
    "moe_init_routing": 5, "paged_attention": 2, "qk_rms_norm": 5,
    "quant_batch_matmul": 4, "recurrent_kda": 4, "rms_norm": 3,
    "rotary_position_embedding": 4, "silu_and_mul": 4,
    "sparse_flash_mla": 5, "swiglu": 3, "top_p_sample": 3,
    "vocab_parallel_embedding": 4, "validation_error": 2,
    "formula_error": 2, "unsupported_operator": 2, "invalid_request": 2,
    "unmodeled_op": 4, "path_hidden": 2,
    # Stable diagnostic codes and bounded-envelope field names.  Each value is
    # the measured maximum over cl100k_base and o200k_base for that fixed
    # literal;  arbitrary strings are still charged their exact UTF-8 bytes.
    "gemm_k_mismatch": 5, "gemm_output_shape": 4, "invalid_world_size": 3,
    "kv_head_mismatch": 4, "missing_tensor_slot": 3,
    "unclassified_kernel": 3, "unknown_attention_layout": 3,
    "unsupported_mixed_dtype": 4, "error_codes": 2, "root_cause_codes": 4,
    "sample_rows_returned": 4, "total_code_count": 3, "codes_truncated": 3,
    "worst_ratio": 3, "modeled_rows": 3, "sample_rows": 2, "rows_omitted": 4,
    "non_floating_dtype": 4, "norm_gamma_shape": 3, "norm_output_shape": 3,
    "quant_scale_shape": 3, "invalid_topk": 3, "activation_output_shape": 3,
    "activation_second_operand": 3, "chunk_output_shape": 3,
    "all_gather_volume": 4, "reduce_scatter_volume": 4,
    "unsupported_quant_scale": 3, "activation_scale_shape": 3,
    "grouped_scale_shape": 4, "invalid_tensor_slot": 3,
    "missing_input_shapes": 3, "unsupported_formula_family": 3,
    "rejected_capture_row": 4, "invalid_sequence_lengths": 3,
    "invalid_boolean_attribute": 3, "invalid_integer_attribute": 3,
    "unsupported_quant_contract": 3, "unknown_dtype": 2,
    "invalid_padding_contract": 3, "q_head_mismatch": 4,
    "contradictory_attention_layout": 6, "unsupported_attention_layout": 3,
    "indexer_length_arity": 5, "invalid_causal_offset": 4,
    "kv_sequence_mismatch": 4, "head_ownership": 3,
    "output_sequence_mismatch": 4, "output_head_mismatch": 4,
    "output_head_dim_mismatch": 5, "qkv_batch_mismatch": 5,
    "mixed_attention_layout": 3, "gemm_batch_mismatch": 5,
    "batch_matmul_rank": 4,
}
