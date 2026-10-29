# Complete Decode Body Operator Families

Only complete events inside the 22 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 / runtime67-refs-retry | 9 / 9 | 0 / 0 | 9 / 9 | 4994 / 34892 | 0 |

## a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 / runtime67-refs-retry

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| DispatchFFNCombine / routed_ffn_native | 880 | 0 / 880 | 718.046 | 712.566 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| reduce_scatterAicpuKernel / unresolved | 880 | 0 / 880 | 137.674 | 130.977 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 1980 | 0 / 1980 | 49.733 | 71.388 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 880 | 0 / 880 | 86.497 | 85.129 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / unresolved | 1760 | 0 / 1760 | 37.257 | 37.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1760 | 0 / 1760 | 23.129 | 23.989 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / unresolved | 880 | 0 / 880 | 35.810 | 35.739 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 2772 | 0 / 2772 | 11.265 | 12.960 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| InplacePartialRotaryMul / unresolved | 2992 | 0 / 2992 | 9.605 | 9.960 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / attention_output_communication | 880 | 0 / 880 | 23.738 | 18.890 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 880 | 0 / 880 | 22.424 | 22.220 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| HcPost / unresolved | 1760 | 0 / 1760 | 10.722 | 10.560 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 880 | 880 / 0 | 21.201 | 21.240 | 18.546 | -2.655 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 880 | 0 / 880 | 17.043 | 16.590 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_a | 880 | 880 / 0 | 16.480 | 16.459 | 20.118 | 3.637 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| VllmAscendQuantLightningIndexerV2 / unresolved | 110 | 0 / 110 | 131.407 | 146.257 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 880 | 880 / 0 | 16.337 | 16.320 | 12.746 | -3.591 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterNdUpdateSk / unresolved | 1144 | 0 / 1144 | 12.525 | 12.450 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopKHash / unresolved | 880 | 0 / 880 | 9.615 | 9.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_a.quantize | 880 | 880 / 0 | 8.751 | 8.740 | 2.500 | -6.251 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TensorMove / unresolved | 902 | 0 / 902 | 7.368 | 7.200 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSwigluQuant / unresolved | 880 | 0 / 880 | 6.679 | 6.579 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / q_b.quantize | 1056 | 1056 / 0 | 5.108 | 5.080 | 2.500 | -2.608 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _prepare_indexer_indices_kernel / unresolved | 176 | 0 / 176 | 29.410 | 29.039 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNormCast / unresolved | 880 | 0 / 880 | 5.871 | 5.740 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / unresolved | 968 | 0 / 968 | 5.213 | 5.260 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _quantize_indexer_query_kernel / unresolved | 176 | 0 / 176 | 17.571 | 17.520 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 176 | 176 / 0 | 15.689 | 15.650 | 9.498 | -6.190 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| VllmAscendQuantLightningIndexerV2 / quant_lightning_indexer | 66 | 0 / 66 | 40.407 | 40.369 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 880 | 0 / 880 | 2.930 | 2.920 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / index_weights | 176 | 176 / 0 | 14.121 | 13.779 | 6.253 | -7.868 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 1386 | 0 / 1386 | 1.738 | 1.420 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 880 | 0 / 880 | 2.290 | 2.280 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 880 | 0 / 880 | 1.496 | 1.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 66 | 0 / 66 | 19.807 | 19.750 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| ReduceMean / unresolved | 66 | 0 / 66 | 13.012 | 12.890 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 44 | 44 / 0 | 13.034 | 13.040 | 2.500 | -10.534 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / compress_gates + compress_values | 22 | 22 / 0 | 23.889 | 23.860 | 25.112 | 1.223 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 66 | 0 / 66 | 7.032 | 7.040 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pool_kernel / unresolved | 66 | 0 / 66 | 6.167 | 6.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _cache_update_kernel / unresolved | 66 | 0 / 66 | 5.651 | 5.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 176 | 0 / 176 | 1.832 | 1.820 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 / runtime67-refs-retry / DispatchFFNCombine / routed_ffn_native | 880 | 0 | 0 | 880 | 0 |
