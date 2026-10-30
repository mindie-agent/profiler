# Complete Decode Body Operator Families

Only complete events inside the 223 accepted target-body windows from 5 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_glm53flash_tp8_c64_p4k / source-full-18c423c7 | 18 / 18 | 1 / 1 | 19 / 19 | 16895 / 81499 | 0 |
| a5_glm53flash_tp8_c32_p4k / source-full-18c423c7 | 18 / 18 | 1 / 1 | 19 / 19 | 16895 / 80445 | 0 |
| glm53flash-a5-tp8-c1 / source-full-18c423c7 | 19 / 19 | 0 / 0 | 19 / 19 | 35425 / 167960 | 0 |
| a3_glm53flash_tp16_aclgraph_c32 / source-full-18c423c7 | 16 / 21 | 0 / 0 | 16 / 21 | 25039 / 101920 | 0 |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 | 12 / 17 | 0 / 4 | 12 / 21 | 24017 / 97760 | 0 |

## a5_glm53flash_tp8_c64_p4k / source-full-18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1302 | 0 / 1302 | 211.089 | 210.722 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1302 | 1302 / 0 | 115.777 | 117.337 | 111.195 | -4.582 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMla / unresolved | 341 | 0 / 341 | 288.254 | 285.492 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1054 | 0 / 1054 | 78.338 | 78.285 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 341 | 0 / 341 | 218.721 | 218.708 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1395 | 0 / 1395 | 43.605 | 39.492 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1395 | 0 / 1395 | 41.711 | 41.084 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
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

## a5_glm53flash_tp8_c32_p4k / source-full-18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1302 | 0 / 1302 | 207.865 | 207.616 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1302 | 1302 / 0 | 109.824 | 110.412 | 106.775 | -3.049 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMla / unresolved | 341 | 0 / 341 | 153.517 | 153.209 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1395 | 0 / 1395 | 36.341 | 36.058 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1395 | 0 / 1395 | 36.213 | 32.117 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
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

## glm53flash-a5-tp8-c1 / source-full-18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 2730 | 0 / 2730 | 33.520 | 33.429 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 2925 | 0 / 2925 | 23.103 | 17.851 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 2730 | 2730 / 0 | 22.482 | 22.473 | 11.527 | -10.954 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 2925 | 0 / 2925 | 20.753 | 18.202 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeInitRoutingV3 / unresolved | 2730 | 0 / 2730 | 20.796 | 20.692 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 2210 | 2210 / 0 | 16.983 | 16.915 | 8.288 | -8.695 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMla / unresolved | 715 | 0 / 715 | 51.517 | 51.481 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 2925 | 0 / 2925 | 11.217 | 11.078 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 2925 | 0 / 2925 | 11.033 | 10.866 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| Slice / unresolved | 14560 | 0 / 14560 | 2.151 | 1.935 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 2210 | 0 / 2210 | 13.004 | 12.695 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 5850 | 0 / 5850 | 4.571 | 3.506 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMlaMetadata / unresolved | 715 | 0 / 715 | 34.980 | 31.811 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 2730 | 2730 / 0 | 8.756 | 8.742 | 16.546 | 7.790 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.gate_up | 2730 | 2730 / 0 | 7.072 | 6.974 | 4.273 | -2.800 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 11960 | 0 / 11960 | 1.522 | 1.559 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _copy_conv_state_kernel / unresolved | 4420 | 0 / 4420 | 3.684 | 3.564 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 2210 | 0 / 2210 | 6.755 | 6.612 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 2210 | 2210 / 0 | 6.347 | 6.348 | 2.152 | -4.194 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 2730 | 2730 / 0 | 4.972 | 4.928 | 1.312 | -3.660 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / unresolved | 2145 | 0 / 2145 | 6.259 | 6.362 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cumsum / unresolved | 2730 | 0 / 2730 | 4.537 | 4.547 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 6565 | 0 / 6565 | 1.866 | 1.641 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 2925 | 2925 / 0 | 4.150 | 4.115 | 1.312 | -2.838 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeFinalizeRoutingV2 / unresolved | 2730 | 0 / 2730 | 4.432 | 4.418 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 2925 | 2925 / 0 | 4.123 | 4.091 | 1.312 | -2.811 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 2730 | 0 / 2730 | 4.213 | 4.196 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 2730 | 2730 / 0 | 4.156 | 4.133 | 1.578 | -2.578 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 5135 | 0 / 5135 | 2.079 | 2.009 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 5850 | 0 / 5850 | 1.621 | 1.633 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 2145 | 0 / 2145 | 4.420 | 4.297 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 2925 | 0 / 2925 | 3.129 | 3.018 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / router_selection | 2730 | 0 / 2730 | 3.213 | 3.193 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 715 | 0 / 715 | 12.144 | 12.159 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 2925 | 2925 / 0 | 2.718 | 2.687 | 1.312 | -1.406 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 2925 | 2925 / 0 | 2.714 | 2.694 | 1.312 | -1.402 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ViewCopy / unresolved | 2210 | 0 / 2210 | 3.514 | 3.501 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 3640 | 0 / 3640 | 2.023 | 1.993 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.down.quantize | 2730 | 2730 / 0 | 2.479 | 2.470 | 1.312 | -1.167 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / index_q | 715 | 715 / 0 | 8.899 | 8.873 | 3.176 | -5.722 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TopKV2 / unresolved | 715 | 0 / 715 | 8.805 | 8.722 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 715 | 0 / 715 | 8.432 | 8.423 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 2210 | 0 / 2210 | 2.657 | 2.630 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 1430 | 0 / 1430 | 3.989 | 3.984 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 715 | 0 / 715 | 7.612 | 7.539 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 2925 | 0 / 2925 | 1.798 | 1.750 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 2210 | 0 / 2210 | 2.257 | 2.192 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 2925 | 0 / 2925 | 1.661 | 1.641 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 715 | 715 / 0 | 5.979 | 5.961 | 1.578 | -4.401 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeBatchMatMul / q_absorb | 715 | 715 / 0 | 5.976 | 5.929 | 1.578 | -4.398 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 2925 | 0 / 2925 | 1.457 | 1.434 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 2210 | 0 / 2210 | 1.905 | 1.818 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 1430 | 0 / 1430 | 2.879 | 2.795 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 2210 | 0 / 2210 | 1.769 | 1.683 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 1430 | 0 / 1430 | 2.482 | 2.485 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 715 | 0 / 715 | 4.792 | 4.772 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 715 | 0 / 715 | 4.498 | 4.498 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 1430 | 0 / 1430 | 2.116 | 2.079 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 715 | 0 / 715 | 3.361 | 3.358 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 1430 | 0 / 1430 | 1.487 | 1.452 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 715 | 0 / 715 | 2.792 | 2.797 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 715 | 0 / 715 | 2.428 | 2.413 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 195 | 195 / 0 | 8.466 | 8.429 | 4.276 | -4.190 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 195 | 195 / 0 | 5.176 | 5.175 | 1.642 | -3.534 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 195 | 195 / 0 | 5.041 | 5.037 | 1.312 | -3.729 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 195 | 195 / 0 | 3.820 | 3.825 | 1.312 | -2.508 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

## a3_glm53flash_tp16_aclgraph_c32 / source-full-18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2058 | 0 / 2058 | 243.005 | 243.005 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| KvQuantSparseFlashAttentionVllm / unresolved | 539 | 0 / 539 | 829.848 | 829.977 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 2058 | 0 / 2058 | 120.125 | 119.862 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1666 | 0 / 1666 | 143.761 | 143.613 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 2205 | 0 / 2205 | 88.072 | 87.222 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / ffn_down_communication | 2205 | 0 / 2205 | 76.407 | 75.842 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
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

## a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| KvQuantSparseFlashAttentionVllm / unresolved | 517 | 0 / 517 | 1632.353 | 1632.673 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 0 / 1974 | 245.405 | 245.005 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| RecurrentKda / unresolved | 1598 | 0 / 1598 | 245.540 | 250.525 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 2115 | 0 / 2115 | 149.172 | 148.443 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / ffn_down_communication | 2115 | 0 / 2115 | 135.178 | 134.783 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1974 | 0 / 1974 | 120.959 | 120.713 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
