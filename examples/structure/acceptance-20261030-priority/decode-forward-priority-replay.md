# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "d9118c6e71ed9c75362c06fc7063be4ab97317ec"}.

Variant: `priority_body_declared_baselines_d9118c6e`. Baseline: null.

Sim 0.8.0; 221 package files; SHA256 `5d7c051180a936039cadc42d39e1d3e7a993d652b322c105b16219de135d5ac6`; package `/Users/maoxx241/code/sim-rewrite-20261027/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 46 | 29.761551 | 29.663812 | 30.046040 | 37.948849 | +27.51% | compared |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | 11 | 28.125816 | 28.052481 | 28.205823 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | 10 | 23.446893 | 23.178823 | 23.585292 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | 6 | 26.153676 | 25.839757 | 27.872717 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 37 | 41.069081 | 40.940238 | 41.282305 | 64.734573 | +57.62% | compared |
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
| glm53flash-a3-tp16-c2:q6_b2_m12 | 46 | 34.118460 | 33.910318 | 35.073041 | 30.804303 | -9.71% | compared |
| glm53flash-a3-tp16-c2:q6_b1_m6 | 12 | 33.269101 | 33.259625 | 33.460529 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4:q6_b4_m24 | 46 | 39.841313 | 39.798305 | 40.056941 | 37.948849 | -4.75% | compared |
| glm53flash-a3-tp16-c4:q6_b1_m6 | 8 | 33.514305 | 33.637173 | 34.066401 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4:q6_b3_m18 | 4 | 36.347326 | 36.075101 | 37.438868 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4:q6_b2_m12 | 3 | 35.088708 | 34.649152 | 36.996219 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 53 | 21.067549 | 21.057180 | 21.170037 | 14.583397 | -30.78% | compared |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 27 | 57.589679 | 57.572611 | 57.734379 | 54.015301 | -6.21% | compared |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 15.683328 | 15.670472 | 15.738329 | 10.029372 | -36.05% | compared |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 63 | 32.555493 | 32.533125 | 32.673798 | 50.998577 | +56.65% | compared |
| v4flash-a3-tp8-c4:q2_b4_m8 | 104 | 32.485961 | 32.416312 | 32.734306 | 27.588757 | -15.07% | compared |
| v4flash-a3-tp8-c4:q2_b1_m2 | 4 | 29.500360 | 29.511530 | 29.660627 | — | — | unresolved: prediction_deferred_by_population_priority |
| v4flash-a3-tp8-c8:q2_b8_m16 | 104 | 37.763131 | 37.868163 | 38.081839 | 35.758309 | -5.31% | compared |
| v4flash-a3-tp8-c8:q2_b2_m4 | 3 | 31.294368 | 31.233516 | 31.612229 | — | — | unresolved: prediction_deferred_by_population_priority |
| v4flash-a3-tp8-c8:q2_b1_m2 | 2 | 29.354813 | 29.354813 | 29.421692 | — | — | unresolved: prediction_deferred_by_population_priority |
| v4flash-a3-tp8-c8:q2_b4_m8 | 2 | 32.488101 | 32.488101 | 32.561889 | — | — | unresolved: prediction_deferred_by_population_priority |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

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
| glm53flash-a3-tp16-c2:q6_b2_m12 | 34.118460 | 32.625252 | 1.493208 | 4.38% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c2:q6_b1_m6 | 33.269101 | 31.831689 | 1.437413 | 4.32% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4:q6_b4_m24 | 39.841313 | 38.323774 | 1.517539 | 3.81% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4:q6_b1_m6 | 33.514305 | 32.078401 | 1.435903 | 4.28% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4:q6_b3_m18 | 36.347326 | 34.841555 | 1.505771 | 4.14% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4:q6_b2_m12 | 35.088708 | 33.595631 | 1.493077 | 4.26% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 21.067549 | 20.805273 | 0.262276 | 1.24% | not_established | 8 / 1 / 1 | none / full |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 57.589679 | 57.354872 | 0.234807 | 0.41% | not_established | 8 / 1 / 1 | none / full |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 15.683328 | 15.421254 | 0.262074 | 1.67% | not_established | 8 / 1 / 1 | none / full |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 32.555493 | — | — | — | FULL_DECODE_ONLY | 8 / 4 / 32 | auto / full |
| v4flash-a3-tp8-c4:q2_b4_m8 | 32.485961 | 30.611484 | 1.874477 | 5.77% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c4:q2_b1_m2 | 29.500360 | 27.578127 | 1.922233 | 6.52% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c8:q2_b8_m16 | 37.763131 | 36.154075 | 1.609056 | 4.26% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c8:q2_b2_m4 | 31.294368 | 29.525103 | 1.769265 | 5.65% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c8:q2_b1_m2 | 29.354813 | 27.413822 | 1.940991 | 6.61% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c8:q2_b4_m8 | 32.488101 | 30.755604 | 1.732496 | 5.33% | not_established | 8 / 1 / 8 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | dense_layer | 0 / 3 | 0.474002 | 0.296531 | 0.829225 | 0.447419 | -5.61% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | moe_layer | 11 / 42 | 0.673523 | 0.590907 | 0.934934 | 0.871586 | +29.41% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | dense_layer | 0 / 3 | 0.619493 | 0.429010 | 1.009248 | 0.766988 | +23.81% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | moe_layer | 7 / 42 | 0.932364 | 0.792325 | 1.381103 | 1.486514 | +59.43% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | dense_layer | 0 / 3 | 0.588732 | 0.573221 | 0.632444 | 0.399567 | -32.13% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | moe_layer | 31 / 42 | 0.769068 | 0.710639 | 0.953812 | 0.704895 | -8.34% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | dense_layer | 0 / 3 | 0.615360 | 0.614060 | 0.624559 | 0.447419 | -27.29% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | moe_layer | 31 / 42 | 0.903418 | 0.812825 | 1.168139 | 0.871586 | -3.52% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | dense_layer | 0 / 3 | 0.313856 | 0.240144 | 0.464978 | 0.164993 | -47.43% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | moe_layer | 0 / 42 | 0.479167 | 0.424416 | 0.634057 | 0.335439 | -30.00% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | dense_layer | 3 / 3 | 0.582792 | 0.572780 | 0.603622 | 0.639262 | +9.69% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | moe_layer | 0 / 42 | 1.329532 | 1.010557 | 2.233884 | 1.240417 | -6.70% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | dense_layer | 0 / 3 | 0.306520 | 0.263452 | 0.422210 | 0.144696 | -52.79% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | moe_layer | 0 / 42 | 0.351495 | 0.302211 | 0.492130 | 0.228459 | -35.00% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | dense_layer | 1 / 1 | 0.257923 | 0.257923 | 0.257923 | 0.226829 | -12.06% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | moe_layer | 1 / 92 | 0.351316 | 0.341372 | 0.378042 | 0.551867 | +57.09% |
| v4flash-a3-tp8-c4:q2_b4_m8 | moe_layer | 20 / 43 | 0.754333 | 0.756827 | 0.850173 | 0.641599 | -14.94% |
| v4flash-a3-tp8-c8:q2_b8_m16 | moe_layer | 43 / 43 | 0.877069 | 0.807240 | 0.979574 | 0.831589 | -5.19% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 0 / 34 | 0.573101 | 0.579816 | 0.610945 | 0.825780 | +44.09% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 11 / 11 | 0.929504 | 0.929149 | 0.937226 | 0.897486 | -3.44% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 0 / 34 | 0.762836 | 0.772892 | 0.829536 | 1.396737 | +83.10% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 7 / 11 | 1.371034 | 1.377786 | 1.396007 | 1.567773 | +14.35% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | kda | 31 / 34 | 0.693117 | 0.694880 | 0.733617 | 0.672569 | -2.96% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | mla | 0 / 11 | 0.954644 | 0.951023 | 0.969821 | 0.721543 | -24.42% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | kda | 31 / 34 | 0.792874 | 0.809037 | 0.816091 | 0.825780 | +4.15% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | mla | 0 / 11 | 1.166537 | 1.165343 | 1.172462 | 0.897486 | -23.06% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 0 / 34 | 0.412816 | 0.421465 | 0.428909 | 0.317761 | -23.03% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 0 / 11 | 0.639166 | 0.633990 | 0.657478 | 0.343594 | -46.24% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | kda | 3 / 34 | 0.971208 | 1.008853 | 1.013906 | 1.143234 | +17.71% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | mla | 0 / 11 | 2.233423 | 2.233777 | 2.258570 | 1.376849 | -38.35% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 0 / 34 | 0.301047 | 0.298533 | 0.305713 | 0.219567 | -27.07% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0 / 11 | 0.495159 | 0.491361 | 0.512266 | 0.233100 | -52.92% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | kda | 1 / 69 | 0.338761 | 0.339556 | 0.344976 | 0.551917 | +62.92% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | mla | 1 / 24 | 0.383520 | 0.376471 | 0.383168 | 0.538179 | +40.33% |
| v4flash-a3-tp8-c4:q2_b4_m8 | mla | 20 / 43 | 0.754333 | 0.756827 | 0.850173 | 0.641599 | -14.94% |
| v4flash-a3-tp8-c8:q2_b8_m16 | mla | 43 / 43 | 0.877069 | 0.807240 | 0.979574 | 0.831589 | -5.19% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 0.573101 | 0.542652 | 0.030449 |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 0.929504 | 0.890143 | 0.039361 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 0.762836 | 0.735536 | 0.027300 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 1.371034 | 1.334754 | 0.036279 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | kda | 0.693117 | 0.662930 | 0.030187 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | mla | 0.954644 | 0.916877 | 0.037767 |
| glm53flash-a3-tp16-c4:q6_b4_m24 | kda | 0.792874 | 0.762296 | 0.030578 |
| glm53flash-a3-tp16-c4:q6_b4_m24 | mla | 1.166537 | 1.127792 | 0.038745 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 0.412816 | 0.407564 | 0.005253 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 0.639166 | 0.631647 | 0.007519 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | kda | 0.971208 | 0.966664 | 0.004543 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | mla | 2.233423 | 2.226208 | 0.007215 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 0.301047 | 0.295812 | 0.005235 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0.495159 | 0.487604 | 0.007555 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | kda | 0.338761 | — | — |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | mla | 0.383520 | — | — |
| v4flash-a3-tp8-c4:q2_b4_m8 | mla | 0.754333 | 0.711895 | 0.042438 |
| v4flash-a3-tp8-c8:q2_b8_m16 | mla | 0.877069 | 0.840792 | 0.036277 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | all | 44 | 2024 | 0.656381 | 0.587042 | 0.862395 | +46.91% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 33 | 1518 | 0.565340 | 0.581631 | 0.862395 | +48.27% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 11 | 506 | 0.929504 | 0.927588 | 0.897486 | -3.25% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | all | 44 | 1628 | 0.909285 | 0.788475 | 1.457681 | +84.87% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 33 | 1221 | 0.755369 | 0.773716 | 1.457681 | +88.40% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 11 | 407 | 1.371034 | 1.376707 | 1.567773 | +13.88% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | all | 44 | 2024 | 0.761223 | 0.671958 | 0.698988 | +4.02% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | kda | 33 | 1518 | 0.696750 | 0.664003 | 0.698988 | +5.27% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | mla | 11 | 506 | 0.954644 | 0.939519 | 0.721543 | -23.20% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | all | 44 | 2024 | 0.890354 | 0.811481 | 0.862395 | +6.27% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | kda | 33 | 1518 | 0.798293 | 0.808226 | 0.862395 | +6.70% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | mla | 11 | 506 | 1.166537 | 1.164423 | 0.897486 | -22.92% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | all | 44 | 2332 | 0.468218 | 0.423968 | 0.332545 | -21.56% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 33 | 1749 | 0.411236 | 0.421213 | 0.332545 | -21.05% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 11 | 583 | 0.639166 | 0.633678 | 0.343594 | -45.78% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | all | 44 | 1188 | 1.295116 | 1.010385 | 1.192006 | +17.98% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | kda | 33 | 891 | 0.982346 | 1.008593 | 1.192006 | +18.19% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | mla | 11 | 297 | 2.233423 | 2.232883 | 1.376849 | -38.34% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | all | 44 | 2860 | 0.346822 | 0.301057 | 0.226813 | -24.66% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 33 | 2145 | 0.297376 | 0.298344 | 0.226813 | -23.98% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 11 | 715 | 0.495159 | 0.490270 | 0.233100 | -52.45% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | all | 92 | 5796 | 0.351316 | 0.340746 | 0.556542 | +63.33% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | kda | 68 | 4284 | 0.339949 | 0.338622 | 0.556542 | +64.36% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | mla | 24 | 1512 | 0.383520 | 0.374659 | 0.537985 | +43.59% |
| v4flash-a3-tp8-c4:q2_b4_m8 | all | 42 | 4368 | 0.754274 | 0.753685 | 0.644658 | -14.47% |
| v4flash-a3-tp8-c4:q2_b4_m8 | mla | 42 | 4368 | 0.754274 | 0.753685 | 0.644658 | -14.47% |
| v4flash-a3-tp8-c8:q2_b8_m16 | all | 42 | 4368 | 0.878732 | 0.883097 | 0.834819 | -5.47% |
| v4flash-a3-tp8-c8:q2_b8_m16 | mla | 42 | 4368 | 0.878732 | 0.883097 | 0.834819 | -5.47% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 46 | 0.829225 | 0.724865 | 0.782496 | 0.447419 | -46.04% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 37 | 1.009248 | 0.849777 | 0.965079 | 0.766988 | -24.00% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | 46 | 0.573221 | 0.501010 | 0.719194 | 0.399567 | -30.29% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | 46 | 0.614060 | 0.582461 | 0.771416 | 0.447419 | -27.14% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 53 | 0.464978 | 0.474452 | 0.536593 | 0.164993 | -64.52% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 27 | 0.603622 | 0.588892 | 0.680723 | 0.639262 | +5.90% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 0.422210 | 0.438253 | 0.487926 | 0.144696 | -65.73% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 63 | 0.257923 | 0.238298 | 0.250875 | 0.226829 | -12.06% |
| v4flash-a3-tp8-c4:q2_b4_m8 | 104 | 0.756827 | 0.717805 | 0.958641 | 0.557862 | -26.29% |
| v4flash-a3-tp8-c8:q2_b8_m16 | 104 | 0.807240 | 0.766765 | 0.954481 | 0.743230 | -7.93% |

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
| glm53flash-a3-tp16-c2:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 2 | 51.625998 | 45.879581 | — | 39.789500 |
| glm53flash-a3-tp16-c2:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 2 | 51.625998 | 45.879581 | — | 39.789500 |
| glm53flash-a3-tp16-c4:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 4 | 61.793469 | 60.389517 | — | 48.155870 |
| glm53flash-a3-tp16-c4:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 4 | 61.793469 | 60.389517 | — | 48.155870 |
| glm53flash-a3-tp16-c4:q6_b3_m18 | 6 | 3 | 18 | unknown | 4096 | 4 | 61.793469 | 60.389517 | — | 48.155870 |
| glm53flash-a3-tp16-c4:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 4 | 61.793469 | 60.389517 | — | 48.155870 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 4 | 4 | 16 | unknown | 4104 | 3 | — | 11.438829 | — | 9.752313 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 4 | 96 | 384 | unknown | 4104 | 96 | — | 26.457978 | — | 27.999716 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 1 | — | 8.534735 | — | 7.355036 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 1 | 1 | 1 | unknown | 32768 | 1 | 66.586585 | 66.586585 | — | 64.353701 |
| v4flash-a3-tp8-c4:q2_b4_m8 | 2 | 4 | 8 | unknown | 4096 | 4 | 53.936384 | 47.929425 | — | 39.377165 |
| v4flash-a3-tp8-c4:q2_b1_m2 | 2 | 1 | 2 | unknown | 4096 | 4 | 53.936384 | 47.929425 | — | 39.377165 |
| v4flash-a3-tp8-c8:q2_b8_m16 | 2 | 8 | 16 | unknown | 4096 | 8 | 68.120259 | 62.964366 | — | 45.008620 |
| v4flash-a3-tp8-c8:q2_b2_m4 | 2 | 2 | 4 | unknown | 4096 | 8 | 68.120259 | 62.964366 | — | 45.008620 |
| v4flash-a3-tp8-c8:q2_b1_m2 | 2 | 1 | 2 | unknown | 4096 | 8 | 68.120259 | 62.964366 | — | 45.008620 |
| v4flash-a3-tp8-c8:q2_b4_m8 | 2 | 4 | 8 | unknown | 4096 | 8 | 68.120259 | 62.964366 | — | 45.008620 |

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
| glm53flash-a3-tp16-c2:q6_b2_m12 | embedding | 46 | 0.004146 | 0.004110 | 0.004340 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | output_head_preparation | 46 | 0.012194 | 0.012140 | 0.012901 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | final_norm | 46 | 0.136332 | 0.134193 | 0.135443 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | lm_head | 46 | 0.104697 | 0.104482 | 0.105662 |
| glm53flash-a3-tp16-c2:q6_b1_m6 | embedding | 12 | 0.003035 | 0.003010 | 0.003080 |
| glm53flash-a3-tp16-c2:q6_b1_m6 | output_head_preparation | 12 | 0.011463 | 0.011420 | 0.012040 |
| glm53flash-a3-tp16-c2:q6_b1_m6 | final_norm | 12 | 0.129586 | 0.129382 | 0.131623 |
| glm53flash-a3-tp16-c2:q6_b1_m6 | lm_head | 12 | 0.092909 | 0.092882 | 0.094442 |
| glm53flash-a3-tp16-c4:q6_b4_m24 | embedding | 46 | 0.006341 | 0.006300 | 0.006541 |
| glm53flash-a3-tp16-c4:q6_b4_m24 | output_head_preparation | 46 | 0.009118 | 0.009111 | 0.009500 |
| glm53flash-a3-tp16-c4:q6_b4_m24 | final_norm | 46 | 0.140019 | 0.139923 | 0.140562 |
| glm53flash-a3-tp16-c4:q6_b4_m24 | lm_head | 46 | 0.110647 | 0.110692 | 0.112002 |
| glm53flash-a3-tp16-c4:q6_b1_m6 | embedding | 8 | 0.003090 | 0.003070 | 0.003420 |
| glm53flash-a3-tp16-c4:q6_b1_m6 | output_head_preparation | 8 | 0.011517 | 0.011640 | 0.012140 |
| glm53flash-a3-tp16-c4:q6_b1_m6 | final_norm | 8 | 0.128490 | 0.128482 | 0.129062 |
| glm53flash-a3-tp16-c4:q6_b1_m6 | lm_head | 8 | 0.092057 | 0.091752 | 0.095182 |
| glm53flash-a3-tp16-c4:q6_b3_m18 | embedding | 4 | 0.005195 | 0.005220 | 0.005280 |
| glm53flash-a3-tp16-c4:q6_b3_m18 | output_head_preparation | 4 | 0.011690 | 0.011750 | 0.012000 |
| glm53flash-a3-tp16-c4:q6_b3_m18 | final_norm | 4 | 0.138433 | 0.137003 | 0.143083 |
| glm53flash-a3-tp16-c4:q6_b3_m18 | lm_head | 4 | 0.114577 | 0.114972 | 0.115823 |
| glm53flash-a3-tp16-c4:q6_b2_m12 | embedding | 3 | 0.004007 | 0.004020 | 0.004040 |
| glm53flash-a3-tp16-c4:q6_b2_m12 | output_head_preparation | 3 | 0.011967 | 0.011781 | 0.012341 |
| glm53flash-a3-tp16-c4:q6_b2_m12 | final_norm | 3 | 0.132942 | 0.132923 | 0.134182 |
| glm53flash-a3-tp16-c4:q6_b2_m12 | lm_head | 3 | 0.105249 | 0.105182 | 0.105922 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | embedding | 53 | 0.004169 | 0.004090 | 0.004625 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | output_head_preparation | 53 | 0.005233 | 0.005053 | 0.005939 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | final_norm | 53 | 0.036160 | 0.036119 | 0.036702 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | lm_head | 53 | 0.049451 | 0.049313 | 0.050247 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | embedding | 27 | 0.005289 | 0.005236 | 0.006251 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | output_head_preparation | 27 | 0.011084 | 0.010990 | 0.011458 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | final_norm | 27 | 0.042626 | 0.042703 | 0.043037 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | lm_head | 27 | 0.160268 | 0.160208 | 0.160486 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | embedding | 65 | 0.003436 | 0.003402 | 0.003777 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | output_head_preparation | 65 | 0.005408 | 0.005362 | 0.005811 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | final_norm | 65 | 0.034594 | 0.034528 | 0.035106 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | lm_head | 65 | 0.048571 | 0.048453 | 0.049677 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | embedding | 63 | 0.003108 | 0.003075 | 0.003299 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | final_norm | 63 | 0.004363 | 0.004258 | 0.004465 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | lm_head | 63 | 0.092173 | 0.092155 | 0.092665 |
| v4flash-a3-tp8-c4:q2_b4_m8 | embedding | 104 | 0.003734 | 0.003720 | 0.003880 |
| v4flash-a3-tp8-c4:q2_b4_m8 | output_head_preparation | 104 | 0.492855 | 0.492950 | 0.495110 |
| v4flash-a3-tp8-c4:q2_b4_m8 | final_norm | 104 | 0.614302 | 0.614038 | 0.616248 |
| v4flash-a3-tp8-c4:q2_b4_m8 | lm_head | 104 | 0.201138 | 0.201166 | 0.201936 |
| v4flash-a3-tp8-c4:q2_b1_m2 | embedding | 4 | 0.002955 | 0.002930 | 0.003200 |
| v4flash-a3-tp8-c4:q2_b1_m2 | output_head_preparation | 4 | 0.475390 | 0.475930 | 0.477611 |
| v4flash-a3-tp8-c4:q2_b1_m2 | final_norm | 4 | 0.615858 | 0.616248 | 0.617227 |
| v4flash-a3-tp8-c4:q2_b1_m2 | lm_head | 4 | 0.200426 | 0.200636 | 0.201416 |
| v4flash-a3-tp8-c8:q2_b8_m16 | embedding | 104 | 0.005220 | 0.005200 | 0.005439 |
| v4flash-a3-tp8-c8:q2_b8_m16 | output_head_preparation | 104 | 0.500068 | 0.500260 | 0.501970 |
| v4flash-a3-tp8-c8:q2_b8_m16 | final_norm | 104 | 0.622421 | 0.622127 | 0.624627 |
| v4flash-a3-tp8-c8:q2_b8_m16 | lm_head | 104 | 0.201475 | 0.201426 | 0.202496 |
| v4flash-a3-tp8-c8:q2_b2_m4 | embedding | 3 | 0.003326 | 0.003360 | 0.003560 |
| v4flash-a3-tp8-c8:q2_b2_m4 | output_head_preparation | 3 | 0.480110 | 0.480730 | 0.480810 |
| v4flash-a3-tp8-c8:q2_b2_m4 | final_norm | 3 | 0.618168 | 0.617988 | 0.619307 |
| v4flash-a3-tp8-c8:q2_b2_m4 | lm_head | 3 | 0.200469 | 0.200676 | 0.200676 |
| v4flash-a3-tp8-c8:q2_b1_m2 | embedding | 2 | 0.003320 | 0.003320 | 0.003380 |
| v4flash-a3-tp8-c8:q2_b1_m2 | output_head_preparation | 2 | 0.476100 | 0.476100 | 0.476410 |
| v4flash-a3-tp8-c8:q2_b1_m2 | final_norm | 2 | 0.615588 | 0.615588 | 0.617988 |
| v4flash-a3-tp8-c8:q2_b1_m2 | lm_head | 2 | 0.201036 | 0.201036 | 0.201276 |
| v4flash-a3-tp8-c8:q2_b4_m8 | embedding | 2 | 0.003930 | 0.003930 | 0.004040 |
| v4flash-a3-tp8-c8:q2_b4_m8 | output_head_preparation | 2 | 0.493360 | 0.493360 | 0.494010 |
| v4flash-a3-tp8-c8:q2_b4_m8 | final_norm | 2 | 0.613738 | 0.613738 | 0.614068 |
| v4flash-a3-tp8-c8:q2_b4_m8 | lm_head | 2 | 0.201346 | 0.201346 | 0.201676 |

Summary: {"case_count": 33, "compared_cases": 10, "failed_cases": 0, "measured_cases": 33, "passed_cases": 4, "source_case_count": 10, "unresolved_cases": 23}
