# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "18c423c7297fc3b3e92a5eb34f204df40a2a6cb6"}.

Variant: `glm-source-five`. Baseline: null.

Sim 0.8.0; 248 package files; SHA256 `53d85688e58a2aff06a970631aeb84a753e0b5f220fcde9b89cc952e631ee719`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | 49 | 69.360606 | 69.418407 | 69.527669 | 68.327418 | -1.49% | compared |
| a3_glm53flash_tp16_aclgraph_c32:q6_b12_m72 | 5 | 52.894180 | 53.227163 | 53.859016 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b1_m6 | 3 | 33.667439 | 33.175563 | 34.874096 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b24_m144 | 3 | 63.044113 | 62.507149 | 64.216403 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b16_m96 | 2 | 54.273544 | 54.273544 | 54.610131 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b8_m48 | 1 | 46.500390 | 46.500390 | 46.500390 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b6_m36 | 1 | 46.450648 | 46.450648 | 46.450648 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b2_m12 | 1 | 33.133282 | 33.133282 | 33.133282 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | 47 | 97.375106 | 97.486768 | 97.895096 | 104.087409 | +6.89% | compared |
| a3_glm53flash_tp16_aclgraph_c64:q6_b1_m6 | 6 | 33.161849 | 33.128011 | 33.585871 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b48_m288 | 3 | 80.931137 | 80.983779 | 82.029499 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b6_m36 | 3 | 45.865343 | 46.344766 | 46.510429 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b32_m192 | 2 | 68.165322 | 68.165322 | 68.192002 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b24_m144 | 2 | 61.995899 | 61.995899 | 62.736414 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b16_m96 | 2 | 53.912307 | 53.912307 | 54.034199 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b2_m12 | 2 | 33.439819 | 33.439819 | 34.072661 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b4_m24 | 1 | 37.485289 | 37.485289 | 37.485289 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b8_m48 | 1 | 46.552310 | 46.552310 | 46.552310 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 15.683328 | 15.670472 | 15.738329 | 9.956093 | -36.52% | compared |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 31 | 37.668964 | 37.665316 | 37.761150 | 28.492200 | -24.36% | compared |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | 2 | 37.705175 | 37.705175 | 37.843605 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | 2 | 37.467978 | 37.467978 | 38.254596 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | 1 | 38.396873 | 38.396873 | 38.396873 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | 1 | 38.002127 | 38.002127 | 38.002127 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 31 | 46.528233 | 46.498735 | 46.644535 | 38.276978 | -17.73% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
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
| glm53flash-a5-tp8-c1:q4_b1_m4 | 15.683328 | 15.421254 | 0.262074 | 1.67% | not_established | 8 / 1 / 1 | none / full |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 37.668964 | 37.413278 | 0.255686 | 0.68% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | 37.705175 | 37.429031 | 0.276145 | 0.73% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | 37.467978 | 37.200235 | 0.267743 | 0.71% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | 38.396873 | 38.137811 | 0.259062 | 0.67% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | 38.002127 | 37.736855 | 0.265272 | 0.70% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 46.528233 | 46.292617 | 0.235616 | 0.51% | not_established | 8 / 1 / 1 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | dense_layer | 0 / 3 | 0.901952 | 0.886134 | 0.953419 | 0.682324 | -24.35% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | moe_layer | 42 / 42 | 1.585782 | 1.326066 | 2.332666 | 1.578106 | -0.48% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | dense_layer | 0 / 3 | 1.307523 | 1.302391 | 1.323245 | 1.089395 | -16.68% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | moe_layer | 31 / 42 | 2.223835 | 1.764160 | 3.531813 | 2.400458 | +7.94% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | dense_layer | 0 / 3 | 0.306520 | 0.263452 | 0.422210 | 0.128580 | -58.05% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | moe_layer | 0 / 42 | 0.351495 | 0.302211 | 0.492130 | 0.227866 | -35.17% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | dense_layer | 0 / 3 | 0.397664 | 0.353061 | 0.487329 | 0.215949 | -45.70% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | moe_layer | 0 / 42 | 0.868453 | 0.754050 | 1.195816 | 0.662961 | -23.66% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | dense_layer | 0 / 3 | 0.496504 | 0.469962 | 0.550965 | 0.312614 | -37.04% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | moe_layer | 0 / 42 | 1.072327 | 0.889656 | 1.589585 | 0.889027 | -17.09% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | kda | 31 / 34 | 1.284063 | 1.318488 | 1.332471 | 1.152297 | -10.26% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | mla | 11 / 11 | 2.331870 | 2.330007 | 2.340216 | 2.649939 | +13.64% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | kda | 31 / 34 | 1.720878 | 1.759555 | 1.769474 | 1.611076 | -6.38% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | mla | 0 / 11 | 3.528525 | 3.530727 | 3.535698 | 4.482802 | +27.04% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 0 / 34 | 0.301047 | 0.298533 | 0.305713 | 0.205934 | -31.59% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0 / 11 | 0.495159 | 0.491361 | 0.512266 | 0.268575 | -45.76% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | kda | 0 / 34 | 0.720522 | 0.752286 | 0.755426 | 0.545283 | -24.32% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | mla | 0 / 11 | 1.197294 | 1.193753 | 1.212146 | 0.904781 | -24.43% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | kda | 0 / 34 | 0.853091 | 0.886410 | 0.892277 | 0.693640 | -18.69% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | mla | 0 / 11 | 1.592925 | 1.584140 | 1.613101 | 1.335747 | -16.15% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | kda | 1.284063 | 1.252331 | 0.031732 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | mla | 2.331870 | 2.294906 | 0.036964 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | kda | 1.720878 | 1.687860 | 0.033018 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | mla | 3.528525 | 3.490678 | 0.037847 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 0.301047 | 0.295812 | 0.005235 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0.495159 | 0.487604 | 0.007555 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | kda | 0.720522 | 0.715290 | 0.005232 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | mla | 1.197294 | 1.190310 | 0.006984 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | kda | 0.853091 | 0.848530 | 0.004561 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | mla | 1.592925 | 1.585690 | 0.007235 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | all | 44 | 2156 | 1.553529 | 1.327067 | 1.197778 | -9.74% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | kda | 33 | 1617 | 1.294083 | 1.320066 | 1.197778 | -9.26% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | mla | 11 | 539 | 2.331870 | 2.330967 | 2.649939 | +13.68% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | all | 44 | 2068 | 2.181827 | 1.764626 | 1.661561 | -5.84% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | kda | 33 | 1551 | 1.732927 | 1.762955 | 1.661561 | -5.75% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | mla | 11 | 517 | 3.528525 | 3.531911 | 4.482802 | +26.92% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | all | 44 | 2860 | 0.346822 | 0.301057 | 0.213420 | -29.11% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 33 | 2145 | 0.297376 | 0.298344 | 0.213420 | -28.47% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 11 | 715 | 0.495159 | 0.490270 | 0.268575 | -45.22% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | all | 44 | 1364 | 0.845015 | 0.753693 | 0.577154 | -23.42% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | kda | 33 | 1023 | 0.727589 | 0.752178 | 0.577154 | -23.27% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | mla | 11 | 341 | 1.197294 | 1.192474 | 0.904781 | -24.13% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | all | 44 | 1364 | 1.044916 | 0.888989 | 0.730514 | -17.83% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | kda | 33 | 1023 | 0.862246 | 0.886644 | 0.730514 | -17.61% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | mla | 11 | 341 | 1.592925 | 1.583919 | 1.335747 | -15.67% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | 49 | 0.953419 | 0.908198 | 0.956559 | 0.682324 | -28.43% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | 47 | 1.323245 | 1.322106 | 1.352347 | 1.089395 | -17.67% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 0.422210 | 0.438253 | 0.487926 | 0.128580 | -69.55% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 31 | 0.487329 | 0.462641 | 0.578271 | 0.215949 | -55.69% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 31 | 0.550965 | 0.529863 | 0.660172 | 0.312614 | -43.26% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
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
| glm53flash-a5-tp8-c1:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 1 | — | 8.534735 | — | 7.355036 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 4 | 32 | 128 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | 4 | 30 | 120 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | 4 | 24 | 96 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | 4 | 28 | 112 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | 4 | 26 | 104 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 4 | 64 | 256 | unknown | 4104 | 64 | — | 29.828263 | — | 19.944121 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
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
| glm53flash-a5-tp8-c1:q4_b1_m4 | embedding | 65 | 0.003436 | 0.003402 | 0.003777 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | output_head_preparation | 65 | 0.005408 | 0.005362 | 0.005811 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | final_norm | 65 | 0.034594 | 0.034528 | 0.035106 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | lm_head | 65 | 0.048571 | 0.048453 | 0.049677 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | embedding | 31 | 0.004420 | 0.004263 | 0.005508 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | output_head_preparation | 31 | 0.007529 | 0.007544 | 0.007864 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | final_norm | 31 | 0.039866 | 0.039788 | 0.040637 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | lm_head | 31 | 0.101230 | 0.101196 | 0.101962 |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | embedding | 2 | 0.004957 | 0.004957 | 0.005440 |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | output_head_preparation | 2 | 0.010142 | 0.010142 | 0.010215 |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | final_norm | 2 | 0.039856 | 0.039856 | 0.040493 |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | lm_head | 2 | 0.098706 | 0.098706 | 0.099093 |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | embedding | 2 | 0.003968 | 0.003968 | 0.004134 |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | output_head_preparation | 2 | 0.007030 | 0.007030 | 0.007152 |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | final_norm | 2 | 0.039509 | 0.039509 | 0.039903 |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | lm_head | 2 | 0.095435 | 0.095435 | 0.095630 |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | embedding | 1 | 0.004301 | 0.004301 | 0.004301 |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | output_head_preparation | 1 | 0.007747 | 0.007747 | 0.007747 |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | final_norm | 1 | 0.039215 | 0.039215 | 0.039215 |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | lm_head | 1 | 0.098549 | 0.098549 | 0.098549 |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | embedding | 1 | 0.006187 | 0.006187 | 0.006187 |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | output_head_preparation | 1 | 0.007494 | 0.007494 | 0.007494 |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | final_norm | 1 | 0.040265 | 0.040265 | 0.040265 |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | lm_head | 1 | 0.096024 | 0.096024 | 0.096024 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | embedding | 31 | 0.005153 | 0.004906 | 0.006278 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | output_head_preparation | 31 | 0.009403 | 0.009451 | 0.009728 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | final_norm | 31 | 0.040726 | 0.040693 | 0.041491 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | lm_head | 31 | 0.107919 | 0.107887 | 0.108171 |

Summary: {"case_count": 25, "compared_cases": 5, "failed_cases": 0, "measured_cases": 25, "passed_cases": 2, "source_case_count": 5, "unresolved_cases": 20}
