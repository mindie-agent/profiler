# Complete Decode Body Operator Families

Only complete events inside the 1769 accepted target-body windows from 17 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c16_p16k / source18c423c7 | 10 / 10 | 1 / 1 | 11 / 11 | 31537 / 253894 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / source18c423c7 | 10 / 10 | 1 / 1 | 11 / 11 | 32879 / 264698 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 | 6 / 6 | 0 / 0 | 6 / 6 | 21830 / 303732 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / source18c423c7 | 6 / 6 | 0 / 0 | 6 / 6 | 21830 / 303732 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / source18c423c7 | 6 / 6 | 0 / 0 | 6 / 6 | 19980 / 301860 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p4k / source18c423c7 | 6 / 6 | 0 / 0 | 6 / 6 | 20350 / 307450 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 | 10 / 10 | 1 / 1 | 11 / 11 | 27511 / 221523 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / source18c423c7 | 10 / 10 | 1 / 1 | 11 / 11 | 30866 / 248538 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / source18c423c7 | 6 / 6 | 0 / 0 | 6 / 6 | 19240 / 290680 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / source18c423c7 | 6 / 6 | 0 / 0 | 6 / 6 | 19610 / 296270 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 | 11 / 11 | 0 / 0 | 11 / 11 | 34221 / 275502 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / source18c423c7 | 11 / 11 | 0 / 0 | 11 / 11 | 34892 / 280904 | 0 |
| a3_kimi4_tp8_w4a8_c1 / source18c423c7 | 8 / 8 | 0 / 1 | 8 / 9 | 5588 / 43180 | 0 |
| a3_kimi4_tp8_w4a8_c16 / source18c423c7 | 18 / 18 | 0 / 1 | 18 / 19 | 8695 / 39245 | 0 |
| a3_kimi4_tp8_w4a8_c32 / source18c423c7 | 18 / 18 | 0 / 1 | 18 / 19 | 8140 / 36960 | 0 |
| a3_kimi4_tp8_w4a8_c4 / source18c423c7 | 8 / 8 | 0 / 1 | 8 / 9 | 4674 / 44526 | 0 |
| a3_kimi4_tp8_w4a8_c64 / source18c423c7 | 17 / 17 | 1 / 2 | 18 / 19 | 7252 / 32928 | 0 |

## a5_kimi_tp8_e16_bf16_c16_p16k / source18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4324 | 0 / 4324 | 44.038 | 44.390 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| FusedInferAttentionScore / unresolved | 1128 | 0 / 1128 | 142.095 | 142.018 | 4.730 | -137.365 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## a5_kimi_tp8_e16_bf16_c16_p4k / source18c423c7

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
| FusedInferAttentionScore / unresolved | 1176 | 0 / 1176 | 47.673 | 47.628 | 1.578 | -46.095 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## a5_kimi_tp8_e16_bf16_c1_p4k / source18c423c7

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
| FusedInferAttentionScore / unresolved | 1416 | 0 / 1416 | 16.075 | 16.056 | 1.578 | -14.497 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## a5_kimi_tp8_e16_bf16_c2_p16k / source18c423c7

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
| FusedInferAttentionScore / unresolved | 1296 | 0 / 1296 | 32.503 | 32.450 | 4.730 | -27.773 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## a5_kimi_tp8_e16_bf16_c2_p4k / source18c423c7

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
| FusedInferAttentionScore / unresolved | 1320 | 0 / 1320 | 18.074 | 18.054 | 1.578 | -16.496 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## a5_kimi_tp8_e16_bf16_c32_p4k / source18c423c7

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
| FusedInferAttentionScore / unresolved | 1104 | 0 / 1104 | 74.792 | 74.778 | 1.578 | -73.214 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## a5_kimi_tp8_e16_bf16_c4_p16k / source18c423c7

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
| FusedInferAttentionScore / unresolved | 1248 | 0 / 1248 | 48.025 | 48.032 | 4.730 | -43.295 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## a5_kimi_tp8_e16_bf16_c4_p4k / source18c423c7

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
| FusedInferAttentionScore / unresolved | 1272 | 0 / 1272 | 23.007 | 22.967 | 1.578 | -21.429 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## a5_kimi_tp8_e16_bf16_c8_p4k / source18c423c7

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
| FusedInferAttentionScore / unresolved | 1248 | 0 / 1248 | 31.708 | 31.686 | 1.578 | -30.130 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
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

## a3_kimi4_tp8_w4a8_c1 / source18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| reduce_scatterAicpuKernel / unresolved | 2032 | 0 / 2032 | 171.783 | 164.056 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 1016 | 0 / 1016 | 123.710 | 94.628 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| MatMulV2 / unresolved | 2032 | 0 / 2032 | 34.932 | 28.730 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 1270 | 0 / 1270 | 46.689 | 22.779 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| QuantBatchMatmulV3 / unresolved | 2794 | 0 / 2794 | 21.189 | 18.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 762 | 0 / 762 | 55.722 | 55.499 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| MoeDistributeDispatchV2 / unresolved | 762 | 0 / 762 | 54.373 | 54.379 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 2286 | 0 / 2286 | 14.300 | 15.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 762 | 0 / 762 | 38.730 | 39.539 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| hcom_reduceScatter_ / attention_output_communication | 1016 | 0 / 1016 | 28.562 | 22.130 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 1016 | 0 / 1016 | 26.897 | 18.140 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| QuantBatchMatmulV3 / latent_down | 762 | 762 / 0 | 29.193 | 29.059 | 35.087 | 5.894 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 2286 | 0 / 2286 | 9.720 | 9.900 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / latent_up | 762 | 762 / 0 | 28.573 | 28.579 | 26.557 | -2.016 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MemSet / unresolved | 2286 | 0 / 2286 | 8.121 | 8.780 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 762 | 0 / 762 | 21.626 | 21.559 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSituQuant / unresolved | 1524 | 0 / 1524 | 10.512 | 9.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV2 / unresolved | 762 | 0 / 762 | 20.267 | 18.600 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 254 | 254 / 0 | 56.548 | 56.538 | 72.287 | 15.739 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RecurrentKda / unresolved | 762 | 0 / 762 | 17.320 | 16.090 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 762 | 0 / 762 | 16.378 | 16.319 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 254 | 0 / 254 | 36.842 | 36.839 | 5.000 | -31.842 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / down | 254 | 254 / 0 | 35.765 | 35.719 | 33.109 | -2.655 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / unresolved | 762 | 0 / 762 | 11.275 | 12.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1270 | 0 / 1270 | 4.186 | 4.780 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_down.quantize | 1524 | 1524 / 0 | 3.150 | 3.100 | 2.500 | -0.650 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 1524 | 0 / 1524 | 3.120 | 1.950 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / unresolved | 1270 | 0 / 1270 | 3.016 | 3.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 762 | 0 / 762 | 4.970 | 4.720 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 254 | 0 / 254 | 12.738 | 12.679 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1270 | 0 / 1270 | 2.435 | 1.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / latent_norm | 762 | 762 / 0 | 3.801 | 3.540 | 2.500 | -1.301 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RealDiv / unresolved | 508 | 0 / 508 | 5.441 | 5.510 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Tanh / unresolved | 508 | 0 / 508 | 5.376 | 5.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 508 | 0 / 508 | 4.905 | 4.800 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 1016 | 0 / 1016 | 2.396 | 2.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 254 | 0 / 254 | 8.173 | 7.940 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_up.quantize | 762 | 762 / 0 | 2.647 | 2.659 | 2.500 | -0.147 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| BatchMatMulV2 / unresolved | 254 | 0 / 254 | 7.695 | 7.680 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 762 | 0 / 762 | 2.406 | 2.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 1016 | 0 / 1016 | 1.514 | 1.500 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 254 | 254 / 0 | 4.649 | 4.640 | 2.500 | -2.149 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / down.quantize | 254 | 254 / 0 | 4.452 | 4.420 | 2.500 | -1.952 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| IndexCheck / unresolved | 254 | 0 / 254 | 2.790 | 2.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterPaKvCache / unresolved | 254 | 0 / 254 | 2.443 | 2.439 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3 | 762 | 38.730 / 39.539 | 89.061 | 0.116 | 0.267 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3 | 762 | 55.722 / 55.499 | 175.598 | 0.167 | 0.527 | capacity_vs_valid_rows_conditional |

## a3_kimi4_tp8_w4a8_c16 / source18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| reduce_scatterAicpuKernel / unresolved | 1880 | 0 / 1880 | 170.781 | 163.357 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 705 | 0 / 705 | 324.459 | 322.654 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| GroupedMatmul / expert_down | 705 | 0 / 705 | 168.962 | 167.496 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| hcom_allGather_ / attention_output_communication | 940 | 0 / 940 | 106.632 | 73.478 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| DequantSituQuant / unresolved | 1410 | 0 / 1410 | 44.784 | 44.440 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 1175 | 0 / 1175 | 42.097 | 26.339 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MatMulV2 / unresolved | 705 | 0 / 705 | 61.218 | 64.858 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1645 | 0 / 1645 | 26.027 | 23.819 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 705 | 0 / 705 | 59.769 | 58.419 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV2 / unresolved | 705 | 0 / 705 | 57.680 | 57.359 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 235 | 0 / 235 | 159.143 | 159.077 | 5.000 | -154.143 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MatMulV2 / linear_output | 705 | 705 / 0 | 32.512 | 33.759 | 25.868 | -6.644 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_reduceScatter_ / ffn_down_communication | 940 | 0 / 940 | 24.204 | 18.400 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV2 / unresolved | 705 | 0 / 705 | 31.810 | 31.999 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AttnResFwd / unresolved | 2115 | 0 / 2115 | 10.055 | 10.219 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / latent_down | 705 | 705 / 0 | 29.484 | 29.399 | 35.241 | 5.757 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_reduceScatter_ / attention_output_communication | 940 | 0 / 940 | 21.866 | 17.340 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| QuantBatchMatmulV3 / latent_up | 705 | 705 / 0 | 28.424 | 28.400 | 26.786 | -1.638 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / unresolved | 705 | 0 / 705 | 25.383 | 25.380 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 235 | 235 / 0 | 55.989 | 55.959 | 74.718 | 18.729 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / unresolved | 705 | 0 / 705 | 17.706 | 17.519 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 705 | 0 / 705 | 17.248 | 17.220 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 705 | 705 / 0 | 13.278 | 13.279 | 6.961 | -6.318 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 235 | 235 / 0 | 35.416 | 35.379 | 35.237 | -0.179 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / output_gate | 235 | 235 / 0 | 31.337 | 31.359 | 39.352 | 8.016 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 2350 | 0 / 2350 | 3.059 | 2.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output | 235 | 235 / 0 | 28.446 | 28.619 | 25.868 | -2.578 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 1175 | 0 / 1175 | 5.130 | 6.240 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 470 | 0 / 470 | 12.608 | 12.389 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 940 | 0 / 940 | 5.887 | 5.700 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 705 | 0 / 705 | 7.316 | 7.400 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 1410 | 0 / 1410 | 3.401 | 2.100 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Transpose / unresolved | 235 | 0 / 235 | 20.407 | 19.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AsStrided / unresolved | 940 | 0 / 940 | 4.577 | 4.470 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1175 | 0 / 1175 | 3.551 | 2.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 705 | 0 / 705 | 5.502 | 5.700 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / shared.gate_up.quantize | 705 | 705 / 0 | 5.308 | 5.300 | 2.500 | -2.808 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / linear_q.quantize | 705 | 705 / 0 | 5.025 | 5.120 | 2.500 | -2.525 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 470 | 0 / 470 | 7.485 | 7.500 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 235 | 0 / 235 | 14.727 | 14.460 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MemSet / unresolved | 470 | 0 / 470 | 7.158 | 7.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / latent_norm | 705 | 705 / 0 | 4.575 | 4.880 | 2.500 | -2.075 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeBatchMatMul / v_expand | 235 | 235 / 0 | 13.460 | 13.420 | 5.000 | -8.460 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_b | 235 | 235 / 0 | 12.942 | 12.920 | 5.000 | -7.942 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Tanh / unresolved | 470 | 0 / 470 | 5.961 | 6.050 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RealDiv / unresolved | 470 | 0 / 470 | 5.960 | 6.150 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_down.quantize | 705 | 705 / 0 | 3.967 | 3.900 | 2.500 | -1.467 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| BatchMatMulV2 / unresolved | 235 | 0 / 235 | 8.370 | 8.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_up.quantize | 705 | 705 / 0 | 2.592 | 2.580 | 2.500 | -0.092 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| IndexCheck / unresolved | 235 | 0 / 235 | 5.547 | 5.520 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 235 | 235 / 0 | 5.280 | 5.280 | 2.500 | -2.780 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / q_b.quantize | 235 | 235 / 0 | 5.267 | 5.260 | 2.500 | -2.767 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / unresolved | 235 | 0 / 235 | 5.110 | 5.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_a.quantize | 235 | 235 / 0 | 5.051 | 5.040 | 2.500 | -2.551 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / down.quantize | 235 | 235 / 0 | 4.547 | 4.480 | 2.500 | -2.047 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3 | 705 | 168.962 / 167.496 | 174.251 | 0.507 | 0.523 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3 | 705 | 324.459 / 322.654 | 346.695 | 0.973 | 1.040 | capacity_vs_valid_rows_conditional |

## a3_kimi4_tp8_w4a8_c32 / source18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 660 | 0 / 660 | 631.825 | 633.147 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| reduce_scatterAicpuKernel / unresolved | 1760 | 0 / 1760 | 171.942 | 163.737 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 660 | 0 / 660 | 303.243 | 302.704 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| DequantSituQuant / unresolved | 1320 | 0 / 1320 | 83.005 | 82.918 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 880 | 0 / 880 | 96.009 | 32.769 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| RecurrentKda / unresolved | 660 | 0 / 660 | 102.069 | 102.738 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 220 | 0 / 220 | 277.586 | 277.455 | 5.000 | -272.586 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MatMulV2 / unresolved | 660 | 0 / 660 | 65.008 | 66.609 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1540 | 0 / 1540 | 26.512 | 21.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV2 / unresolved | 660 | 0 / 660 | 58.279 | 58.639 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 1100 | 0 / 1100 | 31.768 | 26.599 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV2 / unresolved | 660 | 0 / 660 | 42.028 | 39.630 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_output | 660 | 660 / 0 | 38.618 | 41.239 | 28.929 | -9.689 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_reduceScatter_ / ffn_down_communication | 880 | 0 / 880 | 27.660 | 24.049 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 880 | 0 / 880 | 24.170 | 18.580 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| AttnResFwd / unresolved | 1980 | 0 / 1980 | 10.626 | 10.600 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / latent_down | 660 | 660 / 0 | 29.618 | 29.730 | 35.548 | 5.930 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / latent_up | 660 | 660 / 0 | 28.015 | 27.920 | 27.246 | -0.769 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / unresolved | 660 | 0 / 660 | 25.650 | 23.959 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 660 | 0 / 660 | 22.027 | 21.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 220 | 220 / 0 | 56.800 | 56.779 | 79.579 | 22.779 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 660 | 0 / 660 | 17.216 | 17.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 660 | 660 / 0 | 15.492 | 15.249 | 8.074 | -7.418 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / output_gate | 220 | 220 / 0 | 42.152 | 42.179 | 43.796 | 1.644 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 220 | 220 / 0 | 36.931 | 36.849 | 39.492 | 2.561 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 880 | 0 / 880 | 8.047 | 7.999 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1100 | 0 / 1100 | 6.211 | 6.700 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 440 | 0 / 440 | 15.115 | 15.120 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 2200 | 0 / 2200 | 3.008 | 2.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output | 220 | 220 / 0 | 29.754 | 29.759 | 28.929 | -0.826 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 440 | 0 / 440 | 11.555 | 11.580 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 220 | 0 / 220 | 22.538 | 21.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 1320 | 0 / 1320 | 3.554 | 2.159 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AsStrided / unresolved | 880 | 0 / 880 | 5.208 | 5.380 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / shared.gate_up.quantize | 660 | 660 / 0 | 6.942 | 6.900 | 2.500 | -4.442 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Transpose / unresolved | 220 | 0 / 220 | 20.731 | 20.909 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1100 | 0 / 1100 | 4.017 | 1.560 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 660 | 0 / 660 | 6.586 | 6.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / linear_q.quantize | 660 | 660 / 0 | 6.290 | 6.560 | 2.500 | -3.790 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / unresolved | 660 | 0 / 660 | 5.973 | 6.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / latent_norm | 660 | 660 / 0 | 4.957 | 5.220 | 2.500 | -2.457 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MemSet / unresolved | 440 | 0 / 440 | 7.115 | 7.099 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Tanh / unresolved | 440 | 0 / 440 | 6.725 | 6.809 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 220 | 220 / 0 | 13.361 | 13.360 | 5.000 | -8.361 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / latent_down.quantize | 660 | 660 / 0 | 4.229 | 4.120 | 2.500 | -1.729 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_b | 220 | 220 / 0 | 12.678 | 12.640 | 5.084 | -7.594 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RealDiv / unresolved | 440 | 0 / 440 | 6.236 | 6.310 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_up.quantize | 660 | 660 / 0 | 3.905 | 3.900 | 2.500 | -1.405 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| IndexCheck / unresolved | 220 | 0 / 220 | 10.310 | 10.240 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BatchMatMulV2 / unresolved | 220 | 0 / 220 | 8.623 | 8.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 220 | 0 / 220 | 8.356 | 8.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterPaKvCache / unresolved | 220 | 0 / 220 | 8.155 | 8.159 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 220 | 220 / 0 | 6.874 | 6.860 | 2.500 | -4.374 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / q_a.quantize | 220 | 220 / 0 | 6.622 | 6.619 | 2.500 | -4.122 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / q_b.quantize | 220 | 220 / 0 | 4.692 | 4.680 | 2.500 | -2.192 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / down.quantize | 220 | 220 / 0 | 4.613 | 4.560 | 2.500 | -2.113 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3 | 660 | 303.243 / 302.704 | 345.826 | 0.910 | 1.037 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3 | 660 | 631.825 / 633.147 | 688.064 | 1.895 | 2.064 | capacity_vs_valid_rows_conditional |

## a3_kimi4_tp8_w4a8_c4 / source18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| reduce_scatterAicpuKernel / unresolved | 1968 | 0 / 1968 | 171.924 | 163.257 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 984 | 0 / 984 | 103.708 | 85.699 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| GroupedMatmul / expert_up | 738 | 0 / 738 | 103.723 | 103.598 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| MatMulV2 / unresolved | 1968 | 0 / 1968 | 36.611 | 29.439 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 2706 | 0 / 2706 | 20.978 | 18.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 1230 | 0 / 1230 | 40.674 | 24.840 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| GroupedMatmul / expert_down | 738 | 0 / 738 | 62.615 | 62.999 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| MoeDistributeDispatchV2 / unresolved | 738 | 0 / 738 | 55.596 | 54.779 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 2214 | 0 / 2214 | 14.933 | 14.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 738 | 0 / 738 | 34.298 | 33.939 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 984 | 0 / 984 | 25.451 | 20.930 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 984 | 0 / 984 | 23.741 | 18.029 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| DequantSituQuant / unresolved | 1476 | 0 / 1476 | 15.528 | 15.550 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / latent_down | 738 | 738 / 0 | 29.601 | 29.480 | 35.087 | 5.486 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 2214 | 0 / 2214 | 9.705 | 9.940 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / latent_up | 738 | 738 / 0 | 28.752 | 28.579 | 26.557 | -2.196 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MemSet / unresolved | 2214 | 0 / 2214 | 8.546 | 8.920 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV2 / unresolved | 738 | 0 / 738 | 23.757 | 23.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 738 | 0 / 738 | 22.360 | 22.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 246 | 0 / 246 | 60.488 | 60.369 | 5.000 | -55.488 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / gate_up | 246 | 246 / 0 | 54.590 | 54.569 | 72.287 | 17.698 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 738 | 0 / 738 | 16.358 | 16.100 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 738 | 0 / 738 | 16.004 | 15.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / down | 246 | 246 / 0 | 36.832 | 36.780 | 33.109 | -3.722 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / unresolved | 1968 | 0 / 1968 | 4.041 | 4.120 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1230 | 0 / 1230 | 4.197 | 4.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 2460 | 0 / 2460 | 1.968 | 1.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Transpose / unresolved | 246 | 0 / 246 | 19.072 | 18.759 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 1476 | 0 / 1476 | 3.143 | 2.099 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AsStrided / unresolved | 984 | 0 / 984 | 4.237 | 4.210 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 738 | 0 / 738 | 5.003 | 4.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1230 | 0 / 1230 | 2.653 | 1.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 246 | 0 / 246 | 12.912 | 12.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / latent_norm | 738 | 738 / 0 | 3.994 | 3.970 | 2.500 | -1.494 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 492 | 0 / 492 | 5.617 | 5.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 738 | 0 / 738 | 3.656 | 3.720 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RealDiv / unresolved | 492 | 0 / 492 | 5.456 | 5.530 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Tanh / unresolved | 492 | 0 / 492 | 5.343 | 5.269 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_down.quantize | 738 | 738 / 0 | 3.156 | 3.080 | 2.500 | -0.656 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 984 | 0 / 984 | 2.314 | 2.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 246 | 0 / 246 | 8.476 | 8.079 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_up.quantize | 738 | 738 / 0 | 2.664 | 2.660 | 2.500 | -0.164 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| BatchMatMulV2 / unresolved | 246 | 0 / 246 | 7.631 | 7.619 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 246 | 246 / 0 | 4.681 | 4.679 | 2.500 | -2.181 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / down.quantize | 246 | 246 / 0 | 4.535 | 4.519 | 2.500 | -2.035 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| IndexCheck / unresolved | 246 | 0 / 246 | 3.296 | 3.280 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterPaKvCache / unresolved | 246 | 0 / 246 | 2.893 | 2.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3 | 738 | 62.615 / 62.999 | 89.061 | 0.188 | 0.267 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3 | 738 | 103.723 / 103.598 | 175.598 | 0.311 | 0.527 | capacity_vs_valid_rows_conditional |

## a3_kimi4_tp8_w4a8_c64 / source18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 588 | 0 / 588 | 1095.630 | 1098.018 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| GroupedMatmul / expert_down | 588 | 0 / 588 | 520.577 | 518.519 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| reduce_scatterAicpuKernel / unresolved | 1568 | 0 / 1568 | 175.316 | 164.387 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSituQuant / unresolved | 1176 | 0 / 1176 | 140.007 | 139.498 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 588 | 0 / 588 | 176.676 | 178.777 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 196 | 0 / 196 | 505.614 | 505.810 | 5.000 | -500.614 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MatMulV2 / unresolved | 588 | 0 / 588 | 90.415 | 93.658 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 784 | 0 / 784 | 61.707 | 30.479 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| QuantBatchMatmulV3 / unresolved | 1372 | 0 / 1372 | 27.366 | 22.599 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV2 / unresolved | 588 | 0 / 588 | 62.546 | 62.579 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 980 | 0 / 980 | 30.708 | 28.890 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MatMulV2 / linear_output | 588 | 588 / 0 | 40.050 | 38.039 | 35.050 | -5.000 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_reduceScatter_ / ffn_down_communication | 784 | 0 / 784 | 28.643 | 27.200 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| AttnResFwd / unresolved | 1764 | 0 / 1764 | 11.494 | 11.680 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 784 | 0 / 784 | 25.830 | 23.400 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV2 / unresolved | 588 | 0 / 588 | 33.945 | 32.569 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / latent_down | 588 | 588 / 0 | 30.103 | 29.879 | 36.164 | 6.061 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / unresolved | 588 | 0 / 588 | 29.315 | 28.800 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 588 | 0 / 588 | 29.132 | 32.099 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / latent_up | 588 | 588 / 0 | 27.905 | 27.840 | 28.164 | 0.259 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / gate_up | 196 | 196 / 0 | 60.636 | 60.639 | 89.300 | 28.664 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 588 | 0 / 588 | 18.571 | 17.230 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output_gate | 196 | 196 / 0 | 51.145 | 51.199 | 52.683 | 1.538 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 588 | 588 / 0 | 16.957 | 16.940 | 10.301 | -6.656 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 196 | 196 / 0 | 40.148 | 40.039 | 48.003 | 7.855 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 980 | 0 / 980 | 6.952 | 6.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 784 | 0 / 784 | 8.624 | 8.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / shared.gate_up.quantize | 588 | 588 / 0 | 11.055 | 10.280 | 2.500 | -8.555 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 1960 | 0 / 1960 | 3.232 | 3.220 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 392 | 0 / 392 | 15.684 | 15.799 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 588 | 0 / 588 | 9.717 | 9.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / linear_q.quantize | 588 | 588 / 0 | 9.091 | 9.500 | 2.500 | -6.591 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / output | 196 | 196 / 0 | 26.683 | 26.659 | 35.050 | 8.367 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AsStrided / unresolved | 784 | 0 / 784 | 6.382 | 6.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 196 | 0 / 196 | 24.884 | 24.770 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 1176 | 0 / 1176 | 3.720 | 2.550 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 980 | 0 / 980 | 4.140 | 1.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 392 | 0 / 392 | 10.323 | 10.460 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 588 | 0 / 588 | 6.559 | 6.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 196 | 196 / 0 | 16.602 | 16.589 | 5.000 | -11.602 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / latent_norm | 588 | 588 / 0 | 5.530 | 5.739 | 2.500 | -3.030 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Tanh / unresolved | 392 | 0 / 392 | 7.806 | 7.900 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MemSet / unresolved | 392 | 0 / 392 | 7.343 | 7.300 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_down.quantize | 588 | 588 / 0 | 4.676 | 4.700 | 2.500 | -2.176 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_b | 196 | 196 / 0 | 13.983 | 13.999 | 6.351 | -7.631 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RealDiv / unresolved | 392 | 0 / 392 | 6.384 | 6.420 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| IndexCheck / unresolved | 196 | 0 / 196 | 12.764 | 12.680 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_up.quantize | 588 | 588 / 0 | 3.556 | 3.540 | 2.500 | -1.056 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / gate_up.quantize | 196 | 196 / 0 | 10.314 | 10.300 | 2.500 | -7.814 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Transpose / unresolved | 196 | 0 / 196 | 9.704 | 9.690 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_a.quantize | 196 | 196 / 0 | 9.551 | 9.540 | 2.500 | -7.051 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / unresolved | 196 | 0 / 196 | 9.477 | 9.450 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BatchMatMulV2 / unresolved | 196 | 0 / 196 | 9.024 | 9.000 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 196 | 0 / 196 | 8.424 | 8.440 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / down.quantize | 196 | 196 / 0 | 6.544 | 6.540 | 2.500 | -4.044 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / q_b.quantize | 196 | 196 / 0 | 4.646 | 4.620 | 2.500 | -2.146 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3 | 588 | 520.577 / 518.519 | 613.046 | 1.562 | 1.839 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3 | 588 | 1095.630 / 1098.018 | 1214.924 | 3.287 | 3.645 | capacity_vs_valid_rows_conditional |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c16_p16k / source18c423c7 / GroupedMatmul / expert_down | 4324 | 0 | 4324 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p16k / source18c423c7 / GroupedMatmul / expert_up | 4324 | 0 | 4324 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p16k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 4324 | 0 | 0 | 4324 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p16k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 4324 | 0 | 0 | 4324 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / source18c423c7 / GroupedMatmul / expert_down | 4508 | 0 | 4508 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / source18c423c7 / GroupedMatmul / expert_up | 4508 | 0 | 4508 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 4508 | 0 | 0 | 4508 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 4508 | 0 | 0 | 4508 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 / GroupedMatmul / expert_down | 5428 | 0 | 5428 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 / GroupedMatmul / expert_up | 5428 | 0 | 5428 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 5428 | 0 | 0 | 5428 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 5428 | 0 | 0 | 5428 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / source18c423c7 / GroupedMatmul / expert_down | 5428 | 0 | 5428 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / source18c423c7 / GroupedMatmul / expert_up | 5428 | 0 | 5428 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 5428 | 0 | 0 | 5428 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 5428 | 0 | 0 | 5428 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / source18c423c7 / GroupedMatmul / expert_down | 4968 | 0 | 4968 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / source18c423c7 / GroupedMatmul / expert_up | 4968 | 0 | 4968 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 4968 | 0 | 0 | 4968 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 4968 | 0 | 0 | 4968 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p4k / source18c423c7 / GroupedMatmul / expert_down | 5060 | 0 | 5060 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p4k / source18c423c7 / GroupedMatmul / expert_up | 5060 | 0 | 5060 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p4k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 5060 | 0 | 0 | 5060 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p4k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 5060 | 0 | 0 | 5060 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / GroupedMatmul / expert_down | 3772 | 0 | 3772 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / GroupedMatmul / expert_up | 3772 | 0 | 3772 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 3772 | 0 | 0 | 3772 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 3772 | 0 | 0 | 3772 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / source18c423c7 / GroupedMatmul / expert_down | 4232 | 0 | 4232 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / source18c423c7 / GroupedMatmul / expert_up | 4232 | 0 | 4232 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 4232 | 0 | 0 | 4232 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 4232 | 0 | 0 | 4232 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / source18c423c7 / GroupedMatmul / expert_down | 4784 | 0 | 4784 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / source18c423c7 / GroupedMatmul / expert_up | 4784 | 0 | 4784 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 4784 | 0 | 0 | 4784 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 4784 | 0 | 0 | 4784 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / source18c423c7 / GroupedMatmul / expert_down | 4876 | 0 | 4876 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / source18c423c7 / GroupedMatmul / expert_up | 4876 | 0 | 4876 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 4876 | 0 | 0 | 4876 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 4876 | 0 | 0 | 4876 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 / GroupedMatmul / expert_down | 4692 | 0 | 4692 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 / GroupedMatmul / expert_up | 4692 | 0 | 4692 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 4692 | 0 | 0 | 4692 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 4692 | 0 | 0 | 4692 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / source18c423c7 / GroupedMatmul / expert_down | 4784 | 0 | 4784 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / source18c423c7 / GroupedMatmul / expert_up | 4784 | 0 | 4784 | 0 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / source18c423c7 / MoeDistributeCombineV3 / expert_combine_native | 4784 | 0 | 0 | 4784 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / source18c423c7 / MoeDistributeDispatchV3 / expert_dispatch_native | 4784 | 0 | 0 | 4784 | 0 |
| a3_kimi4_tp8_w4a8_c1 / source18c423c7 / GroupedMatmul / expert_down | 762 | 0 | 762 | 0 | 0 |
| a3_kimi4_tp8_w4a8_c1 / source18c423c7 / GroupedMatmul / expert_up | 762 | 0 | 762 | 0 | 0 |
| a3_kimi4_tp8_w4a8_c16 / source18c423c7 / GroupedMatmul / expert_down | 705 | 0 | 705 | 0 | 0 |
| a3_kimi4_tp8_w4a8_c16 / source18c423c7 / GroupedMatmul / expert_up | 705 | 0 | 705 | 0 | 0 |
| a3_kimi4_tp8_w4a8_c32 / source18c423c7 / GroupedMatmul / expert_down | 660 | 0 | 660 | 0 | 0 |
| a3_kimi4_tp8_w4a8_c32 / source18c423c7 / GroupedMatmul / expert_up | 660 | 0 | 660 | 0 | 0 |
| a3_kimi4_tp8_w4a8_c4 / source18c423c7 / GroupedMatmul / expert_down | 738 | 0 | 738 | 0 | 0 |
| a3_kimi4_tp8_w4a8_c4 / source18c423c7 / GroupedMatmul / expert_up | 738 | 0 | 738 | 0 | 0 |
| a3_kimi4_tp8_w4a8_c64 / source18c423c7 / GroupedMatmul / expert_down | 588 | 0 | 588 | 0 | 0 |
| a3_kimi4_tp8_w4a8_c64 / source18c423c7 / GroupedMatmul / expert_up | 588 | 0 | 588 | 0 | 0 |
