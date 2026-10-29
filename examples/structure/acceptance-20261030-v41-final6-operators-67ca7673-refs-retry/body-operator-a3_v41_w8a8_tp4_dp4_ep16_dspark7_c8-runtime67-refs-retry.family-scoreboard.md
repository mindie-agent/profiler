# Complete Decode Body Operator Families

Only complete events inside the 29 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 / runtime67-refs-retry | 9 / 9 | 0 / 0 | 9 / 9 | 6583 / 44805 | 0 |

## a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 / runtime67-refs-retry

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| DispatchFFNCombine / routed_ffn_native | 1160 | 0 / 1160 | 694.018 | 691.047 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| reduce_scatterAicpuKernel / unresolved | 1160 | 0 / 1160 | 140.830 | 131.507 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / unresolved | 2320 | 0 / 2320 | 35.098 | 34.859 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 1160 | 0 / 1160 | 59.101 | 60.339 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 2320 | 0 / 2320 | 23.384 | 23.740 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 2610 | 0 / 2610 | 20.118 | 21.680 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1160 | 0 / 1160 | 33.772 | 33.679 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 3654 | 0 / 3654 | 9.793 | 11.780 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| InplacePartialRotaryMul / unresolved | 3944 | 0 / 3944 | 9.055 | 9.220 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 1160 | 0 / 1160 | 20.748 | 16.019 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| QuantBatchMatmulV3 / q_b | 1160 | 1160 / 0 | 19.899 | 19.899 | 15.332 | -4.566 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_reduceScatter_ / attention_output_communication | 1160 | 0 / 1160 | 18.755 | 18.390 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| HcPost / unresolved | 2320 | 0 / 2320 | 8.961 | 8.820 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_a | 1160 | 1160 / 0 | 17.672 | 17.700 | 9.541 | -8.131 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 1160 | 0 / 1160 | 16.924 | 16.500 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| VllmAscendQuantLightningIndexerV2 / unresolved | 145 | 0 / 145 | 130.172 | 145.657 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdateSk / unresolved | 1508 | 0 / 1508 | 12.361 | 12.040 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 1160 | 1160 / 0 | 14.585 | 14.540 | 6.324 | -8.261 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopKHash / unresolved | 1160 | 0 / 1160 | 6.588 | 6.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_b.quantize | 1392 | 1392 / 0 | 5.173 | 5.119 | 2.500 | -2.673 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / q_a.quantize | 1160 | 1160 / 0 | 6.109 | 6.039 | 2.500 | -3.609 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DequantSwigluQuant / unresolved | 1160 | 0 / 1160 | 5.791 | 5.740 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / unresolved | 1276 | 0 / 1276 | 4.403 | 4.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNormCast / unresolved | 1160 | 0 / 1160 | 4.095 | 4.060 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_indexer_indices_kernel / unresolved | 232 | 0 / 232 | 19.753 | 17.910 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| VllmAscendQuantLightningIndexerV2 / quant_lightning_indexer | 87 | 0 / 87 | 39.009 | 39.099 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 232 | 232 / 0 | 14.224 | 14.240 | 7.771 | -6.454 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _quantize_indexer_query_kernel / unresolved | 232 | 0 / 232 | 13.365 | 13.200 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 1827 | 0 / 1827 | 1.695 | 1.400 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 1160 | 0 / 1160 | 2.665 | 2.640 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / index_weights | 232 | 232 / 0 | 12.247 | 12.229 | 6.252 | -5.995 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Equal / unresolved | 1160 | 0 / 1160 | 2.291 | 2.300 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 1160 | 0 / 1160 | 1.496 | 1.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 87 | 0 / 87 | 17.694 | 17.439 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| ReduceMean / unresolved | 87 | 0 / 87 | 14.317 | 14.180 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 58 | 58 / 0 | 11.904 | 11.870 | 2.500 | -9.404 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / compress_gates + compress_values | 29 | 29 / 0 | 17.910 | 17.899 | 12.536 | -5.374 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _cache_update_kernel / unresolved | 87 | 0 / 87 | 5.176 | 5.140 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pool_kernel / unresolved | 87 | 0 / 87 | 4.920 | 4.720 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 232 | 0 / 232 | 1.593 | 1.580 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 87 | 0 / 87 | 4.019 | 4.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 / runtime67-refs-retry / DispatchFFNCombine / routed_ffn_native | 1160 | 0 | 0 | 1160 | 0 |
