# Complete-Capture Operator Families And Tiered Conditional Errors

Historical captures; report refresh can reuse saved comparisons without raw scans or new predictions.

Policy: observed complete-event mean > 50 us uses absolute relative error <= 15%; mean <= 50 us uses absolute per-call difference <= 15 us, including exactly 50 us. Per-call diff is predicted minus observed. No launch floor is added to predictions. This is an acceptance allowance, not evidence that a residual was caused by launch overhead.

Acceptance is decided per cohort before aggregation. Family/tier means are call-count weighted; pass/fail counts preserve failed cohorts even if signed averages cancel. The scored columns cover the indicated tier and pass/fail subset only: failed cohorts appear in error tables and passed cohorts appear within tolerance, including when a family has both. All/reference event counts describe the whole native family and repeat across these subsets. Every native type and full-family aggregate remains in JSON.

Large failed cohorts lead Top Errors, sorted by their observed activity; small failures are separate and sorted by absolute per-call difference. Within-tolerance groups and unscored coverage have separate tables. Reference, clipped, prediction-failed and unmatched events are not scored; accuracy-failed cohorts remain in the scored denominator.

Activity sums count overlapping events separately and are not wall-clock latency. Variant totals reuse captures and must not be counted as independent evidence.

| Tier | Compared cohorts across variants | Passed | Failed |
| --- | ---: | ---: | ---: |
| relative_15pct | 418 | 121 | 297 |
| absolute_15us | 198 | 168 | 30 |
| All scored | 616 | 289 | 327 |

**Partial prediction coverage: 1 cohort predictions failed and remain outside accuracy denominators.** The full replay receipt retains their failure and retry records.

## Decode Body Forward

Body timing is the per-invocation device wall-clock span, including body communication and internal dependencies. Between-step gaps are excluded. Embedding, final norm/LM head and MTP remain separate boundaries. Kernel activity sums and unidentified graph envelopes are not body latency.

Independent evidence: [Decode multi-case replay](decode-forward-replay.md), JSON SHA256 `9b85505a1253d0ffb65eb3115f3dfc5a8c2bd5c85785420f7fbf6ba6820d6941`. Scenarios and unresolved reasons are retained there.

| Case | Body forwards | Real mean ms | Real P50 ms | Real P90 ms | Sim ms | Relative error | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| a5_qwen36_highconc_c40:q4_b40_m160 | 54 | 20.6839 | 20.6115 | 21.3338 | 9.6201 | -53.5% | compared |
| a5_qwen36_highconc_c128:q4_b128_m512 | 38 | 32.6090 | 32.2274 | 33.8514 | 19.9875 | -38.7% | compared |
| a5_qwen36_highconc_c4:q4_b4_m16 | 73 | 13.3425 | 13.2446 | 13.4847 | 5.0913 | -61.8% | compared |
| a5_qwen38_highconc_c32:q4_b32_m128 | 48 | 22.7913 | 22.7110 | 22.8940 | 8.9550 | -60.7% | compared |
| a5_qwen38_highconc_c128:q4_b128_m512 | 29 | 45.6893 | 45.6903 | 45.7352 | 28.2484 | -38.2% | compared |
| a5_qwen38_highconc_c4:q4_b4_m16 | 45 | 13.0267 | 13.0053 | 13.1669 | 4.3859 | -66.3% | compared |

Body accuracy: **0 / 6** comparable cases; 0 unresolved, 0 failed. Unresolved cases do not count as passes or zero-duration forwards.

## a3_glm53_decode / source_declared_unfused_reference

Graph: `sha256:1172f58016806920eb73d5c105cdeb2344dd3648413a930de99b8e9a387a00b3`.

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
| QuantBatchMatmulV3 | absolute_15us | 18870 | 13320 | 0 | 237.111 | 104.820 | 17.801 | 7.869 | -9.932 | -55.8% | 5 / 0 |
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
| GroupedMatmulSwigluQuantV2 | 7427232611f7 | 5550 | reference_only | 88.039 | 15.560 | -72.479 | - | reference_only | - |
| MlaPrologV3 | 84447ed1168a | 1554 | reference_only | 41.291 | 38.014 | -3.277 | - | reference_only | - |
| MlaPrologV3 | 6da0e3029321 | 4218 | reference_only | 40.913 | 38.014 | -2.899 | - | reference_only | - |
| LightningIndexer | 72e3619a6000 | 1554 | reference_only | 24.905 | 7.500 | -17.405 | - | reference_only | - |
| MoeGatingTopK | 8e49a558ca6d | 5550 | reference_only | 4.013 | 7.500 | 3.487 | - | reference_only | - |

## a3_glm53_decode / selected_native_fusion

Graph: `sha256:26b1edc971fe97e6aa60683d5a1796cb0a62972dafd0299fe5b0b1d80af1d273`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 4 | 1 | 3 | 74 | 16872 |
| absolute_15us | 17 | 14 | 3 | 49802 | 7326 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseFlashAttention | relative_15pct | 5772 | 5772 | 0 | 523.698 | 11.471 | 90.731 | 1.987 | -88.743 | -97.8% | 0 / 1 |
| GroupedMatmulSwigluQuantV2 | relative_15pct | 5550 | 5550 | 0 | 488.615 | 63.668 | 88.039 | 11.472 | -76.567 | -87.0% | 0 / 1 |
| GroupedMatmul | relative_15pct | 5550 | 5550 | 0 | 293.637 | 35.522 | 52.907 | 6.400 | -46.507 | -87.9% | 0 / 1 |

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
| GroupedMatmulSwigluQuantV2 | ae35f7f9e114 | 5550 | compared | 88.039 | 11.472 | -76.567 | -87.0% | relative_15pct | false |
| LightningIndexer | 7c7d22e6f5be | 1554 | compared | 24.905 | 0.909 | -23.996 | -96.4% | absolute_15us | false |
| MlaPrologV3 | 1e54caca5dd1 | 1554 | compared | 41.291 | 18.327 | -22.963 | -55.6% | absolute_15us | false |
| MlaPrologV3 | 9cab9d6197b7 | 4218 | compared | 40.913 | 18.327 | -22.585 | -55.2% | absolute_15us | false |
| MoeGatingTopK | ab539efc67c4 | 5550 | reference_only | 4.013 | 0.003 | -4.010 | - | reference_only | - |

## a3_glm53_decode_shared_quant / source_shared_int32_conditional

Graph: `sha256:079c8f939e5030ef1a06a950858e2a97787e46c0398197b273468032a7af658a`.

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
| QuantBatchMatmulV3 | absolute_15us | 18870 | 18870 | 0 | 310.039 | 132.570 | 16.430 | 7.025 | -9.405 | -57.2% | 6 / 0 |
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
| GroupedMatmulSwigluQuantV2 | 21f68b4bd356 | 5550 | reference_only | 88.039 | 15.560 | -72.479 | - | reference_only | - |
| MlaPrologV3 | 6e2868d26d0a | 1554 | reference_only | 41.291 | 38.014 | -3.277 | - | reference_only | - |
| MlaPrologV3 | c5f7ff218e66 | 4218 | reference_only | 40.913 | 38.014 | -2.899 | - | reference_only | - |
| LightningIndexer | 0021d7c40165 | 1554 | reference_only | 24.905 | 7.500 | -17.405 | - | reference_only | - |
| MoeGatingTopK | 2cbee4cfaa7c | 5550 | reference_only | 4.013 | 7.500 | 3.487 | - | reference_only | - |

## a3_glm53_decode_shared_quant_indexed_arch22 / source_shared_quant_indexed_arch22_conditional

Graph: `sha256:e9a5c5024573bd9566f559b6424c6839b3a5741ca8bda92bf77d903901c1abca`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 2 | 0 | 5846 | 0 |
| absolute_15us | 16 | 16 | 0 | 60902 | 0 |

### Large-call errors: observed mean > 50 us

None.

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | absolute_15us | 18870 | 18870 | 0 | 310.039 | 132.570 | 16.430 | 7.025 | -9.405 | -57.2% | 6 / 0 |
| TransposeBatchMatMul | absolute_15us | 5772 | 5772 | 0 | 81.808 | 28.860 | 14.173 | 5.000 | -9.173 | -64.7% | 1 / 0 |
| DynamicQuant | absolute_15us | 17316 | 17316 | 0 | 50.444 | 43.290 | 2.913 | 2.500 | -0.413 | -14.2% | 3 / 0 |
| AddRmsNormBias | absolute_15us | 11322 | 11322 | 0 | 44.742 | 28.305 | 3.952 | 2.500 | -1.452 | -36.7% | 1 / 0 |
| DequantSwigluQuant | absolute_15us | 5550 | 5550 | 0 | 18.782 | 13.875 | 3.384 | 2.500 | -0.884 | -26.1% | 1 / 0 |
| LayerNormV3 | absolute_15us | 1554 | 1554 | 0 | 8.257 | 3.885 | 5.313 | 2.500 | -2.813 | -52.9% | 1 / 0 |
| AddRmsNormDynamicQuant | absolute_15us | 222 | 222 | 0 | 1.055 | 0.555 | 4.751 | 2.500 | -2.251 | -47.4% | 1 / 0 |
| SwiGlu | absolute_15us | 222 | 222 | 0 | 0.810 | 0.555 | 3.650 | 2.500 | -1.150 | -31.5% | 1 / 0 |
| RmsNorm | absolute_15us | 74 | 74 | 0 | 0.356 | 0.185 | 4.813 | 2.500 | -2.313 | -48.1% | 1 / 0 |
| SparseFlashAttention | relative_15pct | 5772 | 5772 | 0 | 523.698 | 494.783 | 90.731 | 85.721 | -5.010 | -5.5% | 1 / 0 |
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
| GroupedMatmulSwigluQuantV2 | 39f0b1677a1c | 5550 | reference_only | 88.039 | 15.560 | -72.479 | - | reference_only | - |
| MlaPrologV3 | 37f27ca5292d | 1554 | reference_only | 41.291 | 38.014 | -3.277 | - | reference_only | - |
| MlaPrologV3 | 025f6477af8d | 4218 | reference_only | 40.913 | 38.014 | -2.899 | - | reference_only | - |
| LightningIndexer | e9b2c93d0357 | 1554 | reference_only | 24.905 | 7.500 | -17.405 | - | reference_only | - |
| MoeGatingTopK | f9b3cc6fa431 | 5550 | reference_only | 4.013 | 7.500 | 3.487 | - | reference_only | - |

## a5_kimi_k3_decode / source_declared_unfused_reference

Graph: `sha256:a84d6cb3f6ecbb19a911cf03ffcc8f0041c1ccb59bb400377afa605aeb8c6d19`.

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

## a5_kimi_k3_decode_checkpoint / current_checkpoint_conditional

Graph: `sha256:5762f6d1c43f3ab585ffe750a5b8bea7168ef3729a15e7dfab3f1ae5995a4ab6`.

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
| SituMxQuant | cd38938eb970 | 6898 | compared | 65.134 | 0.002 | -65.132 | -100.0% | relative_15pct | false |
| GroupedMatmulSituQuant | 3f44ae69bcef | 7266 | reference_only | 91.780 | 7.735 | -84.045 | - | reference_only | - |
| MlaPrologV3 | 67264fdbcce3 | 1798 | reference_only | 22.248 | 17.439 | -4.809 | - | reference_only | - |

## a5_kimi_k3_decode_checkpoint_eager_single_group / source_single_group_mxfp8_conditional

Graph: `sha256:6f8029d1a8c41e022f593ad3cfb4e144aabf6cc893810380a7094ea14c26bc1a`.

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
| SituMxQuant | 5ebf5baf27a2 | 6898 | compared | 65.134 | 0.002 | -65.132 | -100.0% | relative_15pct | false |
| GroupedMatmulSituQuant | 1abe8b0ec7a7 | 7266 | reference_only | 91.780 | 7.735 | -84.045 | - | reference_only | - |
| MlaPrologV3 | 4e0c0c7643a2 | 1798 | reference_only | 22.248 | 17.439 | -4.809 | - | reference_only | - |

## a5_kimi_k3_decode_checkpoint_situ_arch35 / source_checkpoint_situ_arch35_conditional

Graph: `sha256:e75fd366df1dcd7efc694f7b567ee9ee5cd7da6ad8ff55edb65f8a2efc4a8fc4`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 0 | 2 | 0 | 6965 |
| absolute_15us | 6 | 6 | 0 | 36504 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SituMxQuant | relative_15pct | 7266 | 6898 | 0 | 449.295 | 1.185 | 65.134 | 0.172 | -64.962 | -99.7% | 0 / 1 |
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
| SituMxQuant | d94b28dc9047 | 6898 | compared | 65.134 | 0.172 | -64.962 | -99.7% | relative_15pct | false |
| GroupedMatmulSituQuant | 6d86aa44f0e7 | 7266 | reference_only | 91.780 | 7.735 | -84.045 | - | reference_only | - |
| MlaPrologV3 | 8b9c871d9958 | 1798 | reference_only | 22.248 | 17.439 | -4.809 | - | reference_only | - |

## a5_kimi_k3 / case_default

Graph: `sha256:c90b4894bc025bfd8bdef8d7a1fb18cd6f700f4f72b6171ff0c6bf39bd3a76e2`.

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

## a5_kimi_k3_checkpoint / current_checkpoint_conditional

Graph: `sha256:e4f468f6fd1726549f7701745aad8c356c444bba7455938ef5f669a0a816c2a8`.

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
| SituMxQuant | 2b531219918e | 368 | compared | 147.124 | 14.953 | -132.172 | -89.8% | relative_15pct | false |
| GroupedMatmulSituQuant | 05cac90eb1ed | 7266 | reference_only | 91.780 | 11336.311 | 11244.530 | - | reference_only | - |

## a5_kimi_k3_checkpoint_eager_single_group / source_single_group_mxfp8_conditional

Graph: `sha256:2862a4dfb103945fd1123442efd028a2af518d4fdbffa36b831be7ffe87e2136`.

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
| SituMxQuant | 84a08df292e2 | 368 | compared | 147.124 | 14.953 | -132.172 | -89.8% | relative_15pct | false |
| GroupedMatmulSituQuant | 8d827c43a802 | 7266 | reference_only | 91.780 | 11336.311 | 11244.530 | - | reference_only | - |

## a5_kimi_k3_checkpoint_eager_single_group_sp / source_sp_single_group_mxfp8_conditional

Graph: `sha256:2396d2f42e764add9d4b407fe5a4890ddae427df0ed02ee0479e9a8e596b132e`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 9 | 0 | 9 | 0 | 2295 |
| absolute_15us | 3 | 3 | 0 | 468 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicMxQuant | relative_15pct | 22499 | 1112 | 0 | 76.142 | 49.483 | 68.473 | 44.499 | -23.975 | -35.0% | 0 / 2 |
| GroupedMatmul | relative_15pct | 27248 | 736 | 0 | 54.112 | 79.330 | 73.522 | 107.785 | 34.263 | +46.6% | 0 / 2 |
| MatMulV3 | relative_15pct | 21819 | 163 | 0 | 46.985 | 72.764 | 288.250 | 446.402 | 158.153 | +54.9% | 0 / 2 |
| layer_norm_gated_fwd_kernel | relative_15pct | 5451 | 276 | 0 | 37.608 | 5.209 | 136.262 | 18.874 | -117.388 | -86.1% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 350 | 8 | 0 | 6.967 | 12.136 | 870.894 | 1516.942 | 646.048 | +74.2% | 0 / 2 |

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicMxQuant | absolute_15us | 22499 | 468 | 0 | 4.411 | 3.067 | 9.425 | 6.554 | -2.871 | -30.5% | 3 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_AicpuKernel | 1104 | 919.190 | 0 | no_tensor_candidates (1104) |
| ChunkKdaFwd | 1104 | 881.998 | 0 | no_tensor_candidates (1104) |
| GroupedMatmul | 27248 | 813.481 | 0 | no_tensor_candidates (26512) |
| HcclLaunchAicpuKernel | 1543 | 683.214 | 0 | no_tensor_candidates (1543) |
| GroupedMatmulSituQuant | 7266 | 666.877 | 7266 | mxfp4_native_execution_unmodeled (7266) |
| MatMulV3 | 21819 | 656.394 | 0 | no_tensor_candidates (21656) |
| MatmulReduceScatterV2Mc2AicpuKernel | 744 | 638.124 | 0 | no_tensor_candidates (744) |
| SituMxQuant | 7266 | 503.437 | 368 | no_tensor_candidates (6898), unfused_subgraph_is_not_the_observed_native_kernel (368) |
| QuantBatchMatmulV4 | 14531 | 431.003 | 736 | no_tensor_candidates (13795), mxfp4_native_execution_unmodeled (736) |
| hcom_allGather_ | 15203 | 409.082 | 0 | no_tensor_candidates (15203) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| GroupedMatmulSituQuant | e61c23cbbc20 | 7266 | reference_only | 91.780 | 11336.311 | 11244.530 | - | reference_only | - |
| SituMxQuant | d9aeb5a37d2d | 368 | reference_only | 147.124 | 15.939 | -131.186 | - | reference_only | - |

## a5_kimi_k3_checkpoint_situ_arch35 / source_checkpoint_situ_arch35_conditional

Graph: `sha256:d7b6a6916bf4476ba93732e520c1df2dec34a97bf339b789bf81cf39da137546`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 8 | 0 | 8 | 0 | 1927 |
| absolute_15us | 1 | 1 | 0 | 96 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicMxQuant | relative_15pct | 22499 | 1112 | 0 | 76.142 | 49.483 | 68.473 | 44.499 | -23.975 | -35.0% | 0 / 2 |
| SituMxQuant | relative_15pct | 7266 | 368 | 0 | 54.142 | 21.950 | 147.124 | 59.646 | -87.478 | -59.5% | 0 / 1 |
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
| SituMxQuant | aca84a4eccba | 368 | compared | 147.124 | 59.646 | -87.478 | -59.5% | relative_15pct | false |
| GroupedMatmulSituQuant | 08ad1f514eb5 | 7266 | reference_only | 91.780 | 11336.311 | 11244.530 | - | reference_only | - |

## a5_qwen38_paged_decode_q1 / paged_body_geometry_conditional

Graph: `sha256:38a7563493708572538d35bb238fdac737c25c009998ad23a971ebb0b0767916`.

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

Graph: `sha256:219a0dd593f3cdd9b0c02fd3ea9f40d62e9c537a2aa8975075681dff807982e2`.

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

## a5_qwen38_paged_decode_q1_staged / source_paged_decode_program_conditional

Graph: `sha256:ff03cbc0567f4edd3cce572169c83f4784094b838eee8bd0301b0907b973ff5a`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 2 | 2 | 0 | 61 | 0 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

None.

### Small-call errors: absolute per-call difference > 15 us

None.

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV3 | relative_15pct | 1956 | 37 | 0 | 27.188 | 23.851 | 734.804 | 644.633 | -90.171 | -12.3% | 1 / 0 |
| FusedInferAttentionScore | relative_15pct | 228 | 24 | 0 | 3.240 | 3.402 | 135.013 | 141.759 | 6.745 | +5.0% | 1 / 0 |

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

## a5_qwen38_paged_decode_q4_staged / source_paged_decode_program_conditional

Graph: `sha256:37e2d02964a543e9d29c962c902f589a7b0e9404fb709ac11d8b5a7721c9681a`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 4 | 3 | 1 | 902 | 528 |
| absolute_15us | 12 | 12 | 0 | 5885 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MatMulV3 | relative_15pct | 1956 | 528 | 0 | 27.073 | 22.848 | 51.276 | 43.272 | -8.004 | -15.6% | 0 / 1 |

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
| FusedInferAttentionScore | relative_15pct | 228 | 187 | 0 | 26.912 | 30.739 | 143.916 | 164.382 | 20.467 | +14.2% | 1 / 0 |

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

## a5_qwen38 / case_default

Graph: `sha256:998bf325fd495c64f675a7f2a1501095a6d66328ec8cb87dc9e6c98f999303be`.

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
| ChunkGatedDeltaRuleFwdPrepare | relative_15pct | 48 | 48 | 0 | 73.924 | 58.965 | 1540.079 | 1228.444 | -311.635 | -20.2% | 0 / 1 |
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
| ChunkFwdH | relative_15pct | 48 | 48 | 0 | 38.757 | 40.945 | 807.427 | 853.016 | 45.589 | +5.6% | 1 / 0 |
| fused_gdn_gating_kernel | relative_15pct | 576 | 48 | 0 | 32.340 | 28.031 | 673.758 | 583.985 | -89.773 | -13.3% | 1 / 0 |
| CausalConv1d | relative_15pct | 576 | 48 | 0 | 16.259 | 17.949 | 338.724 | 373.936 | 35.212 | +10.4% | 1 / 0 |

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

Graph: `sha256:0cae669dccd4ab2d8a66d9e760a2ba58158b564b7dbcd7eb21213f9ad481d12c`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 22 | 11 | 11 | 488 | 501 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FusedInferAttentionScore | relative_15pct | 228 | 17 | 0 | 213.742 | 129.650 | 12573.041 | 7626.473 | -4946.568 | -39.3% | 0 / 1 |
| ChunkGatedDeltaRuleFwdPrepare | relative_15pct | 48 | 48 | 0 | 73.924 | 58.965 | 1540.079 | 1228.444 | -311.635 | -20.2% | 0 / 1 |
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
| ChunkFwdH | relative_15pct | 48 | 48 | 0 | 38.757 | 40.945 | 807.427 | 853.016 | 45.589 | +5.6% | 1 / 0 |
| fused_gdn_gating_kernel | relative_15pct | 576 | 48 | 0 | 32.340 | 28.031 | 673.758 | 583.985 | -89.773 | -13.3% | 1 / 0 |
| CausalConv1d | relative_15pct | 576 | 48 | 0 | 16.259 | 17.949 | 338.724 | 373.936 | 35.212 | +10.4% | 1 / 0 |

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

Graph: `sha256:dd8f8319b45e08f6925d4f27c90081bd973db0ae76456c7773b5a1ef1c57efae`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 21 | 4 | 17 | 181 | 791 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 1920 | 160 | 0 | 714.307 | 1253.383 | 4464.419 | 7833.641 | 3369.222 | +75.5% | 0 / 4 |
| MatMulV3 | relative_15pct | 1956 | 147 | 0 | 431.194 | 725.922 | 2933.291 | 4938.243 | 2004.952 | +68.4% | 0 / 3 |
| ChunkGatedDeltaRuleFwdPrepare | relative_15pct | 48 | 48 | 0 | 73.924 | 58.965 | 1540.079 | 1228.444 | -311.635 | -20.2% | 0 / 1 |
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
| ChunkFwdH | relative_15pct | 48 | 48 | 0 | 38.757 | 40.945 | 807.427 | 853.016 | 45.589 | +5.6% | 1 / 0 |
| fused_gdn_gating_kernel | relative_15pct | 576 | 48 | 0 | 32.340 | 28.031 | 673.758 | 583.985 | -89.773 | -13.3% | 1 / 0 |
| CausalConv1d | relative_15pct | 576 | 48 | 0 | 16.259 | 17.949 | 338.724 | 373.936 | 35.212 | +10.4% | 1 / 0 |

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

## a5_qwen38_paged_prefill_combined / source_combined_prefill_conditional

Graph: `sha256:3009b796a21d5e10fceefe0f691052504355fdcb84a59fccb2a99f4e66a8be5d`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 21 | 11 | 10 | 488 | 484 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ChunkGatedDeltaRuleFwdPrepare | relative_15pct | 48 | 48 | 0 | 73.924 | 58.965 | 1540.079 | 1228.444 | -311.635 | -20.2% | 0 / 1 |
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
| ChunkFwdH | relative_15pct | 48 | 48 | 0 | 38.757 | 40.945 | 807.427 | 853.016 | 45.589 | +5.6% | 1 / 0 |
| fused_gdn_gating_kernel | relative_15pct | 576 | 48 | 0 | 32.340 | 28.031 | 673.758 | 583.985 | -89.773 | -13.3% | 1 / 0 |
| CausalConv1d | relative_15pct | 576 | 48 | 0 | 16.259 | 17.949 | 338.724 | 373.936 | 35.212 | +10.4% | 1 / 0 |

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

## a5_qwen38_contiguous_prefill_combined / source_combined_prefill_conditional

Graph: `sha256:92c6f44938275960f9fa91a7fb406698773298e080291f86edd12c4a5130a2f0`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 21 | 11 | 10 | 488 | 484 |
| absolute_15us | 0 | 0 | 0 | 0 | 0 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ChunkGatedDeltaRuleFwdPrepare | relative_15pct | 48 | 48 | 0 | 73.924 | 58.965 | 1540.079 | 1228.444 | -311.635 | -20.2% | 0 / 1 |
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
| ChunkFwdH | relative_15pct | 48 | 48 | 0 | 38.757 | 40.945 | 807.427 | 853.016 | 45.589 | +5.6% | 1 / 0 |
| fused_gdn_gating_kernel | relative_15pct | 576 | 48 | 0 | 32.340 | 28.031 | 673.758 | 583.985 | -89.773 | -13.3% | 1 / 0 |
| CausalConv1d | relative_15pct | 576 | 48 | 0 | 16.259 | 17.949 | 338.724 | 373.936 | 35.212 | +10.4% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| QuantBatchMatmulV3 | 1920 | 781.406 | 0 | no_tensor_candidates (1760) |
| MatMulV3 | 1956 | 611.956 | 0 | no_tensor_candidates (1772) |
| FusedInferAttentionScore | 228 | 243.894 | 0 | no_tensor_candidates (211), physical_program_timeout (17) |
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

## a3_qwen35_paged_decode_q1 / paged_body_geometry_conditional

Graph: `sha256:73a14541946bbec1df06c71a42affa9b9a5c4afed3d92f1d1d6bcaeb8e4b2daf`.

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
| GroupedMatmulSwigluQuant | d1eb68adca54 | 2680 | reference_only | 81.007 | 10.000 | -71.007 | - | reference_only | - |

## a3_qwen35_paged_decode_q2 / paged_body_geometry_conditional

Graph: `sha256:1832150af6f41946284146e063dc0677ea9419497e343ed642d476c1bc1b553f`.

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
| RecurrentGatedDeltaRule | absolute_15us | 1950 | 1950 | 0 | 31.545 | 11.773 | 16.177 | 6.038 | -10.139 | -62.7% | 1 / 0 |
| MoeGatingTopK | absolute_15us | 2747 | 2665 | 0 | 12.166 | 6.663 | 4.565 | 2.500 | -2.065 | -45.2% | 1 / 0 |
| QuantBatchMatmulV3 | absolute_15us | 670 | 650 | 0 | 11.058 | 3.250 | 17.013 | 5.000 | -12.013 | -70.6% | 1 / 0 |
| SwiGlu | absolute_15us | 2814 | 2730 | 0 | 9.726 | 6.825 | 3.563 | 2.500 | -1.063 | -29.8% | 2 / 0 |
| DynamicQuant | absolute_15us | 670 | 650 | 0 | 2.130 | 1.625 | 3.277 | 2.500 | -0.777 | -23.7% | 1 / 0 |
| ScatterPaKvCache | absolute_15us | 737 | 715 | 0 | 1.580 | 1.788 | 2.210 | 2.500 | 0.290 | +13.1% | 1 / 0 |
| GemmaRmsNorm | absolute_15us | 268 | 260 | 0 | 1.133 | 0.650 | 4.357 | 2.500 | -1.857 | -42.6% | 1 / 0 |
| MatMulV2 | relative_15pct | 17879 | 65 | 0 | 14.350 | 13.788 | 220.773 | 212.119 | -8.654 | -3.9% | 1 / 0 |

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
| MoeGatingTopK | aa1dfc7f9acf | 2665 | compared | 4.565 | 2.500 | -2.065 | -45.2% | absolute_15us | true |
| GroupedMatmulSwigluQuant | bcf87984aac1 | 2680 | reference_only | 81.007 | 12.178 | -68.829 | - | reference_only | - |

## a3_qwen35 / case_default

Graph: `sha256:eb1b3bf219e4d3b8e1de4fa3482e4e1b9c776596167c7f5fcaf3b4f0ea2ff53f`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 10 | 2 | 8 | 89 | 447 |
| absolute_15us | 4 | 3 | 1 | 166 | 60 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GroupedMatmul | relative_15pct | 2814 | 80 | 0 | 55.146 | 81.683 | 689.328 | 1021.039 | 331.711 | +48.1% | 0 / 1 |
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
| MatMulV2 | absolute_15us | 17879 | 82 | 0 | 1.952 | 2.295 | 23.799 | 27.982 | 4.183 | +17.6% | 1 / 0 |
| SwiGlu | absolute_15us | 2814 | 84 | 0 | 1.518 | 0.514 | 18.066 | 6.117 | -11.949 | -66.1% | 2 / 0 |
| MatMulV2 | relative_15pct | 17879 | 69 | 0 | 15.683 | 14.629 | 227.293 | 212.009 | -15.284 | -6.7% | 1 / 0 |
| QuantBatchMatmulV3 | relative_15pct | 670 | 20 | 0 | 4.660 | 4.517 | 232.983 | 225.850 | -7.133 | -3.1% | 1 / 0 |

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
| MoeGatingTopK | f8495a5abc28 | 82 | compared | 243.864 | 7.944 | -235.920 | -96.7% | relative_15pct | false |
| GroupedMatmulSwigluQuant | 5a83a825fdcf | 2680 | reference_only | 81.007 | 472.214 | 391.207 | - | reference_only | - |

## a3_qwen35_paged_prefill_q8192 / paged_body_geometry_conditional

Graph: `sha256:86dbb1cafa63f0deeab2c4bfd9ec046f66cd42868973b14ce0ccf8de2a921ffb`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 10 | 2 | 8 | 89 | 447 |
| absolute_15us | 4 | 3 | 1 | 166 | 60 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GroupedMatmul | relative_15pct | 2814 | 80 | 0 | 55.146 | 81.683 | 689.328 | 1021.039 | 331.711 | +48.1% | 0 / 1 |
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
| MatMulV2 | absolute_15us | 17879 | 82 | 0 | 1.952 | 2.295 | 23.799 | 27.982 | 4.183 | +17.6% | 1 / 0 |
| SwiGlu | absolute_15us | 2814 | 84 | 0 | 1.518 | 0.514 | 18.066 | 6.117 | -11.949 | -66.1% | 2 / 0 |
| MatMulV2 | relative_15pct | 17879 | 69 | 0 | 15.683 | 14.629 | 227.293 | 212.009 | -15.284 | -6.7% | 1 / 0 |
| QuantBatchMatmulV3 | relative_15pct | 670 | 20 | 0 | 4.660 | 4.517 | 232.983 | 225.850 | -7.133 | -3.1% | 1 / 0 |

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
| MoeGatingTopK | 6f093b3ff837 | 82 | compared | 243.864 | 7.944 | -235.920 | -96.7% | relative_15pct | false |
| GroupedMatmulSwigluQuant | e948c644eb0b | 2680 | reference_only | 81.007 | 472.214 | 391.207 | - | reference_only | - |

## a3_qwen35_paged_prefill_staged / source_combined_prefill_conditional

Graph: `sha256:cd8de16edd75417c82dc141e76a1c6c4d16c3672c74a7d9974ccb3d97ddb0b1f`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 10 | 3 | 7 | 100 | 436 |
| absolute_15us | 4 | 3 | 1 | 166 | 60 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GroupedMatmul | relative_15pct | 2814 | 80 | 0 | 55.146 | 81.683 | 689.328 | 1021.039 | 331.711 | +48.1% | 0 / 1 |
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
| MatMulV2 | absolute_15us | 17879 | 82 | 0 | 1.952 | 2.295 | 23.799 | 27.982 | 4.183 | +17.6% | 1 / 0 |
| SwiGlu | absolute_15us | 2814 | 84 | 0 | 1.518 | 0.514 | 18.066 | 6.117 | -11.949 | -66.1% | 2 / 0 |
| FusedInferAttentionScore | relative_15pct | 737 | 11 | 0 | 27.242 | 30.066 | 2476.504 | 2733.286 | 256.782 | +10.4% | 1 / 0 |
| MatMulV2 | relative_15pct | 17879 | 69 | 0 | 15.683 | 14.629 | 227.293 | 212.009 | -15.284 | -6.7% | 1 / 0 |
| QuantBatchMatmulV3 | relative_15pct | 670 | 20 | 0 | 4.660 | 4.517 | 232.983 | 225.850 | -7.133 | -3.1% | 1 / 0 |

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
| MoeGatingTopK | 1eecc3a3ac69 | 82 | compared | 243.864 | 7.944 | -235.920 | -96.7% | relative_15pct | false |
| GroupedMatmulSwigluQuant | 7861475797be | 2680 | reference_only | 81.007 | 472.214 | 391.207 | - | reference_only | - |

## a3_qwen36_paged_decode_q1 / paged_body_geometry_conditional

Graph: `sha256:8838546391f32bb525afe558649ca23b99ea703181b78b8e587a79cf3be30449`.

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

Graph: `sha256:7f9001d99bfc4fca4892759a9e30b80eb7d34a9d4d26c882c82b8ac8df8abe13`.

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
| QuantBatchMatmulV3 | absolute_15us | 3740 | 3300 | 0 | 98.231 | 75.185 | 29.767 | 22.783 | -6.984 | -23.5% | 5 / 0 |
| RecurrentGatedDeltaRule | absolute_15us | 720 | 720 | 0 | 18.515 | 8.645 | 25.715 | 12.006 | -13.709 | -53.3% | 1 / 0 |
| DynamicQuant | absolute_15us | 3740 | 3300 | 0 | 13.551 | 8.250 | 4.106 | 2.500 | -1.606 | -39.1% | 3 / 0 |
| SwiGlu | absolute_15us | 1139 | 1005 | 0 | 4.301 | 2.513 | 4.280 | 2.500 | -1.780 | -41.6% | 1 / 0 |
| GemmaRmsNorm | absolute_15us | 170 | 150 | 0 | 0.717 | 0.375 | 4.781 | 2.500 | -2.281 | -47.7% | 1 / 0 |
| ScatterPaKvCache | absolute_15us | 323 | 255 | 0 | 0.671 | 0.638 | 2.630 | 2.500 | -0.130 | -5.0% | 1 / 0 |
| MatMulV2 | relative_15pct | 1649 | 15 | 0 | 8.734 | 7.953 | 582.238 | 530.208 | -52.030 | -8.9% | 1 / 0 |

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

## a3_qwen36 / case_default

Graph: `sha256:ad503a8a46e605995c869b6d51ad0c5c47c33e41c87616c638133d1ea4612608`.

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
| QuantBatchMatmulV3 | relative_15pct | 3740 | 440 | 0 | 437.374 | 430.298 | 994.032 | 977.950 | -16.082 | -1.6% | 5 / 0 |
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

Graph: `sha256:6b055a57e6bde19bd49e60855358b6fc3d38ef5770234f14857742a745525ec6`.

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
| QuantBatchMatmulV3 | relative_15pct | 3740 | 440 | 0 | 437.374 | 430.298 | 994.032 | 977.950 | -16.082 | -1.6% | 5 / 0 |
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

## a3_qwen36_paged_prefill_staged / source_combined_prefill_conditional

Graph: `sha256:ff85086af1b7fd126d58f4f769a2c74d86fe9155345a0ace40a75871dfed4575`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 14 | 8 | 6 | 644 | 590 |
| absolute_15us | 1 | 0 | 1 | 0 | 96 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
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
| QuantBatchMatmulV3 | relative_15pct | 3740 | 440 | 0 | 437.374 | 430.298 | 994.032 | 977.950 | -16.082 | -1.6% | 5 / 0 |
| FusedInferAttentionScore | relative_15pct | 323 | 17 | 0 | 62.532 | 69.117 | 3678.352 | 4065.731 | 387.378 | +10.5% | 1 / 0 |
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

Graph: `sha256:3ce7f00a1d9aa57b78e83ee6518b4d8f00731b2d471a8215aabdd1065cf60817`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 16 | 3 | 13 | 132 | 463 |
| absolute_15us | 1 | 0 | 1 | 0 | 65 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 44 | 44 | 0 | 98.897 | 30.910 | 2247.659 | 702.502 | -1545.157 | -68.7% | 0 / 3 |
| HcPost | relative_15pct | 88 | 88 | 0 | 36.817 | 22.170 | 418.375 | 251.931 | -166.444 | -39.8% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 241 | 109 | 0 | 15.331 | 14.036 | 140.651 | 128.772 | -11.878 | -8.4% | 0 / 3 |
| DynamicQuant | relative_15pct | 239 | 132 | 0 | 8.164 | 5.077 | 61.851 | 38.460 | -23.391 | -37.8% | 0 / 2 |
| RmsNorm | relative_15pct | 182 | 46 | 0 | 4.105 | 2.573 | 89.236 | 55.931 | -33.305 | -37.3% | 0 / 1 |
| MatMulV2 | relative_15pct | 110 | 44 | 0 | 3.396 | 3.243 | 77.171 | 73.710 | -3.461 | -4.5% | 0 / 3 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 239 | 65 | 0 | 2.056 | 0.682 | 31.631 | 10.499 | -21.132 | -66.8% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 241 | 88 | 0 | 9.791 | 9.268 | 111.257 | 105.320 | -5.937 | -5.3% | 2 / 0 |
| MatMulV2 | relative_15pct | 110 | 44 | 0 | 8.414 | 7.187 | 191.226 | 163.344 | -27.882 | -14.6% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_ | 264 | 64.783 | 0 | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | no_tensor_candidates (90) |
| HcPre | 88 | 37.975 | 88 | unfused_subgraph_is_not_the_observed_native_kernel (88) |
| QuantBatchMatmulV3 | 241 | 28.176 | 0 | no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 0 | no_tensor_candidates (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 0 | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 44 | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 0 | no_tensor_candidates (42) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPost | 1403c7ac8af2 | 88 | compared | 418.375 | 251.931 | -166.444 | -39.8% | relative_15pct | false |
| HcPre | 4c5be142ab45 | 88 | reference_only | 431.534 | 929.686 | 498.152 | - | reference_only | - |
| GroupedMatmulSwigluQuant | 18295db0d7a2 | 44 | reference_only | 588.788 | 5681.584 | 5092.796 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | b48a80592a38 | 21 | reference_only | 399.030 | 248.045 | -150.985 | - | reference_only | - |

## a3_v4f / selected_native_fusion

Graph: `sha256:597f711b7db17ab38ca32b1f171b1268daa786a222c980932d8db302e8ca7215`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 17 | 3 | 14 | 132 | 551 |
| absolute_15us | 1 | 0 | 1 | 0 | 65 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 44 | 44 | 0 | 98.897 | 30.910 | 2247.659 | 702.502 | -1545.157 | -68.7% | 0 / 3 |
| HcPre | relative_15pct | 88 | 88 | 0 | 37.975 | 63.496 | 431.534 | 721.550 | 290.016 | +67.2% | 0 / 1 |
| HcPost | relative_15pct | 88 | 88 | 0 | 36.817 | 26.166 | 418.375 | 297.336 | -121.038 | -28.9% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 241 | 109 | 0 | 15.331 | 14.036 | 140.651 | 128.772 | -11.878 | -8.4% | 0 / 3 |
| DynamicQuant | relative_15pct | 239 | 132 | 0 | 8.164 | 5.077 | 61.851 | 38.460 | -23.391 | -37.8% | 0 / 2 |
| RmsNorm | relative_15pct | 182 | 46 | 0 | 4.105 | 2.573 | 89.236 | 55.931 | -33.305 | -37.3% | 0 / 1 |
| MatMulV2 | relative_15pct | 110 | 44 | 0 | 3.396 | 3.243 | 77.171 | 73.710 | -3.461 | -4.5% | 0 / 3 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 239 | 65 | 0 | 2.056 | 0.682 | 31.631 | 10.499 | -21.132 | -66.8% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 241 | 88 | 0 | 9.791 | 9.268 | 111.257 | 105.320 | -5.937 | -5.3% | 2 / 0 |
| MatMulV2 | relative_15pct | 110 | 44 | 0 | 8.414 | 7.187 | 191.226 | 163.344 | -27.882 | -14.6% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_ | 264 | 64.783 | 0 | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | no_tensor_candidates (90) |
| QuantBatchMatmulV3 | 241 | 28.176 | 0 | no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 0 | no_tensor_candidates (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 0 | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 44 | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 0 | no_tensor_candidates (42) |
| MatMulV2 | 110 | 12.384 | 0 | no_tensor_candidates (22) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPre | 41f2212c830c | 88 | compared | 431.534 | 721.550 | 290.016 | +67.2% | relative_15pct | false |
| HcPost | e8b710a8ccb2 | 88 | compared | 418.375 | 297.336 | -121.038 | -28.9% | relative_15pct | false |
| GroupedMatmulSwigluQuant | 9d973974b389 | 44 | reference_only | 588.788 | 5681.584 | 5092.796 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | 5554890b74bc | 21 | reference_only | 399.030 | 248.045 | -150.985 | - | reference_only | - |

## a3_v4f_compressor_fp32 / source_compressor_fp32_conditional_reference

Graph: `sha256:73817318f0a58ed588744b3a7a6f56fd593e5f693a8b244b28ac808846709c61`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 17 | 3 | 14 | 132 | 551 |
| absolute_15us | 1 | 0 | 1 | 0 | 65 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 44 | 44 | 0 | 98.897 | 30.910 | 2247.659 | 702.502 | -1545.157 | -68.7% | 0 / 3 |
| HcPre | relative_15pct | 88 | 88 | 0 | 37.975 | 63.496 | 431.534 | 721.550 | 290.016 | +67.2% | 0 / 1 |
| HcPost | relative_15pct | 88 | 88 | 0 | 36.817 | 26.166 | 418.375 | 297.336 | -121.038 | -28.9% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 241 | 109 | 0 | 15.331 | 14.036 | 140.651 | 128.772 | -11.878 | -8.4% | 0 / 3 |
| DynamicQuant | relative_15pct | 239 | 132 | 0 | 8.164 | 5.077 | 61.851 | 38.460 | -23.391 | -37.8% | 0 / 2 |
| RmsNorm | relative_15pct | 182 | 46 | 0 | 4.105 | 2.573 | 89.236 | 55.931 | -33.305 | -37.3% | 0 / 1 |
| MatMulV2 | relative_15pct | 110 | 44 | 0 | 3.396 | 3.243 | 77.171 | 73.710 | -3.461 | -4.5% | 0 / 3 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 239 | 65 | 0 | 2.056 | 0.682 | 31.631 | 10.499 | -21.132 | -66.8% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 241 | 88 | 0 | 9.791 | 9.268 | 111.257 | 105.320 | -5.937 | -5.3% | 2 / 0 |
| MatMulV2 | relative_15pct | 110 | 44 | 0 | 8.414 | 7.187 | 191.226 | 163.344 | -27.882 | -14.6% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_ | 264 | 64.783 | 0 | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | no_tensor_candidates (90) |
| QuantBatchMatmulV3 | 241 | 28.176 | 0 | no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 62 | unfused_subgraph_is_not_the_observed_native_kernel (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 0 | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 44 | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 0 | no_tensor_candidates (42) |
| MatMulV2 | 110 | 12.384 | 0 | no_tensor_candidates (22) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPre | a449e0eb7001 | 88 | compared | 431.534 | 721.550 | 290.016 | +67.2% | relative_15pct | false |
| HcPost | bd2d4d339a82 | 88 | compared | 418.375 | 297.336 | -121.038 | -28.9% | relative_15pct | false |
| Compressor | a6453675b9a3 | 21 | reference_only | 758.193 | 497.229 | -260.965 | - | reference_only | - |
| Compressor | 3e465ed4dd4a | 21 | reference_only | 239.132 | 155.065 | -84.068 | - | reference_only | - |
| Compressor | 4e50a1356c24 | 20 | reference_only | 320.864 | 269.222 | -51.642 | - | reference_only | - |
| GroupedMatmulSwigluQuant | dac0157d9605 | 44 | reference_only | 588.788 | 5681.584 | 5092.796 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | fc2f42f15d54 | 21 | reference_only | 399.030 | 248.045 | -150.985 | - | reference_only | - |

## a3_v4f_shared_quant / source_shared_int32_conditional

Graph: `sha256:0d6efa768fda03e835adb312f6af9d0641a505847ace86a1270025913e1e671b`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 17 | 4 | 13 | 176 | 463 |
| absolute_15us | 2 | 0 | 2 | 0 | 109 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 44 | 44 | 0 | 98.897 | 30.910 | 2247.659 | 702.502 | -1545.157 | -68.7% | 0 / 3 |
| HcPost | relative_15pct | 88 | 88 | 0 | 36.817 | 22.170 | 418.375 | 251.931 | -166.444 | -39.8% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 241 | 109 | 0 | 15.331 | 14.036 | 140.651 | 128.772 | -11.878 | -8.4% | 0 / 3 |
| DynamicQuant | relative_15pct | 239 | 132 | 0 | 8.164 | 5.077 | 61.851 | 38.460 | -23.391 | -37.8% | 0 / 2 |
| RmsNorm | relative_15pct | 182 | 46 | 0 | 4.105 | 2.573 | 89.236 | 55.931 | -33.305 | -37.3% | 0 / 1 |
| MatMulV2 | relative_15pct | 110 | 44 | 0 | 3.396 | 3.243 | 77.171 | 73.710 | -3.461 | -4.5% | 0 / 3 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DequantSwigluQuant | absolute_15us | 44 | 44 | 0 | 1.450 | 0.446 | 32.948 | 10.131 | -22.817 | -69.3% | 0 / 1 |
| DynamicQuant | absolute_15us | 239 | 65 | 0 | 2.056 | 0.682 | 31.631 | 10.499 | -21.132 | -66.8% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 241 | 132 | 0 | 12.845 | 12.248 | 97.312 | 92.790 | -4.522 | -4.6% | 3 / 0 |
| MatMulV2 | relative_15pct | 110 | 44 | 0 | 8.414 | 7.187 | 191.226 | 163.344 | -27.882 | -14.6% | 1 / 0 |

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
| HcPost | f55fd00b7f26 | 88 | compared | 418.375 | 251.931 | -166.444 | -39.8% | relative_15pct | false |
| HcPre | 454345ef63d5 | 88 | reference_only | 431.534 | 929.686 | 498.152 | - | reference_only | - |
| GroupedMatmulSwigluQuant | 0a33af156d31 | 44 | reference_only | 588.788 | 5681.584 | 5092.796 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | a59eb135c49a | 21 | reference_only | 399.030 | 248.045 | -150.985 | - | reference_only | - |

## a3_v4f_scfa / source_scfa_offchip_conditional

Graph: `sha256:41ed867cb195edc2bbc730300591c194c001c8e2ed666253e2c6ab597934b733`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 16 | 3 | 13 | 132 | 463 |
| absolute_15us | 1 | 0 | 1 | 0 | 65 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 44 | 44 | 0 | 98.897 | 148.983 | 2247.659 | 3385.967 | 1138.308 | +50.6% | 0 / 3 |
| HcPost | relative_15pct | 88 | 88 | 0 | 36.817 | 22.170 | 418.375 | 251.931 | -166.444 | -39.8% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 241 | 109 | 0 | 15.331 | 14.036 | 140.651 | 128.772 | -11.878 | -8.4% | 0 / 3 |
| DynamicQuant | relative_15pct | 239 | 132 | 0 | 8.164 | 5.077 | 61.851 | 38.460 | -23.391 | -37.8% | 0 / 2 |
| RmsNorm | relative_15pct | 182 | 46 | 0 | 4.105 | 2.573 | 89.236 | 55.931 | -33.305 | -37.3% | 0 / 1 |
| MatMulV2 | relative_15pct | 110 | 44 | 0 | 3.396 | 3.243 | 77.171 | 73.710 | -3.461 | -4.5% | 0 / 3 |

### Small-call errors: absolute per-call difference > 15 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DynamicQuant | absolute_15us | 239 | 65 | 0 | 2.056 | 0.682 | 31.631 | 10.499 | -21.132 | -66.8% | 0 / 1 |

### Within tolerance: separate from Top Errors

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 | relative_15pct | 241 | 88 | 0 | 9.791 | 9.268 | 111.257 | 105.320 | -5.937 | -5.3% | 2 / 0 |
| MatMulV2 | relative_15pct | 110 | 44 | 0 | 8.414 | 7.187 | 191.226 | 163.344 | -27.882 | -14.6% | 1 / 0 |

### Unscored coverage: highest activity families

| Native family | All events | All activity ms | Reference events | Unscored reasons |
| --- | ---: | ---: | ---: | --- |
| hcom_alltoallv_ | 264 | 64.783 | 0 | no_tensor_candidates (264) |
| hcom_allReduce_ | 90 | 57.196 | 0 | no_tensor_candidates (90) |
| allreduceAicpuKernel | 90 | 38.762 | 0 | no_tensor_candidates (90) |
| HcPre | 88 | 37.975 | 88 | unfused_subgraph_is_not_the_observed_native_kernel (88) |
| QuantBatchMatmulV3 | 241 | 28.176 | 0 | no_tensor_candidates (44) |
| Compressor | 62 | 27.361 | 0 | no_tensor_candidates (62) |
| hcom_allGather_ | 136 | 27.292 | 0 | no_tensor_candidates (136) |
| RmsNorm | 182 | 26.287 | 0 | no_tensor_candidates (136) |
| GroupedMatmulSwigluQuant | 44 | 25.907 | 44 | unfused_subgraph_is_not_the_observed_native_kernel (44) |
| DynamicQuant | 239 | 16.163 | 0 | no_tensor_candidates (42) |

### Subgraph cohorts

| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| HcPost | 482233a4fb81 | 88 | compared | 418.375 | 251.931 | -166.444 | -39.8% | relative_15pct | false |
| HcPre | de9e2efe8362 | 88 | reference_only | 431.534 | 929.686 | 498.152 | - | reference_only | - |
| GroupedMatmulSwigluQuant | 9a02ee18aea2 | 44 | reference_only | 588.788 | 5681.584 | 5092.796 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | 2527126fd61f | 21 | reference_only | 399.030 | 248.045 | -150.985 | - | reference_only | - |

## a3_v4pro / case_default

Graph: `sha256:1b899932306810944d119c8e0ebe37617c3f33a23d95607ce39b2db0303432df`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 10 | 2 | 8 | 368 | 1740 |
| absolute_15us | 6 | 4 | 2 | 856 | 752 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 248 | 244 | 0 | 173.863 | 17.076 | 712.554 | 69.985 | -642.569 | -90.2% | 0 / 2 |
| HcPost | relative_15pct | 496 | 496 | 0 | 100.241 | 54.644 | 202.098 | 110.169 | -91.930 | -45.5% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 1360 | 744 | 0 | 47.590 | 25.822 | 63.965 | 34.707 | -29.259 | -45.7% | 0 / 3 |
| MatMulV2 | relative_15pct | 616 | 256 | 0 | 29.568 | 35.974 | 115.501 | 140.522 | 25.021 | +21.7% | 0 / 2 |

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
| HcPost | ea18a55f6ba0 | 496 | compared | 202.098 | 110.169 | -91.930 | -45.5% | relative_15pct | false |
| GroupedMatmulSwigluQuantV2 | 5e7ed6d0a068 | 248 | reference_only | 395.623 | 805.300 | 409.678 | - | reference_only | - |
| HcPre | 9dc2d3a0ada2 | 496 | reference_only | 191.803 | 456.458 | 264.655 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | 5169b0c06dfc | 120 | reference_only | 113.425 | 18.539 | -94.886 | - | reference_only | - |

## a3_v4pro / selected_native_fusion

Graph: `sha256:33961614847261e31ae1a142a7a7d6ef04c587dfb49868f28d24f022630e0bdf`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 11 | 2 | 9 | 368 | 2236 |
| absolute_15us | 6 | 4 | 2 | 856 | 752 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 248 | 244 | 0 | 173.863 | 17.076 | 712.554 | 69.985 | -642.569 | -90.2% | 0 / 2 |
| HcPost | relative_15pct | 496 | 496 | 0 | 100.241 | 64.356 | 202.098 | 129.751 | -72.348 | -35.8% | 0 / 1 |
| HcPre | relative_15pct | 496 | 496 | 0 | 95.134 | 156.963 | 191.803 | 316.457 | 124.653 | +65.0% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 1360 | 744 | 0 | 47.590 | 25.822 | 63.965 | 34.707 | -29.259 | -45.7% | 0 / 3 |
| MatMulV2 | relative_15pct | 616 | 256 | 0 | 29.568 | 35.974 | 115.501 | 140.522 | 25.021 | +21.7% | 0 / 2 |

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
| HcPost | 747b372cd7bd | 496 | compared | 202.098 | 129.751 | -72.348 | -35.8% | relative_15pct | false |
| HcPre | 6db54f10f73d | 496 | compared | 191.803 | 316.457 | 124.653 | +65.0% | relative_15pct | false |
| GroupedMatmulSwigluQuantV2 | 36a35dc1cc48 | 248 | reference_only | 395.623 | 805.300 | 409.678 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | 7431f6ff8d60 | 120 | reference_only | 113.425 | 18.539 | -94.886 | - | reference_only | - |

## a3_v4pro_compressor_fp32 / source_compressor_fp32_conditional_reference

Graph: `sha256:aaebd0180968b5dde72099d02d5716199a56ee017019d257461d4192830cbacd`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 11 | 2 | 9 | 368 | 2236 |
| absolute_15us | 6 | 4 | 2 | 856 | 752 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 248 | 244 | 0 | 173.863 | 17.076 | 712.554 | 69.985 | -642.569 | -90.2% | 0 / 2 |
| HcPost | relative_15pct | 496 | 496 | 0 | 100.241 | 64.356 | 202.098 | 129.751 | -72.348 | -35.8% | 0 / 1 |
| HcPre | relative_15pct | 496 | 496 | 0 | 95.134 | 156.963 | 191.803 | 316.457 | 124.653 | +65.0% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 1360 | 744 | 0 | 47.590 | 25.822 | 63.965 | 34.707 | -29.259 | -45.7% | 0 / 3 |
| MatMulV2 | relative_15pct | 616 | 256 | 0 | 29.568 | 35.974 | 115.501 | 140.522 | 25.021 | +21.7% | 0 / 2 |

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
| HcPost | 12a246d6f0e5 | 496 | compared | 202.098 | 129.751 | -72.348 | -35.8% | relative_15pct | false |
| HcPre | 8a1a900105ff | 496 | compared | 191.803 | 316.457 | 124.653 | +65.0% | relative_15pct | false |
| GroupedMatmulSwigluQuantV2 | e4589afc346f | 248 | reference_only | 395.623 | 805.300 | 409.678 | - | reference_only | - |
| Compressor | 964da7fcd6e2 | 124 | reference_only | 148.297 | 133.388 | -14.909 | - | reference_only | - |
| Compressor | 95a0bd2cbf30 | 120 | reference_only | 300.533 | 259.974 | -40.559 | - | reference_only | - |
| Compressor | f9bacb5ed10a | 120 | reference_only | 192.197 | 70.161 | -122.036 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | da34fa3fa16e | 120 | reference_only | 113.425 | 18.539 | -94.886 | - | reference_only | - |

## a3_v4pro_scfa / source_scfa_offchip_conditional

Graph: `sha256:6a4cd198da22737b82e1c2158e8b2acfcadd2c79476a1b451e8cb3fd8fd77eef`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 10 | 2 | 8 | 368 | 1740 |
| absolute_15us | 6 | 4 | 2 | 856 | 752 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseAttnSharedkv | relative_15pct | 248 | 244 | 0 | 173.863 | 101.275 | 712.554 | 415.062 | -297.491 | -41.8% | 0 / 2 |
| HcPost | relative_15pct | 496 | 496 | 0 | 100.241 | 54.644 | 202.098 | 110.169 | -91.930 | -45.5% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 1360 | 744 | 0 | 47.590 | 25.822 | 63.965 | 34.707 | -29.259 | -45.7% | 0 / 3 |
| MatMulV2 | relative_15pct | 616 | 256 | 0 | 29.568 | 35.974 | 115.501 | 140.522 | 25.021 | +21.7% | 0 / 2 |

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
| HcPost | 2d138061d65c | 496 | compared | 202.098 | 110.169 | -91.930 | -45.5% | relative_15pct | false |
| GroupedMatmulSwigluQuantV2 | 207dd106765d | 248 | reference_only | 395.623 | 805.300 | 409.678 | - | reference_only | - |
| HcPre | 9593aa543618 | 496 | reference_only | 191.803 | 456.458 | 264.655 | - | reference_only | - |
| VllmAscendQuantLightningIndexerV2 | 9d7cf80ef863 | 120 | reference_only | 113.425 | 18.539 | -94.886 | - | reference_only | - |

## a3_glm53_prefill / source_declared_unfused_reference

Graph: `sha256:dca3ce6257f5d92fe83252b270bf7344f825ec8ac0615d8800c5390e7b3803b7`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 12 | 4 | 8 | 105 | 542 |
| absolute_15us | 4 | 2 | 2 | 6 | 99 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseFlashAttention | relative_15pct | 78 | 78 | 0 | 1029.574 | 477.452 | 13199.665 | 6121.175 | -7078.489 | -53.6% | 0 / 1 |
| AddRmsNormBias | relative_15pct | 153 | 153 | 0 | 37.924 | 25.674 | 247.871 | 167.806 | -80.065 | -32.3% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 255 | 75 | 0 | 18.215 | 7.803 | 242.871 | 104.044 | -138.827 | -57.2% | 0 / 1 |
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
| QuantBatchMatmulV3 | relative_15pct | 255 | 105 | 0 | 28.038 | 26.670 | 267.032 | 253.996 | -13.035 | -4.9% | 4 / 0 |

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
| MlaPrologV3 | a103b447213c | 21 | reference_only | 1342.506 | 492.484 | -850.023 | - | reference_only | - |
| MlaPrologV3 | 4bf3f27e3281 | 57 | reference_only | 1248.166 | 492.484 | -755.683 | - | reference_only | - |
| GroupedMatmulSwigluQuantV2 | 13d1cf21893f | 75 | reference_only | 1323.133 | 600.414 | -722.719 | - | reference_only | - |
| LightningIndexer | f5331a816b3a | 21 | reference_only | 1492.464 | 1873.906 | 381.442 | - | reference_only | - |
| MoeGatingTopK | 7bda24616d91 | 75 | reference_only | 101.699 | 13.462 | -88.237 | - | reference_only | - |

## a3_glm53_prefill / selected_native_fusion

Graph: `sha256:5bd29e58412d17747ef5b727c18a7b099028ff87a203c8079499e0b36b67c3e4`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 17 | 2 | 15 | 81 | 815 |
| absolute_15us | 4 | 2 | 2 | 6 | 99 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseFlashAttention | relative_15pct | 78 | 78 | 0 | 1029.574 | 477.452 | 13199.665 | 6121.175 | -7078.489 | -53.6% | 0 / 1 |
| MlaPrologV3 | relative_15pct | 78 | 78 | 0 | 99.338 | 35.208 | 1273.566 | 451.382 | -822.184 | -64.6% | 0 / 2 |
| GroupedMatmulSwigluQuantV2 | relative_15pct | 75 | 75 | 0 | 99.235 | 133.562 | 1323.133 | 1780.833 | 457.699 | +34.6% | 0 / 1 |
| GroupedMatmul | relative_15pct | 75 | 75 | 0 | 91.894 | 168.859 | 1225.255 | 2251.455 | 1026.200 | +83.8% | 0 / 1 |
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
| MlaPrologV3 | 7166cb71e735 | 21 | compared | 1342.506 | 451.382 | -891.124 | -66.4% | relative_15pct | false |
| MlaPrologV3 | 8aeced90a06c | 57 | compared | 1248.166 | 451.382 | -796.784 | -63.8% | relative_15pct | false |
| GroupedMatmulSwigluQuantV2 | 70aef56d1bcd | 75 | compared | 1323.133 | 1780.833 | 457.699 | +34.6% | relative_15pct | false |
| LightningIndexer | ee1f15f910fc | 21 | compared | 1492.464 | 1873.906 | 381.442 | +25.6% | relative_15pct | false |
| MoeGatingTopK | f813a4070b83 | 75 | reference_only | 101.699 | 11.181 | -90.518 | - | reference_only | - |

## a3_glm53_prefill_shared_quant / source_shared_int32_conditional

Graph: `sha256:cf74400ad99eb9177a9d35651f98f6b3ca9e7629abd5588d64b165a779b6894e`.

| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |
| --- | ---: | ---: | ---: | ---: | ---: |
| relative_15pct | 13 | 4 | 9 | 105 | 617 |
| absolute_15us | 5 | 3 | 2 | 81 | 99 |

### Large-call errors: observed mean > 50 us

| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SparseFlashAttention | relative_15pct | 78 | 78 | 0 | 1029.574 | 477.452 | 13199.665 | 6121.175 | -7078.489 | -53.6% | 0 / 1 |
| AddRmsNormBias | relative_15pct | 153 | 153 | 0 | 37.924 | 25.674 | 247.871 | 167.806 | -80.065 | -32.3% | 0 / 1 |
| QuantBatchMatmulV3 | relative_15pct | 255 | 150 | 0 | 23.893 | 12.204 | 159.284 | 81.363 | -77.921 | -48.9% | 0 / 2 |
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
| QuantBatchMatmulV3 | relative_15pct | 255 | 105 | 0 | 28.038 | 26.670 | 267.032 | 253.996 | -13.035 | -4.9% | 4 / 0 |

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
| MlaPrologV3 | 90fdb9a1f668 | 21 | reference_only | 1342.506 | 492.484 | -850.023 | - | reference_only | - |
| MlaPrologV3 | 72a02376f67d | 57 | reference_only | 1248.166 | 492.484 | -755.683 | - | reference_only | - |
| GroupedMatmulSwigluQuantV2 | 696b2089b11f | 75 | reference_only | 1323.133 | 600.414 | -722.719 | - | reference_only | - |
| LightningIndexer | 4a736fdbea06 | 21 | reference_only | 1492.464 | 1873.906 | 381.442 | - | reference_only | - |
| MoeGatingTopK | 529a9c65364b | 75 | reference_only | 101.699 | 13.462 | -88.237 | - | reference_only | - |
