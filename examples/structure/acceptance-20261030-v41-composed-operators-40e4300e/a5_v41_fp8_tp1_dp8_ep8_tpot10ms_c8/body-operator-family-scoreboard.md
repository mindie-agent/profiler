# Complete Decode Body Operator Families

Only complete events inside the 145 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / composed-arch35-40e4300e | 16 / 16 | 0 / 0 | 16 / 16 | 73515 / 252886 | 0 |

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


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
