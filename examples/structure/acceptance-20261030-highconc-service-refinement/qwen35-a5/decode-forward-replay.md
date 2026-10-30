# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "21c30821d87a757bace8cf6b2fffea2536db643e"}.

Variant: `qwen35-highconc-native-domains-21c30821`. Baseline: {"path": "/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-qwen35-observed-service/decode-forward-service-replay.json", "sha256": "335d557d7de11cf1ff7f5dd6e931f64bc948f90d6ce8c2d10534fd605157af0c", "size_bytes": 6462353}.

Sim 0.8.0; 288 package files; SHA256 `9f88dac92812c58accec2c6416daa0ea181bd7e5d27b43d9046d1e843b7bfe10`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | 76 | 28.584774 | 28.570657 | 28.703784 | 25.902670 | -9.38% | compared |
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
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 84 | 11.551367 | 11.481642 | 11.817997 | 9.857738 | -14.66% | compared |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | 6 | 8.746954 | 8.802646 | 8.838036 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | 1 | 9.699817 | 9.699817 | 9.699817 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | 79 | 21.956845 | 22.000889 | 22.067637 | 19.838785 | -9.65% | compared |
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

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; without separating that wait, elapsed time does not identify pure link bandwidth. The same observed boundary may calibrate per-call, per-group or payload-regime service responses. Explicit in-sample/heldout declarations are retained separately from contract eligibility; missing evaluation provenance remains not_declared.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
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

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | moe_layer | 30 / 40 | 0.714598 | 0.719591 | 0.721924 | 0.647567 | -9.38% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | moe_layer | 29 / 40 | 0.288763 | 0.283062 | 0.299996 | 0.246443 | -14.66% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | moe_layer | 38 / 40 | 0.548900 | 0.545747 | 0.550616 | 0.495970 | -9.64% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | gdn | 30 / 30 | 0.721017 | 0.720076 | 0.722012 | 0.667428 | -7.43% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | gqa | 0 / 10 | 0.695341 | 0.694634 | 0.697229 | 0.587984 | -15.44% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gdn | 29 / 30 | 0.285398 | 0.282353 | 0.284296 | 0.247707 | -13.21% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gqa | 0 / 10 | 0.298857 | 0.298829 | 0.301088 | 0.242653 | -18.81% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | gdn | 29 / 30 | 0.554528 | 0.547070 | 0.552632 | 0.509889 | -8.05% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | gqa | 9 / 10 | 0.532016 | 0.532480 | 0.533989 | 0.454212 | -14.62% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | gdn | 0.721017 | 0.714203 | 0.006814 |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | gqa | 0.695341 | 0.687425 | 0.007916 |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gdn | 0.285398 | 0.274983 | 0.010415 |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gqa | 0.298857 | 0.288526 | 0.010332 |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | gdn | 0.554528 | 0.545195 | 0.009333 |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | gqa | 0.532016 | 0.521478 | 0.010538 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | all | 39 | 2964 | 0.713577 | 0.719167 | 0.667428 | -7.19% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | gdn | 29 | 2204 | 0.719865 | 0.719916 | 0.667428 | -7.29% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | gqa | 10 | 760 | 0.695341 | 0.694129 | 0.587984 | -15.29% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | all | 39 | 3276 | 0.286250 | 0.283215 | 0.247707 | -12.54% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gdn | 29 | 2436 | 0.281903 | 0.282722 | 0.247707 | -12.39% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gqa | 10 | 840 | 0.298857 | 0.299161 | 0.242653 | -18.89% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | all | 39 | 3081 | 0.543137 | 0.545623 | 0.509889 | -6.55% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | gdn | 29 | 2291 | 0.546971 | 0.546708 | 0.509889 | -6.73% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | gqa | 10 | 790 | 0.532016 | 0.532309 | 0.454212 | -14.67% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | 76 | 0.754430 | 0.723774 | 0.856314 | 0.667428 | -11.53% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 84 | 0.386758 | 0.297328 | 0.630548 | 0.247707 | -35.95% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | 79 | 0.773661 | 0.821604 | 0.881730 | 0.509889 | -34.09% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
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

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
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

Summary: {"case_count": 40, "compared_cases": 3, "failed_cases": 0, "measured_cases": 40, "passed_cases": 3, "source_case_count": 3, "unresolved_cases": 37}
