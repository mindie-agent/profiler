# Complete Decode Body Operator Families

Only complete events inside the 46 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c32_p4k / runtime67 | 8 / 8 | 1 / 1 | 9 / 9 | 25530 / 248538 | 0 |

## a5_kimi_tp8_e16_bf16_c32_p4k / runtime67

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4232 | 0 / 4232 | 46.237 | 47.053 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 11684 | 0 / 11684 | 15.756 | 7.644 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4232 | 0 / 4232 | 34.197 | 34.183 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4232 | 4232 / 0 | 26.875 | 27.136 | 14.433 | -12.442 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 8602 | 0 / 8602 | 11.403 | 11.165 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 3174 | 0 / 3174 | 30.461 | 30.449 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4232 | 4232 / 0 | 22.651 | 22.648 | 14.303 | -8.348 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 25576 | 0 / 25576 | 3.693 | 3.681 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared.gate_up | 4232 | 4232 / 0 | 22.209 | 22.333 | 10.548 | -11.662 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GroupedMatmul / expert_down | 4232 | 0 / 4232 | 22.016 | 22.110 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
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
| ForeachAddList / unresolved | 4232 | 0 / 4232 | 5.807 | 5.803 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / q_a | 1104 | 1104 / 0 | 19.252 | 19.148 | 10.548 | -8.704 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / latent_norm | 4232 | 4232 / 0 | 4.285 | 4.264 | 1.312 | -2.973 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c32_p4k / runtime67 / GroupedMatmul / expert_down | 4232 | 0 | 0 | 4232 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / runtime67 / GroupedMatmul / expert_up | 4232 | 0 | 0 | 4232 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / runtime67 / MoeDistributeCombineV3 / expert_combine_native | 4232 | 0 | 0 | 4232 | 0 |
| a5_kimi_tp8_e16_bf16_c32_p4k / runtime67 / MoeDistributeDispatchV3 / expert_dispatch_native | 4232 | 0 | 0 | 4232 | 0 |
