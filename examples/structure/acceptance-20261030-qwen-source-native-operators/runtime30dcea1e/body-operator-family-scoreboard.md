# Complete Decode Body Operator Families

Only complete events inside the 403 accepted target-body windows from 6 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen35-35b-a5-tp4-c128-graph / source-gdn-native-runtime30dcea1e | 11 / 11 | 1 / 1 | 12 / 12 | 29640 / 145160 | 0 |
| qwen35-35b-a5-tp4-c4-graph / source-gdn-native-runtime30dcea1e | 12 / 12 | 0 / 0 | 12 / 12 | 32760 / 141960 | 0 |
| qwen35-35b-a5-tp4-c64-graph / source-gdn-native-runtime30dcea1e | 11 / 11 | 1 / 1 | 12 / 12 | 30810 / 138250 | 0 |
| qwen36-a5-tp2-c1 / source-gdn-native-runtime30dcea1e | 13 / 13 | 0 / 0 | 13 / 13 | 48960 / 148240 | 0 |
| qwen36-a5-tp2-c12 / source-gdn-native-runtime30dcea1e | 13 / 13 | 0 / 0 | 13 / 13 | 31680 / 98560 | 0 |
| qwen36-a5-tp2-c96 / source-gdn-native-runtime30dcea1e | 7 / 10 | 1 / 3 | 8 / 13 | 13824 / 45312 | 0 |

## qwen35-35b-a5-tp4-c128-graph / source-gdn-native-runtime30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / unresolved | 6080 | 0 / 6080 | 52.598 | 54.684 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2280 | 2280 / 0 | 124.319 | 124.200 | 111.996 | -12.322 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DequantSwigluQuant / unresolved | 3040 | 0 / 3040 | 56.560 | 56.844 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 3040 | 0 / 3040 | 48.966 | 47.539 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_ / ffn_down_communication | 3040 | 0 / 3040 | 45.528 | 45.444 | 18.825 | -26.704 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| MoeDistributeCombineV3 / expert_combine_native | 3040 | 0 / 3040 | 43.109 | 43.058 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / unresolved | 3040 | 0 / 3040 | 41.178 | 41.103 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 760 | 0 / 760 | 145.541 | 144.542 | 135.434 | -10.107 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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
| fused_gdn_gating_kernel / unresolved | 2280 | 0 / 2280 | 6.481 | 6.510 | 42.444 | 35.963 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## qwen35-35b-a5-tp4-c4-graph / source-gdn-native-runtime30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / unresolved | 6720 | 0 / 6720 | 27.975 | 26.755 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 3360 | 0 / 3360 | 27.597 | 25.198 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_ / ffn_down_communication | 3360 | 0 / 3360 | 25.232 | 25.222 | 11.051 | -14.182 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| MoeDistributeDispatchV3 / unresolved | 3360 | 0 / 3360 | 17.246 | 16.954 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 3360 | 0 / 3360 | 11.678 | 11.374 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 840 | 0 / 840 | 45.006 | 44.972 | 32.029 | -12.978 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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
| fused_gdn_gating_kernel / unresolved | 2520 | 0 / 2520 | 5.242 | 4.984 | 11.138 | 5.897 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## qwen35-35b-a5-tp4-c64-graph / source-gdn-native-runtime30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / unresolved | 6320 | 0 / 6320 | 51.347 | 53.046 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSwigluQuant / unresolved | 3160 | 0 / 3160 | 54.031 | 54.304 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2370 | 2370 / 0 | 56.665 | 56.645 | 55.998 | -0.667 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_ / attention_output_communication | 3160 | 0 / 3160 | 40.059 | 34.079 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_ / ffn_down_communication | 3160 | 0 / 3160 | 32.247 | 32.212 | 14.812 | -17.434 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| MoeDistributeDispatchV3 / unresolved | 3160 | 0 / 3160 | 28.796 | 29.044 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 3160 | 0 / 3160 | 27.371 | 28.149 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 3160 | 0 / 3160 | 24.071 | 23.750 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| FusedInferAttentionScore / unresolved | 790 | 0 / 790 | 87.739 | 86.582 | 67.717 | -20.023 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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
| fused_gdn_gating_kernel / unresolved | 2370 | 0 / 2370 | 6.260 | 6.301 | 42.444 | 36.184 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## qwen36-a5-tp2-c1 / source-gdn-native-runtime30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| QuantBatchMatmulV3 / gate_up | 5440 | 5440 / 0 | 28.682 | 28.551 | 26.222 | -2.460 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 5440 | 5440 / 0 | 17.921 | 17.816 | 17.703 | -0.218 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 4080 | 4080 / 0 | 17.147 | 17.150 | 12.540 | -4.608 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 1360 | 0 / 1360 | 47.664 | 47.670 | 32.179 | -15.485 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / linear_qkvz | 4080 | 4080 / 0 | 15.777 | 15.620 | 10.524 | -5.253 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_ / attention_output_communication | 5440 | 0 / 5440 | 11.355 | 10.226 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| fused_gdn_gating_kernel / unresolved | 4080 | 0 / 4080 | 14.513 | 14.507 | 7.112 | -7.401 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| hcom_allReduce_ / ffn_down_communication | 5440 | 0 / 5440 | 10.310 | 9.825 | 3.704 | -6.606 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 4080 | 4080 / 0 | 9.371 | 9.348 | 6.283 | -3.088 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuantV2 / unresolved | 10880 | 0 / 10880 | 2.873 | 2.931 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / short_convolution | 4080 | 4080 / 0 | 7.008 | 6.985 | 1.312 | -5.696 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 13600 | 0 / 13600 | 2.032 | 2.103 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNormDynamicQuant / unresolved | 6800 | 0 / 6800 | 4.048 | 4.000 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 4080 | 4080 / 0 | 6.568 | 6.511 | 4.070 | -2.498 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / qkv | 1360 | 1360 / 0 | 14.573 | 14.500 | 10.449 | -4.125 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SwiGlu / swiglu | 5440 | 5440 / 0 | 3.267 | 3.247 | 1.312 | -1.955 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / k_flat + q_flat | 8160 | 0 / 8160 | 1.949 | 1.940 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 8160 | 0 / 8160 | 1.820 | 1.847 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 5440 | 0 / 5440 | 2.705 | 2.830 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 4080 | 4080 / 0 | 3.517 | 3.497 | 1.312 | -2.205 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 4080 | 0 / 4080 | 3.428 | 3.347 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 8160 | 0 / 8160 | 1.630 | 1.653 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 4080 | 0 / 4080 | 3.254 | 3.227 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNorm / unresolved | 3995 | 0 / 3995 | 3.123 | 3.099 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / output | 1360 | 1360 / 0 | 8.903 | 8.837 | 6.300 | -2.603 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / v_flat | 4080 | 4080 / 0 | 2.843 | 2.840 | 1.312 | -1.531 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 4080 | 0 / 4080 | 2.091 | 2.062 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 1360 | 0 / 1360 | 5.409 | 5.413 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterPaKvCache / cache | 1360 | 1360 / 0 | 3.208 | 3.205 | 1.312 | -1.896 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 1360 | 0 / 1360 | 3.099 | 3.101 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1360 | 0 / 1360 | 2.984 | 2.984 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1360 | 0 / 1360 | 2.577 | 2.546 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 85 | 0 / 85 | 2.950 | 2.887 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## qwen36-a5-tp2-c12 / source-gdn-native-runtime30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| fused_gdn_gating_kernel / unresolved | 2640 | 0 / 2640 | 83.485 | 82.982 | 73.439 | -10.047 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| hcom_allReduce_ / attention_output_communication | 3520 | 0 / 3520 | 48.022 | 42.060 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_ / ffn_down_communication | 3520 | 0 / 3520 | 39.588 | 39.557 | 4.854 | -34.734 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| QuantBatchMatmulV3 / gate_up | 3520 | 3520 / 0 | 30.985 | 30.913 | 35.464 | 4.479 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2640 | 2640 / 0 | 33.701 | 33.493 | 34.157 | 0.456 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 3520 | 3520 / 0 | 20.742 | 20.680 | 23.743 | 3.001 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 2640 | 2640 / 0 | 24.035 | 24.084 | 16.888 | -7.147 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 880 | 0 / 880 | 53.501 | 53.391 | 32.223 | -21.278 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / linear_qkvz | 2640 | 2640 / 0 | 17.226 | 17.107 | 14.255 | -2.971 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuantV2 / unresolved | 7040 | 0 / 7040 | 6.033 | 5.992 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNormDynamicQuant / unresolved | 4400 | 0 / 4400 | 8.424 | 8.309 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / short_convolution | 2640 | 2640 / 0 | 12.756 | 12.793 | 1.345 | -11.411 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SwiGlu / swiglu | 3520 | 3520 / 0 | 6.463 | 6.474 | 1.312 | -5.151 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 6160 | 0 / 6160 | 3.642 | 3.728 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 2640 | 2640 / 0 | 8.012 | 7.920 | 7.560 | -0.452 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 8800 | 0 / 8800 | 2.169 | 2.188 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / k_flat + q_flat | 5280 | 0 / 5280 | 3.249 | 3.238 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNorm / unresolved | 2585 | 0 / 2585 | 6.220 | 6.194 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 2640 | 0 / 2640 | 5.403 | 5.484 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 880 | 880 / 0 | 16.173 | 16.117 | 14.230 | -1.943 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| l2norm_fwd_kernel2 / unresolved | 5280 | 0 / 5280 | 2.445 | 2.329 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 2640 | 0 / 2640 | 4.605 | 4.654 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 2640 | 0 / 2640 | 4.086 | 4.069 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 5280 | 0 / 5280 | 1.989 | 1.909 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 2640 | 2640 / 0 | 3.595 | 3.554 | 1.312 | -2.283 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / output | 880 | 880 / 0 | 10.426 | 10.377 | 8.724 | -1.702 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / v_flat | 2640 | 2640 / 0 | 3.148 | 3.130 | 1.312 | -1.836 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 880 | 0 / 880 | 7.939 | 7.972 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterPaKvCache / cache | 880 | 880 / 0 | 5.263 | 5.227 | 1.312 | -3.951 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 880 | 0 / 880 | 5.152 | 5.128 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 880 | 0 / 880 | 3.672 | 3.679 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 880 | 0 / 880 | 3.341 | 3.337 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 55 | 0 / 55 | 5.807 | 5.785 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## qwen36-a5-tp2-c96 / source-gdn-native-runtime30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 1152 | 1152 / 0 | 277.265 | 277.185 | 251.992 | -25.273 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_ / attention_output_communication | 1536 | 0 / 1536 | 131.762 | 126.662 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_ / ffn_down_communication | 1536 | 0 / 1536 | 127.838 | 127.701 | 13.631 | -114.207 | 15% (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| QuantBatchMatmulV3 / gate_up | 1536 | 1536 / 0 | 92.692 | 92.758 | 137.424 | 44.732 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| fused_gdn_gating_kernel / unresolved | 1152 | 0 / 1152 | 120.051 | 120.044 | 97.215 | -22.836 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / down | 1536 | 1536 / 0 | 53.469 | 53.368 | 70.170 | 16.701 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 384 | 0 / 384 | 211.832 | 211.458 | 204.210 | -7.622 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / linear_qkvz | 1152 | 1152 / 0 | 45.282 | 45.080 | 63.556 | 18.274 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 1152 | 1152 / 0 | 42.278 | 42.222 | 49.954 | 7.676 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 1152 | 1152 / 0 | 36.393 | 36.390 | 10.056 | -26.337 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicQuant / unresolved | 1920 | 0 / 1920 | 12.904 | 13.079 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuantV2 / unresolved | 3072 | 0 / 3072 | 7.810 | 8.028 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 384 | 384 / 0 | 45.349 | 45.157 | 63.372 | 18.023 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SwiGlu / swiglu | 1536 | 1536 / 0 | 11.068 | 11.037 | 5.014 | -6.055 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 2688 | 0 / 2688 | 4.653 | 4.269 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 1152 | 0 / 1152 | 9.659 | 9.591 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 2304 | 0 / 2304 | 4.678 | 4.778 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 1152 | 1152 / 0 | 9.019 | 8.880 | 13.905 | 4.887 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 3840 | 0 / 3840 | 2.632 | 2.875 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNorm / unresolved | 1128 | 0 / 1128 | 8.575 | 8.562 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 2304 | 0 / 2304 | 4.108 | 4.133 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 384 | 0 / 384 | 23.770 | 23.718 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / k_flat + q_flat | 2304 | 0 / 2304 | 3.910 | 3.867 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / output | 384 | 384 / 0 | 22.172 | 22.023 | 26.479 | 4.307 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ConcatD / unresolved | 1152 | 0 / 1152 | 5.427 | 5.401 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 1152 | 1152 / 0 | 5.312 | 5.269 | 1.966 | -3.346 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 1152 | 0 / 1152 | 4.682 | 4.668 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 2304 | 0 / 2304 | 2.300 | 2.357 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / v_flat | 1152 | 1152 / 0 | 4.192 | 4.175 | 1.312 | -2.880 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / cache | 384 | 384 / 0 | 6.906 | 6.909 | 1.312 | -5.594 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 384 | 0 / 384 | 6.200 | 6.205 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 384 | 0 / 384 | 4.695 | 4.660 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 384 | 0 / 384 | 4.405 | 4.407 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 24 | 0 / 24 | 6.789 | 6.795 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen35-35b-a5-tp4-c128-graph / source-gdn-native-runtime30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 3040 | 0 | 0 | 3040 | 0 |
| qwen35-35b-a5-tp4-c4-graph / source-gdn-native-runtime30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 3360 | 0 | 0 | 3360 | 0 |
| qwen35-35b-a5-tp4-c64-graph / source-gdn-native-runtime30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 3160 | 0 | 0 | 3160 | 0 |
