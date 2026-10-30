# Priority Decode body, layer and operator scoreboard

Coverage status: **partial**. Missing predictions and unmatched roles stay visible.

Current selected Body arms: **20/66 passed**. One latest completed receipt per measured source/geometry, selected in input order; each row retains its own runtime and case.

Latest attempted Body arms: **54/66 completed**, **12 failed**, **20 passed**. An earlier completed prediction remains available above when the newest attempt fails; it is not a successful new replay.

Body: **72/308 prediction arms passed**; 66 unique sources, 222 measured geometry populations, 5250 unique complete Forwards (includes deferred populations).

Invalidated prediction rows: **31**. Their measured populations remain; superseded predictions and layer errors are excluded from accuracy statistics.

Current operator strict accuracy (latest input receipt per source/geometry): heavy_relative_15pct: **7/22**; micro_absolute_15us: **588/602**. Conditional references are excluded.

Operator runtime coverage (recorded Sim file-map hash → source/geometry populations): `c27d72c215c2` → 5; `20dbf57be438` → 15; `2db4b7b48698` → 2; `fd8238dbb993` → 22. Scores retain the latest available receipt for each population; this aggregate can contain different runtimes.

Strict event coverage: **1,161,649/6,729,791** events across 44 measured source/geometry populations. A high pass rate within this subset does not establish whole-model accuracy.

Local replay receipts with explicit comparison coverage. Body errors are measured wall-clock differences; operator priorities are nonadditive kernel activity residuals per complete Forward.

## Whole Decode Body — sorted by absolute ms error

| Case / variant | Status | Calls | Real Mean / P50 / P90 ms | Activity ms | Sim ms | Diff ms | Mean / P50 error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / runtime86-glm / `ca6d966131d8` | compared | 44 | 57.817 / 57.597 / 59.092 | 55.203 | 36.987 | -20.830 | -36.027% / -35.783% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / runtime86-glm / `ca6d966131d8` | compared | 44 | 57.639 / 57.562 / 58.995 | 55.027 | 36.987 | -20.652 | -35.830% / -35.743% |
| qwen36-a5-tp2-c96:q4_b96_m384 / body-fixed-grid-qwen / `d0c30b4d63aa` | compared | 24 | 63.853 / 63.562 / 65.419 | 63.565 | 45.410 | -18.443 | -28.884% / -28.558% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / body-fixed-grid-glm / `d0c30b4d63aa` | compared | 37 | 41.069 / 40.940 / 41.282 | 39.691 | 59.251 | 18.182 | 44.271% / 44.725% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / body-fixed-grid-qwen / `d0c30b4d63aa` | compared | 18 | 119.054 / 119.131 / 119.486 | 118.048 | 102.866 | -16.188 | -13.597% / -13.653% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 / kimi-source-a5 / `53d85688e58a` | compared | 41 | 44.666 / 44.645 / 44.662 | 43.971 | 30.332 | -14.334 | -32.091% / -32.059% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / runtime86-glm / `ca6d966131d8` | compared | 49 | 69.556 / 69.489 / 69.830 | 66.970 | 55.529 | -14.027 | -20.167% / -20.089% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / body-fixed-grid-qwen / `d0c30b4d63aa` | compared | 76 | 28.585 / 28.571 / 28.704 | 28.300 | 14.845 | -13.740 | -48.066% / -48.041% |
| qwen36-a5-tp2-c12:q4_b12_m48 / body-fixed-grid-qwen / `d0c30b4d63aa` | compared | 55 | 24.226 / 24.053 / 24.711 | 23.858 | 11.090 | -13.136 | -54.223% / -53.894% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / runtime86-glm / `ca6d966131d8` | compared | 35 | 38.713 / 38.722 / 38.759 | 38.458 | 25.578 | -13.136 | -33.931% / -33.945% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 / kimi-source-a5 / `53d85688e58a` | compared | 47 | 39.247 / 39.245 / 39.263 | 38.567 | 26.442 | -12.805 | -32.627% / -32.623% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / runtime86-glm / `ca6d966131d8` | compared | 32 | 33.616 / 33.626 / 33.710 | 33.358 | 21.502 | -12.115 | -36.038% / -36.056% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 / kimi-source-a5 / `53d85688e58a` | compared | 46 | 40.019 / 40.018 / 40.044 | 39.323 | 27.912 | -12.107 | -30.253% / -30.252% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 / kimi-source-a5 / `53d85688e58a` | compared | 49 | 36.985 / 36.953 / 36.969 | 36.305 | 25.232 | -11.753 | -31.779% / -31.719% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / runtime86-glm / `ca6d966131d8` | compared | 30 | 33.031 / 33.026 / 33.164 | 32.773 | 21.314 | -11.717 | -35.472% / -35.464% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / body-fixed-grid-qwen / `d0c30b4d63aa` | compared | 79 | 21.957 / 22.001 / 22.068 | 21.571 | 10.305 | -11.652 | -53.066% / -53.160% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 / kimi-source-a5 / `53d85688e58a` | compared | 51 | 35.964 / 35.962 / 35.979 | 35.282 | 24.550 | -11.414 | -31.737% / -31.733% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 / kimi-source-a5 / `53d85688e58a` | compared | 52 | 34.816 / 34.794 / 34.813 | 34.115 | 23.934 | -10.882 | -31.256% / -31.211% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 / kimi-source-a5 / `53d85688e58a` | compared | 52 | 34.819 / 34.791 / 34.808 | 34.142 | 23.945 | -10.874 | -31.230% / -31.175% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 / kimi-source-a5 / `53d85688e58a` | compared | 53 | 34.194 / 34.177 / 34.194 | 33.491 | 23.632 | -10.562 | -30.889% / -30.856% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / runtime86-glm / `ca6d966131d8` | compared | 30 | 28.833 / 28.828 / 28.885 | 28.568 | 18.482 | -10.351 | -35.899% / -35.889% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 / kimi-source-a5 / `53d85688e58a` | compared | 54 | 33.876 / 33.858 / 33.873 | 33.190 | 23.694 | -10.182 | -30.058% / -30.021% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 / kimi-source-a5 / `53d85688e58a` | compared | 55 | 33.548 / 33.516 / 33.533 | 32.857 | 23.542 | -10.005 | -29.824% / -29.758% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / glm-source-metadata-corrected / `5dd1cb62f90c` | compared | 31 | 37.669 / 37.665 / 37.761 | 37.413 | 28.492 | -9.177 | -24.362% / -24.354% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / runtime86-glm / `ca6d966131d8` | compared | 50 | 53.893 / 53.871 / 54.021 | 52.393 | 45.037 | -8.857 | -16.433% / -16.398% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / glm-source-metadata-corrected / `5dd1cb62f90c` | compared | 31 | 46.528 / 46.499 / 46.645 | 46.293 | 38.277 | -8.251 | -17.734% / -17.682% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / runtime86-glm / `ca6d966131d8` | compared | 11 | 21.418 / 21.408 / 21.432 | 21.147 | 13.178 | -8.240 | -38.472% / -38.443% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / body-fixed-grid-qwen / `d0c30b4d63aa` | compared | 23 | 76.089 / 76.132 / 76.632 | 75.005 | 68.305 | -7.784 | -10.231% / -10.282% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 / v41-dynamic-rotary / `5dd1cb62f90c` | compared | 73 | 27.286 / 27.266 / 27.290 | 27.188 | 19.989 | -7.297 | -26.741% / -26.687% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 / kimi-source-a5 / `53d85688e58a` | compared | 59 | 30.823 / 30.822 / 30.839 | 30.184 | 23.577 | -7.246 | -23.509% / -23.506% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 / kimi-source-a5 / `53d85688e58a` | compared | 59 | 30.637 / 30.615 / 30.632 | 29.997 | 23.501 | -7.135 | -23.290% / -23.235% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / runtime86-glm / `ca6d966131d8` | compared | 47 | 46.859 / 46.817 / 47.175 | 45.372 | 39.883 | -6.976 | -14.888% / -14.812% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / body-fixed-grid-glm / `d0c30b4d63aa` | compared | 53 | 21.068 / 21.057 / 21.170 | 20.805 | 14.300 | -6.768 | -32.124% / -32.090% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / glm-source-metadata-corrected / `5dd1cb62f90c` | compared | 47 | 97.375 / 97.487 / 97.895 | 95.785 | 104.087 | 6.712 | 6.893% / 6.771% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 / v41-dynamic-rotary / `5dd1cb62f90c` | compared | 75 | 26.328 / 26.306 / 26.336 | 26.229 | 19.675 | -6.653 | -25.269% / -25.206% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / body-fixed-grid-qwen / `d0c30b4d63aa` | compared | 84 | 11.551 / 11.482 / 11.818 | 11.135 | 5.066 | -6.486 | -56.146% / -55.879% |
| v4flash-a3-tp8-c4:q2_b4_m8 / body-fixed-grid-v4_kimi / `d0c30b4d63aa` | compared | 104 | 32.486 / 32.416 / 32.734 | 30.611 | 26.525 | -5.961 | -18.349% / -18.174% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm-source-metadata-corrected / `5dd1cb62f90c` | compared | 65 | 15.683 / 15.670 / 15.738 | 15.421 | 9.956 | -5.727 | -36.518% / -36.466% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 / v41-dynamic-rotary / `5dd1cb62f90c` | compared | 105 | 18.625 / 18.616 / 18.640 | 18.526 | 13.091 | -5.533 | -29.709% / -29.676% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / body-fixed-grid-glm / `d0c30b4d63aa` | compared | 46 | 34.118 / 33.910 / 35.073 | 32.625 | 28.616 | -5.502 | -16.127% / -15.612% |
| a3_glm53_dc4k_b2:q1_b2_m2 / body-fixed-grid-glm / `d0c30b4d63aa` | compared | 70 | 40.970 / 40.935 / 41.046 | — | 35.483 | -5.487 | -13.394% / -13.319% |
| a3_glm53_dc16k_b1:q1_b1_m1 / body-fixed-grid-glm / `d0c30b4d63aa` | compared | 74 | 39.112 / 39.105 / 39.196 | — | 33.637 | -5.475 | -13.999% / -13.983% |
| a3_glm53_dc4k_b1:q1_b1_m1 / body-fixed-grid-glm / `d0c30b4d63aa` | compared | 74 | 38.955 / 38.943 / 39.036 | — | 33.637 | -5.318 | -13.652% / -13.625% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / body-fixed-grid-glm / `d0c30b4d63aa` | compared | 46 | 29.762 / 29.664 / 30.046 | 28.242 | 34.990 | 5.228 | 17.566% / 17.954% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 / v41-dynamic-rotary / `5dd1cb62f90c` | compared | 145 | 13.292 / 12.803 / 12.817 | 13.196 | 8.163 | -5.129 | -38.586% / -36.242% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 / v41-dynamic-rotary / `5dd1cb62f90c` | compared | 129 | 14.929 / 14.914 / 14.929 | 14.832 | 9.806 | -5.124 | -34.319% / -34.254% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 / v41-dynamic-rotary / `5dd1cb62f90c` | compared | 151 | 13.239 / 13.209 / 13.227 | 13.143 | 8.163 | -5.076 | -38.341% / -38.200% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 / v41-dynamic-rotary / `5dd1cb62f90c` | compared | 152 | 13.135 / 13.129 / 13.145 | 13.039 | 8.163 | -4.972 | -37.852% / -37.827% |
| qwen36-a5-tp2-c1:q4_b1_m4 / body-fixed-grid-qwen / `d0c30b4d63aa` | compared | 85 | 12.318 / 12.279 / 12.362 | 11.956 | 7.426 | -4.892 | -39.712% / -39.520% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / body-fixed-grid-glm / `d0c30b4d63aa` | compared | 46 | 39.841 / 39.798 / 40.057 | 38.324 | 34.990 | -4.852 | -12.178% / -12.083% |
| a3_glm53_dc4k_b4:q1_b4_m4 / body-fixed-grid-glm / `d0c30b4d63aa` | compared | 67 | 43.438 / 43.437 / 43.598 | — | 38.631 | -4.807 | -11.066% / -11.065% |
| v4flash-a3-tp8-c8:q2_b8_m16 / body-fixed-grid-v4_kimi / `d0c30b4d63aa` | compared | 104 | 37.763 / 37.868 / 38.082 | 36.154 | 33.556 | -4.207 | -11.142% / -11.388% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / runtime86-v4-kimi / `ca6d966131d8` | compared | 63 | 32.555 / 32.533 / 32.674 | — | 28.761 | -3.795 | -11.657% / -11.596% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 / runtime86-v4-kimi / `ca6d966131d8` | compared | 29 | 48.582 / 48.412 / 48.662 | 47.883 | 51.673 | 3.091 | 6.362% / 6.736% |
| a3_glm53_dc4k_b8:q1_b8_m8 / body-fixed-grid-glm / `d0c30b4d63aa` | compared | 61 | 47.113 / 47.149 / 47.402 | — | 44.125 | -2.989 | -6.344% / -6.414% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 / runtime86-v4-kimi / `ca6d966131d8` | compared | 48 | 47.654 / 47.425 / 47.666 | 46.949 | 50.270 | 2.616 | 5.489% / 5.998% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / body-fixed-grid-glm / `d0c30b4d63aa` | compared | 27 | 57.590 / 57.573 / 57.734 | 57.355 | 55.027 | -2.563 | -4.450% / -4.422% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 / runtime86-v4-kimi / `ca6d966131d8` | compared | 32 | 49.985 / 49.802 / 50.230 | 49.318 | 52.474 | 2.490 | 4.981% / 5.365% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 / runtime86-v4-kimi / `ca6d966131d8` | compared | 21 | 61.811 / 61.629 / 62.042 | 61.115 | 63.541 | 1.729 | 2.798% / 3.102% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 / kimi-source-a3 / `53d85688e58a` | compared | 220 | 6.714 / 6.665 / 6.923 | 6.609 | 5.349 | -1.365 | -20.334% / -19.748% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 / kimi-source-a3 / `53d85688e58a` | compared | 196 | 9.615 / 9.550 / 9.774 | 9.502 | 8.309 | -1.307 | -13.589% / -12.993% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 / kimi-source-a3 / `53d85688e58a` | compared | 235 | 4.807 / 4.779 / 4.992 | 4.709 | 3.522 | -1.285 | -26.729% / -26.299% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / glm-source-metadata-corrected / `5dd1cb62f90c` | compared | 49 | 69.361 / 69.418 / 69.528 | 67.823 | 68.327 | -1.033 | -1.490% / -1.572% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 / runtime86-v4-kimi / `ca6d966131d8` | compared | 22 | 54.967 / 54.880 / 55.047 | 54.296 | 55.972 | 1.005 | 1.828% / 1.989% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 / kimi-source-a3 / `53d85688e58a` | compared | 246 | 3.476 / 3.438 / 3.656 | 3.380 | 2.581 | -0.896 | -25.762% / -24.933% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 / kimi-source-a3 / `53d85688e58a` | compared | 254 | 3.180 / 3.128 / 3.432 | 3.088 | 2.550 | -0.631 | -19.829% / -18.485% |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 / None / `unknown` | prediction_deferred | 11 | 28.126 / 28.052 / 28.206 | 26.591 | — | — | —% / —% |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 / None / `unknown` | prediction_deferred | 10 | 23.447 / 23.179 / 23.585 | 21.956 | — | — | —% / —% |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 / None / `unknown` | prediction_deferred | 6 | 26.154 / 25.840 / 27.873 | 24.653 | — | — | —% / —% |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 / None / `unknown` | prediction_deferred | 16 | 33.619 / 33.419 / 33.980 | 32.091 | — | — | —% / —% |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 / None / `unknown` | prediction_deferred | 13 | 23.486 / 23.363 / 23.611 | 22.012 | — | — | —% / —% |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 / None / `unknown` | prediction_deferred | 9 | 28.227 / 28.041 / 29.858 | 26.716 | — | — | —% / —% |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 / None / `unknown` | prediction_deferred | 7 | 35.014 / 34.765 / 36.431 | 33.490 | — | — | —% / —% |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 / None / `unknown` | prediction_deferred | 6 | 37.826 / 37.534 / 39.879 | 36.322 | — | — | —% / —% |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 / None / `unknown` | prediction_deferred | 5 | 26.385 / 25.916 / 28.429 | 24.885 | — | — | —% / —% |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 / None / `unknown` | prediction_deferred | 4 | 43.282 / 42.788 / 45.252 | 41.753 | — | — | —% / —% |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 / None / `unknown` | prediction_deferred | 4 | 30.244 / 29.665 / 32.051 | 28.749 | — | — | —% / —% |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 / None / `unknown` | prediction_deferred | 3 | 35.070 / 34.379 / 36.534 | 33.686 | — | — | —% / —% |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 / None / `unknown` | prediction_deferred | 2 | 41.544 / 41.544 / 43.477 | 40.004 | — | — | —% / —% |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 / None / `unknown` | prediction_deferred | 1 | 44.811 / 44.811 / 44.811 | 43.263 | — | — | —% / —% |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 / None / `unknown` | prediction_deferred | 1 | 44.980 / 44.980 / 44.980 | 43.459 | — | — | —% / —% |
| glm53flash-a3-tp16-c2:q6_b1_m6 / None / `unknown` | prediction_deferred | 12 | 33.269 / 33.260 / 33.461 | 31.832 | — | — | —% / —% |
| glm53flash-a3-tp16-c4:q6_b1_m6 / None / `unknown` | prediction_deferred | 8 | 33.514 / 33.637 / 34.066 | 32.078 | — | — | —% / —% |
| glm53flash-a3-tp16-c4:q6_b3_m18 / None / `unknown` | prediction_deferred | 4 | 36.347 / 36.075 / 37.439 | 34.842 | — | — | —% / —% |
| glm53flash-a3-tp16-c4:q6_b2_m12 / None / `unknown` | prediction_deferred | 3 | 35.089 / 34.649 / 36.996 | 33.596 | — | — | —% / —% |
| v4flash-a3-tp8-c4:q2_b1_m2 / None / `unknown` | prediction_deferred | 4 | 29.500 / 29.512 / 29.661 | 27.578 | — | — | —% / —% |
| v4flash-a3-tp8-c8:q2_b2_m4 / None / `unknown` | prediction_deferred | 3 | 31.294 / 31.234 / 31.612 | 29.525 | — | — | —% / —% |
| v4flash-a3-tp8-c8:q2_b1_m2 / None / `unknown` | prediction_deferred | 2 | 29.355 / 29.355 / 29.422 | 27.414 | — | — | —% / —% |
| v4flash-a3-tp8-c8:q2_b4_m8 / None / `unknown` | prediction_deferred | 2 | 32.488 / 32.488 / 32.562 | 30.756 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b1_m4 / None / `unknown` | prediction_deferred | 3 | 8.739 / 8.828 / 8.913 | 8.327 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b60_m240 / None / `unknown` | prediction_deferred | 1 | 21.444 / 21.444 / 21.444 | 21.053 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b56_m224 / None / `unknown` | prediction_deferred | 1 | 20.972 / 20.972 / 20.972 | 20.566 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b52_m208 / None / `unknown` | prediction_deferred | 1 | 20.950 / 20.950 / 20.950 | 20.546 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b48_m192 / None / `unknown` | prediction_deferred | 1 | 20.070 / 20.070 / 20.070 | 19.634 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b44_m176 / None / `unknown` | prediction_deferred | 1 | 20.103 / 20.103 / 20.103 | 19.666 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b40_m160 / None / `unknown` | prediction_deferred | 1 | 19.908 / 19.908 / 19.908 | 19.464 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b34_m136 / None / `unknown` | prediction_deferred | 1 | 19.149 / 19.149 / 19.149 | 18.712 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b26_m104 / None / `unknown` | prediction_deferred | 1 | 16.774 / 16.774 / 16.774 | 16.340 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b18_m72 / None / `unknown` | prediction_deferred | 1 | 15.810 / 15.810 / 15.810 | 15.372 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b12_m48 / None / `unknown` | prediction_deferred | 1 | 15.124 / 15.124 / 15.124 | 14.696 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b10_m40 / None / `unknown` | prediction_deferred | 1 | 14.944 / 14.944 / 14.944 | 14.515 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b8_m32 / None / `unknown` | prediction_deferred | 1 | 14.550 / 14.550 / 14.550 | 14.120 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b4_m16 / None / `unknown` | prediction_deferred | 1 | 11.638 / 11.638 / 11.638 | 11.221 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b2_m8 / None / `unknown` | prediction_deferred | 1 | 9.812 / 9.812 / 9.812 | 9.397 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b124_m496 / None / `unknown` | prediction_deferred | 2 | 28.335 / 28.335 / 28.358 | 28.063 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b6_m24 / None / `unknown` | prediction_deferred | 2 | 12.927 / 12.927 / 13.229 | 12.506 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b2_m8 / None / `unknown` | prediction_deferred | 2 | 9.874 / 9.874 / 9.959 | 9.460 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b1_m4 / None / `unknown` | prediction_deferred | 1 | 8.488 / 8.488 / 8.488 | 8.078 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b120_m480 / None / `unknown` | prediction_deferred | 1 | 27.852 / 27.852 / 27.852 | 27.567 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b116_m464 / None / `unknown` | prediction_deferred | 1 | 27.866 / 27.866 / 27.866 | 27.596 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b108_m432 / None / `unknown` | prediction_deferred | 1 | 27.249 / 27.249 / 27.249 | 26.956 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b96_m384 / None / `unknown` | prediction_deferred | 1 | 24.930 / 24.930 / 24.930 | 24.521 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b84_m336 / None / `unknown` | prediction_deferred | 1 | 25.698 / 25.698 / 25.698 | 25.282 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b72_m288 / None / `unknown` | prediction_deferred | 1 | 24.146 / 24.146 / 24.146 | 23.730 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b58_m232 / None / `unknown` | prediction_deferred | 1 | 21.377 / 21.377 / 21.377 | 20.980 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b50_m200 / None / `unknown` | prediction_deferred | 1 | 21.026 / 21.026 / 21.026 | 20.635 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b42_m168 / None / `unknown` | prediction_deferred | 1 | 19.976 / 19.976 / 19.976 | 19.526 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b38_m152 / None / `unknown` | prediction_deferred | 1 | 19.185 / 19.185 / 19.185 | 18.745 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b28_m112 / None / `unknown` | prediction_deferred | 1 | 16.372 / 16.372 / 16.372 | 15.929 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b18_m72 / None / `unknown` | prediction_deferred | 1 | 15.838 / 15.838 / 15.838 | 15.409 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b12_m48 / None / `unknown` | prediction_deferred | 1 | 15.127 / 15.127 / 15.127 | 14.696 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b10_m40 / None / `unknown` | prediction_deferred | 1 | 14.935 / 14.935 / 14.935 | 14.508 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b8_m32 / None / `unknown` | prediction_deferred | 1 | 14.334 / 14.334 / 14.334 | 13.899 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b4_m16 / None / `unknown` | prediction_deferred | 1 | 11.424 / 11.424 / 11.424 | 11.005 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 / None / `unknown` | prediction_deferred | 6 | 8.747 / 8.803 / 8.838 | 8.336 | — | — | —% / —% |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 / None / `unknown` | prediction_deferred | 1 | 9.700 / 9.700 / 9.700 | 9.287 | — | — | —% / —% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 / glm78_tp16_ep16_int8kv_conditional / `unknown` | prediction_deferred | 4 | 57.125 / 57.281 / 57.500 | 54.590 | — | — | —% / —% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 / glm78_tp16_ep16_int8kv_conditional / `unknown` | prediction_deferred | 9 | 57.713 / 57.524 / 58.620 | 55.179 | — | — | —% / —% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 / glm78_tp16_ep16_int8kv_conditional / `unknown` | prediction_deferred | 4 | 56.950 / 56.983 / 57.379 | 54.416 | — | — | —% / —% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 / glm78_tp16_ep16_int8kv_conditional / `unknown` | prediction_deferred | 3 | 56.847 / 56.896 / 57.002 | 54.171 | — | — | —% / —% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 / glm78_tp16_ep16_int8kv_conditional / `unknown` | prediction_deferred | 2 | 68.633 / 68.633 / 68.639 | 65.997 | — | — | —% / —% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 / glm78_tp16_ep16_int8kv_conditional / `unknown` | prediction_deferred | 2 | 58.058 / 58.058 / 58.239 | 55.388 | — | — | —% / —% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 / glm78_tp16_ep16_int8kv_conditional / `unknown` | prediction_deferred | 1 | 57.388 / 57.388 / 57.388 | 54.748 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 / None / `unknown` | superseded-input-binding | 3 | 3.845 / 3.281 / 5.439 | 3.742 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 / None / `unknown` | superseded-input-binding | 3 | 3.240 / 3.278 / 3.411 | 3.159 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 / None / `unknown` | superseded-input-binding | 3 | 3.364 / 3.380 / 3.467 | 3.283 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 / None / `unknown` | superseded-input-binding | 1 | 3.812 / 3.812 / 3.812 | 3.719 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 / None / `unknown` | superseded-input-binding | 1 | 2.978 / 2.978 / 2.978 | 2.887 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 / None / `unknown` | superseded-input-binding | 1 | 4.690 / 4.690 / 4.690 | 4.605 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 / None / `unknown` | superseded-input-binding | 4 | 3.376 / 3.346 / 3.556 | 3.282 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 / None / `unknown` | superseded-input-binding | 3 | 3.191 / 3.245 / 3.294 | 3.094 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 / None / `unknown` | superseded-input-binding | 3 | 3.178 / 3.254 / 3.501 | 3.097 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 / None / `unknown` | superseded-input-binding | 2 | 8.473 / 8.473 / 8.560 | 8.364 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 / None / `unknown` | superseded-input-binding | 2 | 5.631 / 5.631 / 5.720 | 5.532 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 / None / `unknown` | superseded-input-binding | 2 | 4.723 / 4.723 / 4.739 | 4.622 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 / None / `unknown` | superseded-input-binding | 1 | 3.160 / 3.160 / 3.160 | 3.070 | — | — | —% / —% |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 / None / `unknown` | superseded-input-binding | 1 | 3.537 / 3.537 / 3.537 | 3.456 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 / None / `unknown` | prediction_deferred | 4 | 18.010 / 17.896 / 18.413 | 17.748 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 / None / `unknown` | prediction_deferred | 3 | 15.697 / 15.705 / 15.723 | 15.435 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 / None / `unknown` | prediction_deferred | 2 | 24.984 / 24.984 / 25.001 | 24.715 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 / None / `unknown` | prediction_deferred | 1 | 33.211 / 33.211 / 33.211 | 32.950 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 / None / `unknown` | prediction_deferred | 1 | 32.232 / 32.232 / 32.232 | 31.961 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 / None / `unknown` | prediction_deferred | 1 | 31.923 / 31.923 / 31.923 | 31.650 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 / None / `unknown` | prediction_deferred | 1 | 21.417 / 21.417 / 21.417 | 21.145 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 / None / `unknown` | prediction_deferred | 2 | 29.255 / 29.255 / 29.307 | 28.989 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 / None / `unknown` | prediction_deferred | 2 | 21.441 / 21.441 / 21.441 | 21.170 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 / None / `unknown` | prediction_deferred | 2 | 15.624 / 15.624 / 15.655 | 15.364 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 / None / `unknown` | prediction_deferred | 1 | 33.358 / 33.358 / 33.358 | 33.101 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 / None / `unknown` | prediction_deferred | 1 | 32.536 / 32.536 / 32.536 | 32.271 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 / None / `unknown` | prediction_deferred | 1 | 24.990 / 24.990 / 24.990 | 24.722 | — | — | —% / —% |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 / None / `unknown` | prediction_deferred | 1 | 17.717 / 17.717 / 17.717 | 17.455 | — | — | —% / —% |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 / None / `unknown` | prediction_deferred | 2 | 37.705 / 37.705 / 37.844 | 37.429 | — | — | —% / —% |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 / None / `unknown` | prediction_deferred | 2 | 37.468 / 37.468 / 38.255 | 37.200 | — | — | —% / —% |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 / None / `unknown` | prediction_deferred | 1 | 38.397 / 38.397 / 38.397 | 38.138 | — | — | —% / —% |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 / None / `unknown` | prediction_deferred | 1 | 38.002 / 38.002 / 38.002 | 37.737 | — | — | —% / —% |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 / None / `unknown` | prediction_deferred | 1 | 38.635 / 38.635 / 38.635 | 38.374 | — | — | —% / —% |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 / None / `unknown` | prediction_deferred | 9 | 15.590 / 15.583 / 15.642 | 15.328 | — | — | —% / —% |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 / None / `unknown` | prediction_deferred | 3 | 17.682 / 17.672 / 17.709 | 17.420 | — | — | —% / —% |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 / None / `unknown` | prediction_deferred | 3 | 25.113 / 25.067 / 25.283 | 24.845 | — | — | —% / —% |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 / None / `unknown` | prediction_deferred | 2 | 21.340 / 21.340 / 21.389 | 21.068 | — | — | —% / —% |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 / None / `unknown` | prediction_deferred | 2 | 18.882 / 18.882 / 19.872 | 18.618 | — | — | —% / —% |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 / None / `unknown` | prediction_deferred | 1 | 16.092 / 16.092 / 16.092 | 15.829 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b1_m6 / None / `unknown` | prediction_deferred | 4 | 33.477 / 33.401 / 33.975 | 32.045 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b12_m72 / None / `unknown` | prediction_deferred | 4 | 52.671 / 52.569 / 53.565 | 51.119 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b2_m12 / None / `unknown` | prediction_deferred | 3 | 33.946 / 33.337 / 35.257 | 32.453 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b8_m48 / None / `unknown` | prediction_deferred | 2 | 47.322 / 47.322 / 48.210 | 45.832 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b4_m24 / None / `unknown` | prediction_deferred | 1 | 39.385 / 39.385 / 39.385 | 37.860 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b6_m36 / None / `unknown` | prediction_deferred | 1 | 45.421 / 45.421 / 45.421 | 43.893 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b12_m72 / None / `unknown` | prediction_deferred | 5 | 52.894 / 53.227 / 53.859 | 51.338 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b1_m6 / None / `unknown` | prediction_deferred | 3 | 33.667 / 33.176 / 34.874 | 32.243 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b24_m144 / None / `unknown` | prediction_deferred | 3 | 63.044 / 62.507 / 64.216 | 61.537 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b16_m96 / None / `unknown` | prediction_deferred | 2 | 54.274 / 54.274 / 54.610 | 52.776 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b8_m48 / None / `unknown` | prediction_deferred | 1 | 46.500 / 46.500 / 46.500 | 45.015 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b6_m36 / None / `unknown` | prediction_deferred | 1 | 46.451 / 46.451 / 46.451 | 44.843 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b2_m12 / None / `unknown` | prediction_deferred | 1 | 33.133 / 33.133 / 33.133 | 31.645 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b1_m6 / None / `unknown` | prediction_deferred | 6 | 33.162 / 33.128 / 33.586 | 31.725 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b48_m288 / None / `unknown` | prediction_deferred | 3 | 80.931 / 80.984 / 82.029 | 79.325 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b6_m36 / None / `unknown` | prediction_deferred | 3 | 45.865 / 46.345 / 46.510 | 44.283 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b32_m192 / None / `unknown` | prediction_deferred | 2 | 68.165 / 68.165 / 68.192 | 66.526 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b24_m144 / None / `unknown` | prediction_deferred | 2 | 61.996 / 61.996 / 62.736 | 60.454 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b16_m96 / None / `unknown` | prediction_deferred | 2 | 53.912 / 53.912 / 54.034 | 52.371 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b2_m12 / None / `unknown` | prediction_deferred | 2 | 33.440 / 33.440 / 34.073 | 31.949 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b4_m24 / None / `unknown` | prediction_deferred | 1 | 37.485 / 37.485 / 37.485 | 35.971 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b8_m48 / None / `unknown` | prediction_deferred | 1 | 46.552 / 46.552 / 46.552 | 45.063 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b1_m6 / None / `unknown` | prediction_deferred | 6 | 33.545 / 33.104 / 34.940 | 32.110 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b4_m24 / None / `unknown` | prediction_deferred | 4 | 37.953 / 37.468 / 39.615 | 36.433 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b6_m36 / None / `unknown` | prediction_deferred | 3 | 45.218 / 44.930 / 46.274 | 43.682 | — | — | —% / —% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b2_m12 / None / `unknown` | prediction_deferred | 2 | 34.031 / 34.031 / 34.634 | 32.539 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 / None / `unknown` | prediction_deferred | 20 | 50.228 / 50.207 / 50.438 | 49.553 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 / None / `unknown` | prediction_deferred | 15 | 34.239 / 33.682 / 36.062 | 33.579 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 / None / `unknown` | prediction_deferred | 8 | 48.704 / 48.704 / 49.026 | 48.004 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 / None / `unknown` | prediction_deferred | 1 | 185.131 / 185.131 / 185.131 | 181.542 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 / None / `unknown` | prediction_deferred | 17 | 50.515 / 50.460 / 50.932 | 49.845 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 / None / `unknown` | prediction_deferred | 16 | 51.750 / 51.720 / 52.028 | 51.078 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b1_m8 / None / `unknown` | prediction_deferred | 14 | 51.593 / 33.731 / 38.400 | 50.679 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 / None / `unknown` | prediction_deferred | 4 | 50.042 / 49.960 / 50.329 | 49.369 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 / None / `unknown` | prediction_deferred | 3 | 51.608 / 50.564 / 54.168 | 50.921 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 / None / `unknown` | prediction_deferred | 1 | 262.497 / 262.497 / 262.497 | 259.636 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 / None / `unknown` | prediction_deferred | 30 | 50.155 / 34.836 / 37.650 | 48.253 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 / None / `unknown` | prediction_deferred | 13 | 72.359 / 33.725 / 173.015 | 70.912 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 / None / `unknown` | prediction_deferred | 11 | 59.511 / 59.511 / 59.770 | 58.818 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 / None / `unknown` | prediction_deferred | 8 | 55.145 / 55.134 / 55.338 | 54.463 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 / None / `unknown` | prediction_deferred | 7 | 63.461 / 58.535 / 92.715 | 62.708 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 / None / `unknown` | prediction_deferred | 5 | 54.822 / 54.716 / 55.164 | 54.150 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 / None / `unknown` | prediction_deferred | 4 | 58.828 / 58.790 / 59.144 | 58.125 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 / None / `unknown` | prediction_deferred | 2 | 56.627 / 56.627 / 56.743 | 55.954 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b3_m24 / None / `unknown` | prediction_deferred | 2 | 49.514 / 49.514 / 50.934 | 48.795 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 / None / `unknown` | prediction_deferred | 2 | 57.975 / 57.975 / 58.052 | 57.304 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 / None / `unknown` | prediction_deferred | 1 | 50.256 / 50.256 / 50.256 | 49.584 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 / None / `unknown` | prediction_deferred | 28 | 52.940 / 48.199 / 48.363 | 52.211 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 / None / `unknown` | prediction_deferred | 16 | 48.606 / 33.772 / 34.877 | 47.850 | — | — | —% / —% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 / None / `unknown` | prediction_deferred | 4 | 47.116 / 47.165 / 47.202 | 46.410 | — | — | —% / —% |

### Failed local replay attempts

Failed attempts remain visible. Input failures do not create measured populations; prediction failures retain completed observations.

| Case | Failure | Later source comparison present |
|---|---|---|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | declared_forward_extraction_missing | True |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | declared_forward_extraction_missing | True |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | declared_forward_extraction_missing | True |
| glm53flash-a5-tp8-c96:q4_b96_m384 | body_prediction_timeout | True |
| qwen36-a5-tp2-c96:q4_b96_m384 | body_prediction_timeout | True |
| glm53flash-a5-tp8-c96:q4_b96_m384 | body_prediction_timeout | True |
| qwen36-a5-tp2-c96:q4_b96_m384 | body_prediction_timeout | True |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | body_prediction_worker_failed | True |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | body_prediction_worker_failed | True |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | body_prediction_worker_failed | True |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | body_prediction_worker_failed | True |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | body_prediction_worker_failed | True |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | body_prediction_worker_failed | True |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | body_prediction_worker_failed | True |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | body_prediction_worker_failed | True |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | body_prediction_worker_failed | True |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | body_prediction_worker_failed | True |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | body_prediction_worker_failed | True |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | body_prediction_worker_failed | True |

## Layer 0 and steady layer groups

The steady P50 column is median of per-layer call P50, unless a separately linked receipt supplies exact pooled statistics.

| Case | Group | Layers | Real Mean ms | Median layer-call P50 ms | Sim Mean ms | Mean / P50 error |
|---|---|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / runtime86-glm | Layer 0 / mla / dense_layer | 1 | 0.6279 | 0.5491 | 0.3579 | -43.007% / -34.821% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / runtime86-glm | Steady / mla / dense_layer | 2 | 0.5676 | 0.5344 | 0.3579 | -36.948% / -33.033% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / runtime86-glm | Steady / mla / moe_layer | 75 | 0.7473 | 0.7151 | 0.4788 | -35.926% / -33.037% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / runtime86-glm | Layer 0 / mla / dense_layer | 1 | 0.5858 | 0.5425 | 0.3579 | -38.903% / -34.034% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / runtime86-glm | Steady / mla / dense_layer | 2 | 0.5667 | 0.5291 | 0.3579 | -36.851% / -32.360% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / runtime86-glm | Steady / mla / moe_layer | 75 | 0.7455 | 0.7151 | 0.4788 | -35.772% / -33.033% |
| qwen36-a5-tp2-c96:q4_b96_m384 / body-fixed-grid-qwen | Layer 0 / gdn / dense_layer | 1 | 1.3691 | 1.0682 | 0.7603 | -44.469% / -28.823% |
| qwen36-a5-tp2-c96:q4_b96_m384 / body-fixed-grid-qwen | Steady / gdn / dense_layer | 47 | 1.0584 | 1.0584 | 0.7603 | -28.169% / -28.168% |
| qwen36-a5-tp2-c96:q4_b96_m384 / body-fixed-grid-qwen | Steady / gqa / dense_layer | 16 | 0.7931 | 0.7928 | 0.5573 | -29.737% / -29.702% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / body-fixed-grid-glm | Layer 0 / kda / dense_layer | 1 | 1.0092 | 0.8498 | 0.7070 | -29.951% / -16.806% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / body-fixed-grid-glm | Steady / kda / dense_layer | 2 | 0.4246 | 0.4245 | 0.7070 | 66.495% / 66.545% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / body-fixed-grid-glm | Steady / mla / moe_layer | 11 | 1.3710 | 1.3767 | 1.5103 | 10.161% / 9.707% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / body-fixed-grid-glm | Steady / kda / moe_layer | 31 | 0.7767 | 0.7741 | 1.3070 | 68.271% / 68.839% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / body-fixed-grid-qwen | Layer 0 / gdn / moe_layer | 1 | 2.0473 | 1.9983 | 1.6636 | -18.740% / -16.748% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / body-fixed-grid-qwen | Steady / gdn / moe_layer | 44 | 1.9572 | 1.9352 | 1.6636 | -15.001% / -14.033% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / body-fixed-grid-qwen | Steady / gqa / moe_layer | 15 | 2.0544 | 2.0314 | 1.8669 | -9.125% / -8.096% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 / kimi-source-a5 | Layer 0 / kda / dense_layer | 1 | 0.3620 | 0.3384 | 0.2521 | -30.373% / -25.510% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 / kimi-source-a5 | Steady / kda / moe_layer | 68 | 0.4145 | 0.4142 | 0.2992 | -27.813% / -27.764% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 / kimi-source-a5 | Steady / mla / moe_layer | 24 | 0.6715 | 0.6644 | 0.4050 | -39.684% / -39.035% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / runtime86-glm | Layer 0 / mla / dense_layer | 1 | 0.6710 | 0.6210 | 0.4630 | -31.000% / -25.451% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / runtime86-glm | Steady / mla / dense_layer | 2 | 0.6345 | 0.6104 | 0.4630 | -27.037% / -24.156% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / runtime86-glm | Steady / mla / moe_layer | 75 | 0.9015 | 0.8670 | 0.7219 | -19.926% / -16.736% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / body-fixed-grid-qwen | Layer 0 / gdn / moe_layer | 1 | 0.7544 | 0.7238 | 0.3848 | -48.997% / -46.837% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / body-fixed-grid-qwen | Steady / gdn / moe_layer | 29 | 0.7199 | 0.7199 | 0.3848 | -46.548% / -46.552% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / body-fixed-grid-qwen | Steady / gqa / moe_layer | 10 | 0.6953 | 0.6941 | 0.3302 | -52.518% / -52.435% |
| qwen36-a5-tp2-c12:q4_b12_m48 / body-fixed-grid-qwen | Layer 0 / gdn / dense_layer | 1 | 0.6168 | 0.3931 | 0.1839 | -70.181% / -53.210% |
| qwen36-a5-tp2-c12:q4_b12_m48 / body-fixed-grid-qwen | Steady / gdn / dense_layer | 47 | 0.4044 | 0.4033 | 0.1839 | -54.519% / -54.394% |
| qwen36-a5-tp2-c12:q4_b12_m48 / body-fixed-grid-qwen | Steady / gqa / dense_layer | 16 | 0.2846 | 0.2843 | 0.1413 | -50.342% / -50.286% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / runtime86-glm | Layer 0 / kda / dense_layer | 1 | 0.4891 | 0.4818 | 0.2159 | -55.847% / -55.180% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / runtime86-glm | Steady / kda / dense_layer | 2 | 0.3535 | 0.3535 | 0.2159 | -38.919% / -38.907% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / runtime86-glm | Steady / mla / moe_layer | 11 | 1.2946 | 1.2899 | 0.6931 | -46.463% / -46.270% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / runtime86-glm | Steady / kda / moe_layer | 31 | 0.7508 | 0.7507 | 0.5583 | -25.648% / -25.637% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 / kimi-source-a5 | Layer 0 / kda / dense_layer | 1 | 0.3047 | 0.3023 | 0.2248 | -26.239% / -25.647% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 / kimi-source-a5 | Steady / kda / moe_layer | 68 | 0.3858 | 0.3856 | 0.2738 | -29.038% / -28.996% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 / kimi-source-a5 | Steady / mla / moe_layer | 24 | 0.5293 | 0.5223 | 0.3161 | -40.281% / -39.482% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / runtime86-glm | Layer 0 / kda / dense_layer | 1 | 0.3876 | 0.4019 | 0.1697 | -56.227% / -57.785% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / runtime86-glm | Steady / kda / dense_layer | 2 | 0.2980 | 0.2974 | 0.1697 | -43.067% / -42.944% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / runtime86-glm | Steady / mla / moe_layer | 11 | 1.0591 | 1.0543 | 0.5573 | -47.377% / -47.139% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / runtime86-glm | Steady / kda / moe_layer | 31 | 0.6768 | 0.6768 | 0.4794 | -29.166% / -29.165% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 / kimi-source-a5 | Layer 0 / kda / dense_layer | 1 | 0.3379 | 0.3376 | 0.2521 | -25.409% / -25.332% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 / kimi-source-a5 | Steady / kda / moe_layer | 68 | 0.4141 | 0.4140 | 0.2992 | -27.753% / -27.736% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 / kimi-source-a5 | Steady / mla / moe_layer | 24 | 0.4799 | 0.4722 | 0.3042 | -36.612% / -35.586% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 / kimi-source-a5 | Layer 0 / kda / dense_layer | 1 | 0.3353 | 0.3023 | 0.2248 | -32.975% / -25.647% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 / kimi-source-a5 | Steady / kda / moe_layer | 68 | 0.3857 | 0.3855 | 0.2738 | -29.023% / -28.984% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 / kimi-source-a5 | Steady / mla / moe_layer | 24 | 0.4340 | 0.4269 | 0.2657 | -38.786% / -37.760% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / runtime86-glm | Layer 0 / kda / dense_layer | 1 | 0.3980 | 0.3937 | 0.1697 | -57.364% / -56.901% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / runtime86-glm | Steady / kda / dense_layer | 2 | 0.2982 | 0.2982 | 0.1697 | -43.106% / -43.099% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / runtime86-glm | Steady / mla / moe_layer | 11 | 1.0018 | 0.9978 | 0.5403 | -46.068% / -45.852% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / runtime86-glm | Steady / kda / moe_layer | 31 | 0.6779 | 0.6772 | 0.4794 | -29.282% / -29.204% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / body-fixed-grid-qwen | Layer 0 / gdn / moe_layer | 1 | 0.7737 | 0.8216 | 0.2668 | -65.511% / -67.524% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / body-fixed-grid-qwen | Steady / gdn / moe_layer | 29 | 0.5470 | 0.5467 | 0.2668 | -51.218% / -51.194% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / body-fixed-grid-qwen | Steady / gqa / moe_layer | 10 | 0.5320 | 0.5323 | 0.2300 | -56.761% / -56.785% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 / kimi-source-a5 | Layer 0 / kda / dense_layer | 1 | 0.2840 | 0.2810 | 0.2121 | -25.335% / -24.543% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 / kimi-source-a5 | Steady / kda / moe_layer | 68 | 0.3653 | 0.3650 | 0.2619 | -28.298% / -28.241% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 / kimi-source-a5 | Steady / mla / moe_layer | 24 | 0.4517 | 0.4454 | 0.2715 | -39.887% / -39.047% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 / kimi-source-a5 | Layer 0 / kda / dense_layer | 1 | 0.2974 | 0.2770 | 0.2097 | -29.492% / -24.297% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 / kimi-source-a5 | Steady / kda / moe_layer | 68 | 0.3596 | 0.3592 | 0.2595 | -27.832% / -27.755% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 / kimi-source-a5 | Steady / mla / moe_layer | 24 | 0.4192 | 0.4125 | 0.2526 | -39.751% / -38.762% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 / kimi-source-a5 | Layer 0 / kda / dense_layer | 1 | 0.3102 | 0.2816 | 0.2121 | -31.628% / -24.683% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 / kimi-source-a5 | Steady / kda / moe_layer | 68 | 0.3652 | 0.3648 | 0.2619 | -28.295% / -28.206% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 / kimi-source-a5 | Steady / mla / moe_layer | 24 | 0.4029 | 0.3960 | 0.2463 | -38.870% / -37.802% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 / kimi-source-a5 | Layer 0 / kda / dense_layer | 1 | 0.2930 | 0.2771 | 0.2097 | -28.435% / -24.326% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 / kimi-source-a5 | Steady / kda / moe_layer | 68 | 0.3596 | 0.3596 | 0.2595 | -27.834% / -27.818% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 / kimi-source-a5 | Steady / mla / moe_layer | 24 | 0.3935 | 0.3863 | 0.2400 | -39.006% / -37.880% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / runtime86-glm | Layer 0 / kda / dense_layer | 1 | 0.4973 | 0.4989 | 0.1496 | -69.915% / -70.010% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / runtime86-glm | Steady / kda / dense_layer | 2 | 0.2536 | 0.2520 | 0.1496 | -41.010% / -40.636% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / runtime86-glm | Steady / mla / moe_layer | 11 | 0.8678 | 0.8641 | 0.4599 | -47.005% / -46.776% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / runtime86-glm | Steady / kda / moe_layer | 31 | 0.5897 | 0.5893 | 0.4185 | -29.030% / -28.980% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 / kimi-source-a5 | Layer 0 / kda / dense_layer | 1 | 0.2876 | 0.2698 | 0.2095 | -27.145% / -22.348% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 / kimi-source-a5 | Steady / kda / moe_layer | 68 | 0.3531 | 0.3529 | 0.2593 | -26.557% / -26.514% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 / kimi-source-a5 | Steady / mla / moe_layer | 24 | 0.3989 | 0.3918 | 0.2431 | -39.051% / -37.939% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 / kimi-source-a5 | Layer 0 / kda / dense_layer | 1 | 0.3027 | 0.2698 | 0.2095 | -30.779% / -22.362% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 / kimi-source-a5 | Steady / kda / moe_layer | 68 | 0.3533 | 0.3531 | 0.2593 | -26.603% / -26.565% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 / kimi-source-a5 | Steady / mla / moe_layer | 24 | 0.3840 | 0.3767 | 0.2368 | -38.324% / -37.135% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / glm-source-metadata-corrected | Layer 0 / kda / dense_layer | 1 | 0.4873 | 0.4626 | 0.2159 | -55.687% / -53.323% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / glm-source-metadata-corrected | Steady / kda / dense_layer | 2 | 0.3528 | 0.3529 | 0.2159 | -38.795% / -38.804% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / glm-source-metadata-corrected | Steady / mla / moe_layer | 11 | 1.1973 | 1.1925 | 0.9048 | -24.431% / -24.126% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / glm-source-metadata-corrected | Steady / kda / moe_layer | 31 | 0.7518 | 0.7522 | 0.5772 | -23.227% / -23.271% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / runtime86-glm | Layer 0 / kda / dense_layer | 1 | 0.6895 | 0.6689 | 0.4851 | -29.643% / -27.470% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / runtime86-glm | Steady / kda / dense_layer | 2 | 0.6561 | 0.6366 | 0.4851 | -26.056% / -23.788% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / runtime86-glm | Steady / mla / moe_layer | 11 | 1.6861 | 1.6864 | 1.1823 | -29.880% / -29.893% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / runtime86-glm | Steady / kda / moe_layer | 31 | 1.0740 | 1.0740 | 0.9863 | -8.160% / -8.162% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / glm-source-metadata-corrected | Layer 0 / kda / dense_layer | 1 | 0.5510 | 0.5299 | 0.3126 | -43.261% / -41.001% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / glm-source-metadata-corrected | Steady / kda / dense_layer | 2 | 0.4693 | 0.4691 | 0.3126 | -33.383% / -33.352% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / glm-source-metadata-corrected | Steady / mla / moe_layer | 11 | 1.5929 | 1.5839 | 1.3357 | -16.145% / -15.668% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / glm-source-metadata-corrected | Steady / kda / moe_layer | 31 | 0.8876 | 0.8877 | 0.7305 | -17.698% / -17.710% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / runtime86-glm | Layer 0 / kda / dense_layer | 1 | 0.3235 | 0.2805 | 0.1399 | -56.742% / -50.115% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / runtime86-glm | Steady / kda / dense_layer | 2 | 0.2349 | 0.2350 | 0.1399 | -40.442% / -40.454% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / runtime86-glm | Steady / mla / moe_layer | 11 | 0.6731 | 0.6714 | 0.3303 | -50.929% / -50.798% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / runtime86-glm | Steady / kda / moe_layer | 31 | 0.4264 | 0.4251 | 0.2944 | -30.974% / -30.757% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / body-fixed-grid-qwen | Layer 0 / gdn / moe_layer | 1 | 1.3503 | 1.2865 | 1.1044 | -18.212% / -14.153% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / body-fixed-grid-qwen | Steady / gdn / moe_layer | 44 | 1.2329 | 1.2077 | 1.1044 | -10.421% / -8.553% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / body-fixed-grid-qwen | Steady / gqa / moe_layer | 15 | 1.3614 | 1.3469 | 1.2404 | -8.891% / -7.908% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 / v41-dynamic-rotary | Layer 0 / mla / moe_layer | 1 | 0.8025 | 0.7842 | 0.4758 | -40.710% / -39.326% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 / v41-dynamic-rotary | Steady / mla / moe_layer | 39 | 0.6790 | 0.6545 | 0.5003 | -26.315% / -23.556% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 / kimi-source-a5 | Layer 0 / kda / dense_layer | 1 | 0.2595 | 0.2581 | 0.2095 | -19.282% / -18.859% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 / kimi-source-a5 | Steady / kda / moe_layer | 68 | 0.3208 | 0.3208 | 0.2593 | -19.173% / -19.176% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 / kimi-source-a5 | Steady / mla / moe_layer | 24 | 0.3644 | 0.3577 | 0.2384 | -34.585% / -33.359% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 / kimi-source-a5 | Layer 0 / kda / dense_layer | 1 | 0.2772 | 0.2578 | 0.2095 | -24.443% / -18.756% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 / kimi-source-a5 | Steady / kda / moe_layer | 68 | 0.3209 | 0.3210 | 0.2593 | -19.199% / -19.227% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 / kimi-source-a5 | Steady / mla / moe_layer | 24 | 0.3556 | 0.3487 | 0.2353 | -33.852% / -32.535% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / runtime86-glm | Layer 0 / kda / dense_layer | 1 | 0.6412 | 0.5810 | 0.4012 | -37.426% / -30.945% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / runtime86-glm | Steady / kda / dense_layer | 2 | 0.6152 | 0.5329 | 0.4012 | -34.785% / -24.712% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / runtime86-glm | Steady / mla / moe_layer | 11 | 1.4099 | 1.4072 | 1.0155 | -27.971% / -27.835% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / runtime86-glm | Steady / kda / moe_layer | 31 | 0.9493 | 0.9478 | 0.8874 | -6.521% / -6.375% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / body-fixed-grid-glm | Layer 0 / kda / dense_layer | 1 | 0.4650 | 0.4745 | 0.1492 | -67.916% / -68.556% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / body-fixed-grid-glm | Steady / kda / dense_layer | 2 | 0.2383 | 0.2328 | 0.1492 | -37.395% / -35.916% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / body-fixed-grid-glm | Steady / mla / moe_layer | 11 | 0.6392 | 0.6337 | 0.3532 | -44.738% / -44.259% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / body-fixed-grid-glm | Steady / kda / moe_layer | 31 | 0.4224 | 0.4216 | 0.3215 | -23.883% / -23.747% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / glm-source-metadata-corrected | Layer 0 / kda / dense_layer | 1 | 1.3232 | 1.3221 | 1.0894 | -17.672% / -17.602% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / glm-source-metadata-corrected | Steady / kda / dense_layer | 2 | 1.2997 | 1.3012 | 1.0894 | -16.179% / -16.279% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / glm-source-metadata-corrected | Steady / mla / moe_layer | 11 | 3.5285 | 3.5319 | 4.4828 | 27.045% / 26.923% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / glm-source-metadata-corrected | Steady / kda / moe_layer | 31 | 1.7609 | 1.7632 | 1.6616 | -5.640% / -5.764% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 / v41-dynamic-rotary | Layer 0 / mla / moe_layer | 1 | 0.7498 | 0.7292 | 0.4687 | -37.486% / -35.715% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 / v41-dynamic-rotary | Steady / mla / moe_layer | 39 | 0.6558 | 0.6334 | 0.4925 | -24.904% / -22.245% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / body-fixed-grid-qwen | Layer 0 / gdn / moe_layer | 1 | 0.3868 | 0.2973 | 0.1246 | -67.780% / -58.089% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / body-fixed-grid-qwen | Steady / gdn / moe_layer | 29 | 0.2819 | 0.2827 | 0.1246 | -55.795% / -55.923% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / body-fixed-grid-qwen | Steady / gqa / moe_layer | 10 | 0.2989 | 0.2992 | 0.1327 | -55.586% / -55.631% |
| v4flash-a3-tp8-c4:q2_b4_m8 / body-fixed-grid-v4_kimi | Layer 0 / mla / moe_layer | 1 | 0.7568 | 0.7178 | 0.5323 | -29.661% / -25.837% |
| v4flash-a3-tp8-c4:q2_b4_m8 / body-fixed-grid-v4_kimi | Steady / mla / moe_layer | 42 | 0.7543 | 0.7537 | 0.6189 | -17.951% / -17.887% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm-source-metadata-corrected | Layer 0 / kda / dense_layer | 1 | 0.4222 | 0.4383 | 0.1286 | -69.546% / -70.661% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm-source-metadata-corrected | Steady / kda / dense_layer | 2 | 0.2487 | 0.2314 | 0.1286 | -48.294% / -44.430% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm-source-metadata-corrected | Steady / mla / moe_layer | 11 | 0.4952 | 0.4903 | 0.2686 | -45.760% / -45.219% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm-source-metadata-corrected | Steady / kda / moe_layer | 31 | 0.3005 | 0.2985 | 0.2134 | -28.982% / -28.511% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 / v41-dynamic-rotary | Layer 0 / mla / moe_layer | 1 | 0.5279 | 0.5209 | 0.3045 | -42.321% / -41.540% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 / v41-dynamic-rotary | Steady / mla / moe_layer | 39 | 0.4640 | 0.4441 | 0.3279 | -29.332% / -26.166% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / body-fixed-grid-glm | Layer 0 / kda / dense_layer | 1 | 0.5732 | 0.5010 | 0.3604 | -37.133% / -28.072% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / body-fixed-grid-glm | Steady / kda / dense_layer | 2 | 0.5965 | 0.5414 | 0.3604 | -39.585% / -33.435% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / body-fixed-grid-glm | Steady / mla / moe_layer | 11 | 0.9546 | 0.9395 | 0.7133 | -25.281% / -24.078% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / body-fixed-grid-glm | Steady / kda / moe_layer | 31 | 0.7032 | 0.6643 | 0.6351 | -9.683% / -4.392% |
| a3_glm53_dc4k_b2:q1_b2_m2 / body-fixed-grid-glm | Layer 0 / mla / dense_layer | 1 | 0.4105 | 0.3960 | 0.3553 | -13.446% / -10.263% |
| a3_glm53_dc4k_b2:q1_b2_m2 / body-fixed-grid-glm | Steady / mla / dense_layer | 2 | 0.3997 | 0.3865 | 0.3553 | -11.099% / -8.071% |
| a3_glm53_dc4k_b2:q1_b2_m2 / body-fixed-grid-glm | Steady / mla / moe_layer | 75 | 0.5293 | 0.5092 | 0.4589 | -13.300% / -9.874% |
| a3_glm53_dc16k_b1:q1_b1_m1 / body-fixed-grid-glm | Layer 0 / mla / dense_layer | 1 | 0.4020 | 0.3967 | 0.3538 | -11.986% / -10.799% |
| a3_glm53_dc16k_b1:q1_b1_m1 / body-fixed-grid-glm | Steady / mla / dense_layer | 2 | 0.3934 | 0.3879 | 0.3538 | -10.055% / -8.784% |
| a3_glm53_dc16k_b1:q1_b1_m1 / body-fixed-grid-glm | Steady / mla / moe_layer | 75 | 0.5045 | 0.4834 | 0.4343 | -13.904% / -10.159% |
| a3_glm53_dc4k_b1:q1_b1_m1 / body-fixed-grid-glm | Layer 0 / mla / dense_layer | 1 | 0.3943 | 0.3854 | 0.3538 | -10.249% / -8.177% |
| a3_glm53_dc4k_b1:q1_b1_m1 / body-fixed-grid-glm | Steady / mla / dense_layer | 2 | 0.3841 | 0.3775 | 0.3538 | -7.886% / -6.257% |
| a3_glm53_dc4k_b1:q1_b1_m1 / body-fixed-grid-glm | Steady / mla / moe_layer | 75 | 0.5031 | 0.4848 | 0.4343 | -13.663% / -10.409% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / body-fixed-grid-glm | Layer 0 / kda / dense_layer | 1 | 0.8292 | 0.7249 | 0.4057 | -51.070% / -44.026% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / body-fixed-grid-glm | Steady / kda / dense_layer | 2 | 0.2964 | 0.2961 | 0.4057 | 36.893% / 37.020% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / body-fixed-grid-glm | Steady / mla / moe_layer | 11 | 0.9295 | 0.9276 | 0.8750 | -5.864% / -5.669% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / body-fixed-grid-glm | Steady / kda / moe_layer | 31 | 0.5827 | 0.5821 | 0.7789 | 33.681% / 33.812% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 / v41-dynamic-rotary | Layer 0 / mla / moe_layer | 1 | 0.8501 | 0.3611 | 0.1815 | -78.650% / -49.732% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 / v41-dynamic-rotary | Steady / mla / moe_layer | 39 | 0.3189 | 0.3014 | 0.2047 | -35.836% / -32.093% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 / v41-dynamic-rotary | Layer 0 / mla / moe_layer | 1 | 0.4353 | 0.4201 | 0.2225 | -48.879% / -47.034% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 / v41-dynamic-rotary | Steady / mla / moe_layer | 39 | 0.3716 | 0.3526 | 0.2457 | -33.871% / -30.316% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 / v41-dynamic-rotary | Layer 0 / mla / moe_layer | 1 | 0.8470 | 0.8162 | 0.1815 | -78.572% / -77.763% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 / v41-dynamic-rotary | Steady / mla / moe_layer | 39 | 0.3177 | 0.3003 | 0.2047 | -35.579% / -31.851% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 / v41-dynamic-rotary | Layer 0 / mla / moe_layer | 1 | 0.8189 | 0.8103 | 0.1815 | -77.835% / -77.600% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 / v41-dynamic-rotary | Steady / mla / moe_layer | 39 | 0.3157 | 0.2984 | 0.2047 | -35.181% / -31.407% |
| qwen36-a5-tp2-c1:q4_b1_m4 / body-fixed-grid-qwen | Layer 0 / gdn / dense_layer | 1 | 0.2400 | 0.1984 | 0.1156 | -51.821% / -41.727% |
| qwen36-a5-tp2-c1:q4_b1_m4 / body-fixed-grid-qwen | Steady / gdn / dense_layer | 47 | 0.1919 | 0.1915 | 0.1156 | -39.751% / -39.623% |
| qwen36-a5-tp2-c1:q4_b1_m4 / body-fixed-grid-qwen | Steady / gqa / dense_layer | 16 | 0.1880 | 0.1876 | 0.1173 | -37.590% / -37.448% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / body-fixed-grid-glm | Layer 0 / kda / dense_layer | 1 | 0.6141 | 0.5825 | 0.4057 | -33.925% / -30.341% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / body-fixed-grid-glm | Steady / kda / dense_layer | 2 | 0.6160 | 0.5541 | 0.4057 | -34.135% / -26.769% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / body-fixed-grid-glm | Steady / mla / moe_layer | 11 | 1.1665 | 1.1644 | 0.8750 | -24.991% / -24.855% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / body-fixed-grid-glm | Steady / kda / moe_layer | 31 | 0.8101 | 0.8087 | 0.7789 | -3.840% / -3.679% |
| a3_glm53_dc4k_b4:q1_b4_m4 / body-fixed-grid-glm | Layer 0 / mla / dense_layer | 1 | 0.4118 | 0.4071 | 0.3583 | -12.995% / -11.999% |
| a3_glm53_dc4k_b4:q1_b4_m4 / body-fixed-grid-glm | Steady / mla / dense_layer | 2 | 0.3968 | 0.3931 | 0.3583 | -9.722% / -8.853% |
| a3_glm53_dc4k_b4:q1_b4_m4 / body-fixed-grid-glm | Steady / mla / moe_layer | 75 | 0.5622 | 0.5411 | 0.5007 | -10.927% / -7.466% |
| v4flash-a3-tp8-c8:q2_b8_m16 / body-fixed-grid-v4_kimi | Layer 0 / mla / moe_layer | 1 | 0.8072 | 0.7668 | 0.6911 | -14.386% / -9.867% |
| v4flash-a3-tp8-c8:q2_b8_m16 / body-fixed-grid-v4_kimi | Steady / mla / moe_layer | 42 | 0.8787 | 0.8831 | 0.7825 | -10.952% / -11.393% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / runtime86-v4-kimi | Layer 0 / kda / dense_layer | 1 | 0.2579 | 0.2383 | 0.1850 | -28.258% / -22.349% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / runtime86-v4-kimi | Steady / kda / moe_layer | 68 | 0.3399 | 0.3386 | 0.3140 | -7.638% / -7.276% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / runtime86-v4-kimi | Steady / mla / moe_layer | 24 | 0.3835 | 0.3747 | 0.3004 | -21.664% / -19.811% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 / runtime86-v4-kimi | Layer 0 / mla / moe_layer | 1 | 1.4227 | 1.2523 | 1.2727 | -10.548% / 1.624% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 / runtime86-v4-kimi | Steady / mla / moe_layer | 39 | 1.2164 | 1.1586 | 1.2923 | 6.243% / 11.537% |
| a3_glm53_dc4k_b8:q1_b8_m8 / body-fixed-grid-glm | Layer 0 / mla / dense_layer | 1 | 0.4244 | 0.4227 | 0.3663 | -13.700% / -13.347% |
| a3_glm53_dc4k_b8:q1_b8_m8 / body-fixed-grid-glm | Steady / mla / dense_layer | 2 | 0.4119 | 0.4111 | 0.3663 | -11.071% / -10.914% |
| a3_glm53_dc4k_b8:q1_b8_m8 / body-fixed-grid-glm | Steady / mla / moe_layer | 75 | 0.6105 | 0.5863 | 0.5737 | -6.039% / -2.158% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 / runtime86-v4-kimi | Layer 0 / mla / moe_layer | 1 | 1.9490 | 1.6565 | 1.2401 | -36.373% / -25.139% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 / runtime86-v4-kimi | Steady / mla / moe_layer | 39 | 1.1795 | 1.1292 | 1.2572 | 6.588% / 11.333% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / body-fixed-grid-glm | Layer 0 / kda / dense_layer | 1 | 0.6036 | 0.5889 | 0.6465 | 7.102% / 9.781% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / body-fixed-grid-glm | Steady / kda / dense_layer | 2 | 0.5724 | 0.5723 | 0.6465 | 12.948% / 12.973% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / body-fixed-grid-glm | Steady / mla / moe_layer | 11 | 2.2334 | 2.2329 | 1.4272 | -36.097% / -36.082% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / body-fixed-grid-glm | Steady / kda / moe_layer | 31 | 1.0088 | 1.0088 | 1.2061 | 19.554% / 19.556% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 / runtime86-v4-kimi | Layer 0 / mla / moe_layer | 1 | 1.4398 | 1.2987 | 1.2914 | -10.306% / -0.560% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 / runtime86-v4-kimi | Steady / mla / moe_layer | 39 | 1.2521 | 1.1883 | 1.3124 | 4.811% / 10.444% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 / runtime86-v4-kimi | Layer 0 / mla / moe_layer | 1 | 1.6498 | 1.4734 | 1.5525 | -5.894% / 5.374% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 / runtime86-v4-kimi | Steady / mla / moe_layer | 39 | 1.5477 | 1.4627 | 1.5894 | 2.698% / 8.664% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 / kimi-source-a3 | Layer 0 / kda / dense_layer | 1 | 0.8847 | 0.9181 | 0.5126 | -42.054% / -44.162% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 / kimi-source-a3 | Steady / kda / moe_layer | 2 | 1.8592 | 1.8408 | 1.5899 | -14.484% / -13.627% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 / kimi-source-a3 | Steady / mla / moe_layer | 1 | 2.1726 | 2.1723 | 1.6366 | -24.673% / -24.664% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 / kimi-source-a3 | Layer 0 / kda / dense_layer | 1 | 0.9604 | 0.9526 | 0.6391 | -33.453% / -32.908% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 / kimi-source-a3 | Steady / kda / moe_layer | 2 | 2.7714 | 2.7569 | 2.5053 | -9.601% / -9.125% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 / kimi-source-a3 | Steady / mla / moe_layer | 1 | 3.2092 | 3.2089 | 2.6374 | -17.819% / -17.812% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 / kimi-source-a3 | Layer 0 / kda / dense_layer | 1 | 0.9021 | 0.9359 | 0.4496 | -50.159% / -51.958% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 / kimi-source-a3 | Steady / kda / moe_layer | 2 | 1.2773 | 1.2657 | 1.0166 | -20.409% / -19.678% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 / kimi-source-a3 | Steady / mla / moe_layer | 1 | 1.4535 | 1.4525 | 1.0208 | -29.769% / -29.719% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / glm-source-metadata-corrected | Layer 0 / kda / dense_layer | 1 | 0.9534 | 0.9082 | 0.6823 | -28.434% / -24.871% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / glm-source-metadata-corrected | Steady / kda / dense_layer | 2 | 0.8762 | 0.8787 | 0.6823 | -22.129% / -22.348% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / glm-source-metadata-corrected | Steady / mla / moe_layer | 11 | 2.3319 | 2.3310 | 2.6499 | 13.640% / 13.684% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / glm-source-metadata-corrected | Steady / kda / moe_layer | 31 | 1.3210 | 1.3204 | 1.1978 | -9.331% / -9.289% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 / runtime86-v4-kimi | Layer 0 / mla / moe_layer | 1 | 1.6970 | 1.5640 | 1.3737 | -19.053% / -12.170% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 / runtime86-v4-kimi | Steady / mla / moe_layer | 39 | 1.3715 | 1.3077 | 1.4000 | 2.077% / 7.054% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 / kimi-source-a3 | Layer 0 / kda / dense_layer | 1 | 0.8688 | 0.8927 | 0.4144 | -52.305% / -53.583% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 / kimi-source-a3 | Steady / kda / moe_layer | 2 | 0.8910 | 0.8481 | 0.7264 | -18.473% / -14.355% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 / kimi-source-a3 | Steady / mla / moe_layer | 1 | 0.9683 | 0.9617 | 0.6931 | -28.417% / -27.921% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 / kimi-source-a3 | Layer 0 / kda / dense_layer | 1 | 0.9219 | 0.9116 | 0.4090 | -55.636% / -55.134% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 / kimi-source-a3 | Steady / kda / moe_layer | 2 | 0.7774 | 0.7254 | 0.7210 | -7.260% / -0.612% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 / kimi-source-a3 | Steady / mla / moe_layer | 1 | 0.8359 | 0.7994 | 0.6781 | -18.876% / -15.169% |

## Heavy >50us operators — activity residual priority

| Case | Operator / role | Calls | Real / Sim us | Diff us | Absolute ms / Forward | Tier pass |
|---|---|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c16-livepre-q6-b16 / body-fixed-grid-0b822d0e / `2db4b7b48698` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1554 | 142.415 / 285.783 | 143.367 | 6.021 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c8 / 86c1ee8f / `20dbf57be438` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 226.015 / 307.364 | 81.349 | 3.417 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 / `fd8238dbb993` | HcPre / attention.hc_pre | 2115 | 66.201 / 140.275 | 74.073 | 3.333 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 / `fd8238dbb993` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 245.405 / 320.328 | 74.923 | 3.147 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c32 / source-full-18c423c7 / `fd8238dbb993` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2058 | 243.005 / 312.922 | 69.917 | 2.937 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 / `fd8238dbb993` | HcPre / ffn.hc_pre | 2115 | 75.216 / 140.275 | 65.059 | 2.928 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c16 / 86c1ee8f / `20dbf57be438` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2100 | 241.813 / 309.212 | 67.399 | 2.831 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c32 / source-full-18c423c7 / `fd8238dbb993` | HcPre / attention.hc_pre | 2205 | 52.080 / 87.561 | 35.482 | 1.597 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c32 / source-full-18c423c7 / `fd8238dbb993` | HcPre / ffn.hc_pre | 2205 | 52.730 / 87.561 | 34.831 | 1.567 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 / `fd8238dbb993` | MatMulV2 / linear_qkvbfg_a | 1598 | 64.341 / 101.405 | 37.064 | 1.260 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 / `fd8238dbb993` | HcPost / attention.hc_post_group | 2115 | 51.747 / 26.810 | -24.937 | 1.122 | False (compared) |
| a5_glm53flash_tp8_c32_p8k / 86c1ee8f / `20dbf57be438` | GroupedMatmul / expert_down | 1470 | 109.853 / 87.876 | -21.977 | 0.923 | False (compared) |
| a5_glm53flash_tp8_c16_p4k / 86c1ee8f / `20dbf57be438` | GroupedMatmul / expert_down | 1260 | 103.104 / 86.575 | -16.528 | 0.694 | False (compared) |
| a5_glm53flash_tp8_c16_p8k / 86c1ee8f / `20dbf57be438` | GroupedMatmul / expert_down | 1344 | 102.724 / 86.575 | -16.149 | 0.678 | False (compared) |
| a5_glm53flash_tp8_c8_p4k / 86c1ee8f / `20dbf57be438` | GroupedMatmul / expert_down | 1260 | 91.186 / 76.439 | -14.748 | 0.619 | False (compared) |
| glm53flash-a5-tp8-c3 / body-fixed-grid-0b822d0e / `2db4b7b48698` | GroupedMatmul / expert_down | 2226 | 51.524 / 38.227 | -13.297 | 0.558 | False (compared) |
| a5_glm53flash_tp8_c4_p8k / 86c1ee8f / `20dbf57be438` | GroupedMatmul / expert_down | 462 | 51.435 / 38.227 | -13.208 | 0.555 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 / `fd8238dbb993` | MatMulV2 / qkv_a | 517 | 56.384 / 101.486 | 45.102 | 0.496 | False (compared) |
| a5_glm53flash_tp8_c64_p4k / source-full-18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down | 1302 | 115.777 / 111.195 | -4.582 | 0.192 | True (compared) |
| a5_glm53flash_tp8_c32_p4k / source-full-18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down | 1302 | 109.824 / 106.775 | -3.049 | 0.128 | True (compared) |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 / `fd8238dbb993` | MatMulV2 / index_q | 517 | 59.327 / 70.876 | 11.549 | 0.127 | False (compared) |
| a3_kimi4_tp8_w4a8_c64 / source18c423c7 / `fd8238dbb993` | QuantBatchMatmulV3 / gate_up | 196 | 60.636 / 89.300 | 28.664 | 0.029 | False (compared) |
| a3_kimi4_tp8_w4a8_c32 / source18c423c7 / `fd8238dbb993` | QuantBatchMatmulV3 / gate_up | 220 | 56.800 / 79.579 | 22.779 | 0.023 | False (compared) |
| a3_kimi4_tp8_w4a8_c16 / source18c423c7 / `fd8238dbb993` | QuantBatchMatmulV3 / gate_up | 235 | 55.989 / 74.718 | 18.729 | 0.019 | False (compared) |
| a3_kimi4_tp8_w4a8_c4 / source18c423c7 / `fd8238dbb993` | QuantBatchMatmulV3 / gate_up | 246 | 54.590 / 72.287 | 17.698 | 0.018 | False (compared) |
| a3_kimi4_tp8_w4a8_c1 / source18c423c7 / `fd8238dbb993` | QuantBatchMatmulV3 / gate_up | 254 | 56.548 / 72.287 | 15.739 | 0.016 | False (compared) |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / gate_up | 41 | 59.157 / 52.713 | -6.444 | 0.006 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / gate_up | 46 | 59.094 / 52.713 | -6.381 | 0.006 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / gate_up | 47 | 53.443 / 47.325 | -6.118 | 0.006 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / gate_up | 49 | 53.114 / 47.325 | -5.789 | 0.006 | True (compared) |
| a3_kimi4_tp8_w4a8_c64 / source18c423c7 / `fd8238dbb993` | MatMulV2 / output_gate | 196 | 51.145 / 52.683 | 1.538 | 0.002 | True (compared) |

## Micro <=50us operators — activity residual priority

| Case | Operator / role | Calls | Real / Sim us | Diff us | Absolute ms / Forward | Tier pass |
|---|---|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c16-livepre-q6-b16 / body-fixed-grid-0b822d0e / `2db4b7b48698` | HcPre / attention.hc_pre | 1665 | 33.367 / 170.607 | 137.240 | 6.176 | None (reference_only) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / body-fixed-grid-0b822d0e / `2db4b7b48698` | HcPre / ffn.hc_pre | 1665 | 36.039 / 170.607 | 134.568 | 6.056 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 / `fd8238dbb993` | QuantBatchMatmulV3 / shared.down | 1974 | 41.694 / 8.888 | -32.806 | 1.378 | False (compared) |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_down | 3772 | 26.876 / 14.433 | -12.443 | 1.145 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_down | 4232 | 26.875 / 14.433 | -12.442 | 1.145 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_down | 4324 | 25.351 / 14.206 | -11.145 | 1.025 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_down | 4508 | 25.319 / 14.206 | -11.113 | 1.022 | True (compared) |
| a3_glm53flash_tp16_aclgraph_c32 / source-full-18c423c7 / `fd8238dbb993` | QuantBatchMatmulV3 / shared.down | 2058 | 28.641 / 5.000 | -23.641 | 0.993 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c16 / 86c1ee8f / `20dbf57be438` | HcPre / attention.hc_pre | 2250 | 39.826 / 61.206 | 21.381 | 0.962 | None (reference_only) |
| a5_kimi_tp8_e16_bf16_c8_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_down | 4784 | 24.439 / 14.093 | -10.346 | 0.952 | True (compared) |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_down | 4692 | 24.431 / 14.093 | -10.338 | 0.951 | True (compared) |
| a5_kimi_tp8_e16_bf16_c4_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_down | 4876 | 24.291 / 14.093 | -10.198 | 0.938 | True (compared) |
| a5_kimi_tp8_e16_bf16_c4_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_down | 4784 | 24.241 / 14.093 | -10.149 | 0.934 | True (compared) |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 / `fd8238dbb993` | HcPost / ffn.hc_post_group | 2115 | 47.315 / 26.810 | -20.505 | 0.923 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c16 / 86c1ee8f / `20dbf57be438` | HcPre / ffn.hc_pre | 2250 | 41.007 / 61.206 | 20.200 | 0.909 | None (reference_only) |
| a5_kimi_tp8_e16_bf16_c2_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_down | 5060 | 23.910 / 14.093 | -9.818 | 0.903 | True (compared) |
| a5_kimi_tp8_e16_bf16_c2_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_down | 4968 | 23.893 / 14.093 | -9.800 | 0.902 | True (compared) |
| a5_kimi_tp8_e16_bf16_c1_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_down | 5428 | 23.858 / 14.093 | -9.765 | 0.898 | True (compared) |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_down | 5428 | 23.857 / 14.093 | -9.765 | 0.898 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_up | 3772 | 22.659 / 14.303 | -8.357 | 0.769 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_up | 4232 | 22.651 / 14.303 | -8.348 | 0.768 | True (compared) |
| a3_glm53flash_tp16_aclgraph_c32 / source-full-18c423c7 / `fd8238dbb993` | HcPost / attention.hc_post_group | 2205 | 30.239 / 13.405 | -16.834 | 0.758 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c8 / 86c1ee8f / `20dbf57be438` | HcPre / attention.hc_pre | 2115 | 37.137 / 53.874 | 16.738 | 0.753 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c8 / 86c1ee8f / `20dbf57be438` | HcPre / ffn.hc_pre | 2115 | 37.220 / 53.874 | 16.655 | 0.749 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c32 / source-full-18c423c7 / `fd8238dbb993` | MatMulV2 / index_k | 1078 | 8.236 / 40.495 | 32.258 | 0.710 | False (compared) |
| a5_kimi_tp8_e16_bf16_c16_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_up | 4508 | 21.792 / 14.180 | -7.613 | 0.700 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_up | 4324 | 21.790 / 14.180 | -7.610 | 0.700 | True (compared) |
| glm53flash-a5-tp8-c3 / body-fixed-grid-0b822d0e / `2db4b7b48698` | HcPre / attention.hc_pre | 2385 | 11.753 / 27.199 | 15.446 | 0.695 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c32 / source-full-18c423c7 / `fd8238dbb993` | HcPost / ffn.hc_post_group | 2205 | 28.713 / 13.405 | -15.308 | 0.689 | False (compared) |
| glm53flash-a5-tp8-c3 / body-fixed-grid-0b822d0e / `2db4b7b48698` | HcPre / ffn.hc_pre | 2385 | 11.905 / 27.199 | 15.293 | 0.688 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c16 / 86c1ee8f / `20dbf57be438` | QuantBatchMatmulV3 / shared.down | 2100 | 20.759 / 5.000 | -15.759 | 0.662 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 / `fd8238dbb993` | MatMulV2 / index_k | 1034 | 10.620 / 40.495 | 29.875 | 0.657 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c16 / 86c1ee8f / `20dbf57be438` | HcPost / attention.hc_post_group | 2250 | 21.017 / 6.703 | -14.314 | 0.644 | True (compared) |
| a5_kimi_tp8_e16_bf16_c8_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_up | 4784 | 21.042 / 14.118 | -6.924 | 0.637 | True (compared) |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_up | 4692 | 21.032 / 14.118 | -6.913 | 0.636 | True (compared) |
| a5_kimi_tp8_e16_bf16_c4_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_up | 4784 | 20.956 / 14.118 | -6.838 | 0.629 | True (compared) |
| a5_kimi_tp8_e16_bf16_c4_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_up | 4876 | 20.950 / 14.118 | -6.831 | 0.628 | True (compared) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / body-fixed-grid-0b822d0e / `2db4b7b48698` | MatMulV2 / index_k | 814 | 7.501 / 35.375 | 27.873 | 0.613 | False (compared) |
| a5_kimi_tp8_e16_bf16_c2_p16k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_up | 4968 | 20.767 / 14.118 | -6.648 | 0.612 | True (compared) |
| a5_kimi_tp8_e16_bf16_c2_p4k / source18c423c7 / `fd8238dbb993` | MatMulV3 / latent_up | 5060 | 20.757 / 14.118 | -6.639 | 0.611 | True (compared) |

## Highest unscored activity — coverage gaps, not zero predictions

| Case | Operator / role | Unscored calls | Unscored observed activity ms / Forward | Status |
|---|---|---:|---:|---|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs | DispatchFFNCombine / routed_ffn_native | 840 | 28.737 | reference_only |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 / runtime67-refs | DispatchFFNCombine / routed_ffn_native | 880 | 28.722 | reference_only |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 / runtime67-refs | DispatchFFNCombine / routed_ffn_native | 1920 | 28.483 | reference_only |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 / runtime67-refs | DispatchFFNCombine / routed_ffn_native | 1280 | 27.940 | reference_only |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 / runtime67-refs | DispatchFFNCombine / routed_ffn_native | 1160 | 27.761 | reference_only |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 | KvQuantSparseFlashAttentionVllm / unresolved | 517 | 17.956 | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 10.307 | reference_only |
| a3_glm53flash_tp16_aclgraph_c32 / source-full-18c423c7 | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2058 | 10.206 | reference_only |
| a3_glm53flash_tp16_aclgraph_c16 / 86c1ee8f | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2100 | 10.156 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime86-baseline | GroupedMatmul / expert_up | 2920 | 10.006 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime86-baseline | GroupedMatmul / expert_up | 3000 | 9.704 | reference_only |
| a3_glm53flash_tp16_aclgraph_c8 / 86c1ee8f | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 9.493 | reference_only |
| a3_glm53flash_tp16_aclgraph_c32 / source-full-18c423c7 | KvQuantSparseFlashAttentionVllm / unresolved | 539 | 9.128 | unresolved |
| a5_glm53flash_tp8_c64_p4k / source-full-18c423c7 | GroupedMatmulSwigluQuantV2 / unresolved | 1302 | 8.866 | unresolved |
| a5_glm53flash_tp8_c32_p4k / source-full-18c423c7 | GroupedMatmulSwigluQuantV2 / unresolved | 1302 | 8.730 | unresolved |
| a5_glm53flash_tp8_c32_p8k / 86c1ee8f | GroupedMatmulSwigluQuantV2 / unresolved | 1470 | 8.730 | unresolved |
| a5_glm53flash_tp8_c16_p4k / 86c1ee8f | GroupedMatmulSwigluQuantV2 / unresolved | 1260 | 8.662 | unresolved |
| a5_glm53flash_tp8_c16_p8k / 86c1ee8f | GroupedMatmulSwigluQuantV2 / unresolved | 1344 | 8.656 | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 | RecurrentKda / unresolved | 1598 | 8.348 | unresolved |
| a5_glm53flash_tp8_c8_p4k / 86c1ee8f | GroupedMatmulSwigluQuantV2 / unresolved | 1260 | 7.753 | unresolved |
| a5_kimi_k3_p32768_c1 / runtime86-context32768-matrix-only | GroupedMatmul / unresolved | 21735 | 6.993 | unresolved |
| a5_kimi_k3_p32768_c1 / runtime86-context32768-matrix-only | GroupedMatmulSituQuant / grouped_gate_up_situ_quant | 5796 | 6.831 | unresolved |
| a5_kimi_tp8_e16_bf16_c4_p4k / source18c423c7 | MatMulV3 / unresolved | 23267 | 6.745 | unresolved |
| a5_kimi_tp8_e16_bf16_c4_p16k / source18c423c7 | MatMulV3 / unresolved | 22828 | 6.743 | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 | hcom_allReduce_ / attention_output_communication | 2115 | 6.713 | unresolved |
| a5_kimi_tp8_e16_bf16_c2_p16k / source18c423c7 | MatMulV3 / unresolved | 23706 | 6.640 | unresolved |
| a5_kimi_tp8_e16_bf16_c2_p4k / source18c423c7 | MatMulV3 / unresolved | 24145 | 6.635 | unresolved |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 | MatMulV3 / unresolved | 25901 | 6.594 | unresolved |
| a5_kimi_tp8_e16_bf16_c1_p4k / source18c423c7 | MatMulV3 / unresolved | 25901 | 6.593 | unresolved |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 | FusedInferAttentionScore / unresolved | 984 | 6.338 | reference_only |
| a3_glm53flash_tp16_aclgraph_c64 / source-full-18c423c7 | hcom_allReduce_ / ffn_down_communication | 2115 | 6.083 | unresolved |
| a5_kimi_k3_p32768_c1 / runtime86-context32768-matrix-only | SituMxQuant / shared.situ_quant | 5796 | 5.994 | unresolved |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / body-fixed-grid-0b822d0e | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1554 | 5.981 | reference_only |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs | SparseFlashMla / unresolved | 840 | 5.957 | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 / runtime67-refs | reduce_scatterAicpuKernel / unresolved | 1920 | 5.643 | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 / runtime67-refs | reduce_scatterAicpuKernel / unresolved | 1160 | 5.633 | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 / runtime67-refs | reduce_scatterAicpuKernel / unresolved | 1280 | 5.599 | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs | reduce_scatterAicpuKernel / unresolved | 840 | 5.539 | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 / runtime67-refs | reduce_scatterAicpuKernel / unresolved | 880 | 5.507 | unresolved |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline | GroupedMatmul / expert_up | 4200 | 5.096 | reference_only |

## Source-role references — already costed work is not an extra budget

Reference differences have distinct evidence and are excluded from strict cohort accuracy counts.

External native references are selected independently by measured source/geometry, native operator, role, layer set and observed ABI. Each row retains its own histogram P50; rows are not averaged.

| Case | Operator / region | Calls | Real Mean / P50 / reference us | Real / Sim service ms per Forward | Residual ms | Boundary |
|---|---|---:|---:|---:|---:|---|
| a3_glm53flash_tp16_aclgraph_c64 / `fd8238dbb993` | KvQuantSparseFlashAttentionVllm / indexed_attention_batch / layers 3,7,11,15,19,23,27,31,35,39,43 | 517 | 1632.353 / 1632.673 / 2596.536 | 17.956 / 28.562 | 10.606 | whole_batch_packed528_int8_analytic_reference |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs / `c27d72c215c2` | DispatchFFNCombine / routed_ffn_native / mla / ffn | 840 | 718.428 / 712.576 / 972.699 | 28.737 / 38.908 | 10.171 | whole_routed_ffn_decomposed_program_reference |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 / runtime67-refs / `c27d72c215c2` | DispatchFFNCombine / routed_ffn_native / mla / ffn | 1160 | 694.018 / 691.047 / 921.873 | 27.761 / 36.875 | 9.114 | whole_routed_ffn_decomposed_program_reference |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 / runtime67-refs / `c27d72c215c2` | DispatchFFNCombine / routed_ffn_native / mla / ffn | 1280 | 698.498 / 695.156 / 924.931 | 27.940 / 36.997 | 9.057 | whole_routed_ffn_decomposed_program_reference |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 / runtime67-refs / `c27d72c215c2` | DispatchFFNCombine / routed_ffn_native / mla / ffn | 880 | 718.046 / 712.566 / 940.671 | 28.722 / 37.627 | 8.905 | whole_routed_ffn_decomposed_program_reference |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 / runtime67-refs / `c27d72c215c2` | DispatchFFNCombine / routed_ffn_native / mla / ffn | 1920 | 712.078 / 695.766 / 915.819 | 28.483 / 36.633 | 8.150 | whole_routed_ffn_decomposed_program_reference |
| a3_glm53flash_tp16_aclgraph_c32 / `fd8238dbb993` | KvQuantSparseFlashAttentionVllm / indexed_attention_batch / layers 3,7,11,15,19,23,27,31,35,39,43 | 539 | 829.848 / 829.977 / 1298.268 | 9.128 / 14.281 | 5.153 | whole_batch_packed528_int8_analytic_reference |
| a5_glm53flash_tp8_c64_p4k / `fd8238dbb993` | SparseFlashMla / indexed_attention_batch / layers 3,7,11,15,19,23,27,31,35,39,43 | 341 | 288.254 / 285.492 / 590.348 | 3.171 / 6.494 | 3.323 | whole_batch_indexed_attention_reference |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_up / mla / ffn | 2920 | 250.141 / 248.818 / 174.004 | 10.006 / 6.960 | -3.045 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | MoeDistributeDispatchV3 / expert_dispatch_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 3772 | 34.207 / 34.204 / 2.728 | 3.147 / 0.251 | -2.896 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | MoeDistributeDispatchV3 / expert_dispatch_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4232 | 34.197 / 34.183 / 2.728 | 3.146 / 0.251 | -2.895 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | MoeDistributeDispatchV3 / expert_dispatch_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4508 | 33.414 / 33.418 / 2.453 | 3.074 / 0.226 | -2.848 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | MoeDistributeDispatchV3 / expert_dispatch_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4324 | 33.413 / 33.421 / 2.453 | 3.074 / 0.226 | -2.848 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | MoeDistributeDispatchV3 / expert_dispatch_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4692 | 32.982 / 32.979 / 2.315 | 3.034 / 0.213 | -2.821 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | MoeDistributeDispatchV3 / expert_dispatch_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4784 | 32.913 / 32.904 / 2.315 | 3.028 / 0.213 | -2.815 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | MoeDistributeCombineV3 / expert_combine_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4968 | 34.585 / 34.645 / 3.989 | 3.182 / 0.367 | -2.815 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | MoeDistributeCombineV3 / expert_combine_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 5060 | 34.497 / 34.534 / 3.989 | 3.174 / 0.367 | -2.807 | complete_native_mc2_source_phase_program_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_up / mla / ffn | 3000 | 242.599 / 241.331 / 172.568 | 9.704 / 6.903 | -2.801 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | MoeDistributeDispatchV3 / expert_dispatch_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4784 | 31.864 / 31.860 / 2.315 | 2.931 / 0.213 | -2.718 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | MoeDistributeDispatchV3 / expert_dispatch_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4876 | 31.842 / 31.813 / 2.315 | 2.929 / 0.213 | -2.716 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | MoeDistributeDispatchV3 / expert_dispatch_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4968 | 31.565 / 31.543 / 2.315 | 2.904 / 0.213 | -2.691 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | MoeDistributeDispatchV3 / expert_dispatch_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 5060 | 31.532 / 31.513 / 2.315 | 2.901 / 0.213 | -2.688 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | MoeDistributeDispatchV3 / expert_dispatch_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 5428 | 31.335 / 31.323 / 2.315 | 2.883 / 0.213 | -2.670 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | MoeDistributeDispatchV3 / expert_dispatch_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 5428 | 31.319 / 31.314 / 2.315 | 2.881 / 0.213 | -2.668 | complete_native_mc2_source_phase_program_reference |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / linear_reduce / gdn / attention | 1392 | 79.592 / 79.195 / 30.862 | 3.820 / 1.481 | -2.339 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gdn / ffn | 1392 | 76.826 / 76.629 / 30.862 | 3.688 / 1.481 | -2.206 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / linear_reduce / gdn / attention | 3504 | 61.908 / 23.244 / 25.931 | 2.972 / 1.245 | -1.727 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_up / mla / ffn | 4200 | 127.406 / 126.789 / 86.330 | 5.096 / 3.453 | -1.643 | capacity_vs_valid_rows_conditional |
| a3_glm53flash_tp16_aclgraph_c8 / 86c1ee8f / `20dbf57be438` | GroupedMatmul / expert_down / mla / ffn | 1974 | 113.793 / 112.993 / 152.643 | 4.779 / 6.411 | 1.632 | capacity_vs_valid_rows_conditional |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / linear_reduce / gdn / attention | 1824 | 81.530 / 66.266 / 48.606 | 3.913 / 2.333 | -1.580 | reference_only |
| a5_glm53flash_tp8_c32_p4k / `fd8238dbb993` | SparseFlashMla / indexed_attention_batch / layers 3,7,11,15,19,23,27,31,35,39,43 | 341 | 153.517 / 153.209 / 295.174 | 1.689 / 3.247 | 1.558 | whole_batch_indexed_attention_reference |
| a5_glm53flash_tp8_c64_p4k / `fd8238dbb993` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 961 | 211.180 / 210.918 / 161.025 | 6.547 / 4.992 | -1.555 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c32_p4k / `fd8238dbb993` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 961 | 207.720 / 207.499 / 159.681 | 6.439 / 4.950 | -1.489 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c32_p8k / `380cb5516b56` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 1085 | 207.698 / 207.331 / 159.681 | 6.439 / 4.950 | -1.489 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c16_p4k / `380cb5516b56` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 930 | 206.079 / 205.812 / 159.009 | 6.388 / 4.929 | -1.459 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c16_p8k / `380cb5516b56` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 992 | 205.999 / 205.726 / 159.009 | 6.386 / 4.929 | -1.457 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a3_glm53flash_tp16_aclgraph_c16 / 86c1ee8f / `20dbf57be438` | GroupedMatmul / expert_down / mla / ffn | 2100 | 119.516 / 118.882 / 153.715 | 5.020 / 6.456 | 1.436 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c32_p4k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 4232 | 46.237 / 47.053 / 30.880 | 4.254 / 2.841 | -1.413 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 3772 | 46.220 / 47.020 / 30.880 | 4.252 / 2.841 | -1.411 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_down / mla / ffn | 2920 | 123.273 / 122.228 / 89.337 | 4.931 / 3.573 | -1.357 | capacity_vs_valid_rows_conditional |
| a5_glm53flash_tp8_c8_p4k / `380cb5516b56` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 930 | 184.394 / 183.976 / 141.372 | 5.716 / 4.383 | -1.334 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 4324 | 44.038 / 44.390 / 29.886 | 4.052 / 2.750 | -1.302 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c16_p4k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 4508 | 43.967 / 44.307 / 29.886 | 4.045 / 2.750 | -1.295 | capacity_vs_valid_rows_conditional |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / linear_reduce / gdn / attention | 2592 | 58.791 / 32.182 / 32.514 | 2.822 / 1.561 | -1.261 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_down / mla / ffn | 3000 | 119.854 / 118.821 / 88.541 | 4.794 / 3.542 | -1.253 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 4692 | 42.682 / 42.857 / 29.389 | 3.927 / 2.704 | -1.223 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c8_p4k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 4784 | 42.630 / 42.813 / 29.389 | 3.922 / 2.704 | -1.218 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c4_p16k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 4784 | 41.471 / 41.486 / 29.389 | 3.815 / 2.704 | -1.112 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c4_p4k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 4876 | 41.239 / 41.265 / 29.389 | 3.794 / 2.704 | -1.090 | capacity_vs_valid_rows_conditional |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / linear_reduce / gdn / attention | 2304 | 38.341 / 36.834 / 15.816 | 1.840 / 0.759 | -1.081 | reference_only |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | MoeDistributeCombineV3 / expert_combine_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 5428 | 14.550 / 14.394 / 3.989 | 1.339 / 0.367 | -0.972 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | MoeDistributeCombineV3 / expert_combine_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 5428 | 14.544 / 14.416 / 3.989 | 1.338 / 0.367 | -0.971 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | MoeDistributeCombineV3 / expert_combine_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4784 | 14.508 / 14.450 / 3.989 | 1.335 / 0.367 | -0.968 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | MoeDistributeCombineV3 / expert_combine_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4692 | 14.491 / 14.450 / 3.989 | 1.333 / 0.367 | -0.966 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | MoeDistributeCombineV3 / expert_combine_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4508 | 14.726 / 14.598 / 4.266 | 1.355 / 0.393 | -0.962 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | MoeDistributeCombineV3 / expert_combine_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4876 | 14.448 / 14.367 / 3.989 | 1.329 / 0.367 | -0.962 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | MoeDistributeCombineV3 / expert_combine_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4324 | 14.691 / 14.569 / 4.266 | 1.352 / 0.393 | -0.959 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | MoeDistributeCombineV3 / expert_combine_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4784 | 14.338 / 14.266 / 3.989 | 1.319 / 0.367 | -0.952 | complete_native_mc2_source_phase_program_reference |
| a5_glm53flash_tp8_c32_p8k / `380cb5516b56` | SparseFlashMla / indexed_attention_batch / layers 3,7,11,15,19,23,27,31,35,39,43 | 385 | 153.329 / 153.215 / 67.895 | 1.687 / 0.747 | -0.940 | whole_batch_indexed_attention_decomposed_reference |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_up / mla / ffn | 5160 | 68.076 / 67.778 / 44.746 | 2.723 / 1.790 | -0.933 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | MoeDistributeCombineV3 / expert_combine_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 3772 | 14.615 / 14.506 / 4.541 | 1.345 / 0.418 | -0.927 | complete_native_mc2_source_phase_program_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | MoeDistributeCombineV3 / expert_combine_native / layers 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92 | 4232 | 14.584 / 14.442 / 4.541 | 1.342 / 0.418 | -0.924 | complete_native_mc2_source_phase_program_reference |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gdn / ffn | 2304 | 34.882 / 34.719 / 15.816 | 1.674 / 0.759 | -0.915 | reference_only |
| a5_glm53flash_tp8_c64_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 1054 | 78.338 / 78.285 / 103.616 | 2.664 / 3.523 | 0.859 | whole_batch_generic_gating_and_recurrent_reference |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_down / mla / ffn | 4200 | 65.238 / 64.668 / 44.275 | 2.610 / 1.771 | -0.838 | capacity_vs_valid_rows_conditional |
| glm53flash-a5-tp8-c3 / `380cb5516b56` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 1643 | 98.658 / 98.458 / 72.080 | 3.058 / 2.234 | -0.824 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 4232 | 22.016 / 22.110 / 13.086 | 2.025 / 1.204 | -0.822 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c32_p16k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 3772 | 22.006 / 22.107 / 13.086 | 2.025 / 1.204 | -0.821 | capacity_vs_valid_rows_conditional |
| a5_glm53flash_tp8_c4_p8k / `380cb5516b56` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 341 | 98.439 / 98.184 / 71.998 | 3.052 / 2.232 | -0.820 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 4508 | 21.325 / 21.385 / 12.656 | 1.962 / 1.164 | -0.798 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c16_p16k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 4324 | 21.305 / 21.374 / 12.656 | 1.960 / 1.164 | -0.796 | capacity_vs_valid_rows_conditional |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp_attn / gqa / attention | 464 | 79.629 / 78.483 / 30.862 | 1.274 / 0.494 | -0.780 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / tp / gdn / ffn | 1824 | 64.239 / 64.206 / 48.606 | 3.083 / 2.333 | -0.750 | reference_only |
| a5_kimi_tp8_e16_bf16_c8_p4k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 4784 | 20.594 / 20.584 / 12.441 | 1.895 / 1.145 | -0.750 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c8_p16k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 4692 | 20.570 / 20.564 / 12.441 | 1.892 / 1.145 | -0.748 | capacity_vs_valid_rows_conditional |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gqa / ffn | 464 | 76.434 / 76.275 / 30.862 | 1.223 / 0.494 | -0.729 | reference_only |
| a5_kimi_tp8_e16_bf16_c4_p16k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 4784 | 20.097 / 20.084 / 12.441 | 1.849 / 1.145 | -0.704 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c4_p4k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 4876 | 20.066 / 20.058 / 12.441 | 1.846 / 1.145 | -0.701 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c1_p4k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 5428 | 21.918 / 21.895 / 29.389 | 2.016 / 2.704 | 0.687 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 5428 | 21.957 / 21.948 / 29.389 | 2.020 / 2.704 | 0.684 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | CausalConv1d / short_convolution / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 2829 | 10.981 / 10.934 / 1.312 | 0.758 / 0.091 | -0.667 | declared_short_convolution_program_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | CausalConv1d / short_convolution / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3174 | 10.930 / 10.894 / 1.312 | 0.754 / 0.091 | -0.664 | declared_short_convolution_program_reference |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_up / mla / ffn | 6040 | 38.809 / 38.660 / 22.384 | 1.552 / 0.895 | -0.657 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c2_p16k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 4968 | 22.335 / 22.320 / 29.389 | 2.055 / 2.704 | 0.649 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_up / mla / ffn | 6080 | 38.592 / 38.458 / 22.384 | 1.544 / 0.895 | -0.648 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_up / mla / ffn | 5800 | 38.541 / 38.378 / 22.384 | 1.542 / 0.895 | -0.646 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c2_p4k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 5060 | 22.426 / 22.406 / 29.389 | 2.063 / 2.704 | 0.641 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_down / mla / ffn | 5160 | 37.439 / 37.167 / 22.163 | 1.498 / 0.887 | -0.611 | capacity_vs_valid_rows_conditional |
| a5_glm53flash_tp8_c16_p8k / `380cb5516b56` | SparseFlashMla / indexed_attention_batch / layers 3,7,11,15,19,23,27,31,35,39,43 | 352 | 86.858 / 86.710 / 33.948 | 0.955 / 0.373 | -0.582 | whole_batch_indexed_attention_decomposed_reference |
| a5_glm53flash_tp8_c16_p4k / `380cb5516b56` | SparseFlashMla / indexed_attention_batch / layers 3,7,11,15,19,23,27,31,35,39,43 | 330 | 86.586 / 86.495 / 33.948 | 0.952 / 0.373 | -0.579 | whole_batch_indexed_attention_decomposed_reference |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime86-baseline / `20dbf57be438` | HcPre / attention.hc_pre / mla / attention | 2920 | 12.178 / 12.002 / 26.538 | 0.487 / 1.062 | 0.574 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime86-baseline / `20dbf57be438` | HcPre / ffn.hc_pre / mla / ffn | 2920 | 12.209 / 11.944 / 26.538 | 0.488 / 1.062 | 0.573 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 2900 | 29.224 / 29.082 / 1.578 | 0.584 / 0.032 | -0.553 | source_symbol_to_declared_attention_program |
| a5_glm53flash_tp8_c64_p4k / `fd8238dbb993` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 3,7,11,15,19,23,27,31,35,39,43 | 341 | 210.831 / 210.350 / 161.025 | 2.319 / 1.771 | -0.548 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c32_p4k / `fd8238dbb993` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 3,7,11,15,19,23,27,31,35,39,43 | 341 | 208.275 / 208.143 / 159.681 | 2.291 / 1.756 | -0.535 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c32_p8k / `380cb5516b56` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 3,7,11,15,19,23,27,31,35,39,43 | 385 | 208.272 / 207.963 / 159.681 | 2.291 / 1.756 | -0.535 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 2580 | 29.623 / 29.503 / 3.156 | 0.592 / 0.063 | -0.529 | source_symbol_to_declared_attention_program |
| a5_glm53flash_tp8_c16_p4k / `380cb5516b56` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 3,7,11,15,19,23,27,31,35,39,43 | 330 | 206.645 / 206.287 / 159.009 | 2.273 / 1.749 | -0.524 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c16_p8k / `380cb5516b56` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 3,7,11,15,19,23,27,31,35,39,43 | 352 | 206.404 / 206.335 / 159.009 | 2.270 / 1.749 | -0.521 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 2100 | 31.372 / 30.919 / 6.312 | 0.627 / 0.126 | -0.501 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / `36284f768868` | TransposeQuantBatchMatMul / grouped_output_a / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 2920 | 21.093 / 21.082 / 8.638 | 0.844 / 0.346 | -0.498 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 2610 | 29.070 / 28.659 / 1.578 | 0.523 / 0.028 | -0.495 | source_symbol_to_declared_attention_program |
| a5_glm53flash_tp8_c4_p8k / `380cb5516b56` | SparseFlashMla / indexed_attention_batch / layers 3,7,11,15,19,23,27,31,35,39,43 | 121 | 52.802 / 52.896 / 8.487 | 0.581 / 0.093 | -0.487 | whole_batch_indexed_attention_decomposed_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | CausalConv1d / short_convolution / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3243 | 8.341 / 8.304 / 1.312 | 0.575 / 0.091 | -0.485 | declared_short_convolution_program_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | CausalConv1d / short_convolution / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3381 | 8.332 / 8.289 / 1.312 | 0.575 / 0.091 | -0.484 | declared_short_convolution_program_reference |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 2322 | 29.915 / 29.194 / 3.156 | 0.538 / 0.057 | -0.482 | source_symbol_to_declared_attention_program |
| a5_glm53flash_tp8_c8_p4k / `380cb5516b56` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 3,7,11,15,19,23,27,31,35,39,43 | 330 | 185.150 / 184.762 / 141.372 | 2.037 / 1.555 | -0.482 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| glm53flash-a5-tp8-c3 / `380cb5516b56` | SparseFlashMla / indexed_attention_batch / layers 3,7,11,15,19,23,27,31,35,39,43 | 583 | 52.104 / 52.102 / 8.487 | 0.573 / 0.093 | -0.480 | whole_batch_indexed_attention_decomposed_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / `36284f768868` | TransposeQuantBatchMatMul / grouped_output_a / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 3000 | 20.492 / 20.480 / 8.507 | 0.820 / 0.340 | -0.479 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_down / mla / ffn | 5800 | 23.656 / 23.572 / 11.813 | 0.946 / 0.473 | -0.474 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_down / mla / ffn | 6080 | 23.639 / 23.543 / 11.813 | 0.946 / 0.473 | -0.473 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime86-baseline / `20dbf57be438` | GroupedMatmul / expert_down / mla / ffn | 6040 | 23.604 / 23.476 / 11.813 | 0.944 / 0.473 | -0.472 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / `36284f768868` | TransposeQuantBatchMatMul / grouped_output_a / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 4200 | 20.003 / 19.975 / 8.452 | 0.800 / 0.338 | -0.462 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 1890 | 30.876 / 30.200 / 6.312 | 0.556 / 0.114 | -0.442 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / `36284f768868` | TransposeQuantBatchMatMul / grouped_output_a / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 5160 | 19.389 / 19.360 / 8.424 | 0.776 / 0.337 | -0.439 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / `36284f768868` | TransposeQuantBatchMatMul / grouped_output_a / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 5800 | 18.967 / 18.925 / 8.411 | 0.759 / 0.336 | -0.422 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / `36284f768868` | TransposeQuantBatchMatMul / grouped_output_a / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 6040 | 18.932 / 18.897 / 8.411 | 0.757 / 0.336 | -0.421 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / `36284f768868` | TransposeQuantBatchMatMul / grouped_output_a / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 6080 | 18.924 / 18.895 / 8.411 | 0.757 / 0.336 | -0.421 | source_role_conditional_existing_semantic_program |
| glm53flash-a5-tp8-c1 / `fd8238dbb993` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 2015 | 33.520 / 33.438 / 19.967 | 1.039 / 0.619 | -0.420 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 1500 | 33.567 / 32.496 / 12.624 | 0.671 / 0.252 | -0.419 | source_symbol_to_declared_attention_program |
| a5_glm53flash_tp8_c8_p4k / `380cb5516b56` | SparseFlashMla / indexed_attention_batch / layers 3,7,11,15,19,23,27,31,35,39,43 | 330 | 53.600 / 53.586 / 16.974 | 0.590 / 0.187 | -0.403 | whole_batch_indexed_attention_decomposed_reference |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 464 | 28.389 / 28.261 / 3.542 | 0.454 / 0.057 | -0.398 | reference_only |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | CausalConv1d / short_convolution / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3519 | 7.058 / 7.045 / 1.312 | 0.487 / 0.091 | -0.396 | declared_short_convolution_program_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | CausalConv1d / short_convolution / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3588 | 7.043 / 7.032 / 1.312 | 0.486 / 0.091 | -0.395 | declared_short_convolution_program_reference |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / tp_attn / gqa / attention | 608 | 73.299 / 72.073 / 48.606 | 1.173 / 0.778 | -0.395 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime86-baseline / `20dbf57be438` | HcPre / ffn.hc_pre / mla / ffn | 3000 | 11.660 / 11.412 / 21.524 | 0.466 / 0.861 | 0.395 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime86-baseline / `20dbf57be438` | HcPre / attention.hc_pre / mla / attention | 3000 | 11.719 / 11.552 / 21.524 | 0.469 / 0.861 | 0.392 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 1350 | 33.893 / 34.158 / 12.624 | 0.610 / 0.227 | -0.383 | source_symbol_to_declared_attention_program |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 608 | 26.844 / 26.806 / 3.148 | 0.429 / 0.050 | -0.379 | reference_only |
| a3_kimi4_tp8_w4a8_c1 / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 762 | 55.722 / 55.499 / 175.598 | 0.167 / 0.527 | 0.360 | capacity_vs_valid_rows_conditional |
| a3_kimi4_tp8_w4a8_c64 / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 588 | 1095.630 / 1098.018 / 1214.924 | 3.287 / 3.645 | 0.358 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c2_p16k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 4968 | 16.222 / 16.216 / 12.441 | 1.492 / 1.145 | -0.348 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c2_p4k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 5060 | 16.222 / 16.211 / 12.441 | 1.492 / 1.145 | -0.348 | capacity_vs_valid_rows_conditional |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / linear_reduce / gdn / attention | 2160 | 18.655 / 18.451 / 11.427 | 0.895 / 0.548 | -0.347 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp_attn / gqa / attention | 768 | 36.991 / 36.346 / 15.816 | 0.592 / 0.253 | -0.339 | reference_only |
| a5_kimi_tp8_e16_bf16_c1_p16k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 5428 | 16.052 / 16.026 / 12.441 | 1.477 / 1.145 | -0.332 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c1_p4k / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 5428 | 16.045 / 16.026 / 12.441 | 1.476 / 1.145 | -0.332 | capacity_vs_valid_rows_conditional |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 1392 | 8.186 / 8.182 / 1.312 | 0.393 / 0.063 | -0.330 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / `20dbf57be438` | HcPre / ffn.hc_pre / mla / ffn | 4200 | 11.183 / 11.022 / 19.016 | 0.447 / 0.761 | 0.313 | partial_base_program_reference_premix_branch_unresolved |
| a5_glm53flash_tp8_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 1054 | 43.987 / 44.073 / 53.120 | 1.496 / 1.806 | 0.311 | whole_batch_generic_gating_and_recurrent_reference |
| a5_glm53flash_tp8_c32_p8k / `380cb5516b56` | RecurrentKda / kda_recurrent / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 1190 | 44.025 / 44.062 / 53.120 | 1.497 / 1.806 | 0.309 | whole_batch_generic_gating_and_recurrent_reference |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / `20dbf57be438` | HcPre / attention.hc_pre / mla / attention | 4200 | 11.294 / 11.107 / 19.016 | 0.452 / 0.761 | 0.309 | partial_base_program_reference_premix_branch_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gqa / ffn | 768 | 34.787 / 34.649 / 15.816 | 0.557 / 0.253 | -0.304 | reference_only |
| glm53flash-a5-tp8-c1 / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 2210 | 13.004 / 12.695 / 4.202 | 0.442 / 0.143 | -0.299 | whole_batch_generic_gating_and_recurrent_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3128 | 11.525 / 11.296 / 7.175 | 0.784 / 0.488 | -0.296 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 2788 | 11.524 / 11.312 / 7.175 | 0.784 / 0.488 | -0.296 | captured_layer_multiplicity_weighted_source_program_reference |
| glm53flash-a5-tp8-c3 / `380cb5516b56` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 3,7,11,15,19,23,27,31,35,39,43 | 583 | 98.926 / 98.791 / 72.080 | 1.088 / 0.793 | -0.295 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c4_p8k / `380cb5516b56` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 3,7,11,15,19,23,27,31,35,39,43 | 121 | 98.510 / 98.089 / 71.998 | 1.084 / 0.792 | -0.292 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3174 | 11.324 / 11.139 / 7.162 | 0.781 / 0.494 | -0.287 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 2829 | 11.318 / 11.126 / 7.162 | 0.781 / 0.494 | -0.287 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3332 | 11.331 / 11.164 / 7.175 | 0.771 / 0.488 | -0.283 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3196 | 11.325 / 11.134 / 7.175 | 0.770 / 0.488 | -0.282 | captured_layer_multiplicity_weighted_source_program_reference |
| a3_kimi4_tp8_w4a8_c64 / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 588 | 520.577 / 518.519 / 613.046 | 1.562 / 1.839 | 0.277 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3381 | 11.086 / 10.898 / 7.162 | 0.765 / 0.494 | -0.271 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3243 | 11.054 / 10.833 / 7.162 | 0.763 / 0.494 | -0.269 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3468 | 11.079 / 10.893 / 7.175 | 0.753 / 0.488 | -0.266 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-baseline / `20dbf57be438` | HcPre / attention.hc_pre / mla / attention | 6080 | 10.537 / 10.441 / 17.136 | 0.421 / 0.685 | 0.264 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime86-baseline / `20dbf57be438` | HcPre / attention.hc_pre / mla / attention | 5800 | 10.538 / 10.438 / 17.136 | 0.422 / 0.685 | 0.264 | partial_base_program_reference_premix_branch_unresolved |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3536 | 11.051 / 10.880 / 7.175 | 0.751 / 0.488 | -0.264 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3604 | 11.047 / 10.845 / 7.175 | 0.751 / 0.488 | -0.263 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3795 | 10.975 / 10.840 / 7.162 | 0.757 / 0.494 | -0.263 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3588 | 10.966 / 10.774 / 7.162 | 0.757 / 0.494 | -0.263 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3726 | 10.964 / 10.861 / 7.162 | 0.756 / 0.494 | -0.262 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3536 | 11.026 / 10.851 / 7.175 | 0.750 / 0.488 | -0.262 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime86-baseline / `20dbf57be438` | HcPre / attention.hc_pre / mla / attention | 6040 | 10.593 / 10.482 / 17.136 | 0.424 / 0.685 | 0.262 | partial_base_program_reference_premix_branch_unresolved |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3657 | 10.953 / 10.771 / 7.162 | 0.756 / 0.494 | -0.262 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3672 | 11.003 / 10.806 / 7.175 | 0.748 / 0.488 | -0.260 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3740 | 11.002 / 10.803 / 7.175 | 0.748 / 0.488 | -0.260 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime86-baseline / `20dbf57be438` | HcPre / ffn.hc_pre / mla / ffn | 5800 | 10.636 / 10.586 / 17.136 | 0.425 / 0.685 | 0.260 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-baseline / `20dbf57be438` | HcPre / ffn.hc_pre / mla / ffn | 6080 | 10.636 / 10.582 / 17.136 | 0.425 / 0.685 | 0.260 | partial_base_program_reference_premix_branch_unresolved |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 4012 | 10.993 / 10.806 / 7.175 | 0.747 / 0.488 | -0.260 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 4071 | 10.921 / 10.821 / 7.162 | 0.754 / 0.494 | -0.259 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 4071 | 10.920 / 10.808 / 7.162 | 0.754 / 0.494 | -0.259 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 4012 | 10.985 / 10.802 / 7.175 | 0.747 / 0.488 | -0.259 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime86-baseline / `20dbf57be438` | HcPre / ffn.hc_pre / mla / ffn | 6040 | 10.687 / 10.633 / 17.136 | 0.427 / 0.685 | 0.258 | partial_base_program_reference_premix_branch_unresolved |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3519 | 10.894 / 10.650 / 7.162 | 0.752 / 0.494 | -0.257 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62,64,65,66,68,69,70,72,73,74,76,77,78,80,81,82,84,85,86,88,89,90 | 3588 | 10.883 / 10.647 / 7.162 | 0.751 / 0.494 | -0.257 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 1824 | 6.519 / 6.452 / 1.312 | 0.313 / 0.063 | -0.250 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gdn / ffn | 2160 | 16.614 / 16.456 / 11.427 | 0.797 / 0.548 | -0.249 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / tp / gqa / ffn | 608 | 63.948 / 63.946 / 48.606 | 1.023 / 0.778 | -0.245 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime86-baseline / `20dbf57be438` | HcPre / attention.hc_pre / mla / attention | 5160 | 11.736 / 11.691 / 17.763 | 0.469 / 0.711 | 0.241 | partial_base_program_reference_premix_branch_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 2784 | 3.779 / 3.898 / 1.312 | 0.363 / 0.126 | -0.237 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime86-baseline / `20dbf57be438` | HcPre / ffn.hc_pre / mla / ffn | 5160 | 11.978 / 11.948 / 17.763 | 0.479 / 0.711 | 0.231 | partial_base_program_reference_premix_branch_unresolved |
| a3_kimi4_tp8_w4a8_c4 / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 738 | 103.723 / 103.598 / 175.598 | 0.311 / 0.527 | 0.216 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / `36284f768868` | InplacePartialRotaryMul / q_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 2920 | 6.680 / 6.330 / 1.312 | 0.267 / 0.052 | -0.215 | source_role_conditional_existing_semantic_program |
| glm53flash-a5-tp8-c1 / `fd8238dbb993` | SparseFlashMla / indexed_attention_batch / layers 3,7,11,15,19,23,27,31,35,39,43 | 715 | 51.517 / 51.481 / 32.272 | 0.567 / 0.355 | -0.212 | whole_batch_indexed_attention_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / `36284f768868` | InplacePartialRotaryMul / q_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 3000 | 6.454 / 6.206 / 1.312 | 0.258 / 0.052 | -0.206 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 1460 | 35.488 / 35.584 / 25.248 | 0.710 / 0.505 | -0.205 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / `36284f768868` | KvCompressEpilogV2 / kv_store / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 2920 | 6.379 / 6.304 / 1.312 | 0.255 / 0.052 | -0.203 | source_role_conditional_existing_semantic_program |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / tp / gdn / ffn | 3504 | 21.976 / 21.891 / 25.931 | 1.055 / 1.245 | 0.190 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 2304 | 5.123 / 5.125 / 1.312 | 0.246 / 0.063 | -0.183 | reference_only |
| a5_glm53flash_tp8_c4_p8k / `380cb5516b56` | RecurrentKda / kda_recurrent / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 374 | 14.290 / 13.915 / 8.936 | 0.486 / 0.304 | -0.182 | whole_batch_generic_gating_and_recurrent_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / `36284f768868` | KvCompressEpilogV2 / kv_store / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 3000 | 5.738 / 5.588 / 1.312 | 0.230 / 0.052 | -0.177 | source_role_conditional_existing_semantic_program |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | MlaPrologV3 / mla_prolog / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1176 | 34.540 / 34.478 / 41.881 | 0.829 / 1.005 | 0.176 | unfused_MLA_prolog_semantic_program_set_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | MlaPrologV3 / mla_prolog / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1128 | 34.559 / 34.513 / 41.881 | 0.829 / 1.005 | 0.176 | unfused_MLA_prolog_semantic_program_set_reference |
| glm53flash-a5-tp8-c3 / `380cb5516b56` | RecurrentKda / kda_recurrent / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 1802 | 14.053 / 13.812 / 8.936 | 0.478 / 0.304 | -0.174 | whole_batch_generic_gating_and_recurrent_reference |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / `36284f768868` | InplacePartialRotaryMul / q_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 4200 | 5.616 / 5.551 / 1.312 | 0.225 / 0.052 | -0.172 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / `36284f768868` | InplacePartialRotaryMul / output_inverse_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 2920 | 5.583 / 5.466 / 1.312 | 0.223 / 0.052 | -0.171 | source_role_conditional_existing_semantic_program |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 864 | 13.451 / 13.287 / 2.788 | 0.215 / 0.045 | -0.171 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 3040 | 10.067 / 10.133 / 1.578 | 0.201 / 0.032 | -0.170 | source_symbol_to_declared_attention_program |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 3648 | 3.075 / 2.886 / 1.312 | 0.295 / 0.126 | -0.169 | reference_only |
| a3_kimi4_tp8_w4a8_c32 / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 660 | 631.825 / 633.147 / 688.064 | 1.895 / 2.064 | 0.169 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 3020 | 9.938 / 9.948 / 1.578 | 0.199 / 0.032 | -0.167 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / `36284f768868` | InplacePartialRotaryMul / q_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 5160 | 5.459 / 5.383 / 1.312 | 0.218 / 0.052 | -0.166 | source_role_conditional_existing_semantic_program |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 2592 | 4.702 / 4.725 / 1.312 | 0.226 / 0.063 | -0.163 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / `36284f768868` | InplacePartialRotaryMul / q_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 6080 | 5.311 / 5.198 / 1.312 | 0.212 / 0.052 | -0.160 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / `36284f768868` | InplacePartialRotaryMul / q_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 5800 | 5.303 / 5.196 / 1.312 | 0.212 / 0.052 | -0.160 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / `36284f768868` | InplacePartialRotaryMul / q_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 6040 | 5.297 / 5.195 / 1.312 | 0.212 / 0.052 | -0.159 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 1314 | 34.016 / 33.648 / 25.248 | 0.612 / 0.454 | -0.158 | source_symbol_to_declared_attention_program |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | MlaPrologV3 / mla_prolog / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1224 | 33.425 / 33.389 / 39.861 | 0.802 / 0.957 | 0.154 | unfused_MLA_prolog_semantic_program_set_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | MlaPrologV3 / mla_prolog / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1248 | 33.437 / 33.377 / 39.861 | 0.802 / 0.957 | 0.154 | unfused_MLA_prolog_semantic_program_set_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / `36284f768868` | InplacePartialRotaryMul / output_inverse_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 3000 | 5.157 / 5.083 / 1.312 | 0.206 / 0.052 | -0.154 | source_role_conditional_existing_semantic_program |
| a3_kimi4_tp8_w4a8_c1 / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 762 | 38.730 / 39.539 / 89.061 | 0.116 / 0.267 | 0.151 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / `36284f768868` | InplacePartialRotaryMul / output_inverse_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 4200 | 5.043 / 4.974 / 1.312 | 0.202 / 0.052 | -0.149 | source_role_conditional_existing_semantic_program |
| glm53flash-a5-tp8-c1 / `fd8238dbb993` | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant / layers 3,7,11,15,19,23,27,31,35,39,43 | 715 | 33.521 / 33.389 / 19.967 | 0.369 / 0.220 | -0.149 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / `36284f768868` | InplacePartialRotaryMul / output_inverse_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 5160 | 5.026 / 4.973 / 1.312 | 0.201 / 0.052 | -0.149 | source_role_conditional_existing_semantic_program |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 4608 | 2.769 / 2.575 / 1.312 | 0.266 / 0.126 | -0.140 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / `36284f768868` | InplacePartialRotaryMul / output_inverse_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 5800 | 4.773 / 4.725 / 1.312 | 0.191 / 0.052 | -0.138 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / `36284f768868` | InplacePartialRotaryMul / output_inverse_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 6080 | 4.765 / 4.716 / 1.312 | 0.191 / 0.052 | -0.138 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / `36284f768868` | InplacePartialRotaryMul / output_inverse_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 6040 | 4.757 / 4.707 / 1.312 | 0.190 / 0.052 | -0.138 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 2736 | 9.205 / 9.201 / 1.578 | 0.166 / 0.028 | -0.137 | source_symbol_to_declared_attention_program |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 768 | 11.381 / 11.252 / 2.853 | 0.182 / 0.046 | -0.136 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 2718 | 9.116 / 9.153 / 1.578 | 0.164 / 0.028 | -0.136 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / `36284f768868` | KvCompressEpilogV2 / kv_store / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 4200 | 4.703 / 4.570 / 1.312 | 0.188 / 0.052 | -0.136 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / `36284f768868` | KvCompressEpilogV2 / kv_store / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 5800 | 4.511 / 3.954 / 1.312 | 0.180 / 0.052 | -0.128 | source_role_conditional_existing_semantic_program |
| a3_kimi4_tp8_w4a8_c32 / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 660 | 303.243 / 302.704 / 345.826 | 0.910 / 1.037 | 0.128 | capacity_vs_valid_rows_conditional |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 2160 | 3.803 / 3.768 / 1.312 | 0.183 / 0.063 | -0.120 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / `36284f768868` | KvCompressEpilogV2 / kv_store / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 5160 | 4.233 / 4.040 / 1.312 | 0.169 / 0.052 | -0.117 | source_role_conditional_existing_semantic_program |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 5184 | 2.429 / 2.287 / 1.312 | 0.233 / 0.126 | -0.107 | reference_only |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | MlaPrologV3 / mla_prolog / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1104 | 41.661 / 41.627 / 45.920 | 1.000 / 1.102 | 0.102 | unfused_MLA_prolog_semantic_program_set_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | MlaPrologV3 / mla_prolog / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 984 | 41.668 / 41.626 / 45.920 | 1.000 / 1.102 | 0.102 | unfused_MLA_prolog_semantic_program_set_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 984 | 11.616 / 11.372 / 7.392 | 0.279 / 0.177 | -0.101 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1104 | 11.613 / 11.369 / 7.392 | 0.279 / 0.177 | -0.101 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / `36284f768868` | InplacePartialRotaryMul / kv_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 3000 | 3.832 / 3.641 / 1.312 | 0.153 / 0.052 | -0.101 | source_role_conditional_existing_semantic_program |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 3504 | 3.375 / 3.333 / 1.312 | 0.162 / 0.063 | -0.099 | reference_only |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1128 | 11.433 / 11.139 / 7.392 | 0.274 / 0.177 | -0.097 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1176 | 11.413 / 11.108 / 7.392 | 0.274 / 0.177 | -0.097 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1104 | 11.257 / 10.904 / 7.392 | 0.270 / 0.177 | -0.093 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 984 | 11.249 / 10.905 / 7.392 | 0.270 / 0.177 | -0.093 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1224 | 11.208 / 10.861 / 7.392 | 0.269 / 0.177 | -0.092 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1248 | 11.194 / 11.036 / 7.392 | 0.269 / 0.177 | -0.091 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1272 | 11.182 / 11.025 / 7.392 | 0.268 / 0.177 | -0.091 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1248 | 11.182 / 10.823 / 7.392 | 0.268 / 0.177 | -0.091 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1416 | 11.161 / 10.780 / 7.392 | 0.268 / 0.177 | -0.090 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1416 | 11.160 / 10.762 / 7.392 | 0.268 / 0.177 | -0.090 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1320 | 11.126 / 11.057 / 7.392 | 0.267 / 0.177 | -0.090 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1296 | 11.121 / 10.787 / 7.392 | 0.267 / 0.177 | -0.089 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1296 | 11.119 / 11.070 / 7.392 | 0.267 / 0.177 | -0.089 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1320 | 11.112 / 10.777 / 7.392 | 0.267 / 0.177 | -0.089 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1416 | 11.104 / 10.939 / 7.392 | 0.266 / 0.177 | -0.089 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1416 | 11.103 / 10.914 / 7.392 | 0.266 / 0.177 | -0.089 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / `36284f768868` | InplacePartialRotaryMul / kv_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 2920 | 3.537 / 3.330 / 1.312 | 0.141 / 0.052 | -0.089 | source_role_conditional_existing_semantic_program |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1272 | 11.092 / 10.784 / 7.392 | 0.266 / 0.177 | -0.089 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1248 | 11.092 / 10.742 / 7.392 | 0.266 / 0.177 | -0.089 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1176 | 11.046 / 10.940 / 7.392 | 0.265 / 0.177 | -0.088 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1128 | 11.037 / 10.950 / 7.392 | 0.265 / 0.177 | -0.087 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1224 | 11.022 / 10.898 / 7.392 | 0.265 / 0.177 | -0.087 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | AttnResFwd / ffn.attn_res_fwd / layers 3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,92 | 1248 | 11.006 / 10.927 / 7.392 | 0.264 / 0.177 | -0.087 | captured_layer_multiplicity_weighted_source_program_reference |
| a5_glm53flash_tp8_c16_p4k / `380cb5516b56` | RecurrentKda / kda_recurrent / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 1020 | 25.355 / 25.107 / 27.872 | 0.862 / 0.948 | 0.086 | whole_batch_generic_gating_and_recurrent_reference |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp_attn / gqa / attention | 720 | 16.753 / 16.481 / 11.427 | 0.268 / 0.183 | -0.085 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gqa / ffn | 720 | 16.735 / 16.552 / 11.427 | 0.268 / 0.183 | -0.085 | reference_only |
| a5_glm53flash_tp8_c16_p8k / `380cb5516b56` | RecurrentKda / kda_recurrent / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 1088 | 25.509 / 25.294 / 27.872 | 0.867 / 0.948 | 0.080 | whole_batch_generic_gating_and_recurrent_reference |
| a3_kimi4_tp8_w4a8_c4 / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 738 | 62.615 / 62.999 / 89.061 | 0.188 / 0.267 | 0.079 | capacity_vs_valid_rows_conditional |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / tp / gdn / ffn | 2592 | 30.927 / 30.693 / 32.514 | 1.484 / 1.561 | 0.076 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 4320 | 2.102 / 2.072 / 1.312 | 0.202 / 0.126 | -0.076 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / `36284f768868` | KvCompressEpilogV2 / kv_store / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 6080 | 3.146 / 2.630 / 1.312 | 0.126 / 0.052 | -0.073 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / `36284f768868` | KvCompressEpilogV2 / kv_store / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 6040 | 3.131 / 2.598 / 1.312 | 0.125 / 0.052 | -0.073 | source_role_conditional_existing_semantic_program |
| a3_kimi4_tp8_w4a8_c16 / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_up / kda / ffn | 705 | 324.459 / 322.654 / 346.695 | 0.973 / 1.040 | 0.067 | capacity_vs_valid_rows_conditional |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / tp / gqa / ffn | 1168 | 21.989 / 21.956 / 25.931 | 0.352 / 0.415 | 0.063 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / `36284f768868` | InplacePartialRotaryMul / kv_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 4200 | 2.821 / 2.727 / 1.312 | 0.113 / 0.052 | -0.060 | source_role_conditional_existing_semantic_program |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 720 | 6.254 / 6.247 / 2.653 | 0.100 / 0.042 | -0.058 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / `36284f768868` | InplacePartialRotaryMul / kv_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 5800 | 2.687 / 2.515 / 1.312 | 0.107 / 0.052 | -0.055 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / `36284f768868` | InplacePartialRotaryMul / kv_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 5160 | 2.664 / 2.599 / 1.312 | 0.107 / 0.052 | -0.054 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / `36284f768868` | InplacePartialRotaryMul / kv_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 6080 | 2.652 / 2.506 / 1.312 | 0.106 / 0.052 | -0.054 | source_role_conditional_existing_semantic_program |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / tp_attn / gqa / attention | 864 | 35.826 / 35.657 / 32.514 | 0.573 / 0.520 | -0.053 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / `36284f768868` | InplacePartialRotaryMul / kv_rotary / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 6040 | 2.622 / 2.512 / 1.312 | 0.105 / 0.052 | -0.052 | source_role_conditional_existing_semantic_program |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 7008 | 1.817 / 1.841 / 1.312 | 0.174 / 0.126 | -0.049 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 1168 | 5.634 / 5.654 / 2.640 | 0.090 / 0.042 | -0.048 | reference_only |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 12,13,14 | 123 | 30.785 / 30.754 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 16,17,18 | 123 | 30.772 / 30.800 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 88,89,90 | 123 | 30.761 / 30.724 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 72,73,74 | 123 | 30.736 / 30.669 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 88,89,90 | 138 | 30.733 / 30.740 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 40,41,42 | 138 | 30.720 / 30.718 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 40,41,42 | 123 | 30.717 / 30.715 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 84,85,86 | 123 | 30.711 / 30.669 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 12,13,14 | 138 | 30.694 / 30.687 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 68,69,70 | 123 | 30.667 / 30.629 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 72,73,74 | 138 | 30.664 / 30.651 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 56,57,58 | 138 | 30.640 / 30.610 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 28,29,30 | 123 | 30.638 / 30.586 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 44,45,46 | 123 | 30.629 / 30.589 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 32,33,34 | 123 | 30.624 / 30.623 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 68,69,70 | 138 | 30.613 / 30.604 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 76,77,78 | 123 | 30.597 / 30.530 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 28,29,30 | 138 | 30.593 / 30.594 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 56,57,58 | 123 | 30.592 / 30.595 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 52,53,54 | 123 | 30.563 / 30.557 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 48,49,50 | 123 | 30.554 / 30.554 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 36,37,38 | 123 | 30.541 / 30.570 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 64,65,66 | 123 | 30.518 / 30.481 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 24,25,26 | 138 | 30.509 / 30.509 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 60,61,62 | 138 | 30.502 / 30.494 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 52,53,54 | 138 | 30.500 / 30.537 / 14.988 | 0.092 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 60,61,62 | 123 | 30.492 / 30.488 / 14.988 | 0.091 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 16,17,18 | 138 | 30.491 / 30.491 / 14.988 | 0.091 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 84,85,86 | 138 | 30.488 / 30.450 / 14.988 | 0.091 / 0.045 | -0.047 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 44,45,46 | 138 | 30.481 / 30.420 / 14.988 | 0.091 / 0.045 | -0.046 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 76,77,78 | 138 | 30.446 / 30.404 / 14.988 | 0.091 / 0.045 | -0.046 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 48,49,50 | 138 | 30.440 / 30.384 / 14.988 | 0.091 / 0.045 | -0.046 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 80,81,82 | 138 | 30.437 / 30.406 / 14.988 | 0.091 / 0.045 | -0.046 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 24,25,26 | 123 | 30.434 / 30.385 / 14.988 | 0.091 / 0.045 | -0.046 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 80,81,82 | 123 | 30.413 / 30.409 / 14.988 | 0.091 / 0.045 | -0.046 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 20,21,22 | 123 | 30.411 / 30.424 / 14.988 | 0.091 / 0.045 | -0.046 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 20,21,22 | 138 | 30.411 / 30.411 / 14.988 | 0.091 / 0.045 | -0.046 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 64,65,66 | 138 | 30.404 / 30.340 / 14.988 | 0.091 / 0.045 | -0.046 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 36,37,38 | 138 | 30.391 / 30.366 / 14.988 | 0.091 / 0.045 | -0.046 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 32,33,34 | 138 | 30.382 / 30.343 / 14.988 | 0.091 / 0.045 | -0.046 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 4,5,6 | 123 | 30.269 / 30.254 / 14.988 | 0.091 / 0.045 | -0.046 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 8,9,10 | 123 | 30.146 / 30.147 / 14.988 | 0.090 / 0.045 | -0.045 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 4,5,6 | 138 | 30.097 / 30.094 / 14.988 | 0.090 / 0.045 | -0.045 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2 | 123 | 30.097 / 30.093 / 14.988 | 0.090 / 0.045 | -0.045 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2 | 138 | 29.985 / 29.980 / 14.988 | 0.090 / 0.045 | -0.045 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 8,9,10 | 138 | 29.984 / 29.995 / 14.988 | 0.090 / 0.045 | -0.045 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_glm53flash_tp8_c8_p4k / `380cb5516b56` | RecurrentKda / kda_recurrent / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 1020 | 16.455 / 16.289 / 15.248 | 0.559 / 0.518 | -0.041 | whole_batch_generic_gating_and_recurrent_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 24,25,26 | 141 | 20.874 / 20.836 / 7.494 | 0.063 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 76,77,78 | 141 | 20.750 / 20.728 / 7.494 | 0.062 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 80,81,82 | 141 | 20.729 / 20.712 / 7.494 | 0.062 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 28,29,30 | 147 | 20.707 / 20.665 / 7.494 | 0.062 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 64,65,66 | 141 | 20.701 / 20.692 / 7.494 | 0.062 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 20,21,22 | 141 | 20.697 / 20.674 / 7.494 | 0.062 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 12,13,14 | 141 | 20.693 / 20.702 / 7.494 | 0.062 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 60,61,62 | 141 | 20.690 / 20.663 / 7.494 | 0.062 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 16,17,18 | 141 | 20.689 / 20.581 / 7.494 | 0.062 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 76,77,78 | 147 | 20.686 / 20.632 / 7.494 | 0.062 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 36,37,38 | 141 | 20.682 / 20.687 / 7.494 | 0.062 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 52,53,54 | 141 | 20.678 / 20.675 / 7.494 | 0.062 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 48,49,50 | 141 | 20.665 / 20.665 / 7.494 | 0.062 / 0.022 | -0.040 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 88,89,90 | 147 | 20.656 / 20.658 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 56,57,58 | 147 | 20.644 / 20.602 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 24,25,26 | 147 | 20.631 / 20.609 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 32,33,34 | 141 | 20.625 / 20.621 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 68,69,70 | 141 | 20.621 / 20.611 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 72,73,74 | 147 | 20.594 / 20.579 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 40,41,42 | 147 | 20.594 / 20.552 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 88,89,90 | 141 | 20.592 / 20.555 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 56,57,58 | 141 | 20.564 / 20.527 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 72,73,74 | 141 | 20.559 / 20.558 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 36,37,38 | 147 | 20.556 / 20.537 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 52,53,54 | 147 | 20.555 / 20.577 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 64,65,66 | 147 | 20.555 / 20.549 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 12,13,14 | 147 | 20.543 / 20.539 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 28,29,30 | 141 | 20.541 / 20.466 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 16,17,18 | 147 | 20.539 / 20.489 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 84,85,86 | 141 | 20.515 / 20.490 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 32,33,34 | 147 | 20.513 / 20.496 / 7.494 | 0.062 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 44,45,46 | 147 | 20.499 / 20.478 / 7.494 | 0.061 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 60,61,62 | 147 | 20.498 / 20.483 / 7.494 | 0.061 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 20,21,22 | 147 | 20.496 / 20.459 / 7.494 | 0.061 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 40,41,42 | 141 | 20.480 / 20.457 / 7.494 | 0.061 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 84,85,86 | 147 | 20.479 / 20.484 / 7.494 | 0.061 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 48,49,50 | 147 | 20.468 / 20.480 / 7.494 | 0.061 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 80,81,82 | 147 | 20.463 / 20.419 / 7.494 | 0.061 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 68,69,70 | 147 | 20.458 / 20.393 / 7.494 | 0.061 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 44,45,46 | 141 | 20.399 / 20.387 / 7.494 | 0.061 / 0.022 | -0.039 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 4,5,6 | 141 | 20.199 / 20.186 / 7.494 | 0.061 / 0.022 | -0.038 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 8,9,10 | 141 | 20.136 / 20.158 / 7.494 | 0.060 / 0.022 | -0.038 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 4,5,6 | 147 | 20.105 / 20.153 / 7.494 | 0.060 / 0.022 | -0.038 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 8,9,10 | 147 | 20.085 / 20.070 / 7.494 | 0.060 / 0.022 | -0.038 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2 | 141 | 19.925 / 19.942 / 7.494 | 0.060 / 0.022 | -0.037 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2 | 147 | 19.771 / 19.778 / 7.494 | 0.059 / 0.022 | -0.037 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 48,49,50 | 153 | 15.847 / 15.927 / 4.704 | 0.048 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 28,29,30 | 153 | 15.821 / 15.800 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 52,53,54 | 153 | 15.818 / 15.787 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 24,25,26 | 156 | 15.817 / 15.749 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 56,57,58 | 153 | 15.790 / 15.744 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 16,17,18 | 153 | 15.772 / 15.744 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 44,45,46 | 153 | 15.764 / 15.749 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 24,25,26 | 153 | 15.762 / 15.679 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 32,33,34 | 153 | 15.746 / 15.710 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 28,29,30 | 156 | 15.722 / 15.629 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 84,85,86 | 153 | 15.715 / 15.666 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 64,65,66 | 153 | 15.710 / 15.720 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 12,13,14 | 153 | 15.664 / 15.652 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 80,81,82 | 153 | 15.654 / 15.640 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 20,21,22 | 153 | 15.649 / 15.633 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 60,61,62 | 153 | 15.646 / 15.636 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 48,49,50 | 156 | 15.624 / 15.561 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 20,21,22 | 156 | 15.616 / 15.604 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 52,53,54 | 156 | 15.612 / 15.527 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 56,57,58 | 156 | 15.606 / 15.565 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 84,85,86 | 156 | 15.590 / 15.527 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 76,77,78 | 153 | 15.579 / 15.552 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 16,17,18 | 156 | 15.564 / 15.560 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 68,69,70 | 153 | 15.556 / 15.554 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 68,69,70 | 156 | 15.555 / 15.497 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 64,65,66 | 156 | 15.549 / 15.493 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 44,45,46 | 156 | 15.545 / 15.518 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 32,33,34 | 156 | 15.538 / 15.434 / 4.704 | 0.047 / 0.014 | -0.033 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 80,81,82 | 156 | 15.519 / 15.519 / 4.704 | 0.047 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 36,37,38 | 153 | 15.518 / 15.505 / 4.704 | 0.047 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 40,41,42 | 156 | 15.511 / 15.473 / 4.704 | 0.047 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 36,37,38 | 156 | 15.507 / 15.512 / 4.704 | 0.047 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 60,61,62 | 156 | 15.507 / 15.482 / 4.704 | 0.047 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 40,41,42 | 153 | 15.500 / 15.469 / 4.704 | 0.046 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 76,77,78 | 156 | 15.474 / 15.459 / 4.704 | 0.046 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 88,89,90 | 156 | 15.472 / 15.464 / 4.704 | 0.046 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 88,89,90 | 153 | 15.469 / 15.451 / 4.704 | 0.046 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 72,73,74 | 156 | 15.440 / 15.389 / 4.704 | 0.046 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 72,73,74 | 153 | 15.402 / 15.383 / 4.704 | 0.046 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 12,13,14 | 156 | 15.356 / 15.341 / 4.704 | 0.046 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 4,5,6 | 153 | 15.270 / 15.225 / 4.704 | 0.046 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 4,5,6 | 156 | 15.262 / 15.156 / 4.704 | 0.046 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 8,9,10 | 153 | 15.224 / 15.184 / 4.704 | 0.046 / 0.014 | -0.032 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 8,9,10 | 156 | 15.094 / 15.081 / 4.704 | 0.045 / 0.014 | -0.031 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2 | 153 | 15.050 / 15.012 / 4.704 | 0.045 / 0.014 | -0.031 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / tp / gqa / ffn | 864 | 30.577 / 30.497 / 32.514 | 0.489 / 0.520 | 0.031 | reference_only |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2 | 156 | 14.983 / 14.934 / 4.704 | 0.045 / 0.014 | -0.031 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 20,21,22 | 159 | 12.061 / 11.996 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 80,81,82 | 159 | 12.011 / 12.002 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 56,57,58 | 159 | 11.996 / 11.979 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 16,17,18 | 156 | 11.994 / 11.982 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 12,13,14 | 159 | 11.986 / 11.962 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 16,17,18 | 159 | 11.977 / 11.966 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 20,21,22 | 156 | 11.971 / 11.927 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 76,77,78 | 156 | 11.964 / 11.952 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 68,69,70 | 159 | 11.957 / 11.937 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 40,41,42 | 159 | 11.956 / 11.951 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 24,25,26 | 159 | 11.952 / 11.937 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 52,53,54 | 156 | 11.948 / 11.899 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 76,77,78 | 159 | 11.941 / 11.924 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 60,61,62 | 159 | 11.937 / 11.939 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 32,33,34 | 159 | 11.937 / 11.955 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 56,57,58 | 156 | 11.937 / 11.924 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 68,69,70 | 156 | 11.936 / 11.919 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 80,81,82 | 156 | 11.930 / 11.918 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 52,53,54 | 159 | 11.926 / 11.898 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 28,29,30 | 159 | 11.925 / 11.947 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 64,65,66 | 159 | 11.910 / 11.896 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 60,61,62 | 156 | 11.900 / 11.900 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 44,45,46 | 159 | 11.889 / 11.887 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 12,13,14 | 156 | 11.887 / 11.873 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 24,25,26 | 156 | 11.882 / 11.889 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 72,73,74 | 159 | 11.880 / 11.851 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 88,89,90 | 159 | 11.875 / 11.845 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 36,37,38 | 159 | 11.873 / 11.864 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 84,85,86 | 159 | 11.859 / 11.853 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 40,41,42 | 156 | 11.859 / 11.843 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 36,37,38 | 156 | 11.858 / 11.883 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 48,49,50 | 159 | 11.855 / 11.844 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 64,65,66 | 156 | 11.855 / 11.874 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 28,29,30 | 156 | 11.843 / 11.850 / 2.337 | 0.036 / 0.007 | -0.029 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 72,73,74 | 156 | 11.837 / 11.820 / 2.337 | 0.036 / 0.007 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2 | 159 | 11.830 / 11.826 / 2.337 | 0.035 / 0.007 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 32,33,34 | 156 | 11.828 / 11.822 / 2.337 | 0.035 / 0.007 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 8,9,10 | 159 | 11.798 / 11.796 / 2.337 | 0.035 / 0.007 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 4,5,6 | 159 | 11.794 / 11.783 / 2.337 | 0.035 / 0.007 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 44,45,46 | 156 | 11.789 / 11.762 / 2.337 | 0.035 / 0.007 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 84,85,86 | 156 | 11.785 / 11.792 / 2.337 | 0.035 / 0.007 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 48,49,50 | 156 | 11.767 / 11.778 / 2.337 | 0.035 / 0.007 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2 | 156 | 11.764 / 11.767 / 2.337 | 0.035 / 0.007 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 8,9,10 | 156 | 11.756 / 11.774 / 2.337 | 0.035 / 0.007 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 88,89,90 | 156 | 11.730 / 11.698 / 2.337 | 0.035 / 0.007 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 4,5,6 | 156 | 11.715 / 11.729 / 2.337 | 0.035 / 0.007 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 24,25,26 | 165 | 11.400 / 11.398 / 2.140 | 0.034 / 0.006 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 80,81,82 | 165 | 11.393 / 11.386 / 2.140 | 0.034 / 0.006 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 28,29,30 | 165 | 11.390 / 11.375 / 2.140 | 0.034 / 0.006 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 32,33,34 | 165 | 11.383 / 11.361 / 2.140 | 0.034 / 0.006 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 48,49,50 | 165 | 11.370 / 11.369 / 2.140 | 0.034 / 0.006 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 76,77,78 | 165 | 11.367 / 11.373 / 2.140 | 0.034 / 0.006 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 12,13,14 | 165 | 11.365 / 11.352 / 2.140 | 0.034 / 0.006 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 56,57,58 | 165 | 11.333 / 11.322 / 2.140 | 0.034 / 0.006 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 68,69,70 | 165 | 11.329 / 11.329 / 2.140 | 0.034 / 0.006 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 64,65,66 | 165 | 11.324 / 11.354 / 2.140 | 0.034 / 0.006 | -0.028 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / `36284f768868` | InplacePartialRotaryMul / index_query_rotary / layers 2,8,14,20,24,28,32,36 | 584 | 4.737 / 4.699 / 1.312 | 0.038 / 0.010 | -0.027 | source_role_conditional_existing_semantic_program |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 44,45,46 | 165 | 11.254 / 11.232 / 2.140 | 0.034 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 16,17,18 | 165 | 11.247 / 11.267 / 2.140 | 0.034 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 8,9,10 | 165 | 11.242 / 11.255 / 2.140 | 0.034 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 20,21,22 | 165 | 11.235 / 11.208 / 2.140 | 0.034 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 84,85,86 | 165 | 11.203 / 11.218 / 2.140 | 0.034 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 24,25,26 | 162 | 11.176 / 11.177 / 2.140 | 0.034 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 28,29,30 | 162 | 11.175 / 11.133 / 2.140 | 0.034 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 4,5,6 | 165 | 11.166 / 11.167 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 48,49,50 | 162 | 11.161 / 11.152 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 80,81,82 | 162 | 11.161 / 11.161 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / tp_attn / gqa / attention | 1168 | 24.240 / 23.529 / 25.931 | 0.388 / 0.415 | 0.027 | reference_only |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 32,33,34 | 162 | 11.137 / 11.131 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2 | 165 | 11.137 / 11.148 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 72,73,74 | 165 | 11.132 / 11.228 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 60,61,62 | 165 | 11.128 / 11.300 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 20,21,22 | 162 | 11.123 / 11.088 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 76,77,78 | 162 | 11.118 / 11.127 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 12,13,14 | 162 | 11.109 / 11.096 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 52,53,54 | 165 | 11.086 / 11.238 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 88,89,90 | 165 | 11.060 / 11.184 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 56,57,58 | 162 | 11.047 / 11.059 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 36,37,38 | 165 | 11.017 / 11.188 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 68,69,70 | 162 | 11.014 / 11.057 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 64,65,66 | 162 | 11.012 / 11.027 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 8,9,10 | 162 | 11.000 / 11.030 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 16,17,18 | 162 | 10.992 / 11.027 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 40,41,42 | 165 | 10.984 / 11.163 / 2.140 | 0.033 / 0.006 | -0.027 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 4,5,6 | 162 | 10.963 / 10.944 / 2.140 | 0.033 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2 | 162 | 10.950 / 10.923 / 2.140 | 0.033 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 32,33,34 | 177 | 10.898 / 10.900 / 2.098 | 0.033 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 44,45,46 | 162 | 10.939 / 10.978 / 2.140 | 0.033 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 48,49,50 | 177 | 10.892 / 10.863 / 2.098 | 0.033 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 12,13,14 | 177 | 10.847 / 10.817 / 2.098 | 0.033 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 56,57,58 | 177 | 10.839 / 10.887 / 2.098 | 0.033 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 72,73,74 | 162 | 10.873 / 10.934 / 2.140 | 0.033 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 32,33,34 | 177 | 10.828 / 10.813 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 84,85,86 | 162 | 10.866 / 10.966 / 2.140 | 0.033 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / `36284f768868` | InplacePartialRotaryMul / index_query_rotary / layers 2,8,14,20,24,28,32,36 | 600 | 4.584 / 4.566 / 1.312 | 0.037 / 0.010 | -0.026 | source_role_conditional_existing_semantic_program |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 48,49,50 | 177 | 10.815 / 10.823 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 24,25,26 | 177 | 10.800 / 10.802 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 12,13,14 | 177 | 10.796 / 10.817 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 24,25,26 | 177 | 10.791 / 10.809 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 56,57,58 | 177 | 10.771 / 10.795 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 28,29,30 | 177 | 10.766 / 10.742 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 60,61,62 | 162 | 10.808 / 10.985 / 2.140 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 52,53,54 | 162 | 10.808 / 10.979 / 2.140 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 44,45,46 | 177 | 10.763 / 10.766 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 88,89,90 | 162 | 10.804 / 10.943 / 2.140 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 16,17,18 | 177 | 10.751 / 10.767 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 64,65,66 | 177 | 10.745 / 10.733 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 20,21,22 | 177 | 10.744 / 10.740 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 36,37,38 | 162 | 10.780 / 10.957 / 2.140 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 44,45,46 | 177 | 10.736 / 10.715 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 76,77,78 | 177 | 10.727 / 10.711 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 8,9,10 | 177 | 10.724 / 10.772 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 40,41,42 | 162 | 10.761 / 10.938 / 2.140 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 80,81,82 | 177 | 10.719 / 10.699 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 16,17,18 | 177 | 10.703 / 10.714 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 20,21,22 | 177 | 10.695 / 10.706 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 68,69,70 | 177 | 10.693 / 10.685 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 80,81,82 | 177 | 10.689 / 10.644 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 28,29,30 | 177 | 10.684 / 10.655 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 76,77,78 | 177 | 10.679 / 10.663 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 64,65,66 | 177 | 10.678 / 10.676 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 8,9,10 | 177 | 10.672 / 10.750 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2 | 177 | 10.651 / 10.637 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 4,5,6 | 177 | 10.650 / 10.644 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 68,69,70 | 177 | 10.637 / 10.643 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 4,5,6 | 177 | 10.624 / 10.658 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 72,73,74 | 177 | 10.617 / 10.623 / 2.098 | 0.032 / 0.006 | -0.026 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 0,1,2 | 177 | 10.593 / 10.587 / 2.098 | 0.032 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 72,73,74 | 177 | 10.584 / 10.651 / 2.098 | 0.032 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 40,41,42 | 177 | 10.577 / 10.726 / 2.098 | 0.032 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 88,89,90 | 177 | 10.569 / 10.658 / 2.098 | 0.032 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 36,37,38 | 177 | 10.561 / 10.712 / 2.098 | 0.032 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 52,53,54 | 177 | 10.552 / 10.663 / 2.098 | 0.032 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 40,41,42 | 177 | 10.539 / 10.727 / 2.098 | 0.032 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 60,61,62 | 177 | 10.531 / 10.661 / 2.098 | 0.032 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 88,89,90 | 177 | 10.517 / 10.582 / 2.098 | 0.032 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 60,61,62 | 177 | 10.513 / 10.666 / 2.098 | 0.032 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 52,53,54 | 177 | 10.505 / 10.626 / 2.098 | 0.032 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 84,85,86 | 177 | 10.498 / 10.580 / 2.098 | 0.031 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 84,85,86 | 177 | 10.486 / 10.554 / 2.098 | 0.031 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | RecurrentKda / kda_recurrent / layers 36,37,38 | 177 | 10.476 / 10.630 / 2.098 | 0.031 / 0.006 | -0.025 | complete_kda_semantic_program_set_no_accepted_array_reference |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / `36284f768868` | InplacePartialRotaryMul / index_query_rotary / layers 2,8,14,20,24,28,32,36 | 840 | 4.406 / 4.405 / 1.312 | 0.035 / 0.010 | -0.025 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / `36284f768868` | InplacePartialRotaryMul / index_query_rotary / layers 2,8,14,20,24,28,32,36 | 1032 | 4.371 / 4.362 / 1.312 | 0.035 / 0.010 | -0.024 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 290 | 11.092 / 11.153 / 1.578 | 0.022 / 0.003 | -0.019 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 258 | 11.257 / 11.309 / 3.156 | 0.023 / 0.006 | -0.016 | source_symbol_to_declared_attention_program |
| a3_kimi4_tp8_w4a8_c16 / source18c423c7 / `fd8238dbb993` | GroupedMatmul / expert_down / kda / ffn | 705 | 168.962 / 167.496 / 174.251 | 0.507 / 0.523 | 0.016 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 210 | 13.400 / 12.342 / 6.312 | 0.027 / 0.013 | -0.014 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 304 | 8.170 / 8.110 / 1.578 | 0.016 / 0.003 | -0.013 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 302 | 7.891 / 7.845 / 1.578 | 0.016 / 0.003 | -0.013 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / `36284f768868` | InplacePartialRotaryMul / index_query_rotary / layers 2,8,14,20,24,28,32,36 | 1216 | 2.861 / 2.855 / 1.312 | 0.023 / 0.010 | -0.012 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / `36284f768868` | InplacePartialRotaryMul / index_query_rotary / layers 2,8,14,20,24,28,32,36 | 1160 | 2.859 / 2.851 / 1.312 | 0.023 / 0.010 | -0.012 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / `36284f768868` | InplacePartialRotaryMul / index_query_rotary / layers 2,8,14,20,24,28,32,36 | 1208 | 2.844 / 2.835 / 1.312 | 0.023 / 0.010 | -0.012 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 146 | 19.397 / 12.614 / 25.248 | 0.039 / 0.050 | 0.012 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 2,8,14 | 225 | 3.584 / 3.587 / 0.000 | 0.011 / 0.000 | -0.011 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 2,8,14 | 219 | 3.535 / 3.529 / 0.000 | 0.011 / 0.000 | -0.011 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 2,8,14 | 219 | 3.107 / 3.102 / 0.000 | 0.009 / 0.000 | -0.009 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 2,8,14 | 225 | 3.010 / 3.028 / 0.000 | 0.009 / 0.000 | -0.009 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 2,8,14 | 435 | 2.968 / 3.017 / 0.000 | 0.009 / 0.000 | -0.009 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 2,8,14 | 315 | 2.963 / 2.970 / 0.000 | 0.009 / 0.000 | -0.009 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 2,8,14 | 387 | 2.960 / 2.967 / 0.000 | 0.009 / 0.000 | -0.009 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 2,8,14 | 219 | 2.753 / 2.713 / 0.000 | 0.008 / 0.000 | -0.008 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 2,8,14 | 456 | 2.701 / 2.653 / 0.000 | 0.008 / 0.000 | -0.008 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 2,8,14 | 453 | 2.585 / 2.620 / 0.000 | 0.008 / 0.000 | -0.008 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 2,8,14 | 387 | 2.573 / 2.499 / 0.000 | 0.008 / 0.000 | -0.008 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 2,8,14 | 225 | 2.532 / 2.466 / 0.000 | 0.008 / 0.000 | -0.008 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 2,8,14 | 315 | 2.458 / 2.374 / 0.000 | 0.007 / 0.000 | -0.007 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 2,8,14 | 435 | 2.360 / 2.339 / 0.000 | 0.007 / 0.000 | -0.007 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 2,8,14 | 456 | 2.359 / 2.344 / 0.000 | 0.007 / 0.000 | -0.007 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 2,8,14 | 315 | 2.339 / 2.335 / 0.000 | 0.007 / 0.000 | -0.007 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 2,8,14 | 453 | 2.263 / 2.308 / 0.000 | 0.007 / 0.000 | -0.007 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime86-baseline / `20dbf57be438` | MqsmlaKernel___call__ / attention_core / mla / attention | 150 | 16.005 / 12.507 / 12.624 | 0.032 / 0.025 | -0.007 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 2,8,14 | 387 | 2.248 / 2.241 / 0.000 | 0.007 / 0.000 | -0.007 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 2,8,14 | 453 | 2.228 / 2.252 / 0.000 | 0.007 / 0.000 | -0.007 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 2,8,14 | 456 | 2.157 / 2.055 / 0.000 | 0.006 / 0.000 | -0.006 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 2,8,14 | 435 | 2.147 / 2.051 / 0.000 | 0.006 / 0.000 | -0.006 | source_role_conditional_existing_semantic_program |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | AttnResFwd / final.attn_res_fwd / layers 92 | 46 | 14.067 / 13.955 / 10.522 | 0.014 / 0.011 | -0.004 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | AttnResFwd / final.attn_res_fwd / layers 92 | 41 | 14.057 / 14.058 / 10.522 | 0.014 / 0.011 | -0.004 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | AttnResFwd / final.attn_res_fwd / layers 92 | 51 | 13.853 / 13.784 / 10.522 | 0.014 / 0.011 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | AttnResFwd / final.attn_res_fwd / layers 92 | 47 | 13.810 / 13.788 / 10.522 | 0.014 / 0.011 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c16_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 0 | 47 | 4.577 / 4.570 / 1.312 | 0.005 / 0.001 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 0 | 49 | 4.573 / 4.549 / 1.312 | 0.005 / 0.001 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c16_p4k / `fd8238dbb993` | AttnResFwd / final.attn_res_fwd / layers 92 | 49 | 13.771 / 13.753 / 10.522 | 0.014 / 0.011 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | AttnResFwd / final.attn_res_fwd / layers 92 | 52 | 13.758 / 13.706 / 10.522 | 0.014 / 0.011 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c32_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 0 | 46 | 4.379 / 4.317 / 1.312 | 0.004 / 0.001 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c32_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 0 | 41 | 4.364 / 4.330 / 1.312 | 0.004 / 0.001 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | AttnResFwd / final.attn_res_fwd / layers 92 | 59 | 13.428 / 13.392 / 10.522 | 0.013 / 0.011 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | AttnResFwd / final.attn_res_fwd / layers 92 | 52 | 13.412 / 13.386 / 10.522 | 0.013 / 0.011 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | AttnResFwd / final.attn_res_fwd / layers 92 | 59 | 13.401 / 13.366 / 10.522 | 0.013 / 0.011 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 0 | 54 | 4.189 / 4.192 / 1.312 | 0.004 / 0.001 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c2_p16k / `fd8238dbb993` | AttnResFwd / final.attn_res_fwd / layers 92 | 54 | 13.399 / 13.389 / 10.522 | 0.013 / 0.011 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | AttnResFwd / final.attn_res_fwd / layers 92 | 55 | 13.395 / 13.350 / 10.522 | 0.013 / 0.011 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c2_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 0 | 55 | 4.172 / 4.177 / 1.312 | 0.004 / 0.001 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | AttnResFwd / final.attn_res_fwd / layers 92 | 53 | 13.350 / 13.323 / 10.522 | 0.013 / 0.011 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c8_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 0 | 51 | 4.035 / 4.018 / 1.312 | 0.004 / 0.001 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c8_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 0 | 52 | 4.025 / 4.010 / 1.312 | 0.004 / 0.001 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c1_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 0 | 59 | 3.893 / 3.865 / 1.312 | 0.004 / 0.001 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c1_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 0 | 59 | 3.882 / 3.874 / 1.312 | 0.004 / 0.001 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c4_p4k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 0 | 53 | 3.819 / 3.812 / 1.312 | 0.004 / 0.001 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_kimi_tp8_e16_bf16_c4_p16k / `fd8238dbb993` | AttnResFwd / attention.attn_res_fwd / layers 0 | 52 | 3.815 / 3.801 / 1.312 | 0.004 / 0.001 | -0.003 | whole_source_AttnResFwd_point_with_topology_declared_flags |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 20 | 73 | 3.548 / 3.509 / 1.312 | 0.004 / 0.001 | -0.002 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 20 | 75 | 3.270 / 3.340 / 1.312 | 0.003 / 0.001 | -0.002 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 20 | 145 | 3.171 / 3.140 / 1.312 | 0.003 / 0.001 | -0.002 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 20 | 129 | 3.086 / 3.075 / 1.312 | 0.003 / 0.001 | -0.002 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 20 | 105 | 3.084 / 3.048 / 1.312 | 0.003 / 0.001 | -0.002 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 20 | 151 | 2.731 / 2.694 / 1.312 | 0.003 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 20 | 73 | 2.721 / 2.706 / 1.312 | 0.003 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 20 | 73 | 2.677 / 2.675 / 1.312 | 0.003 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / `36284f768868` | KvCompressEpilogV2 / compressed_store / layers 20 | 152 | 2.655 / 2.592 / 1.312 | 0.003 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 20 | 75 | 2.448 / 2.440 / 1.312 | 0.002 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 20 | 75 | 2.376 / 2.370 / 1.312 | 0.002 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 20 | 151 | 2.346 / 2.335 / 1.312 | 0.002 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 20 | 151 | 2.333 / 2.319 / 1.312 | 0.002 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 20 | 105 | 2.320 / 2.318 / 1.312 | 0.002 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 20 | 105 | 2.304 / 2.284 / 1.312 | 0.002 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 20 | 129 | 2.264 / 2.270 / 1.312 | 0.002 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 20 | 129 | 2.246 / 2.252 / 1.312 | 0.002 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 20 | 152 | 2.079 / 2.064 / 1.312 | 0.002 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / `36284f768868` | InplacePartialRotaryMul / index_rotary / layers 20 | 145 | 2.076 / 2.058 / 1.312 | 0.002 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 20 | 152 | 2.074 / 2.059 / 1.312 | 0.002 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / `36284f768868` | InplacePartialRotaryMul / compress_rotary / layers 20 | 145 | 2.066 / 2.050 / 1.312 | 0.002 / 0.001 | -0.001 | source_role_conditional_existing_semantic_program |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | DynamicQuantV2 /  / gdn / attention | 1824 | 7.494 / 7.449 / — | 0.360 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gdn / ffn | 1824 | 15.340 / 15.292 / — | 0.736 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | DynamicQuantV2 /  / gdn / ffn | 1824 | 6.140 / 6.110 / — | 0.295 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | AddRmsNorm /  / gdn / attention | 1786 | 8.789 / 8.765 / — | 0.413 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gqa / attention | 608 | 12.148 / 12.114 / — | 0.194 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | DynamicQuantV2 /  / gqa / attention | 608 | 5.567 / 5.550 / — | 0.089 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gqa / ffn | 608 | 12.621 / 12.596 / — | 0.202 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | DynamicQuantV2 /  / gqa / ffn | 608 | 5.743 / 5.690 / — | 0.092 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | DynamicQuantV2 /  / gdn / attention | 3504 | 4.049 / 4.054 / — | 0.194 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gdn / ffn | 3504 | 5.429 / 5.430 / — | 0.261 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | DynamicQuantV2 /  / gdn / ffn | 3504 | 3.877 / 3.882 / — | 0.186 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | AddRmsNorm /  / gdn / attention | 3431 | 4.089 / 4.093 / — | 0.192 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gqa / attention | 1168 | 5.434 / 5.439 / — | 0.087 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | DynamicQuantV2 /  / gqa / attention | 1168 | 3.762 / 3.776 / — | 0.060 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gqa / ffn | 1168 | 5.422 / 5.454 / — | 0.087 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | DynamicQuantV2 /  / gqa / ffn | 1168 | 3.911 / 3.914 / — | 0.063 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | DynamicQuantV2 /  / gdn / attention | 2592 | 6.016 / 5.927 / — | 0.289 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gdn / ffn | 2592 | 9.468 / 9.434 / — | 0.454 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | DynamicQuantV2 /  / gdn / ffn | 2592 | 5.528 / 5.531 / — | 0.265 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | AddRmsNorm /  / gdn / attention | 2538 | 6.297 / 6.301 / — | 0.296 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gqa / attention | 864 | 8.251 / 8.233 / — | 0.132 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | DynamicQuantV2 /  / gqa / attention | 864 | 4.893 / 4.841 / — | 0.078 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gqa / ffn | 864 | 8.525 / 8.493 / — | 0.136 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | DynamicQuantV2 /  / gqa / ffn | 864 | 5.228 / 5.178 / — | 0.084 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gdn / ffn | 1392 | 14.009 / 13.983 / — | 0.672 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | AddRmsNorm /  / gdn / attention | 1363 | 9.873 / 9.845 / — | 0.464 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gqa / attention | 464 | 12.301 / 12.283 / — | 0.197 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gqa / ffn | 464 | 12.340 / 12.348 / — | 0.197 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gdn / ffn | 2304 | 7.733 / 7.718 / — | 0.371 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | AddRmsNorm /  / gdn / attention | 2256 | 5.956 / 5.947 / — | 0.280 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gqa / attention | 768 | 7.146 / 7.104 / — | 0.114 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gqa / ffn | 768 | 7.275 / 7.274 / — | 0.116 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gdn / ffn | 2160 | 4.405 / 4.322 / — | 0.211 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | AddRmsNorm /  / gdn / attention | 2115 | 4.302 / 4.266 / — | 0.202 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gqa / attention | 720 | 4.180 / 4.136 / — | 0.067 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gqa / ffn | 720 | 4.141 / 4.130 / — | 0.066 / — | — | boundary_unresolved |

## Receipt identities

- [prediction-input-binding-invalidation.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-variants/prediction-input-binding-invalidation.json), SHA256 `d712525f017419c50bae6d882511fe12141e40faee0083ef6db47b119135477f`
- [decode-forward-priority-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-priority-replay.json), SHA256 `dc6d63fe09130151285b50390ccc53136dee834959de127c39e0337018c8d912`
- [decode-forward-second-wave-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-second-wave-replay.json), SHA256 `574bd3ac3b05bded807b10c34d91933c170bb66fbe88eeb301b4b93ef92111c6`
- [decode-forward-kimi-checkpoint-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-kimi-checkpoint-replay.json), SHA256 `f6e82a724d94250f1db854587fcfaf9ca0296c2596c0bcb00cc0525331f42429`
- [decode-forward-system-fix-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-system-fix-replay.json), SHA256 `1cf66ae57bb9e7603c248c4c1a4810e7f2c5610e480333c91e4487becb6617fc`
- [decode-forward-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm78-v41/decode-forward-replay.json), SHA256 `c05015ddbd7e42c0bf907c6eed83723ea232632d21d68ce94383ca8984d76296`
- [decode-forward-glm-runtime-controls-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-glm-runtime-controls-replay.json), SHA256 `56a171a8f6373f450dfd8ac191cc0c5a564aa10943bdc07f413285c9f057a757`
- [decode-forward-qwen397-join-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-qwen397-join-replay.json), SHA256 `2ec24d3aaa8ffc0cbfcd97ab8a75c45e5844ef3ccbc0c574be83258d59da53d3`
- [decode-forward-v41-dp8-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-dp8/decode-forward-v41-dp8-replay.json), SHA256 `08bb49ccccd27929c15d1736b35016fb0c86dafa92ba8b0df667011fae10f1e0`
- [decode-forward-09811dad-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-variants/decode-forward-09811dad-replay.json), SHA256 `b1c86a3cb347ff7230f2809d0005cc4c7d1eeed1d761e3c8dffffa782acf478e`
- [decode-forward-09811dad-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm-flash-ws9/decode-forward-09811dad-replay.json), SHA256 `76eaf93b99340c422948df3802f0ea878ef36aad7e661223f5a682cf3d92fa26`
- [decode-forward-09811dad-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-matrix-extension/decode-forward-09811dad-replay.json), SHA256 `1ad0472e95aa07deceb02c628e0a3c3c29a6d803eed84d701295a4cfc0118083`
- [decode-forward-09811dad-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-dp8/decode-forward-09811dad-replay.json), SHA256 `8db51a3c49addb942e6e9c6b81f9a740947a675d8058b59386d7908cd530e251`
- [decode-forward-332f0420-window8-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-variants/decode-forward-332f0420-window8-replay.json), SHA256 `a7da466863207e05a62d45e297b215b70cdfbddcfa3b79971899ab68309a6f31`
- [decode-forward-d08be4d4-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-final6/decode-forward-d08be4d4-replay.json), SHA256 `b9c82720d5c546bcf142ad72249f571a0c2da2be79f401f4a4170013934da186`
- [decode-forward-kimi-sp-window8-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-kimi-sp-window8-replay.json), SHA256 `a1ba78bef4d37e37c581f2b414240683a6074bbe1bb9b6ea5ca8a0c0cf617338`
- [decode-forward-qwen-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-runtime67/decode-forward-qwen-replay.json), SHA256 `2cd4f86ccca9d998f7d841d3ee01205160a876e281514aecdcd6f82b90b77fc6`
- [decode-forward-glm-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-runtime67/decode-forward-glm-replay.json), SHA256 `ad9dfb1967f6e3cc6f24cad1825eee8a225f2a350d1335881c8ab0abd33d4c4c`
- [decode-forward-v4_kimi-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-runtime67/decode-forward-v4_kimi-replay.json), SHA256 `8ddb66a1aef1382dad37f99224aa3e4c2b03eb846b55c9660886cdc27b36d65e`
- [decode-forward-v4_kimi-retry-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-runtime67/decode-forward-v4_kimi-retry-replay.json), SHA256 `fdc2994d5ff74222a3e1627cd94a294ac07bef571d8a31c4d2ca0a8b0687864e`
- [decode-forward-glm-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-matrix-fix/decode-forward-glm-replay.json), SHA256 `21d2e750181f782ac155886a8f6744046a7331410dfdb88dbfe2e4d2348f2259`
- [decode-forward-qwen-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-matrix-fix/decode-forward-qwen-replay.json), SHA256 `9acf1e12895b5559b4d6117fbf4754493c94ca9cbadefcc0db731a628d70bb71`
- [decode-forward-v4_kimi-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-matrix-fix/decode-forward-v4_kimi-replay.json), SHA256 `b4d3ba76bffba4df0081fc02660bbbe379003bcee644c5a8872d4e7f179b7540`
- [decode-forward-timeout-retry-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-matrix-fix/decode-forward-timeout-retry-replay.json), SHA256 `e2ec07749a9689ffd210f71fff75d1414c1a28e9790373ef468c58aab468f8c1`
- [decode-forward-qwen-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-body-default/decode-forward-qwen-replay.json), SHA256 `c378087d659fbac1b9f7b1d58efb9d54cbf97f5fdb3a19ab69288bf8b07fa1c6`
- [decode-forward-glm-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-body-default/decode-forward-glm-replay.json), SHA256 `5c87f299c6b84adfaf6828e8b61f61fe3e273d88f453b0ebe95dd87cd4d1f093`
- [decode-forward-v4_kimi-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-body-default/decode-forward-v4_kimi-replay.json), SHA256 `0ece8f6cc91da98705d0b4577140d8fa5033d51aeca88b9d2deb797d9161213e`
- [decode-forward-p4k-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-logical96/decode-forward-p4k-replay.json), SHA256 `9f171a13f6a59cfd758c46f964ca36ea9984a7fadd0dcf0c12adc8149cb23e1d`
- [decode-forward-p16k-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-logical96/decode-forward-p16k-replay.json), SHA256 `fe489f097ec0f7fd39bbe14c078501ea15d6a9c0b548be9e4b62df99954774cf`
- [decode-forward-qwen-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-body-fixed-grid/decode-forward-qwen-replay.json), SHA256 `ae90641e330e9ab8d8afe7322124825f35a0d74ce1e3ed67df24fcb0c3e4990a`
- [decode-forward-glm-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-body-fixed-grid/decode-forward-glm-replay.json), SHA256 `60fce49c84f782b4858db1981a7198481b5c54564704bb8ef3d4ec56d1580d0b`
- [decode-forward-v4_kimi-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-body-fixed-grid/decode-forward-v4_kimi-replay.json), SHA256 `ca1d29ac82aef23c533d42ad851e924f3140dd9b5c759d8ce56c480b89bcbd68`
- [decode-forward-kimi-a5-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-source-mechanisms/decode-forward-kimi-a5-replay.json), SHA256 `71f5b7ee2da08b1da4e13b131bea6e3cc3270d782207e6b6041a027fff10b43c`
- [decode-forward-kimi-a3-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-source-mechanisms/decode-forward-kimi-a3-replay.json), SHA256 `9cfdaa3424177d0b6cb121864e12694bf0029e4f5302b9a140a092278fd12aab`
- [decode-forward-glm-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-source-mechanisms/decode-forward-glm-replay.json), SHA256 `20a4704d9a3e735818f871205435fcfca3de9a5a5e4fa89076b3ec96f2397a1d`
- [decode-forward-kimi-glm-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-paged-dynamic/decode-forward-kimi-glm-replay.json), SHA256 `a45d4158dacdcf17a684bca0b9c7bdc84efdf7ed8ef12af155adf678bc379c77`
- [decode-forward-v41-dynamic-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-paged-dynamic/decode-forward-v41-dynamic-replay.json), SHA256 `668ac6b104dad5223f4b0ad52858db5375343bdc5987e0ff3558a9797fcfc169`
- [decode-forward-v41-dynamic-rotary-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-paged-dynamic/decode-forward-v41-dynamic-rotary-replay.json), SHA256 `da8df9155829a30eee457bd4cd7bddc565d0b1a5660a6d7c17c82a833971eb3b`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority-operators/body-operator-family-scoreboard.json), SHA256 `7126d4a275a5f005537517386747e366322a7bed7365763e21cb3a66319b13fc`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority-operators-5935c87b/body-operator-family-scoreboard.json), SHA256 `4f475bce99de8a8908c8fa745ea1ab9cabb8c570ef3b3ec5ef7c9d5d7f29265e`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-operators-09811dad/body-operator-family-scoreboard.json), SHA256 `53e528b2254c3ca55b4eb9e1afa5fc4e46f89ed6ccbee3059639dbbaed10175d`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm-operators-09811dad/body-operator-family-scoreboard.json), SHA256 `66c1e8335a7585608524322f2415ffc5648ae91d2259deadbc47fb8b99391f73`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-operators-332f0420/body-operator-family-scoreboard.json), SHA256 `e2d2bfaffcb017ffa47bc5ac3af1c0e5612951ac21d5dd6324797d9ef31efa6d`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-final6-operators-e8/body-operator-family-scoreboard.json), SHA256 `9cc875e1a79d728c77aaef1fbc71ac558483892a229f8f2f9af366006c401a67`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm-operators-67ca7673/body-operator-family-scoreboard.json), SHA256 `988ec7f991b0273ad19ff0f1d725541af5e0e42aa5e7a780dbd42e54431be2ac`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-operators-67ca7673/body-operator-family-scoreboard.json), SHA256 `090442db68bff96d02819baa27f29483eca7555b679b8ac1ed75c89a4680d299`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-operators-67ca7673-refs/body-operator-family-scoreboard.json), SHA256 `352ae526a827ec4ab5c9859057fbbc03bf01f655f4eb3f69ff0ddaaba537db7d`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-final6-operators-67ca7673-native-rebind/body-operator-family-scoreboard.json), SHA256 `9f7de958613c79fac0d03def2d6bfd1477425ed5335c5d30fd55b9e940ce88e9`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-matrix-fix/glm-operators-86c1ee8f/body-operator-family-scoreboard.json), SHA256 `d4679da03fd23bb74ac06cc2fd609ac3d63de8fd49d535de5ec1fb05591dfcc9`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-matrix-fix/glm-low-concurrency-86c1ee8f/body-operator-family-scoreboard.json), SHA256 `8e81fcca45b35141d4ea70f2f3b7e573aa5d7846635bbe4f02940d0265a0a25a`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-matrix-fix/glm-a3-livepre-86c1ee8f/body-operator-family-scoreboard.json), SHA256 `41034103b55d8f5ca913d5d5ce4072dca92f85f8c28504c40d72529ec0dac18f`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-operators-86c1ee8f/body-operator-family-scoreboard.json), SHA256 `66dd1ed469eb516ad963d134c5f8694e460e7eb9dcbcad79d2ac0ee3625985ea`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-operators-86c1ee8f-baseline/body-operator-family-scoreboard.json), SHA256 `424ec5eea0417cefa30e5ff98340309924b3f16b6abc731284eb0de7edb024fb`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-c128-operators-86c1ee8f-baseline/body-operator-family-scoreboard.json), SHA256 `354e76568d7f1ddbda9b3825933e90a077c67cd8103e0e0315fd4f36b2031f31`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-p32k-operators-86c1ee8f/body-operator-family-scoreboard.json), SHA256 `85cfaad1a2e0a795471c27de7301b1dda18bbf8409b529d6011d636da928daf2`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-body-default/glm-low-concurrency-operators/body-operator-family-scoreboard.json), SHA256 `3c866c0eea14329da75ba70c09f743980e3374ed3a1a2f68d0699c2ee3d0837b`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-body-default/glm-a3-livepre-operators/body-operator-family-scoreboard.json), SHA256 `2e1488d70330a4c337de7229878345b649220d80ff32a2c663a2436ef8ba0b1b`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-logical96-operators/full-matrix-canonical/body-operator-family-scoreboard.json), SHA256 `4c97e7d99d17285aa07d8e4c1b0224b36aa9690a0cf7211347e87f2299e66918`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-body-fixed-grid/glm-low-concurrency-operators/body-operator-family-scoreboard.json), SHA256 `c76aad000e201800e8675dc4cec71f87c4a5b6a3cc81a78c11513dd2ed7fa369`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-body-fixed-grid/glm-a3-livepre-operators/body-operator-family-scoreboard.json), SHA256 `3ab0f547ae14192513d0ca57bf8141c2a488684eb93acf64302267f43a6e1c46`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-source-operators/body-operator-family-scoreboard.json), SHA256 `ed32f17c2bc93f60df5c5a09a0864a7fb0f58a72a4656eaa67dbcef3450cf9d0`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm-source-mechanisms/body-operator-family-scoreboard.json), SHA256 `27c4cdc094278b98648cefd177e55251a7692787391a9aa2ff211bd71f8d8a4c`
- [body-communication-references.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-high-concurrency/body-communication-references.json), SHA256 `dd98c1ba7677ea8d5ef9ea1670c69937a4f8fa2e24ec096c7392c3440ace0caa`
- [glm-native-reference-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm-native-references-c2261d63/glm-native-reference-scoreboard.json), SHA256 `9f0532c8440ca21ada6e591666b1eee28b7962d0cddc556f26b814211445d60a`
- [v41-native-reference-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-native-references-0b822d0e/v41-native-reference-scoreboard.json), SHA256 `9eb32c11a11a661727927fea7e10487acbb58be2691aa15937ed44b053e7981d`
- [kimi-native-reference-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-source-references/kimi-native-reference-scoreboard.json), SHA256 `a65cc71c2de03bcbedd5dc3084c3edfecc07502a736ebd34faa1b6f2097a5761`
- [glm-source-native-reference-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm-source-mechanisms/glm-source-native-reference-scoreboard.json), SHA256 `0a7c9be7015077c031f70fda4725a148af45cabbba6298ee03ac2e902500666f`
- [v41-native-reference-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-native-references-dynamic-rotary/v41-native-reference-scoreboard.json), SHA256 `3171bedea2b596349a72e1c6b26edaa4416221af886e2495cf16b42446b8dcf1`

Additional coverage/source evidence (not silently promoted into body or operator predictions):

- [v41-existing-assets-20261030.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/v41-existing-assets-20261030.json), SHA256 `797183bf8f17978a219a4b96d8340de4b4a01442f66ae48b028aeb130be3f88f`
- [glm-three-level-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm/glm-three-level-evidence.json), SHA256 `f008c591bd6749b522d4500e047629bcd4f30438e54858c90ec5183c458a9f9a`
- [retained-source-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm78-v41/retained-source-evidence.json), SHA256 `cd28e3e6433de424c43d24327d7ad0b08e2ef27eb47cd9410a7bd8fa9fbb30ca`
- [decode-forward-auto-acceptance.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm78-v41/decode-forward-auto-acceptance.json), SHA256 `8241478fcadddf83641ca52edc1f622a624b2d50c57c60394447ca70eec0b18e`
- [retained-source-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-bundle0406/retained-source-evidence.json), SHA256 `ed8e523f3eea92aa697146085cb187258edbbe5d85ccca9d170e81b4efa98301`
- [retained-source-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-additional13/retained-source-evidence.json), SHA256 `38c9678eea4ccb217f9a20aad70896ccc649bd75177e4e9a91a0a50e8f93c57c`
- [c8-outlier-task-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-dp8/c8-outlier-task-evidence.json), SHA256 `75644791187c397dec4dd147ef75b2c1f77074e96148ab687b1305d4c458ba14`
- [body-source-condition-comparison.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-operators-86c1ee8f-source-symmetric/body-source-condition-comparison.json), SHA256 `cdfdd012c17ae978babe728e4fd2daf1d8f7734f286a0fd6ed2057e0514f8d4c`
- [v41-seven-arm-comparison.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-operators-86c1ee8f-source-symmetric/v41-seven-arm-comparison.json), SHA256 `de3d370fc4102007dd2a03fa421099699731dfd3c0d2bfb1961992cf7702d316`
- [kimi-c32-projection-bounded-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-matrix-fix/kimi-c32-projection-bounded-evidence.json), SHA256 `bce98d4671c7b96b8c784872bd7964fc32f7d37cfa9e7ecb57aa94100d12ee74`
- [body-runtime-delta.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-body-default/body-runtime-delta.json), SHA256 `3b60065c34d0ee7ae54182118ec020712f8e38f35a50a62cc986332fa7cebeaa`
- [remaining-family-gap-ledger.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-matrix-fix/remaining-family-gap-ledger.json), SHA256 `a2eed876b4e91beba82550ac21e734bcee764fd5f81444631e71333ca7a3621a`
- [body-runtime-delta.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-body-fixed-grid/body-runtime-delta.json), SHA256 `b7b2c24bd90a80439d555217ff8e717426f5a9f91e10ce3927e2efa44fa5d56f`
- [body-runtime-delta.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-logical96/body-runtime-delta.json), SHA256 `559a5050e945a87d8ac2a33371b2b8120d9eac2090a98f353bb5a60b96cfa9cb`
- [body-runtime-delta.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-source-mechanisms/body-runtime-delta.json), SHA256 `b20c5a0b9e0e44f4127ba8337c21d0c29888a223d86bdecb4d775acd7f946cad`

- Rows retain their own source/runtime/geometry; independently produced receipts are not merged into a synthetic run.
- Per-forward kernel activity residual ranks work to investigate; overlap prevents interpreting its sum as body wall-clock error.
- Unscored activity is a matching/model-boundary coverage gap, not proof that Sim omitted the corresponding work.
- Layer median-of-call-P50 and exact pooled P50 are distinct populations.
