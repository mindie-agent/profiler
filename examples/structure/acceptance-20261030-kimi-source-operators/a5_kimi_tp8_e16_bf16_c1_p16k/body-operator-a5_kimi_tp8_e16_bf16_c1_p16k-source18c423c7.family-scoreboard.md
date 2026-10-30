# Complete Decode Body Operator Families

Only complete events inside the 59 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 | 6 / 6 | 0 / 0 | 6 / 6 | 21830 / 303732 | 0 |

## a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MatMulV3 / unresolved | 25901 | 0 / 25901 | 15.021 | 12.030 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 5428 | 0 / 5428 | 31.319 | 31.314 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 5428 | 5428 / 0 | 23.857 | 23.814 | 14.093 | -9.765 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 11033 | 0 / 11033 | 10.977 | 10.820 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 5428 | 0 / 5428 | 21.957 | 21.948 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MatMulV3 / latent_up | 5428 | 5428 / 0 | 20.594 | 20.593 | 14.118 | -6.476 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 45076 | 0 / 45076 | 2.359 | 1.935 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 5428 | 0 / 5428 | 16.052 | 16.026 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| Cast / unresolved | 38350 | 0 / 38350 | 2.145 | 1.926 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 5487 | 0 / 5487 | 14.604 | 14.477 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 5428 | 0 / 5428 | 14.550 | 14.394 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Tanh / unresolved | 21830 | 0 / 21830 | 3.454 | 3.526 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 5487 | 0 / 5487 | 12.529 | 12.482 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Muls / unresolved | 21830 | 0 / 21830 | 3.051 | 3.192 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 13747 | 0 / 13747 | 3.988 | 3.957 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 5546 | 0 / 5546 | 9.819 | 9.829 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Sigmoid / unresolved | 16402 | 0 / 16402 | 3.218 | 3.049 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 10974 | 0 / 10974 | 4.632 | 4.626 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MlaPrologV3 / unresolved | 1416 | 0 / 1416 | 32.549 | 32.517 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 5487 | 0 / 5487 | 8.241 | 8.187 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| RecurrentKda / unresolved | 4071 | 0 / 4071 | 10.653 | 10.695 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 5428 | 5428 / 0 | 7.319 | 7.250 | 1.857 | -5.462 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 1416 | 0 / 1416 | 24.374 | 24.341 | 4.730 | -19.644 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| ForeachAddList / unresolved | 5428 | 0 / 5428 | 4.784 | 4.772 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 4071 | 0 / 4071 | 5.231 | 5.220 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / latent_norm | 5428 | 5428 / 0 | 3.862 | 3.814 | 1.312 | -2.550 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / unresolved | 5428 | 0 / 5428 | 3.076 | 3.061 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 5487 | 0 / 5487 | 2.613 | 2.687 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 4071 | 0 / 4071 | 2.903 | 2.891 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1416 | 0 / 1416 | 5.368 | 5.330 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / gate_up | 59 | 59 / 0 | 44.882 | 44.855 | 44.631 | -0.250 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / down | 59 | 59 / 0 | 23.900 | 23.867 | 17.109 | -6.791 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 59 | 0 / 59 | 4.695 | 4.626 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 118 | 0 / 118 | 1.567 | 1.444 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 59 | 0 / 59 | 2.539 | 2.561 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 5428 | 16.052 / 16.026 | 12.441 | 1.477 | 1.145 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 5428 | 21.957 / 21.948 | 29.389 | 2.020 | 2.704 | capacity_vs_valid_rows_conditional |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 / GroupedMatmul / expert_down | 5428 | 0 | 5428 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 / GroupedMatmul / expert_up | 5428 | 0 | 5428 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 5428 | 0 | 0 | 5428 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 5428 | 0 | 0 | 5428 | 0 |
