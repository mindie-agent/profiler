# Complete Decode Body Operator Families

Only complete events inside the 393 accepted target-body windows from 11 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_glm53flash_tp8_c64_p4k / 86c1ee8f | 18 / 18 | 0 / 1 | 18 / 19 | 16895 / 81499 | 0 |
| a3_glm53flash_tp16_aclgraph_c16 / 86c1ee8f | 19 / 21 | 0 / 0 | 19 / 21 | 25550 / 102900 | 0 |
| a3_glm53flash_tp16_aclgraph_c32 / 86c1ee8f | 16 / 21 | 0 / 0 | 16 / 21 | 25039 / 101920 | 0 |
| a3_glm53flash_tp16_aclgraph_c64 / 86c1ee8f | 12 / 17 | 0 / 4 | 12 / 21 | 24017 / 97760 | 0 |
| a3_glm53flash_tp16_aclgraph_c8 / 86c1ee8f | 20 / 21 | 0 / 0 | 20 / 21 | 24017 / 96209 | 0 |
| a5_glm53flash_tp8_c16_p4k / 86c1ee8f | 18 / 18 | 0 / 1 | 18 / 19 | 16350 / 77850 | 0 |
| a5_glm53flash_tp8_c16_p8k / 86c1ee8f | 18 / 18 | 0 / 1 | 18 / 19 | 17440 / 83040 | 0 |
| a5_glm53flash_tp8_c32_p4k / 86c1ee8f | 18 / 18 | 0 / 1 | 18 / 19 | 16895 / 80445 | 0 |
| a5_glm53flash_tp8_c32_p8k / 86c1ee8f | 18 / 18 | 0 / 1 | 18 / 19 | 19075 / 90825 | 0 |
| a5_glm53flash_tp8_c4_p8k / 86c1ee8f | 18 / 18 | 0 / 1 | 18 / 19 | 5995 / 28424 | 0 |
| a5_glm53flash_tp8_c8_p4k / 86c1ee8f | 18 / 18 | 0 / 1 | 18 / 19 | 16350 / 77520 | 0 |

## a5_glm53flash_tp8_c64_p4k / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1302 | 0 / 1302 | 211.089 | 210.722 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1302 | 1302 / 0 | 115.777 | 117.337 | 90.476 | -25.300 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMla / unresolved | 341 | 0 / 341 | 288.254 | 285.492 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1054 | 0 / 1054 | 78.338 | 78.285 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 341 | 0 / 341 | 218.721 | 218.708 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1395 | 0 / 1395 | 43.605 | 39.492 | 34.562 | -9.042 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1395 | 0 / 1395 | 41.711 | 41.084 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| _copy_conv_state_kernel / unresolved | 2108 | 0 / 2108 | 21.777 | 21.506 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 1302 | 1302 / 0 | 29.762 | 29.854 | 31.494 | 1.732 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeInitRoutingV3 / unresolved | 1302 | 0 / 1302 | 28.768 | 28.822 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 1054 | 1054 / 0 | 31.997 | 32.020 | 25.498 | -6.499 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPre / attention.hc_pre | 1395 | 0 / 1395 | 22.094 | 21.964 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / ffn.hc_pre | 1395 | 0 / 1395 | 21.748 | 21.578 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| SparseFlashMlaMetadata / unresolved | 341 | 0 / 341 | 81.800 | 78.398 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 6944 | 0 / 6944 | 3.773 | 3.921 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 2790 | 0 / 2790 | 7.874 | 4.164 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 5704 | 0 / 5704 | 3.188 | 2.179 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1054 | 0 / 1054 | 17.222 | 17.235 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 1395 | 1395 / 0 | 11.932 | 12.155 | 5.585 | -6.346 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeFinalizeRoutingV2 / unresolved | 1302 | 0 / 1302 | 11.587 | 11.571 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 1395 | 1395 / 0 | 10.161 | 10.116 | 5.585 | -4.575 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _expand_pool_indices / unresolved | 341 | 0 / 341 | 37.120 | 37.108 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 1054 | 1054 / 0 | 12.008 | 11.988 | 7.351 | -4.657 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.gate_up | 1302 | 1302 / 0 | 8.562 | 8.569 | 8.505 | -0.057 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 1302 | 0 / 1302 | 8.429 | 8.347 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / router_selection | 1302 | 0 / 1302 | 7.892 | 7.804 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| QuantBatchMatmulV3 / unresolved | 1023 | 0 / 1023 | 10.038 | 11.037 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 2449 | 0 / 2449 | 4.088 | 4.256 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 3131 | 0 / 3131 | 3.102 | 2.958 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 341 | 0 / 341 | 27.759 | 27.745 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 1395 | 1395 / 0 | 6.345 | 6.415 | 1.312 | -5.033 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TopKV2 / unresolved | 341 | 0 / 341 | 25.459 | 25.405 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 2790 | 0 / 2790 | 3.028 | 3.046 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cumsum / unresolved | 1302 | 0 / 1302 | 5.776 | 5.813 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 1302 | 1302 / 0 | 5.657 | 5.668 | 1.312 | -4.345 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 1395 | 1395 / 0 | 5.235 | 5.070 | 1.312 | -3.923 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MaskedFill / unresolved | 1395 | 0 / 1395 | 5.029 | 5.658 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 1302 | 1302 / 0 | 5.137 | 5.131 | 1.683 | -3.455 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 341 | 0 / 341 | 17.601 | 17.373 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 1395 | 0 / 1395 | 4.191 | 4.140 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 1736 | 0 / 1736 | 3.310 | 3.426 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1395 | 0 / 1395 | 4.098 | 4.018 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 1395 | 0 / 1395 | 4.043 | 4.018 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1054 | 0 / 1054 | 5.329 | 5.300 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.down.quantize | 1302 | 1302 / 0 | 4.279 | 4.275 | 1.312 | -2.966 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / index_q | 341 | 341 / 0 | 16.317 | 16.387 | 10.392 | -5.926 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 1023 | 0 / 1023 | 5.146 | 5.153 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 1054 | 0 / 1054 | 4.804 | 4.774 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1054 | 0 / 1054 | 4.315 | 4.299 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 682 | 0 / 682 | 5.859 | 5.814 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 341 | 341 / 0 | 11.640 | 11.662 | 2.714 | -8.926 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeBatchMatMul / q_absorb | 341 | 341 / 0 | 10.637 | 10.617 | 2.790 | -7.848 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 1395 | 0 / 1395 | 2.109 | 2.118 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 682 | 0 / 682 | 4.274 | 4.194 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 1054 | 0 / 1054 | 2.602 | 2.591 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 682 | 0 / 682 | 4.011 | 4.139 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 1054 | 0 / 1054 | 2.505 | 2.529 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 682 | 0 / 682 | 3.836 | 3.810 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 341 | 0 / 341 | 6.424 | 6.377 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 341 | 0 / 341 | 6.033 | 6.002 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 341 | 0 / 341 | 5.640 | 5.551 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 93 | 93 / 0 | 16.365 | 16.294 | 13.166 | -3.199 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Equal / unresolved | 341 | 0 / 341 | 4.219 | 4.198 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 682 | 0 / 682 | 1.454 | 1.488 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / down | 93 | 93 / 0 | 9.280 | 9.267 | 5.554 | -3.726 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 93 | 93 / 0 | 5.630 | 5.609 | 1.312 | -4.318 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 93 | 93 / 0 | 4.374 | 4.371 | 1.312 | -3.062 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

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

## a3_glm53flash_tp16_aclgraph_c32 / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2058 | 0 / 2058 | 243.005 | 243.005 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| KvQuantSparseFlashAttentionVllm / unresolved | 539 | 0 / 539 | 829.848 | 829.977 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 2058 | 0 / 2058 | 120.125 | 119.862 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| RecurrentKda / unresolved | 1666 | 0 / 1666 | 143.761 | 143.613 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 2205 | 0 / 2205 | 88.072 | 87.222 | 90.047 | 1.974 | 15% (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| hcom_allReduce_ / ffn_down_communication | 2205 | 0 / 2205 | 76.407 | 75.842 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| HcPre / ffn.hc_pre | 2205 | 0 / 2205 | 52.730 | 52.241 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 2205 | 0 / 2205 | 52.080 | 51.581 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| MoeDistributeDispatchV2 / unresolved | 2058 | 0 / 2058 | 45.358 | 45.241 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 2058 | 0 / 2058 | 42.493 | 42.261 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV2 / unresolved | 2058 | 0 / 2058 | 41.227 | 41.241 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_qkvbfg_a | 1666 | 1666 / 0 | 44.605 | 44.561 | 50.998 | 6.393 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _copy_conv_state_kernel / unresolved | 3332 | 0 / 3332 | 20.581 | 18.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 2205 | 2205 / 0 | 30.239 | 29.960 | 13.405 | -16.834 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 2205 | 2205 / 0 | 28.713 | 28.261 | 13.405 | -15.308 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 2058 | 2058 / 0 | 28.641 | 29.241 | 5.000 | -23.641 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| PoolKeyIndexer / unresolved | 539 | 0 / 539 | 101.316 | 100.862 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 8575 | 0 / 8575 | 5.052 | 4.820 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 2058 | 0 / 2058 | 19.391 | 19.361 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 2058 | 0 / 2058 | 18.195 | 18.161 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 2205 | 0 / 2205 | 16.870 | 16.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1666 | 0 / 1666 | 21.848 | 22.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 2058 | 0 / 2058 | 17.026 | 17.021 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 2205 | 2205 / 0 | 14.699 | 13.680 | 2.628 | -12.071 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 2205 | 2205 / 0 | 14.652 | 14.100 | 2.628 | -12.024 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ViewCopy / unresolved | 1666 | 0 / 1666 | 18.497 | 18.000 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1666 | 0 / 1666 | 18.312 | 18.180 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KeyPool / unresolved | 539 | 0 / 539 | 55.049 | 54.001 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSwigluQuant / unresolved | 2058 | 0 / 2058 | 13.845 | 13.500 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_output | 1666 | 1666 / 0 | 16.228 | 16.241 | 14.688 | -1.540 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / qkv_a | 539 | 539 / 0 | 44.960 | 45.001 | 51.080 | 6.119 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 3332 | 0 / 3332 | 7.082 | 7.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 2205 | 0 / 2205 | 10.461 | 9.920 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / shared.gate_up.quantize | 2058 | 2058 / 0 | 10.800 | 10.720 | 2.500 | -8.300 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_q | 539 | 539 / 0 | 35.153 | 35.160 | 39.512 | 4.359 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / linear_decay_b + linear_gate_b | 3332 | 3332 / 0 | 5.135 | 4.940 | 5.000 | -0.135 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / unresolved | 2058 | 0 / 2058 | 7.004 | 7.090 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1666 | 0 / 1666 | 8.599 | 8.200 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 1078 | 0 / 1078 | 12.143 | 12.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 1617 | 0 / 1617 | 8.035 | 8.260 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 4361 | 0 / 4361 | 2.958 | 1.680 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 539 | 0 / 539 | 23.647 | 23.641 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output | 539 | 539 / 0 | 23.544 | 23.560 | 27.100 | 3.556 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GatherV3 / unresolved | 1078 | 0 / 1078 | 11.398 | 11.060 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV3 / index_norm | 539 | 539 / 0 | 18.658 | 18.421 | 2.500 | -16.158 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_k | 1078 | 1078 / 0 | 8.236 | 8.220 | 40.495 | 32.258 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeBatchMatMul / q_absorb | 539 | 539 / 0 | 14.879 | 14.781 | 5.000 | -9.879 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeBatchMatMul / v_expand | 539 | 539 / 0 | 14.556 | 14.500 | 5.804 | -8.752 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicBlockQuant / unresolved | 539 | 0 / 539 | 14.074 | 13.740 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 539 | 0 / 539 | 12.754 | 12.700 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / q_b | 539 | 539 / 0 | 12.505 | 12.500 | 15.734 | 3.228 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Less / unresolved | 2205 | 0 / 2205 | 2.994 | 3.000 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_keypool_caches_kernel / unresolved | 539 | 0 / 539 | 11.671 | 11.421 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdateSk / unresolved | 539 | 0 / 539 | 11.615 | 11.100 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pack_indices_kernel / unresolved | 539 | 0 / 539 | 11.062 | 10.640 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_nonempty_keypool_inputs_kernel / unresolved | 539 | 0 / 539 | 9.362 | 9.220 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / down | 147 | 147 / 0 | 24.536 | 24.000 | 12.705 | -11.831 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 2205 | 0 / 2205 | 1.466 | 1.460 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 147 | 147 / 0 | 20.042 | 20.061 | 26.652 | 6.609 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ClipByValueV2 / unresolved | 294 | 0 / 294 | 9.597 | 10.130 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 294 | 0 / 294 | 6.519 | 6.600 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 686 | 0 / 686 | 2.763 | 1.960 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 147 | 147 / 0 | 10.007 | 10.021 | 2.500 | -7.507 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 147 | 0 / 147 | 7.729 | 7.720 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 147 | 0 / 147 | 7.600 | 7.520 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / down.quantize | 147 | 147 / 0 | 5.991 | 5.980 | 2.500 | -3.491 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44 | 2058 | 120.125 / 119.862 | 155.873 | 5.045 | 6.547 | capacity_vs_valid_rows_conditional |

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

## a3_glm53flash_tp16_aclgraph_c8 / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 0 / 1974 | 226.015 | 225.564 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| GroupedMatmul / expert_down | 1974 | 0 / 1974 | 113.793 | 112.993 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| KvQuantSparseFlashAttentionVllm / unresolved | 517 | 0 / 517 | 260.822 | 260.605 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 2115 | 0 / 2115 | 46.775 | 43.241 | 78.762 | 31.987 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| MoeDistributeCombineV2 / unresolved | 1974 | 0 / 1974 | 43.088 | 43.271 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV2 / unresolved | 1974 | 0 / 1974 | 40.622 | 40.561 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 1974 | 0 / 1974 | 40.538 | 40.360 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_ / ffn_down_communication | 2115 | 0 / 2115 | 37.327 | 32.941 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
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

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44 | 1974 | 113.793 / 112.993 | 152.643 | 4.779 | 6.411 | capacity_vs_valid_rows_conditional |

## a5_glm53flash_tp8_c16_p4k / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1260 | 0 / 1260 | 206.227 | 205.998 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1260 | 1260 / 0 | 103.104 | 102.832 | 86.575 | -16.528 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1350 | 0 / 1350 | 34.737 | 34.072 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1350 | 0 / 1350 | 34.090 | 31.334 | 27.541 | -6.549 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| MoeInitRoutingV3 / unresolved | 1260 | 0 / 1260 | 23.011 | 23.052 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 330 | 0 / 330 | 86.586 | 86.495 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1020 | 0 / 1020 | 25.355 | 25.107 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 330 | 0 / 330 | 71.028 | 70.959 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 1020 | 1020 / 0 | 22.750 | 22.715 | 12.294 | -10.457 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 6720 | 0 / 6720 | 3.046 | 2.909 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 1350 | 0 / 1350 | 14.527 | 14.265 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / ffn.hc_pre | 1350 | 0 / 1350 | 14.503 | 14.361 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| MatMulV3 / router | 1260 | 1260 / 0 | 13.545 | 13.527 | 10.507 | -3.038 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _copy_conv_state_kernel / unresolved | 2040 | 0 / 2040 | 8.339 | 8.284 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMlaMetadata / unresolved | 330 | 0 / 330 | 50.825 | 47.814 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 2700 | 0 / 2700 | 5.737 | 3.783 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 5520 | 0 / 5520 | 2.599 | 1.927 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1020 | 0 / 1020 | 11.604 | 11.482 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 1260 | 0 / 1260 | 7.342 | 7.304 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeFinalizeRoutingV2 / unresolved | 1260 | 0 / 1260 | 7.274 | 7.283 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 1350 | 1350 / 0 | 6.545 | 6.587 | 1.396 | -5.149 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.gate_up | 1260 | 1260 / 0 | 6.971 | 6.957 | 6.320 | -0.651 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 1020 | 1020 / 0 | 8.404 | 8.406 | 3.381 | -5.022 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 2370 | 0 / 2370 | 3.509 | 3.176 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 1350 | 1350 / 0 | 6.075 | 6.003 | 1.396 | -4.679 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 3030 | 0 / 3030 | 2.661 | 2.361 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 1350 | 1350 / 0 | 5.916 | 5.763 | 1.312 | -4.604 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 1350 | 1350 / 0 | 5.613 | 5.599 | 1.312 | -4.301 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / unresolved | 990 | 0 / 990 | 7.375 | 7.796 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / router_selection | 1260 | 0 / 1260 | 5.767 | 5.638 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| Cumsum / unresolved | 1260 | 0 / 1260 | 5.335 | 5.495 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 2700 | 0 / 2700 | 2.428 | 2.396 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 1260 | 1260 / 0 | 5.054 | 5.071 | 1.312 | -3.742 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.down.quantize | 1260 | 1260 / 0 | 4.918 | 4.923 | 1.312 | -3.606 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ViewCopy / unresolved | 1020 | 0 / 1020 | 5.867 | 5.865 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 1350 | 0 / 1350 | 4.284 | 4.612 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 1260 | 1260 / 0 | 4.012 | 4.008 | 1.578 | -2.434 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 990 | 0 / 990 | 4.721 | 4.663 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 1680 | 0 / 1680 | 2.631 | 2.618 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 330 | 0 / 330 | 13.115 | 13.059 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 1350 | 0 / 1350 | 2.986 | 2.828 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 330 | 330 / 0 | 12.143 | 12.066 | 4.871 | -7.272 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 1350 | 0 / 1350 | 2.673 | 2.597 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 330 | 0 / 330 | 10.926 | 10.941 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 660 | 0 / 660 | 5.369 | 5.330 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1020 | 0 / 1020 | 3.462 | 3.549 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 660 | 0 / 660 | 5.268 | 5.387 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 330 | 0 / 330 | 10.495 | 10.419 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1020 | 0 / 1020 | 3.266 | 3.257 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 330 | 0 / 330 | 9.100 | 9.119 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 330 | 330 / 0 | 7.566 | 7.551 | 1.578 | -5.988 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Range / unresolved | 1020 | 0 / 1020 | 2.434 | 2.473 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 330 | 330 / 0 | 7.075 | 7.087 | 1.827 | -5.248 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SelectV2 / unresolved | 660 | 0 / 660 | 3.529 | 3.439 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 1350 | 0 / 1350 | 1.699 | 1.641 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 330 | 0 / 330 | 6.787 | 6.657 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 660 | 0 / 660 | 3.142 | 3.175 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 330 | 0 / 330 | 5.879 | 5.881 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 1020 | 0 / 1020 | 1.883 | 1.691 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 330 | 0 / 330 | 4.572 | 4.524 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 330 | 0 / 330 | 4.060 | 4.030 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 330 | 0 / 330 | 3.365 | 3.341 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 660 | 0 / 660 | 1.433 | 1.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 90 | 90 / 0 | 8.991 | 8.976 | 6.380 | -2.612 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 90 | 90 / 0 | 6.400 | 6.394 | 2.573 | -3.827 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 90 | 90 / 0 | 4.990 | 5.029 | 1.312 | -3.678 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 90 | 90 / 0 | 4.448 | 4.436 | 1.312 | -3.136 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

## a5_glm53flash_tp8_c16_p8k / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1344 | 0 / 1344 | 206.105 | 205.956 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1344 | 1344 / 0 | 102.724 | 102.578 | 86.575 | -16.149 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1440 | 0 / 1440 | 34.790 | 34.321 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1440 | 0 / 1440 | 33.869 | 31.148 | 27.541 | -6.329 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 352 | 0 / 352 | 126.802 | 126.864 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeInitRoutingV3 / unresolved | 1344 | 0 / 1344 | 22.800 | 22.881 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 352 | 0 / 352 | 86.858 | 86.710 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1088 | 0 / 1088 | 25.509 | 25.294 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 1088 | 1088 / 0 | 22.732 | 22.767 | 12.294 | -10.439 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 7168 | 0 / 7168 | 3.042 | 2.916 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 1440 | 0 / 1440 | 14.576 | 14.436 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 1440 | 0 / 1440 | 14.474 | 14.170 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| MatMulV3 / router | 1344 | 1344 / 0 | 13.497 | 13.474 | 10.507 | -2.991 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMlaMetadata / unresolved | 352 | 0 / 352 | 50.775 | 47.837 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _copy_conv_state_kernel / unresolved | 2176 | 0 / 2176 | 8.170 | 8.200 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 2880 | 0 / 2880 | 5.712 | 3.752 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 5888 | 0 / 5888 | 2.600 | 1.931 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1088 | 0 / 1088 | 11.723 | 11.664 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 1344 | 0 / 1344 | 7.408 | 7.379 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeFinalizeRoutingV2 / unresolved | 1344 | 0 / 1344 | 7.295 | 7.289 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 1344 | 1344 / 0 | 6.950 | 6.921 | 6.320 | -0.629 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / attention.hc_post_group | 1440 | 1440 / 0 | 6.437 | 6.449 | 1.396 | -5.041 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 1088 | 1088 / 0 | 8.398 | 8.413 | 3.381 | -5.016 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 2528 | 0 / 2528 | 3.522 | 3.146 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 1440 | 1440 / 0 | 6.060 | 5.992 | 1.396 | -4.663 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 3232 | 0 / 3232 | 2.694 | 2.366 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 1440 | 1440 / 0 | 5.972 | 5.817 | 1.312 | -4.660 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 1440 | 1440 / 0 | 5.614 | 5.603 | 1.312 | -4.302 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / router_selection | 1344 | 0 / 1344 | 5.812 | 5.734 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| QuantBatchMatmulV3 / unresolved | 1056 | 0 / 1056 | 7.378 | 7.794 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cumsum / unresolved | 1344 | 0 / 1344 | 5.385 | 5.519 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 2880 | 0 / 2880 | 2.425 | 2.389 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 1344 | 1344 / 0 | 5.052 | 5.062 | 1.312 | -3.740 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.down.quantize | 1344 | 1344 / 0 | 4.918 | 4.910 | 1.312 | -3.606 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ViewCopy / unresolved | 1088 | 0 / 1088 | 5.858 | 5.864 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 1440 | 0 / 1440 | 4.260 | 4.521 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 1344 | 1344 / 0 | 4.002 | 3.994 | 1.578 | -2.424 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 1056 | 0 / 1056 | 4.740 | 4.691 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 1792 | 0 / 1792 | 2.639 | 2.615 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 352 | 0 / 352 | 13.114 | 13.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 1440 | 0 / 1440 | 2.985 | 2.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 352 | 352 / 0 | 12.044 | 12.020 | 4.871 | -7.173 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 1440 | 0 / 1440 | 2.674 | 2.592 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 352 | 0 / 352 | 10.932 | 10.946 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1088 | 0 / 1088 | 3.505 | 3.603 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 704 | 0 / 704 | 5.381 | 5.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 352 | 0 / 352 | 10.551 | 10.430 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 704 | 0 / 704 | 5.230 | 5.160 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1088 | 0 / 1088 | 3.262 | 3.235 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 352 | 0 / 352 | 9.201 | 9.175 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 1088 | 0 / 1088 | 2.470 | 2.481 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 352 | 352 / 0 | 7.526 | 7.509 | 1.578 | -5.948 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SelectV2 / unresolved | 704 | 0 / 704 | 3.539 | 3.463 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 352 | 352 / 0 | 7.074 | 7.125 | 1.827 | -5.247 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 1440 | 0 / 1440 | 1.701 | 1.658 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 352 | 0 / 352 | 6.768 | 6.657 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 704 | 0 / 704 | 3.130 | 3.197 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 1088 | 0 / 1088 | 2.001 | 1.866 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 352 | 0 / 352 | 5.866 | 5.881 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 352 | 0 / 352 | 4.546 | 4.478 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 352 | 0 / 352 | 4.138 | 4.106 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 352 | 0 / 352 | 3.333 | 3.329 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 704 | 0 / 704 | 1.440 | 1.488 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 96 | 96 / 0 | 9.034 | 9.007 | 6.380 | -2.655 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 96 | 96 / 0 | 6.432 | 6.416 | 2.573 | -3.859 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 96 | 96 / 0 | 4.990 | 5.044 | 1.312 | -3.678 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 96 | 96 / 0 | 4.392 | 4.427 | 1.312 | -3.080 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

## a5_glm53flash_tp8_c32_p4k / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1302 | 0 / 1302 | 207.865 | 207.616 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1302 | 1302 / 0 | 109.824 | 110.412 | 87.876 | -21.948 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMla / unresolved | 341 | 0 / 341 | 153.517 | 153.209 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1395 | 0 / 1395 | 36.341 | 36.058 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1395 | 0 / 1395 | 36.213 | 32.117 | 29.881 | -6.332 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| RecurrentKda / unresolved | 1054 | 0 / 1054 | 43.987 | 44.073 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 341 | 0 / 341 | 121.532 | 121.562 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeInitRoutingV3 / unresolved | 1302 | 0 / 1302 | 24.685 | 24.843 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 1054 | 1054 / 0 | 26.517 | 26.599 | 16.566 | -9.951 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _copy_conv_state_kernel / unresolved | 2108 | 0 / 2108 | 12.896 | 12.476 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 1302 | 1302 / 0 | 19.915 | 19.981 | 19.750 | -0.165 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 6944 | 0 / 6944 | 3.616 | 3.741 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 1395 | 0 / 1395 | 16.554 | 16.336 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / ffn.hc_pre | 1395 | 0 / 1395 | 16.095 | 15.947 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| SparseFlashMlaMetadata / unresolved | 341 | 0 / 341 | 58.347 | 54.620 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 2790 | 0 / 2790 | 6.255 | 3.947 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 5704 | 0 / 5704 | 2.935 | 2.034 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1054 | 0 / 1054 | 13.045 | 13.113 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 1395 | 1395 / 0 | 8.079 | 8.107 | 2.793 | -5.286 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeFinalizeRoutingV2 / unresolved | 1302 | 0 / 1302 | 8.615 | 8.595 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 1054 | 1054 / 0 | 10.354 | 10.358 | 4.699 | -5.654 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 1395 | 1395 / 0 | 7.378 | 7.312 | 2.793 | -4.586 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 1302 | 0 / 1302 | 7.858 | 7.826 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 1302 | 1302 / 0 | 7.584 | 7.555 | 8.505 | 0.921 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 2449 | 0 / 2449 | 3.995 | 4.117 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1023 | 0 / 1023 | 8.909 | 8.679 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 3131 | 0 / 3131 | 2.892 | 2.544 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / router_selection | 1302 | 0 / 1302 | 6.633 | 6.528 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| ClipByValueV2 / unresolved | 2790 | 0 / 2790 | 2.954 | 2.813 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 1395 | 1395 / 0 | 5.554 | 5.503 | 1.312 | -4.242 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cumsum / unresolved | 1302 | 0 / 1302 | 5.612 | 5.705 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 341 | 0 / 341 | 21.113 | 21.074 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 1302 | 1302 / 0 | 5.266 | 5.299 | 1.312 | -3.954 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MaskedFill / unresolved | 1395 | 0 / 1395 | 4.805 | 5.359 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 1395 | 1395 / 0 | 4.607 | 4.552 | 1.312 | -3.295 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 1302 | 1302 / 0 | 4.424 | 4.414 | 1.578 | -2.846 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.down.quantize | 1302 | 1302 / 0 | 4.349 | 4.343 | 1.312 | -3.037 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sort / unresolved | 341 | 0 / 341 | 16.602 | 16.621 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 341 | 0 / 341 | 15.415 | 15.298 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 1054 | 0 / 1054 | 4.977 | 4.973 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 1736 | 0 / 1736 | 2.906 | 2.934 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 341 | 341 / 0 | 14.627 | 14.589 | 6.685 | -7.941 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 1395 | 0 / 1395 | 3.556 | 3.542 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 1023 | 0 / 1023 | 4.844 | 4.795 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1395 | 0 / 1395 | 3.358 | 3.261 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 341 | 0 / 341 | 12.922 | 12.969 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1054 | 0 / 1054 | 3.998 | 3.997 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1054 | 0 / 1054 | 3.631 | 3.622 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 682 | 0 / 682 | 5.468 | 5.481 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 341 | 341 / 0 | 8.709 | 8.716 | 1.721 | -6.989 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 682 | 0 / 682 | 4.265 | 4.221 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 341 | 341 / 0 | 8.328 | 8.331 | 2.582 | -5.746 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 1395 | 0 / 1395 | 2.033 | 2.051 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 1054 | 0 / 1054 | 2.635 | 2.594 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 1054 | 0 / 1054 | 2.568 | 2.622 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 682 | 0 / 682 | 3.760 | 3.756 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 682 | 0 / 682 | 3.365 | 3.317 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 341 | 0 / 341 | 5.884 | 5.916 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 341 | 0 / 341 | 5.604 | 5.457 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 341 | 0 / 341 | 5.069 | 5.034 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 341 | 0 / 341 | 4.242 | 4.221 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 341 | 0 / 341 | 3.701 | 3.666 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 93 | 93 / 0 | 11.509 | 11.425 | 8.624 | -2.885 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Fill / unresolved | 682 | 0 / 682 | 1.446 | 1.497 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / down | 93 | 93 / 0 | 7.035 | 7.002 | 3.569 | -3.465 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 93 | 93 / 0 | 5.285 | 5.293 | 1.312 | -3.973 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 93 | 93 / 0 | 4.304 | 4.279 | 1.312 | -2.992 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

## a5_glm53flash_tp8_c32_p8k / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1470 | 0 / 1470 | 207.849 | 207.460 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1470 | 1470 / 0 | 109.853 | 110.481 | 87.876 | -21.977 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 385 | 0 / 385 | 218.772 | 218.705 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 385 | 0 / 385 | 153.329 | 153.215 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1575 | 0 / 1575 | 36.168 | 32.281 | 29.881 | -6.286 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1575 | 0 / 1575 | 36.137 | 35.532 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| RecurrentKda / unresolved | 1190 | 0 / 1190 | 44.025 | 44.062 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeInitRoutingV3 / unresolved | 1470 | 0 / 1470 | 24.737 | 24.852 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 1190 | 1190 / 0 | 26.307 | 26.424 | 16.566 | -9.742 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _copy_conv_state_kernel / unresolved | 2380 | 0 / 2380 | 12.624 | 12.438 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 1470 | 1470 / 0 | 19.930 | 20.008 | 19.750 | -0.181 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 7840 | 0 / 7840 | 3.618 | 3.752 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 1575 | 0 / 1575 | 16.534 | 16.295 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / ffn.hc_pre | 1575 | 0 / 1575 | 16.156 | 15.992 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| SparseFlashMlaMetadata / unresolved | 385 | 0 / 385 | 58.595 | 55.515 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 3150 | 0 / 3150 | 6.248 | 3.953 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 6440 | 0 / 6440 | 2.930 | 2.030 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1190 | 0 / 1190 | 13.052 | 13.098 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 1575 | 1575 / 0 | 8.074 | 8.081 | 2.793 | -5.281 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeFinalizeRoutingV2 / unresolved | 1470 | 0 / 1470 | 8.595 | 8.582 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 1190 | 1190 / 0 | 10.287 | 10.296 | 4.699 | -5.587 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 1470 | 0 / 1470 | 7.959 | 7.907 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 1575 | 1575 / 0 | 7.360 | 7.286 | 2.793 | -4.567 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.gate_up | 1470 | 1470 / 0 | 7.570 | 7.546 | 8.505 | 0.935 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 2765 | 0 / 2765 | 4.001 | 4.115 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1155 | 0 / 1155 | 8.925 | 8.736 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 3535 | 0 / 3535 | 2.907 | 2.623 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / router_selection | 1470 | 0 / 1470 | 6.604 | 6.508 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| ClipByValueV2 / unresolved | 3150 | 0 / 3150 | 2.971 | 2.838 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 1575 | 1575 / 0 | 5.525 | 5.496 | 1.312 | -4.213 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cumsum / unresolved | 1470 | 0 / 1470 | 5.685 | 5.740 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 385 | 0 / 385 | 21.136 | 21.091 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 1470 | 1470 / 0 | 5.270 | 5.311 | 1.312 | -3.958 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MaskedFill / unresolved | 1575 | 0 / 1575 | 4.813 | 5.365 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 1575 | 1575 / 0 | 4.602 | 4.551 | 1.312 | -3.290 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 1470 | 1470 / 0 | 4.423 | 4.417 | 1.578 | -2.845 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.down.quantize | 1470 | 1470 / 0 | 4.357 | 4.353 | 1.312 | -3.045 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sort / unresolved | 385 | 0 / 385 | 16.620 | 16.615 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 385 | 0 / 385 | 15.560 | 15.505 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 1190 | 0 / 1190 | 4.950 | 4.974 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 1960 | 0 / 1960 | 2.910 | 2.922 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 385 | 385 / 0 | 14.624 | 14.605 | 6.685 | -7.939 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 1155 | 0 / 1155 | 4.832 | 4.785 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 1575 | 0 / 1575 | 3.525 | 3.535 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1575 | 0 / 1575 | 3.380 | 3.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 385 | 0 / 385 | 13.008 | 13.077 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1190 | 0 / 1190 | 4.022 | 4.030 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1190 | 0 / 1190 | 3.622 | 3.597 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 770 | 0 / 770 | 5.453 | 5.462 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 385 | 385 / 0 | 8.696 | 8.690 | 1.721 | -6.975 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 770 | 0 / 770 | 4.284 | 4.239 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 385 | 385 / 0 | 8.349 | 8.342 | 2.582 | -5.766 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 1575 | 0 / 1575 | 2.010 | 2.026 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 1190 | 0 / 1190 | 2.642 | 2.594 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 1190 | 0 / 1190 | 2.559 | 2.611 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 770 | 0 / 770 | 3.748 | 4.124 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 770 | 0 / 770 | 3.351 | 3.318 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 385 | 0 / 385 | 5.913 | 5.926 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 385 | 0 / 385 | 5.617 | 5.507 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 385 | 0 / 385 | 5.039 | 5.009 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 385 | 0 / 385 | 4.233 | 4.197 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 385 | 0 / 385 | 3.685 | 3.676 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 105 | 105 / 0 | 11.517 | 11.447 | 8.624 | -2.893 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Fill / unresolved | 770 | 0 / 770 | 1.453 | 1.498 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / down | 105 | 105 / 0 | 7.047 | 7.045 | 3.569 | -3.478 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 105 | 105 / 0 | 5.304 | 5.295 | 1.312 | -3.992 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 105 | 105 / 0 | 4.295 | 4.313 | 1.312 | -2.983 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

## a5_glm53flash_tp8_c4_p8k / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 462 | 0 / 462 | 98.458 | 98.182 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 462 | 462 / 0 | 51.435 | 51.334 | 38.227 | -13.208 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 495 | 0 / 495 | 23.918 | 22.357 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 495 | 0 / 495 | 21.899 | 20.531 | 25.785 | 3.886 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| MoeInitRoutingV3 / unresolved | 462 | 0 / 462 | 21.821 | 21.538 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 374 | 374 / 0 | 18.014 | 17.927 | 9.089 | -8.924 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 2464 | 0 / 2464 | 2.608 | 2.140 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 121 | 0 / 121 | 52.802 | 52.896 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 495 | 0 / 495 | 11.933 | 11.783 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 495 | 0 / 495 | 11.761 | 11.581 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 121 | 0 / 121 | 48.097 | 49.747 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 374 | 0 / 374 | 14.290 | 13.915 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMlaMetadata / unresolved | 121 | 0 / 121 | 39.293 | 36.752 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 990 | 0 / 990 | 4.716 | 3.554 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 462 | 462 / 0 | 9.708 | 9.543 | 4.093 | -5.615 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 2024 | 0 / 2024 | 1.867 | 1.847 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 462 | 462 / 0 | 7.366 | 7.275 | 4.682 | -2.684 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _copy_conv_state_kernel / unresolved | 748 | 0 / 748 | 4.524 | 4.452 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 374 | 0 / 374 | 8.331 | 8.139 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 374 | 374 / 0 | 6.738 | 6.710 | 2.393 | -4.345 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 462 | 0 / 462 | 5.415 | 5.330 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 363 | 0 / 363 | 6.439 | 6.408 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1111 | 0 / 1111 | 2.037 | 1.637 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 495 | 495 / 0 | 4.542 | 4.522 | 1.312 | -3.230 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cumsum / unresolved | 462 | 0 / 462 | 4.828 | 4.643 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 495 | 495 / 0 | 4.462 | 4.465 | 1.312 | -3.150 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 462 | 462 / 0 | 4.763 | 4.737 | 1.312 | -3.451 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeFinalizeRoutingV2 / unresolved | 462 | 0 / 462 | 4.756 | 4.720 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 869 | 0 / 869 | 2.470 | 2.526 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 374 | 0 / 374 | 5.613 | 5.579 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 495 | 495 / 0 | 4.071 | 4.063 | 1.312 | -2.759 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 495 | 495 / 0 | 4.034 | 4.038 | 1.312 | -2.722 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 462 | 462 / 0 | 4.212 | 4.173 | 1.578 | -2.634 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ClipByValueV2 / unresolved | 990 | 0 / 990 | 1.829 | 1.818 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 495 | 0 / 495 | 3.588 | 3.630 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.down.quantize | 462 | 462 / 0 | 3.690 | 3.691 | 1.312 | -2.378 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / router_selection | 462 | 0 / 462 | 3.530 | 3.514 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| DynamicMxQuant / unresolved | 363 | 0 / 363 | 4.456 | 4.458 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 616 | 0 / 616 | 2.114 | 2.050 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 121 | 0 / 121 | 10.111 | 10.121 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 121 | 121 / 0 | 9.590 | 9.573 | 3.510 | -6.079 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| layer_norm_gated_fwd_kernel / unresolved | 374 | 0 / 374 | 2.952 | 2.784 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 121 | 0 / 121 | 9.030 | 9.027 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 374 | 0 / 374 | 2.855 | 2.837 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 242 | 0 / 242 | 4.184 | 4.135 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 495 | 0 / 495 | 2.004 | 1.904 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 121 | 0 / 121 | 8.038 | 8.008 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 121 | 0 / 121 | 8.004 | 7.994 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 242 | 0 / 242 | 3.868 | 3.865 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 495 | 0 / 495 | 1.830 | 1.723 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 242 | 0 / 242 | 3.479 | 3.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 121 | 121 / 0 | 6.749 | 6.744 | 1.578 | -5.171 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Range / unresolved | 374 | 0 / 374 | 2.093 | 1.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 495 | 0 / 495 | 1.532 | 1.448 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 121 | 121 / 0 | 6.185 | 6.172 | 1.578 | -4.607 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Less / unresolved | 374 | 0 / 374 | 1.993 | 1.742 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 242 | 0 / 242 | 2.808 | 2.720 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 121 | 0 / 121 | 5.115 | 5.095 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 121 | 0 / 121 | 4.254 | 4.213 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 121 | 0 / 121 | 3.353 | 3.350 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 121 | 0 / 121 | 3.072 | 3.066 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 242 | 0 / 242 | 1.452 | 1.444 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 33 | 33 / 0 | 8.698 | 8.648 | 4.697 | -4.001 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 33 | 33 / 0 | 5.470 | 5.447 | 1.825 | -3.645 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 33 | 33 / 0 | 4.585 | 4.567 | 1.312 | -3.273 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 33 | 33 / 0 | 3.864 | 3.832 | 1.312 | -2.552 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

## a5_glm53flash_tp8_c8_p4k / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1260 | 0 / 1260 | 184.592 | 184.147 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1260 | 1260 / 0 | 91.186 | 90.988 | 76.439 | -14.748 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1350 | 0 / 1350 | 28.659 | 23.094 | 26.370 | -2.289 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1350 | 0 / 1350 | 27.877 | 27.107 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeInitRoutingV3 / unresolved | 1260 | 0 / 1260 | 21.641 | 21.509 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 330 | 0 / 330 | 69.982 | 69.982 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 1020 | 1020 / 0 | 20.058 | 19.984 | 10.157 | -9.901 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPre / ffn.hc_pre | 1350 | 0 / 1350 | 14.085 | 13.919 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| Slice / unresolved | 6720 | 0 / 6720 | 2.797 | 2.424 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 1350 | 0 / 1350 | 13.620 | 13.421 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| SparseFlashMla / unresolved | 330 | 0 / 330 | 53.600 | 53.586 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1020 | 0 / 1020 | 16.455 | 16.289 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 1260 | 1260 / 0 | 12.319 | 12.226 | 6.588 | -5.731 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMlaMetadata / unresolved | 330 | 0 / 330 | 43.981 | 41.179 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 2700 | 0 / 2700 | 5.075 | 3.628 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 5520 | 0 / 5520 | 2.331 | 1.898 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _copy_conv_state_kernel / unresolved | 2040 | 0 / 2040 | 5.823 | 5.816 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 1260 | 0 / 1260 | 7.253 | 7.213 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1020 | 0 / 1020 | 8.920 | 8.912 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 1260 | 1260 / 0 | 6.450 | 6.428 | 5.228 | -1.221 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 1350 | 1350 / 0 | 5.651 | 5.638 | 1.312 | -4.339 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 1350 | 1350 / 0 | 5.592 | 5.572 | 1.312 | -4.280 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 1020 | 1020 / 0 | 7.355 | 7.335 | 2.723 | -4.632 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 2370 | 0 / 2370 | 2.998 | 2.724 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeFinalizeRoutingV2 / unresolved | 1260 | 0 / 1260 | 5.590 | 5.567 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 1350 | 1350 / 0 | 5.067 | 5.034 | 1.312 | -3.755 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 3030 | 0 / 3030 | 2.217 | 1.858 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 1350 | 1350 / 0 | 4.953 | 4.931 | 1.312 | -3.641 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cumsum / unresolved | 1260 | 0 / 1260 | 5.238 | 5.396 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 990 | 0 / 990 | 6.514 | 6.824 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 1260 | 1260 / 0 | 4.908 | 4.912 | 1.312 | -3.596 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ViewCopy / unresolved | 1020 | 0 / 1020 | 5.735 | 5.721 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 2700 | 0 / 2700 | 2.007 | 2.069 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / router_selection | 1260 | 0 / 1260 | 4.114 | 4.046 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| MaskedFill / unresolved | 1350 | 0 / 1350 | 3.726 | 3.715 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.down.quantize | 1260 | 1260 / 0 | 3.824 | 3.814 | 1.312 | -2.512 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 1260 | 1260 / 0 | 3.782 | 3.772 | 1.578 | -2.204 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 990 | 0 / 990 | 4.696 | 4.646 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1020 | 0 / 1020 | 4.153 | 3.848 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 1680 | 0 / 1680 | 2.401 | 2.421 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 660 | 0 / 660 | 5.371 | 5.387 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 330 | 330 / 0 | 10.543 | 10.458 | 3.964 | -6.579 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 1350 | 0 / 1350 | 2.445 | 2.421 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 330 | 0 / 330 | 9.863 | 9.678 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 330 | 0 / 330 | 9.646 | 9.611 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 330 | 0 / 330 | 9.609 | 9.573 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 660 | 0 / 660 | 4.719 | 4.647 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1020 | 0 / 1020 | 2.952 | 2.962 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 1350 | 0 / 1350 | 2.200 | 2.095 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 330 | 0 / 330 | 8.327 | 8.328 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 1020 | 0 / 1020 | 2.366 | 2.530 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 1020 | 0 / 1020 | 2.327 | 2.362 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 660 | 0 / 660 | 3.548 | 3.455 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 330 | 330 / 0 | 7.082 | 7.080 | 1.578 | -5.504 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 1350 | 0 / 1350 | 1.599 | 1.507 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 330 | 330 / 0 | 6.389 | 6.287 | 1.578 | -4.811 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LayerNormV4 / unresolved | 330 | 0 / 330 | 6.007 | 5.972 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 660 | 0 / 660 | 2.894 | 2.829 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 330 | 0 / 330 | 5.225 | 5.160 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 330 | 0 / 330 | 3.885 | 3.857 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 330 | 0 / 330 | 3.467 | 3.445 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 660 | 0 / 660 | 1.477 | 1.488 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 90 | 90 / 0 | 8.263 | 8.241 | 5.258 | -3.005 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 90 | 90 / 0 | 5.747 | 5.734 | 2.074 | -3.673 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 90 | 90 / 0 | 4.856 | 4.832 | 1.312 | -3.544 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 90 | 90 / 0 | 4.348 | 4.357 | 1.312 | -3.036 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_glm53flash_tp16_aclgraph_c16 / 86c1ee8f / GroupedMatmul / expert_down | 2100 | 0 | 2100 | 0 | 0 |
| a3_glm53flash_tp16_aclgraph_c32 / 86c1ee8f / GroupedMatmul / expert_down | 2058 | 0 | 2058 | 0 | 0 |
| a3_glm53flash_tp16_aclgraph_c64 / 86c1ee8f / GroupedMatmul / expert_down | 1974 | 0 | 1974 | 0 | 0 |
| a3_glm53flash_tp16_aclgraph_c8 / 86c1ee8f / GroupedMatmul / expert_down | 1974 | 0 | 1974 | 0 | 0 |
