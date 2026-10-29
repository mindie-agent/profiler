# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "d9118c6e71ed9c75362c06fc7063be4ab97317ec"}.

Variant: `priority_legacy_glm_qwen_system_checks_d9118c6e`. Baseline: null.

Sim 0.8.0; 221 package files; SHA256 `5d7c051180a936039cadc42d39e1d3e7a993d652b322c105b16219de135d5ac6`; package `/Users/maoxx241/code/sim-rewrite-20261027/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a3_glm53_dc4k_b1:q1_b1_m1 | 74 | 38.954827 | 38.942772 | 39.036040 | 36.960603 | -5.12% | compared |
| a3_glm53_dc4k_b2:q1_b2_m2 | 70 | 40.969878 | 40.934812 | 41.046340 | 48.792423 | +19.09% | compared |
| a3_glm53_dc4k_b4:q1_b4_m4 | 67 | 43.437734 | 43.436892 | 43.597669 | 72.002182 | +65.76% | compared |
| a3_glm53_dc4k_b8:q1_b8_m8 | 61 | 47.113275 | 47.148578 | 47.401813 | 116.778952 | +147.87% | compared |
| a3_glm53_dc16k_b1:q1_b1_m1 | 74 | 39.112085 | 39.104879 | 39.195917 | 36.960603 | -5.50% | compared |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 23 | 76.089008 | 76.132320 | 76.632160 | 512.836482 | +574.00% | compared |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 18 | 119.054350 | 119.130970 | 119.486280 | 1404.679354 | +1079.86% | compared |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | 79 | 21.956845 | 22.000889 | 22.067637 | 10.219090 | -53.46% | compared |
| qwen35-35b-a5-tp4-c64-graph:q4_b1_m4 | 3 | 8.738856 | 8.827963 | 8.913333 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b60_m240 | 1 | 21.444033 | 21.444033 | 21.444033 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b56_m224 | 1 | 20.971886 | 20.971886 | 20.971886 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b52_m208 | 1 | 20.949956 | 20.949956 | 20.949956 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b48_m192 | 1 | 20.070326 | 20.070326 | 20.070326 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b44_m176 | 1 | 20.103043 | 20.103043 | 20.103043 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b40_m160 | 1 | 19.908259 | 19.908259 | 19.908259 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b34_m136 | 1 | 19.148523 | 19.148523 | 19.148523 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b26_m104 | 1 | 16.773756 | 16.773756 | 16.773756 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b18_m72 | 1 | 15.809891 | 15.809891 | 15.809891 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b12_m48 | 1 | 15.123936 | 15.123936 | 15.123936 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b10_m40 | 1 | 14.943669 | 14.943669 | 14.943669 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b8_m32 | 1 | 14.550287 | 14.550287 | 14.550287 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b4_m16 | 1 | 11.637842 | 11.637842 | 11.637842 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b2_m8 | 1 | 9.811599 | 9.811599 | 9.811599 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | 76 | 28.584774 | 28.570657 | 28.703784 | 14.676774 | -48.66% | compared |
| qwen35-35b-a5-tp4-c128-graph:q4_b124_m496 | 2 | 28.334813 | 28.334813 | 28.358286 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b6_m24 | 2 | 12.927148 | 12.927148 | 13.228714 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b2_m8 | 2 | 9.874035 | 9.874035 | 9.959215 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b1_m4 | 1 | 8.487783 | 8.487783 | 8.487783 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b120_m480 | 1 | 27.851872 | 27.851872 | 27.851872 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b116_m464 | 1 | 27.866303 | 27.866303 | 27.866303 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b108_m432 | 1 | 27.248782 | 27.248782 | 27.248782 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b96_m384 | 1 | 24.930448 | 24.930448 | 24.930448 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b84_m336 | 1 | 25.697986 | 25.697986 | 25.697986 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b72_m288 | 1 | 24.145611 | 24.145611 | 24.145611 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b58_m232 | 1 | 21.377453 | 21.377453 | 21.377453 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b50_m200 | 1 | 21.025810 | 21.025810 | 21.025810 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b42_m168 | 1 | 19.975946 | 19.975946 | 19.975946 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b38_m152 | 1 | 19.184599 | 19.184599 | 19.184599 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b28_m112 | 1 | 16.371933 | 16.371933 | 16.371933 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b18_m72 | 1 | 15.838246 | 15.838246 | 15.838246 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b12_m48 | 1 | 15.126906 | 15.126906 | 15.126906 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b10_m40 | 1 | 14.935133 | 14.935133 | 14.935133 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b8_m32 | 1 | 14.333941 | 14.333941 | 14.333941 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c128-graph:q4_b4_m16 | 1 | 11.424036 | 11.424036 | 11.424036 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 84 | 11.551367 | 11.481642 | 11.817997 | 5.048611 | -56.29% | compared |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | 6 | 8.746954 | 8.802646 | 8.838036 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | 1 | 9.699817 | 9.699817 | 9.699817 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen36-a5-tp2-c12:q4_b12_m48 | 55 | 24.225774 | 24.052762 | 24.710750 | 10.998503 | -54.60% | compared |
| qwen36-a5-tp2-c96:q4_b96_m384 | 24 | 63.853365 | 63.561524 | 65.419347 | 45.126349 | -29.33% | compared |
| qwen36-a5-tp2-c1:q4_b1_m4 | 85 | 12.318284 | 12.279117 | 12.362065 | 7.412887 | -39.82% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a3_glm53_dc4k_b1:q1_b1_m1 | 38.954827 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b2:q1_b2_m2 | 40.969878 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b4:q1_b4_m4 | 43.437734 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b8:q1_b8_m8 | 47.113275 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc16k_b1:q1_b1_m1 | 39.112085 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 76.089008 | 75.005135 | 1.083873 | 1.42% | FULL_DECODE_ONLY | 16 / 1 / 1 | none / full |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 119.054350 | 118.048221 | 1.006129 | 0.85% | FULL_DECODE_ONLY | 16 / 1 / 1 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | 21.956845 | 21.570616 | 0.386228 | 1.76% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b1_m4 | 8.738856 | 8.327275 | 0.411581 | 4.71% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b60_m240 | 21.444033 | 21.052657 | 0.391376 | 1.83% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b56_m224 | 20.971886 | 20.566321 | 0.405565 | 1.93% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b52_m208 | 20.949956 | 20.546382 | 0.403574 | 1.93% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b48_m192 | 20.070326 | 19.633751 | 0.436575 | 2.18% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b44_m176 | 20.103043 | 19.666032 | 0.437011 | 2.17% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b40_m160 | 19.908259 | 19.463747 | 0.444512 | 2.23% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b34_m136 | 19.148523 | 18.711708 | 0.436815 | 2.28% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b26_m104 | 16.773756 | 16.340313 | 0.433443 | 2.58% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b18_m72 | 15.809891 | 15.371932 | 0.437959 | 2.77% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b12_m48 | 15.123936 | 14.695564 | 0.428372 | 2.83% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b10_m40 | 14.943669 | 14.515121 | 0.428548 | 2.87% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b8_m32 | 14.550287 | 14.119789 | 0.430498 | 2.96% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b4_m16 | 11.637842 | 11.220951 | 0.416891 | 3.58% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c64-graph:q4_b2_m8 | 9.811599 | 9.397245 | 0.414354 | 4.22% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | 28.584774 | 28.300327 | 0.284446 | 1.00% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b124_m496 | 28.334813 | 28.063363 | 0.271451 | 0.96% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b6_m24 | 12.927148 | 12.505978 | 0.421170 | 3.26% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b2_m8 | 9.874035 | 9.460026 | 0.414010 | 4.19% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b1_m4 | 8.487783 | 8.077760 | 0.410023 | 4.83% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b120_m480 | 27.851872 | 27.566628 | 0.285244 | 1.02% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b116_m464 | 27.866303 | 27.595819 | 0.270484 | 0.97% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b108_m432 | 27.248782 | 26.956256 | 0.292526 | 1.07% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b96_m384 | 24.930448 | 24.521488 | 0.408960 | 1.64% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b84_m336 | 25.697986 | 25.281934 | 0.416052 | 1.62% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b72_m288 | 24.145611 | 23.730163 | 0.415448 | 1.72% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b58_m232 | 21.377453 | 20.980405 | 0.397048 | 1.86% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b50_m200 | 21.025810 | 20.635201 | 0.390609 | 1.86% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b42_m168 | 19.975946 | 19.525886 | 0.450060 | 2.25% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b38_m152 | 19.184599 | 18.744937 | 0.439662 | 2.29% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b28_m112 | 16.371933 | 15.928753 | 0.443180 | 2.71% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b18_m72 | 15.838246 | 15.409340 | 0.428906 | 2.71% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b12_m48 | 15.126906 | 14.695534 | 0.431372 | 2.85% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b10_m40 | 14.935133 | 14.507604 | 0.427529 | 2.86% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b8_m32 | 14.333941 | 13.898611 | 0.435330 | 3.04% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c128-graph:q4_b4_m16 | 11.424036 | 11.005363 | 0.418673 | 3.66% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 11.551367 | 11.134754 | 0.416613 | 3.61% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | 8.746954 | 8.336170 | 0.410784 | 4.70% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | 9.699817 | 9.286883 | 0.412934 | 4.26% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen36-a5-tp2-c12:q4_b12_m48 | 24.225774 | 23.857914 | 0.367860 | 1.52% | ACLGraph; campaign report | 2 / 1 / 1 | none / full |
| qwen36-a5-tp2-c96:q4_b96_m384 | 63.853365 | 63.564919 | 0.288446 | 0.45% | ACLGraph; campaign report | 2 / 1 / 1 | none / full |
| qwen36-a5-tp2-c1:q4_b1_m4 | 12.318284 | 11.955626 | 0.362658 | 2.94% | ACLGraph; campaign report | 2 / 1 / 1 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | dense_layer | 3 / 3 | 0.387506 | 0.384723 | 0.394250 | 0.352607 | -9.01% |
| a3_glm53_dc4k_b1:q1_b1_m1 | moe_layer | 75 / 75 | 0.503075 | 0.484378 | 0.566864 | 0.478704 | -4.84% |
| a3_glm53_dc4k_b2:q1_b2_m2 | dense_layer | 3 / 3 | 0.403290 | 0.407802 | 0.410515 | 0.439748 | +9.04% |
| a3_glm53_dc4k_b2:q1_b2_m2 | moe_layer | 18 / 75 | 0.529285 | 0.509096 | 0.601701 | 0.632976 | +19.59% |
| a3_glm53_dc4k_b4:q1_b4_m4 | dense_layer | 0 / 3 | 0.401821 | 0.399081 | 0.411774 | 0.614031 | +52.81% |
| a3_glm53_dc4k_b4:q1_b4_m4 | moe_layer | 0 / 75 | 0.562175 | 0.540899 | 0.637391 | 0.935468 | +66.40% |
| a3_glm53_dc4k_b8:q1_b8_m8 | dense_layer | 0 / 3 | 0.416038 | 0.413257 | 0.424403 | 0.964697 | +131.88% |
| a3_glm53_dc4k_b8:q1_b8_m8 | moe_layer | 0 / 75 | 0.610549 | 0.587718 | 0.698046 | 1.518465 | +148.70% |
| a3_glm53_dc16k_b1:q1_b1_m1 | dense_layer | 3 / 3 | 0.396276 | 0.393697 | 0.402033 | 0.352607 | -11.02% |
| a3_glm53_dc16k_b1:q1_b1_m1 | moe_layer | 75 / 75 | 0.504482 | 0.483485 | 0.576161 | 0.478704 | -5.11% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | moe_layer | 0 / 60 | 1.266992 | 1.278787 | 1.381181 | 8.547275 | +574.61% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | moe_layer | 0 / 60 | 1.983005 | 1.996372 | 2.053669 | 23.411323 | +1080.60% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | moe_layer | 0 / 40 | 0.548900 | 0.545747 | 0.550616 | 0.255477 | -53.46% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | moe_layer | 0 / 40 | 0.714598 | 0.719591 | 0.721924 | 0.366919 | -48.65% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | moe_layer | 0 / 40 | 0.288763 | 0.283062 | 0.299996 | 0.126215 | -56.29% |
| qwen36-a5-tp2-c12:q4_b12_m48 | dense_layer | 0 / 64 | 0.377769 | 0.402171 | 0.410517 | 0.171852 | -54.51% |
| qwen36-a5-tp2-c96:q4_b96_m384 | dense_layer | 0 / 64 | 0.996962 | 1.057504 | 1.060586 | 0.705099 | -29.28% |
| qwen36-a5-tp2-c1:q4_b1_m4 | dense_layer | 0 / 64 | 0.191663 | 0.191309 | 0.193238 | 0.115826 | -39.57% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 78 / 78 | 0.498630 | 0.484310 | 0.566864 | 0.473854 | -4.97% |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 21 / 78 | 0.524439 | 0.508658 | 0.601701 | 0.625544 | +19.28% |
| a3_glm53_dc4k_b4:q1_b4_m4 | mla | 0 / 78 | 0.556008 | 0.540114 | 0.637391 | 0.923105 | +66.02% |
| a3_glm53_dc4k_b8:q1_b8_m8 | mla | 0 / 78 | 0.603068 | 0.587228 | 0.698046 | 1.497166 | +148.26% |
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 78 / 78 | 0.500321 | 0.482807 | 0.576161 | 0.473854 | -5.29% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gdn | 0 / 45 | 1.235511 | 1.203183 | 1.311698 | 8.512967 | +589.02% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gqa | 0 / 15 | 1.361434 | 1.341377 | 1.455367 | 8.650199 | +535.37% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gdn | 0 / 45 | 1.959216 | 1.940194 | 2.025587 | 23.359497 | +1092.29% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gqa | 0 / 15 | 2.054372 | 2.022060 | 2.122093 | 23.566801 | +1047.15% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | gdn | 0 / 30 | 0.554528 | 0.547070 | 0.552632 | 0.264532 | -52.30% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | gqa | 0 / 10 | 0.532016 | 0.532480 | 0.533989 | 0.228313 | -57.09% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | gdn | 0 / 30 | 0.721017 | 0.720076 | 0.722012 | 0.380268 | -47.26% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | gqa | 0 / 10 | 0.695341 | 0.694634 | 0.697229 | 0.326872 | -52.99% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gdn | 0 / 30 | 0.285398 | 0.282353 | 0.284296 | 0.124152 | -56.50% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gqa | 0 / 10 | 0.298857 | 0.298829 | 0.301088 | 0.132404 | -55.70% |
| qwen36-a5-tp2-c12:q4_b12_m48 | gdn | 0 / 48 | 0.408829 | 0.404015 | 0.411737 | 0.182452 | -55.37% |
| qwen36-a5-tp2-c12:q4_b12_m48 | gqa | 0 / 16 | 0.284588 | 0.284472 | 0.285798 | 0.140051 | -50.79% |
| qwen36-a5-tp2-c96:q4_b96_m384 | gdn | 0 / 48 | 1.064900 | 1.058731 | 1.060743 | 0.755556 | -29.05% |
| qwen36-a5-tp2-c96:q4_b96_m384 | gqa | 0 / 16 | 0.793149 | 0.792915 | 0.794736 | 0.553729 | -30.19% |
| qwen36-a5-tp2-c1:q4_b1_m4 | gdn | 0 / 48 | 0.192884 | 0.191633 | 0.193801 | 0.115396 | -40.17% |
| qwen36-a5-tp2-c1:q4_b1_m4 | gqa | 0 / 16 | 0.188000 | 0.188164 | 0.188947 | 0.117116 | -37.70% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 0.498630 | — | — |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 0.524439 | — | — |
| a3_glm53_dc4k_b4:q1_b4_m4 | mla | 0.556008 | — | — |
| a3_glm53_dc4k_b8:q1_b8_m8 | mla | 0.603068 | — | — |
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 0.500321 | — | — |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gdn | 1.235511 | 1.218935 | 0.016576 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gqa | 1.361434 | 1.343537 | 0.017897 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gdn | 1.959216 | 1.944578 | 0.014638 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gqa | 2.054372 | 2.036149 | 0.018223 |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | gdn | 0.554528 | 0.545195 | 0.009333 |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | gqa | 0.532016 | 0.521478 | 0.010538 |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | gdn | 0.721017 | 0.714203 | 0.006814 |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | gqa | 0.695341 | 0.687425 | 0.007916 |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gdn | 0.285398 | 0.274983 | 0.010415 |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gqa | 0.298857 | 0.288526 | 0.010332 |
| qwen36-a5-tp2-c12:q4_b12_m48 | gdn | 0.408829 | 0.403692 | 0.005137 |
| qwen36-a5-tp2-c12:q4_b12_m48 | gqa | 0.284588 | 0.280043 | 0.004545 |
| qwen36-a5-tp2-c96:q4_b96_m384 | gdn | 1.064900 | 1.061406 | 0.003494 |
| qwen36-a5-tp2-c96:q4_b96_m384 | gqa | 0.793149 | 0.788590 | 0.004559 |
| qwen36-a5-tp2-c1:q4_b1_m4 | gdn | 0.192884 | 0.188024 | 0.004860 |
| qwen36-a5-tp2-c1:q4_b1_m4 | gqa | 0.188000 | 0.183155 | 0.004844 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | all | 77 | 5698 | 0.499986 | 0.484650 | 0.465447 | -3.96% |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 77 | 5698 | 0.499986 | 0.484650 | 0.465447 | -3.96% |
| a3_glm53_dc4k_b2:q1_b2_m2 | all | 77 | 5390 | 0.525918 | 0.508590 | 0.619613 | +21.83% |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 77 | 5390 | 0.525918 | 0.508590 | 0.619613 | +21.83% |
| a3_glm53_dc4k_b4:q1_b4_m4 | all | 77 | 5159 | 0.557881 | 0.540369 | 0.921892 | +70.60% |
| a3_glm53_dc4k_b4:q1_b4_m4 | mla | 77 | 5159 | 0.557881 | 0.540369 | 0.921892 | +70.60% |
| a3_glm53_dc4k_b8:q1_b8_m8 | all | 77 | 4697 | 0.605388 | 0.586108 | 1.503959 | +156.60% |
| a3_glm53_dc4k_b8:q1_b8_m8 | mla | 77 | 4697 | 0.605388 | 0.586108 | 1.503959 | +156.60% |
| a3_glm53_dc16k_b1:q1_b1_m1 | all | 77 | 5698 | 0.501597 | 0.482860 | 0.465447 | -3.61% |
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 77 | 5698 | 0.501597 | 0.482860 | 0.465447 | -3.61% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | all | 59 | 1357 | 1.265579 | 1.271900 | 8.512967 | +569.31% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gdn | 44 | 1012 | 1.232902 | 1.207710 | 8.512967 | +604.89% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gqa | 15 | 345 | 1.361434 | 1.346900 | 8.650199 | +542.23% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | all | 59 | 1062 | 1.981915 | 1.992890 | 23.359497 | +1072.14% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gdn | 44 | 792 | 1.957214 | 1.935175 | 23.359497 | +1107.10% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gqa | 15 | 270 | 2.054372 | 2.031370 | 23.566801 | +1060.14% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | all | 39 | 3081 | 0.543137 | 0.545623 | 0.264532 | -51.52% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | gdn | 29 | 2291 | 0.546971 | 0.546708 | 0.264532 | -51.61% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | gqa | 10 | 790 | 0.532016 | 0.532309 | 0.228313 | -57.11% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | all | 39 | 2964 | 0.713577 | 0.719167 | 0.380268 | -47.12% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | gdn | 29 | 2204 | 0.719865 | 0.719916 | 0.380268 | -47.18% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | gqa | 10 | 760 | 0.695341 | 0.694129 | 0.326872 | -52.91% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | all | 39 | 3276 | 0.286250 | 0.283215 | 0.124152 | -56.16% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gdn | 29 | 2436 | 0.281903 | 0.282722 | 0.124152 | -56.09% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gqa | 10 | 840 | 0.298857 | 0.299161 | 0.132404 | -55.74% |
| qwen36-a5-tp2-c12:q4_b12_m48 | all | 63 | 3465 | 0.373974 | 0.401967 | 0.182452 | -54.61% |
| qwen36-a5-tp2-c12:q4_b12_m48 | gdn | 47 | 2585 | 0.404404 | 0.403298 | 0.182452 | -54.76% |
| qwen36-a5-tp2-c12:q4_b12_m48 | gqa | 16 | 880 | 0.284588 | 0.284266 | 0.140051 | -50.73% |
| qwen36-a5-tp2-c96:q4_b96_m384 | all | 63 | 1512 | 0.991056 | 1.057303 | 0.755556 | -28.54% |
| qwen36-a5-tp2-c96:q4_b96_m384 | gdn | 47 | 1128 | 1.058428 | 1.058404 | 0.755556 | -28.61% |
| qwen36-a5-tp2-c96:q4_b96_m384 | gqa | 16 | 384 | 0.793149 | 0.792751 | 0.553729 | -30.15% |
| qwen36-a5-tp2-c1:q4_b1_m4 | all | 63 | 5355 | 0.190897 | 0.191201 | 0.115396 | -39.65% |
| qwen36-a5-tp2-c1:q4_b1_m4 | gdn | 47 | 3995 | 0.191883 | 0.191473 | 0.115396 | -39.73% |
| qwen36-a5-tp2-c1:q4_b1_m4 | gqa | 16 | 1360 | 0.188000 | 0.187574 | 0.117116 | -37.56% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | 74 | 0.394250 | 0.385352 | 0.415732 | 0.352607 | -10.56% |
| a3_glm53_dc4k_b2:q1_b2_m2 | 70 | 0.410515 | 0.395952 | 0.454831 | 0.439748 | +7.12% |
| a3_glm53_dc4k_b4:q1_b4_m4 | 67 | 0.411774 | 0.407112 | 0.411352 | 0.614031 | +49.12% |
| a3_glm53_dc4k_b8:q1_b8_m8 | 61 | 0.424403 | 0.422672 | 0.425891 | 0.964697 | +127.31% |
| a3_glm53_dc16k_b1:q1_b1_m1 | 74 | 0.402033 | 0.396682 | 0.411171 | 0.352607 | -12.29% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 23 | 1.350335 | 1.286500 | 1.407580 | 8.512967 | +530.43% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 18 | 2.047277 | 1.998270 | 2.165240 | 23.359497 | +1041.00% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | 79 | 0.773661 | 0.821604 | 0.881730 | 0.264532 | -65.81% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | 76 | 0.754430 | 0.723774 | 0.856314 | 0.380268 | -49.60% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 84 | 0.386758 | 0.297328 | 0.630548 | 0.124152 | -67.90% |
| qwen36-a5-tp2-c12:q4_b12_m48 | 55 | 0.616826 | 0.393097 | 1.098361 | 0.182452 | -70.42% |
| qwen36-a5-tp2-c96:q4_b96_m384 | 24 | 1.369095 | 1.068151 | 2.946417 | 0.755556 | -44.81% |
| qwen36-a5-tp2-c1:q4_b1_m4 | 85 | 0.239954 | 0.198388 | 0.228723 | 0.115396 | -51.91% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 1 | — | — | — | — |
| a3_glm53_dc4k_b2:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 2 | — | — | — | — |
| a3_glm53_dc4k_b4:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 4 | — | — | — | — |
| a3_glm53_dc4k_b8:q1_b8_m8 | 1 | 8 | 8 | unknown | 4096 | 8 | — | — | — | — |
| a3_glm53_dc16k_b1:q1_b1_m1 | 1 | 1 | 1 | unknown | 16384 | 1 | — | — | — | — |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 4 | 64 | 256 | unknown | 4104 | 48 | 39.264375 | 39.367968 | — | — |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 4 | 160 | 640 | unknown | 4104 | 136 | 59.413752 | 59.082504 | — | — |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | 4 | 64 | 256 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b1_m4 | 4 | 1 | 4 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b60_m240 | 4 | 60 | 240 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b56_m224 | 4 | 56 | 224 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b52_m208 | 4 | 52 | 208 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b48_m192 | 4 | 48 | 192 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b44_m176 | 4 | 44 | 176 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b40_m160 | 4 | 40 | 160 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b34_m136 | 4 | 34 | 136 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b26_m104 | 4 | 26 | 104 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b18_m72 | 4 | 18 | 72 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b12_m48 | 4 | 12 | 48 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b10_m40 | 4 | 10 | 40 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b8_m32 | 4 | 8 | 32 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b4_m16 | 4 | 4 | 16 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c64-graph:q4_b2_m8 | 4 | 2 | 8 | unknown | 4096 | 64 | 12.604055 | 11.999976 | — | 10.693848 |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | 4 | 128 | 512 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b124_m496 | 4 | 124 | 496 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b6_m24 | 4 | 6 | 24 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b2_m8 | 4 | 2 | 8 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b1_m4 | 4 | 1 | 4 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b120_m480 | 4 | 120 | 480 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b116_m464 | 4 | 116 | 464 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b108_m432 | 4 | 108 | 432 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b96_m384 | 4 | 96 | 384 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b84_m336 | 4 | 84 | 336 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b72_m288 | 4 | 72 | 288 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b58_m232 | 4 | 58 | 232 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b50_m200 | 4 | 50 | 200 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b42_m168 | 4 | 42 | 168 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b38_m152 | 4 | 38 | 152 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b28_m112 | 4 | 28 | 112 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b18_m72 | 4 | 18 | 72 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b12_m48 | 4 | 12 | 48 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b10_m40 | 4 | 10 | 40 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b8_m32 | 4 | 8 | 32 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c128-graph:q4_b4_m16 | 4 | 4 | 16 | unknown | 4096 | 128 | 15.922305 | 15.843076 | — | 14.042577 |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 4 | 4 | 16 | unknown | 4096 | 4 | 7.155375 | 7.133439 | — | 5.955661 |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | 4 | 1 | 4 | unknown | 4096 | 4 | 7.155375 | 7.133439 | — | 5.955661 |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | 4 | 2 | 8 | unknown | 4096 | 4 | 7.155375 | 7.133439 | — | 5.955661 |
| qwen36-a5-tp2-c12:q4_b12_m48 | 4 | 12 | 48 | unknown | 4104 | 12 | 12.737826 | 12.657177 | 13.606740 | 10.182462 |
| qwen36-a5-tp2-c96:q4_b96_m384 | 4 | 96 | 384 | unknown | 4104 | 96 | 31.633699 | 31.824432 | 30.608581 | 30.201530 |
| qwen36-a5-tp2-c1:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 1 | 8.043380 | 8.043380 | 8.239878 | 5.939812 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | embedding | 74 | 0.007841 | 0.007839 | 0.007960 |
| a3_glm53_dc4k_b1:q1_b1_m1 | final_norm | 74 | 0.153796 | 0.153077 | 0.157037 |
| a3_glm53_dc4k_b1:q1_b1_m1 | lm_head | 74 | 0.216579 | 0.216606 | 0.217935 |
| a3_glm53_dc4k_b2:q1_b2_m2 | embedding | 70 | 0.002795 | 0.002780 | 0.003000 |
| a3_glm53_dc4k_b2:q1_b2_m2 | final_norm | 70 | 0.156513 | 0.156497 | 0.158957 |
| a3_glm53_dc4k_b2:q1_b2_m2 | lm_head | 70 | 0.227520 | 0.227626 | 0.229775 |
| a3_glm53_dc4k_b4:q1_b4_m4 | embedding | 67 | 0.003206 | 0.003160 | 0.003420 |
| a3_glm53_dc4k_b4:q1_b4_m4 | final_norm | 67 | 0.157700 | 0.155217 | 0.165517 |
| a3_glm53_dc4k_b4:q1_b4_m4 | lm_head | 67 | 0.246052 | 0.245875 | 0.248355 |
| a3_glm53_dc4k_b8:q1_b8_m8 | embedding | 61 | 0.003748 | 0.003760 | 0.003920 |
| a3_glm53_dc4k_b8:q1_b8_m8 | final_norm | 61 | 0.157658 | 0.157397 | 0.159617 |
| a3_glm53_dc4k_b8:q1_b8_m8 | lm_head | 61 | 0.272210 | 0.272394 | 0.273895 |
| a3_glm53_dc16k_b1:q1_b1_m1 | embedding | 74 | 0.007803 | 0.007780 | 0.007920 |
| a3_glm53_dc16k_b1:q1_b1_m1 | final_norm | 74 | 0.160420 | 0.160087 | 0.166337 |
| a3_glm53_dc16k_b1:q1_b1_m1 | lm_head | 74 | 0.221647 | 0.221575 | 0.223536 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | embedding | 23 | 0.010090 | 0.010000 | 0.010280 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | final_norm | 23 | 0.166548 | 0.166700 | 0.168400 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | lm_head | 23 | 0.272729 | 0.272680 | 0.274060 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | embedding | 18 | 0.011200 | 0.011080 | 0.011840 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | final_norm | 18 | 0.188559 | 0.189710 | 0.192900 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | lm_head | 18 | 0.435398 | 0.436110 | 0.441320 |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | embedding | 79 | 0.004645 | 0.004571 | 0.005220 |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | final_norm | 79 | 0.049051 | 0.049024 | 0.049686 |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | lm_head | 79 | 0.166624 | 0.166616 | 0.167082 |
| qwen35-35b-a5-tp4-c64-graph:q4_b1_m4 | embedding | 3 | 0.002275 | 0.002330 | 0.002456 |
| qwen35-35b-a5-tp4-c64-graph:q4_b1_m4 | final_norm | 3 | 0.042747 | 0.042721 | 0.043150 |
| qwen35-35b-a5-tp4-c64-graph:q4_b1_m4 | lm_head | 3 | 0.074199 | 0.074226 | 0.075373 |
| qwen35-35b-a5-tp4-c64-graph:q4_b60_m240 | embedding | 1 | 0.004954 | 0.004954 | 0.004954 |
| qwen35-35b-a5-tp4-c64-graph:q4_b60_m240 | final_norm | 1 | 0.048400 | 0.048400 | 0.048400 |
| qwen35-35b-a5-tp4-c64-graph:q4_b60_m240 | lm_head | 1 | 0.155692 | 0.155692 | 0.155692 |
| qwen35-35b-a5-tp4-c64-graph:q4_b56_m224 | embedding | 1 | 0.004099 | 0.004099 | 0.004099 |
| qwen35-35b-a5-tp4-c64-graph:q4_b56_m224 | final_norm | 1 | 0.048737 | 0.048737 | 0.048737 |
| qwen35-35b-a5-tp4-c64-graph:q4_b56_m224 | lm_head | 1 | 0.150095 | 0.150095 | 0.150095 |
| qwen35-35b-a5-tp4-c64-graph:q4_b52_m208 | embedding | 1 | 0.005077 | 0.005077 | 0.005077 |
| qwen35-35b-a5-tp4-c64-graph:q4_b52_m208 | final_norm | 1 | 0.050695 | 0.050695 | 0.050695 |
| qwen35-35b-a5-tp4-c64-graph:q4_b52_m208 | lm_head | 1 | 0.140240 | 0.140240 | 0.140240 |
| qwen35-35b-a5-tp4-c64-graph:q4_b48_m192 | embedding | 1 | 0.005287 | 0.005287 | 0.005287 |
| qwen35-35b-a5-tp4-c64-graph:q4_b48_m192 | final_norm | 1 | 0.050125 | 0.050125 | 0.050125 |
| qwen35-35b-a5-tp4-c64-graph:q4_b48_m192 | lm_head | 1 | 0.127098 | 0.127098 | 0.127098 |
| qwen35-35b-a5-tp4-c64-graph:q4_b44_m176 | embedding | 1 | 0.003582 | 0.003582 | 0.003582 |
| qwen35-35b-a5-tp4-c64-graph:q4_b44_m176 | final_norm | 1 | 0.048018 | 0.048018 | 0.048018 |
| qwen35-35b-a5-tp4-c64-graph:q4_b44_m176 | lm_head | 1 | 0.118382 | 0.118382 | 0.118382 |
| qwen35-35b-a5-tp4-c64-graph:q4_b40_m160 | embedding | 1 | 0.004259 | 0.004259 | 0.004259 |
| qwen35-35b-a5-tp4-c64-graph:q4_b40_m160 | final_norm | 1 | 0.048096 | 0.048096 | 0.048096 |
| qwen35-35b-a5-tp4-c64-graph:q4_b40_m160 | lm_head | 1 | 0.116232 | 0.116232 | 0.116232 |
| qwen35-35b-a5-tp4-c64-graph:q4_b34_m136 | embedding | 1 | 0.004627 | 0.004627 | 0.004627 |
| qwen35-35b-a5-tp4-c64-graph:q4_b34_m136 | final_norm | 1 | 0.047829 | 0.047829 | 0.047829 |
| qwen35-35b-a5-tp4-c64-graph:q4_b34_m136 | lm_head | 1 | 0.121132 | 0.121132 | 0.121132 |
| qwen35-35b-a5-tp4-c64-graph:q4_b26_m104 | embedding | 1 | 0.003708 | 0.003708 | 0.003708 |
| qwen35-35b-a5-tp4-c64-graph:q4_b26_m104 | final_norm | 1 | 0.048717 | 0.048717 | 0.048717 |
| qwen35-35b-a5-tp4-c64-graph:q4_b26_m104 | lm_head | 1 | 0.094547 | 0.094547 | 0.094547 |
| qwen35-35b-a5-tp4-c64-graph:q4_b18_m72 | embedding | 1 | 0.003821 | 0.003821 | 0.003821 |
| qwen35-35b-a5-tp4-c64-graph:q4_b18_m72 | final_norm | 1 | 0.047466 | 0.047466 | 0.047466 |
| qwen35-35b-a5-tp4-c64-graph:q4_b18_m72 | lm_head | 1 | 0.085497 | 0.085497 | 0.085497 |
| qwen35-35b-a5-tp4-c64-graph:q4_b12_m48 | embedding | 1 | 0.003608 | 0.003608 | 0.003608 |
| qwen35-35b-a5-tp4-c64-graph:q4_b12_m48 | final_norm | 1 | 0.049431 | 0.049431 | 0.049431 |
| qwen35-35b-a5-tp4-c64-graph:q4_b12_m48 | lm_head | 1 | 0.077218 | 0.077218 | 0.077218 |
| qwen35-35b-a5-tp4-c64-graph:q4_b10_m40 | embedding | 1 | 0.003178 | 0.003178 | 0.003178 |
| qwen35-35b-a5-tp4-c64-graph:q4_b10_m40 | final_norm | 1 | 0.047271 | 0.047271 | 0.047271 |
| qwen35-35b-a5-tp4-c64-graph:q4_b10_m40 | lm_head | 1 | 0.075914 | 0.075914 | 0.075914 |
| qwen35-35b-a5-tp4-c64-graph:q4_b8_m32 | embedding | 1 | 0.002534 | 0.002534 | 0.002534 |
| qwen35-35b-a5-tp4-c64-graph:q4_b8_m32 | final_norm | 1 | 0.048878 | 0.048878 | 0.048878 |
| qwen35-35b-a5-tp4-c64-graph:q4_b8_m32 | lm_head | 1 | 0.078248 | 0.078248 | 0.078248 |
| qwen35-35b-a5-tp4-c64-graph:q4_b4_m16 | embedding | 1 | 0.003792 | 0.003792 | 0.003792 |
| qwen35-35b-a5-tp4-c64-graph:q4_b4_m16 | final_norm | 1 | 0.044319 | 0.044319 | 0.044319 |
| qwen35-35b-a5-tp4-c64-graph:q4_b4_m16 | lm_head | 1 | 0.075286 | 0.075286 | 0.075286 |
| qwen35-35b-a5-tp4-c64-graph:q4_b2_m8 | embedding | 1 | 0.002675 | 0.002675 | 0.002675 |
| qwen35-35b-a5-tp4-c64-graph:q4_b2_m8 | final_norm | 1 | 0.042872 | 0.042872 | 0.042872 |
| qwen35-35b-a5-tp4-c64-graph:q4_b2_m8 | lm_head | 1 | 0.074102 | 0.074102 | 0.074102 |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | embedding | 76 | 0.004838 | 0.004733 | 0.005598 |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | final_norm | 76 | 0.050266 | 0.050226 | 0.051055 |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | lm_head | 76 | 0.336015 | 0.336019 | 0.336269 |
| qwen35-35b-a5-tp4-c128-graph:q4_b124_m496 | embedding | 2 | 0.004597 | 0.004597 | 0.005066 |
| qwen35-35b-a5-tp4-c128-graph:q4_b124_m496 | final_norm | 2 | 0.049883 | 0.049883 | 0.050369 |
| qwen35-35b-a5-tp4-c128-graph:q4_b124_m496 | lm_head | 2 | 0.334454 | 0.334454 | 0.334621 |
| qwen35-35b-a5-tp4-c128-graph:q4_b6_m24 | embedding | 2 | 0.003291 | 0.003291 | 0.003477 |
| qwen35-35b-a5-tp4-c128-graph:q4_b6_m24 | final_norm | 2 | 0.045831 | 0.045831 | 0.046198 |
| qwen35-35b-a5-tp4-c128-graph:q4_b6_m24 | lm_head | 2 | 0.077698 | 0.077698 | 0.078135 |
| qwen35-35b-a5-tp4-c128-graph:q4_b2_m8 | embedding | 2 | 0.002683 | 0.002683 | 0.002717 |
| qwen35-35b-a5-tp4-c128-graph:q4_b2_m8 | final_norm | 2 | 0.042653 | 0.042653 | 0.042896 |
| qwen35-35b-a5-tp4-c128-graph:q4_b2_m8 | lm_head | 2 | 0.073520 | 0.073520 | 0.074027 |
| qwen35-35b-a5-tp4-c128-graph:q4_b1_m4 | embedding | 1 | 0.002250 | 0.002250 | 0.002250 |
| qwen35-35b-a5-tp4-c128-graph:q4_b1_m4 | final_norm | 1 | 0.042621 | 0.042621 | 0.042621 |
| qwen35-35b-a5-tp4-c128-graph:q4_b1_m4 | lm_head | 1 | 0.073523 | 0.073523 | 0.073523 |
| qwen35-35b-a5-tp4-c128-graph:q4_b120_m480 | embedding | 1 | 0.004776 | 0.004776 | 0.004776 |
| qwen35-35b-a5-tp4-c128-graph:q4_b120_m480 | final_norm | 1 | 0.050272 | 0.050272 | 0.050272 |
| qwen35-35b-a5-tp4-c128-graph:q4_b120_m480 | lm_head | 1 | 0.296347 | 0.296347 | 0.296347 |
| qwen35-35b-a5-tp4-c128-graph:q4_b116_m464 | embedding | 1 | 0.004763 | 0.004763 | 0.004763 |
| qwen35-35b-a5-tp4-c128-graph:q4_b116_m464 | final_norm | 1 | 0.049067 | 0.049067 | 0.049067 |
| qwen35-35b-a5-tp4-c128-graph:q4_b116_m464 | lm_head | 1 | 0.295536 | 0.295536 | 0.295536 |
| qwen35-35b-a5-tp4-c128-graph:q4_b108_m432 | embedding | 1 | 0.005007 | 0.005007 | 0.005007 |
| qwen35-35b-a5-tp4-c128-graph:q4_b108_m432 | final_norm | 1 | 0.050401 | 0.050401 | 0.050401 |
| qwen35-35b-a5-tp4-c128-graph:q4_b108_m432 | lm_head | 1 | 0.275395 | 0.275395 | 0.275395 |
| qwen35-35b-a5-tp4-c128-graph:q4_b96_m384 | embedding | 1 | 0.004313 | 0.004313 | 0.004313 |
| qwen35-35b-a5-tp4-c128-graph:q4_b96_m384 | final_norm | 1 | 0.049200 | 0.049200 | 0.049200 |
| qwen35-35b-a5-tp4-c128-graph:q4_b96_m384 | lm_head | 1 | 0.257361 | 0.257361 | 0.257361 |
| qwen35-35b-a5-tp4-c128-graph:q4_b84_m336 | embedding | 1 | 0.004952 | 0.004952 | 0.004952 |
| qwen35-35b-a5-tp4-c128-graph:q4_b84_m336 | final_norm | 1 | 0.049397 | 0.049397 | 0.049397 |
| qwen35-35b-a5-tp4-c128-graph:q4_b84_m336 | lm_head | 1 | 0.220721 | 0.220721 | 0.220721 |
| qwen35-35b-a5-tp4-c128-graph:q4_b72_m288 | embedding | 1 | 0.004404 | 0.004404 | 0.004404 |
| qwen35-35b-a5-tp4-c128-graph:q4_b72_m288 | final_norm | 1 | 0.049669 | 0.049669 | 0.049669 |
| qwen35-35b-a5-tp4-c128-graph:q4_b72_m288 | lm_head | 1 | 0.205846 | 0.205846 | 0.205846 |
| qwen35-35b-a5-tp4-c128-graph:q4_b58_m232 | embedding | 1 | 0.004572 | 0.004572 | 0.004572 |
| qwen35-35b-a5-tp4-c128-graph:q4_b58_m232 | final_norm | 1 | 0.048717 | 0.048717 | 0.048717 |
| qwen35-35b-a5-tp4-c128-graph:q4_b58_m232 | lm_head | 1 | 0.163674 | 0.163674 | 0.163674 |
| qwen35-35b-a5-tp4-c128-graph:q4_b50_m200 | embedding | 1 | 0.004257 | 0.004257 | 0.004257 |
| qwen35-35b-a5-tp4-c128-graph:q4_b50_m200 | final_norm | 1 | 0.047221 | 0.047221 | 0.047221 |
| qwen35-35b-a5-tp4-c128-graph:q4_b50_m200 | lm_head | 1 | 0.141813 | 0.141813 | 0.141813 |
| qwen35-35b-a5-tp4-c128-graph:q4_b42_m168 | embedding | 1 | 0.005473 | 0.005473 | 0.005473 |
| qwen35-35b-a5-tp4-c128-graph:q4_b42_m168 | final_norm | 1 | 0.047757 | 0.047757 | 0.047757 |
| qwen35-35b-a5-tp4-c128-graph:q4_b42_m168 | lm_head | 1 | 0.133399 | 0.133399 | 0.133399 |
| qwen35-35b-a5-tp4-c128-graph:q4_b38_m152 | embedding | 1 | 0.005491 | 0.005491 | 0.005491 |
| qwen35-35b-a5-tp4-c128-graph:q4_b38_m152 | final_norm | 1 | 0.049387 | 0.049387 | 0.049387 |
| qwen35-35b-a5-tp4-c128-graph:q4_b38_m152 | lm_head | 1 | 0.115365 | 0.115365 | 0.115365 |
| qwen35-35b-a5-tp4-c128-graph:q4_b28_m112 | embedding | 1 | 0.005211 | 0.005211 | 0.005211 |
| qwen35-35b-a5-tp4-c128-graph:q4_b28_m112 | final_norm | 1 | 0.048181 | 0.048181 | 0.048181 |
| qwen35-35b-a5-tp4-c128-graph:q4_b28_m112 | lm_head | 1 | 0.089770 | 0.089770 | 0.089770 |
| qwen35-35b-a5-tp4-c128-graph:q4_b18_m72 | embedding | 1 | 0.003861 | 0.003861 | 0.003861 |
| qwen35-35b-a5-tp4-c128-graph:q4_b18_m72 | final_norm | 1 | 0.048688 | 0.048688 | 0.048688 |
| qwen35-35b-a5-tp4-c128-graph:q4_b18_m72 | lm_head | 1 | 0.087108 | 0.087108 | 0.087108 |
| qwen35-35b-a5-tp4-c128-graph:q4_b12_m48 | embedding | 1 | 0.004316 | 0.004316 | 0.004316 |
| qwen35-35b-a5-tp4-c128-graph:q4_b12_m48 | final_norm | 1 | 0.048807 | 0.048807 | 0.048807 |
| qwen35-35b-a5-tp4-c128-graph:q4_b12_m48 | lm_head | 1 | 0.081369 | 0.081369 | 0.081369 |
| qwen35-35b-a5-tp4-c128-graph:q4_b10_m40 | embedding | 1 | 0.003730 | 0.003730 | 0.003730 |
| qwen35-35b-a5-tp4-c128-graph:q4_b10_m40 | final_norm | 1 | 0.048144 | 0.048144 | 0.048144 |
| qwen35-35b-a5-tp4-c128-graph:q4_b10_m40 | lm_head | 1 | 0.077380 | 0.077380 | 0.077380 |
| qwen35-35b-a5-tp4-c128-graph:q4_b8_m32 | embedding | 1 | 0.003758 | 0.003758 | 0.003758 |
| qwen35-35b-a5-tp4-c128-graph:q4_b8_m32 | final_norm | 1 | 0.046013 | 0.046013 | 0.046013 |
| qwen35-35b-a5-tp4-c128-graph:q4_b8_m32 | lm_head | 1 | 0.077168 | 0.077168 | 0.077168 |
| qwen35-35b-a5-tp4-c128-graph:q4_b4_m16 | embedding | 1 | 0.003379 | 0.003379 | 0.003379 |
| qwen35-35b-a5-tp4-c128-graph:q4_b4_m16 | final_norm | 1 | 0.044782 | 0.044782 | 0.044782 |
| qwen35-35b-a5-tp4-c128-graph:q4_b4_m16 | lm_head | 1 | 0.073216 | 0.073216 | 0.073216 |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | embedding | 84 | 0.003342 | 0.003354 | 0.003503 |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | final_norm | 84 | 0.044109 | 0.044152 | 0.044444 |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | lm_head | 84 | 0.075013 | 0.074908 | 0.076167 |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | embedding | 6 | 0.002201 | 0.002262 | 0.002299 |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | final_norm | 6 | 0.042644 | 0.042531 | 0.043062 |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | lm_head | 6 | 0.072861 | 0.072813 | 0.073381 |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | embedding | 1 | 0.002755 | 0.002755 | 0.002755 |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | final_norm | 1 | 0.042579 | 0.042579 | 0.042579 |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | lm_head | 1 | 0.072404 | 0.072404 | 0.072404 |
| qwen36-a5-tp2-c12:q4_b12_m48 | embedding | 55 | 0.004170 | 0.004186 | 0.004651 |
| qwen36-a5-tp2-c12:q4_b12_m48 | final_norm | 55 | 0.036794 | 0.036682 | 0.037460 |
| qwen36-a5-tp2-c12:q4_b12_m48 | lm_head | 55 | 0.402777 | 0.402984 | 0.405412 |
| qwen36-a5-tp2-c96:q4_b96_m384 | embedding | 24 | 0.005769 | 0.005723 | 0.006566 |
| qwen36-a5-tp2-c96:q4_b96_m384 | final_norm | 24 | 0.040660 | 0.040637 | 0.041410 |
| qwen36-a5-tp2-c96:q4_b96_m384 | lm_head | 24 | 1.198757 | 1.198186 | 1.198974 |
| qwen36-a5-tp2-c1:q4_b1_m4 | embedding | 85 | 0.003458 | 0.003498 | 0.003705 |
| qwen36-a5-tp2-c1:q4_b1_m4 | final_norm | 85 | 0.031253 | 0.031243 | 0.031619 |
| qwen36-a5-tp2-c1:q4_b1_m4 | lm_head | 85 | 0.376379 | 0.376409 | 0.378443 |

Summary: {"case_count": 50, "compared_cases": 13, "failed_cases": 0, "measured_cases": 50, "passed_cases": 2, "source_case_count": 13, "unresolved_cases": 37}
