# Complete Decode Body Operator Families

Only complete events inside the 85 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen36-a5-tp2-c1 / source-gdn-native-runtime30dcea1e | 13 / 13 | 0 / 0 | 13 / 13 | 48960 / 148240 | 0 |

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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
