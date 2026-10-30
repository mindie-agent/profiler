# Complete Decode Body Operator Families

Only complete events inside the 830 accepted target-body windows from 7 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / composed-arch35-40e4300e | 16 / 16 | 0 / 0 | 16 / 16 | 37011 / 127446 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / composed-arch35-40e4300e | 16 / 16 | 0 / 0 | 16 / 16 | 65403 / 224840 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / composed-arch35-40e4300e | 16 / 16 | 0 / 0 | 16 / 16 | 53235 / 183011 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / composed-arch35-40e4300e | 16 / 16 | 0 / 0 | 16 / 16 | 76557 / 263341 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / composed-arch35-40e4300e | 16 / 16 | 0 / 0 | 16 / 16 | 73515 / 252886 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / composed-arch35-40e4300e | 16 / 16 | 0 / 0 | 16 / 16 | 38025 / 130725 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / composed-arch35-40e4300e | 16 / 16 | 0 / 0 | 16 / 16 | 77064 / 265115 | 0 |

## a5_v41_fp8_tp1_dp8_ep8_c128_p2k / composed-arch35-40e4300e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 2920 | 0 / 2920 | 250.141 | 248.818 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 2920 | 0 / 2920 | 123.273 | 122.228 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 2920 | 0 / 2920 | 34.021 | 34.734 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / grouped_output_b | 2920 | 2920 / 0 | 21.429 | 21.417 | 17.558 | -3.871 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 2920 | 0 / 2920 | 21.093 | 21.082 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 2920 | 0 / 2920 | 21.045 | 19.659 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| InplacePartialRotaryMul / unresolved | 9928 | 0 / 9928 | 5.095 | 5.294 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 2920 | 2920 / 0 | 16.909 | 16.807 | 11.499 | -5.409 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeDistributeCombineV3 / expert_combine_native | 2920 | 0 / 2920 | 15.402 | 15.216 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 3650 | 0 / 3650 | 11.519 | 11.223 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 2920 | 2920 / 0 | 12.334 | 12.320 | 10.723 | -1.611 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPre / ffn.hc_pre | 2920 | 0 / 2920 | 12.209 | 11.944 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 2920 | 0 / 2920 | 12.178 | 12.002 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwigluGroupQuant / unresolved | 5840 | 0 / 5840 | 4.496 | 4.456 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 6278 | 0 / 6278 | 3.870 | 3.873 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 2920 | 2920 / 0 | 7.481 | 7.428 | 4.909 | -2.573 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| KvCompressEpilogV2 / unresolved | 3212 | 0 / 3212 | 6.121 | 6.165 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_a | 2920 | 2920 / 0 | 6.173 | 6.147 | 5.683 | -0.490 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 2920 | 0 / 2920 | 5.857 | 5.822 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopKHash / unresolved | 2920 | 0 / 2920 | 5.433 | 5.492 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 6644 | 0 / 6644 | 2.374 | 2.091 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 3066 | 0 / 3066 | 4.962 | 4.923 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 2920 | 2920 / 0 | 5.096 | 5.073 | 5.683 | 0.587 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 2920 | 0 / 2920 | 5.033 | 5.016 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 2920 | 0 / 2920 | 4.907 | 4.881 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 2920 | 2920 / 0 | 4.889 | 4.887 | 1.312 | -3.577 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_a.quantize | 2920 | 2920 / 0 | 4.634 | 4.589 | 1.312 | -3.322 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_b.quantize | 3504 | 3504 / 0 | 3.783 | 3.743 | 1.312 | -2.471 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 2920 | 2920 / 0 | 4.176 | 4.177 | 1.312 | -2.864 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _quantize_mxfp4_indexer_kernel / unresolved | 584 | 0 / 584 | 20.764 | 19.503 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / grouped_output_b.quantize | 2920 | 2920 / 0 | 4.120 | 4.109 | 1.312 | -2.808 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 2920 | 2920 / 0 | 4.104 | 4.080 | 1.312 | -2.792 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _Z15metadata_kernel4Args_interface / unresolved | 434 | 0 / 434 | 21.331 | 20.197 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 146 | 0 / 146 | 60.575 | 60.566 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 2920 | 0 / 2920 | 2.769 | 2.948 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_weights | 584 | 584 / 0 | 12.241 | 12.175 | 3.765 | -8.477 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Equal / unresolved | 3066 | 0 / 3066 | 2.218 | 2.179 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Neg / unresolved | 2920 | 0 / 2920 | 2.010 | 1.931 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantSparseLightningIndexer / unresolved | 292 | 0 / 292 | 18.026 | 17.915 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 2920 | 0 / 2920 | 1.685 | 1.747 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantLightningIndexer / unresolved | 292 | 0 / 292 | 13.967 | 12.334 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_indexer_indices_kernel / unresolved | 584 | 0 / 584 | 6.707 | 6.684 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_host_uva_gather_dequant_kernel / unresolved | 146 | 0 / 146 | 25.685 | 26.114 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 584 | 584 / 0 | 5.483 | 5.431 | 1.578 | -3.905 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 584 | 0 / 584 | 2.903 | 2.863 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_mxfp4_indexer_cache_kernel / unresolved | 292 | 0 / 292 | 5.348 | 5.354 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _hash_ids_kernel / unresolved | 73 | 0 / 73 | 20.806 | 20.609 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 146 | 146 / 0 | 9.554 | 9.336 | 1.312 | -8.242 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _pool_kernel / unresolved | 219 | 0 / 219 | 5.167 | 5.145 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_gate_kernel / unresolved | 146 | 0 / 146 | 7.197 | 7.157 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _cache_update_kernel / unresolved | 219 | 0 / 219 | 3.571 | 3.558 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 64 | 0 / 64 | 10.545 | 10.419 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / compress_gates + compress_values | 73 | 73 / 0 | 8.741 | 8.752 | 11.307 | 2.566 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 219 | 0 / 219 | 2.733 | 2.719 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 146 | 0 / 146 | 3.931 | 3.896 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 73 | 0 / 73 | 6.516 | 6.436 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 146 | 0 / 146 | 3.145 | 2.908 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalOr / unresolved | 146 | 0 / 146 | 1.902 | 1.539 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 73 | 0 / 73 | 2.637 | 2.603 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 73 | 0 / 73 | 2.153 | 2.085 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

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

## a5_v41_fp8_tp1_dp8_ep8_c32_p2k / composed-arch35-40e4300e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4200 | 0 / 4200 | 127.406 | 126.789 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 4200 | 0 / 4200 | 65.238 | 64.668 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 4200 | 0 / 4200 | 30.251 | 30.550 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / grouped_output_b | 4200 | 4200 / 0 | 20.138 | 20.121 | 16.738 | -3.400 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 4200 | 0 / 4200 | 20.003 | 19.975 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4200 | 0 / 4200 | 18.548 | 17.867 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 4200 | 4200 / 0 | 16.397 | 16.233 | 10.880 | -5.517 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| InplacePartialRotaryMul / unresolved | 14280 | 0 / 14280 | 4.364 | 4.761 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 5250 | 0 / 5250 | 10.241 | 10.146 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 4200 | 0 / 4200 | 12.381 | 12.229 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 4200 | 4200 / 0 | 11.617 | 11.578 | 10.194 | -1.423 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPre / attention.hc_pre | 4200 | 0 / 4200 | 11.294 | 11.107 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 4200 | 0 / 4200 | 11.183 | 11.022 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwigluGroupQuant / unresolved | 8400 | 0 / 8400 | 3.996 | 4.091 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 4200 | 4200 / 0 | 7.171 | 7.115 | 4.640 | -2.531 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_a | 4200 | 4200 / 0 | 5.841 | 5.804 | 5.177 | -0.664 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 9030 | 0 / 9030 | 2.562 | 2.548 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvCompressEpilogV2 / unresolved | 4620 | 0 / 4620 | 4.547 | 4.446 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 4410 | 0 / 4410 | 4.722 | 4.671 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 4200 | 4200 / 0 | 4.875 | 4.861 | 5.177 | 0.302 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 4200 | 0 / 4200 | 4.521 | 4.472 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 4200 | 0 / 4200 | 4.502 | 4.468 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 4200 | 0 / 4200 | 4.499 | 4.481 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
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

## a5_v41_fp8_tp1_dp8_ep8_c4_p2k / composed-arch35-40e4300e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MoeDistributeDispatchV3 / expert_dispatch_native | 6040 | 0 / 6040 | 47.766 | 35.270 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 6040 | 0 / 6040 | 38.809 | 38.660 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 6040 | 0 / 6040 | 23.604 | 23.476 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / grouped_output_b | 6040 | 6040 / 0 | 19.568 | 19.564 | 16.532 | -3.035 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 6040 | 0 / 6040 | 18.932 | 18.897 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 6040 | 6040 / 0 | 16.163 | 16.012 | 10.830 | -5.333 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| InplacePartialRotaryMul / unresolved | 20536 | 0 / 20536 | 4.029 | 4.579 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 7550 | 0 / 7550 | 9.682 | 9.753 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 6040 | 6040 / 0 | 11.361 | 11.319 | 10.061 | -1.300 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeDistributeCombineV3 / expert_combine_native | 6040 | 0 / 6040 | 11.254 | 11.175 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 6040 | 0 / 6040 | 10.687 | 10.633 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 6040 | 0 / 6040 | 10.593 | 10.482 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 6040 | 0 / 6040 | 9.466 | 9.499 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwigluGroupQuant / unresolved | 12080 | 0 / 12080 | 3.723 | 3.595 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 6040 | 6040 / 0 | 6.977 | 6.922 | 4.573 | -2.405 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_a | 6040 | 6040 / 0 | 5.795 | 5.720 | 5.051 | -0.744 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 6342 | 0 / 6342 | 4.602 | 4.584 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 6040 | 6040 / 0 | 4.818 | 4.794 | 5.051 | 0.232 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 12986 | 0 / 12986 | 2.186 | 2.197 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 6040 | 0 / 6040 | 4.232 | 4.263 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 6040 | 0 / 6040 | 4.101 | 4.064 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 6040 | 0 / 6040 | 4.071 | 4.093 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
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
| MatMulV3 / index_weights | 1208 | 1208 / 0 | 9.203 | 9.113 | 2.581 | -6.623 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| MatMulV3 / compress_gates + compress_values | 151 | 151 / 0 | 8.148 | 8.050 | 10.088 | 1.940 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 453 | 0 / 453 | 2.504 | 2.478 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pool_kernel / unresolved | 453 | 0 / 453 | 1.831 | 1.792 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 151 | 0 / 151 | 5.225 | 5.192 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 302 | 302 / 0 | 2.210 | 2.229 | 1.312 | -0.898 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _cache_update_kernel / unresolved | 453 | 0 / 453 | 1.388 | 1.370 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalOr / unresolved | 302 | 0 / 302 | 1.376 | 1.346 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 151 | 0 / 151 | 2.511 | 2.473 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 151 | 0 / 151 | 2.206 | 2.171 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 151 | 0 / 151 | 1.985 | 1.963 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / composed-arch35-40e4300e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 5800 | 0 / 5800 | 38.541 | 38.378 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 5800 | 0 / 5800 | 29.449 | 16.841 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 5800 | 0 / 5800 | 28.248 | 28.863 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 5800 | 0 / 5800 | 23.656 | 23.572 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / grouped_output_b | 5800 | 5800 / 0 | 19.567 | 19.558 | 16.532 | -3.035 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 5800 | 0 / 5800 | 18.967 | 18.925 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 5800 | 5800 / 0 | 16.144 | 15.990 | 10.830 | -5.314 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| InplacePartialRotaryMul / unresolved | 19720 | 0 / 19720 | 4.052 | 4.601 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 7250 | 0 / 7250 | 9.702 | 9.730 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 5800 | 5800 / 0 | 11.338 | 11.295 | 10.061 | -1.277 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeDistributeCombineV3 / expert_combine_native | 5800 | 0 / 5800 | 11.209 | 11.140 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 5800 | 0 / 5800 | 10.636 | 10.586 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 5800 | 0 / 5800 | 10.538 | 10.438 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwigluGroupQuant / unresolved | 11600 | 0 / 11600 | 3.730 | 3.674 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 5800 | 5800 / 0 | 7.012 | 6.955 | 4.573 | -2.440 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_a | 5800 | 5800 / 0 | 5.799 | 5.732 | 5.051 | -0.748 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 6090 | 0 / 6090 | 4.622 | 4.606 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvCompressEpilogV2 / unresolved | 6380 | 0 / 6380 | 4.375 | 3.779 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 5800 | 5800 / 0 | 4.800 | 4.779 | 5.051 | 0.250 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 12470 | 0 / 12470 | 2.198 | 2.203 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 5800 | 0 / 5800 | 4.102 | 4.062 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 5800 | 0 / 5800 | 4.100 | 4.074 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 5800 | 0 / 5800 | 4.044 | 4.084 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
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
| MatMulV3 / index_weights | 1160 | 1160 / 0 | 9.290 | 9.185 | 2.581 | -6.709 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| MatMulV3 / compress_gates + compress_values | 145 | 145 / 0 | 8.093 | 8.093 | 10.088 | 1.995 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _engram_req_index_kernel / unresolved | 145 | 0 / 145 | 5.858 | 5.835 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 290 | 290 / 0 | 2.339 | 2.344 | 1.312 | -1.027 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalOr / unresolved | 296 | 0 / 296 | 1.515 | 1.397 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 145 | 0 / 145 | 2.699 | 2.577 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 145 | 0 / 145 | 2.248 | 2.110 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 145 | 0 / 145 | 2.129 | 2.127 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / composed-arch35-40e4300e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 3000 | 0 / 3000 | 242.599 | 241.331 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 3000 | 0 / 3000 | 119.854 | 118.821 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 3000 | 0 / 3000 | 32.836 | 33.035 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / grouped_output_b | 3000 | 3000 / 0 | 20.692 | 20.686 | 17.011 | -3.681 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 3000 | 0 / 3000 | 20.492 | 20.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3000 | 0 / 3000 | 19.944 | 18.578 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 3000 | 0 / 3000 | 19.057 | 18.962 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| InplacePartialRotaryMul / unresolved | 10200 | 0 / 10200 | 4.969 | 4.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 3000 | 3000 / 0 | 16.742 | 16.628 | 11.036 | -5.706 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / unresolved | 3750 | 0 / 3750 | 10.821 | 10.698 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 3000 | 3000 / 0 | 12.082 | 12.063 | 10.370 | -1.712 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPre / attention.hc_pre | 3000 | 0 / 3000 | 11.719 | 11.552 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 3000 | 0 / 3000 | 11.660 | 11.412 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwigluGroupQuant / unresolved | 6000 | 0 / 6000 | 4.221 | 4.134 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 3000 | 3000 / 0 | 7.307 | 7.261 | 4.730 | -2.578 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 6450 | 0 / 6450 | 2.999 | 2.985 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvCompressEpilogV2 / unresolved | 3300 | 0 / 3300 | 5.535 | 5.452 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_a | 3000 | 3000 / 0 | 6.024 | 5.988 | 5.346 | -0.678 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 3150 | 0 / 3150 | 4.802 | 4.764 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopKHash / unresolved | 3000 | 0 / 3000 | 5.001 | 5.064 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 3000 | 3000 / 0 | 4.999 | 4.982 | 5.346 | 0.346 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 3000 | 0 / 3000 | 4.915 | 4.913 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 3000 | 0 / 3000 | 4.822 | 4.806 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / q_b.quantize | 3600 | 3600 / 0 | 4.014 | 4.001 | 1.312 | -2.702 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / attention.hc_post_group | 3000 | 0 / 3000 | 4.627 | 4.592 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
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
| MatMulV3 / index_weights | 600 | 600 / 0 | 11.876 | 11.782 | 3.133 | -8.743 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| MatMulV3 / compress_gates + compress_values | 75 | 75 / 0 | 8.637 | 8.675 | 10.657 | 2.020 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 225 | 0 / 225 | 2.832 | 2.814 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 150 | 0 / 150 | 3.728 | 3.828 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 75 | 0 / 75 | 5.797 | 5.720 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 75 | 0 / 75 | 2.606 | 2.575 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 75 | 0 / 75 | 2.098 | 2.070 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / composed-arch35-40e4300e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| MoeDistributeDispatchV3 / expert_dispatch_native | 6080 | 0 / 6080 | 45.332 | 33.641 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_up | 6080 | 0 / 6080 | 38.592 | 38.458 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 6080 | 0 / 6080 | 23.639 | 23.543 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / grouped_output_b | 6080 | 6080 / 0 | 19.567 | 19.561 | 16.532 | -3.034 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 6080 | 0 / 6080 | 18.924 | 18.895 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 6080 | 6080 / 0 | 16.130 | 15.983 | 10.830 | -5.299 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
