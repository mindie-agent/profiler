# Complete Decode Body Operator Families

Only complete events inside the 47 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_glm53flash_tp16_aclgraph_c8 / source-complete-30dcea1e | 20 / 21 | 0 / 0 | 20 / 21 | 24017 / 96209 | 0 |

## a3_glm53flash_tp16_aclgraph_c8 / source-complete-30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 0 / 1974 | 226.015 | 225.564 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| GroupedMatmul / expert_down | 1974 | 0 / 1974 | 113.793 | 112.993 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvQuantSparseFlashAttentionVllm / unresolved | 517 | 0 / 517 | 260.822 | 260.605 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 2115 | 0 / 2115 | 46.775 | 43.241 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV2 / unresolved | 1974 | 0 / 1974 | 43.088 | 43.271 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV2 / unresolved | 1974 | 0 / 1974 | 40.622 | 40.561 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 1974 | 0 / 1974 | 40.538 | 40.360 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_ / ffn_down_communication | 2115 | 0 / 2115 | 37.327 | 32.941 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 2115 | 0 / 2115 | 37.220 | 37.240 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 2115 | 0 / 2115 | 37.137 | 36.921 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| RecurrentKda / unresolved | 1598 | 0 / 1598 | 45.783 | 45.221 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_qkvbfg_a | 1598 | 1598 / 0 | 27.754 | 26.940 | 27.780 | 0.025 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 1974 | 1974 / 0 | 18.707 | 19.281 | 5.000 | -13.707 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / attention.hc_post_group | 2115 | 2115 / 0 | 16.098 | 15.220 | 3.351 | -12.747 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 2115 | 2115 / 0 | 15.306 | 14.480 | 3.351 | -11.955 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 1974 | 0 / 1974 | 16.286 | 15.900 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PoolKeyIndexer / unresolved | 517 | 0 / 517 | 61.264 | 60.361 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 8225 | 0 / 8225 | 3.788 | 3.641 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1974 | 0 / 1974 | 15.321 | 15.121 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1598 | 0 / 1598 | 18.855 | 18.401 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 1974 | 0 / 1974 | 15.078 | 14.960 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _copy_conv_state_kernel / unresolved | 3196 | 0 / 3196 | 9.230 | 8.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 1598 | 0 / 1598 | 17.319 | 16.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 2115 | 0 / 2115 | 12.620 | 12.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSwigluQuant / unresolved | 1974 | 0 / 1974 | 12.787 | 12.580 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_output | 1598 | 1598 / 0 | 12.895 | 12.921 | 6.766 | -6.128 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| KeyPool / unresolved | 517 | 0 / 517 | 38.393 | 37.941 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 2115 | 0 / 2115 | 9.102 | 8.840 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 3196 | 0 / 3196 | 5.764 | 5.910 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 2115 | 2115 / 0 | 8.518 | 8.640 | 2.500 | -6.018 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 2115 | 2115 / 0 | 8.144 | 7.980 | 2.500 | -5.644 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / qkv_a | 517 | 517 / 0 | 31.689 | 31.821 | 27.800 | -3.889 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / linear_decay_b + linear_gate_b | 3196 | 3196 / 0 | 4.684 | 4.870 | 5.000 | 0.316 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / shared.gate_up.quantize | 1974 | 1974 / 0 | 6.514 | 6.431 | 2.500 | -4.014 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_q | 517 | 517 / 0 | 24.512 | 24.760 | 18.558 | -5.954 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterUpdate / unresolved | 1598 | 0 / 1598 | 7.919 | 7.761 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1598 | 0 / 1598 | 7.103 | 6.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GatherV3 / unresolved | 1034 | 0 / 1034 | 10.480 | 10.421 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / index_k | 1034 | 1034 / 0 | 9.850 | 9.960 | 27.695 | 17.845 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 1034 | 0 / 1034 | 9.000 | 8.931 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 4183 | 0 / 4183 | 2.210 | 1.460 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 1974 | 0 / 1974 | 4.604 | 4.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output | 517 | 517 / 0 | 16.982 | 16.921 | 12.662 | -4.320 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicBlockQuant / unresolved | 517 | 0 / 517 | 14.051 | 13.260 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 517 | 517 / 0 | 13.640 | 13.620 | 5.000 | -8.640 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeBatchMatMul / q_absorb | 517 | 517 / 0 | 13.145 | 13.160 | 5.000 | -8.145 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LayerNormV3 / index_norm | 517 | 517 / 0 | 11.714 | 11.761 | 2.500 | -9.214 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterNdUpdateSk / unresolved | 517 | 0 / 517 | 11.189 | 10.840 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 2115 | 0 / 2115 | 2.681 | 2.660 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / q_b | 517 | 517 / 0 | 10.274 | 10.260 | 10.652 | 0.377 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _pack_indices_kernel / unresolved | 517 | 0 / 517 | 9.394 | 8.960 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 517 | 0 / 517 | 9.045 | 9.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_keypool_caches_kernel / unresolved | 517 | 0 / 517 | 8.216 | 7.940 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 517 | 0 / 517 | 6.185 | 6.160 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_nonempty_keypool_inputs_kernel / unresolved | 517 | 0 / 517 | 6.147 | 6.040 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 2115 | 0 / 2115 | 1.340 | 1.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 282 | 0 / 282 | 8.146 | 8.430 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 141 | 141 / 0 | 15.484 | 15.720 | 14.185 | -1.298 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 141 | 141 / 0 | 13.015 | 12.960 | 5.514 | -7.501 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 282 | 0 / 282 | 5.948 | 5.990 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 658 | 0 / 658 | 2.222 | 1.420 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 141 | 0 / 141 | 6.810 | 6.740 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 141 | 0 / 141 | 6.753 | 6.660 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 141 | 141 / 0 | 5.918 | 5.920 | 2.500 | -3.418 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / down.quantize | 141 | 141 / 0 | 5.114 | 5.020 | 2.500 | -2.614 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
