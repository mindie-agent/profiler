# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "67ca76738c3d6acaa44d8258cc4ba9b5534e1cbf"}.

Variant: `runtime67-v4_kimi`. Baseline: null.

Sim 0.8.0; 240 package files; SHA256 `f2810bee7993d859560eaea1d264035ce35f75329b8e9468bbea0e5f6d95432c`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 129 | 14.929338 | 14.914454 | 14.928722 | 8.977486 | -39.87% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 105 | 18.624557 | 18.615864 | 18.640311 | 11.800140 | -36.64% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 151 | 13.238803 | 13.208635 | 13.227353 | 7.531621 | -43.11% | compared |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 254 | 3.180250 | 3.127828 | 3.431912 | 2.352350 | -26.03% | compared |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 235 | 4.807080 | 4.779005 | 4.992080 | 3.530424 | -26.56% | compared |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | 3 | 3.844777 | 3.280615 | 5.439251 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 220 | 6.713782 | 6.664787 | 6.922921 | 5.494102 | -18.17% | compared |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 3 | 3.240302 | 3.278234 | 3.410932 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 3 | 3.363853 | 3.379593 | 3.466951 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 1 | 3.812064 | 3.812064 | 3.812064 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 1 | 2.978001 | 2.978001 | 2.978001 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 1 | 4.690486 | 4.690486 | 4.690486 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 246 | 3.476353 | 3.437971 | 3.655687 | 2.412350 | -30.61% | compared |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | 4 | 3.375663 | 3.346474 | 3.556049 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | 3 | 3.190596 | 3.244875 | 3.293894 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 196 | 9.615404 | 9.549549 | 9.774245 | 8.740269 | -9.10% | compared |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | 3 | 3.178496 | 3.253895 | 3.501150 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | 2 | 8.472921 | 8.472921 | 8.559829 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | 2 | 5.631388 | 5.631388 | 5.719806 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | 2 | 4.722715 | 4.722715 | 4.738645 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | 1 | 3.160037 | 3.160037 | 3.160037 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | 1 | 3.536929 | 3.536929 | 3.536929 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 47 | 39.247386 | 39.244948 | 39.262920 | 23.144530 | -41.03% | compared |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 49 | 36.985292 | 36.952793 | 36.968819 | 21.934205 | -40.69% | compared |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 59 | 30.823435 | 30.822007 | 30.838985 | 18.977039 | -38.43% | compared |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 59 | 30.636854 | 30.614967 | 30.632466 | 18.901393 | -38.31% | compared |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 54 | 33.875753 | 33.857996 | 33.873078 | 19.199438 | -43.32% | compared |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 55 | 33.547630 | 33.515767 | 33.532651 | 19.048147 | -43.22% | compared |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 41 | 44.666193 | 44.645272 | 44.661803 | 28.078222 | -37.14% | compared |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 46 | 40.018728 | 40.017751 | 40.043741 | 25.657572 | -35.89% | compared |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 52 | 34.816498 | 34.793753 | 34.812948 | 19.644237 | -43.58% | compared |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 53 | 34.193709 | 34.177425 | 34.194190 | 19.341655 | -43.44% | compared |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 51 | 35.964417 | 35.962094 | 35.978788 | 20.532522 | -42.91% | compared |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 52 | 34.819213 | 34.791110 | 34.808453 | 19.927359 | -42.77% | compared |
| v4flash-a3-tp8-c4:q2_b4_m8 | 104 | 32.485961 | 32.416312 | 32.734306 | 26.445347 | -18.59% | compared |
| v4flash-a3-tp8-c4:q2_b1_m2 | 4 | 29.500360 | 29.511530 | 29.660627 | — | — | unresolved: prediction_deferred_by_population_priority |
| v4flash-a3-tp8-c8:q2_b8_m16 | 104 | 37.763131 | 37.868163 | 38.081839 | 33.463656 | -11.39% | compared |
| v4flash-a3-tp8-c8:q2_b2_m4 | 3 | 31.294368 | 31.233516 | 31.612229 | — | — | unresolved: prediction_deferred_by_population_priority |
| v4flash-a3-tp8-c8:q2_b1_m2 | 2 | 29.354813 | 29.354813 | 29.421692 | — | — | unresolved: prediction_deferred_by_population_priority |
| v4flash-a3-tp8-c8:q2_b4_m8 | 2 | 32.488101 | 32.488101 | 32.561889 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | 0 | — | — | — | — | — | failed: declared_forward_extraction_missing |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | 0 | — | — | — | — | — | failed: declared_forward_extraction_missing |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 0 | — | — | — | — | — | failed: declared_forward_extraction_missing |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | 32 | 49.984739 | 49.802195 | 50.230116 | 50.615471 | +1.26% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | 20 | 50.227508 | 50.207347 | 50.437972 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | 15 | 34.239103 | 33.682167 | 36.061940 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | 8 | 48.703795 | 48.703717 | 49.026360 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | 1 | 185.130761 | 185.130761 | 185.130761 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | 22 | 54.967136 | 54.880343 | 55.046901 | 54.634417 | -0.61% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | 17 | 50.515059 | 50.459912 | 50.932142 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | 16 | 51.750107 | 51.719686 | 52.027841 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b1_m8 | 14 | 51.592999 | 33.731086 | 38.400113 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | 4 | 50.042250 | 49.960392 | 50.329354 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | 3 | 51.607722 | 50.563670 | 54.167837 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | 1 | 262.496916 | 262.496916 | 262.496916 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | 48 | 47.654000 | 47.425103 | 47.666347 | 48.472711 | +1.72% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | 30 | 50.154700 | 34.835994 | 37.649748 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | 21 | 61.811249 | 61.628568 | 62.041601 | 61.948993 | +0.22% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 | 13 | 72.359330 | 33.725246 | 173.014883 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 | 11 | 59.510906 | 59.510991 | 59.770166 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 | 8 | 55.144861 | 55.133909 | 55.338375 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 | 7 | 63.460852 | 58.535011 | 92.715408 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 | 5 | 54.821604 | 54.715706 | 55.163818 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 | 4 | 58.827980 | 58.789946 | 59.143718 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 | 2 | 56.627079 | 56.627079 | 56.742766 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b3_m24 | 2 | 49.513901 | 49.513901 | 50.934043 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 | 2 | 57.975442 | 57.975442 | 58.051780 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 | 1 | 50.256336 | 50.256336 | 50.256336 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | 29 | 48.581862 | 48.411553 | 48.662328 | 49.830677 | +2.57% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | 28 | 52.940304 | 48.199387 | 48.363454 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | 16 | 48.606206 | 33.771646 | 34.877383 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | 4 | 47.116268 | 47.165278 | 47.201657 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 73 | 27.285973 | 27.265820 | 27.290260 | 18.810921 | -31.06% | compared |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 63 | 32.555493 | 32.533125 | 32.673798 | 24.862792 | -23.63% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 14.929338 | 14.831607 | 0.097731 | 0.65% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 18.624557 | 18.525544 | 0.099013 | 0.53% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 13.238803 | 13.143250 | 0.095554 | 0.72% | not_established | 1 / 8 / 8 | auto / full |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 3.180250 | 3.088476 | 0.091774 | 2.89% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 4.807080 | 4.709462 | 0.097618 | 2.03% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | 3.844777 | 3.742211 | 0.102565 | 2.67% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 6.713782 | 6.609395 | 0.104386 | 1.55% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 3.240302 | 3.159277 | 0.081025 | 2.50% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 3.363853 | 3.282654 | 0.081199 | 2.41% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 3.812064 | 3.719127 | 0.092937 | 2.44% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 2.978001 | 2.886602 | 0.091399 | 3.07% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 4.690486 | 4.604887 | 0.085599 | 1.82% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 3.476353 | 3.379951 | 0.096402 | 2.77% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | 3.375663 | 3.281668 | 0.093994 | 2.78% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | 3.190596 | 3.093745 | 0.096851 | 3.04% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 9.615404 | 9.502317 | 0.113087 | 1.18% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | 3.178496 | 3.096751 | 0.081745 | 2.57% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | 8.472921 | 8.364464 | 0.108457 | 1.28% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | 5.631388 | 5.531740 | 0.099647 | 1.77% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | 4.722715 | 4.622307 | 0.100409 | 2.13% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | 3.160037 | 3.069540 | 0.090497 | 2.86% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | 3.536929 | 3.456050 | 0.080879 | 2.29% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 39.247386 | 38.566577 | 0.680809 | 1.73% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 36.985292 | 36.304665 | 0.680627 | 1.84% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 30.823435 | 30.183881 | 0.639554 | 2.07% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 30.636854 | 29.997042 | 0.639813 | 2.09% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 33.875753 | 33.190409 | 0.685344 | 2.02% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 33.547630 | 32.856947 | 0.690684 | 2.06% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 44.666193 | 43.970836 | 0.695357 | 1.56% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 40.018728 | 39.322926 | 0.695802 | 1.74% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 34.816498 | 34.115094 | 0.701404 | 2.01% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 34.193709 | 33.491477 | 0.702232 | 2.05% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 35.964417 | 35.281594 | 0.682823 | 1.90% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 34.819213 | 34.142215 | 0.676998 | 1.94% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| v4flash-a3-tp8-c4:q2_b4_m8 | 32.485961 | 30.611484 | 1.874477 | 5.77% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c4:q2_b1_m2 | 29.500360 | 27.578127 | 1.922233 | 6.52% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c8:q2_b8_m16 | 37.763131 | 36.154075 | 1.609056 | 4.26% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c8:q2_b2_m4 | 31.294368 | 29.525103 | 1.769265 | 5.65% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c8:q2_b1_m2 | 29.354813 | 27.413822 | 1.940991 | 6.61% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c8:q2_b4_m8 | 32.488101 | 30.755604 | 1.732496 | 5.33% | not_established | 8 / 1 / 8 | none / full |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | — | — | — | — | not_established | — / — / — | — / — |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | — | — | — | — | not_established | — / — / — | — / — |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | — | — | — | — | not_established | — / — / — | — / — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | 49.984739 | 49.317682 | 0.667058 | 1.33% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | 50.227508 | 49.552575 | 0.674933 | 1.34% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | 34.239103 | 33.579092 | 0.660011 | 1.93% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | 48.703795 | 48.003864 | 0.699931 | 1.44% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | 185.130761 | 181.542159 | 3.588602 | 1.94% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | 54.967136 | 54.296272 | 0.670864 | 1.22% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | 50.515059 | 49.845037 | 0.670022 | 1.33% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | 51.750107 | 51.077579 | 0.672528 | 1.30% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b1_m8 | 51.592999 | 50.678830 | 0.914169 | 1.77% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | 50.042250 | 49.369207 | 0.673044 | 1.34% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | 51.607722 | 50.920601 | 0.687121 | 1.33% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | 262.496916 | 259.635735 | 2.861181 | 1.09% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | 47.654000 | 46.948644 | 0.705356 | 1.48% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | 50.154700 | 48.252669 | 1.902031 | 3.79% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | 61.811249 | 61.114951 | 0.696298 | 1.13% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 | 72.359330 | 70.911770 | 1.447560 | 2.00% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 | 59.510906 | 58.818469 | 0.692436 | 1.16% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 | 55.144861 | 54.462681 | 0.682180 | 1.24% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 | 63.460852 | 62.707830 | 0.753022 | 1.19% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 | 54.821604 | 54.149919 | 0.671686 | 1.23% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 | 58.827980 | 58.125277 | 0.702703 | 1.19% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 | 56.627079 | 55.953760 | 0.673318 | 1.19% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b3_m24 | 49.513901 | 48.795326 | 0.718575 | 1.45% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 | 57.975442 | 57.304422 | 0.671019 | 1.16% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 | 50.256336 | 49.584132 | 0.672204 | 1.34% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | 48.581862 | 47.882945 | 0.698917 | 1.44% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | 52.940304 | 52.210892 | 0.729412 | 1.38% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | 48.606206 | 47.850255 | 0.755951 | 1.56% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | 47.116268 | 46.410050 | 0.706218 | 1.50% | not_established | 4 / 4 / 16 | eager / full |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 27.285973 | 27.187901 | 0.098072 | 0.36% | not_established | 1 / 8 / 8 | auto / full |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 32.555493 | — | — | — | FULL_DECODE_ONLY | 8 / 4 / 32 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | moe_layer | 1 / 40 | 0.373173 | 0.352684 | 0.435251 | 0.224437 | -39.86% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | moe_layer | 1 / 40 | 0.465552 | 0.444202 | 0.534740 | 0.295004 | -36.63% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | moe_layer | 1 / 40 | 0.330911 | 0.300274 | 0.378501 | 0.188291 | -43.10% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | dense_layer | 0 / 1 | 0.921918 | 0.921918 | 0.921918 | 0.373289 | -59.51% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | moe_layer | 1 / 3 | 0.796936 | 0.814264 | 0.835939 | 0.652850 | -18.08% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | dense_layer | 0 / 1 | 0.902124 | 0.902124 | 0.902124 | 0.477502 | -47.07% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | moe_layer | 1 / 3 | 1.336028 | 1.365465 | 1.453488 | 1.011466 | -24.29% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | dense_layer | 0 / 1 | 0.884665 | 0.884665 | 0.884665 | 0.585183 | -33.85% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | moe_layer | 2 / 3 | 1.963693 | 1.922699 | 2.172615 | 1.629790 | -17.00% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | dense_layer | 0 / 1 | 0.868805 | 0.868805 | 0.868805 | 0.388289 | -55.31% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | moe_layer | 0 / 3 | 0.916748 | 0.941859 | 0.968316 | 0.667850 | -27.15% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | dense_layer | 0 / 1 | 0.960436 | 0.960436 | 0.960436 | 0.804913 | -16.19% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | moe_layer | 2 / 3 | 2.917340 | 2.803217 | 3.209222 | 2.637920 | -9.58% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | dense_layer | 0 / 1 | 0.304707 | 0.304707 | 0.304707 | 0.204823 | -32.78% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | moe_layer | 0 / 92 | 0.423260 | 0.387824 | 0.524838 | 0.249202 | -41.12% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | dense_layer | 0 / 1 | 0.335331 | 0.335331 | 0.335331 | 0.204823 | -38.92% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | moe_layer | 0 / 92 | 0.398339 | 0.387665 | 0.429149 | 0.236046 | -40.74% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | dense_layer | 0 / 1 | 0.259493 | 0.259493 | 0.259493 | 0.171311 | -33.98% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | moe_layer | 0 / 92 | 0.332185 | 0.322766 | 0.359609 | 0.204256 | -38.51% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | dense_layer | 0 / 1 | 0.277218 | 0.277218 | 0.277218 | 0.171311 | -38.20% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | moe_layer | 0 / 92 | 0.329965 | 0.323096 | 0.350795 | 0.203434 | -38.35% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | dense_layer | 0 / 1 | 0.287557 | 0.287557 | 0.287557 | 0.172889 | -39.88% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | moe_layer | 0 / 92 | 0.365059 | 0.354655 | 0.392704 | 0.206656 | -43.39% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | dense_layer | 0 / 1 | 0.302651 | 0.302651 | 0.302651 | 0.172889 | -42.88% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | moe_layer | 0 / 92 | 0.361328 | 0.354921 | 0.377885 | 0.205012 | -43.26% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | dense_layer | 0 / 1 | 0.362005 | 0.362005 | 0.362005 | 0.246251 | -31.98% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | moe_layer | 0 / 92 | 0.481537 | 0.416109 | 0.665712 | 0.302373 | -37.21% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | dense_layer | 0 / 1 | 0.337916 | 0.337916 | 0.337916 | 0.246251 | -27.13% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | moe_layer | 0 / 92 | 0.431283 | 0.415274 | 0.473567 | 0.276062 | -35.99% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | dense_layer | 0 / 1 | 0.297407 | 0.297407 | 0.297407 | 0.176045 | -40.81% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | moe_layer | 0 / 92 | 0.375177 | 0.361169 | 0.412914 | 0.211457 | -43.64% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | dense_layer | 0 / 1 | 0.293014 | 0.293014 | 0.293014 | 0.176045 | -39.92% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | moe_layer | 0 / 92 | 0.368455 | 0.361005 | 0.387096 | 0.208168 | -43.50% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | dense_layer | 0 / 1 | 0.284019 | 0.284019 | 0.284019 | 0.182357 | -35.79% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | moe_layer | 0 / 92 | 0.387800 | 0.367269 | 0.446146 | 0.221058 | -43.00% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | dense_layer | 0 / 1 | 0.310159 | 0.310159 | 0.310159 | 0.182357 | -41.21% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | moe_layer | 0 / 92 | 0.375068 | 0.367254 | 0.397893 | 0.214480 | -42.82% |
| v4flash-a3-tp8-c4:q2_b4_m8 | moe_layer | 19 / 43 | 0.754333 | 0.756827 | 0.850173 | 0.615008 | -18.47% |
| v4flash-a3-tp8-c8:q2_b8_m16 | moe_layer | 31 / 43 | 0.877069 | 0.807240 | 0.979574 | 0.778225 | -11.27% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | moe_layer | 39 / 40 | 1.256829 | 1.189883 | 1.439809 | 1.265387 | +0.68% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | moe_layer | 39 / 40 | 1.379618 | 1.308635 | 1.584825 | 1.365860 | -1.00% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | moe_layer | 39 / 40 | 1.198705 | 1.131824 | 1.351136 | 1.211818 | +1.09% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | moe_layer | 39 / 40 | 1.550226 | 1.465994 | 1.871356 | 1.548725 | -0.10% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | moe_layer | 40 / 40 | 1.221524 | 1.164096 | 1.419689 | 1.245767 | +1.98% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | moe_layer | 1 / 40 | 0.682128 | 0.654867 | 0.771288 | 0.470273 | -31.06% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | dense_layer | 0 / 1 | 0.257923 | 0.257923 | 0.257923 | 0.153245 | -40.58% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | moe_layer | 0 / 92 | 0.351316 | 0.341372 | 0.378042 | 0.268428 | -23.59% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | mla | 1 / 40 | 0.373173 | 0.352684 | 0.435251 | 0.224437 | -39.86% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 1 / 40 | 0.465552 | 0.444202 | 0.534740 | 0.295004 | -36.63% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 1 / 40 | 0.330911 | 0.300274 | 0.378501 | 0.188291 | -43.10% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | kda | 1 / 3 | 0.825596 | 0.814264 | 0.921918 | 0.565632 | -31.49% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | mla | 0 / 1 | 0.835939 | 0.835939 | 0.835939 | 0.634942 | -24.04% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | kda | 1 / 3 | 1.152240 | 1.189132 | 1.365465 | 0.841669 | -26.95% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | mla | 0 / 1 | 1.453488 | 1.453488 | 1.453488 | 0.986894 | -32.10% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 2 / 3 | 1.534376 | 1.795764 | 1.922699 | 1.290298 | -15.91% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 0 / 1 | 2.172615 | 2.172615 | 2.172615 | 1.603659 | -26.19% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | kda | 0 / 3 | 0.883578 | 0.868805 | 0.941859 | 0.580632 | -34.29% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | mla | 0 / 1 | 0.968316 | 0.968316 | 0.968316 | 0.649942 | -32.88% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | kda | 2 / 3 | 2.167745 | 2.739582 | 2.803217 | 2.037393 | -6.01% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | mla | 0 / 1 | 3.209222 | 3.209222 | 3.209222 | 2.606493 | -18.78% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 0 / 69 | 0.384646 | 0.385628 | 0.391398 | 0.238376 | -38.03% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 0 / 24 | 0.529336 | 0.522407 | 0.529076 | 0.278477 | -47.39% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 0 / 69 | 0.385013 | 0.385311 | 0.391916 | 0.238376 | -38.09% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 0 / 24 | 0.434026 | 0.426707 | 0.433591 | 0.228047 | -47.46% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | kda | 0 / 69 | 0.319910 | 0.320784 | 0.326143 | 0.205244 | -35.84% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | mla | 0 / 24 | 0.364449 | 0.357714 | 0.364380 | 0.200044 | -45.11% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | kda | 0 / 69 | 0.320268 | 0.320936 | 0.326067 | 0.205244 | -35.91% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | mla | 0 / 24 | 0.355645 | 0.348782 | 0.355492 | 0.196892 | -44.64% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | kda | 0 / 69 | 0.352160 | 0.352714 | 0.358215 | 0.206822 | -41.27% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | mla | 0 / 24 | 0.398913 | 0.391929 | 0.399012 | 0.204773 | -48.67% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | kda | 0 / 69 | 0.352595 | 0.353094 | 0.358531 | 0.206822 | -41.34% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | mla | 0 / 24 | 0.383988 | 0.376708 | 0.384608 | 0.198470 | -48.31% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 0 / 69 | 0.413723 | 0.414344 | 0.421089 | 0.278727 | -32.63% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 0 / 24 | 0.671523 | 0.664634 | 0.670936 | 0.368019 | -45.20% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 0 / 69 | 0.413032 | 0.413826 | 0.420032 | 0.278727 | -32.52% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 0 / 24 | 0.479865 | 0.472316 | 0.479303 | 0.267158 | -44.33% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | kda | 0 / 69 | 0.358721 | 0.359340 | 0.364725 | 0.209978 | -41.46% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | mla | 0 / 24 | 0.419247 | 0.412473 | 0.418457 | 0.214233 | -48.90% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | kda | 0 / 69 | 0.358666 | 0.359601 | 0.365194 | 0.209978 | -41.46% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | mla | 0 / 24 | 0.393454 | 0.386399 | 0.392108 | 0.201626 | -48.75% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | kda | 0 / 69 | 0.364080 | 0.364932 | 0.370969 | 0.216290 | -40.59% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | mla | 0 / 24 | 0.451672 | 0.445328 | 0.451445 | 0.233153 | -48.38% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | kda | 0 / 69 | 0.364444 | 0.364580 | 0.370731 | 0.216290 | -40.65% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | mla | 0 / 24 | 0.402906 | 0.396176 | 0.402359 | 0.207938 | -48.39% |
| v4flash-a3-tp8-c4:q2_b4_m8 | mla | 19 / 43 | 0.754333 | 0.756827 | 0.850173 | 0.615008 | -18.47% |
| v4flash-a3-tp8-c8:q2_b8_m16 | mla | 31 / 43 | 0.877069 | 0.807240 | 0.979574 | 0.778225 | -11.27% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | mla | 39 / 40 | 1.256829 | 1.189883 | 1.439809 | 1.265387 | +0.68% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | mla | 39 / 40 | 1.379618 | 1.308635 | 1.584825 | 1.365860 | -1.00% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | mla | 39 / 40 | 1.198705 | 1.131824 | 1.351136 | 1.211818 | +1.09% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | mla | 39 / 40 | 1.550226 | 1.465994 | 1.871356 | 1.548725 | -0.10% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | mla | 40 / 40 | 1.221524 | 1.164096 | 1.419689 | 1.245767 | +1.98% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | mla | 1 / 40 | 0.682128 | 0.654867 | 0.771288 | 0.470273 | -31.06% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | kda | 0 / 69 | 0.338761 | 0.339556 | 0.344976 | 0.266478 | -21.34% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | mla | 0 / 24 | 0.383520 | 0.376471 | 0.383168 | 0.269234 | -29.80% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | mla | 0.373173 | 0.370790 | 0.002383 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 0.465552 | 0.463139 | 0.002414 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 0.330911 | 0.328581 | 0.002330 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | kda | 0.825596 | 0.811190 | 0.014406 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | mla | 0.835939 | 0.784698 | 0.051240 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | kda | 1.152240 | 1.136963 | 0.015278 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | mla | 1.453488 | 1.399692 | 0.053796 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 1.534376 | 1.517276 | 0.017100 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 2.172615 | 2.118742 | 0.053873 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | kda | 0.883578 | 0.868957 | 0.014621 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | mla | 0.968316 | 0.912434 | 0.055882 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | kda | 2.167745 | 2.147499 | 0.020246 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | mla | 3.209222 | 3.155193 | 0.054029 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 0.384646 | 0.379054 | 0.005591 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 0.529336 | 0.517159 | 0.012177 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 0.385013 | 0.379424 | 0.005589 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 0.434026 | 0.421850 | 0.012176 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | kda | 0.319910 | 0.314950 | 0.004960 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | mla | 0.364449 | 0.352180 | 0.012269 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | kda | 0.320268 | 0.315305 | 0.004963 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | mla | 0.355645 | 0.343375 | 0.012270 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | kda | 0.352160 | 0.346560 | 0.005600 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | mla | 0.398913 | 0.386575 | 0.012338 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | kda | 0.352595 | 0.346938 | 0.005657 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | mla | 0.383988 | 0.371592 | 0.012396 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 0.413723 | 0.407971 | 0.005752 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 0.671523 | 0.659202 | 0.012321 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 0.413032 | 0.407278 | 0.005754 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 0.479865 | 0.467530 | 0.012334 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | kda | 0.358721 | 0.352935 | 0.005785 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | mla | 0.419247 | 0.406773 | 0.012474 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | kda | 0.358666 | 0.352873 | 0.005793 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | mla | 0.393454 | 0.380967 | 0.012487 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | kda | 0.364080 | 0.358480 | 0.005600 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | mla | 0.451672 | 0.439438 | 0.012234 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | kda | 0.364444 | 0.358904 | 0.005540 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | mla | 0.402906 | 0.390743 | 0.012163 |
| v4flash-a3-tp8-c4:q2_b4_m8 | mla | 0.754333 | 0.711895 | 0.042438 |
| v4flash-a3-tp8-c8:q2_b8_m16 | mla | 0.877069 | 0.840792 | 0.036277 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | mla | 1.256829 | 1.240894 | 0.015936 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | mla | 1.379618 | 1.363695 | 0.015922 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | mla | 1.198705 | 1.181799 | 0.016906 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | mla | 1.550226 | 1.533748 | 0.016479 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | mla | 1.221524 | 1.204788 | 0.016735 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | mla | 0.682128 | 0.679698 | 0.002430 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | kda | 0.338761 | — | — |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | mla | 0.383520 | — | — |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | all | 39 | 5031 | 0.371581 | 0.352624 | 0.216564 | -38.59% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | mla | 39 | 5031 | 0.371581 | 0.352624 | 0.216564 | -38.59% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | all | 39 | 4095 | 0.463953 | 0.444058 | 0.287046 | -35.36% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 39 | 4095 | 0.463953 | 0.444058 | 0.287046 | -35.36% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | all | 39 | 5889 | 0.317677 | 0.300299 | 0.180459 | -39.91% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 39 | 5889 | 0.317677 | 0.300299 | 0.180459 | -39.91% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | all | 3 | 762 | 0.796936 | 0.776385 | 0.661804 | -14.76% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | kda | 2 | 508 | 0.777435 | 0.725436 | 0.661804 | -8.77% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | mla | 1 | 254 | 0.835939 | 0.799415 | 0.634942 | -20.57% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | all | 3 | 705 | 1.336028 | 1.346153 | 1.023752 | -23.95% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | kda | 2 | 470 | 1.277298 | 1.265664 | 1.023752 | -19.11% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | mla | 1 | 235 | 1.453488 | 1.452451 | 0.986894 | -32.05% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | all | 3 | 660 | 1.963693 | 1.885652 | 1.642856 | -12.88% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 2 | 440 | 1.859231 | 1.840788 | 1.642856 | -10.75% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 1 | 220 | 2.172615 | 2.172336 | 1.603659 | -26.18% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | all | 3 | 738 | 0.916748 | 0.892432 | 0.676804 | -24.16% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | kda | 2 | 492 | 0.890964 | 0.848128 | 0.676804 | -20.20% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | mla | 1 | 246 | 0.968316 | 0.961650 | 0.649942 | -32.41% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | all | 3 | 588 | 2.917340 | 2.774904 | 2.653634 | -4.37% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | kda | 2 | 392 | 2.771399 | 2.756885 | 2.653634 | -3.75% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | mla | 1 | 196 | 3.209222 | 3.208946 | 2.606493 | -18.77% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | all | 92 | 4324 | 0.423260 | 0.387808 | 0.242721 | -37.41% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 68 | 3196 | 0.385821 | 0.385597 | 0.238539 | -38.14% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 24 | 1128 | 0.529336 | 0.522342 | 0.278365 | -46.71% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | all | 92 | 4508 | 0.398339 | 0.387570 | 0.235145 | -39.33% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 68 | 3332 | 0.385744 | 0.385530 | 0.238539 | -38.13% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 24 | 1176 | 0.434026 | 0.426871 | 0.227935 | -46.60% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | all | 92 | 5428 | 0.332185 | 0.322654 | 0.205158 | -36.42% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | kda | 68 | 4012 | 0.320798 | 0.320809 | 0.205412 | -35.97% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | mla | 24 | 1416 | 0.364449 | 0.357739 | 0.199931 | -44.11% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | all | 92 | 5428 | 0.329965 | 0.323043 | 0.202018 | -37.46% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | kda | 68 | 4012 | 0.320901 | 0.321012 | 0.205412 | -36.01% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | mla | 24 | 1416 | 0.355645 | 0.348701 | 0.196779 | -43.57% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | all | 92 | 4968 | 0.365059 | 0.354617 | 0.206990 | -41.63% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | kda | 68 | 3672 | 0.353110 | 0.352903 | 0.206990 | -41.35% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | mla | 24 | 1296 | 0.398913 | 0.391767 | 0.204661 | -47.76% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | all | 92 | 5060 | 0.361328 | 0.354858 | 0.203596 | -42.63% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | kda | 68 | 3740 | 0.353330 | 0.353148 | 0.206990 | -41.39% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | mla | 24 | 1320 | 0.383988 | 0.376723 | 0.198357 | -47.35% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | all | 92 | 3772 | 0.481537 | 0.415844 | 0.283056 | -31.93% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 68 | 2788 | 0.414483 | 0.414203 | 0.278874 | -32.67% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 24 | 984 | 0.671523 | 0.664380 | 0.367906 | -44.62% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | all | 92 | 4232 | 0.431283 | 0.415334 | 0.275480 | -33.67% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 68 | 3128 | 0.414137 | 0.414040 | 0.278874 | -32.65% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 24 | 1104 | 0.479865 | 0.472222 | 0.267046 | -43.45% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | all | 92 | 4784 | 0.375177 | 0.361188 | 0.212237 | -41.24% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | kda | 68 | 3536 | 0.359622 | 0.359235 | 0.210146 | -41.50% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | mla | 24 | 1248 | 0.419247 | 0.412474 | 0.214121 | -48.09% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | all | 92 | 4876 | 0.368455 | 0.361070 | 0.206752 | -42.74% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | kda | 68 | 3604 | 0.359632 | 0.359552 | 0.210146 | -41.55% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | mla | 24 | 1272 | 0.393454 | 0.386327 | 0.201513 | -47.84% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | all | 92 | 4692 | 0.387800 | 0.367070 | 0.220640 | -39.89% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | kda | 68 | 3468 | 0.365257 | 0.364968 | 0.216458 | -40.69% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | mla | 24 | 1224 | 0.451672 | 0.445448 | 0.233040 | -47.68% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | all | 92 | 4784 | 0.375068 | 0.366904 | 0.213064 | -41.93% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | kda | 68 | 3536 | 0.365243 | 0.364788 | 0.216458 | -40.66% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | mla | 24 | 1248 | 0.402906 | 0.395987 | 0.207825 | -47.52% |
| v4flash-a3-tp8-c4:q2_b4_m8 | all | 42 | 4368 | 0.754274 | 0.753685 | 0.618068 | -17.99% |
| v4flash-a3-tp8-c4:q2_b4_m8 | mla | 42 | 4368 | 0.754274 | 0.753685 | 0.618068 | -17.99% |
| v4flash-a3-tp8-c8:q2_b8_m16 | all | 42 | 4368 | 0.878732 | 0.883097 | 0.781455 | -11.51% |
| v4flash-a3-tp8-c8:q2_b8_m16 | mla | 42 | 4368 | 0.878732 | 0.883097 | 0.781455 | -11.51% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | all | 39 | 1248 | 1.252138 | 1.188276 | 1.250278 | +5.22% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | mla | 39 | 1248 | 1.252138 | 1.188276 | 1.250278 | +5.22% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | all | 39 | 858 | 1.371480 | 1.307714 | 1.345893 | +2.92% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | mla | 39 | 858 | 1.371480 | 1.307714 | 1.345893 | +2.92% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | all | 39 | 1872 | 1.179467 | 1.129198 | 1.199545 | +6.23% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | mla | 39 | 1872 | 1.179467 | 1.129198 | 1.199545 | +6.23% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | all | 39 | 819 | 1.547673 | 1.462711 | 1.520335 | +3.94% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | mla | 39 | 819 | 1.547673 | 1.462711 | 1.520335 | +3.94% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | all | 39 | 1131 | 1.216364 | 1.158637 | 1.231637 | +6.30% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | mla | 39 | 1131 | 1.216364 | 1.158637 | 1.231637 | +6.30% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | all | 39 | 2847 | 0.679042 | 0.654527 | 0.461163 | -29.54% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | mla | 39 | 2847 | 0.679042 | 0.654527 | 0.461163 | -29.54% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | all | 92 | 5796 | 0.351316 | 0.340746 | 0.268058 | -21.33% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | kda | 68 | 4284 | 0.339949 | 0.338622 | 0.267981 | -20.86% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | mla | 24 | 1512 | 0.383520 | 0.374659 | 0.269032 | -28.19% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 129 | 0.435251 | 0.420089 | 0.424730 | 0.216564 | -50.24% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 105 | 0.527918 | 0.520862 | 0.527346 | 0.287046 | -45.63% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 151 | 0.847040 | 0.816238 | 0.820195 | 0.180459 | -78.70% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 254 | 0.921918 | 0.911601 | 1.011820 | 0.373289 | -59.51% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 235 | 0.902124 | 0.935902 | 1.032420 | 0.477502 | -47.07% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 220 | 0.884665 | 0.918071 | 1.035580 | 0.585183 | -33.85% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 246 | 0.868805 | 0.892722 | 0.986620 | 0.388289 | -55.31% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 196 | 0.960436 | 0.952631 | 1.021539 | 0.804913 | -16.19% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 47 | 0.304707 | 0.302280 | 0.304417 | 0.204823 | -32.78% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 49 | 0.335331 | 0.302283 | 0.304588 | 0.204823 | -38.92% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 59 | 0.259493 | 0.258140 | 0.259720 | 0.171311 | -33.98% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 59 | 0.277218 | 0.257813 | 0.259545 | 0.171311 | -38.20% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 54 | 0.287557 | 0.269792 | 0.271359 | 0.172889 | -39.88% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 55 | 0.302651 | 0.269840 | 0.271908 | 0.172889 | -42.88% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 41 | 0.362005 | 0.338372 | 0.341159 | 0.246251 | -31.98% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 46 | 0.337916 | 0.337564 | 0.341257 | 0.246251 | -27.13% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 52 | 0.297407 | 0.276998 | 0.278997 | 0.176045 | -40.81% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 53 | 0.293014 | 0.277106 | 0.279247 | 0.176045 | -39.92% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 51 | 0.284019 | 0.281037 | 0.283397 | 0.182357 | -35.79% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 52 | 0.310159 | 0.281559 | 0.283741 | 0.182357 | -41.21% |
| v4flash-a3-tp8-c4:q2_b4_m8 | 104 | 0.756827 | 0.717805 | 0.958641 | 0.531272 | -29.80% |
| v4flash-a3-tp8-c8:q2_b8_m16 | 104 | 0.807240 | 0.766765 | 0.954481 | 0.689866 | -14.54% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | 32 | 1.439809 | 1.298684 | 1.648967 | 1.250278 | -13.16% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | 22 | 1.697000 | 1.564018 | 1.749065 | 1.345893 | -20.69% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | 48 | 1.948982 | 1.656527 | 2.027239 | 1.199545 | -38.45% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | 21 | 1.649789 | 1.473370 | 1.851743 | 1.520335 | -7.85% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | 29 | 1.422735 | 1.252335 | 1.455071 | 1.231637 | -13.43% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 73 | 0.802473 | 0.784160 | 0.791435 | 0.461163 | -42.53% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 63 | 0.257923 | 0.238298 | 0.250875 | 0.153245 | -40.58% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 1 | 2 | 2 | unknown | 2048 | 16 | 21.239293 | 20.616566 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 1 | 4 | 4 | unknown | 2048 | 32 | 22.363334 | 22.393036 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 1 | 1 | 1 | unknown | 2048 | 4 | 16.557655 | 16.561941 | — | — |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 1 | 7.167215 | 7.167215 | — | — |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 1 | 16 | 16 | unknown | 4096 | 16 | 8.646915 | 8.627808 | — | — |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 16 | 8.646915 | 8.627808 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 1 | 32 | 32 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 1 | 8 | 8 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 1 | 16 | 16 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 4 | 7.450663 | 7.475983 | — | — |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 4 | 7.450663 | 7.475983 | — | — |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 4 | 7.450663 | 7.475983 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 1 | 64 | 64 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | 1 | 48 | 48 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | 1 | 24 | 24 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | 1 | 16 | 16 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 1 | 16 | 16 | unknown | 16392 | 16 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 1 | 16 | 16 | unknown | 4104 | 16 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 1 | 1 | 1 | unknown | 16392 | 1 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 1 | 1 | 1 | unknown | 4104 | 1 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 1 | 2 | 2 | unknown | 16392 | 2 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 1 | 2 | 2 | unknown | 4104 | 2 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 1 | 32 | 32 | unknown | 16392 | 32 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 1 | 32 | 32 | unknown | 4104 | 32 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 1 | 4 | 4 | unknown | 16392 | 4 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 1 | 4 | 4 | unknown | 4104 | 4 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 1 | 8 | 8 | unknown | 16392 | 8 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 1 | 8 | 8 | unknown | 4104 | 8 | — | — | — | — |
| v4flash-a3-tp8-c4:q2_b4_m8 | 2 | 4 | 8 | unknown | 4096 | 4 | 53.936384 | 47.929425 | — | 39.377165 |
| v4flash-a3-tp8-c4:q2_b1_m2 | 2 | 1 | 2 | unknown | 4096 | 4 | 53.936384 | 47.929425 | — | 39.377165 |
| v4flash-a3-tp8-c8:q2_b8_m16 | 2 | 8 | 16 | unknown | 4096 | 8 | 68.120259 | 62.964366 | — | 45.008620 |
| v4flash-a3-tp8-c8:q2_b2_m4 | 2 | 2 | 4 | unknown | 4096 | 8 | 68.120259 | 62.964366 | — | 45.008620 |
| v4flash-a3-tp8-c8:q2_b1_m2 | 2 | 1 | 2 | unknown | 4096 | 8 | 68.120259 | 62.964366 | — | 45.008620 |
| v4flash-a3-tp8-c8:q2_b4_m8 | 2 | 4 | 8 | unknown | 4096 | 8 | 68.120259 | 62.964366 | — | 45.008620 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | — | — | — | unknown | — | — | — | — | — | — |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | — | — | — | unknown | — | — | — | — | — | — |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | — | — | — | unknown | — | — | — | — | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | 8 | 5 | 40 | unknown | 4096 | 16 | — | 58.612550 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | 8 | 6 | 48 | unknown | 4096 | 16 | — | 58.612550 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | 8 | 1 | 8 | unknown | 4096 | 16 | — | 58.612550 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | 8 | 4 | 32 | unknown | 4096 | 16 | — | 58.612550 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | 8 | 3 | 24 | unknown | 4096 | 16 | — | 58.612550 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | 8 | 9 | 72 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | 8 | 7 | 56 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | 8 | 8 | 64 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b1_m8 | 8 | 1 | 8 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | 8 | 6 | 48 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | 8 | 5 | 40 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | 8 | 3 | 24 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | 8 | 2 | 16 | unknown | 4096 | 4 | — | 56.226793 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | 8 | 1 | 8 | unknown | 4096 | 4 | — | 56.226793 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | 8 | 17 | 136 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 | 8 | 1 | 8 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 | 8 | 15 | 120 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 | 8 | 10 | 80 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 | 8 | 16 | 128 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 | 8 | 9 | 72 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 | 8 | 14 | 112 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 | 8 | 12 | 96 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b3_m24 | 8 | 3 | 24 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 | 8 | 13 | 104 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 | 8 | 5 | 40 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | 8 | 4 | 32 | unknown | 4096 | 8 | — | 57.909682 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | 8 | 3 | 24 | unknown | 4096 | 8 | — | 57.909682 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | 8 | 1 | 8 | unknown | 4096 | 8 | — | 57.909682 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | 8 | 2 | 16 | unknown | 4096 | 8 | — | 57.909682 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 1 | 16 | 16 | unknown | 2048 | 128 | — | 33.341304 | — | — |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 1 | 1 | 1 | unknown | 32768 | 1 | 66.586585 | 66.586585 | — | 64.353701 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | embedding | 129 | 0.003381 | 0.003336 | 0.003618 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | output_head_preparation | 129 | 0.014962 | 0.014987 | 0.015300 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | final_norm | 129 | 0.002669 | 0.002646 | 0.002780 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | embedding | 105 | 0.004095 | 0.004051 | 0.004470 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | output_head_preparation | 105 | 0.016335 | 0.016280 | 0.016827 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | final_norm | 105 | 0.002770 | 0.002767 | 0.002848 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | output_head_preparation | 151 | 0.013937 | 0.013868 | 0.014536 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | final_norm | 151 | 0.002446 | 0.002420 | 0.002571 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | embedding | 254 | 0.009523 | 0.009420 | 0.009740 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | final_norm | 254 | 0.003637 | 0.003640 | 0.003700 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | lm_head | 254 | 0.275756 | 0.275744 | 0.278314 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | embedding | 235 | 0.005061 | 0.005020 | 0.005320 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | final_norm | 235 | 0.006631 | 0.006500 | 0.006819 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | lm_head | 235 | 0.312556 | 0.312613 | 0.316314 |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | embedding | 3 | 0.009047 | 0.009080 | 0.009300 |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | final_norm | 3 | 0.003587 | 0.003580 | 0.003600 |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | lm_head | 3 | 0.276741 | 0.277055 | 0.278654 |
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
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | embedding | 246 | 0.003053 | 0.003040 | 0.003319 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | final_norm | 246 | 0.004334 | 0.004320 | 0.004480 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | lm_head | 246 | 0.284209 | 0.284254 | 0.287035 |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | embedding | 4 | 0.002780 | 0.002780 | 0.002980 |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | final_norm | 4 | 0.003945 | 0.003949 | 0.004000 |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | lm_head | 4 | 0.282285 | 0.282095 | 0.286114 |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | embedding | 3 | 0.009247 | 0.009240 | 0.009300 |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | final_norm | 3 | 0.003627 | 0.003640 | 0.003660 |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | lm_head | 3 | 0.275981 | 0.276014 | 0.276755 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | embedding | 196 | 0.009384 | 0.009360 | 0.009680 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | final_norm | 196 | 0.010675 | 0.010400 | 0.010640 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | lm_head | 196 | 0.329141 | 0.328854 | 0.332534 |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | embedding | 3 | 0.008933 | 0.008899 | 0.009060 |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | final_norm | 3 | 0.003567 | 0.003560 | 0.003580 |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | lm_head | 3 | 0.276587 | 0.276014 | 0.279314 |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | embedding | 2 | 0.006850 | 0.006850 | 0.007000 |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | final_norm | 2 | 0.009080 | 0.009080 | 0.009199 |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | lm_head | 2 | 0.320554 | 0.320554 | 0.320933 |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | embedding | 2 | 0.006979 | 0.006979 | 0.007100 |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | final_norm | 2 | 0.008540 | 0.008540 | 0.008640 |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | lm_head | 2 | 0.307554 | 0.307554 | 0.309354 |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | embedding | 2 | 0.005020 | 0.005020 | 0.005060 |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | final_norm | 2 | 0.007720 | 0.007720 | 0.008960 |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | lm_head | 2 | 0.310954 | 0.310954 | 0.311894 |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | embedding | 1 | 0.002520 | 0.002520 | 0.002520 |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | final_norm | 1 | 0.004000 | 0.004000 | 0.004000 |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | lm_head | 1 | 0.287334 | 0.287334 | 0.287334 |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | embedding | 1 | 0.002840 | 0.002840 | 0.002840 |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | final_norm | 1 | 0.004400 | 0.004400 | 0.004400 |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | lm_head | 1 | 0.281494 | 0.281494 | 0.281494 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | embedding | 47 | 0.004621 | 0.004452 | 0.005158 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | final_norm | 47 | 0.004149 | 0.004128 | 0.004346 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | lm_head | 47 | 0.092373 | 0.092297 | 0.093138 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | embedding | 49 | 0.004593 | 0.004509 | 0.005168 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | final_norm | 49 | 0.004091 | 0.004082 | 0.004295 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | lm_head | 49 | 0.092424 | 0.092431 | 0.093127 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | embedding | 59 | 0.003153 | 0.003145 | 0.003345 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | final_norm | 59 | 0.002648 | 0.002644 | 0.002801 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | lm_head | 59 | 0.090694 | 0.090708 | 0.091441 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | embedding | 59 | 0.003171 | 0.003139 | 0.003410 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | final_norm | 59 | 0.002656 | 0.002643 | 0.002785 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | lm_head | 59 | 0.090801 | 0.090715 | 0.091604 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | embedding | 54 | 0.003248 | 0.003227 | 0.003438 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | final_norm | 54 | 0.003575 | 0.003547 | 0.003697 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | lm_head | 54 | 0.090737 | 0.090634 | 0.091393 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | embedding | 55 | 0.003310 | 0.003279 | 0.003502 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | final_norm | 55 | 0.003606 | 0.003582 | 0.003776 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | lm_head | 55 | 0.090726 | 0.090704 | 0.091558 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | embedding | 41 | 0.003452 | 0.003466 | 0.003683 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | final_norm | 41 | 0.005865 | 0.005876 | 0.006045 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | lm_head | 41 | 0.117608 | 0.117655 | 0.118201 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | embedding | 46 | 0.003423 | 0.003405 | 0.003697 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | final_norm | 46 | 0.005558 | 0.005548 | 0.005768 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | lm_head | 46 | 0.117594 | 0.117492 | 0.118427 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | embedding | 52 | 0.004307 | 0.004195 | 0.004880 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | final_norm | 52 | 0.003656 | 0.003638 | 0.003791 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | lm_head | 52 | 0.091122 | 0.090941 | 0.091927 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | embedding | 53 | 0.004472 | 0.004372 | 0.005045 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | final_norm | 53 | 0.003639 | 0.003622 | 0.003763 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | lm_head | 53 | 0.091033 | 0.090857 | 0.091549 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | embedding | 51 | 0.004301 | 0.004254 | 0.004600 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | final_norm | 51 | 0.003739 | 0.003723 | 0.003842 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | lm_head | 51 | 0.091241 | 0.091220 | 0.091749 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | embedding | 52 | 0.004275 | 0.004245 | 0.004557 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | final_norm | 52 | 0.003738 | 0.003722 | 0.003837 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | lm_head | 52 | 0.091316 | 0.091258 | 0.092021 |
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
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | embedding | 32 | 0.008862 | 0.008890 | 0.009200 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | output_head_preparation | 32 | 0.356277 | 0.355973 | 0.358613 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | final_norm | 32 | 0.014816 | 0.014760 | 0.015240 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | embedding | 20 | 0.007475 | 0.007430 | 0.007759 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | output_head_preparation | 20 | 0.351240 | 0.351013 | 0.352973 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | final_norm | 20 | 0.009730 | 0.009729 | 0.009960 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | output_head_preparation | 15 | 0.312376 | 0.311674 | 0.315154 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | final_norm | 15 | 0.005845 | 0.005820 | 0.006080 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | embedding | 2 | 0.003830 | 0.003830 | 0.004060 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | embedding | 8 | 0.005952 | 0.005970 | 0.007260 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | output_head_preparation | 8 | 0.333853 | 0.334693 | 0.336334 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | final_norm | 8 | 0.011817 | 0.011810 | 0.012420 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | embedding | 1 | 0.005840 | 0.005840 | 0.005840 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | output_head_preparation | 1 | 0.350973 | 0.350973 | 0.350973 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | final_norm | 1 | 0.009360 | 0.009360 | 0.009360 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | embedding | 22 | 0.007214 | 0.007140 | 0.007660 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | output_head_preparation | 22 | 0.368570 | 0.367993 | 0.370632 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | final_norm | 22 | 0.014659 | 0.014680 | 0.014880 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | embedding | 17 | 0.006761 | 0.006940 | 0.007120 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | output_head_preparation | 17 | 0.358314 | 0.358513 | 0.360813 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | final_norm | 17 | 0.011328 | 0.011260 | 0.011700 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | embedding | 16 | 0.006899 | 0.006860 | 0.007060 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | output_head_preparation | 16 | 0.359054 | 0.359463 | 0.361693 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | final_norm | 16 | 0.013194 | 0.013189 | 0.013640 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b1_m8 | output_head_preparation | 14 | 0.313637 | 0.313224 | 0.315394 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b1_m8 | final_norm | 14 | 0.005784 | 0.005830 | 0.006019 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | embedding | 4 | 0.007105 | 0.006370 | 0.009480 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | output_head_preparation | 4 | 0.353663 | 0.353323 | 0.357252 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | final_norm | 4 | 0.009695 | 0.009620 | 0.009940 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | embedding | 3 | 0.006387 | 0.006040 | 0.007280 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | output_head_preparation | 3 | 0.354926 | 0.355413 | 0.356253 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | final_norm | 3 | 0.014506 | 0.014540 | 0.014620 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | embedding | 1 | 0.005700 | 0.005700 | 0.005700 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | output_head_preparation | 1 | 0.378372 | 0.378372 | 0.378372 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | final_norm | 1 | 0.008400 | 0.008400 | 0.008400 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | output_head_preparation | 48 | 0.325974 | 0.324164 | 0.332453 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | final_norm | 48 | 0.007295 | 0.007260 | 0.007680 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | embedding | 17 | 0.004945 | 0.004900 | 0.005120 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | output_head_preparation | 30 | 0.351012 | 0.312613 | 0.316094 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | final_norm | 30 | 0.005851 | 0.005840 | 0.006120 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | embedding | 11 | 0.003611 | 0.003620 | 0.003780 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | embedding | 21 | 0.008124 | 0.008119 | 0.008460 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | output_head_preparation | 21 | 0.402302 | 0.402352 | 0.406091 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | final_norm | 21 | 0.015404 | 0.015340 | 0.015859 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 | output_head_preparation | 13 | 0.317838 | 0.312053 | 0.326034 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 | final_norm | 13 | 0.005801 | 0.005760 | 0.006040 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 | embedding | 1 | 0.003740 | 0.003740 | 0.003740 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 | embedding | 11 | 0.007723 | 0.007740 | 0.008440 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 | output_head_preparation | 11 | 0.385694 | 0.385952 | 0.387272 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 | final_norm | 11 | 0.017636 | 0.017440 | 0.018120 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 | embedding | 8 | 0.007963 | 0.008340 | 0.008600 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 | output_head_preparation | 8 | 0.370152 | 0.370113 | 0.372393 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 | final_norm | 8 | 0.016395 | 0.016379 | 0.016740 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 | embedding | 7 | 0.008251 | 0.008080 | 0.009140 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 | output_head_preparation | 7 | 0.394901 | 0.392072 | 0.413811 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 | final_norm | 7 | 0.014714 | 0.014700 | 0.015180 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 | embedding | 5 | 0.007140 | 0.007340 | 0.007700 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 | output_head_preparation | 5 | 0.369109 | 0.370793 | 0.371773 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 | final_norm | 5 | 0.014908 | 0.015000 | 0.015060 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 | embedding | 4 | 0.008470 | 0.008430 | 0.008880 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 | output_head_preparation | 4 | 0.388932 | 0.389422 | 0.392272 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 | final_norm | 4 | 0.021625 | 0.021700 | 0.022040 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 | embedding | 2 | 0.008250 | 0.008250 | 0.008300 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 | output_head_preparation | 2 | 0.384402 | 0.384402 | 0.385072 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 | final_norm | 2 | 0.013640 | 0.013640 | 0.013740 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b3_m24 | output_head_preparation | 2 | 0.325094 | 0.325094 | 0.326253 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b3_m24 | final_norm | 2 | 0.008959 | 0.008959 | 0.009099 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 | embedding | 2 | 0.007120 | 0.007120 | 0.007220 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 | output_head_preparation | 2 | 0.377993 | 0.377993 | 0.379273 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 | final_norm | 2 | 0.015480 | 0.015480 | 0.015879 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 | embedding | 1 | 0.008560 | 0.008560 | 0.008560 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 | output_head_preparation | 1 | 0.359973 | 0.359973 | 0.359973 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 | final_norm | 1 | 0.015000 | 0.015000 | 0.015000 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | embedding | 29 | 0.007257 | 0.007240 | 0.007380 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | output_head_preparation | 29 | 0.336221 | 0.336313 | 0.338114 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | final_norm | 29 | 0.011816 | 0.011760 | 0.012219 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | embedding | 28 | 0.003791 | 0.003720 | 0.004000 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | output_head_preparation | 28 | 0.327837 | 0.326354 | 0.329513 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | final_norm | 28 | 0.008859 | 0.008840 | 0.009080 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | output_head_preparation | 16 | 0.312757 | 0.312584 | 0.314913 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | final_norm | 16 | 0.005796 | 0.005780 | 0.006019 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | embedding | 2 | 0.003660 | 0.003660 | 0.003740 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | embedding | 4 | 0.003770 | 0.003680 | 0.004060 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | output_head_preparation | 4 | 0.325269 | 0.325554 | 0.327473 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | final_norm | 4 | 0.007425 | 0.007380 | 0.007620 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | embedding | 73 | 0.004227 | 0.004184 | 0.004651 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | output_head_preparation | 73 | 0.020123 | 0.020179 | 0.020740 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | final_norm | 73 | 0.003980 | 0.003950 | 0.004119 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | embedding | 63 | 0.003108 | 0.003075 | 0.003299 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | final_norm | 63 | 0.004363 | 0.004258 | 0.004465 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | lm_head | 63 | 0.092173 | 0.092155 | 0.092665 |

Summary: {"case_count": 74, "compared_cases": 29, "failed_cases": 3, "measured_cases": 71, "passed_cases": 7, "source_case_count": 32, "unresolved_cases": 42}
