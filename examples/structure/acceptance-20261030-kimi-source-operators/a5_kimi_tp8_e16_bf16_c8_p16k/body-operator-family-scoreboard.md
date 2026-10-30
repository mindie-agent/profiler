# Complete Decode Body Operator Families

Only complete events inside the 51 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 | 11 / 11 | 0 / 0 | 11 / 11 | 34221 / 275502 | 0 |

## a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4692 | 0 / 4692 | 42.682 | 42.857 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4692 | 0 / 4692 | 32.982 | 32.979 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 7038 | 0 / 7038 | 19.580 | 19.294 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4692 | 4692 / 0 | 24.431 | 24.471 | 14.093 | -10.338 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 9537 | 0 / 9537 | 10.997 | 10.763 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 28356 | 0 / 28356 | 3.512 | 3.586 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4692 | 4692 / 0 | 21.032 | 21.030 | 14.118 | -6.913 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 1224 | 0 / 1224 | 79.395 | 79.282 | 4.730 | -74.665 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| GroupedMatmul / expert_down | 4692 | 0 / 4692 | 20.570 | 20.564 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MatMulV3 / shared.gate_up | 4692 | 4692 / 0 | 20.040 | 20.041 | 14.878 | -5.162 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 38964 | 0 / 38964 | 2.265 | 1.872 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 33150 | 0 / 33150 | 2.197 | 2.165 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 4743 | 0 / 4743 | 14.512 | 14.319 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 4692 | 0 / 4692 | 14.491 | 14.450 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 4743 | 0 / 4743 | 14.199 | 14.178 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Tanh / unresolved | 18870 | 0 / 18870 | 3.548 | 3.612 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 18870 | 0 / 18870 | 3.415 | 3.407 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 3519 | 0 / 3519 | 15.605 | 15.587 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 4743 | 0 / 4743 | 10.329 | 10.276 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allGather_ / ffn_down_communication | 4794 | 0 / 4794 | 9.945 | 9.931 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MatMulV3 / linear_output | 3519 | 3519 / 0 | 11.974 | 11.912 | 6.357 | -5.617 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 14178 | 0 / 14178 | 2.963 | 3.183 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MlaPrologV3 / unresolved | 1224 | 0 / 1224 | 33.425 | 33.389 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared.down | 4692 | 4692 / 0 | 8.355 | 8.343 | 3.285 | -5.070 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / router | 4692 | 4692 / 0 | 7.769 | 7.690 | 1.857 | -5.912 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 4692 | 0 / 4692 | 5.341 | 5.334 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 3519 | 0 / 3519 | 7.058 | 7.045 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / output_gate + q_a | 1224 | 1224 / 0 | 18.792 | 18.722 | 14.878 | -3.914 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / latent_norm | 4692 | 4692 / 0 | 4.008 | 4.034 | 1.312 | -2.696 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / output | 1224 | 1224 / 0 | 12.287 | 12.268 | 6.357 | -5.930 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AsStrided / unresolved | 3519 | 0 / 3519 | 4.068 | 4.046 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 4692 | 0 / 4692 | 2.998 | 3.032 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 4743 | 0 / 4743 | 2.936 | 2.933 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 3519 | 0 / 3519 | 3.431 | 3.417 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 2448 | 0 / 2448 | 3.626 | 3.667 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1224 | 0 / 1224 | 5.417 | 5.393 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / gate_up | 51 | 51 / 0 | 49.535 | 49.526 | 44.631 | -4.904 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / down | 51 | 51 / 0 | 24.165 | 24.129 | 17.109 | -7.056 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 51 | 0 / 51 | 4.871 | 4.912 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 102 | 0 / 102 | 1.664 | 1.641 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 51 | 0 / 51 | 2.438 | 2.417 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4692 | 20.570 / 20.564 | 12.441 | 1.892 | 1.145 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4692 | 42.682 / 42.857 | 29.389 | 3.927 | 2.704 | capacity_vs_valid_rows_conditional |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 / GroupedMatmul / expert_down | 4692 | 0 | 4692 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 / GroupedMatmul / expert_up | 4692 | 0 | 4692 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 4692 | 0 | 0 | 4692 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 4692 | 0 | 0 | 4692 | 0 |
