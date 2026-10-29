# Complete Decode Body Operator Families

Only complete events inside the 52 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c4_p16k / runtime67 | 5 / 5 | 0 / 0 | 5 / 5 | 14456 / 290680 | 0 |

## a5_kimi_tp8_e16_bf16_c4_p16k / runtime67

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MatMulV3 / unresolved | 27612 | 0 / 27612 | 14.026 | 11.549 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 4784 | 0 / 4784 | 41.471 | 41.486 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4784 | 0 / 4784 | 31.864 | 31.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4784 | 4784 / 0 | 24.241 | 24.248 | 12.999 | -11.242 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 9724 | 0 / 9724 | 11.008 | 10.821 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4784 | 4784 / 0 | 20.956 | 20.941 | 14.118 | -6.838 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 28912 | 0 / 28912 | 3.357 | 3.459 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 4784 | 0 / 4784 | 20.097 | 20.084 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c4_p16k / runtime67 / GroupedMatmul / expert_down | 4784 | 0 | 0 | 4784 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / runtime67 / GroupedMatmul / expert_up | 4784 | 0 | 0 | 4784 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / runtime67 / MoeDistributeCombineV3 / expert_combine_native | 4784 | 0 | 0 | 4784 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p16k / runtime67 / MoeDistributeDispatchV3 / expert_dispatch_native | 4784 | 0 | 0 | 4784 | 0 |
