# Complete Decode Body Operator Families

Only complete events inside the 757 accepted target-body windows from 6 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs | 18 / 18 | 0 / 0 | 18 / 18 | 75723 / 224840 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs | 18 / 18 | 0 / 0 | 18 / 18 | 61635 / 183011 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs | 18 / 18 | 0 / 0 | 18 / 18 | 88637 / 263341 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs | 18 / 18 | 0 / 0 | 18 / 18 | 85115 / 252886 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs | 18 / 18 | 0 / 0 | 18 / 18 | 44025 / 130725 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs | 18 / 18 | 0 / 0 | 18 / 18 | 89224 / 265115 | 0 |

## a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 5160 | 0 / 5160 | 68.076 | 67.778 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 5160 | 0 / 5160 | 37.439 | 37.167 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 5160 | 0 / 5160 | 28.836 | 29.341 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| QuantBatchMatmulV3 / grouped_output_b | 5160 | 5160 / 0 | 19.815 | 19.807 | 16.117 | -3.697 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 5160 | 0 / 5160 | 19.389 | 19.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 5160 | 0 / 5160 | 17.898 | 17.041 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 5160 | 5160 / 0 | 16.232 | 16.091 | 10.529 | -5.703 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| InplacePartialRotaryMul / unresolved | 17544 | 0 / 17544 | 4.264 | 4.725 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 6450 | 0 / 6450 | 9.873 | 9.890 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 5160 | 0 / 5160 | 11.978 | 11.948 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MoeDistributeCombineV3 / expert_combine_native | 5160 | 0 / 5160 | 11.810 | 11.729 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 5160 | 0 / 5160 | 11.736 | 11.691 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| QuantBatchMatmulV3 / shared.gate_up | 5160 | 5160 / 0 | 11.475 | 11.424 | 10.105 | -1.370 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SwigluGroupQuant / unresolved | 10320 | 0 / 10320 | 3.928 | 3.892 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 5160 | 5160 / 0 | 7.077 | 7.016 | 4.595 | -2.482 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_a | 5160 | 5160 / 0 | 5.755 | 5.707 | 2.122 | -3.634 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 11094 | 0 / 11094 | 2.352 | 2.335 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 5418 | 0 / 5418 | 4.648 | 4.607 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 5160 | 5160 / 0 | 4.768 | 4.754 | 1.578 | -3.190 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / grouped_output_b.quantize | 5160 | 5160 / 0 | 4.598 | 4.583 | 1.312 | -3.286 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| KvCompressEpilogV2 / unresolved | 5676 | 0 / 5676 | 4.120 | 3.936 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / q_a.quantize | 5160 | 5160 / 0 | 4.376 | 4.361 | 1.312 | -3.064 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 5160 | 5160 / 0 | 4.366 | 4.348 | 1.312 | -3.054 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / attention.hc_post_group | 5160 | 5160 / 0 | 4.289 | 4.266 | 1.312 | -2.977 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 5160 | 0 / 5160 | 4.287 | 4.175 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 5160 | 5160 / 0 | 4.162 | 4.138 | 1.312 | -2.850 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopKHash / unresolved | 5160 | 0 / 5160 | 3.873 | 3.630 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / q_b.quantize | 6192 | 6192 / 0 | 3.062 | 3.022 | 1.312 | -1.750 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 11739 | 0 / 11739 | 1.516 | 1.524 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 258 | 0 / 258 | 58.751 | 58.719 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 5160 | 5160 / 0 | 2.742 | 2.750 | 1.312 | -1.430 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 5160 | 5160 / 0 | 2.718 | 2.745 | 1.312 | -1.406 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _quantize_mxfp4_indexer_kernel / unresolved | 1032 | 0 / 1032 | 11.389 | 10.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_weights | 1032 | 1032 / 0 | 10.825 | 10.723 | 1.578 | -9.247 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _Z15metadata_kernel4Args_interface / unresolved | 766 | 0 / 766 | 13.711 | 14.030 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 5160 | 0 / 5160 | 1.936 | 1.774 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 5418 | 0 / 5418 | 1.754 | 1.697 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Neg / unresolved | 5160 | 0 / 5160 | 1.474 | 1.403 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 5160 | 0 / 5160 | 1.364 | 1.347 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantSparseLightningIndexer / unresolved | 516 | 0 / 516 | 13.446 | 13.412 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantLightningIndexer / unresolved | 516 | 0 / 516 | 12.304 | 9.871 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_indexer_indices_kernel / unresolved | 1032 | 0 / 1032 | 5.297 | 5.290 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 1032 | 1032 / 0 | 5.284 | 5.237 | 1.578 | -3.706 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _hash_ids_kernel / unresolved | 129 | 0 / 129 | 22.170 | 22.239 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1032 | 0 / 1032 | 2.693 | 2.655 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_mxfp4_indexer_cache_kernel / unresolved | 516 | 0 / 516 | 4.761 | 4.749 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_host_uva_gather_dequant_kernel / unresolved | 258 | 0 / 258 | 7.542 | 7.209 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_gate_kernel / unresolved | 258 | 0 / 258 | 5.667 | 5.657 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalOr / unresolved | 258 | 0 / 258 | 5.440 | 1.878 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pool_kernel / unresolved | 387 | 0 / 387 | 3.059 | 2.182 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _cache_update_kernel / unresolved | 387 | 0 / 387 | 2.981 | 2.913 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 258 | 258 / 0 | 4.436 | 5.199 | 1.312 | -3.124 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / compress_gates + compress_values | 129 | 129 / 0 | 8.275 | 8.273 | 1.578 | -6.697 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 387 | 0 / 387 | 2.624 | 2.535 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 129 | 0 / 129 | 6.105 | 6.014 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 258 | 0 / 258 | 2.861 | 2.661 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 129 | 0 / 129 | 2.377 | 2.351 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 129 | 0 / 129 | 2.176 | 2.116 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 1 | 0 / 1 | 11.728 | 11.728 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 5160 | 11.736 / 11.691 | 17.763 | 0.469 | 0.711 | partial_base_program_reference_premix_branch_unresolved |
| HcPre / ffn.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 5160 | 11.978 / 11.948 | 17.763 | 0.479 | 0.711 | partial_base_program_reference_premix_branch_unresolved |
| MqsmlaKernel___call__ / attention_core / layers 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 2580 | 29.623 / 29.503 | 3.156 | 0.592 | 0.063 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 2322 | 29.915 / 29.194 | 3.156 | 0.538 | 0.057 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 0, 1 | 258 | 11.257 / 11.309 | 3.156 | 0.023 | 0.006 | source_symbol_to_declared_attention_program |

## a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4200 | 0 / 4200 | 127.406 | 126.789 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 4200 | 0 / 4200 | 65.238 | 64.668 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
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
| QuantBatchMatmulV3 / q_a | 4200 | 4200 / 0 | 5.841 | 5.804 | 2.365 | -3.476 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 9030 | 0 / 9030 | 2.562 | 2.548 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvCompressEpilogV2 / unresolved | 4620 | 0 / 4620 | 4.547 | 4.446 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 4410 | 0 / 4410 | 4.722 | 4.671 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 4200 | 4200 / 0 | 4.875 | 4.861 | 1.578 | -3.297 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| MatMulV3 / index_weights | 840 | 840 / 0 | 10.851 | 10.798 | 1.578 | -9.273 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| MatMulV3 / compress_gates + compress_values | 105 | 105 / 0 | 8.554 | 8.556 | 1.578 | -6.976 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 315 | 0 / 315 | 2.769 | 2.830 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 210 | 0 / 210 | 3.550 | 3.474 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 105 | 0 / 105 | 6.267 | 6.113 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 105 | 0 / 105 | 2.462 | 2.447 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 105 | 0 / 105 | 2.222 | 2.254 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 4200 | 11.294 / 11.107 | 19.016 | 0.452 | 0.761 | partial_base_program_reference_premix_branch_unresolved |
| HcPre / ffn.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 4200 | 11.183 / 11.022 | 19.016 | 0.447 | 0.761 | partial_base_program_reference_premix_branch_unresolved |
| MqsmlaKernel___call__ / attention_core / layers 0, 1 | 210 | 13.400 / 12.342 | 6.312 | 0.027 | 0.013 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1890 | 30.876 / 30.200 | 6.312 | 0.556 | 0.114 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 2100 | 31.372 / 30.919 | 6.312 | 0.627 | 0.126 | source_symbol_to_declared_attention_program |

## a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MoeDistributeDispatchV3 / expert_dispatch_native | 6040 | 0 / 6040 | 47.766 | 35.270 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 6040 | 0 / 6040 | 38.809 | 38.660 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 6040 | 0 / 6040 | 23.604 | 23.476 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / grouped_output_b | 6040 | 6040 / 0 | 19.568 | 19.564 | 16.049 | -3.518 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 6040 | 0 / 6040 | 18.932 | 18.897 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 6040 | 6040 / 0 | 16.163 | 16.012 | 10.513 | -5.650 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| InplacePartialRotaryMul / unresolved | 20536 | 0 / 20536 | 4.029 | 4.579 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 7550 | 0 / 7550 | 9.682 | 9.753 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 6040 | 6040 / 0 | 11.361 | 11.319 | 10.061 | -1.300 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeDistributeCombineV3 / expert_combine_native | 6040 | 0 / 6040 | 11.254 | 11.175 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 6040 | 0 / 6040 | 10.687 | 10.633 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| HcPre / attention.hc_pre | 6040 | 0 / 6040 | 10.593 | 10.482 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MqsmlaKernel___call__ / attention_core | 6040 | 0 / 6040 | 9.466 | 9.499 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| SwigluGroupQuant / unresolved | 12080 | 0 / 12080 | 3.723 | 3.595 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 6040 | 6040 / 0 | 6.977 | 6.922 | 4.573 | -2.405 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_a | 6040 | 6040 / 0 | 5.795 | 5.720 | 2.000 | -3.795 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 6342 | 0 / 6342 | 4.602 | 4.584 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 6040 | 6040 / 0 | 4.818 | 4.794 | 1.578 | -3.240 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 12986 | 0 / 12986 | 2.186 | 2.197 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 6040 | 6040 / 0 | 4.232 | 4.263 | 1.312 | -2.920 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 6040 | 0 / 6040 | 4.101 | 4.064 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 6040 | 6040 / 0 | 4.071 | 4.093 | 1.312 | -2.759 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 6040 | 6040 / 0 | 3.974 | 3.969 | 1.312 | -2.662 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_a.quantize | 6040 | 6040 / 0 | 3.892 | 3.881 | 1.312 | -2.580 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / grouped_output_b.quantize | 6040 | 6040 / 0 | 3.805 | 3.795 | 1.312 | -2.493 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopKHash / unresolved | 6040 | 0 / 6040 | 3.615 | 3.469 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 13892 | 0 / 13892 | 1.497 | 1.508 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvCompressEpilogV2 / unresolved | 6644 | 0 / 6644 | 3.085 | 2.614 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / q_b.quantize | 7248 | 7248 / 0 | 2.519 | 2.488 | 1.312 | -1.207 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / unresolved | 302 | 0 / 302 | 58.422 | 58.406 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 6040 | 6040 / 0 | 2.525 | 2.511 | 1.312 | -1.213 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 6040 | 6040 / 0 | 2.485 | 2.482 | 1.312 | -1.173 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _quantize_mxfp4_indexer_kernel / unresolved | 1208 | 0 / 1208 | 11.022 | 9.968 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 6040 | 0 / 6040 | 1.944 | 1.844 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 6342 | 0 / 6342 | 1.794 | 1.787 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _Z15metadata_kernel4Args_interface / unresolved | 906 | 0 / 906 | 12.421 | 13.329 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_weights | 1208 | 1208 / 0 | 9.203 | 9.113 | 1.578 | -7.625 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Neg / unresolved | 6040 | 0 / 6040 | 1.396 | 1.337 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 6040 | 0 / 6040 | 1.340 | 1.327 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantSparseLightningIndexer / unresolved | 604 | 0 / 604 | 11.455 | 11.450 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 1208 | 1208 / 0 | 5.222 | 5.194 | 1.578 | -3.644 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _prepare_indexer_indices_kernel / unresolved | 1208 | 0 / 1208 | 4.898 | 4.877 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantLightningIndexer / unresolved | 604 | 0 / 604 | 6.237 | 5.448 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _hash_ids_kernel / unresolved | 151 | 0 / 151 | 23.539 | 23.447 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1208 | 0 / 1208 | 2.681 | 2.654 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_mxfp4_indexer_cache_kernel / unresolved | 604 | 0 / 604 | 4.397 | 4.378 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_host_uva_gather_dequant_kernel / unresolved | 302 | 0 / 302 | 5.956 | 5.393 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_gate_kernel / unresolved | 302 | 0 / 302 | 5.491 | 5.473 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 148 | 0 / 148 | 9.301 | 9.222 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / compress_gates + compress_values | 151 | 151 / 0 | 8.148 | 8.050 | 1.578 | -6.570 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 453 | 0 / 453 | 2.504 | 2.478 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pool_kernel / unresolved | 453 | 0 / 453 | 1.831 | 1.792 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 151 | 0 / 151 | 5.225 | 5.192 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 302 | 302 / 0 | 2.210 | 2.229 | 1.312 | -0.898 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _cache_update_kernel / unresolved | 453 | 0 / 453 | 1.388 | 1.370 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalOr / unresolved | 302 | 0 / 302 | 1.376 | 1.346 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 151 | 0 / 151 | 2.511 | 2.473 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 151 | 0 / 151 | 2.206 | 2.171 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 151 | 0 / 151 | 1.985 | 1.963 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 6040 | 10.593 / 10.482 | 17.136 | 0.424 | 0.685 | partial_base_program_reference_premix_branch_unresolved |
| HcPre / ffn.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 6040 | 10.687 / 10.633 | 17.136 | 0.427 | 0.685 | partial_base_program_reference_premix_branch_unresolved |
| MqsmlaKernel___call__ / attention_core / layers 0, 1 | 302 | 7.891 / 7.845 | 1.578 | 0.016 | 0.003 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 3020 | 9.938 / 9.948 | 1.578 | 0.199 | 0.032 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 2718 | 9.116 / 9.153 | 1.578 | 0.164 | 0.028 | source_symbol_to_declared_attention_program |

## a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 5800 | 0 / 5800 | 38.541 | 38.378 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 5800 | 0 / 5800 | 29.449 | 16.841 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 5800 | 0 / 5800 | 28.248 | 28.863 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| GroupedMatmul / expert_down | 5800 | 0 / 5800 | 23.656 | 23.572 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / grouped_output_b | 5800 | 5800 / 0 | 19.567 | 19.558 | 16.049 | -3.518 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 5800 | 0 / 5800 | 18.967 | 18.925 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 5800 | 5800 / 0 | 16.144 | 15.990 | 10.513 | -5.631 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| InplacePartialRotaryMul / unresolved | 19720 | 0 / 19720 | 4.052 | 4.601 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 7250 | 0 / 7250 | 9.702 | 9.730 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 5800 | 5800 / 0 | 11.338 | 11.295 | 10.061 | -1.277 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeDistributeCombineV3 / expert_combine_native | 5800 | 0 / 5800 | 11.209 | 11.140 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 5800 | 0 / 5800 | 10.636 | 10.586 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| HcPre / attention.hc_pre | 5800 | 0 / 5800 | 10.538 | 10.438 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| SwigluGroupQuant / unresolved | 11600 | 0 / 11600 | 3.730 | 3.674 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 5800 | 5800 / 0 | 7.012 | 6.955 | 4.573 | -2.440 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_a | 5800 | 5800 / 0 | 5.799 | 5.732 | 2.000 | -3.799 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 6090 | 0 / 6090 | 4.622 | 4.606 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvCompressEpilogV2 / unresolved | 6380 | 0 / 6380 | 4.375 | 3.779 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 5800 | 5800 / 0 | 4.800 | 4.779 | 1.578 | -3.222 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 12470 | 0 / 12470 | 2.198 | 2.203 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 5800 | 0 / 5800 | 4.102 | 4.062 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 5800 | 5800 / 0 | 4.100 | 4.074 | 1.312 | -2.788 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 5800 | 5800 / 0 | 4.044 | 4.084 | 1.312 | -2.732 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 5800 | 5800 / 0 | 4.011 | 4.013 | 1.312 | -2.699 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_a.quantize | 5800 | 5800 / 0 | 3.913 | 3.893 | 1.312 | -2.601 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / grouped_output_b.quantize | 5800 | 5800 / 0 | 3.775 | 3.773 | 1.312 | -2.463 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopKHash / unresolved | 5800 | 0 / 5800 | 3.613 | 3.492 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 13340 | 0 / 13340 | 1.526 | 1.536 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / q_b.quantize | 6960 | 6960 / 0 | 2.530 | 2.501 | 1.312 | -1.218 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / unresolved | 290 | 0 / 290 | 58.424 | 58.413 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 5800 | 5800 / 0 | 2.553 | 2.533 | 1.312 | -1.241 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 5800 | 5800 / 0 | 2.506 | 2.499 | 1.312 | -1.194 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _quantize_mxfp4_indexer_kernel / unresolved | 1160 | 0 / 1160 | 11.054 | 9.866 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 5800 | 0 / 5800 | 1.951 | 1.848 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _Z15metadata_kernel4Args_interface / unresolved | 870 | 0 / 870 | 12.769 | 13.587 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 6090 | 0 / 6090 | 1.798 | 1.776 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_weights | 1160 | 1160 / 0 | 9.290 | 9.185 | 1.578 | -7.712 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Neg / unresolved | 5800 | 0 / 5800 | 1.397 | 1.374 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantSparseLightningIndexer / unresolved | 580 | 0 / 580 | 13.869 | 13.876 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 5800 | 0 / 5800 | 1.340 | 1.333 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantLightningIndexer / unresolved | 580 | 0 / 580 | 11.915 | 9.710 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 1160 | 1160 / 0 | 5.238 | 5.216 | 1.578 | -3.660 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _prepare_indexer_indices_kernel / unresolved | 1160 | 0 / 1160 | 4.996 | 4.998 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _hash_ids_kernel / unresolved | 145 | 0 / 145 | 25.234 | 25.314 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1160 | 0 / 1160 | 2.711 | 2.678 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_mxfp4_indexer_cache_kernel / unresolved | 580 | 0 / 580 | 4.523 | 4.494 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_host_uva_gather_dequant_kernel / unresolved | 290 | 0 / 290 | 5.984 | 5.904 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_gate_kernel / unresolved | 290 | 0 / 290 | 5.527 | 5.510 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pool_kernel / unresolved | 435 | 0 / 435 | 3.118 | 4.315 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 145 | 0 / 145 | 8.916 | 9.139 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _cache_update_kernel / unresolved | 435 | 0 / 435 | 2.929 | 2.859 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 435 | 0 / 435 | 2.814 | 2.792 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / compress_gates + compress_values | 145 | 145 / 0 | 8.093 | 8.093 | 1.578 | -6.515 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _engram_req_index_kernel / unresolved | 145 | 0 / 145 | 5.858 | 5.835 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 290 | 290 / 0 | 2.339 | 2.344 | 1.312 | -1.027 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalOr / unresolved | 296 | 0 / 296 | 1.515 | 1.397 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 145 | 0 / 145 | 2.699 | 2.577 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 145 | 0 / 145 | 2.248 | 2.110 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 145 | 0 / 145 | 2.129 | 2.127 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 5800 | 10.538 / 10.438 | 17.136 | 0.422 | 0.685 | partial_base_program_reference_premix_branch_unresolved |
| HcPre / ffn.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 5800 | 10.636 / 10.586 | 17.136 | 0.425 | 0.685 | partial_base_program_reference_premix_branch_unresolved |
| MqsmlaKernel___call__ / attention_core / layers 0, 1 | 290 | 11.092 / 11.153 | 1.578 | 0.022 | 0.003 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 2900 | 29.224 / 29.082 | 1.578 | 0.584 | 0.032 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 2610 | 29.070 / 28.659 | 1.578 | 0.523 | 0.028 | source_symbol_to_declared_attention_program |

## a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 3000 | 0 / 3000 | 242.599 | 241.331 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 3000 | 0 / 3000 | 119.854 | 118.821 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 3000 | 0 / 3000 | 32.836 | 33.035 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| QuantBatchMatmulV3 / grouped_output_b | 3000 | 3000 / 0 | 20.692 | 20.686 | 16.528 | -4.165 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 3000 | 0 / 3000 | 20.492 | 20.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3000 | 0 / 3000 | 19.944 | 18.578 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 3000 | 0 / 3000 | 19.057 | 18.962 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| InplacePartialRotaryMul / unresolved | 10200 | 0 / 10200 | 4.969 | 4.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 3000 | 3000 / 0 | 16.742 | 16.628 | 10.697 | -6.046 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / unresolved | 3750 | 0 / 3750 | 10.821 | 10.698 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 3000 | 3000 / 0 | 12.082 | 12.063 | 10.370 | -1.712 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPre / attention.hc_pre | 3000 | 0 / 3000 | 11.719 | 11.552 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| HcPre / ffn.hc_pre | 3000 | 0 / 3000 | 11.660 | 11.412 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| SwigluGroupQuant / unresolved | 6000 | 0 / 6000 | 4.221 | 4.134 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 3000 | 3000 / 0 | 7.307 | 7.261 | 4.730 | -2.578 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 6450 | 0 / 6450 | 2.999 | 2.985 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvCompressEpilogV2 / unresolved | 3300 | 0 / 3300 | 5.535 | 5.452 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_a | 3000 | 3000 / 0 | 6.024 | 5.988 | 2.837 | -3.187 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 3150 | 0 / 3150 | 4.802 | 4.764 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopKHash / unresolved | 3000 | 0 / 3000 | 5.001 | 5.064 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 3000 | 3000 / 0 | 4.999 | 4.982 | 1.578 | -3.421 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 3000 | 0 / 3000 | 4.915 | 4.913 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 3000 | 3000 / 0 | 4.822 | 4.806 | 1.312 | -3.510 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_b.quantize | 3600 | 3600 / 0 | 4.014 | 4.001 | 1.312 | -2.702 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / attention.hc_post_group | 3000 | 3000 / 0 | 4.627 | 4.592 | 1.312 | -3.315 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 6825 | 0 / 6825 | 1.984 | 2.053 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / grouped_output_b.quantize | 3000 | 3000 / 0 | 4.074 | 4.069 | 1.312 | -2.762 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 3000 | 3000 / 0 | 4.050 | 4.026 | 1.312 | -2.738 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_a.quantize | 3000 | 3000 / 0 | 3.822 | 3.805 | 1.312 | -2.510 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 3000 | 3000 / 0 | 3.318 | 3.290 | 1.312 | -2.006 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 3000 | 3000 / 0 | 3.250 | 3.247 | 1.312 | -1.938 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _quantize_mxfp4_indexer_kernel / unresolved | 600 | 0 / 600 | 16.150 | 15.082 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 150 | 0 / 150 | 59.867 | 59.847 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _Z15metadata_kernel4Args_interface / unresolved | 450 | 0 / 450 | 18.983 | 19.549 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 3000 | 0 / 3000 | 2.410 | 2.400 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_weights | 600 | 600 / 0 | 11.876 | 11.782 | 1.879 | -9.997 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Equal / unresolved | 3150 | 0 / 3150 | 2.083 | 1.960 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantSparseLightningIndexer / unresolved | 300 | 0 / 300 | 18.595 | 18.593 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Neg / unresolved | 3000 | 0 / 3000 | 1.734 | 1.623 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 3000 | 0 / 3000 | 1.542 | 1.460 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantLightningIndexer / unresolved | 300 | 0 / 300 | 13.395 | 11.555 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_indexer_indices_kernel / unresolved | 600 | 0 / 600 | 5.988 | 5.968 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 600 | 600 / 0 | 5.346 | 5.295 | 1.578 | -3.768 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _engram_host_uva_gather_dequant_kernel / unresolved | 150 | 0 / 150 | 13.464 | 13.014 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 600 | 0 / 600 | 2.790 | 2.758 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_mxfp4_indexer_cache_kernel / unresolved | 300 | 0 / 300 | 5.047 | 5.024 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _hash_ids_kernel / unresolved | 75 | 0 / 75 | 20.107 | 20.044 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pool_kernel / unresolved | 225 | 0 / 225 | 4.734 | 4.717 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 150 | 150 / 0 | 6.527 | 6.301 | 1.312 | -5.215 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _engram_gate_kernel / unresolved | 150 | 0 / 150 | 6.165 | 6.166 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _cache_update_kernel / unresolved | 225 | 0 / 225 | 3.406 | 3.392 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalOr / unresolved | 150 | 0 / 150 | 4.999 | 4.405 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / compress_gates + compress_values | 75 | 75 / 0 | 8.637 | 8.675 | 1.881 | -6.756 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 225 | 0 / 225 | 2.832 | 2.814 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 150 | 0 / 150 | 3.728 | 3.828 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 75 | 0 / 75 | 5.797 | 5.720 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 75 | 0 / 75 | 2.606 | 2.575 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 75 | 0 / 75 | 2.098 | 2.070 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 3000 | 11.719 / 11.552 | 21.524 | 0.469 | 0.861 | partial_base_program_reference_premix_branch_unresolved |
| HcPre / ffn.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 3000 | 11.660 / 11.412 | 21.524 | 0.466 | 0.861 | partial_base_program_reference_premix_branch_unresolved |
| MqsmlaKernel___call__ / attention_core / layers 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1350 | 33.893 / 34.158 | 12.624 | 0.610 | 0.227 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 0, 1 | 150 | 16.005 / 12.507 | 12.624 | 0.032 | 0.025 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 1500 | 33.567 / 32.496 | 12.624 | 0.671 | 0.252 | source_symbol_to_declared_attention_program |

## a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MoeDistributeDispatchV3 / expert_dispatch_native | 6080 | 0 / 6080 | 45.332 | 33.641 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 6080 | 0 / 6080 | 38.592 | 38.458 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 6080 | 0 / 6080 | 23.639 | 23.543 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / grouped_output_b | 6080 | 6080 / 0 | 19.567 | 19.561 | 16.049 | -3.518 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 6080 | 0 / 6080 | 18.924 | 18.895 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 6080 | 6080 / 0 | 16.130 | 15.983 | 10.513 | -5.617 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| InplacePartialRotaryMul / unresolved | 20672 | 0 / 20672 | 4.042 | 4.585 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 7600 | 0 / 7600 | 9.697 | 9.728 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 6080 | 6080 / 0 | 11.347 | 11.302 | 10.061 | -1.286 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeDistributeCombineV3 / expert_combine_native | 6080 | 0 / 6080 | 11.198 | 11.141 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 6080 | 0 / 6080 | 10.636 | 10.582 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| HcPre / attention.hc_pre | 6080 | 0 / 6080 | 10.537 | 10.441 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| MqsmlaKernel___call__ / attention_core | 6080 | 0 / 6080 | 9.584 | 9.595 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| SwigluGroupQuant / unresolved | 12160 | 0 / 12160 | 3.724 | 3.514 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 6080 | 6080 / 0 | 7.015 | 6.964 | 4.573 | -2.442 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_a | 6080 | 6080 / 0 | 5.798 | 5.732 | 2.000 | -3.798 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 6384 | 0 / 6384 | 4.619 | 4.606 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 6080 | 6080 / 0 | 4.804 | 4.782 | 1.578 | -3.226 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 13072 | 0 / 13072 | 2.200 | 2.203 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 6080 | 6080 / 0 | 4.103 | 4.093 | 1.312 | -2.791 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 6080 | 0 / 6080 | 4.096 | 4.055 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 6080 | 6080 / 0 | 4.044 | 4.087 | 1.312 | -2.732 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| MatMulV3 / index_weights | 1216 | 1216 / 0 | 9.247 | 9.134 | 1.578 | -7.669 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| MatMulV3 / compress_gates + compress_values | 152 | 152 / 0 | 8.096 | 8.091 | 1.578 | -6.518 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| HcPre / attention.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 6080 | 10.537 / 10.441 | 17.136 | 0.421 | 0.685 | partial_base_program_reference_premix_branch_unresolved |
| HcPre / ffn.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 6080 | 10.636 / 10.582 | 17.136 | 0.425 | 0.685 | partial_base_program_reference_premix_branch_unresolved |
| MqsmlaKernel___call__ / attention_core / layers 0, 1 | 304 | 8.170 / 8.110 | 1.578 | 0.016 | 0.003 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 3040 | 10.067 / 10.133 | 1.578 | 0.201 | 0.032 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 2736 | 9.205 / 9.201 | 1.578 | 0.166 | 0.028 | source_symbol_to_declared_attention_program |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs / GroupedMatmul / expert_down | 5160 | 0 | 0 | 5160 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs / GroupedMatmul / expert_up | 5160 | 0 | 0 | 5160 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs / HcPre / attention.hc_pre | 5160 | 0 | 5160 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs / HcPre / ffn.hc_pre | 5160 | 0 | 5160 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs / MoeDistributeCombineV3 / expert_combine_native | 5160 | 0 | 0 | 5160 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs / MoeDistributeDispatchV3 / expert_dispatch_native | 5160 | 0 | 0 | 5160 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs / MqsmlaKernel___call__ / attention_core | 5160 | 0 | 5160 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs / GroupedMatmul / expert_down | 4200 | 0 | 0 | 4200 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs / GroupedMatmul / expert_up | 4200 | 0 | 0 | 4200 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs / HcPre / attention.hc_pre | 4200 | 0 | 4200 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs / HcPre / ffn.hc_pre | 4200 | 0 | 4200 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs / MoeDistributeCombineV3 / expert_combine_native | 4200 | 0 | 0 | 4200 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs / MoeDistributeDispatchV3 / expert_dispatch_native | 4200 | 0 | 0 | 4200 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs / MqsmlaKernel___call__ / attention_core | 4200 | 0 | 4200 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs / GroupedMatmul / expert_down | 6040 | 0 | 0 | 6040 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs / GroupedMatmul / expert_up | 6040 | 0 | 0 | 6040 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs / HcPre / attention.hc_pre | 6040 | 0 | 6040 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs / HcPre / ffn.hc_pre | 6040 | 0 | 6040 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs / MoeDistributeCombineV3 / expert_combine_native | 6040 | 0 | 0 | 6040 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs / MoeDistributeDispatchV3 / expert_dispatch_native | 6040 | 0 | 0 | 6040 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs / MqsmlaKernel___call__ / attention_core | 6040 | 0 | 6040 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs / GroupedMatmul / expert_down | 5800 | 0 | 0 | 5800 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs / GroupedMatmul / expert_up | 5800 | 0 | 0 | 5800 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs / HcPre / attention.hc_pre | 5800 | 0 | 5800 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs / HcPre / ffn.hc_pre | 5800 | 0 | 5800 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs / MoeDistributeCombineV3 / expert_combine_native | 5800 | 0 | 0 | 5800 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs / MoeDistributeDispatchV3 / expert_dispatch_native | 5800 | 0 | 0 | 5800 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs / MqsmlaKernel___call__ / attention_core | 5800 | 0 | 5800 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / GroupedMatmul / expert_down | 3000 | 0 | 0 | 3000 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / GroupedMatmul / expert_up | 3000 | 0 | 0 | 3000 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / HcPre / attention.hc_pre | 3000 | 0 | 3000 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / HcPre / ffn.hc_pre | 3000 | 0 | 3000 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / MoeDistributeCombineV3 / expert_combine_native | 3000 | 0 | 0 | 3000 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / MoeDistributeDispatchV3 / expert_dispatch_native | 3000 | 0 | 0 | 3000 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / MqsmlaKernel___call__ / attention_core | 3000 | 0 | 3000 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs / GroupedMatmul / expert_down | 6080 | 0 | 0 | 6080 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs / GroupedMatmul / expert_up | 6080 | 0 | 0 | 6080 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs / HcPre / attention.hc_pre | 6080 | 0 | 6080 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs / HcPre / ffn.hc_pre | 6080 | 0 | 6080 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs / MoeDistributeCombineV3 / expert_combine_native | 6080 | 0 | 0 | 6080 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs / MoeDistributeDispatchV3 / expert_dispatch_native | 6080 | 0 | 0 | 6080 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs / MqsmlaKernel___call__ / attention_core | 6080 | 0 | 6080 | 0 | 0 |
