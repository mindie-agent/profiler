# Complete Decode Body Operator Families

Only complete events inside the 48 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 / runtime67-refs-retry | 9 / 9 | 0 / 0 | 9 / 9 | 10896 / 74160 | 0 |

## a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 / runtime67-refs-retry

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| DispatchFFNCombine / routed_ffn_native | 1920 | 0 / 1920 | 712.078 | 695.766 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| reduce_scatterAicpuKernel / unresolved | 1920 | 0 / 1920 | 141.086 | 131.717 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / unresolved | 3840 | 0 / 3840 | 33.759 | 33.619 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 1920 | 0 / 1920 | 55.699 | 55.599 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 3840 | 0 / 3840 | 23.312 | 24.119 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 4320 | 0 / 4320 | 19.263 | 17.100 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 1920 | 0 / 1920 | 28.246 | 22.380 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 1920 | 0 / 1920 | 26.033 | 16.380 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| RmsNorm / unresolved | 6048 | 0 / 6048 | 7.304 | 7.949 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| InplacePartialRotaryMul / unresolved | 6528 | 0 / 6528 | 6.042 | 5.940 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdateSk / unresolved | 2496 | 0 / 2496 | 14.008 | 14.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 1920 | 1920 / 0 | 17.903 | 17.960 | 14.047 | -3.856 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 1920 | 0 / 1920 | 17.048 | 16.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_a | 1920 | 1920 / 0 | 16.827 | 16.860 | 7.897 | -8.930 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_reduceScatter_ / attention_output_communication | 1920 | 0 / 1920 | 16.642 | 16.620 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| HcPost / unresolved | 3840 | 0 / 3840 | 8.230 | 8.120 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 1920 | 1920 / 0 | 12.422 | 12.419 | 5.000 | -7.422 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| VllmAscendQuantLightningIndexerV2 / unresolved | 240 | 0 / 240 | 64.702 | 30.750 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_b.quantize | 2304 | 2304 / 0 | 5.004 | 4.940 | 2.500 | -2.504 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopKHash / unresolved | 1920 | 0 / 1920 | 5.684 | 5.460 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSwigluQuant / unresolved | 1920 | 0 / 1920 | 5.342 | 5.280 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_a.quantize | 1920 | 1920 / 0 | 5.237 | 5.220 | 2.500 | -2.737 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / unresolved | 2112 | 0 / 2112 | 4.099 | 4.180 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNormCast / unresolved | 1920 | 0 / 1920 | 3.498 | 3.460 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_indexer_indices_kernel / unresolved | 384 | 0 / 384 | 15.345 | 15.360 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 384 | 384 / 0 | 13.729 | 13.760 | 7.080 | -6.649 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 3024 | 0 / 3024 | 1.688 | 1.420 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 1920 | 0 / 1920 | 2.585 | 2.560 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / index_weights | 384 | 384 / 0 | 11.460 | 11.440 | 6.252 | -5.208 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| VllmAscendQuantLightningIndexerV2 / quant_lightning_indexer | 144 | 0 / 144 | 30.098 | 28.750 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 1920 | 0 / 1920 | 2.254 | 2.240 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _quantize_indexer_query_kernel / unresolved | 384 | 0 / 384 | 9.762 | 9.660 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 1920 | 0 / 1920 | 1.553 | 1.520 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 144 | 0 / 144 | 17.817 | 17.450 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| ReduceMean / unresolved | 144 | 0 / 144 | 13.222 | 13.419 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 96 | 96 / 0 | 9.023 | 8.810 | 2.500 | -6.523 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / compress_gates + compress_values | 48 | 48 / 0 | 13.047 | 13.040 | 9.391 | -3.657 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 384 | 0 / 384 | 1.572 | 1.579 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _cache_update_kernel / unresolved | 144 | 0 / 144 | 4.069 | 4.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pool_kernel / unresolved | 144 | 0 / 144 | 2.954 | 2.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 144 | 0 / 144 | 2.717 | 2.700 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 / runtime67-refs-retry / DispatchFFNCombine / routed_ffn_native | 1920 | 0 | 0 | 1920 | 0 |
