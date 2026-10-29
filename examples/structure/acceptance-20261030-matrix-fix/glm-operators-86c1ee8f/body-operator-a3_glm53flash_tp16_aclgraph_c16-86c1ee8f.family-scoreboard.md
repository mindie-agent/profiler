# Complete Decode Body Operator Families

Only complete events inside the 50 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_glm53flash_tp16_aclgraph_c16 / 86c1ee8f | 19 / 21 | 0 / 0 | 19 / 21 | 25550 / 102900 | 0 |

## a3_glm53flash_tp16_aclgraph_c16 / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2100 | 0 / 2100 | 241.813 | 241.925 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| GroupedMatmul / expert_down | 2100 | 0 / 2100 | 119.516 | 118.882 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| KvQuantSparseFlashAttentionVllm / unresolved | 550 | 0 / 550 | 423.890 | 423.878 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1700 | 0 / 1700 | 79.841 | 78.381 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 2250 | 0 / 2250 | 58.617 | 58.341 | 82.523 | 23.906 | 15% (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| hcom_allReduce_ / ffn_down_communication | 2250 | 0 / 2250 | 48.325 | 46.481 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| HcPre / ffn.hc_pre | 2250 | 0 / 2250 | 41.007 | 41.301 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 2250 | 0 / 2250 | 39.826 | 39.141 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| MoeDistributeDispatchV2 / unresolved | 2100 | 0 / 2100 | 42.572 | 42.281 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 2100 | 0 / 2100 | 40.844 | 40.861 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV2 / unresolved | 2100 | 0 / 2100 | 33.700 | 33.031 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_qkvbfg_a | 1700 | 1700 / 0 | 30.332 | 30.401 | 35.545 | 5.213 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _copy_conv_state_kernel / unresolved | 3400 | 0 / 3400 | 13.923 | 13.740 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 2250 | 2250 / 0 | 21.017 | 20.701 | 6.703 | -14.314 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 2250 | 2250 / 0 | 19.447 | 19.800 | 6.703 | -12.745 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 2100 | 2100 / 0 | 20.759 | 21.221 | 5.000 | -15.759 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 8750 | 0 / 8750 | 4.424 | 4.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 2100 | 0 / 2100 | 17.918 | 17.870 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PoolKeyIndexer / unresolved | 550 | 0 / 550 | 65.291 | 64.181 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 2100 | 0 / 2100 | 16.900 | 16.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 2100 | 0 / 2100 | 16.598 | 16.441 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 2250 | 0 / 2250 | 14.925 | 14.700 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1700 | 0 / 1700 | 17.702 | 15.961 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSwigluQuant / unresolved | 2100 | 0 / 2100 | 13.621 | 13.431 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 1700 | 0 / 1700 | 16.744 | 16.560 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KeyPool / unresolved | 550 | 0 / 550 | 46.627 | 45.871 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 2250 | 2250 / 0 | 11.152 | 11.161 | 2.500 | -8.652 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 2250 | 2250 / 0 | 11.115 | 10.500 | 2.500 | -8.615 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 3400 | 0 / 3400 | 7.197 | 6.960 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_output | 1700 | 1700 / 0 | 13.611 | 13.641 | 8.258 | -5.353 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Range / unresolved | 2250 | 0 / 2250 | 9.607 | 9.411 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1700 | 0 / 1700 | 11.389 | 11.400 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / qkv_a | 550 | 550 / 0 | 33.936 | 34.000 | 35.586 | 1.650 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / shared.gate_up.quantize | 2100 | 2100 / 0 | 8.649 | 8.520 | 2.500 | -6.149 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / linear_decay_b + linear_gate_b | 3400 | 3400 / 0 | 4.751 | 4.820 | 5.000 | 0.249 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_q | 550 | 550 / 0 | 27.513 | 27.420 | 21.911 | -5.602 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_k | 1100 | 1100 / 0 | 11.362 | 11.510 | 35.375 | 24.013 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GatherV3 / unresolved | 1100 | 0 / 1100 | 11.000 | 10.901 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 1100 | 0 / 1100 | 10.718 | 11.170 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 2100 | 0 / 2100 | 5.358 | 5.120 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output | 550 | 550 / 0 | 19.946 | 19.940 | 15.084 | -4.861 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 4450 | 0 / 4450 | 2.405 | 1.600 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1700 | 0 / 1700 | 5.484 | 5.460 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV3 / index_norm | 550 | 550 / 0 | 15.501 | 15.460 | 2.500 | -13.001 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeBatchMatMul / v_expand | 550 | 550 / 0 | 13.844 | 13.840 | 5.012 | -8.831 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeBatchMatMul / q_absorb | 550 | 550 / 0 | 13.806 | 13.800 | 5.000 | -8.806 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicBlockQuant / unresolved | 550 | 0 / 550 | 13.601 | 13.600 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 2250 | 0 / 2250 | 2.772 | 2.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdateSk / unresolved | 550 | 0 / 550 | 11.118 | 11.101 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / q_b | 550 | 550 / 0 | 10.991 | 10.981 | 13.701 | 2.709 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _pack_indices_kernel / unresolved | 550 | 0 / 550 | 9.573 | 9.580 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 550 | 0 / 550 | 9.525 | 9.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_nonempty_keypool_inputs_kernel / unresolved | 550 | 0 / 550 | 9.475 | 8.840 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 550 | 0 / 550 | 8.593 | 8.600 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_keypool_caches_kernel / unresolved | 550 | 0 / 550 | 8.460 | 8.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 550 | 0 / 550 | 8.434 | 8.400 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 2250 | 0 / 2250 | 1.363 | 1.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 300 | 0 / 300 | 8.956 | 9.251 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 150 | 150 / 0 | 17.474 | 17.600 | 18.354 | 0.879 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 150 | 150 / 0 | 15.061 | 15.030 | 7.122 | -7.939 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 300 | 0 / 300 | 6.374 | 6.481 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 700 | 0 / 700 | 2.410 | 1.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 150 | 150 / 0 | 7.878 | 7.860 | 2.500 | -5.378 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 150 | 0 / 150 | 7.304 | 7.220 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 150 | 0 / 150 | 7.271 | 7.180 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / down.quantize | 150 | 150 / 0 | 5.468 | 5.440 | 2.500 | -2.968 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44 | 2100 | 119.516 / 118.882 | 153.715 | 5.020 | 6.456 | capacity_vs_valid_rows_conditional |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_glm53flash_tp16_aclgraph_c16 / 86c1ee8f / GroupedMatmul / expert_down | 2100 | 0 | 2100 | 0 | 0 |
