# Complete Decode Body Operator Families

Only complete events inside the 55 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen36-a5-tp2-c12 / source-gdn-native-runtime30dcea1e | 13 / 13 | 0 / 0 | 13 / 13 | 31680 / 98560 | 0 |

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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
