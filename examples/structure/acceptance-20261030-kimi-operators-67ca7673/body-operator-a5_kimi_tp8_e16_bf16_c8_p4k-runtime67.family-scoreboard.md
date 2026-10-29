# Complete Decode Body Operator Families

Only complete events inside the 52 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c8_p4k / runtime67 | 9 / 9 | 0 / 0 | 9 / 9 | 28860 / 280904 | 0 |

## a5_kimi_tp8_e16_bf16_c8_p4k / runtime67

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4784 | 0 / 4784 | 42.630 | 42.813 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 13208 | 0 / 13208 | 14.603 | 7.882 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4784 | 0 / 4784 | 32.913 | 32.904 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4784 | 4784 / 0 | 24.439 | 24.471 | 12.999 | -11.440 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 9724 | 0 / 9724 | 10.977 | 10.745 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 28912 | 0 / 28912 | 3.509 | 3.583 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4784 | 4784 / 0 | 21.042 | 21.027 | 14.118 | -6.924 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GroupedMatmul / expert_down | 4784 | 0 / 4784 | 20.594 | 20.584 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared.gate_up | 4784 | 4784 / 0 | 20.054 | 20.070 | 7.879 | -12.175 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| ForeachAddList / unresolved | 4784 | 0 / 4784 | 5.306 | 5.303 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 3588 | 0 / 3588 | 7.043 | 7.032 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / q_a | 1248 | 1248 / 0 | 18.715 | 18.535 | 7.879 | -10.836 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / latent_norm | 4784 | 4784 / 0 | 4.016 | 4.037 | 1.312 | -2.704 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c8_p4k / runtime67 / GroupedMatmul / expert_down | 4784 | 0 | 0 | 4784 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / runtime67 / GroupedMatmul / expert_up | 4784 | 0 | 0 | 4784 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / runtime67 / MoeDistributeCombineV3 / expert_combine_native | 4784 | 0 | 0 | 4784 | 0 |
| a5_kimi_tp8_e16_bf16_c8_p4k / runtime67 / MoeDistributeDispatchV3 / expert_dispatch_native | 4784 | 0 | 0 | 4784 | 0 |
