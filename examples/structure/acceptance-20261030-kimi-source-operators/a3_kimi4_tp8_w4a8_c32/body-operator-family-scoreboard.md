# Complete Decode Body Operator Families

Only complete events inside the 220 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_kimi4_tp8_w4a8_c32 / source18c423c7 | 18 / 18 | 0 / 1 | 18 / 19 | 8140 / 36960 | 0 |

## a3_kimi4_tp8_w4a8_c32 / source18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 660 | 0 / 660 | 631.825 | 633.147 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| reduce_scatterAicpuKernel / unresolved | 1760 | 0 / 1760 | 171.942 | 163.737 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 660 | 0 / 660 | 303.243 | 302.704 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| DequantSituQuant / unresolved | 1320 | 0 / 1320 | 83.005 | 82.918 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 880 | 0 / 880 | 96.009 | 32.769 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| RecurrentKda / unresolved | 660 | 0 / 660 | 102.069 | 102.738 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 220 | 0 / 220 | 277.586 | 277.455 | 5.000 | -272.586 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MatMulV2 / unresolved | 660 | 0 / 660 | 65.008 | 66.609 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1540 | 0 / 1540 | 26.512 | 21.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV2 / unresolved | 660 | 0 / 660 | 58.279 | 58.639 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 1100 | 0 / 1100 | 31.768 | 26.599 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV2 / unresolved | 660 | 0 / 660 | 42.028 | 39.630 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_output | 660 | 660 / 0 | 38.618 | 41.239 | 28.929 | -9.689 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_reduceScatter_ / ffn_down_communication | 880 | 0 / 880 | 27.660 | 24.049 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 880 | 0 / 880 | 24.170 | 18.580 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| AttnResFwd / unresolved | 1980 | 0 / 1980 | 10.626 | 10.600 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / latent_down | 660 | 660 / 0 | 29.618 | 29.730 | 35.548 | 5.930 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / latent_up | 660 | 660 / 0 | 28.015 | 27.920 | 27.246 | -0.769 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / unresolved | 660 | 0 / 660 | 25.650 | 23.959 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 660 | 0 / 660 | 22.027 | 21.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 220 | 220 / 0 | 56.800 | 56.779 | 79.579 | 22.779 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 660 | 0 / 660 | 17.216 | 17.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 660 | 660 / 0 | 15.492 | 15.249 | 8.074 | -7.418 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / output_gate | 220 | 220 / 0 | 42.152 | 42.179 | 43.796 | 1.644 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 220 | 220 / 0 | 36.931 | 36.849 | 39.492 | 2.561 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 880 | 0 / 880 | 8.047 | 7.999 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1100 | 0 / 1100 | 6.211 | 6.700 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 440 | 0 / 440 | 15.115 | 15.120 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 2200 | 0 / 2200 | 3.008 | 2.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output | 220 | 220 / 0 | 29.754 | 29.759 | 28.929 | -0.826 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 440 | 0 / 440 | 11.555 | 11.580 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 220 | 0 / 220 | 22.538 | 21.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 1320 | 0 / 1320 | 3.554 | 2.159 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AsStrided / unresolved | 880 | 0 / 880 | 5.208 | 5.380 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / shared.gate_up.quantize | 660 | 660 / 0 | 6.942 | 6.900 | 2.500 | -4.442 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Transpose / unresolved | 220 | 0 / 220 | 20.731 | 20.909 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1100 | 0 / 1100 | 4.017 | 1.560 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 660 | 0 / 660 | 6.586 | 6.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / linear_q.quantize | 660 | 660 / 0 | 6.290 | 6.560 | 2.500 | -3.790 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / unresolved | 660 | 0 / 660 | 5.973 | 6.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / latent_norm | 660 | 660 / 0 | 4.957 | 5.220 | 2.500 | -2.457 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MemSet / unresolved | 440 | 0 / 440 | 7.115 | 7.099 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Tanh / unresolved | 440 | 0 / 440 | 6.725 | 6.809 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 220 | 220 / 0 | 13.361 | 13.360 | 5.000 | -8.361 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / latent_down.quantize | 660 | 660 / 0 | 4.229 | 4.120 | 2.500 | -1.729 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_b | 220 | 220 / 0 | 12.678 | 12.640 | 5.084 | -7.594 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RealDiv / unresolved | 440 | 0 / 440 | 6.236 | 6.310 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_up.quantize | 660 | 660 / 0 | 3.905 | 3.900 | 2.500 | -1.405 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| IndexCheck / unresolved | 220 | 0 / 220 | 10.310 | 10.240 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BatchMatMulV2 / unresolved | 220 | 0 / 220 | 8.623 | 8.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 220 | 0 / 220 | 8.356 | 8.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterPaKvCache / unresolved | 220 | 0 / 220 | 8.155 | 8.159 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 220 | 220 / 0 | 6.874 | 6.860 | 2.500 | -4.374 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / q_a.quantize | 220 | 220 / 0 | 6.622 | 6.619 | 2.500 | -4.122 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / q_b.quantize | 220 | 220 / 0 | 4.692 | 4.680 | 2.500 | -2.192 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / down.quantize | 220 | 220 / 0 | 4.613 | 4.560 | 2.500 | -2.113 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 1, 2, 3 | 660 | 303.243 / 302.704 | 345.826 | 0.910 | 1.037 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 1, 2, 3 | 660 | 631.825 / 633.147 | 688.064 | 1.895 | 2.064 | capacity_vs_valid_rows_conditional |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_kimi4_tp8_w4a8_c32 / source18c423c7 / GroupedMatmul / expert_down | 660 | 0 | 660 | 0 | 0 |
| a3_kimi4_tp8_w4a8_c32 / source18c423c7 / GroupedMatmul / expert_up | 660 | 0 | 660 | 0 | 0 |
