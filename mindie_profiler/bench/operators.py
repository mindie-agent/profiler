"""Canonical 1:1 operator-builder registry and fail-fast structure resolver.

[Role]
  Assemble the 101+ canonical NPU/HCCL/Triton/``fla`` operator builders across
  ``operators_norm_quant``, ``operators_attention_mla``, ``operators_moe_comm``
  and ``operators_recurrent_mhc``, and enforce 1:1 fail-fast resolution for
  every non-control ``(family, recipe, implementation)`` triple.

[Invariants]
  * Every non-control operator resolves to a real fused kernel builder;
    unknown builders or missing runtime kernels raise
    ``BenchUnmodeledOperatorError`` (``UnmodeledCapabilityError``) carrying a
    ``mindie-unmodeled-structure-hint/1`` JSON payload.
  * Zero ``inspect.signature`` calls and zero composite PyTorch fallbacks
    anywhere in the operator stack.

[Timeouts & Locks]
  Pure setup outside the timed window; no locks or threads.

[Side-Effect Policy]
  Allocates tensors and enqueues work only on the caller-provided ``torch``.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from .operators_attention_mla import ATTENTION_MLA_BUILDERS
from .operators_common import (
    BenchUnmodeledOperatorError,
    DTYPE_NAMES,
    ELEMENT_BYTES,
    OP_CFG,
    UNMODELED_HINT_SCHEMA,
    UnmodeledCapabilityError,
    device_of,
    element_bytes,
    has_npu_surface,
    raise_unmodeled,
    resolve_op,
    torch_dtype,
    unmodeled_payload,
    upstream_input,
)
from .operators_moe_comm import (
    COLLECTIVE_ALIASES,
    COLLECTIVE_OPS,
    MOE_COMM_BUILDERS,
    _bind_collective,
)
from .operators_norm_quant import NORM_QUANT_BUILDERS
from .operators_recurrent_mhc import RECURRENT_MHC_BUILDERS

CONTROL_FAMILIES = frozenset({"barrier", "event", "hccl_boundary"})
_MEGAMOE_MODES = frozenset(int(x) for x in OP_CFG["megamoe_modes"])
_MEGAMOE_UNPERMUTE = int(OP_CFG["megamoe_unpermute_mode"])
_GEMM_RECIPES = frozenset({
    "", "linear", "matmul", "bmm", "gemm", "qkv", "q_proj", "k_proj", "v_proj",
    "o_proj", "gate_up", "up_proj", "down_proj", "lm_head", "logits", "router",
    "eh_proj", "mla_q", "mla_kv", "dense", "quant_linear", "w8a8", "w4a8", "w4a16",
    "q_a", "q_b", "kv_a", "q_absorb", "v_expand", "output", "draft_features",
    "index_q", "index_k", "index_weights", "index_query_hadamard",
    "index_key_hadamard", "hc_lowrank_up", "hc_lowrank_down_inject",
    "grouped_output_a", "grouped_output_b", "gate", "up", "down", "engram_q_gate",
})
_GEMM_RECIPE_TOKENS = ("proj", "linear", "matmul", "gemm", "head", "router")
_GEMM_IMPL_PREFIXES = ("aclnn", "torch", "npu", "atb", "cann", "triton", "vllm", "hccl", "fla")
_DENSE_GEMM_FAMILIES = frozenset({
    "gemm", "qkv_projection", "output_projection", "gate_up_projection",
    "down_projection", "index_projection", "gate_projection", "projection",
    "router", "logits", "attention_qk", "attention_pv", "vision_merge",
})
_VALIDATED_GEMM_FAMILIES = frozenset({"gemm", "matmul", "linear"})
_UNQUANTIZED_GEMM_ROLES = frozenset({
    "router", "logits", "attention_qk", "attention_pv", "vision_merge",
})


def build_graph_boundary(
    _torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    """No-op control-plane node: pass any upstream operand through untouched."""
    return lambda: upstream_input(case, context)


OPERATOR_BUILDERS: dict[str, Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]] = {
    **NORM_QUANT_BUILDERS,
    **ATTENTION_MLA_BUILDERS,
    **MOE_COMM_BUILDERS,
    **RECURRENT_MHC_BUILDERS,
    "graph_boundary": build_graph_boundary,
}

_PROBE_ALIASES = frozenset(
    {
        "empty_event_pair",
        "empty_launch",
        "mte2_transfer",
        "pinned_copy",
        "noop_probe",
        "stream_read_probe",
        "send_recv",
        "graph_boundary",
        *COLLECTIVE_ALIASES.keys(),
    }
    - {"all_reduce", "all_gather", "reduce_scatter", "all_to_all_v"}
)
CANONICAL_BUILDERS: frozenset[str] = frozenset(
    name for name in OPERATOR_BUILDERS if name not in _PROBE_ALIASES
)
RING_BUILDERS: frozenset[str] = frozenset(
    name
    for name in OPERATOR_BUILDERS
    if name not in {"empty_event_pair", "empty_launch", "mte2_transfer", "noop_probe", "graph_boundary"}
)
_OP_ALIASES: dict[str, str] = {
    "cube_matmul": "matmul",
    "w8a8_matmul": "quant_matmul",
    "npu_quant_matmul": "quant_matmul",
    "npu_grouped_matmul": "grouped_matmul",
    "npu_fusion_attention": "fusion_attention",
    "npu_fused_infer_attention_score": "fused_infer_attention",
    "npu_incre_flash_attention": "incre_flash_attention",
    "npu_chunk_gated_delta_rule": "chunk_gated_delta_rule",
    "index_add_": "index_add",
    "gather": "strided_gather",
    "mte2_aic": "mte2_transfer",
    "mte2_aiv": "mte2_transfer",
    "npu_rms_norm": "rms_norm",
    "npu_add_rms_norm": "add_rms_norm",
    "npu_swiglu": "swiglu",
    "npu_geglu": "geglu",
    "npu_moe_gating_top_k_softmax": "moe_gating_topk",
    "npu_moe_init_routing_v2": "moe_init_routing",
    "npu_moe_distribute_dispatch_v2": "mc2_dispatch",
    "npu_moe_distribute_combine_v2": "mc2_combine",
}


def resolve_builder_strict(
    family: str,
    recipe: str,
    impl: str,
    dtypes: Sequence[str] = (),
    meta: Mapping[str, Any] | None = None,
    *,
    model_id: str = "",
    layer_idx: int = -1,
    local_shape: Sequence[int] | None = None,
) -> tuple[str, str]:
    """Return ``(builder_name, upstream_abi)`` or raise ``BenchUnmodeledOperatorError``."""
    meta_map = meta or {}
    fam = (family or "").strip()
    rec = (recipe or "").strip()
    imp = (impl or "").strip()
    has_quant = (
        any(d in {"int8", "int4", "w4a8", "w4a16", "fp8_e4m3", "mxfp8", "mxfp4"} for d in dtypes)
        or str(meta_map.get("weight_format") or "")
        in {"int8", "int4", "w4a8", "w4a16", "fp8_e4m3", "mxfp8", "mxfp4"}
        or str(meta_map.get("dequant") or "") not in {"", "none"}
    )

    if fam in CONTROL_FAMILIES:
        return ("graph_boundary", fam)
    if fam == "sp_matmul_collective" or rec == "sp_matmul_collective_pipeline":
        if "pipeline_gather" in meta_map or "pipeline_scatter" in meta_map:
            pipeline_gather = bool(meta_map.get("pipeline_gather")) and not bool(
                meta_map.get("pipeline_scatter")
            )
            direction = "all_gather" if pipeline_gather else "reduce_scatter"
        else:
            direction = str(meta_map.get("sp_collective_kind") or "")
        if "all_gather" in direction or "allgather" in direction:
            return ("all_gather_matmul", "aclnnAllGatherMatmul")
        return ("matmul_reduce_scatter", "aclnnMatmulReduceScatter")
    if fam == "mc2_protocol":
        if "Dispatch" in imp or "dispatch" in rec:
            return ("mc2_dispatch_v3", "aclnnMoeDistributeDispatchV3")
        if "Combine" in imp or "combine" in rec:
            return ("mc2_combine_v3", "aclnnMoeDistributeCombineV3")
    if fam in {"alltoall", "alltoallv"}:
        if int(meta_map.get("mc2_mode") or 0) in _MEGAMOE_MODES:
            return ("megamoe_fused_mc2", "aclnnMegaMoe")
        if rec == "expert_dispatch":
            return ("mc2_dispatch", "aclnnMoeDistributeDispatchV2")
        if rec == "expert_combine":
            return ("mc2_combine", "aclnnMoeDistributeCombineV2")
        if rec == "all_to_all":
            return ("all_to_all", "hcclAlltoAll")
        return ("all_to_all_v", "hcclAlltoAllV")
    if fam in {"allgather", "engram_broadcast", "dcp_allgather"}:
        return ("all_gather", "hcclAllGather")
    if fam == "engram_ids":
        return ("all_to_all_v", "hcclAlltoAllV")
    if fam in {"allreduce", "tp_allreduce"}:
        if (
            meta_map.get("quantized_all_reduce")
            or meta_map.get("quantized_all_reduce_applied")
            or "quant" in rec
        ):
            return ("quantized_all_reduce", "hcclAllReduceInt8")
        return ("all_reduce", "hcclAllReduce")
    if fam == "reduce_scatter":
        return ("reduce_scatter", "hcclReduceScatter")
    if fam in {"pp_p2p", "cache_transfer", "state_publish"}:
        return ("p2p_send_recv", "hcclSendRecv")

    if fam == "add_rmsnorm_quant":
        return ("add_rms_norm_quant", "aclnnAddRmsNormDynamicQuantV2")
    if fam == "rmsnorm_quant":
        if (
            meta_map.get("residual")
            or meta_map.get("fused_add")
            or "residual" in rec
            or "fused_add" in rec
        ):
            return ("add_rms_norm_quant", "aclnnAddRmsNormDynamicQuantV2")
        return ("rms_norm_quant", "aclnnRmsNormDynamicQuant")
    if fam == "add_rmsnorm":
        return ("add_rms_norm", "aclnnAddRmsNorm")
    if fam == "rmsnorm":
        return ("gemma_rms_norm", "aclnnGemmaRmsNorm") if "gemma" in rec else ("rms_norm", "aclnnRmsNorm")
    if fam == "layernorm":
        return ("layer_norm", "aclnnLayerNorm")

    if fam == "swiglu":
        return ("swiglu_oai", "aclnnSwiGluOai") if "oai" in rec else ("swiglu", "aclnnSwiGlu")
    if fam == "geglu":
        return ("geglu", "aclnnGeGluV2")
    if fam == "gelu":
        return ("gelu", "aclnnGelu")
    if fam == "situ":
        return ("situ_activation", "aclnnSitu")
    if fam == "activation" and rec == "hc_silu":
        return ("silu_mul", "aclnnSilu")
    if fam == "sigmoid":
        return ("sigmoid", "aclnnSigmoid")
    if fam in {"softmax", "attention_softmax"}:
        return ("softmax", "aclnnSoftmaxV2")
    if fam == "dequant_swiglu_quant":
        return ("dequant_swiglu_quant", "aclnnDequantSwigluQuant")
    if fam == "quantize":
        if rec == "swiglu_quantize":
            return ("swiglu_dynamic_quant", "aclnnSwigluQuant")
        if rec == "situ_quantize":
            return ("dequant_situ_quant", "aclnnDequantSituQuant")
        if rec in {"dynamic_quantize", "index_query_quantize"}:
            return ("dynamic_quant", "aclnnDynamicQuantV2")
        if rec in {"dynamic_quant", "quantize", "per_token_quant"}:
            return ("dynamic_quant", "aclnnDynamicQuantV2")

    if fam == "grouped_gemm" or (fam == "gemm" and rec in {"grouped_output_a", "grouped_output_b"}):
        if meta_map.get("onchip_handoff_to"):
            return ("grouped_matmul_swiglu_quant", "aclnnGroupedMatmulSwigluQuantWeightNZ")
        return ("grouped_matmul", "aclnnGroupedMatmulV5")

    if fam == "mla" and rec == "draft_context_mla_prolog_v3":
        return ("mla_prolog_v3", "aclnnMlaPrologV3WeightNz")
    if fam == "mla_prolog" or rec in {"mla_prolog_v2", "mla_prolog", "mla_preprocess"}:
        return ("mla_prolog_v2", "aclnnMlaPrologV2WeightNz")
    if fam == "compressed_attention" and rec == "aclnn_compressor":
        return ("mla_kv_compressor", "aclnnCompressor")
    if fam == "attention_merge":
        return ("dcp_lse_attention_merge", "aclnnRingAttentionUpdate")
    if fam == "attention":
        if rec == "aclnn_mixed_quant_sparse_flash_mla" or imp == "aclnnMixedQuantSparseFlashMla":
            return ("mixed_quant_sparse_mla", "aclnnMixedQuantSparseFlashMla")
        if rec in {"sparse_flash_attention", "dsa_sparse_attention"} or imp == "SparseFlashAttention":
            return ("sparse_flash_attention", "aclnnSparseFlashAttention")
        if rec in {
            "ascend_paged_mla_decode_arch22",
            "ascend_paged_mla_decode_arch35",
            "latent_attention0",
            "latent_attention_batch",
            "paired_mla_attention_analytic",
        }:
            return ("absorbed_mla", "aclnnFusedInferAttentionScoreV4")
        if str(meta_map.get("cache_layout") or "") == "int8_fa3" or rec in {
            "gbsa_attention",
            "generic_block_sparse_attention",
        }:
            return ("block_sparse_attention_c8", "aclnnGenericBlockSparseAttention")
        if rec == "flash_attention_decode":
            return ("incre_flash_attention", "aclnnFusedInferAttentionScoreV3")
        if rec in {"flash_attention", "flash_attention_prefill"}:
            return ("fusion_attention", "aclnnFlashAttentionVarLenScoreV2")
        if rec == "fused_infer_attention":
            return ("fused_infer_attention", "aclnnFusedInferAttentionScoreV3")

    if fam == "indexer":
        if rec == "cann_pool_key_indexer" or imp == "PoolKeyIndexer":
            return ("pool_key_indexer", "aclnnPoolKeyIndexer")
        if rec in {"quant_lightning_indexer", "index_scores", "index_online_topk"}:
            return ("lightning_indexer", "aclnnQuantLightningIndexerV2")
    if fam == "indexer_quant_cache":
        return ("indexer_quant_cache", "aclnnIndexerQuantCache")
    if fam == "key_pool":
        return ("key_pool", "aclnnKeyPool")
    if fam == "kv_compress_epilog":
        return ("kv_compress_epilog", "aclnnKvCompressEpilog")
    if fam == "histogram":
        return ("histogram_v2", "aclnnHistogramV2")
    if fam == "cache_store":
        if rec in {"kv_store", "draft_context_kv_scatter"}:
            return ("scatter_pa_kv_cache", "aclnnScatterPaKvCache")
        if rec in {"index_store", "cann_keypool_cache_write"}:
            return ("scatter_index_cache", "aclnnScatterNdUpdate")
    if fam == "topk":
        if rec == "moe_gating_topk":
            if "Hash" in imp:
                return ("moe_gating_topk_hash", "aclnnMoeGatingTopKHash")
            return ("moe_gating_topk", "aclnnMoeGatingTopKSoftmaxV2")
        if rec in {
            "index_topk",
            "index_online_topk",
            "router_expert_topk",
            "router_group_score_top2",
            "router_group_topk",
        }:
            return ("indexer_topk", "aclnnTopkV2")

    if fam == "routing":
        if rec == "moe_init_routing_v3":
            return ("moe_init_routing", "aclnnMoeInitRoutingV3")
        if rec == "route_pack":
            return ("moe_token_permute", "aclnnMoeTokenPermute")
        if rec == "router_weight_gather":
            return ("strided_gather", "aclnnGatherElements")
        if rec == "route_unpack":
            if int(meta_map.get("mc2_mode") or 0) == _MEGAMOE_UNPERMUTE:
                return ("megamoe_fused_mc2", "aclnnMegaMoe")
            return ("moe_token_unpermute", "aclnnMoeTokenUnpermute")
    if fam == "moe_init_routing":
        return ("moe_init_routing", "aclnnMoeInitRoutingV3")

    if fam == "rotary" or (fam == "elementwise" and rec == "rotary"):
        if rec in {
            "split_qkv_rmsnorm_mrope_fused",
            "split_qkv_rmsnorm_rope_fused",
            "split_qkv_rmsnorm_rope_vnorm_fused",
        }:
            return ("split_qkv_rmsnorm_rope", "split_qkv_rmsnorm_mrope_kernel")
        return ("rotary_embedding", "aclnnApplyRotaryPosEmbV2")

    if fam == "causal_conv1d_fn":
        return ("causal_conv1d_fn", "aclnnCausalConv1d")
    if fam in {"short_convolution", "conv1d"} or (fam == "elementwise" and rec == "short_convolution"):
        return ("causal_conv1d_update", "aclnnCausalConv1dUpdate")
    if fam == "gdn_gating" or (fam == "elementwise" and rec == "delta_gates"):
        return ("fused_gdn_gating", "fused_gdn_gating_kernel")
    if fam == "gdn_prefill" and rec == "gdn_phase6_arch22":
        return ("chunk_gated_delta_rule", "aclnnChunkGatedDeltaRuleFwd")
    if fam == "gdn_prepare":
        return ("chunk_gdn_fwd_prepare", "aclnnChunkGatedDeltaRuleFwdPrepare")
    if fam == "gdn_state":
        return ("chunk_gdn_fwd_h", "aclnnChunkFwdH")
    if fam == "gdn_output":
        return ("chunk_gdn_fwd_o", "aclnnChunkFwdO")
    if fam == "recurrent_vector":
        if "recover_ssm" in rec or meta_map.get("recover_ssm"):
            return ("recurrent_gdn_recover_ssm", "aclnnRecurrentGatedDeltaRule")
        return ("recurrent_gated_delta_rule", "aclnnRecurrentGatedDeltaRule")
    if fam in {"recurrent_scan", "kda_recurrent"}:
        if "kda" in rec or "kda" in imp.lower():
            return ("fused_recurrent_kda", "aclnnRecurrentKda")
        return ("recurrent_gated_delta_rule", "aclnnRecurrentGatedDeltaRule")
    if fam == "recurrent_local":
        if rec.startswith("chunk_products") or "chunk_kda_gate_prepare" in rec:
            return ("kda_chunk_products", "aclnnChunkKdaFwdPrepare")
        if rec.startswith("wy_transform"):
            return ("kda_wy_transform", "recompute_w_u_fwd_kernel")
    if fam == "recurrent_output" and rec.startswith("recurrent_output"):
        return ("kda_chunk_output", "aclnnChunkKdaFwdFinalize")
    if fam == "triangular_solve":
        return ("kda_triangular_solve", "solve_tril_16x16_kernel")
    if fam == "state_gather" or (fam == "copy" and rec == "cann_keypool_state_gather"):
        return ("ssm_state_gather", "_gather_ssm_states_kernel")
    if fam == "state_scatter" or (fam == "elementwise" and rec == "recover_ssm_commit"):
        return ("ssm_state_scatter", "_scatter_ssm_states_kernel")

    if fam == "mhc":
        if rec in {"hc_pre_fused", "hc_pre"}:
            return ("hc_pre", "aclnnHcPre")
        if rec in {"hc_post_fused", "hc_post"}:
            return ("hc_post", "aclnnHcPost")
        if rec == "hc_combine_norm":
            return ("hc_combine_norm", "_hc_combine_norm_kernel")
        if rec == "mc2_routed_expert_program":
            return ("megamoe_fused_mc2", "aclnnMegaMoe")
        if rec == "hc_sinkhorn":
            raise_unmodeled(
                {
                    "family": fam, "recipe": rec, "implementation": imp,
                    "dtypes": [str(item) for item in dtypes],
                    "metadata": dict(meta_map), "model_id": model_id,
                    "layer_idx": layer_idx, "local_shape": list(local_shape or ()),
                },
                builder="", upstream_abi="",
                reason="unmodeled_structure_triple",
                code="unmodeled_structure_triple",
            )
        return ("mhc_stream_mix", f"mhc_{rec}_kernel")
    if fam == "attn_res_prefix":
        return ("attn_res_prefix", "aclnnAttnResFwd")

    if fam == "engram_gather":
        return ("ple_lookup", "aclnnEmbedding")
    if fam == "engram_query":
        return ("engram_ngram_hash", "engram_ngram_ids_kernel")
    if fam == "engram_rh2d":
        return ("engram_uva_h2d", "aclrtMemcpyAsync")
    if fam == "engram_apply":
        return ("gated_mul_add", "aclnnMul")
    if fam == "embedding":
        return ("vocab_embedding", "aclnnEmbedding")

    if fam == "acceptance" and rec == "speculative_acceptance":
        return ("rejection_sampler", "rejection_sample_kernel")
    if fam in {"sampling", "confidence", "token_commit"}:
        if "reject" in rec:
            return ("rejection_sampler", "rejection_sample_kernel")
        return ("categorical_sampler", "_categorical_sample_kernel")

    if fam in _VALIDATED_GEMM_FAMILIES:
        known_recipe = rec in _GEMM_RECIPES or any(
            token in rec.lower() for token in _GEMM_RECIPE_TOKENS
        )
        known_impl = not imp or imp.lower().startswith(_GEMM_IMPL_PREFIXES)
        if not known_recipe or not known_impl:
            raise_unmodeled(
                {
                    "family": fam, "recipe": rec, "implementation": imp,
                    "dtypes": [str(item) for item in dtypes],
                    "metadata": dict(meta_map), "model_id": model_id,
                    "layer_idx": layer_idx, "local_shape": list(local_shape or ()),
                },
                builder="", upstream_abi="",
                reason="unmodeled_structure_triple",
                code="unmodeled_structure_triple",
            )
        if has_quant:
            return ("quant_matmul", "aclnnQuantMatmulWeightNz")
        return ("matmul", "aclnnMatmul")

    if fam in _DENSE_GEMM_FAMILIES:
        if has_quant and fam not in _UNQUANTIZED_GEMM_ROLES:
            return ("quant_matmul", "aclnnQuantMatmulWeightNz")
        return ("matmul", "aclnnMatmul")

    if fam == "elementwise":
        if "l2norm" in rec:
            return ("l2_norm", "l2norm_fwd_kernel2")
        if rec == "linear_output_norm_gate":
            return ("rms_norm_gated", "_layer_norm_fwd_1pass_kernel_npu")
        if rec in {
            "residual_add",
            "expert_add",
            "draft_feature_add",
            "catalog_engram_residual_add",
            "markov_bias",
            "attention_residual_mix",
            "catalog_aligner_bias",
            "catalog_qwen_merger_bias",
            "catalog_vision_bias",
            "catalog_vision_residual",
            "gemma_gamma_shift",
            "router_correction_bias",
        }:
            return ("vector_add", "aclnnAdd")
        if rec in {"muls_add", "moe_muls_add"}:
            return ("muls_add", "muls_add_kernel")
        if rec in {
            "attention_gate",
            "gated_output",
            "shared_gate_apply",
            "index_key_basis_scale",
            "index_query_basis_scale",
            "route_normalize",
            "router_group_mask",
        }:
            return ("vector_mul_gate", "aclnnMul")
        if rec in {"gdn_packed_prepare", "candidate_blocks"}:
            return ("vector_pack_indices", "aclnnIndexSelect")
    if fam == "pad":
        return ("tensor_pad", "aclnnPadV3")
    if fam == "cast":
        return ("dtype_cast", "aclnnCast")
    if fam in {"tensor_copy", "copy", "tensor_materialization", "tensor_view"}:
        return ("tensor_copy", "aclnnInplaceCopy")
    if fam in {"index_add", "scatter_add"}:
        return ("index_add", "aclnnIndexAdd")
    if fam in {"gather", "strided_gather", "tensor_select"}:
        return ("strided_gather", "aclnnIndexSelect")
    if fam in {"tensor_fill", "zero_fill", "fill"}:
        return ("tensor_fill", "aclnnInplaceZero")

    raise BenchUnmodeledOperatorError(
        {
            "schema": UNMODELED_HINT_SCHEMA,
            "builder": "",
            "upstream_abi": "",
            "reason": "unmodeled_structure_triple",
            "candidates_checked": [],
            "model_id": model_id,
            "layer_idx": layer_idx,
            "family": fam,
            "recipe": rec,
            "implementation": imp,
            "local_shape": list(local_shape or ()),
            "dtypes": [str(item) for item in dtypes],
            "metadata": dict(meta_map),
            "agent_action": (
                "inspect upstream kernel ABI in vllm-ascend/cann/fla and register "
                "explicit PhysicalRecipe + bench operator builder"
            ),
        },
        code="unmodeled_structure_triple",
    )


def _inferred_node_triple(case: Mapping[str, Any]) -> tuple[str, str, str]:
    family = str(case.get("family") or "").strip()
    recipe = str(case.get("recipe") or "").strip()
    impl = str(case.get("implementation") or "").strip()
    op_name = str(case.get("op") or "").strip()
    is_subgraph_node = (
        str(case.get("schema") or "") == "mindie-bench-subgraph-node/1"
        or str(case.get("builder") or "") == "unmapped_catalog_op"
    )
    if not family and ":" in impl:
        fam_part, rec_part = impl.split(":", 1)
        family = fam_part.strip()
        recipe = recipe or op_name or rec_part.strip()
        impl = ""
    elif is_subgraph_node and not family:
        if impl == "aclnnLayerNorm" or op_name == "index_norm":
            family = "layernorm"
        elif op_name == "rmsnorm_quantize":
            family = "rmsnorm_quant"
        elif op_name == "add_rmsnorm_quantize":
            family = "add_rmsnorm_quant"
        elif impl == "RecurrentKda" or "recurrent_kda" in op_name:
            family = "kda_recurrent"
        elif op_name == "moe_gating_topk":
            family = "topk"
        elif op_name == "quant_lightning_indexer":
            family = "indexer"
        elif op_name == "cann_key_pool" or impl == "KeyPool":
            family = "key_pool"
        elif op_name == "attn_res_fwd" or impl == "AttnResFwd":
            family = "attn_res_prefix"
        elif op_name == "aclnn_compressor" or impl == "aclnnCompressor":
            family = "compressed_attention"
        elif op_name == "indexer_quant_cache" or impl == "aclnnIndexerQuantCache":
            family = "indexer_quant_cache"
        if family and not recipe:
            recipe = op_name
    elif family and ":" in impl and impl.startswith(f"{family}:"):
        impl = ""
    return family, recipe, impl


def _case_strict_builder(case: Mapping[str, Any]) -> str:
    family, recipe, impl = _inferred_node_triple(case)
    raw_dtypes = case.get("dtypes")
    dtypes = (
        [str(item) for item in raw_dtypes]
        if isinstance(raw_dtypes, (list, tuple))
        else ([str(case["dtype"])] if case.get("dtype") else [])
    )
    meta = case.get("metadata") if isinstance(case.get("metadata"), Mapping) else {}
    if not meta and isinstance(case.get("meta"), Mapping):
        meta = case["meta"]
    builder_name, _abi = resolve_builder_strict(
        family,
        recipe,
        impl,
        dtypes,
        meta,
        model_id=str(case.get("model_id") or ""),
        layer_idx=int(case.get("layer_idx", -1)),
        local_shape=case.get("local_shape"),
    )
    if builder_name in OPERATOR_BUILDERS:
        return builder_name
    if builder_name in _OP_ALIASES:
        return _OP_ALIASES[builder_name]
    raise_unmodeled(
        case,
        builder=builder_name,
        upstream_abi=str(case.get("kernel") or ""),
        reason="unknown_operator_builder",
        code=f"bench_builder_unknown: {builder_name!r}",
    )
    raise AssertionError("unreachable")


def resolve_builder(case: Mapping[str, Any]) -> str:
    """Resolve the canonical builder name for ``case`` or raise fail-fast."""
    family, recipe, _impl = _inferred_node_triple(case)
    if family and recipe:
        return _case_strict_builder(case)
    declared = str(case.get("builder") or "").strip()
    if not declared and isinstance(case.get("binding"), Mapping):
        declared = str(case["binding"].get("builder") or "").strip()
    if declared:
        if declared in OPERATOR_BUILDERS:
            return declared
        if declared in _OP_ALIASES:
            return _OP_ALIASES[declared]
        raise_unmodeled(
            case,
            builder=declared,
            upstream_abi=str(case.get("kernel") or ""),
            reason="unknown_operator_builder",
            code=f"bench_builder_unknown: {declared!r}",
        )
    op_name = str(case.get("op") or "").strip()
    if op_name in OPERATOR_BUILDERS:
        return op_name
    if op_name in _OP_ALIASES:
        return _OP_ALIASES[op_name]
    if family or recipe:
        return _case_strict_builder(case)
    raise_unmodeled(
        case,
        builder=op_name or "unknown",
        upstream_abi=str(case.get("kernel") or ""),
        reason="unknown_operator_builder",
        code=f"bench_builder_unknown: {op_name or 'unknown'!r}",
    )
    raise AssertionError("unreachable")


def supports_cold_ring(case: Mapping[str, Any]) -> bool:
    return resolve_builder(case) in RING_BUILDERS


def build_operator_enqueue(
    torch: Any,
    case: Mapping[str, Any],
    context: Mapping[str, Any] | None = None,
    *,
    hot: bool = False,
) -> Callable[[], Any]:
    """Return a zero-arg callable enqueueing ``case``, or raise fail-fast."""
    name = resolve_builder(case)
    ctx = {**(context or {})}
    if hot:
        ctx["hot"] = True
    ctx["_ring_arena"] = {"sub_offset": 0, "invocation_bytes": 0, "base_slot": None}
    return OPERATOR_BUILDERS[name](torch, case, ctx)


__all__ = [
    "BenchUnmodeledOperatorError",
    "CANONICAL_BUILDERS",
    "COLLECTIVE_ALIASES",
    "COLLECTIVE_OPS",
    "CONTROL_FAMILIES",
    "DTYPE_NAMES",
    "ELEMENT_BYTES",
    "OPERATOR_BUILDERS",
    "RING_BUILDERS",
    "UNMODELED_HINT_SCHEMA",
    "UnmodeledCapabilityError",
    "_bind_collective",
    "build_graph_boundary",
    "build_operator_enqueue",
    "device_of",
    "element_bytes",
    "has_npu_surface",
    "resolve_builder",
    "resolve_builder_strict",
    "resolve_op",
    "supports_cold_ring",
    "torch_dtype",
    "unmodeled_payload",
]
