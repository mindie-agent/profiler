# Complete Decode Body Operator Families

Only complete events inside the 24 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen36-a5-tp2-c96 / source-gdn-native-runtime30dcea1e | 7 / 10 | 1 / 3 | 8 / 13 | 13824 / 45312 | 0 |

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
