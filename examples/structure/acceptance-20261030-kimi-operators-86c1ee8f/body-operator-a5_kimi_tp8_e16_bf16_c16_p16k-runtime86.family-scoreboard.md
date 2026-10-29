# Complete Decode Body Operator Families

Only complete events inside the 47 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c16_p16k / runtime86 | 8 / 8 | 1 / 1 | 9 / 9 | 26085 / 253894 | 0 |

## a5_kimi_tp8_e16_bf16_c16_p16k / runtime86

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4324 | 0 / 4324 | 44.038 | 44.390 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MatMulV3 / unresolved | 11938 | 0 / 11938 | 15.046 | 7.549 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 1128 | 0 / 1128 | 142.095 | 142.018 | 4.730 | -137.365 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4324 | 0 / 4324 | 33.413 | 33.421 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4324 | 4324 / 0 | 25.351 | 25.449 | 14.206 | -11.145 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 8789 | 0 / 8789 | 11.179 | 10.967 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 26132 | 0 / 26132 | 3.611 | 3.669 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4324 | 4324 / 0 | 21.790 | 21.785 | 14.180 | -7.610 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GroupedMatmul / expert_down | 4324 | 0 / 4324 | 21.305 | 21.374 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| Mul / unresolved | 35908 | 0 / 35908 | 2.550 | 2.068 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared.gate_up | 4324 | 4324 / 0 | 20.707 | 20.727 | 15.778 | -4.929 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 30550 | 0 / 30550 | 2.500 | 2.300 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Tanh / unresolved | 17390 | 0 / 17390 | 4.016 | 4.173 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 4371 | 0 / 4371 | 15.326 | 15.003 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| RecurrentKda / unresolved | 3243 | 0 / 3243 | 20.565 | 20.553 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 17390 | 0 / 17390 | 3.778 | 3.857 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 4371 | 0 / 4371 | 14.909 | 14.890 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 4324 | 0 / 4324 | 14.691 | 14.569 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 4371 | 0 / 4371 | 10.454 | 10.413 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allGather_ / ffn_down_communication | 4418 | 0 / 4418 | 10.291 | 10.279 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Sigmoid / unresolved | 13066 | 0 / 13066 | 3.276 | 3.468 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 3243 | 3243 / 0 | 12.339 | 12.282 | 6.601 | -5.738 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MlaPrologV3 / unresolved | 1128 | 0 / 1128 | 34.559 | 34.513 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared.down | 4324 | 4324 / 0 | 8.622 | 8.616 | 3.436 | -5.186 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / unresolved | 3243 | 0 / 3243 | 8.341 | 8.304 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 4324 | 0 / 4324 | 5.519 | 5.517 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / q_a | 1128 | 1128 / 0 | 19.145 | 18.951 | 15.778 | -3.368 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / latent_norm | 4324 | 4324 / 0 | 4.216 | 4.187 | 1.312 | -2.904 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / unresolved | 4324 | 0 / 4324 | 3.300 | 3.300 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AsStrided / unresolved | 3243 | 0 / 3243 | 4.333 | 4.305 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 4371 | 0 / 4371 | 3.029 | 3.006 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 3243 | 0 / 3243 | 3.461 | 3.456 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 2256 | 0 / 2256 | 4.301 | 4.261 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1128 | 0 / 1128 | 5.418 | 5.376 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / gate_up | 47 | 47 / 0 | 53.443 | 53.409 | 47.325 | -6.118 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / down | 47 | 47 / 0 | 25.433 | 25.429 | 17.679 | -7.754 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 47 | 0 / 47 | 5.230 | 5.249 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 94 | 0 / 94 | 1.655 | 1.742 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 47 | 0 / 47 | 2.460 | 2.426 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4324 | 21.305 / 21.374 | 12.501 | 1.960 | 1.150 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4324 | 44.038 / 44.390 | 22.487 | 4.052 | 2.069 | capacity_vs_valid_rows_conditional |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c16_p16k / runtime86 / GroupedMatmul / expert_down | 4324 | 0 | 4324 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p16k / runtime86 / GroupedMatmul / expert_up | 4324 | 0 | 4324 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p16k / runtime86 / MoeDistributeCombineV3 / expert_combine_native | 4324 | 0 | 0 | 4324 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p16k / runtime86 / MoeDistributeDispatchV3 / expert_dispatch_native | 4324 | 0 | 0 | 4324 | 0 |
