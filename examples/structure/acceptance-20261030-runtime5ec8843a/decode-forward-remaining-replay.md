# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "5ec8843a7e1711d0333dd59f9aec4f19f4f40363"}.

Variant: `body-runtime5ec8843a-remaining`. Baseline: null.

Sim 0.8.0; 261 package files; SHA256 `c8393b666a67919c06c6929112c49eeef8519c4a757e486c59d63938c8db79e9`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 63 | 32.555493 | 32.533125 | 32.673798 | — | — | failed: body_prediction_memory_budget_exceeded |
| v4flash-a3-tp8-c4:q2_b4_m8 | 104 | 32.485961 | 32.416312 | 32.734306 | 26.525128 | -18.35% | compared |
| v4flash-a3-tp8-c4:q2_b1_m2 | 4 | 29.500360 | 29.511530 | 29.660627 | — | — | unresolved: prediction_deferred_by_population_priority |
| v4flash-a3-tp8-c8:q2_b8_m16 | 104 | 37.763131 | 37.868163 | 38.081839 | 33.555657 | -11.14% | compared |
| v4flash-a3-tp8-c8:q2_b2_m4 | 3 | 31.294368 | 31.233516 | 31.612229 | — | — | unresolved: prediction_deferred_by_population_priority |
| v4flash-a3-tp8-c8:q2_b1_m2 | 2 | 29.354813 | 29.354813 | 29.421692 | — | — | unresolved: prediction_deferred_by_population_priority |
| v4flash-a3-tp8-c8:q2_b4_m8 | 2 | 32.488101 | 32.488101 | 32.561889 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 23 | 76.089008 | 76.132320 | 76.632160 | 68.304549 | -10.23% | compared |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 18 | 119.054350 | 119.130970 | 119.486280 | 102.866205 | -13.60% | compared |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 254 | 3.180250 | 3.127828 | 3.431912 | 2.528191 | -20.50% | compared |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 235 | 4.807080 | 4.779005 | 4.992080 | 3.522175 | -26.73% | compared |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | 3 | 3.844777 | 3.280615 | 5.439251 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 220 | 6.713782 | 6.664787 | 6.922921 | 5.348630 | -20.33% | compared |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 3 | 3.240302 | 3.278234 | 3.410932 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 3 | 3.363853 | 3.379593 | 3.466951 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 1 | 3.812064 | 3.812064 | 3.812064 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 1 | 2.978001 | 2.978001 | 2.978001 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 1 | 4.690486 | 4.690486 | 4.690486 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 246 | 3.476353 | 3.437971 | 3.655687 | 2.572222 | -26.01% | compared |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | 4 | 3.375663 | 3.346474 | 3.556049 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | 3 | 3.190596 | 3.244875 | 3.293894 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 196 | 9.615404 | 9.549549 | 9.774245 | 8.308757 | -13.59% | compared |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | 3 | 3.178496 | 3.253895 | 3.501150 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | 2 | 8.472921 | 8.472921 | 8.559829 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | 2 | 5.631388 | 5.631388 | 5.719806 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | 2 | 4.722715 | 4.722715 | 4.738645 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | 1 | 3.160037 | 3.160037 | 3.160037 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | 1 | 3.536929 | 3.536929 | 3.536929 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | 32 | 49.984739 | 49.802195 | 50.230116 | 52.474283 | +4.98% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | 20 | 50.227508 | 50.207347 | 50.437972 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | 15 | 34.239103 | 33.682167 | 36.061940 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | 8 | 48.703795 | 48.703717 | 49.026360 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | 1 | 185.130761 | 185.130761 | 185.130761 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | 22 | 54.967136 | 54.880343 | 55.046901 | 55.972067 | +1.83% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | 17 | 50.515059 | 50.459912 | 50.932142 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | 16 | 51.750107 | 51.719686 | 52.027841 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b1_m8 | 14 | 51.592999 | 33.731086 | 38.400113 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | 4 | 50.042250 | 49.960392 | 50.329354 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | 3 | 51.607722 | 50.563670 | 54.167837 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | 1 | 262.496916 | 262.496916 | 262.496916 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | 48 | 47.654000 | 47.425103 | 47.666347 | 50.269556 | +5.49% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | 30 | 50.154700 | 34.835994 | 37.649748 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | 21 | 61.811249 | 61.628568 | 62.041601 | 63.540573 | +2.80% | compared |
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
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | 29 | 48.581862 | 48.411553 | 48.662328 | 51.672506 | +6.36% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | 28 | 52.940304 | 48.199387 | 48.363454 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | 16 | 48.606206 | 33.771646 | 34.877383 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | 4 | 47.116268 | 47.165278 | 47.201657 | — | — | unresolved: prediction_deferred_by_population_priority |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 32.555493 | — | — | — | FULL_DECODE_ONLY | 8 / 4 / 32 | auto / full |
| v4flash-a3-tp8-c4:q2_b4_m8 | 32.485961 | 30.611484 | 1.874477 | 5.77% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c4:q2_b1_m2 | 29.500360 | 27.578127 | 1.922233 | 6.52% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c8:q2_b8_m16 | 37.763131 | 36.154075 | 1.609056 | 4.26% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c8:q2_b2_m4 | 31.294368 | 29.525103 | 1.769265 | 5.65% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c8:q2_b1_m2 | 29.354813 | 27.413822 | 1.940991 | 6.61% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c8:q2_b4_m8 | 32.488101 | 30.755604 | 1.732496 | 5.33% | not_established | 8 / 1 / 8 | none / full |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 76.089008 | 75.005135 | 1.083873 | 1.42% | FULL_DECODE_ONLY | 16 / 1 / 1 | none / full |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 119.054350 | 118.048221 | 1.006129 | 0.85% | FULL_DECODE_ONLY | 16 / 1 / 1 | none / full |
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

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| v4flash-a3-tp8-c4:q2_b4_m8 | moe_layer | 19 / 43 | 0.754333 | 0.756827 | 0.850173 | 0.616863 | -18.22% |
| v4flash-a3-tp8-c8:q2_b8_m16 | moe_layer | 35 / 43 | 0.877069 | 0.807240 | 0.979574 | 0.780364 | -11.03% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | moe_layer | 48 / 60 | 1.266992 | 1.278787 | 1.381181 | 1.138409 | -10.15% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | moe_layer | 38 / 60 | 1.983005 | 1.996372 | 2.053669 | 1.714437 | -13.54% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | dense_layer | 0 / 1 | 0.921918 | 0.921918 | 0.921918 | 0.402779 | -56.31% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | moe_layer | 2 / 3 | 0.796936 | 0.814264 | 0.835939 | 0.701633 | -11.96% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | dense_layer | 0 / 1 | 0.902124 | 0.902124 | 0.902124 | 0.449630 | -50.16% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | moe_layer | 1 / 3 | 1.336028 | 1.365465 | 1.453488 | 1.018007 | -23.80% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | dense_layer | 0 / 1 | 0.884665 | 0.884665 | 0.884665 | 0.512630 | -42.05% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | moe_layer | 1 / 3 | 1.963693 | 1.922699 | 2.172615 | 1.605484 | -18.24% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | dense_layer | 0 / 1 | 0.868805 | 0.868805 | 0.868805 | 0.411698 | -52.61% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | moe_layer | 1 / 3 | 0.916748 | 0.941859 | 0.968316 | 0.713337 | -22.19% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | dense_layer | 0 / 1 | 0.960436 | 0.960436 | 0.960436 | 0.639143 | -33.45% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | moe_layer | 2 / 3 | 2.917340 | 2.803217 | 3.209222 | 2.549339 | -12.61% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | moe_layer | 40 / 40 | 1.256829 | 1.189883 | 1.439809 | 1.311857 | +4.38% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | moe_layer | 39 / 40 | 1.379618 | 1.308635 | 1.584825 | 1.399302 | +1.43% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | moe_layer | 39 / 40 | 1.198705 | 1.131824 | 1.351136 | 1.256739 | +4.84% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | moe_layer | 40 / 40 | 1.550226 | 1.465994 | 1.871356 | 1.588514 | +2.47% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | moe_layer | 40 / 40 | 1.221524 | 1.164096 | 1.419689 | 1.291813 | +5.75% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| v4flash-a3-tp8-c4:q2_b4_m8 | mla | 19 / 43 | 0.754333 | 0.756827 | 0.850173 | 0.616863 | -18.22% |
| v4flash-a3-tp8-c8:q2_b8_m16 | mla | 35 / 43 | 0.877069 | 0.807240 | 0.979574 | 0.780364 | -11.03% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gdn | 33 / 45 | 1.235511 | 1.203183 | 1.311698 | 1.104417 | -10.61% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gqa | 15 / 15 | 1.361434 | 1.341377 | 1.455367 | 1.240386 | -8.89% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gdn | 23 / 45 | 1.959216 | 1.940194 | 2.025587 | 1.663609 | -15.09% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gqa | 15 / 15 | 2.054372 | 2.022060 | 2.122093 | 1.866919 | -9.12% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | kda | 2 / 3 | 0.825596 | 0.814264 | 0.921918 | 0.610778 | -26.02% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | mla | 0 / 1 | 0.835939 | 0.835939 | 0.835939 | 0.675346 | -19.21% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | kda | 1 / 3 | 1.152240 | 1.189132 | 1.365465 | 0.827617 | -28.17% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | mla | 0 / 1 | 1.453488 | 1.453488 | 1.453488 | 1.020800 | -29.77% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 1 / 3 | 1.534376 | 1.795764 | 1.922699 | 1.230842 | -19.78% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 0 / 1 | 2.172615 | 2.172615 | 2.172615 | 1.636556 | -24.67% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | kda | 1 / 3 | 0.883578 | 0.868805 | 0.941859 | 0.619697 | -29.86% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | mla | 0 / 1 | 0.968316 | 0.968316 | 0.968316 | 0.692619 | -28.47% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | kda | 2 / 3 | 2.167745 | 2.739582 | 2.803217 | 1.883267 | -13.12% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | mla | 0 / 1 | 3.209222 | 3.209222 | 3.209222 | 2.637361 | -17.82% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | mla | 40 / 40 | 1.256829 | 1.189883 | 1.439809 | 1.311857 | +4.38% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | mla | 39 / 40 | 1.379618 | 1.308635 | 1.584825 | 1.399302 | +1.43% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | mla | 39 / 40 | 1.198705 | 1.131824 | 1.351136 | 1.256739 | +4.84% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | mla | 40 / 40 | 1.550226 | 1.465994 | 1.871356 | 1.588514 | +2.47% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | mla | 40 / 40 | 1.221524 | 1.164096 | 1.419689 | 1.291813 | +5.75% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| v4flash-a3-tp8-c4:q2_b4_m8 | mla | 0.754333 | 0.711895 | 0.042438 |
| v4flash-a3-tp8-c8:q2_b8_m16 | mla | 0.877069 | 0.840792 | 0.036277 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gdn | 1.235511 | 1.218935 | 0.016576 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gqa | 1.361434 | 1.343537 | 0.017897 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gdn | 1.959216 | 1.944578 | 0.014638 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gqa | 2.054372 | 2.036149 | 0.018223 |
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
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | mla | 1.256829 | 1.240894 | 0.015936 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | mla | 1.379618 | 1.363695 | 0.015922 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | mla | 1.198705 | 1.181799 | 0.016906 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | mla | 1.550226 | 1.533748 | 0.016479 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | mla | 1.221524 | 1.204788 | 0.016735 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| v4flash-a3-tp8-c4:q2_b4_m8 | all | 42 | 4368 | 0.754274 | 0.753685 | 0.619949 | -17.74% |
| v4flash-a3-tp8-c4:q2_b4_m8 | mla | 42 | 4368 | 0.754274 | 0.753685 | 0.619949 | -17.74% |
| v4flash-a3-tp8-c8:q2_b8_m16 | all | 42 | 4368 | 0.878732 | 0.883097 | 0.783624 | -11.26% |
| v4flash-a3-tp8-c8:q2_b8_m16 | mla | 42 | 4368 | 0.878732 | 0.883097 | 0.783624 | -11.26% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | all | 59 | 1357 | 1.265579 | 1.271900 | 1.104417 | -13.17% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gdn | 44 | 1012 | 1.232902 | 1.207710 | 1.104417 | -8.55% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gqa | 15 | 345 | 1.361434 | 1.346900 | 1.240386 | -7.91% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | all | 59 | 1062 | 1.981915 | 1.992890 | 1.663609 | -16.52% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gdn | 44 | 792 | 1.957214 | 1.935175 | 1.663609 | -14.03% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gqa | 15 | 270 | 2.054372 | 2.031370 | 1.866919 | -8.10% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | all | 3 | 762 | 0.796936 | 0.776385 | 0.714777 | -7.94% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | kda | 2 | 508 | 0.777435 | 0.725436 | 0.714777 | -1.47% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | mla | 1 | 254 | 0.835939 | 0.799415 | 0.675346 | -15.52% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | all | 3 | 705 | 1.336028 | 1.346153 | 1.016611 | -24.48% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | kda | 2 | 470 | 1.277298 | 1.265664 | 1.016611 | -19.68% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | mla | 1 | 235 | 1.453488 | 1.452451 | 1.020800 | -29.72% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | all | 3 | 660 | 1.963693 | 1.885652 | 1.589948 | -15.68% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 2 | 440 | 1.859231 | 1.840788 | 1.589948 | -13.63% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 1 | 220 | 2.172615 | 2.172336 | 1.636556 | -24.66% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | all | 3 | 738 | 0.916748 | 0.892432 | 0.723697 | -18.91% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | kda | 2 | 492 | 0.890964 | 0.848128 | 0.723697 | -14.67% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | mla | 1 | 246 | 0.968316 | 0.961650 | 0.692619 | -27.98% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | all | 3 | 588 | 2.917340 | 2.774904 | 2.505328 | -9.71% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | kda | 2 | 392 | 2.771399 | 2.756885 | 2.505328 | -9.12% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | mla | 1 | 196 | 3.209222 | 3.208946 | 2.637361 | -17.81% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | all | 39 | 1248 | 1.252138 | 1.188276 | 1.291416 | +8.68% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | mla | 39 | 1248 | 1.252138 | 1.188276 | 1.291416 | +8.68% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | all | 39 | 858 | 1.371480 | 1.307714 | 1.373677 | +5.04% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | mla | 39 | 858 | 1.371480 | 1.307714 | 1.373677 | +5.04% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | all | 39 | 1872 | 1.179467 | 1.129198 | 1.240086 | +9.82% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | mla | 39 | 1872 | 1.179467 | 1.129198 | 1.240086 | +9.82% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | all | 39 | 819 | 1.547673 | 1.462711 | 1.552544 | +6.14% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | mla | 39 | 819 | 1.547673 | 1.462711 | 1.552544 | +6.14% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | all | 39 | 1131 | 1.216364 | 1.158637 | 1.272668 | +9.84% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | mla | 39 | 1131 | 1.216364 | 1.158637 | 1.272668 | +9.84% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| v4flash-a3-tp8-c4:q2_b4_m8 | 104 | 0.756827 | 0.717805 | 0.958641 | 0.532348 | -29.66% |
| v4flash-a3-tp8-c8:q2_b8_m16 | 104 | 0.807240 | 0.766765 | 0.954481 | 0.691109 | -14.39% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 23 | 1.350335 | 1.286500 | 1.407580 | 1.104417 | -18.21% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 18 | 2.047277 | 1.998270 | 2.165240 | 1.663609 | -18.74% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 254 | 0.921918 | 0.911601 | 1.011820 | 0.402779 | -56.31% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 235 | 0.902124 | 0.935902 | 1.032420 | 0.449630 | -50.16% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 220 | 0.884665 | 0.918071 | 1.035580 | 0.512630 | -42.05% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 246 | 0.868805 | 0.892722 | 0.986620 | 0.411698 | -52.61% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 196 | 0.960436 | 0.952631 | 1.021539 | 0.639143 | -33.45% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | 32 | 1.439809 | 1.298684 | 1.648967 | 1.291416 | -10.31% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | 22 | 1.697000 | 1.564018 | 1.749065 | 1.373677 | -19.05% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | 48 | 1.948982 | 1.656527 | 2.027239 | 1.240086 | -36.37% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | 21 | 1.649789 | 1.473370 | 1.851743 | 1.552544 | -5.89% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | 29 | 1.422735 | 1.252335 | 1.455071 | 1.272668 | -10.55% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 1 | 1 | 1 | unknown | 32768 | 1 | 66.586585 | 66.586585 | — | 64.353701 |
| v4flash-a3-tp8-c4:q2_b4_m8 | 2 | 4 | 8 | unknown | 4096 | 4 | 53.936384 | 47.929425 | — | 39.377165 |
| v4flash-a3-tp8-c4:q2_b1_m2 | 2 | 1 | 2 | unknown | 4096 | 4 | 53.936384 | 47.929425 | — | 39.377165 |
| v4flash-a3-tp8-c8:q2_b8_m16 | 2 | 8 | 16 | unknown | 4096 | 8 | 68.120259 | 62.964366 | — | 45.008620 |
| v4flash-a3-tp8-c8:q2_b2_m4 | 2 | 2 | 4 | unknown | 4096 | 8 | 68.120259 | 62.964366 | — | 45.008620 |
| v4flash-a3-tp8-c8:q2_b1_m2 | 2 | 1 | 2 | unknown | 4096 | 8 | 68.120259 | 62.964366 | — | 45.008620 |
| v4flash-a3-tp8-c8:q2_b4_m8 | 2 | 4 | 8 | unknown | 4096 | 8 | 68.120259 | 62.964366 | — | 45.008620 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 4 | 64 | 256 | unknown | 4104 | 48 | 39.264375 | 39.367968 | — | — |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 4 | 160 | 640 | unknown | 4104 | 136 | 59.413752 | 59.082504 | — | — |
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

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
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
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | embedding | 23 | 0.010090 | 0.010000 | 0.010280 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | final_norm | 23 | 0.166548 | 0.166700 | 0.168400 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | lm_head | 23 | 0.272729 | 0.272680 | 0.274060 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | embedding | 18 | 0.011200 | 0.011080 | 0.011840 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | final_norm | 18 | 0.188559 | 0.189710 | 0.192900 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | lm_head | 18 | 0.435398 | 0.436110 | 0.441320 |
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

Summary: {"case_count": 57, "compared_cases": 14, "failed_cases": 1, "measured_cases": 57, "passed_cases": 9, "source_case_count": 15, "unresolved_cases": 42}
