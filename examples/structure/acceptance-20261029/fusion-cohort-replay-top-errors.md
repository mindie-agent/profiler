# Complete-Capture Operator Families And Tiered Conditional Errors

Historical captures; report refresh can reuse saved comparisons without raw scans or new predictions.

Policy: observed complete-event mean > 50 us uses absolute relative error <= 15%; mean <= 50 us uses absolute per-call difference <= 15 us, including exactly 50 us. Per-call diff is predicted minus observed. No launch floor is added to predictions. This is an acceptance allowance, not evidence that a residual was caused by launch overhead.

Acceptance is decided per cohort before aggregation. Family/tier means are call-count weighted; pass/fail counts preserve failed cohorts even if signed averages cancel. The scored columns cover the indicated tier and pass/fail subset only: failed cohorts appear in error tables and passed cohorts appear within tolerance, including when a family has both. All/reference event counts describe the whole native family and repeat across these subsets. Every native type and full-family aggregate remains in JSON.

Large failed cohorts lead Top Errors, sorted by their observed activity; small failures are separate and sorted by absolute per-call difference. Within-tolerance groups and unscored coverage have separate tables. Reference, clipped, failed and unmatched events are not scored.

Activity sums count overlapping events separately and are not wall-clock latency. Variant totals reuse captures and must not be counted as independent evidence.

| Tier | Compared cohorts across variants | Passed | Failed |
| --- | ---: | ---: | ---: |
| relative_15pct | 141 | 32 | 109 |
| absolute_15us | 69 | 54 | 15 |

## a3_glm53_prefill / source_declared_unfused_reference

Graph: `sha256:efab891b052788506e4786bf36254bd71464fd53ba74decdac5bff57be6bdbf8`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 12 | 4 | 8 | 105 | 542 |
| absolute_15us | 4 | 2 | 2 | 6 | 99 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseFlashAttention | relative_15pct | 78 | 78 | 0 | 1029.574 | 477.452 | 13199.665 | 6121.175 | -7078.489 | -53.6% | 0 / 1 |
| AddRmsNormBias | relative_15pct | 153 | 153 | 0 | 37.924 | 25.674 | 247.871 | 167.806 | -80.065 | -32.3% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 255 | 75 | 0 | 18.215 | 7.723 | 242.871 | 102.978 | -139.892 | -57.6% | 0 / 1 |
| DynamicQuant | relative_15pct | 234 | 153 | 0 | 13.512 | 9.628 | 88.316 | 62.928 | -25.388 | -28.7% | 0 / 1 |
| TransposeBatchMatMul | relative_15pct | 78 | 78 | 0 | 5.432 | 3.582 | 69.647 | 45.922 | -23.724 | -34.1% | 0 / 1 |
| AddRmsNormDynamicQuant | relative_15pct | 3 | 3 | 0 | 0.796 | 0.441 | 265.468 | 146.835 | -118.633 | -44.7% | 0 / 1 |
| MatMulV2 | relative_15pct | 22 | 1 | 0 | 0.339 | 0.198 | 339.013 | 198.291 | -140.722 | -41.5% | 0 / 1 |
| RmsNorm | relative_15pct | 1 | 1 | 0 | 0.114 | 0.084 | 113.558 | 83.896 | -29.662 | -26.1% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LayerNormV3 | absolute_15us | 21 | 21 | 0 | 0.534 | 0.073 | 25.414 | 3.496 | -21.918 | -86.2% | 0 / 1 |
| DynamicQuant | absolute_15us | 234 | 78 | 0 | 2.924 | 1.637 | 37.486 | 20.985 | -16.501 | -44.0% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 234 | 3 | 0 | 0.091 | 0.047 | 30.413 | 15.742 | -14.670 | -48.2% | 1 / 0 |
| SwiGlu | absolute_15us | 3 | 3 | 0 | 0.105 | 0.094 | 35.033 | 31.457 | -3.575 | -10.2% | 1 / 0 |
| QuantBatchMatmulV3 | relative_15pct | 255 | 105 | 0 | 28.038 | 26.566 | 267.032 | 253.007 | -14.025 | -5.3% | 4 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 157 | 1552.089 | 0 | no_tensor_candidates (157) |
| MlaPrologV3 | 78 | 99.338 | 78 | unfused_subgraph_is_not_the_observed_native_kernel (78) |
| GroupedMatmulSwigluQuantV2 | 75 | 99.235 | 75 | quantized_epilogue_unmodeled (75) |
| hcom_allReduce_ | 157 | 93.667 | 0 | no_tensor_candidates (157) |
| GroupedMatmul | 75 | 91.894 | 75 | quantized_epilogue_unmodeled (75) |
| QuantBatchMatmulV3 | 255 | 51.931 | 0 | no_tensor_candidates (75) |
| MoeTokenUnpermute | 75 | 37.376 | 0 | no_tensor_candidates (75) |
| LightningIndexer | 21 | 31.342 | 21 | unfused_subgraph_is_not_the_observed_native_kernel (21) |
| MoeInitRoutingV3 | 75 | 24.498 | 0 | no_tensor_candidates (75) |
| ForeachAddList | 75 | 10.799 | 0 | no_tensor_candidates (75) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| MlaPrologV3 | 2b611c379a4b | 21 | reference_only | 1342.506 | 491.634 | -850.872 | - | reference_only | - |
| MlaPrologV3 | cf8c783edf4a | 57 | reference_only | 1248.166 | 491.634 | -756.532 | - | reference_only | - |
| GroupedMatmulSwigluQuantV2 | 2a7eba85203a | 75 | reference_only | 1323.133 | 600.368 | -722.765 | - | reference_only | - |
| LightningIndexer | 377d598098b3 | 21 | reference_only | 1492.464 | 1873.906 | 381.442 | - | reference_only | - |
| MoeGatingTopK | dc79d7dfecc0 | 75 | reference_only | 101.699 | 11.181 | -90.518 | - | reference_only | - |

## a3_glm53_prefill / selected_native_fusion

Graph: `sha256:7ab3dfe60b5643d82417a46de8b2a548940d11b3f765eada2960b3abbd68f043`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 17 | 3 | 14 | 156 | 740 |
| absolute_15us | 4 | 2 | 2 | 6 | 99 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseFlashAttention | relative_15pct | 78 | 78 | 0 | 1029.574 | 477.452 | 13199.665 | 6121.175 | -7078.489 | -53.6% | 0 / 1 |
| MlaPrologV3 | relative_15pct | 78 | 78 | 0 | 99.338 | 35.208 | 1273.566 | 451.382 | -822.184 | -64.6% | 0 / 2 |
| GroupedMatmul | relative_15pct | 75 | 75 | 0 | 91.894 | 142.060 | 1225.255 | 1894.139 | 668.884 | +54.6% | 0 / 1 |
| AddRmsNormBias | relative_15pct | 153 | 153 | 0 | 37.924 | 25.674 | 247.871 | 167.806 | -80.065 | -32.3% | 0 / 1 |
| LightningIndexer | relative_15pct | 21 | 21 | 0 | 31.342 | 39.352 | 1492.464 | 1873.906 | 381.442 | +25.6% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 255 | 99 | 0 | 23.099 | 9.572 | 233.327 | 96.690 | -136.637 | -58.6% | 0 / 3 |
| DynamicQuant | relative_15pct | 234 | 153 | 0 | 13.512 | 9.628 | 88.316 | 62.928 | -25.388 | -28.7% | 0 / 1 |
| TransposeBatchMatMul | relative_15pct | 78 | 78 | 0 | 5.432 | 3.423 | 69.647 | 43.882 | -25.764 | -37.0% | 0 / 1 |
| AddRmsNormDynamicQuant | relative_15pct | 3 | 3 | 0 | 0.796 | 0.441 | 265.468 | 146.835 | -118.633 | -44.7% | 0 / 1 |
| MatMulV2 | relative_15pct | 22 | 1 | 0 | 0.339 | 0.198 | 339.013 | 198.289 | -140.724 | -41.5% | 0 / 1 |
| RmsNorm | relative_15pct | 1 | 1 | 0 | 0.114 | 0.084 | 113.558 | 83.896 | -29.662 | -26.1% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LayerNormV3 | absolute_15us | 21 | 21 | 0 | 0.534 | 0.073 | 25.414 | 3.496 | -21.918 | -86.2% | 0 / 1 |
| DynamicQuant | absolute_15us | 234 | 78 | 0 | 2.924 | 1.637 | 37.486 | 20.985 | -16.501 | -44.0% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 234 | 3 | 0 | 0.091 | 0.047 | 30.413 | 15.742 | -14.670 | -48.2% | 1 / 0 |
| SwiGlu | absolute_15us | 3 | 3 | 0 | 0.105 | 0.094 | 35.033 | 31.457 | -3.575 | -10.2% | 1 / 0 |
| GroupedMatmulSwigluQuantV2 | relative_15pct | 75 | 75 | 0 | 99.235 | 95.695 | 1323.133 | 1275.932 | -47.201 | -3.6% | 1 / 0 |
| QuantBatchMatmulV3 | relative_15pct | 255 | 81 | 0 | 23.154 | 19.786 | 285.855 | 244.274 | -41.581 | -14.5% | 2 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 157 | 1552.089 | 0 | no_tensor_candidates (157) |
| hcom_allReduce_ | 157 | 93.667 | 0 | no_tensor_candidates (157) |
| QuantBatchMatmulV3 | 255 | 51.931 | 0 | no_tensor_candidates (75) |
| MoeTokenUnpermute | 75 | 37.376 | 0 | no_tensor_candidates (75) |
| MoeInitRoutingV3 | 75 | 24.498 | 0 | no_tensor_candidates (75) |
| ForeachAddList | 75 | 10.799 | 0 | no_tensor_candidates (75) |
| Muls | 75 | 9.240 | 0 | no_tensor_candidates (75) |
| MoeGatingTopK | 75 | 7.627 | 75 | unfused_subgraph_is_not_the_observed_native_kernel (75) |
| MatMulV3 | 75 | 7.599 | 0 | no_tensor_candidates (75) |
| TensorMove | 104 | 6.961 | 0 | no_tensor_candidates (104) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| MlaPrologV3 | efdde47c60fa | 21 | compared | 1342.506 | 451.382 | -891.124 | -66.4% | relative_15pct | false |
| MlaPrologV3 | c2d216655129 | 57 | compared | 1248.166 | 451.382 | -796.784 | -63.8% | relative_15pct | false |
| LightningIndexer | b7aeac887bbe | 21 | compared | 1492.464 | 1873.906 | 381.442 | +25.6% | relative_15pct | false |
| GroupedMatmulSwigluQuantV2 | 384f4293368c | 75 | compared | 1323.133 | 1275.932 | -47.201 | -3.6% | relative_15pct | true |
| MoeGatingTopK | 06d02ced79c3 | 75 | reference_only | 101.699 | 11.181 | -90.518 | - | reference_only | - |

## a3_glm53_decode / source_declared_unfused_reference

Graph: `sha256:8bd7c0be412291cf2bb53d03506eed1e83b823996b0fd90fd704d69ed66b1126`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 1 | 1 | 74 | 5772 |
| absolute_15us | 14 | 14 | 0 | 49802 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseFlashAttention | relative_15pct | 5772 | 5772 | 0 | 523.698 | 11.471 | 90.731 | 1.987 | -88.743 | -97.8% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | absolute_15us | 18870 | 13320 | 0 | 237.111 | 84.645 | 17.801 | 6.355 | -11.446 | -64.3% | 5 / 0 |
| TransposeBatchMatMul | absolute_15us | 5772 | 5772 | 0 | 81.808 | 10.160 | 14.173 | 1.760 | -12.413 | -87.6% | 1 / 0 |
| DynamicQuant | absolute_15us | 17316 | 17316 | 0 | 50.444 | 0.204 | 2.913 | 0.012 | -2.901 | -99.6% | 3 / 0 |
| AddRmsNormBias | absolute_15us | 11322 | 11322 | 0 | 44.742 | 0.696 | 3.952 | 0.061 | -3.890 | -98.4% | 1 / 0 |
| LayerNormV3 | absolute_15us | 1554 | 1554 | 0 | 8.257 | 0.003 | 5.313 | 0.002 | -5.311 | -100.0% | 1 / 0 |
| AddRmsNormDynamicQuant | absolute_15us | 222 | 222 | 0 | 1.055 | 0.013 | 4.751 | 0.056 | -4.695 | -98.8% | 1 / 0 |
| SwiGlu | absolute_15us | 222 | 222 | 0 | 0.810 | 0.002 | 3.650 | 0.008 | -3.642 | -99.8% | 1 / 0 |
| RmsNorm | absolute_15us | 74 | 74 | 0 | 0.356 | 0.002 | 4.813 | 0.031 | -4.782 | -99.4% | 1 / 0 |
| MatMulV2 | relative_15pct | 1628 | 74 | 0 | 16.027 | 14.674 | 216.579 | 198.291 | -18.287 | -8.4% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 11618 | 1977.841 | 0 | no_tensor_candidates (11618) |
| GroupedMatmulSwigluQuantV2 | 5550 | 488.615 | 5550 | quantized_epilogue_unmodeled (5550) |
| QuantBatchMatmulV3 | 18870 | 310.039 | 0 | no_tensor_candidates (5550) |
| hcom_allReduce_ | 11618 | 300.822 | 0 | no_tensor_candidates (11618) |
| GroupedMatmul | 5550 | 293.637 | 5550 | quantized_epilogue_unmodeled (5550) |
| MlaPrologV3 | 5772 | 236.735 | 5772 | unfused_subgraph_is_not_the_observed_native_kernel (5772) |
| Slice | 296 | 107.526 | 0 | no_tensor_candidates (296) |
| ForeachAddList | 5550 | 91.679 | 0 | no_tensor_candidates (5550) |
| MatMulV3 | 5550 | 81.786 | 0 | no_tensor_candidates (5550) |
| MoeInitRoutingV3 | 5550 | 71.053 | 0 | no_tensor_candidates (5550) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| GroupedMatmulSwigluQuantV2 | ea6f615fafb1 | 5550 | reference_only | 88.039 | 10.572 | -77.466 | - | reference_only | - |
| MlaPrologV3 | 191176b2fad9 | 1554 | reference_only | 41.291 | 18.338 | -22.953 | - | reference_only | - |
| MlaPrologV3 | 2ad63c281a71 | 4218 | reference_only | 40.913 | 18.338 | -22.575 | - | reference_only | - |
| LightningIndexer | e74702e81219 | 1554 | reference_only | 24.905 | 0.909 | -23.996 | - | reference_only | - |
| MoeGatingTopK | f3fa0d4872c1 | 5550 | reference_only | 4.013 | 0.003 | -4.010 | - | reference_only | - |

## a3_glm53_decode / selected_native_fusion

Graph: `sha256:3bb549c0ce97e1973bfa0d228eb5c79519aa0587c9465530b2b9ab8da2d9f209`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 4 | 1 | 3 | 74 | 16872 |
| absolute_15us | 17 | 14 | 3 | 49802 | 7326 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseFlashAttention | relative_15pct | 5772 | 5772 | 0 | 523.698 | 11.471 | 90.731 | 1.987 | -88.743 | -97.8% | 0 / 1 |
| GroupedMatmulSwigluQuantV2 | relative_15pct | 5550 | 5550 | 0 | 488.615 | 59.696 | 88.039 | 10.756 | -77.283 | -87.8% | 0 / 1 |
| GroupedMatmul | relative_15pct | 5550 | 5550 | 0 | 293.637 | 34.144 | 52.907 | 6.152 | -46.755 | -88.4% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LightningIndexer | absolute_15us | 1554 | 1554 | 0 | 38.703 | 1.413 | 24.905 | 0.909 | -23.996 | -96.4% | 0 / 1 |
| MlaPrologV3 | absolute_15us | 5772 | 5772 | 0 | 236.735 | 105.784 | 41.014 | 18.327 | -22.687 | -55.3% | 0 / 2 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | absolute_15us | 18870 | 13320 | 0 | 237.111 | 84.564 | 17.801 | 6.349 | -11.452 | -64.3% | 5 / 0 |
| TransposeBatchMatMul | absolute_15us | 5772 | 5772 | 0 | 81.808 | 10.160 | 14.173 | 1.760 | -12.413 | -87.6% | 1 / 0 |
| DynamicQuant | absolute_15us | 17316 | 17316 | 0 | 50.444 | 0.204 | 2.913 | 0.012 | -2.901 | -99.6% | 3 / 0 |
| AddRmsNormBias | absolute_15us | 11322 | 11322 | 0 | 44.742 | 0.696 | 3.952 | 0.061 | -3.890 | -98.4% | 1 / 0 |
| LayerNormV3 | absolute_15us | 1554 | 1554 | 0 | 8.257 | 0.003 | 5.313 | 0.002 | -5.311 | -100.0% | 1 / 0 |
| AddRmsNormDynamicQuant | absolute_15us | 222 | 222 | 0 | 1.055 | 0.013 | 4.751 | 0.056 | -4.695 | -98.8% | 1 / 0 |
| SwiGlu | absolute_15us | 222 | 222 | 0 | 0.810 | 0.002 | 3.650 | 0.008 | -3.642 | -99.8% | 1 / 0 |
| RmsNorm | absolute_15us | 74 | 74 | 0 | 0.356 | 0.002 | 4.813 | 0.031 | -4.782 | -99.4% | 1 / 0 |
| MatMulV2 | relative_15pct | 1628 | 74 | 0 | 16.027 | 14.673 | 216.579 | 198.289 | -18.290 | -8.4% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 11618 | 1977.841 | 0 | no_tensor_candidates (11618) |
| QuantBatchMatmulV3 | 18870 | 310.039 | 0 | no_tensor_candidates (5550) |
| hcom_allReduce_ | 11618 | 300.822 | 0 | no_tensor_candidates (11618) |
| Slice | 296 | 107.526 | 0 | no_tensor_candidates (296) |
| ForeachAddList | 5550 | 91.679 | 0 | no_tensor_candidates (5550) |
| MatMulV3 | 5550 | 81.786 | 0 | no_tensor_candidates (5550) |
| MoeInitRoutingV3 | 5550 | 71.053 | 0 | no_tensor_candidates (5550) |
| MatMulV2 | 1628 | 39.855 | 0 | no_tensor_candidates (1554) |
| MoeTokenUnpermute | 5550 | 26.160 | 0 | no_tensor_candidates (5550) |
| MoeGatingTopK | 5550 | 22.270 | 5550 | unfused_subgraph_is_not_the_observed_native_kernel (5550) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| GroupedMatmulSwigluQuantV2 | e41e237309f2 | 5550 | compared | 88.039 | 10.756 | -77.283 | -87.8% | relative_15pct | false |
| LightningIndexer | 794631f68c84 | 1554 | compared | 24.905 | 0.909 | -23.996 | -96.4% | absolute_15us | false |
| MlaPrologV3 | da186cb419f7 | 1554 | compared | 41.291 | 18.327 | -22.963 | -55.6% | absolute_15us | false |
| MlaPrologV3 | 67f03fbdff71 | 4218 | compared | 40.913 | 18.327 | -22.585 | -55.2% | absolute_15us | false |
| MoeGatingTopK | 546f21216db3 | 5550 | reference_only | 4.013 | 0.003 | -4.010 | - | reference_only | - |

## a3_qwen35 / case_default

Graph: `sha256:e31eb9f5f499d122b1f5f1b8e2d5a81213359afc2331d8a3ed4d00a492c2dd51`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 10 | 2 | 8 | 89 | 447 |
| absolute_15us | 4 | 3 | 1 | 166 | 60 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GroupedMatmul | relative_15pct | 2814 | 80 | 0 | 55.146 | 25.818 | 689.328 | 322.728 | -366.599 | -53.2% | 0 / 1 |
| MoeGatingTopK | relative_15pct | 2747 | 82 | 0 | 19.997 | 0.651 | 243.864 | 7.944 | -235.920 | -96.7% | 0 / 1 |
| MatMulV2 | relative_15pct | 17879 | 164 | 0 | 10.487 | 6.263 | 63.943 | 38.190 | -25.754 | -40.3% | 0 / 1 |
| FusedInferAttentionScore | relative_15pct | 737 | 11 | 0 | 9.699 | 5.593 | 881.709 | 508.463 | -373.246 | -42.3% | 0 / 1 |
| _layer_norm_fwd_1pass_kernel_npu | relative_15pct | 2010 | 60 | 0 | 4.495 | 2.517 | 74.909 | 41.943 | -32.966 | -44.0% | 0 / 1 |
| ScatterPaKvCache | relative_15pct | 737 | 22 | 0 | 1.422 | 0.308 | 64.639 | 13.981 | -50.658 | -78.4% | 0 / 1 |
| DynamicQuant | relative_15pct | 670 | 20 | 0 | 1.232 | 0.839 | 61.623 | 41.970 | -19.653 | -31.9% | 0 / 1 |
| GemmaRmsNorm | relative_15pct | 268 | 8 | 0 | 1.026 | 0.447 | 128.190 | 55.927 | -72.263 | -56.4% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fused_gdn_gating_kernel | absolute_15us | 2010 | 60 | 0 | 1.785 | 0.033 | 29.754 | 0.546 | -29.208 | -98.2% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV2 | absolute_15us | 17879 | 82 | 0 | 1.952 | 2.294 | 23.799 | 27.982 | 4.183 | +17.6% | 1 / 0 |
| SwiGlu | absolute_15us | 2814 | 84 | 0 | 1.518 | 0.514 | 18.066 | 6.117 | -11.949 | -66.1% | 2 / 0 |
| MatMulV2 | relative_15pct | 17879 | 69 | 0 | 15.683 | 14.629 | 227.293 | 212.009 | -15.284 | -6.7% | 1 / 0 |
| QuantBatchMatmulV3 | relative_15pct | 670 | 20 | 0 | 4.660 | 4.499 | 232.983 | 224.963 | -8.020 | -3.4% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 5628 | 913.004 | 0 | no_tensor_candidates (5628) |
| GroupedMatmulSwigluQuant | 2680 | 217.099 | 2680 | unfused_subgraph_is_not_the_observed_native_kernel (2680) |
| MatMulV2 | 17879 | 190.026 | 0 | no_tensor_candidates (17564) |
| GroupedMatmul | 2814 | 178.155 | 0 | no_tensor_candidates (2734) |
| hcom_allReduce_ | 5628 | 159.599 | 0 | no_tensor_candidates (5628) |
| Cumsum | 2680 | 130.645 | 0 | no_tensor_candidates (2680) |
| ChunkGatedDeltaRuleFwd | 60 | 78.393 | 0 | no_tensor_candidates (60) |
| FusedInferAttentionScore | 737 | 75.245 | 0 | no_tensor_candidates (726) |
| MoeInitRoutingV3 | 2747 | 72.001 | 0 | no_tensor_candidates (2747) |
| AddRmsNormBias | 5494 | 51.285 | 0 | no_tensor_candidates (5494) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| MoeGatingTopK | e9bae15fd0aa | 82 | compared | 243.864 | 7.944 | -235.920 | -96.7% | relative_15pct | false |
| GroupedMatmulSwigluQuant | 172c1cc606f0 | 2680 | reference_only | 81.007 | 344.126 | 263.118 | - | reference_only | - |

## a3_qwen36 / case_default

Graph: `sha256:242186ecdc7c3050fee97a32062f0a85612aca7d2c6718d947f72e049dfebad4`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 14 | 7 | 7 | 627 | 607 |
| absolute_15us | 1 | 0 | 1 | 0 | 96 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | relative_15pct | 3740 | 440 | 0 | 53.447 | 41.253 | 121.472 | 93.756 | -27.716 | -22.8% | 0 / 3 |
| FusedInferAttentionScore | relative_15pct | 323 | 17 | 0 | 21.614 | 12.966 | 1271.390 | 762.694 | -508.696 | -40.0% | 0 / 1 |
| _layer_norm_fwd_1pass_kernel_npu | relative_15pct | 816 | 96 | 0 | 10.352 | 6.040 | 107.831 | 62.915 | -44.916 | -41.7% | 0 / 1 |
| GemmaRmsNorm | relative_15pct | 170 | 20 | 0 | 4.161 | 2.796 | 208.058 | 139.819 | -68.239 | -32.8% | 0 / 1 |
| ScatterPaKvCache | relative_15pct | 323 | 34 | 0 | 2.194 | 0.475 | 64.518 | 13.981 | -50.537 | -78.3% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fused_gdn_gating_kernel | absolute_15us | 816 | 96 | 0 | 4.216 | 0.079 | 43.921 | 0.819 | -43.102 | -98.1% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 3740 | 440 | 0 | 437.374 | 429.389 | 994.032 | 975.883 | -18.149 | -1.8% | 5 / 0 |
| MatMulV2 | relative_15pct | 1649 | 53 | 0 | 29.339 | 28.083 | 553.565 | 529.864 | -23.701 | -4.3% | 1 / 0 |
| SwiGlu | relative_15pct | 1139 | 134 | 0 | 28.000 | 23.887 | 208.954 | 178.258 | -30.696 | -14.7% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 2346 | 1284.175 | 0 | no_tensor_candidates (2346) |
| QuantBatchMatmulV3 | 3740 | 535.605 | 0 | no_tensor_candidates (3300) |
| hcom_allReduce_ | 2346 | 233.875 | 0 | no_tensor_candidates (2346) |
| ChunkGatedDeltaRuleFwd | 96 | 164.082 | 0 | no_tensor_candidates (96) |
| AddRmsNormBias | 2278 | 107.967 | 0 | no_tensor_candidates (2278) |
| FusedInferAttentionScore | 323 | 100.845 | 0 | no_tensor_candidates (306) |
| MatMulV2 | 1649 | 75.506 | 0 | no_tensor_candidates (1596) |
| DynamicQuant | 3740 | 66.998 | 0 | no_tensor_candidates (3300) |
| MatMulV3 | 102 | 57.571 | 0 | no_tensor_candidates (102) |
| allgatherAicpuKernel | 119 | 34.120 | 0 | no_tensor_candidates (119) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| - | - | 0 | No valid subgraph cohort | - | - | - | - | - | - |

## a3_v4f / case_default

Graph: `sha256:889a2079ea7768a1599aabf21de97eaad21818a6ad862ebe67b6ed8e9a8691da`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 14 | 2 | 12 | 88 | 466 |
| absolute_15us | 1 | 0 | 1 | 0 | 65 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HcPost | relative_15pct | 88 | 88 | 0 | 36.817 | 22.170 | 418.375 | 251.931 | -166.444 | -39.8% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 241 | 109 | 0 | 15.331 | 14.036 | 140.651 | 128.772 | -11.878 | -8.4% | 0 / 3 |
| MatMulV2 | relative_15pct | 110 | 88 | 0 | 11.809 | 9.528 | 134.198 | 108.274 | -25.924 | -19.3% | 0 / 4 |
| DynamicQuant | relative_15pct | 239 | 132 | 0 | 8.164 | 5.077 | 61.851 | 38.460 | -23.391 | -37.8% | 0 / 2 |
| RmsNorm | relative_15pct | 182 | 46 | 0 | 4.105 | 2.573 | 89.236 | 55.931 | -33.305 | -37.3% | 0 / 1 |
| SparseAttnSharedkv | relative_15pct | 44 | 3 | 0 | 1.467 | 0.178 | 489.163 | 59.419 | -429.744 | -87.9% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 239 | 65 | 0 | 2.056 | 0.682 | 31.631 | 10.499 | -21.132 | -66.8% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 241 | 88 | 0 | 9.791 | 9.268 | 111.257 | 105.320 | -5.937 | -5.3% | 2 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| SparseAttnSharedkv | 44 | 98.897 | 0 | candidate_physical_work_differs (41) |
| hcom_alltoallv_ | 264 | 64.783 | 0 | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | no_tensor_candidates (90) |
| HcPre | 88 | 37.975 | 88 | unfused_subgraph_is_not_the_observed_native_kernel (88) |
| QuantBatchMatmulV3 | 241 | 28.176 | 0 | no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 0 | no_tensor_candidates (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 0 | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 44 | unfused_subgraph_is_not_the_observed_native_kernel (44) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPost | 1131dabe1958 | 88 | compared | 418.375 | 251.931 | -166.444 | -39.8% | relative_15pct | false |
| HcPre | 7285ede614e3 | 88 | reference_only | 431.534 | 926.170 | 494.636 | - | reference_only | - |
| GroupedMatmulSwigluQuant | d955db45e826 | 44 | reference_only | 588.788 | 5681.584 | 5092.796 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | 0c7dd0ae8efd | 21 | reference_only | 399.030 | 248.045 | -150.985 | - | reference_only | - |

## a3_v4f / selected_native_fusion

Graph: `sha256:6ed31ea0ee0f31aaf0da3b8375c67ae06f78f9cec3fc19f365a3246fb346a70f`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 15 | 2 | 13 | 88 | 554 |
| absolute_15us | 1 | 0 | 1 | 0 | 65 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HcPre | relative_15pct | 88 | 88 | 0 | 37.975 | 63.496 | 431.534 | 721.545 | 290.011 | +67.2% | 0 / 1 |
| HcPost | relative_15pct | 88 | 88 | 0 | 36.817 | 26.166 | 418.375 | 297.336 | -121.038 | -28.9% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 241 | 109 | 0 | 15.331 | 14.036 | 140.651 | 128.772 | -11.878 | -8.4% | 0 / 3 |
| MatMulV2 | relative_15pct | 110 | 88 | 0 | 11.809 | 9.528 | 134.198 | 108.274 | -25.924 | -19.3% | 0 / 4 |
| DynamicQuant | relative_15pct | 239 | 132 | 0 | 8.164 | 5.077 | 61.851 | 38.460 | -23.391 | -37.8% | 0 / 2 |
| RmsNorm | relative_15pct | 182 | 46 | 0 | 4.105 | 2.573 | 89.236 | 55.931 | -33.305 | -37.3% | 0 / 1 |
| SparseAttnSharedkv | relative_15pct | 44 | 3 | 0 | 1.467 | 0.178 | 489.163 | 59.419 | -429.744 | -87.9% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 239 | 65 | 0 | 2.056 | 0.682 | 31.631 | 10.499 | -21.132 | -66.8% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 241 | 88 | 0 | 9.791 | 9.268 | 111.257 | 105.320 | -5.937 | -5.3% | 2 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| SparseAttnSharedkv | 44 | 98.897 | 0 | candidate_physical_work_differs (41) |
| hcom_alltoallv_ | 264 | 64.783 | 0 | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | no_tensor_candidates (90) |
| QuantBatchMatmulV3 | 241 | 28.176 | 0 | no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 0 | no_tensor_candidates (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 0 | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 44 | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 0 | no_tensor_candidates (42) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPre | ed360ba09e04 | 88 | compared | 431.534 | 721.545 | 290.011 | +67.2% | relative_15pct | false |
| HcPost | 429394f8813d | 88 | compared | 418.375 | 297.336 | -121.038 | -28.9% | relative_15pct | false |
| GroupedMatmulSwigluQuant | 924f31dfc74b | 44 | reference_only | 588.788 | 5681.584 | 5092.796 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | e635c8e0bf69 | 21 | reference_only | 399.030 | 248.045 | -150.985 | - | reference_only | - |

## a3_v4pro / case_default

Graph: `sha256:8ce87fb19c206cb57a836717055db8e36e11370f5ee7e37ce6ed9b588ce61dc8`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 8 | 3 | 5 | 616 | 1248 |
| absolute_15us | 6 | 4 | 2 | 856 | 752 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HcPost | relative_15pct | 496 | 496 | 0 | 100.241 | 54.644 | 202.098 | 110.169 | -91.930 | -45.5% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 1360 | 744 | 0 | 47.590 | 25.822 | 63.965 | 34.707 | -29.259 | -45.7% | 0 / 3 |
| MatMulV2 | relative_15pct | 616 | 8 | 0 | 1.764 | 0.857 | 220.496 | 107.186 | -113.309 | -51.4% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 1352 | 496 | 0 | 17.150 | 9.103 | 34.576 | 18.353 | -16.223 | -46.9% | 0 / 1 |
| RmsNorm | absolute_15us | 1016 | 256 | 0 | 10.399 | 6.267 | 40.621 | 24.479 | -16.142 | -39.7% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 1352 | 616 | 0 | 11.805 | 3.155 | 19.164 | 5.122 | -14.042 | -73.3% | 2 / 0 |
| MatMulV2 | absolute_15us | 616 | 240 | 0 | 5.230 | 6.146 | 21.793 | 25.609 | 3.816 | +17.5% | 2 / 0 |
| QuantBatchMatmulV3 | relative_15pct | 1360 | 368 | 0 | 32.511 | 31.878 | 88.346 | 86.626 | -1.721 | -1.9% | 2 / 0 |
| MatMulV2 | relative_15pct | 616 | 248 | 0 | 27.804 | 30.782 | 112.114 | 124.121 | 12.007 | +10.7% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_allReduce_ | 1008 | 963.972 | 0 | no_tensor_candidates (1008) |
| hcom_alltoallv_ | 1488 | 429.531 | 0 | no_tensor_candidates (1488) |
| hcom_allGather_ | 760 | 420.935 | 0 | no_tensor_candidates (760) |
| SparseAttnSharedkv | 248 | 174.437 | 0 | candidate_physical_work_differs (244), no_tensor_candidates (4) |
| GroupedMatmulSwigluQuantV2 | 248 | 98.114 | 248 | quantized_epilogue_unmodeled (248) |
| HcPre | 496 | 95.134 | 496 | unfused_subgraph_is_not_the_observed_native_kernel (496) |
| QuantBatchMatmulV3 | 1360 | 90.278 | 0 | no_tensor_candidates (248) |
| Compressor | 364 | 77.516 | 0 | no_tensor_candidates (364) |
| allgatherAicpuKernel | 248 | 75.079 | 0 | no_tensor_candidates (248) |
| GroupedMatmul | 248 | 60.731 | 0 | no_tensor_candidates (248) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPost | 04c396525349 | 496 | compared | 202.098 | 110.169 | -91.930 | -45.5% | relative_15pct | false |
| GroupedMatmulSwigluQuantV2 | e3ad41c42490 | 248 | reference_only | 395.623 | 805.300 | 409.678 | - | reference_only | - |
| HcPre | 683c5493fe46 | 496 | reference_only | 191.803 | 451.742 | 259.939 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | 875041d784ca | 120 | reference_only | 113.425 | 18.539 | -94.886 | - | reference_only | - |

## a3_v4pro / selected_native_fusion

Graph: `sha256:a58a6da73dd7540a4766c5f7b921649af3b565c218a8fb86812238ace3a5f8b8`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 9 | 3 | 6 | 616 | 1744 |
| absolute_15us | 6 | 4 | 2 | 856 | 752 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HcPost | relative_15pct | 496 | 496 | 0 | 100.241 | 64.356 | 202.098 | 129.751 | -72.348 | -35.8% | 0 / 1 |
| HcPre | relative_15pct | 496 | 496 | 0 | 95.134 | 156.963 | 191.803 | 316.457 | 124.653 | +65.0% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 1360 | 744 | 0 | 47.590 | 25.822 | 63.965 | 34.707 | -29.259 | -45.7% | 0 / 3 |
| MatMulV2 | relative_15pct | 616 | 8 | 0 | 1.764 | 0.857 | 220.496 | 107.186 | -113.309 | -51.4% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 1352 | 496 | 0 | 17.150 | 9.103 | 34.576 | 18.353 | -16.223 | -46.9% | 0 / 1 |
| RmsNorm | absolute_15us | 1016 | 256 | 0 | 10.399 | 6.267 | 40.621 | 24.479 | -16.142 | -39.7% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 1352 | 616 | 0 | 11.805 | 3.155 | 19.164 | 5.122 | -14.042 | -73.3% | 2 / 0 |
| MatMulV2 | absolute_15us | 616 | 240 | 0 | 5.230 | 6.146 | 21.793 | 25.609 | 3.816 | +17.5% | 2 / 0 |
| QuantBatchMatmulV3 | relative_15pct | 1360 | 368 | 0 | 32.511 | 31.878 | 88.346 | 86.626 | -1.721 | -1.9% | 2 / 0 |
| MatMulV2 | relative_15pct | 616 | 248 | 0 | 27.804 | 30.782 | 112.114 | 124.121 | 12.007 | +10.7% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_allReduce_ | 1008 | 963.972 | 0 | no_tensor_candidates (1008) |
| hcom_alltoallv_ | 1488 | 429.531 | 0 | no_tensor_candidates (1488) |
| hcom_allGather_ | 760 | 420.935 | 0 | no_tensor_candidates (760) |
| SparseAttnSharedkv | 248 | 174.437 | 0 | candidate_physical_work_differs (244), no_tensor_candidates (4) |
| GroupedMatmulSwigluQuantV2 | 248 | 98.114 | 248 | quantized_epilogue_unmodeled (248) |
| QuantBatchMatmulV3 | 1360 | 90.278 | 0 | no_tensor_candidates (248) |
| Compressor | 364 | 77.516 | 0 | no_tensor_candidates (364) |
| allgatherAicpuKernel | 248 | 75.079 | 0 | no_tensor_candidates (248) |
| GroupedMatmul | 248 | 60.731 | 0 | no_tensor_candidates (248) |
| RmsNorm | 1016 | 43.695 | 0 | no_tensor_candidates (760) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPost | 2b7f4fbb5d9b | 496 | compared | 202.098 | 129.751 | -72.348 | -35.8% | relative_15pct | false |
| HcPre | 4840438935f1 | 496 | compared | 191.803 | 316.457 | 124.653 | +65.0% | relative_15pct | false |
| GroupedMatmulSwigluQuantV2 | 1439616849b6 | 248 | reference_only | 395.623 | 805.300 | 409.678 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | 4dd29ed3e598 | 120 | reference_only | 113.425 | 18.539 | -94.886 | - | reference_only | - |

## a5_kimi_k3 / case_default

Graph: `sha256:4e276b5d271500709658fc62e7aa983fe585376a443511ed22a31db9839faed8`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 3 | 0 | 3 | 0 | 439 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV3 | relative_15pct | 21819 | 163 | 0 | 46.985 | 72.764 | 288.250 | 446.402 | 158.153 | +54.9% | 0 / 2 |
| layer_norm_gated_fwd_kernel | relative_15pct | 5451 | 276 | 0 | 37.608 | 5.209 | 136.262 | 18.874 | -117.388 | -86.1% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

None.

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_AicpuKernel | 1104 | 919.190 | 0 | no_tensor_candidates (1104) |
| ChunkKdaFwd | 1104 | 881.998 | 0 | no_tensor_candidates (1104) |
| GroupedMatmul | 27248 | 813.481 | 0 | no_tensor_candidates (27248) |
| HcclLaunchAicpuKernel | 1543 | 683.214 | 0 | no_tensor_candidates (1543) |
| GroupedMatmulSituQuant | 7266 | 666.877 | 0 | no_tensor_candidates (7266) |
| MatMulV3 | 21819 | 656.394 | 0 | no_tensor_candidates (21656) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 0 | no_tensor_candidates (7266) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 0 | no_tensor_candidates (14531) |
| hcom_allGather_ | 15203 | 409.082 | 0 | no_tensor_candidates (15203) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| - | - | 0 | No valid subgraph cohort | - | - | - | - | - | - |

## a5_kimi_k3_decode / source_declared_unfused_reference

Graph: `sha256:32ef79bccf2ae9eff3ec6cabfc362542996d9a9635f14dc3b9284398ca8ab9ec`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 1 | 0 | 1 | 0 | 67 |
| absolute_15us | 4 | 4 | 0 | 10636 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV3 | relative_15pct | 21819 | 67 | 0 | 6.178 | 4.957 | 92.208 | 73.978 | -18.230 | -19.8% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV3 | absolute_15us | 21819 | 8771 | 0 | 117.848 | 70.853 | 13.436 | 8.078 | -5.358 | -39.9% | 2 / 0 |
| TransposeBatchMatMul | absolute_15us | 1798 | 1798 | 0 | 10.496 | 1.908 | 5.838 | 1.061 | -4.776 | -81.8% | 1 / 0 |
| RmsNorm | absolute_15us | 259 | 67 | 0 | 0.292 | 0.001 | 4.358 | 0.011 | -4.347 | -99.8% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_AicpuKernel | 1104 | 919.190 | 0 | no_tensor_candidates (1104) |
| ChunkKdaFwd | 1104 | 881.998 | 0 | no_tensor_candidates (1104) |
| GroupedMatmul | 27248 | 813.481 | 0 | no_tensor_candidates (27248) |
| HcclLaunchAicpuKernel | 1543 | 683.214 | 0 | no_tensor_candidates (1543) |
| GroupedMatmulSituQuant | 7266 | 666.877 | 0 | no_tensor_candidates (7266) |
| MatMulV3 | 21819 | 656.394 | 0 | no_tensor_candidates (12981) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 0 | no_tensor_candidates (7266) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 0 | no_tensor_candidates (14531) |
| hcom_allGather_ | 15203 | 409.082 | 0 | no_tensor_candidates (15203) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| - | - | 0 | No valid subgraph cohort | - | - | - | - | - | - |

## a5_kimi_k3_checkpoint / current_checkpoint_conditional

Graph: `sha256:598acc0a45fb0d2cc2c1577c3fb16f31fb07ba8d093e46fb514c0dfc81a05501`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 8 | 0 | 8 | 0 | 1927 |
| absolute_15us | 1 | 1 | 0 | 96 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicMxQuant | relative_15pct | 22499 | 1112 | 0 | 76.142 | 49.483 | 68.473 | 44.499 | -23.975 | -35.0% | 0 / 2 |
| SituMxQuant | relative_15pct | 7266 | 368 | 0 | 54.142 | 5.503 | 147.124 | 14.953 | -132.172 | -89.8% | 0 / 1 |
| MatMulV3 | relative_15pct | 21819 | 163 | 0 | 46.985 | 72.764 | 288.250 | 446.402 | 158.153 | +54.9% | 0 / 2 |
| layer_norm_gated_fwd_kernel | relative_15pct | 5451 | 276 | 0 | 37.608 | 5.209 | 136.262 | 18.874 | -117.388 | -86.1% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 350 | 8 | 0 | 6.967 | 12.136 | 870.894 | 1516.942 | 646.048 | +74.2% | 0 / 2 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicMxQuant | absolute_15us | 22499 | 96 | 0 | 1.077 | 0.915 | 11.214 | 9.535 | -1.679 | -15.0% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_AicpuKernel | 1104 | 919.190 | 0 | no_tensor_candidates (1104) |
| ChunkKdaFwd | 1104 | 881.998 | 0 | no_tensor_candidates (1104) |
| GroupedMatmul | 27248 | 813.481 | 0 | no_tensor_candidates (27248) |
| HcclLaunchAicpuKernel | 1543 | 683.214 | 0 | no_tensor_candidates (1543) |
| GroupedMatmulSituQuant | 7266 | 666.877 | 7266 | mxfp4_native_execution_unmodeled (7266) |
| MatMulV3 | 21819 | 656.394 | 0 | no_tensor_candidates (21656) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 0 | no_tensor_candidates (6898) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 736 | no_tensor_candidates (13795), mxfp4_native_execution_unmodeled (736) |
| hcom_allGather_ | 15203 | 409.082 | 0 | no_tensor_candidates (15203) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| SituMxQuant | 2506d4b77b15 | 368 | compared | 147.124 | 14.953 | -132.172 | -89.8% | relative_15pct | false |
| GroupedMatmulSituQuant | a3c7aca518de | 7266 | reference_only | 91.780 | 11336.311 | 11244.530 | - | reference_only | - |

## a5_kimi_k3_decode_checkpoint / current_checkpoint_conditional

Graph: `sha256:4e36212b6422955d69fec949ea7b33d30c449dd9145b97ee57f9ceca8e53fa5c`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 0 | 2 | 0 | 6965 |
| absolute_15us | 6 | 6 | 0 | 36504 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SituMxQuant | relative_15pct | 7266 | 6898 | 0 | 449.295 | 0.013 | 65.134 | 0.002 | -65.132 | -100.0% | 0 / 1 |
| MatMulV3 | relative_15pct | 21819 | 67 | 0 | 6.178 | 4.957 | 92.208 | 73.978 | -18.230 | -19.8% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV3 | absolute_15us | 21819 | 8771 | 0 | 117.848 | 70.853 | 13.436 | 8.078 | -5.358 | -39.9% | 2 / 0 |
| DynamicMxQuant | absolute_15us | 22499 | 18971 | 0 | 78.422 | 0.103 | 4.134 | 0.005 | -4.128 | -99.9% | 1 / 0 |
| RmsNormDynamicMxQuant | absolute_15us | 7265 | 6897 | 0 | 20.611 | 0.033 | 2.988 | 0.005 | -2.984 | -99.8% | 1 / 0 |
| TransposeBatchMatMul | absolute_15us | 1798 | 1798 | 0 | 10.496 | 1.908 | 5.838 | 1.061 | -4.776 | -81.8% | 1 / 0 |
| RmsNorm | absolute_15us | 259 | 67 | 0 | 0.292 | 0.001 | 4.358 | 0.011 | -4.347 | -99.8% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_AicpuKernel | 1104 | 919.190 | 0 | no_tensor_candidates (1104) |
| ChunkKdaFwd | 1104 | 881.998 | 0 | no_tensor_candidates (1104) |
| GroupedMatmul | 27248 | 813.481 | 0 | no_tensor_candidates (27248) |
| HcclLaunchAicpuKernel | 1543 | 683.214 | 0 | no_tensor_candidates (1543) |
| GroupedMatmulSituQuant | 7266 | 666.877 | 7266 | mxfp4_native_execution_unmodeled (7266) |
| MatMulV3 | 21819 | 656.394 | 0 | no_tensor_candidates (12981) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 0 | no_tensor_candidates (368) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 13795 | mxfp4_native_execution_unmodeled (13795), no_tensor_candidates (736) |
| hcom_allGather_ | 15203 | 409.082 | 0 | no_tensor_candidates (15203) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| SituMxQuant | 68b483bece8d | 6898 | compared | 65.134 | 0.002 | -65.132 | -100.0% | relative_15pct | false |
| GroupedMatmulSituQuant | 793279dcd26d | 7266 | reference_only | 91.780 | 7.735 | -84.045 | - | reference_only | - |
| MlaPrologV3 | 828f6ca5e170 | 1798 | reference_only | 22.248 | 17.439 | -4.809 | - | reference_only | - |

## a5_qwen38 / case_default

Graph: `sha256:83f53cbcffb2bab2a1dab5381b0adf82fc3d7b116bfaaa70f8b19c7402ea8fda`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 22 | 4 | 18 | 181 | 808 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 1920 | 160 | 0 | 714.307 | 1253.383 | 4464.419 | 7833.641 | 3369.222 | +75.5% | 0 / 4 |
| MatMulV3 | relative_15pct | 1956 | 147 | 0 | 431.194 | 725.922 | 2933.291 | 4938.243 | 2004.952 | +68.4% | 0 / 3 |
| FusedInferAttentionScore | relative_15pct | 228 | 17 | 0 | 213.742 | 129.650 | 12573.041 | 7626.473 | -4946.568 | -39.3% | 0 / 1 |
| ChunkGatedDeltaRuleFwdPrepare | relative_15pct | 48 | 48 | 0 | 73.924 | 58.965 | 1540.079 | 1228.428 | -311.651 | -20.2% | 0 / 1 |
| SwiGlu | relative_15pct | 804 | 67 | 0 | 34.369 | 28.664 | 512.964 | 427.819 | -85.145 | -16.6% | 0 / 1 |
| ChunkFwdO | relative_15pct | 48 | 48 | 0 | 24.817 | 17.128 | 517.022 | 356.831 | -160.192 | -31.0% | 0 / 1 |
| DynamicMxQuant | relative_15pct | 960 | 80 | 0 | 18.255 | 15.053 | 228.193 | 188.167 | -40.026 | -17.5% | 0 / 2 |
| Slice | relative_15pct | 4273 | 96 | 0 | 16.809 | 12.885 | 175.089 | 134.218 | -40.871 | -23.3% | 0 / 2 |
| AddRmsNormDynamicMxQuant | relative_15pct | 960 | 80 | 0 | 14.951 | 11.797 | 186.888 | 147.459 | -39.429 | -21.1% | 0 / 1 |
| _layer_norm_fwd_1pass_kernel_npu | relative_15pct | 576 | 48 | 0 | 11.478 | 7.248 | 239.125 | 150.995 | -88.130 | -36.9% | 0 / 1 |
| ScatterPaKvCache | relative_15pct | 228 | 17 | 0 | 1.674 | 0.570 | 98.500 | 33.554 | -64.945 | -65.9% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV3 | relative_15pct | 1956 | 37 | 0 | 27.188 | 23.851 | 734.804 | 644.633 | -90.171 | -12.3% | 1 / 0 |
| ChunkFwdH | relative_15pct | 48 | 48 | 0 | 38.757 | 40.620 | 807.427 | 846.259 | 38.832 | +4.8% | 1 / 0 |
| fused_gdn_gating_kernel | relative_15pct | 576 | 48 | 0 | 32.340 | 28.031 | 673.758 | 583.985 | -89.773 | -13.3% | 1 / 0 |
| CausalConv1d | relative_15pct | 576 | 48 | 0 | 16.259 | 17.948 | 338.724 | 373.912 | 35.189 | +10.4% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| QuantBatchMatmulV3 | 1920 | 781.406 | 0 | no_tensor_candidates (1760) |
| MatMulV3 | 1956 | 611.956 | 0 | no_tensor_candidates (1772) |
| FusedInferAttentionScore | 228 | 243.894 | 0 | no_tensor_candidates (211) |
| fused_gdn_gating_kernel | 576 | 44.045 | 0 | no_tensor_candidates (528) |
| Slice | 4273 | 39.010 | 0 | no_tensor_candidates (3985), candidate_physical_work_differs (192) |
| SwiGlu | 804 | 37.136 | 0 | no_tensor_candidates (737) |
| DynamicMxQuant | 960 | 21.934 | 0 | no_tensor_candidates (880) |
| split_qkv_rmsnorm_mrope_kernel | 228 | 20.694 | 0 | no_tensor_candidates (228) |
| CausalConv1d | 576 | 20.357 | 0 | no_tensor_candidates (528) |
| Transpose | 384 | 19.707 | 0 | no_tensor_candidates (384) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| - | - | 0 | No valid subgraph cohort | - | - | - | - | - | - |
