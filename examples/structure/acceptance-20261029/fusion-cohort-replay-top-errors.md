# Complete-Capture Operator Families And Conditional Errors

Historical captures replayed locally; no new live collection.

The event denominator is every valid positive-duration event in the complete capture window. Activity sums add event intersections separately, including overlapping events. Every native type remains in the JSON tables, including types with no valid cohort. This readable view shows the 20 highest measured-activity families per declaration (event count when old mapping metadata has no activity total), plus all subgraph cohorts. Errors cover only scored events; activity sums are not wall-clock latency or throughput.

Several declarations may reuse one capture. Their event totals are not independent and must not be added as additional captures.

## a3_glm53_prefill / source_declared_unfused_reference

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:b791771d7482c37285717afaa86d276b457748a9faa4ce52351deddb6957b46d`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 157 | 1552.089 | 0 | - | - | - | no_tensor_candidates (157) |
| SparseFlashAttention | 78 | 1029.574 | 78 | 1029.574 | 477.452 | -53.6% |  |
| MlaPrologV3 | 78 | 99.338 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (78) |
| GroupedMatmulSwigluQuantV2 | 75 | 99.235 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (75) |
| hcom_allReduce_ | 157 | 93.667 | 0 | - | - | - | no_tensor_candidates (157) |
| GroupedMatmul | 75 | 91.894 | 0 | - | - | - | quantized_epilogue_unmodeled (75) |
| QuantBatchMatmulV3 | 255 | 51.931 | 180 | 46.254 | 34.289 | -25.9% | no_tensor_candidates (75) |
| AddRmsNormBias | 153 | 37.924 | 153 | 37.924 | 25.674 | -32.3% |  |
| MoeTokenUnpermute | 75 | 37.376 | 0 | - | - | - | no_tensor_candidates (75) |
| LightningIndexer | 21 | 31.342 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (21) |
| MoeInitRoutingV3 | 75 | 24.498 | 0 | - | - | - | no_tensor_candidates (75) |
| DynamicQuant | 234 | 16.527 | 234 | 16.527 | 11.312 | -31.6% |  |
| ForeachAddList | 75 | 10.799 | 0 | - | - | - | no_tensor_candidates (75) |
| Muls | 75 | 9.240 | 0 | - | - | - | no_tensor_candidates (75) |
| MoeGatingTopK | 75 | 7.627 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (75) |
| MatMulV3 | 75 | 7.599 | 0 | - | - | - | no_tensor_candidates (75) |
| TensorMove | 104 | 6.961 | 0 | - | - | - | no_tensor_candidates (104) |
| _triton_rope_siso | 42 | 6.517 | 0 | - | - | - | no_tensor_candidates (42) |
| TransposeBatchMatMul | 78 | 5.432 | 78 | 5.432 | 3.582 | -34.1% |  |
| MatMulV2 | 22 | 2.564 | 1 | 0.339 | 0.198 | -41.5% | no_tensor_candidates (21) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| MlaPrologV3 | 26f6df125e3c | 21 | reference_only | 1.342506 | 0.491634 | - |
| MlaPrologV3 | 504e5a1976c8 | 57 | reference_only | 1.248166 | 0.491634 | - |
| GroupedMatmulSwigluQuantV2 | 87bd657716f3 | 75 | reference_only | 1.323133 | 0.600368 | - |
| LightningIndexer | 07fd62672b7e | 21 | reference_only | 1.492464 | 1.873906 | - |
| MoeGatingTopK | c44f03df1316 | 75 | reference_only | 0.101699 | 0.011181 | - |

## a3_glm53_prefill / selected_native_fusion

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:c59d4cdf682919a09521ff275beb2e233e1b0dbdbfe6016d212cbc4c6d56ab88`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 157 | 1552.089 | 0 | - | - | - | no_tensor_candidates (157) |
| SparseFlashAttention | 78 | 1029.574 | 78 | 1029.574 | 477.452 | -53.6% |  |
| MlaPrologV3 | 78 | 99.338 | 78 | 99.338 | 37.287 | -62.5% |  |
| GroupedMatmulSwigluQuantV2 | 75 | 99.235 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (75) |
| hcom_allReduce_ | 157 | 93.667 | 0 | - | - | - | no_tensor_candidates (157) |
| GroupedMatmul | 75 | 91.894 | 0 | - | - | - | quantized_epilogue_unmodeled (75) |
| QuantBatchMatmulV3 | 255 | 51.931 | 180 | 46.254 | 34.289 | -25.9% | no_tensor_candidates (75) |
| AddRmsNormBias | 153 | 37.924 | 153 | 37.924 | 25.674 | -32.3% |  |
| MoeTokenUnpermute | 75 | 37.376 | 0 | - | - | - | no_tensor_candidates (75) |
| LightningIndexer | 21 | 31.342 | 21 | 31.342 | 39.352 | +25.6% |  |
| MoeInitRoutingV3 | 75 | 24.498 | 0 | - | - | - | no_tensor_candidates (75) |
| DynamicQuant | 234 | 16.527 | 234 | 16.527 | 11.312 | -31.6% |  |
| ForeachAddList | 75 | 10.799 | 0 | - | - | - | no_tensor_candidates (75) |
| Muls | 75 | 9.240 | 0 | - | - | - | no_tensor_candidates (75) |
| MoeGatingTopK | 75 | 7.627 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (75) |
| MatMulV3 | 75 | 7.599 | 0 | - | - | - | no_tensor_candidates (75) |
| TensorMove | 104 | 6.961 | 0 | - | - | - | no_tensor_candidates (104) |
| _triton_rope_siso | 42 | 6.517 | 0 | - | - | - | no_tensor_candidates (42) |
| TransposeBatchMatMul | 78 | 5.432 | 78 | 5.432 | 3.582 | -34.1% |  |
| MatMulV2 | 22 | 2.564 | 1 | 0.339 | 0.198 | -41.5% | no_tensor_candidates (21) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| MlaPrologV3 | 09437c2af0db | 21 | compared | 1.342506 | 0.478035 | -64.4% |
| MlaPrologV3 | 366f9ca23420 | 57 | compared | 1.248166 | 0.478035 | -61.7% |
| GroupedMatmulSwigluQuantV2 | a56f5848ad62 | 75 | reference_only | 1.323133 | 0.600368 | - |
| LightningIndexer | 0dc9669cc5b8 | 21 | compared | 1.492464 | 1.873906 | +25.6% |
| MoeGatingTopK | 69d4c574e5d8 | 75 | reference_only | 0.101699 | 0.011181 | - |

## a3_glm53_decode / source_declared_unfused_reference

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:5511e36128cfcd1456dae497732a2e2fcf72de5b73293c4cbb5ed077ff44a2dd`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 11618 | 1977.841 | 0 | - | - | - | no_tensor_candidates (11618) |
| SparseFlashAttention | 5772 | 523.698 | 5772 | 523.698 | 11.471 | -97.8% |  |
| GroupedMatmulSwigluQuantV2 | 5550 | 488.615 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (5550) |
| QuantBatchMatmulV3 | 18870 | 310.039 | 13320 | 237.111 | 84.645 | -64.3% | no_tensor_candidates (5550) |
| hcom_allReduce_ | 11618 | 300.822 | 0 | - | - | - | no_tensor_candidates (11618) |
| GroupedMatmul | 5550 | 293.637 | 0 | - | - | - | quantized_epilogue_unmodeled (5550) |
| MlaPrologV3 | 5772 | 236.735 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (5772) |
| Slice | 296 | 107.526 | 0 | - | - | - | no_tensor_candidates (296) |
| ForeachAddList | 5550 | 91.679 | 0 | - | - | - | no_tensor_candidates (5550) |
| TransposeBatchMatMul | 5772 | 81.808 | 5772 | 81.808 | 10.160 | -87.6% |  |
| MatMulV3 | 5550 | 81.786 | 0 | - | - | - | no_tensor_candidates (5550) |
| MoeInitRoutingV3 | 5550 | 71.053 | 0 | - | - | - | no_tensor_candidates (5550) |
| DynamicQuant | 17316 | 50.444 | 17316 | 50.444 | 0.204 | -99.6% |  |
| AddRmsNormBias | 11322 | 44.742 | 11322 | 44.742 | 0.696 | -98.4% |  |
| MatMulV2 | 1628 | 39.855 | 74 | 16.027 | 14.674 | -8.4% | no_tensor_candidates (1554) |
| LightningIndexer | 1554 | 38.703 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (1554) |
| MoeTokenUnpermute | 5550 | 26.160 | 0 | - | - | - | no_tensor_candidates (5550) |
| MoeGatingTopK | 5550 | 22.270 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (5550) |
| DequantSwigluQuant | 5550 | 18.782 | 0 | - | - | - | no_tensor_candidates (5550) |
| ScatterNdUpdateSk | 1554 | 13.891 | 0 | - | - | - | no_tensor_candidates (1554) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| GroupedMatmulSwigluQuantV2 | 99339ed3fe9e | 5550 | reference_only | 0.088039 | 0.010572 | - |
| MlaPrologV3 | f16038273967 | 1554 | reference_only | 0.041291 | 0.018338 | - |
| MlaPrologV3 | 64ddb783e6c8 | 4218 | reference_only | 0.040913 | 0.018338 | - |
| LightningIndexer | c343274adfb8 | 1554 | reference_only | 0.024905 | 0.000909 | - |
| MoeGatingTopK | adcee4917af0 | 5550 | reference_only | 0.004013 | 0.000003 | - |

## a3_glm53_decode / selected_native_fusion

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:45a83f71659e42cd95c3b37d9a2bcf243f6f484461ef6c1edee9b64298f34a92`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 11618 | 1977.841 | 0 | - | - | - | no_tensor_candidates (11618) |
| SparseFlashAttention | 5772 | 523.698 | 5772 | 523.698 | 11.471 | -97.8% |  |
| GroupedMatmulSwigluQuantV2 | 5550 | 488.615 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (5550) |
| QuantBatchMatmulV3 | 18870 | 310.039 | 13320 | 237.111 | 84.645 | -64.3% | no_tensor_candidates (5550) |
| hcom_allReduce_ | 11618 | 300.822 | 0 | - | - | - | no_tensor_candidates (11618) |
| GroupedMatmul | 5550 | 293.637 | 0 | - | - | - | quantized_epilogue_unmodeled (5550) |
| MlaPrologV3 | 5772 | 236.735 | 5772 | 236.735 | 105.791 | -55.3% |  |
| Slice | 296 | 107.526 | 0 | - | - | - | no_tensor_candidates (296) |
| ForeachAddList | 5550 | 91.679 | 0 | - | - | - | no_tensor_candidates (5550) |
| TransposeBatchMatMul | 5772 | 81.808 | 5772 | 81.808 | 10.160 | -87.6% |  |
| MatMulV3 | 5550 | 81.786 | 0 | - | - | - | no_tensor_candidates (5550) |
| MoeInitRoutingV3 | 5550 | 71.053 | 0 | - | - | - | no_tensor_candidates (5550) |
| DynamicQuant | 17316 | 50.444 | 17316 | 50.444 | 0.204 | -99.6% |  |
| AddRmsNormBias | 11322 | 44.742 | 11322 | 44.742 | 0.696 | -98.4% |  |
| MatMulV2 | 1628 | 39.855 | 74 | 16.027 | 14.674 | -8.4% | no_tensor_candidates (1554) |
| LightningIndexer | 1554 | 38.703 | 1554 | 38.703 | 1.413 | -96.4% |  |
| MoeTokenUnpermute | 5550 | 26.160 | 0 | - | - | - | no_tensor_candidates (5550) |
| MoeGatingTopK | 5550 | 22.270 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (5550) |
| DequantSwigluQuant | 5550 | 18.782 | 0 | - | - | - | no_tensor_candidates (5550) |
| ScatterNdUpdateSk | 1554 | 13.891 | 0 | - | - | - | no_tensor_candidates (1554) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| GroupedMatmulSwigluQuantV2 | 24298bdf0c67 | 5550 | reference_only | 0.088039 | 0.010572 | - |
| MlaPrologV3 | ed0632626ec0 | 1554 | compared | 0.041291 | 0.018328 | -55.6% |
| MlaPrologV3 | 9583c555d50b | 4218 | compared | 0.040913 | 0.018328 | -55.2% |
| LightningIndexer | cf9b4fd5048b | 1554 | compared | 0.024905 | 0.000909 | -96.4% |
| MoeGatingTopK | 338ad5d07bbe | 5550 | reference_only | 0.004013 | 0.000003 | - |

## a3_qwen35 / case_default

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:c8d0db9443f604bc6678e6bbd4d473f47fd1a793545f4cc6e62829302b89bfea`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 5628 | 913.004 | 0 | - | - | - | no_tensor_candidates (5628) |
| GroupedMatmulSwigluQuant | 2680 | 217.099 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (2680) |
| MatMulV2 | 17879 | 190.026 | 315 | 28.121 | 23.186 | -17.5% | no_tensor_candidates (17564) |
| GroupedMatmul | 2814 | 178.155 | 80 | 55.146 | 25.818 | -53.2% | no_tensor_candidates (2734) |
| hcom_allReduce_ | 5628 | 159.599 | 0 | - | - | - | no_tensor_candidates (5628) |
| Cumsum | 2680 | 130.645 | 0 | - | - | - | no_tensor_candidates (2680) |
| ChunkGatedDeltaRuleFwd | 60 | 78.393 | 0 | - | - | - | no_tensor_candidates (60) |
| FusedInferAttentionScore | 737 | 75.245 | 11 | 9.699 | 5.593 | -42.3% | no_tensor_candidates (726) |
| MoeInitRoutingV3 | 2747 | 72.001 | 0 | - | - | - | no_tensor_candidates (2747) |
| AddRmsNormBias | 5494 | 51.285 | 0 | - | - | - | no_tensor_candidates (5494) |
| ForeachAddList | 2747 | 50.085 | 0 | - | - | - | no_tensor_candidates (2747) |
| MoeTokenUnpermute | 2747 | 42.820 | 0 | - | - | - | no_tensor_candidates (2747) |
| MatMulV3 | 144 | 38.849 | 0 | - | - | - | no_tensor_candidates (144) |
| allgatherAicpuKernel | 201 | 37.228 | 0 | - | - | - | no_tensor_candidates (201) |
| MoeGatingTopK | 2747 | 32.163 | 82 | 19.997 | 0.651 | -96.7% | no_tensor_candidates (2665) |
| RecurrentGatedDeltaRule | 1950 | 31.545 | 0 | - | - | - | no_tensor_candidates (1950) |
| Slice | 15500 | 31.495 | 0 | - | - | - | no_tensor_candidates (15500) |
| Mul | 3752 | 30.330 | 0 | - | - | - | no_tensor_candidates (3752) |
| CausalConv1d | 2010 | 24.882 | 0 | - | - | - | no_tensor_candidates (2010) |
| fused_gdn_gating_kernel | 2010 | 20.774 | 60 | 1.785 | 0.033 | -98.2% | no_tensor_candidates (1950) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| GroupedMatmulSwigluQuant | e3c52f7cd05a | 2680 | reference_only | 0.081007 | 0.344126 | - |
| MoeGatingTopK | ce8133c583e0 | 82 | compared | 0.243864 | 0.007944 | -96.7% |

## a3_qwen36 / case_default

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:7527b4310d3beb047e6a1d95e083df0fbaf6d77ebbe85aa09d65dbf4049e118d`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 2346 | 1284.175 | 0 | - | - | - | no_tensor_candidates (2346) |
| QuantBatchMatmulV3 | 3740 | 535.605 | 402 | 422.311 | 415.350 | -1.6% | no_tensor_candidates (3300), candidate_physical_work_differs (38) |
| hcom_allReduce_ | 2346 | 233.875 | 0 | - | - | - | no_tensor_candidates (2346) |
| ChunkGatedDeltaRuleFwd | 96 | 164.082 | 0 | - | - | - | no_tensor_candidates (96) |
| AddRmsNormBias | 2278 | 107.967 | 0 | - | - | - | no_tensor_candidates (2278) |
| FusedInferAttentionScore | 323 | 100.845 | 17 | 21.614 | 12.966 | -40.0% | no_tensor_candidates (306) |
| MatMulV2 | 1649 | 75.506 | 53 | 29.339 | 28.083 | -4.3% | no_tensor_candidates (1596) |
| DynamicQuant | 3740 | 66.998 | 440 | 53.447 | 41.253 | -22.8% | no_tensor_candidates (3300) |
| MatMulV3 | 102 | 57.571 | 0 | - | - | - | no_tensor_candidates (102) |
| allgatherAicpuKernel | 119 | 34.120 | 0 | - | - | - | no_tensor_candidates (119) |
| SwiGlu | 1139 | 32.301 | 134 | 28.000 | 23.887 | -14.7% | no_tensor_candidates (1005) |
| CausalConv1d | 816 | 27.117 | 0 | - | - | - | no_tensor_candidates (816) |
| Slice | 6106 | 23.423 | 0 | - | - | - | no_tensor_candidates (6106) |
| Transpose | 1028 | 22.152 | 0 | - | - | - | no_tensor_candidates (1028) |
| RecurrentGatedDeltaRule | 720 | 18.515 | 0 | - | - | - | no_tensor_candidates (720) |
| split_qkv_rmsnorm_mrope_kernel | 323 | 16.850 | 0 | - | - | - | no_tensor_candidates (323) |
| _layer_norm_fwd_1pass_kernel_npu | 816 | 13.821 | 96 | 10.352 | 6.040 | -41.7% | no_tensor_candidates (720) |
| Index | 673 | 12.506 | 0 | - | - | - | no_tensor_candidates (673) |
| fused_gdn_gating_kernel | 816 | 12.109 | 96 | 4.216 | 0.079 | -98.1% | no_tensor_candidates (720) |
| TensorMove | 285 | 8.786 | 0 | - | - | - | no_tensor_candidates (285) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| - | - | 0 | No valid subgraph cohort | - | - | - |

## a3_v4f / case_default

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:ccdf3b27ef091aef68ebbe9a296126ba56835705763d21530fa9686ea03677d7`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| SparseAttnSharedkv | 44 | 98.897 | 3 | 1.467 | 0.178 | -87.9% | candidate_physical_work_differs (41) |
| hcom_alltoallv_ | 264 | 64.783 | 0 | - | - | - | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | - | - | - | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | - | - | - | no_tensor_candidates (90) |
| HcPre | 88 | 37.975 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (88) |
| HcPost | 88 | 36.817 | 88 | 36.817 | 22.170 | -39.8% |  |
| QuantBatchMatmulV3 | 241 | 28.176 | 109 | 15.331 | 14.036 | -8.4% | candidate_physical_work_differs (88), no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 0 | - | - | - | no_tensor_candidates (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | - | - | - | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 46 | 4.105 | 2.573 | -37.3% | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 197 | 10.220 | 5.759 | -43.6% | no_tensor_candidates (42) |
| MatMulV2 | 110 | 12.384 | 88 | 11.809 | 9.528 | -19.3% | no_tensor_candidates (22) |
| GroupedMatmul | 44 | 10.988 | 0 | - | - | - | no_tensor_candidates (44) |
| allgatherAicpuKernel | 44 | 10.441 | 0 | - | - | - | no_tensor_candidates (44) |
| ScatterNdUpdateSk | 127 | 9.996 | 0 | - | - | - | no_tensor_candidates (127) |
| MatMulV3 | 47 | 9.758 | 0 | - | - | - | no_tensor_candidates (47) |
| TensorMove | 446 | 8.914 | 0 | - | - | - | no_tensor_candidates (446) |
| VllmAscendQuantLightningIndexerV2 | 21 | 8.380 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (21) |
| TransposeBatchMatMul | 44 | 7.473 | 0 | - | - | - | no_tensor_candidates (44) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| HcPre | de7bcab3f8d9 | 88 | reference_only | 0.431534 | 0.926170 | - |
| HcPost | 4fdc62318f10 | 88 | compared | 0.418375 | 0.251931 | -39.8% |
| GroupedMatmulSwigluQuant | c0ab2e7830dd | 44 | reference_only | 0.588788 | 5.681584 | - |
| VllmAscendQuantLightningIndexerV2 | 675e38568a80 | 21 | reference_only | 0.399030 | 0.248045 | - |

## a3_v4f / selected_native_fusion

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:e3c6926ee6f4db6d2b708bab1e3d82b51f14d46e7520bcbc63eb7fdd12cc8813`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| SparseAttnSharedkv | 44 | 98.897 | 3 | 1.467 | 0.178 | -87.9% | candidate_physical_work_differs (41) |
| hcom_alltoallv_ | 264 | 64.783 | 0 | - | - | - | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | - | - | - | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | - | - | - | no_tensor_candidates (90) |
| HcPre | 88 | 37.975 | 88 | 37.975 | 81.459 | +114.5% |  |
| HcPost | 88 | 36.817 | 88 | 36.817 | 22.170 | -39.8% |  |
| QuantBatchMatmulV3 | 241 | 28.176 | 109 | 15.331 | 14.036 | -8.4% | candidate_physical_work_differs (88), no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 0 | - | - | - | no_tensor_candidates (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | - | - | - | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 46 | 4.105 | 2.573 | -37.3% | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 197 | 10.220 | 5.759 | -43.6% | no_tensor_candidates (42) |
| MatMulV2 | 110 | 12.384 | 88 | 11.809 | 9.528 | -19.3% | no_tensor_candidates (22) |
| GroupedMatmul | 44 | 10.988 | 0 | - | - | - | no_tensor_candidates (44) |
| allgatherAicpuKernel | 44 | 10.441 | 0 | - | - | - | no_tensor_candidates (44) |
| ScatterNdUpdateSk | 127 | 9.996 | 0 | - | - | - | no_tensor_candidates (127) |
| MatMulV3 | 47 | 9.758 | 0 | - | - | - | no_tensor_candidates (47) |
| TensorMove | 446 | 8.914 | 0 | - | - | - | no_tensor_candidates (446) |
| VllmAscendQuantLightningIndexerV2 | 21 | 8.380 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (21) |
| TransposeBatchMatMul | 44 | 7.473 | 0 | - | - | - | no_tensor_candidates (44) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| HcPre | 149afca4eb26 | 88 | compared | 0.431534 | 0.925671 | +114.5% |
| HcPost | c5b24bc1ef61 | 88 | compared | 0.418375 | 0.251931 | -39.8% |
| GroupedMatmulSwigluQuant | 74df649fcb44 | 44 | reference_only | 0.588788 | 5.681584 | - |
| VllmAscendQuantLightningIndexerV2 | 36ab9031b9eb | 21 | reference_only | 0.399030 | 0.248045 | - |

## a3_v4pro / case_default

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:2d5c508b966fd7cf5926c01c57736bfe5e093da8ea755c718f8c500d0adbce23`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| hcom_allReduce_ | 1008 | 963.972 | 0 | - | - | - | no_tensor_candidates (1008) |
| hcom_alltoallv_ | 1488 | 429.531 | 0 | - | - | - | no_tensor_candidates (1488) |
| hcom_allGather_ | 760 | 420.935 | 0 | - | - | - | no_tensor_candidates (760) |
| SparseAttnSharedkv | 248 | 174.437 | 0 | - | - | - | candidate_physical_work_differs (244), no_tensor_candidates (4) |
| HcPost | 496 | 100.241 | 496 | 100.241 | 54.644 | -45.5% |  |
| GroupedMatmulSwigluQuantV2 | 248 | 98.114 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (248) |
| HcPre | 496 | 95.134 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (496) |
| QuantBatchMatmulV3 | 1360 | 90.278 | 1112 | 80.102 | 57.700 | -28.0% | no_tensor_candidates (248) |
| Compressor | 364 | 77.516 | 0 | - | - | - | no_tensor_candidates (364) |
| allgatherAicpuKernel | 248 | 75.079 | 0 | - | - | - | no_tensor_candidates (248) |
| GroupedMatmul | 248 | 60.731 | 0 | - | - | - | no_tensor_candidates (248) |
| RmsNorm | 1016 | 43.695 | 256 | 10.399 | 6.267 | -39.7% | no_tensor_candidates (760) |
| DynamicQuant | 1352 | 37.072 | 1112 | 28.955 | 12.258 | -57.7% | no_tensor_candidates (240) |
| MatMulV2 | 616 | 35.772 | 496 | 34.799 | 37.786 | +8.6% | no_tensor_candidates (120) |
| MatMulV3 | 264 | 32.596 | 0 | - | - | - | no_tensor_candidates (264) |
| TensorMove | 4488 | 29.113 | 0 | - | - | - | no_tensor_candidates (4488) |
| InplacePartialRotaryMul | 864 | 17.121 | 0 | - | - | - | no_tensor_candidates (864) |
| TransposeBatchMatMul | 248 | 15.726 | 0 | - | - | - | no_tensor_candidates (248) |
| RmsNormCast | 248 | 13.898 | 0 | - | - | - | no_tensor_candidates (248) |
| VllmAscendQuantLightningIndexerV2 | 120 | 13.611 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (120) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| HcPost | 3b8c46e4b281 | 496 | compared | 0.202098 | 0.110169 | -45.5% |
| GroupedMatmulSwigluQuantV2 | 792bdaa6aad9 | 248 | reference_only | 0.395623 | 0.805300 | - |
| HcPre | 27c52baf6177 | 496 | reference_only | 0.191803 | 0.451742 | - |
| VllmAscendQuantLightningIndexerV2 | aead89290e26 | 120 | reference_only | 0.113425 | 0.018539 | - |

## a3_v4pro / selected_native_fusion

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:b923c8c76e939da2bc0cf16de60c422006eb80196b321a21516e8bf1b71655fa`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| hcom_allReduce_ | 1008 | 963.972 | 0 | - | - | - | no_tensor_candidates (1008) |
| hcom_alltoallv_ | 1488 | 429.531 | 0 | - | - | - | no_tensor_candidates (1488) |
| hcom_allGather_ | 760 | 420.935 | 0 | - | - | - | no_tensor_candidates (760) |
| SparseAttnSharedkv | 248 | 174.437 | 0 | - | - | - | candidate_physical_work_differs (244), no_tensor_candidates (4) |
| HcPost | 496 | 100.241 | 496 | 100.241 | 54.644 | -45.5% |  |
| GroupedMatmulSwigluQuantV2 | 248 | 98.114 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (248) |
| HcPre | 496 | 95.134 | 496 | 95.134 | 201.574 | +111.9% |  |
| QuantBatchMatmulV3 | 1360 | 90.278 | 1112 | 80.102 | 57.700 | -28.0% | no_tensor_candidates (248) |
| Compressor | 364 | 77.516 | 0 | - | - | - | no_tensor_candidates (364) |
| allgatherAicpuKernel | 248 | 75.079 | 0 | - | - | - | no_tensor_candidates (248) |
| GroupedMatmul | 248 | 60.731 | 0 | - | - | - | no_tensor_candidates (248) |
| RmsNorm | 1016 | 43.695 | 256 | 10.399 | 6.267 | -39.7% | no_tensor_candidates (760) |
| DynamicQuant | 1352 | 37.072 | 1112 | 28.955 | 12.258 | -57.7% | no_tensor_candidates (240) |
| MatMulV2 | 616 | 35.772 | 496 | 34.799 | 37.786 | +8.6% | no_tensor_candidates (120) |
| MatMulV3 | 264 | 32.596 | 0 | - | - | - | no_tensor_candidates (264) |
| TensorMove | 4488 | 29.113 | 0 | - | - | - | no_tensor_candidates (4488) |
| InplacePartialRotaryMul | 864 | 17.121 | 0 | - | - | - | no_tensor_candidates (864) |
| TransposeBatchMatMul | 248 | 15.726 | 0 | - | - | - | no_tensor_candidates (248) |
| RmsNormCast | 248 | 13.898 | 0 | - | - | - | no_tensor_candidates (248) |
| VllmAscendQuantLightningIndexerV2 | 120 | 13.611 | 0 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (120) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| HcPost | 79269415aaa2 | 496 | compared | 0.202098 | 0.110169 | -45.5% |
| GroupedMatmulSwigluQuantV2 | 61550d1dc9a2 | 248 | reference_only | 0.395623 | 0.805300 | - |
| HcPre | 2fe1837feca2 | 496 | compared | 0.191803 | 0.406399 | +111.9% |
| VllmAscendQuantLightningIndexerV2 | 91de2f507799 | 120 | reference_only | 0.113425 | 0.018539 | - |

## a5_kimi_k3 / case_default

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:b67b7d3c3422c9db6f6854198367166850d897db40b59a2744ab9904dd363dc7`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| hcom_alltoallv_AicpuKernel | 1104 | 919.190 | 0 | - | - | - | no_tensor_candidates (1104) |
| ChunkKdaFwd | 1104 | 881.998 | 0 | - | - | - | no_tensor_candidates (1104) |
| GroupedMatmul | 27248 | 813.481 | 0 | - | - | - | no_tensor_candidates (27248) |
| HcclLaunchAicpuKernel | 1543 | 683.214 | 0 | - | - | - | no_tensor_candidates (1543) |
| GroupedMatmulSituQuant | 7266 | 666.877 | 0 | - | - | - | no_tensor_candidates (7266) |
| MatMulV3 | 21819 | 656.394 | 0 | - | - | - | no_tensor_candidates (21656), candidate_physical_work_differs (96) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | - | - | - | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 0 | - | - | - | no_tensor_candidates (7266) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 0 | - | - | - | no_tensor_candidates (14531) |
| hcom_allGather_ | 15203 | 409.082 | 0 | - | - | - | no_tensor_candidates (15203) |
| MatmulReduceScatterV2 | 372 | 344.763 | 0 | - | - | - | no_tensor_candidates (372) |
| FusedInferAttentionScore | 1966 | 331.488 | 0 | - | - | - | no_tensor_candidates (1966) |
| AttnResFwd | 14768 | 245.588 | 0 | - | - | - | no_tensor_candidates (14768) |
| hcom_reduceScatter_ | 13945 | 182.792 | 0 | - | - | - | no_tensor_candidates (13945) |
| hcom_reduceScatter_AicpuKernel | 372 | 171.224 | 0 | - | - | - | no_tensor_candidates (372) |
| MoeDistributeDispatchV3 | 6898 | 168.750 | 0 | - | - | - | no_tensor_candidates (6898) |
| DynamicMxQuant | 22499 | 166.851 | 0 | - | - | - | no_tensor_candidates (22499) |
| Cast | 10332 | 100.414 | 0 | - | - | - | no_tensor_candidates (10332) |
| MoeDistributeCombineV3 | 6897 | 98.662 | 0 | - | - | - | no_tensor_candidates (6897) |
| PadV3 | 17616 | 65.378 | 0 | - | - | - | no_tensor_candidates (17616) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| - | - | 0 | No valid subgraph cohort | - | - | - |

## a5_kimi_k3_decode / source_declared_unfused_reference

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:c1b63a290d169ad9e6ae0c7a6423667c04853ec1a2a205a3c6a48ceb7efb5f88`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| hcom_alltoallv_AicpuKernel | 1104 | 919.190 | 0 | - | - | - | no_tensor_candidates (1104) |
| ChunkKdaFwd | 1104 | 881.998 | 0 | - | - | - | no_tensor_candidates (1104) |
| GroupedMatmul | 27248 | 813.481 | 0 | - | - | - | no_tensor_candidates (27248) |
| HcclLaunchAicpuKernel | 1543 | 683.214 | 0 | - | - | - | no_tensor_candidates (1543) |
| GroupedMatmulSituQuant | 7266 | 666.877 | 0 | - | - | - | no_tensor_candidates (7266) |
| MatMulV3 | 21819 | 656.394 | 0 | - | - | - | no_tensor_candidates (12981), candidate_physical_work_differs (8771) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | - | - | - | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 0 | - | - | - | no_tensor_candidates (7266) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 0 | - | - | - | no_tensor_candidates (14531) |
| hcom_allGather_ | 15203 | 409.082 | 0 | - | - | - | no_tensor_candidates (15203) |
| MatmulReduceScatterV2 | 372 | 344.763 | 0 | - | - | - | no_tensor_candidates (372) |
| FusedInferAttentionScore | 1966 | 331.488 | 0 | - | - | - | no_tensor_candidates (1966) |
| AttnResFwd | 14768 | 245.588 | 0 | - | - | - | no_tensor_candidates (14768) |
| hcom_reduceScatter_ | 13945 | 182.792 | 0 | - | - | - | no_tensor_candidates (13945) |
| hcom_reduceScatter_AicpuKernel | 372 | 171.224 | 0 | - | - | - | no_tensor_candidates (372) |
| MoeDistributeDispatchV3 | 6898 | 168.750 | 0 | - | - | - | no_tensor_candidates (6898) |
| DynamicMxQuant | 22499 | 166.851 | 0 | - | - | - | no_tensor_candidates (22499) |
| Cast | 10332 | 100.414 | 0 | - | - | - | no_tensor_candidates (10332) |
| MoeDistributeCombineV3 | 6897 | 98.662 | 0 | - | - | - | no_tensor_candidates (6897) |
| PadV3 | 17616 | 65.378 | 0 | - | - | - | no_tensor_candidates (17616) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| - | - | 0 | No valid subgraph cohort | - | - | - |

## a5_qwen38 / case_default

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:adf2d50a3280ffcd34219075c500fa232f93247c25e0ef0d4979a4ed6e99cf96`.

| Native family | All events | All activity ms | Scored events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| QuantBatchMatmulV3 | 1920 | 781.406 | 160 | 714.307 | 1253.383 | +75.5% | no_tensor_candidates (1760) |
| MatMulV3 | 1956 | 611.956 | 184 | 458.381 | 749.773 | +63.6% | no_tensor_candidates (1772) |
| FusedInferAttentionScore | 228 | 243.894 | 17 | 213.742 | 129.650 | -39.3% | no_tensor_candidates (211) |
| ChunkGatedDeltaRuleFwdPrepare | 48 | 73.924 | 48 | 73.924 | 58.965 | -20.2% |  |
| fused_gdn_gating_kernel | 576 | 44.045 | 48 | 32.340 | 28.031 | -13.3% | no_tensor_candidates (528) |
| Slice | 4273 | 39.010 | 96 | 16.809 | 12.885 | -23.3% | no_tensor_candidates (3985), candidate_physical_work_differs (192) |
| ChunkFwdH | 48 | 38.757 | 48 | 38.757 | 40.620 | +4.8% |  |
| SwiGlu | 804 | 37.136 | 67 | 34.369 | 28.664 | -16.6% | no_tensor_candidates (737) |
| ChunkFwdO | 48 | 24.817 | 48 | 24.817 | 17.128 | -31.0% |  |
| DynamicMxQuant | 960 | 21.934 | 80 | 18.255 | 15.053 | -17.5% | no_tensor_candidates (880) |
| split_qkv_rmsnorm_mrope_kernel | 228 | 20.694 | 0 | - | - | - | no_tensor_candidates (228) |
| CausalConv1d | 576 | 20.357 | 48 | 16.259 | 17.948 | +10.4% | no_tensor_candidates (528) |
| Transpose | 384 | 19.707 | 0 | - | - | - | no_tensor_candidates (384) |
| AddRmsNormDynamicMxQuant | 960 | 18.459 | 80 | 14.951 | 11.797 | -21.1% | no_tensor_candidates (880) |
| TensorMove | 194 | 17.095 | 0 | - | - | - | no_tensor_candidates (194) |
| _layer_norm_fwd_1pass_kernel_npu | 576 | 13.590 | 48 | 11.478 | 7.248 | -36.9% | no_tensor_candidates (528) |
| AddRmsNorm | 648 | 13.052 | 0 | - | - | - | no_tensor_candidates (648) |
| ConcatD | 612 | 12.851 | 0 | - | - | - | no_tensor_candidates (612) |
| RecurrentGatedDeltaRule | 528 | 5.628 | 0 | - | - | - | no_tensor_candidates (528) |
| Add | 2338 | 4.845 | 0 | - | - | - | no_tensor_candidates (2338) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| - | - | 0 | No valid subgraph cohort | - | - | - |
