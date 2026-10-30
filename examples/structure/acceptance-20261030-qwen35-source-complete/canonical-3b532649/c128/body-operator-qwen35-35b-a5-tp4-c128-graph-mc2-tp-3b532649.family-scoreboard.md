# Complete Decode Body Operator Families

Only complete events inside the 76 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen35-35b-a5-tp4-c128-graph / mc2-tp-3b532649 | 11 / 11 | 1 / 1 | 12 / 12 | 29640 / 145160 | 0 |

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
