# Complete Decode Body Operator Families

Only complete events inside the 225 accepted target-body windows from 6 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 / runtime67-refs | 9 / 9 | 0 / 0 | 9 / 9 | 7264 / 50720 | 0 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 / runtime67-refs | 9 / 9 | 0 / 0 | 9 / 9 | 4994 / 34892 | 0 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 / runtime67-refs | 9 / 9 | 0 / 0 | 9 / 9 | 10896 / 74160 | 0 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs | 9 / 9 | 0 / 0 | 9 / 9 | 4767 / 33306 | 0 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 / runtime67-refs | 9 / 9 | 0 / 0 | 9 / 9 | 6583 / 44805 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs | 18 / 18 | 0 / 0 | 18 / 18 | 42851 / 127446 | 0 |

## a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| DispatchFFNCombine / routed_ffn_native | 1280 | 0 / 1280 | 698.498 | 695.156 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
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

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| DispatchFFNCombine / routed_ffn_native / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 1280 | 698.498 / 695.156 | 924.931 | 27.940 | 36.997 | whole_routed_ffn_decomposed_program_reference |

## a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| DispatchFFNCombine / routed_ffn_native | 880 | 0 / 880 | 718.046 | 712.566 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
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

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| DispatchFFNCombine / routed_ffn_native / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 880 | 718.046 / 712.566 | 940.671 | 28.722 | 37.627 | whole_routed_ffn_decomposed_program_reference |

## a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| DispatchFFNCombine / routed_ffn_native | 1920 | 0 / 1920 | 712.078 | 695.766 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
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

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| DispatchFFNCombine / routed_ffn_native / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 1920 | 712.078 / 695.766 | 915.819 | 28.483 | 36.633 | whole_routed_ffn_decomposed_program_reference |

## a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| DispatchFFNCombine / routed_ffn_native | 840 | 0 / 840 | 718.428 | 712.576 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
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

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| DispatchFFNCombine / routed_ffn_native / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 840 | 718.428 / 712.576 | 972.699 | 28.737 | 38.908 | whole_routed_ffn_decomposed_program_reference |

## a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| DispatchFFNCombine / routed_ffn_native | 1160 | 0 / 1160 | 694.018 | 691.047 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
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

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| DispatchFFNCombine / routed_ffn_native / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 1160 | 694.018 / 691.047 | 921.873 | 27.761 | 36.875 | whole_routed_ffn_decomposed_program_reference |

## a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 2920 | 0 / 2920 | 250.141 | 248.818 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 2920 | 0 / 2920 | 123.273 | 122.228 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 2920 | 0 / 2920 | 34.021 | 34.734 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| QuantBatchMatmulV3 / grouped_output_b | 2920 | 2920 / 0 | 21.429 | 21.417 | 17.075 | -4.354 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 2920 | 0 / 2920 | 21.093 | 21.082 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 2920 | 0 / 2920 | 21.045 | 19.659 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| InplacePartialRotaryMul / unresolved | 9928 | 0 / 9928 | 5.095 | 5.294 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 2920 | 2920 / 0 | 16.909 | 16.807 | 11.131 | -5.777 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeDistributeCombineV3 / expert_combine_native | 2920 | 0 / 2920 | 15.402 | 15.216 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 3650 | 0 / 3650 | 11.519 | 11.223 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 2920 | 2920 / 0 | 12.334 | 12.320 | 10.723 | -1.611 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPre / ffn.hc_pre | 2920 | 0 / 2920 | 12.209 | 11.944 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| HcPre / attention.hc_pre | 2920 | 0 / 2920 | 12.178 | 12.002 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| SwigluGroupQuant / unresolved | 5840 | 0 / 5840 | 4.496 | 4.456 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 6278 | 0 / 6278 | 3.870 | 3.873 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 2920 | 2920 / 0 | 7.481 | 7.428 | 4.909 | -2.573 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| KvCompressEpilogV2 / unresolved | 3212 | 0 / 3212 | 6.121 | 6.165 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_a | 2920 | 2920 / 0 | 6.173 | 6.147 | 3.169 | -3.003 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 2920 | 0 / 2920 | 5.857 | 5.822 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopKHash / unresolved | 2920 | 0 / 2920 | 5.433 | 5.492 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 6644 | 0 / 6644 | 2.374 | 2.091 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 3066 | 0 / 3066 | 4.962 | 4.923 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 2920 | 2920 / 0 | 5.096 | 5.073 | 1.578 | -3.518 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 2920 | 2920 / 0 | 5.033 | 5.016 | 1.312 | -3.721 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / attention.hc_post_group | 2920 | 2920 / 0 | 4.907 | 4.881 | 1.312 | -3.595 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| MatMulV3 / index_weights | 584 | 584 / 0 | 12.241 | 12.175 | 2.508 | -9.734 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
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
| MatMulV3 / compress_gates + compress_values | 73 | 73 / 0 | 8.741 | 8.752 | 2.511 | -6.230 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 219 | 0 / 219 | 2.733 | 2.719 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 146 | 0 / 146 | 3.931 | 3.896 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 73 | 0 / 73 | 6.516 | 6.436 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 146 | 0 / 146 | 3.145 | 2.908 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalOr / unresolved | 146 | 0 / 146 | 1.902 | 1.539 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 73 | 0 / 73 | 2.637 | 2.603 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 73 | 0 / 73 | 2.153 | 2.085 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 2920 | 12.178 / 12.002 | 26.538 | 0.487 | 1.062 | partial_base_program_reference_premix_branch_unresolved |
| HcPre / ffn.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 2920 | 12.209 / 11.944 | 26.538 | 0.488 | 1.062 | partial_base_program_reference_premix_branch_unresolved |
| MqsmlaKernel___call__ / attention_core / layers 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 1460 | 35.488 / 35.584 | 25.248 | 0.710 | 0.505 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1314 | 34.016 / 33.648 | 25.248 | 0.612 | 0.454 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 0, 1 | 146 | 19.397 / 12.614 | 25.248 | 0.039 | 0.050 | source_symbol_to_declared_attention_program |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 / runtime67-refs / DispatchFFNCombine / routed_ffn_native | 1280 | 0 | 1280 | 0 | 0 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 / runtime67-refs / DispatchFFNCombine / routed_ffn_native | 880 | 0 | 880 | 0 | 0 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 / runtime67-refs / DispatchFFNCombine / routed_ffn_native | 1920 | 0 | 1920 | 0 | 0 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs / DispatchFFNCombine / routed_ffn_native | 840 | 0 | 840 | 0 | 0 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 / runtime67-refs / DispatchFFNCombine / routed_ffn_native | 1160 | 0 | 1160 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs / GroupedMatmul / expert_down | 2920 | 0 | 0 | 2920 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs / GroupedMatmul / expert_up | 2920 | 0 | 0 | 2920 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs / HcPre / attention.hc_pre | 2920 | 0 | 2920 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs / HcPre / ffn.hc_pre | 2920 | 0 | 2920 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs / MoeDistributeCombineV3 / expert_combine_native | 2920 | 0 | 0 | 2920 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs / MoeDistributeDispatchV3 / expert_dispatch_native | 2920 | 0 | 0 | 2920 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs / MqsmlaKernel___call__ / attention_core | 2920 | 0 | 2920 | 0 | 0 |
