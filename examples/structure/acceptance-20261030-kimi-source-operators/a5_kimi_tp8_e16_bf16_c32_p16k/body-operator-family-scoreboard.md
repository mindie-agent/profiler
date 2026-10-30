# Complete Decode Body Operator Families

Only complete events inside the 41 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 | 10 / 10 | 1 / 1 | 11 / 11 | 27511 / 221523 | 0 |

## a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| FusedInferAttentionScore / unresolved | 984 | 0 / 984 | 264.091 | 263.991 | 4.730 | -259.361 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| GroupedMatmul / expert_up | 3772 | 0 / 3772 | 46.220 | 47.020 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3772 | 0 / 3772 | 34.207 | 34.204 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 5658 | 0 / 5658 | 21.498 | 21.529 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 3772 | 3772 / 0 | 26.876 | 27.136 | 14.433 | -12.443 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 7667 | 0 / 7667 | 11.400 | 11.175 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 2829 | 0 / 2829 | 30.551 | 30.527 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 3772 | 3772 / 0 | 22.659 | 22.649 | 14.303 | -8.357 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 22796 | 0 / 22796 | 3.695 | 3.687 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared.gate_up | 3772 | 3772 / 0 | 22.209 | 22.337 | 17.576 | -4.633 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GroupedMatmul / expert_down | 3772 | 0 / 3772 | 22.006 | 22.107 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| Mul / unresolved | 31324 | 0 / 31324 | 2.520 | 2.181 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 26650 | 0 / 26650 | 2.769 | 2.696 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 3813 | 0 / 3813 | 17.210 | 16.451 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Tanh / unresolved | 15170 | 0 / 15170 | 4.225 | 4.412 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 3813 | 0 / 3813 | 15.848 | 15.645 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Muls / unresolved | 15170 | 0 / 15170 | 3.932 | 3.926 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 3772 | 0 / 3772 | 14.615 | 14.506 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 3813 | 0 / 3813 | 11.053 | 10.775 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allGather_ / ffn_down_communication | 3854 | 0 / 3854 | 10.752 | 10.742 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MlaPrologV3 / unresolved | 984 | 0 / 984 | 41.668 | 41.626 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 11398 | 0 / 11398 | 3.484 | 3.829 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 2829 | 2829 / 0 | 13.836 | 13.796 | 7.089 | -6.747 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / shared.down | 3772 | 3772 / 0 | 9.527 | 9.509 | 3.737 | -5.789 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / unresolved | 2829 | 0 / 2829 | 10.981 | 10.934 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 3772 | 3772 / 0 | 7.588 | 7.525 | 2.186 | -5.402 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 3772 | 0 / 3772 | 5.810 | 5.806 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / output_gate + q_a | 984 | 984 / 0 | 19.244 | 19.120 | 17.576 | -1.668 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / latent_norm | 3772 | 3772 / 0 | 4.281 | 4.263 | 1.312 | -2.969 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / output | 984 | 984 / 0 | 14.090 | 14.098 | 7.089 | -7.001 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AsStrided / unresolved | 2829 | 0 / 2829 | 4.873 | 4.847 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 3772 | 0 / 3772 | 3.513 | 3.514 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 3813 | 0 / 3813 | 3.269 | 3.243 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 2829 | 0 / 2829 | 3.576 | 3.569 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 1968 | 0 / 1968 | 4.530 | 4.582 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 984 | 0 / 984 | 5.608 | 5.566 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / gate_up | 41 | 41 / 0 | 59.157 | 59.067 | 52.713 | -6.444 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / down | 41 | 41 / 0 | 27.331 | 27.323 | 18.818 | -8.513 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 41 | 0 / 41 | 5.823 | 5.804 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 41 | 0 / 41 | 3.933 | 3.910 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 82 | 0 / 82 | 1.683 | 1.722 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 41 | 0 / 41 | 2.351 | 2.367 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 3772 | 22.006 / 22.107 | 13.086 | 2.025 | 1.204 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 3772 | 46.220 / 47.020 | 30.880 | 4.252 | 2.841 | capacity_vs_valid_rows_conditional |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / GroupedMatmul / expert_down | 3772 | 0 | 3772 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / GroupedMatmul / expert_up | 3772 | 0 | 3772 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 3772 | 0 | 0 | 3772 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 3772 | 0 | 0 | 3772 | 0 |
