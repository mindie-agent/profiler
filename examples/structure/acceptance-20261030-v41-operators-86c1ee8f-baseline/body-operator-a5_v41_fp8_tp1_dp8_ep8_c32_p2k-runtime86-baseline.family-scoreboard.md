# Complete Decode Body Operator Families

Only complete events inside the 105 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline | 18 / 18 | 0 / 0 | 18 / 18 | 61635 / 183011 | 0 |

## a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4200 | 0 / 4200 | 127.406 | 126.789 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| GroupedMatmul / expert_down | 4200 | 0 / 4200 | 65.238 | 64.668 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| MqsmlaKernel___call__ / attention_core | 4200 | 0 / 4200 | 30.251 | 30.550 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| QuantBatchMatmulV3 / grouped_output_b | 4200 | 4200 / 0 | 20.138 | 20.121 | 16.254 | -3.884 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 4200 | 0 / 4200 | 20.003 | 19.975 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4200 | 0 / 4200 | 18.548 | 17.867 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 4200 | 4200 / 0 | 16.397 | 16.233 | 10.563 | -5.834 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| InplacePartialRotaryMul / unresolved | 14280 | 0 / 14280 | 4.364 | 4.761 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 5250 | 0 / 5250 | 10.241 | 10.146 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 4200 | 0 / 4200 | 12.381 | 12.229 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 4200 | 4200 / 0 | 11.617 | 11.578 | 10.194 | -1.423 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPre / attention.hc_pre | 4200 | 0 / 4200 | 11.294 | 11.107 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| HcPre / ffn.hc_pre | 4200 | 0 / 4200 | 11.183 | 11.022 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| SwigluGroupQuant / unresolved | 8400 | 0 / 8400 | 3.996 | 4.091 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 4200 | 4200 / 0 | 7.171 | 7.115 | 4.640 | -2.531 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_a | 4200 | 4200 / 0 | 5.841 | 5.804 | 5.177 | -0.664 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 9030 | 0 / 9030 | 2.562 | 2.548 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvCompressEpilogV2 / unresolved | 4620 | 0 / 4620 | 4.547 | 4.446 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 4410 | 0 / 4410 | 4.722 | 4.671 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 4200 | 4200 / 0 | 4.875 | 4.861 | 5.177 | 0.302 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 4200 | 0 / 4200 | 4.521 | 4.472 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 4200 | 4200 / 0 | 4.502 | 4.468 | 1.312 | -3.190 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 4200 | 4200 / 0 | 4.499 | 4.481 | 1.312 | -3.187 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_b.quantize | 5040 | 5040 / 0 | 3.685 | 3.641 | 1.312 | -2.373 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopKHash / unresolved | 4200 | 0 / 4200 | 4.176 | 4.022 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / grouped_output_b.quantize | 4200 | 4200 / 0 | 4.125 | 4.108 | 1.312 | -2.813 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 4200 | 4200 / 0 | 3.954 | 3.911 | 1.312 | -2.642 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_a.quantize | 4200 | 4200 / 0 | 3.875 | 3.854 | 1.312 | -2.563 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 9555 | 0 / 9555 | 1.623 | 1.688 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 210 | 0 / 210 | 58.925 | 58.899 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 4200 | 4200 / 0 | 2.848 | 2.820 | 1.312 | -1.536 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 4200 | 4200 / 0 | 2.788 | 2.782 | 1.312 | -1.476 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _quantize_mxfp4_indexer_kernel / unresolved | 840 | 0 / 840 | 13.728 | 12.554 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _Z15metadata_kernel4Args_interface / unresolved | 626 | 0 / 626 | 15.767 | 15.418 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_weights | 840 | 840 / 0 | 10.851 | 10.798 | 2.818 | -8.033 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SelectV2 / unresolved | 4200 | 0 / 4200 | 2.129 | 1.836 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 4410 | 0 / 4410 | 1.817 | 1.723 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Neg / unresolved | 4200 | 0 / 4200 | 1.513 | 1.439 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantSparseLightningIndexer / unresolved | 420 | 0 / 420 | 14.789 | 14.617 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 4200 | 0 / 4200 | 1.429 | 1.378 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantLightningIndexer / unresolved | 420 | 0 / 420 | 12.644 | 10.309 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_indexer_indices_kernel / unresolved | 840 | 0 / 840 | 5.579 | 5.588 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 840 | 840 / 0 | 5.333 | 5.307 | 1.578 | -3.755 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _hash_ids_kernel / unresolved | 105 | 0 / 105 | 21.976 | 21.930 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 840 | 0 / 840 | 2.689 | 2.655 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_mxfp4_indexer_cache_kernel / unresolved | 420 | 0 / 420 | 4.852 | 4.832 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_host_uva_gather_dequant_kernel / unresolved | 210 | 0 / 210 | 9.438 | 9.271 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_gate_kernel / unresolved | 210 | 0 / 210 | 5.808 | 5.793 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalOr / unresolved | 210 | 0 / 210 | 5.362 | 4.657 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 210 | 210 / 0 | 5.135 | 4.992 | 1.312 | -3.823 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _pool_kernel / unresolved | 315 | 0 / 315 | 3.288 | 2.519 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _cache_update_kernel / unresolved | 315 | 0 / 315 | 3.143 | 3.125 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / compress_gates + compress_values | 105 | 105 / 0 | 8.554 | 8.556 | 10.332 | 1.778 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 315 | 0 / 315 | 2.769 | 2.830 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 210 | 0 / 210 | 3.550 | 3.474 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 105 | 0 / 105 | 6.267 | 6.113 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 105 | 0 / 105 | 2.462 | 2.447 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 105 | 0 / 105 | 2.222 | 2.254 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 4200 | 65.238 / 64.668 | 44.275 | 2.610 | 1.771 | capacity_vs_valid_rows_conditional |
| GroupedMatmul / expert_up / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 4200 | 127.406 / 126.789 | 86.330 | 5.096 | 3.453 | capacity_vs_valid_rows_conditional |
| HcPre / attention.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 4200 | 11.294 / 11.107 | 19.016 | 0.452 | 0.761 | partial_base_program_reference_premix_branch_unresolved |
| HcPre / ffn.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 4200 | 11.183 / 11.022 | 19.016 | 0.447 | 0.761 | partial_base_program_reference_premix_branch_unresolved |
| MqsmlaKernel___call__ / attention_core / layers 0, 1 | 210 | 13.400 / 12.342 | 6.312 | 0.027 | 0.013 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1890 | 30.876 / 30.200 | 6.312 | 0.556 | 0.114 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 2100 | 31.372 / 30.919 | 6.312 | 0.627 | 0.126 | source_symbol_to_declared_attention_program |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / GroupedMatmul / expert_down | 4200 | 0 | 4200 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / GroupedMatmul / expert_up | 4200 | 0 | 4200 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / HcPre / attention.hc_pre | 4200 | 0 | 4200 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / HcPre / ffn.hc_pre | 4200 | 0 | 4200 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / MoeDistributeCombineV3 / expert_combine_native | 4200 | 0 | 0 | 4200 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / MoeDistributeDispatchV3 / expert_dispatch_native | 4200 | 0 | 0 | 4200 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / MqsmlaKernel___call__ / attention_core | 4200 | 0 | 4200 | 0 | 0 |
