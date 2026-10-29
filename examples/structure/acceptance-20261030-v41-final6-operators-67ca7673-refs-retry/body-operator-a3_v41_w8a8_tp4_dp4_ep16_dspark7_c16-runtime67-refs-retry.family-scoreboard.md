# Complete Decode Body Operator Families

Only complete events inside the 32 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 / runtime67-refs-retry | 9 / 9 | 0 / 0 | 9 / 9 | 7264 / 50720 | 0 |

## a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 / runtime67-refs-retry

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| DispatchFFNCombine / routed_ffn_native | 1280 | 0 / 1280 | 698.498 | 695.156 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| reduce_scatterAicpuKernel / unresolved | 1280 | 0 / 1280 | 139.964 | 130.797 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / unresolved | 2560 | 0 / 2560 | 35.523 | 35.380 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 1280 | 0 / 1280 | 60.656 | 61.758 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 2880 | 0 / 2880 | 22.883 | 21.530 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 2560 | 0 / 2560 | 23.246 | 23.800 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 4032 | 0 / 4032 | 11.371 | 14.160 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| InplacePartialRotaryMul / unresolved | 4352 | 0 / 4352 | 10.521 | 11.100 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1280 | 0 / 1280 | 34.502 | 34.380 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 1280 | 1280 / 0 | 21.261 | 21.279 | 15.975 | -5.286 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allGather_ / attention_output_communication | 1280 | 0 / 1280 | 20.591 | 17.349 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 1280 | 0 / 1280 | 20.300 | 19.459 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| HcPost / unresolved | 2560 | 0 / 2560 | 9.271 | 9.160 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_a | 1280 | 1280 / 0 | 18.041 | 18.019 | 10.363 | -7.678 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / kv_a | 1280 | 1280 / 0 | 17.469 | 17.399 | 7.124 | -10.344 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 1280 | 0 / 1280 | 16.927 | 16.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| VllmAscendQuantLightningIndexerV2 / unresolved | 160 | 0 / 160 | 129.227 | 145.887 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdateSk / unresolved | 1664 | 0 / 1664 | 12.255 | 12.140 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 1280 | 0 / 1280 | 7.510 | 7.100 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopKHash / unresolved | 1280 | 0 / 1280 | 7.087 | 6.880 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_a.quantize | 1280 | 1280 / 0 | 6.583 | 6.560 | 2.500 | -4.083 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DequantSwigluQuant / unresolved | 1280 | 0 / 1280 | 5.940 | 5.880 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_b.quantize | 1536 | 1536 / 0 | 4.948 | 4.920 | 2.500 | -2.448 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / unresolved | 1408 | 0 / 1408 | 4.632 | 4.700 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_indexer_indices_kernel / unresolved | 256 | 0 / 256 | 22.112 | 19.379 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNormCast / unresolved | 1280 | 0 / 1280 | 4.391 | 4.380 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| VllmAscendQuantLightningIndexerV2 / quant_lightning_indexer | 96 | 0 / 96 | 43.666 | 44.800 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 256 | 256 / 0 | 14.596 | 14.659 | 8.116 | -6.479 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_weights | 256 | 256 / 0 | 14.030 | 13.580 | 6.252 | -7.778 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SelectV2 / unresolved | 1280 | 0 / 1280 | 2.667 | 2.660 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _quantize_indexer_query_kernel / unresolved | 256 | 0 / 256 | 13.333 | 13.260 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 2016 | 0 / 2016 | 1.644 | 1.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 1280 | 0 / 1280 | 2.244 | 2.260 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 1280 | 0 / 1280 | 1.492 | 1.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 96 | 0 / 96 | 19.615 | 19.560 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| ReduceMean / unresolved | 96 | 0 / 96 | 13.877 | 13.560 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 64 | 64 / 0 | 14.162 | 14.180 | 2.500 | -11.662 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / compress_gates + compress_values | 32 | 32 / 0 | 22.501 | 22.540 | 14.109 | -8.392 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _pool_kernel / unresolved | 96 | 0 / 96 | 5.538 | 5.390 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _cache_update_kernel / unresolved | 96 | 0 / 96 | 5.134 | 5.110 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 96 | 0 / 96 | 4.608 | 4.600 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 256 | 0 / 256 | 1.629 | 1.609 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 / runtime67-refs-retry / DispatchFFNCombine / routed_ffn_native | 1280 | 0 | 0 | 1280 | 0 |
