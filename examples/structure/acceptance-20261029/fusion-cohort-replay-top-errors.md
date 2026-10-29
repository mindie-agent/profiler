# Complete-Capture Operator Families And Tiered Conditional Errors

Historical captures; report refresh can reuse saved comparisons without raw scans or new predictions.

Policy: observed complete-event mean > 50 us uses absolute relative error <= 15%; mean <= 50 us uses absolute per-call difference <= 15 us, including exactly 50 us. Per-call diff is predicted minus observed. No launch floor is added to predictions. This is an acceptance allowance, not evidence that a residual was caused by launch overhead.

Acceptance is decided per cohort before aggregation. Family/tier means are call-count weighted; pass/fail counts preserve failed cohorts even if signed averages cancel. The scored columns cover the indicated tier and pass/fail subset only: failed cohorts appear in error tables and passed cohorts appear within tolerance, including when a family has both. All/reference event counts describe the whole native family and repeat across these subsets. Every native type and full-family aggregate remains in JSON.

Large failed cohorts lead Top Errors, sorted by their observed activity; small failures are separate and sorted by absolute per-call difference. Within-tolerance groups and unscored coverage have separate tables. Reference, clipped, failed and unmatched events are not scored.

Activity sums count overlapping events separately and are not wall-clock latency. Variant totals reuse captures and must not be counted as independent evidence.

| Tier | Compared cohorts across variants | Passed | Failed |
| --- | ---: | ---: | ---: |
| relative_15pct | 295 | 73 | 222 |
| absolute_15us | 147 | 122 | 25 |
| All scored | 442 | 195 | 247 |

## a3_glm53_prefill / source_declared_unfused_reference

Graph: `sha256:8e4d8b685df1dbaa3d6ff0bdd56a661daa811fe60fc7ec76ee68d93d8561346b`.

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
| MlaPrologV3 | 30a81e6afd86 | 21 | reference_only | 1342.506 | 491.634 | -850.872 | - | reference_only | - |
| MlaPrologV3 | 9c64cc88b208 | 57 | reference_only | 1248.166 | 491.634 | -756.532 | - | reference_only | - |
| GroupedMatmulSwigluQuantV2 | 9d2e3cf2fc3b | 75 | reference_only | 1323.133 | 600.368 | -722.765 | - | reference_only | - |
| LightningIndexer | b78e3b676bc6 | 21 | reference_only | 1492.464 | 1873.906 | 381.442 | - | reference_only | - |
| MoeGatingTopK | 36fbad1fcfaf | 75 | reference_only | 101.699 | 13.462 | -88.237 | - | reference_only | - |

## a3_glm53_prefill / selected_native_fusion

Graph: `sha256:0eb86c0a13a556ba3d7515e1a82d8026bd9155fbf6e736ac2d8a2c545f1f44e4`.

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
| MlaPrologV3 | e6d1c339b747 | 21 | compared | 1342.506 | 451.382 | -891.124 | -66.4% | relative_15pct | false |
| MlaPrologV3 | 915206591845 | 57 | compared | 1248.166 | 451.382 | -796.784 | -63.8% | relative_15pct | false |
| LightningIndexer | eb8f815075ae | 21 | compared | 1492.464 | 1873.906 | 381.442 | +25.6% | relative_15pct | false |
| GroupedMatmulSwigluQuantV2 | f0b38b6472c2 | 75 | compared | 1323.133 | 1275.932 | -47.201 | -3.6% | relative_15pct | true |
| MoeGatingTopK | 6b7561b11714 | 75 | reference_only | 101.699 | 11.181 | -90.518 | - | reference_only | - |

## a3_glm53_prefill_shared_quant / source_shared_int32_conditional

Graph: `sha256:0e558bd4b1af23576c8204e3238e5acd3de53779b178d0966fb07daaf9ba0521`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 13 | 4 | 9 | 105 | 617 |
| absolute_15us | 5 | 3 | 2 | 81 | 99 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseFlashAttention | relative_15pct | 78 | 78 | 0 | 1029.574 | 477.452 | 13199.665 | 6121.175 | -7078.489 | -53.6% | 0 / 1 |
| AddRmsNormBias | relative_15pct | 153 | 153 | 0 | 37.924 | 25.674 | 247.871 | 167.806 | -80.065 | -32.3% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 255 | 150 | 0 | 23.893 | 12.125 | 159.284 | 80.830 | -78.454 | -49.3% | 0 / 2 |
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
| DequantSwigluQuant | absolute_15us | 75 | 75 | 0 | 1.779 | 1.263 | 23.720 | 16.846 | -6.874 | -29.0% | 1 / 0 |
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
| MoeTokenUnpermute | 75 | 37.376 | 0 | no_tensor_candidates (75) |
| LightningIndexer | 21 | 31.342 | 21 | unfused_subgraph_is_not_the_observed_native_kernel (21) |
| MoeInitRoutingV3 | 75 | 24.498 | 0 | no_tensor_candidates (75) |
| ForeachAddList | 75 | 10.799 | 0 | no_tensor_candidates (75) |
| Muls | 75 | 9.240 | 0 | no_tensor_candidates (75) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| MlaPrologV3 | fdaa682a6927 | 21 | reference_only | 1342.506 | 491.634 | -850.872 | - | reference_only | - |
| MlaPrologV3 | 76e795f16eb7 | 57 | reference_only | 1248.166 | 491.634 | -756.532 | - | reference_only | - |
| GroupedMatmulSwigluQuantV2 | 4a1fc50a5427 | 75 | reference_only | 1323.133 | 600.368 | -722.765 | - | reference_only | - |
| LightningIndexer | 8cb1a5387f35 | 21 | reference_only | 1492.464 | 1873.906 | 381.442 | - | reference_only | - |
| MoeGatingTopK | 068ff48c2bab | 75 | reference_only | 101.699 | 13.462 | -88.237 | - | reference_only | - |

## a3_glm53_decode / source_declared_unfused_reference

Graph: `sha256:fb2fc64d62f7425b5fa76cf930db54897975c1efb96877142a4ebf8e6f46314e`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 1 | 1 | 74 | 5772 |
| absolute_15us | 14 | 14 | 0 | 49802 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseFlashAttention | relative_15pct | 5772 | 5772 | 0 | 523.698 | 28.860 | 90.731 | 5.000 | -85.731 | -94.5% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | absolute_15us | 18870 | 13320 | 0 | 237.111 | 104.801 | 17.801 | 7.868 | -9.933 | -55.8% | 5 / 0 |
| TransposeBatchMatMul | absolute_15us | 5772 | 5772 | 0 | 81.808 | 28.860 | 14.173 | 5.000 | -9.173 | -64.7% | 1 / 0 |
| DynamicQuant | absolute_15us | 17316 | 17316 | 0 | 50.444 | 43.290 | 2.913 | 2.500 | -0.413 | -14.2% | 3 / 0 |
| AddRmsNormBias | absolute_15us | 11322 | 11322 | 0 | 44.742 | 28.305 | 3.952 | 2.500 | -1.452 | -36.7% | 1 / 0 |
| LayerNormV3 | absolute_15us | 1554 | 1554 | 0 | 8.257 | 3.885 | 5.313 | 2.500 | -2.813 | -52.9% | 1 / 0 |
| AddRmsNormDynamicQuant | absolute_15us | 222 | 222 | 0 | 1.055 | 0.555 | 4.751 | 2.500 | -2.251 | -47.4% | 1 / 0 |
| SwiGlu | absolute_15us | 222 | 222 | 0 | 0.810 | 0.555 | 3.650 | 2.500 | -1.150 | -31.5% | 1 / 0 |
| RmsNorm | absolute_15us | 74 | 74 | 0 | 0.356 | 0.185 | 4.813 | 2.500 | -2.313 | -48.1% | 1 / 0 |
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
| GroupedMatmulSwigluQuantV2 | 273c3ed9b9e2 | 5550 | reference_only | 88.039 | 15.557 | -72.482 | - | reference_only | - |
| MlaPrologV3 | 3b92648d8108 | 1554 | reference_only | 41.291 | 38.014 | -3.277 | - | reference_only | - |
| MlaPrologV3 | 0dcd3acad83a | 4218 | reference_only | 40.913 | 38.014 | -2.899 | - | reference_only | - |
| LightningIndexer | de166070c677 | 1554 | reference_only | 24.905 | 7.500 | -17.405 | - | reference_only | - |
| MoeGatingTopK | c7c0cbddfc8a | 5550 | reference_only | 4.013 | 7.500 | 3.487 | - | reference_only | - |

## a3_glm53_decode / selected_native_fusion

Graph: `sha256:de5b454843d69005fa85ba5aae3a636a14d60a447fd77eacde015a23d125314f`.

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
| GroupedMatmulSwigluQuantV2 | aa32ef207ffd | 5550 | compared | 88.039 | 10.756 | -77.283 | -87.8% | relative_15pct | false |
| LightningIndexer | b27417f69183 | 1554 | compared | 24.905 | 0.909 | -23.996 | -96.4% | absolute_15us | false |
| MlaPrologV3 | 3a1c59cb2c4e | 1554 | compared | 41.291 | 18.327 | -22.963 | -55.6% | absolute_15us | false |
| MlaPrologV3 | 195c50492b57 | 4218 | compared | 40.913 | 18.327 | -22.585 | -55.2% | absolute_15us | false |
| MoeGatingTopK | 6deac7758ba0 | 5550 | reference_only | 4.013 | 0.003 | -4.010 | - | reference_only | - |

## a3_glm53_decode_shared_quant / source_shared_int32_conditional

Graph: `sha256:eac22972be740053a58ad158ed09fa22849587298933008a4497677208ee69fb`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 1 | 1 | 74 | 5772 |
| absolute_15us | 16 | 16 | 0 | 60902 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseFlashAttention | relative_15pct | 5772 | 5772 | 0 | 523.698 | 28.860 | 90.731 | 5.000 | -85.731 | -94.5% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | absolute_15us | 18870 | 18870 | 0 | 310.039 | 132.551 | 16.430 | 7.024 | -9.406 | -57.2% | 6 / 0 |
| TransposeBatchMatMul | absolute_15us | 5772 | 5772 | 0 | 81.808 | 28.860 | 14.173 | 5.000 | -9.173 | -64.7% | 1 / 0 |
| DynamicQuant | absolute_15us | 17316 | 17316 | 0 | 50.444 | 43.290 | 2.913 | 2.500 | -0.413 | -14.2% | 3 / 0 |
| AddRmsNormBias | absolute_15us | 11322 | 11322 | 0 | 44.742 | 28.305 | 3.952 | 2.500 | -1.452 | -36.7% | 1 / 0 |
| DequantSwigluQuant | absolute_15us | 5550 | 5550 | 0 | 18.782 | 13.875 | 3.384 | 2.500 | -0.884 | -26.1% | 1 / 0 |
| LayerNormV3 | absolute_15us | 1554 | 1554 | 0 | 8.257 | 3.885 | 5.313 | 2.500 | -2.813 | -52.9% | 1 / 0 |
| AddRmsNormDynamicQuant | absolute_15us | 222 | 222 | 0 | 1.055 | 0.555 | 4.751 | 2.500 | -2.251 | -47.4% | 1 / 0 |
| SwiGlu | absolute_15us | 222 | 222 | 0 | 0.810 | 0.555 | 3.650 | 2.500 | -1.150 | -31.5% | 1 / 0 |
| RmsNorm | absolute_15us | 74 | 74 | 0 | 0.356 | 0.185 | 4.813 | 2.500 | -2.313 | -48.1% | 1 / 0 |
| MatMulV2 | relative_15pct | 1628 | 74 | 0 | 16.027 | 14.674 | 216.579 | 198.291 | -18.287 | -8.4% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 11618 | 1977.841 | 0 | no_tensor_candidates (11618) |
| GroupedMatmulSwigluQuantV2 | 5550 | 488.615 | 5550 | quantized_epilogue_unmodeled (5550) |
| hcom_allReduce_ | 11618 | 300.822 | 0 | no_tensor_candidates (11618) |
| GroupedMatmul | 5550 | 293.637 | 5550 | quantized_epilogue_unmodeled (5550) |
| MlaPrologV3 | 5772 | 236.735 | 5772 | unfused_subgraph_is_not_the_observed_native_kernel (5772) |
| Slice | 296 | 107.526 | 0 | no_tensor_candidates (296) |
| ForeachAddList | 5550 | 91.679 | 0 | no_tensor_candidates (5550) |
| MatMulV3 | 5550 | 81.786 | 0 | no_tensor_candidates (5550) |
| MoeInitRoutingV3 | 5550 | 71.053 | 0 | no_tensor_candidates (5550) |
| MatMulV2 | 1628 | 39.855 | 0 | no_tensor_candidates (1554) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| GroupedMatmulSwigluQuantV2 | b5b0f8e42de3 | 5550 | reference_only | 88.039 | 15.557 | -72.482 | - | reference_only | - |
| MlaPrologV3 | 1e962f1d73b0 | 1554 | reference_only | 41.291 | 38.014 | -3.277 | - | reference_only | - |
| MlaPrologV3 | 1cac1b59e630 | 4218 | reference_only | 40.913 | 38.014 | -2.899 | - | reference_only | - |
| LightningIndexer | 2938776a0164 | 1554 | reference_only | 24.905 | 7.500 | -17.405 | - | reference_only | - |
| MoeGatingTopK | cc72ca720e14 | 5550 | reference_only | 4.013 | 7.500 | 3.487 | - | reference_only | - |

## a3_qwen35 / case_default

Graph: `sha256:612a05fe0104c8ff6909f7a01782329a924623b0161aa052db4c444b20178f99`.

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
| fused_gdn_gating_kernel | absolute_15us | 2010 | 60 | 0 | 1.785 | 0.150 | 29.754 | 2.500 | -27.254 | -91.6% | 0 / 1 |

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
| MoeGatingTopK | 83ddb50a5241 | 82 | compared | 243.864 | 7.944 | -235.920 | -96.7% | relative_15pct | false |
| GroupedMatmulSwigluQuant | fe0f00cfb280 | 2680 | reference_only | 81.007 | 344.126 | 263.118 | - | reference_only | - |

## a3_qwen35_paged_prefill_q8192 / paged_body_geometry_conditional

Graph: `sha256:13f8556ff1eb3178e0c716611c54197a4e6924e78eb0b08317dea71b487c56e9`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 10 | 2 | 8 | 89 | 447 |
| absolute_15us | 4 | 3 | 1 | 166 | 60 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GroupedMatmul | relative_15pct | 2814 | 80 | 0 | 55.146 | 25.818 | 689.328 | 322.728 | -366.599 | -53.2% | 0 / 1 |
| FusedInferAttentionScore | relative_15pct | 737 | 11 | 0 | 27.242 | 5.593 | 2476.504 | 508.463 | -1968.041 | -79.5% | 0 / 1 |
| MoeGatingTopK | relative_15pct | 2747 | 82 | 0 | 19.997 | 0.651 | 243.864 | 7.944 | -235.920 | -96.7% | 0 / 1 |
| MatMulV2 | relative_15pct | 17879 | 164 | 0 | 10.487 | 6.263 | 63.943 | 38.190 | -25.754 | -40.3% | 0 / 1 |
| _layer_norm_fwd_1pass_kernel_npu | relative_15pct | 2010 | 60 | 0 | 4.495 | 2.517 | 74.909 | 41.943 | -32.966 | -44.0% | 0 / 1 |
| ScatterPaKvCache | relative_15pct | 737 | 22 | 0 | 1.422 | 0.308 | 64.639 | 13.981 | -50.658 | -78.4% | 0 / 1 |
| DynamicQuant | relative_15pct | 670 | 20 | 0 | 1.232 | 0.839 | 61.623 | 41.970 | -19.653 | -31.9% | 0 / 1 |
| GemmaRmsNorm | relative_15pct | 268 | 8 | 0 | 1.026 | 0.447 | 128.190 | 55.927 | -72.263 | -56.4% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fused_gdn_gating_kernel | absolute_15us | 2010 | 60 | 0 | 1.785 | 0.150 | 29.754 | 2.500 | -27.254 | -91.6% | 0 / 1 |

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
| MoeGatingTopK | 02f530feac8b | 82 | compared | 243.864 | 7.944 | -235.920 | -96.7% | relative_15pct | false |
| GroupedMatmulSwigluQuant | 1893e381e021 | 2680 | reference_only | 81.007 | 344.126 | 263.118 | - | reference_only | - |

## a3_qwen35_paged_decode_q1 / paged_body_geometry_conditional

Graph: `sha256:41bd390fb7cf9cbd684879a1b93fdbdd8858be3ba9a0511e40077828e9935640`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 1 | 1 | 0 | 69 | 0 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

None.

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV2 | relative_15pct | 17879 | 69 | 0 | 15.683 | 14.629 | 227.293 | 212.009 | -15.284 | -6.7% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 5628 | 913.004 | 0 | no_tensor_candidates (5628) |
| GroupedMatmulSwigluQuant | 2680 | 217.099 | 2680 | unfused_subgraph_is_not_the_observed_native_kernel (2680) |
| MatMulV2 | 17879 | 190.026 | 0 | no_tensor_candidates (17810) |
| GroupedMatmul | 2814 | 178.155 | 0 | no_tensor_candidates (2814) |
| hcom_allReduce_ | 5628 | 159.599 | 0 | no_tensor_candidates (5628) |
| Cumsum | 2680 | 130.645 | 0 | no_tensor_candidates (2680) |
| ChunkGatedDeltaRuleFwd | 60 | 78.393 | 0 | no_tensor_candidates (60) |
| FusedInferAttentionScore | 737 | 75.245 | 0 | no_tensor_candidates (737) |
| MoeInitRoutingV3 | 2747 | 72.001 | 0 | no_tensor_candidates (2747) |
| AddRmsNormBias | 5494 | 51.285 | 0 | no_tensor_candidates (5494) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| GroupedMatmulSwigluQuant | 6c7676bc05f1 | 2680 | reference_only | 81.007 | 10.000 | -71.007 | - | reference_only | - |

## a3_qwen35_paged_decode_q2 / paged_body_geometry_conditional

Graph: `sha256:a2f0e933fd841be9b01eabd9a022ddf788706d6ad6d2b7bed7e83efa759f02e4`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 1 | 1 | 65 | 715 |
| absolute_15us | 11 | 10 | 1 | 17615 | 2600 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FusedInferAttentionScore | relative_15pct | 737 | 715 | 0 | 38.305 | 5.004 | 53.574 | 6.999 | -46.574 | -86.9% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GroupedMatmul | absolute_15us | 2814 | 2600 | 0 | 116.411 | 13.000 | 44.773 | 5.000 | -39.773 | -88.8% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV2 | absolute_15us | 17879 | 7995 | 0 | 46.325 | 39.975 | 5.794 | 5.000 | -0.794 | -13.7% | 2 / 0 |
| RecurrentGatedDeltaRule | absolute_15us | 1950 | 1950 | 0 | 31.545 | 11.054 | 16.177 | 5.669 | -10.508 | -65.0% | 1 / 0 |
| MoeGatingTopK | absolute_15us | 2747 | 2665 | 0 | 12.166 | 6.663 | 4.565 | 2.500 | -2.065 | -45.2% | 1 / 0 |
| QuantBatchMatmulV3 | absolute_15us | 670 | 650 | 0 | 11.058 | 3.250 | 17.013 | 5.000 | -12.013 | -70.6% | 1 / 0 |
| SwiGlu | absolute_15us | 2814 | 2730 | 0 | 9.726 | 6.825 | 3.563 | 2.500 | -1.063 | -29.8% | 2 / 0 |
| DynamicQuant | absolute_15us | 670 | 650 | 0 | 2.130 | 1.625 | 3.277 | 2.500 | -0.777 | -23.7% | 1 / 0 |
| ScatterPaKvCache | absolute_15us | 737 | 715 | 0 | 1.580 | 1.788 | 2.210 | 2.500 | 0.290 | +13.1% | 1 / 0 |
| GemmaRmsNorm | absolute_15us | 268 | 260 | 0 | 1.133 | 0.650 | 4.357 | 2.500 | -1.857 | -42.6% | 1 / 0 |
| MatMulV2 | relative_15pct | 17879 | 65 | 0 | 14.350 | 13.788 | 220.773 | 212.118 | -8.655 | -3.9% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 5628 | 913.004 | 0 | no_tensor_candidates (5628) |
| GroupedMatmulSwigluQuant | 2680 | 217.099 | 2680 | unfused_subgraph_is_not_the_observed_native_kernel (2680) |
| MatMulV2 | 17879 | 190.026 | 0 | no_tensor_candidates (9819) |
| GroupedMatmul | 2814 | 178.155 | 0 | no_tensor_candidates (214) |
| hcom_allReduce_ | 5628 | 159.599 | 0 | no_tensor_candidates (5628) |
| Cumsum | 2680 | 130.645 | 0 | no_tensor_candidates (2680) |
| ChunkGatedDeltaRuleFwd | 60 | 78.393 | 0 | no_tensor_candidates (60) |
| FusedInferAttentionScore | 737 | 75.245 | 0 | no_tensor_candidates (22) |
| MoeInitRoutingV3 | 2747 | 72.001 | 0 | no_tensor_candidates (2747) |
| AddRmsNormBias | 5494 | 51.285 | 0 | no_tensor_candidates (5494) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| MoeGatingTopK | 9cb50b5571e8 | 2665 | compared | 4.565 | 2.500 | -2.065 | -45.2% | absolute_15us | true |
| GroupedMatmulSwigluQuant | d67e0cba7033 | 2680 | reference_only | 81.007 | 12.039 | -68.968 | - | reference_only | - |

## a3_qwen36 / case_default

Graph: `sha256:c94cfa15d4a83655ad4db4bbbae68e29181a6c7d1d8797ccd1a84e300f92467e`.

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
| fused_gdn_gating_kernel | absolute_15us | 816 | 96 | 0 | 4.216 | 0.240 | 43.921 | 2.500 | -41.421 | -94.3% | 0 / 1 |

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

## a3_qwen36_paged_prefill_q8192 / paged_body_geometry_conditional

Graph: `sha256:08bcfa4dc8c036ddf56e5705dbca9822f7b363b39b73073435fa6aa9d12ecb79`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 14 | 7 | 7 | 627 | 607 |
| absolute_15us | 1 | 0 | 1 | 0 | 96 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FusedInferAttentionScore | relative_15pct | 323 | 17 | 0 | 62.532 | 12.966 | 3678.352 | 762.694 | -2915.659 | -79.3% | 0 / 1 |
| DynamicQuant | relative_15pct | 3740 | 440 | 0 | 53.447 | 41.253 | 121.472 | 93.756 | -27.716 | -22.8% | 0 / 3 |
| _layer_norm_fwd_1pass_kernel_npu | relative_15pct | 816 | 96 | 0 | 10.352 | 6.040 | 107.831 | 62.915 | -44.916 | -41.7% | 0 / 1 |
| GemmaRmsNorm | relative_15pct | 170 | 20 | 0 | 4.161 | 2.796 | 208.058 | 139.819 | -68.239 | -32.8% | 0 / 1 |
| ScatterPaKvCache | relative_15pct | 323 | 34 | 0 | 2.194 | 0.475 | 64.518 | 13.981 | -50.537 | -78.3% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fused_gdn_gating_kernel | absolute_15us | 816 | 96 | 0 | 4.216 | 0.240 | 43.921 | 2.500 | -41.421 | -94.3% | 0 / 1 |

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

## a3_qwen36_paged_decode_q1 / paged_body_geometry_conditional

Graph: `sha256:df571a257a44db62337b9b98bc338bf164d70430c9899bf8f96e6dcee9a326c1`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 1 | 1 | 53 | 34 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FusedInferAttentionScore | relative_15pct | 323 | 34 | 0 | 1.860 | 0.238 | 54.717 | 6.996 | -47.721 | -87.2% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV2 | relative_15pct | 1649 | 53 | 0 | 29.339 | 28.083 | 553.565 | 529.864 | -23.701 | -4.3% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 2346 | 1284.175 | 0 | no_tensor_candidates (2346) |
| QuantBatchMatmulV3 | 3740 | 535.605 | 0 | no_tensor_candidates (3740) |
| hcom_allReduce_ | 2346 | 233.875 | 0 | no_tensor_candidates (2346) |
| ChunkGatedDeltaRuleFwd | 96 | 164.082 | 0 | no_tensor_candidates (96) |
| AddRmsNormBias | 2278 | 107.967 | 0 | no_tensor_candidates (2278) |
| FusedInferAttentionScore | 323 | 100.845 | 0 | no_tensor_candidates (289) |
| MatMulV2 | 1649 | 75.506 | 0 | no_tensor_candidates (1596) |
| DynamicQuant | 3740 | 66.998 | 0 | no_tensor_candidates (3740) |
| MatMulV3 | 102 | 57.571 | 0 | no_tensor_candidates (102) |
| allgatherAicpuKernel | 119 | 34.120 | 0 | no_tensor_candidates (119) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| - | - | 0 | No valid subgraph cohort | - | - | - | - | - | - |

## a3_qwen36_paged_decode_q4 / paged_body_geometry_conditional

Graph: `sha256:b70ac3aa1db108c1d9d486840f8ef8521cafd11fa6483d6c7dcffa3769814409`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 1 | 1 | 15 | 255 |
| absolute_15us | 12 | 12 | 0 | 8730 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FusedInferAttentionScore | relative_15pct | 323 | 255 | 0 | 14.839 | 1.789 | 58.192 | 7.014 | -51.178 | -87.9% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | absolute_15us | 3740 | 3300 | 0 | 98.231 | 75.181 | 29.767 | 22.782 | -6.985 | -23.5% | 5 / 0 |
| RecurrentGatedDeltaRule | absolute_15us | 720 | 720 | 0 | 18.515 | 8.645 | 25.715 | 12.006 | -13.709 | -53.3% | 1 / 0 |
| DynamicQuant | absolute_15us | 3740 | 3300 | 0 | 13.551 | 8.250 | 4.106 | 2.500 | -1.606 | -39.1% | 3 / 0 |
| SwiGlu | absolute_15us | 1139 | 1005 | 0 | 4.301 | 2.513 | 4.280 | 2.500 | -1.780 | -41.6% | 1 / 0 |
| GemmaRmsNorm | absolute_15us | 170 | 150 | 0 | 0.717 | 0.375 | 4.781 | 2.500 | -2.281 | -47.7% | 1 / 0 |
| ScatterPaKvCache | absolute_15us | 323 | 255 | 0 | 0.671 | 0.638 | 2.630 | 2.500 | -0.130 | -5.0% | 1 / 0 |
| MatMulV2 | relative_15pct | 1649 | 15 | 0 | 8.734 | 7.953 | 582.238 | 530.207 | -52.031 | -8.9% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| allreduceAicpuKernel | 2346 | 1284.175 | 0 | no_tensor_candidates (2346) |
| QuantBatchMatmulV3 | 3740 | 535.605 | 0 | no_tensor_candidates (440) |
| hcom_allReduce_ | 2346 | 233.875 | 0 | no_tensor_candidates (2346) |
| ChunkGatedDeltaRuleFwd | 96 | 164.082 | 0 | no_tensor_candidates (96) |
| AddRmsNormBias | 2278 | 107.967 | 0 | no_tensor_candidates (2278) |
| FusedInferAttentionScore | 323 | 100.845 | 0 | no_tensor_candidates (68) |
| MatMulV2 | 1649 | 75.506 | 0 | no_tensor_candidates (1634) |
| DynamicQuant | 3740 | 66.998 | 0 | no_tensor_candidates (440) |
| MatMulV3 | 102 | 57.571 | 0 | no_tensor_candidates (102) |
| allgatherAicpuKernel | 119 | 34.120 | 0 | no_tensor_candidates (119) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| - | - | 0 | No valid subgraph cohort | - | - | - | - | - | - |

## a3_v4f / case_default

Graph: `sha256:167eeb53f3ff5135c399d1d1b49eb0b21587ab0c85ab7a366f3fe2b19b47d8b6`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 15 | 1 | 14 | 44 | 507 |
| absolute_15us | 1 | 0 | 1 | 0 | 65 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 44 | 44 | 0 | 98.897 | 30.910 | 2247.659 | 702.502 | -1545.157 | -68.7% | 0 / 3 |
| HcPost | relative_15pct | 88 | 88 | 0 | 36.817 | 22.170 | 418.375 | 251.931 | -166.444 | -39.8% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 241 | 109 | 0 | 15.331 | 14.036 | 140.651 | 128.772 | -11.878 | -8.4% | 0 / 3 |
| MatMulV2 | relative_15pct | 110 | 88 | 0 | 11.809 | 9.528 | 134.198 | 108.274 | -25.924 | -19.3% | 0 / 4 |
| DynamicQuant | relative_15pct | 239 | 132 | 0 | 8.164 | 5.077 | 61.851 | 38.460 | -23.391 | -37.8% | 0 / 2 |
| RmsNorm | relative_15pct | 182 | 46 | 0 | 4.105 | 2.573 | 89.236 | 55.931 | -33.305 | -37.3% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 239 | 65 | 0 | 2.056 | 0.682 | 31.631 | 10.499 | -21.132 | -66.8% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 241 | 44 | 0 | 6.876 | 6.390 | 156.268 | 145.237 | -11.031 | -7.1% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_ | 264 | 64.783 | 0 | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | no_tensor_candidates (90) |
| HcPre | 88 | 37.975 | 88 | unfused_subgraph_is_not_the_observed_native_kernel (88) |
| QuantBatchMatmulV3 | 241 | 28.176 | 0 | candidate_physical_work_differs (44), no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 0 | no_tensor_candidates (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 0 | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 44 | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 0 | no_tensor_candidates (42) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPost | 7fd5b2872c5c | 88 | compared | 418.375 | 251.931 | -166.444 | -39.8% | relative_15pct | false |
| HcPre | 1d5888fcba73 | 88 | reference_only | 431.534 | 929.570 | 498.036 | - | reference_only | - |
| GroupedMatmulSwigluQuant | c053836b873b | 44 | reference_only | 588.788 | 5681.584 | 5092.796 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | 15ae241c83ef | 21 | reference_only | 399.030 | 248.045 | -150.985 | - | reference_only | - |

## a3_v4f / selected_native_fusion

Graph: `sha256:07f8d631b3a4854810e4e16f39160016df67d63e84bff8118c6681bc3f359881`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 16 | 1 | 15 | 44 | 595 |
| absolute_15us | 1 | 0 | 1 | 0 | 65 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 44 | 44 | 0 | 98.897 | 30.910 | 2247.659 | 702.502 | -1545.157 | -68.7% | 0 / 3 |
| HcPre | relative_15pct | 88 | 88 | 0 | 37.975 | 63.496 | 431.534 | 721.545 | 290.011 | +67.2% | 0 / 1 |
| HcPost | relative_15pct | 88 | 88 | 0 | 36.817 | 26.166 | 418.375 | 297.336 | -121.038 | -28.9% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 241 | 109 | 0 | 15.331 | 14.036 | 140.651 | 128.772 | -11.878 | -8.4% | 0 / 3 |
| MatMulV2 | relative_15pct | 110 | 88 | 0 | 11.809 | 9.528 | 134.198 | 108.274 | -25.924 | -19.3% | 0 / 4 |
| DynamicQuant | relative_15pct | 239 | 132 | 0 | 8.164 | 5.077 | 61.851 | 38.460 | -23.391 | -37.8% | 0 / 2 |
| RmsNorm | relative_15pct | 182 | 46 | 0 | 4.105 | 2.573 | 89.236 | 55.931 | -33.305 | -37.3% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 239 | 65 | 0 | 2.056 | 0.682 | 31.631 | 10.499 | -21.132 | -66.8% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 241 | 44 | 0 | 6.876 | 6.390 | 156.268 | 145.237 | -11.031 | -7.1% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_ | 264 | 64.783 | 0 | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | no_tensor_candidates (90) |
| QuantBatchMatmulV3 | 241 | 28.176 | 0 | candidate_physical_work_differs (44), no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 0 | no_tensor_candidates (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 0 | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 44 | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 0 | no_tensor_candidates (42) |
| MatMulV2 | 110 | 12.384 | 0 | no_tensor_candidates (22) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPre | a497063ee99f | 88 | compared | 431.534 | 721.545 | 290.011 | +67.2% | relative_15pct | false |
| HcPost | b340de554166 | 88 | compared | 418.375 | 297.336 | -121.038 | -28.9% | relative_15pct | false |
| GroupedMatmulSwigluQuant | 2dd11eb37d7e | 44 | reference_only | 588.788 | 5681.584 | 5092.796 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | ef6242cb228d | 21 | reference_only | 399.030 | 248.045 | -150.985 | - | reference_only | - |

## a3_v4f_compressor_fp32 / source_compressor_fp32_conditional_reference

Graph: `sha256:9b0a09f327e42013d931d2e516160b92ac313f58a895091e15a521caf320fa09`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 16 | 1 | 15 | 44 | 595 |
| absolute_15us | 1 | 0 | 1 | 0 | 65 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 44 | 44 | 0 | 98.897 | 30.910 | 2247.659 | 702.502 | -1545.157 | -68.7% | 0 / 3 |
| HcPre | relative_15pct | 88 | 88 | 0 | 37.975 | 63.496 | 431.534 | 721.545 | 290.011 | +67.2% | 0 / 1 |
| HcPost | relative_15pct | 88 | 88 | 0 | 36.817 | 26.166 | 418.375 | 297.336 | -121.038 | -28.9% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 241 | 109 | 0 | 15.331 | 14.036 | 140.651 | 128.772 | -11.878 | -8.4% | 0 / 3 |
| MatMulV2 | relative_15pct | 110 | 88 | 0 | 11.809 | 9.528 | 134.198 | 108.274 | -25.924 | -19.3% | 0 / 4 |
| DynamicQuant | relative_15pct | 239 | 132 | 0 | 8.164 | 5.077 | 61.851 | 38.460 | -23.391 | -37.8% | 0 / 2 |
| RmsNorm | relative_15pct | 182 | 46 | 0 | 4.105 | 2.573 | 89.236 | 55.931 | -33.305 | -37.3% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 239 | 65 | 0 | 2.056 | 0.682 | 31.631 | 10.499 | -21.132 | -66.8% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 241 | 44 | 0 | 6.876 | 6.390 | 156.268 | 145.237 | -11.031 | -7.1% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_ | 264 | 64.783 | 0 | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | no_tensor_candidates (90) |
| QuantBatchMatmulV3 | 241 | 28.176 | 0 | candidate_physical_work_differs (44), no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 62 | unfused_subgraph_is_not_the_observed_native_kernel (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 0 | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 44 | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 0 | no_tensor_candidates (42) |
| MatMulV2 | 110 | 12.384 | 0 | no_tensor_candidates (22) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPre | ca7251d5b671 | 88 | compared | 431.534 | 721.545 | 290.011 | +67.2% | relative_15pct | false |
| HcPost | 71115b8e2df4 | 88 | compared | 418.375 | 297.336 | -121.038 | -28.9% | relative_15pct | false |
| Compressor | cd5607523164 | 21 | reference_only | 758.193 | 497.229 | -260.965 | - | reference_only | - |
| Compressor | 1eae9c56b650 | 21 | reference_only | 239.132 | 155.065 | -84.068 | - | reference_only | - |
| Compressor | ae5cf546211c | 20 | reference_only | 320.864 | 269.222 | -51.642 | - | reference_only | - |
| GroupedMatmulSwigluQuant | e56632764c36 | 44 | reference_only | 588.788 | 5681.584 | 5092.796 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | adfc89af6880 | 21 | reference_only | 399.030 | 248.045 | -150.985 | - | reference_only | - |

## a3_v4f_shared_quant / source_shared_int32_conditional

Graph: `sha256:9220bc7ec22b162a3d1a9d1776c3d939b9566f46f2347796ea1686a25eb4cfa4`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 17 | 3 | 14 | 132 | 507 |
| absolute_15us | 2 | 0 | 2 | 0 | 109 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 44 | 44 | 0 | 98.897 | 30.910 | 2247.659 | 702.502 | -1545.157 | -68.7% | 0 / 3 |
| HcPost | relative_15pct | 88 | 88 | 0 | 36.817 | 22.170 | 418.375 | 251.931 | -166.444 | -39.8% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 241 | 109 | 0 | 15.331 | 14.036 | 140.651 | 128.772 | -11.878 | -8.4% | 0 / 3 |
| MatMulV2 | relative_15pct | 110 | 88 | 0 | 11.809 | 9.528 | 134.198 | 108.274 | -25.924 | -19.3% | 0 / 4 |
| DynamicQuant | relative_15pct | 239 | 132 | 0 | 8.164 | 5.077 | 61.851 | 38.460 | -23.391 | -37.8% | 0 / 2 |
| RmsNorm | relative_15pct | 182 | 46 | 0 | 4.105 | 2.573 | 89.236 | 55.931 | -33.305 | -37.3% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DequantSwigluQuant | absolute_15us | 44 | 44 | 0 | 1.450 | 0.446 | 32.948 | 10.131 | -22.817 | -69.3% | 0 / 1 |
| DynamicQuant | absolute_15us | 239 | 65 | 0 | 2.056 | 0.682 | 31.631 | 10.499 | -21.132 | -66.8% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 241 | 132 | 0 | 12.845 | 12.248 | 97.312 | 92.790 | -4.522 | -4.6% | 3 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_ | 264 | 64.783 | 0 | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | no_tensor_candidates (90) |
| HcPre | 88 | 37.975 | 88 | unfused_subgraph_is_not_the_observed_native_kernel (88) |
| Compressor | 62 | 27.361 | 0 | no_tensor_candidates (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 0 | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 44 | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 0 | no_tensor_candidates (42) |
| MatMulV2 | 110 | 12.384 | 0 | no_tensor_candidates (22) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPost | c26c46432f80 | 88 | compared | 418.375 | 251.931 | -166.444 | -39.8% | relative_15pct | false |
| HcPre | a73a0001c639 | 88 | reference_only | 431.534 | 929.570 | 498.036 | - | reference_only | - |
| GroupedMatmulSwigluQuant | e0b68d8ba92c | 44 | reference_only | 588.788 | 5681.584 | 5092.796 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | 44448c57c65d | 21 | reference_only | 399.030 | 248.045 | -150.985 | - | reference_only | - |

## a3_v4pro / case_default

Graph: `sha256:cc0d61b9b2126c6983f3f06f729ff858ad35310e4bdd40cabf4e77d54b9d2c9c`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 10 | 3 | 7 | 616 | 1492 |
| absolute_15us | 6 | 4 | 2 | 856 | 752 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 248 | 244 | 0 | 173.863 | 17.076 | 712.554 | 69.985 | -642.569 | -90.2% | 0 / 2 |
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
| SparseAttnSharedkv | 248 | 174.437 | 0 | no_tensor_candidates (4) |
| GroupedMatmulSwigluQuantV2 | 248 | 98.114 | 248 | quantized_epilogue_unmodeled (248) |
| HcPre | 496 | 95.134 | 496 | unfused_subgraph_is_not_the_observed_native_kernel (496) |
| QuantBatchMatmulV3 | 1360 | 90.278 | 0 | no_tensor_candidates (248) |
| Compressor | 364 | 77.516 | 0 | no_tensor_candidates (364) |
| allgatherAicpuKernel | 248 | 75.079 | 0 | no_tensor_candidates (248) |
| GroupedMatmul | 248 | 60.731 | 0 | no_tensor_candidates (248) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPost | 3a6127304c54 | 496 | compared | 202.098 | 110.169 | -91.930 | -45.5% | relative_15pct | false |
| GroupedMatmulSwigluQuantV2 | 2ce51e2fc1b2 | 248 | reference_only | 395.623 | 805.300 | 409.678 | - | reference_only | - |
| HcPre | b3e79bd75156 | 496 | reference_only | 191.803 | 456.342 | 264.539 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | 81ba47198748 | 120 | reference_only | 113.425 | 18.539 | -94.886 | - | reference_only | - |

## a3_v4pro / selected_native_fusion

Graph: `sha256:7a639007bccd5b9fcea4954af3d589c4dc4843f76c2faddd7883945bbbb949f5`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 11 | 3 | 8 | 616 | 1988 |
| absolute_15us | 6 | 4 | 2 | 856 | 752 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 248 | 244 | 0 | 173.863 | 17.076 | 712.554 | 69.985 | -642.569 | -90.2% | 0 / 2 |
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
| SparseAttnSharedkv | 248 | 174.437 | 0 | no_tensor_candidates (4) |
| GroupedMatmulSwigluQuantV2 | 248 | 98.114 | 248 | quantized_epilogue_unmodeled (248) |
| QuantBatchMatmulV3 | 1360 | 90.278 | 0 | no_tensor_candidates (248) |
| Compressor | 364 | 77.516 | 0 | no_tensor_candidates (364) |
| allgatherAicpuKernel | 248 | 75.079 | 0 | no_tensor_candidates (248) |
| GroupedMatmul | 248 | 60.731 | 0 | no_tensor_candidates (248) |
| RmsNorm | 1016 | 43.695 | 0 | no_tensor_candidates (760) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPost | c5c9f99bc0a9 | 496 | compared | 202.098 | 129.751 | -72.348 | -35.8% | relative_15pct | false |
| HcPre | 91a77df2c043 | 496 | compared | 191.803 | 316.457 | 124.653 | +65.0% | relative_15pct | false |
| GroupedMatmulSwigluQuantV2 | 792afb84e19d | 248 | reference_only | 395.623 | 805.300 | 409.678 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | c66c89287651 | 120 | reference_only | 113.425 | 18.539 | -94.886 | - | reference_only | - |

## a3_v4pro_compressor_fp32 / source_compressor_fp32_conditional_reference

Graph: `sha256:311fcead3ad15366ff2114dae253e696e05535629767c5320a5b9107a9ca1d2d`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 11 | 3 | 8 | 616 | 1988 |
| absolute_15us | 6 | 4 | 2 | 856 | 752 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 248 | 244 | 0 | 173.863 | 17.076 | 712.554 | 69.985 | -642.569 | -90.2% | 0 / 2 |
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
| SparseAttnSharedkv | 248 | 174.437 | 0 | no_tensor_candidates (4) |
| GroupedMatmulSwigluQuantV2 | 248 | 98.114 | 248 | quantized_epilogue_unmodeled (248) |
| QuantBatchMatmulV3 | 1360 | 90.278 | 0 | no_tensor_candidates (248) |
| Compressor | 364 | 77.516 | 364 | unfused_subgraph_is_not_the_observed_native_kernel (364) |
| allgatherAicpuKernel | 248 | 75.079 | 0 | no_tensor_candidates (248) |
| GroupedMatmul | 248 | 60.731 | 0 | no_tensor_candidates (248) |
| RmsNorm | 1016 | 43.695 | 0 | no_tensor_candidates (760) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPost | 76a3d7df96f3 | 496 | compared | 202.098 | 129.751 | -72.348 | -35.8% | relative_15pct | false |
| HcPre | c45d0c017108 | 496 | compared | 191.803 | 316.457 | 124.653 | +65.0% | relative_15pct | false |
| GroupedMatmulSwigluQuantV2 | b630cbe6bda3 | 248 | reference_only | 395.623 | 805.300 | 409.678 | - | reference_only | - |
| Compressor | 776bfc94db4f | 124 | reference_only | 148.297 | 133.388 | -14.909 | - | reference_only | - |
| Compressor | 32afa02671c1 | 120 | reference_only | 300.533 | 259.974 | -40.559 | - | reference_only | - |
| Compressor | c1cde179774f | 120 | reference_only | 192.197 | 70.161 | -122.036 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | e91be672d424 | 120 | reference_only | 113.425 | 18.539 | -94.886 | - | reference_only | - |

## a5_kimi_k3 / case_default

Graph: `sha256:b3c2f8fd8e41d24fc1a8cd7e6733654b2697416069104c5a66698d0cea701b51`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 0 | 2 | 0 | 343 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| layer_norm_gated_fwd_kernel | relative_15pct | 5451 | 276 | 0 | 37.608 | 5.209 | 136.262 | 18.874 | -117.388 | -86.1% | 0 / 1 |
| MatMulV3 | relative_15pct | 21819 | 67 | 0 | 6.178 | 4.957 | 92.208 | 73.978 | -18.230 | -19.8% | 0 / 1 |

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
| MatMulV3 | 21819 | 656.394 | 0 | no_tensor_candidates (21656), candidate_physical_work_differs (96) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 0 | no_tensor_candidates (7266) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 0 | no_tensor_candidates (14531) |
| hcom_allGather_ | 15203 | 409.082 | 0 | no_tensor_candidates (15203) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| - | - | 0 | No valid subgraph cohort | - | - | - | - | - | - |

## a5_kimi_k3_decode / source_declared_unfused_reference

Graph: `sha256:8dcaa2c8e82317c962376b4b53f25a6e52bb286f94d5f78271dbd9b9ef1269f0`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 1 | 0 | 1 | 0 | 67 |
| absolute_15us | 3 | 3 | 0 | 8838 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV3 | relative_15pct | 21819 | 67 | 0 | 6.178 | 4.957 | 92.208 | 73.978 | -18.230 | -19.8% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV3 | absolute_15us | 21819 | 6973 | 0 | 87.407 | 44.244 | 12.535 | 6.345 | -6.190 | -49.4% | 1 / 0 |
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
| MatMulV3 | 21819 | 656.394 | 0 | no_tensor_candidates (12981), candidate_physical_work_differs (1798) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 0 | no_tensor_candidates (7266) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 0 | no_tensor_candidates (14531) |
| hcom_allGather_ | 15203 | 409.082 | 0 | no_tensor_candidates (15203) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| - | - | 0 | No valid subgraph cohort | - | - | - | - | - | - |

## a5_kimi_k3_checkpoint / current_checkpoint_conditional

Graph: `sha256:586aa1126db6aadda8dc709fbe59de4324287b912fb84e481a8bf5749b7016c2`.

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
| SituMxQuant | e28ac1a25b26 | 368 | compared | 147.124 | 14.953 | -132.172 | -89.8% | relative_15pct | false |
| GroupedMatmulSituQuant | 1bb2bab42f39 | 7266 | reference_only | 91.780 | 11336.311 | 11244.530 | - | reference_only | - |

## a5_kimi_k3_decode_checkpoint / current_checkpoint_conditional

Graph: `sha256:cdb020e16572c812a73329db7ab53cb7cac36953146500b9caa5b4aa0456fa1c`.

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
| SituMxQuant | 500c945e14d4 | 6898 | compared | 65.134 | 0.002 | -65.132 | -100.0% | relative_15pct | false |
| GroupedMatmulSituQuant | df42e867aca7 | 7266 | reference_only | 91.780 | 7.735 | -84.045 | - | reference_only | - |
| MlaPrologV3 | 04e553830c14 | 1798 | reference_only | 22.248 | 17.439 | -4.809 | - | reference_only | - |

## a5_kimi_k3_checkpoint_eager_single_group / source_single_group_mxfp8_conditional

Graph: `sha256:00a5891938fc06d5e95ee78ba7c02ccdf6019334a12fdef1663710770ed2d5ce`.

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
| SituMxQuant | c76aae3cb95b | 368 | compared | 147.124 | 14.953 | -132.172 | -89.8% | relative_15pct | false |
| GroupedMatmulSituQuant | a047a342334c | 7266 | reference_only | 91.780 | 11336.311 | 11244.530 | - | reference_only | - |

## a5_kimi_k3_decode_checkpoint_eager_single_group / source_single_group_mxfp8_conditional

Graph: `sha256:df4c839f68bc310ab89a8b43582e166badd2412162ce41938dd563bde4827acd`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 0 | 2 | 0 | 6965 |
| absolute_15us | 8 | 8 | 0 | 50299 | 0 |

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
| GroupedMatmul | absolute_15us | 27248 | 13795 | 0 | 189.476 | 105.281 | 13.735 | 7.632 | -6.103 | -44.4% | 2 / 0 |
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
| GroupedMatmul | 27248 | 813.481 | 0 | no_tensor_candidates (13453) |
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
| SituMxQuant | 510aa9df8084 | 6898 | compared | 65.134 | 0.002 | -65.132 | -100.0% | relative_15pct | false |
| GroupedMatmulSituQuant | 3788bb1d3d1e | 7266 | reference_only | 91.780 | 7.735 | -84.045 | - | reference_only | - |
| MlaPrologV3 | bf69d508dfbf | 1798 | reference_only | 22.248 | 17.439 | -4.809 | - | reference_only | - |

## a5_qwen38 / case_default

Graph: `sha256:12b62da5b83c5c8de72b0ca887692c3ca5c741c7c566b7753637dc42a141f663`.

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

## a5_qwen38_steady / selected_steady_matrix_conditional

Graph: `sha256:5d350819b7df59cc9ccd03eaf2cefbf0aaec2bde03b7453143c3438b61f8b057`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 22 | 11 | 11 | 488 | 501 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
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
| QuantBatchMatmulV3 | relative_15pct | 1920 | 160 | 0 | 714.307 | 749.188 | 4464.419 | 4682.426 | 218.007 | +4.9% | 4 / 0 |
| MatMulV3 | relative_15pct | 1956 | 184 | 0 | 458.381 | 471.914 | 2491.204 | 2564.751 | 73.547 | +3.0% | 4 / 0 |
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

## a5_qwen38_paged_prefill_q16384 / paged_body_geometry_conditional

Graph: `sha256:8a23588c5063b383a1a8a96473fbebe6cde9726de788478d97168c4a0df336eb`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 21 | 4 | 17 | 181 | 791 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 1920 | 160 | 0 | 714.307 | 1253.383 | 4464.419 | 7833.641 | 3369.222 | +75.5% | 0 / 4 |
| MatMulV3 | relative_15pct | 1956 | 147 | 0 | 431.194 | 725.922 | 2933.291 | 4938.243 | 2004.952 | +68.4% | 0 / 3 |
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
| FusedInferAttentionScore | 228 | 243.894 | 0 | no_tensor_candidates (228) |
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

## a5_qwen38_paged_decode_q1 / paged_body_geometry_conditional

Graph: `sha256:eff424b7e1ccaeb4424a6d19120120d12cccd8a65eab4429278b47bcc4b90e69`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 1 | 1 | 37 | 24 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FusedInferAttentionScore | relative_15pct | 228 | 24 | 0 | 3.240 | 0.403 | 135.013 | 16.784 | -118.229 | -87.6% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV3 | relative_15pct | 1956 | 37 | 0 | 27.188 | 23.851 | 734.804 | 644.633 | -90.171 | -12.3% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| QuantBatchMatmulV3 | 1920 | 781.406 | 0 | no_tensor_candidates (1920) |
| MatMulV3 | 1956 | 611.956 | 0 | no_tensor_candidates (1919) |
| FusedInferAttentionScore | 228 | 243.894 | 0 | no_tensor_candidates (204) |
| ChunkGatedDeltaRuleFwdPrepare | 48 | 73.924 | 0 | no_tensor_candidates (48) |
| fused_gdn_gating_kernel | 576 | 44.045 | 0 | no_tensor_candidates (576) |
| Slice | 4273 | 39.010 | 0 | no_tensor_candidates (4273) |
| ChunkFwdH | 48 | 38.757 | 0 | no_tensor_candidates (48) |
| SwiGlu | 804 | 37.136 | 0 | no_tensor_candidates (804) |
| ChunkFwdO | 48 | 24.817 | 0 | no_tensor_candidates (48) |
| DynamicMxQuant | 960 | 21.934 | 0 | no_tensor_candidates (960) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| - | - | 0 | No valid subgraph cohort | - | - | - | - | - | - |

## a5_qwen38_paged_decode_q4 / paged_body_geometry_conditional

Graph: `sha256:8e04acd4a156cbdad65759f2a066acb5ae7a495c0edad2bdb5a47a6b1ca04dff`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 4 | 2 | 2 | 715 | 715 |
| absolute_15us | 12 | 12 | 0 | 5885 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV3 | relative_15pct | 1956 | 528 | 0 | 27.073 | 22.848 | 51.276 | 43.272 | -8.004 | -15.6% | 0 / 1 |
| FusedInferAttentionScore | relative_15pct | 228 | 187 | 0 | 26.912 | 3.143 | 143.916 | 16.806 | -127.110 | -88.3% | 0 / 1 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | absolute_15us | 1920 | 1056 | 0 | 29.541 | 32.988 | 27.974 | 31.238 | 3.264 | +11.7% | 3 / 0 |
| MatMulV3 | absolute_15us | 1956 | 1089 | 0 | 20.480 | 18.902 | 18.806 | 17.357 | -1.449 | -7.7% | 2 / 0 |
| RecurrentGatedDeltaRule | absolute_15us | 528 | 528 | 0 | 5.628 | 5.097 | 10.658 | 9.653 | -1.005 | -9.4% | 1 / 0 |
| DynamicMxQuant | absolute_15us | 960 | 880 | 0 | 3.678 | 0.040 | 4.180 | 0.046 | -4.134 | -98.9% | 2 / 0 |
| AddRmsNormDynamicMxQuant | absolute_15us | 960 | 880 | 0 | 3.508 | 0.034 | 3.986 | 0.039 | -3.948 | -99.0% | 1 / 0 |
| SwiGlu | absolute_15us | 804 | 737 | 0 | 2.768 | 0.077 | 3.755 | 0.104 | -3.651 | -97.2% | 1 / 0 |
| Slice | absolute_15us | 4273 | 528 | 0 | 2.240 | 0.022 | 4.243 | 0.041 | -4.202 | -99.0% | 1 / 0 |
| ScatterPaKvCache | absolute_15us | 228 | 187 | 0 | 0.659 | 0.002 | 3.525 | 0.008 | -3.517 | -99.8% | 1 / 0 |
| QuantBatchMatmulV3 | relative_15pct | 1920 | 704 | 0 | 37.559 | 35.356 | 53.350 | 50.222 | -3.128 | -5.9% | 1 / 0 |
| MatMulV3 | relative_15pct | 1956 | 11 | 0 | 8.125 | 7.256 | 738.650 | 659.638 | -79.012 | -10.7% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| QuantBatchMatmulV3 | 1920 | 781.406 | 0 | no_tensor_candidates (160) |
| MatMulV3 | 1956 | 611.956 | 0 | no_tensor_candidates (328) |
| FusedInferAttentionScore | 228 | 243.894 | 0 | no_tensor_candidates (41) |
| ChunkGatedDeltaRuleFwdPrepare | 48 | 73.924 | 0 | no_tensor_candidates (48) |
| fused_gdn_gating_kernel | 576 | 44.045 | 0 | no_tensor_candidates (576) |
| Slice | 4273 | 39.010 | 0 | no_tensor_candidates (2689), candidate_physical_work_differs (1056) |
| ChunkFwdH | 48 | 38.757 | 0 | no_tensor_candidates (48) |
| SwiGlu | 804 | 37.136 | 0 | no_tensor_candidates (67) |
| ChunkFwdO | 48 | 24.817 | 0 | no_tensor_candidates (48) |
| DynamicMxQuant | 960 | 21.934 | 0 | no_tensor_candidates (80) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| - | - | 0 | No valid subgraph cohort | - | - | - | - | - | - |
