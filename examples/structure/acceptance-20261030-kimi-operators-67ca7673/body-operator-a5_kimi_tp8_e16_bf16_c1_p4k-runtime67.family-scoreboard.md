# Complete Decode Body Operator Families

Only complete events inside the 59 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c1_p4k / runtime67 | 5 / 5 | 0 / 0 | 5 / 5 | 16402 / 303732 | 0 |

## a5_kimi_tp8_e16_bf16_c1_p4k / runtime67

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MatMulV3 / unresolved | 31329 | 0 / 31329 | 13.689 | 11.485 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 5428 | 0 / 5428 | 31.335 | 31.323 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_down | 5428 | 5428 / 0 | 23.858 | 23.819 | 12.999 | -10.859 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AttnResFwd / unresolved | 11033 | 0 / 11033 | 10.974 | 10.821 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 5428 | 0 / 5428 | 21.918 | 21.895 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / latent_up | 5428 | 5428 / 0 | 20.571 | 20.570 | 14.118 | -6.452 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 45076 | 0 / 45076 | 2.370 | 1.955 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 5428 | 0 / 5428 | 16.045 | 16.026 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c1_p4k / runtime67 / GroupedMatmul / expert_down | 5428 | 0 | 0 | 5428 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / runtime67 / GroupedMatmul / expert_up | 5428 | 0 | 0 | 5428 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / runtime67 / MoeDistributeCombineV3 / expert_combine_native | 5428 | 0 | 0 | 5428 | 0 |
| a5_kimi_tp8_e16_bf16_c1_p4k / runtime67 / MoeDistributeDispatchV3 / expert_dispatch_native | 5428 | 0 | 0 | 5428 | 0 |
