# Complete Decode Body Operator Families

Only complete events inside the 239 accepted target-body windows from 3 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen35-35b-a5-tp4-c4-graph / mc2-tp-3b532649 | 12 / 12 | 0 / 0 | 12 / 12 | 32760 / 141960 | 0 |
| qwen35-35b-a5-tp4-c64-graph / mc2-tp-3b532649 | 11 / 11 | 1 / 1 | 12 / 12 | 30810 / 138250 | 0 |
| qwen35-35b-a5-tp4-c128-graph / mc2-tp-3b532649 | 11 / 11 | 1 / 1 | 12 / 12 | 29640 / 145160 | 0 |

## qwen35-35b-a5-tp4-c4-graph / mc2-tp-3b532649

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / unresolved | 6720 | 0 / 6720 | 27.975 | 26.755 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 3360 | 0 / 3360 | 27.597 | 25.198 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / ffn_down_communication | 3360 | 0 / 3360 | 25.232 | 25.222 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / unresolved | 3360 | 0 / 3360 | 17.246 | 16.954 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 3360 | 0 / 3360 | 11.678 | 11.374 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 840 | 0 / 840 | 45.006 | 44.972 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 3360 | 0 / 3360 | 10.573 | 10.290 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MatMulV3 / router | 6720 | 6720 / 0 | 3.939 | 3.928 | 4.604 | 0.665 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2520 | 2520 / 0 | 10.133 | 10.102 | 6.415 | -3.718 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DequantSwigluQuant / unresolved | 3360 | 0 / 3360 | 7.299 | 7.286 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNorm / unresolved | 5796 | 0 / 5796 | 3.971 | 3.956 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvz | 2520 | 2520 / 0 | 8.154 | 8.075 | 4.619 | -3.535 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 2520 | 2520 / 0 | 7.337 | 7.293 | 1.312 | -6.025 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 3360 | 0 / 3360 | 4.776 | 4.735 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 8400 | 0 / 8400 | 1.910 | 1.952 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 5880 | 0 / 5880 | 2.717 | 2.485 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 4200 | 0 / 4200 | 3.425 | 3.053 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 4200 | 0 / 4200 | 3.244 | 3.194 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| fused_gdn_gating_kernel / unresolved | 2520 | 0 / 2520 | 5.242 | 4.984 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 2520 | 2520 / 0 | 4.698 | 4.676 | 2.377 | -2.321 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / k_flat + q_flat | 5040 | 0 / 5040 | 2.221 | 2.236 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 3360 | 0 / 3360 | 3.141 | 3.130 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 5040 | 0 / 5040 | 2.017 | 1.950 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared_gate | 3360 | 3360 / 0 | 2.825 | 2.841 | 1.578 | -1.247 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / alpha_contiguous + beta_contiguous | 5040 | 0 / 5040 | 1.840 | 1.831 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 2520 | 0 / 2520 | 3.657 | 3.502 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 3360 | 0 / 3360 | 2.627 | 2.548 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 2520 | 2520 / 0 | 3.260 | 3.265 | 1.578 | -1.682 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RealDiv / unresolved | 3360 | 0 / 3360 | 2.437 | 2.453 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / shared.swiglu | 3360 | 3360 / 0 | 2.345 | 2.397 | 1.312 | -1.033 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ReduceSum / unresolved | 3360 | 0 / 3360 | 2.295 | 2.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 4200 | 0 / 4200 | 1.777 | 1.603 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNormDynamicQuant / unresolved | 840 | 0 / 840 | 8.085 | 8.397 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 2520 | 2520 / 0 | 2.513 | 2.492 | 1.312 | -1.201 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 2520 | 0 / 2520 | 2.354 | 2.233 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 840 | 840 / 0 | 6.768 | 6.694 | 2.365 | -4.404 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / v_flat | 2520 | 2520 / 0 | 2.084 | 2.080 | 1.312 | -0.772 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 840 | 0 / 840 | 6.229 | 6.253 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sub / unresolved | 3360 | 0 / 3360 | 1.502 | 1.440 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 3360 | 0 / 3360 | 1.407 | 1.373 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterPaKvCache / cache | 840 | 840 / 0 | 3.827 | 3.804 | 1.312 | -2.515 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 840 | 0 / 840 | 3.399 | 3.396 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 84 | 0 / 84 | 4.159 | 4.138 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## qwen35-35b-a5-tp4-c64-graph / mc2-tp-3b532649

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / unresolved | 6320 | 0 / 6320 | 51.347 | 53.046 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSwigluQuant / unresolved | 3160 | 0 / 3160 | 54.031 | 54.304 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2370 | 2370 / 0 | 56.665 | 56.645 | 55.998 | -0.667 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_ / attention_output_communication | 3160 | 0 / 3160 | 40.059 | 34.079 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / ffn_down_communication | 3160 | 0 / 3160 | 32.247 | 32.212 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / unresolved | 3160 | 0 / 3160 | 28.796 | 29.044 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 3160 | 0 / 3160 | 27.371 | 28.149 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 3160 | 0 / 3160 | 24.071 | 23.750 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| FusedInferAttentionScore / unresolved | 790 | 0 / 790 | 87.739 | 86.582 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 6320 | 6320 / 0 | 6.457 | 6.417 | 8.487 | 2.030 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_qkvz | 2370 | 2370 / 0 | 15.706 | 15.604 | 17.027 | 1.321 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNorm / unresolved | 5451 | 0 / 5451 | 5.822 | 5.791 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / short_convolution | 2370 | 2370 / 0 | 10.995 | 11.030 | 2.792 | -8.203 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 3160 | 0 / 3160 | 7.439 | 7.419 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 5530 | 0 / 5530 | 4.132 | 4.344 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 3160 | 0 / 3160 | 6.696 | 6.681 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 3950 | 0 / 3950 | 5.271 | 5.701 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 2370 | 2370 / 0 | 8.334 | 8.315 | 4.699 | -3.635 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TensorMove / unresolved | 4740 | 0 / 4740 | 3.872 | 3.878 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 3950 | 0 / 3950 | 4.617 | 3.761 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / k_flat + q_flat | 4740 | 0 / 4740 | 3.732 | 3.690 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 7900 | 0 / 7900 | 2.147 | 2.188 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| fused_gdn_gating_kernel / unresolved | 2370 | 0 / 2370 | 6.260 | 6.301 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 4740 | 0 / 4740 | 2.898 | 2.815 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 2370 | 0 / 2370 | 5.704 | 5.789 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 790 | 0 / 790 | 17.054 | 16.941 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / shared.swiglu | 3160 | 3160 / 0 | 3.799 | 3.790 | 1.312 | -2.487 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 3950 | 0 / 3950 | 2.813 | 2.379 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared_gate | 3160 | 3160 / 0 | 3.503 | 3.507 | 4.084 | 0.581 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / convolution_input_contiguous | 2370 | 2370 / 0 | 4.528 | 4.495 | 1.312 | -3.216 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / alpha_contiguous + beta_contiguous | 4740 | 0 / 4740 | 2.247 | 2.239 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 3160 | 0 / 3160 | 3.341 | 3.423 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 2370 | 0 / 2370 | 4.390 | 4.392 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RealDiv / unresolved | 3160 | 0 / 3160 | 3.194 | 3.289 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 790 | 790 / 0 | 11.906 | 11.793 | 9.208 | -2.698 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ReduceSum / unresolved | 3160 | 0 / 3160 | 2.866 | 2.850 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 2370 | 2370 / 0 | 3.706 | 3.683 | 4.604 | 0.898 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / v_flat | 2370 | 2370 / 0 | 3.604 | 3.590 | 1.312 | -2.292 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sub / unresolved | 3160 | 0 / 3160 | 2.419 | 2.603 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNormDynamicQuant / unresolved | 790 | 0 / 790 | 9.539 | 9.482 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 3160 | 0 / 3160 | 1.888 | 1.905 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterPaKvCache / cache | 790 | 790 / 0 | 6.499 | 6.490 | 1.312 | -5.187 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 790 | 0 / 790 | 4.119 | 4.131 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 79 | 0 / 79 | 6.399 | 6.411 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## qwen35-35b-a5-tp4-c128-graph / mc2-tp-3b532649

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / unresolved | 6080 | 0 / 6080 | 52.598 | 54.684 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2280 | 2280 / 0 | 124.319 | 124.200 | 111.996 | -12.322 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DequantSwigluQuant / unresolved | 3040 | 0 / 3040 | 56.560 | 56.844 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 3040 | 0 / 3040 | 48.966 | 47.539 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / ffn_down_communication | 3040 | 0 / 3040 | 45.528 | 45.444 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 3040 | 0 / 3040 | 43.109 | 43.058 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / unresolved | 3040 | 0 / 3040 | 41.178 | 41.103 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 760 | 0 / 760 | 145.541 | 144.542 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 3040 | 0 / 3040 | 30.174 | 30.088 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| TensorMove / unresolved | 16720 | 0 / 16720 | 3.677 | 3.628 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvz | 2280 | 2280 / 0 | 22.362 | 22.328 | 25.645 | 3.283 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / router | 6080 | 6080 / 0 | 7.620 | 7.598 | 8.487 | 0.867 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 2280 | 2280 / 0 | 16.326 | 16.367 | 5.584 | -10.742 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNorm / unresolved | 5244 | 0 / 5244 | 6.703 | 6.728 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 2280 | 2280 / 0 | 10.719 | 10.700 | 9.214 | -1.505 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 3040 | 0 / 3040 | 7.671 | 7.644 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 5320 | 0 / 5320 | 4.252 | 4.419 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 3800 | 0 / 3800 | 5.918 | 6.368 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 760 | 0 / 760 | 29.411 | 29.408 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 3040 | 0 / 3040 | 7.245 | 7.226 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 3800 | 0 / 3800 | 5.672 | 4.363 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / k_flat + q_flat | 4560 | 0 / 4560 | 3.885 | 3.850 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 7600 | 0 / 7600 | 2.262 | 2.237 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 4560 | 0 / 4560 | 3.746 | 3.564 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 2280 | 0 / 2280 | 7.063 | 7.064 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| fused_gdn_gating_kernel / unresolved | 2280 | 0 / 2280 | 6.481 | 6.510 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared_gate | 3040 | 3040 / 0 | 4.194 | 4.145 | 4.084 | -0.110 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SwiGlu / shared.swiglu | 3040 | 3040 / 0 | 4.162 | 4.129 | 1.312 | -2.850 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 3800 | 0 / 3800 | 2.913 | 2.430 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 760 | 760 / 0 | 14.180 | 14.036 | 13.866 | -0.314 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / convolution_input_contiguous | 2280 | 2280 / 0 | 4.706 | 4.669 | 1.312 | -3.394 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RealDiv / unresolved | 3040 | 0 / 3040 | 3.416 | 3.484 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 3040 | 0 / 3040 | 3.366 | 3.365 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 2280 | 0 / 2280 | 4.478 | 4.481 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 4560 | 0 / 4560 | 2.191 | 2.166 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 2280 | 2280 / 0 | 4.184 | 4.164 | 4.604 | 0.420 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ReduceSum / unresolved | 3040 | 0 / 3040 | 2.889 | 2.912 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / v_flat | 2280 | 2280 / 0 | 3.839 | 3.830 | 1.312 | -2.527 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicQuant / unresolved | 760 | 0 / 760 | 10.336 | 10.325 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sub / unresolved | 3040 | 0 / 3040 | 2.520 | 2.546 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 3040 | 0 / 3040 | 1.973 | 1.976 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterPaKvCache / cache | 760 | 760 / 0 | 7.165 | 7.141 | 1.312 | -5.853 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 760 | 0 / 760 | 4.782 | 4.759 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 76 | 0 / 76 | 6.589 | 6.644 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
