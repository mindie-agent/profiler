# Priority Decode body, layer and operator scoreboard

Coverage status: **partial**. Missing predictions and unmatched roles stay visible.

Current selected Body arms: **16/66 passed**. One latest completed receipt per measured source/geometry, selected in input order; each row retains its own runtime and case.

Body: **36/147 prediction arms passed**; 66 unique sources, 222 measured geometry populations, 5250 unique complete Forwards (includes deferred populations).

Invalidated prediction rows: **31**. Their measured populations remain; superseded predictions and layer errors are excluded from accuracy statistics.

Current operator strict accuracy (latest input receipt per source/geometry): heavy_relative_15pct: **5/23**; micro_absolute_15us: **581/591**. Conditional references are excluded.

Operator runtime coverage (recorded Sim file-map hash → source/geometry populations): `886c1fa5bd45` → 1; `df7c8117e01b` → 3; `c27d72c215c2` → 40. Scores retain the latest available receipt for each population; this aggregate can contain different runtimes.

Strict event coverage: **1,134,343/6,729,791** events across 44 measured source/geometry populations. A high pass rate within this subset does not establish whole-model accuracy.

Local replay receipts with explicit comparison coverage. Body errors are measured wall-clock differences; operator priorities are nonadditive kernel activity residuals per complete Forward.

## Whole Decode Body — sorted by absolute ms error

| Case / variant | Status | Calls | Real Mean / P50 / P90 ms | Activity ms | Sim ms | Diff ms | Mean / P50 error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / runtime67-glm / `f2810bee7993` | compared | 44 | 57.817 / 57.597 / 59.092 | 55.203 | 34.967 | -22.850 | -39.521% / -39.290% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / runtime67-glm / `f2810bee7993` | compared | 44 | 57.639 / 57.562 / 58.995 | 55.027 | 34.967 | -22.672 | -39.334% / -39.252% |
| qwen36-a5-tp2-c96:q4_b96_m384 / runtime67-qwen / `f2810bee7993` | compared | 24 | 63.853 / 63.562 / 65.419 | 63.565 | 45.126 | -18.727 | -29.328% / -29.004% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / runtime67-glm / `f2810bee7993` | compared | 47 | 97.375 / 97.487 / 97.895 | 95.785 | 78.885 | -18.490 | -18.989% / -19.082% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / runtime67-glm / `f2810bee7993` | compared | 37 | 41.069 / 40.940 / 41.282 | 39.691 | 59.176 | 18.107 | 44.089% / 44.543% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / runtime67-qwen / `f2810bee7993` | compared | 18 | 119.054 / 119.131 / 119.486 | 118.048 | 102.211 | -16.843 | -14.148% / -14.203% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / runtime67-glm / `f2810bee7993` | compared | 49 | 69.556 / 69.489 / 69.830 | 66.970 | 52.924 | -16.632 | -23.912% / -23.838% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 / runtime67-v4_kimi / `f2810bee7993` | compared | 41 | 44.666 / 44.645 / 44.662 | 43.971 | 28.078 | -16.588 | -37.138% / -37.108% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 / runtime67-v4_kimi / `f2810bee7993` | compared | 47 | 39.247 / 39.245 / 39.263 | 38.567 | 23.145 | -16.103 | -41.029% / -41.025% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 / runtime67-v4_kimi / `f2810bee7993` | compared | 51 | 35.964 / 35.962 / 35.979 | 35.282 | 20.533 | -15.432 | -42.909% / -42.905% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 / runtime67-v4_kimi / `f2810bee7993` | compared | 52 | 34.816 / 34.794 / 34.813 | 34.115 | 19.644 | -15.172 | -43.578% / -43.541% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 / runtime67-v4_kimi / `f2810bee7993` | compared | 49 | 36.985 / 36.953 / 36.969 | 36.305 | 21.934 | -15.051 | -40.695% / -40.643% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 / runtime67-v4_kimi / `f2810bee7993` | compared | 52 | 34.819 / 34.791 / 34.808 | 34.142 | 19.927 | -14.892 | -42.769% / -42.723% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 / runtime67-v4_kimi / `f2810bee7993` | compared | 53 | 34.194 / 34.177 / 34.194 | 33.491 | 19.342 | -14.852 | -43.435% / -43.408% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 / runtime67-v4_kimi / `f2810bee7993` | compared | 54 | 33.876 / 33.858 / 33.873 | 33.190 | 19.199 | -14.676 | -43.324% / -43.294% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / runtime67-glm / `f2810bee7993` | compared | 31 | 46.528 / 46.499 / 46.645 | 46.293 | 32.002 | -14.526 | -31.220% / -31.176% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 / runtime67-v4_kimi / `f2810bee7993` | compared | 55 | 33.548 / 33.516 / 33.533 | 32.857 | 19.048 | -14.499 | -43.221% / -43.167% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 / runtime67-v4_kimi / `f2810bee7993` | compared | 46 | 40.019 / 40.018 / 40.044 | 39.323 | 25.658 | -14.361 | -35.886% / -35.885% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / runtime67-glm / `f2810bee7993` | compared | 49 | 69.361 / 69.418 / 69.528 | 67.823 | 55.002 | -14.358 | -20.701% / -20.767% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / runtime67-qwen / `f2810bee7993` | compared | 76 | 28.585 / 28.571 / 28.704 | 28.300 | 14.651 | -13.934 | -48.746% / -48.721% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / runtime67-glm / `f2810bee7993` | compared | 35 | 38.713 / 38.722 / 38.759 | 38.458 | 25.116 | -13.597 | -35.122% / -35.137% |
| qwen36-a5-tp2-c12:q4_b12_m48 / runtime67-qwen / `f2810bee7993` | compared | 55 | 24.226 / 24.053 / 24.711 | 23.858 | 10.999 | -13.227 | -54.600% / -54.273% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / runtime67-glm / `f2810bee7993` | compared | 31 | 37.669 / 37.665 / 37.761 | 37.413 | 24.737 | -12.932 | -34.331% / -34.324% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / runtime67-glm / `f2810bee7993` | compared | 32 | 33.616 / 33.626 / 33.710 | 33.358 | 21.102 | -12.514 | -37.227% / -37.245% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / runtime67-glm / `f2810bee7993` | compared | 30 | 33.031 / 33.026 / 33.164 | 32.773 | 20.914 | -12.117 | -36.683% / -36.674% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 / runtime67-v4_kimi / `f2810bee7993` | compared | 59 | 30.823 / 30.822 / 30.839 | 30.184 | 18.977 | -11.846 | -38.433% / -38.430% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 / runtime67-v4_kimi / `f2810bee7993` | compared | 59 | 30.637 / 30.615 / 30.632 | 29.997 | 18.901 | -11.735 | -38.305% / -38.261% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / runtime67-qwen / `f2810bee7993` | compared | 79 | 21.957 / 22.001 / 22.068 | 21.571 | 10.223 | -11.734 | -53.441% / -53.535% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / runtime67-glm / `f2810bee7993` | compared | 30 | 28.833 / 28.828 / 28.885 | 28.568 | 18.156 | -10.678 | -37.032% / -37.021% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / runtime67-glm / `f2810bee7993` | compared | 50 | 53.893 / 53.871 / 54.021 | 52.393 | 44.149 | -9.744 | -18.080% / -18.046% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 / runtime67-v4_kimi / `f2810bee7993` | compared | 75 | 26.328 / 26.306 / 26.336 | 26.229 | 17.591 | -8.737 | -33.186% / -33.129% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / runtime67-glm / `f2810bee7993` | compared | 11 | 21.418 / 21.408 / 21.432 | 21.147 | 12.898 | -8.521 | -39.782% / -39.753% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 / runtime67-v4_kimi / `f2810bee7993` | compared | 73 | 27.286 / 27.266 / 27.290 | 27.188 | 18.811 | -8.475 | -31.060% / -31.009% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / runtime67-qwen / `f2810bee7993` | compared | 23 | 76.089 / 76.132 / 76.632 | 75.005 | 68.098 | -7.991 | -10.502% / -10.553% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / runtime67-v4_kimi / `f2810bee7993` | compared | 63 | 32.555 / 32.533 / 32.674 | — | 24.863 | -7.693 | -23.630% / -23.577% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / runtime67-glm / `f2810bee7993` | compared | 47 | 46.859 / 46.817 / 47.175 | 45.372 | 39.174 | -7.685 | -16.401% / -16.326% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / runtime67-glm / `f2810bee7993` | compared | 53 | 21.068 / 21.057 / 21.170 | 20.805 | 14.028 | -7.039 | -33.413% / -33.381% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 / runtime67-v4_kimi / `f2810bee7993` | compared | 105 | 18.625 / 18.616 / 18.640 | 18.526 | 11.800 | -6.824 | -36.642% / -36.612% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / runtime67-qwen / `f2810bee7993` | compared | 84 | 11.551 / 11.482 / 11.818 | 11.135 | 5.052 | -6.499 | -56.265% / -56.000% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / runtime67-glm / `f2810bee7993` | compared | 65 | 15.683 / 15.670 / 15.738 | 15.421 | 9.501 | -6.182 | -39.417% / -39.367% |
| v4flash-a3-tp8-c4:q2_b4_m8 / runtime67-v4_kimi / `f2810bee7993` | compared | 104 | 32.486 / 32.416 / 32.734 | 30.611 | 26.445 | -6.041 | -18.595% / -18.420% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 / runtime67-v4_kimi / `f2810bee7993` | compared | 129 | 14.929 / 14.914 / 14.929 | 14.832 | 8.977 | -5.952 | -39.867% / -39.807% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 / runtime67-v4_kimi / `f2810bee7993` | compared | 145 | 13.292 / 12.803 / 12.817 | 13.196 | 7.532 | -5.760 | -43.335% / -41.173% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 / runtime67-v4_kimi / `f2810bee7993` | compared | 151 | 13.239 / 13.209 / 13.227 | 13.143 | 7.532 | -5.707 | -43.110% / -42.980% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 / runtime67-v4_kimi / `f2810bee7993` | compared | 152 | 13.135 / 13.129 / 13.145 | 13.039 | 7.532 | -5.603 | -42.658% / -42.635% |
| a3_glm53_dc4k_b2:q1_b2_m2 / runtime67-glm / `f2810bee7993` | compared | 70 | 40.970 / 40.935 / 41.046 | — | 35.417 | -5.553 | -13.553% / -13.479% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / runtime67-glm / `f2810bee7993` | compared | 46 | 34.118 / 33.910 / 35.073 | 32.625 | 28.566 | -5.552 | -16.273% / -15.759% |
| a3_glm53_dc16k_b1:q1_b1_m1 / runtime67-glm / `f2810bee7993` | compared | 74 | 39.112 / 39.105 / 39.196 | — | 33.573 | -5.539 | -14.162% / -14.146% |
| a3_glm53_dc4k_b1:q1_b1_m1 / runtime67-glm / `f2810bee7993` | compared | 74 | 38.955 / 38.943 / 39.036 | — | 33.573 | -5.382 | -13.816% / -13.789% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / runtime67-glm / `f2810bee7993` | compared | 46 | 29.762 / 29.664 / 30.046 | 28.242 | 34.933 | 5.172 | 17.378% / 17.765% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / runtime67-glm / `f2810bee7993` | compared | 46 | 39.841 / 39.798 / 40.057 | 38.324 | 34.933 | -4.908 | -12.318% / -12.224% |
| qwen36-a5-tp2-c1:q4_b1_m4 / runtime67-qwen / `f2810bee7993` | compared | 85 | 12.318 / 12.279 / 12.362 | 11.956 | 7.413 | -4.905 | -39.822% / -39.630% |
| a3_glm53_dc4k_b4:q1_b4_m4 / runtime67-glm / `f2810bee7993` | compared | 67 | 43.438 / 43.437 / 43.598 | — | 38.562 | -4.875 | -11.224% / -11.222% |
| v4flash-a3-tp8-c8:q2_b8_m16 / runtime67-v4_kimi / `f2810bee7993` | compared | 104 | 37.763 / 37.868 / 38.082 | 36.154 | 33.464 | -4.299 | -11.385% / -11.631% |
| a3_glm53_dc4k_b8:q1_b8_m8 / runtime67-glm / `f2810bee7993` | compared | 61 | 47.113 / 47.149 / 47.402 | — | 44.050 | -3.063 | -6.502% / -6.572% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / runtime67-glm / `f2810bee7993` | compared | 27 | 57.590 / 57.573 / 57.734 | 57.355 | 54.554 | -3.036 | -5.272% / -5.244% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 / runtime67-v4_kimi / `f2810bee7993` | compared | 235 | 4.807 / 4.779 / 4.992 | 4.709 | 3.530 | -1.277 | -26.558% / -26.126% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 / runtime67-v4_kimi / `f2810bee7993` | compared | 29 | 48.582 / 48.412 / 48.662 | 47.883 | 49.831 | 1.249 | 2.571% / 2.931% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 / runtime67-v4_kimi / `f2810bee7993` | compared | 220 | 6.714 / 6.665 / 6.923 | 6.609 | 5.494 | -1.220 | -18.167% / -17.565% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 / runtime67-v4_kimi / `f2810bee7993` | compared | 246 | 3.476 / 3.438 / 3.656 | 3.380 | 2.412 | -1.064 | -30.607% / -29.832% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 / runtime67-v4_kimi / `f2810bee7993` | compared | 196 | 9.615 / 9.550 / 9.774 | 9.502 | 8.740 | -0.875 | -9.101% / -8.475% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 / runtime67-v4_kimi / `f2810bee7993` | compared | 254 | 3.180 / 3.128 / 3.432 | 3.088 | 2.352 | -0.828 | -26.033% / -24.793% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 / runtime67-v4_kimi / `f2810bee7993` | compared | 48 | 47.654 / 47.425 / 47.666 | 46.949 | 48.473 | 0.819 | 1.718% / 2.209% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 / runtime67-v4_kimi / `f2810bee7993` | compared | 32 | 49.985 / 49.802 / 50.230 | 49.318 | 50.615 | 0.631 | 1.262% / 1.633% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 / runtime67-v4_kimi / `f2810bee7993` | compared | 22 | 54.967 / 54.880 / 55.047 | 54.296 | 54.634 | -0.333 | -0.605% / -0.448% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 / runtime67-v4_kimi / `f2810bee7993` | compared | 21 | 61.811 / 61.629 / 62.042 | 61.115 | 61.949 | 0.138 | 0.223% / 0.520% |
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

Failed reads remain visible and do not become zero-duration measured populations.

| Case | Failure | Later source comparison present |
|---|---|---|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | declared_forward_extraction_missing | True |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | declared_forward_extraction_missing | True |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | declared_forward_extraction_missing | True |

## Layer 0 and steady layer groups

The steady P50 column is median of per-layer call P50, unless a separately linked receipt supplies exact pooled statistics.

| Case | Group | Layers | Real Mean ms | Median layer-call P50 ms | Sim Mean ms | Mean / P50 error |
|---|---|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / runtime67-glm | Layer 0 / mla / dense_layer | 1 | 0.6279 | 0.5491 | 0.3305 | -47.362% / -39.801% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / runtime67-glm | Steady / mla / dense_layer | 2 | 0.5676 | 0.5344 | 0.3305 | -41.765% / -38.150% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / runtime67-glm | Steady / mla / moe_layer | 75 | 0.7473 | 0.7151 | 0.4530 | -39.383% / -36.650% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / runtime67-glm | Layer 0 / mla / dense_layer | 1 | 0.5858 | 0.5425 | 0.3305 | -43.571% / -39.074% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / runtime67-glm | Steady / mla / dense_layer | 2 | 0.5667 | 0.5291 | 0.3305 | -41.676% / -37.528% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / runtime67-glm | Steady / mla / moe_layer | 75 | 0.7455 | 0.7151 | 0.4530 | -39.238% / -36.647% |
| qwen36-a5-tp2-c96:q4_b96_m384 / runtime67-qwen | Layer 0 / gdn / dense_layer | 1 | 1.3691 | 1.0682 | 0.7556 | -44.813% / -29.265% |
| qwen36-a5-tp2-c96:q4_b96_m384 / runtime67-qwen | Steady / gdn / dense_layer | 47 | 1.0584 | 1.0584 | 0.7556 | -28.615% / -28.614% |
| qwen36-a5-tp2-c96:q4_b96_m384 / runtime67-qwen | Steady / gqa / dense_layer | 16 | 0.7931 | 0.7928 | 0.5537 | -30.186% / -30.151% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 1.3232 | 1.3221 | 1.0894 | -17.672% / -17.602% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / runtime67-glm | Steady / kda / dense_layer | 2 | 1.2997 | 1.3012 | 1.0894 | -16.179% / -16.279% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / runtime67-glm | Steady / mla / moe_layer | 11 | 3.5285 | 3.5319 | 2.1916 | -37.888% / -37.947% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / runtime67-glm | Steady / kda / moe_layer | 31 | 1.7609 | 1.7632 | 1.6616 | -5.640% / -5.764% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 1.0092 | 0.8498 | 0.7050 | -30.142% / -17.032% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.4246 | 0.4245 | 0.7050 | 66.042% / 66.092% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / runtime67-glm | Steady / mla / moe_layer | 11 | 1.3710 | 1.3767 | 1.5075 | 9.955% / 9.501% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.7767 | 0.7741 | 1.3058 | 68.114% / 68.681% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / runtime67-qwen | Layer 0 / gdn / moe_layer | 1 | 2.0473 | 1.9983 | 1.6517 | -19.323% / -17.344% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / runtime67-qwen | Steady / gdn / moe_layer | 44 | 1.9572 | 1.9352 | 1.6517 | -15.610% / -14.649% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / runtime67-qwen | Steady / gqa / moe_layer | 15 | 2.0544 | 2.0314 | 1.8590 | -9.510% / -8.486% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / runtime67-glm | Layer 0 / mla / dense_layer | 1 | 0.6710 | 0.6210 | 0.4226 | -37.013% / -31.947% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / runtime67-glm | Steady / mla / dense_layer | 2 | 0.6345 | 0.6104 | 0.4226 | -33.395% / -30.765% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / runtime67-glm | Steady / mla / moe_layer | 75 | 0.9015 | 0.8670 | 0.6887 | -23.600% / -20.556% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.3620 | 0.3384 | 0.2463 | -31.976% / -27.225% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.4145 | 0.4142 | 0.2792 | -32.638% / -32.592% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.6715 | 0.6644 | 0.3680 | -45.196% / -44.607% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.3047 | 0.3023 | 0.2048 | -32.780% / -32.241% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.3858 | 0.3856 | 0.2389 | -38.088% / -38.052% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.5293 | 0.5223 | 0.2785 | -47.391% / -46.687% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.2840 | 0.2810 | 0.1824 | -35.794% / -35.113% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.3653 | 0.3650 | 0.2168 | -40.648% / -40.601% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.4517 | 0.4454 | 0.2332 | -48.380% / -47.659% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.2974 | 0.2770 | 0.1760 | -40.807% / -36.445% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.3596 | 0.3592 | 0.2105 | -41.473% / -41.410% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.4192 | 0.4125 | 0.2142 | -48.900% / -48.061% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.3353 | 0.3023 | 0.2048 | -38.919% / -32.241% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.3857 | 0.3855 | 0.2389 | -38.076% / -38.041% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.4340 | 0.4269 | 0.2280 | -47.458% / -46.577% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.3102 | 0.2816 | 0.1824 | -41.205% / -35.233% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.3652 | 0.3648 | 0.2168 | -40.645% / -40.571% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.4029 | 0.3960 | 0.2079 | -48.391% / -47.489% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.2930 | 0.2771 | 0.1760 | -39.919% / -36.470% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.3596 | 0.3596 | 0.2105 | -41.474% / -41.461% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.3935 | 0.3863 | 0.2016 | -48.755% / -47.810% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.2876 | 0.2698 | 0.1729 | -39.877% / -35.918% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.3531 | 0.3529 | 0.2073 | -41.287% / -41.253% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.3989 | 0.3918 | 0.2048 | -48.667% / -47.731% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.5510 | 0.5299 | 0.3126 | -43.261% / -41.001% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.4693 | 0.4691 | 0.3126 | -33.383% / -33.352% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / runtime67-glm | Steady / mla / moe_layer | 11 | 1.5929 | 1.5839 | 0.8357 | -47.536% / -47.238% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.8876 | 0.8877 | 0.7055 | -20.512% / -20.524% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.3027 | 0.2698 | 0.1729 | -42.875% / -35.929% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.3533 | 0.3531 | 0.2073 | -41.324% / -41.294% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.3840 | 0.3767 | 0.1985 | -48.314% / -47.317% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.3379 | 0.3376 | 0.2463 | -27.126% / -27.051% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.4141 | 0.4140 | 0.2792 | -32.582% / -32.566% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.4799 | 0.4722 | 0.2672 | -44.326% / -43.425% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.9534 | 0.9082 | 0.6823 | -28.434% / -24.871% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.8762 | 0.8787 | 0.6823 | -22.129% / -22.348% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / runtime67-glm | Steady / mla / moe_layer | 11 | 2.3319 | 2.3310 | 1.4684 | -37.027% / -37.003% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / runtime67-glm | Steady / kda / moe_layer | 31 | 1.3210 | 1.3204 | 1.1872 | -10.134% / -10.092% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / runtime67-qwen | Layer 0 / gdn / moe_layer | 1 | 0.7544 | 0.7238 | 0.3796 | -49.681% / -47.550% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / runtime67-qwen | Steady / gdn / moe_layer | 29 | 0.7199 | 0.7199 | 0.3796 | -47.265% / -47.269% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / runtime67-qwen | Steady / gqa / moe_layer | 10 | 0.6953 | 0.6941 | 0.3262 | -53.084% / -53.003% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.4891 | 0.4818 | 0.2159 | -55.847% / -55.180% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.3535 | 0.3535 | 0.2159 | -38.919% / -38.907% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / runtime67-glm | Steady / mla / moe_layer | 11 | 1.2946 | 1.2899 | 0.6662 | -48.539% / -48.353% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.7508 | 0.7507 | 0.5529 | -26.361% / -26.350% |
| qwen36-a5-tp2-c12:q4_b12_m48 / runtime67-qwen | Layer 0 / gdn / dense_layer | 1 | 0.6168 | 0.3931 | 0.1825 | -70.421% / -53.586% |
| qwen36-a5-tp2-c12:q4_b12_m48 / runtime67-qwen | Steady / gdn / dense_layer | 47 | 0.4044 | 0.4033 | 0.1825 | -54.884% / -54.760% |
| qwen36-a5-tp2-c12:q4_b12_m48 / runtime67-qwen | Steady / gqa / dense_layer | 16 | 0.2846 | 0.2843 | 0.1401 | -50.788% / -50.733% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.4873 | 0.4626 | 0.2159 | -55.687% / -53.323% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.3528 | 0.3529 | 0.2159 | -38.795% / -38.804% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / runtime67-glm | Steady / mla / moe_layer | 11 | 1.1973 | 1.1925 | 0.6317 | -47.236% / -47.023% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.7518 | 0.7522 | 0.5529 | -26.453% / -26.495% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.3876 | 0.4019 | 0.1697 | -56.227% / -57.785% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.2980 | 0.2974 | 0.1697 | -43.067% / -42.944% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / runtime67-glm | Steady / mla / moe_layer | 11 | 1.0591 | 1.0543 | 0.5329 | -49.684% / -49.457% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.6768 | 0.6768 | 0.4752 | -29.791% / -29.790% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.3980 | 0.3937 | 0.1697 | -57.364% / -56.901% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.2982 | 0.2982 | 0.1697 | -43.106% / -43.099% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / runtime67-glm | Steady / mla / moe_layer | 11 | 1.0018 | 0.9978 | 0.5159 | -48.507% / -48.300% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.6779 | 0.6772 | 0.4752 | -29.905% / -29.829% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.2595 | 0.2581 | 0.1713 | -33.983% / -33.636% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.3208 | 0.3208 | 0.2057 | -35.865% / -35.868% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.3644 | 0.3577 | 0.2000 | -45.111% / -44.081% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.2772 | 0.2578 | 0.1713 | -38.204% / -33.552% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.3209 | 0.3210 | 0.2057 | -35.886% / -35.908% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.3556 | 0.3487 | 0.1969 | -44.638% / -43.536% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / runtime67-qwen | Layer 0 / gdn / moe_layer | 1 | 0.7737 | 0.8216 | 0.2646 | -65.796% / -67.792% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / runtime67-qwen | Steady / gdn / moe_layer | 29 | 0.5470 | 0.5467 | 0.2646 | -51.620% / -51.597% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / runtime67-qwen | Steady / gqa / moe_layer | 10 | 0.5320 | 0.5323 | 0.2284 | -57.068% / -57.092% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.4973 | 0.4989 | 0.1496 | -69.915% / -70.010% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.2536 | 0.2520 | 0.1496 | -41.010% / -40.636% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / runtime67-glm | Steady / mla / moe_layer | 11 | 0.8678 | 0.8641 | 0.4405 | -49.241% / -49.022% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.5897 | 0.5893 | 0.4149 | -29.649% / -29.599% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.6895 | 0.6689 | 0.4851 | -29.643% / -27.470% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.6561 | 0.6366 | 0.4851 | -26.056% / -23.788% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / runtime67-glm | Steady / mla / moe_layer | 11 | 1.6861 | 1.6864 | 1.1313 | -32.902% / -32.914% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / runtime67-glm | Steady / kda / moe_layer | 31 | 1.0740 | 1.0740 | 0.9758 | -9.142% / -9.143% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 0.7498 | 0.7292 | 0.4315 | -42.457% / -40.827% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 / runtime67-v4_kimi | Steady / mla / moe_layer | 39 | 0.6558 | 0.6334 | 0.4400 | -32.908% / -30.533% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.3235 | 0.2805 | 0.1399 | -56.742% / -50.115% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.2349 | 0.2350 | 0.1399 | -40.442% / -40.454% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / runtime67-glm | Steady / mla / moe_layer | 11 | 0.6731 | 0.6714 | 0.3136 | -53.417% / -53.293% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.4264 | 0.4251 | 0.2912 | -31.702% / -31.487% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 0.8025 | 0.7842 | 0.4612 | -42.532% / -41.190% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 / runtime67-v4_kimi | Steady / mla / moe_layer | 39 | 0.6790 | 0.6545 | 0.4705 | -30.710% / -28.115% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / runtime67-qwen | Layer 0 / gdn / moe_layer | 1 | 1.3503 | 1.2865 | 1.1007 | -18.490% / -14.445% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / runtime67-qwen | Steady / gdn / moe_layer | 44 | 1.2329 | 1.2077 | 1.1007 | -10.726% / -8.864% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / runtime67-qwen | Steady / gqa / moe_layer | 15 | 1.3614 | 1.3469 | 1.2379 | -9.074% / -8.093% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.2579 | 0.2383 | 0.1532 | -40.585% / -35.692% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / runtime67-v4_kimi | Steady / kda / moe_layer | 68 | 0.3399 | 0.3386 | 0.2681 | -21.123% / -20.813% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / runtime67-v4_kimi | Steady / mla / moe_layer | 24 | 0.3835 | 0.3747 | 0.2692 | -29.799% / -28.139% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.6412 | 0.5810 | 0.4012 | -37.426% / -30.945% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.6152 | 0.5329 | 0.4012 | -34.785% / -24.712% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / runtime67-glm | Steady / mla / moe_layer | 11 | 1.4099 | 1.4072 | 0.9753 | -30.821% / -30.690% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.9493 | 0.9478 | 0.8788 | -7.428% / -7.283% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.4650 | 0.4745 | 0.1476 | -68.256% / -68.890% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.2383 | 0.2328 | 0.1476 | -38.059% / -36.597% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / runtime67-glm | Steady / mla / moe_layer | 11 | 0.6392 | 0.6337 | 0.3466 | -45.766% / -45.296% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.4224 | 0.4216 | 0.3152 | -25.370% / -25.236% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 0.5279 | 0.5209 | 0.2870 | -45.627% / -44.890% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 / runtime67-v4_kimi | Steady / mla / moe_layer | 39 | 0.4640 | 0.4441 | 0.2952 | -36.371% / -33.520% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / runtime67-qwen | Layer 0 / gdn / moe_layer | 1 | 0.3868 | 0.2973 | 0.1242 | -67.878% / -58.216% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / runtime67-qwen | Steady / gdn / moe_layer | 29 | 0.2819 | 0.2827 | 0.1242 | -55.930% / -56.057% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / runtime67-qwen | Steady / gqa / moe_layer | 10 | 0.2989 | 0.2992 | 0.1325 | -55.669% / -55.714% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.4222 | 0.4383 | 0.1284 | -69.600% / -70.713% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.2487 | 0.2314 | 0.1284 | -48.386% / -44.529% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / runtime67-glm | Steady / mla / moe_layer | 11 | 0.4952 | 0.4903 | 0.2354 | -52.460% / -51.986% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.3005 | 0.2985 | 0.2105 | -29.938% / -29.473% |
| v4flash-a3-tp8-c4:q2_b4_m8 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 0.7568 | 0.7178 | 0.5313 | -29.803% / -25.987% |
| v4flash-a3-tp8-c4:q2_b4_m8 / runtime67-v4_kimi | Steady / mla / moe_layer | 42 | 0.7543 | 0.7537 | 0.6170 | -18.199% / -18.135% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 0.4353 | 0.4201 | 0.2166 | -50.244% / -48.448% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 / runtime67-v4_kimi | Steady / mla / moe_layer | 39 | 0.3716 | 0.3526 | 0.2246 | -39.545% / -36.295% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 0.8501 | 0.3611 | 0.1805 | -78.773% / -50.022% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 / runtime67-v4_kimi | Steady / mla / moe_layer | 39 | 0.3189 | 0.3014 | 0.1885 | -40.902% / -37.455% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 0.8470 | 0.8162 | 0.1805 | -78.695% / -77.891% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 / runtime67-v4_kimi | Steady / mla / moe_layer | 39 | 0.3177 | 0.3003 | 0.1885 | -40.666% / -37.232% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 0.8189 | 0.8103 | 0.1805 | -77.963% / -77.729% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 / runtime67-v4_kimi | Steady / mla / moe_layer | 39 | 0.3157 | 0.2984 | 0.1885 | -40.299% / -36.824% |
| a3_glm53_dc4k_b2:q1_b2_m2 / runtime67-glm | Layer 0 / mla / dense_layer | 1 | 0.4105 | 0.3960 | 0.3540 | -13.760% / -10.588% |
| a3_glm53_dc4k_b2:q1_b2_m2 / runtime67-glm | Steady / mla / dense_layer | 2 | 0.3997 | 0.3865 | 0.3540 | -11.422% / -8.405% |
| a3_glm53_dc4k_b2:q1_b2_m2 / runtime67-glm | Steady / mla / moe_layer | 75 | 0.5293 | 0.5092 | 0.4581 | -13.455% / -10.035% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.5732 | 0.5010 | 0.3596 | -37.275% / -28.234% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.5965 | 0.5414 | 0.3596 | -39.722% / -33.585% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / runtime67-glm | Steady / mla / moe_layer | 11 | 0.9546 | 0.9395 | 0.7116 | -25.459% / -24.259% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.7032 | 0.6643 | 0.6342 | -9.814% / -4.531% |
| a3_glm53_dc16k_b1:q1_b1_m1 / runtime67-glm | Layer 0 / mla / dense_layer | 1 | 0.4020 | 0.3967 | 0.3526 | -12.294% / -11.111% |
| a3_glm53_dc16k_b1:q1_b1_m1 / runtime67-glm | Steady / mla / dense_layer | 2 | 0.3934 | 0.3879 | 0.3526 | -10.369% / -9.102% |
| a3_glm53_dc16k_b1:q1_b1_m1 / runtime67-glm | Steady / mla / moe_layer | 75 | 0.5045 | 0.4834 | 0.4335 | -14.063% / -10.325% |
| a3_glm53_dc4k_b1:q1_b1_m1 / runtime67-glm | Layer 0 / mla / dense_layer | 1 | 0.3943 | 0.3854 | 0.3526 | -10.563% / -8.497% |
| a3_glm53_dc4k_b1:q1_b1_m1 / runtime67-glm | Steady / mla / dense_layer | 2 | 0.3841 | 0.3775 | 0.3526 | -8.207% / -6.585% |
| a3_glm53_dc4k_b1:q1_b1_m1 / runtime67-glm | Steady / mla / moe_layer | 75 | 0.5031 | 0.4848 | 0.4335 | -13.823% / -10.574% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.8292 | 0.7249 | 0.4048 | -51.188% / -44.160% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.2964 | 0.2961 | 0.4048 | 36.564% / 36.691% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / runtime67-glm | Steady / mla / moe_layer | 11 | 0.9295 | 0.9276 | 0.8731 | -6.071% / -5.877% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.5827 | 0.5821 | 0.7779 | 33.504% / 33.634% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.6141 | 0.5825 | 0.4048 | -34.084% / -30.508% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.6160 | 0.5541 | 0.4048 | -34.293% / -26.945% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / runtime67-glm | Steady / mla / moe_layer | 11 | 1.1665 | 1.1644 | 0.8731 | -25.156% / -25.021% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / runtime67-glm | Steady / kda / moe_layer | 31 | 0.8101 | 0.8087 | 0.7779 | -3.967% / -3.806% |
| qwen36-a5-tp2-c1:q4_b1_m4 / runtime67-qwen | Layer 0 / gdn / dense_layer | 1 | 0.2400 | 0.1984 | 0.1154 | -51.909% / -41.833% |
| qwen36-a5-tp2-c1:q4_b1_m4 / runtime67-qwen | Steady / gdn / dense_layer | 47 | 0.1919 | 0.1915 | 0.1154 | -39.861% / -39.732% |
| qwen36-a5-tp2-c1:q4_b1_m4 / runtime67-qwen | Steady / gqa / dense_layer | 16 | 0.1880 | 0.1876 | 0.1171 | -37.704% / -37.562% |
| a3_glm53_dc4k_b4:q1_b4_m4 / runtime67-glm | Layer 0 / mla / dense_layer | 1 | 0.4118 | 0.4071 | 0.3569 | -13.334% / -12.342% |
| a3_glm53_dc4k_b4:q1_b4_m4 / runtime67-glm | Steady / mla / dense_layer | 2 | 0.3968 | 0.3931 | 0.3569 | -10.074% / -9.208% |
| a3_glm53_dc4k_b4:q1_b4_m4 / runtime67-glm | Steady / mla / moe_layer | 75 | 0.5622 | 0.5411 | 0.4999 | -11.079% / -7.624% |
| v4flash-a3-tp8-c8:q2_b8_m16 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 0.8072 | 0.7668 | 0.6899 | -14.540% / -10.029% |
| v4flash-a3-tp8-c8:q2_b8_m16 / runtime67-v4_kimi | Steady / mla / moe_layer | 42 | 0.8787 | 0.8831 | 0.7803 | -11.198% / -11.637% |
| a3_glm53_dc4k_b8:q1_b8_m8 / runtime67-glm | Layer 0 / mla / dense_layer | 1 | 0.4244 | 0.4227 | 0.3646 | -14.080% / -13.728% |
| a3_glm53_dc4k_b8:q1_b8_m8 / runtime67-glm | Steady / mla / dense_layer | 2 | 0.4119 | 0.4111 | 0.3646 | -11.462% / -11.306% |
| a3_glm53_dc4k_b8:q1_b8_m8 / runtime67-glm | Steady / mla / moe_layer | 75 | 0.6105 | 0.5863 | 0.5727 | -6.191% / -2.316% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / runtime67-glm | Layer 0 / kda / dense_layer | 1 | 0.6036 | 0.5889 | 0.6439 | 6.677% / 9.346% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / runtime67-glm | Steady / kda / dense_layer | 2 | 0.5724 | 0.5723 | 0.6439 | 12.501% / 12.525% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / runtime67-glm | Steady / mla / moe_layer | 11 | 2.2334 | 2.2329 | 1.4138 | -36.699% / -36.683% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / runtime67-glm | Steady / kda / moe_layer | 31 | 1.0088 | 1.0088 | 1.1958 | 18.539% / 18.540% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.9021 | 0.9359 | 0.4775 | -47.069% / -48.979% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 / runtime67-v4_kimi | Steady / kda / moe_layer | 2 | 1.2773 | 1.2657 | 1.0238 | -19.850% / -19.113% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 / runtime67-v4_kimi | Steady / mla / moe_layer | 1 | 1.4535 | 1.4525 | 0.9869 | -32.102% / -32.053% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 1.4227 | 1.2523 | 1.2316 | -13.432% / -1.653% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 / runtime67-v4_kimi | Steady / mla / moe_layer | 39 | 1.2164 | 1.1586 | 1.2461 | 2.447% / 7.551% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.8847 | 0.9181 | 0.5852 | -33.853% / -36.260% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 / runtime67-v4_kimi | Steady / kda / moe_layer | 2 | 1.8592 | 1.8408 | 1.6429 | -11.638% / -10.753% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 / runtime67-v4_kimi | Steady / mla / moe_layer | 1 | 2.1726 | 2.1723 | 1.6037 | -26.188% / -26.178% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.8688 | 0.8927 | 0.3883 | -55.308% / -56.505% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 / runtime67-v4_kimi | Steady / kda / moe_layer | 2 | 0.8910 | 0.8481 | 0.6768 | -24.037% / -20.200% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 / runtime67-v4_kimi | Steady / mla / moe_layer | 1 | 0.9683 | 0.9617 | 0.6499 | -32.879% / -32.414% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.9604 | 0.9526 | 0.8049 | -16.193% / -15.506% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 / runtime67-v4_kimi | Steady / kda / moe_layer | 2 | 2.7714 | 2.7569 | 2.6536 | -4.249% / -3.745% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 / runtime67-v4_kimi | Steady / mla / moe_layer | 1 | 3.2092 | 3.2089 | 2.6065 | -18.781% / -18.774% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 / runtime67-v4_kimi | Layer 0 / kda / dense_layer | 1 | 0.9219 | 0.9116 | 0.3733 | -59.510% / -59.051% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 / runtime67-v4_kimi | Steady / kda / moe_layer | 2 | 0.7774 | 0.7254 | 0.6618 | -14.873% / -8.772% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 / runtime67-v4_kimi | Steady / mla / moe_layer | 1 | 0.8359 | 0.7994 | 0.6349 | -24.044% / -20.574% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 1.9490 | 1.6565 | 1.1995 | -38.453% / -27.587% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 / runtime67-v4_kimi | Steady / mla / moe_layer | 39 | 1.1795 | 1.1292 | 1.2121 | 2.769% / 7.345% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 1.4398 | 1.2987 | 1.2503 | -13.164% / -3.727% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 / runtime67-v4_kimi | Steady / mla / moe_layer | 39 | 1.2521 | 1.1883 | 1.2658 | 1.089% / 6.522% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 1.6970 | 1.5640 | 1.3459 | -20.690% / -13.946% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 / runtime67-v4_kimi | Steady / mla / moe_layer | 39 | 1.3715 | 1.3077 | 1.3664 | -0.372% / 4.486% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 / runtime67-v4_kimi | Layer 0 / mla / moe_layer | 1 | 1.6498 | 1.4734 | 1.5203 | -7.847% / 3.188% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 / runtime67-v4_kimi | Steady / mla / moe_layer | 39 | 1.5477 | 1.4627 | 1.5495 | 0.115% / 5.930% |

## Heavy >50us operators — activity residual priority

| Case | Operator / role | Calls | Real / Sim us | Diff us | Absolute ms / Forward | Tier pass |
|---|---|---:|---:|---:|---:|---|
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | GroupedMatmulSituQuant / grouped_gate_up_situ_quant | 5796 | 74.250 / 7.735 | -66.515 | 6.119 | None (reference_only) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1554 | 142.415 / 285.783 | 143.367 | 6.021 | None (reference_only) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | SituMxQuant / shared.situ_quant | 5796 | 65.155 / 1.312 | -63.843 | 5.874 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c8 / 67ca7673 / `c27d72c215c2` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 226.015 / 307.364 | 81.349 | 3.417 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 / `c27d72c215c2` | HcPre / attention.hc_pre | 2115 | 66.201 / 140.275 | 74.073 | 3.333 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 / `c27d72c215c2` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 245.405 / 320.328 | 74.923 | 3.147 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c32 / 67ca7673 / `c27d72c215c2` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2058 | 243.005 / 312.922 | 69.917 | 2.937 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 / `c27d72c215c2` | HcPre / ffn.hc_pre | 2115 | 75.216 / 140.275 | 65.059 | 2.928 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c16 / 67ca7673 / `c27d72c215c2` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2100 | 241.813 / 309.212 | 67.399 | 2.831 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c32 / 67ca7673 / `c27d72c215c2` | HcPre / attention.hc_pre | 2205 | 52.080 / 87.561 | 35.482 | 1.597 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c32 / 67ca7673 / `c27d72c215c2` | HcPre / ffn.hc_pre | 2205 | 52.730 / 87.561 | 34.831 | 1.567 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 / `c27d72c215c2` | MatMulV2 / linear_qkvbfg_a | 1598 | 64.341 / 101.405 | 37.064 | 1.260 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 / `c27d72c215c2` | HcPost / attention.hc_post_group | 2115 | 51.747 / 26.810 | -24.937 | 1.122 | False (compared) |
| a5_glm53flash_tp8_c64_p4k / 67ca7673 / `c27d72c215c2` | GroupedMatmul / expert_down | 1302 | 115.777 / 90.476 | -25.300 | 1.063 | False (compared) |
| a5_glm53flash_tp8_c32_p8k / 67ca7673 / `c27d72c215c2` | GroupedMatmul / expert_down | 1470 | 109.853 / 87.876 | -21.977 | 0.923 | False (compared) |
| a5_glm53flash_tp8_c32_p4k / 67ca7673 / `c27d72c215c2` | GroupedMatmul / expert_down | 1302 | 109.824 / 87.876 | -21.948 | 0.922 | False (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | GroupedMatmul / expert_down | 2226 | 51.524 / 34.915 | -16.609 | 0.698 | False (compared) |
| a5_glm53flash_tp8_c16_p4k / 67ca7673 / `c27d72c215c2` | GroupedMatmul / expert_down | 1260 | 103.104 / 86.575 | -16.528 | 0.694 | False (compared) |
| a5_glm53flash_tp8_c16_p8k / 67ca7673 / `c27d72c215c2` | GroupedMatmul / expert_down | 1344 | 102.724 / 86.575 | -16.149 | 0.678 | False (compared) |
| a5_glm53flash_tp8_c8_p4k / 67ca7673 / `c27d72c215c2` | GroupedMatmul / expert_down | 1260 | 91.186 / 76.439 | -14.748 | 0.619 | False (compared) |
| a5_glm53flash_tp8_c4_p8k / 67ca7673 / `c27d72c215c2` | GroupedMatmul / expert_down | 462 | 51.435 / 38.227 | -13.208 | 0.555 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 / `c27d72c215c2` | MatMulV2 / qkv_a | 517 | 56.384 / 101.486 | 45.102 | 0.496 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 / `c27d72c215c2` | MatMulV2 / index_q | 517 | 59.327 / 70.876 | 11.549 | 0.127 | False (compared) |
| a3_kimi4_tp8_w4a8_c64 / runtime67 / `c27d72c215c2` | QuantBatchMatmulV3 / gate_up | 196 | 60.636 / 89.300 | 28.664 | 0.029 | False (compared) |
| a3_kimi4_tp8_w4a8_c32 / runtime67 / `c27d72c215c2` | QuantBatchMatmulV3 / gate_up | 220 | 56.800 / 79.579 | 22.779 | 0.023 | False (compared) |
| a3_kimi4_tp8_w4a8_c16 / runtime67 / `c27d72c215c2` | QuantBatchMatmulV3 / gate_up | 235 | 55.989 / 74.718 | 18.729 | 0.019 | False (compared) |
| a3_kimi4_tp8_w4a8_c4 / runtime67 / `c27d72c215c2` | QuantBatchMatmulV3 / gate_up | 246 | 54.590 / 72.287 | 17.698 | 0.018 | False (compared) |
| a3_kimi4_tp8_w4a8_c1 / runtime67 / `c27d72c215c2` | QuantBatchMatmulV3 / gate_up | 254 | 56.548 / 72.287 | 15.739 | 0.016 | False (compared) |
| a5_kimi_tp8_e16_bf16_c32_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / gate_up | 41 | 59.157 / 52.713 | -6.444 | 0.006 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / gate_up | 46 | 59.094 / 52.713 | -6.381 | 0.006 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / gate_up | 47 | 53.443 / 47.325 | -6.118 | 0.006 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / gate_up | 49 | 53.114 / 47.325 | -5.789 | 0.006 | True (compared) |
| a3_kimi4_tp8_w4a8_c64 / runtime67 / `c27d72c215c2` | MatMulV2 / output_gate | 196 | 51.145 / 52.683 | 1.538 | 0.002 | True (compared) |

## Micro <=50us operators — activity residual priority

| Case | Operator / role | Calls | Real / Sim us | Diff us | Absolute ms / Forward | Tier pass |
|---|---|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | HcPre / attention.hc_pre | 1665 | 33.367 / 170.549 | 137.182 | 6.173 | None (reference_only) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | HcPre / ffn.hc_pre | 1665 | 36.039 / 170.549 | 134.510 | 6.053 | None (reference_only) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | QuantBatchMatmulV4 / shared.gate_up | 5796 | 30.427 / 3.963 | -26.464 | 2.435 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 / `c27d72c215c2` | QuantBatchMatmulV3 / shared.down | 1974 | 41.694 / 8.888 | -32.806 | 1.378 | False (compared) |
| a5_kimi_tp8_e16_bf16_c32_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_down | 3772 | 26.876 / 14.433 | -12.443 | 1.145 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_down | 4232 | 26.875 / 14.433 | -12.442 | 1.145 | True (compared) |
| a5_kimi_tp8_e16_bf16_c8_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / shared.gate_up | 4784 | 20.054 / 7.879 | -12.175 | 1.120 | True (compared) |
| a5_kimi_tp8_e16_bf16_c8_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / shared.gate_up | 4692 | 20.040 / 7.879 | -12.161 | 1.119 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / shared.gate_up | 4508 | 20.727 / 8.769 | -11.958 | 1.100 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / shared.gate_up | 4324 | 20.707 / 8.769 | -11.938 | 1.098 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / shared.gate_up | 4232 | 22.209 / 10.548 | -11.662 | 1.073 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / shared.gate_up | 3772 | 22.209 / 10.548 | -11.661 | 1.073 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_down | 4324 | 25.351 / 13.766 | -11.584 | 1.066 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | QuantBatchMatmulV4 / shared.down | 5796 | 13.143 / 1.578 | -11.565 | 1.064 | None (reference_only) |
| a5_kimi_tp8_e16_bf16_c16_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_down | 4508 | 25.319 / 13.766 | -11.552 | 1.063 | True (compared) |
| a5_kimi_tp8_e16_bf16_c8_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_down | 4784 | 24.439 / 12.999 | -11.440 | 1.052 | True (compared) |
| a5_kimi_tp8_e16_bf16_c8_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_down | 4692 | 24.431 / 12.999 | -11.432 | 1.052 | True (compared) |
| a5_kimi_tp8_e16_bf16_c4_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_down | 4876 | 24.291 / 12.999 | -11.292 | 1.039 | True (compared) |
| a5_kimi_tp8_e16_bf16_c4_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_down | 4784 | 24.241 / 12.999 | -11.242 | 1.034 | True (compared) |
| a5_kimi_tp8_e16_bf16_c2_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_down | 5060 | 23.910 / 12.999 | -10.911 | 1.004 | True (compared) |
| a5_kimi_tp8_e16_bf16_c2_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_down | 4968 | 23.893 / 12.999 | -10.894 | 1.002 | True (compared) |
| a5_kimi_tp8_e16_bf16_c1_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_down | 5428 | 23.858 / 12.999 | -10.859 | 0.999 | True (compared) |
| a5_kimi_tp8_e16_bf16_c1_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_down | 5428 | 23.857 / 12.999 | -10.858 | 0.999 | True (compared) |
| a3_glm53flash_tp16_aclgraph_c32 / 67ca7673 / `c27d72c215c2` | QuantBatchMatmulV3 / shared.down | 2058 | 28.641 / 5.000 | -23.641 | 0.993 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c16 / 67ca7673 / `c27d72c215c2` | HcPre / attention.hc_pre | 2250 | 39.826 / 61.206 | 21.381 | 0.962 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 / `c27d72c215c2` | HcPost / ffn.hc_post_group | 2115 | 47.315 / 26.810 | -20.505 | 0.923 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c16 / 67ca7673 / `c27d72c215c2` | HcPre / ffn.hc_pre | 2250 | 41.007 / 61.206 | 20.200 | 0.909 | None (reference_only) |
| a5_kimi_tp8_e16_bf16_c32_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_up | 3772 | 22.659 / 14.303 | -8.357 | 0.769 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_up | 4232 | 22.651 / 14.303 | -8.348 | 0.768 | True (compared) |
| a3_glm53flash_tp16_aclgraph_c32 / 67ca7673 / `c27d72c215c2` | HcPost / attention.hc_post_group | 2205 | 30.239 / 13.405 | -16.834 | 0.758 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c8 / 67ca7673 / `c27d72c215c2` | HcPre / attention.hc_pre | 2115 | 37.137 / 53.874 | 16.738 | 0.753 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c8 / 67ca7673 / `c27d72c215c2` | HcPre / ffn.hc_pre | 2115 | 37.220 / 53.874 | 16.655 | 0.749 | None (reference_only) |
| a5_kimi_tp8_e16_bf16_c16_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_up | 4508 | 21.792 / 14.180 | -7.613 | 0.700 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p16k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_up | 4324 | 21.790 / 14.180 | -7.610 | 0.700 | True (compared) |
| a3_glm53flash_tp16_aclgraph_c32 / 67ca7673 / `c27d72c215c2` | HcPost / ffn.hc_post_group | 2205 | 28.713 / 13.405 | -15.308 | 0.689 | False (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | HcPre / attention.hc_pre | 2385 | 11.753 / 26.539 | 14.787 | 0.665 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c16 / 67ca7673 / `c27d72c215c2` | QuantBatchMatmulV3 / shared.down | 2100 | 20.759 / 5.000 | -15.759 | 0.662 | False (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | HcPre / ffn.hc_pre | 2385 | 11.905 / 26.539 | 14.634 | 0.659 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c16 / 67ca7673 / `c27d72c215c2` | HcPost / attention.hc_post_group | 2250 | 21.017 / 6.703 | -14.314 | 0.644 | True (compared) |
| a5_kimi_tp8_e16_bf16_c8_p4k / runtime67 / `c27d72c215c2` | MatMulV3 / latent_up | 4784 | 21.042 / 14.118 | -6.924 | 0.637 | True (compared) |

## Highest unscored activity — coverage gaps, not zero predictions

| Case | Operator / role | Unscored calls | Unscored observed activity ms / Forward | Status |
|---|---|---:|---:|---|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs | DispatchFFNCombine / routed_ffn_native | 840 | 28.737 | reference_only |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 / runtime67-refs | DispatchFFNCombine / routed_ffn_native | 880 | 28.722 | reference_only |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 / runtime67-refs | DispatchFFNCombine / routed_ffn_native | 1920 | 28.483 | reference_only |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 / runtime67-refs | DispatchFFNCombine / routed_ffn_native | 1280 | 27.940 | reference_only |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 / runtime67-refs | DispatchFFNCombine / routed_ffn_native | 1160 | 27.761 | reference_only |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 | KvQuantSparseFlashAttentionVllm / unresolved | 517 | 17.956 | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 10.307 | reference_only |
| a3_glm53flash_tp16_aclgraph_c32 / 67ca7673 | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2058 | 10.206 | reference_only |
| a3_glm53flash_tp16_aclgraph_c16 / 67ca7673 | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2100 | 10.156 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs | GroupedMatmul / expert_up | 2920 | 10.006 | unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs | GroupedMatmul / expert_up | 3000 | 9.704 | unresolved |
| a3_glm53flash_tp16_aclgraph_c8 / 67ca7673 | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 9.493 | reference_only |
| a3_glm53flash_tp16_aclgraph_c32 / 67ca7673 | KvQuantSparseFlashAttentionVllm / unresolved | 539 | 9.128 | unresolved |
| a5_glm53flash_tp8_c64_p4k / 67ca7673 | GroupedMatmulSwigluQuantV2 / unresolved | 1302 | 8.866 | unresolved |
| a5_glm53flash_tp8_c32_p4k / 67ca7673 | GroupedMatmulSwigluQuantV2 / unresolved | 1302 | 8.730 | unresolved |
| a5_glm53flash_tp8_c32_p8k / 67ca7673 | GroupedMatmulSwigluQuantV2 / unresolved | 1470 | 8.730 | unresolved |
| a5_glm53flash_tp8_c16_p4k / 67ca7673 | GroupedMatmulSwigluQuantV2 / unresolved | 1260 | 8.662 | unresolved |
| a5_glm53flash_tp8_c16_p8k / 67ca7673 | GroupedMatmulSwigluQuantV2 / unresolved | 1344 | 8.656 | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 | RecurrentKda / unresolved | 1598 | 8.348 | unresolved |
| a5_glm53flash_tp8_c8_p4k / 67ca7673 | GroupedMatmulSwigluQuantV2 / unresolved | 1260 | 7.753 | unresolved |
| a5_kimi_tp8_e16_bf16_c4_p4k / runtime67 | MatMulV3 / unresolved | 28143 | 7.451 | unresolved |
| a5_kimi_tp8_e16_bf16_c4_p16k / runtime67 | MatMulV3 / unresolved | 27612 | 7.448 | unresolved |
| a5_kimi_tp8_e16_bf16_c2_p16k / runtime67 | MatMulV3 / unresolved | 28674 | 7.325 | unresolved |
| a5_kimi_tp8_e16_bf16_c2_p4k / runtime67 | MatMulV3 / unresolved | 29205 | 7.323 | unresolved |
| a5_kimi_tp8_e16_bf16_c1_p4k / runtime67 | MatMulV3 / unresolved | 31329 | 7.269 | unresolved |
| a5_kimi_tp8_e16_bf16_c1_p16k / runtime67 | MatMulV3 / unresolved | 31329 | 7.268 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | GroupedMatmul / unresolved | 21735 | 6.993 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | GroupedMatmulSituQuant / grouped_gate_up_situ_quant | 5796 | 6.831 | reference_only |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 | hcom_allReduce_ / attention_output_communication | 2115 | 6.713 | reference_only |
| a5_kimi_tp8_e16_bf16_c32_p16k / runtime67 | FusedInferAttentionScore / unresolved | 984 | 6.338 | reference_only |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 | hcom_allReduce_ / ffn_down_communication | 2115 | 6.083 | unresolved |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1554 | 5.981 | reference_only |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs | SparseFlashMla / unresolved | 840 | 5.957 | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 / runtime67-refs | reduce_scatterAicpuKernel / unresolved | 1920 | 5.643 | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 / runtime67-refs | reduce_scatterAicpuKernel / unresolved | 1160 | 5.633 | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 / runtime67-refs | reduce_scatterAicpuKernel / unresolved | 1280 | 5.599 | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs | reduce_scatterAicpuKernel / unresolved | 840 | 5.539 | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 / runtime67-refs | reduce_scatterAicpuKernel / unresolved | 880 | 5.507 | unresolved |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs | GroupedMatmul / expert_up | 4200 | 5.096 | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 / 67ca7673 | GroupedMatmul / expert_down | 1974 | 5.080 | unresolved |

## Source-role references — already costed work is not an extra budget

Reference differences have distinct evidence and are excluded from strict cohort accuracy counts.

| Case | Operator / region | Real / reference us | Real / Sim service ms per Forward | Residual ms | Boundary |
|---|---|---:|---:|---:|---|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 / runtime67-refs / `c27d72c215c2` | DispatchFFNCombine / routed_ffn_native / mla / ffn | 718.428 / 972.699 | 28.737 / 38.908 | 10.171 | whole_routed_ffn_decomposed_program_reference |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 / runtime67-refs / `c27d72c215c2` | DispatchFFNCombine / routed_ffn_native / mla / ffn | 694.018 / 921.873 | 27.761 / 36.875 | 9.114 | whole_routed_ffn_decomposed_program_reference |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 / runtime67-refs / `c27d72c215c2` | DispatchFFNCombine / routed_ffn_native / mla / ffn | 698.498 / 924.931 | 27.940 / 36.997 | 9.057 | whole_routed_ffn_decomposed_program_reference |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 / runtime67-refs / `c27d72c215c2` | DispatchFFNCombine / routed_ffn_native / mla / ffn | 718.046 / 940.671 | 28.722 / 37.627 | 8.905 | whole_routed_ffn_decomposed_program_reference |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 / runtime67-refs / `c27d72c215c2` | DispatchFFNCombine / routed_ffn_native / mla / ffn | 712.078 / 915.819 | 28.483 / 36.633 | 8.150 | whole_routed_ffn_decomposed_program_reference |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / linear_reduce / gdn / attention | 79.592 / 30.862 | 3.820 / 1.481 | -2.339 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gdn / ffn | 76.826 / 30.862 | 3.688 / 1.481 | -2.206 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / linear_reduce / gdn / attention | 61.908 / 25.931 | 2.972 / 1.245 | -1.727 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / linear_reduce / gdn / attention | 81.530 / 48.606 | 3.913 / 2.333 | -1.580 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / linear_reduce / gdn / attention | 58.791 / 32.514 | 2.822 / 1.561 | -1.261 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / linear_reduce / gdn / attention | 38.341 / 15.816 | 1.840 / 0.759 | -1.081 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gdn / ffn | 34.882 / 15.816 | 1.674 / 0.759 | -0.915 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp_attn / gqa / attention | 79.629 / 30.862 | 1.274 / 0.494 | -0.780 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / tp / gdn / ffn | 64.239 / 48.606 | 3.083 / 2.333 | -0.750 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gqa / ffn | 76.434 / 30.862 | 1.223 / 0.494 | -0.729 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs / `c27d72c215c2` | HcPre / attention.hc_pre / mla / attention | 12.178 / 26.538 | 0.487 / 1.062 | 0.574 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs / `c27d72c215c2` | HcPre / ffn.hc_pre / mla / ffn | 12.209 / 26.538 | 0.488 / 1.062 | 0.573 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 29.224 / 1.578 | 0.584 / 0.032 | -0.553 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 29.623 / 3.156 | 0.592 / 0.063 | -0.529 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 31.372 / 6.312 | 0.627 / 0.126 | -0.501 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 29.070 / 1.578 | 0.523 / 0.028 | -0.495 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 29.915 / 3.156 | 0.538 / 0.057 | -0.482 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 30.876 / 6.312 | 0.556 / 0.114 | -0.442 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 33.567 / 12.624 | 0.671 / 0.252 | -0.419 | source_symbol_to_declared_attention_program |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 28.389 / 3.542 | 0.454 / 0.057 | -0.398 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / tp_attn / gqa / attention | 73.299 / 48.606 | 1.173 / 0.778 | -0.395 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / `c27d72c215c2` | HcPre / ffn.hc_pre / mla / ffn | 11.660 / 21.524 | 0.466 / 0.861 | 0.395 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / `c27d72c215c2` | HcPre / attention.hc_pre / mla / attention | 11.719 / 21.524 | 0.469 / 0.861 | 0.392 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 33.893 / 12.624 | 0.610 / 0.227 | -0.383 | source_symbol_to_declared_attention_program |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 26.844 / 3.148 | 0.429 / 0.050 | -0.379 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / linear_reduce / gdn / attention | 18.655 / 11.427 | 0.895 / 0.548 | -0.347 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp_attn / gqa / attention | 36.991 / 15.816 | 0.592 / 0.253 | -0.339 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 8.186 / 1.312 | 0.393 / 0.063 | -0.330 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs / `c27d72c215c2` | HcPre / ffn.hc_pre / mla / ffn | 11.183 / 19.016 | 0.447 / 0.761 | 0.313 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs / `c27d72c215c2` | HcPre / attention.hc_pre / mla / attention | 11.294 / 19.016 | 0.452 / 0.761 | 0.309 | partial_base_program_reference_premix_branch_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gqa / ffn | 34.787 / 15.816 | 0.557 / 0.253 | -0.304 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs / `c27d72c215c2` | HcPre / attention.hc_pre / mla / attention | 10.537 / 17.136 | 0.421 / 0.685 | 0.264 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs / `c27d72c215c2` | HcPre / attention.hc_pre / mla / attention | 10.538 / 17.136 | 0.422 / 0.685 | 0.264 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs / `c27d72c215c2` | HcPre / attention.hc_pre / mla / attention | 10.593 / 17.136 | 0.424 / 0.685 | 0.262 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs / `c27d72c215c2` | HcPre / ffn.hc_pre / mla / ffn | 10.636 / 17.136 | 0.425 / 0.685 | 0.260 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs / `c27d72c215c2` | HcPre / ffn.hc_pre / mla / ffn | 10.636 / 17.136 | 0.425 / 0.685 | 0.260 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs / `c27d72c215c2` | HcPre / ffn.hc_pre / mla / ffn | 10.687 / 17.136 | 0.427 / 0.685 | 0.258 | partial_base_program_reference_premix_branch_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 6.519 / 1.312 | 0.313 / 0.063 | -0.250 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gdn / ffn | 16.614 / 11.427 | 0.797 / 0.548 | -0.249 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / tp / gqa / ffn | 63.948 / 48.606 | 1.023 / 0.778 | -0.245 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs / `c27d72c215c2` | HcPre / attention.hc_pre / mla / attention | 11.736 / 17.763 | 0.469 / 0.711 | 0.241 | partial_base_program_reference_premix_branch_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 3.779 / 1.312 | 0.363 / 0.126 | -0.237 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs / `c27d72c215c2` | HcPre / ffn.hc_pre / mla / ffn | 11.978 / 17.763 | 0.479 / 0.711 | 0.231 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 35.488 / 25.248 | 0.710 / 0.505 | -0.205 | source_symbol_to_declared_attention_program |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / tp / gdn / ffn | 21.976 / 25.931 | 1.055 / 1.245 | 0.190 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 5.123 / 1.312 | 0.246 / 0.063 | -0.183 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 13.451 / 2.788 | 0.215 / 0.045 | -0.171 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 10.067 / 1.578 | 0.201 / 0.032 | -0.170 | source_symbol_to_declared_attention_program |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 3.075 / 1.312 | 0.295 / 0.126 | -0.169 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 9.938 / 1.578 | 0.199 / 0.032 | -0.167 | source_symbol_to_declared_attention_program |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 4.702 / 1.312 | 0.226 / 0.063 | -0.163 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 34.016 / 25.248 | 0.612 / 0.454 | -0.158 | source_symbol_to_declared_attention_program |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 2.769 / 1.312 | 0.266 / 0.126 | -0.140 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 9.205 / 1.578 | 0.166 / 0.028 | -0.137 | source_symbol_to_declared_attention_program |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 11.381 / 2.853 | 0.182 / 0.046 | -0.136 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 9.116 / 1.578 | 0.164 / 0.028 | -0.136 | source_symbol_to_declared_attention_program |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 3.803 / 1.312 | 0.183 / 0.063 | -0.120 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 2.429 / 1.312 | 0.233 / 0.126 | -0.107 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 3.375 / 1.312 | 0.162 / 0.063 | -0.099 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp_attn / gqa / attention | 16.753 / 11.427 | 0.268 / 0.183 | -0.085 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gqa / ffn | 16.735 / 11.427 | 0.268 / 0.183 | -0.085 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / tp / gdn / ffn | 30.927 / 32.514 | 1.484 / 1.561 | 0.076 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 2.102 / 1.312 | 0.202 / 0.126 | -0.076 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / tp / gqa / ffn | 21.989 / 25.931 | 0.352 / 0.415 | 0.063 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 6.254 / 2.653 | 0.100 / 0.042 | -0.058 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / tp_attn / gqa / attention | 35.826 / 32.514 | 0.573 / 0.520 | -0.053 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 1.817 / 1.312 | 0.174 / 0.126 | -0.049 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 5.634 / 2.640 | 0.090 / 0.042 | -0.048 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / tp / gqa / ffn | 30.577 / 32.514 | 0.489 / 0.520 | 0.031 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / tp_attn / gqa / attention | 24.240 / 25.931 | 0.388 / 0.415 | 0.027 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 11.092 / 1.578 | 0.022 / 0.003 | -0.019 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 11.257 / 3.156 | 0.023 / 0.006 | -0.016 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 13.400 / 6.312 | 0.027 / 0.013 | -0.014 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 8.170 / 1.578 | 0.016 / 0.003 | -0.013 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 7.891 / 1.578 | 0.016 / 0.003 | -0.013 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 19.397 / 25.248 | 0.039 / 0.050 | 0.012 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / `c27d72c215c2` | MqsmlaKernel___call__ / attention_core / mla / attention | 16.005 / 12.624 | 0.032 / 0.025 | -0.007 | source_symbol_to_declared_attention_program |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | DynamicQuantV2 /  / gdn / attention | 7.494 / — | 0.360 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gdn / ffn | 15.340 / — | 0.736 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | DynamicQuantV2 /  / gdn / ffn | 6.140 / — | 0.295 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | AddRmsNorm /  / gdn / attention | 8.789 / — | 0.413 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gqa / attention | 12.148 / — | 0.194 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | DynamicQuantV2 /  / gqa / attention | 5.567 / — | 0.089 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gqa / ffn | 12.621 / — | 0.202 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | DynamicQuantV2 /  / gqa / ffn | 5.743 / — | 0.092 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | DynamicQuantV2 /  / gdn / attention | 4.049 / — | 0.194 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gdn / ffn | 5.429 / — | 0.261 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | DynamicQuantV2 /  / gdn / ffn | 3.877 / — | 0.186 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | AddRmsNorm /  / gdn / attention | 4.089 / — | 0.192 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gqa / attention | 5.434 / — | 0.087 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | DynamicQuantV2 /  / gqa / attention | 3.762 / — | 0.060 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gqa / ffn | 5.422 / — | 0.087 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | DynamicQuantV2 /  / gqa / ffn | 3.911 / — | 0.063 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | DynamicQuantV2 /  / gdn / attention | 6.016 / — | 0.289 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gdn / ffn | 9.468 / — | 0.454 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | DynamicQuantV2 /  / gdn / ffn | 5.528 / — | 0.265 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | AddRmsNorm /  / gdn / attention | 6.297 / — | 0.296 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gqa / attention | 8.251 / — | 0.132 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | DynamicQuantV2 /  / gqa / attention | 4.893 / — | 0.078 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | AddRmsNormDynamicQuant /  / gqa / ffn | 8.525 / — | 0.136 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | DynamicQuantV2 /  / gqa / ffn | 5.228 / — | 0.084 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gdn / ffn | 14.009 / — | 0.672 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | AddRmsNorm /  / gdn / attention | 9.873 / — | 0.464 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gqa / attention | 12.301 / — | 0.197 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gqa / ffn | 12.340 / — | 0.197 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gdn / ffn | 7.733 / — | 0.371 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | AddRmsNorm /  / gdn / attention | 5.956 / — | 0.280 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gqa / attention | 7.146 / — | 0.114 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gqa / ffn | 7.275 / — | 0.116 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gdn / ffn | 4.405 / — | 0.211 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | AddRmsNorm /  / gdn / attention | 4.302 / — | 0.202 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gqa / attention | 4.180 / — | 0.067 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant /  / gqa / ffn | 4.141 / — | 0.066 / — | — | boundary_unresolved |

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
- [body-communication-references.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-high-concurrency/body-communication-references.json), SHA256 `dd98c1ba7677ea8d5ef9ea1670c69937a4f8fa2e24ec096c7392c3440ace0caa`

Additional coverage/source evidence (not silently promoted into body or operator predictions):

- [v41-existing-assets-20261030.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/v41-existing-assets-20261030.json), SHA256 `797183bf8f17978a219a4b96d8340de4b4a01442f66ae48b028aeb130be3f88f`
- [glm-three-level-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm/glm-three-level-evidence.json), SHA256 `f008c591bd6749b522d4500e047629bcd4f30438e54858c90ec5183c458a9f9a`
- [retained-source-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm78-v41/retained-source-evidence.json), SHA256 `cd28e3e6433de424c43d24327d7ad0b08e2ef27eb47cd9410a7bd8fa9fbb30ca`
- [decode-forward-auto-acceptance.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm78-v41/decode-forward-auto-acceptance.json), SHA256 `8241478fcadddf83641ca52edc1f622a624b2d50c57c60394447ca70eec0b18e`
- [retained-source-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-bundle0406/retained-source-evidence.json), SHA256 `ed8e523f3eea92aa697146085cb187258edbbe5d85ccca9d170e81b4efa98301`
- [retained-source-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-additional13/retained-source-evidence.json), SHA256 `38c9678eea4ccb217f9a20aad70896ccc649bd75177e4e9a91a0a50e8f93c57c`
- [c8-outlier-task-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-dp8/c8-outlier-task-evidence.json), SHA256 `75644791187c397dec4dd147ef75b2c1f77074e96148ab687b1305d4c458ba14`

- Rows retain their own source/runtime/geometry; independently produced receipts are not merged into a synthetic run.
- Per-forward kernel activity residual ranks work to investigate; overlap prevents interpreting its sum as body wall-clock error.
- Unscored activity is a matching/model-boundary coverage gap, not proof that Sim omitted the corresponding work.
- Layer median-of-call-P50 and exact pooled P50 are distinct populations.
