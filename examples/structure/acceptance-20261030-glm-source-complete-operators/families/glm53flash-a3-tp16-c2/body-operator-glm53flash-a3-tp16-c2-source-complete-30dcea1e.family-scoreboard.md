# Complete Decode Body Operator Families

Only complete events inside the 46 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| glm53flash-a3-tp16-c2 / source-complete-30dcea1e | 21 / 21 | 0 / 0 | 21 / 21 | 23506 / 98026 | 0 |

## glm53flash-a3-tp16-c2 / source-complete-30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1932 | 0 / 1932 | 90.887 | 90.531 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| hcom_allReduce_ / ffn_down_communication | 2070 | 0 / 2070 | 54.261 | 23.441 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1932 | 0 / 1932 | 54.576 | 54.441 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 2070 | 0 / 2070 | 41.777 | 30.820 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 1932 | 0 / 1932 | 42.440 | 39.041 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeDispatchV2 / unresolved | 1932 | 0 / 1932 | 38.491 | 38.450 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 2070 | 0 / 2070 | 33.355 | 33.221 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / ffn.hc_pre | 2070 | 0 / 2070 | 31.871 | 31.241 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| MoeDistributeCombineV2 / unresolved | 1932 | 0 / 1932 | 33.149 | 32.901 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1564 | 0 / 1564 | 39.742 | 39.261 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 4370 | 0 / 4370 | 13.078 | 14.061 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvQuantSparseFlashAttentionVllm / unresolved | 506 | 0 / 506 | 97.824 | 97.332 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_qkvbfg_a | 1564 | 1564 / 0 | 24.054 | 24.221 | 21.956 | -2.098 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / unresolved | 1932 | 0 / 1932 | 19.030 | 19.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 1932 | 0 / 1932 | 17.651 | 17.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 1932 | 1932 / 0 | 16.752 | 17.100 | 5.000 | -11.752 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| PoolKeyIndexer / unresolved | 506 | 0 / 506 | 57.781 | 57.731 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 1932 | 0 / 1932 | 13.269 | 13.180 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _copy_conv_state_kernel / unresolved | 3128 | 0 / 3128 | 7.679 | 7.560 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 8050 | 0 / 8050 | 2.436 | 2.420 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSwigluQuant / unresolved | 1932 | 0 / 1932 | 10.038 | 9.940 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 2070 | 0 / 2070 | 9.289 | 9.301 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KeyPool / unresolved | 506 | 0 / 506 | 36.524 | 36.181 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 2070 | 2070 / 0 | 8.616 | 8.540 | 2.500 | -6.116 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / linear_output | 1564 | 1564 / 0 | 11.397 | 11.200 | 5.873 | -5.524 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / unresolved | 1564 | 0 / 1564 | 10.888 | 10.600 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 2070 | 2070 / 0 | 8.221 | 8.180 | 2.500 | -5.721 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / linear_decay_b + linear_gate_b | 3128 | 3128 / 0 | 5.222 | 5.240 | 5.000 | -0.222 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Range / unresolved | 2070 | 0 / 2070 | 6.428 | 6.100 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 1564 | 0 / 1564 | 8.401 | 7.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / qkv_a | 506 | 506 / 0 | 25.193 | 24.920 | 21.961 | -3.232 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 2070 | 2070 / 0 | 5.823 | 5.780 | 2.500 | -3.323 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 2070 | 2070 / 0 | 5.685 | 5.600 | 2.500 | -3.185 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_q | 506 | 506 / 0 | 20.306 | 20.100 | 16.734 | -3.572 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / shared.gate_up.quantize | 1932 | 1932 / 0 | 5.310 | 5.340 | 2.500 | -2.810 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 3128 | 0 / 3128 | 3.100 | 2.981 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / index_k | 1012 | 1012 / 0 | 9.332 | 9.300 | 21.935 | 12.602 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 4094 | 0 / 4094 | 2.010 | 1.240 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 1932 | 0 / 1932 | 4.071 | 3.901 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 506 | 506 / 0 | 14.315 | 14.300 | 5.000 | -9.315 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / output | 506 | 506 / 0 | 14.110 | 13.880 | 11.303 | -2.807 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 1012 | 0 / 1012 | 6.905 | 6.700 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 506 | 506 / 0 | 13.523 | 13.710 | 5.000 | -8.523 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterUpdate / unresolved | 1564 | 0 / 1564 | 4.227 | 4.100 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicBlockQuant / unresolved | 506 | 0 / 506 | 12.963 | 12.411 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1564 | 0 / 1564 | 3.503 | 3.420 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdateSk / unresolved | 506 | 0 / 506 | 10.194 | 10.180 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 2070 | 0 / 2070 | 2.385 | 2.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GatherV3 / unresolved | 1012 | 0 / 1012 | 4.603 | 4.640 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 506 | 0 / 506 | 8.634 | 8.621 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV3 / index_norm | 506 | 506 / 0 | 7.868 | 7.880 | 2.500 | -5.368 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / q_b | 506 | 506 / 0 | 7.566 | 7.560 | 8.365 | 0.799 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 2070 | 0 / 2070 | 1.363 | 1.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_keypool_caches_kernel / unresolved | 506 | 0 / 506 | 4.479 | 4.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 138 | 138 / 0 | 16.172 | 15.920 | 11.059 | -5.113 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _pack_indices_kernel / unresolved | 506 | 0 / 506 | 4.005 | 4.011 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_nonempty_keypool_inputs_kernel / unresolved | 506 | 0 / 506 | 3.882 | 3.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / down | 138 | 138 / 0 | 11.409 | 11.450 | 5.000 | -6.409 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ClipByValueV2 / unresolved | 276 | 0 / 276 | 4.188 | 4.120 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 644 | 0 / 644 | 1.534 | 1.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 276 | 0 / 276 | 3.254 | 3.280 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 138 | 138 / 0 | 4.641 | 4.611 | 2.500 | -2.141 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / down.quantize | 138 | 138 / 0 | 3.591 | 3.420 | 2.500 | -1.091 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 138 | 0 / 138 | 2.653 | 2.700 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 138 | 0 / 138 | 2.496 | 2.450 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
