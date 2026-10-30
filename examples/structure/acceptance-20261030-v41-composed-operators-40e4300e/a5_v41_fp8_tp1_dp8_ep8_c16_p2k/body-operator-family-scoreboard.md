# Complete Decode Body Operator Families

Only complete events inside the 129 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / composed-arch35-40e4300e | 16 / 16 | 0 / 0 | 16 / 16 | 65403 / 224840 | 0 |

## a5_v41_fp8_tp1_dp8_ep8_c16_p2k / composed-arch35-40e4300e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 5160 | 0 / 5160 | 68.076 | 67.778 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 5160 | 0 / 5160 | 37.439 | 37.167 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 5160 | 0 / 5160 | 28.836 | 29.341 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / grouped_output_b | 5160 | 5160 / 0 | 19.815 | 19.807 | 16.601 | -3.214 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 5160 | 0 / 5160 | 19.389 | 19.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 5160 | 0 / 5160 | 17.898 | 17.041 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 5160 | 5160 / 0 | 16.232 | 16.091 | 10.847 | -5.385 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| InplacePartialRotaryMul / unresolved | 17544 | 0 / 17544 | 4.264 | 4.725 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 6450 | 0 / 6450 | 9.873 | 9.890 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 5160 | 0 / 5160 | 11.978 | 11.948 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 5160 | 0 / 5160 | 11.810 | 11.729 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 5160 | 0 / 5160 | 11.736 | 11.691 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 5160 | 5160 / 0 | 11.475 | 11.424 | 10.105 | -1.370 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SwigluGroupQuant / unresolved | 10320 | 0 / 10320 | 3.928 | 3.892 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 5160 | 5160 / 0 | 7.077 | 7.016 | 4.595 | -2.482 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_a | 5160 | 5160 / 0 | 5.755 | 5.707 | 5.093 | -0.662 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 11094 | 0 / 11094 | 2.352 | 2.335 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 5418 | 0 / 5418 | 4.648 | 4.607 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 5160 | 5160 / 0 | 4.768 | 4.754 | 5.093 | 0.325 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / grouped_output_b.quantize | 5160 | 5160 / 0 | 4.598 | 4.583 | 1.312 | -3.286 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| KvCompressEpilogV2 / unresolved | 5676 | 0 / 5676 | 4.120 | 3.936 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / q_a.quantize | 5160 | 5160 / 0 | 4.376 | 4.361 | 1.312 | -3.064 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 5160 | 5160 / 0 | 4.366 | 4.348 | 1.312 | -3.054 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / attention.hc_post_group | 5160 | 0 / 5160 | 4.289 | 4.266 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 5160 | 0 / 5160 | 4.287 | 4.175 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 5160 | 0 / 5160 | 4.162 | 4.138 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopKHash / unresolved | 5160 | 0 / 5160 | 3.873 | 3.630 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / q_b.quantize | 6192 | 6192 / 0 | 3.062 | 3.022 | 1.312 | -1.750 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 11739 | 0 / 11739 | 1.516 | 1.524 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 258 | 0 / 258 | 58.751 | 58.719 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 5160 | 5160 / 0 | 2.742 | 2.750 | 1.312 | -1.430 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 5160 | 5160 / 0 | 2.718 | 2.745 | 1.312 | -1.406 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _quantize_mxfp4_indexer_kernel / unresolved | 1032 | 0 / 1032 | 11.389 | 10.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_weights | 1032 | 1032 / 0 | 10.825 | 10.723 | 2.660 | -8.165 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| MatMulV3 / compress_gates + compress_values | 129 | 129 / 0 | 8.275 | 8.273 | 10.170 | 1.895 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 387 | 0 / 387 | 2.624 | 2.535 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 129 | 0 / 129 | 6.105 | 6.014 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 258 | 0 / 258 | 2.861 | 2.661 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 129 | 0 / 129 | 2.377 | 2.351 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 129 | 0 / 129 | 2.176 | 2.116 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 1 | 0 / 1 | 11.728 | 11.728 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
