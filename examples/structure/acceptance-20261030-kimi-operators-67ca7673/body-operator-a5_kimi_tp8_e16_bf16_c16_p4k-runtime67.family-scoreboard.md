# Complete Decode Body Operator Families

Only complete events inside the 49 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c16_p4k / runtime67 | 8 / 8 | 1 / 1 | 9 / 9 | 27195 / 264698 | 0 |

## a5_kimi_tp8_e16_bf16_c16_p4k / runtime67

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4508 | 0 / 4508 | 43.967 | 44.307 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 12446 | 0 / 12446 | 15.043 | 7.542 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4508 | 0 / 4508 | 33.414 | 33.418 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4508 | 4508 / 0 | 25.319 | 25.415 | 13.766 | -11.552 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 9163 | 0 / 9163 | 11.191 | 10.965 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 27244 | 0 / 27244 | 3.613 | 3.680 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4508 | 4508 / 0 | 21.792 | 21.791 | 14.180 | -7.613 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GroupedMatmul / expert_down | 4508 | 0 / 4508 | 21.325 | 21.385 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 37436 | 0 / 37436 | 2.551 | 2.072 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared.gate_up | 4508 | 4508 / 0 | 20.727 | 20.756 | 8.769 | -11.958 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| CausalConv1d / unresolved | 3381 | 0 / 3381 | 8.332 | 8.289 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 4508 | 0 / 4508 | 5.519 | 5.516 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / q_a | 1176 | 1176 / 0 | 19.147 | 18.956 | 8.769 | -10.378 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / latent_norm | 4508 | 4508 / 0 | 4.209 | 4.181 | 1.312 | -2.897 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c16_p4k / runtime67 / GroupedMatmul / expert_down | 4508 | 0 | 0 | 4508 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / runtime67 / GroupedMatmul / expert_up | 4508 | 0 | 0 | 4508 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / runtime67 / MoeDistributeCombineV3 / expert_combine_native | 4508 | 0 | 0 | 4508 | 0 |
| a5_kimi_tp8_e16_bf16_c16_p4k / runtime67 / MoeDistributeDispatchV3 / expert_dispatch_native | 4508 | 0 | 0 | 4508 | 0 |
