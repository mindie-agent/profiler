# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "0e2d144ff6a64e797b37a858b0f88ee3cddda3dc"}.

Variant: `body-default-glm`. Baseline: null.

Sim 0.8.0; 245 package files; SHA256 `a24d0690d120906b430f7670f41f4c443a75a2958c8b49e45d0d87d22840318d`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a3_glm53_dc4k_b2:q1_b2_m2 | 70 | 40.969878 | 40.934812 | 41.046340 | 31.561282 | -22.96% | compared |
| a3_glm53_dc4k_b4:q1_b4_m4 | 67 | 43.437734 | 43.436892 | 43.597669 | 34.706725 | -20.10% | compared |
| a3_glm53_dc16k_b1:q1_b1_m1 | 74 | 39.112085 | 39.104879 | 39.195917 | 29.717102 | -24.02% | compared |
| a3_glm53_dc4k_b1:q1_b1_m1 | 74 | 38.954827 | 38.942772 | 39.036040 | 29.717102 | -23.71% | compared |
| a3_glm53_dc4k_b8:q1_b8_m8 | 61 | 47.113275 | 47.148578 | 47.401813 | 40.194774 | -14.68% | compared |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 37 | 41.069081 | 40.940238 | 41.282305 | 47.549602 | +15.78% | compared |
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
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 15.683328 | 15.670472 | 15.738329 | 8.594151 | -45.20% | compared |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 53 | 21.067549 | 21.057180 | 21.170037 | 13.131320 | -37.67% | compared |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 46 | 29.761551 | 29.663812 | 30.046040 | 31.686960 | +6.47% | compared |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | 11 | 28.125816 | 28.052481 | 28.205823 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | 10 | 23.446893 | 23.178823 | 23.585292 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | 6 | 26.153676 | 25.839757 | 27.872717 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c2:q6_b2_m12 | 46 | 34.118460 | 33.910318 | 35.073041 | 26.233215 | -23.11% | compared |
| glm53flash-a3-tp16-c2:q6_b1_m6 | 12 | 33.269101 | 33.259625 | 33.460529 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4:q6_b4_m24 | 46 | 39.841313 | 39.798305 | 40.056941 | 31.686960 | -20.47% | compared |
| glm53flash-a3-tp16-c4:q6_b1_m6 | 8 | 33.514305 | 33.637173 | 34.066401 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4:q6_b3_m18 | 4 | 36.347326 | 36.075101 | 37.438868 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4:q6_b2_m12 | 3 | 35.088708 | 34.649152 | 36.996219 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 27 | 57.589679 | 57.572611 | 57.734379 | 40.528582 | -29.63% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a3_glm53_dc4k_b2:q1_b2_m2 | 40.969878 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b4:q1_b4_m4 | 43.437734 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc16k_b1:q1_b1_m1 | 39.112085 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b1:q1_b1_m1 | 38.954827 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b8:q1_b8_m8 | 47.113275 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
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
| glm53flash-a5-tp8-c1:q4_b1_m4 | 15.683328 | 15.421254 | 0.262074 | 1.67% | not_established | 8 / 1 / 1 | none / full |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 21.067549 | 20.805273 | 0.262276 | 1.24% | not_established | 8 / 1 / 1 | none / full |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 29.761551 | 28.241752 | 1.519799 | 5.11% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | 28.125816 | 26.591383 | 1.534434 | 5.46% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | 23.446893 | 21.955512 | 1.491381 | 6.36% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | 26.153676 | 24.653222 | 1.500454 | 5.74% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c2:q6_b2_m12 | 34.118460 | 32.625252 | 1.493208 | 4.38% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c2:q6_b1_m6 | 33.269101 | 31.831689 | 1.437413 | 4.32% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4:q6_b4_m24 | 39.841313 | 38.323774 | 1.517539 | 3.81% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4:q6_b1_m6 | 33.514305 | 32.078401 | 1.435903 | 4.28% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4:q6_b3_m18 | 36.347326 | 34.841555 | 1.505771 | 4.14% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c4:q6_b2_m12 | 35.088708 | 33.595631 | 1.493077 | 4.26% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 57.589679 | 57.354872 | 0.234807 | 0.41% | not_established | 8 / 1 / 1 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b2:q1_b2_m2 | dense_layer | 3 / 3 | 0.403290 | 0.407802 | 0.410515 | 0.355022 | -11.97% |
| a3_glm53_dc4k_b2:q1_b2_m2 | moe_layer | 0 / 75 | 0.529285 | 0.509096 | 0.601701 | 0.406616 | -23.18% |
| a3_glm53_dc4k_b4:q1_b4_m4 | dense_layer | 3 / 3 | 0.401821 | 0.399081 | 0.411774 | 0.357665 | -10.99% |
| a3_glm53_dc4k_b4:q1_b4_m4 | moe_layer | 0 / 75 | 0.562175 | 0.540899 | 0.637391 | 0.448450 | -20.23% |
| a3_glm53_dc16k_b1:q1_b1_m1 | dense_layer | 3 / 3 | 0.396276 | 0.393697 | 0.402033 | 0.353700 | -10.74% |
| a3_glm53_dc16k_b1:q1_b1_m1 | moe_layer | 0 / 75 | 0.504482 | 0.483485 | 0.576161 | 0.382080 | -24.26% |
| a3_glm53_dc4k_b1:q1_b1_m1 | dense_layer | 3 / 3 | 0.387506 | 0.384723 | 0.394250 | 0.353700 | -8.72% |
| a3_glm53_dc4k_b1:q1_b1_m1 | moe_layer | 0 / 75 | 0.503075 | 0.484378 | 0.566864 | 0.382080 | -24.05% |
| a3_glm53_dc4k_b8:q1_b8_m8 | dense_layer | 3 / 3 | 0.416038 | 0.413257 | 0.424403 | 0.365053 | -12.25% |
| a3_glm53_dc4k_b8:q1_b8_m8 | moe_layer | 49 / 75 | 0.610549 | 0.587718 | 0.698046 | 0.521328 | -14.61% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | dense_layer | 1 / 3 | 0.619493 | 0.429010 | 1.009248 | 0.485143 | -21.69% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | moe_layer | 11 / 42 | 0.932364 | 0.792325 | 1.381103 | 1.097480 | +17.71% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | dense_layer | 0 / 3 | 0.306520 | 0.263452 | 0.422210 | 0.120597 | -60.66% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | moe_layer | 0 / 42 | 0.351495 | 0.302211 | 0.492130 | 0.196009 | -44.24% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | dense_layer | 0 / 3 | 0.313856 | 0.240144 | 0.464978 | 0.139919 | -55.42% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | moe_layer | 0 / 42 | 0.479167 | 0.424416 | 0.634057 | 0.302656 | -36.84% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | dense_layer | 0 / 3 | 0.474002 | 0.296531 | 0.829225 | 0.365422 | -22.91% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | moe_layer | 12 / 42 | 0.673523 | 0.590907 | 0.934934 | 0.728350 | +8.14% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | dense_layer | 0 / 3 | 0.588732 | 0.573221 | 0.632444 | 0.340224 | -42.21% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | moe_layer | 7 / 42 | 0.769068 | 0.710639 | 0.953812 | 0.600299 | -21.94% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | dense_layer | 0 / 3 | 0.615360 | 0.614060 | 0.624559 | 0.365422 | -40.62% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | moe_layer | 31 / 42 | 0.903418 | 0.812825 | 1.168139 | 0.728350 | -19.38% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | dense_layer | 0 / 3 | 0.582792 | 0.572780 | 0.603622 | 0.432008 | -25.87% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | moe_layer | 31 / 42 | 1.329532 | 1.010557 | 2.233884 | 0.934108 | -29.74% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 3 / 78 | 0.524439 | 0.508658 | 0.601701 | 0.404632 | -22.84% |
| a3_glm53_dc4k_b4:q1_b4_m4 | mla | 3 / 78 | 0.556008 | 0.540114 | 0.637391 | 0.444958 | -19.97% |
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 3 / 78 | 0.500321 | 0.482807 | 0.576161 | 0.380988 | -23.85% |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 3 / 78 | 0.498630 | 0.484310 | 0.566864 | 0.380988 | -23.59% |
| a3_glm53_dc4k_b8:q1_b8_m8 | mla | 52 / 78 | 0.603068 | 0.587228 | 0.698046 | 0.515318 | -14.55% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 1 / 34 | 0.762836 | 0.772892 | 0.829536 | 0.996652 | +30.65% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 11 / 11 | 1.371034 | 1.377786 | 1.396007 | 1.242129 | -9.40% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 0 / 34 | 0.301047 | 0.298533 | 0.305713 | 0.183384 | -39.08% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0 / 11 | 0.495159 | 0.491361 | 0.512266 | 0.214465 | -56.69% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 0 / 34 | 0.412816 | 0.421465 | 0.428909 | 0.280726 | -32.00% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 0 / 11 | 0.639166 | 0.633990 | 0.657478 | 0.326057 | -48.99% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 2 / 34 | 0.573101 | 0.579816 | 0.610945 | 0.673830 | +17.58% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 10 / 11 | 0.929504 | 0.929149 | 0.937226 | 0.797885 | -14.16% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | kda | 7 / 34 | 0.693117 | 0.694880 | 0.733617 | 0.558904 | -19.36% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | mla | 0 / 11 | 0.954644 | 0.951023 | 0.969821 | 0.657316 | -31.15% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | kda | 31 / 34 | 0.792874 | 0.809037 | 0.816091 | 0.673830 | -15.01% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | mla | 0 / 11 | 1.166537 | 1.165343 | 1.172462 | 0.797885 | -31.60% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | kda | 31 / 34 | 0.971208 | 1.008853 | 1.013906 | 0.839112 | -13.60% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | mla | 0 / 11 | 2.233423 | 2.233777 | 2.258570 | 1.090797 | -51.16% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 0.524439 | — | — |
| a3_glm53_dc4k_b4:q1_b4_m4 | mla | 0.556008 | — | — |
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 0.500321 | — | — |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 0.498630 | — | — |
| a3_glm53_dc4k_b8:q1_b8_m8 | mla | 0.603068 | — | — |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 0.762836 | 0.735536 | 0.027300 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 1.371034 | 1.334754 | 0.036279 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 0.301047 | 0.295812 | 0.005235 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0.495159 | 0.487604 | 0.007555 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 0.412816 | 0.407564 | 0.005253 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 0.639166 | 0.631647 | 0.007519 |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 0.573101 | 0.542652 | 0.030449 |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 0.929504 | 0.890143 | 0.039361 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | kda | 0.693117 | 0.662930 | 0.030187 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | mla | 0.954644 | 0.916877 | 0.037767 |
| glm53flash-a3-tp16-c4:q6_b4_m24 | kda | 0.792874 | 0.762296 | 0.030578 |
| glm53flash-a3-tp16-c4:q6_b4_m24 | mla | 1.166537 | 1.127792 | 0.038745 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | kda | 0.971208 | 0.966664 | 0.004543 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | mla | 2.233423 | 2.226208 | 0.007215 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b2:q1_b2_m2 | all | 77 | 5390 | 0.525918 | 0.508590 | 0.393197 | -22.69% |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 77 | 5390 | 0.525918 | 0.508590 | 0.393197 | -22.69% |
| a3_glm53_dc4k_b4:q1_b4_m4 | all | 77 | 5159 | 0.557881 | 0.540369 | 0.434830 | -19.53% |
| a3_glm53_dc4k_b4:q1_b4_m4 | mla | 77 | 5159 | 0.557881 | 0.540369 | 0.434830 | -19.53% |
| a3_glm53_dc16k_b1:q1_b1_m1 | all | 77 | 5698 | 0.501597 | 0.482860 | 0.368761 | -23.63% |
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 77 | 5698 | 0.501597 | 0.482860 | 0.368761 | -23.63% |
| a3_glm53_dc4k_b1:q1_b1_m1 | all | 77 | 5698 | 0.499986 | 0.484650 | 0.368761 | -23.91% |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 77 | 5698 | 0.499986 | 0.484650 | 0.368761 | -23.91% |
| a3_glm53_dc4k_b8:q1_b8_m8 | all | 77 | 4697 | 0.605388 | 0.586108 | 0.506804 | -13.53% |
| a3_glm53_dc4k_b8:q1_b8_m8 | mla | 77 | 4697 | 0.605388 | 0.586108 | 0.506804 | -13.53% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | all | 44 | 1628 | 0.909285 | 0.788475 | 1.046153 | +32.68% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 33 | 1221 | 0.755369 | 0.773716 | 1.046153 | +35.21% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 11 | 407 | 1.371034 | 1.376707 | 1.242129 | -9.78% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | all | 44 | 2860 | 0.346822 | 0.301057 | 0.189460 | -37.07% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 33 | 2145 | 0.297376 | 0.298344 | 0.189460 | -36.50% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 11 | 715 | 0.495159 | 0.490270 | 0.214465 | -56.26% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | all | 44 | 2332 | 0.468218 | 0.423968 | 0.294353 | -30.57% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 33 | 1749 | 0.411236 | 0.421213 | 0.294353 | -30.12% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 11 | 583 | 0.639166 | 0.633678 | 0.326057 | -48.55% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | all | 44 | 2024 | 0.656381 | 0.587042 | 0.703676 | +19.87% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 33 | 1518 | 0.565340 | 0.581631 | 0.703676 | +20.98% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 11 | 506 | 0.929504 | 0.927588 | 0.797885 | -13.98% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | all | 44 | 2024 | 0.761223 | 0.671958 | 0.580067 | -13.68% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | kda | 33 | 1518 | 0.696750 | 0.664003 | 0.580067 | -12.64% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | mla | 11 | 506 | 0.954644 | 0.939519 | 0.657316 | -30.04% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | all | 44 | 2024 | 0.890354 | 0.811481 | 0.703676 | -13.28% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | kda | 33 | 1518 | 0.798293 | 0.808226 | 0.703676 | -12.94% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | mla | 11 | 506 | 1.166537 | 1.164423 | 0.797885 | -31.48% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | all | 44 | 1188 | 1.295116 | 1.010385 | 0.878509 | -13.05% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | kda | 33 | 891 | 0.982346 | 1.008593 | 0.878509 | -12.90% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | mla | 11 | 297 | 2.233423 | 2.232883 | 1.090797 | -51.15% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b2:q1_b2_m2 | 70 | 0.410515 | 0.395952 | 0.454831 | 0.355022 | -13.52% |
| a3_glm53_dc4k_b4:q1_b4_m4 | 67 | 0.411774 | 0.407112 | 0.411352 | 0.357665 | -13.14% |
| a3_glm53_dc16k_b1:q1_b1_m1 | 74 | 0.402033 | 0.396682 | 0.411171 | 0.353700 | -12.02% |
| a3_glm53_dc4k_b1:q1_b1_m1 | 74 | 0.394250 | 0.385352 | 0.415732 | 0.353700 | -10.29% |
| a3_glm53_dc4k_b8:q1_b8_m8 | 61 | 0.424403 | 0.422672 | 0.425891 | 0.365053 | -13.98% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 37 | 1.009248 | 0.849777 | 0.965079 | 0.485143 | -51.93% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 0.422210 | 0.438253 | 0.487926 | 0.120597 | -71.44% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 53 | 0.464978 | 0.474452 | 0.536593 | 0.139919 | -69.91% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 46 | 0.829225 | 0.724865 | 0.782496 | 0.365422 | -55.93% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | 46 | 0.573221 | 0.501010 | 0.719194 | 0.340224 | -40.65% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | 46 | 0.614060 | 0.582461 | 0.771416 | 0.365422 | -40.49% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 27 | 0.603622 | 0.588892 | 0.680723 | 0.432008 | -28.43% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b2:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 2 | — | — | — | — |
| a3_glm53_dc4k_b4:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 4 | — | — | — | — |
| a3_glm53_dc16k_b1:q1_b1_m1 | 1 | 1 | 1 | unknown | 16384 | 1 | — | — | — | — |
| a3_glm53_dc4k_b1:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 1 | — | — | — | — |
| a3_glm53_dc4k_b8:q1_b8_m8 | 1 | 8 | 8 | unknown | 4096 | 8 | — | — | — | — |
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
| glm53flash-a5-tp8-c1:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 1 | — | 8.534735 | — | 7.355036 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 4 | 4 | 16 | unknown | 4104 | 3 | — | 11.438829 | — | 9.752313 |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 4 | 43.224297 | 39.289980 | — | 34.898571 |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | 6 | 3 | 18 | unknown | 4096 | 4 | 43.224297 | 39.289980 | — | 34.898571 |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 4 | 43.224297 | 39.289980 | — | 34.898571 |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 4 | 43.224297 | 39.289980 | — | 34.898571 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 2 | 51.625998 | 45.879581 | — | 39.789500 |
| glm53flash-a3-tp16-c2:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 2 | 51.625998 | 45.879581 | — | 39.789500 |
| glm53flash-a3-tp16-c4:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 4 | 61.793469 | 60.389517 | — | 48.155870 |
| glm53flash-a3-tp16-c4:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 4 | 61.793469 | 60.389517 | — | 48.155870 |
| glm53flash-a3-tp16-c4:q6_b3_m18 | 6 | 3 | 18 | unknown | 4096 | 4 | 61.793469 | 60.389517 | — | 48.155870 |
| glm53flash-a3-tp16-c4:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 4 | 61.793469 | 60.389517 | — | 48.155870 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 4 | 96 | 384 | unknown | 4104 | 96 | — | 26.457978 | — | 27.999716 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a3_glm53_dc4k_b2:q1_b2_m2 | embedding | 70 | 0.002795 | 0.002780 | 0.003000 |
| a3_glm53_dc4k_b2:q1_b2_m2 | final_norm | 70 | 0.156513 | 0.156497 | 0.158957 |
| a3_glm53_dc4k_b2:q1_b2_m2 | lm_head | 70 | 0.227520 | 0.227626 | 0.229775 |
| a3_glm53_dc4k_b4:q1_b4_m4 | embedding | 67 | 0.003206 | 0.003160 | 0.003420 |
| a3_glm53_dc4k_b4:q1_b4_m4 | final_norm | 67 | 0.157700 | 0.155217 | 0.165517 |
| a3_glm53_dc4k_b4:q1_b4_m4 | lm_head | 67 | 0.246052 | 0.245875 | 0.248355 |
| a3_glm53_dc16k_b1:q1_b1_m1 | embedding | 74 | 0.007803 | 0.007780 | 0.007920 |
| a3_glm53_dc16k_b1:q1_b1_m1 | final_norm | 74 | 0.160420 | 0.160087 | 0.166337 |
| a3_glm53_dc16k_b1:q1_b1_m1 | lm_head | 74 | 0.221647 | 0.221575 | 0.223536 |
| a3_glm53_dc4k_b1:q1_b1_m1 | embedding | 74 | 0.007841 | 0.007839 | 0.007960 |
| a3_glm53_dc4k_b1:q1_b1_m1 | final_norm | 74 | 0.153796 | 0.153077 | 0.157037 |
| a3_glm53_dc4k_b1:q1_b1_m1 | lm_head | 74 | 0.216579 | 0.216606 | 0.217935 |
| a3_glm53_dc4k_b8:q1_b8_m8 | embedding | 61 | 0.003748 | 0.003760 | 0.003920 |
| a3_glm53_dc4k_b8:q1_b8_m8 | final_norm | 61 | 0.157658 | 0.157397 | 0.159617 |
| a3_glm53_dc4k_b8:q1_b8_m8 | lm_head | 61 | 0.272210 | 0.272394 | 0.273895 |
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
| glm53flash-a5-tp8-c1:q4_b1_m4 | embedding | 65 | 0.003436 | 0.003402 | 0.003777 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | output_head_preparation | 65 | 0.005408 | 0.005362 | 0.005811 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | final_norm | 65 | 0.034594 | 0.034528 | 0.035106 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | lm_head | 65 | 0.048571 | 0.048453 | 0.049677 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | embedding | 53 | 0.004169 | 0.004090 | 0.004625 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | output_head_preparation | 53 | 0.005233 | 0.005053 | 0.005939 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | final_norm | 53 | 0.036160 | 0.036119 | 0.036702 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | lm_head | 53 | 0.049451 | 0.049313 | 0.050247 |
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
| glm53flash-a5-tp8-c96:q4_b96_m384 | embedding | 27 | 0.005289 | 0.005236 | 0.006251 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | output_head_preparation | 27 | 0.011084 | 0.010990 | 0.011458 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | final_norm | 27 | 0.042626 | 0.042703 | 0.043037 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | lm_head | 27 | 0.160268 | 0.160208 | 0.160486 |

Summary: {"case_count": 31, "compared_cases": 12, "failed_cases": 0, "measured_cases": 31, "passed_cases": 2, "source_case_count": 12, "unresolved_cases": 19}
