# Complete Decode Body Operator Families

Only complete events inside the 151 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / composed-arch35-40e4300e | 16 / 16 | 0 / 0 | 16 / 16 | 76557 / 263341 | 0 |

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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
