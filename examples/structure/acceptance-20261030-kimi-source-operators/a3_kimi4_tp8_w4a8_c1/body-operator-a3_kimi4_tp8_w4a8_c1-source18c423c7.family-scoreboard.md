# Complete Decode Body Operator Families

Only complete events inside the 254 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_kimi4_tp8_w4a8_c1 / source18c423c7 | 8 / 8 | 0 / 1 | 8 / 9 | 5588 / 43180 | 0 |

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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_kimi4_tp8_w4a8_c1 / source18c423c7 / GroupedMatmul / expert_down | 762 | 0 | 762 | 0 | 0 |
| a3_kimi4_tp8_w4a8_c1 / source18c423c7 / GroupedMatmul / expert_up | 762 | 0 | 762 | 0 | 0 |
