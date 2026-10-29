# Complete Decode Body Operator Families

Only complete events inside the 196 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_kimi4_tp8_w4a8_c64 / runtime67 | 17 / 17 | 1 / 2 | 18 / 19 | 7252 / 32928 | 0 |

## a3_kimi4_tp8_w4a8_c64 / runtime67

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 588 | 0 / 588 | 1095.630 | 1098.018 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 588 | 0 / 588 | 520.577 | 518.519 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| reduce_scatterAicpuKernel / unresolved | 1568 | 0 / 1568 | 175.316 | 164.387 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSituQuant / unresolved | 1176 | 0 / 1176 | 140.007 | 139.498 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 588 | 0 / 588 | 176.676 | 178.777 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 196 | 0 / 196 | 505.614 | 505.810 | 5.000 | -500.614 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MatMulV2 / unresolved | 588 | 0 / 588 | 90.415 | 93.658 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 784 | 0 / 784 | 61.707 | 30.479 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| QuantBatchMatmulV3 / unresolved | 1372 | 0 / 1372 | 27.366 | 22.599 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV2 / unresolved | 588 | 0 / 588 | 62.546 | 62.579 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 980 | 0 / 980 | 30.708 | 28.890 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MatMulV2 / linear_output | 588 | 588 / 0 | 40.050 | 38.039 | 35.050 | -5.000 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_reduceScatter_ / ffn_down_communication | 784 | 0 / 784 | 28.643 | 27.200 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| AttnResFwd / unresolved | 1764 | 0 / 1764 | 11.494 | 11.680 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 784 | 0 / 784 | 25.830 | 23.400 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeDistributeCombineV2 / unresolved | 588 | 0 / 588 | 33.945 | 32.569 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / latent_down | 588 | 588 / 0 | 30.103 | 29.879 | 36.164 | 6.061 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / unresolved | 588 | 0 / 588 | 29.315 | 28.800 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 588 | 0 / 588 | 29.132 | 32.099 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / latent_up | 588 | 588 / 0 | 27.905 | 27.840 | 28.164 | 0.259 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / gate_up | 196 | 196 / 0 | 60.636 | 60.639 | 89.300 | 28.664 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 588 | 0 / 588 | 18.571 | 17.230 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output_gate | 196 | 196 / 0 | 51.145 | 51.199 | 52.683 | 1.538 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 588 | 588 / 0 | 16.957 | 16.940 | 10.301 | -6.656 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 196 | 196 / 0 | 40.148 | 40.039 | 48.003 | 7.855 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 980 | 0 / 980 | 6.952 | 6.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 784 | 0 / 784 | 8.624 | 8.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / shared.gate_up.quantize | 588 | 588 / 0 | 11.055 | 10.280 | 2.500 | -8.555 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 1960 | 0 / 1960 | 3.232 | 3.220 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 392 | 0 / 392 | 15.684 | 15.799 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 588 | 0 / 588 | 9.717 | 9.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / linear_q.quantize | 588 | 588 / 0 | 9.091 | 9.500 | 2.500 | -6.591 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / output | 196 | 196 / 0 | 26.683 | 26.659 | 35.050 | 8.367 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AsStrided / unresolved | 784 | 0 / 784 | 6.382 | 6.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 196 | 0 / 196 | 24.884 | 24.770 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 1176 | 0 / 1176 | 3.720 | 2.550 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 980 | 0 / 980 | 4.140 | 1.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 392 | 0 / 392 | 10.323 | 10.460 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 588 | 0 / 588 | 6.559 | 6.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 196 | 196 / 0 | 16.602 | 16.589 | 5.000 | -11.602 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / latent_norm | 588 | 588 / 0 | 5.530 | 5.739 | 2.500 | -3.030 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Tanh / unresolved | 392 | 0 / 392 | 7.806 | 7.900 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MemSet / unresolved | 392 | 0 / 392 | 7.343 | 7.300 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_down.quantize | 588 | 588 / 0 | 4.676 | 4.700 | 2.500 | -2.176 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_b | 196 | 196 / 0 | 13.983 | 13.999 | 6.351 | -7.631 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RealDiv / unresolved | 392 | 0 / 392 | 6.384 | 6.420 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| IndexCheck / unresolved | 196 | 0 / 196 | 12.764 | 12.680 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / latent_up.quantize | 588 | 588 / 0 | 3.556 | 3.540 | 2.500 | -1.056 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / gate_up.quantize | 196 | 196 / 0 | 10.314 | 10.300 | 2.500 | -7.814 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Transpose / unresolved | 196 | 0 / 196 | 9.704 | 9.690 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_a.quantize | 196 | 196 / 0 | 9.551 | 9.540 | 2.500 | -7.051 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / unresolved | 196 | 0 / 196 | 9.477 | 9.450 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BatchMatMulV2 / unresolved | 196 | 0 / 196 | 9.024 | 9.000 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 196 | 0 / 196 | 8.424 | 8.440 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / down.quantize | 196 | 196 / 0 | 6.544 | 6.540 | 2.500 | -4.044 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / q_b.quantize | 196 | 196 / 0 | 4.646 | 4.620 | 2.500 | -2.146 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_kimi4_tp8_w4a8_c64 / runtime67 / GroupedMatmul / expert_down | 588 | 0 | 0 | 588 | 0 |
| a3_kimi4_tp8_w4a8_c64 / runtime67 / GroupedMatmul / expert_up | 588 | 0 | 0 | 588 | 0 |
