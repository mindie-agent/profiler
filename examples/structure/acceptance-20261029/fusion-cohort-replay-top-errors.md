# Complete-Capture Operator Families And Conditional Errors

Historical captures replayed locally; no new live collection.

The event denominator is every valid positive-duration event in the complete capture window. Activity sums add event intersections separately, including overlapping events. Every native type remains in the JSON tables, including types with no valid cohort. This readable view shows the 20 highest measured-activity families per declaration (event count when old mapping metadata has no activity total), plus all subgraph cohorts. Reference events have a cohort and conditional cost but do not enter error scoring. Errors cover only scored events; activity sums are not wall-clock latency or throughput.

Several declarations may reuse one capture. Their event totals are not independent and must not be added as additional captures.

## a3_glm53_prefill / source_declared_unfused_reference

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:efab891b052788506e4786bf36254bd71464fd53ba74decdac5bff57be6bdbf8`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 157 | 1552.089 | 0 | 0 | - | - | - | no_tensor_candidates (157) |
| SparseFlashAttention | 78 | 1029.574 | 78 | 0 | 1029.574 | 477.452 | -53.6% |  |
| MlaPrologV3 | 78 | 99.338 | 0 | 78 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (78) |
| GroupedMatmulSwigluQuantV2 | 75 | 99.235 | 0 | 75 | - | - | - | quantized_epilogue_unmodeled (75) |
| hcom_allReduce_ | 157 | 93.667 | 0 | 0 | - | - | - | no_tensor_candidates (157) |
| GroupedMatmul | 75 | 91.894 | 0 | 75 | - | - | - | quantized_epilogue_unmodeled (75) |
| QuantBatchMatmulV3 | 255 | 51.931 | 180 | 0 | 46.254 | 34.289 | -25.9% | no_tensor_candidates (75) |
| AddRmsNormBias | 153 | 37.924 | 153 | 0 | 37.924 | 25.674 | -32.3% |  |
| MoeTokenUnpermute | 75 | 37.376 | 0 | 0 | - | - | - | no_tensor_candidates (75) |
| LightningIndexer | 21 | 31.342 | 0 | 21 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (21) |
| MoeInitRoutingV3 | 75 | 24.498 | 0 | 0 | - | - | - | no_tensor_candidates (75) |
| DynamicQuant | 234 | 16.527 | 234 | 0 | 16.527 | 11.312 | -31.6% |  |
| ForeachAddList | 75 | 10.799 | 0 | 0 | - | - | - | no_tensor_candidates (75) |
| Muls | 75 | 9.240 | 0 | 0 | - | - | - | no_tensor_candidates (75) |
| MoeGatingTopK | 75 | 7.627 | 0 | 75 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (75) |
| MatMulV3 | 75 | 7.599 | 0 | 0 | - | - | - | no_tensor_candidates (75) |
| TensorMove | 104 | 6.961 | 0 | 0 | - | - | - | no_tensor_candidates (104) |
| _triton_rope_siso | 42 | 6.517 | 0 | 0 | - | - | - | no_tensor_candidates (42) |
| TransposeBatchMatMul | 78 | 5.432 | 78 | 0 | 5.432 | 3.582 | -34.1% |  |
| MatMulV2 | 22 | 2.564 | 1 | 0 | 0.339 | 0.198 | -41.5% | no_tensor_candidates (21) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| MlaPrologV3 | 2b611c379a4b | 21 | reference_only | 1.342506 | 0.491634 | - |
| MlaPrologV3 | cf8c783edf4a | 57 | reference_only | 1.248166 | 0.491634 | - |
| GroupedMatmulSwigluQuantV2 | 2a7eba85203a | 75 | reference_only | 1.323133 | 0.600368 | - |
| LightningIndexer | 377d598098b3 | 21 | reference_only | 1.492464 | 1.873906 | - |
| MoeGatingTopK | dc79d7dfecc0 | 75 | reference_only | 0.101699 | 0.011181 | - |

## a3_glm53_prefill / selected_native_fusion

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:7ab3dfe60b5643d82417a46de8b2a548940d11b3f765eada2960b3abbd68f043`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 157 | 1552.089 | 0 | 0 | - | - | - | no_tensor_candidates (157) |
| SparseFlashAttention | 78 | 1029.574 | 78 | 0 | 1029.574 | 477.452 | -53.6% |  |
| MlaPrologV3 | 78 | 99.338 | 78 | 0 | 99.338 | 35.208 | -64.6% |  |
| GroupedMatmulSwigluQuantV2 | 75 | 99.235 | 75 | 0 | 99.235 | 95.695 | -3.6% |  |
| hcom_allReduce_ | 157 | 93.667 | 0 | 0 | - | - | - | no_tensor_candidates (157) |
| GroupedMatmul | 75 | 91.894 | 75 | 0 | 91.894 | 142.060 | +54.6% |  |
| QuantBatchMatmulV3 | 255 | 51.931 | 180 | 0 | 46.254 | 29.358 | -36.5% | no_tensor_candidates (75) |
| AddRmsNormBias | 153 | 37.924 | 153 | 0 | 37.924 | 25.674 | -32.3% |  |
| MoeTokenUnpermute | 75 | 37.376 | 0 | 0 | - | - | - | no_tensor_candidates (75) |
| LightningIndexer | 21 | 31.342 | 21 | 0 | 31.342 | 39.352 | +25.6% |  |
| MoeInitRoutingV3 | 75 | 24.498 | 0 | 0 | - | - | - | no_tensor_candidates (75) |
| DynamicQuant | 234 | 16.527 | 234 | 0 | 16.527 | 11.312 | -31.6% |  |
| ForeachAddList | 75 | 10.799 | 0 | 0 | - | - | - | no_tensor_candidates (75) |
| Muls | 75 | 9.240 | 0 | 0 | - | - | - | no_tensor_candidates (75) |
| MoeGatingTopK | 75 | 7.627 | 0 | 75 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (75) |
| MatMulV3 | 75 | 7.599 | 0 | 0 | - | - | - | no_tensor_candidates (75) |
| TensorMove | 104 | 6.961 | 0 | 0 | - | - | - | no_tensor_candidates (104) |
| _triton_rope_siso | 42 | 6.517 | 0 | 0 | - | - | - | no_tensor_candidates (42) |
| TransposeBatchMatMul | 78 | 5.432 | 78 | 0 | 5.432 | 3.423 | -37.0% |  |
| MatMulV2 | 22 | 2.564 | 1 | 0 | 0.339 | 0.198 | -41.5% | no_tensor_candidates (21) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| MlaPrologV3 | efdde47c60fa | 21 | compared | 1.342506 | 0.451382 | -66.4% |
| MlaPrologV3 | c2d216655129 | 57 | compared | 1.248166 | 0.451382 | -63.8% |
| GroupedMatmulSwigluQuantV2 | 384f4293368c | 75 | compared | 1.323133 | 1.275932 | -3.6% |
| LightningIndexer | b7aeac887bbe | 21 | compared | 1.492464 | 1.873906 | +25.6% |
| MoeGatingTopK | 06d02ced79c3 | 75 | reference_only | 0.101699 | 0.011181 | - |

## a3_glm53_decode / source_declared_unfused_reference

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:8bd7c0be412291cf2bb53d03506eed1e83b823996b0fd90fd704d69ed66b1126`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 11618 | 1977.841 | 0 | 0 | - | - | - | no_tensor_candidates (11618) |
| SparseFlashAttention | 5772 | 523.698 | 5772 | 0 | 523.698 | 11.471 | -97.8% |  |
| GroupedMatmulSwigluQuantV2 | 5550 | 488.615 | 0 | 5550 | - | - | - | quantized_epilogue_unmodeled (5550) |
| QuantBatchMatmulV3 | 18870 | 310.039 | 13320 | 0 | 237.111 | 84.645 | -64.3% | no_tensor_candidates (5550) |
| hcom_allReduce_ | 11618 | 300.822 | 0 | 0 | - | - | - | no_tensor_candidates (11618) |
| GroupedMatmul | 5550 | 293.637 | 0 | 5550 | - | - | - | quantized_epilogue_unmodeled (5550) |
| MlaPrologV3 | 5772 | 236.735 | 0 | 5772 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (5772) |
| Slice | 296 | 107.526 | 0 | 0 | - | - | - | no_tensor_candidates (296) |
| ForeachAddList | 5550 | 91.679 | 0 | 0 | - | - | - | no_tensor_candidates (5550) |
| TransposeBatchMatMul | 5772 | 81.808 | 5772 | 0 | 81.808 | 10.160 | -87.6% |  |
| MatMulV3 | 5550 | 81.786 | 0 | 0 | - | - | - | no_tensor_candidates (5550) |
| MoeInitRoutingV3 | 5550 | 71.053 | 0 | 0 | - | - | - | no_tensor_candidates (5550) |
| DynamicQuant | 17316 | 50.444 | 17316 | 0 | 50.444 | 0.204 | -99.6% |  |
| AddRmsNormBias | 11322 | 44.742 | 11322 | 0 | 44.742 | 0.696 | -98.4% |  |
| MatMulV2 | 1628 | 39.855 | 74 | 0 | 16.027 | 14.674 | -8.4% | no_tensor_candidates (1554) |
| LightningIndexer | 1554 | 38.703 | 0 | 1554 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (1554) |
| MoeTokenUnpermute | 5550 | 26.160 | 0 | 0 | - | - | - | no_tensor_candidates (5550) |
| MoeGatingTopK | 5550 | 22.270 | 0 | 5550 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (5550) |
| DequantSwigluQuant | 5550 | 18.782 | 0 | 0 | - | - | - | no_tensor_candidates (5550) |
| ScatterNdUpdateSk | 1554 | 13.891 | 0 | 0 | - | - | - | no_tensor_candidates (1554) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| GroupedMatmulSwigluQuantV2 | ea6f615fafb1 | 5550 | reference_only | 0.088039 | 0.010572 | - |
| MlaPrologV3 | 191176b2fad9 | 1554 | reference_only | 0.041291 | 0.018338 | - |
| MlaPrologV3 | 2ad63c281a71 | 4218 | reference_only | 0.040913 | 0.018338 | - |
| LightningIndexer | e74702e81219 | 1554 | reference_only | 0.024905 | 0.000909 | - |
| MoeGatingTopK | f3fa0d4872c1 | 5550 | reference_only | 0.004013 | 0.000003 | - |

## a3_glm53_decode / selected_native_fusion

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:3bb549c0ce97e1973bfa0d228eb5c79519aa0587c9465530b2b9ab8da2d9f209`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 11618 | 1977.841 | 0 | 0 | - | - | - | no_tensor_candidates (11618) |
| SparseFlashAttention | 5772 | 523.698 | 5772 | 0 | 523.698 | 11.471 | -97.8% |  |
| GroupedMatmulSwigluQuantV2 | 5550 | 488.615 | 5550 | 0 | 488.615 | 59.696 | -87.8% |  |
| QuantBatchMatmulV3 | 18870 | 310.039 | 13320 | 0 | 237.111 | 84.564 | -64.3% | no_tensor_candidates (5550) |
| hcom_allReduce_ | 11618 | 300.822 | 0 | 0 | - | - | - | no_tensor_candidates (11618) |
| GroupedMatmul | 5550 | 293.637 | 5550 | 0 | 293.637 | 34.144 | -88.4% |  |
| MlaPrologV3 | 5772 | 236.735 | 5772 | 0 | 236.735 | 105.784 | -55.3% |  |
| Slice | 296 | 107.526 | 0 | 0 | - | - | - | no_tensor_candidates (296) |
| ForeachAddList | 5550 | 91.679 | 0 | 0 | - | - | - | no_tensor_candidates (5550) |
| TransposeBatchMatMul | 5772 | 81.808 | 5772 | 0 | 81.808 | 10.160 | -87.6% |  |
| MatMulV3 | 5550 | 81.786 | 0 | 0 | - | - | - | no_tensor_candidates (5550) |
| MoeInitRoutingV3 | 5550 | 71.053 | 0 | 0 | - | - | - | no_tensor_candidates (5550) |
| DynamicQuant | 17316 | 50.444 | 17316 | 0 | 50.444 | 0.204 | -99.6% |  |
| AddRmsNormBias | 11322 | 44.742 | 11322 | 0 | 44.742 | 0.696 | -98.4% |  |
| MatMulV2 | 1628 | 39.855 | 74 | 0 | 16.027 | 14.673 | -8.4% | no_tensor_candidates (1554) |
| LightningIndexer | 1554 | 38.703 | 1554 | 0 | 38.703 | 1.413 | -96.4% |  |
| MoeTokenUnpermute | 5550 | 26.160 | 0 | 0 | - | - | - | no_tensor_candidates (5550) |
| MoeGatingTopK | 5550 | 22.270 | 0 | 5550 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (5550) |
| DequantSwigluQuant | 5550 | 18.782 | 0 | 0 | - | - | - | no_tensor_candidates (5550) |
| ScatterNdUpdateSk | 1554 | 13.891 | 0 | 0 | - | - | - | no_tensor_candidates (1554) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| GroupedMatmulSwigluQuantV2 | e41e237309f2 | 5550 | compared | 0.088039 | 0.010756 | -87.8% |
| MlaPrologV3 | da186cb419f7 | 1554 | compared | 0.041291 | 0.018327 | -55.6% |
| MlaPrologV3 | 67f03fbdff71 | 4218 | compared | 0.040913 | 0.018327 | -55.2% |
| LightningIndexer | 794631f68c84 | 1554 | compared | 0.024905 | 0.000909 | -96.4% |
| MoeGatingTopK | 546f21216db3 | 5550 | reference_only | 0.004013 | 0.000003 | - |

## a3_qwen35 / case_default

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:e31eb9f5f499d122b1f5f1b8e2d5a81213359afc2331d8a3ed4d00a492c2dd51`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 5628 | 913.004 | 0 | 0 | - | - | - | no_tensor_candidates (5628) |
| GroupedMatmulSwigluQuant | 2680 | 217.099 | 0 | 2680 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (2680) |
| MatMulV2 | 17879 | 190.026 | 315 | 0 | 28.121 | 23.186 | -17.5% | no_tensor_candidates (17564) |
| GroupedMatmul | 2814 | 178.155 | 80 | 0 | 55.146 | 25.818 | -53.2% | no_tensor_candidates (2734) |
| hcom_allReduce_ | 5628 | 159.599 | 0 | 0 | - | - | - | no_tensor_candidates (5628) |
| Cumsum | 2680 | 130.645 | 0 | 0 | - | - | - | no_tensor_candidates (2680) |
| ChunkGatedDeltaRuleFwd | 60 | 78.393 | 0 | 0 | - | - | - | no_tensor_candidates (60) |
| FusedInferAttentionScore | 737 | 75.245 | 11 | 0 | 9.699 | 5.593 | -42.3% | no_tensor_candidates (726) |
| MoeInitRoutingV3 | 2747 | 72.001 | 0 | 0 | - | - | - | no_tensor_candidates (2747) |
| AddRmsNormBias | 5494 | 51.285 | 0 | 0 | - | - | - | no_tensor_candidates (5494) |
| ForeachAddList | 2747 | 50.085 | 0 | 0 | - | - | - | no_tensor_candidates (2747) |
| MoeTokenUnpermute | 2747 | 42.820 | 0 | 0 | - | - | - | no_tensor_candidates (2747) |
| MatMulV3 | 144 | 38.849 | 0 | 0 | - | - | - | no_tensor_candidates (144) |
| allgatherAicpuKernel | 201 | 37.228 | 0 | 0 | - | - | - | no_tensor_candidates (201) |
| MoeGatingTopK | 2747 | 32.163 | 82 | 0 | 19.997 | 0.651 | -96.7% | no_tensor_candidates (2665) |
| RecurrentGatedDeltaRule | 1950 | 31.545 | 0 | 0 | - | - | - | no_tensor_candidates (1950) |
| Slice | 15500 | 31.495 | 0 | 0 | - | - | - | no_tensor_candidates (15500) |
| Mul | 3752 | 30.330 | 0 | 0 | - | - | - | no_tensor_candidates (3752) |
| CausalConv1d | 2010 | 24.882 | 0 | 0 | - | - | - | no_tensor_candidates (2010) |
| fused_gdn_gating_kernel | 2010 | 20.774 | 60 | 0 | 1.785 | 0.033 | -98.2% | no_tensor_candidates (1950) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| GroupedMatmulSwigluQuant | 172c1cc606f0 | 2680 | reference_only | 0.081007 | 0.344126 | - |
| MoeGatingTopK | e9bae15fd0aa | 82 | compared | 0.243864 | 0.007944 | -96.7% |

## a3_qwen36 / case_default

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:242186ecdc7c3050fee97a32062f0a85612aca7d2c6718d947f72e049dfebad4`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 2346 | 1284.175 | 0 | 0 | - | - | - | no_tensor_candidates (2346) |
| QuantBatchMatmulV3 | 3740 | 535.605 | 440 | 0 | 437.374 | 429.389 | -1.8% | no_tensor_candidates (3300) |
| hcom_allReduce_ | 2346 | 233.875 | 0 | 0 | - | - | - | no_tensor_candidates (2346) |
| ChunkGatedDeltaRuleFwd | 96 | 164.082 | 0 | 0 | - | - | - | no_tensor_candidates (96) |
| AddRmsNormBias | 2278 | 107.967 | 0 | 0 | - | - | - | no_tensor_candidates (2278) |
| FusedInferAttentionScore | 323 | 100.845 | 17 | 0 | 21.614 | 12.966 | -40.0% | no_tensor_candidates (306) |
| MatMulV2 | 1649 | 75.506 | 53 | 0 | 29.339 | 28.083 | -4.3% | no_tensor_candidates (1596) |
| DynamicQuant | 3740 | 66.998 | 440 | 0 | 53.447 | 41.253 | -22.8% | no_tensor_candidates (3300) |
| MatMulV3 | 102 | 57.571 | 0 | 0 | - | - | - | no_tensor_candidates (102) |
| allgatherAicpuKernel | 119 | 34.120 | 0 | 0 | - | - | - | no_tensor_candidates (119) |
| SwiGlu | 1139 | 32.301 | 134 | 0 | 28.000 | 23.887 | -14.7% | no_tensor_candidates (1005) |
| CausalConv1d | 816 | 27.117 | 0 | 0 | - | - | - | no_tensor_candidates (816) |
| Slice | 6106 | 23.423 | 0 | 0 | - | - | - | no_tensor_candidates (6106) |
| Transpose | 1028 | 22.152 | 0 | 0 | - | - | - | no_tensor_candidates (1028) |
| RecurrentGatedDeltaRule | 720 | 18.515 | 0 | 0 | - | - | - | no_tensor_candidates (720) |
| split_qkv_rmsnorm_mrope_kernel | 323 | 16.850 | 0 | 0 | - | - | - | no_tensor_candidates (323) |
| _layer_norm_fwd_1pass_kernel_npu | 816 | 13.821 | 96 | 0 | 10.352 | 6.040 | -41.7% | no_tensor_candidates (720) |
| Index | 673 | 12.506 | 0 | 0 | - | - | - | no_tensor_candidates (673) |
| fused_gdn_gating_kernel | 816 | 12.109 | 96 | 0 | 4.216 | 0.079 | -98.1% | no_tensor_candidates (720) |
| TensorMove | 285 | 8.786 | 0 | 0 | - | - | - | no_tensor_candidates (285) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| - | - | 0 | No valid subgraph cohort | - | - | - |

## a3_v4f / case_default

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:889a2079ea7768a1599aabf21de97eaad21818a6ad862ebe67b6ed8e9a8691da`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| SparseAttnSharedkv | 44 | 98.897 | 3 | 0 | 1.467 | 0.178 | -87.9% | candidate_physical_work_differs (41) |
| hcom_alltoallv_ | 264 | 64.783 | 0 | 0 | - | - | - | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | 0 | - | - | - | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | 0 | - | - | - | no_tensor_candidates (90) |
| HcPre | 88 | 37.975 | 0 | 88 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (88) |
| HcPost | 88 | 36.817 | 88 | 0 | 36.817 | 22.170 | -39.8% |  |
| QuantBatchMatmulV3 | 241 | 28.176 | 197 | 0 | 25.122 | 23.304 | -7.2% | no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 0 | 0 | - | - | - | no_tensor_candidates (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | 0 | - | - | - | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 46 | 0 | 4.105 | 2.573 | -37.3% | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 0 | 44 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 197 | 0 | 10.220 | 5.759 | -43.6% | no_tensor_candidates (42) |
| MatMulV2 | 110 | 12.384 | 88 | 0 | 11.809 | 9.528 | -19.3% | no_tensor_candidates (22) |
| GroupedMatmul | 44 | 10.988 | 0 | 0 | - | - | - | no_tensor_candidates (44) |
| allgatherAicpuKernel | 44 | 10.441 | 0 | 0 | - | - | - | no_tensor_candidates (44) |
| ScatterNdUpdateSk | 127 | 9.996 | 0 | 0 | - | - | - | no_tensor_candidates (127) |
| MatMulV3 | 47 | 9.758 | 0 | 0 | - | - | - | no_tensor_candidates (47) |
| TensorMove | 446 | 8.914 | 0 | 0 | - | - | - | no_tensor_candidates (446) |
| VllmAscendQuantLightningIndexerV2 | 21 | 8.380 | 0 | 21 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (21) |
| TransposeBatchMatMul | 44 | 7.473 | 0 | 0 | - | - | - | no_tensor_candidates (44) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| HcPre | 7285ede614e3 | 88 | reference_only | 0.431534 | 0.926170 | - |
| HcPost | 1131dabe1958 | 88 | compared | 0.418375 | 0.251931 | -39.8% |
| GroupedMatmulSwigluQuant | d955db45e826 | 44 | reference_only | 0.588788 | 5.681584 | - |
| VllmAscendQuantLightningIndexerV2 | 0c7dd0ae8efd | 21 | reference_only | 0.399030 | 0.248045 | - |

## a3_v4f / selected_native_fusion

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:6ed31ea0ee0f31aaf0da3b8375c67ae06f78f9cec3fc19f365a3246fb346a70f`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| SparseAttnSharedkv | 44 | 98.897 | 3 | 0 | 1.467 | 0.178 | -87.9% | candidate_physical_work_differs (41) |
| hcom_alltoallv_ | 264 | 64.783 | 0 | 0 | - | - | - | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | 0 | - | - | - | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | 0 | - | - | - | no_tensor_candidates (90) |
| HcPre | 88 | 37.975 | 88 | 0 | 37.975 | 63.496 | +67.2% |  |
| HcPost | 88 | 36.817 | 88 | 0 | 36.817 | 26.166 | -28.9% |  |
| QuantBatchMatmulV3 | 241 | 28.176 | 197 | 0 | 25.122 | 23.304 | -7.2% | no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 0 | 0 | - | - | - | no_tensor_candidates (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | 0 | - | - | - | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 46 | 0 | 4.105 | 2.573 | -37.3% | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 0 | 44 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 197 | 0 | 10.220 | 5.759 | -43.6% | no_tensor_candidates (42) |
| MatMulV2 | 110 | 12.384 | 88 | 0 | 11.809 | 9.528 | -19.3% | no_tensor_candidates (22) |
| GroupedMatmul | 44 | 10.988 | 0 | 0 | - | - | - | no_tensor_candidates (44) |
| allgatherAicpuKernel | 44 | 10.441 | 0 | 0 | - | - | - | no_tensor_candidates (44) |
| ScatterNdUpdateSk | 127 | 9.996 | 0 | 0 | - | - | - | no_tensor_candidates (127) |
| MatMulV3 | 47 | 9.758 | 0 | 0 | - | - | - | no_tensor_candidates (47) |
| TensorMove | 446 | 8.914 | 0 | 0 | - | - | - | no_tensor_candidates (446) |
| VllmAscendQuantLightningIndexerV2 | 21 | 8.380 | 0 | 21 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (21) |
| TransposeBatchMatMul | 44 | 7.473 | 0 | 0 | - | - | - | no_tensor_candidates (44) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| HcPre | ed360ba09e04 | 88 | compared | 0.431534 | 0.721545 | +67.2% |
| HcPost | 429394f8813d | 88 | compared | 0.418375 | 0.297336 | -28.9% |
| GroupedMatmulSwigluQuant | 924f31dfc74b | 44 | reference_only | 0.588788 | 5.681584 | - |
| VllmAscendQuantLightningIndexerV2 | e635c8e0bf69 | 21 | reference_only | 0.399030 | 0.248045 | - |

## a3_v4pro / case_default

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:8ce87fb19c206cb57a836717055db8e36e11370f5ee7e37ce6ed9b588ce61dc8`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| hcom_allReduce_ | 1008 | 963.972 | 0 | 0 | - | - | - | no_tensor_candidates (1008) |
| hcom_alltoallv_ | 1488 | 429.531 | 0 | 0 | - | - | - | no_tensor_candidates (1488) |
| hcom_allGather_ | 760 | 420.935 | 0 | 0 | - | - | - | no_tensor_candidates (760) |
| SparseAttnSharedkv | 248 | 174.437 | 0 | 0 | - | - | - | candidate_physical_work_differs (244), no_tensor_candidates (4) |
| HcPost | 496 | 100.241 | 496 | 0 | 100.241 | 54.644 | -45.5% |  |
| GroupedMatmulSwigluQuantV2 | 248 | 98.114 | 0 | 248 | - | - | - | quantized_epilogue_unmodeled (248) |
| HcPre | 496 | 95.134 | 0 | 496 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (496) |
| QuantBatchMatmulV3 | 1360 | 90.278 | 1112 | 0 | 80.102 | 57.700 | -28.0% | no_tensor_candidates (248) |
| Compressor | 364 | 77.516 | 0 | 0 | - | - | - | no_tensor_candidates (364) |
| allgatherAicpuKernel | 248 | 75.079 | 0 | 0 | - | - | - | no_tensor_candidates (248) |
| GroupedMatmul | 248 | 60.731 | 0 | 0 | - | - | - | no_tensor_candidates (248) |
| RmsNorm | 1016 | 43.695 | 256 | 0 | 10.399 | 6.267 | -39.7% | no_tensor_candidates (760) |
| DynamicQuant | 1352 | 37.072 | 1112 | 0 | 28.955 | 12.258 | -57.7% | no_tensor_candidates (240) |
| MatMulV2 | 616 | 35.772 | 496 | 0 | 34.799 | 37.786 | +8.6% | no_tensor_candidates (120) |
| MatMulV3 | 264 | 32.596 | 0 | 0 | - | - | - | no_tensor_candidates (264) |
| TensorMove | 4488 | 29.113 | 0 | 0 | - | - | - | no_tensor_candidates (4488) |
| InplacePartialRotaryMul | 864 | 17.121 | 0 | 0 | - | - | - | no_tensor_candidates (864) |
| TransposeBatchMatMul | 248 | 15.726 | 0 | 0 | - | - | - | no_tensor_candidates (248) |
| RmsNormCast | 248 | 13.898 | 0 | 0 | - | - | - | no_tensor_candidates (248) |
| VllmAscendQuantLightningIndexerV2 | 120 | 13.611 | 0 | 120 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (120) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| HcPost | 04c396525349 | 496 | compared | 0.202098 | 0.110169 | -45.5% |
| GroupedMatmulSwigluQuantV2 | e3ad41c42490 | 248 | reference_only | 0.395623 | 0.805300 | - |
| HcPre | 683c5493fe46 | 496 | reference_only | 0.191803 | 0.451742 | - |
| VllmAscendQuantLightningIndexerV2 | 875041d784ca | 120 | reference_only | 0.113425 | 0.018539 | - |

## a3_v4pro / selected_native_fusion

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:a58a6da73dd7540a4766c5f7b921649af3b565c218a8fb86812238ace3a5f8b8`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| hcom_allReduce_ | 1008 | 963.972 | 0 | 0 | - | - | - | no_tensor_candidates (1008) |
| hcom_alltoallv_ | 1488 | 429.531 | 0 | 0 | - | - | - | no_tensor_candidates (1488) |
| hcom_allGather_ | 760 | 420.935 | 0 | 0 | - | - | - | no_tensor_candidates (760) |
| SparseAttnSharedkv | 248 | 174.437 | 0 | 0 | - | - | - | candidate_physical_work_differs (244), no_tensor_candidates (4) |
| HcPost | 496 | 100.241 | 496 | 0 | 100.241 | 64.356 | -35.8% |  |
| GroupedMatmulSwigluQuantV2 | 248 | 98.114 | 0 | 248 | - | - | - | quantized_epilogue_unmodeled (248) |
| HcPre | 496 | 95.134 | 496 | 0 | 95.134 | 156.963 | +65.0% |  |
| QuantBatchMatmulV3 | 1360 | 90.278 | 1112 | 0 | 80.102 | 57.700 | -28.0% | no_tensor_candidates (248) |
| Compressor | 364 | 77.516 | 0 | 0 | - | - | - | no_tensor_candidates (364) |
| allgatherAicpuKernel | 248 | 75.079 | 0 | 0 | - | - | - | no_tensor_candidates (248) |
| GroupedMatmul | 248 | 60.731 | 0 | 0 | - | - | - | no_tensor_candidates (248) |
| RmsNorm | 1016 | 43.695 | 256 | 0 | 10.399 | 6.267 | -39.7% | no_tensor_candidates (760) |
| DynamicQuant | 1352 | 37.072 | 1112 | 0 | 28.955 | 12.258 | -57.7% | no_tensor_candidates (240) |
| MatMulV2 | 616 | 35.772 | 496 | 0 | 34.799 | 37.786 | +8.6% | no_tensor_candidates (120) |
| MatMulV3 | 264 | 32.596 | 0 | 0 | - | - | - | no_tensor_candidates (264) |
| TensorMove | 4488 | 29.113 | 0 | 0 | - | - | - | no_tensor_candidates (4488) |
| InplacePartialRotaryMul | 864 | 17.121 | 0 | 0 | - | - | - | no_tensor_candidates (864) |
| TransposeBatchMatMul | 248 | 15.726 | 0 | 0 | - | - | - | no_tensor_candidates (248) |
| RmsNormCast | 248 | 13.898 | 0 | 0 | - | - | - | no_tensor_candidates (248) |
| VllmAscendQuantLightningIndexerV2 | 120 | 13.611 | 0 | 120 | - | - | - | unfused_subgraph_is_not_the_observed_native_kernel (120) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| HcPost | 2b7f4fbb5d9b | 496 | compared | 0.202098 | 0.129751 | -35.8% |
| GroupedMatmulSwigluQuantV2 | 1439616849b6 | 248 | reference_only | 0.395623 | 0.805300 | - |
| HcPre | 4840438935f1 | 496 | compared | 0.191803 | 0.316457 | +65.0% |
| VllmAscendQuantLightningIndexerV2 | 4dd29ed3e598 | 120 | reference_only | 0.113425 | 0.018539 | - |

## a5_kimi_k3 / case_default

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:4e276b5d271500709658fc62e7aa983fe585376a443511ed22a31db9839faed8`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| hcom_alltoallv_AicpuKernel | 1104 | 919.190 | 0 | 0 | - | - | - | no_tensor_candidates (1104) |
| ChunkKdaFwd | 1104 | 881.998 | 0 | 0 | - | - | - | no_tensor_candidates (1104) |
| GroupedMatmul | 27248 | 813.481 | 0 | 0 | - | - | - | no_tensor_candidates (27248) |
| HcclLaunchAicpuKernel | 1543 | 683.214 | 0 | 0 | - | - | - | no_tensor_candidates (1543) |
| GroupedMatmulSituQuant | 7266 | 666.877 | 0 | 0 | - | - | - | no_tensor_candidates (7266) |
| MatMulV3 | 21819 | 656.394 | 163 | 0 | 46.985 | 72.764 | +54.9% | no_tensor_candidates (21656) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | 0 | - | - | - | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 0 | 0 | - | - | - | no_tensor_candidates (7266) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 0 | 0 | - | - | - | no_tensor_candidates (14531) |
| hcom_allGather_ | 15203 | 409.082 | 0 | 0 | - | - | - | no_tensor_candidates (15203) |
| MatmulReduceScatterV2 | 372 | 344.763 | 0 | 0 | - | - | - | no_tensor_candidates (372) |
| FusedInferAttentionScore | 1966 | 331.488 | 0 | 0 | - | - | - | no_tensor_candidates (1966) |
| AttnResFwd | 14768 | 245.588 | 0 | 0 | - | - | - | no_tensor_candidates (14768) |
| hcom_reduceScatter_ | 13945 | 182.792 | 0 | 0 | - | - | - | no_tensor_candidates (13945) |
| hcom_reduceScatter_AicpuKernel | 372 | 171.224 | 0 | 0 | - | - | - | no_tensor_candidates (372) |
| MoeDistributeDispatchV3 | 6898 | 168.750 | 0 | 0 | - | - | - | no_tensor_candidates (6898) |
| DynamicMxQuant | 22499 | 166.851 | 0 | 0 | - | - | - | no_tensor_candidates (22499) |
| Cast | 10332 | 100.414 | 0 | 0 | - | - | - | no_tensor_candidates (10332) |
| MoeDistributeCombineV3 | 6897 | 98.662 | 0 | 0 | - | - | - | no_tensor_candidates (6897) |
| PadV3 | 17616 | 65.378 | 0 | 0 | - | - | - | no_tensor_candidates (17616) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| - | - | 0 | No valid subgraph cohort | - | - | - |

## a5_kimi_k3_decode / source_declared_unfused_reference

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:32ef79bccf2ae9eff3ec6cabfc362542996d9a9635f14dc3b9284398ca8ab9ec`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| hcom_alltoallv_AicpuKernel | 1104 | 919.190 | 0 | 0 | - | - | - | no_tensor_candidates (1104) |
| ChunkKdaFwd | 1104 | 881.998 | 0 | 0 | - | - | - | no_tensor_candidates (1104) |
| GroupedMatmul | 27248 | 813.481 | 0 | 0 | - | - | - | no_tensor_candidates (27248) |
| HcclLaunchAicpuKernel | 1543 | 683.214 | 0 | 0 | - | - | - | no_tensor_candidates (1543) |
| GroupedMatmulSituQuant | 7266 | 666.877 | 0 | 0 | - | - | - | no_tensor_candidates (7266) |
| MatMulV3 | 21819 | 656.394 | 8838 | 0 | 124.026 | 75.810 | -38.9% | no_tensor_candidates (12981) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | 0 | - | - | - | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 0 | 0 | - | - | - | no_tensor_candidates (7266) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 0 | 0 | - | - | - | no_tensor_candidates (14531) |
| hcom_allGather_ | 15203 | 409.082 | 0 | 0 | - | - | - | no_tensor_candidates (15203) |
| MatmulReduceScatterV2 | 372 | 344.763 | 0 | 0 | - | - | - | no_tensor_candidates (372) |
| FusedInferAttentionScore | 1966 | 331.488 | 0 | 0 | - | - | - | no_tensor_candidates (1966) |
| AttnResFwd | 14768 | 245.588 | 0 | 0 | - | - | - | no_tensor_candidates (14768) |
| hcom_reduceScatter_ | 13945 | 182.792 | 0 | 0 | - | - | - | no_tensor_candidates (13945) |
| hcom_reduceScatter_AicpuKernel | 372 | 171.224 | 0 | 0 | - | - | - | no_tensor_candidates (372) |
| MoeDistributeDispatchV3 | 6898 | 168.750 | 0 | 0 | - | - | - | no_tensor_candidates (6898) |
| DynamicMxQuant | 22499 | 166.851 | 0 | 0 | - | - | - | no_tensor_candidates (22499) |
| Cast | 10332 | 100.414 | 0 | 0 | - | - | - | no_tensor_candidates (10332) |
| MoeDistributeCombineV3 | 6897 | 98.662 | 0 | 0 | - | - | - | no_tensor_candidates (6897) |
| PadV3 | 17616 | 65.378 | 0 | 0 | - | - | - | no_tensor_candidates (17616) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| - | - | 0 | No valid subgraph cohort | - | - | - |

## a5_kimi_k3_checkpoint / current_checkpoint_conditional

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:598acc0a45fb0d2cc2c1577c3fb16f31fb07ba8d093e46fb514c0dfc81a05501`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| hcom_alltoallv_AicpuKernel | 1104 | 919.190 | 0 | 0 | - | - | - | no_tensor_candidates (1104) |
| ChunkKdaFwd | 1104 | 881.998 | 0 | 0 | - | - | - | no_tensor_candidates (1104) |
| GroupedMatmul | 27248 | 813.481 | 0 | 0 | - | - | - | no_tensor_candidates (27248) |
| HcclLaunchAicpuKernel | 1543 | 683.214 | 0 | 0 | - | - | - | no_tensor_candidates (1543) |
| GroupedMatmulSituQuant | 7266 | 666.877 | 0 | 7266 | - | - | - | mxfp4_native_execution_unmodeled (7266) |
| MatMulV3 | 21819 | 656.394 | 163 | 0 | 46.985 | 72.764 | +54.9% | no_tensor_candidates (21656) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | 0 | - | - | - | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 368 | 0 | 54.142 | 5.503 | -89.8% | no_tensor_candidates (6898) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 0 | 736 | - | - | - | no_tensor_candidates (13795), mxfp4_native_execution_unmodeled (736) |
| hcom_allGather_ | 15203 | 409.082 | 0 | 0 | - | - | - | no_tensor_candidates (15203) |
| MatmulReduceScatterV2 | 372 | 344.763 | 0 | 0 | - | - | - | no_tensor_candidates (372) |
| FusedInferAttentionScore | 1966 | 331.488 | 0 | 0 | - | - | - | no_tensor_candidates (1966) |
| AttnResFwd | 14768 | 245.588 | 0 | 0 | - | - | - | no_tensor_candidates (14768) |
| hcom_reduceScatter_ | 13945 | 182.792 | 0 | 0 | - | - | - | no_tensor_candidates (13945) |
| hcom_reduceScatter_AicpuKernel | 372 | 171.224 | 0 | 0 | - | - | - | no_tensor_candidates (372) |
| MoeDistributeDispatchV3 | 6898 | 168.750 | 0 | 0 | - | - | - | no_tensor_candidates (6898) |
| DynamicMxQuant | 22499 | 166.851 | 1208 | 0 | 77.219 | 50.398 | -34.7% | no_tensor_candidates (21291) |
| Cast | 10332 | 100.414 | 0 | 0 | - | - | - | no_tensor_candidates (10332) |
| MoeDistributeCombineV3 | 6897 | 98.662 | 0 | 0 | - | - | - | no_tensor_candidates (6897) |
| PadV3 | 17616 | 65.378 | 0 | 0 | - | - | - | no_tensor_candidates (17616) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| GroupedMatmulSituQuant | a3c7aca518de | 7266 | reference_only | 0.091780 | 11.336311 | - |
| SituMxQuant | 2506d4b77b15 | 368 | compared | 0.147124 | 0.014953 | -89.8% |

## a5_kimi_k3_decode_checkpoint / current_checkpoint_conditional

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:4e36212b6422955d69fec949ea7b33d30c449dd9145b97ee57f9ceca8e53fa5c`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| hcom_alltoallv_AicpuKernel | 1104 | 919.190 | 0 | 0 | - | - | - | no_tensor_candidates (1104) |
| ChunkKdaFwd | 1104 | 881.998 | 0 | 0 | - | - | - | no_tensor_candidates (1104) |
| GroupedMatmul | 27248 | 813.481 | 0 | 0 | - | - | - | no_tensor_candidates (27248) |
| HcclLaunchAicpuKernel | 1543 | 683.214 | 0 | 0 | - | - | - | no_tensor_candidates (1543) |
| GroupedMatmulSituQuant | 7266 | 666.877 | 0 | 7266 | - | - | - | mxfp4_native_execution_unmodeled (7266) |
| MatMulV3 | 21819 | 656.394 | 8838 | 0 | 124.026 | 75.810 | -38.9% | no_tensor_candidates (12981) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | 0 | - | - | - | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 6898 | 0 | 449.295 | 0.013 | -100.0% | no_tensor_candidates (368) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 0 | 13795 | - | - | - | mxfp4_native_execution_unmodeled (13795), no_tensor_candidates (736) |
| hcom_allGather_ | 15203 | 409.082 | 0 | 0 | - | - | - | no_tensor_candidates (15203) |
| MatmulReduceScatterV2 | 372 | 344.763 | 0 | 0 | - | - | - | no_tensor_candidates (372) |
| FusedInferAttentionScore | 1966 | 331.488 | 0 | 0 | - | - | - | no_tensor_candidates (1966) |
| AttnResFwd | 14768 | 245.588 | 0 | 0 | - | - | - | no_tensor_candidates (14768) |
| hcom_reduceScatter_ | 13945 | 182.792 | 0 | 0 | - | - | - | no_tensor_candidates (13945) |
| hcom_reduceScatter_AicpuKernel | 372 | 171.224 | 0 | 0 | - | - | - | no_tensor_candidates (372) |
| MoeDistributeDispatchV3 | 6898 | 168.750 | 0 | 0 | - | - | - | no_tensor_candidates (6898) |
| DynamicMxQuant | 22499 | 166.851 | 18971 | 0 | 78.422 | 0.103 | -99.9% | no_tensor_candidates (3528) |
| Cast | 10332 | 100.414 | 0 | 0 | - | - | - | no_tensor_candidates (10332) |
| MoeDistributeCombineV3 | 6897 | 98.662 | 0 | 0 | - | - | - | no_tensor_candidates (6897) |
| PadV3 | 17616 | 65.378 | 0 | 0 | - | - | - | no_tensor_candidates (17616) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| GroupedMatmulSituQuant | 793279dcd26d | 7266 | reference_only | 0.091780 | 0.007735 | - |
| SituMxQuant | 68b483bece8d | 6898 | compared | 0.065134 | 0.000002 | -100.0% |
| MlaPrologV3 | 828f6ca5e170 | 1798 | reference_only | 0.022248 | 0.017439 | - |

## a5_qwen38 / case_default

Sort: `complete_capture_activity_sum_ns`. Graph: `sha256:83f53cbcffb2bab2a1dab5381b0adf82fc3d7b116bfaaa70f8b19c7402ea8fda`.

| Native family | All events | All activity ms | Scored events | Reference events | Scored observed ms | Predicted ms | Relative error | Mapping / comparison reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| QuantBatchMatmulV3 | 1920 | 781.406 | 160 | 0 | 714.307 | 1253.383 | +75.5% | no_tensor_candidates (1760) |
| MatMulV3 | 1956 | 611.956 | 184 | 0 | 458.381 | 749.773 | +63.6% | no_tensor_candidates (1772) |
| FusedInferAttentionScore | 228 | 243.894 | 17 | 0 | 213.742 | 129.650 | -39.3% | no_tensor_candidates (211) |
| ChunkGatedDeltaRuleFwdPrepare | 48 | 73.924 | 48 | 0 | 73.924 | 58.965 | -20.2% |  |
| fused_gdn_gating_kernel | 576 | 44.045 | 48 | 0 | 32.340 | 28.031 | -13.3% | no_tensor_candidates (528) |
| Slice | 4273 | 39.010 | 96 | 0 | 16.809 | 12.885 | -23.3% | no_tensor_candidates (3985), candidate_physical_work_differs (192) |
| ChunkFwdH | 48 | 38.757 | 48 | 0 | 38.757 | 40.620 | +4.8% |  |
| SwiGlu | 804 | 37.136 | 67 | 0 | 34.369 | 28.664 | -16.6% | no_tensor_candidates (737) |
| ChunkFwdO | 48 | 24.817 | 48 | 0 | 24.817 | 17.128 | -31.0% |  |
| DynamicMxQuant | 960 | 21.934 | 80 | 0 | 18.255 | 15.053 | -17.5% | no_tensor_candidates (880) |
| split_qkv_rmsnorm_mrope_kernel | 228 | 20.694 | 0 | 0 | - | - | - | no_tensor_candidates (228) |
| CausalConv1d | 576 | 20.357 | 48 | 0 | 16.259 | 17.948 | +10.4% | no_tensor_candidates (528) |
| Transpose | 384 | 19.707 | 0 | 0 | - | - | - | no_tensor_candidates (384) |
| AddRmsNormDynamicMxQuant | 960 | 18.459 | 80 | 0 | 14.951 | 11.797 | -21.1% | no_tensor_candidates (880) |
| TensorMove | 194 | 17.095 | 0 | 0 | - | - | - | no_tensor_candidates (194) |
| _layer_norm_fwd_1pass_kernel_npu | 576 | 13.590 | 48 | 0 | 11.478 | 7.248 | -36.9% | no_tensor_candidates (528) |
| AddRmsNorm | 648 | 13.052 | 0 | 0 | - | - | - | no_tensor_candidates (648) |
| ConcatD | 612 | 12.851 | 0 | 0 | - | - | - | no_tensor_candidates (612) |
| RecurrentGatedDeltaRule | 528 | 5.628 | 0 | 0 | - | - | - | no_tensor_candidates (528) |
| Add | 2338 | 4.845 | 0 | 0 | - | - | - | no_tensor_candidates (2338) |

| Subgraph native family | Cohort | Events | Status | Observed mean ms | Predicted call ms | Mean error |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| - | - | 0 | No valid subgraph cohort | - | - | - |
