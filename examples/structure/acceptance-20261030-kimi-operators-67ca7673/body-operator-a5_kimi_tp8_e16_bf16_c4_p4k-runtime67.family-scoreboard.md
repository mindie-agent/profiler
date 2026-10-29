# Complete Decode Body Operator Families

Only complete events inside the 53 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c4_p4k / runtime67 | 5 / 5 | 0 / 0 | 5 / 5 | 14734 / 296270 | 0 |

## a5_kimi_tp8_e16_bf16_c4_p4k / runtime67

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MatMulV3 / unresolved | 28143 | 0 / 28143 | 14.033 | 11.529 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 4876 | 0 / 4876 | 41.239 | 41.265 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4876 | 0 / 4876 | 31.842 | 31.813 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 4876 | 4876 / 0 | 24.291 | 24.304 | 12.999 | -11.292 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 9911 | 0 / 9911 | 11.009 | 10.828 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 4876 | 4876 / 0 | 20.950 | 20.938 | 14.118 | -6.831 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 29468 | 0 / 29468 | 3.358 | 3.459 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 4876 | 0 / 4876 | 20.066 | 20.058 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c4_p4k / runtime67 / GroupedMatmul / expert_down | 4876 | 0 | 0 | 4876 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / runtime67 / GroupedMatmul / expert_up | 4876 | 0 | 0 | 4876 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / runtime67 / MoeDistributeCombineV3 / expert_combine_native | 4876 | 0 | 0 | 4876 | 0 |
| a5_kimi_tp8_e16_bf16_c4_p4k / runtime67 / MoeDistributeDispatchV3 / expert_dispatch_native | 4876 | 0 | 0 | 4876 | 0 |
