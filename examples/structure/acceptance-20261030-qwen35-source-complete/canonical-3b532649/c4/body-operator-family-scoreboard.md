# Complete Decode Body Operator Families

Only complete events inside the 84 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen35-35b-a5-tp4-c4-graph / mc2-tp-3b532649 | 12 / 12 | 0 / 0 | 12 / 12 | 32760 / 141960 | 0 |

## qwen35-35b-a5-tp4-c4-graph / mc2-tp-3b532649

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / unresolved | 6720 | 0 / 6720 | 27.975 | 26.755 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 3360 | 0 / 3360 | 27.597 | 25.198 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / ffn_down_communication | 3360 | 0 / 3360 | 25.232 | 25.222 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / unresolved | 3360 | 0 / 3360 | 17.246 | 16.954 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 3360 | 0 / 3360 | 11.678 | 11.374 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 840 | 0 / 840 | 45.006 | 44.972 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 3360 | 0 / 3360 | 10.573 | 10.290 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MatMulV3 / router | 6720 | 6720 / 0 | 3.939 | 3.928 | 4.604 | 0.665 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2520 | 2520 / 0 | 10.133 | 10.102 | 6.415 | -3.718 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DequantSwigluQuant / unresolved | 3360 | 0 / 3360 | 7.299 | 7.286 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNorm / unresolved | 5796 | 0 / 5796 | 3.971 | 3.956 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvz | 2520 | 2520 / 0 | 8.154 | 8.075 | 4.619 | -3.535 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 2520 | 2520 / 0 | 7.337 | 7.293 | 1.312 | -6.025 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 3360 | 0 / 3360 | 4.776 | 4.735 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 8400 | 0 / 8400 | 1.910 | 1.952 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 5880 | 0 / 5880 | 2.717 | 2.485 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 4200 | 0 / 4200 | 3.425 | 3.053 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 4200 | 0 / 4200 | 3.244 | 3.194 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| fused_gdn_gating_kernel / unresolved | 2520 | 0 / 2520 | 5.242 | 4.984 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 2520 | 2520 / 0 | 4.698 | 4.676 | 2.377 | -2.321 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / k_flat + q_flat | 5040 | 0 / 5040 | 2.221 | 2.236 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 3360 | 0 / 3360 | 3.141 | 3.130 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 5040 | 0 / 5040 | 2.017 | 1.950 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / shared_gate | 3360 | 3360 / 0 | 2.825 | 2.841 | 1.578 | -1.247 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / alpha_contiguous + beta_contiguous | 5040 | 0 / 5040 | 1.840 | 1.831 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 2520 | 0 / 2520 | 3.657 | 3.502 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 3360 | 0 / 3360 | 2.627 | 2.548 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 2520 | 2520 / 0 | 3.260 | 3.265 | 1.578 | -1.682 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RealDiv / unresolved | 3360 | 0 / 3360 | 2.437 | 2.453 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / shared.swiglu | 3360 | 3360 / 0 | 2.345 | 2.397 | 1.312 | -1.033 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ReduceSum / unresolved | 3360 | 0 / 3360 | 2.295 | 2.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 4200 | 0 / 4200 | 1.777 | 1.603 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNormDynamicQuant / unresolved | 840 | 0 / 840 | 8.085 | 8.397 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 2520 | 2520 / 0 | 2.513 | 2.492 | 1.312 | -1.201 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 2520 | 0 / 2520 | 2.354 | 2.233 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 840 | 840 / 0 | 6.768 | 6.694 | 2.365 | -4.404 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / v_flat | 2520 | 2520 / 0 | 2.084 | 2.080 | 1.312 | -0.772 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 840 | 0 / 840 | 6.229 | 6.253 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sub / unresolved | 3360 | 0 / 3360 | 1.502 | 1.440 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 3360 | 0 / 3360 | 1.407 | 1.373 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterPaKvCache / cache | 840 | 840 / 0 | 3.827 | 3.804 | 1.312 | -2.515 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 840 | 0 / 840 | 3.399 | 3.396 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 84 | 0 / 84 | 4.159 | 4.138 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
