# Complete Decode Body Operator Families

Only complete events inside the 105 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / composed-arch35-ec58ce79 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 183011 | 16 |

## a5_v41_fp8_tp1_dp8_ep8_c32_p2k / composed-arch35-ec58ce79

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 4200 | 0 / 4200 | 127.406 | 126.789 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 4200 | 0 / 4200 | 65.238 | 64.668 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 4200 | 0 / 4200 | 30.251 | 30.550 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / grouped_output_b | 4200 | 0 / 4200 | 20.138 | 20.121 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| TransposeQuantBatchMatMul / unresolved | 4200 | 0 / 4200 | 20.003 | 19.975 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4200 | 0 / 4200 | 18.548 | 17.867 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 4200 | 0 / 4200 | 16.397 | 16.233 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| InplacePartialRotaryMul / unresolved | 14280 | 0 / 14280 | 4.364 | 4.761 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 5250 | 0 / 5250 | 10.241 | 10.146 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 4200 | 0 / 4200 | 12.381 | 12.229 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 4200 | 0 / 4200 | 11.617 | 11.578 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 4200 | 0 / 4200 | 11.294 | 11.107 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 4200 | 0 / 4200 | 11.183 | 11.022 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwigluGroupQuant / unresolved | 8400 | 0 / 8400 | 3.996 | 4.091 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 4200 | 0 / 4200 | 7.171 | 7.115 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| QuantBatchMatmulV3 / q_a | 4200 | 0 / 4200 | 5.841 | 5.804 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| RmsNorm / unresolved | 9030 | 0 / 9030 | 2.562 | 2.548 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvCompressEpilogV2 / unresolved | 4620 | 0 / 4620 | 4.547 | 4.446 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 4410 | 0 / 4410 | 4.722 | 4.671 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 4200 | 0 / 4200 | 4.875 | 4.861 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| ForeachAddList / unresolved | 4200 | 0 / 4200 | 4.521 | 4.472 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 4200 | 0 / 4200 | 4.502 | 4.468 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 4200 | 0 / 4200 | 4.499 | 4.481 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / q_b.quantize | 5040 | 0 / 5040 | 3.685 | 3.641 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| MoeGatingTopKHash / unresolved | 4200 | 0 / 4200 | 4.176 | 4.022 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / grouped_output_b.quantize | 4200 | 0 / 4200 | 4.125 | 4.108 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| DynamicMxQuant / shared.gate_up.quantize | 4200 | 0 / 4200 | 3.954 | 3.911 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| DynamicMxQuant / q_a.quantize | 4200 | 0 / 4200 | 3.875 | 3.854 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| Cast / unresolved | 9555 | 0 / 9555 | 1.623 | 1.688 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 210 | 0 / 210 | 58.925 | 58.899 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 4200 | 0 / 4200 | 2.848 | 2.820 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| RmsNorm / norm2 | 4200 | 0 / 4200 | 2.788 | 2.782 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| _quantize_mxfp4_indexer_kernel / unresolved | 840 | 0 / 840 | 13.728 | 12.554 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _Z15metadata_kernel4Args_interface / unresolved | 626 | 0 / 626 | 15.767 | 15.418 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_weights | 840 | 0 / 840 | 10.851 | 10.798 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| SelectV2 / unresolved | 4200 | 0 / 4200 | 2.129 | 1.836 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 4410 | 0 / 4410 | 1.817 | 1.723 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Neg / unresolved | 4200 | 0 / 4200 | 1.513 | 1.439 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantSparseLightningIndexer / unresolved | 420 | 0 / 420 | 14.789 | 14.617 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 4200 | 0 / 4200 | 1.429 | 1.378 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantLightningIndexer / unresolved | 420 | 0 / 420 | 12.644 | 10.309 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_indexer_indices_kernel / unresolved | 840 | 0 / 840 | 5.579 | 5.588 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 840 | 0 / 840 | 5.333 | 5.307 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| _hash_ids_kernel / unresolved | 105 | 0 / 105 | 21.976 | 21.930 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 840 | 0 / 840 | 2.689 | 2.655 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_mxfp4_indexer_cache_kernel / unresolved | 420 | 0 / 420 | 4.852 | 4.832 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_host_uva_gather_dequant_kernel / unresolved | 210 | 0 / 210 | 9.438 | 9.271 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_gate_kernel / unresolved | 210 | 0 / 210 | 5.808 | 5.793 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalOr / unresolved | 210 | 0 / 210 | 5.362 | 4.657 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 210 | 0 / 210 | 5.135 | 4.992 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| _pool_kernel / unresolved | 315 | 0 / 315 | 3.288 | 2.519 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _cache_update_kernel / unresolved | 315 | 0 / 315 | 3.143 | 3.125 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / compress_gates + compress_values | 105 | 0 / 105 | 8.554 | 8.556 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| ZerosLike / unresolved | 315 | 0 / 315 | 2.769 | 2.830 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 210 | 0 / 210 | 3.550 | 3.474 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 105 | 0 / 105 | 6.267 | 6.113 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 105 | 0 / 105 | 2.462 | 2.447 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 105 | 0 / 105 | 2.222 | 2.254 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
