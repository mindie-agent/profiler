# Complete Decode Body Operator Families

Only complete events inside the 21 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs-retry | 9 / 9 | 0 / 0 | 9 / 9 | 4767 / 33306 | 0 |

## a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs-retry

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| DispatchFFNCombine / routed_ffn_native | 840 | 0 / 840 | 718.428 | 712.576 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 840 | 0 / 840 | 148.913 | 154.737 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| reduce_scatterAicpuKernel / unresolved | 840 | 0 / 840 | 138.464 | 130.597 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 1890 | 0 / 1890 | 55.288 | 70.819 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / unresolved | 1680 | 0 / 1680 | 43.826 | 44.059 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1680 | 0 / 1680 | 23.947 | 24.319 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 840 | 0 / 840 | 41.953 | 41.830 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 2646 | 0 / 2646 | 12.639 | 12.680 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| InplacePartialRotaryMul / unresolved | 2856 | 0 / 2856 | 9.918 | 10.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / unresolved | 1680 | 0 / 1680 | 16.362 | 16.509 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| VllmAscendQuantLightningIndexerV2 / unresolved | 105 | 0 / 105 | 240.289 | 272.175 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 840 | 840 / 0 | 25.649 | 25.479 | 19.001 | -6.648 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_reduceScatter_ / attention_output_communication | 840 | 0 / 840 | 25.633 | 24.820 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| QuantBatchMatmulV3 / q_b | 840 | 840 / 0 | 25.513 | 25.560 | 30.236 | 4.724 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_a | 840 | 840 / 0 | 23.346 | 23.399 | 26.043 | 2.697 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allGather_ / attention_output_communication | 840 | 0 / 840 | 20.978 | 19.629 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| ScatterNdUpdateSk / unresolved | 1092 | 0 / 1092 | 15.979 | 16.479 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 840 | 0 / 840 | 17.098 | 16.740 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopKHash / unresolved | 840 | 0 / 840 | 14.821 | 14.430 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_a.quantize | 840 | 840 / 0 | 10.414 | 10.420 | 2.500 | -7.914 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _prepare_indexer_indices_kernel / unresolved | 168 | 0 / 168 | 46.987 | 46.839 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNormCast / unresolved | 840 | 0 / 840 | 9.310 | 9.120 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSwigluQuant / unresolved | 840 | 0 / 840 | 8.239 | 8.160 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 861 | 0 / 861 | 7.703 | 7.440 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_b.quantize | 1008 | 1008 / 0 | 6.467 | 6.400 | 2.500 | -3.967 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / unresolved | 924 | 0 / 924 | 6.437 | 6.420 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 168 | 168 / 0 | 28.238 | 28.259 | 15.301 | -12.937 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _quantize_indexer_query_kernel / unresolved | 168 | 0 / 168 | 23.942 | 23.799 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| VllmAscendQuantLightningIndexerV2 / quant_lightning_indexer | 63 | 0 / 63 | 62.225 | 62.459 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / index_weights | 168 | 168 / 0 | 16.315 | 16.190 | 6.257 | -10.058 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 1323 | 0 / 1323 | 1.928 | 1.580 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 840 | 0 / 840 | 2.994 | 2.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 840 | 0 / 840 | 2.404 | 2.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 840 | 0 / 840 | 1.511 | 1.500 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 63 | 0 / 63 | 18.473 | 18.200 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| ReduceMean / unresolved | 63 | 0 / 63 | 11.944 | 11.900 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / compress_gates + compress_values | 21 | 21 / 0 | 27.890 | 28.079 | 37.607 | 9.717 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / compress_norm | 42 | 42 / 0 | 13.048 | 12.950 | 2.500 | -10.548 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _cache_update_kernel / unresolved | 63 | 0 / 63 | 8.056 | 8.000 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pool_kernel / unresolved | 63 | 0 / 63 | 7.893 | 7.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 63 | 0 / 63 | 7.513 | 7.520 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 168 | 0 / 168 | 2.157 | 2.140 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs-retry / DispatchFFNCombine / routed_ffn_native | 840 | 0 | 0 | 840 | 0 |
