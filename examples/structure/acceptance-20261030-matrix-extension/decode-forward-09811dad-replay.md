# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "09811dad268203b6d021e01715b1c245d877c40f"}.

Variant: `source-bound-latest-defaults-09811dad`. Baseline: {"basis": "same measured source and geometry; source-bound Sim cases with current defaults"}.

Sim 0.8.0; 228 package files; SHA256 `57d40b5b746923be0f725879f83825c3d4e428230ab72fa9bf920c0fde5d3360`; package `/Users/maoxx241/code/sim-rewrite-20261027/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | 50 | 53.893389 | 53.870786 | 54.020920 | 46.557395 | -13.61% | compared |
| a3_glm53flash_tp16_aclgraph_c16:q6_b1_m6 | 4 | 33.477328 | 33.400787 | 33.975338 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c16:q6_b12_m72 | 4 | 52.671202 | 52.568690 | 53.565410 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c16:q6_b2_m12 | 3 | 33.945585 | 33.337166 | 35.257205 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c16:q6_b8_m48 | 2 | 47.322035 | 47.322035 | 48.209823 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c16:q6_b4_m24 | 1 | 39.385447 | 39.385447 | 39.385447 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c16:q6_b6_m36 | 1 | 45.421267 | 45.421267 | 45.421267 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | 49 | 69.360606 | 69.418407 | 69.527669 | 57.412048 | -17.23% | compared |
| a3_glm53flash_tp16_aclgraph_c32:q6_b12_m72 | 5 | 52.894180 | 53.227163 | 53.859016 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b1_m6 | 3 | 33.667439 | 33.175563 | 34.874096 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b24_m144 | 3 | 63.044113 | 62.507149 | 64.216403 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b16_m96 | 2 | 54.273544 | 54.273544 | 54.610131 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b8_m48 | 1 | 46.500390 | 46.500390 | 46.500390 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b6_m36 | 1 | 46.450648 | 46.450648 | 46.450648 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b2_m12 | 1 | 33.133282 | 33.133282 | 33.133282 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | 47 | 97.375106 | 97.486768 | 97.895096 | 79.098947 | -18.77% | compared |
| a3_glm53flash_tp16_aclgraph_c64:q6_b1_m6 | 6 | 33.161849 | 33.128011 | 33.585871 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b48_m288 | 3 | 80.931137 | 80.983779 | 82.029499 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b6_m36 | 3 | 45.865343 | 46.344766 | 46.510429 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b32_m192 | 2 | 68.165322 | 68.165322 | 68.192002 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b24_m144 | 2 | 61.995899 | 61.995899 | 62.736414 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b16_m96 | 2 | 53.912307 | 53.912307 | 54.034199 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b2_m12 | 2 | 33.439819 | 33.439819 | 34.072661 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b4_m24 | 1 | 37.485289 | 37.485289 | 37.485289 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b8_m48 | 1 | 46.552310 | 46.552310 | 46.552310 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | 47 | 46.859200 | 46.817395 | 47.174542 | 40.675865 | -13.20% | compared |
| a3_glm53flash_tp16_aclgraph_c8:q6_b1_m6 | 6 | 33.544533 | 33.104051 | 34.939998 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c8:q6_b4_m24 | 4 | 37.952883 | 37.467638 | 39.614791 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c8:q6_b6_m36 | 3 | 45.218403 | 44.930438 | 46.273504 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c8:q6_b2_m12 | 2 | 34.030780 | 34.030780 | 34.633912 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 129 | 14.929338 | 14.914454 | 14.928722 | 9.648726 | -35.37% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 105 | 18.624557 | 18.615864 | 18.640311 | 12.480063 | -32.99% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 151 | 13.238803 | 13.208635 | 13.227353 | 8.200338 | -38.06% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | 53.893389 | 52.393173 | 1.500215 | 2.78% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c16:q6_b1_m6 | 33.477328 | 32.045087 | 1.432241 | 4.28% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c16:q6_b12_m72 | 52.671202 | 51.119017 | 1.552185 | 2.95% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c16:q6_b2_m12 | 33.945585 | 32.452642 | 1.492943 | 4.40% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c16:q6_b8_m48 | 47.322035 | 45.831987 | 1.490048 | 3.15% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c16:q6_b4_m24 | 39.385447 | 37.860052 | 1.525395 | 3.87% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c16:q6_b6_m36 | 45.421267 | 43.892742 | 1.528525 | 3.37% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | 69.360606 | 67.823207 | 1.537399 | 2.22% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c32:q6_b12_m72 | 52.894180 | 51.338013 | 1.556167 | 2.94% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c32:q6_b1_m6 | 33.667439 | 32.243169 | 1.424270 | 4.23% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c32:q6_b24_m144 | 63.044113 | 61.537222 | 1.506891 | 2.39% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c32:q6_b16_m96 | 54.273544 | 52.775613 | 1.497931 | 2.76% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c32:q6_b8_m48 | 46.500390 | 45.014972 | 1.485418 | 3.19% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c32:q6_b6_m36 | 46.450648 | 44.842757 | 1.607891 | 3.46% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c32:q6_b2_m12 | 33.133282 | 31.644657 | 1.488625 | 4.49% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | 97.375106 | 95.784705 | 1.590400 | 1.63% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c64:q6_b1_m6 | 33.161849 | 31.725255 | 1.436594 | 4.33% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c64:q6_b48_m288 | 80.931137 | 79.324681 | 1.606456 | 1.98% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c64:q6_b6_m36 | 45.865343 | 44.283253 | 1.582090 | 3.45% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c64:q6_b32_m192 | 68.165322 | 66.526217 | 1.639105 | 2.40% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c64:q6_b24_m144 | 61.995899 | 60.453719 | 1.542180 | 2.49% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c64:q6_b16_m96 | 53.912307 | 52.370694 | 1.541613 | 2.86% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c64:q6_b2_m12 | 33.439819 | 31.949244 | 1.490575 | 4.46% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c64:q6_b4_m24 | 37.485289 | 35.971403 | 1.513886 | 4.04% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c64:q6_b8_m48 | 46.552310 | 45.063035 | 1.489275 | 3.20% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | 46.859200 | 45.372203 | 1.486998 | 3.17% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c8:q6_b1_m6 | 33.544533 | 32.110033 | 1.434500 | 4.28% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c8:q6_b4_m24 | 37.952883 | 36.433268 | 1.519615 | 4.00% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c8:q6_b6_m36 | 45.218403 | 43.681619 | 1.536785 | 3.40% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53flash_tp16_aclgraph_c8:q6_b2_m12 | 34.030780 | 32.538886 | 1.491894 | 4.38% | not_established | 16 / 1 / 16 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 14.929338 | 14.831607 | 0.097731 | 0.65% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 18.624557 | 18.525544 | 0.099013 | 0.53% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 13.238803 | 13.143250 | 0.095554 | 0.72% | not_established | 1 / 8 / 8 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | dense_layer | 0 / 3 | 0.667246 | 0.669540 | 0.689545 | 0.485046 | -27.31% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | moe_layer | 31 / 42 | 1.234289 | 1.077833 | 1.688344 | 1.073863 | -13.00% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | dense_layer | 0 / 3 | 0.901952 | 0.886134 | 0.953419 | 0.682198 | -24.36% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | moe_layer | 31 / 42 | 1.585782 | 1.326066 | 2.332666 | 1.318225 | -16.87% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | dense_layer | 0 / 3 | 1.307523 | 1.302391 | 1.323245 | 1.089202 | -16.70% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | moe_layer | 31 / 42 | 2.223835 | 1.764160 | 3.531813 | 1.805508 | -18.81% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | dense_layer | 0 / 3 | 0.623883 | 0.618011 | 0.641189 | 0.401123 | -35.71% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | moe_layer | 31 / 42 | 1.069907 | 0.952253 | 1.409976 | 0.939821 | -12.16% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | moe_layer | 1 / 40 | 0.373173 | 0.352684 | 0.435251 | 0.241218 | -35.36% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | moe_layer | 1 / 40 | 0.465552 | 0.444202 | 0.534740 | 0.312002 | -32.98% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | moe_layer | 1 / 40 | 0.330911 | 0.300274 | 0.378501 | 0.205008 | -38.05% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | kda | 31 / 34 | 1.038076 | 1.073693 | 1.083795 | 0.978717 | -5.72% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | mla | 0 / 11 | 1.686116 | 1.687182 | 1.691235 | 1.207365 | -28.39% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | kda | 31 / 34 | 1.284063 | 1.318488 | 1.332471 | 1.188880 | -7.41% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | mla | 0 / 11 | 2.331870 | 2.330007 | 2.340216 | 1.544558 | -33.76% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | kda | 31 / 34 | 1.720878 | 1.759555 | 1.769474 | 1.610882 | -6.39% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | mla | 0 / 11 | 3.528525 | 3.530727 | 3.535698 | 2.211723 | -37.32% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | kda | 31 / 34 | 0.920568 | 0.947606 | 0.957843 | 0.863497 | -6.20% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | mla | 0 / 11 | 1.409856 | 1.409699 | 1.416413 | 1.028816 | -27.03% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | mla | 1 / 40 | 0.373173 | 0.352684 | 0.435251 | 0.241218 | -35.36% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 1 / 40 | 0.465552 | 0.444202 | 0.534740 | 0.312002 | -32.98% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 1 / 40 | 0.330911 | 0.300274 | 0.378501 | 0.205008 | -38.05% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | kda | 1.038076 | 1.007952 | 0.030124 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | mla | 1.686116 | 1.647526 | 0.038590 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | kda | 1.284063 | 1.252331 | 0.031732 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | mla | 2.331870 | 2.294906 | 0.036964 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | kda | 1.720878 | 1.687860 | 0.033018 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | mla | 3.528525 | 3.490678 | 0.037847 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | kda | 0.920568 | 0.890728 | 0.029840 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | mla | 1.409856 | 1.371585 | 0.038270 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | mla | 0.373173 | 0.370790 | 0.002383 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 0.465552 | 0.463139 | 0.002414 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 0.330911 | 0.328581 | 0.002330 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | all | 44 | 2200 | 1.208007 | 1.076586 | 1.026492 | -4.65% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | kda | 33 | 1650 | 1.048638 | 1.073441 | 1.026492 | -4.37% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | mla | 11 | 550 | 1.686116 | 1.686414 | 1.207365 | -28.41% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | all | 44 | 2156 | 1.553529 | 1.327067 | 1.237914 | -6.72% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | kda | 33 | 1617 | 1.294083 | 1.320066 | 1.237914 | -6.22% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | mla | 11 | 539 | 2.331870 | 2.330967 | 1.544558 | -33.74% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | all | 44 | 2068 | 2.181827 | 1.764626 | 1.661367 | -5.85% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | kda | 33 | 1551 | 1.732927 | 1.762955 | 1.661367 | -5.76% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | mla | 11 | 517 | 3.528525 | 3.531911 | 2.211723 | -37.38% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | all | 44 | 2068 | 1.049240 | 0.951629 | 0.908242 | -4.56% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | kda | 33 | 1551 | 0.929034 | 0.947759 | 0.908242 | -4.17% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | mla | 11 | 517 | 1.409856 | 1.407188 | 1.028816 | -26.89% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | all | 39 | 5031 | 0.371581 | 0.352624 | 0.231626 | -34.31% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | mla | 39 | 5031 | 0.371581 | 0.352624 | 0.231626 | -34.31% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | all | 39 | 4095 | 0.463953 | 0.444058 | 0.302293 | -31.92% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 39 | 4095 | 0.463953 | 0.444058 | 0.302293 | -31.92% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | all | 39 | 5889 | 0.317677 | 0.300299 | 0.195475 | -34.91% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 39 | 5889 | 0.317677 | 0.300299 | 0.195475 | -34.91% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | 50 | 0.689545 | 0.668883 | 0.733735 | 0.485046 | -29.66% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | 49 | 0.953419 | 0.908198 | 0.956559 | 0.682198 | -28.45% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | 47 | 1.323245 | 1.322106 | 1.352347 | 1.089202 | -17.69% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | 47 | 0.641189 | 0.581011 | 0.861818 | 0.401123 | -37.44% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 129 | 0.435251 | 0.420089 | 0.424730 | 0.231626 | -46.78% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 105 | 0.527918 | 0.520862 | 0.527346 | 0.302293 | -42.74% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 151 | 0.847040 | 0.816238 | 0.820195 | 0.195475 | -76.92% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | 6 | 16 | 96 | unknown | 4096 | 16 | — | 70.241911 | — | — |
| a3_glm53flash_tp16_aclgraph_c16:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 16 | — | 70.241911 | — | — |
| a3_glm53flash_tp16_aclgraph_c16:q6_b12_m72 | 6 | 12 | 72 | unknown | 4096 | 16 | — | 70.241911 | — | — |
| a3_glm53flash_tp16_aclgraph_c16:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 16 | — | 70.241911 | — | — |
| a3_glm53flash_tp16_aclgraph_c16:q6_b8_m48 | 6 | 8 | 48 | unknown | 4096 | 16 | — | 70.241911 | — | — |
| a3_glm53flash_tp16_aclgraph_c16:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 16 | — | 70.241911 | — | — |
| a3_glm53flash_tp16_aclgraph_c16:q6_b6_m36 | 6 | 6 | 36 | unknown | 4096 | 16 | — | 70.241911 | — | — |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | 6 | 32 | 192 | unknown | 4096 | 32 | — | 92.211155 | — | — |
| a3_glm53flash_tp16_aclgraph_c32:q6_b12_m72 | 6 | 12 | 72 | unknown | 4096 | 32 | — | 92.211155 | — | — |
| a3_glm53flash_tp16_aclgraph_c32:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 32 | — | 92.211155 | — | — |
| a3_glm53flash_tp16_aclgraph_c32:q6_b24_m144 | 6 | 24 | 144 | unknown | 4096 | 32 | — | 92.211155 | — | — |
| a3_glm53flash_tp16_aclgraph_c32:q6_b16_m96 | 6 | 16 | 96 | unknown | 4096 | 32 | — | 92.211155 | — | — |
| a3_glm53flash_tp16_aclgraph_c32:q6_b8_m48 | 6 | 8 | 48 | unknown | 4096 | 32 | — | 92.211155 | — | — |
| a3_glm53flash_tp16_aclgraph_c32:q6_b6_m36 | 6 | 6 | 36 | unknown | 4096 | 32 | — | 92.211155 | — | — |
| a3_glm53flash_tp16_aclgraph_c32:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 32 | — | 92.211155 | — | — |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | 6 | 64 | 384 | unknown | 4096 | 64 | — | 301.643190 | — | — |
| a3_glm53flash_tp16_aclgraph_c64:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 64 | — | 301.643190 | — | — |
| a3_glm53flash_tp16_aclgraph_c64:q6_b48_m288 | 6 | 48 | 288 | unknown | 4096 | 64 | — | 301.643190 | — | — |
| a3_glm53flash_tp16_aclgraph_c64:q6_b6_m36 | 6 | 6 | 36 | unknown | 4096 | 64 | — | 301.643190 | — | — |
| a3_glm53flash_tp16_aclgraph_c64:q6_b32_m192 | 6 | 32 | 192 | unknown | 4096 | 64 | — | 301.643190 | — | — |
| a3_glm53flash_tp16_aclgraph_c64:q6_b24_m144 | 6 | 24 | 144 | unknown | 4096 | 64 | — | 301.643190 | — | — |
| a3_glm53flash_tp16_aclgraph_c64:q6_b16_m96 | 6 | 16 | 96 | unknown | 4096 | 64 | — | 301.643190 | — | — |
| a3_glm53flash_tp16_aclgraph_c64:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 64 | — | 301.643190 | — | — |
| a3_glm53flash_tp16_aclgraph_c64:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 64 | — | 301.643190 | — | — |
| a3_glm53flash_tp16_aclgraph_c64:q6_b8_m48 | 6 | 8 | 48 | unknown | 4096 | 64 | — | 301.643190 | — | — |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | 6 | 8 | 48 | unknown | 4096 | 8 | — | 60.274800 | — | — |
| a3_glm53flash_tp16_aclgraph_c8:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 8 | — | 60.274800 | — | — |
| a3_glm53flash_tp16_aclgraph_c8:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 8 | — | 60.274800 | — | — |
| a3_glm53flash_tp16_aclgraph_c8:q6_b6_m36 | 6 | 6 | 36 | unknown | 4096 | 8 | — | 60.274800 | — | — |
| a3_glm53flash_tp16_aclgraph_c8:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 8 | — | 60.274800 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 1 | 2 | 2 | unknown | 2048 | 16 | 21.239293 | 20.616566 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 1 | 4 | 4 | unknown | 2048 | 32 | 22.363334 | 22.393036 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 1 | 1 | 1 | unknown | 2048 | 4 | 16.557655 | 16.561941 | — | — |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | embedding | 50 | 0.008971 | 0.008830 | 0.009260 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | output_head_preparation | 50 | 0.009624 | 0.009650 | 0.009840 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | final_norm | 50 | 0.153281 | 0.153053 | 0.154503 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | lm_head | 50 | 0.130576 | 0.130993 | 0.132343 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b1_m6 | embedding | 4 | 0.003365 | 0.003420 | 0.003560 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b1_m6 | output_head_preparation | 4 | 0.010750 | 0.010710 | 0.011000 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b1_m6 | final_norm | 4 | 0.134253 | 0.130733 | 0.147263 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b1_m6 | lm_head | 4 | 0.090591 | 0.090471 | 0.091842 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b12_m72 | embedding | 4 | 0.008836 | 0.008751 | 0.010000 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b12_m72 | output_head_preparation | 4 | 0.009421 | 0.009421 | 0.009581 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b12_m72 | final_norm | 4 | 0.149903 | 0.149593 | 0.151263 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b12_m72 | lm_head | 4 | 0.122997 | 0.123902 | 0.125002 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b2_m12 | embedding | 3 | 0.004067 | 0.004080 | 0.004200 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b2_m12 | output_head_preparation | 3 | 0.010820 | 0.010541 | 0.011460 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b2_m12 | final_norm | 3 | 0.132656 | 0.132703 | 0.132782 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b2_m12 | lm_head | 3 | 0.103975 | 0.104142 | 0.104602 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b8_m48 | embedding | 2 | 0.005821 | 0.005821 | 0.006001 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b8_m48 | output_head_preparation | 2 | 0.007690 | 0.007690 | 0.007740 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b8_m48 | final_norm | 2 | 0.146183 | 0.146183 | 0.146203 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b8_m48 | lm_head | 2 | 0.120952 | 0.120952 | 0.121283 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b4_m24 | embedding | 1 | 0.005440 | 0.005440 | 0.005440 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b4_m24 | output_head_preparation | 1 | 0.009000 | 0.009000 | 0.009000 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b4_m24 | final_norm | 1 | 0.137263 | 0.137263 | 0.137263 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b4_m24 | lm_head | 1 | 0.104742 | 0.104742 | 0.104742 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b6_m36 | embedding | 1 | 0.009461 | 0.009461 | 0.009461 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b6_m36 | output_head_preparation | 1 | 0.011721 | 0.011721 | 0.011721 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b6_m36 | final_norm | 1 | 0.149603 | 0.149603 | 0.149603 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b6_m36 | lm_head | 1 | 0.116242 | 0.116242 | 0.116242 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | embedding | 49 | 0.010883 | 0.010860 | 0.011320 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | output_head_preparation | 49 | 0.012675 | 0.012660 | 0.013000 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | final_norm | 49 | 0.159989 | 0.159803 | 0.160843 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | lm_head | 49 | 0.176423 | 0.176543 | 0.178724 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b12_m72 | embedding | 5 | 0.009100 | 0.009740 | 0.009880 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b12_m72 | output_head_preparation | 5 | 0.009488 | 0.009480 | 0.009640 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b12_m72 | final_norm | 5 | 0.151811 | 0.151203 | 0.155543 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b12_m72 | lm_head | 5 | 0.122899 | 0.123243 | 0.125342 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b1_m6 | embedding | 3 | 0.003367 | 0.003500 | 0.003500 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b1_m6 | output_head_preparation | 3 | 0.010434 | 0.010420 | 0.010600 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b1_m6 | final_norm | 3 | 0.163557 | 0.133062 | 0.229225 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b1_m6 | lm_head | 3 | 0.091415 | 0.091422 | 0.092041 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b24_m144 | embedding | 3 | 0.009700 | 0.009780 | 0.009840 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b24_m144 | output_head_preparation | 3 | 0.011694 | 0.011720 | 0.011940 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b24_m144 | final_norm | 3 | 0.156297 | 0.155604 | 0.157903 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b24_m144 | lm_head | 3 | 0.167596 | 0.167383 | 0.168283 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b16_m96 | embedding | 2 | 0.008941 | 0.008941 | 0.009181 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b16_m96 | output_head_preparation | 2 | 0.009610 | 0.009610 | 0.009620 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b16_m96 | final_norm | 2 | 0.155983 | 0.155983 | 0.158504 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b16_m96 | lm_head | 2 | 0.130562 | 0.130562 | 0.131062 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b8_m48 | embedding | 1 | 0.005740 | 0.005740 | 0.005740 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b8_m48 | output_head_preparation | 1 | 0.007320 | 0.007320 | 0.007320 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b8_m48 | final_norm | 1 | 0.146903 | 0.146903 | 0.146903 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b8_m48 | lm_head | 1 | 0.120182 | 0.120182 | 0.120182 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b6_m36 | embedding | 1 | 0.010260 | 0.010260 | 0.010260 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b6_m36 | output_head_preparation | 1 | 0.012141 | 0.012141 | 0.012141 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b6_m36 | final_norm | 1 | 0.155423 | 0.155423 | 0.155423 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b6_m36 | lm_head | 1 | 0.125082 | 0.125082 | 0.125082 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b2_m12 | embedding | 1 | 0.004020 | 0.004020 | 0.004020 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b2_m12 | output_head_preparation | 1 | 0.011020 | 0.011020 | 0.011020 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b2_m12 | final_norm | 1 | 0.132503 | 0.132503 | 0.132503 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b2_m12 | lm_head | 1 | 0.102922 | 0.102922 | 0.102922 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | embedding | 47 | 0.011467 | 0.011261 | 0.013060 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | output_head_preparation | 47 | 0.018294 | 0.018241 | 0.018540 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | final_norm | 47 | 0.162928 | 0.162663 | 0.164083 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | lm_head | 47 | 0.207129 | 0.207104 | 0.211684 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b1_m6 | embedding | 6 | 0.003210 | 0.003210 | 0.003480 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b1_m6 | output_head_preparation | 6 | 0.010687 | 0.010641 | 0.011100 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b1_m6 | final_norm | 6 | 0.130526 | 0.130432 | 0.133583 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b1_m6 | lm_head | 6 | 0.091835 | 0.091882 | 0.093881 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b48_m288 | embedding | 3 | 0.010867 | 0.009920 | 0.012980 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b48_m288 | output_head_preparation | 3 | 0.015947 | 0.015880 | 0.016100 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b48_m288 | final_norm | 3 | 0.167943 | 0.166603 | 0.171563 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b48_m288 | lm_head | 3 | 0.184737 | 0.183464 | 0.190484 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b6_m36 | embedding | 3 | 0.009440 | 0.009720 | 0.009860 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b6_m36 | output_head_preparation | 3 | 0.011774 | 0.011860 | 0.012120 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b6_m36 | final_norm | 3 | 0.149756 | 0.149743 | 0.151363 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b6_m36 | lm_head | 3 | 0.120916 | 0.121942 | 0.123003 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b32_m192 | embedding | 2 | 0.009820 | 0.009820 | 0.009860 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b32_m192 | output_head_preparation | 2 | 0.012650 | 0.012650 | 0.012720 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b32_m192 | final_norm | 2 | 0.165324 | 0.165324 | 0.166623 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b32_m192 | lm_head | 2 | 0.177233 | 0.177233 | 0.181024 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b24_m144 | embedding | 2 | 0.010830 | 0.010830 | 0.010980 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b24_m144 | output_head_preparation | 2 | 0.011760 | 0.011760 | 0.012020 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b24_m144 | final_norm | 2 | 0.158693 | 0.158693 | 0.160963 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b24_m144 | lm_head | 2 | 0.140023 | 0.140023 | 0.141343 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b16_m96 | embedding | 2 | 0.009500 | 0.009500 | 0.010721 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b16_m96 | output_head_preparation | 2 | 0.009820 | 0.009820 | 0.009920 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b16_m96 | final_norm | 2 | 0.158264 | 0.158264 | 0.158444 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b16_m96 | lm_head | 2 | 0.128082 | 0.128082 | 0.128942 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b2_m12 | embedding | 2 | 0.004450 | 0.004450 | 0.004560 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b2_m12 | output_head_preparation | 2 | 0.011380 | 0.011380 | 0.011580 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b2_m12 | final_norm | 2 | 0.133003 | 0.133003 | 0.133843 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b2_m12 | lm_head | 2 | 0.103882 | 0.103882 | 0.104322 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b4_m24 | embedding | 1 | 0.005300 | 0.005300 | 0.005300 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b4_m24 | output_head_preparation | 1 | 0.008540 | 0.008540 | 0.008540 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b4_m24 | final_norm | 1 | 0.137463 | 0.137463 | 0.137463 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b4_m24 | lm_head | 1 | 0.104982 | 0.104982 | 0.104982 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b8_m48 | embedding | 1 | 0.006920 | 0.006920 | 0.006920 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b8_m48 | output_head_preparation | 1 | 0.007280 | 0.007280 | 0.007280 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b8_m48 | final_norm | 1 | 0.145363 | 0.145363 | 0.145363 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b8_m48 | lm_head | 1 | 0.123543 | 0.123543 | 0.123543 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | embedding | 47 | 0.006626 | 0.006680 | 0.006840 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | output_head_preparation | 47 | 0.007581 | 0.007620 | 0.007760 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | final_norm | 47 | 0.146343 | 0.146243 | 0.147023 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | lm_head | 47 | 0.123969 | 0.124142 | 0.125343 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b1_m6 | embedding | 6 | 0.003083 | 0.003020 | 0.003320 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b1_m6 | output_head_preparation | 6 | 0.010741 | 0.010670 | 0.011140 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b1_m6 | final_norm | 6 | 0.149999 | 0.130412 | 0.249845 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b1_m6 | lm_head | 6 | 0.091615 | 0.091272 | 0.093702 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b4_m24 | embedding | 4 | 0.005841 | 0.005490 | 0.007021 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b4_m24 | output_head_preparation | 4 | 0.008635 | 0.008581 | 0.008880 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b4_m24 | final_norm | 4 | 0.138158 | 0.137643 | 0.139943 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b4_m24 | lm_head | 4 | 0.106197 | 0.104382 | 0.112282 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b6_m36 | embedding | 3 | 0.009054 | 0.008740 | 0.009881 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b6_m36 | output_head_preparation | 3 | 0.011567 | 0.011281 | 0.012461 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b6_m36 | final_norm | 3 | 0.146863 | 0.146503 | 0.148063 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b6_m36 | lm_head | 3 | 0.119442 | 0.118922 | 0.121122 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b2_m12 | embedding | 2 | 0.004120 | 0.004120 | 0.004160 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b2_m12 | output_head_preparation | 2 | 0.010621 | 0.010621 | 0.010941 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b2_m12 | final_norm | 2 | 0.132822 | 0.132822 | 0.133182 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b2_m12 | lm_head | 2 | 0.102852 | 0.102852 | 0.103382 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | embedding | 129 | 0.003381 | 0.003336 | 0.003618 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | output_head_preparation | 129 | 0.014962 | 0.014987 | 0.015300 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | final_norm | 129 | 0.002669 | 0.002646 | 0.002780 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | embedding | 105 | 0.004095 | 0.004051 | 0.004470 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | output_head_preparation | 105 | 0.016335 | 0.016280 | 0.016827 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | final_norm | 105 | 0.002770 | 0.002767 | 0.002848 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | output_head_preparation | 151 | 0.013937 | 0.013868 | 0.014536 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | final_norm | 151 | 0.002446 | 0.002420 | 0.002571 |

Summary: {"case_count": 33, "compared_cases": 7, "failed_cases": 0, "measured_cases": 33, "passed_cases": 2, "source_case_count": 7, "unresolved_cases": 26}
