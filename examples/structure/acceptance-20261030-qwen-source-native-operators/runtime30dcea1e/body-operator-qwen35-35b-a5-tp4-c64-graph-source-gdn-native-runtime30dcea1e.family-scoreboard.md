# Complete Decode Body Operator Families

Only complete events inside the 79 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen35-35b-a5-tp4-c64-graph / source-gdn-native-runtime30dcea1e | 11 / 11 | 1 / 1 | 12 / 12 | 30810 / 138250 | 0 |

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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen35-35b-a5-tp4-c64-graph / source-gdn-native-runtime30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 3160 | 0 | 0 | 3160 | 0 |
