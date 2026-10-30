# Complete Decode Body Operator Families

Only complete events inside the 618 accepted target-body windows from 12 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c16_p16k / source-complete30dcea1e | 10 / 10 | 1 / 1 | 11 / 11 | 31537 / 253894 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / source-complete30dcea1e | 10 / 10 | 1 / 1 | 11 / 11 | 32879 / 264698 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source-complete30dcea1e | 6 / 6 | 0 / 0 | 6 / 6 | 21830 / 303732 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / source-complete30dcea1e | 6 / 6 | 0 / 0 | 6 / 6 | 21830 / 303732 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / source-complete30dcea1e | 6 / 6 | 0 / 0 | 6 / 6 | 19980 / 301860 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p4k / source-complete30dcea1e | 6 / 6 | 0 / 0 | 6 / 6 | 20350 / 307450 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source-complete30dcea1e | 10 / 10 | 1 / 1 | 11 / 11 | 27511 / 221523 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / source-complete30dcea1e | 10 / 10 | 1 / 1 | 11 / 11 | 30866 / 248538 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / source-complete30dcea1e | 6 / 6 | 0 / 0 | 6 / 6 | 19240 / 290680 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / source-complete30dcea1e | 6 / 6 | 0 / 0 | 6 / 6 | 19610 / 296270 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source-complete30dcea1e | 11 / 11 | 0 / 0 | 11 / 11 | 34221 / 275502 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / source-complete30dcea1e | 11 / 11 | 0 / 0 | 11 / 11 | 34892 / 280904 | 0 |

## a5_kimi_tp8_e16_bf16_c16_p16k / source-complete30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4324 | 0 / 4324 | 44.038 | 44.390 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| FusedInferAttentionScore / unresolved | 1128 | 0 / 1128 | 142.095 | 142.018 | 78.256 | -63.839 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4324 | 0 / 4324 | 33.413 | 33.421 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 6486 | 0 / 6486 | 20.494 | 20.349 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
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
| MatMulV3 / router | 4324 | 4324 / 0 | 7.482 | 7.412 | 1.967 | -5.516 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / unresolved | 3243 | 0 / 3243 | 8.341 | 8.304 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 4324 | 0 / 4324 | 5.519 | 5.517 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / output_gate + q_a | 1128 | 1128 / 0 | 19.145 | 18.951 | 15.778 | -3.368 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / latent_norm | 4324 | 4324 / 0 | 4.216 | 4.187 | 1.312 | -2.904 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / output | 1128 | 1128 / 0 | 12.713 | 12.664 | 6.601 | -6.112 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4324 | 21.305 / 21.374 | 12.656 | 1.960 | 1.164 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4324 | 44.038 / 44.390 | 29.886 | 4.052 | 2.750 | capacity_vs_valid_rows_conditional |

## a5_kimi_tp8_e16_bf16_c16_p4k / source-complete30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4508 | 0 / 4508 | 43.967 | 44.307 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4508 | 0 / 4508 | 33.414 | 33.418 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 6762 | 0 / 6762 | 20.491 | 20.202 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4508 | 4508 / 0 | 25.319 | 25.415 | 14.206 | -11.113 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 9163 | 0 / 9163 | 11.191 | 10.965 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 27244 | 0 / 27244 | 3.613 | 3.680 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4508 | 4508 / 0 | 21.792 | 21.791 | 14.180 | -7.613 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GroupedMatmul / expert_down | 4508 | 0 / 4508 | 21.325 | 21.385 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| Mul / unresolved | 37436 | 0 / 37436 | 2.551 | 2.072 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared.gate_up | 4508 | 4508 / 0 | 20.727 | 20.756 | 15.778 | -4.949 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 31850 | 0 / 31850 | 2.500 | 2.299 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Tanh / unresolved | 18130 | 0 / 18130 | 4.010 | 4.167 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 3381 | 0 / 3381 | 20.482 | 20.479 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 4557 | 0 / 4557 | 15.124 | 14.947 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Muls / unresolved | 18130 | 0 / 18130 | 3.779 | 3.864 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 4557 | 0 / 4557 | 14.920 | 14.869 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 4508 | 0 / 4508 | 14.726 | 14.598 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 1176 | 0 / 1176 | 47.673 | 47.628 | 21.631 | -26.042 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| hcom_allGather_ / attention_output_communication | 4557 | 0 / 4557 | 10.797 | 10.410 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allGather_ / ffn_down_communication | 4606 | 0 / 4606 | 10.284 | 10.281 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Sigmoid / unresolved | 13622 | 0 / 13622 | 3.279 | 3.475 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 3381 | 3381 / 0 | 12.313 | 12.263 | 6.601 | -5.713 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MlaPrologV3 / unresolved | 1176 | 0 / 1176 | 34.540 | 34.478 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared.down | 4508 | 4508 / 0 | 8.603 | 8.589 | 3.436 | -5.167 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / router | 4508 | 4508 / 0 | 7.477 | 7.404 | 1.967 | -5.510 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / unresolved | 3381 | 0 / 3381 | 8.332 | 8.289 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 4508 | 0 / 4508 | 5.519 | 5.516 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / output_gate + q_a | 1176 | 1176 / 0 | 19.147 | 18.956 | 15.778 | -3.369 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / latent_norm | 4508 | 4508 / 0 | 4.209 | 4.181 | 1.312 | -2.897 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / output | 1176 | 1176 / 0 | 12.723 | 12.662 | 6.601 | -6.122 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / unresolved | 4508 | 0 / 4508 | 3.300 | 3.297 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AsStrided / unresolved | 3381 | 0 / 3381 | 4.331 | 4.301 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 4557 | 0 / 4557 | 3.031 | 3.006 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 3381 | 0 / 3381 | 3.461 | 3.455 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 2352 | 0 / 2352 | 4.288 | 4.298 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1176 | 0 / 1176 | 5.420 | 5.396 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / gate_up | 49 | 49 / 0 | 53.114 | 53.023 | 47.325 | -5.789 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / down | 49 | 49 / 0 | 25.535 | 25.516 | 17.679 | -7.857 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 49 | 0 / 49 | 5.317 | 5.332 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 98 | 0 / 98 | 1.669 | 1.762 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 49 | 0 / 49 | 2.427 | 2.397 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4508 | 21.325 / 21.385 | 12.656 | 1.962 | 1.164 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4508 | 43.967 / 44.307 | 29.886 | 4.045 | 2.750 | capacity_vs_valid_rows_conditional |

## a5_kimi_tp8_e16_bf16_c1_p16k / source-complete30dcea1e

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
| FusedInferAttentionScore / unresolved | 1416 | 0 / 1416 | 24.374 | 24.341 | 8.484 | -15.890 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## a5_kimi_tp8_e16_bf16_c1_p4k / source-complete30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MatMulV3 / unresolved | 25901 | 0 / 25901 | 15.019 | 12.016 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 5428 | 0 / 5428 | 31.335 | 31.323 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 5428 | 5428 / 0 | 23.858 | 23.819 | 14.093 | -9.765 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 11033 | 0 / 11033 | 10.974 | 10.821 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 5428 | 0 / 5428 | 21.918 | 21.895 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MatMulV3 / latent_up | 5428 | 5428 / 0 | 20.571 | 20.570 | 14.118 | -6.452 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 45076 | 0 / 45076 | 2.370 | 1.955 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 5428 | 0 / 5428 | 16.045 | 16.026 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| Cast / unresolved | 38350 | 0 / 38350 | 2.168 | 1.961 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 5487 | 0 / 5487 | 14.656 | 14.535 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 5428 | 0 / 5428 | 14.544 | 14.416 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Tanh / unresolved | 21830 | 0 / 21830 | 3.452 | 3.520 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 5487 | 0 / 5487 | 12.525 | 12.474 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Muls / unresolved | 21830 | 0 / 21830 | 3.051 | 3.189 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 13747 | 0 / 13747 | 3.954 | 3.951 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 5546 | 0 / 5546 | 9.784 | 9.773 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Sigmoid / unresolved | 16402 | 0 / 16402 | 3.223 | 3.075 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 10974 | 0 / 10974 | 4.626 | 4.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 5487 | 0 / 5487 | 8.430 | 8.186 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MlaPrologV3 / unresolved | 1416 | 0 / 1416 | 32.518 | 32.474 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 4071 | 0 / 4071 | 10.701 | 10.738 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 5428 | 5428 / 0 | 7.341 | 7.269 | 1.857 | -5.484 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 5428 | 0 / 5428 | 4.780 | 4.772 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 1416 | 0 / 1416 | 16.075 | 16.056 | 4.866 | -11.209 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| CausalConv1d / unresolved | 4071 | 0 / 4071 | 5.221 | 5.206 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / latent_norm | 5428 | 5428 / 0 | 3.902 | 3.842 | 1.312 | -2.590 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / unresolved | 5428 | 0 / 5428 | 3.075 | 3.058 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 5487 | 0 / 5487 | 2.615 | 2.689 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 4071 | 0 / 4071 | 2.899 | 2.885 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1416 | 0 / 1416 | 5.328 | 5.290 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / gate_up | 59 | 59 / 0 | 45.165 | 45.141 | 44.631 | -0.534 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / down | 59 | 59 / 0 | 23.163 | 23.150 | 17.109 | -6.054 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 59 | 0 / 59 | 4.549 | 4.562 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 118 | 0 / 118 | 1.585 | 1.427 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 59 | 0 / 59 | 2.497 | 2.497 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 5428 | 16.045 / 16.026 | 12.441 | 1.476 | 1.145 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 5428 | 21.918 / 21.895 | 29.389 | 2.016 | 2.704 | capacity_vs_valid_rows_conditional |

## a5_kimi_tp8_e16_bf16_c2_p16k / source-complete30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MatMulV3 / unresolved | 23706 | 0 / 23706 | 15.125 | 12.103 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 4968 | 0 / 4968 | 34.585 | 34.645 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4968 | 0 / 4968 | 31.565 | 31.543 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4968 | 4968 / 0 | 23.893 | 23.864 | 14.093 | -9.800 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 10098 | 0 / 10098 | 10.995 | 10.826 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 4968 | 0 / 4968 | 22.335 | 22.320 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MatMulV3 / latent_up | 4968 | 4968 / 0 | 20.767 | 20.778 | 14.118 | -6.648 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 41256 | 0 / 41256 | 2.463 | 2.055 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 30024 | 0 / 30024 | 3.264 | 3.021 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 4968 | 0 / 4968 | 16.222 | 16.216 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| Cast / unresolved | 35208 | 0 / 35208 | 2.132 | 2.083 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 5022 | 0 / 5022 | 14.100 | 14.132 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 5022 | 0 / 5022 | 13.948 | 13.741 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Tanh / unresolved | 19980 | 0 / 19980 | 3.439 | 3.668 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 19980 | 0 / 19980 | 3.271 | 3.483 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 5076 | 0 / 5076 | 9.980 | 9.975 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| PadV3 / unresolved | 12582 | 0 / 12582 | 4.011 | 3.932 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 5022 | 0 / 5022 | 9.799 | 9.528 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MlaPrologV3 / unresolved | 1296 | 0 / 1296 | 32.727 | 32.670 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 1296 | 0 / 1296 | 32.503 | 32.450 | 14.108 | -18.394 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| Sigmoid / unresolved | 15012 | 0 / 15012 | 2.760 | 2.727 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 3726 | 0 / 3726 | 10.990 | 11.044 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 4968 | 4968 / 0 | 7.447 | 7.378 | 1.857 | -5.590 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 4968 | 0 / 4968 | 4.975 | 4.971 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 3726 | 0 / 3726 | 5.810 | 5.791 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / latent_norm | 4968 | 4968 / 0 | 3.851 | 3.812 | 1.312 | -2.539 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AsStrided / unresolved | 3726 | 0 / 3726 | 4.011 | 3.978 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 4968 | 0 / 4968 | 2.957 | 3.018 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 5022 | 0 / 5022 | 2.791 | 2.789 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 3726 | 0 / 3726 | 3.430 | 3.419 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1296 | 0 / 1296 | 5.426 | 5.403 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / gate_up | 54 | 54 / 0 | 46.925 | 46.852 | 44.631 | -2.294 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / down | 54 | 54 / 0 | 23.406 | 23.385 | 17.109 | -6.297 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 54 | 0 / 54 | 4.472 | 4.449 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 108 | 0 / 108 | 1.633 | 1.643 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 108 | 0 / 108 | 1.584 | 1.472 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4968 | 16.222 / 16.216 | 12.441 | 1.492 | 1.145 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4968 | 22.335 / 22.320 | 29.389 | 2.055 | 2.704 | capacity_vs_valid_rows_conditional |

## a5_kimi_tp8_e16_bf16_c2_p4k / source-complete30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MatMulV3 / unresolved | 24145 | 0 / 24145 | 15.113 | 12.076 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 5060 | 0 / 5060 | 34.497 | 34.534 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 5060 | 0 / 5060 | 31.532 | 31.513 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 5060 | 5060 / 0 | 23.910 | 23.873 | 14.093 | -9.818 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GroupedMatmul / expert_up | 5060 | 0 / 5060 | 22.426 | 22.406 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| AttnResFwd / unresolved | 10285 | 0 / 10285 | 10.998 | 10.814 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 5060 | 5060 / 0 | 20.757 | 20.748 | 14.118 | -6.639 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 42020 | 0 / 42020 | 2.449 | 2.051 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 30580 | 0 / 30580 | 3.261 | 3.023 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 5060 | 0 / 5060 | 16.222 | 16.211 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| Cast / unresolved | 35860 | 0 / 35860 | 2.132 | 2.079 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 5115 | 0 / 5115 | 14.081 | 14.126 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 5115 | 0 / 5115 | 13.827 | 13.627 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Tanh / unresolved | 20350 | 0 / 20350 | 3.436 | 3.656 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 20350 | 0 / 20350 | 3.300 | 3.487 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 5170 | 0 / 5170 | 10.015 | 10.011 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| PadV3 / unresolved | 12815 | 0 / 12815 | 4.000 | 3.934 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 5115 | 0 / 5115 | 9.955 | 9.551 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MlaPrologV3 / unresolved | 1320 | 0 / 1320 | 32.739 | 32.682 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 3795 | 0 / 3795 | 11.241 | 11.293 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 15290 | 0 / 15290 | 2.763 | 2.736 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 5060 | 5060 / 0 | 7.486 | 7.408 | 1.857 | -5.629 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 5060 | 0 / 5060 | 4.975 | 4.973 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 1320 | 0 / 1320 | 18.074 | 18.054 | 5.961 | -12.113 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| CausalConv1d / unresolved | 3795 | 0 / 3795 | 5.814 | 5.786 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / latent_norm | 5060 | 5060 / 0 | 3.851 | 3.812 | 1.312 | -2.539 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AsStrided / unresolved | 3795 | 0 / 3795 | 4.018 | 3.985 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 5060 | 0 / 5060 | 2.958 | 3.018 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 5115 | 0 / 5115 | 2.788 | 2.786 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 3795 | 0 / 3795 | 3.430 | 3.417 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1320 | 0 / 1320 | 5.392 | 5.362 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / gate_up | 55 | 55 / 0 | 46.726 | 46.682 | 44.631 | -2.095 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / down | 55 | 55 / 0 | 23.565 | 23.596 | 17.109 | -6.456 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 55 | 0 / 55 | 4.564 | 4.550 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 110 | 0 / 110 | 1.628 | 1.419 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 110 | 0 / 110 | 1.528 | 1.577 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 5060 | 16.222 / 16.211 | 12.441 | 1.492 | 1.145 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 5060 | 22.426 / 22.406 | 29.389 | 2.063 | 2.704 | capacity_vs_valid_rows_conditional |

## a5_kimi_tp8_e16_bf16_c32_p16k / source-complete30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| FusedInferAttentionScore / unresolved | 984 | 0 / 984 | 264.091 | 263.991 | 153.265 | -110.826 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## a5_kimi_tp8_e16_bf16_c32_p4k / source-complete30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4232 | 0 / 4232 | 46.237 | 47.053 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4232 | 0 / 4232 | 34.197 | 34.183 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 6348 | 0 / 6348 | 21.497 | 21.616 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4232 | 4232 / 0 | 26.875 | 27.136 | 14.433 | -12.442 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 8602 | 0 / 8602 | 11.403 | 11.165 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 3174 | 0 / 3174 | 30.461 | 30.449 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4232 | 4232 / 0 | 22.651 | 22.648 | 14.303 | -8.348 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 25576 | 0 / 25576 | 3.693 | 3.681 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared.gate_up | 4232 | 4232 / 0 | 22.209 | 22.333 | 17.576 | -4.633 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GroupedMatmul / expert_down | 4232 | 0 / 4232 | 22.016 | 22.110 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| Mul / unresolved | 35144 | 0 / 35144 | 2.520 | 2.179 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 29900 | 0 / 29900 | 2.769 | 2.689 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 1104 | 0 / 1104 | 74.792 | 74.778 | 40.016 | -34.776 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| Tanh / unresolved | 17020 | 0 / 17020 | 4.225 | 4.390 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 4278 | 0 / 4278 | 16.550 | 16.268 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 4278 | 0 / 4278 | 15.802 | 15.549 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Muls / unresolved | 17020 | 0 / 17020 | 3.926 | 3.931 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 4232 | 0 / 4232 | 14.584 | 14.442 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 4324 | 0 / 4324 | 10.715 | 10.698 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allGather_ / attention_output_communication | 4278 | 0 / 4278 | 10.760 | 10.707 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MlaPrologV3 / unresolved | 1104 | 0 / 1104 | 41.661 | 41.627 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 12788 | 0 / 12788 | 3.479 | 3.828 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 3174 | 3174 / 0 | 13.776 | 13.711 | 7.089 | -6.688 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / shared.down | 4232 | 4232 / 0 | 9.540 | 9.516 | 3.737 | -5.802 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / unresolved | 3174 | 0 / 3174 | 10.930 | 10.894 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 4232 | 4232 / 0 | 7.583 | 7.505 | 2.186 | -5.397 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 4232 | 0 / 4232 | 5.807 | 5.803 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / output_gate + q_a | 1104 | 1104 / 0 | 19.252 | 19.148 | 17.576 | -1.676 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / latent_norm | 4232 | 4232 / 0 | 4.285 | 4.264 | 1.312 | -2.973 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / output | 1104 | 1104 / 0 | 14.073 | 14.063 | 7.089 | -6.984 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AsStrided / unresolved | 3174 | 0 / 3174 | 4.869 | 4.842 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 4232 | 0 / 4232 | 3.512 | 3.505 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 4278 | 0 / 4278 | 3.264 | 3.236 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 3174 | 0 / 3174 | 3.579 | 3.570 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 2208 | 0 / 2208 | 4.528 | 4.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1104 | 0 / 1104 | 5.589 | 5.546 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / gate_up | 46 | 46 / 0 | 59.094 | 59.051 | 52.713 | -6.381 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / down | 46 | 46 / 0 | 27.431 | 27.393 | 18.818 | -8.613 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 46 | 0 / 46 | 5.696 | 5.667 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 46 | 0 / 46 | 3.987 | 4.003 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 92 | 0 / 92 | 1.702 | 1.575 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 46 | 0 / 46 | 2.461 | 2.433 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4232 | 22.016 / 22.110 | 13.086 | 2.025 | 1.204 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4232 | 46.237 / 47.053 | 30.880 | 4.254 | 2.841 | capacity_vs_valid_rows_conditional |

## a5_kimi_tp8_e16_bf16_c4_p16k / source-complete30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MatMulV3 / unresolved | 22828 | 0 / 22828 | 15.360 | 12.095 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 4784 | 0 / 4784 | 41.471 | 41.486 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4784 | 0 / 4784 | 31.864 | 31.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4784 | 4784 / 0 | 24.241 | 24.248 | 14.093 | -10.149 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 9724 | 0 / 9724 | 11.008 | 10.821 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4784 | 4784 / 0 | 20.956 | 20.941 | 14.118 | -6.838 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 28912 | 0 / 28912 | 3.357 | 3.459 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 4784 | 0 / 4784 | 20.097 | 20.084 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| Mul / unresolved | 39728 | 0 / 39728 | 2.190 | 1.801 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 33904 | 0 / 33904 | 2.150 | 2.090 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 4836 | 0 / 4836 | 14.188 | 13.979 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 4784 | 0 / 4784 | 14.338 | 14.266 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Tanh / unresolved | 19240 | 0 / 19240 | 3.542 | 3.609 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 4836 | 0 / 4836 | 13.732 | 13.675 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Muls / unresolved | 19240 | 0 / 19240 | 3.360 | 3.387 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 1248 | 0 / 1248 | 48.025 | 48.032 | 23.505 | -24.520 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| PadV3 / unresolved | 12116 | 0 / 12116 | 4.092 | 4.004 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 4888 | 0 / 4888 | 9.802 | 9.804 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allGather_ / attention_output_communication | 4836 | 0 / 4836 | 9.874 | 9.626 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Sigmoid / unresolved | 14456 | 0 / 14456 | 2.954 | 3.165 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 3588 | 0 / 3588 | 11.858 | 11.851 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MlaPrologV3 / unresolved | 1248 | 0 / 1248 | 32.878 | 32.827 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 4784 | 4784 / 0 | 7.664 | 7.591 | 1.857 | -5.807 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 4784 | 0 / 4784 | 5.314 | 5.313 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 3588 | 0 / 3588 | 6.929 | 6.904 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / latent_norm | 4784 | 4784 / 0 | 3.790 | 3.784 | 1.312 | -2.478 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / unresolved | 4784 | 0 / 4784 | 3.053 | 3.074 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AsStrided / unresolved | 3588 | 0 / 3588 | 4.020 | 3.991 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 4836 | 0 / 4836 | 2.854 | 2.852 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 3588 | 0 / 3588 | 3.437 | 3.415 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1248 | 0 / 1248 | 5.338 | 5.290 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / gate_up | 52 | 52 / 0 | 47.970 | 47.907 | 44.631 | -3.339 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / down | 52 | 52 / 0 | 24.444 | 24.375 | 17.109 | -7.335 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 52 | 0 / 52 | 4.797 | 4.787 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 104 | 0 / 104 | 1.638 | 1.573 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 104 | 0 / 104 | 1.592 | 1.597 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4784 | 20.097 / 20.084 | 12.441 | 1.849 | 1.145 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4784 | 41.471 / 41.486 | 29.389 | 3.815 | 2.704 | capacity_vs_valid_rows_conditional |

## a5_kimi_tp8_e16_bf16_c4_p4k / source-complete30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MatMulV3 / unresolved | 23267 | 0 / 23267 | 15.364 | 12.048 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 4876 | 0 / 4876 | 41.239 | 41.265 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4876 | 0 / 4876 | 31.842 | 31.813 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4876 | 4876 / 0 | 24.291 | 24.304 | 14.093 | -10.198 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 9911 | 0 / 9911 | 11.009 | 10.828 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4876 | 4876 / 0 | 20.950 | 20.938 | 14.118 | -6.831 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 29468 | 0 / 29468 | 3.358 | 3.459 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 4876 | 0 / 4876 | 20.066 | 20.058 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| Mul / unresolved | 40492 | 0 / 40492 | 2.163 | 1.800 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 34556 | 0 / 34556 | 2.154 | 2.096 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 4876 | 0 / 4876 | 14.448 | 14.367 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Tanh / unresolved | 19610 | 0 / 19610 | 3.539 | 3.606 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 4929 | 0 / 4929 | 14.056 | 13.917 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 4929 | 0 / 4929 | 13.714 | 13.609 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Muls / unresolved | 19610 | 0 / 19610 | 3.360 | 3.390 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 12349 | 0 / 12349 | 4.086 | 4.005 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 4982 | 0 / 4982 | 9.878 | 9.878 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allGather_ / attention_output_communication | 4929 | 0 / 4929 | 9.818 | 9.596 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| RecurrentKda / unresolved | 3657 | 0 / 3657 | 11.919 | 11.906 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 14734 | 0 / 14734 | 2.955 | 3.165 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MlaPrologV3 / unresolved | 1272 | 0 / 1272 | 32.878 | 32.850 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 4876 | 4876 / 0 | 7.680 | 7.614 | 1.857 | -5.823 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 1272 | 0 / 1272 | 23.007 | 22.967 | 9.587 | -13.420 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| ForeachAddList / unresolved | 4876 | 0 / 4876 | 5.308 | 5.304 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 3657 | 0 / 3657 | 6.919 | 6.887 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / latent_norm | 4876 | 4876 / 0 | 3.790 | 3.781 | 1.312 | -2.478 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / unresolved | 4876 | 0 / 4876 | 3.050 | 3.072 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AsStrided / unresolved | 3657 | 0 / 3657 | 4.018 | 3.991 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 4929 | 0 / 4929 | 2.856 | 2.849 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 3657 | 0 / 3657 | 3.436 | 3.416 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1272 | 0 / 1272 | 5.339 | 5.300 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / gate_up | 53 | 53 / 0 | 48.255 | 48.225 | 44.631 | -3.624 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / down | 53 | 53 / 0 | 23.717 | 23.703 | 17.109 | -6.608 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 53 | 0 / 53 | 4.732 | 4.724 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 106 | 0 / 106 | 1.618 | 1.595 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 106 | 0 / 106 | 1.598 | 1.569 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4876 | 20.066 / 20.058 | 12.441 | 1.846 | 1.145 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4876 | 41.239 / 41.265 | 29.389 | 3.794 | 2.704 | capacity_vs_valid_rows_conditional |

## a5_kimi_tp8_e16_bf16_c8_p16k / source-complete30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4692 | 0 / 4692 | 42.682 | 42.857 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4692 | 0 / 4692 | 32.982 | 32.979 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 7038 | 0 / 7038 | 19.580 | 19.294 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4692 | 4692 / 0 | 24.431 | 24.471 | 14.093 | -10.338 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 9537 | 0 / 9537 | 10.997 | 10.763 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 28356 | 0 / 28356 | 3.512 | 3.586 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4692 | 4692 / 0 | 21.032 | 21.030 | 14.118 | -6.913 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 1224 | 0 / 1224 | 79.395 | 79.282 | 41.363 | -38.032 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## a5_kimi_tp8_e16_bf16_c8_p4k / source-complete30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4784 | 0 / 4784 | 42.630 | 42.813 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4784 | 0 / 4784 | 32.913 | 32.904 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 7176 | 0 / 7176 | 19.583 | 19.416 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4784 | 4784 / 0 | 24.439 | 24.471 | 14.093 | -10.346 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 9724 | 0 / 9724 | 10.977 | 10.745 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 28912 | 0 / 28912 | 3.509 | 3.583 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4784 | 4784 / 0 | 21.042 | 21.027 | 14.118 | -6.924 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GroupedMatmul / expert_down | 4784 | 0 / 4784 | 20.594 | 20.584 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MatMulV3 / shared.gate_up | 4784 | 4784 / 0 | 20.054 | 20.070 | 14.878 | -5.175 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 39728 | 0 / 39728 | 2.265 | 1.875 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 33800 | 0 / 33800 | 2.197 | 2.165 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 4836 | 0 / 4836 | 14.510 | 14.420 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 4784 | 0 / 4784 | 14.508 | 14.450 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 4836 | 0 / 4836 | 14.243 | 14.193 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| Tanh / unresolved | 19240 | 0 / 19240 | 3.549 | 3.626 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 19240 | 0 / 19240 | 3.408 | 3.405 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 3588 | 0 / 3588 | 15.498 | 15.467 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 4836 | 0 / 4836 | 10.682 | 10.346 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allGather_ / ffn_down_communication | 4888 | 0 / 4888 | 9.988 | 9.978 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MatMulV3 / linear_output | 3588 | 3588 / 0 | 11.969 | 11.896 | 6.357 | -5.612 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 14456 | 0 / 14456 | 2.960 | 3.180 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MlaPrologV3 / unresolved | 1248 | 0 / 1248 | 33.437 | 33.377 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared.down | 4784 | 4784 / 0 | 8.341 | 8.322 | 3.285 | -5.056 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 1248 | 0 / 1248 | 31.708 | 31.686 | 13.051 | -18.657 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MatMulV3 / router | 4784 | 4784 / 0 | 7.792 | 7.718 | 1.857 | -5.935 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 4784 | 0 / 4784 | 5.306 | 5.303 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 3588 | 0 / 3588 | 7.043 | 7.032 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / output_gate + q_a | 1248 | 1248 / 0 | 18.715 | 18.535 | 14.878 | -3.837 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / latent_norm | 4784 | 4784 / 0 | 4.016 | 4.037 | 1.312 | -2.704 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / output | 1248 | 1248 / 0 | 12.073 | 12.058 | 6.357 | -5.716 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AsStrided / unresolved | 3588 | 0 / 3588 | 4.069 | 4.049 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 4784 | 0 / 4784 | 2.996 | 3.027 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 4836 | 0 / 4836 | 2.937 | 2.934 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 3588 | 0 / 3588 | 3.434 | 3.420 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 2496 | 0 / 2496 | 3.633 | 3.607 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1248 | 0 / 1248 | 5.407 | 5.381 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / gate_up | 52 | 52 / 0 | 49.715 | 49.689 | 44.631 | -5.084 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / down | 52 | 52 / 0 | 24.347 | 24.299 | 17.109 | -7.238 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 52 | 0 / 52 | 4.963 | 4.910 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 104 | 0 / 104 | 1.655 | 1.587 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 52 | 0 / 52 | 2.410 | 2.389 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4784 | 20.594 / 20.584 | 12.441 | 1.895 | 1.145 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92 | 4784 | 42.630 / 42.813 | 29.389 | 3.922 | 2.704 | capacity_vs_valid_rows_conditional |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c16_p16k / source-complete30dcea1e / GroupedMatmul / expert_down | 4324 | 0 | 4324 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p16k / source-complete30dcea1e / GroupedMatmul / expert_up | 4324 | 0 | 4324 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p16k / source-complete30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 4324 | 0 | 0 | 4324 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p16k / source-complete30dcea1e / MoeDistributeDispatchV3 / expert_dispatch_native | 4324 | 0 | 0 | 4324 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / source-complete30dcea1e / GroupedMatmul / expert_down | 4508 | 0 | 4508 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / source-complete30dcea1e / GroupedMatmul / expert_up | 4508 | 0 | 4508 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / source-complete30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 4508 | 0 | 0 | 4508 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / source-complete30dcea1e / MoeDistributeDispatchV3 / expert_dispatch_native | 4508 | 0 | 0 | 4508 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source-complete30dcea1e / GroupedMatmul / expert_down | 5428 | 0 | 5428 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source-complete30dcea1e / GroupedMatmul / expert_up | 5428 | 0 | 5428 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source-complete30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 5428 | 0 | 0 | 5428 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source-complete30dcea1e / MoeDistributeDispatchV3 / expert_dispatch_native | 5428 | 0 | 0 | 5428 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / source-complete30dcea1e / GroupedMatmul / expert_down | 5428 | 0 | 5428 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / source-complete30dcea1e / GroupedMatmul / expert_up | 5428 | 0 | 5428 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / source-complete30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 5428 | 0 | 0 | 5428 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / source-complete30dcea1e / MoeDistributeDispatchV3 / expert_dispatch_native | 5428 | 0 | 0 | 5428 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / source-complete30dcea1e / GroupedMatmul / expert_down | 4968 | 0 | 4968 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / source-complete30dcea1e / GroupedMatmul / expert_up | 4968 | 0 | 4968 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / source-complete30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 4968 | 0 | 0 | 4968 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / source-complete30dcea1e / MoeDistributeDispatchV3 / expert_dispatch_native | 4968 | 0 | 0 | 4968 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p4k / source-complete30dcea1e / GroupedMatmul / expert_down | 5060 | 0 | 5060 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p4k / source-complete30dcea1e / GroupedMatmul / expert_up | 5060 | 0 | 5060 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p4k / source-complete30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 5060 | 0 | 0 | 5060 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p4k / source-complete30dcea1e / MoeDistributeDispatchV3 / expert_dispatch_native | 5060 | 0 | 0 | 5060 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source-complete30dcea1e / GroupedMatmul / expert_down | 3772 | 0 | 3772 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source-complete30dcea1e / GroupedMatmul / expert_up | 3772 | 0 | 3772 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source-complete30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 3772 | 0 | 0 | 3772 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source-complete30dcea1e / MoeDistributeDispatchV3 / expert_dispatch_native | 3772 | 0 | 0 | 3772 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / source-complete30dcea1e / GroupedMatmul / expert_down | 4232 | 0 | 4232 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / source-complete30dcea1e / GroupedMatmul / expert_up | 4232 | 0 | 4232 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / source-complete30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 4232 | 0 | 0 | 4232 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / source-complete30dcea1e / MoeDistributeDispatchV3 / expert_dispatch_native | 4232 | 0 | 0 | 4232 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / source-complete30dcea1e / GroupedMatmul / expert_down | 4784 | 0 | 4784 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / source-complete30dcea1e / GroupedMatmul / expert_up | 4784 | 0 | 4784 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / source-complete30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 4784 | 0 | 0 | 4784 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / source-complete30dcea1e / MoeDistributeDispatchV3 / expert_dispatch_native | 4784 | 0 | 0 | 4784 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / source-complete30dcea1e / GroupedMatmul / expert_down | 4876 | 0 | 4876 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / source-complete30dcea1e / GroupedMatmul / expert_up | 4876 | 0 | 4876 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / source-complete30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 4876 | 0 | 0 | 4876 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / source-complete30dcea1e / MoeDistributeDispatchV3 / expert_dispatch_native | 4876 | 0 | 0 | 4876 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source-complete30dcea1e / GroupedMatmul / expert_down | 4692 | 0 | 4692 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source-complete30dcea1e / GroupedMatmul / expert_up | 4692 | 0 | 4692 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source-complete30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 4692 | 0 | 0 | 4692 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source-complete30dcea1e / MoeDistributeDispatchV3 / expert_dispatch_native | 4692 | 0 | 0 | 4692 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / source-complete30dcea1e / GroupedMatmul / expert_down | 4784 | 0 | 4784 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / source-complete30dcea1e / GroupedMatmul / expert_up | 4784 | 0 | 4784 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / source-complete30dcea1e / MoeDistributeCombineV3 / expert_combine_native | 4784 | 0 | 0 | 4784 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / source-complete30dcea1e / MoeDistributeDispatchV3 / expert_dispatch_native | 4784 | 0 | 0 | 4784 | 0 |
