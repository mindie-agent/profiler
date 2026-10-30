# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "5ec8843a7e1711d0333dd59f9aec4f19f4f40363"}.

Variant: `body-runtime5ec8843a-glm`. Baseline: null.

Sim 0.8.0; 261 package files; SHA256 `c8393b666a67919c06c6929112c49eeef8519c4a757e486c59d63938c8db79e9`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 46 | 29.761551 | 29.663812 | 30.046040 | 36.251359 | +21.81% | compared |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 | 11 | 28.125816 | 28.052481 | 28.205823 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 | 10 | 23.446893 | 23.178823 | 23.585292 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 | 6 | 26.153676 | 25.839757 | 27.872717 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 37 | 41.069081 | 40.940238 | 41.282305 | 63.851407 | +55.47% | compared |
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
| glm53flash-a3-tp16-c2:q6_b2_m12 | 46 | 34.118460 | 33.910318 | 35.073041 | 29.433955 | -13.73% | compared |
| glm53flash-a3-tp16-c2:q6_b1_m6 | 12 | 33.269101 | 33.259625 | 33.460529 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4:q6_b4_m24 | 46 | 39.841313 | 39.798305 | 40.056941 | 36.251359 | -9.01% | compared |
| glm53flash-a3-tp16-c4:q6_b1_m6 | 8 | 33.514305 | 33.637173 | 34.066401 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4:q6_b3_m18 | 4 | 36.347326 | 36.075101 | 37.438868 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c4:q6_b2_m12 | 3 | 35.088708 | 34.649152 | 36.996219 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 53 | 21.067549 | 21.057180 | 21.170037 | 14.826715 | -29.62% | compared |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 27 | 57.589679 | 57.572611 | 57.734379 | 61.385314 | +6.59% | compared |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 15.683328 | 15.670472 | 15.738329 | 9.899969 | -36.88% | compared |
| a3_glm53_dc4k_b1:q1_b1_m1 | 74 | 38.954827 | 38.942772 | 39.036040 | 33.636900 | -13.65% | compared |
| a3_glm53_dc4k_b2:q1_b2_m2 | 70 | 40.969878 | 40.934812 | 41.046340 | 35.482501 | -13.39% | compared |
| a3_glm53_dc4k_b4:q1_b4_m4 | 67 | 43.437734 | 43.436892 | 43.597669 | 38.630789 | -11.07% | compared |
| a3_glm53_dc4k_b8:q1_b8_m8 | 61 | 47.113275 | 47.148578 | 47.401813 | 44.124525 | -6.34% | compared |
| a3_glm53_dc16k_b1:q1_b1_m1 | 74 | 39.112085 | 39.104879 | 39.195917 | 33.636900 | -14.00% | compared |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 44 | 57.639270 | 57.561540 | 58.994579 | 36.987368 | -35.83% | compared |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | 4 | 57.124636 | 57.281174 | 57.499588 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 44 | 57.817112 | 57.597031 | 59.091621 | 36.987368 | -36.03% | compared |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | 9 | 57.713255 | 57.524210 | 58.619531 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 49 | 69.556298 | 69.488848 | 69.830375 | 55.528929 | -20.17% | compared |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | 4 | 56.950323 | 56.982838 | 57.378767 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | 3 | 56.846876 | 56.895876 | 57.002119 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | 2 | 68.632741 | 68.632741 | 68.639131 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | 2 | 58.058190 | 58.058190 | 58.239184 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | 1 | 57.387626 | 57.387626 | 57.387626 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 30 | 33.030918 | 33.026482 | 33.164019 | 22.985651 | -30.41% | compared |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | 4 | 18.010107 | 17.896268 | 18.412903 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | 3 | 15.697300 | 15.704795 | 15.723134 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | 2 | 24.984322 | 24.984322 | 25.001368 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | 1 | 33.211164 | 33.211164 | 33.211164 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | 1 | 32.232000 | 32.232000 | 32.232000 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | 1 | 31.922655 | 31.922655 | 31.922655 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | 1 | 21.416720 | 21.416720 | 21.416720 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 32 | 33.616091 | 33.625860 | 33.709694 | 23.173084 | -31.07% | compared |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | 2 | 29.255343 | 29.255343 | 29.307106 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | 2 | 21.440818 | 21.440818 | 21.440852 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | 2 | 15.623967 | 15.623967 | 15.655241 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | 1 | 33.357579 | 33.357579 | 33.357579 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | 1 | 32.536283 | 32.536283 | 32.536283 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | 1 | 24.989969 | 24.989969 | 24.989969 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | 1 | 17.717363 | 17.717363 | 17.717363 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 31 | 37.668964 | 37.665316 | 37.761150 | 27.808326 | -26.18% | compared |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | 2 | 37.705175 | 37.705175 | 37.843605 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | 2 | 37.467978 | 37.467978 | 38.254596 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | 1 | 38.396873 | 38.396873 | 38.396873 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | 1 | 38.002127 | 38.002127 | 38.002127 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 35 | 38.713189 | 38.721850 | 38.759233 | 28.187557 | -27.19% | compared |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | 1 | 38.635279 | 38.635279 | 38.635279 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 11 | 21.418246 | 21.408145 | 21.432068 | 13.705018 | -36.01% | compared |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | 9 | 15.589915 | 15.582603 | 15.642063 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | 3 | 17.682321 | 17.672472 | 17.709316 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 31 | 46.528233 | 46.498735 | 46.644535 | 36.892480 | -20.71% | compared |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 30 | 28.833324 | 28.828410 | 28.884507 | 19.581842 | -32.09% | compared |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | 3 | 25.112799 | 25.067088 | 25.282855 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | 2 | 21.340235 | 21.340235 | 21.389070 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | 2 | 18.881633 | 18.881633 | 19.871570 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | 1 | 16.092148 | 16.092148 | 16.092148 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | 50 | 53.893389 | 53.870786 | 54.020920 | 49.637449 | -7.90% | compared |
| a3_glm53flash_tp16_aclgraph_c16:q6_b1_m6 | 4 | 33.477328 | 33.400787 | 33.975338 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c16:q6_b12_m72 | 4 | 52.671202 | 52.568690 | 53.565410 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c16:q6_b2_m12 | 3 | 33.945585 | 33.337166 | 35.257205 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c16:q6_b8_m48 | 2 | 47.322035 | 47.322035 | 48.209823 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c16:q6_b4_m24 | 1 | 39.385447 | 39.385447 | 39.385447 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c16:q6_b6_m36 | 1 | 45.421267 | 45.421267 | 45.421267 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | 49 | 69.360606 | 69.418407 | 69.527669 | 65.399673 | -5.71% | compared |
| a3_glm53flash_tp16_aclgraph_c32:q6_b12_m72 | 5 | 52.894180 | 53.227163 | 53.859016 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b1_m6 | 3 | 33.667439 | 33.175563 | 34.874096 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b24_m144 | 3 | 63.044113 | 62.507149 | 64.216403 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b16_m96 | 2 | 54.273544 | 54.273544 | 54.610131 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b8_m48 | 1 | 46.500390 | 46.500390 | 46.500390 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b6_m36 | 1 | 46.450648 | 46.450648 | 46.450648 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c32:q6_b2_m12 | 1 | 33.133282 | 33.133282 | 33.133282 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | 47 | 97.375106 | 97.486768 | 97.895096 | 97.858272 | +0.50% | compared |
| a3_glm53flash_tp16_aclgraph_c64:q6_b1_m6 | 6 | 33.161849 | 33.128011 | 33.585871 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b48_m288 | 3 | 80.931137 | 80.983779 | 82.029499 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b6_m36 | 3 | 45.865343 | 46.344766 | 46.510429 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b32_m192 | 2 | 68.165322 | 68.165322 | 68.192002 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b24_m144 | 2 | 61.995899 | 61.995899 | 62.736414 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b16_m96 | 2 | 53.912307 | 53.912307 | 54.034199 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b2_m12 | 2 | 33.439819 | 33.439819 | 34.072661 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b4_m24 | 1 | 37.485289 | 37.485289 | 37.485289 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c64:q6_b8_m48 | 1 | 46.552310 | 46.552310 | 46.552310 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | 47 | 46.859200 | 46.817395 | 47.174542 | 42.055565 | -10.25% | compared |
| a3_glm53flash_tp16_aclgraph_c8:q6_b1_m6 | 6 | 33.544533 | 33.104051 | 34.939998 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c8:q6_b4_m24 | 4 | 37.952883 | 37.467638 | 39.614791 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c8:q6_b6_m36 | 3 | 45.218403 | 44.930438 | 46.273504 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53flash_tp16_aclgraph_c8:q6_b2_m12 | 2 | 34.030780 | 34.030780 | 34.633912 | — | — | unresolved: prediction_deferred_by_population_priority |

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
| a3_glm53_dc4k_b1:q1_b1_m1 | 38.954827 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b2:q1_b2_m2 | 40.969878 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b4:q1_b4_m4 | 43.437734 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b8:q1_b8_m8 | 47.113275 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc16k_b1:q1_b1_m1 | 39.112085 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 57.639270 | 55.026876 | 2.612393 | 4.53% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | 57.124636 | 54.590343 | 2.534293 | 4.44% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 57.817112 | 55.202675 | 2.614437 | 4.52% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | 57.713255 | 55.178693 | 2.534562 | 4.39% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 69.556298 | 66.970324 | 2.585974 | 3.72% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | 56.950323 | 54.416393 | 2.533930 | 4.45% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | 56.846876 | 54.171133 | 2.675742 | 4.71% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | 68.632741 | 65.996625 | 2.636115 | 3.84% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | 58.058190 | 55.387721 | 2.670469 | 4.60% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | 57.387626 | 54.748359 | 2.639267 | 4.60% | not_established | 16 / 1 / 16 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 33.030918 | 32.772932 | 0.257985 | 0.78% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | 18.010107 | 17.748127 | 0.261980 | 1.45% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | 15.697300 | 15.434811 | 0.262489 | 1.67% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | 24.984322 | 24.715387 | 0.268936 | 1.08% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | 33.211164 | 32.950234 | 0.260930 | 0.79% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | 32.232000 | 31.960848 | 0.271152 | 0.84% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | 31.922655 | 31.650425 | 0.272230 | 0.85% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | 21.416720 | 21.144840 | 0.271880 | 1.27% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 33.616091 | 33.357768 | 0.258323 | 0.77% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | 29.255343 | 28.989496 | 0.265847 | 0.91% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | 21.440818 | 21.169837 | 0.270981 | 1.26% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | 15.623967 | 15.363616 | 0.260350 | 1.67% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | 33.357579 | 33.100602 | 0.256977 | 0.77% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | 32.536283 | 32.271388 | 0.264895 | 0.81% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | 24.989969 | 24.722395 | 0.267574 | 1.07% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | 17.717363 | 17.455317 | 0.262046 | 1.48% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 37.668964 | 37.413278 | 0.255686 | 0.68% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | 37.705175 | 37.429031 | 0.276145 | 0.73% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | 37.467978 | 37.200235 | 0.267743 | 0.71% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | 38.396873 | 38.137811 | 0.259062 | 0.67% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | 38.002127 | 37.736855 | 0.265272 | 0.70% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 38.713189 | 38.457571 | 0.255617 | 0.66% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | 38.635279 | 38.374234 | 0.261045 | 0.68% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 21.418246 | 21.147118 | 0.271128 | 1.27% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | 15.589915 | 15.327661 | 0.262254 | 1.68% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | 17.682321 | 17.420494 | 0.261827 | 1.48% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 46.528233 | 46.292617 | 0.235616 | 0.51% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 28.833324 | 28.568438 | 0.264886 | 0.92% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | 25.112799 | 24.844953 | 0.267846 | 1.07% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | 21.340235 | 21.068491 | 0.271744 | 1.27% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | 18.881633 | 18.617714 | 0.263919 | 1.40% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | 16.092148 | 15.828829 | 0.263319 | 1.64% | not_established | 8 / 1 / 1 | auto / full |
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

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | dense_layer | 0 / 3 | 0.474002 | 0.296531 | 0.829225 | 0.397236 | -16.20% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | moe_layer | 11 / 42 | 0.673523 | 0.590907 | 0.934934 | 0.834754 | +23.94% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | dense_layer | 0 / 3 | 0.619493 | 0.429010 | 1.009248 | 0.659825 | +6.51% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | moe_layer | 0 / 42 | 0.932364 | 0.792325 | 1.381103 | 1.473141 | +58.00% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | dense_layer | 0 / 3 | 0.588732 | 0.573221 | 0.632444 | 0.361609 | -38.58% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | moe_layer | 29 / 42 | 0.769068 | 0.710639 | 0.953812 | 0.674979 | -12.23% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | dense_layer | 0 / 3 | 0.615360 | 0.614060 | 0.624559 | 0.397236 | -35.45% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | moe_layer | 42 / 42 | 0.903418 | 0.812825 | 1.168139 | 0.834754 | -7.60% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | dense_layer | 0 / 3 | 0.313856 | 0.240144 | 0.464978 | 0.145252 | -53.72% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | moe_layer | 0 / 42 | 0.479167 | 0.424416 | 0.634057 | 0.342642 | -28.49% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | dense_layer | 3 / 3 | 0.582792 | 0.572780 | 0.603622 | 0.573554 | -1.59% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | moe_layer | 15 / 42 | 1.329532 | 1.010557 | 2.233884 | 1.420587 | +6.85% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | dense_layer | 0 / 3 | 0.306520 | 0.263452 | 0.422210 | 0.129167 | -57.86% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | moe_layer | 0 / 42 | 0.351495 | 0.302211 | 0.492130 | 0.226487 | -35.56% |
| a3_glm53_dc4k_b1:q1_b1_m1 | dense_layer | 3 / 3 | 0.387506 | 0.384723 | 0.394250 | 0.353843 | -8.69% |
| a3_glm53_dc4k_b1:q1_b1_m1 | moe_layer | 55 / 75 | 0.503075 | 0.484378 | 0.566864 | 0.434338 | -13.66% |
| a3_glm53_dc4k_b2:q1_b2_m2 | dense_layer | 3 / 3 | 0.403290 | 0.407802 | 0.410515 | 0.355317 | -11.90% |
| a3_glm53_dc4k_b2:q1_b2_m2 | moe_layer | 57 / 75 | 0.529285 | 0.509096 | 0.601701 | 0.458887 | -13.30% |
| a3_glm53_dc4k_b4:q1_b4_m4 | dense_layer | 3 / 3 | 0.401821 | 0.399081 | 0.411774 | 0.358264 | -10.84% |
| a3_glm53_dc4k_b4:q1_b4_m4 | moe_layer | 70 / 75 | 0.562175 | 0.540899 | 0.637391 | 0.500747 | -10.93% |
| a3_glm53_dc4k_b8:q1_b8_m8 | dense_layer | 3 / 3 | 0.416038 | 0.413257 | 0.424403 | 0.366260 | -11.96% |
| a3_glm53_dc4k_b8:q1_b8_m8 | moe_layer | 75 / 75 | 0.610549 | 0.587718 | 0.698046 | 0.573677 | -6.04% |
| a3_glm53_dc16k_b1:q1_b1_m1 | dense_layer | 3 / 3 | 0.396276 | 0.393697 | 0.402033 | 0.353843 | -10.71% |
| a3_glm53_dc16k_b1:q1_b1_m1 | moe_layer | 52 / 75 | 0.504482 | 0.483485 | 0.576161 | 0.434338 | -13.90% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | dense_layer | 0 / 3 | 0.573069 | 0.577426 | 0.585758 | 0.357878 | -37.55% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | moe_layer | 0 / 75 | 0.745549 | 0.745723 | 0.781082 | 0.478850 | -35.77% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | dense_layer | 0 / 3 | 0.587706 | 0.567711 | 0.627936 | 0.357878 | -39.11% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | moe_layer | 0 / 75 | 0.747336 | 0.742162 | 0.785962 | 0.478850 | -35.93% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | dense_layer | 0 / 3 | 0.646681 | 0.655584 | 0.670978 | 0.462974 | -28.41% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | moe_layer | 0 / 75 | 0.901497 | 0.866973 | 1.013966 | 0.721867 | -19.93% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | dense_layer | 0 / 3 | 0.331484 | 0.299064 | 0.397976 | 0.154244 | -53.47% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | moe_layer | 0 / 42 | 0.762750 | 0.680149 | 1.000371 | 0.536260 | -29.69% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | dense_layer | 0 / 3 | 0.327901 | 0.298229 | 0.387636 | 0.154244 | -52.96% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | moe_layer | 0 / 42 | 0.776939 | 0.678147 | 1.059929 | 0.540723 | -30.40% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | dense_layer | 0 / 3 | 0.397664 | 0.353061 | 0.487329 | 0.189013 | -52.47% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | moe_layer | 0 / 42 | 0.868453 | 0.754050 | 1.195816 | 0.648602 | -25.32% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | dense_layer | 0 / 3 | 0.398729 | 0.353734 | 0.489095 | 0.189013 | -52.60% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | moe_layer | 0 / 42 | 0.893239 | 0.753253 | 1.295158 | 0.657631 | -26.38% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | dense_layer | 0 / 3 | 0.264436 | 0.235357 | 0.323452 | 0.135987 | -48.57% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | moe_layer | 0 / 42 | 0.491047 | 0.428691 | 0.670685 | 0.316597 | -35.53% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | dense_layer | 0 / 3 | 0.496504 | 0.469962 | 0.550965 | 0.262679 | -47.09% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | moe_layer | 2 / 42 | 1.072327 | 0.889656 | 1.589585 | 0.859630 | -19.84% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | dense_layer | 0 / 3 | 0.334844 | 0.257668 | 0.497291 | 0.139924 | -58.21% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | moe_layer | 0 / 42 | 0.662567 | 0.593192 | 0.867922 | 0.456240 | -31.14% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | dense_layer | 0 / 3 | 0.667246 | 0.669540 | 0.689545 | 0.438003 | -34.36% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | moe_layer | 42 / 42 | 1.234289 | 1.077833 | 1.688344 | 1.150558 | -6.78% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | dense_layer | 0 / 3 | 0.901952 | 0.886134 | 0.953419 | 0.596214 | -33.90% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | moe_layer | 13 / 42 | 1.585782 | 1.326066 | 2.332666 | 1.514548 | -4.49% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | dense_layer | 0 / 3 | 1.307523 | 1.302391 | 1.323245 | 0.906186 | -30.69% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | moe_layer | 0 / 42 | 2.223835 | 1.764160 | 3.531813 | 2.265231 | +1.86% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | dense_layer | 0 / 3 | 0.623883 | 0.618011 | 0.641189 | 0.373900 | -40.07% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | moe_layer | 42 / 42 | 1.069907 | 0.952253 | 1.409976 | 0.974616 | -8.91% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 0 / 34 | 0.573101 | 0.579816 | 0.610945 | 0.737515 | +28.69% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 11 / 11 | 0.929504 | 0.929149 | 0.937226 | 1.015987 | +9.30% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 0 / 34 | 0.762836 | 0.772892 | 0.829536 | 1.206894 | +58.21% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 0 / 11 | 1.371034 | 1.377786 | 1.396007 | 2.074275 | +51.29% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | kda | 29 / 34 | 0.693117 | 0.694880 | 0.733617 | 0.612125 | -11.69% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | mla | 0 / 11 | 0.954644 | 0.951023 | 0.969821 | 0.783790 | -17.90% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | kda | 31 / 34 | 0.792874 | 0.809037 | 0.816091 | 0.737515 | -6.98% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | mla | 11 / 11 | 1.166537 | 1.165343 | 1.172462 | 1.015987 | -12.91% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 0 / 34 | 0.412816 | 0.421465 | 0.428909 | 0.309931 | -24.92% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 0 / 11 | 0.639166 | 0.633990 | 0.657478 | 0.389914 | -39.00% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | kda | 7 / 34 | 0.971208 | 1.008853 | 1.013906 | 1.112802 | +14.58% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | mla | 11 / 11 | 2.233423 | 2.233777 | 2.258570 | 2.140914 | -4.14% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 0 / 34 | 0.301047 | 0.298533 | 0.305713 | 0.204870 | -31.95% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0 / 11 | 0.495159 | 0.491361 | 0.512266 | 0.266763 | -46.13% |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 58 / 78 | 0.498630 | 0.484310 | 0.566864 | 0.431242 | -13.51% |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 60 / 78 | 0.524439 | 0.508658 | 0.601701 | 0.454904 | -13.26% |
| a3_glm53_dc4k_b4:q1_b4_m4 | mla | 73 / 78 | 0.556008 | 0.540114 | 0.637391 | 0.495267 | -10.92% |
| a3_glm53_dc4k_b8:q1_b8_m8 | mla | 78 / 78 | 0.603068 | 0.587228 | 0.698046 | 0.565699 | -6.20% |
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 55 / 78 | 0.500321 | 0.482807 | 0.576161 | 0.431242 | -13.81% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | mla | 0 / 78 | 0.738916 | 0.743060 | 0.781082 | 0.474197 | -35.83% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | mla | 0 / 78 | 0.741196 | 0.741208 | 0.785962 | 0.474197 | -36.02% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | mla | 0 / 78 | 0.891696 | 0.866537 | 1.013966 | 0.711909 | -20.16% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | kda | 0 / 34 | 0.647355 | 0.676956 | 0.682362 | 0.457192 | -29.38% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | mla | 0 / 11 | 1.001808 | 0.997207 | 1.015218 | 0.676465 | -32.48% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | kda | 0 / 34 | 0.646030 | 0.676663 | 0.682706 | 0.457192 | -29.23% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | mla | 0 / 11 | 1.059101 | 1.055154 | 1.070667 | 0.693504 | -34.52% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | kda | 0 / 34 | 0.720522 | 0.752286 | 0.755426 | 0.523382 | -27.36% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | mla | 0 / 11 | 1.197294 | 1.193753 | 1.212146 | 0.910303 | -23.97% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | kda | 0 / 34 | 0.719759 | 0.750541 | 0.755133 | 0.523382 | -27.28% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | mla | 0 / 11 | 1.294585 | 1.290762 | 1.308970 | 0.944779 | -27.02% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | kda | 0 / 34 | 0.412141 | 0.424787 | 0.432720 | 0.284349 | -31.01% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | mla | 0 / 11 | 0.673135 | 0.669531 | 0.677515 | 0.367013 | -45.48% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | kda | 0 / 34 | 0.853091 | 0.886410 | 0.892277 | 0.650506 | -23.75% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | mla | 2 / 11 | 1.592925 | 1.584140 | 1.613101 | 1.343207 | -15.68% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | kda | 0 / 34 | 0.567253 | 0.588717 | 0.597100 | 0.402575 | -29.03% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | mla | 0 / 11 | 0.867794 | 0.867858 | 0.875472 | 0.535845 | -38.25% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | kda | 31 / 34 | 1.038076 | 1.073693 | 1.083795 | 0.894965 | -13.79% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | mla | 11 / 11 | 1.686116 | 1.687182 | 1.691235 | 1.746240 | +3.57% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | kda | 2 / 34 | 1.284063 | 1.318488 | 1.332471 | 1.066186 | -16.97% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | mla | 11 / 11 | 2.331870 | 2.330007 | 2.340216 | 2.649939 | +13.64% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | kda | 0 / 34 | 1.720878 | 1.759555 | 1.769474 | 1.427866 | -17.03% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | mla | 0 / 11 | 3.528525 | 3.530727 | 3.535698 | 4.482802 | +27.04% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | kda | 31 / 34 | 0.920568 | 0.947606 | 0.957843 | 0.817159 | -11.23% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | mla | 11 / 11 | 1.409856 | 1.409699 | 1.416413 | 1.297470 | -7.97% |

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
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 0.498630 | — | — |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 0.524439 | — | — |
| a3_glm53_dc4k_b4:q1_b4_m4 | mla | 0.556008 | — | — |
| a3_glm53_dc4k_b8:q1_b8_m8 | mla | 0.603068 | — | — |
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 0.500321 | — | — |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | mla | 0.738916 | 0.705473 | 0.033443 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | mla | 0.741196 | 0.707727 | 0.033469 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | mla | 0.891696 | 0.858594 | 0.033102 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | kda | 0.647355 | 0.642067 | 0.005288 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | mla | 1.001808 | 0.994786 | 0.007022 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | kda | 0.646030 | 0.640731 | 0.005298 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | mla | 1.059101 | 1.052082 | 0.007019 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | kda | 0.720522 | 0.715290 | 0.005232 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | mla | 1.197294 | 1.190310 | 0.006984 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | kda | 0.719759 | 0.714524 | 0.005234 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | mla | 1.294585 | 1.287614 | 0.006971 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | kda | 0.412141 | 0.406748 | 0.005393 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | mla | 0.673135 | 0.665243 | 0.007892 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | kda | 0.853091 | 0.848530 | 0.004561 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | mla | 1.592925 | 1.585690 | 0.007235 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | kda | 0.567253 | 0.562039 | 0.005215 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | mla | 0.867794 | 0.859921 | 0.007874 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | kda | 1.038076 | 1.007952 | 0.030124 |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | mla | 1.686116 | 1.647526 | 0.038590 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | kda | 1.284063 | 1.252331 | 0.031732 |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | mla | 2.331870 | 2.294906 | 0.036964 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | kda | 1.720878 | 1.687860 | 0.033018 |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | mla | 3.528525 | 3.490678 | 0.037847 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | kda | 0.920568 | 0.890728 | 0.029840 |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | mla | 1.409856 | 1.371585 | 0.038270 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | all | 44 | 2024 | 0.656381 | 0.587042 | 0.770445 | +31.24% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | kda | 33 | 1518 | 0.565340 | 0.581631 | 0.770445 | +32.46% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | mla | 11 | 506 | 0.929504 | 0.927588 | 1.015987 | +9.53% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | all | 44 | 1628 | 0.909285 | 0.788475 | 1.259836 | +59.78% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 33 | 1221 | 0.755369 | 0.773716 | 1.259836 | +62.83% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 11 | 407 | 1.371034 | 1.376707 | 2.074275 | +50.67% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | all | 44 | 2024 | 0.761223 | 0.671958 | 0.636369 | -5.30% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | kda | 33 | 1518 | 0.696750 | 0.664003 | 0.636369 | -4.16% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | mla | 11 | 506 | 0.954644 | 0.939519 | 0.783790 | -16.58% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | all | 44 | 2024 | 0.890354 | 0.811481 | 0.770445 | -5.06% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | kda | 33 | 1518 | 0.798293 | 0.808226 | 0.770445 | -4.67% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | mla | 11 | 506 | 1.166537 | 1.164423 | 1.015987 | -12.75% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | all | 44 | 2332 | 0.468218 | 0.423968 | 0.325868 | -23.14% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 33 | 1749 | 0.411236 | 0.421213 | 0.325868 | -22.64% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 11 | 583 | 0.639166 | 0.633678 | 0.389914 | -38.47% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | all | 44 | 1188 | 1.295116 | 1.010385 | 1.164987 | +15.30% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | kda | 33 | 891 | 0.982346 | 1.008593 | 1.164987 | +15.51% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | mla | 11 | 297 | 2.233423 | 2.232883 | 2.140914 | -4.12% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | all | 44 | 2860 | 0.346822 | 0.301057 | 0.212196 | -29.52% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 33 | 2145 | 0.297376 | 0.298344 | 0.212196 | -28.88% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 11 | 715 | 0.495159 | 0.490270 | 0.266763 | -45.59% |
| a3_glm53_dc4k_b1:q1_b1_m1 | all | 77 | 5698 | 0.499986 | 0.484650 | 0.421012 | -13.13% |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 77 | 5698 | 0.499986 | 0.484650 | 0.421012 | -13.13% |
| a3_glm53_dc4k_b2:q1_b2_m2 | all | 77 | 5390 | 0.525918 | 0.508590 | 0.445452 | -12.41% |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 77 | 5390 | 0.525918 | 0.508590 | 0.445452 | -12.41% |
| a3_glm53_dc4k_b4:q1_b4_m4 | all | 77 | 5159 | 0.557881 | 0.540369 | 0.487094 | -9.86% |
| a3_glm53_dc4k_b4:q1_b4_m4 | mla | 77 | 5159 | 0.557881 | 0.540369 | 0.487094 | -9.86% |
| a3_glm53_dc4k_b8:q1_b8_m8 | all | 77 | 4697 | 0.605388 | 0.586108 | 0.559083 | -4.61% |
| a3_glm53_dc4k_b8:q1_b8_m8 | mla | 77 | 4697 | 0.605388 | 0.586108 | 0.559083 | -4.61% |
| a3_glm53_dc16k_b1:q1_b1_m1 | all | 77 | 5698 | 0.501597 | 0.482860 | 0.421012 | -12.81% |
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 77 | 5698 | 0.501597 | 0.482860 | 0.421012 | -12.81% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | all | 77 | 3388 | 0.740905 | 0.713924 | 0.462191 | -35.26% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | mla | 77 | 3388 | 0.740905 | 0.713924 | 0.462191 | -35.26% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | all | 77 | 3388 | 0.742667 | 0.714665 | 0.462191 | -35.33% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | mla | 77 | 3388 | 0.742667 | 0.714665 | 0.462191 | -35.33% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | all | 77 | 3773 | 0.894563 | 0.866817 | 0.694813 | -19.84% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | mla | 77 | 3773 | 0.894563 | 0.866817 | 0.694813 | -19.84% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | all | 44 | 1320 | 0.741636 | 0.679557 | 0.486510 | -28.41% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | kda | 33 | 990 | 0.654912 | 0.676975 | 0.486510 | -28.13% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | mla | 11 | 330 | 1.001808 | 0.997804 | 0.676465 | -32.20% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | all | 44 | 1408 | 0.755170 | 0.677909 | 0.486510 | -28.23% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | kda | 33 | 1056 | 0.653860 | 0.676787 | 0.486510 | -28.11% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | mla | 11 | 352 | 1.059101 | 1.054342 | 0.693504 | -34.22% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | all | 44 | 1364 | 0.845015 | 0.753693 | 0.555740 | -26.26% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | kda | 33 | 1023 | 0.727589 | 0.752178 | 0.555740 | -26.12% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | mla | 11 | 341 | 1.197294 | 1.192474 | 0.910303 | -23.66% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | all | 44 | 1540 | 0.868707 | 0.752074 | 0.555740 | -26.11% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | kda | 33 | 1155 | 0.726748 | 0.750199 | 0.555740 | -25.92% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | mla | 11 | 385 | 1.294585 | 1.289925 | 0.944779 | -26.76% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | all | 44 | 484 | 0.479405 | 0.428782 | 0.298707 | -30.34% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | kda | 33 | 363 | 0.414829 | 0.424868 | 0.298707 | -29.69% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | mla | 11 | 121 | 0.673135 | 0.671351 | 0.367013 | -45.33% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | all | 44 | 1364 | 1.044916 | 0.888989 | 0.688038 | -22.60% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | kda | 33 | 1023 | 0.862246 | 0.886644 | 0.688038 | -22.40% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | mla | 11 | 341 | 1.592925 | 1.583919 | 1.343207 | -15.20% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | all | 44 | 1320 | 0.643979 | 0.591855 | 0.427993 | -27.69% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | kda | 33 | 990 | 0.569374 | 0.588956 | 0.427993 | -27.33% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | mla | 11 | 330 | 0.867794 | 0.864061 | 0.535845 | -37.99% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | all | 44 | 2200 | 1.208007 | 1.076586 | 0.939187 | -12.76% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | kda | 33 | 1650 | 1.048638 | 1.073441 | 0.939187 | -12.51% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | mla | 11 | 550 | 1.686116 | 1.686414 | 1.746240 | +3.55% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | all | 44 | 2156 | 1.553529 | 1.327067 | 1.111668 | -16.23% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | kda | 33 | 1617 | 1.294083 | 1.320066 | 1.111668 | -15.79% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | mla | 11 | 539 | 2.331870 | 2.330967 | 2.649939 | +13.68% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | all | 44 | 2068 | 2.181827 | 1.764626 | 1.478351 | -16.22% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | kda | 33 | 1551 | 1.732927 | 1.762955 | 1.478351 | -16.14% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | mla | 11 | 517 | 3.528525 | 3.531911 | 4.482802 | +26.92% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | all | 44 | 2068 | 1.049240 | 0.951629 | 0.860055 | -9.62% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | kda | 33 | 1551 | 0.929034 | 0.947759 | 0.860055 | -9.25% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | mla | 11 | 517 | 1.409856 | 1.407188 | 1.297470 | -7.80% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 46 | 0.829225 | 0.724865 | 0.782496 | 0.397236 | -52.10% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 37 | 1.009248 | 0.849777 | 0.965079 | 0.659825 | -34.62% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | 46 | 0.573221 | 0.501010 | 0.719194 | 0.361609 | -36.92% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | 46 | 0.614060 | 0.582461 | 0.771416 | 0.397236 | -35.31% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 53 | 0.464978 | 0.474452 | 0.536593 | 0.145252 | -68.76% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 27 | 0.603622 | 0.588892 | 0.680723 | 0.573554 | -4.98% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 0.422210 | 0.438253 | 0.487926 | 0.129167 | -69.41% |
| a3_glm53_dc4k_b1:q1_b1_m1 | 74 | 0.394250 | 0.385352 | 0.415732 | 0.353843 | -10.25% |
| a3_glm53_dc4k_b2:q1_b2_m2 | 70 | 0.410515 | 0.395952 | 0.454831 | 0.355317 | -13.45% |
| a3_glm53_dc4k_b4:q1_b4_m4 | 67 | 0.411774 | 0.407112 | 0.411352 | 0.358264 | -12.99% |
| a3_glm53_dc4k_b8:q1_b8_m8 | 61 | 0.424403 | 0.422672 | 0.425891 | 0.366260 | -13.70% |
| a3_glm53_dc16k_b1:q1_b1_m1 | 74 | 0.402033 | 0.396682 | 0.411171 | 0.353843 | -11.99% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 44 | 0.585758 | 0.542520 | 0.733755 | 0.357878 | -38.90% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 44 | 0.627936 | 0.549071 | 0.813657 | 0.357878 | -43.01% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 49 | 0.670978 | 0.621032 | 0.820996 | 0.462974 | -31.00% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 30 | 0.397976 | 0.393700 | 0.533420 | 0.154244 | -61.24% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 32 | 0.387636 | 0.401942 | 0.466389 | 0.154244 | -60.21% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 31 | 0.487329 | 0.462641 | 0.578271 | 0.189013 | -61.21% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 35 | 0.489095 | 0.481810 | 0.547052 | 0.189013 | -61.35% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 11 | 0.323452 | 0.280486 | 0.344031 | 0.135987 | -57.96% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 31 | 0.550965 | 0.529863 | 0.660172 | 0.262679 | -52.32% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 30 | 0.497291 | 0.498862 | 0.512161 | 0.139924 | -71.86% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 | 50 | 0.689545 | 0.668883 | 0.733735 | 0.438003 | -36.48% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 | 49 | 0.953419 | 0.908198 | 0.956559 | 0.596214 | -37.47% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 | 47 | 1.323245 | 1.322106 | 1.352347 | 0.906186 | -31.52% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 | 47 | 0.641189 | 0.581011 | 0.861818 | 0.373900 | -41.69% |

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
| a3_glm53_dc4k_b1:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 1 | — | — | — | — |
| a3_glm53_dc4k_b2:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 2 | — | — | — | — |
| a3_glm53_dc4k_b4:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 4 | — | — | — | — |
| a3_glm53_dc4k_b8:q1_b8_m8 | 1 | 8 | 8 | unknown | 4096 | 8 | — | — | — | — |
| a3_glm53_dc16k_b1:q1_b1_m1 | 1 | 1 | 1 | unknown | 16384 | 1 | — | — | — | — |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 2 | 81.123653 | 76.399375 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 2 | 81.123653 | 76.399375 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 2 | 80.812579 | 76.184906 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 2 | 80.812579 | 76.184906 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 6 | 8 | 48 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | 6 | 6 | 36 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | 6 | 3 | 18 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 4 | 16 | 64 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | 4 | 2 | 8 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | 4 | 6 | 24 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | 4 | 14 | 56 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | 4 | 12 | 48 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | 4 | 10 | 40 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | 4 | 4 | 16 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 4 | 16 | 64 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | 4 | 8 | 32 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | 4 | 4 | 16 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | 4 | 1 | 4 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | 4 | 14 | 56 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | 4 | 12 | 48 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | 4 | 6 | 24 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | 4 | 2 | 8 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 4 | 32 | 128 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | 4 | 30 | 120 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | 4 | 24 | 96 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | 4 | 28 | 112 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | 4 | 26 | 104 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 4 | 32 | 128 | unknown | 8200 | 32 | — | 25.049886 | — | 16.568588 |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | 4 | 30 | 120 | unknown | 8200 | 32 | — | 25.049886 | — | 16.568588 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 4 | 4 | 16 | unknown | 8200 | 4 | — | 12.932970 | — | 10.172629 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | 4 | 1 | 4 | unknown | 8200 | 4 | — | 12.932970 | — | 10.172629 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | 4 | 2 | 8 | unknown | 8200 | 4 | — | 12.932970 | — | 10.172629 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 4 | 64 | 256 | unknown | 4104 | 64 | — | 29.828263 | — | 19.944121 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 4 | 8 | 32 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | 4 | 6 | 24 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | 4 | 4 | 16 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | 4 | 2 | 8 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
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
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | embedding | 30 | 0.004553 | 0.004525 | 0.005564 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | output_head_preparation | 30 | 0.006682 | 0.006729 | 0.007088 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | final_norm | 30 | 0.040526 | 0.040494 | 0.041248 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | lm_head | 30 | 0.088715 | 0.088786 | 0.089602 |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | embedding | 4 | 0.003420 | 0.003452 | 0.003850 |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | output_head_preparation | 4 | 0.005153 | 0.005201 | 0.005332 |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | final_norm | 4 | 0.034924 | 0.034920 | 0.035321 |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | lm_head | 4 | 0.049094 | 0.049037 | 0.049990 |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | embedding | 3 | 0.002951 | 0.002885 | 0.003313 |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | output_head_preparation | 3 | 0.005360 | 0.005500 | 0.005603 |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | final_norm | 3 | 0.034749 | 0.034833 | 0.034835 |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | lm_head | 3 | 0.048303 | 0.048403 | 0.048578 |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | embedding | 2 | 0.003848 | 0.003848 | 0.003962 |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | output_head_preparation | 2 | 0.005883 | 0.005883 | 0.006297 |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | final_norm | 2 | 0.038606 | 0.038606 | 0.039156 |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | lm_head | 2 | 0.049973 | 0.049973 | 0.050734 |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | embedding | 1 | 0.004096 | 0.004096 | 0.004096 |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | output_head_preparation | 1 | 0.007392 | 0.007392 | 0.007392 |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | final_norm | 1 | 0.039928 | 0.039928 | 0.039928 |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | lm_head | 1 | 0.085771 | 0.085771 | 0.085771 |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | embedding | 1 | 0.003766 | 0.003766 | 0.003766 |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | output_head_preparation | 1 | 0.006667 | 0.006667 | 0.006667 |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | final_norm | 1 | 0.040490 | 0.040490 | 0.040490 |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | lm_head | 1 | 0.059180 | 0.059180 | 0.059180 |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | embedding | 1 | 0.002906 | 0.002906 | 0.002906 |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | output_head_preparation | 1 | 0.007098 | 0.007098 | 0.007098 |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | final_norm | 1 | 0.040217 | 0.040217 | 0.040217 |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | lm_head | 1 | 0.059376 | 0.059376 | 0.059376 |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | embedding | 1 | 0.003926 | 0.003926 | 0.003926 |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | output_head_preparation | 1 | 0.004996 | 0.004996 | 0.004996 |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | final_norm | 1 | 0.036260 | 0.036260 | 0.036260 |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | lm_head | 1 | 0.049699 | 0.049699 | 0.049699 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | embedding | 32 | 0.004520 | 0.004431 | 0.005326 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | output_head_preparation | 32 | 0.006810 | 0.006925 | 0.007141 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | final_norm | 32 | 0.040588 | 0.040555 | 0.041123 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | lm_head | 32 | 0.088318 | 0.088529 | 0.089220 |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | embedding | 2 | 0.003769 | 0.003769 | 0.004572 |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | output_head_preparation | 2 | 0.006301 | 0.006301 | 0.006349 |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | final_norm | 2 | 0.038984 | 0.038984 | 0.039594 |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | lm_head | 2 | 0.050176 | 0.050176 | 0.050733 |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | embedding | 2 | 0.003302 | 0.003302 | 0.003438 |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | output_head_preparation | 2 | 0.005175 | 0.005175 | 0.005456 |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | final_norm | 2 | 0.036297 | 0.036297 | 0.036311 |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | lm_head | 2 | 0.050319 | 0.050319 | 0.050635 |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | embedding | 2 | 0.003207 | 0.003207 | 0.003371 |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | output_head_preparation | 2 | 0.005476 | 0.005476 | 0.005500 |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | final_norm | 2 | 0.034876 | 0.034876 | 0.034992 |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | lm_head | 2 | 0.048877 | 0.048877 | 0.049106 |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | embedding | 1 | 0.004029 | 0.004029 | 0.004029 |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | output_head_preparation | 1 | 0.008101 | 0.008101 | 0.008101 |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | final_norm | 1 | 0.039601 | 0.039601 | 0.039601 |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | lm_head | 1 | 0.084248 | 0.084248 | 0.084248 |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | embedding | 1 | 0.003431 | 0.003431 | 0.003431 |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | output_head_preparation | 1 | 0.005966 | 0.005966 | 0.005966 |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | final_norm | 1 | 0.040585 | 0.040585 | 0.040585 |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | lm_head | 1 | 0.058436 | 0.058436 | 0.058436 |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | embedding | 1 | 0.003757 | 0.003757 | 0.003757 |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | output_head_preparation | 1 | 0.006379 | 0.006379 | 0.006379 |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | final_norm | 1 | 0.038149 | 0.038149 | 0.038149 |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | lm_head | 1 | 0.050160 | 0.050160 | 0.050160 |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | embedding | 1 | 0.002750 | 0.002750 | 0.002750 |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | output_head_preparation | 1 | 0.005298 | 0.005298 | 0.005298 |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | final_norm | 1 | 0.035537 | 0.035537 | 0.035537 |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | lm_head | 1 | 0.047421 | 0.047421 | 0.047421 |
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
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | embedding | 35 | 0.004283 | 0.004021 | 0.005149 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | output_head_preparation | 35 | 0.007651 | 0.007655 | 0.007883 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | final_norm | 35 | 0.039854 | 0.039860 | 0.040524 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | lm_head | 35 | 0.100081 | 0.100014 | 0.100637 |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | embedding | 1 | 0.004700 | 0.004700 | 0.004700 |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | output_head_preparation | 1 | 0.009528 | 0.009528 | 0.009528 |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | final_norm | 1 | 0.039851 | 0.039851 | 0.039851 |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | lm_head | 1 | 0.097564 | 0.097564 | 0.097564 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | embedding | 11 | 0.003148 | 0.003088 | 0.003418 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | output_head_preparation | 11 | 0.005225 | 0.005255 | 0.005539 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | final_norm | 11 | 0.036308 | 0.036356 | 0.036607 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | lm_head | 11 | 0.050044 | 0.050001 | 0.050849 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | embedding | 9 | 0.002952 | 0.002875 | 0.003418 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | output_head_preparation | 9 | 0.005144 | 0.005175 | 0.005625 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | final_norm | 9 | 0.034639 | 0.034648 | 0.035308 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | lm_head | 9 | 0.048629 | 0.048585 | 0.049569 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | embedding | 3 | 0.003078 | 0.003057 | 0.003300 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | output_head_preparation | 3 | 0.005326 | 0.005324 | 0.005616 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | final_norm | 3 | 0.034953 | 0.035107 | 0.035348 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | lm_head | 3 | 0.049295 | 0.049272 | 0.049677 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | embedding | 31 | 0.005153 | 0.004906 | 0.006278 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | output_head_preparation | 31 | 0.009403 | 0.009451 | 0.009728 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | final_norm | 31 | 0.040726 | 0.040693 | 0.041491 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | lm_head | 31 | 0.107919 | 0.107887 | 0.108171 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | embedding | 30 | 0.003182 | 0.003112 | 0.003608 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | output_head_preparation | 30 | 0.005864 | 0.005867 | 0.006163 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | final_norm | 30 | 0.039579 | 0.039516 | 0.040315 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | lm_head | 30 | 0.051001 | 0.050651 | 0.052626 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | embedding | 3 | 0.003911 | 0.003955 | 0.004103 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | output_head_preparation | 3 | 0.006226 | 0.006167 | 0.006562 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | final_norm | 3 | 0.037290 | 0.037535 | 0.037677 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | lm_head | 3 | 0.049996 | 0.050208 | 0.050628 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | embedding | 2 | 0.003790 | 0.003790 | 0.004197 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | output_head_preparation | 2 | 0.005394 | 0.005394 | 0.005662 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | final_norm | 2 | 0.035840 | 0.035840 | 0.035918 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | lm_head | 2 | 0.050087 | 0.050087 | 0.050191 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | embedding | 2 | 0.002894 | 0.002894 | 0.003096 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | output_head_preparation | 2 | 0.005300 | 0.005300 | 0.005735 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | final_norm | 2 | 0.035452 | 0.035452 | 0.035793 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | lm_head | 2 | 0.048963 | 0.048963 | 0.049836 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | embedding | 1 | 0.003240 | 0.003240 | 0.003240 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | output_head_preparation | 1 | 0.004987 | 0.004987 | 0.004987 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | final_norm | 1 | 0.034165 | 0.034165 | 0.034165 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | lm_head | 1 | 0.048935 | 0.048935 | 0.048935 |
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

Summary: {"case_count": 103, "compared_cases": 26, "failed_cases": 0, "measured_cases": 103, "passed_cases": 12, "source_case_count": 26, "unresolved_cases": 77}
