# Complete Decode Body Operator Families

Only complete events inside the 152 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-source-symmetric | 16 / 16 | 0 / 0 | 16 / 16 | 77064 / 265115 | 0 |

## a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-source-symmetric

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MoeDistributeDispatchV3 / expert_dispatch_native | 6080 | 0 / 6080 | 45.332 | 33.641 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 6080 | 0 / 6080 | 38.592 | 38.458 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| GroupedMatmul / expert_down | 6080 | 0 / 6080 | 23.639 | 23.543 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| QuantBatchMatmulV3 / grouped_output_b | 6080 | 6080 / 0 | 19.567 | 19.561 | 16.049 | -3.518 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 6080 | 0 / 6080 | 18.924 | 18.895 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 6080 | 6080 / 0 | 16.130 | 15.983 | 10.513 | -5.617 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| InplacePartialRotaryMul / unresolved | 20672 | 0 / 20672 | 4.042 | 4.585 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 7600 | 0 / 7600 | 9.697 | 9.728 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 6080 | 6080 / 0 | 11.347 | 11.302 | 10.061 | -1.286 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeDistributeCombineV3 / expert_combine_native | 6080 | 0 / 6080 | 11.198 | 11.141 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 6080 | 0 / 6080 | 10.636 | 10.582 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 6080 | 0 / 6080 | 10.537 | 10.441 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 6080 | 0 / 6080 | 9.584 | 9.595 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwigluGroupQuant / unresolved | 12160 | 0 / 12160 | 3.724 | 3.514 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 6080 | 6080 / 0 | 7.015 | 6.964 | 4.573 | -2.442 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_a | 6080 | 6080 / 0 | 5.798 | 5.732 | 5.051 | -0.747 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 6384 | 0 / 6384 | 4.619 | 4.606 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 6080 | 6080 / 0 | 4.804 | 4.782 | 5.051 | 0.246 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 13072 | 0 / 13072 | 2.200 | 2.203 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 6080 | 0 / 6080 | 4.103 | 4.093 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 6080 | 0 / 6080 | 4.096 | 4.055 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 6080 | 0 / 6080 | 4.044 | 4.087 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 6080 | 6080 / 0 | 4.014 | 4.015 | 1.312 | -2.702 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_a.quantize | 6080 | 6080 / 0 | 3.913 | 3.897 | 1.312 | -2.601 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / grouped_output_b.quantize | 6080 | 6080 / 0 | 3.773 | 3.770 | 1.312 | -2.461 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopKHash / unresolved | 6080 | 0 / 6080 | 3.628 | 3.488 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 13984 | 0 / 13984 | 1.505 | 1.523 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvCompressEpilogV2 / unresolved | 6688 | 0 / 6688 | 3.104 | 2.626 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / q_b.quantize | 7296 | 7296 / 0 | 2.531 | 2.502 | 1.312 | -1.219 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / unresolved | 304 | 0 / 304 | 58.442 | 58.373 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 6080 | 6080 / 0 | 2.551 | 2.531 | 1.312 | -1.239 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 6080 | 6080 / 0 | 2.500 | 2.495 | 1.312 | -1.188 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _quantize_mxfp4_indexer_kernel / unresolved | 1216 | 0 / 1216 | 11.080 | 9.781 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 6080 | 0 / 6080 | 1.939 | 1.846 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 6384 | 0 / 6384 | 1.797 | 1.775 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _Z15metadata_kernel4Args_interface / unresolved | 912 | 0 / 912 | 12.423 | 13.425 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_weights | 1216 | 1216 / 0 | 9.247 | 9.134 | 2.581 | -6.667 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Neg / unresolved | 6080 | 0 / 6080 | 1.398 | 1.372 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 6080 | 0 / 6080 | 1.338 | 1.333 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantSparseLightningIndexer / unresolved | 608 | 0 / 608 | 11.918 | 11.918 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 1216 | 1216 / 0 | 5.247 | 5.225 | 1.578 | -3.669 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _prepare_indexer_indices_kernel / unresolved | 1216 | 0 / 1216 | 4.831 | 4.803 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantLightningIndexer / unresolved | 608 | 0 / 608 | 6.485 | 5.772 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _hash_ids_kernel / unresolved | 152 | 0 / 152 | 24.000 | 24.074 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1216 | 0 / 1216 | 2.709 | 2.679 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_mxfp4_indexer_cache_kernel / unresolved | 608 | 0 / 608 | 4.413 | 4.386 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_host_uva_gather_dequant_kernel / unresolved | 304 | 0 / 304 | 5.698 | 5.189 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_gate_kernel / unresolved | 304 | 0 / 304 | 5.517 | 5.505 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 456 | 0 / 456 | 2.813 | 2.792 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / compress_gates + compress_values | 152 | 152 / 0 | 8.096 | 8.091 | 10.088 | 1.992 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Range / unresolved | 152 | 0 / 152 | 7.489 | 8.537 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pool_kernel / unresolved | 456 | 0 / 456 | 1.761 | 1.744 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 152 | 0 / 152 | 5.064 | 5.041 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 304 | 304 / 0 | 2.338 | 2.342 | 1.312 | -1.026 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalOr / unresolved | 331 | 0 / 331 | 2.131 | 1.403 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _cache_update_kernel / unresolved | 456 | 0 / 456 | 1.508 | 1.489 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 152 | 0 / 152 | 2.678 | 2.616 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 152 | 0 / 152 | 2.208 | 2.062 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 152 | 0 / 152 | 2.095 | 2.052 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 6080 | 23.639 / 23.543 | 26.130 | 0.946 | 1.045 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 6080 | 38.592 / 38.458 | 55.882 | 1.544 | 2.235 | capacity_vs_valid_rows_conditional |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-source-symmetric / GroupedMatmul / expert_down | 6080 | 0 | 6080 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-source-symmetric / GroupedMatmul / expert_up | 6080 | 0 | 6080 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-source-symmetric / HcPre / attention.hc_pre | 6080 | 0 | 0 | 6080 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-source-symmetric / HcPre / ffn.hc_pre | 6080 | 0 | 0 | 6080 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-source-symmetric / MoeDistributeCombineV3 / expert_combine_native | 6080 | 0 | 0 | 6080 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-source-symmetric / MoeDistributeDispatchV3 / expert_dispatch_native | 6080 | 0 | 0 | 6080 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-source-symmetric / MqsmlaKernel___call__ / attention_core | 6080 | 0 | 0 | 6080 | 0 |
