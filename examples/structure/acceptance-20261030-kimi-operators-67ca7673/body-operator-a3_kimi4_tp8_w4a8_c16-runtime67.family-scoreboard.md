# Complete Decode Body Operator Families

Only complete events inside the 235 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_kimi4_tp8_w4a8_c16 / runtime67 | 18 / 18 | 0 / 1 | 18 / 19 | 8695 / 39245 | 0 |

## a3_kimi4_tp8_w4a8_c16 / runtime67

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| reduce_scatterAicpuKernel / unresolved | 1880 | 0 / 1880 | 170.781 | 163.357 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 705 | 0 / 705 | 324.459 | 322.654 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 705 | 0 / 705 | 168.962 | 167.496 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 940 | 0 / 940 | 106.632 | 73.478 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| DequantSituQuant / unresolved | 1410 | 0 / 1410 | 44.784 | 44.440 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 1175 | 0 / 1175 | 42.097 | 26.339 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MatMulV2 / unresolved | 705 | 0 / 705 | 61.218 | 64.858 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1645 | 0 / 1645 | 26.027 | 23.819 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 705 | 0 / 705 | 59.769 | 58.419 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV2 / unresolved | 705 | 0 / 705 | 57.680 | 57.359 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 235 | 0 / 235 | 159.143 | 159.077 | 5.000 | -154.143 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MatMulV2 / linear_output | 705 | 705 / 0 | 32.512 | 33.759 | 25.868 | -6.644 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_reduceScatter_ / ffn_down_communication | 940 | 0 / 940 | 24.204 | 18.400 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV2 / unresolved | 705 | 0 / 705 | 31.810 | 31.999 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AttnResFwd / unresolved | 2115 | 0 / 2115 | 10.055 | 10.219 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / latent_down | 705 | 705 / 0 | 29.484 | 29.399 | 35.241 | 5.757 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_reduceScatter_ / attention_output_communication | 940 | 0 / 940 | 21.866 | 17.340 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| QuantBatchMatmulV3 / latent_up | 705 | 705 / 0 | 28.424 | 28.400 | 26.786 | -1.638 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / unresolved | 705 | 0 / 705 | 25.383 | 25.380 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 235 | 235 / 0 | 55.989 | 55.959 | 74.718 | 18.729 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / unresolved | 705 | 0 / 705 | 17.706 | 17.519 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 705 | 0 / 705 | 17.248 | 17.220 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 705 | 705 / 0 | 13.278 | 13.279 | 6.961 | -6.318 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 235 | 235 / 0 | 35.416 | 35.379 | 35.237 | -0.179 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / output_gate | 235 | 235 / 0 | 31.337 | 31.359 | 39.352 | 8.016 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 2350 | 0 / 2350 | 3.059 | 2.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output | 235 | 235 / 0 | 28.446 | 28.619 | 25.868 | -2.578 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 1175 | 0 / 1175 | 5.130 | 6.240 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 470 | 0 / 470 | 12.608 | 12.389 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 940 | 0 / 940 | 5.887 | 5.700 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 705 | 0 / 705 | 7.316 | 7.400 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 1410 | 0 / 1410 | 3.401 | 2.100 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Transpose / unresolved | 235 | 0 / 235 | 20.407 | 19.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AsStrided / unresolved | 940 | 0 / 940 | 4.577 | 4.470 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1175 | 0 / 1175 | 3.551 | 2.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 705 | 0 / 705 | 5.502 | 5.700 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / shared.gate_up.quantize | 705 | 705 / 0 | 5.308 | 5.300 | 2.500 | -2.808 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / linear_q.quantize | 705 | 705 / 0 | 5.025 | 5.120 | 2.500 | -2.525 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 470 | 0 / 470 | 7.485 | 7.500 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 235 | 0 / 235 | 14.727 | 14.460 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MemSet / unresolved | 470 | 0 / 470 | 7.158 | 7.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / latent_norm | 705 | 705 / 0 | 4.575 | 4.880 | 2.500 | -2.075 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeBatchMatMul / v_expand | 235 | 235 / 0 | 13.460 | 13.420 | 5.000 | -8.460 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_b | 235 | 235 / 0 | 12.942 | 12.920 | 5.000 | -7.942 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Tanh / unresolved | 470 | 0 / 470 | 5.961 | 6.050 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RealDiv / unresolved | 470 | 0 / 470 | 5.960 | 6.150 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_down.quantize | 705 | 705 / 0 | 3.967 | 3.900 | 2.500 | -1.467 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| BatchMatMulV2 / unresolved | 235 | 0 / 235 | 8.370 | 8.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_up.quantize | 705 | 705 / 0 | 2.592 | 2.580 | 2.500 | -0.092 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| IndexCheck / unresolved | 235 | 0 / 235 | 5.547 | 5.520 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 235 | 235 / 0 | 5.280 | 5.280 | 2.500 | -2.780 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / q_b.quantize | 235 | 235 / 0 | 5.267 | 5.260 | 2.500 | -2.767 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / unresolved | 235 | 0 / 235 | 5.110 | 5.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_a.quantize | 235 | 235 / 0 | 5.051 | 5.040 | 2.500 | -2.551 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / down.quantize | 235 | 235 / 0 | 4.547 | 4.480 | 2.500 | -2.047 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_kimi4_tp8_w4a8_c16 / runtime67 / GroupedMatmul / expert_down | 705 | 0 | 0 | 705 | 0 |
| a3_kimi4_tp8_w4a8_c16 / runtime67 / GroupedMatmul / expert_up | 705 | 0 | 0 | 705 | 0 |
