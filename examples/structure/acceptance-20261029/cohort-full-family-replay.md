# Complete Family And Physical-Cohort Replay

This partial historical replay uses **8 complete A3/A5 captures and 668,835 positive-duration events**, with 44 variants and 40 serial capture scans. No new NPU workload was launched.

Every valid tensor/physical-work cohort enters comparison. There is no operator-type allowlist. Different declarations reuse the same captures; their counts below are conditional comparisons, not independent hardware trials.

Prediction status: **failed**; 616 compared, 91 reference, 1 prediction-failed cohorts. Prediction failures remain outside the accuracy denominator; recorded timeout attempts remain in the full replay receipt.

## Global Accuracy

| Observed complete-event mean | Criterion | Passed / compared cohorts | Failed |
| --- | --- | ---: | ---: |
| <= 50 us | Absolute per-call difference <= 15 us | 168 / 198 | 30 |
| > 50 us | Absolute relative error <= 15% | 121 / 418 | 297 |
| All scored | Each cohort's own tier | 289 / 616 | 327 |

**91 reference cohorts remain unscored.** The absolute tolerance does not change predictions or establish that launch overhead caused a residual. Family means are call-count weighted; cancellation of signed errors cannot turn a failed cohort into a pass.

## Complete Variant Results

| Declaration / variant | Cohort events | Scored events | Reference events | Passed / compared | Reference cohorts |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_glm53_decode / source_declared_unfused_reference | 79,624 | 55,648 | 23,976 | 15 / 16 | 6 |
| a3_glm53_decode / selected_native_fusion | 79,624 | 74,074 | 5,550 | 15 / 21 | 1 |
| a3_glm53_decode_shared_quant / source_shared_int32_conditional | 90,724 | 66,748 | 23,976 | 17 / 18 | 6 |
| a3_glm53_decode_shared_quant_indexed_arch22 / source_shared_quant_indexed_arch22_conditional | 90,724 | 66,748 | 23,976 | 18 / 18 | 6 |
| a5_kimi_k3_decode / source_declared_unfused_reference | 10,703 | 10,703 | 0 | 4 / 5 | 0 |
| a5_kimi_k3_decode_checkpoint / current_checkpoint_conditional | 66,328 | 43,469 | 22,859 | 6 / 8 | 4 |
| a5_kimi_k3_decode_checkpoint_eager_single_group / source_single_group_mxfp8_conditional | 80,123 | 57,264 | 22,859 | 8 / 10 | 4 |
| a5_kimi_k3_decode_checkpoint_situ_arch35 / source_checkpoint_situ_arch35_conditional | 66,328 | 43,469 | 22,859 | 6 / 8 | 4 |
| a5_kimi_k3 / case_default | 439 | 439 | 0 | 0 / 3 | 0 |
| a5_kimi_k3_checkpoint / current_checkpoint_conditional | 10,025 | 2,023 | 8,002 | 1 / 9 | 3 |
| a5_kimi_k3_checkpoint_eager_single_group / source_single_group_mxfp8_conditional | 10,025 | 2,023 | 8,002 | 1 / 9 | 3 |
| a5_kimi_k3_checkpoint_eager_single_group_sp / source_sp_single_group_mxfp8_conditional | 11,133 | 2,763 | 8,370 | 3 / 12 | 4 |
| a5_kimi_k3_checkpoint_situ_arch35 / source_checkpoint_situ_arch35_conditional | 10,025 | 2,023 | 8,002 | 1 / 9 | 3 |
| a5_qwen38_paged_decode_q1 / paged_body_geometry_conditional | 61 | 61 | 0 | 1 / 2 | 0 |
| a5_qwen38_paged_decode_q4 / paged_body_geometry_conditional | 7,315 | 7,315 | 0 | 14 / 16 | 0 |
| a5_qwen38_paged_decode_q1_staged / source_paged_decode_program_conditional | 61 | 61 | 0 | 2 / 2 | 0 |
| a5_qwen38_paged_decode_q4_staged / source_paged_decode_program_conditional | 7,315 | 7,315 | 0 | 15 / 16 | 0 |
| a5_qwen38 / case_default | 989 | 989 | 0 | 4 / 22 | 0 |
| a5_qwen38_steady / selected_steady_matrix_conditional | 989 | 989 | 0 | 11 / 22 | 0 |
| a5_qwen38_paged_prefill_q16384 / paged_body_geometry_conditional | 972 | 972 | 0 | 4 / 21 | 0 |
| a5_qwen38_paged_prefill_combined / source_combined_prefill_conditional | 972 | 972 | 0 | 11 / 21 | 0 |
| a5_qwen38_contiguous_prefill_combined / source_combined_prefill_conditional | 989 | 972 | 0 | 11 / 21 | 0 |
| a3_qwen35_paged_decode_q1 / paged_body_geometry_conditional | 2,749 | 69 | 2,680 | 1 / 1 | 1 |
| a3_qwen35_paged_decode_q2 / paged_body_geometry_conditional | 23,675 | 20,995 | 2,680 | 11 / 13 | 1 |
| a3_qwen35 / case_default | 3,442 | 762 | 2,680 | 5 / 14 | 1 |
| a3_qwen35_paged_prefill_q8192 / paged_body_geometry_conditional | 3,442 | 762 | 2,680 | 5 / 14 | 1 |
| a3_qwen35_paged_prefill_staged / source_combined_prefill_conditional | 3,442 | 762 | 2,680 | 6 / 14 | 1 |
| a3_qwen36_paged_decode_q1 / paged_body_geometry_conditional | 87 | 87 | 0 | 1 / 2 | 0 |
| a3_qwen36_paged_decode_q4 / paged_body_geometry_conditional | 9,000 | 9,000 | 0 | 13 / 14 | 0 |
| a3_qwen36 / case_default | 1,330 | 1,330 | 0 | 7 / 15 | 0 |
| a3_qwen36_paged_prefill_q8192 / paged_body_geometry_conditional | 1,330 | 1,330 | 0 | 7 / 15 | 0 |
| a3_qwen36_paged_prefill_staged / source_combined_prefill_conditional | 1,330 | 1,330 | 0 | 8 / 15 | 0 |
| a3_v4f / case_default | 813 | 660 | 153 | 3 / 17 | 3 |
| a3_v4f / selected_native_fusion | 813 | 748 | 65 | 3 / 18 | 2 |
| a3_v4f_compressor_fp32 / source_compressor_fp32_conditional_reference | 875 | 748 | 127 | 3 / 18 | 5 |
| a3_v4f_shared_quant / source_shared_int32_conditional | 901 | 748 | 153 | 4 / 19 | 3 |
| a3_v4f_scfa / source_scfa_offchip_conditional | 813 | 660 | 153 | 3 / 17 | 3 |
| a3_v4pro / case_default | 4,580 | 3,716 | 864 | 6 / 16 | 3 |
| a3_v4pro / selected_native_fusion | 4,580 | 4,212 | 368 | 6 / 17 | 2 |
| a3_v4pro_compressor_fp32 / source_compressor_fp32_conditional_reference | 4,944 | 4,212 | 732 | 6 / 17 | 5 |
| a3_v4pro_scfa / source_scfa_offchip_conditional | 4,580 | 3,716 | 864 | 6 / 16 | 3 |
| a3_glm53_prefill / source_declared_unfused_reference | 1,076 | 752 | 324 | 6 / 16 | 6 |
| a3_glm53_prefill / selected_native_fusion | 1,076 | 1,001 | 75 | 4 / 21 | 1 |
| a3_glm53_prefill_shared_quant / source_shared_int32_conditional | 1,226 | 902 | 324 | 7 / 18 | 6 |

## Combined Prefill Recipe Coverage

These rows use the same declarations and cohorts as the complete table. Steady matmul applies to standalone projections; staged prefill owns its internal QK/PV work. Other body recipes remain selected as declared. Paged and contiguous tensor interfaces stay separate, including zero-match arms.

| Declaration | Native family | All capture events | Scored events | Passed / compared | Observed us/call | Predicted us/call | Per-call diff us |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| a5_qwen38_paged_prefill_combined | QuantBatchMatmulV3 | 1920 | 160 | 4 / 4 | 4464.419 | 4682.426 | 218.007 |
| a5_qwen38_paged_prefill_combined | MatMulV3 | 1956 | 184 | 4 / 4 | 2491.204 | 2564.751 | 73.547 |
| a5_qwen38_paged_prefill_combined | FusedInferAttentionScore | 228 | 0 | 0 / 0 | - | - | - |
| a5_qwen38_contiguous_prefill_combined | QuantBatchMatmulV3 | 1920 | 160 | 4 / 4 | 4464.419 | 4682.426 | 218.007 |
| a5_qwen38_contiguous_prefill_combined | MatMulV3 | 1956 | 184 | 4 / 4 | 2491.204 | 2564.751 | 73.547 |
| a5_qwen38_contiguous_prefill_combined | FusedInferAttentionScore | 228 | 0 | 0 / 0 | - | - | - |
| a3_qwen35_paged_prefill_staged | FusedInferAttentionScore | 737 | 11 | 1 / 1 | 2476.504 | 2733.286 | 256.782 |
| a3_qwen35_paged_prefill_staged | QuantBatchMatmulV3 | 670 | 20 | 1 / 1 | 232.983 | 225.850 | -7.133 |
| a3_qwen35_paged_prefill_staged | MatMulV3 | 144 | 0 | 0 / 0 | - | - | - |
| a3_qwen36_paged_prefill_staged | QuantBatchMatmulV3 | 3740 | 440 | 5 / 5 | 994.032 | 977.950 | -16.082 |
| a3_qwen36_paged_prefill_staged | FusedInferAttentionScore | 323 | 17 | 1 / 1 | 3678.352 | 4065.731 | 387.378 |
| a3_qwen36_paged_prefill_staged | MatMulV3 | 102 | 0 | 0 / 0 | - | - | - |

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

## Coverage And Interpretation

Paged attention uses independently declared query and cache-block geometry. Cache capacity does not establish active context, and query width does not identify verify or draft execution. Recurrent GDN retains exact state dtype. Sparse-attention buckets use observed index descriptors and independently declared layer structure; no event is duplicated between heterogeneous buckets within one declaration. Across declarations the same captured events can be reused; summed scored-event counts are not a unique-event coverage rate.

Source-selected shared INT32 quantization separates the accumulator producer from its dequantization/activation consumer. Compressor normalization references retain their missing native state-write/reuse boundary and stay outside accuracy counts. Kimi single-bank wrappers require their explicit source caller and execution domain. Missing routing/scalar/dispatch evidence remains visible in the unscored reasons.

Exported physical-work signatures describe semantic operator contracts. Predictions execute the selected recipe, whose staged transfer traffic can differ from that semantic work. Source selection is conditional and does not prove which binary dispatched the captured kernel.

All occurrence-level layer/replica/step identities remain unbound. Activity sums count overlapping events separately and are not model latency. Per-operator passes do not establish complete model coverage or end-to-end accuracy.

## Reproducibility

Full replay: 3265.525 seconds. Peak mapping 453.02 MiB; peak comparison 457.28 MiB. Runtime sources unchanged: True. Capture failures: 0; comparison failures: 1.

The [full replay receipt](fusion-cohort-validation.json) records capture SHA256, runtime source hashes, case declarations and program budgets. The [Top Errors](fusion-cohort-replay-top-errors.md), [large-call report](fusion-cohort-large-call-errors.md), and [complete family JSON index](fusion-cohort-replay-families.json) share this replay. See [maintained-suite verification](cohort-verification.json) and [independent review](fusion-cohort-independent-review.json) for their recorded runs.
