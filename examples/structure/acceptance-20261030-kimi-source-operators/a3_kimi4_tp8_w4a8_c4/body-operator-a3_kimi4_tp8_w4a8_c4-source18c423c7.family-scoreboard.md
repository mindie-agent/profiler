# Complete Decode Body Operator Families

Only complete events inside the 246 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_kimi4_tp8_w4a8_c4 / source18c423c7 | 8 / 8 | 0 / 1 | 8 / 9 | 4674 / 44526 | 0 |

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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_kimi4_tp8_w4a8_c4 / source18c423c7 / GroupedMatmul / expert_down | 738 | 0 | 738 | 0 | 0 |
| a3_kimi4_tp8_w4a8_c4 / source18c423c7 / GroupedMatmul / expert_up | 738 | 0 | 738 | 0 | 0 |
