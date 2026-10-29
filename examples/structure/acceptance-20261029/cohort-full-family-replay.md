# Complete Family And Physical-Cohort Replay

This completed historical replay uses **8 complete A3/A5 captures and 668,835 positive-duration events**, with 35 variants and 31 serial capture scans. No new NPU workload was launched.

Every valid tensor/physical-work cohort enters comparison. There is no operator-type allowlist. Different declarations reuse the same captures; their counts below are conditional comparisons, not independent hardware trials.

## Global Accuracy

| Observed complete-event mean | Criterion | Passed / compared cohorts | Failed |
| --- | --- | ---: | ---: |
| <= 50 us | Absolute per-call difference <= 15 us | 138 / 163 | 25 |
| > 50 us | Absolute relative error <= 15% | 81 / 314 | 233 |
| All scored | Each cohort's own tier | 219 / 477 | 258 |

**71 reference cohorts remain unscored.** The absolute tolerance does not change predictions or establish that launch overhead caused a residual. Family means are call-count weighted; cancellation of signed errors cannot turn a failed cohort into a pass.

## Complete Variant Results

| Declaration / variant | Cohort events | Scored events | Reference events | Passed / compared | Reference cohorts |
| --- | ---: | ---: | ---: | ---: | ---: |
| a3_glm53_prefill / source_declared_unfused_reference | 1,076 | 752 | 324 | 6 / 16 | 6 |
| a3_glm53_prefill / selected_native_fusion | 1,076 | 1,001 | 75 | 5 / 21 | 1 |
| a3_glm53_prefill_shared_quant / source_shared_int32_conditional | 1,226 | 902 | 324 | 7 / 18 | 6 |
| a3_glm53_decode / source_declared_unfused_reference | 79,624 | 55,648 | 23,976 | 15 / 16 | 6 |
| a3_glm53_decode / selected_native_fusion | 79,624 | 74,074 | 5,550 | 15 / 21 | 1 |
| a3_glm53_decode_shared_quant / source_shared_int32_conditional | 90,724 | 66,748 | 23,976 | 17 / 18 | 6 |
| a3_qwen35 / case_default | 3,442 | 762 | 2,680 | 5 / 14 | 1 |
| a3_qwen35_paged_prefill_q8192 / paged_body_geometry_conditional | 3,442 | 762 | 2,680 | 5 / 14 | 1 |
| a3_qwen35_paged_decode_q1 / paged_body_geometry_conditional | 2,749 | 69 | 2,680 | 1 / 1 | 1 |
| a3_qwen35_paged_decode_q2 / paged_body_geometry_conditional | 23,675 | 20,995 | 2,680 | 11 / 13 | 1 |
| a3_qwen36 / case_default | 1,330 | 1,330 | 0 | 7 / 15 | 0 |
| a3_qwen36_paged_prefill_q8192 / paged_body_geometry_conditional | 1,330 | 1,330 | 0 | 7 / 15 | 0 |
| a3_qwen36_paged_decode_q1 / paged_body_geometry_conditional | 87 | 87 | 0 | 1 / 2 | 0 |
| a3_qwen36_paged_decode_q4 / paged_body_geometry_conditional | 9,000 | 9,000 | 0 | 13 / 14 | 0 |
| a3_v4f / case_default | 813 | 660 | 153 | 2 / 17 | 3 |
| a3_v4f / selected_native_fusion | 813 | 748 | 65 | 2 / 18 | 2 |
| a3_v4f_compressor_fp32 / source_compressor_fp32_conditional_reference | 875 | 748 | 127 | 2 / 18 | 5 |
| a3_v4f_shared_quant / source_shared_int32_conditional | 901 | 748 | 153 | 3 / 19 | 3 |
| a3_v4pro / case_default | 4,580 | 3,716 | 864 | 7 / 16 | 3 |
| a3_v4pro / selected_native_fusion | 4,580 | 4,212 | 368 | 7 / 17 | 2 |
| a3_v4pro_compressor_fp32 / source_compressor_fp32_conditional_reference | 4,944 | 4,212 | 732 | 7 / 17 | 5 |
| a5_kimi_k3 / case_default | 439 | 439 | 0 | 0 / 3 | 0 |
| a5_kimi_k3_decode / source_declared_unfused_reference | 10,703 | 10,703 | 0 | 4 / 5 | 0 |
| a5_kimi_k3_checkpoint / current_checkpoint_conditional | 10,025 | 2,023 | 8,002 | 1 / 9 | 3 |
| a5_kimi_k3_decode_checkpoint / current_checkpoint_conditional | 66,328 | 43,469 | 22,859 | 6 / 8 | 4 |
| a5_kimi_k3_checkpoint_eager_single_group / source_single_group_mxfp8_conditional | 10,025 | 2,023 | 8,002 | 1 / 9 | 3 |
| a5_kimi_k3_decode_checkpoint_eager_single_group / source_single_group_mxfp8_conditional | 80,123 | 57,264 | 22,859 | 8 / 10 | 4 |
| a5_kimi_k3_checkpoint_eager_single_group_sp / source_sp_single_group_mxfp8_conditional | 11,133 | 2,763 | 8,370 | 3 / 12 | 4 |
| a5_qwen38 / case_default | 989 | 989 | 0 | 4 / 22 | 0 |
| a5_qwen38_steady / selected_steady_matrix_conditional | 989 | 989 | 0 | 11 / 22 | 0 |
| a5_qwen38_paged_prefill_q16384 / paged_body_geometry_conditional | 972 | 972 | 0 | 4 / 21 | 0 |
| a5_qwen38_paged_decode_q1 / paged_body_geometry_conditional | 61 | 61 | 0 | 1 / 2 | 0 |
| a5_qwen38_paged_decode_q4 / paged_body_geometry_conditional | 7,315 | 7,315 | 0 | 14 / 16 | 0 |
| a5_qwen38_paged_decode_q1_staged / source_paged_decode_program_conditional | 61 | 61 | 0 | 2 / 2 | 0 |
| a5_qwen38_paged_decode_q4_staged / source_paged_decode_program_conditional | 7,315 | 7,315 | 0 | 15 / 16 | 0 |

## Coverage And Interpretation

Paged attention uses independently declared query and cache-block geometry. Cache capacity does not establish active context, and query width does not identify verify or draft execution. Recurrent GDN retains exact state dtype. Sparse-attention buckets use observed index descriptors and independently declared layer structure; no event is duplicated between heterogeneous buckets within one declaration. Across declarations the same captured events can be reused; summed scored-event counts are not a unique-event coverage rate.

Source-selected shared INT32 quantization separates the accumulator producer from its dequantization/activation consumer. Compressor normalization references retain their missing native state-write/reuse boundary and stay outside accuracy counts. Kimi single-bank wrappers require their explicit source caller and execution domain. Missing routing/scalar/dispatch evidence remains visible in the unscored reasons.

All occurrence-level layer/replica/step identities remain unbound. Activity sums count overlapping events separately and are not model latency. Per-operator passes do not establish complete model coverage or end-to-end accuracy.

## Reproducibility

Full replay: 1414.439 seconds. Peak mapping 452.73 MiB; peak comparison 454.95 MiB. Runtime sources unchanged: True. Capture failures: 0; comparison failures: 0.

The [full replay receipt](fusion-cohort-validation.json) records capture SHA256, runtime source hashes, case declarations and program budgets. The [Top Errors](fusion-cohort-replay-top-errors.md), [large-call report](fusion-cohort-large-call-errors.md), and [complete family JSON index](fusion-cohort-replay-families.json) share this replay. See [maintained-suite verification](cohort-verification.json) and [independent review](fusion-cohort-independent-review.json) for their recorded runs.
