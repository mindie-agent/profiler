# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "f6e68d5e326ccbc6aade4f62fffbd816b23da500"}.

Variant: `livepre-complete-native-joint-f6e68d5e`. Baseline: null.

Sim 0.8.0; 288 package files; SHA256 `9f88dac92812c58accec2c6416daa0ea181bd7e5d27b43d9046d1e843b7bfe10`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 46 | 29.761551 | 29.663812 | 30.046040 | 29.545482 | -0.73% | compared |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | 11 | 28.125816 | 28.052481 | 28.205823 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | 10 | 23.446893 | 23.178823 | 23.585292 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | 6 | 26.153676 | 25.839757 | 27.872717 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 37 | 41.069081 | 40.940238 | 41.282305 | 40.882155 | -0.46% | compared |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | 16 | 33.619412 | 33.419468 | 33.979959 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | 13 | 23.486220 | 23.362747 | 23.611371 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | 9 | 28.226931 | 28.040600 | 29.858177 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | 7 | 35.013734 | 34.765394 | 36.430748 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | 6 | 37.826433 | 37.533850 | 39.879377 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | 5 | 26.385455 | 25.915717 | 28.428948 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | 4 | 43.281560 | 42.787796 | 45.251624 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | 4 | 30.244200 | 29.664923 | 32.051220 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | 3 | 35.070247 | 34.379047 | 36.534050 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | 2 | 41.543810 | 41.543810 | 43.477069 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | 1 | 44.811275 | 44.811275 | 44.811275 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | 1 | 44.979779 | 44.979779 | 44.979779 | — | — | unresolved: prediction_deferred_by_population_priority |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; without separating that wait, elapsed time does not identify pure link bandwidth. The same observed boundary may calibrate per-call, per-group or payload-regime service responses. Explicit in-sample/heldout declarations are retained separately from contract eligibility; missing evaluation provenance remains not_declared.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 29.761551 | 28.241752 | 1.519799 | 5.11% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | 28.125816 | 26.591383 | 1.534434 | 5.46% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | 23.446893 | 21.955512 | 1.491381 | 6.36% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | 26.153676 | 24.653222 | 1.500454 | 5.74% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 41.069081 | 39.690511 | 1.378570 | 3.36% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | 33.619412 | 32.091259 | 1.528153 | 4.55% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | 23.486220 | 22.012155 | 1.474066 | 6.28% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | 28.226931 | 26.716230 | 1.510701 | 5.35% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | 35.013734 | 33.489845 | 1.523889 | 4.35% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | 37.826433 | 36.321708 | 1.504725 | 3.98% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | 26.385455 | 24.884894 | 1.500561 | 5.69% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | 43.281560 | 41.753200 | 1.528360 | 3.53% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | 30.244200 | 28.749138 | 1.495061 | 4.94% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | 35.070247 | 33.685758 | 1.384489 | 3.95% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | 41.543810 | 40.003616 | 1.540195 | 3.71% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | 44.811275 | 43.263086 | 1.548189 | 3.45% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | 44.979779 | 43.458533 | 1.521246 | 3.38% | not_established | 16 / 1 / 16 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | dense_layer | 0 / 3 | 0.474002 | 0.296531 | 0.829225 | 0.358989 | -24.26% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | moe_layer | 42 / 42 | 0.673523 | 0.590907 | 0.934934 | 0.677822 | +0.64% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | dense_layer | 2 / 3 | 0.619493 | 0.429010 | 1.009248 | 0.414900 | -33.03% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | moe_layer | 42 / 42 | 0.932364 | 0.792325 | 1.381103 | 0.943749 | +1.22% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 31 / 34 | 0.573101 | 0.579816 | 0.610945 | 0.600051 | +4.70% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 11 / 11 | 0.929504 | 0.929149 | 0.937226 | 0.831249 | -10.57% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 33 / 34 | 0.762836 | 0.772892 | 0.829536 | 0.767447 | +0.60% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 11 / 11 | 1.371034 | 1.377786 | 1.396007 | 1.344450 | -1.94% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 0.573101 | 0.542652 | 0.030449 |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 0.929504 | 0.890143 | 0.039361 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 0.762836 | 0.735536 | 0.027300 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 1.371034 | 1.334754 | 0.036279 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | all | 44 | 2024 | 0.656381 | 0.587042 | 0.623380 | +6.19% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 33 | 1518 | 0.565340 | 0.581631 | 0.623380 | +7.18% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 11 | 506 | 0.929504 | 0.927588 | 0.831249 | -10.39% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | all | 44 | 1628 | 0.909285 | 0.788475 | 0.801565 | +1.66% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 33 | 1221 | 0.755369 | 0.773716 | 0.801565 | +3.60% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 11 | 407 | 1.371034 | 1.376707 | 1.344450 | -2.34% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 46 | 0.829225 | 0.724865 | 0.782496 | 0.358989 | -56.71% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 37 | 1.009248 | 0.849777 | 0.965079 | 0.414900 | -58.89% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 4 | 43.224297 | 39.289980 | — | 34.898571 |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | 6 | 3 | 18 | unknown | 4096 | 4 | 43.224297 | 39.289980 | — | 34.898571 |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 4 | 43.224297 | 39.289980 | — | 34.898571 |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 4 | 43.224297 | 39.289980 | — | 34.898571 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 6 | 16 | 96 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | 6 | 6 | 36 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | 6 | 3 | 18 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | 6 | 7 | 42 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | 6 | 10 | 60 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | 6 | 14 | 84 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | 6 | 8 | 48 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | 6 | 11 | 66 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | 6 | 12 | 72 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | 6 | 15 | 90 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
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
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | embedding | 37 | 0.008829 | 0.008820 | 0.009060 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | output_head_preparation | 37 | 0.007358 | 0.007360 | 0.007461 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | final_norm | 37 | 0.136148 | 0.135162 | 0.141542 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | lm_head | 37 | 0.134106 | 0.133942 | 0.135363 |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | embedding | 16 | 0.009413 | 0.009781 | 0.010120 |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | output_head_preparation | 16 | 0.005665 | 0.005680 | 0.005820 |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | final_norm | 16 | 0.140800 | 0.139463 | 0.145103 |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | lm_head | 16 | 0.118555 | 0.119532 | 0.122162 |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | embedding | 13 | 0.003308 | 0.003280 | 0.003540 |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | output_head_preparation | 13 | 0.004592 | 0.004580 | 0.004820 |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | final_norm | 13 | 0.111430 | 0.110242 | 0.114462 |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | lm_head | 13 | 0.091983 | 0.092142 | 0.092762 |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | embedding | 9 | 0.005600 | 0.005561 | 0.005980 |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | output_head_preparation | 9 | 0.004851 | 0.004860 | 0.004980 |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | final_norm | 9 | 0.130892 | 0.127222 | 0.152443 |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | lm_head | 9 | 0.115880 | 0.115882 | 0.117903 |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | embedding | 7 | 0.006106 | 0.006080 | 0.006260 |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | output_head_preparation | 7 | 0.005786 | 0.005780 | 0.005940 |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | final_norm | 7 | 0.147500 | 0.141523 | 0.166983 |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | lm_head | 7 | 0.117742 | 0.118062 | 0.119462 |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | embedding | 6 | 0.008247 | 0.008350 | 0.008440 |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | output_head_preparation | 6 | 0.005980 | 0.006000 | 0.006120 |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | final_norm | 6 | 0.132472 | 0.132692 | 0.133303 |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | lm_head | 6 | 0.125696 | 0.125943 | 0.126943 |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | embedding | 5 | 0.004268 | 0.004281 | 0.004300 |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | output_head_preparation | 5 | 0.004024 | 0.004080 | 0.004080 |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | final_norm | 5 | 0.120771 | 0.119742 | 0.128023 |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | lm_head | 5 | 0.106558 | 0.106382 | 0.107562 |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | embedding | 4 | 0.009325 | 0.009320 | 0.010880 |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | output_head_preparation | 4 | 0.006905 | 0.006840 | 0.007120 |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | final_norm | 4 | 0.134823 | 0.134732 | 0.135582 |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | lm_head | 4 | 0.128772 | 0.128682 | 0.130323 |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | embedding | 4 | 0.006780 | 0.006680 | 0.007180 |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | output_head_preparation | 4 | 0.004225 | 0.004280 | 0.004380 |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | final_norm | 4 | 0.129198 | 0.128493 | 0.132643 |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | lm_head | 4 | 0.111252 | 0.111482 | 0.112162 |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | embedding | 3 | 0.006673 | 0.006720 | 0.006720 |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | output_head_preparation | 3 | 0.005847 | 0.005840 | 0.005920 |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | final_norm | 3 | 0.137029 | 0.133223 | 0.145142 |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | lm_head | 3 | 0.121856 | 0.121482 | 0.122883 |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | embedding | 2 | 0.009030 | 0.009030 | 0.009220 |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | output_head_preparation | 2 | 0.007870 | 0.007870 | 0.008040 |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | final_norm | 2 | 0.137733 | 0.137733 | 0.138843 |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | lm_head | 2 | 0.123722 | 0.123722 | 0.123742 |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | embedding | 1 | 0.010040 | 0.010040 | 0.010040 |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | output_head_preparation | 1 | 0.007760 | 0.007760 | 0.007760 |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | final_norm | 1 | 0.137523 | 0.137523 | 0.137523 |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | lm_head | 1 | 0.125983 | 0.125983 | 0.125983 |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | embedding | 1 | 0.008781 | 0.008781 | 0.008781 |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | output_head_preparation | 1 | 0.007660 | 0.007660 | 0.007660 |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | final_norm | 1 | 0.136902 | 0.136902 | 0.136902 |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | lm_head | 1 | 0.131863 | 0.131863 | 0.131863 |

Summary: {"case_count": 17, "compared_cases": 2, "failed_cases": 0, "measured_cases": 17, "passed_cases": 2, "source_case_count": 2, "unresolved_cases": 15}
