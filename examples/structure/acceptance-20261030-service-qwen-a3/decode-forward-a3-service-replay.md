# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "2f48346b"}.

Variant: `a3-observable-service-2f48346b`. Baseline: null.

Sim 0.8.0; 276 package files; SHA256 `e71d76a0e8fb32f59648503ffa653c55a08cf912e081941a4af9c62e61905a24`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 220 | 6.713782 | 6.664787 | 6.922921 | 5.972107 | -11.05% | compared |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 3 | 3.240302 | 3.278234 | 3.410932 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 3 | 3.363853 | 3.379593 | 3.466951 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 1 | 3.812064 | 3.812064 | 3.812064 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 1 | 2.978001 | 2.978001 | 2.978001 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 1 | 4.690486 | 4.690486 | 4.690486 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 235 | 4.807080 | 4.779005 | 4.992080 | 4.173895 | -13.17% | compared |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | 3 | 3.844777 | 3.280615 | 5.439251 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 246 | 3.476353 | 3.437971 | 3.655687 | 3.195859 | -8.07% | compared |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | 4 | 3.375663 | 3.346474 | 3.556049 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | 3 | 3.190596 | 3.244875 | 3.293894 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 254 | 3.180250 | 3.127828 | 3.431912 | 3.237990 | +1.82% | compared |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 49 | 69.556298 | 69.488848 | 69.830375 | 55.528929 | -20.17% | compared |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | 4 | 56.950323 | 56.982838 | 57.378767 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | 3 | 56.846876 | 56.895876 | 57.002119 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | 2 | 68.632741 | 68.632741 | 68.639131 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | 2 | 58.058190 | 58.058190 | 58.239184 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | 1 | 57.387626 | 57.387626 | 57.387626 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 44 | 57.639270 | 57.561540 | 58.994579 | 36.987368 | -35.83% | compared |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | 4 | 57.124636 | 57.281174 | 57.499588 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 44 | 57.817112 | 57.597031 | 59.091621 | 36.987368 | -36.03% | compared |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | 9 | 57.713255 | 57.524210 | 58.619531 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 46 | 29.761551 | 29.663812 | 30.046040 | 37.342291 | +25.47% | compared |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | 11 | 28.125816 | 28.052481 | 28.205823 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | 10 | 23.446893 | 23.178823 | 23.585292 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | 6 | 26.153676 | 25.839757 | 27.872717 | — | — | unresolved: prediction_deferred_by_population_priority |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; without separating that wait, elapsed time does not identify pure link bandwidth. The same observed boundary may calibrate per-call, per-group or payload-regime service responses. Explicit in-sample/heldout declarations are retained separately from contract eligibility; missing evaluation provenance remains not_declared.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 6.713782 | 6.584489 | 0.129293 | 1.93% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 3.240302 | 3.098912 | 0.141390 | 4.36% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 3.363853 | 3.219977 | 0.143876 | 4.28% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 3.812064 | 3.685928 | 0.126136 | 3.31% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 2.978001 | 2.829064 | 0.148937 | 5.00% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 4.690486 | 4.563168 | 0.127318 | 2.71% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 4.807080 | 4.678044 | 0.129036 | 2.68% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | 3.844777 | 3.703579 | 0.141197 | 3.67% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 3.476353 | 3.332731 | 0.143622 | 4.13% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | 3.375663 | 3.233090 | 0.142573 | 4.22% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | 3.190596 | 3.049126 | 0.141471 | 4.43% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 3.180250 | 3.035460 | 0.144790 | 4.55% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 69.556298 | 66.970324 | 2.585974 | 3.72% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | 56.950323 | 54.416393 | 2.533930 | 4.45% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | 56.846876 | 54.171133 | 2.675742 | 4.71% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | 68.632741 | 65.996625 | 2.636115 | 3.84% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | 58.058190 | 55.387721 | 2.670469 | 4.60% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | 57.387626 | 54.748359 | 2.639267 | 4.60% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 57.639270 | 55.026876 | 2.612393 | 4.53% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | 57.124636 | 54.590343 | 2.534293 | 4.44% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 57.817112 | 55.202675 | 2.614437 | 4.52% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | 57.713255 | 55.178693 | 2.534562 | 4.39% | not_established | 16 / 1 / 16 | auto / full |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 29.761551 | 28.241752 | 1.519799 | 5.11% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | 28.125816 | 26.591383 | 1.534434 | 5.46% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | 23.446893 | 21.955512 | 1.491381 | 6.36% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | 26.153676 | 24.653222 | 1.500454 | 5.74% | not_established | 16 / 1 / 16 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | dense_layer | 0 / 1 | 0.838259 | 0.838259 | 0.838259 | 0.675439 | -19.42% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | moe_layer | 2 / 3 | 1.958234 | 1.906321 | 2.172615 | 1.745449 | -10.87% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | dense_layer | 0 / 1 | 0.849301 | 0.849301 | 0.849301 | 0.611607 | -27.99% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | moe_layer | 2 / 3 | 1.318979 | 1.314317 | 1.453488 | 1.163836 | -11.76% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | dense_layer | 0 / 1 | 0.798719 | 0.798719 | 0.798719 | 0.564511 | -29.32% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | moe_layer | 2 / 3 | 0.892274 | 0.900944 | 0.968316 | 0.853386 | -4.36% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | dense_layer | 0 / 1 | 0.842561 | 0.842561 | 0.842561 | 0.569992 | -32.35% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | moe_layer | 2 / 3 | 0.778970 | 0.789438 | 0.835939 | 0.861526 | +10.60% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | dense_layer | 0 / 3 | 0.646681 | 0.655584 | 0.670978 | 0.462974 | -28.41% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | moe_layer | 0 / 75 | 0.901497 | 0.866973 | 1.013966 | 0.721867 | -19.93% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | dense_layer | 0 / 3 | 0.573069 | 0.577426 | 0.585758 | 0.357878 | -37.55% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | moe_layer | 0 / 75 | 0.745549 | 0.745723 | 0.781082 | 0.478850 | -35.77% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | dense_layer | 0 / 3 | 0.587706 | 0.567711 | 0.627936 | 0.357878 | -39.11% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | moe_layer | 0 / 75 | 0.747336 | 0.742162 | 0.785962 | 0.478850 | -35.93% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | dense_layer | 0 / 3 | 0.474002 | 0.296531 | 0.829225 | 0.429322 | -9.43% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | moe_layer | 11 / 42 | 0.673523 | 0.590907 | 0.934934 | 0.858436 | +27.45% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 2 / 3 | 1.513448 | 1.795764 | 1.906321 | 1.393651 | -7.92% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 0 / 1 | 2.172615 | 2.172615 | 2.172615 | 1.730833 | -20.33% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | kda | 2 / 3 | 1.117583 | 1.189132 | 1.314317 | 0.989594 | -11.45% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | mla | 0 / 1 | 1.453488 | 1.453488 | 1.453488 | 1.134333 | -21.96% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | kda | 2 / 3 | 0.835742 | 0.807561 | 0.900944 | 0.772509 | -7.57% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | mla | 0 / 1 | 0.968316 | 0.968316 | 0.968316 | 0.807142 | -16.64% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | kda | 1 / 3 | 0.781178 | 0.789438 | 0.842561 | 0.777990 | -0.41% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | mla | 1 / 1 | 0.835939 | 0.835939 | 0.835939 | 0.820598 | -1.84% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | mla | 0 / 78 | 0.891696 | 0.866537 | 1.013966 | 0.711909 | -20.16% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | mla | 0 / 78 | 0.738916 | 0.743060 | 0.781082 | 0.474197 | -35.83% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | mla | 0 / 78 | 0.741196 | 0.741208 | 0.785962 | 0.474197 | -36.02% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 0 / 34 | 0.573101 | 0.579816 | 0.610945 | 0.769601 | +34.29% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 11 / 11 | 0.929504 | 0.929149 | 0.937226 | 1.015987 | +9.30% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 1.513448 | 1.488582 | 0.024866 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 2.172615 | 2.118742 | 0.053873 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | kda | 1.117583 | 1.092787 | 0.024796 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | mla | 1.453488 | 1.399683 | 0.053805 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | kda | 0.835742 | 0.807502 | 0.028239 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | mla | 0.968316 | 0.910224 | 0.058092 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | kda | 0.781178 | 0.752972 | 0.028205 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | mla | 0.835939 | 0.776543 | 0.059396 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | mla | 0.891696 | 0.858594 | 0.033102 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | mla | 0.738916 | 0.705473 | 0.033443 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | mla | 0.741196 | 0.707727 | 0.033469 |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 0.573101 | 0.542652 | 0.030449 |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 0.929504 | 0.890143 | 0.039361 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | all | 3 | 660 | 1.958234 | 1.879452 | 1.752757 | -6.74% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 2 | 440 | 1.851043 | 1.837689 | 1.752757 | -4.62% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 1 | 220 | 2.172615 | 2.172336 | 1.730833 | -20.32% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | all | 3 | 705 | 1.318979 | 1.287515 | 1.178588 | -8.46% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | kda | 2 | 470 | 1.251724 | 1.236346 | 1.178588 | -4.67% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | mla | 1 | 235 | 1.453488 | 1.452451 | 1.134333 | -21.90% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | all | 3 | 738 | 0.892274 | 0.878833 | 0.876509 | -0.26% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | kda | 2 | 492 | 0.854253 | 0.837738 | 0.876509 | +4.63% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | mla | 1 | 246 | 0.968316 | 0.961650 | 0.807142 | -16.07% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | all | 3 | 762 | 0.778970 | 0.760995 | 0.881990 | +15.90% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | kda | 2 | 508 | 0.750486 | 0.714456 | 0.881990 | +23.45% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | mla | 1 | 254 | 0.835939 | 0.799415 | 0.820598 | +2.65% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | all | 77 | 3773 | 0.894563 | 0.866817 | 0.694813 | -19.84% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | mla | 77 | 3773 | 0.894563 | 0.866817 | 0.694813 | -19.84% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | all | 77 | 3388 | 0.740905 | 0.713924 | 0.462191 | -35.26% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | mla | 77 | 3388 | 0.740905 | 0.713924 | 0.462191 | -35.26% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | all | 77 | 3388 | 0.742667 | 0.714665 | 0.462191 | -35.33% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | mla | 77 | 3388 | 0.742667 | 0.714665 | 0.462191 | -35.33% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | all | 44 | 2024 | 0.656381 | 0.587042 | 0.802531 | +36.71% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 33 | 1518 | 0.565340 | 0.581631 | 0.802531 | +37.98% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 11 | 506 | 0.929504 | 0.927588 | 1.015987 | +9.53% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 220 | 0.838259 | 0.793934 | 1.000700 | 0.675439 | -19.42% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 235 | 0.849301 | 0.820683 | 1.000940 | 0.611607 | -27.99% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 246 | 0.798719 | 0.778574 | 0.951541 | 0.564511 | -29.32% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 254 | 0.842561 | 0.814714 | 0.989400 | 0.569992 | -32.35% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 49 | 0.670978 | 0.621032 | 0.820996 | 0.462974 | -31.00% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 44 | 0.585758 | 0.542520 | 0.733755 | 0.357878 | -38.90% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 44 | 0.627936 | 0.549071 | 0.813657 | 0.357878 | -43.01% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 46 | 0.829225 | 0.724865 | 0.782496 | 0.429322 | -48.23% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 1 | 32 | 32 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 1 | 8 | 8 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 1 | 16 | 16 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 1 | 16 | 16 | unknown | 4096 | 16 | 8.646915 | 8.627808 | — | — |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 16 | 8.646915 | 8.627808 | — | — |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 4 | 7.450663 | 7.475983 | — | — |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 4 | 7.450663 | 7.475983 | — | — |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 4 | 7.450663 | 7.475983 | — | — |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 1 | 7.167215 | 7.167215 | — | — |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 6 | 8 | 48 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | 6 | 6 | 36 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | 6 | 3 | 18 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 2 | 81.123653 | 76.399375 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 2 | 81.123653 | 76.399375 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 2 | 80.812579 | 76.184906 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 2 | 80.812579 | 76.184906 | — | 68.544460 |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 4 | 43.224297 | 39.289980 | — | 34.898571 |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | 6 | 3 | 18 | unknown | 4096 | 4 | 43.224297 | 39.289980 | — | 34.898571 |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 4 | 43.224297 | 39.289980 | — | 34.898571 |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 4 | 43.224297 | 39.289980 | — | 34.898571 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | embedding | 220 | 0.009116 | 0.009080 | 0.009420 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | final_norm | 220 | 0.009454 | 0.009280 | 0.009460 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | lm_head | 220 | 0.313890 | 0.313543 | 0.317654 |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | embedding | 3 | 0.009493 | 0.009499 | 0.009760 |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | final_norm | 3 | 0.003600 | 0.003600 | 0.003660 |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | lm_head | 3 | 0.277841 | 0.276815 | 0.280234 |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | embedding | 3 | 0.003020 | 0.002940 | 0.003300 |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | final_norm | 3 | 0.004353 | 0.004400 | 0.004440 |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | lm_head | 3 | 0.284234 | 0.285574 | 0.285794 |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | embedding | 1 | 0.003660 | 0.003660 | 0.003660 |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | final_norm | 1 | 0.004940 | 0.004940 | 0.004940 |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | lm_head | 1 | 0.292854 | 0.292854 | 0.292854 |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | embedding | 1 | 0.002720 | 0.002720 | 0.002720 |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | final_norm | 1 | 0.003840 | 0.003840 | 0.003840 |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | lm_head | 1 | 0.280574 | 0.280574 | 0.280574 |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | embedding | 1 | 0.005100 | 0.005100 | 0.005100 |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | final_norm | 1 | 0.006300 | 0.006300 | 0.006300 |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | lm_head | 1 | 0.317034 | 0.317034 | 0.317034 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | embedding | 235 | 0.005061 | 0.005020 | 0.005320 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | final_norm | 235 | 0.006631 | 0.006500 | 0.006819 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | lm_head | 235 | 0.312556 | 0.312613 | 0.316314 |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | embedding | 3 | 0.009047 | 0.009080 | 0.009300 |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | final_norm | 3 | 0.003587 | 0.003580 | 0.003600 |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | lm_head | 3 | 0.276741 | 0.277055 | 0.278654 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | embedding | 246 | 0.003053 | 0.003040 | 0.003319 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | final_norm | 246 | 0.004334 | 0.004320 | 0.004480 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | lm_head | 246 | 0.284209 | 0.284254 | 0.287035 |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | embedding | 4 | 0.002780 | 0.002780 | 0.002980 |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | final_norm | 4 | 0.003945 | 0.003949 | 0.004000 |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | lm_head | 4 | 0.282285 | 0.282095 | 0.286114 |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | embedding | 3 | 0.009247 | 0.009240 | 0.009300 |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | final_norm | 3 | 0.003627 | 0.003640 | 0.003660 |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | lm_head | 3 | 0.275981 | 0.276014 | 0.276755 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | embedding | 254 | 0.009523 | 0.009420 | 0.009740 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | final_norm | 254 | 0.003637 | 0.003640 | 0.003700 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | lm_head | 254 | 0.275756 | 0.275744 | 0.278314 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | embedding | 49 | 0.006817 | 0.006780 | 0.007080 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | final_norm | 49 | 0.237354 | 0.236984 | 0.239424 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | lm_head | 49 | 0.175891 | 0.175883 | 0.177523 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | embedding | 4 | 0.003640 | 0.003670 | 0.003760 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | final_norm | 4 | 0.214025 | 0.213995 | 0.214944 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | lm_head | 4 | 0.128073 | 0.128013 | 0.129162 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | embedding | 3 | 0.004373 | 0.004380 | 0.004400 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | final_norm | 3 | 0.220524 | 0.221044 | 0.221585 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | lm_head | 3 | 0.144196 | 0.144463 | 0.145003 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | embedding | 2 | 0.009291 | 0.009291 | 0.009360 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | final_norm | 2 | 0.236475 | 0.236475 | 0.239465 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | lm_head | 2 | 0.179673 | 0.179673 | 0.180283 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | embedding | 2 | 0.005621 | 0.005621 | 0.005721 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | final_norm | 2 | 0.222944 | 0.222944 | 0.223365 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | lm_head | 2 | 0.171333 | 0.171333 | 0.171443 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | embedding | 1 | 0.007061 | 0.007061 | 0.007061 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | final_norm | 1 | 0.225365 | 0.225365 | 0.225365 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | lm_head | 1 | 0.163543 | 0.163543 | 0.163543 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | embedding | 44 | 0.004439 | 0.004430 | 0.004660 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | final_norm | 44 | 0.224448 | 0.218014 | 0.222065 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | lm_head | 44 | 0.144133 | 0.144193 | 0.145663 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | embedding | 4 | 0.003600 | 0.003440 | 0.004201 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | final_norm | 4 | 0.213759 | 0.213774 | 0.214284 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | lm_head | 4 | 0.128878 | 0.128733 | 0.129703 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | embedding | 44 | 0.004420 | 0.004410 | 0.004640 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | final_norm | 44 | 0.219680 | 0.218044 | 0.219305 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | lm_head | 44 | 0.144156 | 0.144263 | 0.145303 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | embedding | 9 | 0.003396 | 0.003360 | 0.003940 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | final_norm | 9 | 0.223267 | 0.213164 | 0.302506 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | lm_head | 9 | 0.129758 | 0.129442 | 0.131202 |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | embedding | 46 | 0.006879 | 0.006820 | 0.007060 |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | output_head_preparation | 46 | 0.004287 | 0.004280 | 0.004360 |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | final_norm | 46 | 0.132206 | 0.128833 | 0.142423 |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | lm_head | 46 | 0.110465 | 0.110572 | 0.111682 |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | embedding | 11 | 0.005607 | 0.005561 | 0.005840 |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | output_head_preparation | 11 | 0.004844 | 0.004860 | 0.004940 |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | final_norm | 11 | 0.143830 | 0.135922 | 0.167364 |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | lm_head | 11 | 0.115795 | 0.115463 | 0.116942 |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | embedding | 10 | 0.003252 | 0.003190 | 0.003380 |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | output_head_preparation | 10 | 0.004660 | 0.004630 | 0.004820 |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | final_norm | 10 | 0.115398 | 0.112622 | 0.123683 |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | lm_head | 10 | 0.092292 | 0.092372 | 0.092642 |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | embedding | 6 | 0.004273 | 0.004310 | 0.004440 |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | output_head_preparation | 6 | 0.004027 | 0.004020 | 0.004060 |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | final_norm | 6 | 0.136483 | 0.136783 | 0.153344 |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | lm_head | 6 | 0.105955 | 0.105972 | 0.106962 |

Summary: {"case_count": 26, "compared_cases": 8, "failed_cases": 0, "measured_cases": 26, "passed_cases": 4, "source_case_count": 8, "unresolved_cases": 18}
