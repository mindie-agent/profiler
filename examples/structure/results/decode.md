# Current profiling validation

One canonical case registry and one recorded Sim package. All costs are fresh in this run. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.

| Case | Phase | Calls | Real mean / P50 / P90 ms | Sim ms | Error | Status |
|---|---|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c4-livepre | decode | 46 | 29.762 / 29.664 / 30.046 | 30.314 | +1.86% | PASS |
| glm53flash-a3-tp16-c16-livepre | decode | 37 | 41.069 / 40.940 / 41.282 | 44.390 | +8.09% | PASS |
| glm53flash-a3-tp16-c2 | decode | 46 | 34.118 / 33.910 / 35.073 | 31.755 | -6.93% | PASS |
| glm53flash-a3-tp16-c4 | decode | 46 | 39.841 / 39.798 / 40.057 | 36.959 | -7.24% | PASS |
| glm53flash-a5-tp8-c3 | decode | 53 | 21.068 / 21.057 / 21.170 | 20.811 | -1.22% | PASS |
| glm53flash-a5-tp8-c96 | decode | 27 | 57.590 / 57.573 / 57.734 | 61.998 | +7.65% | PASS |
| glm53flash-a5-tp8-c1 | decode | 65 | 15.683 / 15.670 / 15.738 | 15.462 | -1.41% | PASS |
| a5_kimi_k3_p32768_c1 | decode | 63 | 32.555 / 32.533 / 32.674 | 32.151 | -1.24% | PASS |
| v4flash-a3-tp8-c4 | decode | 104 | 32.486 / 32.416 / 32.734 | 29.272 | -9.89% | PASS |
| v4flash-a3-tp8-c8 | decode | 104 | 37.763 / 37.868 / 38.082 | 34.707 | -8.09% | PASS |
| a3_glm53_dc4k_b1 | decode | 74 | 38.955 / 38.943 / 39.036 | 38.046 | -2.33% | PASS |
| a3_glm53_dc4k_b2 | decode | 70 | 40.970 / 40.935 / 41.046 | 39.767 | -2.94% | PASS |
| a3_glm53_dc4k_b4 | decode | 67 | 43.438 / 43.437 / 43.598 | 42.943 | -1.14% | PASS |
| a3_glm53_dc4k_b8 | decode | 61 | 47.113 / 47.149 / 47.402 | 44.125 | -6.34% | PASS |
| a3_glm53_dc16k_b1 | decode | 74 | 39.112 / 39.105 / 39.196 | 38.334 | -1.99% | PASS |
| qwen35-397b-a3-tp16-c48 | decode | 23 | 76.089 / 76.132 / 76.632 | 75.153 | -1.23% | PASS |
| qwen35-397b-a3-tp16-c136 | decode | 18 | 119.054 / 119.131 / 119.486 | 117.659 | -1.17% | PASS |
| qwen35-35b-a5-tp4-c64-graph | decode | 79 | 21.957 / 22.001 / 22.068 | 19.975 | -9.03% | PASS |
| qwen35-35b-a5-tp4-c128-graph | decode | 76 | 28.585 / 28.571 / 28.704 | 26.059 | -8.83% | PASS |
| qwen35-35b-a5-tp4-c4-graph | decode | 84 | 11.551 / 11.482 / 11.818 | 11.401 | -1.30% | PASS |
| qwen36-a5-tp2-c12 | decode | 55 | 24.226 / 24.053 / 24.711 | 23.954 | -1.12% | PASS |
| qwen36-a5-tp2-c96 | decode | 24 | 63.853 / 63.562 / 65.419 | 62.838 | -1.59% | PASS |
| qwen36-a5-tp2-c1 | decode | 85 | 12.318 / 12.279 / 12.362 | 12.284 | -0.28% | PASS |
| a3_glm53_w4a8_tp16_tpot30_c2 | decode | 44 | 57.639 / 57.562 / 58.995 | 56.941 | -1.21% | PASS |
| a3_glm53_w4a8_tp16_tpot50_c2 | decode | 44 | 57.817 / 57.597 / 59.092 | 57.179 | -1.10% | PASS |
| a3_glm53_w4a8_tp16_tpot88_c8 | decode | 49 | 69.556 / 69.489 / 69.830 | 66.764 | -4.01% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | decode | 152 | 13.135 / 13.129 / 13.145 | 12.436 | -5.32% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | decode | 145 | 13.292 / 12.803 / 12.817 | 12.155 | -8.55% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | decode | 75 | 26.328 / 26.306 / 26.336 | 24.812 | -5.76% | PASS |
| a5_glm53flash_tp8_c16_p4k | decode | 30 | 33.031 / 33.026 / 33.164 | 32.563 | -1.42% | PASS |
| a5_glm53flash_tp8_c16_p8k | decode | 32 | 33.616 / 33.626 / 33.710 | 33.073 | -1.62% | PASS |
| a5_glm53flash_tp8_c32_p4k | decode | 31 | 37.669 / 37.665 / 37.761 | 34.590 | -8.17% | PASS |
| a5_glm53flash_tp8_c32_p8k | decode | 35 | 38.713 / 38.722 / 38.759 | 38.095 | -1.60% | PASS |
| a5_glm53flash_tp8_c4_p8k | decode | 11 | 21.418 / 21.408 / 21.432 | 21.082 | -1.57% | PASS |
| a5_glm53flash_tp8_c64_p4k | decode | 31 | 46.528 / 46.499 / 46.645 | 45.975 | -1.19% | PASS |
| a5_glm53flash_tp8_c8_p4k | decode | 30 | 28.833 / 28.828 / 28.885 | 28.384 | -1.56% | PASS |
| a3_glm53flash_tp16_aclgraph_c16 | decode | 50 | 53.893 / 53.871 / 54.021 | 49.051 | -8.99% | PASS |
| a3_glm53flash_tp16_aclgraph_c32 | decode | 49 | 69.361 / 69.418 / 69.528 | 64.395 | -7.16% | PASS |
| a3_glm53flash_tp16_aclgraph_c64 | decode | 47 | 97.375 / 97.487 / 97.895 | 96.015 | -1.40% | PASS |
| a3_glm53flash_tp16_aclgraph_c8 | decode | 47 | 46.859 / 46.817 / 47.175 | 46.362 | -1.06% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k | decode | 129 | 14.929 / 14.914 / 14.929 | 13.749 | -7.91% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k | decode | 105 | 18.625 / 18.616 / 18.640 | 17.361 | -6.78% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k | decode | 151 | 13.239 / 13.209 / 13.227 | 12.550 | -5.21% | PASS |
| a3_kimi4_tp8_w4a8_c1 | decode | 254 | 3.180 / 3.128 / 3.432 | 3.238 | +1.82% | PASS |
| a3_kimi4_tp8_w4a8_c16 | decode | 235 | 4.807 / 4.779 / 4.992 | 4.918 | +2.31% | PASS |
| a3_kimi4_tp8_w4a8_c32 | decode | 220 | 6.714 / 6.665 / 6.923 | 6.097 | -9.19% | PASS |
| a3_kimi4_tp8_w4a8_c4 | decode | 246 | 3.476 / 3.438 / 3.656 | 3.196 | -8.07% | PASS |
| a3_kimi4_tp8_w4a8_c64 | decode | 196 | 9.615 / 9.550 / 9.774 | 8.699 | -9.53% | PASS |
| a5_kimi_tp8_e16_bf16_c16_p16k | decode | 47 | 39.247 / 39.245 / 39.263 | 40.764 | +3.86% | PASS |
| a5_kimi_tp8_e16_bf16_c16_p4k | decode | 49 | 36.985 / 36.953 / 36.969 | 38.388 | +3.79% | PASS |
| a5_kimi_tp8_e16_bf16_c1_p16k | decode | 59 | 30.823 / 30.822 / 30.839 | 31.866 | +3.38% | PASS |
| a5_kimi_tp8_e16_bf16_c1_p4k | decode | 59 | 30.637 / 30.615 / 30.632 | 31.672 | +3.38% | PASS |
| a5_kimi_tp8_e16_bf16_c2_p16k | decode | 54 | 33.876 / 33.858 / 33.873 | 34.119 | +0.72% | PASS |
| a5_kimi_tp8_e16_bf16_c2_p4k | decode | 55 | 33.548 / 33.516 / 33.533 | 33.778 | +0.69% | PASS |
| a5_kimi_tp8_e16_bf16_c32_p16k | decode | 41 | 44.666 / 44.645 / 44.662 | 41.963 | -6.05% | PASS |
| a5_kimi_tp8_e16_bf16_c32_p4k | decode | 46 | 40.019 / 40.018 / 40.044 | 36.969 | -7.62% | PASS |
| a5_kimi_tp8_e16_bf16_c4_p16k | decode | 52 | 34.816 / 34.794 / 34.813 | 35.074 | +0.74% | PASS |
| a5_kimi_tp8_e16_bf16_c4_p4k | decode | 53 | 34.194 / 34.177 / 34.194 | 34.462 | +0.78% | PASS |
| a5_kimi_tp8_e16_bf16_c8_p16k | decode | 51 | 35.964 / 35.962 / 35.979 | 37.585 | +4.51% | PASS |
| a5_kimi_tp8_e16_bf16_c8_p4k | decode | 52 | 34.819 / 34.791 / 34.808 | 36.421 | +4.60% | PASS |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 | decode | 32 | 49.985 / 49.802 / 50.230 | 52.474 | +4.98% | PASS |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | decode | 22 | 54.967 / 54.880 / 55.047 | 55.972 | +1.83% | PASS |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 | decode | 48 | 47.654 / 47.425 / 47.666 | 50.270 | +5.49% | PASS |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | decode | 21 | 61.811 / 61.629 / 62.042 | 63.580 | +2.86% | PASS |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | decode | 29 | 48.582 / 48.412 / 48.662 | 51.673 | +6.36% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k | decode | 73 | 27.286 / 27.266 / 27.290 | 25.540 | -6.40% | PASS |
| qwen35-35b-a3-tp4-c144 | decode | 25 | 61.750 / 61.784 / 62.102 | 60.933 | -1.32% | PASS |
| qwen35-35b-a3-tp4-c320 | decode | 21 | 99.692 / 99.679 / 100.090 | 94.185 | -5.52% | PASS |
| qwen36-a3-tp4-c64 | decode | 27 | 62.520 / 62.407 / 62.858 | 61.622 | -1.44% | PASS |
| qwen36-a3-tp4-c128 | decode | 22 | 97.566 / 97.506 / 97.890 | 89.346 | -8.42% | PASS |
| qwen38-a3-tp4-c64 | decode | 27 | 62.648 / 62.586 / 63.058 | 61.622 | -1.64% | PASS |
| qwen38-a3-tp4-c128 | decode | 22 | 97.457 / 97.455 / 97.787 | 89.346 | -8.32% | PASS |
| a5_qwen36_highconc_c4 | decode | 73 | 13.342 / 13.245 / 13.485 | 13.450 | +0.81% | PASS |
| a5_qwen36_highconc_c40 | decode | 54 | 20.684 / 20.612 / 21.334 | 20.447 | -1.15% | PASS |
| a5_qwen36_highconc_c128 | decode | 38 | 32.609 / 32.227 / 33.851 | 31.914 | -2.13% | PASS |
| a5_qwen38_highconc_c4 | decode | 45 | 13.027 / 13.005 / 13.167 | 13.140 | +0.87% | PASS |
| a5_qwen38_highconc_c32 | decode | 48 | 22.791 / 22.711 / 22.894 | 22.556 | -1.03% | PASS |
| a5_qwen38_highconc_c128 | decode | 29 | 45.689 / 45.690 / 45.735 | 45.941 | +0.55% | PASS |
| a3_glm53flash_heldout_c12_p4k | decode | 13 | 23.412 / 23.008 / 23.288 | 22.631 | -3.34% | PASS |
| a3_glm53flash_heldout_c24_p12k | decode | 14 | 23.601 / 23.242 / 23.719 | 22.647 | -4.04% | PASS |
| a5_glm53flash_heldout_c12_p4k | decode | 20 | 18.133 / 18.108 / 18.148 | 17.908 | -1.24% | PASS |
| a5_glm53flash_heldout_c24_p12k | decode | 21 | 38.995 / 39.210 / 39.263 | 38.456 | -1.38% | PASS |
| a5_glm53flash_heldout_c48_p4k | decode | 26 | 43.228 / 43.355 / 43.400 | 41.035 | -5.07% | PASS |
| a3_glm53flash_static_on_c10_p131201 | decode | 68 | 22.603 / 22.348 / 23.552 | 22.621 | +0.08% | PASS |
| a3-qwen35-tp4-longctx-p-126976-c1 | decode | 65 | 16.054 / 16.058 / 16.121 | 15.829 | -1.40% | PASS |
| a3-qwen35-tp4-longctx-p-126976-c4 | decode | 34 | 20.465 / 20.804 / 20.975 | 20.144 | -1.57% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c1 | decode | 64 | 15.530 / 15.511 / 15.646 | 15.298 | -1.50% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c2 | decode | 55 | 16.750 / 16.724 / 16.909 | 16.259 | -2.93% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c4 | decode | 50 | 18.893 / 18.984 / 19.070 | 18.252 | -3.39% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c8 | decode | 32 | 21.417 / 21.608 / 22.212 | 21.901 | +2.26% | PASS |
| a3-qwen36-tp4-longctx-p-126976-c1 | decode | 10 | 18.924 / 18.932 / 19.020 | 18.786 | -0.73% | PASS |
| a3-qwen36-tp4-longctx-p-126976-c4 | decode | 47 | 27.951 / 27.941 / 28.060 | 27.398 | -1.98% | PASS |
| a3-qwen36-tp4-longctx-p-65536-c1 | decode | 15 | 18.048 / 17.939 / 18.590 | 17.808 | -1.33% | PASS |
| a3-qwen36-tp4-longctx-p-65536-c4 | decode | 49 | 24.880 / 24.783 / 25.010 | 24.223 | -2.64% | PASS |
| a5-qwen35-tp4-longctx-p126976-c1-hold | decode | 161 | 18.202 / 18.181 / 18.223 | 18.945 | +4.08% | PASS |
| a5-qwen35-tp4-longctx-p126976-c1-o32 | decode | 9 | 19.345 / 18.879 / 23.000 | 18.945 | -2.07% | PASS |
| a5-qwen35-tp4-longctx-p126976-c4-hold | decode | 221 | 20.420 / 20.404 / 20.494 | 20.225 | -0.95% | PASS |
| a5-qwen35-tp4-longctx-p126976-c4-o32 | decode | 11 | 18.132 / 18.133 / 18.193 | 18.945 | +4.48% | PASS |
| a5-qwen35-tp4-longctx-p65536-c1-hold | decode | 196 | 13.678 / 13.649 / 13.717 | 14.179 | +3.66% | PASS |
| a5-qwen35-tp4-longctx-p65536-c1-o32 | decode | 11 | 13.892 / 13.921 / 14.105 | 14.179 | +2.06% | PASS |
| a5-qwen35-tp4-longctx-p65536-c4-hold | decode | 222 | 15.799 / 15.771 / 15.885 | 15.459 | -2.15% | PASS |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | decode | 10 | 14.477 / 14.397 / 14.516 | 14.179 | -2.06% | PASS |
| a5-qwen38-tp1-longctx-p126976-c4 | decode | 9 | 32.215 / 32.211 / 32.237 | 31.774 | -1.37% | PASS |
| a5-qwen38-tp1-longctx-p65536-c4 | decode | 5 | 24.481 / 24.481 / 24.493 | 24.148 | -1.36% | PASS |
| a5-qwen36-tp8-longctx-p126976-c1-hold | decode | 121 | 25.271 / 25.202 / 25.297 | 26.174 | +3.57% | PASS |
| a5-qwen36-tp8-longctx-p126976-c4-hold | decode | 176 | 26.646 / 26.650 / 26.767 | 26.800 | +0.57% | PASS |
| a5-qwen36-tp8-longctx-p65536-c1-hold | decode | 137 | 17.801 / 17.796 / 17.900 | 18.548 | +4.20% | PASS |
| a5-qwen36-tp8-longctx-p65536-c4-hold | decode | 183 | 19.130 / 19.111 / 19.217 | 19.174 | +0.23% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | decode | 242 | 3.397 / 3.323 / 3.643 | 3.620 | +6.57% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | decode | 228 | 6.922 / 6.899 / 7.128 | 6.702 | -3.18% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | decode | 198 | 8.287 / 8.231 / 8.548 | 7.631 | -7.91% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | decode | 240 | 3.593 / 3.568 / 3.831 | 3.837 | +6.79% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | decode | 153 | 10.962 / 10.873 / 11.210 | 10.214 | -6.83% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | decode | 124 | 13.725 / 13.665 / 13.952 | 12.862 | -6.29% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | decode | 243 | 4.403 / 4.366 / 4.615 | 4.271 | -2.99% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | decode | 91 | 19.074 / 19.036 / 19.275 | 18.100 | -5.10% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | decode | 233 | 4.795 / 4.727 / 5.001 | 4.711 | -1.75% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | decode | 74 | 23.694 / 23.656 / 23.841 | 22.642 | -4.44% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | decode | 236 | 5.467 / 5.396 / 5.675 | 5.011 | -8.35% | PASS |
| a3-kimi4-tp8-longctx-decode-c12-p16k | decode | 189 | 4.435 / 4.402 / 4.659 | 4.669 | +5.27% | PASS |
| a3-kimi4-tp8-longctx-decode-c12-p32k | decode | 189 | 4.621 / 4.558 / 4.808 | 4.997 | +8.12% | PASS |
| a3-kimi4-tp8-longctx-decode-c12-p4k | decode | 191 | 4.229 / 4.195 / 4.479 | 4.419 | +4.48% | PASS |
| a3-kimi4-tp8-longctx-decode-c12-p8k | decode | 190 | 4.249 / 4.217 / 4.437 | 4.504 | +6.00% | PASS |
| a3-kimi4-tp8-longctx-decode-c24-p16k | decode | 190 | 6.096 / 6.046 / 6.322 | 5.932 | -2.70% | PASS |
| a3-kimi4-tp8-longctx-decode-c24-p32k | decode | 193 | 6.437 / 6.353 / 6.658 | 6.583 | +2.27% | PASS |
| a3-kimi4-tp8-longctx-decode-c24-p4k | decode | 200 | 5.641 / 5.582 / 5.874 | 5.446 | -3.46% | PASS |
| a3-kimi4-tp8-longctx-decode-c24-p8k | decode | 195 | 5.829 / 5.787 / 6.088 | 5.612 | -3.72% | PASS |
| a3-kimi4-tp8-longctx-decode-c2-p4k | decode | 200 | 3.285 / 3.243 / 3.520 | 3.424 | +4.23% | PASS |
| a3-kimi4-tp8-longctx-decode-c48-p4k | decode | 159 | 8.472 / 8.430 / 8.705 | 8.600 | +1.51% | PASS |
| a3-kimi4-tp8-longctx-decode-c6-p4k | decode | 186 | 3.701 / 3.632 / 3.935 | 3.491 | -5.68% | PASS |
| a3-kimi4-tp8-longctx-decode-c8-p4k | decode | 191 | 3.839 / 3.765 / 4.168 | 3.522 | -8.25% | PASS |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | decode | 228 | 4.093 / 3.992 / 4.443 | 4.387 | +7.19% | PASS |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | decode | 207 | 6.865 / 6.792 / 7.109 | 6.546 | -4.65% | PASS |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | decode | 206 | 7.840 / 7.747 / 8.108 | 7.437 | -5.14% | PASS |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | decode | 232 | 4.362 / 4.303 / 4.648 | 4.596 | +5.35% | PASS |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | decode | 167 | 10.062 / 10.014 / 10.358 | 9.754 | -3.07% | PASS |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | decode | 138 | 12.295 / 12.243 / 12.550 | 11.409 | -7.21% | PASS |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | decode | 226 | 5.008 / 4.905 / 5.299 | 5.009 | +0.03% | PASS |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | decode | 103 | 16.734 / 16.715 / 16.992 | 15.361 | -8.21% | PASS |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | decode | 222 | 5.264 / 5.192 / 5.571 | 5.445 | +3.45% | PASS |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | decode | 83 | 20.942 / 20.922 / 21.125 | 19.205 | -8.29% | PASS |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | decode | 212 | 5.865 / 5.802 / 6.140 | 5.727 | -2.35% | PASS |
| a3-kimi4-tp16-128k-decode-c12-p16k | decode | 180 | 4.430 / 4.375 / 4.726 | 4.563 | +2.99% | PASS |
| a3-kimi4-tp16-128k-decode-c12-p32k | decode | 178 | 4.659 / 4.586 / 4.886 | 4.886 | +4.89% | PASS |
| a3-kimi4-tp16-128k-decode-c12-p4k | decode | 162 | 4.439 / 4.155 / 4.610 | 4.315 | -2.79% | PASS |
| a3-kimi4-tp16-128k-decode-c12-p8k | decode | 173 | 4.379 / 4.203 / 4.614 | 4.399 | +0.47% | PASS |
| a3-kimi4-tp16-128k-decode-c24-p16k | decode | 175 | 5.260 / 5.124 / 5.362 | 5.576 | +6.02% | PASS |
| a3-kimi4-tp16-128k-decode-c24-p32k | decode | 186 | 5.661 / 5.606 / 5.932 | 6.214 | +9.77% | PASS |
| a3-kimi4-tp16-128k-decode-c24-p4k | decode | 177 | 4.841 / 4.788 / 5.056 | 5.096 | +5.28% | PASS |
| a3-kimi4-tp16-128k-decode-c24-p8k | decode | 179 | 4.939 / 4.913 / 5.134 | 5.261 | +6.52% | PASS |
| a3-kimi4-tp16-128k-decode-c2-p4k | decode | 186 | 4.055 / 3.989 / 4.321 | 4.189 | +3.30% | PASS |
| a3-kimi4-tp16-128k-decode-c48-p4k | decode | 172 | 6.201 / 6.157 / 6.393 | 6.033 | -2.71% | PASS |
| a3-kimi4-tp16-128k-decode-c6-p4k | decode | 181 | 4.110 / 4.033 / 4.408 | 4.248 | +3.37% | PASS |
| a3-kimi4-tp16-128k-decode-c8-p4k | decode | 183 | 4.188 / 4.058 / 4.447 | 4.271 | +1.99% | PASS |
| a5_kimi_tp8_e16_bf16_128k_c1 | decode | 56 | 32.485 / 32.470 / 32.485 | 32.895 | +1.26% | PASS |
| a5_kimi_tp8_e16_bf16_128k_c2 | decode | 50 | 36.854 / 36.840 / 36.856 | 34.691 | -5.87% | PASS |
| a5_kimi_tp8_e16_bf16_128k_c4 | decode | 45 | 40.416 / 40.391 / 40.420 | 38.093 | -5.75% | PASS |
| a5_kimi_tp8_e16_bf16_128k_c6 | decode | 42 | 43.589 / 43.560 / 43.578 | 41.533 | -4.72% | PASS |
| a5_kimi_tp8_e16_bf16_128k_c8 | decode | 40 | 46.691 / 46.673 / 46.694 | 44.890 | -3.86% | PASS |
| a5_kimi_tp8_e16_bf16_128k_c12 | decode | 34 | 54.147 / 54.132 / 54.160 | 52.914 | -2.28% | PASS |
| a3-v41-tp4dp4-128k-c12 | decode | 82 | 54.204 / 54.120 / 54.263 | 52.970 | -2.28% | PASS |
| a3-v41-tp4dp4-128k-c16 | decode | 81 | 54.432 / 54.359 / 54.566 | 52.970 | -2.69% | PASS |
| a3-v41-tp4dp4-128k-c24 | decode | 78 | 56.274 / 56.219 / 56.324 | 56.478 | +0.36% | PASS |
| a3-v41-tp4dp4-128k-c32 | decode | 76 | 57.786 / 57.711 / 57.953 | 57.688 | -0.17% | PASS |
| a3-v41-tp4dp4-128k-c4 | decode | 85 | 53.220 / 53.218 / 53.339 | 50.909 | -4.34% | PASS |
| a3-v41-tp4dp4-128k-c48 | decode | 61 | 74.011 / 73.921 / 74.097 | 74.516 | +0.68% | PASS |
| a3-v41-tp4dp4-128k-c64 | decode | 58 | 77.498 / 77.469 / 77.623 | 78.329 | +1.07% | PASS |
| a3-v41-tp4dp4-128k-c8 | decode | 82 | 53.618 / 53.549 / 53.745 | 51.898 | -3.21% | PASS |
| a3-qwen35-tp4-decode-c1-p126000 | decode | 169 | 17.505 / 17.528 / 17.656 | 17.423 | -0.47% | PASS |
| a3-qwen35-tp4-decode-c12-p126000 | decode | 97 | 36.173 / 36.158 / 36.304 | 34.835 | -3.70% | PASS |
| a3-qwen35-tp4-decode-c16-p126000 | decode | 87 | 40.651 / 40.639 / 40.884 | 39.626 | -2.52% | PASS |
| a3-qwen35-tp4-decode-c2-p126000 | decode | 156 | 19.585 / 19.593 / 19.734 | 19.058 | -2.69% | PASS |
| a3-qwen35-tp4-decode-c24-p126000 | decode | 57 | 63.494 / 63.631 / 63.779 | 61.850 | -2.59% | PASS |
| a3-qwen35-tp4-decode-c32-p126000 | decode | 55 | 65.343 / 65.297 / 65.724 | 64.476 | -1.33% | PASS |
| a3-qwen35-tp4-decode-c4-p126000 | decode | 138 | 22.871 / 22.871 / 23.010 | 22.960 | +0.39% | PASS |
| a3-qwen35-tp4-decode-c48-p126000 | decode | 42 | 86.442 / 86.447 / 86.585 | 85.820 | -0.72% | PASS |
| a3-qwen35-tp4-decode-c6-p126000 | decode | 121 | 27.566 / 27.525 / 27.659 | 26.500 | -3.87% | PASS |
| a3-qwen35-tp4-decode-c64-p126000 | decode | 34 | 107.680 / 107.516 / 108.525 | 107.214 | -0.43% | PASS |
| a3-qwen35-tp4-decode-c8-p126000 | decode | 111 | 31.009 / 30.990 / 31.159 | 30.251 | -2.44% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | decode | 47 | 27.914 / 27.905 / 28.026 | 27.072 | -3.02% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | decode | 45 | 30.548 / 30.507 / 30.812 | 30.132 | -1.36% | PASS |
| a3-qwen35-tp4-decode-c12-p8512 | decode | 43 | 27.435 / 27.433 / 27.570 | 26.367 | -3.89% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | decode | 58 | 33.166 / 33.160 / 33.280 | 32.580 | -1.77% | PASS |
| a3-qwen35-tp4-decode-c24-p24512 | decode | 66 | 35.550 / 35.558 / 35.723 | 34.955 | -1.67% | PASS |
| a3-qwen35-tp4-decode-c24-p64512 | decode | 63 | 44.868 / 44.851 / 45.016 | 45.555 | +1.53% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | decode | 57 | 31.676 / 31.677 / 31.775 | 30.991 | -2.16% | PASS |
| a3-qwen35-tp4-decode-c24-p96512 | decode | 52 | 54.896 / 55.004 / 55.143 | 54.035 | -1.57% | PASS |
| a3-qwen35-tp4-decode-c2-p24512 | decode | 16 | 16.697 / 16.657 / 16.860 | 16.543 | -0.93% | PASS |
| a3-qwen35-tp4-decode-c2-p64512 | decode | 7 | 17.136 / 17.138 / 17.270 | 16.911 | -1.31% | PASS |
| a3-qwen35-tp4-decode-c2-p8512 | decode | 7 | 16.319 / 16.333 / 16.372 | 16.396 | +0.47% | PASS |
| a3-qwen35-tp4-decode-c2-p96512 | decode | 12 | 17.338 / 17.324 / 17.456 | 17.205 | -0.76% | PASS |
| a3-qwen35-tp4-decode-c6-p24512 | decode | 23 | 23.225 / 23.181 / 23.327 | 22.440 | -3.38% | PASS |
| a3-qwen35-tp4-decode-c6-p64512 | decode | 40 | 24.666 / 24.667 / 24.763 | 24.040 | -2.54% | PASS |
| a3-qwen35-tp4-decode-c6-p8512 | decode | 21 | 22.846 / 22.849 / 22.926 | 22.080 | -3.35% | PASS |
| a3-qwen35-tp4-decode-c6-p96512 | decode | 42 | 26.149 / 25.837 / 26.090 | 25.320 | -3.17% | PASS |
| a3-qwen36-tp2-decode-c1-p126000 | decode | 118 | 27.505 / 27.460 / 27.662 | 27.383 | -0.45% | PASS |
| a3-qwen36-tp2-decode-c12-p126000 | decode | 40 | 92.965 / 92.683 / 93.492 | 93.285 | +0.34% | PASS |
| a3-qwen36-tp2-decode-c16-p126000 | decode | 39 | 96.424 / 96.221 / 97.153 | 97.698 | +1.32% | PASS |
| a3-qwen36-tp2-decode-c2-p126000 | decode | 107 | 32.035 / 32.023 / 32.214 | 31.161 | -2.73% | PASS |
| a3-qwen36-tp2-decode-c24-p126000 | decode | 29 | 132.699 / 132.704 / 132.775 | 131.030 | -1.26% | PASS |
| a3-qwen36-tp2-decode-c4-p126000 | decode | 88 | 40.819 / 40.826 / 41.229 | 39.622 | -2.93% | PASS |
| a3-qwen36-tp2-decode-c6-p126000 | decode | 74 | 50.103 / 50.017 / 50.304 | 49.629 | -0.95% | PASS |
| a3-qwen36-tp2-decode-c8-p126000 | decode | 66 | 56.360 / 56.274 / 56.741 | 56.533 | +0.31% | PASS |
| a3-qwen36-tp2-decode-c12-p24512 | decode | 63 | 45.843 / 45.864 / 46.024 | 47.656 | +3.95% | PASS |
| a3-qwen36-tp2-decode-c12-p64512 | decode | 46 | 63.620 / 63.439 / 64.028 | 65.640 | +3.17% | PASS |
| a3-qwen36-tp2-decode-c12-p8512 | decode | 68 | 39.923 / 39.905 / 40.004 | 40.462 | +1.35% | PASS |
| a3-qwen36-tp2-decode-c24-p24512 | decode | 49 | 60.836 / 60.802 / 60.974 | 60.735 | -0.17% | PASS |
| a3-qwen36-tp2-decode-c24-p64512 | decode | 34 | 87.080 / 87.073 / 87.154 | 89.514 | +2.79% | PASS |
| a3-qwen36-tp2-decode-c24-p8512 | decode | 56 | 52.156 / 52.152 / 52.263 | 50.879 | -2.45% | PASS |
| a3-qwen36-tp2-decode-c2-p24512 | decode | 58 | 26.724 / 26.694 / 26.806 | 25.884 | -3.14% | PASS |
| a3-qwen36-tp2-decode-c2-p64512 | decode | 58 | 28.868 / 28.845 / 28.903 | 27.964 | -3.13% | PASS |
| a3-qwen36-tp2-decode-c2-p8512 | decode | 45 | 25.809 / 25.747 / 25.801 | 25.052 | -2.93% | PASS |
| a3-qwen36-tp2-decode-c2-p96512 | decode | 62 | 30.222 / 30.218 / 30.266 | 29.628 | -1.96% | PASS |
| a3-qwen36-tp2-decode-c6-p24512 | decode | 71 | 33.717 / 33.762 / 33.825 | 34.040 | +0.96% | PASS |
| a3-qwen36-tp2-decode-c6-p64512 | decode | 71 | 39.714 / 39.641 / 39.741 | 40.184 | +1.18% | PASS |
| a3-qwen36-tp2-decode-c6-p8512 | decode | 61 | 32.027 / 31.966 / 32.038 | 31.583 | -1.39% | PASS |
| a3-qwen36-tp2-decode-c6-p96512 | decode | 64 | 44.510 / 44.533 / 44.618 | 45.100 | +1.32% | PASS |
| a3-qwen36-tp4-decode-c1-p126000 | decode | 132 | 19.697 / 19.667 / 19.812 | 19.488 | -1.06% | PASS |
| a3-qwen36-tp4-decode-c12-p126000 | decode | 83 | 44.267 / 44.229 / 44.445 | 42.851 | -3.20% | PASS |
| a3-qwen36-tp4-decode-c16-p126000 | decode | 72 | 51.997 / 51.884 / 52.229 | 51.176 | -1.58% | PASS |
| a3-qwen36-tp4-decode-c2-p126000 | decode | 128 | 21.879 / 21.733 / 21.892 | 21.469 | -1.88% | PASS |
| a3-qwen36-tp4-decode-c24-p126000 | decode | 42 | 89.034 / 88.904 / 89.802 | 90.830 | +2.02% | PASS |
| a3-qwen36-tp4-decode-c4-p126000 | decode | 121 | 26.965 / 26.819 / 26.895 | 26.039 | -3.43% | PASS |
| a3-qwen36-tp4-decode-c6-p126000 | decode | 105 | 32.038 / 31.950 / 32.050 | 30.200 | -5.74% | PASS |
| a3-qwen36-tp4-decode-c8-p126000 | decode | 97 | 36.585 / 36.585 / 36.725 | 34.711 | -5.12% | PASS |
| a3-qwen38-tp2-decode-c1-p126000 | decode | 119 | 27.543 / 27.497 / 27.703 | 27.383 | -0.58% | PASS |
| a3-qwen38-tp2-decode-c12-p126000 | decode | 40 | 93.228 / 93.357 / 93.478 | 93.285 | +0.06% | PASS |
| a3-qwen38-tp2-decode-c16-p126000 | decode | 39 | 96.251 / 96.054 / 96.900 | 97.698 | +1.50% | PASS |
| a3-qwen38-tp2-decode-c2-p126000 | decode | 107 | 32.136 / 32.139 / 32.349 | 31.161 | -3.03% | PASS |
| a3-qwen38-tp2-decode-c4-p126000 | decode | 90 | 40.524 / 40.550 / 40.876 | 39.622 | -2.23% | PASS |
| a3-qwen38-tp2-decode-c6-p126000 | decode | 74 | 50.273 / 50.197 / 50.502 | 49.629 | -1.28% | PASS |
| a3-qwen38-tp2-decode-c8-p126000 | decode | 66 | 56.370 / 56.313 / 56.643 | 56.533 | +0.29% | PASS |
| a3-qwen38-tp4-decode-c1-p126000 | decode | 135 | 19.886 / 19.681 / 19.804 | 19.488 | -2.00% | PASS |
| a3-qwen38-tp4-decode-c12-p126000 | decode | 84 | 44.305 / 44.261 / 44.463 | 42.851 | -3.28% | PASS |
| a3-qwen38-tp4-decode-c16-p126000 | decode | 73 | 51.793 / 51.612 / 52.084 | 51.176 | -1.19% | PASS |
| a3-qwen38-tp4-decode-c2-p126000 | decode | 137 | 21.825 / 21.761 / 21.870 | 21.469 | -1.63% | PASS |
| a3-qwen38-tp4-decode-c24-p126000 | decode | 43 | 88.988 / 88.982 / 89.108 | 90.830 | +2.07% | PASS |
| a3-qwen38-tp4-decode-c32-p126000 | decode | 41 | 93.356 / 93.203 / 93.861 | 95.319 | +2.10% | PASS |
| a3-qwen38-tp4-decode-c4-p126000 | decode | 124 | 26.807 / 26.771 / 26.837 | 26.039 | -2.86% | PASS |
| a3-qwen38-tp4-decode-c6-p126000 | decode | 108 | 31.992 / 31.979 / 32.091 | 30.200 | -5.60% | PASS |
| a3-qwen38-tp4-decode-c8-p126000 | decode | 98 | 36.460 / 36.463 / 36.611 | 34.711 | -4.80% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | decode | 56 | 30.908 / 30.898 / 30.968 | 29.698 | -3.92% | PASS |
| a3-qwen38-tp4-decode-c12-p64512 | decode | 68 | 35.845 / 35.986 / 36.161 | 34.882 | -2.69% | PASS |
| a3-qwen38-tp4-decode-c12-p96512 | decode | 65 | 39.782 / 39.852 / 40.095 | 39.029 | -1.89% | PASS |
| a3-qwen38-tp4-decode-c24-p24512 | decode | 65 | 43.632 / 43.656 / 43.714 | 45.763 | +4.89% | PASS |
| a3-qwen38-tp4-decode-c24-p64512 | decode | 49 | 60.117 / 60.324 / 60.463 | 63.526 | +5.67% | PASS |
| a3-qwen38-tp4-decode-c24-p96512 | decode | 40 | 75.162 / 75.093 / 75.331 | 77.735 | +3.42% | PASS |
| a3-qwen38-tp4-decode-c2-p24512 | decode | 11 | 19.404 / 19.244 / 20.150 | 19.033 | -1.91% | PASS |
| a3-qwen38-tp4-decode-c2-p64512 | decode | 20 | 20.210 / 20.021 / 20.180 | 19.993 | -1.07% | PASS |
| a3-qwen38-tp4-decode-c2-p96512 | decode | 24 | 20.989 / 20.830 / 21.239 | 20.761 | -1.08% | PASS |
| a3-qwen38-tp4-decode-c6-p24512 | decode | 38 | 24.761 / 24.752 / 24.829 | 23.299 | -5.91% | PASS |
| a3-qwen38-tp4-decode-c6-p64512 | decode | 40 | 27.237 / 27.135 / 27.365 | 26.019 | -4.47% | PASS |
| a3-qwen38-tp4-decode-c6-p96512 | decode | 42 | 29.560 / 29.308 / 29.565 | 28.195 | -4.62% | PASS |
| a5-qwen36-tp2-decode-c1-p126000 | decode | 54 | 27.332 / 27.209 / 27.445 | 26.695 | -2.33% | PASS |
| a5-qwen36-tp2-decode-c12-p126000 | decode | 38 | 39.512 / 39.500 / 39.595 | 37.785 | -4.37% | PASS |
| a5-qwen36-tp2-decode-c16-p126000 | decode | 35 | 43.048 / 43.038 / 43.179 | 43.147 | +0.23% | PASS |
| a5-qwen36-tp2-decode-c2-p126000 | decode | 52 | 28.841 / 28.804 / 28.991 | 27.707 | -3.93% | PASS |
| a5-qwen36-tp2-decode-c24-p126000 | decode | 25 | 63.879 / 63.873 / 63.963 | 65.318 | +2.25% | PASS |
| a5-qwen36-tp2-decode-c4-p126000 | decode | 48 | 31.689 / 31.648 / 31.862 | 30.086 | -5.06% | PASS |
| a5-qwen36-tp2-decode-c6-p126000 | decode | 43 | 34.972 / 34.963 / 35.029 | 32.585 | -6.83% | PASS |
| a5-qwen36-tp2-decode-c8-p126000 | decode | 41 | 35.597 / 35.582 / 35.641 | 33.637 | -5.51% | PASS |
| a5-qwen38-tp2-decode-c1-p126000 | decode | 53 | 28.447 / 28.429 / 28.570 | 27.745 | -2.47% | PASS |
| a5-qwen38-tp2-decode-c12-p126000 | decode | 37 | 40.788 / 40.789 / 40.880 | 38.986 | -4.42% | PASS |
| a5-qwen38-tp2-decode-c16-p126000 | decode | 34 | 44.535 / 44.520 / 44.705 | 44.404 | -0.29% | PASS |
| a5-qwen38-tp2-decode-c2-p126000 | decode | 51 | 30.056 / 30.048 / 30.111 | 28.765 | -4.29% | PASS |
| a5-qwen38-tp2-decode-c24-p126000 | decode | 24 | 64.457 / 64.427 / 64.559 | 66.689 | +3.46% | PASS |
| a5-qwen38-tp2-decode-c4-p126000 | decode | 47 | 32.711 / 32.699 / 32.777 | 31.173 | -4.70% | PASS |
| a5-qwen38-tp2-decode-c6-p126000 | decode | 42 | 36.091 / 36.084 / 36.136 | 33.700 | -6.62% | PASS |
| a5-qwen38-tp2-decode-c8-p126000 | decode | 40 | 37.428 / 37.420 / 37.480 | 34.780 | -7.08% | PASS |
| a5-qwen36-tp4-decode-c1-p126000 | decode | 58 | 25.585 / 25.621 / 25.711 | 25.223 | -1.42% | PASS |
| a5-qwen36-tp4-decode-c2-p126000 | decode | 54 | 27.536 / 27.580 / 27.663 | 26.962 | -2.08% | PASS |
| a5-qwen36-tp4-decode-c4-p126000 | decode | 52 | 28.964 / 28.988 / 29.039 | 28.199 | -2.64% | PASS |
| a5-qwen36-tp4-decode-c6-p126000 | decode | 49 | 30.604 / 30.612 / 30.773 | 28.711 | -6.19% | PASS |
| a5-qwen36-tp4-decode-c8-p126000 | decode | 48 | 31.660 / 31.718 / 31.765 | 29.518 | -6.76% | PASS |
| a5-qwen38-tp4-decode-c1-p126000 | decode | 56 | 25.808 / 25.757 / 26.012 | 25.456 | -1.37% | PASS |
| a5-qwen38-tp4-decode-c2-p126000 | decode | 53 | 28.147 / 28.200 / 28.244 | 27.204 | -3.35% | PASS |
| a5-qwen38-tp4-decode-c4-p126000 | decode | 52 | 29.240 / 29.178 / 29.387 | 28.490 | -2.57% | PASS |
| a5-qwen38-tp4-decode-c6-p126000 | decode | 49 | 30.974 / 30.930 / 31.177 | 29.036 | -6.25% | PASS |
| a5-qwen38-tp4-decode-c8-p126000 | decode | 47 | 31.871 / 31.845 / 32.020 | 29.872 | -6.27% | PASS |
| a3-v41-tp4dp4-decode-c4-p8512 | decode | 28 | 35.585 / 36.156 / 36.274 | 32.194 | -9.53% | PASS |

Communication summaries without device-task bindings can extend beyond a dependent Head. For verified hidden-state consumer chains, structural consumer start provides a conditional completion upper bound. Original summary intervals remain in the evidence; these bounds are not measured transport service times.
- a3-kimi4-tp16-128k-decode-c24-p4k: {"additive_body_time_cause": false, "affected_events": 78, "affected_forwards": 78, "basis": "structural_consumer_upper_bound", "physical_transport_completion_observed": false, "raw_envelope_total_ns": 646243092, "unassigned_summary_suffix_total_ns": 643576396}
- a3-qwen36-tp4-decode-c4-p126000: {"additive_body_time_cause": false, "affected_events": 96, "affected_forwards": 24, "basis": "structural_consumer_upper_bound", "physical_transport_completion_observed": false, "raw_envelope_total_ns": 3628147413, "unassigned_summary_suffix_total_ns": 3626517451}

| Case | Body validation basis | Target native timings used in rules |
|---|---|---|
| qwen36-a3-tp4-c128 | in_sample_native_physical_domains | True |
| qwen38-a3-tp4-c128 | retrospective_same_geometry_cross_capture | False |
| a5_qwen36_highconc_c4 | in_sample | True |
| a5_qwen36_highconc_c40 | in_sample | True |
| a5_qwen36_highconc_c128 | mixed_native_transfer_and_in_sample_hccl_gating | True |
| a5_qwen38_highconc_c4 | in_sample | True |
| a5_qwen38_highconc_c32 | in_sample | True |
| a5_qwen38_highconc_c128 | mixed_native_transfer_and_in_sample_hccl_gating | True |
| a5_glm53flash_heldout_c12_p4k | in_sample | True |
| a5_glm53flash_heldout_c24_p12k | in_sample | True |
| a5_glm53flash_heldout_c48_p4k | frozen_native_functions_from_prior_capture_training | False |
| a3_glm53flash_static_on_c10_p131201 | operator_calibrated_not_pristine_holdout | True |
| a3-qwen36-tp4-longctx-p-126976-c1 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-longctx-p-126976-c4 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-longctx-p-65536-c1 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-longctx-p-65536-c4 | frozen_native_service_transfer | False |
| a5_kimi_tp8_e16_bf16_128k_c1 | source_mechanism_conditional; captured_binary_unobserved | False |
| a5_kimi_tp8_e16_bf16_128k_c2 | source_mechanism_conditional; captured_binary_unobserved | False |
| a5_kimi_tp8_e16_bf16_128k_c4 | source_mechanism_conditional; captured_binary_unobserved | False |
| a5_kimi_tp8_e16_bf16_128k_c6 | source_mechanism_conditional; captured_binary_unobserved | False |
| a5_kimi_tp8_e16_bf16_128k_c8 | source_mechanism_conditional; captured_binary_unobserved | False |
| a5_kimi_tp8_e16_bf16_128k_c12 | source_mechanism_conditional; captured_binary_unobserved | False |
| a3-qwen35-tp4-decode-c1-p126000 | frozen_native_service_transfer; not_blind | False |
| a3-qwen35-tp4-decode-c12-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c16-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c2-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c24-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c32-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c4-p126000 | frozen_native_service_transfer; not_blind | False |
| a3-qwen35-tp4-decode-c48-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c6-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c64-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c8-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c12-p24512 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c12-p64512 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c12-p8512 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c12-p96512 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c24-p24512 | target_native_calibrated | True |
| a3-qwen35-tp4-decode-c24-p64512 | target_native_calibrated | True |
| a3-qwen35-tp4-decode-c24-p8512 | target_native_calibrated | True |
| a3-qwen35-tp4-decode-c24-p96512 | target_native_calibrated | True |
| a3-qwen35-tp4-decode-c2-p24512 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c2-p64512 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c2-p8512 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c2-p96512 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c6-p24512 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c6-p64512 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c6-p8512 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c6-p96512 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c1-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c12-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c16-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c2-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c24-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c4-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c6-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c8-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c12-p24512 | target_native_calibrated | True |
| a3-qwen36-tp2-decode-c12-p64512 | target_native_calibrated | True |
| a3-qwen36-tp2-decode-c12-p8512 | target_native_calibrated | True |
| a3-qwen36-tp2-decode-c24-p24512 | target_native_calibrated | True |
| a3-qwen36-tp2-decode-c24-p64512 | target_native_calibrated | True |
| a3-qwen36-tp2-decode-c24-p8512 | target_native_calibrated | True |
| a3-qwen36-tp2-decode-c2-p24512 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c2-p64512 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c2-p8512 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c2-p96512 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c6-p24512 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c6-p64512 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c6-p8512 | frozen_native_service_transfer | False |
| a3-qwen36-tp2-decode-c6-p96512 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-decode-c1-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-decode-c12-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-decode-c16-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-decode-c2-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-decode-c24-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-decode-c4-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-decode-c6-p126000 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-decode-c8-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp2-decode-c1-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp2-decode-c12-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp2-decode-c16-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp2-decode-c2-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp2-decode-c4-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp2-decode-c6-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp2-decode-c8-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c1-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c12-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c16-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c2-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c24-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c32-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c4-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c6-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c8-p126000 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c12-p24512 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c12-p64512 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c12-p96512 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c24-p24512 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c24-p64512 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c24-p96512 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c2-p24512 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c2-p64512 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c2-p96512 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c6-p24512 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c6-p64512 | frozen_native_service_transfer | False |
| a3-qwen38-tp4-decode-c6-p96512 | frozen_native_service_transfer | False |

A Body pass with target-calibrated native rules is calibration evidence, not zero-shot generalization. Frozen native-family transfer scores remain separately reported in generalization.md.

The headline scores the population with the most complete Forward calls (ties retain input order), independent of timing or prediction success. This does not establish Host-observed steady state. Other geometries do not veto the headline; complete coverage and all-population pass remain separate audits.

| Case | B | q | Context | Calls | Real mean / P50 / P90 ms | Sim ms | Error | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c4-livepre | 4 | 6 | 4096 | 46 | 29.762 / 29.664 / 30.046 | 30.314 | +1.86% | PASS |
| glm53flash-a3-tp16-c4-livepre | 3 | 6 | 4096 | 11 | 28.126 / 28.052 / 28.206 | — | — | unresolved |
| glm53flash-a3-tp16-c4-livepre | 1 | 6 | 4096 | 10 | 23.447 / 23.179 / 23.585 | — | — | unresolved |
| glm53flash-a3-tp16-c4-livepre | 2 | 6 | 4096 | 6 | 26.154 / 25.840 / 27.873 | — | — | unresolved |

glm53flash-a3-tp16-c4-livepre: scored 46 / 73 calls; all-population pass: None.
| glm53flash-a3-tp16-c16-livepre | 16 | 6 | 4096 | 37 | 41.069 / 40.940 / 41.282 | 44.390 | +8.09% | PASS |
| glm53flash-a3-tp16-c16-livepre | 6 | 6 | 4096 | 16 | 33.619 / 33.419 / 33.980 | — | — | unresolved |
| glm53flash-a3-tp16-c16-livepre | 1 | 6 | 4096 | 13 | 23.486 / 23.363 / 23.611 | — | — | unresolved |
| glm53flash-a3-tp16-c16-livepre | 3 | 6 | 4096 | 9 | 28.227 / 28.041 / 29.858 | — | — | unresolved |
| glm53flash-a3-tp16-c16-livepre | 7 | 6 | 4096 | 7 | 35.014 / 34.765 / 36.431 | — | — | unresolved |
| glm53flash-a3-tp16-c16-livepre | 10 | 6 | 4096 | 6 | 37.826 / 37.534 / 39.879 | — | — | unresolved |
| glm53flash-a3-tp16-c16-livepre | 2 | 6 | 4096 | 5 | 26.385 / 25.916 / 28.429 | — | — | unresolved |
| glm53flash-a3-tp16-c16-livepre | 14 | 6 | 4096 | 4 | 43.282 / 42.788 / 45.252 | — | — | unresolved |
| glm53flash-a3-tp16-c16-livepre | 4 | 6 | 4096 | 4 | 30.244 / 29.665 / 32.051 | — | — | unresolved |
| glm53flash-a3-tp16-c16-livepre | 8 | 6 | 4096 | 3 | 35.070 / 34.379 / 36.534 | — | — | unresolved |
| glm53flash-a3-tp16-c16-livepre | 11 | 6 | 4096 | 2 | 41.544 / 41.544 / 43.477 | — | — | unresolved |
| glm53flash-a3-tp16-c16-livepre | 12 | 6 | 4096 | 1 | 44.811 / 44.811 / 44.811 | — | — | unresolved |
| glm53flash-a3-tp16-c16-livepre | 15 | 6 | 4096 | 1 | 44.980 / 44.980 / 44.980 | — | — | unresolved |

glm53flash-a3-tp16-c16-livepre: scored 37 / 108 calls; all-population pass: None.
| glm53flash-a3-tp16-c2 | 2 | 6 | 4096 | 46 | 34.118 / 33.910 / 35.073 | 31.755 | -6.93% | PASS |
| glm53flash-a3-tp16-c2 | 1 | 6 | 4096 | 12 | 33.269 / 33.260 / 33.461 | — | — | unresolved |

glm53flash-a3-tp16-c2: scored 46 / 58 calls; all-population pass: None.
| glm53flash-a3-tp16-c4 | 4 | 6 | 4096 | 46 | 39.841 / 39.798 / 40.057 | 36.959 | -7.24% | PASS |
| glm53flash-a3-tp16-c4 | 1 | 6 | 4096 | 8 | 33.514 / 33.637 / 34.066 | — | — | unresolved |
| glm53flash-a3-tp16-c4 | 3 | 6 | 4096 | 4 | 36.347 / 36.075 / 37.439 | — | — | unresolved |
| glm53flash-a3-tp16-c4 | 2 | 6 | 4096 | 3 | 35.089 / 34.649 / 36.996 | — | — | unresolved |

glm53flash-a3-tp16-c4: scored 46 / 61 calls; all-population pass: None.
| v4flash-a3-tp8-c4 | 4 | 2 | 4096 | 104 | 32.486 / 32.416 / 32.734 | 29.272 | -9.89% | PASS |
| v4flash-a3-tp8-c4 | 1 | 2 | 4096 | 4 | 29.500 / 29.512 / 29.661 | — | — | unresolved |

v4flash-a3-tp8-c4: scored 104 / 108 calls; all-population pass: None.
| v4flash-a3-tp8-c8 | 8 | 2 | 4096 | 104 | 37.763 / 37.868 / 38.082 | 34.707 | -8.09% | PASS |
| v4flash-a3-tp8-c8 | 2 | 2 | 4096 | 3 | 31.294 / 31.234 / 31.612 | — | — | unresolved |
| v4flash-a3-tp8-c8 | 1 | 2 | 4096 | 2 | 29.355 / 29.355 / 29.422 | — | — | unresolved |
| v4flash-a3-tp8-c8 | 4 | 2 | 4096 | 2 | 32.488 / 32.488 / 32.562 | — | — | unresolved |

v4flash-a3-tp8-c8: scored 104 / 111 calls; all-population pass: None.
| qwen35-35b-a5-tp4-c64-graph | 64 | 4 | 4096 | 79 | 21.957 / 22.001 / 22.068 | 19.975 | -9.03% | PASS |
| qwen35-35b-a5-tp4-c64-graph | 1 | 4 | 4096 | 3 | 8.739 / 8.828 / 8.913 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 60 | 4 | 4096 | 1 | 21.444 / 21.444 / 21.444 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 56 | 4 | 4096 | 1 | 20.972 / 20.972 / 20.972 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 52 | 4 | 4096 | 1 | 20.950 / 20.950 / 20.950 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 48 | 4 | 4096 | 1 | 20.070 / 20.070 / 20.070 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 44 | 4 | 4096 | 1 | 20.103 / 20.103 / 20.103 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 40 | 4 | 4096 | 1 | 19.908 / 19.908 / 19.908 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 34 | 4 | 4096 | 1 | 19.149 / 19.149 / 19.149 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 26 | 4 | 4096 | 1 | 16.774 / 16.774 / 16.774 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 18 | 4 | 4096 | 1 | 15.810 / 15.810 / 15.810 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 12 | 4 | 4096 | 1 | 15.124 / 15.124 / 15.124 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 10 | 4 | 4096 | 1 | 14.944 / 14.944 / 14.944 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 8 | 4 | 4096 | 1 | 14.550 / 14.550 / 14.550 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 4 | 4 | 4096 | 1 | 11.638 / 11.638 / 11.638 | — | — | unresolved |
| qwen35-35b-a5-tp4-c64-graph | 2 | 4 | 4096 | 1 | 9.812 / 9.812 / 9.812 | — | — | unresolved |

qwen35-35b-a5-tp4-c64-graph: scored 79 / 96 calls; all-population pass: None.
| qwen35-35b-a5-tp4-c128-graph | 128 | 4 | 4096 | 76 | 28.585 / 28.571 / 28.704 | 26.059 | -8.83% | PASS |
| qwen35-35b-a5-tp4-c128-graph | 124 | 4 | 4096 | 2 | 28.335 / 28.335 / 28.358 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 6 | 4 | 4096 | 2 | 12.927 / 12.927 / 13.229 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 2 | 4 | 4096 | 2 | 9.874 / 9.874 / 9.959 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 1 | 4 | 4096 | 1 | 8.488 / 8.488 / 8.488 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 120 | 4 | 4096 | 1 | 27.852 / 27.852 / 27.852 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 116 | 4 | 4096 | 1 | 27.866 / 27.866 / 27.866 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 108 | 4 | 4096 | 1 | 27.249 / 27.249 / 27.249 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 96 | 4 | 4096 | 1 | 24.930 / 24.930 / 24.930 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 84 | 4 | 4096 | 1 | 25.698 / 25.698 / 25.698 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 72 | 4 | 4096 | 1 | 24.146 / 24.146 / 24.146 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 58 | 4 | 4096 | 1 | 21.377 / 21.377 / 21.377 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 50 | 4 | 4096 | 1 | 21.026 / 21.026 / 21.026 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 42 | 4 | 4096 | 1 | 19.976 / 19.976 / 19.976 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 38 | 4 | 4096 | 1 | 19.185 / 19.185 / 19.185 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 28 | 4 | 4096 | 1 | 16.372 / 16.372 / 16.372 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 18 | 4 | 4096 | 1 | 15.838 / 15.838 / 15.838 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 12 | 4 | 4096 | 1 | 15.127 / 15.127 / 15.127 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 10 | 4 | 4096 | 1 | 14.935 / 14.935 / 14.935 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 8 | 4 | 4096 | 1 | 14.334 / 14.334 / 14.334 | — | — | unresolved |
| qwen35-35b-a5-tp4-c128-graph | 4 | 4 | 4096 | 1 | 11.424 / 11.424 / 11.424 | — | — | unresolved |

qwen35-35b-a5-tp4-c128-graph: scored 76 / 99 calls; all-population pass: None.
| qwen35-35b-a5-tp4-c4-graph | 4 | 4 | 4096 | 84 | 11.551 / 11.482 / 11.818 | 11.401 | -1.30% | PASS |
| qwen35-35b-a5-tp4-c4-graph | 1 | 4 | 4096 | 6 | 8.747 / 8.803 / 8.838 | — | — | unresolved |
| qwen35-35b-a5-tp4-c4-graph | 2 | 4 | 4096 | 1 | 9.700 / 9.700 / 9.700 | — | — | unresolved |

qwen35-35b-a5-tp4-c4-graph: scored 84 / 91 calls; all-population pass: None.
| a3_glm53_w4a8_tp16_tpot30_c2 | 2 | 6 | 4096 | 44 | 57.639 / 57.562 / 58.995 | 56.941 | -1.21% | PASS |
| a3_glm53_w4a8_tp16_tpot30_c2 | 1 | 6 | 4096 | 4 | 57.125 / 57.281 / 57.500 | — | — | unresolved |

a3_glm53_w4a8_tp16_tpot30_c2: scored 44 / 48 calls; all-population pass: None.
| a3_glm53_w4a8_tp16_tpot50_c2 | 2 | 6 | 4096 | 44 | 57.817 / 57.597 / 59.092 | 57.179 | -1.10% | PASS |
| a3_glm53_w4a8_tp16_tpot50_c2 | 1 | 6 | 4096 | 9 | 57.713 / 57.524 / 58.620 | — | — | unresolved |

a3_glm53_w4a8_tp16_tpot50_c2: scored 44 / 53 calls; all-population pass: None.
| a3_glm53_w4a8_tp16_tpot88_c8 | 8 | 6 | 4096 | 49 | 69.556 / 69.489 / 69.830 | 66.764 | -4.01% | PASS |
| a3_glm53_w4a8_tp16_tpot88_c8 | 1 | 6 | 4096 | 4 | 56.950 / 56.983 / 57.379 | — | — | unresolved |
| a3_glm53_w4a8_tp16_tpot88_c8 | 2 | 6 | 4096 | 3 | 56.847 / 56.896 / 57.002 | — | — | unresolved |
| a3_glm53_w4a8_tp16_tpot88_c8 | 6 | 6 | 4096 | 2 | 68.633 / 68.633 / 68.639 | — | — | unresolved |
| a3_glm53_w4a8_tp16_tpot88_c8 | 3 | 6 | 4096 | 2 | 58.058 / 58.058 / 58.239 | — | — | unresolved |
| a3_glm53_w4a8_tp16_tpot88_c8 | 4 | 6 | 4096 | 1 | 57.388 / 57.388 / 57.388 | — | — | unresolved |

a3_glm53_w4a8_tp16_tpot88_c8: scored 49 / 61 calls; all-population pass: None.
| a5_glm53flash_tp8_c16_p4k | 16 | 4 | 4104 | 30 | 33.031 / 33.026 / 33.164 | 32.563 | -1.42% | PASS |
| a5_glm53flash_tp8_c16_p4k | 2 | 4 | 4104 | 4 | 18.010 / 17.896 / 18.413 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p4k | 1 | 4 | 4104 | 3 | 15.697 / 15.705 / 15.723 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p4k | 6 | 4 | 4104 | 2 | 24.984 / 24.984 / 25.001 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p4k | 14 | 4 | 4104 | 1 | 33.211 / 33.211 / 33.211 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p4k | 12 | 4 | 4104 | 1 | 32.232 / 32.232 / 32.232 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p4k | 10 | 4 | 4104 | 1 | 31.923 / 31.923 / 31.923 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p4k | 4 | 4 | 4104 | 1 | 21.417 / 21.417 / 21.417 | — | — | unresolved |

a5_glm53flash_tp8_c16_p4k: scored 30 / 43 calls; all-population pass: None.
| a5_glm53flash_tp8_c16_p8k | 16 | 4 | 8200 | 32 | 33.616 / 33.626 / 33.710 | 33.073 | -1.62% | PASS |
| a5_glm53flash_tp8_c16_p8k | 8 | 4 | 8200 | 2 | 29.255 / 29.255 / 29.307 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p8k | 4 | 4 | 8200 | 2 | 21.441 / 21.441 / 21.441 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p8k | 1 | 4 | 8200 | 2 | 15.624 / 15.624 / 15.655 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p8k | 14 | 4 | 8200 | 1 | 33.358 / 33.358 / 33.358 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p8k | 12 | 4 | 8200 | 1 | 32.536 / 32.536 / 32.536 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p8k | 6 | 4 | 8200 | 1 | 24.990 / 24.990 / 24.990 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p8k | 2 | 4 | 8200 | 1 | 17.717 / 17.717 / 17.717 | — | — | unresolved |

a5_glm53flash_tp8_c16_p8k: scored 32 / 42 calls; all-population pass: None.
| a5_glm53flash_tp8_c32_p4k | 32 | 4 | 4104 | 31 | 37.669 / 37.665 / 37.761 | 34.590 | -8.17% | PASS |
| a5_glm53flash_tp8_c32_p4k | 30 | 4 | 4104 | 2 | 37.705 / 37.705 / 37.844 | — | — | unresolved |
| a5_glm53flash_tp8_c32_p4k | 24 | 4 | 4104 | 2 | 37.468 / 37.468 / 38.255 | — | — | unresolved |
| a5_glm53flash_tp8_c32_p4k | 28 | 4 | 4104 | 1 | 38.397 / 38.397 / 38.397 | — | — | unresolved |
| a5_glm53flash_tp8_c32_p4k | 26 | 4 | 4104 | 1 | 38.002 / 38.002 / 38.002 | — | — | unresolved |

a5_glm53flash_tp8_c32_p4k: scored 31 / 37 calls; all-population pass: None.
| a5_glm53flash_tp8_c32_p8k | 32 | 4 | 8200 | 35 | 38.713 / 38.722 / 38.759 | 38.095 | -1.60% | PASS |
| a5_glm53flash_tp8_c32_p8k | 30 | 4 | 8200 | 1 | 38.635 / 38.635 / 38.635 | — | — | unresolved |

a5_glm53flash_tp8_c32_p8k: scored 35 / 36 calls; all-population pass: None.
| a5_glm53flash_tp8_c4_p8k | 4 | 4 | 8200 | 11 | 21.418 / 21.408 / 21.432 | 21.082 | -1.57% | PASS |
| a5_glm53flash_tp8_c4_p8k | 1 | 4 | 8200 | 9 | 15.590 / 15.583 / 15.642 | — | — | unresolved |
| a5_glm53flash_tp8_c4_p8k | 2 | 4 | 8200 | 3 | 17.682 / 17.672 / 17.709 | — | — | unresolved |

a5_glm53flash_tp8_c4_p8k: scored 11 / 23 calls; all-population pass: None.
| a5_glm53flash_tp8_c8_p4k | 8 | 4 | 4104 | 30 | 28.833 / 28.828 / 28.885 | 28.384 | -1.56% | PASS |
| a5_glm53flash_tp8_c8_p4k | 6 | 4 | 4104 | 3 | 25.113 / 25.067 / 25.283 | — | — | unresolved |
| a5_glm53flash_tp8_c8_p4k | 4 | 4 | 4104 | 2 | 21.340 / 21.340 / 21.389 | — | — | unresolved |
| a5_glm53flash_tp8_c8_p4k | 2 | 4 | 4104 | 2 | 18.882 / 18.882 / 19.872 | — | — | unresolved |
| a5_glm53flash_tp8_c8_p4k | 1 | 4 | 4104 | 1 | 16.092 / 16.092 / 16.092 | — | — | unresolved |

a5_glm53flash_tp8_c8_p4k: scored 30 / 38 calls; all-population pass: None.
| a3_glm53flash_tp16_aclgraph_c16 | 16 | 6 | 4096 | 50 | 53.893 / 53.871 / 54.021 | 49.051 | -8.99% | PASS |
| a3_glm53flash_tp16_aclgraph_c16 | 1 | 6 | 4096 | 4 | 33.477 / 33.401 / 33.975 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c16 | 12 | 6 | 4096 | 4 | 52.671 / 52.569 / 53.565 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c16 | 2 | 6 | 4096 | 3 | 33.946 / 33.337 / 35.257 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c16 | 8 | 6 | 4096 | 2 | 47.322 / 47.322 / 48.210 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c16 | 4 | 6 | 4096 | 1 | 39.385 / 39.385 / 39.385 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c16 | 6 | 6 | 4096 | 1 | 45.421 / 45.421 / 45.421 | — | — | unresolved |

a3_glm53flash_tp16_aclgraph_c16: scored 50 / 65 calls; all-population pass: None.
| a3_glm53flash_tp16_aclgraph_c32 | 32 | 6 | 4096 | 49 | 69.361 / 69.418 / 69.528 | 64.395 | -7.16% | PASS |
| a3_glm53flash_tp16_aclgraph_c32 | 12 | 6 | 4096 | 5 | 52.894 / 53.227 / 53.859 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c32 | 1 | 6 | 4096 | 3 | 33.667 / 33.176 / 34.874 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c32 | 24 | 6 | 4096 | 3 | 63.044 / 62.507 / 64.216 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c32 | 16 | 6 | 4096 | 2 | 54.274 / 54.274 / 54.610 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c32 | 8 | 6 | 4096 | 1 | 46.500 / 46.500 / 46.500 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c32 | 6 | 6 | 4096 | 1 | 46.451 / 46.451 / 46.451 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c32 | 2 | 6 | 4096 | 1 | 33.133 / 33.133 / 33.133 | — | — | unresolved |

a3_glm53flash_tp16_aclgraph_c32: scored 49 / 65 calls; all-population pass: None.
| a3_glm53flash_tp16_aclgraph_c64 | 64 | 6 | 4096 | 47 | 97.375 / 97.487 / 97.895 | 96.015 | -1.40% | PASS |
| a3_glm53flash_tp16_aclgraph_c64 | 1 | 6 | 4096 | 6 | 33.162 / 33.128 / 33.586 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 | 48 | 6 | 4096 | 3 | 80.931 / 80.984 / 82.029 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 | 6 | 6 | 4096 | 3 | 45.865 / 46.345 / 46.510 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 | 32 | 6 | 4096 | 2 | 68.165 / 68.165 / 68.192 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 | 24 | 6 | 4096 | 2 | 61.996 / 61.996 / 62.736 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 | 16 | 6 | 4096 | 2 | 53.912 / 53.912 / 54.034 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 | 2 | 6 | 4096 | 2 | 33.440 / 33.440 / 34.073 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 | 4 | 6 | 4096 | 1 | 37.485 / 37.485 / 37.485 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 | 8 | 6 | 4096 | 1 | 46.552 / 46.552 / 46.552 | — | — | unresolved |

a3_glm53flash_tp16_aclgraph_c64: scored 47 / 69 calls; all-population pass: None.
| a3_glm53flash_tp16_aclgraph_c8 | 8 | 6 | 4096 | 47 | 46.859 / 46.817 / 47.175 | 46.362 | -1.06% | PASS |
| a3_glm53flash_tp16_aclgraph_c8 | 1 | 6 | 4096 | 6 | 33.545 / 33.104 / 34.940 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c8 | 4 | 6 | 4096 | 4 | 37.953 / 37.468 / 39.615 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c8 | 6 | 6 | 4096 | 3 | 45.218 / 44.930 / 46.274 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c8 | 2 | 6 | 4096 | 2 | 34.031 / 34.031 / 34.634 | — | — | unresolved |

a3_glm53flash_tp16_aclgraph_c8: scored 47 / 62 calls; all-population pass: None.
| a3_kimi4_tp8_w4a8_c16 | 16 | 1 | 4096 | 235 | 4.807 / 4.779 / 4.992 | 4.918 | +2.31% | PASS |
| a3_kimi4_tp8_w4a8_c16 | 1 | 1 | 4096 | 3 | 3.845 / 3.281 / 5.439 | — | — | unresolved |

a3_kimi4_tp8_w4a8_c16: scored 235 / 238 calls; all-population pass: None.
| a3_kimi4_tp8_w4a8_c32 | 32 | 1 | 4096 | 220 | 6.714 / 6.665 / 6.923 | 6.097 | -9.19% | PASS |
| a3_kimi4_tp8_w4a8_c32 | 1 | 1 | 4096 | 3 | 3.240 / 3.278 / 3.411 | — | — | unresolved |
| a3_kimi4_tp8_w4a8_c32 | 4 | 1 | 4096 | 3 | 3.364 / 3.380 / 3.467 | — | — | unresolved |
| a3_kimi4_tp8_w4a8_c32 | 8 | 1 | 4096 | 1 | 3.812 / 3.812 / 3.812 | — | — | unresolved |
| a3_kimi4_tp8_w4a8_c32 | 2 | 1 | 4096 | 1 | 2.978 / 2.978 / 2.978 | — | — | unresolved |
| a3_kimi4_tp8_w4a8_c32 | 16 | 1 | 4096 | 1 | 4.690 / 4.690 / 4.690 | — | — | unresolved |

a3_kimi4_tp8_w4a8_c32: scored 220 / 229 calls; all-population pass: None.
| a3_kimi4_tp8_w4a8_c4 | 4 | 1 | 4096 | 246 | 3.476 / 3.438 / 3.656 | 3.196 | -8.07% | PASS |
| a3_kimi4_tp8_w4a8_c4 | 2 | 1 | 4096 | 4 | 3.376 / 3.346 / 3.556 | — | — | unresolved |
| a3_kimi4_tp8_w4a8_c4 | 1 | 1 | 4096 | 3 | 3.191 / 3.245 / 3.294 | — | — | unresolved |

a3_kimi4_tp8_w4a8_c4: scored 246 / 253 calls; all-population pass: None.
| a3_kimi4_tp8_w4a8_c64 | 64 | 1 | 4096 | 196 | 9.615 / 9.550 / 9.774 | 8.699 | -9.53% | PASS |
| a3_kimi4_tp8_w4a8_c64 | 1 | 1 | 4096 | 3 | 3.178 / 3.254 / 3.501 | — | — | unresolved |
| a3_kimi4_tp8_w4a8_c64 | 48 | 1 | 4096 | 2 | 8.473 / 8.473 / 8.560 | — | — | unresolved |
| a3_kimi4_tp8_w4a8_c64 | 24 | 1 | 4096 | 2 | 5.631 / 5.631 / 5.720 | — | — | unresolved |
| a3_kimi4_tp8_w4a8_c64 | 16 | 1 | 4096 | 2 | 4.723 / 4.723 / 4.739 | — | — | unresolved |
| a3_kimi4_tp8_w4a8_c64 | 2 | 1 | 4096 | 1 | 3.160 / 3.160 / 3.160 | — | — | unresolved |
| a3_kimi4_tp8_w4a8_c64 | 4 | 1 | 4096 | 1 | 3.537 / 3.537 / 3.537 | — | — | unresolved |

a3_kimi4_tp8_w4a8_c64: scored 196 / 207 calls; all-population pass: None.
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 | 5 | 8 | 4096 | 32 | 49.985 / 49.802 / 50.230 | 52.474 | +4.98% | PASS |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 | 6 | 8 | 4096 | 20 | 50.228 / 50.207 / 50.438 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 | 1 | 8 | 4096 | 15 | 34.239 / 33.682 / 36.062 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 | 4 | 8 | 4096 | 8 | 48.704 / 48.704 / 49.026 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 | 3 | 8 | 4096 | 1 | 185.131 / 185.131 / 185.131 | — | — | unresolved |

a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16: scored 32 / 76 calls; all-population pass: None.
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 9 | 8 | 4096 | 22 | 54.967 / 54.880 / 55.047 | 55.972 | +1.83% | PASS |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 7 | 8 | 4096 | 17 | 50.515 / 50.460 / 50.932 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 8 | 8 | 4096 | 16 | 51.750 / 51.720 / 52.028 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 1 | 8 | 4096 | 14 | 51.593 / 33.731 / 38.400 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 6 | 8 | 4096 | 4 | 50.042 / 49.960 / 50.329 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 5 | 8 | 4096 | 3 | 51.608 / 50.564 / 54.168 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 3 | 8 | 4096 | 1 | 262.497 / 262.497 / 262.497 | — | — | unresolved |

a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32: scored 22 / 77 calls; all-population pass: None.
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 | 2 | 8 | 4096 | 48 | 47.654 / 47.425 / 47.666 | 50.270 | +5.49% | PASS |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 | 1 | 8 | 4096 | 30 | 50.155 / 34.836 / 37.650 | — | — | unresolved |

a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4: scored 48 / 78 calls; all-population pass: None.
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 17 | 8 | 4096 | 21 | 61.811 / 61.629 / 62.042 | 63.580 | +2.86% | PASS |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 1 | 8 | 4096 | 13 | 72.359 / 33.725 / 173.015 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 15 | 8 | 4096 | 11 | 59.511 / 59.511 / 59.770 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 10 | 8 | 4096 | 8 | 55.145 / 55.134 / 55.338 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 16 | 8 | 4096 | 7 | 63.461 / 58.535 / 92.715 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 9 | 8 | 4096 | 5 | 54.822 / 54.716 / 55.164 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 14 | 8 | 4096 | 4 | 58.828 / 58.790 / 59.144 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 12 | 8 | 4096 | 2 | 56.627 / 56.627 / 56.743 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 3 | 8 | 4096 | 2 | 49.514 / 49.514 / 50.934 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 13 | 8 | 4096 | 2 | 57.975 / 57.975 / 58.052 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 5 | 8 | 4096 | 1 | 50.256 / 50.256 / 50.256 | — | — | unresolved |

a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64: scored 21 / 76 calls; all-population pass: None.
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | 4 | 8 | 4096 | 29 | 48.582 / 48.412 / 48.662 | 51.673 | +6.36% | PASS |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | 3 | 8 | 4096 | 28 | 52.940 / 48.199 / 48.363 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | 1 | 8 | 4096 | 16 | 48.606 / 33.772 / 34.877 | — | — | unresolved |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | 2 | 8 | 4096 | 4 | 47.116 / 47.165 / 47.202 | — | — | unresolved |

a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8: scored 29 / 77 calls; all-population pass: None.
| a5_glm53flash_heldout_c12_p4k | 2 | 4 | 4104 | 20 | 18.133 / 18.108 / 18.148 | 17.908 | -1.24% | PASS |
| a5_glm53flash_heldout_c12_p4k | 3 | 4 | 4104 | 15 | 19.876 / 19.730 / 20.375 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 12 | 4 | 4104 | 10 | 32.310 / 32.084 / 32.482 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 6 | 4 | 4104 | 9 | 25.926 / 25.380 / 27.537 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 4 | 4 | 4104 | 5 | 21.675 / 21.618 / 21.897 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 8 | 4 | 4104 | 1 | 28.855 / 28.855 / 28.855 | — | — | unresolved |

a5_glm53flash_heldout_c12_p4k: scored 20 / 60 calls; all-population pass: None.
| a5_glm53flash_heldout_c24_p12k | 24 | 4 | 12296 | 21 | 38.995 / 39.210 / 39.263 | 38.456 | -1.38% | PASS |
| a5_glm53flash_heldout_c24_p12k | 12 | 4 | 12296 | 10 | 32.978 / 32.904 / 33.062 | — | — | unresolved |
| a5_glm53flash_heldout_c24_p12k | 16 | 4 | 12296 | 6 | 34.357 / 34.349 / 34.465 | — | — | unresolved |
| a5_glm53flash_heldout_c24_p12k | 8 | 4 | 12296 | 4 | 29.935 / 29.876 / 30.133 | — | — | unresolved |

a5_glm53flash_heldout_c24_p12k: scored 21 / 41 calls; all-population pass: None.
| a5_glm53flash_heldout_c48_p4k | 48 | 4 | 4104 | 26 | 43.228 / 43.355 / 43.400 | 41.035 | -5.07% | PASS |
| a5_glm53flash_heldout_c48_p4k | 32 | 4 | 4104 | 9 | 38.189 / 38.157 / 38.314 | — | — | unresolved |
| a5_glm53flash_heldout_c48_p4k | 24 | 4 | 4104 | 2 | 37.382 / 37.382 / 37.552 | — | — | unresolved |

a5_glm53flash_heldout_c48_p4k: scored 26 / 37 calls; all-population pass: None.
| a3_glm53flash_static_on_c10_p131201 | 1 | 6 | 131201 | 68 | 22.603 / 22.348 / 23.552 | 22.621 | +0.08% | PASS |
| a3_glm53flash_static_on_c10_p131201 | 4 | 6 | 131201 | 13 | 28.251 / 27.985 / 28.308 | 30.978 | +9.65% | PASS |
| a3_glm53flash_static_on_c10_p131201 | 8 | 6 | 131201 | 12 | 31.580 / 31.520 / 31.998 | 30.890 | -2.19% | PASS |
| a3_glm53flash_static_on_c10_p131201 | 2 | 6 | 131201 | 3 | 25.713 / 24.344 / 28.811 | 25.407 | -1.19% | PASS |
| a3_glm53flash_static_on_c10_p131201 | 3 | 6 | 131201 | 1 | 31.415 / 31.415 / 31.415 | 28.159 | -10.36% | PASS |
| a3_glm53flash_static_on_c10_p131201 | 7 | 6 | 131201 | 1 | 35.748 / 35.748 / 35.748 | 29.843 | -16.52% | FAIL |

a3_glm53flash_static_on_c10_p131201: scored 98 / 98 calls; all-population pass: False.
Context: same_run_prompt_plus_requested_output_bounds; representative 131201, bounds 131201–131265 tokens. 131201 is a conditional initial-context representative. The requested 64 output tokens only bound context growth; no per-step sequence-length values are retained. KV cache capacity is not active context.
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 | 2 | 126976 | 34 | 20.465 / 20.804 / 20.975 | 20.144 | -1.57% | PASS |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 | 2 | 126976 | 16 | 16.107 / 16.100 / 16.156 | 15.829 | -1.72% | PASS |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 | 2 | 126976 | 15 | 17.687 / 17.706 / 17.759 | 17.310 | -2.13% | PASS |

a3-qwen35-tp4-longctx-p-126976-c4: scored 65 / 65 calls; all-population pass: True.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 126976, bounds 126976–127104 tokens.
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 | 2 | 65536 | 55 | 16.750 / 16.724 / 16.909 | 16.259 | -2.93% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 | 2 | 65536 | 11 | 15.583 / 15.520 / 15.562 | 15.298 | -1.83% | PASS |

a3-qwen35-tp4-longctx-p-65536-c2: scored 66 / 66 calls; all-population pass: True.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65664 tokens.
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 | 2 | 65536 | 50 | 18.893 / 18.984 / 19.070 | 18.252 | -3.39% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 | 2 | 65536 | 8 | 15.649 / 15.561 / 16.432 | 15.298 | -2.24% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 | 2 | 65536 | 7 | 16.789 / 16.628 / 17.557 | 16.259 | -3.16% | PASS |

a3-qwen35-tp4-longctx-p-65536-c4: scored 65 / 65 calls; all-population pass: True.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65664 tokens.
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 | 2 | 65536 | 32 | 21.417 / 21.608 / 22.212 | 21.901 | +2.26% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 | 2 | 65536 | 17 | 18.901 / 18.818 / 19.256 | 18.252 | -3.43% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 | 2 | 65536 | 8 | 16.891 / 16.719 / 17.533 | 16.259 | -3.74% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 | 2 | 65536 | 8 | 15.502 / 15.507 / 15.581 | 15.298 | -1.32% | PASS |

a3-qwen35-tp4-longctx-p-65536-c8: scored 65 / 65 calls; all-population pass: True.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65664 tokens.
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 1 | 4 | 65536 | 10 | 14.477 / 14.397 / 14.516 | 14.179 | -2.06% | PASS |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 2 | 4 | 65536 | 1 | 17.269 / 17.269 / 17.269 | 16.423 | -4.90% | PASS |

a5-qwen35-tp4-longctx-p65536-c4-o32: scored 11 / 11 calls; all-population pass: True.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65568 tokens.
| a5-qwen38-tp1-longctx-p126976-c4 | 1 | 4 | 126976 | 9 | 32.215 / 32.211 / 32.237 | 31.774 | -1.37% | PASS |
| a5-qwen38-tp1-longctx-p126976-c4 | 2 | 4 | 126976 | 8 | 35.503 / 35.500 / 35.516 | 34.003 | -4.22% | PASS |

a5-qwen38-tp1-longctx-p126976-c4: scored 17 / 17 calls; all-population pass: True.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 126976, bounds 126976–127008 tokens.
| a5-qwen38-tp1-longctx-p65536-c4 | 1 | 4 | 65536 | 5 | 24.481 / 24.481 / 24.493 | 24.148 | -1.36% | PASS |
| a5-qwen38-tp1-longctx-p65536-c4 | 2 | 4 | 65536 | 4 | 26.848 / 26.851 / 26.858 | 26.377 | -1.76% | PASS |
| a5-qwen38-tp1-longctx-p65536-c4 | 4 | 4 | 65536 | 2 | 29.056 / 29.056 / 29.389 | 28.814 | -0.83% | PASS |

a5-qwen38-tp1-longctx-p65536-c4: scored 11 / 11 calls; all-population pass: True.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65568 tokens.
| a3-qwen35-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 47 | 27.914 / 27.905 / 28.026 | 27.072 | -3.02% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 5 | 27.606 / 27.594 / 27.674 | 27.072 | -1.93% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | 4 | 4 | 24512 | 3 | 20.159 / 20.179 / 20.344 | 19.921 | -1.18% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 2 | 26.737 / 26.737 / 26.783 | 27.072 | +1.25% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | 6 | 4 | 24512 | 2 | 22.561 / 22.561 / 22.616 | 22.440 | -0.54% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | 3 | 4 | 24512 | 2 | 19.339 / 19.339 / 19.366 | 18.999 | -1.76% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | 2 | 4 | 24512 | 2 | 18.245 / 18.245 / 18.469 | 17.657 | -3.22% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 1 | 27.320 / 27.320 / 27.320 | 27.072 | -0.91% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | 8 | 4 | 24512 | 1 | 25.229 / 25.229 / 25.229 | 24.973 | -1.01% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | 1 | 4 | 24512 | 1 | 16.443 / 16.443 / 16.443 | 16.543 | +0.60% | PASS |

a3-qwen35-tp4-decode-c12-p24512: scored 66 / 66 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 45 | 30.548 / 30.507 / 30.812 | 30.132 | -1.36% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 5 | 29.822 / 29.824 / 29.931 | 30.132 | +1.04% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 2 | 4 | 64512 | 3 | 18.649 / 18.670 / 18.717 | 18.209 | -2.36% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 1 | 4 | 64512 | 3 | 17.131 / 17.174 / 17.190 | 16.911 | -1.28% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 2 | 30.154 / 30.154 / 30.172 | 30.132 | -0.07% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 8 | 4 | 64512 | 2 | 27.144 / 27.144 / 27.191 | 27.053 | -0.33% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 4 | 4 | 64512 | 2 | 21.293 / 21.293 / 21.391 | 21.061 | -1.09% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 8 | 4 | 64512 | 1 | 26.644 / 26.644 / 26.644 | 27.053 | +1.54% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 6 | 4 | 64512 | 1 | 24.465 / 24.465 / 24.465 | 24.040 | -1.73% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 6 | 4 | 64512 | 1 | 24.030 / 24.030 / 24.030 | 24.040 | +0.04% | PASS |

a3-qwen35-tp4-decode-c12-p64512: scored 65 / 65 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c12-p8512 | 12 | 4 | 8512 | 43 | 27.435 / 27.433 / 27.570 | 26.367 | -3.89% | PASS |
| a3-qwen35-tp4-decode-c12-p8512 | 8 | 4 | 8512 | 4 | 24.846 / 24.637 / 25.539 | 24.141 | -2.83% | PASS |
| a3-qwen35-tp4-decode-c12-p8512 | 12 | 4 | 8512 | 3 | 26.729 / 26.732 / 26.738 | 26.367 | -1.36% | PASS |
| a3-qwen35-tp4-decode-c12-p8512 | 1 | 4 | 8512 | 3 | 16.478 / 16.400 / 16.704 | 16.396 | -0.50% | PASS |
| a3-qwen35-tp4-decode-c12-p8512 | 12 | 4 | 8512 | 2 | 26.571 / 26.571 / 26.579 | 26.367 | -0.77% | PASS |
| a3-qwen35-tp4-decode-c12-p8512 | 6 | 4 | 8512 | 2 | 22.579 / 22.579 / 23.015 | 22.080 | -2.21% | PASS |
| a3-qwen35-tp4-decode-c12-p8512 | 2 | 4 | 8512 | 2 | 18.301 / 18.301 / 18.746 | 17.436 | -4.72% | PASS |
| a3-qwen35-tp4-decode-c12-p8512 | 6 | 4 | 8512 | 1 | 22.895 / 22.895 / 22.895 | 22.080 | -3.56% | PASS |
| a3-qwen35-tp4-decode-c12-p8512 | 4 | 4 | 8512 | 1 | 20.122 / 20.122 / 20.122 | 19.465 | -3.26% | PASS |
| a3-qwen35-tp4-decode-c12-p8512 | 3 | 4 | 8512 | 1 | 19.868 / 19.868 / 19.868 | 18.543 | -6.67% | PASS |

a3-qwen35-tp4-decode-c12-p8512: scored 62 / 62 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 58 | 33.166 / 33.160 / 33.280 | 32.580 | -1.77% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 2 | 4 | 96512 | 4 | 19.093 / 19.097 / 19.126 | 18.651 | -2.32% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 2 | 32.148 / 32.148 / 32.172 | 32.580 | +1.34% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 6 | 4 | 96512 | 2 | 24.892 / 24.892 / 24.934 | 25.320 | +1.72% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 1 | 32.464 / 32.464 / 32.464 | 32.580 | +0.36% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 1 | 30.525 / 30.525 / 30.525 | 32.580 | +6.73% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 8 | 4 | 96512 | 1 | 29.152 / 29.152 / 29.152 | 28.717 | -1.49% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 8 | 4 | 96512 | 1 | 28.172 / 28.172 / 28.172 | 28.717 | +1.94% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 6 | 4 | 96512 | 1 | 25.749 / 25.749 / 25.749 | 25.320 | -1.67% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 3 | 4 | 96512 | 1 | 20.650 / 20.650 / 20.650 | 21.051 | +1.94% | PASS |

a3-qwen35-tp4-decode-c12-p96512: scored 72 / 72 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 66 | 35.550 / 35.558 / 35.723 | 34.955 | -1.67% | PASS |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 4 | 35.286 / 35.290 / 35.309 | 34.955 | -0.94% | PASS |
| a3-qwen35-tp4-decode-c24-p24512 | 16 | 4 | 24512 | 2 | 29.030 / 29.030 / 29.088 | 29.071 | +0.14% | PASS |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 1 | 35.290 / 35.290 / 35.290 | 34.955 | -0.95% | PASS |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 1 | 35.251 / 35.251 / 35.251 | 34.955 | -0.84% | PASS |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 1 | 32.578 / 32.578 / 32.578 | 34.955 | +7.30% | PASS |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 1 | 32.499 / 32.499 / 32.499 | 34.955 | +7.56% | PASS |

a3-qwen35-tp4-decode-c24-p24512: scored 76 / 76 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 57 | 31.676 / 31.677 / 31.775 | 30.991 | -2.16% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 5 | 31.676 / 31.674 / 31.785 | 30.991 | -2.16% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | 1 | 4 | 8512 | 4 | 16.276 / 16.290 / 16.309 | 16.396 | +0.73% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | 8 | 4 | 8512 | 3 | 24.803 / 24.876 / 24.914 | 24.141 | -2.67% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 2 | 31.743 / 31.743 / 31.762 | 30.991 | -2.37% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | 6 | 4 | 8512 | 2 | 23.229 / 23.229 / 23.757 | 22.080 | -4.95% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | 4 | 4 | 8512 | 2 | 19.631 / 19.631 / 19.754 | 19.465 | -0.85% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 1 | 30.205 / 30.205 / 30.205 | 30.991 | +2.60% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 1 | 30.045 / 30.045 / 30.045 | 30.991 | +3.15% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | 16 | 4 | 8512 | 1 | 27.966 / 27.966 / 27.966 | 27.407 | -2.00% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | 12 | 4 | 8512 | 1 | 27.150 / 27.150 / 27.150 | 26.367 | -2.88% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | 12 | 4 | 8512 | 1 | 26.616 / 26.616 / 26.616 | 26.367 | -0.94% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | 12 | 4 | 8512 | 1 | 26.505 / 26.505 / 26.505 | 26.367 | -0.52% | PASS |

a3-qwen35-tp4-decode-c24-p8512: scored 81 / 81 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c2-p24512 | 1 | 4 | 24512 | 16 | 16.697 / 16.657 / 16.860 | 16.543 | -0.93% | PASS |
| a3-qwen35-tp4-decode-c2-p24512 | 2 | 4 | 24512 | 2 | 18.147 / 18.147 / 18.217 | 17.657 | -2.70% | PASS |

a3-qwen35-tp4-decode-c2-p24512: scored 18 / 18 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c2-p64512 | 1 | 4 | 64512 | 7 | 17.136 / 17.138 / 17.270 | 16.911 | -1.31% | PASS |
| a3-qwen35-tp4-decode-c2-p64512 | 2 | 4 | 64512 | 4 | 18.681 / 18.662 / 18.872 | 18.209 | -2.53% | PASS |

a3-qwen35-tp4-decode-c2-p64512: scored 11 / 11 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c2-p96512 | 1 | 4 | 96512 | 12 | 17.338 / 17.324 / 17.456 | 17.205 | -0.76% | PASS |
| a3-qwen35-tp4-decode-c2-p96512 | 2 | 4 | 96512 | 1 | 19.025 / 19.025 / 19.025 | 18.651 | -1.97% | PASS |

a3-qwen35-tp4-decode-c2-p96512: scored 13 / 13 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c6-p24512 | 6 | 4 | 24512 | 23 | 23.225 / 23.181 / 23.327 | 22.440 | -3.38% | PASS |
| a3-qwen35-tp4-decode-c6-p24512 | 6 | 4 | 24512 | 10 | 22.732 / 22.725 / 22.825 | 22.440 | -1.28% | PASS |
| a3-qwen35-tp4-decode-c6-p24512 | 1 | 4 | 24512 | 8 | 16.594 / 16.577 / 16.924 | 16.543 | -0.31% | PASS |
| a3-qwen35-tp4-decode-c6-p24512 | 2 | 4 | 24512 | 3 | 18.051 / 18.068 / 18.143 | 17.657 | -2.18% | PASS |
| a3-qwen35-tp4-decode-c6-p24512 | 3 | 4 | 24512 | 1 | 19.134 / 19.134 / 19.134 | 18.999 | -0.70% | PASS |

a3-qwen35-tp4-decode-c6-p24512: scored 45 / 45 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c6-p64512 | 6 | 4 | 64512 | 40 | 24.666 / 24.667 / 24.763 | 24.040 | -2.54% | PASS |
| a3-qwen35-tp4-decode-c6-p64512 | 2 | 4 | 64512 | 2 | 18.846 / 18.846 / 18.912 | 18.209 | -3.38% | PASS |
| a3-qwen35-tp4-decode-c6-p64512 | 6 | 4 | 64512 | 1 | 24.044 / 24.044 / 24.044 | 24.040 | -0.02% | PASS |
| a3-qwen35-tp4-decode-c6-p64512 | 3 | 4 | 64512 | 1 | 20.966 / 20.966 / 20.966 | 20.139 | -3.94% | PASS |

a3-qwen35-tp4-decode-c6-p64512: scored 44 / 44 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c6-p8512 | 6 | 4 | 8512 | 21 | 22.846 / 22.849 / 22.926 | 22.080 | -3.35% | PASS |
| a3-qwen35-tp4-decode-c6-p8512 | 6 | 4 | 8512 | 6 | 22.307 / 22.130 / 23.271 | 22.080 | -1.02% | PASS |
| a3-qwen35-tp4-decode-c6-p8512 | 1 | 4 | 8512 | 4 | 16.413 / 16.480 / 16.495 | 16.396 | -0.11% | PASS |
| a3-qwen35-tp4-decode-c6-p8512 | 4 | 4 | 8512 | 3 | 19.802 / 19.803 / 19.841 | 19.465 | -1.71% | PASS |
| a3-qwen35-tp4-decode-c6-p8512 | 2 | 4 | 8512 | 3 | 17.950 / 17.777 / 18.306 | 17.436 | -2.86% | PASS |

a3-qwen35-tp4-decode-c6-p8512: scored 37 / 37 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c6-p96512 | 6 | 4 | 96512 | 42 | 26.149 / 25.837 / 26.090 | 25.320 | -3.17% | PASS |
| a3-qwen35-tp4-decode-c6-p96512 | 1 | 4 | 96512 | 3 | 17.198 / 17.217 / 17.249 | 17.205 | +0.04% | PASS |
| a3-qwen35-tp4-decode-c6-p96512 | 4 | 4 | 96512 | 2 | 22.157 / 22.157 / 22.231 | 21.973 | -0.83% | PASS |
| a3-qwen35-tp4-decode-c6-p96512 | 3 | 4 | 96512 | 2 | 20.734 / 20.734 / 20.752 | 21.051 | +1.53% | PASS |
| a3-qwen35-tp4-decode-c6-p96512 | 6 | 4 | 96512 | 1 | 24.858 / 24.858 / 24.858 | 25.320 | +1.86% | PASS |
| a3-qwen35-tp4-decode-c6-p96512 | 2 | 4 | 96512 | 1 | 19.098 / 19.098 / 19.098 | 18.651 | -2.34% | PASS |

a3-qwen35-tp4-decode-c6-p96512: scored 51 / 51 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c2-p24512 | 2 | 4 | 24512 | 58 | 26.724 / 26.694 / 26.806 | 25.884 | -3.14% | PASS |
| a3-qwen36-tp2-decode-c2-p24512 | 1 | 4 | 24512 | 4 | 24.082 / 24.057 / 24.170 | 24.135 | +0.22% | PASS |

a3-qwen36-tp2-decode-c2-p24512: scored 62 / 62 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c2-p64512 | 2 | 4 | 64512 | 58 | 28.868 / 28.845 / 28.903 | 27.964 | -3.13% | PASS |
| a3-qwen36-tp2-decode-c2-p64512 | 1 | 4 | 64512 | 2 | 25.571 / 25.571 / 25.671 | 25.415 | -0.61% | PASS |

a3-qwen36-tp2-decode-c2-p64512: scored 60 / 60 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c2-p8512 | 2 | 4 | 8512 | 45 | 25.809 / 25.747 / 25.801 | 25.052 | -2.93% | PASS |
| a3-qwen36-tp2-decode-c2-p8512 | 1 | 4 | 8512 | 1 | 23.898 / 23.898 / 23.898 | 23.623 | -1.15% | PASS |

a3-qwen36-tp2-decode-c2-p8512: scored 46 / 46 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c2-p96512 | 2 | 4 | 96512 | 62 | 30.222 / 30.218 / 30.266 | 29.628 | -1.96% | PASS |
| a3-qwen36-tp2-decode-c2-p96512 | 1 | 4 | 96512 | 8 | 26.458 / 26.465 / 26.476 | 26.439 | -0.07% | PASS |

a3-qwen36-tp2-decode-c2-p96512: scored 70 / 70 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c6-p24512 | 6 | 4 | 24512 | 71 | 33.717 / 33.762 / 33.825 | 34.040 | +0.96% | PASS |
| a3-qwen36-tp2-decode-c6-p24512 | 6 | 4 | 24512 | 3 | 32.197 / 32.189 / 32.215 | 34.040 | +5.72% | PASS |
| a3-qwen36-tp2-decode-c6-p24512 | 2 | 4 | 24512 | 3 | 26.611 / 26.592 / 26.658 | 25.884 | -2.73% | PASS |
| a3-qwen36-tp2-decode-c6-p24512 | 3 | 4 | 24512 | 2 | 28.284 / 28.284 / 28.296 | 28.328 | +0.16% | PASS |
| a3-qwen36-tp2-decode-c6-p24512 | 1 | 4 | 24512 | 2 | 24.086 / 24.086 / 24.086 | 24.135 | +0.20% | PASS |

a3-qwen36-tp2-decode-c6-p24512: scored 81 / 81 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c6-p8512 | 6 | 4 | 8512 | 61 | 32.027 / 31.966 / 32.038 | 31.583 | -1.39% | PASS |
| a3-qwen36-tp2-decode-c6-p8512 | 2 | 4 | 8512 | 4 | 25.655 / 25.632 / 25.749 | 25.052 | -2.35% | PASS |
| a3-qwen36-tp2-decode-c6-p8512 | 4 | 4 | 8512 | 3 | 29.068 / 29.004 / 29.228 | 28.061 | -3.46% | PASS |
| a3-qwen36-tp2-decode-c6-p8512 | 6 | 4 | 8512 | 2 | 31.017 / 31.017 / 31.028 | 31.583 | +1.82% | PASS |
| a3-qwen36-tp2-decode-c6-p8512 | 3 | 4 | 8512 | 2 | 26.970 / 26.970 / 26.987 | 26.754 | -0.80% | PASS |

a3-qwen36-tp2-decode-c6-p8512: scored 72 / 72 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 56 | 30.908 / 30.898 / 30.968 | 29.698 | -3.92% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 1 | 4 | 24512 | 5 | 17.858 / 17.763 / 18.319 | 17.872 | +0.08% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 4 | 29.450 / 29.456 / 29.484 | 29.698 | +0.84% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 3 | 30.283 / 30.285 / 30.300 | 29.698 | -1.93% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 2 | 4 | 24512 | 2 | 19.259 / 19.259 / 19.377 | 19.033 | -1.18% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 1 | 28.776 / 28.776 / 28.776 | 29.698 | +3.20% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 6 | 4 | 24512 | 1 | 24.934 / 24.934 / 24.934 | 23.299 | -6.56% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 6 | 4 | 24512 | 1 | 24.287 / 24.287 / 24.287 | 23.299 | -4.07% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 3 | 4 | 24512 | 1 | 20.102 / 20.102 / 20.102 | 20.261 | +0.79% | PASS |

a3-qwen38-tp4-decode-c12-p24512: scored 74 / 74 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 68 | 35.845 / 35.986 / 36.161 | 34.882 | -2.69% | PASS |
| a3-qwen38-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 5 | 32.176 / 32.177 / 32.195 | 34.882 | +8.41% | PASS |
| a3-qwen38-tp4-decode-c12-p64512 | 8 | 4 | 64512 | 2 | 31.108 / 31.108 / 31.443 | 29.152 | -6.29% | PASS |
| a3-qwen38-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 1 | 34.707 / 34.707 / 34.707 | 34.882 | +0.50% | PASS |

a3-qwen38-tp4-decode-c12-p64512: scored 76 / 76 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 65 | 39.782 / 39.852 / 40.095 | 39.029 | -1.89% | PASS |
| a3-qwen38-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 3 | 35.379 / 35.367 / 35.422 | 39.029 | +10.32% | PASS |
| a3-qwen38-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 2 | 38.252 / 38.252 / 38.309 | 39.029 | +2.03% | PASS |
| a3-qwen38-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 1 | 37.966 / 37.966 / 37.966 | 39.029 | +2.80% | PASS |

a3-qwen38-tp4-decode-c12-p96512: scored 71 / 71 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c2-p24512 | 2 | 4 | 24512 | 11 | 19.404 / 19.244 / 20.150 | 19.033 | -1.91% | PASS |
| a3-qwen38-tp4-decode-c2-p24512 | 1 | 4 | 24512 | 4 | 17.817 / 17.836 / 17.873 | 17.872 | +0.31% | PASS |

a3-qwen38-tp4-decode-c2-p24512: scored 15 / 15 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c2-p64512 | 2 | 4 | 64512 | 20 | 20.210 / 20.021 / 20.180 | 19.993 | -1.07% | PASS |
| a3-qwen38-tp4-decode-c2-p64512 | 1 | 4 | 64512 | 3 | 18.455 / 18.447 / 18.491 | 18.509 | +0.29% | PASS |

a3-qwen38-tp4-decode-c2-p64512: scored 23 / 23 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c2-p96512 | 2 | 4 | 96512 | 24 | 20.989 / 20.830 / 21.239 | 20.761 | -1.08% | PASS |
| a3-qwen38-tp4-decode-c2-p96512 | 1 | 4 | 96512 | 3 | 19.328 / 19.048 / 19.910 | 19.019 | -1.60% | PASS |

a3-qwen38-tp4-decode-c2-p96512: scored 27 / 27 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c6-p24512 | 6 | 4 | 24512 | 38 | 24.761 / 24.752 / 24.829 | 23.299 | -5.91% | PASS |
| a3-qwen38-tp4-decode-c6-p24512 | 6 | 4 | 24512 | 3 | 24.323 / 24.320 / 24.333 | 23.299 | -4.21% | PASS |
| a3-qwen38-tp4-decode-c6-p24512 | 2 | 4 | 24512 | 2 | 19.597 / 19.597 / 19.909 | 19.033 | -2.88% | PASS |
| a3-qwen38-tp4-decode-c6-p24512 | 1 | 4 | 24512 | 2 | 17.817 / 17.817 / 17.863 | 17.872 | +0.31% | PASS |
| a3-qwen38-tp4-decode-c6-p24512 | 4 | 4 | 24512 | 1 | 22.503 / 22.503 / 22.503 | 21.395 | -4.92% | PASS |

a3-qwen38-tp4-decode-c6-p24512: scored 46 / 46 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c6-p64512 | 6 | 4 | 64512 | 40 | 27.237 / 27.135 / 27.365 | 26.019 | -4.47% | PASS |
| a3-qwen38-tp4-decode-c6-p64512 | 4 | 4 | 64512 | 5 | 23.956 / 23.825 / 24.480 | 23.226 | -3.05% | PASS |
| a3-qwen38-tp4-decode-c6-p64512 | 3 | 4 | 64512 | 4 | 22.568 / 22.104 / 24.375 | 21.733 | -3.70% | PASS |
| a3-qwen38-tp4-decode-c6-p64512 | 6 | 4 | 64512 | 2 | 26.501 / 26.501 / 26.502 | 26.019 | -1.82% | PASS |
| a3-qwen38-tp4-decode-c6-p64512 | 2 | 4 | 64512 | 2 | 20.478 / 20.478 / 20.765 | 19.993 | -2.37% | PASS |
| a3-qwen38-tp4-decode-c6-p64512 | 1 | 4 | 64512 | 2 | 18.774 / 18.774 / 19.076 | 18.509 | -1.41% | PASS |

a3-qwen38-tp4-decode-c6-p64512: scored 55 / 55 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c6-p96512 | 6 | 4 | 96512 | 42 | 29.560 / 29.308 / 29.565 | 28.195 | -4.62% | PASS |
| a3-qwen38-tp4-decode-c6-p96512 | 1 | 4 | 96512 | 6 | 19.227 / 19.055 / 20.072 | 19.019 | -1.08% | PASS |
| a3-qwen38-tp4-decode-c6-p96512 | 3 | 4 | 96512 | 5 | 22.911 / 22.846 / 23.176 | 22.911 | +0.00% | PASS |
| a3-qwen38-tp4-decode-c6-p96512 | 6 | 4 | 96512 | 4 | 28.344 / 28.354 / 28.383 | 28.195 | -0.52% | PASS |
| a3-qwen38-tp4-decode-c6-p96512 | 2 | 4 | 96512 | 4 | 20.979 / 20.931 / 21.140 | 20.761 | -1.04% | PASS |
| a3-qwen38-tp4-decode-c6-p96512 | 4 | 4 | 96512 | 3 | 25.537 / 25.517 / 25.608 | 24.690 | -3.32% | PASS |

a3-qwen38-tp4-decode-c6-p96512: scored 64 / 64 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-v41-tp4dp4-decode-c4-p8512 | 1 | 8 | 8512 | 28 | 35.585 / 36.156 / 36.274 | 32.194 | -9.53% | PASS |
| a3-v41-tp4dp4-decode-c4-p8512 | 2 | 8 | 8512 | 4 | 48.069 / 48.195 / 48.257 | 50.317 | +4.68% | PASS |

a3-v41-tp4dp4-decode-c4-p8512: scored 32 / 32 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.

| Case | B / q | Layer group | Layers | Real mean / P50 ms | Sim mean / P50 ms | Mean / P50 error |
|---|---|---|---:|---:|---:|---:|
| glm53flash-a3-tp16-c4-livepre | 4 / 6 | kda | 34 | 0.573 / 0.580 | 0.600 / 0.623 | +4.70% / +7.51% |
| glm53flash-a3-tp16-c4-livepre | 4 / 6 | mla | 11 | 0.930 / 0.929 | 0.901 / 0.901 | -3.05% / -3.02% |
| glm53flash-a3-tp16-c4-livepre | 4 / 6 | dense_layer | 3 | 0.474 / 0.297 | 0.359 / 0.359 | -24.26% / +21.06% |
| glm53flash-a3-tp16-c4-livepre | 4 / 6 | moe_layer | 42 | 0.674 / 0.591 | 0.696 / 0.623 | +3.36% / +5.50% |
| glm53flash-a3-tp16-c16-livepre | 16 / 6 | kda | 34 | 0.763 / 0.773 | 0.767 / 0.802 | +0.60% / +3.71% |
| glm53flash-a3-tp16-c16-livepre | 16 / 6 | mla | 11 | 1.371 / 1.378 | 1.663 / 1.663 | +21.32% / +20.73% |
| glm53flash-a3-tp16-c16-livepre | 16 / 6 | dense_layer | 3 | 0.619 / 0.429 | 0.415 / 0.415 | -33.03% / -3.29% |
| glm53flash-a3-tp16-c16-livepre | 16 / 6 | moe_layer | 42 | 0.932 / 0.792 | 1.027 / 0.802 | +10.18% / +1.17% |
| glm53flash-a3-tp16-c2 | 2 / 6 | kda | 34 | 0.693 / 0.695 | 0.641 / 0.665 | -7.48% / -4.23% |
| glm53flash-a3-tp16-c2 | 2 / 6 | mla | 11 | 0.955 / 0.951 | 0.905 / 0.905 | -5.23% / -4.87% |
| glm53flash-a3-tp16-c2 | 2 / 6 | dense_layer | 3 | 0.589 / 0.573 | 0.392 / 0.392 | -33.49% / -31.69% |
| glm53flash-a3-tp16-c2 | 2 / 6 | moe_layer | 42 | 0.769 / 0.711 | 0.728 / 0.665 | -5.33% / -6.36% |
| glm53flash-a3-tp16-c4 | 4 / 6 | kda | 34 | 0.793 / 0.809 | 0.738 / 0.770 | -6.98% / -4.77% |
| glm53flash-a3-tp16-c4 | 4 / 6 | mla | 11 | 1.167 / 1.165 | 1.080 / 1.080 | -7.39% / -7.30% |
| glm53flash-a3-tp16-c4 | 4 / 6 | dense_layer | 3 | 0.615 / 0.614 | 0.397 / 0.397 | -35.45% / -35.31% |
| glm53flash-a3-tp16-c4 | 4 / 6 | moe_layer | 42 | 0.903 / 0.813 | 0.852 / 0.770 | -5.74% / -5.21% |
| glm53flash-a5-tp8-c3 | 4 / 4 | kda | 34 | 0.413 / 0.421 | 0.409 / 0.429 | -0.84% / +1.89% |
| glm53flash-a5-tp8-c3 | 4 / 4 | mla | 11 | 0.639 / 0.634 | 0.627 / 0.627 | -1.96% / -1.16% |
| glm53flash-a5-tp8-c3 | 4 / 4 | dense_layer | 3 | 0.314 / 0.240 | 0.202 / 0.202 | -35.76% / -16.04% |
| glm53flash-a5-tp8-c3 | 4 / 4 | moe_layer | 42 | 0.479 / 0.424 | 0.481 / 0.429 | +0.40% / +1.18% |
| glm53flash-a5-tp8-c96 | 96 / 4 | kda | 34 | 0.971 / 1.009 | 1.073 / 1.112 | +10.49% / +10.24% |
| glm53flash-a5-tp8-c96 | 96 / 4 | mla | 11 | 2.233 / 2.234 | 2.319 / 2.319 | +3.84% / +3.83% |
| glm53flash-a5-tp8-c96 | 96 / 4 | dense_layer | 3 | 0.583 / 0.573 | 0.669 / 0.669 | +14.85% / +16.86% |
| glm53flash-a5-tp8-c96 | 96 / 4 | moe_layer | 42 | 1.330 / 1.011 | 1.428 / 1.112 | +7.43% / +10.06% |
| glm53flash-a5-tp8-c1 | 1 / 4 | kda | 34 | 0.301 / 0.299 | 0.298 / 0.309 | -0.87% / +3.63% |
| glm53flash-a5-tp8-c1 | 1 / 4 | mla | 11 | 0.495 / 0.491 | 0.483 / 0.483 | -2.41% / -1.66% |
| glm53flash-a5-tp8-c1 | 1 / 4 | dense_layer | 3 | 0.307 / 0.263 | 0.186 / 0.186 | -39.47% / -29.58% |
| glm53flash-a5-tp8-c1 | 1 / 4 | moe_layer | 42 | 0.351 / 0.302 | 0.355 / 0.309 | +0.97% / +2.37% |
| a5_kimi_k3_p32768_c1 | 1 / 1 | kda | 69 | 0.338 / 0.339 | 0.335 / 0.337 | -0.91% / -0.67% |
| a5_kimi_k3_p32768_c1 | 1 / 1 | mla | 24 | 0.383 / 0.376 | 0.375 / 0.375 | -2.21% / -0.35% |
| a5_kimi_k3_p32768_c1 | 1 / 1 | dense_layer | 1 | 0.258 / 0.258 | 0.208 / 0.208 | -19.23% / -19.23% |
| a5_kimi_k3_p32768_c1 | 1 / 1 | moe_layer | 92 | 0.351 / 0.341 | 0.347 / 0.337 | -1.14% / -1.18% |
| v4flash-a3-tp8-c4 | 4 / 2 | mla | 43 | 0.754 / 0.757 | 0.681 / 0.634 | -9.75% / -16.29% |
| v4flash-a3-tp8-c4 | 4 / 2 | moe_layer | 43 | 0.754 / 0.757 | 0.681 / 0.634 | -9.75% / -16.29% |
| v4flash-a3-tp8-c8 | 8 / 2 | mla | 43 | 0.877 / 0.807 | 0.807 / 0.766 | -7.97% / -5.17% |
| v4flash-a3-tp8-c8 | 8 / 2 | moe_layer | 43 | 0.877 / 0.807 | 0.807 / 0.766 | -7.97% / -5.17% |
| a3_glm53_dc4k_b1 | 1 / 1 | mla | 78 | 0.499 / 0.484 | 0.488 / 0.472 | -2.18% / -2.56% |
| a3_glm53_dc4k_b1 | 1 / 1 | dense_layer | 3 | 0.388 / 0.385 | 0.392 / 0.392 | +1.11% / +1.77% |
| a3_glm53_dc4k_b1 | 1 / 1 | moe_layer | 75 | 0.503 / 0.484 | 0.492 / 0.472 | -2.28% / -2.58% |
| a3_glm53_dc4k_b2 | 2 / 1 | mla | 78 | 0.524 / 0.509 | 0.510 / 0.494 | -2.79% / -2.93% |
| a3_glm53_dc4k_b2 | 2 / 1 | dense_layer | 3 | 0.403 / 0.408 | 0.400 / 0.400 | -0.80% / -1.98% |
| a3_glm53_dc4k_b2 | 2 / 1 | moe_layer | 75 | 0.529 / 0.509 | 0.514 / 0.494 | -2.85% / -3.01% |
| a3_glm53_dc4k_b4 | 4 / 1 | mla | 78 | 0.556 / 0.540 | 0.551 / 0.542 | -0.98% / +0.42% |
| a3_glm53_dc4k_b4 | 4 / 1 | dense_layer | 3 | 0.402 / 0.399 | 0.414 / 0.414 | +2.92% / +3.62% |
| a3_glm53_dc4k_b4 | 4 / 1 | moe_layer | 75 | 0.562 / 0.541 | 0.556 / 0.542 | -1.09% / +0.27% |
| a3_glm53_dc4k_b8 | 8 / 1 | mla | 78 | 0.603 / 0.587 | 0.566 / 0.559 | -6.20% / -4.79% |
| a3_glm53_dc4k_b8 | 8 / 1 | dense_layer | 3 | 0.416 / 0.413 | 0.366 / 0.366 | -11.96% / -11.37% |
| a3_glm53_dc4k_b8 | 8 / 1 | moe_layer | 75 | 0.611 / 0.588 | 0.574 / 0.559 | -6.04% / -4.87% |
| a3_glm53_dc16k_b1 | 1 / 1 | mla | 78 | 0.500 / 0.483 | 0.491 / 0.473 | -1.77% / -2.10% |
| a3_glm53_dc16k_b1 | 1 / 1 | dense_layer | 3 | 0.396 / 0.394 | 0.404 / 0.403 | +1.87% / +2.47% |
| a3_glm53_dc16k_b1 | 1 / 1 | moe_layer | 75 | 0.504 / 0.483 | 0.495 / 0.473 | -1.88% / -2.24% |
| qwen35-397b-a3-tp16-c48 | 64 / 4 | gdn | 45 | 1.236 / 1.203 | 1.221 / 1.222 | -1.14% / +1.53% |
| qwen35-397b-a3-tp16-c48 | 64 / 4 | gqa | 15 | 1.361 / 1.341 | 1.346 / 1.346 | -1.13% / +0.32% |
| qwen35-397b-a3-tp16-c48 | 64 / 4 | moe_layer | 60 | 1.267 / 1.279 | 1.253 / 1.222 | -1.14% / -4.48% |
| qwen35-397b-a3-tp16-c136 | 160 / 4 | gdn | 45 | 1.959 / 1.940 | 1.936 / 1.936 | -1.18% / -0.21% |
| qwen35-397b-a3-tp16-c136 | 160 / 4 | gqa | 15 | 2.054 / 2.022 | 2.036 / 2.036 | -0.91% / +0.67% |
| qwen35-397b-a3-tp16-c136 | 160 / 4 | moe_layer | 60 | 1.983 / 1.996 | 1.961 / 1.936 | -1.11% / -3.02% |
| qwen35-35b-a5-tp4-c64-graph | 64 / 4 | gdn | 30 | 0.555 / 0.547 | 0.513 / 0.513 | -7.44% / -6.17% |
| qwen35-35b-a5-tp4-c64-graph | 64 / 4 | gqa | 10 | 0.532 / 0.532 | 0.458 / 0.458 | -13.98% / -14.06% |
| qwen35-35b-a5-tp4-c64-graph | 64 / 4 | moe_layer | 40 | 0.549 / 0.546 | 0.499 / 0.513 | -9.02% / -5.95% |
| qwen35-35b-a5-tp4-c128-graph | 128 / 4 | gdn | 30 | 0.721 / 0.720 | 0.671 / 0.671 | -6.89% / -6.77% |
| qwen35-35b-a5-tp4-c128-graph | 128 / 4 | gqa | 10 | 0.695 / 0.695 | 0.592 / 0.592 | -14.88% / -14.79% |
| qwen35-35b-a5-tp4-c128-graph | 128 / 4 | moe_layer | 40 | 0.715 / 0.720 | 0.651 / 0.671 | -8.83% / -6.70% |
| qwen35-35b-a5-tp4-c4-graph | 4 / 4 | gdn | 30 | 0.285 / 0.282 | 0.282 / 0.282 | -1.09% / -0.02% |
| qwen35-35b-a5-tp4-c4-graph | 4 / 4 | gqa | 10 | 0.299 / 0.299 | 0.293 / 0.293 | -1.88% / -1.87% |
| qwen35-35b-a5-tp4-c4-graph | 4 / 4 | moe_layer | 40 | 0.289 / 0.283 | 0.285 / 0.282 | -1.30% / -0.27% |
| qwen36-a5-tp2-c12 | 12 / 4 | gdn | 48 | 0.409 / 0.404 | 0.422 / 0.422 | +3.15% / +4.38% |
| qwen36-a5-tp2-c12 | 12 / 4 | gqa | 16 | 0.285 / 0.284 | 0.232 / 0.232 | -18.49% / -18.46% |
| qwen36-a5-tp2-c12 | 12 / 4 | dense_layer | 64 | 0.378 / 0.402 | 0.374 / 0.422 | -0.92% / +4.86% |
| qwen36-a5-tp2-c96 | 96 / 4 | gdn | 48 | 1.065 / 1.059 | 1.046 / 1.046 | -1.78% / -1.21% |
| qwen36-a5-tp2-c96 | 96 / 4 | gqa | 16 | 0.793 / 0.793 | 0.790 / 0.790 | -0.44% / -0.41% |
| qwen36-a5-tp2-c96 | 96 / 4 | dense_layer | 64 | 0.997 / 1.058 | 0.982 / 1.046 | -1.52% / -1.10% |
| qwen36-a5-tp2-c1 | 1 / 4 | gdn | 48 | 0.193 / 0.192 | 0.191 / 0.191 | -0.96% / -0.32% |
| qwen36-a5-tp2-c1 | 1 / 4 | gqa | 16 | 0.188 / 0.188 | 0.195 / 0.195 | +3.55% / +3.46% |
| qwen36-a5-tp2-c1 | 1 / 4 | dense_layer | 64 | 0.192 / 0.191 | 0.192 / 0.191 | +0.14% / -0.15% |
| a3_glm53_w4a8_tp16_tpot30_c2 | 2 / 6 | mla | 78 | 0.739 / 0.743 | 0.730 / 0.707 | -1.21% / -4.92% |
| a3_glm53_w4a8_tp16_tpot30_c2 | 2 / 6 | dense_layer | 3 | 0.573 / 0.577 | 0.674 / 0.674 | +17.63% / +16.64% |
| a3_glm53_w4a8_tp16_tpot30_c2 | 2 / 6 | moe_layer | 75 | 0.746 / 0.746 | 0.732 / 0.707 | -1.78% / -5.26% |
| a3_glm53_w4a8_tp16_tpot50_c2 | 2 / 6 | mla | 78 | 0.741 / 0.741 | 0.733 / 0.709 | -1.10% / -4.29% |
| a3_glm53_w4a8_tp16_tpot50_c2 | 2 / 6 | dense_layer | 3 | 0.588 / 0.568 | 0.681 / 0.680 | +15.81% / +19.78% |
| a3_glm53_w4a8_tp16_tpot50_c2 | 2 / 6 | moe_layer | 75 | 0.747 / 0.742 | 0.735 / 0.709 | -1.63% / -4.41% |
| a3_glm53_w4a8_tp16_tpot88_c8 | 8 / 6 | mla | 78 | 0.892 / 0.867 | 0.856 / 0.829 | -4.01% / -4.28% |
| a3_glm53_w4a8_tp16_tpot88_c8 | 8 / 6 | dense_layer | 3 | 0.647 / 0.656 | 0.671 / 0.672 | +3.73% / +2.45% |
| a3_glm53_w4a8_tp16_tpot88_c8 | 8 / 6 | moe_layer | 75 | 0.901 / 0.867 | 0.863 / 0.829 | -4.23% / -4.33% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | 1 / 1 | mla | 40 | 0.328 / 0.299 | 0.311 / 0.300 | -5.30% / +0.34% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | 1 / 1 | moe_layer | 40 | 0.328 / 0.299 | 0.311 / 0.300 | -5.30% / +0.34% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | 1 / 1 | mla | 40 | 0.332 / 0.302 | 0.304 / 0.293 | -8.53% / -2.86% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | 1 / 1 | moe_layer | 40 | 0.332 / 0.302 | 0.304 / 0.293 | -8.53% / -2.86% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 8 / 1 | mla | 40 | 0.658 / 0.634 | 0.620 / 0.608 | -5.75% / -4.00% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 8 / 1 | moe_layer | 40 | 0.658 / 0.634 | 0.620 / 0.608 | -5.75% / -4.00% |
| a5_glm53flash_tp8_c16_p4k | 16 / 4 | kda | 34 | 0.647 / 0.677 | 0.643 / 0.678 | -0.70% / +0.11% |
| a5_glm53flash_tp8_c16_p4k | 16 / 4 | mla | 11 | 1.002 / 0.997 | 0.973 / 0.973 | -2.84% / -2.39% |
| a5_glm53flash_tp8_c16_p4k | 16 / 4 | dense_layer | 3 | 0.331 / 0.299 | 0.282 / 0.282 | -14.78% / -5.55% |
| a5_glm53flash_tp8_c16_p4k | 16 / 4 | moe_layer | 42 | 0.763 / 0.680 | 0.755 / 0.678 | -1.00% / -0.36% |
| a5_glm53flash_tp8_c16_p8k | 16 / 4 | kda | 34 | 0.646 / 0.677 | 0.642 / 0.677 | -0.60% / +0.04% |
| a5_glm53flash_tp8_c16_p8k | 16 / 4 | mla | 11 | 1.059 / 1.055 | 1.022 / 1.022 | -3.51% / -3.15% |
| a5_glm53flash_tp8_c16_p8k | 16 / 4 | dense_layer | 3 | 0.328 / 0.298 | 0.282 / 0.282 | -13.94% / -5.38% |
| a5_glm53flash_tp8_c16_p8k | 16 / 4 | moe_layer | 42 | 0.777 / 0.678 | 0.767 / 0.677 | -1.24% / -0.17% |
| a5_glm53flash_tp8_c32_p4k | 32 / 4 | kda | 34 | 0.721 / 0.752 | 0.677 / 0.714 | -6.09% / -5.04% |
| a5_glm53flash_tp8_c32_p4k | 32 / 4 | mla | 11 | 1.197 / 1.194 | 1.053 / 1.053 | -12.04% / -11.78% |
| a5_glm53flash_tp8_c32_p4k | 32 / 4 | dense_layer | 3 | 0.398 / 0.353 | 0.286 / 0.286 | -28.05% / -18.96% |
| a5_glm53flash_tp8_c32_p4k | 32 / 4 | moe_layer | 42 | 0.868 / 0.754 | 0.803 / 0.714 | -7.52% / -5.26% |
| a5_glm53flash_tp8_c32_p8k | 32 / 4 | kda | 34 | 0.720 / 0.751 | 0.716 / 0.753 | -0.57% / +0.39% |
| a5_glm53flash_tp8_c32_p8k | 32 / 4 | mla | 11 | 1.295 / 1.291 | 1.251 / 1.251 | -3.35% / -3.07% |
| a5_glm53flash_tp8_c32_p8k | 32 / 4 | dense_layer | 3 | 0.399 / 0.354 | 0.325 / 0.325 | -18.47% / -8.10% |
| a5_glm53flash_tp8_c32_p8k | 32 / 4 | moe_layer | 42 | 0.893 / 0.753 | 0.884 / 0.753 | -1.06% / +0.03% |
| a5_glm53flash_tp8_c4_p8k | 4 / 4 | kda | 34 | 0.412 / 0.425 | 0.408 / 0.427 | -0.91% / +0.63% |
| a5_glm53flash_tp8_c4_p8k | 4 / 4 | mla | 11 | 0.673 / 0.670 | 0.654 / 0.654 | -2.80% / -2.27% |
| a5_glm53flash_tp8_c4_p8k | 4 / 4 | dense_layer | 3 | 0.264 / 0.235 | 0.211 / 0.211 | -20.19% / -10.32% |
| a5_glm53flash_tp8_c4_p8k | 4 / 4 | moe_layer | 42 | 0.491 / 0.429 | 0.487 / 0.427 | -0.85% / -0.28% |
| a5_glm53flash_tp8_c64_p4k | 64 / 4 | kda | 34 | 0.853 / 0.886 | 0.857 / 0.900 | +0.43% / +1.51% |
| a5_glm53flash_tp8_c64_p4k | 64 / 4 | mla | 11 | 1.593 / 1.584 | 1.531 / 1.531 | -3.87% / -3.34% |
| a5_glm53flash_tp8_c64_p4k | 64 / 4 | dense_layer | 3 | 0.497 / 0.470 | 0.413 / 0.413 | -16.86% / -12.17% |
| a5_glm53flash_tp8_c64_p4k | 64 / 4 | moe_layer | 42 | 1.072 / 0.890 | 1.065 / 0.900 | -0.67% / +1.14% |
| a5_glm53flash_tp8_c8_p4k | 8 / 4 | kda | 34 | 0.567 / 0.589 | 0.563 / 0.593 | -0.83% / +0.78% |
| a5_glm53flash_tp8_c8_p4k | 8 / 4 | mla | 11 | 0.868 / 0.868 | 0.842 / 0.842 | -3.02% / -3.03% |
| a5_glm53flash_tp8_c8_p4k | 8 / 4 | dense_layer | 3 | 0.335 / 0.258 | 0.245 / 0.245 | -26.97% / -5.09% |
| a5_glm53flash_tp8_c8_p4k | 8 / 4 | moe_layer | 42 | 0.663 / 0.593 | 0.658 / 0.593 | -0.64% / +0.02% |
| a3_glm53flash_tp16_aclgraph_c16 | 16 / 6 | kda | 34 | 1.038 / 1.074 | 0.895 / 0.939 | -13.79% / -12.53% |
| a3_glm53flash_tp16_aclgraph_c16 | 16 / 6 | mla | 11 | 1.686 / 1.687 | 1.693 / 1.693 | +0.40% / +0.34% |
| a3_glm53flash_tp16_aclgraph_c16 | 16 / 6 | dense_layer | 3 | 0.667 / 0.670 | 0.438 / 0.438 | -34.36% / -34.58% |
| a3_glm53flash_tp16_aclgraph_c16 | 16 / 6 | moe_layer | 42 | 1.234 / 1.078 | 1.137 / 0.939 | -7.92% / -12.86% |
| a3_glm53flash_tp16_aclgraph_c32 | 32 / 6 | kda | 34 | 1.284 / 1.318 | 1.067 / 1.113 | -16.87% / -15.59% |
| a3_glm53flash_tp16_aclgraph_c32 | 32 / 6 | mla | 11 | 2.332 / 2.330 | 2.555 / 2.555 | +9.57% / +9.65% |
| a3_glm53flash_tp16_aclgraph_c32 | 32 / 6 | dense_layer | 3 | 0.902 / 0.886 | 0.596 / 0.596 | -33.90% / -32.72% |
| a3_glm53flash_tp16_aclgraph_c32 | 32 / 6 | moe_layer | 42 | 1.586 / 1.326 | 1.491 / 1.113 | -6.00% / -16.07% |
| a3_glm53flash_tp16_aclgraph_c64 | 64 / 6 | kda | 34 | 1.721 / 1.760 | 1.430 / 1.481 | -16.89% / -15.83% |
| a3_glm53flash_tp16_aclgraph_c64 | 64 / 6 | mla | 11 | 3.529 / 3.531 | 4.308 / 4.308 | +22.09% / +22.01% |
| a3_glm53flash_tp16_aclgraph_c64 | 64 / 6 | dense_layer | 3 | 1.308 / 1.302 | 0.906 / 0.906 | -30.69% / -30.42% |
| a3_glm53flash_tp16_aclgraph_c64 | 64 / 6 | moe_layer | 42 | 2.224 / 1.764 | 2.221 / 1.481 | -0.11% / -16.05% |
| a3_glm53flash_tp16_aclgraph_c8 | 8 / 6 | kda | 34 | 0.921 / 0.948 | 0.912 / 0.955 | -0.93% / +0.77% |
| a3_glm53flash_tp16_aclgraph_c8 | 8 / 6 | mla | 11 | 1.410 / 1.410 | 1.396 / 1.396 | -0.99% / -0.98% |
| a3_glm53flash_tp16_aclgraph_c8 | 8 / 6 | dense_layer | 3 | 0.624 / 0.618 | 0.469 / 0.469 | -24.87% / -24.16% |
| a3_glm53flash_tp16_aclgraph_c8 | 8 / 6 | moe_layer | 42 | 1.070 / 0.952 | 1.070 / 0.955 | +0.04% / +0.28% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k | 2 / 1 | mla | 40 | 0.373 / 0.353 | 0.344 / 0.333 | -7.89% / -5.71% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k | 2 / 1 | moe_layer | 40 | 0.373 / 0.353 | 0.344 / 0.333 | -7.89% / -5.71% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k | 4 / 1 | mla | 40 | 0.466 / 0.444 | 0.434 / 0.423 | -6.77% / -4.83% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k | 4 / 1 | moe_layer | 40 | 0.466 / 0.444 | 0.434 / 0.423 | -6.77% / -4.83% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k | 1 / 1 | mla | 40 | 0.331 / 0.300 | 0.314 / 0.303 | -5.19% / +0.75% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k | 1 / 1 | moe_layer | 40 | 0.331 / 0.300 | 0.314 / 0.303 | -5.19% / +0.75% |
| a3_kimi4_tp8_w4a8_c1 | 1 / 1 | kda | 3 | 0.781 / 0.789 | 0.778 / 0.882 | -0.41% / +11.72% |
| a3_kimi4_tp8_w4a8_c1 | 1 / 1 | mla | 1 | 0.836 / 0.836 | 0.821 / 0.821 | -1.84% / -1.84% |
| a3_kimi4_tp8_w4a8_c1 | 1 / 1 | dense_layer | 1 | 0.843 / 0.843 | 0.570 / 0.570 | -32.35% / -32.35% |
| a3_kimi4_tp8_w4a8_c1 | 1 / 1 | moe_layer | 3 | 0.779 / 0.789 | 0.862 / 0.882 | +10.60% / +11.72% |
| a3_kimi4_tp8_w4a8_c16 | 16 / 1 | kda | 3 | 1.118 / 1.189 | 1.103 / 1.292 | -1.34% / +8.62% |
| a3_kimi4_tp8_w4a8_c16 | 16 / 1 | mla | 1 | 1.453 / 1.453 | 1.539 / 1.539 | +5.91% / +5.91% |
| a3_kimi4_tp8_w4a8_c16 | 16 / 1 | dense_layer | 1 | 0.849 / 0.849 | 0.725 / 0.725 | -14.68% / -14.68% |
| a3_kimi4_tp8_w4a8_c16 | 16 / 1 | moe_layer | 3 | 1.319 / 1.314 | 1.374 / 1.292 | +4.18% / -1.73% |
| a3_kimi4_tp8_w4a8_c32 | 32 / 1 | kda | 3 | 1.513 / 1.796 | 1.422 / 1.785 | -6.07% / -0.63% |
| a3_kimi4_tp8_w4a8_c32 | 32 / 1 | mla | 1 | 2.173 / 2.173 | 1.772 / 1.772 | -18.44% / -18.44% |
| a3_kimi4_tp8_w4a8_c32 | 32 / 1 | dense_layer | 1 | 0.838 / 0.838 | 0.696 / 0.696 | -17.03% / -17.03% |
| a3_kimi4_tp8_w4a8_c32 | 32 / 1 | moe_layer | 3 | 1.958 / 1.906 | 1.780 / 1.785 | -9.09% / -6.39% |
| a3_kimi4_tp8_w4a8_c4 | 4 / 1 | kda | 3 | 0.836 / 0.808 | 0.773 / 0.877 | -7.57% / +8.54% |
| a3_kimi4_tp8_w4a8_c4 | 4 / 1 | mla | 1 | 0.968 / 0.968 | 0.807 / 0.807 | -16.64% / -16.64% |
| a3_kimi4_tp8_w4a8_c4 | 4 / 1 | dense_layer | 1 | 0.799 / 0.799 | 0.565 / 0.565 | -29.32% / -29.32% |
| a3_kimi4_tp8_w4a8_c4 | 4 / 1 | moe_layer | 3 | 0.892 / 0.901 | 0.853 / 0.877 | -4.36% / -2.71% |
| a3_kimi4_tp8_w4a8_c64 | 64 / 1 | kda | 3 | 2.135 / 2.740 | 1.970 / 2.595 | -7.72% / -5.26% |
| a3_kimi4_tp8_w4a8_c64 | 64 / 1 | mla | 1 | 3.209 / 3.209 | 2.744 / 2.744 | -14.50% / -14.50% |
| a3_kimi4_tp8_w4a8_c64 | 64 / 1 | dense_layer | 1 | 0.863 / 0.863 | 0.720 / 0.720 | -16.49% / -16.49% |
| a3_kimi4_tp8_w4a8_c64 | 64 / 1 | moe_layer | 3 | 2.917 / 2.803 | 2.645 / 2.595 | -9.34% / -7.41% |
| a5_kimi_tp8_e16_bf16_c16_p16k | 16 / 1 | kda | 69 | 0.385 / 0.386 | 0.413 / 0.414 | +7.26% / +7.46% |
| a5_kimi_tp8_e16_bf16_c16_p16k | 16 / 1 | mla | 24 | 0.529 / 0.522 | 0.512 / 0.511 | -3.30% / -2.11% |
| a5_kimi_tp8_e16_bf16_c16_p16k | 16 / 1 | dense_layer | 1 | 0.305 / 0.305 | 0.288 / 0.288 | -5.58% / -5.58% |
| a5_kimi_tp8_e16_bf16_c16_p16k | 16 / 1 | moe_layer | 92 | 0.423 / 0.388 | 0.440 / 0.414 | +3.91% / +6.85% |
| a5_kimi_tp8_e16_bf16_c16_p4k | 16 / 1 | kda | 69 | 0.385 / 0.385 | 0.412 / 0.414 | +7.06% / +7.46% |
| a5_kimi_tp8_e16_bf16_c16_p4k | 16 / 1 | mla | 24 | 0.434 / 0.427 | 0.414 / 0.413 | -4.65% / -3.13% |
| a5_kimi_tp8_e16_bf16_c16_p4k | 16 / 1 | dense_layer | 1 | 0.335 / 0.335 | 0.287 / 0.287 | -14.35% / -14.35% |
| a5_kimi_tp8_e16_bf16_c16_p4k | 16 / 1 | moe_layer | 92 | 0.398 / 0.388 | 0.414 / 0.414 | +3.93% / +6.81% |
| a5_kimi_tp8_e16_bf16_c1_p16k | 1 / 1 | kda | 69 | 0.320 / 0.321 | 0.344 / 0.346 | +7.66% / +7.77% |
| a5_kimi_tp8_e16_bf16_c1_p16k | 1 / 1 | mla | 24 | 0.364 / 0.358 | 0.337 / 0.336 | -7.53% / -5.94% |
| a5_kimi_tp8_e16_bf16_c1_p16k | 1 / 1 | dense_layer | 1 | 0.259 / 0.259 | 0.253 / 0.253 | -2.55% / -2.55% |
| a5_kimi_tp8_e16_bf16_c1_p16k | 1 / 1 | moe_layer | 92 | 0.332 / 0.323 | 0.343 / 0.346 | +3.40% / +7.11% |
| a5_kimi_tp8_e16_bf16_c1_p4k | 1 / 1 | kda | 69 | 0.320 / 0.321 | 0.344 / 0.346 | +7.56% / +7.75% |
| a5_kimi_tp8_e16_bf16_c1_p4k | 1 / 1 | mla | 24 | 0.356 / 0.349 | 0.329 / 0.328 | -7.59% / -5.92% |
| a5_kimi_tp8_e16_bf16_c1_p4k | 1 / 1 | dense_layer | 1 | 0.277 / 0.277 | 0.253 / 0.253 | -8.91% / -8.91% |
| a5_kimi_tp8_e16_bf16_c1_p4k | 1 / 1 | moe_layer | 92 | 0.330 / 0.323 | 0.341 / 0.346 | +3.45% / +7.03% |
| a5_kimi_tp8_e16_bf16_c2_p16k | 2 / 1 | kda | 69 | 0.352 / 0.353 | 0.366 / 0.368 | +4.04% / +4.33% |
| a5_kimi_tp8_e16_bf16_c2_p16k | 2 / 1 | mla | 24 | 0.399 / 0.392 | 0.368 / 0.367 | -7.84% / -6.32% |
| a5_kimi_tp8_e16_bf16_c2_p16k | 2 / 1 | dense_layer | 1 | 0.288 / 0.288 | 0.256 / 0.256 | -11.13% / -11.13% |
| a5_kimi_tp8_e16_bf16_c2_p16k | 2 / 1 | moe_layer | 92 | 0.365 / 0.355 | 0.368 / 0.368 | +0.79% / +3.76% |
| a5_kimi_tp8_e16_bf16_c2_p4k | 2 / 1 | kda | 69 | 0.353 / 0.353 | 0.367 / 0.368 | +3.95% / +4.26% |
| a5_kimi_tp8_e16_bf16_c2_p4k | 2 / 1 | mla | 24 | 0.384 / 0.377 | 0.353 / 0.353 | -8.06% / -6.42% |
| a5_kimi_tp8_e16_bf16_c2_p4k | 2 / 1 | dense_layer | 1 | 0.303 / 0.303 | 0.256 / 0.256 | -15.53% / -15.53% |
| a5_kimi_tp8_e16_bf16_c2_p4k | 2 / 1 | moe_layer | 92 | 0.361 / 0.355 | 0.364 / 0.368 | +0.80% / +3.72% |
| a5_kimi_tp8_e16_bf16_c32_p16k | 32 / 1 | kda | 69 | 0.414 / 0.414 | 0.390 / 0.392 | -5.70% / -5.43% |
| a5_kimi_tp8_e16_bf16_c32_p16k | 32 / 1 | mla | 24 | 0.672 / 0.665 | 0.626 / 0.626 | -6.72% / -5.77% |
| a5_kimi_tp8_e16_bf16_c32_p16k | 32 / 1 | dense_layer | 1 | 0.362 / 0.362 | 0.252 / 0.252 | -30.39% / -30.39% |
| a5_kimi_tp8_e16_bf16_c32_p16k | 32 / 1 | moe_layer | 92 | 0.482 / 0.416 | 0.453 / 0.396 | -5.87% / -4.83% |
| a5_kimi_tp8_e16_bf16_c32_p4k | 32 / 1 | kda | 69 | 0.413 / 0.414 | 0.390 / 0.392 | -5.54% / -5.31% |
| a5_kimi_tp8_e16_bf16_c32_p4k | 32 / 1 | mla | 24 | 0.480 / 0.472 | 0.418 / 0.418 | -12.83% / -11.46% |
| a5_kimi_tp8_e16_bf16_c32_p4k | 32 / 1 | dense_layer | 1 | 0.338 / 0.338 | 0.252 / 0.252 | -25.43% / -25.43% |
| a5_kimi_tp8_e16_bf16_c32_p4k | 32 / 1 | moe_layer | 92 | 0.431 / 0.415 | 0.399 / 0.396 | -7.49% / -4.64% |
| a5_kimi_tp8_e16_bf16_c4_p16k | 4 / 1 | kda | 69 | 0.359 / 0.359 | 0.373 / 0.375 | +4.06% / +4.33% |
| a5_kimi_tp8_e16_bf16_c4_p16k | 4 / 1 | mla | 24 | 0.419 / 0.412 | 0.388 / 0.387 | -7.54% / -6.14% |
| a5_kimi_tp8_e16_bf16_c4_p16k | 4 / 1 | dense_layer | 1 | 0.297 / 0.297 | 0.261 / 0.261 | -12.31% / -12.31% |
| a5_kimi_tp8_e16_bf16_c4_p16k | 4 / 1 | moe_layer | 92 | 0.375 / 0.361 | 0.378 / 0.375 | +0.82% / +3.80% |
| a5_kimi_tp8_e16_bf16_c4_p4k | 4 / 1 | kda | 69 | 0.359 / 0.360 | 0.373 / 0.375 | +4.01% / +4.20% |
| a5_kimi_tp8_e16_bf16_c4_p4k | 4 / 1 | mla | 24 | 0.393 / 0.386 | 0.363 / 0.362 | -7.80% / -6.25% |
| a5_kimi_tp8_e16_bf16_c4_p4k | 4 / 1 | dense_layer | 1 | 0.293 / 0.293 | 0.260 / 0.260 | -11.18% / -11.18% |
| a5_kimi_tp8_e16_bf16_c4_p4k | 4 / 1 | moe_layer | 92 | 0.368 / 0.361 | 0.372 / 0.375 | +0.85% / +3.79% |
| a5_kimi_tp8_e16_bf16_c8_p16k | 8 / 1 | kda | 69 | 0.364 / 0.365 | 0.393 / 0.395 | +7.93% / +8.17% |
| a5_kimi_tp8_e16_bf16_c8_p16k | 8 / 1 | mla | 24 | 0.452 / 0.445 | 0.436 / 0.435 | -3.52% / -2.26% |
| a5_kimi_tp8_e16_bf16_c8_p16k | 8 / 1 | dense_layer | 1 | 0.284 / 0.284 | 0.268 / 0.268 | -5.59% / -5.59% |
| a5_kimi_tp8_e16_bf16_c8_p16k | 8 / 1 | moe_layer | 92 | 0.388 / 0.367 | 0.405 / 0.395 | +4.56% / +7.48% |
| a5_kimi_tp8_e16_bf16_c8_p4k | 8 / 1 | kda | 69 | 0.364 / 0.365 | 0.393 / 0.395 | +7.78% / +8.23% |
| a5_kimi_tp8_e16_bf16_c8_p4k | 8 / 1 | mla | 24 | 0.403 / 0.396 | 0.388 / 0.387 | -3.77% / -2.27% |
| a5_kimi_tp8_e16_bf16_c8_p4k | 8 / 1 | dense_layer | 1 | 0.310 / 0.310 | 0.268 / 0.268 | -13.47% / -13.47% |
| a5_kimi_tp8_e16_bf16_c8_p4k | 8 / 1 | moe_layer | 92 | 0.375 / 0.367 | 0.393 / 0.395 | +4.73% / +7.45% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 | 5 / 8 | mla | 40 | 1.248 / 1.187 | 1.312 / 1.291 | +5.08% / +8.77% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 | 5 / 8 | moe_layer | 40 | 1.248 / 1.187 | 1.312 / 1.291 | +5.08% / +8.77% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 9 / 8 | mla | 40 | 1.373 / 1.307 | 1.399 / 1.374 | +1.92% / +5.12% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 9 / 8 | moe_layer | 40 | 1.373 / 1.307 | 1.399 / 1.374 | +1.92% / +5.12% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 | 2 / 8 | mla | 40 | 1.190 / 1.126 | 1.257 / 1.240 | +5.59% / +10.10% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 | 2 / 8 | moe_layer | 40 | 1.190 / 1.126 | 1.257 / 1.240 | +5.59% / +10.10% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 17 / 8 | mla | 40 | 1.544 / 1.461 | 1.589 / 1.554 | +2.94% / +6.33% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 17 / 8 | moe_layer | 40 | 1.544 / 1.461 | 1.589 / 1.554 | +2.94% / +6.33% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | 4 / 8 | mla | 40 | 1.213 / 1.160 | 1.292 / 1.273 | +6.47% / +9.75% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | 4 / 8 | moe_layer | 40 | 1.213 / 1.160 | 1.292 / 1.273 | +6.47% / +9.75% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k | 16 / 1 | mla | 40 | 0.682 / 0.655 | 0.638 / 0.626 | -6.40% / -4.38% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k | 16 / 1 | moe_layer | 40 | 0.682 / 0.655 | 0.638 / 0.626 | -6.40% / -4.38% |
| qwen35-35b-a3-tp4-c144 | 160 / 4 | gdn | 30 | 1.579 / 1.574 | 1.559 / 1.559 | -1.27% / -0.95% |
| qwen35-35b-a3-tp4-c144 | 160 / 4 | gqa | 10 | 1.435 / 1.432 | 1.417 / 1.417 | -1.28% / -1.04% |
| qwen35-35b-a3-tp4-c144 | 160 / 4 | moe_layer | 40 | 1.543 / 1.572 | 1.523 / 1.559 | -1.27% / -0.83% |
| qwen35-35b-a3-tp4-c320 | 320 / 4 | gdn | 30 | 2.609 / 2.608 | 2.414 / 2.414 | -7.48% / -7.45% |
| qwen35-35b-a3-tp4-c320 | 320 / 4 | gqa | 10 | 2.138 / 2.137 | 2.177 / 2.177 | +1.78% / +1.83% |
| qwen35-35b-a3-tp4-c320 | 320 / 4 | moe_layer | 40 | 2.491 / 2.601 | 2.355 / 2.414 | -5.49% / -7.20% |
| qwen36-a3-tp4-c64 | 64 / 4 | gdn | 48 | 1.011 / 1.011 | 1.008 / 1.008 | -0.21% / -0.20% |
| qwen36-a3-tp4-c64 | 64 / 4 | gqa | 16 | 0.873 / 0.873 | 0.826 / 0.826 | -5.39% / -5.34% |
| qwen36-a3-tp4-c64 | 64 / 4 | dense_layer | 64 | 0.976 / 1.007 | 0.963 / 1.008 | -1.37% / +0.13% |
| qwen36-a3-tp4-c128 | 128 / 4 | gdn | 48 | 1.626 / 1.625 | 1.468 / 1.468 | -9.74% / -9.68% |
| qwen36-a3-tp4-c128 | 128 / 4 | gqa | 16 | 1.216 / 1.216 | 1.180 / 1.180 | -2.92% / -2.95% |
| qwen36-a3-tp4-c128 | 128 / 4 | dense_layer | 64 | 1.524 / 1.623 | 1.396 / 1.468 | -8.38% / -9.55% |
| qwen38-a3-tp4-c64 | 64 / 4 | gdn | 48 | 1.013 / 1.013 | 1.008 / 1.008 | -0.43% / -0.42% |
| qwen38-a3-tp4-c64 | 64 / 4 | gqa | 16 | 0.874 / 0.874 | 0.826 / 0.826 | -5.45% / -5.53% |
| qwen38-a3-tp4-c64 | 64 / 4 | dense_layer | 64 | 0.978 / 1.011 | 0.963 / 1.008 | -1.55% / -0.24% |
| qwen38-a3-tp4-c128 | 128 / 4 | gdn | 48 | 1.625 / 1.626 | 1.468 / 1.468 | -9.65% / -9.70% |
| qwen38-a3-tp4-c128 | 128 / 4 | gqa | 16 | 1.213 / 1.213 | 1.180 / 1.180 | -2.73% / -2.73% |
| qwen38-a3-tp4-c128 | 128 / 4 | dense_layer | 64 | 1.522 / 1.622 | 1.396 / 1.468 | -8.27% / -9.49% |
| a5_qwen36_highconc_c4 | 4 / 4 | gdn | 48 | 0.216 / 0.177 | 0.213 / 0.213 | -1.32% / +20.19% |
| a5_qwen36_highconc_c4 | 4 / 4 | gqa | 16 | 0.183 / 0.183 | 0.202 / 0.202 | +10.07% / +10.45% |
| a5_qwen36_highconc_c4 | 4 / 4 | dense_layer | 64 | 0.208 / 0.178 | 0.210 / 0.213 | +1.19% / +19.89% |
| a5_qwen36_highconc_c40 | 40 / 4 | gdn | 48 | 0.333 / 0.308 | 0.345 / 0.345 | +3.66% / +12.24% |
| a5_qwen36_highconc_c40 | 40 / 4 | gqa | 16 | 0.290 / 0.290 | 0.242 / 0.242 | -16.61% / -16.63% |
| a5_qwen36_highconc_c40 | 40 / 4 | dense_layer | 64 | 0.322 / 0.307 | 0.319 / 0.345 | -0.89% / +12.55% |
| a5_qwen36_highconc_c128 | 128 / 4 | gdn | 48 | 0.516 / 0.500 | 0.514 / 0.514 | -0.26% / +2.78% |
| a5_qwen36_highconc_c128 | 128 / 4 | gqa | 16 | 0.488 / 0.488 | 0.452 / 0.452 | -7.42% / -7.41% |
| a5_qwen36_highconc_c128 | 128 / 4 | dense_layer | 64 | 0.509 / 0.500 | 0.499 / 0.514 | -1.98% / +2.89% |
| a5_qwen38_highconc_c4 | 4 / 4 | gdn | 48 | 0.208 / 0.208 | 0.206 / 0.206 | -0.73% / -0.70% |
| a5_qwen38_highconc_c4 | 4 / 4 | gqa | 16 | 0.188 / 0.182 | 0.203 / 0.203 | +8.07% / +11.56% |
| a5_qwen38_highconc_c4 | 4 / 4 | dense_layer | 64 | 0.203 / 0.207 | 0.205 / 0.206 | +1.31% / -0.46% |
| a5_qwen38_highconc_c32 | 32 / 4 | gdn | 48 | 0.381 / 0.382 | 0.406 / 0.406 | +6.47% / +6.35% |
| a5_qwen38_highconc_c32 | 32 / 4 | gqa | 16 | 0.278 / 0.274 | 0.192 / 0.192 | -30.74% / -29.86% |
| a5_qwen38_highconc_c32 | 32 / 4 | dense_layer | 64 | 0.355 / 0.379 | 0.352 / 0.406 | -0.79% / +7.09% |
| a5_qwen38_highconc_c128 | 128 / 4 | gdn | 48 | 0.762 / 0.762 | 0.779 / 0.779 | +2.30% / +2.29% |
| a5_qwen38_highconc_c128 | 128 / 4 | gqa | 16 | 0.567 / 0.567 | 0.533 / 0.533 | -5.88% / -5.85% |
| a5_qwen38_highconc_c128 | 128 / 4 | dense_layer | 64 | 0.713 / 0.761 | 0.718 / 0.779 | +0.67% / +2.42% |
| a3_glm53flash_heldout_c12_p4k | 1 / 6 | kda | 34 | 0.456 / 0.446 | 0.448 / 0.466 | -1.70% / +4.60% |
| a3_glm53flash_heldout_c12_p4k | 1 / 6 | mla | 11 | 0.716 / 0.714 | 0.673 / 0.673 | -5.93% / -5.78% |
| a3_glm53flash_heldout_c12_p4k | 1 / 6 | dense_layer | 3 | 0.538 / 0.244 | 0.258 / 0.258 | -51.98% / +5.61% |
| a3_glm53flash_heldout_c12_p4k | 1 / 6 | moe_layer | 42 | 0.518 / 0.453 | 0.520 / 0.466 | +0.50% / +2.88% |
| a3_glm53flash_heldout_c24_p12k | 1 / 6 | kda | 34 | 0.452 / 0.446 | 0.448 / 0.466 | -0.83% / +4.61% |
| a3_glm53flash_heldout_c24_p12k | 1 / 6 | mla | 11 | 0.745 / 0.743 | 0.675 / 0.675 | -9.46% / -9.20% |
| a3_glm53flash_heldout_c24_p12k | 1 / 6 | dense_layer | 3 | 0.487 / 0.245 | 0.258 / 0.258 | -47.00% / +5.56% |
| a3_glm53flash_heldout_c24_p12k | 1 / 6 | moe_layer | 42 | 0.526 / 0.450 | 0.521 / 0.466 | -0.98% / +3.52% |
| a5_glm53flash_heldout_c12_p4k | 2 / 4 | kda | 34 | 0.340 / 0.343 | 0.339 / 0.353 | -0.33% / +3.08% |
| a5_glm53flash_heldout_c12_p4k | 2 / 4 | mla | 11 | 0.598 / 0.595 | 0.582 / 0.582 | -2.83% / -2.25% |
| a5_glm53flash_heldout_c12_p4k | 2 / 4 | dense_layer | 3 | 0.289 / 0.237 | 0.188 / 0.188 | -35.00% / -20.84% |
| a5_glm53flash_heldout_c12_p4k | 2 / 4 | moe_layer | 42 | 0.411 / 0.346 | 0.413 / 0.353 | +0.46% / +1.97% |
| a5_glm53flash_heldout_c24_p12k | 24 / 4 | kda | 34 | 0.692 / 0.725 | 0.686 / 0.722 | -0.89% / -0.41% |
| a5_glm53flash_heldout_c24_p12k | 24 / 4 | mla | 11 | 1.406 / 1.404 | 1.376 / 1.376 | -2.13% / -2.03% |
| a5_glm53flash_heldout_c24_p12k | 24 / 4 | dense_layer | 3 | 0.345 / 0.334 | 0.312 / 0.312 | -9.57% / -6.51% |
| a5_glm53flash_heldout_c24_p12k | 24 / 4 | moe_layer | 42 | 0.904 / 0.728 | 0.893 / 0.722 | -1.15% / -0.85% |
| a5_glm53flash_heldout_c48_p4k | 48 / 4 | kda | 34 | 0.786 / 0.821 | 0.801 / 0.845 | +1.92% / +2.88% |
| a5_glm53flash_heldout_c48_p4k | 48 / 4 | mla | 11 | 1.501 / 1.498 | 1.256 / 1.256 | -16.38% / -16.17% |
| a5_glm53flash_heldout_c48_p4k | 48 / 4 | dense_layer | 3 | 0.419 / 0.411 | 0.346 / 0.346 | -17.53% / -15.96% |
| a5_glm53flash_heldout_c48_p4k | 48 / 4 | moe_layer | 42 | 0.999 / 0.823 | 0.952 / 0.845 | -4.70% / +2.61% |
| a3_glm53flash_static_on_c10_p131201 | 1 / 6 | kda | 34 | 0.449 / 0.450 | 0.448 / 0.466 | -0.30% / +3.51% |
| a3_glm53flash_static_on_c10_p131201 | 1 / 6 | mla | 11 | 0.662 / 0.661 | 0.672 / 0.672 | +1.58% / +1.77% |
| a3_glm53flash_static_on_c10_p131201 | 1 / 6 | dense_layer | 3 | 0.427 / 0.248 | 0.258 / 0.258 | -39.61% / +4.21% |
| a3_glm53flash_static_on_c10_p131201 | 1 / 6 | moe_layer | 42 | 0.506 / 0.455 | 0.520 / 0.466 | +2.72% / +2.56% |
| a3_glm53flash_static_on_c10_p131201 | 4 / 6 | kda | 34 | 0.577 / 0.571 | 0.606 / 0.639 | +5.08% / +11.90% |
| a3_glm53flash_static_on_c10_p131201 | 4 / 6 | mla | 11 | 0.780 / 0.771 | 0.942 / 0.942 | +20.78% / +22.18% |
| a3_glm53flash_static_on_c10_p131201 | 4 / 6 | dense_layer | 3 | 0.603 / 0.295 | 0.271 / 0.271 | -55.09% / -8.33% |
| a3_glm53flash_static_on_c10_p131201 | 4 / 6 | moe_layer | 42 | 0.628 / 0.577 | 0.718 / 0.639 | +14.30% / +10.66% |
| a3_glm53flash_static_on_c10_p131201 | 8 / 6 | kda | 34 | 0.592 / 0.583 | 0.562 / 0.588 | -4.93% / +0.72% |
| a3_glm53flash_static_on_c10_p131201 | 8 / 6 | mla | 11 | 1.038 / 1.036 | 1.070 / 1.070 | +3.09% / +3.27% |
| a3_glm53flash_static_on_c10_p131201 | 8 / 6 | dense_layer | 3 | 0.625 / 0.345 | 0.301 / 0.301 | -51.81% / -12.54% |
| a3_glm53flash_static_on_c10_p131201 | 8 / 6 | moe_layer | 42 | 0.706 / 0.601 | 0.714 / 0.588 | +1.12% / -2.21% |
| a3_glm53flash_static_on_c10_p131201 | 2 / 6 | kda | 34 | 0.530 / 0.499 | 0.507 / 0.531 | -4.44% / +6.36% |
| a3_glm53flash_static_on_c10_p131201 | 2 / 6 | mla | 11 | 0.693 / 0.688 | 0.743 / 0.743 | +7.16% / +7.97% |
| a3_glm53flash_static_on_c10_p131201 | 2 / 6 | dense_layer | 3 | 0.883 / 0.264 | 0.261 / 0.261 | -70.47% / -1.05% |
| a3_glm53flash_static_on_c10_p131201 | 2 / 6 | moe_layer | 42 | 0.548 / 0.504 | 0.586 / 0.531 | +7.01% / +5.34% |
| a3_glm53flash_static_on_c10_p131201 | 3 / 6 | kda | 34 | 0.677 / 0.549 | 0.556 / 0.584 | -17.88% / +6.41% |
| a3_glm53flash_static_on_c10_p131201 | 3 / 6 | mla | 11 | 0.758 / 0.759 | 0.841 / 0.841 | +10.93% / +10.89% |
| a3_glm53flash_static_on_c10_p131201 | 3 / 6 | dense_layer | 3 | 1.895 / 0.289 | 0.265 / 0.265 | -86.00% / -8.12% |
| a3_glm53flash_static_on_c10_p131201 | 3 / 6 | moe_layer | 42 | 0.611 / 0.565 | 0.652 / 0.584 | +6.56% / +3.38% |
| a3_glm53flash_static_on_c10_p131201 | 7 / 6 | kda | 34 | 0.704 / 0.638 | 0.550 / 0.575 | -21.85% / -9.93% |
| a3_glm53flash_static_on_c10_p131201 | 7 / 6 | mla | 11 | 1.069 / 1.060 | 1.012 / 1.012 | -5.30% / -4.53% |
| a3_glm53flash_static_on_c10_p131201 | 7 / 6 | dense_layer | 3 | 1.405 / 0.339 | 0.296 / 0.296 | -78.93% / -12.65% |
| a3_glm53flash_static_on_c10_p131201 | 7 / 6 | moe_layer | 42 | 0.750 / 0.648 | 0.689 / 0.575 | -8.03% / -11.31% |
| a3-qwen35-tp4-longctx-p-126976-c1 | 1 / 2 | gdn | 30 | 0.367 / 0.367 | 0.371 / 0.371 | +1.16% / +1.08% |
| a3-qwen35-tp4-longctx-p-126976-c1 | 1 / 2 | gqa | 10 | 0.499 / 0.500 | 0.469 / 0.469 | -6.10% / -6.30% |
| a3-qwen35-tp4-longctx-p-126976-c1 | 1 / 2 | moe_layer | 40 | 0.400 / 0.370 | 0.396 / 0.371 | -1.11% / +0.28% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 / 2 | gdn | 30 | 0.410 / 0.409 | 0.401 / 0.401 | -2.31% / -2.05% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 / 2 | gqa | 10 | 0.813 / 0.814 | 0.813 / 0.813 | +0.03% / -0.17% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 / 2 | moe_layer | 40 | 0.511 / 0.414 | 0.504 / 0.401 | -1.38% / -3.20% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 / 2 | gdn | 30 | 0.369 / 0.368 | 0.371 / 0.371 | +0.63% / +1.03% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 / 2 | gqa | 10 | 0.499 / 0.500 | 0.469 / 0.469 | -6.02% / -6.31% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 / 2 | moe_layer | 40 | 0.401 / 0.373 | 0.396 / 0.371 | -1.43% / -0.52% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 / 2 | gdn | 30 | 0.380 / 0.380 | 0.381 / 0.381 | +0.25% / +0.38% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 / 2 | gqa | 10 | 0.625 / 0.626 | 0.588 / 0.588 | -5.91% / -6.10% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 / 2 | moe_layer | 40 | 0.441 / 0.385 | 0.433 / 0.381 | -1.93% / -0.95% |
| a3-qwen35-tp4-longctx-p-65536-c1 | 1 / 2 | gdn | 30 | 0.368 / 0.366 | 0.371 / 0.371 | +0.94% / +1.45% |
| a3-qwen35-tp4-longctx-p-65536-c1 | 1 / 2 | gqa | 10 | 0.444 / 0.444 | 0.416 / 0.416 | -6.45% / -6.48% |
| a3-qwen35-tp4-longctx-p-65536-c1 | 1 / 2 | moe_layer | 40 | 0.387 / 0.368 | 0.382 / 0.371 | -1.18% / +0.93% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 / 2 | gdn | 30 | 0.385 / 0.381 | 0.381 / 0.381 | -1.07% / +0.10% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 / 2 | gqa | 10 | 0.516 / 0.517 | 0.483 / 0.483 | -6.42% / -6.60% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 / 2 | moe_layer | 40 | 0.418 / 0.385 | 0.406 / 0.381 | -2.72% / -1.05% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 / 2 | gdn | 30 | 0.369 / 0.365 | 0.371 / 0.371 | +0.59% / +1.78% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 / 2 | gqa | 10 | 0.446 / 0.447 | 0.416 / 0.416 | -6.83% / -6.97% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 / 2 | moe_layer | 40 | 0.388 / 0.367 | 0.382 / 0.371 | -1.54% / +1.29% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 / 2 | gdn | 30 | 0.411 / 0.410 | 0.401 / 0.401 | -2.56% / -2.24% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 / 2 | gqa | 10 | 0.653 / 0.652 | 0.624 / 0.624 | -4.45% / -4.34% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 / 2 | moe_layer | 40 | 0.471 / 0.416 | 0.456 / 0.401 | -3.21% / -3.65% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 / 2 | gdn | 30 | 0.371 / 0.366 | 0.371 / 0.371 | +0.12% / +1.57% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 / 2 | gqa | 10 | 0.448 / 0.447 | 0.416 / 0.416 | -7.26% / -7.10% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 / 2 | moe_layer | 40 | 0.390 / 0.369 | 0.382 / 0.371 | -2.00% / +0.57% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 / 2 | gdn | 30 | 0.386 / 0.381 | 0.381 / 0.381 | -1.36% / +0.12% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 / 2 | gqa | 10 | 0.517 / 0.517 | 0.483 / 0.483 | -6.61% / -6.73% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 / 2 | moe_layer | 40 | 0.419 / 0.384 | 0.406 / 0.381 | -2.98% / -0.86% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 / 2 | gdn | 30 | 0.430 / 0.429 | 0.439 / 0.439 | +2.25% / +2.48% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 / 2 | gqa | 10 | 0.849 / 0.851 | 0.872 / 0.872 | +2.72% / +2.40% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 / 2 | moe_layer | 40 | 0.534 / 0.431 | 0.548 / 0.439 | +2.44% / +1.93% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 / 2 | gdn | 30 | 0.416 / 0.408 | 0.401 / 0.401 | -3.83% / -1.90% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 / 2 | gqa | 10 | 0.636 / 0.636 | 0.624 / 0.624 | -1.99% / -1.92% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 / 2 | moe_layer | 40 | 0.471 / 0.416 | 0.456 / 0.401 | -3.21% / -3.80% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 / 2 | gdn | 30 | 0.390 / 0.382 | 0.381 / 0.381 | -2.20% / -0.28% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 / 2 | gqa | 10 | 0.517 / 0.518 | 0.483 / 0.483 | -6.59% / -6.78% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 / 2 | moe_layer | 40 | 0.421 / 0.387 | 0.406 / 0.381 | -3.54% / -1.43% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 / 2 | gdn | 30 | 0.367 / 0.366 | 0.371 / 0.371 | +1.27% / +1.51% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 / 2 | gqa | 10 | 0.445 / 0.446 | 0.416 / 0.416 | -6.63% / -6.76% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 / 2 | moe_layer | 40 | 0.386 / 0.367 | 0.382 / 0.371 | -1.00% / +1.20% |
| a3-qwen36-tp4-longctx-p-126976-c1 | 1 / 4 | gdn | 48 | 0.264 / 0.263 | 0.265 / 0.265 | +0.27% / +0.90% |
| a3-qwen36-tp4-longctx-p-126976-c1 | 1 / 4 | gqa | 16 | 0.387 / 0.387 | 0.379 / 0.379 | -2.09% / -2.26% |
| a3-qwen36-tp4-longctx-p-126976-c1 | 1 / 4 | dense_layer | 64 | 0.295 / 0.265 | 0.294 / 0.265 | -0.50% / +0.05% |
| a3-qwen36-tp4-longctx-p-126976-c4 | 4 / 4 | gdn | 48 | 0.313 / 0.312 | 0.310 / 0.310 | -1.06% / -0.78% |
| a3-qwen36-tp4-longctx-p-126976-c4 | 4 / 4 | gqa | 16 | 0.805 / 0.804 | 0.783 / 0.783 | -2.72% / -2.61% |
| a3-qwen36-tp4-longctx-p-126976-c4 | 4 / 4 | dense_layer | 64 | 0.436 / 0.315 | 0.428 / 0.310 | -1.82% / -1.60% |
| a3-qwen36-tp4-longctx-p-65536-c1 | 1 / 4 | gdn | 48 | 0.264 / 0.261 | 0.265 / 0.265 | +0.55% / +1.78% |
| a3-qwen36-tp4-longctx-p-65536-c1 | 1 / 4 | gqa | 16 | 0.334 / 0.330 | 0.318 / 0.318 | -4.99% / -3.73% |
| a3-qwen36-tp4-longctx-p-65536-c1 | 1 / 4 | dense_layer | 64 | 0.281 / 0.264 | 0.278 / 0.265 | -1.10% / +0.61% |
| a3-qwen36-tp4-longctx-p-65536-c4 | 4 / 4 | gdn | 48 | 0.315 / 0.312 | 0.310 / 0.310 | -1.70% / -0.68% |
| a3-qwen36-tp4-longctx-p-65536-c4 | 4 / 4 | gqa | 16 | 0.607 / 0.607 | 0.584 / 0.584 | -3.67% / -3.75% |
| a3-qwen36-tp4-longctx-p-65536-c4 | 4 / 4 | dense_layer | 64 | 0.388 / 0.315 | 0.378 / 0.310 | -2.47% / -1.52% |
| a5-qwen35-tp4-longctx-p126976-c1-hold | 1 / 4 | gdn | 30 | 0.223 / 0.222 | 0.241 / 0.241 | +8.07% / +8.56% |
| a5-qwen35-tp4-longctx-p126976-c1-hold | 1 / 4 | gqa | 10 | 1.148 / 1.148 | 1.171 / 1.171 | +2.04% / +2.02% |
| a5-qwen35-tp4-longctx-p126976-c1-hold | 1 / 4 | moe_layer | 40 | 0.454 / 0.223 | 0.474 / 0.241 | +4.26% / +7.96% |
| a5-qwen35-tp4-longctx-p126976-c1-o32 | 1 / 4 | gdn | 30 | 0.263 / 0.220 | 0.241 / 0.241 | -8.25% / +9.76% |
| a5-qwen35-tp4-longctx-p126976-c1-o32 | 1 / 4 | gqa | 10 | 1.143 / 1.143 | 1.171 / 1.171 | +2.45% / +2.46% |
| a5-qwen35-tp4-longctx-p126976-c1-o32 | 1 / 4 | moe_layer | 40 | 0.483 / 0.221 | 0.474 / 0.241 | -1.92% / +8.92% |
| a5-qwen35-tp4-longctx-p126976-c4-hold | 4 / 4 | gdn | 30 | 0.276 / 0.278 | 0.273 / 0.273 | -0.96% / -1.60% |
| a5-qwen35-tp4-longctx-p126976-c4-hold | 4 / 4 | gqa | 10 | 1.212 / 1.214 | 1.204 / 1.203 | -0.70% / -0.91% |
| a5-qwen35-tp4-longctx-p126976-c4-hold | 4 / 4 | moe_layer | 40 | 0.510 / 0.280 | 0.506 / 0.273 | -0.81% / -2.44% |
| a5-qwen35-tp4-longctx-p126976-c4-o32 | 1 / 4 | gdn | 30 | 0.222 / 0.221 | 0.241 / 0.241 | +8.74% / +9.30% |
| a5-qwen35-tp4-longctx-p126976-c4-o32 | 1 / 4 | gqa | 10 | 1.145 / 1.145 | 1.171 / 1.171 | +2.29% / +2.25% |
| a5-qwen35-tp4-longctx-p126976-c4-o32 | 1 / 4 | moe_layer | 40 | 0.453 / 0.223 | 0.474 / 0.241 | +4.66% / +8.22% |
| a5-qwen35-tp4-longctx-p65536-c1-hold | 1 / 4 | gdn | 30 | 0.222 / 0.221 | 0.241 / 0.241 | +8.58% / +9.23% |
| a5-qwen35-tp4-longctx-p65536-c1-hold | 1 / 4 | gqa | 10 | 0.698 / 0.698 | 0.694 / 0.694 | -0.56% / -0.59% |
| a5-qwen35-tp4-longctx-p65536-c1-hold | 1 / 4 | moe_layer | 40 | 0.341 / 0.222 | 0.354 / 0.241 | +3.90% / +8.72% |
| a5-qwen35-tp4-longctx-p65536-c1-o32 | 1 / 4 | gdn | 30 | 0.229 / 0.221 | 0.241 / 0.241 | +5.34% / +9.06% |
| a5-qwen35-tp4-longctx-p65536-c1-o32 | 1 / 4 | gqa | 10 | 0.699 / 0.699 | 0.694 / 0.694 | -0.72% / -0.75% |
| a5-qwen35-tp4-longctx-p65536-c1-o32 | 1 / 4 | moe_layer | 40 | 0.347 / 0.223 | 0.354 / 0.241 | +2.28% / +8.02% |
| a5-qwen35-tp4-longctx-p65536-c4-hold | 4 / 4 | gdn | 30 | 0.273 / 0.274 | 0.273 / 0.273 | -0.11% / -0.23% |
| a5-qwen35-tp4-longctx-p65536-c4-hold | 4 / 4 | gqa | 10 | 0.757 / 0.759 | 0.727 / 0.727 | -3.97% / -4.20% |
| a5-qwen35-tp4-longctx-p65536-c4-hold | 4 / 4 | moe_layer | 40 | 0.394 / 0.278 | 0.386 / 0.273 | -1.96% / -1.61% |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 1 / 4 | gdn | 30 | 0.249 / 0.221 | 0.241 / 0.241 | -3.13% / +9.00% |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 1 / 4 | gqa | 10 | 0.698 / 0.697 | 0.694 / 0.694 | -0.47% / -0.38% |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 1 / 4 | moe_layer | 40 | 0.361 / 0.222 | 0.354 / 0.241 | -1.84% / +8.56% |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 2 / 4 | gdn | 30 | 0.335 / 0.243 | 0.312 / 0.312 | -6.83% / +28.79% |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 2 / 4 | gqa | 10 | 0.718 / 0.718 | 0.705 / 0.705 | -1.77% / -1.81% |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 2 / 4 | moe_layer | 40 | 0.431 / 0.244 | 0.411 / 0.312 | -4.72% / +28.02% |
| a5-qwen38-tp1-longctx-p126976-c4 | 1 / 4 | gdn | 48 | 0.273 / 0.272 | 0.281 / 0.281 | +2.98% / +3.08% |
| a5-qwen38-tp1-longctx-p126976-c4 | 1 / 4 | gqa | 16 | 1.195 / 1.195 | 1.143 / 1.143 | -4.34% / -4.33% |
| a5-qwen38-tp1-longctx-p126976-c4 | 1 / 4 | dense_layer | 64 | 0.503 / 0.273 | 0.496 / 0.281 | -1.36% / +2.86% |
| a5-qwen38-tp1-longctx-p126976-c4 | 2 / 4 | gdn | 48 | 0.299 / 0.299 | 0.305 / 0.305 | +1.81% / +1.84% |
| a5-qwen38-tp1-longctx-p126976-c4 | 2 / 4 | gqa | 16 | 1.321 / 1.321 | 1.211 / 1.211 | -8.32% / -8.34% |
| a5-qwen38-tp1-longctx-p126976-c4 | 2 / 4 | dense_layer | 64 | 0.555 / 0.300 | 0.531 / 0.305 | -4.22% / +1.55% |
| a5-qwen38-tp1-longctx-p65536-c4 | 1 / 4 | gdn | 48 | 0.273 / 0.273 | 0.281 / 0.281 | +2.92% / +3.01% |
| a5-qwen38-tp1-longctx-p65536-c4 | 1 / 4 | gqa | 16 | 0.711 / 0.711 | 0.667 / 0.667 | -6.28% / -6.27% |
| a5-qwen38-tp1-longctx-p65536-c4 | 1 / 4 | dense_layer | 64 | 0.382 / 0.274 | 0.377 / 0.281 | -1.35% / +2.62% |
| a5-qwen38-tp1-longctx-p65536-c4 | 2 / 4 | gdn | 48 | 0.299 / 0.299 | 0.305 / 0.305 | +1.89% / +1.79% |
| a5-qwen38-tp1-longctx-p65536-c4 | 2 / 4 | gqa | 16 | 0.780 / 0.780 | 0.734 / 0.734 | -5.93% / -5.92% |
| a5-qwen38-tp1-longctx-p65536-c4 | 2 / 4 | dense_layer | 64 | 0.419 / 0.300 | 0.412 / 0.305 | -1.75% / +1.54% |
| a5-qwen38-tp1-longctx-p65536-c4 | 4 / 4 | gdn | 48 | 0.337 / 0.337 | 0.352 / 0.352 | +4.61% / +4.68% |
| a5-qwen38-tp1-longctx-p65536-c4 | 4 / 4 | gqa | 16 | 0.805 / 0.806 | 0.744 / 0.744 | -7.65% / -7.67% |
| a5-qwen38-tp1-longctx-p65536-c4 | 4 / 4 | dense_layer | 64 | 0.454 / 0.338 | 0.450 / 0.352 | -0.83% / +4.32% |
| a5-qwen36-tp8-longctx-p126976-c1-hold | 1 / 4 | gdn | 48 | 0.169 / 0.158 | 0.175 / 0.175 | +3.31% / +10.66% |
| a5-qwen36-tp8-longctx-p126976-c1-hold | 1 / 4 | gqa | 16 | 1.069 / 1.069 | 1.112 / 1.112 | +4.00% / +4.04% |
| a5-qwen36-tp8-longctx-p126976-c1-hold | 1 / 4 | dense_layer | 64 | 0.394 / 0.161 | 0.409 / 0.175 | +3.78% / +8.25% |
| a5-qwen36-tp8-longctx-p126976-c4-hold | 4 / 4 | gdn | 48 | 0.188 / 0.180 | 0.187 / 0.187 | -0.91% / +3.90% |
| a5-qwen36-tp8-longctx-p126976-c4-hold | 4 / 4 | gqa | 16 | 1.097 / 1.097 | 1.115 / 1.115 | +1.66% / +1.67% |
| a5-qwen36-tp8-longctx-p126976-c4-hold | 4 / 4 | dense_layer | 64 | 0.415 / 0.183 | 0.419 / 0.187 | +0.78% / +1.93% |
| a5-qwen36-tp8-longctx-p65536-c1-hold | 1 / 4 | gdn | 48 | 0.160 / 0.158 | 0.175 / 0.175 | +8.85% / +10.64% |
| a5-qwen36-tp8-longctx-p65536-c1-hold | 1 / 4 | gqa | 16 | 0.628 / 0.622 | 0.635 / 0.635 | +1.12% / +2.16% |
| a5-qwen36-tp8-longctx-p65536-c1-hold | 1 / 4 | dense_layer | 64 | 0.277 / 0.161 | 0.290 / 0.175 | +4.47% / +8.57% |
| a5-qwen36-tp8-longctx-p65536-c4-hold | 4 / 4 | gdn | 48 | 0.183 / 0.180 | 0.187 / 0.187 | +2.16% / +3.71% |
| a5-qwen36-tp8-longctx-p65536-c4-hold | 4 / 4 | gqa | 16 | 0.644 / 0.644 | 0.638 / 0.638 | -0.95% / -0.95% |
| a5-qwen36-tp8-longctx-p65536-c4-hold | 4 / 4 | dense_layer | 64 | 0.298 / 0.183 | 0.300 / 0.187 | +0.48% / +1.85% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | 1 / 1 | kda | 3 | 0.780 / 0.795 | 0.802 / 0.943 | +2.77% / +18.57% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | 1 / 1 | mla | 1 | 1.055 / 1.055 | 1.141 / 1.141 | +8.14% / +8.14% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | 1 / 1 | dense_layer | 1 | 0.813 / 0.813 | 0.520 / 0.520 | -36.00% / -36.00% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | 1 / 1 | moe_layer | 3 | 0.861 / 0.795 | 1.009 / 0.943 | +17.17% / +18.57% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | 12 / 1 | kda | 3 | 0.994 / 1.047 | 1.024 / 1.262 | +2.97% / +20.57% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | 12 / 1 | mla | 1 | 3.938 / 3.938 | 3.568 / 3.568 | -9.40% / -9.40% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | 12 / 1 | dense_layer | 1 | 0.789 / 0.789 | 0.548 / 0.548 | -30.57% / -30.57% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | 12 / 1 | moe_layer | 3 | 2.044 / 1.147 | 2.031 / 1.262 | -0.66% / +9.98% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | 16 / 1 | kda | 3 | 1.103 / 1.204 | 1.034 / 1.272 | -6.27% / +5.69% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | 16 / 1 | mla | 1 | 4.976 / 4.976 | 4.466 / 4.466 | -10.25% / -10.25% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | 16 / 1 | dense_layer | 1 | 0.774 / 0.774 | 0.558 / 0.558 | -27.84% / -27.84% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | 16 / 1 | moe_layer | 3 | 2.504 / 1.333 | 2.337 / 1.272 | -6.68% / -4.55% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | 2 / 1 | kda | 3 | 0.763 / 0.744 | 0.805 / 0.946 | +5.55% / +27.10% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | 2 / 1 | mla | 1 | 1.304 / 1.304 | 1.348 / 1.348 | +3.41% / +3.41% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | 2 / 1 | dense_layer | 1 | 0.698 / 0.698 | 0.524 / 0.524 | -25.01% / -25.01% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | 2 / 1 | moe_layer | 3 | 0.965 / 0.846 | 1.080 / 0.946 | +11.96% / +11.81% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | 24 / 1 | kda | 3 | 1.293 / 1.517 | 1.246 / 1.582 | -3.60% / +4.29% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | 24 / 1 | mla | 1 | 7.084 / 7.084 | 6.421 / 6.421 | -9.35% / -9.35% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | 24 / 1 | dense_layer | 1 | 0.754 / 0.754 | 0.574 / 0.574 | -23.90% / -23.90% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | 24 / 1 | moe_layer | 3 | 3.402 / 1.607 | 3.195 / 1.582 | -6.09% / -1.52% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | 32 / 1 | kda | 3 | 1.496 / 1.813 | 1.473 / 1.905 | -1.60% / +5.06% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | 32 / 1 | mla | 1 | 9.235 / 9.235 | 8.391 / 8.391 | -9.14% / -9.14% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | 32 / 1 | dense_layer | 1 | 0.790 / 0.790 | 0.607 / 0.607 | -23.15% / -23.15% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | 32 / 1 | moe_layer | 3 | 4.311 / 1.886 | 4.067 / 1.905 | -5.67% / +1.03% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | 4 / 1 | kda | 3 | 0.826 / 0.835 | 0.812 / 0.953 | -1.60% / +14.10% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | 4 / 1 | mla | 1 | 1.925 / 1.925 | 1.761 / 1.761 | -8.53% / -8.53% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | 4 / 1 | dense_layer | 1 | 0.719 / 0.719 | 0.531 / 0.531 | -26.14% / -26.14% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | 4 / 1 | moe_layer | 3 | 1.228 / 0.923 | 1.223 / 0.953 | -0.44% / +3.29% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | 48 / 1 | kda | 3 | 1.907 / 2.420 | 1.937 / 2.568 | +1.54% / +6.14% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | 48 / 1 | mla | 1 | 13.351 / 13.351 | 12.239 / 12.239 | -8.33% / -8.33% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | 48 / 1 | dense_layer | 1 | 0.848 / 0.848 | 0.674 / 0.674 | -20.59% / -20.59% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | 48 / 1 | moe_layer | 3 | 6.075 / 2.454 | 5.792 / 2.568 | -4.66% / +4.66% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | 6 / 1 | kda | 3 | 0.861 / 0.829 | 0.819 / 0.960 | -4.85% / +15.81% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | 6 / 1 | mla | 1 | 2.213 / 2.213 | 2.185 / 2.185 | -1.29% / -1.29% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | 6 / 1 | dense_layer | 1 | 0.805 / 0.805 | 0.537 / 0.537 | -33.29% / -33.29% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | 6 / 1 | moe_layer | 3 | 1.330 / 0.948 | 1.368 / 0.960 | +2.87% / +1.24% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | 64 / 1 | kda | 3 | 2.136 / 2.758 | 2.229 / 2.974 | +4.35% / +7.84% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | 64 / 1 | mla | 1 | 17.286 / 17.286 | 15.903 / 15.903 | -8.00% / -8.00% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | 64 / 1 | dense_layer | 1 | 0.871 / 0.871 | 0.739 / 0.739 | -15.13% / -15.13% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | 64 / 1 | moe_layer | 3 | 7.608 / 2.779 | 7.284 / 2.974 | -4.26% / +6.99% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | 8 / 1 | kda | 3 | 0.861 / 0.895 | 0.824 / 0.965 | -4.33% / +7.84% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | 8 / 1 | mla | 1 | 2.883 / 2.883 | 2.468 / 2.468 | -14.37% / -14.37% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | 8 / 1 | dense_layer | 1 | 0.696 / 0.696 | 0.543 / 0.543 | -22.00% / -22.00% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | 8 / 1 | moe_layer | 3 | 1.590 / 0.994 | 1.466 / 0.965 | -7.82% / -2.92% |
| a3-kimi4-tp8-longctx-decode-c12-p16k | 12 / 1 | kda | 3 | 0.990 / 1.054 | 1.024 / 1.262 | +3.41% / +19.74% |
| a3-kimi4-tp8-longctx-decode-c12-p16k | 12 / 1 | mla | 1 | 1.464 / 1.464 | 1.535 / 1.535 | +4.82% / +4.82% |
| a3-kimi4-tp8-longctx-decode-c12-p16k | 12 / 1 | dense_layer | 1 | 0.773 / 0.773 | 0.548 / 0.548 | -29.13% / -29.13% |
| a3-kimi4-tp8-longctx-decode-c12-p16k | 12 / 1 | moe_layer | 3 | 1.220 / 1.143 | 1.353 / 1.262 | +10.84% / +10.35% |
| a3-kimi4-tp8-longctx-decode-c12-p32k | 12 / 1 | kda | 3 | 0.961 / 1.056 | 1.024 / 1.262 | +6.49% / +19.46% |
| a3-kimi4-tp8-longctx-decode-c12-p32k | 12 / 1 | mla | 1 | 1.737 / 1.737 | 1.863 / 1.863 | +7.28% / +7.28% |
| a3-kimi4-tp8-longctx-decode-c12-p32k | 12 / 1 | dense_layer | 1 | 0.679 / 0.679 | 0.548 / 0.548 | -19.34% / -19.34% |
| a3-kimi4-tp8-longctx-decode-c12-p32k | 12 / 1 | moe_layer | 3 | 1.314 / 1.149 | 1.462 / 1.262 | +11.29% / +9.84% |
| a3-kimi4-tp8-longctx-decode-c12-p4k | 12 / 1 | kda | 3 | 0.985 / 1.050 | 1.024 / 1.262 | +3.90% / +20.14% |
| a3-kimi4-tp8-longctx-decode-c12-p4k | 12 / 1 | mla | 1 | 1.273 / 1.273 | 1.285 / 1.285 | +0.97% / +0.97% |
| a3-kimi4-tp8-longctx-decode-c12-p4k | 12 / 1 | dense_layer | 1 | 0.763 / 0.763 | 0.548 / 0.548 | -28.22% / -28.22% |
| a3-kimi4-tp8-longctx-decode-c12-p4k | 12 / 1 | moe_layer | 3 | 1.155 / 1.143 | 1.270 / 1.262 | +9.90% / +10.42% |
| a3-kimi4-tp8-longctx-decode-c12-p8k | 12 / 1 | kda | 3 | 0.974 / 1.052 | 1.024 / 1.262 | +5.11% / +19.93% |
| a3-kimi4-tp8-longctx-decode-c12-p8k | 12 / 1 | mla | 1 | 1.326 / 1.326 | 1.370 / 1.370 | +3.29% / +3.29% |
| a3-kimi4-tp8-longctx-decode-c12-p8k | 12 / 1 | dense_layer | 1 | 0.726 / 0.726 | 0.548 / 0.548 | -24.55% / -24.55% |
| a3-kimi4-tp8-longctx-decode-c12-p8k | 12 / 1 | moe_layer | 3 | 1.174 / 1.144 | 1.298 / 1.262 | +10.54% / +10.32% |
| a3-kimi4-tp8-longctx-decode-c24-p16k | 24 / 1 | kda | 3 | 1.320 / 1.515 | 1.246 / 1.582 | -5.60% / +4.45% |
| a3-kimi4-tp8-longctx-decode-c24-p16k | 24 / 1 | mla | 1 | 2.136 / 2.136 | 2.139 / 2.139 | +0.14% / +0.14% |
| a3-kimi4-tp8-longctx-decode-c24-p16k | 24 / 1 | dense_layer | 1 | 0.841 / 0.841 | 0.574 / 0.574 | -31.77% / -31.77% |
| a3-kimi4-tp8-longctx-decode-c24-p16k | 24 / 1 | moe_layer | 3 | 1.752 / 1.604 | 1.768 / 1.582 | +0.93% / -1.36% |
| a3-kimi4-tp8-longctx-decode-c24-p32k | 24 / 1 | kda | 3 | 1.277 / 1.521 | 1.246 / 1.582 | -2.39% / +4.00% |
| a3-kimi4-tp8-longctx-decode-c24-p32k | 24 / 1 | mla | 1 | 2.606 / 2.606 | 2.790 / 2.790 | +7.06% / +7.06% |
| a3-kimi4-tp8-longctx-decode-c24-p32k | 24 / 1 | dense_layer | 1 | 0.722 / 0.722 | 0.574 / 0.574 | -20.53% / -20.53% |
| a3-kimi4-tp8-longctx-decode-c24-p32k | 24 / 1 | moe_layer | 3 | 1.905 / 1.586 | 1.985 / 1.582 | +4.21% / -0.25% |
| a3-kimi4-tp8-longctx-decode-c24-p4k | 24 / 1 | kda | 3 | 1.290 / 1.510 | 1.246 / 1.582 | -3.39% / +4.78% |
| a3-kimi4-tp8-longctx-decode-c24-p4k | 24 / 1 | mla | 1 | 1.771 / 1.771 | 1.653 / 1.653 | -6.64% / -6.64% |
| a3-kimi4-tp8-longctx-decode-c24-p4k | 24 / 1 | dense_layer | 1 | 0.743 / 0.743 | 0.574 / 0.574 | -22.81% / -22.81% |
| a3-kimi4-tp8-longctx-decode-c24-p4k | 24 / 1 | moe_layer | 3 | 1.632 / 1.616 | 1.606 / 1.582 | -1.62% / -2.09% |
| a3-kimi4-tp8-longctx-decode-c24-p8k | 24 / 1 | kda | 3 | 1.316 / 1.512 | 1.246 / 1.582 | -5.34% / +4.66% |
| a3-kimi4-tp8-longctx-decode-c24-p8k | 24 / 1 | mla | 1 | 1.880 / 1.880 | 1.820 / 1.820 | -3.19% / -3.19% |
| a3-kimi4-tp8-longctx-decode-c24-p8k | 24 / 1 | dense_layer | 1 | 0.835 / 0.835 | 0.574 / 0.574 | -31.28% / -31.28% |
| a3-kimi4-tp8-longctx-decode-c24-p8k | 24 / 1 | moe_layer | 3 | 1.664 / 1.602 | 1.661 / 1.582 | -0.19% / -1.25% |
| a3-kimi4-tp8-longctx-decode-c2-p4k | 2 / 1 | kda | 3 | 0.791 / 0.774 | 0.805 / 0.946 | +1.84% / +22.21% |
| a3-kimi4-tp8-longctx-decode-c2-p4k | 2 / 1 | mla | 1 | 0.912 / 0.912 | 0.935 / 0.935 | +2.52% / +2.52% |
| a3-kimi4-tp8-longctx-decode-c2-p4k | 2 / 1 | dense_layer | 1 | 0.774 / 0.774 | 0.524 / 0.524 | -32.34% / -32.34% |
| a3-kimi4-tp8-longctx-decode-c2-p4k | 2 / 1 | moe_layer | 3 | 0.837 / 0.838 | 0.942 / 0.946 | +12.63% / +12.87% |
| a3-kimi4-tp8-longctx-decode-c48-p4k | 48 / 1 | kda | 3 | 1.913 / 2.423 | 1.937 / 2.568 | +1.25% / +5.97% |
| a3-kimi4-tp8-longctx-decode-c48-p4k | 48 / 1 | mla | 1 | 2.733 / 2.733 | 2.738 / 2.738 | +0.19% / +0.19% |
| a3-kimi4-tp8-longctx-decode-c48-p4k | 48 / 1 | dense_layer | 1 | 0.846 / 0.846 | 0.674 / 0.674 | -20.42% / -20.42% |
| a3-kimi4-tp8-longctx-decode-c48-p4k | 48 / 1 | moe_layer | 3 | 2.542 / 2.468 | 2.625 / 2.568 | +3.27% / +4.04% |
| a3-kimi4-tp8-longctx-decode-c6-p4k | 6 / 1 | kda | 3 | 0.887 / 0.857 | 0.819 / 0.960 | -7.69% / +11.98% |
| a3-kimi4-tp8-longctx-decode-c6-p4k | 6 / 1 | mla | 1 | 1.039 / 1.039 | 0.964 / 0.964 | -7.26% / -7.26% |
| a3-kimi4-tp8-longctx-decode-c6-p4k | 6 / 1 | dense_layer | 1 | 0.857 / 0.857 | 0.537 / 0.537 | -37.31% / -37.31% |
| a3-kimi4-tp8-longctx-decode-c6-p4k | 6 / 1 | moe_layer | 3 | 0.948 / 0.951 | 0.961 / 0.960 | +1.39% / +0.95% |
| a3-kimi4-tp8-longctx-decode-c8-p4k | 8 / 1 | kda | 3 | 0.915 / 0.888 | 0.824 / 0.965 | -9.93% / +8.66% |
| a3-kimi4-tp8-longctx-decode-c8-p4k | 8 / 1 | mla | 1 | 1.094 / 1.094 | 0.980 / 0.980 | -10.44% / -10.44% |
| a3-kimi4-tp8-longctx-decode-c8-p4k | 8 / 1 | dense_layer | 1 | 0.842 / 0.842 | 0.543 / 0.543 | -35.58% / -35.58% |
| a3-kimi4-tp8-longctx-decode-c8-p4k | 8 / 1 | moe_layer | 3 | 0.999 / 1.015 | 0.970 / 0.965 | -2.90% / -4.90% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | 1 / 1 | kda | 3 | 0.952 / 0.931 | 0.955 / 1.113 | +0.28% / +19.53% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | 1 / 1 | mla | 1 | 1.236 / 1.236 | 1.364 / 1.364 | +10.31% / +10.31% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | 1 / 1 | dense_layer | 1 | 0.931 / 0.931 | 0.638 / 0.638 | -31.43% / -31.43% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | 1 / 1 | moe_layer | 3 | 1.054 / 0.995 | 1.196 / 1.113 | +13.54% / +11.80% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | 12 / 1 | kda | 3 | 1.008 / 0.971 | 0.977 / 1.135 | -3.07% / +16.90% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | 12 / 1 | mla | 1 | 3.842 / 3.842 | 3.459 / 3.459 | -9.96% / -9.96% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | 12 / 1 | dense_layer | 1 | 0.971 / 0.971 | 0.660 / 0.660 | -31.97% / -31.97% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | 12 / 1 | moe_layer | 3 | 1.965 / 1.118 | 1.910 / 1.135 | -2.80% / +1.53% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | 16 / 1 | kda | 3 | 1.039 / 0.981 | 0.982 / 1.140 | -5.46% / +16.19% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | 16 / 1 | mla | 1 | 4.724 / 4.724 | 4.335 / 4.335 | -8.23% / -8.23% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | 16 / 1 | dense_layer | 1 | 0.971 / 0.971 | 0.666 / 0.666 | -31.46% / -31.46% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | 16 / 1 | moe_layer | 3 | 2.289 / 1.163 | 2.205 / 1.140 | -3.69% / -2.01% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | 2 / 1 | kda | 3 | 0.956 / 0.936 | 0.957 / 1.115 | +0.04% / +19.09% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | 2 / 1 | mla | 1 | 1.493 / 1.493 | 1.567 / 1.567 | +4.95% / +4.95% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | 2 / 1 | dense_layer | 1 | 0.936 / 0.936 | 0.640 / 0.640 | -31.59% / -31.59% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | 2 / 1 | moe_layer | 3 | 1.142 / 1.004 | 1.265 / 1.115 | +10.82% / +11.07% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | 24 / 1 | kda | 3 | 1.121 / 1.115 | 1.136 / 1.392 | +1.34% / +24.83% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | 24 / 1 | mla | 1 | 6.698 / 6.698 | 6.206 / 6.206 | -7.34% / -7.34% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | 24 / 1 | dense_layer | 1 | 0.884 / 0.884 | 0.625 / 0.625 | -29.33% / -29.33% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | 24 / 1 | moe_layer | 3 | 3.059 / 1.364 | 2.997 / 1.392 | -2.04% / +2.00% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | 32 / 1 | kda | 3 | 1.230 / 1.218 | 1.150 / 1.405 | -6.52% / +15.41% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | 32 / 1 | mla | 1 | 8.605 / 8.605 | 7.824 / 7.824 | -9.08% / -9.08% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | 32 / 1 | dense_layer | 1 | 0.985 / 0.985 | 0.638 / 0.638 | -35.19% / -35.19% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | 32 / 1 | moe_layer | 3 | 3.770 / 1.487 | 3.545 / 1.405 | -5.97% / -5.49% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | 4 / 1 | kda | 3 | 0.983 / 0.958 | 0.960 / 1.119 | -2.32% / +16.71% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | 4 / 1 | mla | 1 | 2.057 / 2.057 | 1.969 / 1.969 | -4.31% / -4.31% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | 4 / 1 | dense_layer | 1 | 0.958 / 0.958 | 0.644 / 0.644 | -32.78% / -32.78% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | 4 / 1 | moe_layer | 3 | 1.350 / 1.051 | 1.402 / 1.119 | +3.88% / +6.41% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | 48 / 1 | kda | 3 | 1.418 / 1.515 | 1.319 / 1.673 | -7.01% / +10.47% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | 48 / 1 | mla | 1 | 12.478 / 12.478 | 11.288 / 11.288 | -9.54% / -9.54% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | 48 / 1 | dense_layer | 1 | 1.007 / 1.007 | 0.611 / 0.611 | -39.36% / -39.36% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | 48 / 1 | moe_layer | 3 | 5.242 / 1.734 | 4.878 / 1.673 | -6.95% / -3.50% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | 6 / 1 | kda | 3 | 0.984 / 0.944 | 0.966 / 1.124 | -1.82% / +19.08% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | 6 / 1 | mla | 1 | 2.312 / 2.312 | 2.389 / 2.389 | +3.31% / +3.31% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | 6 / 1 | dense_layer | 1 | 0.944 / 0.944 | 0.650 / 0.650 | -31.18% / -31.18% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | 6 / 1 | moe_layer | 3 | 1.440 / 1.068 | 1.545 / 1.124 | +7.34% / +5.22% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | 64 / 1 | kda | 3 | 1.540 / 1.702 | 1.471 / 1.884 | -4.47% / +10.66% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | 64 / 1 | mla | 1 | 16.320 / 16.320 | 14.675 / 14.675 | -10.08% / -10.08% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | 64 / 1 | dense_layer | 1 | 0.991 / 0.991 | 0.647 / 0.647 | -34.70% / -34.70% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | 64 / 1 | moe_layer | 3 | 6.650 / 1.928 | 6.147 / 1.884 | -7.56% / -2.29% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | 8 / 1 | kda | 3 | 0.977 / 0.947 | 0.968 / 1.127 | -0.84% / +18.93% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | 8 / 1 | mla | 1 | 2.934 / 2.934 | 2.663 / 2.663 | -9.26% / -9.26% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | 8 / 1 | dense_layer | 1 | 0.912 / 0.912 | 0.652 / 0.652 | -28.50% / -28.50% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | 8 / 1 | moe_layer | 3 | 1.651 / 1.070 | 1.639 / 1.127 | -0.73% / +5.24% |
| a3-kimi4-tp16-128k-decode-c12-p16k | 12 / 1 | kda | 3 | 1.022 / 1.012 | 0.977 / 1.135 | -4.46% / +12.14% |
| a3-kimi4-tp16-128k-decode-c12-p16k | 12 / 1 | mla | 1 | 1.363 / 1.363 | 1.476 / 1.476 | +8.29% / +8.29% |
| a3-kimi4-tp16-128k-decode-c12-p16k | 12 / 1 | dense_layer | 1 | 1.012 / 1.012 | 0.660 / 0.660 | -34.74% / -34.74% |
| a3-kimi4-tp16-128k-decode-c12-p16k | 12 / 1 | moe_layer | 3 | 1.139 / 1.094 | 1.249 / 1.135 | +9.59% / +3.72% |
| a3-kimi4-tp16-128k-decode-c12-p32k | 12 / 1 | kda | 3 | 0.998 / 0.970 | 0.977 / 1.135 | -2.10% / +16.96% |
| a3-kimi4-tp16-128k-decode-c12-p32k | 12 / 1 | mla | 1 | 1.665 / 1.665 | 1.800 / 1.800 | +8.08% / +8.08% |
| a3-kimi4-tp16-128k-decode-c12-p32k | 12 / 1 | dense_layer | 1 | 0.970 / 0.970 | 0.660 / 0.660 | -31.94% / -31.94% |
| a3-kimi4-tp16-128k-decode-c12-p32k | 12 / 1 | moe_layer | 3 | 1.229 / 1.071 | 1.356 / 1.135 | +10.35% / +5.94% |
| a3-kimi4-tp16-128k-decode-c12-p4k | 12 / 1 | kda | 3 | 1.008 / 0.965 | 0.977 / 1.135 | -3.10% / +17.54% |
| a3-kimi4-tp16-128k-decode-c12-p4k | 12 / 1 | mla | 1 | 1.415 / 1.415 | 1.228 / 1.228 | -13.17% / -13.17% |
| a3-kimi4-tp16-128k-decode-c12-p4k | 12 / 1 | dense_layer | 1 | 0.965 / 0.965 | 0.660 / 0.660 | -31.60% / -31.60% |
| a3-kimi4-tp16-128k-decode-c12-p4k | 12 / 1 | moe_layer | 3 | 1.158 / 1.110 | 1.166 / 1.135 | +0.72% / +2.20% |
| a3-kimi4-tp16-128k-decode-c12-p8k | 12 / 1 | kda | 3 | 1.003 / 0.956 | 0.977 / 1.135 | -2.60% / +18.68% |
| a3-kimi4-tp16-128k-decode-c12-p8k | 12 / 1 | mla | 1 | 1.370 / 1.370 | 1.313 / 1.313 | -4.19% / -4.19% |
| a3-kimi4-tp16-128k-decode-c12-p8k | 12 / 1 | dense_layer | 1 | 0.951 / 0.951 | 0.660 / 0.660 | -30.57% / -30.57% |
| a3-kimi4-tp16-128k-decode-c12-p8k | 12 / 1 | moe_layer | 3 | 1.142 / 1.101 | 1.194 / 1.135 | +4.53% / +3.08% |
| a3-kimi4-tp16-128k-decode-c24-p16k | 24 / 1 | kda | 3 | 1.122 / 1.109 | 1.136 / 1.392 | +1.28% / +25.49% |
| a3-kimi4-tp16-128k-decode-c24-p16k | 24 / 1 | mla | 1 | 1.893 / 1.893 | 2.029 / 2.029 | +7.16% / +7.16% |
| a3-kimi4-tp16-128k-decode-c24-p16k | 24 / 1 | dense_layer | 1 | 0.914 / 0.914 | 0.625 / 0.625 | -31.68% / -31.68% |
| a3-kimi4-tp16-128k-decode-c24-p16k | 24 / 1 | moe_layer | 3 | 1.448 / 1.342 | 1.604 / 1.392 | +10.78% / +3.73% |
| a3-kimi4-tp16-128k-decode-c24-p32k | 24 / 1 | kda | 3 | 1.139 / 1.121 | 1.136 / 1.392 | -0.23% / +24.19% |
| a3-kimi4-tp16-128k-decode-c24-p32k | 24 / 1 | mla | 1 | 2.244 / 2.244 | 2.667 / 2.667 | +18.83% / +18.83% |
| a3-kimi4-tp16-128k-decode-c24-p32k | 24 / 1 | dense_layer | 1 | 0.934 / 0.934 | 0.625 / 0.625 | -33.13% / -33.13% |
| a3-kimi4-tp16-128k-decode-c24-p32k | 24 / 1 | moe_layer | 3 | 1.575 / 1.361 | 1.817 / 1.392 | +15.32% / +2.24% |
| a3-kimi4-tp16-128k-decode-c24-p4k | 24 / 1 | kda | 3 | 1.141 / 1.111 | 1.136 / 1.392 | -0.46% / +25.29% |
| a3-kimi4-tp16-128k-decode-c24-p4k | 24 / 1 | mla | 1 | 1.416 / 1.416 | 1.549 / 1.549 | +9.41% / +9.41% |
| a3-kimi4-tp16-128k-decode-c24-p4k | 24 / 1 | dense_layer | 1 | 0.961 / 0.961 | 0.625 / 0.625 | -34.98% / -34.98% |
| a3-kimi4-tp16-128k-decode-c24-p4k | 24 / 1 | moe_layer | 3 | 1.293 / 1.352 | 1.444 / 1.392 | +11.69% / +2.91% |
| a3-kimi4-tp16-128k-decode-c24-p8k | 24 / 1 | kda | 3 | 1.137 / 1.123 | 1.136 / 1.392 | -0.11% / +23.96% |
| a3-kimi4-tp16-128k-decode-c24-p8k | 24 / 1 | mla | 1 | 1.526 / 1.526 | 1.713 / 1.713 | +12.27% / +12.27% |
| a3-kimi4-tp16-128k-decode-c24-p8k | 24 / 1 | dense_layer | 1 | 0.946 / 0.946 | 0.625 / 0.625 | -33.97% / -33.97% |
| a3-kimi4-tp16-128k-decode-c24-p8k | 24 / 1 | moe_layer | 3 | 1.331 / 1.343 | 1.499 / 1.392 | +12.65% / +3.63% |
| a3-kimi4-tp16-128k-decode-c2-p4k | 2 / 1 | kda | 3 | 0.969 / 0.954 | 0.957 / 1.115 | -1.26% / +16.84% |
| a3-kimi4-tp16-128k-decode-c2-p4k | 2 / 1 | mla | 1 | 1.148 / 1.148 | 1.160 / 1.160 | +1.03% / +1.03% |
| a3-kimi4-tp16-128k-decode-c2-p4k | 2 / 1 | dense_layer | 1 | 0.954 / 0.954 | 0.640 / 0.640 | -32.88% / -32.88% |
| a3-kimi4-tp16-128k-decode-c2-p4k | 2 / 1 | moe_layer | 3 | 1.034 / 1.019 | 1.130 / 1.115 | +9.32% / +9.37% |
| a3-kimi4-tp16-128k-decode-c48-p4k | 48 / 1 | kda | 3 | 1.425 / 1.510 | 1.319 / 1.673 | -7.45% / +10.78% |
| a3-kimi4-tp16-128k-decode-c48-p4k | 48 / 1 | mla | 1 | 1.925 / 1.925 | 1.960 / 1.960 | +1.81% / +1.81% |
| a3-kimi4-tp16-128k-decode-c48-p4k | 48 / 1 | dense_layer | 1 | 1.011 / 1.011 | 0.611 / 0.611 | -39.60% / -39.60% |
| a3-kimi4-tp16-128k-decode-c48-p4k | 48 / 1 | moe_layer | 3 | 1.730 / 1.754 | 1.769 / 1.673 | +2.25% / -4.61% |
| a3-kimi4-tp16-128k-decode-c6-p4k | 6 / 1 | kda | 3 | 0.981 / 0.951 | 0.966 / 1.124 | -1.52% / +18.16% |
| a3-kimi4-tp16-128k-decode-c6-p4k | 6 / 1 | mla | 1 | 1.167 / 1.167 | 1.192 / 1.192 | +2.12% / +2.12% |
| a3-kimi4-tp16-128k-decode-c6-p4k | 6 / 1 | dense_layer | 1 | 0.937 / 0.937 | 0.650 / 0.650 | -30.65% / -30.65% |
| a3-kimi4-tp16-128k-decode-c6-p4k | 6 / 1 | moe_layer | 3 | 1.057 / 1.054 | 1.146 / 1.124 | +8.42% / +6.61% |
| a3-kimi4-tp16-128k-decode-c8-p4k | 8 / 1 | kda | 3 | 1.013 / 0.983 | 0.968 / 1.127 | -4.44% / +14.58% |
| a3-kimi4-tp16-128k-decode-c8-p4k | 8 / 1 | mla | 1 | 1.147 / 1.147 | 1.207 / 1.207 | +5.23% / +5.23% |
| a3-kimi4-tp16-128k-decode-c8-p4k | 8 / 1 | dense_layer | 1 | 0.983 / 0.983 | 0.652 / 0.652 | -33.67% / -33.67% |
| a3-kimi4-tp16-128k-decode-c8-p4k | 8 / 1 | moe_layer | 3 | 1.068 / 1.092 | 1.153 / 1.127 | +7.99% / +3.13% |
| a5_kimi_tp8_e16_bf16_128k_c1 | 1 / 1 | kda | 69 | 0.323 / 0.324 | 0.345 / 0.346 | +6.71% / +7.06% |
| a5_kimi_tp8_e16_bf16_128k_c1 | 1 / 1 | mla | 24 | 0.424 / 0.417 | 0.379 / 0.378 | -10.78% / -9.38% |
| a5_kimi_tp8_e16_bf16_128k_c1 | 1 / 1 | dense_layer | 1 | 0.276 / 0.276 | 0.240 / 0.240 | -12.77% / -12.77% |
| a5_kimi_tp8_e16_bf16_128k_c1 | 1 / 1 | moe_layer | 92 | 0.350 / 0.325 | 0.355 / 0.346 | +1.35% / +6.44% |
| a5_kimi_tp8_e16_bf16_128k_c2 | 2 / 1 | kda | 69 | 0.356 / 0.357 | 0.346 / 0.348 | -2.70% / -2.56% |
| a5_kimi_tp8_e16_bf16_128k_c2 | 2 / 1 | mla | 24 | 0.512 / 0.505 | 0.449 / 0.449 | -12.30% / -11.21% |
| a5_kimi_tp8_e16_bf16_128k_c2 | 2 / 1 | dense_layer | 1 | 0.288 / 0.288 | 0.242 / 0.242 | -16.03% / -16.03% |
| a5_kimi_tp8_e16_bf16_128k_c2 | 2 / 1 | moe_layer | 92 | 0.397 / 0.359 | 0.374 / 0.348 | -5.82% / -3.05% |
| a5_kimi_tp8_e16_bf16_128k_c4 | 4 / 1 | kda | 69 | 0.363 / 0.364 | 0.349 / 0.351 | -3.79% / -3.52% |
| a5_kimi_tp8_e16_bf16_128k_c4 | 4 / 1 | mla | 24 | 0.640 / 0.632 | 0.582 / 0.582 | -9.01% / -7.96% |
| a5_kimi_tp8_e16_bf16_128k_c4 | 4 / 1 | dense_layer | 1 | 0.302 / 0.302 | 0.245 / 0.245 | -19.01% / -19.01% |
| a5_kimi_tp8_e16_bf16_128k_c4 | 4 / 1 | moe_layer | 92 | 0.436 / 0.366 | 0.411 / 0.351 | -5.68% / -4.03% |
| a5_kimi_tp8_e16_bf16_128k_c6 | 6 / 1 | kda | 69 | 0.367 / 0.368 | 0.353 / 0.354 | -3.96% / -3.81% |
| a5_kimi_tp8_e16_bf16_128k_c6 | 6 / 1 | mla | 24 | 0.760 / 0.754 | 0.716 / 0.715 | -5.82% / -5.10% |
| a5_kimi_tp8_e16_bf16_128k_c6 | 6 / 1 | dense_layer | 1 | 0.308 / 0.308 | 0.248 / 0.248 | -19.52% / -19.52% |
| a5_kimi_tp8_e16_bf16_128k_c6 | 6 / 1 | moe_layer | 92 | 0.470 / 0.370 | 0.449 / 0.354 | -4.64% / -4.22% |
| a5_kimi_tp8_e16_bf16_128k_c8 | 8 / 1 | kda | 69 | 0.369 / 0.370 | 0.354 / 0.356 | -3.86% / -3.77% |
| a5_kimi_tp8_e16_bf16_128k_c8 | 8 / 1 | mla | 24 | 0.886 / 0.878 | 0.851 / 0.850 | -3.91% / -3.11% |
| a5_kimi_tp8_e16_bf16_128k_c8 | 8 / 1 | dense_layer | 1 | 0.301 / 0.301 | 0.250 / 0.250 | -17.06% / -17.06% |
| a5_kimi_tp8_e16_bf16_128k_c8 | 8 / 1 | moe_layer | 92 | 0.504 / 0.371 | 0.485 / 0.356 | -3.79% / -4.09% |
| a5_kimi_tp8_e16_bf16_128k_c12 | 12 / 1 | kda | 69 | 0.387 / 0.387 | 0.373 / 0.374 | -3.58% / -3.25% |
| a5_kimi_tp8_e16_bf16_128k_c12 | 12 / 1 | mla | 24 | 1.145 / 1.138 | 1.133 / 1.132 | -1.05% / -0.52% |
| a5_kimi_tp8_e16_bf16_128k_c12 | 12 / 1 | dense_layer | 1 | 0.314 / 0.314 | 0.266 / 0.266 | -15.29% / -15.29% |
| a5_kimi_tp8_e16_bf16_128k_c12 | 12 / 1 | moe_layer | 92 | 0.585 / 0.390 | 0.572 / 0.374 | -2.22% / -3.94% |
| a3-v41-tp4dp4-128k-c12 | 4 / 8 | mla | 40 | 1.354 / 1.177 | 1.324 / 1.273 | -2.19% / +8.17% |
| a3-v41-tp4dp4-128k-c12 | 4 / 8 | moe_layer | 40 | 1.354 / 1.177 | 1.324 / 1.273 | -2.19% / +8.17% |
| a3-v41-tp4dp4-128k-c16 | 4 / 8 | mla | 40 | 1.360 / 1.180 | 1.324 / 1.273 | -2.60% / +7.90% |
| a3-v41-tp4dp4-128k-c16 | 4 / 8 | moe_layer | 40 | 1.360 / 1.180 | 1.324 / 1.273 | -2.60% / +7.90% |
| a3-v41-tp4dp4-128k-c24 | 7 / 8 | mla | 40 | 1.406 / 1.224 | 1.412 / 1.332 | +0.45% / +8.82% |
| a3-v41-tp4dp4-128k-c24 | 7 / 8 | moe_layer | 40 | 1.406 / 1.224 | 1.412 / 1.332 | +0.45% / +8.82% |
| a3-v41-tp4dp4-128k-c32 | 8 / 8 | mla | 40 | 1.443 / 1.261 | 1.442 / 1.353 | -0.09% / +7.23% |
| a3-v41-tp4dp4-128k-c32 | 8 / 8 | moe_layer | 40 | 1.443 / 1.261 | 1.442 / 1.353 | -0.09% / +7.23% |
| a3-v41-tp4dp4-128k-c4 | 2 / 8 | mla | 40 | 1.329 / 1.147 | 1.273 / 1.240 | -4.25% / +8.08% |
| a3-v41-tp4dp4-128k-c4 | 2 / 8 | moe_layer | 40 | 1.329 / 1.147 | 1.273 / 1.240 | -4.25% / +8.08% |
| a3-v41-tp4dp4-128k-c48 | 13 / 8 | mla | 40 | 1.849 / 1.392 | 1.863 / 1.726 | +0.75% / +23.93% |
| a3-v41-tp4dp4-128k-c48 | 13 / 8 | moe_layer | 40 | 1.849 / 1.392 | 1.863 / 1.726 | +0.75% / +23.93% |
| a3-v41-tp4dp4-128k-c64 | 17 / 8 | mla | 40 | 1.936 / 1.475 | 1.958 / 1.783 | +1.13% / +20.89% |
| a3-v41-tp4dp4-128k-c64 | 17 / 8 | moe_layer | 40 | 1.936 / 1.475 | 1.958 / 1.783 | +1.13% / +20.89% |
| a3-v41-tp4dp4-128k-c8 | 3 / 8 | mla | 40 | 1.339 / 1.163 | 1.297 / 1.255 | -3.12% / +7.93% |
| a3-v41-tp4dp4-128k-c8 | 3 / 8 | moe_layer | 40 | 1.339 / 1.163 | 1.297 / 1.255 | -3.12% / +7.93% |
| a3-qwen35-tp4-decode-c1-p126000 | 1 / 4 | gdn | 30 | 0.407 / 0.407 | 0.410 / 0.410 | +0.76% / +0.93% |
| a3-qwen35-tp4-decode-c1-p126000 | 1 / 4 | gqa | 10 | 0.526 / 0.526 | 0.511 / 0.511 | -2.82% / -2.88% |
| a3-qwen35-tp4-decode-c1-p126000 | 1 / 4 | moe_layer | 40 | 0.437 / 0.410 | 0.436 / 0.410 | -0.31% / +0.11% |
| a3-qwen35-tp4-decode-c12-p126000 | 12 / 4 | gdn | 30 | 0.654 / 0.652 | 0.628 / 0.628 | -4.04% / -3.66% |
| a3-qwen35-tp4-decode-c12-p126000 | 12 / 4 | gqa | 10 | 1.652 / 1.649 | 1.600 / 1.600 | -3.13% / -2.97% |
| a3-qwen35-tp4-decode-c12-p126000 | 12 / 4 | moe_layer | 40 | 0.904 / 0.658 | 0.871 / 0.628 | -3.62% / -4.56% |
| a3-qwen35-tp4-decode-c16-p126000 | 16 / 4 | gdn | 30 | 0.688 / 0.687 | 0.661 / 0.661 | -3.88% / -3.72% |
| a3-qwen35-tp4-decode-c16-p126000 | 16 / 4 | gqa | 10 | 1.999 / 1.996 | 1.979 / 1.979 | -0.99% / -0.88% |
| a3-qwen35-tp4-decode-c16-p126000 | 16 / 4 | moe_layer | 40 | 1.016 / 0.692 | 0.991 / 0.661 | -2.46% / -4.49% |
| a3-qwen35-tp4-decode-c2-p126000 | 2 / 4 | gdn | 30 | 0.447 / 0.443 | 0.435 / 0.435 | -2.60% / -1.81% |
| a3-qwen35-tp4-decode-c2-p126000 | 2 / 4 | gqa | 10 | 0.615 / 0.615 | 0.600 / 0.600 | -2.47% / -2.52% |
| a3-qwen35-tp4-decode-c2-p126000 | 2 / 4 | moe_layer | 40 | 0.489 / 0.447 | 0.476 / 0.435 | -2.56% / -2.53% |
| a3-qwen35-tp4-decode-c24-p126000 | 24 / 4 | gdn | 30 | 0.744 / 0.740 | 0.724 / 0.724 | -2.62% / -2.14% |
| a3-qwen35-tp4-decode-c24-p126000 | 24 / 4 | gqa | 10 | 4.115 / 4.114 | 4.012 / 4.012 | -2.51% / -2.47% |
| a3-qwen35-tp4-decode-c24-p126000 | 24 / 4 | moe_layer | 40 | 1.587 / 0.745 | 1.546 / 0.724 | -2.55% / -2.81% |
| a3-qwen35-tp4-decode-c32-p126000 | 32 / 4 | gdn | 30 | 0.794 / 0.790 | 0.798 / 0.798 | +0.53% / +0.98% |
| a3-qwen35-tp4-decode-c32-p126000 | 32 / 4 | gqa | 10 | 4.151 / 4.146 | 4.054 / 4.054 | -2.33% / -2.21% |
| a3-qwen35-tp4-decode-c32-p126000 | 32 / 4 | moe_layer | 40 | 1.633 / 0.798 | 1.612 / 0.798 | -1.29% / -0.02% |
| a3-qwen35-tp4-decode-c4-p126000 | 4 / 4 | gdn | 30 | 0.481 / 0.482 | 0.478 / 0.478 | -0.51% / -0.84% |
| a3-qwen35-tp4-decode-c4-p126000 | 4 / 4 | gqa | 10 | 0.842 / 0.843 | 0.861 / 0.861 | +2.25% / +2.16% |
| a3-qwen35-tp4-decode-c4-p126000 | 4 / 4 | moe_layer | 40 | 0.571 / 0.484 | 0.574 / 0.478 | +0.51% / -1.23% |
| a3-qwen35-tp4-decode-c48-p126000 | 48 / 4 | gdn | 30 | 0.909 / 0.906 | 0.924 / 0.924 | +1.67% / +2.08% |
| a3-qwen35-tp4-decode-c48-p126000 | 48 / 4 | gqa | 10 | 5.914 / 5.908 | 5.809 / 5.809 | -1.78% / -1.69% |
| a3-qwen35-tp4-decode-c48-p126000 | 48 / 4 | moe_layer | 40 | 2.160 / 0.913 | 2.145 / 0.924 | -0.69% / +1.25% |
| a3-qwen35-tp4-decode-c6-p126000 | 6 / 4 | gdn | 30 | 0.558 / 0.555 | 0.539 / 0.539 | -3.51% / -3.00% |
| a3-qwen35-tp4-decode-c6-p126000 | 6 / 4 | gqa | 10 | 1.079 / 1.075 | 1.033 / 1.033 | -4.19% / -3.88% |
| a3-qwen35-tp4-decode-c6-p126000 | 6 / 4 | moe_layer | 40 | 0.688 / 0.558 | 0.662 / 0.539 | -3.78% / -3.47% |
| a3-qwen35-tp4-decode-c64-p126000 | 64 / 4 | gdn | 30 | 1.011 / 1.007 | 1.045 / 1.045 | +3.36% / +3.75% |
| a3-qwen35-tp4-decode-c64-p126000 | 64 / 4 | gqa | 10 | 7.732 / 7.732 | 7.586 / 7.586 | -1.89% / -1.88% |
| a3-qwen35-tp4-decode-c64-p126000 | 64 / 4 | moe_layer | 40 | 2.691 / 1.011 | 2.680 / 1.045 | -0.41% / +3.31% |
| a3-qwen35-tp4-decode-c8-p126000 | 8 / 4 | gdn | 30 | 0.601 / 0.600 | 0.588 / 0.588 | -2.31% / -2.14% |
| a3-qwen35-tp4-decode-c8-p126000 | 8 / 4 | gqa | 10 | 1.294 / 1.292 | 1.263 / 1.263 | -2.43% / -2.28% |
| a3-qwen35-tp4-decode-c8-p126000 | 8 / 4 | moe_layer | 40 | 0.775 / 0.603 | 0.756 / 0.588 | -2.36% / -2.50% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gdn | 30 | 0.659 / 0.657 | 0.628 / 0.628 | -4.66% / -4.48% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gqa | 10 | 0.813 / 0.813 | 0.824 / 0.824 | +1.30% / +1.32% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | moe_layer | 40 | 0.697 / 0.664 | 0.677 / 0.628 | -2.92% / -5.40% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gdn | 30 | 0.658 / 0.656 | 0.628 / 0.628 | -4.53% / -4.22% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gqa | 10 | 0.785 / 0.786 | 0.824 / 0.824 | +4.94% / +4.77% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | moe_layer | 40 | 0.689 / 0.663 | 0.677 / 0.628 | -1.84% / -5.28% |
| a3-qwen35-tp4-decode-c12-p24512 | 4 / 4 | gdn | 30 | 0.489 / 0.482 | 0.482 / 0.482 | -1.26% / +0.08% |
| a3-qwen35-tp4-decode-c12-p24512 | 4 / 4 | gqa | 10 | 0.547 / 0.550 | 0.545 / 0.545 | -0.52% / -0.95% |
| a3-qwen35-tp4-decode-c12-p24512 | 4 / 4 | moe_layer | 40 | 0.503 / 0.489 | 0.498 / 0.482 | -1.06% / -1.25% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gdn | 30 | 0.637 / 0.637 | 0.628 / 0.628 | -1.39% / -1.43% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gqa | 10 | 0.761 / 0.760 | 0.824 / 0.824 | +8.23% / +8.34% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | moe_layer | 40 | 0.668 / 0.641 | 0.677 / 0.628 | +1.35% / -2.07% |
| a3-qwen35-tp4-decode-c12-p24512 | 6 / 4 | gdn | 30 | 0.544 / 0.542 | 0.539 / 0.539 | -0.89% / -0.53% |
| a3-qwen35-tp4-decode-c12-p24512 | 6 / 4 | gqa | 10 | 0.622 / 0.622 | 0.628 / 0.628 | +0.83% / +0.84% |
| a3-qwen35-tp4-decode-c12-p24512 | 6 / 4 | moe_layer | 40 | 0.563 / 0.550 | 0.561 / 0.539 | -0.42% / -1.97% |
| a3-qwen35-tp4-decode-c12-p24512 | 3 / 4 | gdn | 30 | 0.471 / 0.471 | 0.459 / 0.459 | -2.64% / -2.58% |
| a3-qwen35-tp4-decode-c12-p24512 | 3 / 4 | gqa | 10 | 0.517 / 0.517 | 0.523 / 0.523 | +1.14% / +1.15% |
| a3-qwen35-tp4-decode-c12-p24512 | 3 / 4 | moe_layer | 40 | 0.483 / 0.474 | 0.475 / 0.459 | -1.63% / -3.14% |
| a3-qwen35-tp4-decode-c12-p24512 | 2 / 4 | gdn | 30 | 0.449 / 0.444 | 0.435 / 0.435 | -2.99% / -1.91% |
| a3-qwen35-tp4-decode-c12-p24512 | 2 / 4 | gqa | 10 | 0.476 / 0.477 | 0.460 / 0.460 | -3.36% / -3.68% |
| a3-qwen35-tp4-decode-c12-p24512 | 2 / 4 | moe_layer | 40 | 0.455 / 0.447 | 0.441 / 0.435 | -3.08% / -2.66% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gdn | 30 | 0.640 / 0.639 | 0.628 / 0.628 | -1.93% / -1.80% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gqa | 10 | 0.808 / 0.803 | 0.824 / 0.824 | +1.87% / +2.55% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | moe_layer | 40 | 0.682 / 0.643 | 0.677 / 0.628 | -0.81% / -2.37% |
| a3-qwen35-tp4-decode-c12-p24512 | 8 / 4 | gdn | 30 | 0.608 / 0.599 | 0.588 / 0.588 | -3.31% / -1.97% |
| a3-qwen35-tp4-decode-c12-p24512 | 8 / 4 | gqa | 10 | 0.698 / 0.698 | 0.735 / 0.735 | +5.34% / +5.30% |
| a3-qwen35-tp4-decode-c12-p24512 | 8 / 4 | moe_layer | 40 | 0.630 / 0.606 | 0.624 / 0.588 | -0.92% / -3.11% |
| a3-qwen35-tp4-decode-c12-p24512 | 1 / 4 | gdn | 30 | 0.406 / 0.404 | 0.412 / 0.412 | +1.38% / +1.94% |
| a3-qwen35-tp4-decode-c12-p24512 | 1 / 4 | gqa | 10 | 0.423 / 0.426 | 0.419 / 0.419 | -0.98% / -1.55% |
| a3-qwen35-tp4-decode-c12-p24512 | 1 / 4 | moe_layer | 40 | 0.410 / 0.406 | 0.414 / 0.412 | +0.77% / +1.32% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gdn | 30 | 0.661 / 0.656 | 0.628 / 0.628 | -5.06% / -4.27% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gqa | 10 | 1.068 / 1.068 | 1.130 / 1.130 | +5.74% / +5.76% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | moe_layer | 40 | 0.763 / 0.664 | 0.753 / 0.628 | -1.28% / -5.48% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gdn | 30 | 0.659 / 0.656 | 0.628 / 0.628 | -4.69% / -4.33% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gqa | 10 | 1.003 / 1.005 | 1.130 / 1.130 | +12.58% / +12.40% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | moe_layer | 40 | 0.745 / 0.663 | 0.753 / 0.628 | +1.13% / -5.28% |
| a3-qwen35-tp4-decode-c12-p64512 | 2 / 4 | gdn | 30 | 0.445 / 0.443 | 0.435 / 0.435 | -2.14% / -1.65% |
| a3-qwen35-tp4-decode-c12-p64512 | 2 / 4 | gqa | 10 | 0.528 / 0.528 | 0.515 / 0.515 | -2.42% / -2.41% |
| a3-qwen35-tp4-decode-c12-p64512 | 2 / 4 | moe_layer | 40 | 0.466 / 0.445 | 0.455 / 0.435 | -2.22% / -2.26% |
| a3-qwen35-tp4-decode-c12-p64512 | 1 / 4 | gdn | 30 | 0.414 / 0.406 | 0.412 / 0.412 | -0.44% / +1.52% |
| a3-qwen35-tp4-decode-c12-p64512 | 1 / 4 | gqa | 10 | 0.470 / 0.471 | 0.456 / 0.456 | -2.93% / -3.15% |
| a3-qwen35-tp4-decode-c12-p64512 | 1 / 4 | moe_layer | 40 | 0.428 / 0.407 | 0.423 / 0.412 | -1.13% / +1.19% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gdn | 30 | 0.642 / 0.641 | 0.628 / 0.628 | -2.13% / -2.06% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gqa | 10 | 1.088 / 1.090 | 1.130 / 1.130 | +3.80% / +3.61% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | moe_layer | 40 | 0.753 / 0.645 | 0.753 / 0.628 | +0.01% / -2.62% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | gdn | 30 | 0.604 / 0.603 | 0.588 / 0.588 | -2.71% / -2.49% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | gqa | 10 | 0.900 / 0.900 | 0.943 / 0.943 | +4.75% / +4.73% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | moe_layer | 40 | 0.678 / 0.606 | 0.676 / 0.588 | -0.24% / -3.12% |
| a3-qwen35-tp4-decode-c12-p64512 | 4 / 4 | gdn | 30 | 0.491 / 0.483 | 0.482 / 0.482 | -1.70% / -0.11% |
| a3-qwen35-tp4-decode-c12-p64512 | 4 / 4 | gqa | 10 | 0.654 / 0.651 | 0.659 / 0.659 | +0.71% / +1.21% |
| a3-qwen35-tp4-decode-c12-p64512 | 4 / 4 | moe_layer | 40 | 0.532 / 0.487 | 0.527 / 0.482 | -0.96% / -0.92% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | gdn | 30 | 0.602 / 0.602 | 0.588 / 0.588 | -2.38% / -2.42% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | gqa | 10 | 0.856 / 0.848 | 0.943 / 0.943 | +10.10% / +11.21% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | moe_layer | 40 | 0.665 / 0.605 | 0.676 / 0.588 | +1.64% / -2.83% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | gdn | 30 | 0.560 / 0.560 | 0.539 / 0.539 | -3.71% / -3.84% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | gqa | 10 | 0.765 / 0.764 | 0.788 / 0.788 | +2.94% / +3.06% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | moe_layer | 40 | 0.611 / 0.563 | 0.601 / 0.539 | -1.63% / -4.26% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | gdn | 30 | 0.547 / 0.544 | 0.539 / 0.539 | -1.52% / -0.99% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | gqa | 10 | 0.759 / 0.759 | 0.788 / 0.788 | +3.77% / +3.72% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | moe_layer | 40 | 0.600 / 0.546 | 0.601 / 0.539 | +0.15% / -1.30% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gdn | 30 | 0.662 / 0.660 | 0.628 / 0.628 | -5.16% / -4.82% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gqa | 10 | 0.755 / 0.754 | 0.753 / 0.753 | -0.22% / -0.10% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | moe_layer | 40 | 0.685 / 0.663 | 0.659 / 0.628 | -3.80% / -5.28% |
| a3-qwen35-tp4-decode-c12-p8512 | 8 / 4 | gdn | 30 | 0.613 / 0.602 | 0.588 / 0.588 | -4.18% / -2.34% |
| a3-qwen35-tp4-decode-c12-p8512 | 8 / 4 | gqa | 10 | 0.642 / 0.644 | 0.652 / 0.652 | +1.43% / +1.25% |
| a3-qwen35-tp4-decode-c12-p8512 | 8 / 4 | moe_layer | 40 | 0.620 / 0.604 | 0.604 / 0.588 | -2.73% / -2.75% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gdn | 30 | 0.640 / 0.640 | 0.628 / 0.628 | -1.85% / -1.86% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gqa | 10 | 0.751 / 0.752 | 0.753 / 0.753 | +0.25% / +0.17% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | moe_layer | 40 | 0.668 / 0.642 | 0.659 / 0.628 | -1.26% / -2.22% |
| a3-qwen35-tp4-decode-c12-p8512 | 1 / 4 | gdn | 30 | 0.413 / 0.405 | 0.412 / 0.412 | -0.22% / +1.71% |
| a3-qwen35-tp4-decode-c12-p8512 | 1 / 4 | gqa | 10 | 0.407 / 0.408 | 0.404 / 0.404 | -0.67% / -0.95% |
| a3-qwen35-tp4-decode-c12-p8512 | 1 / 4 | moe_layer | 40 | 0.411 / 0.406 | 0.410 / 0.412 | -0.33% / +1.47% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gdn | 30 | 0.637 / 0.635 | 0.628 / 0.628 | -1.38% / -1.12% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gqa | 10 | 0.744 / 0.740 | 0.753 / 0.753 | +1.17% / +1.74% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | moe_layer | 40 | 0.664 / 0.643 | 0.659 / 0.628 | -0.67% / -2.28% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | gdn | 30 | 0.559 / 0.546 | 0.539 / 0.539 | -3.67% / -1.34% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | gqa | 10 | 0.577 / 0.577 | 0.592 / 0.592 | +2.48% / +2.58% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | moe_layer | 40 | 0.564 / 0.550 | 0.552 / 0.539 | -2.09% / -2.02% |
| a3-qwen35-tp4-decode-c12-p8512 | 2 / 4 | gdn | 30 | 0.460 / 0.444 | 0.435 / 0.435 | -5.35% / -1.86% |
| a3-qwen35-tp4-decode-c12-p8512 | 2 / 4 | gqa | 10 | 0.448 / 0.451 | 0.438 / 0.438 | -2.23% / -2.85% |
| a3-qwen35-tp4-decode-c12-p8512 | 2 / 4 | moe_layer | 40 | 0.457 / 0.446 | 0.436 / 0.435 | -4.59% / -2.32% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | gdn | 30 | 0.566 / 0.558 | 0.539 / 0.539 | -4.75% / -3.45% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | gqa | 10 | 0.590 / 0.591 | 0.592 / 0.592 | +0.31% / +0.10% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | moe_layer | 40 | 0.572 / 0.564 | 0.552 / 0.539 | -3.45% / -4.47% |
| a3-qwen35-tp4-decode-c12-p8512 | 4 / 4 | gdn | 30 | 0.501 / 0.486 | 0.482 / 0.482 | -3.73% / -0.82% |
| a3-qwen35-tp4-decode-c12-p8512 | 4 / 4 | gqa | 10 | 0.506 / 0.503 | 0.499 / 0.499 | -1.34% / -0.72% |
| a3-qwen35-tp4-decode-c12-p8512 | 4 / 4 | moe_layer | 40 | 0.502 / 0.490 | 0.487 / 0.482 | -3.13% / -1.56% |
| a3-qwen35-tp4-decode-c12-p8512 | 3 / 4 | gdn | 30 | 0.498 / 0.473 | 0.459 / 0.459 | -7.78% / -2.95% |
| a3-qwen35-tp4-decode-c12-p8512 | 3 / 4 | gqa | 10 | 0.491 / 0.490 | 0.478 / 0.478 | -2.76% / -2.58% |
| a3-qwen35-tp4-decode-c12-p8512 | 3 / 4 | moe_layer | 40 | 0.496 / 0.475 | 0.464 / 0.459 | -6.54% / -3.29% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gdn | 30 | 0.661 / 0.654 | 0.628 / 0.628 | -5.07% / -4.01% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gqa | 10 | 1.330 / 1.333 | 1.374 / 1.374 | +3.35% / +3.10% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | moe_layer | 40 | 0.828 / 0.660 | 0.814 / 0.628 | -1.69% / -4.92% |
| a3-qwen35-tp4-decode-c12-p96512 | 2 / 4 | gdn | 30 | 0.443 / 0.444 | 0.435 / 0.435 | -1.84% / -1.98% |
| a3-qwen35-tp4-decode-c12-p96512 | 2 / 4 | gqa | 10 | 0.576 / 0.578 | 0.559 / 0.559 | -2.95% / -3.20% |
| a3-qwen35-tp4-decode-c12-p96512 | 2 / 4 | moe_layer | 40 | 0.477 / 0.446 | 0.466 / 0.435 | -2.18% / -2.47% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gdn | 30 | 0.657 / 0.653 | 0.628 / 0.628 | -4.39% / -3.84% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gqa | 10 | 1.242 / 1.240 | 1.374 / 1.374 | +10.66% / +10.79% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | moe_layer | 40 | 0.803 / 0.662 | 0.814 / 0.628 | +1.43% / -5.22% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | gdn | 30 | 0.541 / 0.540 | 0.539 / 0.539 | -0.42% / -0.16% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | gqa | 10 | 0.863 / 0.863 | 0.916 / 0.916 | +6.06% / +6.11% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | moe_layer | 40 | 0.622 / 0.545 | 0.633 / 0.539 | +1.83% / -1.05% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gdn | 30 | 0.641 / 0.634 | 0.628 / 0.628 | -2.08% / -0.99% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gqa | 10 | 1.320 / 1.318 | 1.374 / 1.374 | +4.12% / +4.29% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | moe_layer | 40 | 0.811 / 0.642 | 0.814 / 0.628 | +0.44% / -2.22% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gdn | 30 | 0.638 / 0.635 | 0.628 / 0.628 | -1.59% / -1.09% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gqa | 10 | 1.136 / 1.135 | 1.374 / 1.374 | +21.01% / +21.07% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | moe_layer | 40 | 0.762 / 0.643 | 0.814 / 0.628 | +6.83% / -2.34% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | gdn | 30 | 0.609 / 0.605 | 0.588 / 0.588 | -3.48% / -2.94% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | gqa | 10 | 1.086 / 1.079 | 1.109 / 1.109 | +2.10% / +2.76% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | moe_layer | 40 | 0.728 / 0.615 | 0.718 / 0.588 | -1.40% / -4.51% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | gdn | 30 | 0.601 / 0.597 | 0.588 / 0.588 | -2.21% / -1.56% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | gqa | 10 | 1.012 / 1.014 | 1.109 / 1.109 | +9.58% / +9.38% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | moe_layer | 40 | 0.704 / 0.606 | 0.718 / 0.588 | +2.03% / -3.00% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | gdn | 30 | 0.558 / 0.557 | 0.539 / 0.539 | -3.46% / -3.33% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | gqa | 10 | 0.898 / 0.897 | 0.916 / 0.916 | +1.96% / +2.05% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | moe_layer | 40 | 0.643 / 0.561 | 0.633 / 0.539 | -1.56% / -3.95% |
| a3-qwen35-tp4-decode-c12-p96512 | 3 / 4 | gdn | 30 | 0.469 / 0.471 | 0.459 / 0.459 | -2.18% / -2.66% |
| a3-qwen35-tp4-decode-c12-p96512 | 3 / 4 | gqa | 10 | 0.655 / 0.658 | 0.728 / 0.728 | +11.23% / +10.67% |
| a3-qwen35-tp4-decode-c12-p96512 | 3 / 4 | moe_layer | 40 | 0.516 / 0.474 | 0.526 / 0.459 | +2.08% / -3.26% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.752 / 0.747 | 0.724 / 0.724 | -3.74% / -3.07% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.295 / 1.295 | 1.323 / 1.323 | +2.13% / +2.16% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.888 / 0.755 | 0.874 / 0.724 | -1.60% / -4.05% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.745 / 0.742 | 0.724 / 0.724 | -2.72% / -2.40% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.292 / 1.291 | 1.323 / 1.323 | +2.35% / +2.43% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.881 / 0.749 | 0.874 / 0.724 | -0.86% / -3.29% |
| a3-qwen35-tp4-decode-c24-p24512 | 16 / 4 | gdn | 30 | 0.680 / 0.676 | 0.661 / 0.661 | -2.77% / -2.13% |
| a3-qwen35-tp4-decode-c24-p24512 | 16 / 4 | gqa | 10 | 0.860 / 0.859 | 0.923 / 0.923 | +7.37% / +7.52% |
| a3-qwen35-tp4-decode-c24-p24512 | 16 / 4 | moe_layer | 40 | 0.725 / 0.682 | 0.727 / 0.661 | +0.24% / -3.02% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.747 / 0.742 | 0.724 / 0.724 | -2.98% / -2.41% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.287 / 1.290 | 1.323 / 1.323 | +2.78% / +2.54% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.882 / 0.748 | 0.874 / 0.724 | -0.88% / -3.21% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.745 / 0.743 | 0.724 / 0.724 | -2.81% / -2.46% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.286 / 1.290 | 1.323 / 1.323 | +2.81% / +2.55% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.881 / 0.747 | 0.874 / 0.724 | -0.76% / -3.08% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.728 / 0.728 | 0.724 / 0.724 | -0.44% / -0.54% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.072 / 1.071 | 1.323 / 1.323 | +23.32% / +23.50% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.814 / 0.731 | 0.874 / 0.724 | +7.39% / -0.98% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.731 / 0.726 | 0.724 / 0.724 | -0.87% / -0.25% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.055 / 1.057 | 1.323 / 1.323 | +25.37% / +25.13% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.812 / 0.732 | 0.874 / 0.724 | +7.65% / -1.11% |
| a3-qwen35-tp4-decode-c24-p64512 | 24 / 4 | gdn | 30 | 0.748 / 0.745 | 0.724 / 0.724 | -3.13% / -2.73% |
| a3-qwen35-tp4-decode-c24-p64512 | 24 / 4 | gqa | 10 | 2.241 / 2.240 | 2.383 / 2.383 | +6.32% / +6.36% |
| a3-qwen35-tp4-decode-c24-p64512 | 24 / 4 | moe_layer | 40 | 1.121 / 0.753 | 1.139 / 0.724 | +1.59% / -3.78% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.748 / 0.745 | 0.724 / 0.724 | -3.11% / -2.78% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.922 / 0.919 | 0.926 / 0.926 | +0.41% / +0.74% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.791 / 0.754 | 0.775 / 0.724 | -2.08% / -3.89% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.746 / 0.746 | 0.724 / 0.724 | -2.90% / -2.86% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.927 / 0.925 | 0.926 / 0.926 | -0.09% / +0.12% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.791 / 0.752 | 0.775 / 0.724 | -2.08% / -3.66% |
| a3-qwen35-tp4-decode-c24-p8512 | 1 / 4 | gdn | 30 | 0.405 / 0.406 | 0.412 / 0.412 | +1.57% / +1.39% |
| a3-qwen35-tp4-decode-c24-p8512 | 1 / 4 | gqa | 10 | 0.409 / 0.410 | 0.404 / 0.404 | -1.10% / -1.35% |
| a3-qwen35-tp4-decode-c24-p8512 | 1 / 4 | moe_layer | 40 | 0.406 / 0.407 | 0.410 / 0.412 | +0.90% / +1.26% |
| a3-qwen35-tp4-decode-c24-p8512 | 8 / 4 | gdn | 30 | 0.611 / 0.607 | 0.588 / 0.588 | -3.83% / -3.16% |
| a3-qwen35-tp4-decode-c24-p8512 | 8 / 4 | gqa | 10 | 0.645 / 0.643 | 0.652 / 0.652 | +1.02% / +1.31% |
| a3-qwen35-tp4-decode-c24-p8512 | 8 / 4 | moe_layer | 40 | 0.619 / 0.612 | 0.604 / 0.588 | -2.56% / -4.01% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.748 / 0.746 | 0.724 / 0.724 | -3.14% / -2.84% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.928 / 0.923 | 0.926 / 0.926 | -0.22% / +0.35% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.793 / 0.752 | 0.775 / 0.724 | -2.29% / -3.67% |
| a3-qwen35-tp4-decode-c24-p8512 | 6 / 4 | gdn | 30 | 0.576 / 0.561 | 0.539 / 0.539 | -6.50% / -3.87% |
| a3-qwen35-tp4-decode-c24-p8512 | 6 / 4 | gqa | 10 | 0.592 / 0.590 | 0.592 / 0.592 | -0.01% / +0.20% |
| a3-qwen35-tp4-decode-c24-p8512 | 6 / 4 | moe_layer | 40 | 0.580 / 0.566 | 0.552 / 0.539 | -4.85% / -4.78% |
| a3-qwen35-tp4-decode-c24-p8512 | 4 / 4 | gdn | 30 | 0.486 / 0.483 | 0.482 / 0.482 | -0.71% / -0.01% |
| a3-qwen35-tp4-decode-c24-p8512 | 4 / 4 | gqa | 10 | 0.503 / 0.503 | 0.499 / 0.499 | -0.72% / -0.73% |
| a3-qwen35-tp4-decode-c24-p8512 | 4 / 4 | moe_layer | 40 | 0.490 / 0.485 | 0.487 / 0.482 | -0.71% / -0.47% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.727 / 0.725 | 0.724 / 0.724 | -0.33% / -0.07% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.838 / 0.838 | 0.926 / 0.926 | +10.55% / +10.48% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.754 / 0.730 | 0.775 / 0.724 | +2.69% / -0.78% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.725 / 0.725 | 0.724 / 0.724 | -0.07% / -0.08% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.828 / 0.824 | 0.926 / 0.926 | +11.89% / +12.37% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.751 / 0.729 | 0.775 / 0.724 | +3.23% / -0.65% |
| a3-qwen35-tp4-decode-c24-p8512 | 16 / 4 | gdn | 30 | 0.674 / 0.674 | 0.661 / 0.661 | -1.89% / -1.87% |
| a3-qwen35-tp4-decode-c24-p8512 | 16 / 4 | gqa | 10 | 0.772 / 0.773 | 0.757 / 0.757 | -1.95% / -2.05% |
| a3-qwen35-tp4-decode-c24-p8512 | 16 / 4 | moe_layer | 40 | 0.699 / 0.680 | 0.685 / 0.661 | -1.91% / -2.77% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gdn | 30 | 0.655 / 0.657 | 0.628 / 0.628 | -4.13% / -4.42% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gqa | 10 | 0.748 / 0.745 | 0.753 / 0.753 | +0.74% / +1.05% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | moe_layer | 40 | 0.678 / 0.658 | 0.659 / 0.628 | -2.79% / -4.65% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gdn | 30 | 0.637 / 0.637 | 0.628 / 0.628 | -1.49% / -1.47% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gqa | 10 | 0.747 / 0.745 | 0.753 / 0.753 | +0.83% / +1.12% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | moe_layer | 40 | 0.665 / 0.642 | 0.659 / 0.628 | -0.84% / -2.20% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gdn | 30 | 0.634 / 0.633 | 0.628 / 0.628 | -1.00% / -0.88% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gqa | 10 | 0.745 / 0.745 | 0.753 / 0.753 | +1.06% / +1.14% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | moe_layer | 40 | 0.662 / 0.637 | 0.659 / 0.628 | -0.42% / -1.39% |
| a3-qwen35-tp4-decode-c24-p96512 | 24 / 4 | gdn | 30 | 0.746 / 0.743 | 0.724 / 0.724 | -2.90% / -2.47% |
| a3-qwen35-tp4-decode-c24-p96512 | 24 / 4 | gqa | 10 | 3.249 / 3.255 | 3.231 / 3.231 | -0.57% / -0.76% |
| a3-qwen35-tp4-decode-c24-p96512 | 24 / 4 | moe_layer | 40 | 1.372 / 0.748 | 1.351 / 0.724 | -1.52% / -3.18% |
| a3-qwen35-tp4-decode-c2-p24512 | 1 / 4 | gdn | 30 | 0.413 / 0.408 | 0.412 / 0.412 | -0.30% / +0.94% |
| a3-qwen35-tp4-decode-c2-p24512 | 1 / 4 | gqa | 10 | 0.428 / 0.429 | 0.419 / 0.419 | -2.09% / -2.27% |
| a3-qwen35-tp4-decode-c2-p24512 | 1 / 4 | moe_layer | 40 | 0.417 / 0.410 | 0.414 / 0.412 | -0.76% / +0.45% |
| a3-qwen35-tp4-decode-c2-p24512 | 2 / 4 | gdn | 30 | 0.446 / 0.443 | 0.435 / 0.435 | -2.46% / -1.65% |
| a3-qwen35-tp4-decode-c2-p24512 | 2 / 4 | gqa | 10 | 0.473 / 0.474 | 0.460 / 0.460 | -2.81% / -2.97% |
| a3-qwen35-tp4-decode-c2-p24512 | 2 / 4 | moe_layer | 40 | 0.453 / 0.446 | 0.441 / 0.435 | -2.55% / -2.39% |
| a3-qwen35-tp4-decode-c2-p64512 | 1 / 4 | gdn | 30 | 0.413 / 0.407 | 0.412 / 0.412 | -0.26% / +1.17% |
| a3-qwen35-tp4-decode-c2-p64512 | 1 / 4 | gqa | 10 | 0.472 / 0.473 | 0.456 / 0.456 | -3.49% / -3.53% |
| a3-qwen35-tp4-decode-c2-p64512 | 1 / 4 | moe_layer | 40 | 0.428 / 0.409 | 0.423 / 0.412 | -1.15% / +0.72% |
| a3-qwen35-tp4-decode-c2-p64512 | 2 / 4 | gdn | 30 | 0.447 / 0.442 | 0.435 / 0.435 | -2.55% / -1.47% |
| a3-qwen35-tp4-decode-c2-p64512 | 2 / 4 | gqa | 10 | 0.525 / 0.525 | 0.515 / 0.515 | -1.97% / -1.85% |
| a3-qwen35-tp4-decode-c2-p64512 | 2 / 4 | moe_layer | 40 | 0.466 / 0.445 | 0.455 / 0.435 | -2.39% / -2.23% |
| a3-qwen35-tp4-decode-c2-p8512 | 1 / 4 | gdn | 30 | 0.407 / 0.407 | 0.412 / 0.412 | +1.25% / +1.19% |
| a3-qwen35-tp4-decode-c2-p8512 | 1 / 4 | gqa | 10 | 0.409 / 0.412 | 0.404 / 0.404 | -1.16% / -1.86% |
| a3-qwen35-tp4-decode-c2-p8512 | 1 / 4 | moe_layer | 40 | 0.407 / 0.407 | 0.410 / 0.412 | +0.64% / +1.06% |
| a3-qwen35-tp4-decode-c2-p96512 | 1 / 4 | gdn | 30 | 0.410 / 0.408 | 0.412 / 0.412 | +0.35% / +0.93% |
| a3-qwen35-tp4-decode-c2-p96512 | 1 / 4 | gqa | 10 | 0.500 / 0.502 | 0.485 / 0.485 | -2.95% / -3.34% |
| a3-qwen35-tp4-decode-c2-p96512 | 1 / 4 | moe_layer | 40 | 0.433 / 0.411 | 0.430 / 0.412 | -0.60% / +0.19% |
| a3-qwen35-tp4-decode-c2-p96512 | 2 / 4 | gdn | 30 | 0.443 / 0.440 | 0.435 / 0.435 | -1.75% / -1.08% |
| a3-qwen35-tp4-decode-c2-p96512 | 2 / 4 | gqa | 10 | 0.571 / 0.569 | 0.559 / 0.559 | -2.00% / -1.78% |
| a3-qwen35-tp4-decode-c2-p96512 | 2 / 4 | moe_layer | 40 | 0.475 / 0.445 | 0.466 / 0.435 | -1.83% / -2.20% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | gdn | 30 | 0.563 / 0.557 | 0.539 / 0.539 | -4.32% / -3.32% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | gqa | 10 | 0.630 / 0.633 | 0.628 / 0.628 | -0.45% / -0.86% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | moe_layer | 40 | 0.580 / 0.562 | 0.561 / 0.539 | -3.27% / -4.04% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | gdn | 30 | 0.549 / 0.546 | 0.539 / 0.539 | -1.91% / -1.34% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | gqa | 10 | 0.623 / 0.625 | 0.628 / 0.628 | +0.78% / +0.47% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | moe_layer | 40 | 0.568 / 0.550 | 0.561 / 0.539 | -1.17% / -1.98% |
| a3-qwen35-tp4-decode-c6-p24512 | 1 / 4 | gdn | 30 | 0.410 / 0.409 | 0.412 / 0.412 | +0.48% / +0.75% |
| a3-qwen35-tp4-decode-c6-p24512 | 1 / 4 | gqa | 10 | 0.427 / 0.428 | 0.419 / 0.419 | -1.95% / -2.08% |
| a3-qwen35-tp4-decode-c6-p24512 | 1 / 4 | moe_layer | 40 | 0.414 / 0.410 | 0.414 / 0.412 | -0.15% / +0.39% |
| a3-qwen35-tp4-decode-c6-p24512 | 2 / 4 | gdn | 30 | 0.443 / 0.441 | 0.435 / 0.435 | -1.69% / -1.29% |
| a3-qwen35-tp4-decode-c6-p24512 | 2 / 4 | gqa | 10 | 0.474 / 0.476 | 0.460 / 0.460 | -3.02% / -3.40% |
| a3-qwen35-tp4-decode-c6-p24512 | 2 / 4 | moe_layer | 40 | 0.451 / 0.444 | 0.441 / 0.435 | -2.04% / -1.98% |
| a3-qwen35-tp4-decode-c6-p24512 | 3 / 4 | gdn | 30 | 0.466 / 0.467 | 0.459 / 0.459 | -1.53% / -1.79% |
| a3-qwen35-tp4-decode-c6-p24512 | 3 / 4 | gqa | 10 | 0.513 / 0.515 | 0.523 / 0.523 | +2.08% / +1.52% |
| a3-qwen35-tp4-decode-c6-p24512 | 3 / 4 | moe_layer | 40 | 0.478 / 0.469 | 0.475 / 0.459 | -0.56% / -2.20% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | gdn | 30 | 0.566 / 0.557 | 0.539 / 0.539 | -4.81% / -3.28% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | gqa | 10 | 0.766 / 0.767 | 0.788 / 0.788 | +2.84% / +2.66% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | moe_layer | 40 | 0.616 / 0.562 | 0.601 / 0.539 | -2.43% / -4.08% |
| a3-qwen35-tp4-decode-c6-p64512 | 2 / 4 | gdn | 30 | 0.451 / 0.444 | 0.435 / 0.435 | -3.52% / -1.92% |
| a3-qwen35-tp4-decode-c6-p64512 | 2 / 4 | gqa | 10 | 0.528 / 0.530 | 0.515 / 0.515 | -2.54% / -2.81% |
| a3-qwen35-tp4-decode-c6-p64512 | 2 / 4 | moe_layer | 40 | 0.471 / 0.447 | 0.455 / 0.435 | -3.25% / -2.61% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | gdn | 30 | 0.549 / 0.540 | 0.539 / 0.539 | -1.80% / -0.30% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | gqa | 10 | 0.756 / 0.748 | 0.788 / 0.788 | +4.22% / +5.32% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | moe_layer | 40 | 0.600 / 0.543 | 0.601 / 0.539 | +0.09% / -0.72% |
| a3-qwen35-tp4-decode-c6-p64512 | 3 / 4 | gdn | 30 | 0.503 / 0.469 | 0.459 / 0.459 | -8.72% / -2.07% |
| a3-qwen35-tp4-decode-c6-p64512 | 3 / 4 | gqa | 10 | 0.586 / 0.585 | 0.637 / 0.637 | +8.78% / +8.88% |
| a3-qwen35-tp4-decode-c6-p64512 | 3 / 4 | moe_layer | 40 | 0.524 / 0.471 | 0.503 / 0.459 | -3.83% / -2.63% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | gdn | 30 | 0.564 / 0.560 | 0.539 / 0.539 | -4.54% / -3.80% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | gqa | 10 | 0.589 / 0.593 | 0.592 / 0.592 | +0.49% / -0.17% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | moe_layer | 40 | 0.570 / 0.562 | 0.552 / 0.539 | -3.24% / -4.07% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | gdn | 30 | 0.552 / 0.543 | 0.539 / 0.539 | -2.35% / -0.74% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | gqa | 10 | 0.573 / 0.578 | 0.592 / 0.592 | +3.29% / +2.41% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | moe_layer | 40 | 0.557 / 0.545 | 0.552 / 0.539 | -0.90% / -1.17% |
| a3-qwen35-tp4-decode-c6-p8512 | 1 / 4 | gdn | 30 | 0.409 / 0.406 | 0.412 / 0.412 | +0.55% / +1.33% |
| a3-qwen35-tp4-decode-c6-p8512 | 1 / 4 | gqa | 10 | 0.410 / 0.411 | 0.404 / 0.404 | -1.43% / -1.68% |
| a3-qwen35-tp4-decode-c6-p8512 | 1 / 4 | moe_layer | 40 | 0.410 / 0.407 | 0.410 / 0.412 | +0.05% / +1.15% |
| a3-qwen35-tp4-decode-c6-p8512 | 4 / 4 | gdn | 30 | 0.490 / 0.486 | 0.482 / 0.482 | -1.63% / -0.75% |
| a3-qwen35-tp4-decode-c6-p8512 | 4 / 4 | gqa | 10 | 0.506 / 0.508 | 0.499 / 0.499 | -1.39% / -1.82% |
| a3-qwen35-tp4-decode-c6-p8512 | 4 / 4 | moe_layer | 40 | 0.494 / 0.489 | 0.487 / 0.482 | -1.57% / -1.35% |
| a3-qwen35-tp4-decode-c6-p8512 | 2 / 4 | gdn | 30 | 0.450 / 0.444 | 0.435 / 0.435 | -3.30% / -1.88% |
| a3-qwen35-tp4-decode-c6-p8512 | 2 / 4 | gqa | 10 | 0.442 / 0.442 | 0.438 / 0.438 | -0.94% / -0.91% |
| a3-qwen35-tp4-decode-c6-p8512 | 2 / 4 | moe_layer | 40 | 0.448 / 0.443 | 0.436 / 0.435 | -2.72% / -1.80% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | gdn | 30 | 0.562 / 0.558 | 0.539 / 0.539 | -4.08% / -3.48% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | gqa | 10 | 0.927 / 0.897 | 0.916 / 0.916 | -1.23% / +2.08% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | moe_layer | 40 | 0.653 / 0.560 | 0.633 / 0.539 | -3.07% / -3.82% |
| a3-qwen35-tp4-decode-c6-p96512 | 1 / 4 | gdn | 30 | 0.406 / 0.408 | 0.412 / 0.412 | +1.31% / +1.03% |
| a3-qwen35-tp4-decode-c6-p96512 | 1 / 4 | gqa | 10 | 0.498 / 0.500 | 0.485 / 0.485 | -2.51% / -2.83% |
| a3-qwen35-tp4-decode-c6-p96512 | 1 / 4 | moe_layer | 40 | 0.429 / 0.410 | 0.430 / 0.412 | +0.21% / +0.45% |
| a3-qwen35-tp4-decode-c6-p96512 | 4 / 4 | gdn | 30 | 0.487 / 0.484 | 0.482 / 0.482 | -0.94% / -0.37% |
| a3-qwen35-tp4-decode-c6-p96512 | 4 / 4 | gqa | 10 | 0.752 / 0.751 | 0.750 / 0.750 | -0.26% / -0.14% |
| a3-qwen35-tp4-decode-c6-p96512 | 4 / 4 | moe_layer | 40 | 0.553 / 0.489 | 0.549 / 0.482 | -0.71% / -1.25% |
| a3-qwen35-tp4-decode-c6-p96512 | 3 / 4 | gdn | 30 | 0.471 / 0.473 | 0.459 / 0.459 | -2.63% / -2.97% |
| a3-qwen35-tp4-decode-c6-p96512 | 3 / 4 | gqa | 10 | 0.657 / 0.655 | 0.728 / 0.728 | +10.86% / +11.17% |
| a3-qwen35-tp4-decode-c6-p96512 | 3 / 4 | moe_layer | 40 | 0.518 / 0.474 | 0.526 / 0.459 | +1.65% / -3.12% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | gdn | 30 | 0.540 / 0.541 | 0.539 / 0.539 | -0.24% / -0.48% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | gqa | 10 | 0.863 / 0.867 | 0.916 / 0.916 | +6.12% / +5.54% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | moe_layer | 40 | 0.621 / 0.544 | 0.633 / 0.539 | +1.97% / -0.92% |
| a3-qwen35-tp4-decode-c6-p96512 | 2 / 4 | gdn | 30 | 0.445 / 0.446 | 0.435 / 0.435 | -2.08% / -2.34% |
| a3-qwen35-tp4-decode-c6-p96512 | 2 / 4 | gqa | 10 | 0.573 / 0.571 | 0.559 / 0.559 | -2.50% / -2.03% |
| a3-qwen35-tp4-decode-c6-p96512 | 2 / 4 | moe_layer | 40 | 0.477 / 0.449 | 0.466 / 0.435 | -2.20% / -3.02% |
| a3-qwen36-tp2-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.370 / 0.368 | 0.378 / 0.378 | +2.20% / +2.68% |
| a3-qwen36-tp2-decode-c1-p126000 | 1 / 4 | gqa | 16 | 0.607 / 0.606 | 0.578 / 0.578 | -4.76% / -4.66% |
| a3-qwen36-tp2-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.429 / 0.371 | 0.428 / 0.378 | -0.26% / +1.81% |
| a3-qwen36-tp2-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.600 / 0.600 | 0.615 / 0.615 | +2.46% / +2.60% |
| a3-qwen36-tp2-decode-c12-p126000 | 12 / 4 | gqa | 16 | 4.006 / 4.006 | 3.985 / 3.985 | -0.54% / -0.52% |
| a3-qwen36-tp2-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 1.452 / 0.603 | 1.458 / 0.615 | +0.39% / +2.08% |
| a3-qwen36-tp2-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.666 / 0.666 | 0.695 / 0.695 | +4.36% / +4.48% |
| a3-qwen36-tp2-decode-c16-p126000 | 16 / 4 | gqa | 16 | 4.025 / 4.023 | 4.020 / 4.020 | -0.12% / -0.07% |
| a3-qwen36-tp2-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 1.506 / 0.669 | 1.527 / 0.695 | +1.37% / +3.95% |
| a3-qwen36-tp2-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.408 / 0.405 | 0.401 / 0.401 | -1.59% / -1.00% |
| a3-qwen36-tp2-decode-c2-p126000 | 2 / 4 | gqa | 16 | 0.775 / 0.775 | 0.744 / 0.744 | -4.02% / -4.03% |
| a3-qwen36-tp2-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.500 / 0.408 | 0.487 / 0.401 | -2.53% / -1.61% |
| a3-qwen36-tp2-decode-c24-p126000 | 24 / 4 | gdn | 48 | 0.796 / 0.795 | 0.790 / 0.790 | -0.82% / -0.71% |
| a3-qwen36-tp2-decode-c24-p126000 | 24 / 4 | gqa | 16 | 5.902 / 5.902 | 5.821 / 5.821 | -1.39% / -1.38% |
| a3-qwen36-tp2-decode-c24-p126000 | 24 / 4 | dense_layer | 64 | 2.073 / 0.797 | 2.047 / 0.790 | -1.22% / -0.90% |
| a3-qwen36-tp2-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.459 / 0.461 | 0.448 / 0.448 | -2.53% / -2.84% |
| a3-qwen36-tp2-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.171 / 1.170 | 1.133 / 1.133 | -3.18% / -3.14% |
| a3-qwen36-tp2-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.637 / 0.464 | 0.619 / 0.448 | -2.83% / -3.50% |
| a3-qwen36-tp2-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.489 / 0.489 | 0.495 / 0.495 | +1.27% / +1.27% |
| a3-qwen36-tp2-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.662 / 1.663 | 1.617 / 1.617 | -2.73% / -2.76% |
| a3-qwen36-tp2-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.782 / 0.493 | 0.775 / 0.495 | -0.86% / +0.34% |
| a3-qwen36-tp2-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.520 / 0.519 | 0.535 / 0.535 | +2.84% / +3.06% |
| a3-qwen36-tp2-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.959 / 1.960 | 1.928 / 1.928 | -1.57% / -1.62% |
| a3-qwen36-tp2-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.880 / 0.522 | 0.883 / 0.535 | +0.38% / +2.47% |
| a3-qwen36-tp2-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.602 / 0.601 | 0.615 / 0.615 | +2.18% / +2.28% |
| a3-qwen36-tp2-decode-c12-p24512 | 12 / 4 | gqa | 16 | 1.056 / 1.056 | 1.133 / 1.133 | +7.25% / +7.27% |
| a3-qwen36-tp2-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.716 / 0.603 | 0.745 / 0.615 | +4.05% / +2.06% |
| a3-qwen36-tp2-decode-c12-p64512 | 12 / 4 | gdn | 48 | 0.601 / 0.600 | 0.615 / 0.615 | +2.32% / +2.58% |
| a3-qwen36-tp2-decode-c12-p64512 | 12 / 4 | gqa | 16 | 2.170 / 2.170 | 2.257 / 2.257 | +4.02% / +4.02% |
| a3-qwen36-tp2-decode-c12-p64512 | 12 / 4 | dense_layer | 64 | 0.993 / 0.604 | 1.026 / 0.615 | +3.25% / +1.88% |
| a3-qwen36-tp2-decode-c12-p8512 | 12 / 4 | gdn | 48 | 0.602 / 0.601 | 0.615 / 0.615 | +2.22% / +2.40% |
| a3-qwen36-tp2-decode-c12-p8512 | 12 / 4 | gqa | 16 | 0.687 / 0.686 | 0.683 / 0.683 | -0.52% / -0.41% |
| a3-qwen36-tp2-decode-c12-p8512 | 12 / 4 | dense_layer | 64 | 0.623 / 0.603 | 0.632 / 0.615 | +1.46% / +2.07% |
| a3-qwen36-tp2-decode-c24-p24512 | 24 / 4 | gdn | 48 | 0.797 / 0.797 | 0.790 / 0.790 | -0.87% / -0.88% |
| a3-qwen36-tp2-decode-c24-p24512 | 24 / 4 | gqa | 16 | 1.410 / 1.407 | 1.427 / 1.427 | +1.22% / +1.44% |
| a3-qwen36-tp2-decode-c24-p24512 | 24 / 4 | dense_layer | 64 | 0.950 / 0.798 | 0.949 / 0.790 | -0.09% / -0.99% |
| a3-qwen36-tp2-decode-c24-p64512 | 24 / 4 | gdn | 48 | 0.796 / 0.796 | 0.790 / 0.790 | -0.79% / -0.76% |
| a3-qwen36-tp2-decode-c24-p64512 | 24 / 4 | gqa | 16 | 3.052 / 3.053 | 3.226 / 3.226 | +5.69% / +5.68% |
| a3-qwen36-tp2-decode-c24-p64512 | 24 / 4 | dense_layer | 64 | 1.360 / 0.797 | 1.399 / 0.790 | +2.85% / -0.94% |
| a3-qwen36-tp2-decode-c24-p8512 | 24 / 4 | gdn | 48 | 0.796 / 0.796 | 0.790 / 0.790 | -0.86% / -0.82% |
| a3-qwen36-tp2-decode-c24-p8512 | 24 / 4 | gqa | 16 | 0.868 / 0.868 | 0.811 / 0.811 | -6.52% / -6.53% |
| a3-qwen36-tp2-decode-c24-p8512 | 24 / 4 | dense_layer | 64 | 0.814 / 0.798 | 0.795 / 0.790 | -2.37% / -1.02% |
| a3-qwen36-tp2-decode-c2-p24512 | 2 / 4 | gdn | 48 | 0.410 / 0.409 | 0.401 / 0.401 | -2.24% / -1.93% |
| a3-qwen36-tp2-decode-c2-p24512 | 2 / 4 | gqa | 16 | 0.436 / 0.436 | 0.414 / 0.414 | -5.07% / -4.90% |
| a3-qwen36-tp2-decode-c2-p24512 | 2 / 4 | dense_layer | 64 | 0.417 / 0.412 | 0.404 / 0.401 | -2.98% / -2.63% |
| a3-qwen36-tp2-decode-c2-p24512 | 1 / 4 | gdn | 48 | 0.371 / 0.369 | 0.378 / 0.378 | +1.95% / +2.38% |
| a3-qwen36-tp2-decode-c2-p24512 | 1 / 4 | gqa | 16 | 0.390 / 0.391 | 0.375 / 0.375 | -3.99% / -4.23% |
| a3-qwen36-tp2-decode-c2-p24512 | 1 / 4 | dense_layer | 64 | 0.376 / 0.372 | 0.377 / 0.378 | +0.41% / +1.68% |
| a3-qwen36-tp2-decode-c2-p64512 | 2 / 4 | gdn | 48 | 0.407 / 0.406 | 0.401 / 0.401 | -1.43% / -1.24% |
| a3-qwen36-tp2-decode-c2-p64512 | 2 / 4 | gqa | 16 | 0.581 / 0.580 | 0.544 / 0.544 | -6.25% / -6.22% |
| a3-qwen36-tp2-decode-c2-p64512 | 2 / 4 | dense_layer | 64 | 0.450 / 0.408 | 0.437 / 0.401 | -2.98% / -1.68% |
| a3-qwen36-tp2-decode-c2-p64512 | 1 / 4 | gdn | 48 | 0.371 / 0.369 | 0.378 / 0.378 | +1.73% / +2.39% |
| a3-qwen36-tp2-decode-c2-p64512 | 1 / 4 | gqa | 16 | 0.481 / 0.480 | 0.455 / 0.455 | -5.43% / -5.27% |
| a3-qwen36-tp2-decode-c2-p64512 | 1 / 4 | dense_layer | 64 | 0.399 / 0.373 | 0.397 / 0.378 | -0.43% / +1.32% |
| a3-qwen36-tp2-decode-c2-p8512 | 2 / 4 | gdn | 48 | 0.409 / 0.408 | 0.401 / 0.401 | -1.89% / -1.60% |
| a3-qwen36-tp2-decode-c2-p8512 | 2 / 4 | gqa | 16 | 0.384 / 0.379 | 0.362 / 0.362 | -5.56% / -4.48% |
| a3-qwen36-tp2-decode-c2-p8512 | 2 / 4 | dense_layer | 64 | 0.403 / 0.407 | 0.391 / 0.401 | -2.76% / -1.34% |
| a3-qwen36-tp2-decode-c2-p8512 | 1 / 4 | gdn | 48 | 0.380 / 0.369 | 0.378 / 0.378 | -0.49% / +2.43% |
| a3-qwen36-tp2-decode-c2-p8512 | 1 / 4 | gqa | 16 | 0.351 / 0.350 | 0.343 / 0.343 | -2.50% / -2.16% |
| a3-qwen36-tp2-decode-c2-p8512 | 1 / 4 | dense_layer | 64 | 0.373 / 0.366 | 0.369 / 0.378 | -0.96% / +3.26% |
| a3-qwen36-tp2-decode-c2-p96512 | 2 / 4 | gdn | 48 | 0.404 / 0.403 | 0.401 / 0.401 | -0.73% / -0.56% |
| a3-qwen36-tp2-decode-c2-p96512 | 2 / 4 | gqa | 16 | 0.674 / 0.673 | 0.648 / 0.648 | -3.78% / -3.73% |
| a3-qwen36-tp2-decode-c2-p96512 | 2 / 4 | dense_layer | 64 | 0.472 / 0.407 | 0.463 / 0.401 | -1.82% / -1.46% |
| a3-qwen36-tp2-decode-c2-p96512 | 1 / 4 | gdn | 48 | 0.367 / 0.367 | 0.378 / 0.378 | +2.86% / +3.00% |
| a3-qwen36-tp2-decode-c2-p96512 | 1 / 4 | gqa | 16 | 0.549 / 0.549 | 0.519 / 0.519 | -5.46% / -5.51% |
| a3-qwen36-tp2-decode-c2-p96512 | 1 / 4 | dense_layer | 64 | 0.413 / 0.369 | 0.413 / 0.378 | +0.09% / +2.29% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | gdn | 48 | 0.492 / 0.490 | 0.495 / 0.495 | +0.57% / +0.92% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | gqa | 16 | 0.628 / 0.628 | 0.643 / 0.643 | +2.30% / +2.43% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | dense_layer | 64 | 0.526 / 0.494 | 0.532 / 0.495 | +1.09% / +0.17% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | gdn | 48 | 0.474 / 0.473 | 0.495 / 0.495 | +4.32% / +4.71% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | gqa | 16 | 0.586 / 0.586 | 0.643 / 0.643 | +9.60% / +9.64% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | dense_layer | 64 | 0.502 / 0.477 | 0.532 / 0.495 | +5.86% / +3.80% |
| a3-qwen36-tp2-decode-c6-p24512 | 2 / 4 | gdn | 48 | 0.410 / 0.408 | 0.401 / 0.401 | -2.07% / -1.80% |
| a3-qwen36-tp2-decode-c6-p24512 | 2 / 4 | gqa | 16 | 0.432 / 0.430 | 0.414 / 0.414 | -3.99% / -3.75% |
| a3-qwen36-tp2-decode-c6-p24512 | 2 / 4 | dense_layer | 64 | 0.415 / 0.412 | 0.404 / 0.401 | -2.57% / -2.66% |
| a3-qwen36-tp2-decode-c6-p24512 | 3 / 4 | gdn | 48 | 0.425 / 0.424 | 0.424 / 0.424 | -0.16% / +0.07% |
| a3-qwen36-tp2-decode-c6-p24512 | 3 / 4 | gqa | 16 | 0.490 / 0.490 | 0.497 / 0.497 | +1.50% / +1.46% |
| a3-qwen36-tp2-decode-c6-p24512 | 3 / 4 | dense_layer | 64 | 0.441 / 0.428 | 0.443 / 0.424 | +0.30% / -0.85% |
| a3-qwen36-tp2-decode-c6-p24512 | 1 / 4 | gdn | 48 | 0.370 / 0.369 | 0.378 / 0.378 | +2.12% / +2.55% |
| a3-qwen36-tp2-decode-c6-p24512 | 1 / 4 | gqa | 16 | 0.392 / 0.393 | 0.375 / 0.375 | -4.48% / -4.54% |
| a3-qwen36-tp2-decode-c6-p24512 | 1 / 4 | dense_layer | 64 | 0.376 / 0.371 | 0.377 / 0.378 | +0.39% / +1.77% |
| a3-qwen36-tp2-decode-c6-p64512 | 6 / 4 | gdn | 48 | 0.487 / 0.488 | 0.495 / 0.495 | +1.57% / +1.44% |
| a3-qwen36-tp2-decode-c6-p64512 | 6 / 4 | gqa | 16 | 1.018 / 1.013 | 1.027 / 1.027 | +0.90% / +1.32% |
| a3-qwen36-tp2-decode-c6-p64512 | 6 / 4 | dense_layer | 64 | 0.620 / 0.489 | 0.628 / 0.495 | +1.30% / +1.17% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | gdn | 48 | 0.493 / 0.491 | 0.495 / 0.495 | +0.34% / +0.85% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | gqa | 16 | 0.519 / 0.520 | 0.489 / 0.489 | -5.79% / -5.87% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | dense_layer | 64 | 0.500 / 0.494 | 0.493 / 0.495 | -1.25% / +0.20% |
| a3-qwen36-tp2-decode-c6-p8512 | 2 / 4 | gdn | 48 | 0.408 / 0.406 | 0.401 / 0.401 | -1.72% / -1.27% |
| a3-qwen36-tp2-decode-c6-p8512 | 2 / 4 | gqa | 16 | 0.376 / 0.375 | 0.362 / 0.362 | -3.70% / -3.50% |
| a3-qwen36-tp2-decode-c6-p8512 | 2 / 4 | dense_layer | 64 | 0.400 / 0.405 | 0.391 / 0.401 | -2.18% / -0.99% |
| a3-qwen36-tp2-decode-c6-p8512 | 4 / 4 | gdn | 48 | 0.459 / 0.457 | 0.448 / 0.448 | -2.49% / -2.14% |
| a3-qwen36-tp2-decode-c6-p8512 | 4 / 4 | gqa | 16 | 0.437 / 0.435 | 0.411 / 0.411 | -5.93% / -5.58% |
| a3-qwen36-tp2-decode-c6-p8512 | 4 / 4 | dense_layer | 64 | 0.454 / 0.455 | 0.438 / 0.448 | -3.32% / -1.51% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | gdn | 48 | 0.474 / 0.473 | 0.495 / 0.495 | +4.45% / +4.71% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | gqa | 16 | 0.514 / 0.516 | 0.489 / 0.489 | -4.91% / -5.24% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | dense_layer | 64 | 0.484 / 0.476 | 0.493 / 0.495 | +1.96% / +3.92% |
| a3-qwen36-tp2-decode-c6-p8512 | 3 / 4 | gdn | 48 | 0.423 / 0.424 | 0.424 / 0.424 | +0.25% / +0.17% |
| a3-qwen36-tp2-decode-c6-p8512 | 3 / 4 | gqa | 16 | 0.413 / 0.413 | 0.399 / 0.399 | -3.39% / -3.44% |
| a3-qwen36-tp2-decode-c6-p8512 | 3 / 4 | dense_layer | 64 | 0.421 / 0.420 | 0.418 / 0.424 | -0.65% / +1.15% |
| a3-qwen36-tp2-decode-c6-p96512 | 6 / 4 | gdn | 48 | 0.487 / 0.488 | 0.495 / 0.495 | +1.54% / +1.47% |
| a3-qwen36-tp2-decode-c6-p96512 | 6 / 4 | gqa | 16 | 1.317 / 1.318 | 1.334 / 1.334 | +1.29% / +1.24% |
| a3-qwen36-tp2-decode-c6-p96512 | 6 / 4 | dense_layer | 64 | 0.695 / 0.491 | 0.705 / 0.495 | +1.42% / +0.74% |
| a3-qwen36-tp4-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.279 / 0.276 | 0.280 / 0.280 | +0.30% / +1.36% |
| a3-qwen36-tp4-decode-c1-p126000 | 1 / 4 | gqa | 16 | 0.390 / 0.389 | 0.378 / 0.378 | -3.13% / -2.97% |
| a3-qwen36-tp4-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.307 / 0.280 | 0.305 / 0.280 | -0.79% / +0.11% |
| a3-qwen36-tp4-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.437 / 0.436 | 0.428 / 0.428 | -2.12% / -1.97% |
| a3-qwen36-tp4-decode-c12-p126000 | 12 / 4 | gqa | 16 | 1.454 / 1.453 | 1.396 / 1.396 | -3.99% / -3.97% |
| a3-qwen36-tp4-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 0.691 / 0.439 | 0.670 / 0.428 | -3.10% / -2.53% |
| a3-qwen36-tp4-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.482 / 0.480 | 0.480 / 0.480 | -0.43% / -0.04% |
| a3-qwen36-tp4-decode-c16-p126000 | 16 / 4 | gqa | 16 | 1.801 / 1.801 | 1.759 / 1.759 | -2.35% / -2.35% |
| a3-qwen36-tp4-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 0.812 / 0.483 | 0.800 / 0.480 | -1.49% / -0.60% |
| a3-qwen36-tp4-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.294 / 0.292 | 0.295 / 0.295 | +0.35% / +1.14% |
| a3-qwen36-tp4-decode-c2-p126000 | 2 / 4 | gqa | 16 | 0.482 / 0.474 | 0.457 / 0.457 | -5.28% / -3.73% |
| a3-qwen36-tp4-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.341 / 0.295 | 0.335 / 0.295 | -1.64% / +0.08% |
| a3-qwen36-tp4-decode-c24-p126000 | 24 / 4 | gdn | 48 | 0.551 / 0.550 | 0.586 / 0.586 | +6.47% / +6.52% |
| a3-qwen36-tp4-decode-c24-p126000 | 24 / 4 | gqa | 16 | 3.910 / 3.910 | 3.918 / 3.918 | +0.20% / +0.21% |
| a3-qwen36-tp4-decode-c24-p126000 | 24 / 4 | dense_layer | 64 | 1.390 / 0.553 | 1.419 / 0.586 | +2.07% / +6.03% |
| a3-qwen36-tp4-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.334 / 0.331 | 0.325 / 0.325 | -2.61% / -1.78% |
| a3-qwen36-tp4-decode-c4-p126000 | 4 / 4 | gqa | 16 | 0.682 / 0.675 | 0.653 / 0.653 | -4.26% / -3.23% |
| a3-qwen36-tp4-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.421 / 0.336 | 0.407 / 0.325 | -3.28% / -3.20% |
| a3-qwen36-tp4-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.364 / 0.362 | 0.349 / 0.349 | -4.23% / -3.74% |
| a3-qwen36-tp4-decode-c6-p126000 | 6 / 4 | gqa | 16 | 0.907 / 0.902 | 0.841 / 0.841 | -7.27% / -6.76% |
| a3-qwen36-tp4-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.500 / 0.366 | 0.472 / 0.349 | -5.61% / -4.77% |
| a3-qwen36-tp4-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.397 / 0.397 | 0.375 / 0.375 | -5.57% / -5.43% |
| a3-qwen36-tp4-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.092 / 1.092 | 1.044 / 1.044 | -4.40% / -4.35% |
| a3-qwen36-tp4-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.571 / 0.398 | 0.542 / 0.375 | -5.01% / -5.77% |
| a3-qwen38-tp2-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.369 / 0.369 | 0.378 / 0.378 | +2.36% / +2.41% |
| a3-qwen38-tp2-decode-c1-p126000 | 1 / 4 | gqa | 16 | 0.611 / 0.607 | 0.578 / 0.578 | -5.38% / -4.90% |
| a3-qwen38-tp2-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.430 / 0.371 | 0.428 / 0.378 | -0.39% / +1.82% |
| a3-qwen38-tp2-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.600 / 0.599 | 0.615 / 0.615 | +2.58% / +2.65% |
| a3-qwen38-tp2-decode-c12-p126000 | 12 / 4 | gqa | 16 | 4.025 / 4.010 | 3.985 / 3.985 | -1.00% / -0.62% |
| a3-qwen38-tp2-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 1.456 / 0.601 | 1.458 / 0.615 | +0.11% / +2.34% |
| a3-qwen38-tp2-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.661 / 0.661 | 0.695 / 0.695 | +5.20% / +5.17% |
| a3-qwen38-tp2-decode-c16-p126000 | 16 / 4 | gqa | 16 | 4.030 / 4.029 | 4.020 / 4.020 | -0.25% / -0.22% |
| a3-qwen38-tp2-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 1.503 / 0.663 | 1.527 / 0.695 | +1.55% / +4.85% |
| a3-qwen38-tp2-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.408 / 0.407 | 0.401 / 0.401 | -1.69% / -1.51% |
| a3-qwen38-tp2-decode-c2-p126000 | 2 / 4 | gqa | 16 | 0.780 / 0.778 | 0.744 / 0.744 | -4.59% / -4.34% |
| a3-qwen38-tp2-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.501 / 0.410 | 0.487 / 0.401 | -2.82% / -2.12% |
| a3-qwen38-tp2-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.454 / 0.454 | 0.448 / 0.448 | -1.39% / -1.34% |
| a3-qwen38-tp2-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.168 / 1.166 | 1.133 / 1.133 | -2.95% / -2.82% |
| a3-qwen38-tp2-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.632 / 0.458 | 0.619 / 0.448 | -2.11% / -2.26% |
| a3-qwen38-tp2-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.490 / 0.491 | 0.495 / 0.495 | +1.00% / +0.75% |
| a3-qwen38-tp2-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.669 / 1.669 | 1.617 / 1.617 | -3.12% / -3.10% |
| a3-qwen38-tp2-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.785 / 0.495 | 0.775 / 0.495 | -1.19% / -0.05% |
| a3-qwen38-tp2-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.519 / 0.519 | 0.535 / 0.535 | +2.99% / +3.06% |
| a3-qwen38-tp2-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.962 / 1.962 | 1.928 / 1.928 | -1.72% / -1.71% |
| a3-qwen38-tp2-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.880 / 0.523 | 0.883 / 0.535 | +0.37% / +2.38% |
| a3-qwen38-tp4-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.280 / 0.277 | 0.280 / 0.280 | +0.04% / +1.16% |
| a3-qwen38-tp4-decode-c1-p126000 | 1 / 4 | gqa | 16 | 0.400 / 0.391 | 0.378 / 0.378 | -5.61% / -3.41% |
| a3-qwen38-tp4-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.310 / 0.279 | 0.305 / 0.280 | -1.78% / +0.47% |
| a3-qwen38-tp4-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.438 / 0.436 | 0.428 / 0.428 | -2.30% / -1.91% |
| a3-qwen38-tp4-decode-c12-p126000 | 12 / 4 | gqa | 16 | 1.453 / 1.452 | 1.396 / 1.396 | -3.98% / -3.92% |
| a3-qwen38-tp4-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 0.692 / 0.438 | 0.670 / 0.428 | -3.18% / -2.36% |
| a3-qwen38-tp4-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.478 / 0.477 | 0.480 / 0.480 | +0.40% / +0.60% |
| a3-qwen38-tp4-decode-c16-p126000 | 16 / 4 | gqa | 16 | 1.800 / 1.800 | 1.759 / 1.759 | -2.30% / -2.31% |
| a3-qwen38-tp4-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 0.809 / 0.481 | 0.800 / 0.480 | -1.11% / -0.25% |
| a3-qwen38-tp4-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.295 / 0.292 | 0.295 / 0.295 | +0.10% / +1.07% |
| a3-qwen38-tp4-decode-c2-p126000 | 2 / 4 | gqa | 16 | 0.476 / 0.475 | 0.457 / 0.457 | -4.13% / -3.77% |
| a3-qwen38-tp4-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.340 / 0.296 | 0.335 / 0.295 | -1.38% / -0.28% |
| a3-qwen38-tp4-decode-c24-p126000 | 24 / 4 | gdn | 48 | 0.554 / 0.553 | 0.586 / 0.586 | +5.92% / +6.02% |
| a3-qwen38-tp4-decode-c24-p126000 | 24 / 4 | gqa | 16 | 3.899 / 3.896 | 3.918 / 3.918 | +0.50% / +0.57% |
| a3-qwen38-tp4-decode-c24-p126000 | 24 / 4 | dense_layer | 64 | 1.390 / 0.555 | 1.419 / 0.586 | +2.12% / +5.69% |
| a3-qwen38-tp4-decode-c32-p126000 | 32 / 4 | gdn | 48 | 0.623 / 0.623 | 0.664 / 0.664 | +6.55% / +6.62% |
| a3-qwen38-tp4-decode-c32-p126000 | 32 / 4 | gqa | 16 | 3.962 / 3.964 | 3.965 / 3.965 | +0.07% / +0.04% |
| a3-qwen38-tp4-decode-c32-p126000 | 32 / 4 | dense_layer | 64 | 1.458 / 0.624 | 1.489 / 0.664 | +2.15% / +6.43% |
| a3-qwen38-tp4-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.332 / 0.331 | 0.325 / 0.325 | -2.25% / -1.72% |
| a3-qwen38-tp4-decode-c4-p126000 | 4 / 4 | gqa | 16 | 0.676 / 0.675 | 0.653 / 0.653 | -3.38% / -3.23% |
| a3-qwen38-tp4-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.418 / 0.335 | 0.407 / 0.325 | -2.71% / -2.89% |
| a3-qwen38-tp4-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.364 / 0.363 | 0.349 / 0.349 | -4.09% / -3.87% |
| a3-qwen38-tp4-decode-c6-p126000 | 6 / 4 | gqa | 16 | 0.906 / 0.907 | 0.841 / 0.841 | -7.14% / -7.25% |
| a3-qwen38-tp4-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.499 / 0.366 | 0.472 / 0.349 | -5.47% / -4.65% |
| a3-qwen38-tp4-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.396 / 0.394 | 0.375 / 0.375 | -5.22% / -4.88% |
| a3-qwen38-tp4-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.089 / 1.088 | 1.044 / 1.044 | -4.11% / -4.00% |
| a3-qwen38-tp4-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.569 / 0.396 | 0.542 / 0.375 | -4.68% / -5.38% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.444 / 0.444 | 0.428 / 0.428 | -3.66% / -3.66% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gqa | 16 | 0.598 / 0.597 | 0.574 / 0.574 | -4.04% / -3.92% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.482 / 0.447 | 0.464 / 0.428 | -3.78% / -4.28% |
| a3-qwen38-tp4-decode-c12-p24512 | 1 / 4 | gdn | 48 | 0.277 / 0.275 | 0.280 / 0.280 | +1.16% / +2.00% |
| a3-qwen38-tp4-decode-c12-p24512 | 1 / 4 | gqa | 16 | 0.283 / 0.283 | 0.277 / 0.277 | -2.12% / -2.13% |
| a3-qwen38-tp4-decode-c12-p24512 | 1 / 4 | dense_layer | 64 | 0.278 / 0.276 | 0.279 / 0.280 | +0.32% / +1.61% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.424 / 0.425 | 0.428 / 0.428 | +0.72% / +0.57% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gqa | 16 | 0.565 / 0.565 | 0.574 / 0.574 | +1.59% / +1.50% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.459 / 0.427 | 0.464 / 0.428 | +0.99% / +0.11% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.441 / 0.442 | 0.428 / 0.428 | -3.14% / -3.35% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gqa | 16 | 0.566 / 0.564 | 0.574 / 0.574 | +1.38% / +1.64% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.472 / 0.444 | 0.464 / 0.428 | -1.79% / -3.76% |
| a3-qwen38-tp4-decode-c12-p24512 | 2 / 4 | gdn | 48 | 0.294 / 0.291 | 0.295 / 0.295 | +0.45% / +1.21% |
| a3-qwen38-tp4-decode-c12-p24512 | 2 / 4 | gqa | 16 | 0.320 / 0.320 | 0.304 / 0.304 | -4.88% / -4.87% |
| a3-qwen38-tp4-decode-c12-p24512 | 2 / 4 | dense_layer | 64 | 0.300 / 0.294 | 0.297 / 0.295 | -0.97% / +0.35% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.423 / 0.423 | 0.428 / 0.428 | +1.01% / +0.97% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gqa | 16 | 0.526 / 0.526 | 0.574 / 0.574 | +9.00% / +9.12% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.449 / 0.426 | 0.464 / 0.428 | +3.35% / +0.42% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | gdn | 48 | 0.372 / 0.366 | 0.349 / 0.349 | -6.20% / -4.67% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | gqa | 16 | 0.440 / 0.439 | 0.410 / 0.410 | -6.90% / -6.68% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | dense_layer | 64 | 0.389 / 0.368 | 0.364 / 0.349 | -6.40% / -5.18% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | gdn | 48 | 0.363 / 0.363 | 0.349 / 0.349 | -3.87% / -3.82% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | gqa | 16 | 0.427 / 0.425 | 0.410 / 0.410 | -4.03% / -3.62% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | dense_layer | 64 | 0.379 / 0.365 | 0.364 / 0.349 | -3.91% / -4.31% |
| a3-qwen38-tp4-decode-c12-p24512 | 3 / 4 | gdn | 48 | 0.304 / 0.304 | 0.310 / 0.310 | +2.03% / +2.07% |
| a3-qwen38-tp4-decode-c12-p24512 | 3 / 4 | gqa | 16 | 0.342 / 0.344 | 0.336 / 0.336 | -1.71% / -2.10% |
| a3-qwen38-tp4-decode-c12-p24512 | 3 / 4 | dense_layer | 64 | 0.313 / 0.306 | 0.317 / 0.310 | +1.01% / +1.23% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gdn | 48 | 0.443 / 0.443 | 0.428 / 0.428 | -3.45% / -3.39% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gqa | 16 | 0.909 / 0.908 | 0.898 / 0.898 | -1.28% / -1.20% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | dense_layer | 64 | 0.559 / 0.445 | 0.545 / 0.428 | -2.57% / -3.95% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gdn | 48 | 0.425 / 0.425 | 0.428 / 0.428 | +0.53% / +0.66% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gqa | 16 | 0.733 / 0.734 | 0.898 / 0.898 | +22.53% / +22.26% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | dense_layer | 64 | 0.502 / 0.426 | 0.545 / 0.428 | +8.55% / +0.25% |
| a3-qwen38-tp4-decode-c12-p64512 | 8 / 4 | gdn | 48 | 0.416 / 0.401 | 0.375 / 0.375 | -9.74% / -6.35% |
| a3-qwen38-tp4-decode-c12-p64512 | 8 / 4 | gqa | 16 | 0.695 / 0.694 | 0.697 / 0.697 | +0.23% / +0.40% |
| a3-qwen38-tp4-decode-c12-p64512 | 8 / 4 | dense_layer | 64 | 0.485 / 0.403 | 0.456 / 0.375 | -6.17% / -6.84% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gdn | 48 | 0.441 / 0.441 | 0.428 / 0.428 | -3.12% / -2.94% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gqa | 16 | 0.843 / 0.843 | 0.898 / 0.898 | +6.50% / +6.49% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | dense_layer | 64 | 0.542 / 0.444 | 0.545 / 0.428 | +0.62% / -3.62% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gdn | 48 | 0.442 / 0.442 | 0.428 / 0.428 | -3.26% / -3.32% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gqa | 16 | 1.158 / 1.157 | 1.157 / 1.157 | -0.10% / -0.03% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | dense_layer | 64 | 0.621 / 0.445 | 0.610 / 0.428 | -1.79% / -3.86% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gdn | 48 | 0.424 / 0.423 | 0.428 / 0.428 | +0.95% / +1.12% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gqa | 16 | 0.938 / 0.936 | 1.157 / 1.157 | +23.33% / +23.56% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | dense_layer | 64 | 0.552 / 0.425 | 0.610 / 0.428 | +10.45% / +0.49% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gdn | 48 | 0.440 / 0.441 | 0.428 / 0.428 | -2.90% / -3.14% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gqa | 16 | 1.067 / 1.066 | 1.157 / 1.157 | +8.38% / +8.46% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | dense_layer | 64 | 0.597 / 0.443 | 0.610 / 0.428 | +2.14% / -3.49% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gdn | 48 | 0.424 / 0.424 | 0.428 / 0.428 | +0.84% / +0.78% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gqa | 16 | 1.098 / 1.100 | 1.157 / 1.157 | +5.30% / +5.18% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | dense_layer | 64 | 0.593 / 0.427 | 0.610 / 0.428 | +2.91% / +0.12% |
| a3-qwen38-tp4-decode-c24-p24512 | 24 / 4 | gdn | 48 | 0.556 / 0.555 | 0.586 / 0.586 | +5.38% / +5.58% |
| a3-qwen38-tp4-decode-c24-p24512 | 24 / 4 | gqa | 16 | 1.055 / 1.056 | 1.101 / 1.101 | +4.37% / +4.31% |
| a3-qwen38-tp4-decode-c24-p24512 | 24 / 4 | dense_layer | 64 | 0.681 / 0.557 | 0.715 / 0.586 | +4.99% / +5.29% |
| a3-qwen38-tp4-decode-c24-p64512 | 24 / 4 | gdn | 48 | 0.556 / 0.555 | 0.586 / 0.586 | +5.51% / +5.54% |
| a3-qwen38-tp4-decode-c24-p64512 | 24 / 4 | gqa | 16 | 2.088 / 2.087 | 2.212 / 2.212 | +5.93% / +5.96% |
| a3-qwen38-tp4-decode-c24-p64512 | 24 / 4 | dense_layer | 64 | 0.939 / 0.556 | 0.993 / 0.586 | +5.75% / +5.43% |
| a3-qwen38-tp4-decode-c24-p96512 | 24 / 4 | gdn | 48 | 0.555 / 0.554 | 0.586 / 0.586 | +5.72% / +5.77% |
| a3-qwen38-tp4-decode-c24-p96512 | 24 / 4 | gqa | 16 | 3.031 / 3.033 | 3.100 / 3.100 | +2.26% / +2.19% |
| a3-qwen38-tp4-decode-c24-p96512 | 24 / 4 | dense_layer | 64 | 1.174 / 0.556 | 1.215 / 0.586 | +3.48% / +5.52% |
| a3-qwen38-tp4-decode-c2-p24512 | 2 / 4 | gdn | 48 | 0.294 / 0.292 | 0.295 / 0.295 | +0.28% / +1.03% |
| a3-qwen38-tp4-decode-c2-p24512 | 2 / 4 | gqa | 16 | 0.327 / 0.321 | 0.304 / 0.304 | -7.00% / -5.22% |
| a3-qwen38-tp4-decode-c2-p24512 | 2 / 4 | dense_layer | 64 | 0.302 / 0.295 | 0.297 / 0.295 | -1.69% / +0.12% |
| a3-qwen38-tp4-decode-c2-p24512 | 1 / 4 | gdn | 48 | 0.276 / 0.275 | 0.280 / 0.280 | +1.42% / +1.82% |
| a3-qwen38-tp4-decode-c2-p24512 | 1 / 4 | gqa | 16 | 0.282 / 0.282 | 0.277 / 0.277 | -2.01% / -1.91% |
| a3-qwen38-tp4-decode-c2-p24512 | 1 / 4 | dense_layer | 64 | 0.278 / 0.276 | 0.279 / 0.280 | +0.55% / +1.42% |
| a3-qwen38-tp4-decode-c2-p64512 | 2 / 4 | gdn | 48 | 0.294 / 0.290 | 0.295 / 0.295 | +0.42% / +1.60% |
| a3-qwen38-tp4-decode-c2-p64512 | 2 / 4 | gqa | 16 | 0.379 / 0.377 | 0.364 / 0.364 | -3.85% / -3.45% |
| a3-qwen38-tp4-decode-c2-p64512 | 2 / 4 | dense_layer | 64 | 0.315 / 0.292 | 0.312 / 0.295 | -0.86% / +1.13% |
| a3-qwen38-tp4-decode-c2-p64512 | 1 / 4 | gdn | 48 | 0.273 / 0.273 | 0.280 / 0.280 | +2.50% / +2.70% |
| a3-qwen38-tp4-decode-c2-p64512 | 1 / 4 | gqa | 16 | 0.331 / 0.330 | 0.316 / 0.316 | -4.39% / -4.23% |
| a3-qwen38-tp4-decode-c2-p64512 | 1 / 4 | dense_layer | 64 | 0.288 / 0.275 | 0.289 / 0.280 | +0.52% / +1.88% |
| a3-qwen38-tp4-decode-c2-p96512 | 2 / 4 | gdn | 48 | 0.295 / 0.291 | 0.295 / 0.295 | +0.14% / +1.35% |
| a3-qwen38-tp4-decode-c2-p96512 | 2 / 4 | gqa | 16 | 0.425 / 0.425 | 0.412 / 0.412 | -3.00% / -2.99% |
| a3-qwen38-tp4-decode-c2-p96512 | 2 / 4 | dense_layer | 64 | 0.327 / 0.293 | 0.324 / 0.295 | -0.88% / +0.66% |
| a3-qwen38-tp4-decode-c2-p96512 | 1 / 4 | gdn | 48 | 0.275 / 0.274 | 0.280 / 0.280 | +1.98% / +2.38% |
| a3-qwen38-tp4-decode-c2-p96512 | 1 / 4 | gqa | 16 | 0.381 / 0.361 | 0.348 / 0.348 | -8.66% / -3.53% |
| a3-qwen38-tp4-decode-c2-p96512 | 1 / 4 | dense_layer | 64 | 0.301 / 0.275 | 0.297 / 0.280 | -1.39% / +1.76% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | gdn | 48 | 0.367 / 0.366 | 0.349 / 0.349 | -4.98% / -4.69% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | gqa | 16 | 0.443 / 0.442 | 0.410 / 0.410 | -7.61% / -7.32% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | dense_layer | 64 | 0.386 / 0.369 | 0.364 / 0.349 | -5.73% / -5.33% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | gdn | 48 | 0.364 / 0.363 | 0.349 / 0.349 | -4.02% / -3.81% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | gqa | 16 | 0.427 / 0.426 | 0.410 / 0.410 | -4.06% / -3.82% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | dense_layer | 64 | 0.379 / 0.365 | 0.364 / 0.349 | -4.03% / -4.34% |
| a3-qwen38-tp4-decode-c6-p24512 | 2 / 4 | gdn | 48 | 0.301 / 0.292 | 0.295 / 0.295 | -1.88% / +1.05% |
| a3-qwen38-tp4-decode-c6-p24512 | 2 / 4 | gqa | 16 | 0.320 / 0.319 | 0.304 / 0.304 | -4.82% / -4.45% |
| a3-qwen38-tp4-decode-c6-p24512 | 2 / 4 | dense_layer | 64 | 0.305 / 0.294 | 0.297 / 0.295 | -2.65% / +0.44% |
| a3-qwen38-tp4-decode-c6-p24512 | 1 / 4 | gdn | 48 | 0.276 / 0.275 | 0.280 / 0.280 | +1.49% / +2.05% |
| a3-qwen38-tp4-decode-c6-p24512 | 1 / 4 | gqa | 16 | 0.283 / 0.283 | 0.277 / 0.277 | -2.17% / -2.15% |
| a3-qwen38-tp4-decode-c6-p24512 | 1 / 4 | dense_layer | 64 | 0.278 / 0.276 | 0.279 / 0.280 | +0.56% / +1.34% |
| a3-qwen38-tp4-decode-c6-p24512 | 4 / 4 | gdn | 48 | 0.344 / 0.334 | 0.325 / 0.325 | -5.55% / -2.61% |
| a3-qwen38-tp4-decode-c6-p24512 | 4 / 4 | gqa | 16 | 0.372 / 0.371 | 0.363 / 0.363 | -2.55% / -2.32% |
| a3-qwen38-tp4-decode-c6-p24512 | 4 / 4 | dense_layer | 64 | 0.351 / 0.335 | 0.334 / 0.325 | -4.76% / -3.15% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | gdn | 48 | 0.367 / 0.366 | 0.349 / 0.349 | -5.03% / -4.78% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | gqa | 16 | 0.598 / 0.597 | 0.580 / 0.580 | -3.01% / -2.90% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | dense_layer | 64 | 0.425 / 0.369 | 0.407 / 0.349 | -4.32% / -5.35% |
| a3-qwen38-tp4-decode-c6-p64512 | 4 / 4 | gdn | 48 | 0.336 / 0.333 | 0.325 / 0.325 | -3.42% / -2.43% |
| a3-qwen38-tp4-decode-c6-p64512 | 4 / 4 | gqa | 16 | 0.485 / 0.485 | 0.477 / 0.477 | -1.74% / -1.74% |
| a3-qwen38-tp4-decode-c6-p64512 | 4 / 4 | dense_layer | 64 | 0.374 / 0.335 | 0.363 / 0.325 | -2.87% / -2.91% |
| a3-qwen38-tp4-decode-c6-p64512 | 3 / 4 | gdn | 48 | 0.323 / 0.304 | 0.310 / 0.310 | -4.17% / +2.07% |
| a3-qwen38-tp4-decode-c6-p64512 | 3 / 4 | gqa | 16 | 0.437 / 0.438 | 0.428 / 0.428 | -2.05% / -2.25% |
| a3-qwen38-tp4-decode-c6-p64512 | 3 / 4 | dense_layer | 64 | 0.352 / 0.304 | 0.340 / 0.310 | -3.51% / +1.80% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | gdn | 48 | 0.364 / 0.363 | 0.349 / 0.349 | -4.06% / -4.01% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | gqa | 16 | 0.563 / 0.561 | 0.580 / 0.580 | +2.99% / +3.28% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | dense_layer | 64 | 0.413 / 0.366 | 0.407 / 0.349 | -1.66% / -4.63% |
| a3-qwen38-tp4-decode-c6-p64512 | 2 / 4 | gdn | 48 | 0.299 / 0.289 | 0.295 / 0.295 | -1.30% / +2.08% |
| a3-qwen38-tp4-decode-c6-p64512 | 2 / 4 | gqa | 16 | 0.380 / 0.379 | 0.364 / 0.364 | -4.21% / -3.80% |
| a3-qwen38-tp4-decode-c6-p64512 | 2 / 4 | dense_layer | 64 | 0.319 / 0.290 | 0.312 / 0.295 | -2.17% / +1.57% |
| a3-qwen38-tp4-decode-c6-p64512 | 1 / 4 | gdn | 48 | 0.280 / 0.273 | 0.280 / 0.280 | -0.05% / +2.63% |
| a3-qwen38-tp4-decode-c6-p64512 | 1 / 4 | gqa | 16 | 0.330 / 0.331 | 0.316 / 0.316 | -4.07% / -4.31% |
| a3-qwen38-tp4-decode-c6-p64512 | 1 / 4 | dense_layer | 64 | 0.293 / 0.276 | 0.289 / 0.280 | -1.18% / +1.55% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | gdn | 48 | 0.368 / 0.366 | 0.349 / 0.349 | -5.18% / -4.68% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | gqa | 16 | 0.741 / 0.727 | 0.716 / 0.716 | -3.43% / -1.56% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | dense_layer | 64 | 0.461 / 0.367 | 0.441 / 0.349 | -4.48% / -5.05% |
| a3-qwen38-tp4-decode-c6-p96512 | 1 / 4 | gdn | 48 | 0.280 / 0.274 | 0.280 / 0.280 | +0.17% / +2.38% |
| a3-qwen38-tp4-decode-c6-p96512 | 1 / 4 | gqa | 16 | 0.360 / 0.360 | 0.348 / 0.348 | -3.28% / -3.37% |
| a3-qwen38-tp4-decode-c6-p96512 | 1 / 4 | dense_layer | 64 | 0.300 / 0.276 | 0.297 / 0.280 | -0.87% / +1.66% |
| a3-qwen38-tp4-decode-c6-p96512 | 3 / 4 | gdn | 48 | 0.307 / 0.305 | 0.310 / 0.310 | +0.98% / +1.77% |
| a3-qwen38-tp4-decode-c6-p96512 | 3 / 4 | gqa | 16 | 0.508 / 0.503 | 0.502 / 0.502 | -1.23% / -0.11% |
| a3-qwen38-tp4-decode-c6-p96512 | 3 / 4 | dense_layer | 64 | 0.357 / 0.307 | 0.358 / 0.310 | +0.20% / +1.02% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | gdn | 48 | 0.365 / 0.364 | 0.349 / 0.349 | -4.34% / -4.20% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | gqa | 16 | 0.675 / 0.673 | 0.716 / 0.716 | +6.07% / +6.25% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | dense_layer | 64 | 0.442 / 0.366 | 0.441 / 0.349 | -0.37% / -4.60% |
| a3-qwen38-tp4-decode-c6-p96512 | 2 / 4 | gdn | 48 | 0.294 / 0.291 | 0.295 / 0.295 | +0.30% / +1.25% |
| a3-qwen38-tp4-decode-c6-p96512 | 2 / 4 | gqa | 16 | 0.426 / 0.426 | 0.412 / 0.412 | -3.19% / -3.08% |
| a3-qwen38-tp4-decode-c6-p96512 | 2 / 4 | dense_layer | 64 | 0.327 / 0.293 | 0.324 / 0.295 | -0.84% / +0.74% |
| a3-qwen38-tp4-decode-c6-p96512 | 4 / 4 | gdn | 48 | 0.336 / 0.334 | 0.325 / 0.325 | -3.43% / -2.77% |
| a3-qwen38-tp4-decode-c6-p96512 | 4 / 4 | gqa | 16 | 0.584 / 0.585 | 0.569 / 0.569 | -2.67% / -2.77% |
| a3-qwen38-tp4-decode-c6-p96512 | 4 / 4 | dense_layer | 64 | 0.398 / 0.337 | 0.386 / 0.325 | -3.15% / -3.52% |
| a5-qwen36-tp2-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.198 / 0.193 | 0.187 / 0.187 | -5.56% / -3.39% |
| a5-qwen36-tp2-decode-c1-p126000 | 1 / 4 | gqa | 16 | 1.112 / 1.111 | 1.108 / 1.108 | -0.34% / -0.31% |
| a5-qwen36-tp2-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.426 / 0.197 | 0.417 / 0.187 | -2.16% / -5.02% |
| a5-qwen36-tp2-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.404 / 0.404 | 0.387 / 0.387 | -4.36% / -4.32% |
| a5-qwen36-tp2-decode-c12-p126000 | 12 / 4 | gqa | 16 | 1.254 / 1.253 | 1.202 / 1.202 | -4.15% / -4.14% |
| a5-qwen36-tp2-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 0.617 / 0.406 | 0.590 / 0.387 | -4.26% / -4.69% |
| a5-qwen36-tp2-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.466 / 0.466 | 0.467 / 0.467 | +0.19% / +0.26% |
| a5-qwen36-tp2-decode-c16-p126000 | 16 / 4 | gqa | 16 | 1.290 / 1.290 | 1.296 / 1.296 | +0.52% / +0.49% |
| a5-qwen36-tp2-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 0.672 / 0.467 | 0.674 / 0.467 | +0.35% / +0.01% |
| a5-qwen36-tp2-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.221 / 0.217 | 0.205 / 0.205 | -6.90% / -5.42% |
| a5-qwen36-tp2-decode-c2-p126000 | 2 / 4 | gqa | 16 | 1.138 / 1.138 | 1.116 / 1.116 | -1.95% / -1.94% |
| a5-qwen36-tp2-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.450 / 0.221 | 0.433 / 0.205 | -3.77% / -7.00% |
| a5-qwen36-tp2-decode-c24-p126000 | 24 / 4 | gdn | 48 | 0.556 / 0.559 | 0.576 / 0.576 | +3.49% / +3.11% |
| a5-qwen36-tp2-decode-c24-p126000 | 24 / 4 | gqa | 16 | 2.320 / 2.320 | 2.355 / 2.355 | +1.50% / +1.50% |
| a5-qwen36-tp2-decode-c24-p126000 | 24 / 4 | dense_layer | 64 | 0.997 / 0.560 | 1.021 / 0.576 | +2.33% / +2.89% |
| a5-qwen36-tp2-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.261 / 0.258 | 0.245 / 0.245 | -5.89% / -4.98% |
| a5-qwen36-tp2-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.195 / 1.195 | 1.144 / 1.144 | -4.25% / -4.29% |
| a5-qwen36-tp2-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.494 / 0.261 | 0.470 / 0.245 | -4.90% / -5.99% |
| a5-qwen36-tp2-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.298 / 0.297 | 0.277 / 0.277 | -7.32% / -7.01% |
| a5-qwen36-tp2-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.287 / 1.288 | 1.207 / 1.207 | -6.25% / -6.28% |
| a5-qwen36-tp2-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.546 / 0.299 | 0.509 / 0.277 | -6.69% / -7.54% |
| a5-qwen36-tp2-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.336 / 0.336 | 0.312 / 0.312 | -7.07% / -7.04% |
| a5-qwen36-tp2-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.214 / 1.213 | 1.166 / 1.166 | -3.97% / -3.95% |
| a5-qwen36-tp2-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.555 / 0.337 | 0.526 / 0.312 | -5.38% / -7.29% |
| a5-qwen38-tp2-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.219 / 0.218 | 0.211 / 0.211 | -3.98% / -3.38% |
| a5-qwen38-tp2-decode-c1-p126000 | 1 / 4 | gqa | 16 | 1.117 / 1.117 | 1.102 / 1.102 | -1.30% / -1.32% |
| a5-qwen38-tp2-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.444 / 0.218 | 0.434 / 0.211 | -2.29% / -3.61% |
| a5-qwen38-tp2-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.430 / 0.432 | 0.413 / 0.413 | -3.83% / -4.41% |
| a5-qwen38-tp2-decode-c12-p126000 | 12 / 4 | gqa | 16 | 1.257 / 1.257 | 1.197 / 1.197 | -4.80% / -4.79% |
| a5-qwen38-tp2-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 0.637 / 0.434 | 0.609 / 0.413 | -4.30% / -4.67% |
| a5-qwen38-tp2-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.488 / 0.490 | 0.494 / 0.494 | +1.42% / +0.87% |
| a5-qwen38-tp2-decode-c16-p126000 | 16 / 4 | gqa | 16 | 1.318 / 1.317 | 1.292 / 1.292 | -1.96% / -1.92% |
| a5-qwen38-tp2-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 0.695 / 0.492 | 0.694 / 0.494 | -0.18% / +0.46% |
| a5-qwen38-tp2-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.243 / 0.242 | 0.229 / 0.229 | -5.66% / -5.18% |
| a5-qwen38-tp2-decode-c2-p126000 | 2 / 4 | gqa | 16 | 1.146 / 1.146 | 1.110 / 1.110 | -3.17% / -3.15% |
| a5-qwen38-tp2-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.469 / 0.242 | 0.449 / 0.229 | -4.14% / -5.43% |
| a5-qwen38-tp2-decode-c24-p126000 | 24 / 4 | gdn | 48 | 0.571 / 0.575 | 0.606 / 0.606 | +6.03% / +5.38% |
| a5-qwen38-tp2-decode-c24-p126000 | 24 / 4 | gqa | 16 | 2.312 / 2.312 | 2.351 / 2.351 | +1.69% / +1.68% |
| a5-qwen38-tp2-decode-c24-p126000 | 24 / 4 | dense_layer | 64 | 1.006 / 0.576 | 1.042 / 0.606 | +3.54% / +5.09% |
| a5-qwen38-tp2-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.283 / 0.282 | 0.270 / 0.270 | -4.59% / -4.44% |
| a5-qwen38-tp2-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.193 / 1.192 | 1.138 / 1.138 | -4.53% / -4.52% |
| a5-qwen38-tp2-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.510 / 0.283 | 0.487 / 0.270 | -4.56% / -4.69% |
| a5-qwen38-tp2-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.321 / 0.321 | 0.302 / 0.302 | -6.05% / -5.99% |
| a5-qwen38-tp2-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.289 / 1.289 | 1.201 / 1.201 | -6.81% / -6.79% |
| a5-qwen38-tp2-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.563 / 0.322 | 0.527 / 0.302 | -6.49% / -6.24% |
| a5-qwen38-tp2-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.359 / 0.361 | 0.338 / 0.338 | -5.89% / -6.40% |
| a5-qwen38-tp2-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.259 / 1.259 | 1.160 / 1.160 | -7.86% / -7.85% |
| a5-qwen38-tp2-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.584 / 0.362 | 0.543 / 0.338 | -6.95% / -6.78% |
| a5-qwen36-tp4-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.166 / 0.160 | 0.162 / 0.162 | -2.32% / +1.33% |
| a5-qwen36-tp4-decode-c1-p126000 | 1 / 4 | gqa | 16 | 1.099 / 1.099 | 1.091 / 1.091 | -0.72% / -0.72% |
| a5-qwen36-tp4-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.399 / 0.164 | 0.394 / 0.162 | -1.22% / -1.16% |
| a5-qwen36-tp4-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.197 / 0.191 | 0.190 / 0.190 | -3.31% / -0.67% |
| a5-qwen36-tp4-decode-c2-p126000 | 2 / 4 | gqa | 16 | 1.128 / 1.128 | 1.115 / 1.115 | -1.18% / -1.19% |
| a5-qwen36-tp4-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.429 / 0.195 | 0.421 / 0.190 | -1.91% / -2.67% |
| a5-qwen36-tp4-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.217 / 0.211 | 0.210 / 0.210 | -3.27% / -0.41% |
| a5-qwen36-tp4-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.155 / 1.155 | 1.132 / 1.132 | -2.03% / -2.01% |
| a5-qwen36-tp4-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.452 / 0.215 | 0.441 / 0.210 | -2.48% / -2.20% |
| a5-qwen36-tp4-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.236 / 0.232 | 0.223 / 0.223 | -5.41% / -3.79% |
| a5-qwen36-tp4-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.203 / 1.203 | 1.126 / 1.126 | -6.40% / -6.39% |
| a5-qwen36-tp4-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.477 / 0.235 | 0.449 / 0.223 | -6.04% / -5.00% |
| a5-qwen36-tp4-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.255 / 0.250 | 0.238 / 0.238 | -6.74% / -4.83% |
| a5-qwen36-tp4-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.211 / 1.211 | 1.131 / 1.131 | -6.53% / -6.56% |
| a5-qwen36-tp4-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.494 / 0.253 | 0.461 / 0.238 | -6.61% / -6.17% |
| a5-qwen38-tp4-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.172 / 0.168 | 0.171 / 0.171 | -0.71% / +1.40% |
| a5-qwen38-tp4-decode-c1-p126000 | 1 / 4 | gqa | 16 | 1.095 / 1.095 | 1.079 / 1.079 | -1.38% / -1.40% |
| a5-qwen38-tp4-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.402 / 0.173 | 0.398 / 0.171 | -1.16% / -1.44% |
| a5-qwen38-tp4-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.210 / 0.203 | 0.199 / 0.199 | -5.01% / -2.14% |
| a5-qwen38-tp4-decode-c2-p126000 | 2 / 4 | gqa | 16 | 1.127 / 1.127 | 1.103 / 1.103 | -2.17% / -2.17% |
| a5-qwen38-tp4-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.439 / 0.208 | 0.425 / 0.199 | -3.18% / -4.17% |
| a5-qwen38-tp4-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.226 / 0.223 | 0.220 / 0.220 | -2.51% / -1.42% |
| a5-qwen38-tp4-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.147 / 1.148 | 1.121 / 1.121 | -2.34% / -2.36% |
| a5-qwen38-tp4-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.456 / 0.225 | 0.445 / 0.220 | -2.41% / -2.26% |
| a5-qwen38-tp4-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.245 / 0.244 | 0.233 / 0.233 | -4.77% / -4.41% |
| a5-qwen38-tp4-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.198 / 1.198 | 1.115 / 1.115 | -6.93% / -6.93% |
| a5-qwen38-tp4-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.483 / 0.245 | 0.454 / 0.233 | -6.11% / -4.80% |
| a5-qwen38-tp4-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.261 / 0.260 | 0.249 / 0.249 | -4.68% / -4.31% |
| a5-qwen38-tp4-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.206 / 1.206 | 1.121 / 1.121 | -7.06% / -7.05% |
| a5-qwen38-tp4-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.497 / 0.261 | 0.467 / 0.249 | -6.12% / -4.73% |
| a3-v41-tp4dp4-decode-c4-p8512 | 1 / 8 | mla | 40 | 0.888 / 0.823 | 0.805 / 0.789 | -9.41% / -4.18% |
| a3-v41-tp4dp4-decode-c4-p8512 | 1 / 8 | moe_layer | 40 | 0.888 / 0.823 | 0.805 / 0.789 | -9.41% / -4.18% |
| a3-v41-tp4dp4-decode-c4-p8512 | 2 / 8 | mla | 40 | 1.201 / 1.130 | 1.258 / 1.240 | +4.78% / +9.74% |
| a3-v41-tp4dp4-decode-c4-p8512 | 2 / 8 | moe_layer | 40 | 1.201 / 1.130 | 1.258 / 1.240 | +4.78% / +9.74% |

Layer-group statistics summarize complete layer spans, not isolated attention or FFN kernel time. Group P50 is across layer means; steady-layer P50 remains the median of per-layer call P50 values in JSON. Full layer membership, extrema, stream details and alignment assumptions remain in the SHA256-pinned evidence.

Summary: {"compared": 280, "passed": 280, "requested_sources": 280, "sources": 280, "status_counts": {"compared": 280}}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
