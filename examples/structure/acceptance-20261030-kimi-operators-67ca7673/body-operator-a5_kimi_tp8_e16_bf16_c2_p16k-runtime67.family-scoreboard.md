# Complete Decode Body Operator Families

Only complete events inside the 54 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c2_p16k / runtime67 | 5 / 5 | 0 / 0 | 5 / 5 | 15012 / 301860 | 0 |

## a5_kimi_tp8_e16_bf16_c2_p16k / runtime67

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MatMulV3 / unresolved | 28674 | 0 / 28674 | 13.794 | 11.546 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 4968 | 0 / 4968 | 34.585 | 34.645 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4968 | 0 / 4968 | 31.565 | 31.543 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4968 | 4968 / 0 | 23.893 | 23.864 | 12.999 | -10.894 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 10098 | 0 / 10098 | 10.995 | 10.826 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 4968 | 0 / 4968 | 22.335 | 22.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4968 | 4968 / 0 | 20.767 | 20.778 | 14.118 | -6.648 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 41256 | 0 / 41256 | 2.463 | 2.055 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 30024 | 0 / 30024 | 3.264 | 3.021 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 4968 | 0 / 4968 | 16.222 | 16.216 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c2_p16k / runtime67 / GroupedMatmul / expert_down | 4968 | 0 | 0 | 4968 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / runtime67 / GroupedMatmul / expert_up | 4968 | 0 | 0 | 4968 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / runtime67 / MoeDistributeCombineV3 / expert_combine_native | 4968 | 0 | 0 | 4968 | 0 |
| a5_kimi_tp8_e16_bf16_c2_p16k / runtime67 / MoeDistributeDispatchV3 / expert_dispatch_native | 4968 | 0 | 0 | 4968 | 0 |
