# Complete Decode Body Operator Families

Only complete events inside the 46 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| glm53flash-a3-tp16-c4 / source-complete-30dcea1e | 21 / 21 | 0 / 0 | 21 / 21 | 23506 / 98026 | 0 |

## glm53flash-a3-tp16-c4 / source-complete-30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1932 | 0 / 1932 | 163.330 | 162.523 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| GroupedMatmul / expert_down | 1932 | 0 / 1932 | 84.140 | 84.082 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvQuantSparseFlashAttentionVllm / unresolved | 506 | 0 / 506 | 178.125 | 178.114 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 2070 | 0 / 2070 | 39.520 | 35.251 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 2070 | 0 / 2070 | 37.467 | 37.161 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / ffn.hc_pre | 2070 | 0 / 2070 | 36.928 | 36.361 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| hcom_allGather_ / ffn_down_communication | 1932 | 0 / 1932 | 39.029 | 39.021 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeDispatchV2 / unresolved | 1932 | 0 / 1932 | 38.621 | 38.581 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / ffn_down_communication | 2070 | 0 / 2070 | 33.824 | 25.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1564 | 0 / 1564 | 42.042 | 40.921 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 4370 | 0 / 4370 | 13.144 | 13.880 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV2 / unresolved | 1932 | 0 / 1932 | 28.262 | 27.541 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1932 | 0 / 1932 | 20.823 | 20.191 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_qkvbfg_a | 1564 | 1564 / 0 | 25.274 | 25.580 | 23.897 | -1.377 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 1932 | 0 / 1932 | 17.778 | 17.520 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 1932 | 1932 / 0 | 17.522 | 17.890 | 5.000 | -12.522 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 8050 | 0 / 8050 | 3.665 | 3.580 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PoolKeyIndexer / unresolved | 506 | 0 / 506 | 57.982 | 57.701 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 1932 | 0 / 1932 | 14.215 | 14.120 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _copy_conv_state_kernel / unresolved | 3128 | 0 / 3128 | 7.443 | 7.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 2070 | 2070 / 0 | 10.853 | 10.780 | 2.500 | -8.353 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / unresolved | 1564 | 0 / 1564 | 14.101 | 13.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 2070 | 2070 / 0 | 10.632 | 10.540 | 2.500 | -8.132 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DequantSwigluQuant / unresolved | 1932 | 0 / 1932 | 10.352 | 10.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 2070 | 0 / 2070 | 9.431 | 9.361 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_output | 1564 | 1564 / 0 | 11.803 | 11.600 | 6.471 | -5.332 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 2070 | 2070 / 0 | 8.879 | 8.461 | 2.500 | -6.379 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| KeyPool / unresolved | 506 | 0 / 506 | 35.784 | 35.781 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 2070 | 2070 / 0 | 8.398 | 8.160 | 2.500 | -5.898 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / linear_decay_b + linear_gate_b | 3128 | 3128 / 0 | 5.100 | 5.310 | 5.000 | -0.100 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 3128 | 0 / 3128 | 4.783 | 4.901 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 2070 | 0 / 2070 | 6.688 | 6.240 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 1564 | 0 / 1564 | 8.334 | 8.000 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / qkv_a | 506 | 506 / 0 | 24.993 | 24.881 | 23.907 | -1.086 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / shared.gate_up.quantize | 1932 | 1932 / 0 | 5.905 | 5.880 | 2.500 | -3.405 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_q | 506 | 506 / 0 | 21.782 | 21.601 | 18.263 | -3.520 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_k | 1012 | 1012 / 0 | 10.236 | 10.240 | 23.855 | 13.619 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterUpdate / unresolved | 1564 | 0 / 1564 | 6.569 | 6.520 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 1932 | 0 / 1932 | 4.516 | 4.260 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 1012 | 0 / 1012 | 8.176 | 8.130 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 4094 | 0 / 4094 | 2.017 | 1.260 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1564 | 0 / 1564 | 5.160 | 4.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output | 506 | 506 / 0 | 15.332 | 15.180 | 12.367 | -2.965 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GatherV3 / unresolved | 1012 | 0 / 1012 | 6.969 | 7.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 506 | 506 / 0 | 13.513 | 13.460 | 5.000 | -8.513 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicBlockQuant / unresolved | 506 | 0 / 506 | 12.937 | 12.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 506 | 506 / 0 | 12.441 | 12.410 | 5.000 | -7.441 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LayerNormV3 / index_norm | 506 | 506 / 0 | 11.994 | 11.980 | 2.500 | -9.494 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterNdUpdateSk / unresolved | 506 | 0 / 506 | 10.550 | 10.441 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 2070 | 0 / 2070 | 2.435 | 2.400 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 506 | 0 / 506 | 8.767 | 8.761 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / q_b | 506 | 506 / 0 | 7.849 | 7.840 | 9.127 | 1.278 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _write_keypool_caches_kernel / unresolved | 506 | 0 / 506 | 7.088 | 7.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pack_indices_kernel / unresolved | 506 | 0 / 506 | 6.091 | 6.100 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 2070 | 0 / 2070 | 1.355 | 1.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_nonempty_keypool_inputs_kernel / unresolved | 506 | 0 / 506 | 4.251 | 4.140 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 138 | 138 / 0 | 14.464 | 14.400 | 12.101 | -2.363 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 138 | 138 / 0 | 12.193 | 12.250 | 5.009 | -7.184 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ClipByValueV2 / unresolved | 276 | 0 / 276 | 5.625 | 5.660 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 644 | 0 / 644 | 1.800 | 1.380 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 276 | 0 / 276 | 3.800 | 3.550 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 138 | 138 / 0 | 5.191 | 5.180 | 2.500 | -2.691 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / down.quantize | 138 | 138 / 0 | 4.840 | 4.760 | 2.500 | -2.340 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 138 | 0 / 138 | 3.764 | 3.671 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 138 | 0 / 138 | 3.709 | 3.580 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
