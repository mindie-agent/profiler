# Complete Decode Body Operator Families

Only complete events inside the 47 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_glm53flash_tp16_aclgraph_c64 / 86c1ee8f | 12 / 17 | 0 / 4 | 12 / 21 | 24017 / 97760 | 0 |

## a3_glm53flash_tp16_aclgraph_c64 / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| KvQuantSparseFlashAttentionVllm / unresolved | 517 | 0 / 517 | 1632.353 | 1632.673 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 0 / 1974 | 245.405 | 245.005 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| RecurrentKda / unresolved | 1598 | 0 / 1598 | 245.540 | 250.525 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 2115 | 0 / 2115 | 149.172 | 148.443 | 105.093 | -44.079 | 15% (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| hcom_allReduce_ / ffn_down_communication | 2115 | 0 / 2115 | 135.178 | 134.783 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| GroupedMatmul / expert_down | 1974 | 0 / 1974 | 120.959 | 120.713 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| HcPre / ffn.hc_pre | 2115 | 0 / 2115 | 75.216 | 77.602 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 2115 | 0 / 2115 | 66.201 | 66.121 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| _copy_conv_state_kernel / unresolved | 3196 | 0 / 3196 | 39.981 | 33.030 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 2115 | 2115 / 0 | 51.747 | 51.981 | 26.810 | -24.937 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeDistributeDispatchV2 / unresolved | 1974 | 0 / 1974 | 53.409 | 53.201 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_qkvbfg_a | 1598 | 1598 / 0 | 64.341 | 64.531 | 101.405 | 37.064 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 2115 | 2115 / 0 | 47.315 | 47.361 | 26.810 | -20.505 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allGather_ / ffn_down_communication | 1974 | 0 / 1974 | 49.565 | 49.481 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV2 / unresolved | 1974 | 0 / 1974 | 49.508 | 50.581 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PoolKeyIndexer / unresolved | 517 | 0 / 517 | 163.806 | 164.924 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 1974 | 1974 / 0 | 41.694 | 43.221 | 8.888 | -32.806 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / unresolved | 1974 | 0 / 1974 | 25.727 | 25.561 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1598 | 0 / 1598 | 30.788 | 30.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1598 | 0 / 1598 | 29.273 | 29.301 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 8225 | 0 / 8225 | 5.416 | 4.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 1974 | 0 / 1974 | 21.598 | 21.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1974 | 0 / 1974 | 21.251 | 20.991 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 2115 | 0 / 2115 | 18.196 | 17.501 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 2115 | 2115 / 0 | 18.056 | 17.661 | 5.250 | -12.807 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 2115 | 2115 / 0 | 17.765 | 16.820 | 5.250 | -12.515 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| KeyPool / unresolved | 517 | 0 / 517 | 72.021 | 71.981 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 1598 | 0 / 1598 | 19.926 | 19.640 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_output | 1598 | 1598 / 0 | 19.457 | 19.421 | 26.192 | 6.735 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_q | 517 | 517 / 0 | 59.327 | 59.281 | 70.876 | 11.549 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / qkv_a | 517 | 517 / 0 | 56.384 | 56.341 | 101.486 | 45.102 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / shared.gate_up.quantize | 1974 | 1974 / 0 | 14.674 | 14.561 | 3.933 | -10.740 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DequantSwigluQuant / unresolved | 1974 | 0 / 1974 | 14.302 | 13.920 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 3196 | 0 / 3196 | 7.502 | 7.500 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 2115 | 0 / 2115 | 10.268 | 9.920 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_decay_b + linear_gate_b | 3196 | 3196 / 0 | 6.226 | 6.040 | 5.000 | -1.226 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / unresolved | 1974 | 0 / 1974 | 9.584 | 9.541 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1598 | 0 / 1598 | 10.527 | 10.681 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 1034 | 0 / 1034 | 15.281 | 14.570 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 4183 | 0 / 4183 | 3.531 | 1.740 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 1551 | 0 / 1551 | 8.477 | 8.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 517 | 0 / 517 | 24.550 | 24.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GatherV3 / unresolved | 1034 | 0 / 1034 | 11.705 | 11.440 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output | 517 | 517 / 0 | 22.615 | 22.580 | 48.534 | 25.919 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_k | 1034 | 1034 / 0 | 10.620 | 10.620 | 40.495 | 29.875 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / q_b | 517 | 517 / 0 | 19.012 | 19.000 | 23.928 | 4.916 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LayerNormV3 / index_norm | 517 | 517 / 0 | 18.863 | 18.840 | 2.500 | -16.363 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _write_keypool_caches_kernel / unresolved | 517 | 0 / 517 | 18.720 | 18.640 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 517 | 517 / 0 | 16.861 | 16.800 | 8.373 | -8.488 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeBatchMatMul / v_expand | 517 | 517 / 0 | 15.676 | 15.660 | 9.034 | -6.643 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicBlockQuant / unresolved | 517 | 0 / 517 | 13.642 | 13.621 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pack_indices_kernel / unresolved | 517 | 0 / 517 | 13.051 | 13.040 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 517 | 0 / 517 | 13.018 | 12.941 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 2115 | 0 / 2115 | 3.147 | 3.120 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdateSk / unresolved | 517 | 0 / 517 | 11.337 | 11.300 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_nonempty_keypool_inputs_kernel / unresolved | 517 | 0 / 517 | 11.060 | 10.500 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 141 | 141 / 0 | 33.917 | 34.121 | 32.503 | -1.414 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 141 | 141 / 0 | 30.526 | 30.501 | 23.007 | -7.519 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 2115 | 0 / 2115 | 1.500 | 1.500 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 282 | 0 / 282 | 10.007 | 10.230 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 658 | 0 / 658 | 3.318 | 2.640 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 141 | 141 / 0 | 13.587 | 13.560 | 3.933 | -9.654 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 282 | 0 / 282 | 6.775 | 6.930 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 141 | 0 / 141 | 8.737 | 8.121 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 141 | 0 / 141 | 8.031 | 8.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / down.quantize | 141 | 141 / 0 | 7.823 | 7.781 | 2.500 | -5.323 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44 | 1974 | 120.959 / 120.713 | 160.177 | 5.080 | 6.727 | capacity_vs_valid_rows_conditional |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_glm53flash_tp16_aclgraph_c64 / 86c1ee8f / GroupedMatmul / expert_down | 1974 | 0 | 1974 | 0 | 0 |
