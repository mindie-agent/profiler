# Current profiling validation

One canonical case registry and one recorded Sim package. Selected costs are freshly replayed; unchanged cases retain verified evidence from this same Sim package. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.

| Case | Phase | Calls | Real mean / P50 / P90 ms | Sim ms | Error | Status |
|---|---|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c4-livepre | decode | 46 | 29.762 / 29.664 / 30.046 | 30.314 | +1.86% | PASS |
| glm53flash-a3-tp16-c16-livepre | decode | 37 | 41.069 / 40.940 / 41.282 | 44.390 | +8.09% | PASS |
| glm53flash-a3-tp16-c2 | decode | 46 | 34.118 / 33.910 / 35.073 | 31.755 | -6.93% | PASS |
| glm53flash-a3-tp16-c4 | decode | 46 | 39.841 / 39.798 / 40.057 | 36.959 | -7.24% | PASS |
| glm53flash-a5-tp8-c3 | decode | 53 | 21.068 / 21.057 / 21.170 | 18.891 | -10.33% | PASS |
| glm53flash-a5-tp8-c96 | decode | 27 | 57.590 / 57.573 / 57.734 | 61.998 | +7.65% | PASS |
| glm53flash-a5-tp8-c1 | decode | 65 | 15.683 / 15.670 / 15.738 | 13.868 | -11.58% | PASS |
| a5_kimi_k3_p32768_c1 | decode | 63 | 32.555 / 32.533 / 32.674 | 28.561 | -12.27% | PASS |
| v4flash-a3-tp8-c4 | decode | 104 | 32.486 / 32.416 / 32.734 | 29.272 | -9.89% | PASS |
| v4flash-a3-tp8-c8 | decode | 104 | 37.763 / 37.868 / 38.082 | 34.707 | -8.09% | PASS |
| a3_glm53_dc4k_b1 | decode | 74 | 38.955 / 38.943 / 39.036 | 38.046 | -2.33% | PASS |
| a3_glm53_dc4k_b2 | decode | 70 | 40.970 / 40.935 / 41.046 | 39.767 | -2.94% | PASS |
| a3_glm53_dc4k_b4 | decode | 67 | 43.438 / 43.437 / 43.598 | 38.631 | -11.07% | PASS |
| a3_glm53_dc4k_b8 | decode | 61 | 47.113 / 47.149 / 47.402 | 44.125 | -6.34% | PASS |
| a3_glm53_dc16k_b1 | decode | 74 | 39.112 / 39.105 / 39.196 | 38.334 | -1.99% | PASS |
| qwen35-397b-a3-tp16-c48 | decode | 23 | 76.089 / 76.132 / 76.632 | 66.888 | -12.09% | PASS |
| qwen35-397b-a3-tp16-c136 | decode | 18 | 119.054 / 119.131 / 119.486 | 104.744 | -12.02% | PASS |
| qwen35-35b-a5-tp4-c64-graph | decode | 79 | 21.957 / 22.001 / 22.068 | 19.975 | -9.03% | PASS |
| qwen35-35b-a5-tp4-c128-graph | decode | 76 | 28.585 / 28.571 / 28.704 | 26.059 | -8.83% | PASS |
| qwen35-35b-a5-tp4-c4-graph | decode | 84 | 11.551 / 11.482 / 11.818 | 9.901 | -14.29% | PASS |
| qwen36-a5-tp2-c12 | decode | 55 | 24.226 / 24.053 / 24.711 | 21.480 | -11.33% | PASS |
| qwen36-a5-tp2-c96 | decode | 24 | 63.853 / 63.562 / 65.419 | 62.838 | -1.59% | PASS |
| qwen36-a5-tp2-c1 | decode | 85 | 12.318 / 12.279 / 12.362 | 10.719 | -12.98% | PASS |
| a3_glm53_w4a8_tp16_tpot30_c2 | decode | 44 | 57.639 / 57.562 / 58.995 | 49.582 | -13.98% | PASS |
| a3_glm53_w4a8_tp16_tpot50_c2 | decode | 44 | 57.817 / 57.597 / 59.092 | 49.554 | -14.29% | PASS |
| a3_glm53_w4a8_tp16_tpot88_c8 | decode | 49 | 69.556 / 69.489 / 69.830 | 66.764 | -4.01% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | decode | 152 | 13.135 / 13.129 / 13.145 | 12.436 | -5.32% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | decode | 145 | 13.292 / 12.803 / 12.817 | 12.155 | -8.55% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | decode | 75 | 26.328 / 26.306 / 26.336 | 24.812 | -5.76% | PASS |
| a5_glm53flash_tp8_c16_p4k | decode | 30 | 33.031 / 33.026 / 33.164 | 29.476 | -10.76% | PASS |
| a5_glm53flash_tp8_c16_p8k | decode | 32 | 33.616 / 33.626 / 33.710 | 29.491 | -12.27% | PASS |
| a5_glm53flash_tp8_c32_p4k | decode | 31 | 37.669 / 37.665 / 37.761 | 34.590 | -8.17% | PASS |
| a5_glm53flash_tp8_c32_p8k | decode | 35 | 38.713 / 38.722 / 38.759 | 34.652 | -10.49% | PASS |
| a5_glm53flash_tp8_c4_p8k | decode | 11 | 21.418 / 21.408 / 21.432 | 18.666 | -12.85% | PASS |
| a5_glm53flash_tp8_c64_p4k | decode | 31 | 46.528 / 46.499 / 46.645 | 45.975 | -1.19% | PASS |
| a5_glm53flash_tp8_c8_p4k | decode | 30 | 28.833 / 28.828 / 28.885 | 25.200 | -12.60% | PASS |
| a3_glm53flash_tp16_aclgraph_c16 | decode | 50 | 53.893 / 53.871 / 54.021 | 49.051 | -8.99% | PASS |
| a3_glm53flash_tp16_aclgraph_c32 | decode | 49 | 69.361 / 69.418 / 69.528 | 64.395 | -7.16% | PASS |
| a3_glm53flash_tp16_aclgraph_c64 | decode | 47 | 97.375 / 97.487 / 97.895 | 96.015 | -1.40% | PASS |
| a3_glm53flash_tp16_aclgraph_c8 | decode | 47 | 46.859 / 46.817 / 47.175 | 41.817 | -10.76% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k | decode | 129 | 14.929 / 14.914 / 14.929 | 13.749 | -7.91% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k | decode | 105 | 18.625 / 18.616 / 18.640 | 17.361 | -6.78% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k | decode | 151 | 13.239 / 13.209 / 13.227 | 12.550 | -5.21% | PASS |
| a3_kimi4_tp8_w4a8_c1 | decode | 254 | 3.180 / 3.128 / 3.432 | 3.238 | +1.82% | PASS |
| a3_kimi4_tp8_w4a8_c16 | decode | 235 | 4.807 / 4.779 / 4.992 | 4.174 | -13.17% | PASS |
| a3_kimi4_tp8_w4a8_c32 | decode | 220 | 6.714 / 6.665 / 6.923 | 6.097 | -9.19% | PASS |
| a3_kimi4_tp8_w4a8_c4 | decode | 246 | 3.476 / 3.438 / 3.656 | 3.196 | -8.07% | PASS |
| a3_kimi4_tp8_w4a8_c64 | decode | 196 | 9.615 / 9.550 / 9.774 | 8.699 | -9.53% | PASS |
| a5_kimi_tp8_e16_bf16_c16_p16k | decode | 47 | 39.247 / 39.245 / 39.263 | 40.764 | +3.86% | PASS |
| a5_kimi_tp8_e16_bf16_c16_p4k | decode | 49 | 36.985 / 36.953 / 36.969 | 38.388 | +3.79% | PASS |
| a5_kimi_tp8_e16_bf16_c1_p16k | decode | 59 | 30.823 / 30.822 / 30.839 | 31.866 | +3.38% | PASS |
| a5_kimi_tp8_e16_bf16_c1_p4k | decode | 59 | 30.637 / 30.615 / 30.632 | 31.672 | +3.38% | PASS |
| a5_kimi_tp8_e16_bf16_c2_p16k | decode | 54 | 33.876 / 33.858 / 33.873 | 34.119 | +0.72% | PASS |
| a5_kimi_tp8_e16_bf16_c2_p4k | decode | 55 | 33.548 / 33.516 / 33.533 | 33.778 | +0.69% | PASS |
| a5_kimi_tp8_e16_bf16_c32_p16k | decode | 41 | 44.666 / 44.645 / 44.662 | 42.156 | -5.62% | PASS |
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
| qwen35-35b-a3-tp4-c144 | decode | 25 | 61.750 / 61.784 / 62.102 | 53.661 | -13.10% | PASS |
| qwen35-35b-a3-tp4-c320 | decode | 21 | 99.692 / 99.679 / 100.090 | 94.185 | -5.52% | PASS |
| qwen36-a3-tp4-c64 | decode | 27 | 62.520 / 62.407 / 62.858 | 61.622 | -1.44% | PASS |
| qwen36-a3-tp4-c128 | decode | 22 | 97.566 / 97.506 / 97.890 | 89.346 | -8.42% | PASS |
| qwen38-a3-tp4-c64 | decode | 27 | 62.648 / 62.586 / 63.058 | 61.622 | -1.64% | PASS |
| qwen38-a3-tp4-c128 | decode | 22 | 97.457 / 97.455 / 97.787 | 89.346 | -8.32% | PASS |
| a5_qwen36_highconc_c4 | decode | 73 | 13.342 / 13.245 / 13.485 | 11.548 | -13.45% | PASS |
| a5_qwen36_highconc_c40 | decode | 54 | 20.684 / 20.612 / 21.334 | 18.071 | -12.63% | PASS |
| a5_qwen36_highconc_c128 | decode | 38 | 32.609 / 32.227 / 33.851 | 31.914 | -2.13% | PASS |
| a5_qwen38_highconc_c4 | decode | 45 | 13.027 / 13.005 / 13.167 | 11.383 | -12.62% | PASS |
| a5_qwen38_highconc_c32 | decode | 48 | 22.791 / 22.711 / 22.894 | 20.060 | -11.98% | PASS |
| a5_qwen38_highconc_c128 | decode | 29 | 45.689 / 45.690 / 45.735 | 45.941 | +0.55% | PASS |
| a3_glm53flash_heldout_c12_p4k | decode | 13 | 23.412 / 23.008 / 23.288 | 22.631 | -3.34% | PASS |
| a3_glm53flash_heldout_c24_p12k | decode | 14 | 23.601 / 23.242 / 23.719 | 22.647 | -4.04% | PASS |
| a5_glm53flash_heldout_c12_p4k | decode | 20 | 18.133 / 18.108 / 18.148 | 15.490 | -14.58% | PASS |
| a5_glm53flash_heldout_c24_p12k | decode | 21 | 38.995 / 39.210 / 39.263 | 33.641 | -13.73% | PASS |
| a5_glm53flash_heldout_c48_p4k | decode | 26 | 43.228 / 43.355 / 43.400 | 41.035 | -5.07% | PASS |
| a3_glm53flash_static_on_c10_p131201 | decode | 68 | 22.603 / 22.348 / 23.552 | 22.621 | +0.08% | FAIL |
| a3-qwen35-tp4-longctx-p-126976-c1 | decode | 65 | 16.054 / 16.058 / 16.121 | 8.201 | -48.92% | FAIL |
| a3-qwen35-tp4-longctx-p-126976-c4 | decode | 34 | 20.465 / 20.804 / 20.975 | 13.514 | -33.97% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c1 | decode | 64 | 15.530 / 15.511 / 15.646 | 7.585 | -51.16% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c2 | decode | 55 | 16.750 / 16.724 / 16.909 | 8.833 | -47.27% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c4 | decode | 50 | 18.893 / 18.984 / 19.070 | 11.056 | -41.48% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c8 | decode | 32 | 21.417 / 21.608 / 22.212 | 15.749 | -26.46% | FAIL |
| a3-qwen36-tp4-longctx-p-126976-c1 | decode | 10 | 18.924 / 18.932 / 19.020 | 15.765 | -16.69% | FAIL |
| a3-qwen36-tp4-longctx-p-126976-c4 | decode | 47 | 27.951 / 27.941 / 28.060 | 24.004 | -14.12% | PASS |
| a3-qwen36-tp4-longctx-p-65536-c1 | decode | 15 | 18.048 / 17.939 / 18.590 | 14.716 | -18.46% | FAIL |
| a3-qwen36-tp4-longctx-p-65536-c4 | decode | 49 | 24.880 / 24.783 / 25.010 | 19.834 | -20.28% | FAIL |
| a5-qwen35-tp4-longctx-p126976-c1-hold | decode | 161 | 18.202 / 18.181 / 18.223 | 13.793 | -24.22% | FAIL |
| a5-qwen35-tp4-longctx-p126976-c1-o32 | decode | 9 | 19.345 / 18.879 / 23.000 | 13.793 | -28.70% | FAIL |
| a5-qwen35-tp4-longctx-p126976-c4-hold | decode | 221 | 20.420 / 20.404 / 20.494 | 14.852 | -27.27% | FAIL |
| a5-qwen35-tp4-longctx-p126976-c4-o32 | decode | 11 | 18.132 / 18.133 / 18.193 | 13.793 | -23.93% | FAIL |
| a5-qwen35-tp4-longctx-p65536-c1-hold | decode | 196 | 13.678 / 13.649 / 13.717 | 9.027 | -34.01% | FAIL |
| a5-qwen35-tp4-longctx-p65536-c1-o32 | decode | 11 | 13.892 / 13.921 / 14.105 | 9.027 | -35.02% | FAIL |
| a5-qwen35-tp4-longctx-p65536-c4-hold | decode | 222 | 15.799 / 15.771 / 15.885 | 10.086 | -36.16% | FAIL |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | decode | 10 | 14.477 / 14.397 / 14.516 | 9.027 | -37.65% | FAIL |
| a5-qwen38-tp1-longctx-p126976-c4 | decode | 9 | 32.215 / 32.211 / 32.237 | 27.823 | -13.63% | FAIL |
| a5-qwen38-tp1-longctx-p65536-c4 | decode | 5 | 24.481 / 24.481 / 24.493 | 20.197 | -17.50% | FAIL |
| a5-qwen36-tp8-longctx-p126976-c1-hold | decode | 121 | 25.271 / 25.202 / 25.297 | 22.624 | -10.48% | PASS |
| a5-qwen36-tp8-longctx-p126976-c4-hold | decode | 176 | 26.646 / 26.650 / 26.767 | 23.162 | -13.08% | PASS |
| a5-qwen36-tp8-longctx-p65536-c1-hold | decode | 137 | 17.801 / 17.796 / 17.900 | 14.998 | -15.74% | FAIL |
| a5-qwen36-tp8-longctx-p65536-c4-hold | decode | 183 | 19.130 / 19.111 / 19.217 | 15.536 | -18.79% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | decode | 242 | 3.397 / 3.323 / 3.643 | 2.747 | -19.13% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | decode | 228 | 6.922 / 6.899 / 7.128 | 5.895 | -14.83% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | decode | 198 | 8.287 / 8.231 / 8.548 | 6.723 | -18.87% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | decode | 240 | 3.593 / 3.568 / 3.831 | 2.957 | -17.72% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | decode | 153 | 10.962 / 10.873 / 11.210 | 9.203 | -16.04% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | decode | 124 | 13.725 / 13.665 / 13.952 | 11.713 | -14.66% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | decode | 243 | 4.403 / 4.366 / 4.615 | 3.388 | -23.05% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | decode | 91 | 19.074 / 19.036 / 19.275 | 16.687 | -12.51% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | decode | 233 | 4.795 / 4.727 / 5.001 | 3.812 | -20.51% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | decode | 74 | 23.694 / 23.656 / 23.841 | 20.965 | -11.52% | PASS |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | decode | 236 | 5.467 / 5.396 / 5.675 | 4.221 | -22.79% | FAIL |
| a3-kimi4-tp8-longctx-decode-c12-p16k | decode | 189 | 4.435 / 4.402 / 4.659 | 3.721 | -16.10% | FAIL |
| a3-kimi4-tp8-longctx-decode-c12-p32k | decode | 189 | 4.621 / 4.558 / 4.808 | 4.049 | -12.38% | PASS |
| a3-kimi4-tp8-longctx-decode-c12-p4k | decode | 191 | 4.229 / 4.195 / 4.479 | 3.471 | -17.93% | FAIL |
| a3-kimi4-tp8-longctx-decode-c12-p8k | decode | 190 | 4.249 / 4.217 / 4.437 | 3.556 | -16.31% | FAIL |
| a3-kimi4-tp8-longctx-decode-c24-p16k | decode | 190 | 6.096 / 6.046 / 6.322 | 4.921 | -19.28% | FAIL |
| a3-kimi4-tp8-longctx-decode-c24-p32k | decode | 193 | 6.437 / 6.353 / 6.658 | 5.572 | -13.43% | PASS |
| a3-kimi4-tp8-longctx-decode-c24-p4k | decode | 200 | 5.641 / 5.582 / 5.874 | 4.435 | -21.37% | FAIL |
| a3-kimi4-tp8-longctx-decode-c24-p8k | decode | 195 | 5.829 / 5.787 / 6.088 | 4.602 | -21.06% | FAIL |
| a3-kimi4-tp8-longctx-decode-c2-p4k | decode | 200 | 3.285 / 3.243 / 3.520 | 2.543 | -22.58% | FAIL |
| a3-kimi4-tp8-longctx-decode-c48-p4k | decode | 159 | 8.472 / 8.430 / 8.705 | 7.186 | -15.18% | FAIL |
| a3-kimi4-tp8-longctx-decode-c6-p4k | decode | 186 | 3.701 / 3.632 / 3.935 | 2.591 | -29.99% | FAIL |
| a3-kimi4-tp8-longctx-decode-c8-p4k | decode | 191 | 3.839 / 3.765 / 4.168 | 2.621 | -31.73% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | decode | 228 | 4.093 / 3.992 / 4.443 | 2.958 | -27.72% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | decode | 207 | 6.865 / 6.792 / 7.109 | 5.221 | -23.95% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | decode | 206 | 7.840 / 7.747 / 8.108 | 6.022 | -23.18% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | decode | 232 | 4.362 / 4.303 / 4.648 | 3.163 | -27.49% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | decode | 167 | 10.062 / 10.014 / 10.358 | 8.458 | -15.95% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | decode | 138 | 12.295 / 12.243 / 12.550 | 10.095 | -17.89% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | decode | 226 | 5.008 / 4.905 / 5.299 | 3.569 | -28.74% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | decode | 103 | 16.734 / 16.715 / 16.992 | 14.207 | -15.10% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | decode | 222 | 5.264 / 5.192 / 5.571 | 3.997 | -24.06% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | decode | 83 | 20.942 / 20.922 / 21.125 | 17.921 | -14.42% | PASS |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | decode | 212 | 5.865 / 5.802 / 6.140 | 4.395 | -25.06% | FAIL |
| a3-kimi4-tp16-128k-decode-c12-p16k | decode | 180 | 4.430 / 4.375 / 4.726 | 3.103 | -29.96% | FAIL |
| a3-kimi4-tp16-128k-decode-c12-p32k | decode | 178 | 4.659 / 4.586 / 4.886 | 3.427 | -26.44% | FAIL |
| a3-kimi4-tp16-128k-decode-c12-p4k | decode | 162 | 4.439 / 4.155 / 4.610 | 2.855 | -35.67% | FAIL |
| a3-kimi4-tp16-128k-decode-c12-p8k | decode | 173 | 4.379 / 4.203 / 4.614 | 2.940 | -32.86% | FAIL |
| a3-kimi4-tp16-128k-decode-c24-p16k | decode | 175 | 5.260 / 5.124 / 5.362 | 4.280 | -18.62% | FAIL |
| a3-kimi4-tp16-128k-decode-c24-p32k | decode | 186 | 5.661 / 5.606 / 5.932 | 4.918 | -13.12% | PASS |
| a3-kimi4-tp16-128k-decode-c24-p4k | decode | 177 | 4.841 / 4.788 / 5.056 | 3.800 | -21.49% | FAIL |
| a3-kimi4-tp16-128k-decode-c24-p8k | decode | 179 | 4.939 / 4.913 / 5.134 | 3.965 | -19.72% | FAIL |
| a3-kimi4-tp16-128k-decode-c2-p4k | decode | 186 | 4.055 / 3.989 / 4.321 | 2.756 | -32.03% | FAIL |
| a3-kimi4-tp16-128k-decode-c48-p4k | decode | 172 | 6.201 / 6.157 / 6.393 | 4.879 | -21.32% | FAIL |
| a3-kimi4-tp16-128k-decode-c6-p4k | decode | 181 | 4.110 / 4.033 / 4.408 | 2.800 | -31.86% | FAIL |
| a3-kimi4-tp16-128k-decode-c8-p4k | decode | 183 | 4.188 / 4.058 / 4.447 | 2.829 | -32.46% | FAIL |
| a5_kimi_tp8_e16_bf16_128k_c1 | decode | 56 | 32.485 / 32.470 / 32.485 | 26.201 | -19.34% | FAIL |
| a5_kimi_tp8_e16_bf16_128k_c2 | decode | 50 | 36.854 / 36.840 / 36.856 | 27.125 | -26.40% | FAIL |
| a5_kimi_tp8_e16_bf16_128k_c4 | decode | 45 | 40.416 / 40.391 / 40.420 | 28.996 | -28.26% | FAIL |
| a5_kimi_tp8_e16_bf16_128k_c6 | decode | 42 | 43.589 / 43.560 / 43.578 | 31.012 | -28.85% | FAIL |
| a5_kimi_tp8_e16_bf16_128k_c8 | decode | 40 | 46.691 / 46.673 / 46.694 | 32.762 | -29.83% | FAIL |
| a5_kimi_tp8_e16_bf16_128k_c12 | decode | 34 | 54.147 / 54.132 / 54.160 | 37.216 | -31.27% | FAIL |
| a3-v41-tp4dp4-128k-c12 | decode | 82 | 54.204 / 54.120 / 54.263 | 52.970 | -2.28% | PASS |
| a3-v41-tp4dp4-128k-c16 | decode | 81 | 54.432 / 54.359 / 54.566 | 52.970 | -2.69% | PASS |
| a3-v41-tp4dp4-128k-c24 | decode | 78 | 56.274 / 56.219 / 56.324 | 56.478 | +0.36% | PASS |
| a3-v41-tp4dp4-128k-c32 | decode | 76 | 57.786 / 57.711 / 57.953 | 57.688 | -0.17% | PASS |
| a3-v41-tp4dp4-128k-c4 | decode | 85 | 53.220 / 53.218 / 53.339 | 50.909 | -4.34% | PASS |
| a3-v41-tp4dp4-128k-c48 | decode | 61 | 74.011 / 73.921 / 74.097 | 63.842 | -13.74% | PASS |
| a3-v41-tp4dp4-128k-c64 | decode | 58 | 77.498 / 77.469 / 77.623 | 69.155 | -10.77% | PASS |
| a3-v41-tp4dp4-128k-c8 | decode | 82 | 53.618 / 53.549 / 53.745 | 51.898 | -3.21% | PASS |
| a3-qwen35-tp4-decode-c1-p126000 | decode | 169 | 17.505 / 17.528 / 17.656 | 9.582 | -45.26% | FAIL |
| a3-qwen35-tp4-decode-c12-p126000 | decode | 97 | 36.173 / 36.158 / 36.304 | 33.374 | -7.74% | PASS |
| a3-qwen35-tp4-decode-c16-p126000 | decode | 87 | 40.651 / 40.639 / 40.884 | 39.465 | -2.92% | PASS |
| a3-qwen35-tp4-decode-c2-p126000 | decode | 156 | 19.585 / 19.593 / 19.734 | 11.986 | -38.80% | FAIL |
| a3-qwen35-tp4-decode-c24-p126000 | decode | 57 | 63.494 / 63.631 / 63.779 | 53.303 | -16.05% | FAIL |
| a3-qwen35-tp4-decode-c32-p126000 | decode | 55 | 65.343 / 65.297 / 65.724 | 55.420 | -15.19% | FAIL |
| a3-qwen35-tp4-decode-c4-p126000 | decode | 138 | 22.871 / 22.871 / 23.010 | 16.948 | -25.90% | FAIL |
| a3-qwen35-tp4-decode-c48-p126000 | decode | 42 | 86.442 / 86.447 / 86.585 | 75.262 | -12.93% | PASS |
| a3-qwen35-tp4-decode-c6-p126000 | decode | 121 | 27.566 / 27.525 / 27.659 | 22.308 | -19.08% | FAIL |
| a3-qwen35-tp4-decode-c64-p126000 | decode | 34 | 107.680 / 107.516 / 108.525 | 94.521 | -12.22% | PASS |
| a3-qwen35-tp4-decode-c8-p126000 | decode | 111 | 31.009 / 30.990 / 31.159 | 27.248 | -12.13% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | decode | 47 | 27.914 / 27.905 / 28.026 | 20.804 | -25.47% | FAIL |
| a3-qwen35-tp4-decode-c12-p64512 | decode | 45 | 30.548 / 30.507 / 30.812 | 25.769 | -15.64% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | decode | 43 | 27.435 / 27.433 / 27.570 | 19.490 | -28.96% | FAIL |
| a3-qwen35-tp4-decode-c12-p96512 | decode | 58 | 33.166 / 33.160 / 33.280 | 29.772 | -10.23% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | decode | 66 | 35.550 / 35.558 / 35.723 | 26.891 | -24.36% | FAIL |
| a3-qwen35-tp4-decode-c24-p64512 | decode | 63 | 44.868 / 44.851 / 45.016 | 37.301 | -16.87% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | decode | 57 | 31.676 / 31.677 / 31.775 | 22.727 | -28.25% | FAIL |
| a3-qwen35-tp4-decode-c24-p96512 | decode | 52 | 54.896 / 55.004 / 55.143 | 45.628 | -16.88% | FAIL |
| a3-qwen35-tp4-decode-c2-p24512 | decode | 16 | 16.697 / 16.657 / 16.860 | 8.519 | -48.98% | FAIL |
| a3-qwen35-tp4-decode-c2-p64512 | decode | 7 | 17.136 / 17.138 / 17.270 | 8.949 | -47.77% | FAIL |
| a3-qwen35-tp4-decode-c2-p8512 | decode | 7 | 16.319 / 16.333 / 16.372 | 8.310 | -49.07% | FAIL |
| a3-qwen35-tp4-decode-c2-p96512 | decode | 12 | 17.338 / 17.324 / 17.456 | 9.266 | -46.56% | FAIL |
| a3-qwen35-tp4-decode-c6-p24512 | decode | 23 | 23.225 / 23.181 / 23.327 | 16.067 | -30.82% | FAIL |
| a3-qwen35-tp4-decode-c6-p64512 | decode | 40 | 24.666 / 24.667 / 24.763 | 18.502 | -24.99% | FAIL |
| a3-qwen35-tp4-decode-c6-p8512 | decode | 21 | 22.846 / 22.849 / 22.926 | 15.086 | -33.97% | FAIL |
| a3-qwen35-tp4-decode-c6-p96512 | decode | 42 | 26.149 / 25.837 / 26.090 | 20.559 | -21.38% | FAIL |
| a3-qwen36-tp2-decode-c1-p126000 | decode | 118 | 27.505 / 27.460 / 27.662 | 23.052 | -16.19% | FAIL |
| a3-qwen36-tp2-decode-c12-p126000 | decode | 40 | 92.965 / 92.683 / 93.492 | 86.649 | -6.79% | PASS |
| a3-qwen36-tp2-decode-c16-p126000 | decode | 39 | 96.424 / 96.221 / 97.153 | 90.747 | -5.89% | PASS |
| a3-qwen36-tp2-decode-c2-p126000 | decode | 107 | 32.035 / 32.023 / 32.214 | 28.674 | -10.49% | PASS |
| a3-qwen36-tp2-decode-c24-p126000 | decode | 29 | 132.699 / 132.704 / 132.775 | 127.597 | -3.84% | PASS |
| a3-qwen36-tp2-decode-c4-p126000 | decode | 88 | 40.819 / 40.826 / 41.229 | 39.172 | -4.03% | PASS |
| a3-qwen36-tp2-decode-c6-p126000 | decode | 74 | 50.103 / 50.017 / 50.304 | 49.717 | -0.77% | PASS |
| a3-qwen36-tp2-decode-c8-p126000 | decode | 66 | 56.360 / 56.274 / 56.741 | 60.306 | +7.00% | PASS |
| a3-qwen36-tp2-decode-c12-p24512 | decode | 63 | 45.843 / 45.864 / 46.024 | 41.583 | -9.29% | PASS |
| a3-qwen36-tp2-decode-c12-p64512 | decode | 46 | 63.620 / 63.439 / 64.028 | 59.345 | -6.72% | PASS |
| a3-qwen36-tp2-decode-c12-p8512 | decode | 68 | 39.923 / 39.905 / 40.004 | 34.478 | -13.64% | PASS |
| a3-qwen36-tp2-decode-c24-p24512 | decode | 49 | 60.836 / 60.802 / 60.974 | 59.998 | -1.38% | PASS |
| a3-qwen36-tp2-decode-c24-p64512 | decode | 34 | 87.080 / 87.073 / 87.154 | 86.641 | -0.50% | PASS |
| a3-qwen36-tp2-decode-c24-p8512 | decode | 56 | 52.156 / 52.152 / 52.263 | 49.340 | -5.40% | PASS |
| a3-qwen36-tp2-decode-c2-p24512 | decode | 58 | 26.724 / 26.694 / 26.806 | 21.700 | -18.80% | FAIL |
| a3-qwen36-tp2-decode-c2-p64512 | decode | 58 | 28.868 / 28.845 / 28.903 | 24.493 | -15.16% | FAIL |
| a3-qwen36-tp2-decode-c2-p8512 | decode | 45 | 25.809 / 25.747 / 25.801 | 20.650 | -19.99% | FAIL |
| a3-qwen36-tp2-decode-c2-p96512 | decode | 62 | 30.222 / 30.218 / 30.266 | 26.665 | -11.77% | FAIL |
| a3-qwen36-tp2-decode-c6-p24512 | decode | 71 | 33.717 / 33.762 / 33.825 | 29.011 | -13.96% | FAIL |
| a3-qwen36-tp2-decode-c6-p64512 | decode | 71 | 39.714 / 39.641 / 39.741 | 37.193 | -6.35% | PASS |
| a3-qwen36-tp2-decode-c6-p8512 | decode | 61 | 32.027 / 31.966 / 32.038 | 26.840 | -16.19% | FAIL |
| a3-qwen36-tp2-decode-c6-p96512 | decode | 64 | 44.510 / 44.533 / 44.618 | 43.781 | -1.64% | PASS |
| a3-qwen36-tp4-decode-c1-p126000 | decode | 132 | 19.697 / 19.667 / 19.812 | 15.756 | -20.01% | FAIL |
| a3-qwen36-tp4-decode-c12-p126000 | decode | 83 | 44.267 / 44.229 / 44.445 | 45.589 | +2.98% | PASS |
| a3-qwen36-tp4-decode-c16-p126000 | decode | 72 | 51.997 / 51.884 / 52.229 | 56.444 | +8.55% | PASS |
| a3-qwen36-tp4-decode-c2-p126000 | decode | 128 | 21.879 / 21.733 / 21.892 | 18.258 | -16.55% | FAIL |
| a3-qwen36-tp4-decode-c24-p126000 | decode | 42 | 89.034 / 88.904 / 89.802 | 83.299 | -6.44% | PASS |
| a3-qwen36-tp4-decode-c4-p126000 | decode | 121 | 26.965 / 26.819 / 26.895 | 24.013 | -10.95% | PASS |
| a3-qwen36-tp4-decode-c6-p126000 | decode | 105 | 32.038 / 31.950 / 32.050 | 29.052 | -9.32% | PASS |
| a3-qwen36-tp4-decode-c8-p126000 | decode | 97 | 36.585 / 36.585 / 36.725 | 34.777 | -4.94% | PASS |
| a3-qwen38-tp2-decode-c1-p126000 | decode | 119 | 27.543 / 27.497 / 27.703 | 23.052 | -16.30% | FAIL |
| a3-qwen38-tp2-decode-c12-p126000 | decode | 40 | 93.228 / 93.357 / 93.478 | 86.649 | -7.06% | PASS |
| a3-qwen38-tp2-decode-c16-p126000 | decode | 39 | 96.251 / 96.054 / 96.900 | 90.747 | -5.72% | PASS |
| a3-qwen38-tp2-decode-c2-p126000 | decode | 107 | 32.136 / 32.139 / 32.349 | 28.674 | -10.77% | PASS |
| a3-qwen38-tp2-decode-c4-p126000 | decode | 90 | 40.524 / 40.550 / 40.876 | 39.172 | -3.33% | PASS |
| a3-qwen38-tp2-decode-c6-p126000 | decode | 74 | 50.273 / 50.197 / 50.502 | 49.717 | -1.11% | PASS |
| a3-qwen38-tp2-decode-c8-p126000 | decode | 66 | 56.370 / 56.313 / 56.643 | 60.306 | +6.98% | PASS |
| a3-qwen38-tp4-decode-c1-p126000 | decode | 135 | 19.886 / 19.681 / 19.804 | 15.756 | -20.77% | FAIL |
| a3-qwen38-tp4-decode-c12-p126000 | decode | 84 | 44.305 / 44.261 / 44.463 | 45.589 | +2.90% | PASS |
| a3-qwen38-tp4-decode-c16-p126000 | decode | 73 | 51.793 / 51.612 / 52.084 | 56.444 | +8.98% | PASS |
| a3-qwen38-tp4-decode-c2-p126000 | decode | 137 | 21.825 / 21.761 / 21.870 | 18.258 | -16.35% | FAIL |
| a3-qwen38-tp4-decode-c24-p126000 | decode | 43 | 88.988 / 88.982 / 89.108 | 83.299 | -6.39% | PASS |
| a3-qwen38-tp4-decode-c32-p126000 | decode | 41 | 93.356 / 93.203 / 93.861 | 88.049 | -5.68% | PASS |
| a3-qwen38-tp4-decode-c4-p126000 | decode | 124 | 26.807 / 26.771 / 26.837 | 24.013 | -10.42% | PASS |
| a3-qwen38-tp4-decode-c6-p126000 | decode | 108 | 31.992 / 31.979 / 32.091 | 29.052 | -9.19% | PASS |
| a3-qwen38-tp4-decode-c8-p126000 | decode | 98 | 36.460 / 36.463 / 36.611 | 34.777 | -4.62% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | decode | 56 | 30.908 / 30.898 / 30.968 | 24.882 | -19.50% | FAIL |
| a3-qwen38-tp4-decode-c12-p64512 | decode | 68 | 35.845 / 35.986 / 36.161 | 33.065 | -7.76% | FAIL |
| a3-qwen38-tp4-decode-c12-p96512 | decode | 65 | 39.782 / 39.852 / 40.095 | 39.653 | -0.33% | PASS |
| a3-qwen38-tp4-decode-c24-p24512 | decode | 65 | 43.632 / 43.656 / 43.714 | 38.233 | -12.37% | PASS |
| a3-qwen38-tp4-decode-c24-p64512 | decode | 49 | 60.117 / 60.324 / 60.463 | 55.995 | -6.86% | PASS |
| a3-qwen38-tp4-decode-c24-p96512 | decode | 40 | 75.162 / 75.093 / 75.331 | 70.205 | -6.60% | PASS |
| a3-qwen38-tp4-decode-c2-p24512 | decode | 11 | 19.404 / 19.244 / 20.150 | 14.759 | -23.94% | FAIL |
| a3-qwen38-tp4-decode-c2-p64512 | decode | 20 | 20.210 / 20.021 / 20.180 | 16.161 | -20.03% | FAIL |
| a3-qwen38-tp4-decode-c2-p96512 | decode | 24 | 20.989 / 20.830 / 21.239 | 17.291 | -17.62% | FAIL |
| a3-qwen38-tp4-decode-c6-p24512 | decode | 38 | 24.761 / 24.752 / 24.829 | 18.769 | -24.20% | FAIL |
| a3-qwen38-tp4-decode-c6-p64512 | decode | 40 | 27.237 / 27.135 / 27.365 | 22.786 | -16.34% | FAIL |
| a3-qwen38-tp4-decode-c6-p96512 | decode | 42 | 29.560 / 29.308 / 29.565 | 26.174 | -11.45% | FAIL |
| a5-qwen36-tp2-decode-c1-p126000 | decode | 54 | 27.332 / 27.209 / 27.445 | 23.713 | -13.24% | PASS |
| a5-qwen36-tp2-decode-c12-p126000 | decode | 38 | 39.512 / 39.500 / 39.595 | 29.107 | -26.34% | FAIL |
| a5-qwen36-tp2-decode-c16-p126000 | decode | 35 | 43.048 / 43.038 / 43.179 | 32.215 | -25.16% | FAIL |
| a5-qwen36-tp2-decode-c2-p126000 | decode | 52 | 28.841 / 28.804 / 28.991 | 23.274 | -19.30% | FAIL |
| a5-qwen36-tp2-decode-c24-p126000 | decode | 25 | 63.879 / 63.873 / 63.963 | 60.286 | -5.62% | PASS |
| a5-qwen36-tp2-decode-c4-p126000 | decode | 48 | 31.689 / 31.648 / 31.862 | 25.626 | -19.13% | FAIL |
| a5-qwen36-tp2-decode-c6-p126000 | decode | 43 | 34.972 / 34.963 / 35.029 | 25.720 | -26.46% | FAIL |
| a5-qwen36-tp2-decode-c8-p126000 | decode | 41 | 35.597 / 35.582 / 35.641 | 26.668 | -25.08% | FAIL |
| a5-qwen38-tp2-decode-c1-p126000 | decode | 53 | 28.447 / 28.429 / 28.570 | 24.245 | -14.77% | PASS |
| a5-qwen38-tp2-decode-c12-p126000 | decode | 37 | 40.788 / 40.789 / 40.880 | 29.762 | -27.03% | FAIL |
| a5-qwen38-tp2-decode-c16-p126000 | decode | 34 | 44.535 / 44.520 / 44.705 | 32.920 | -26.08% | FAIL |
| a5-qwen38-tp2-decode-c2-p126000 | decode | 51 | 30.056 / 30.048 / 30.111 | 23.806 | -20.79% | FAIL |
| a5-qwen38-tp2-decode-c24-p126000 | decode | 24 | 64.457 / 64.427 / 64.559 | 61.090 | -5.22% | PASS |
| a5-qwen38-tp2-decode-c4-p126000 | decode | 47 | 32.711 / 32.699 / 32.777 | 26.182 | -19.96% | FAIL |
| a5-qwen38-tp2-decode-c6-p126000 | decode | 42 | 36.091 / 36.084 / 36.136 | 26.301 | -27.13% | FAIL |
| a5-qwen38-tp2-decode-c8-p126000 | decode | 40 | 37.428 / 37.420 / 37.480 | 27.274 | -27.13% | FAIL |
| a5-qwen36-tp4-decode-c1-p126000 | decode | 58 | 25.585 / 25.621 / 25.711 | 21.070 | -17.65% | FAIL |
| a5-qwen36-tp4-decode-c2-p126000 | decode | 54 | 27.536 / 27.580 / 27.663 | 21.839 | -20.69% | FAIL |
| a5-qwen36-tp4-decode-c4-p126000 | decode | 52 | 28.964 / 28.988 / 29.039 | 24.187 | -16.49% | FAIL |
| a5-qwen36-tp4-decode-c6-p126000 | decode | 49 | 30.604 / 30.612 / 30.773 | 23.267 | -23.97% | FAIL |
| a5-qwen36-tp4-decode-c8-p126000 | decode | 48 | 31.660 / 31.718 / 31.765 | 25.924 | -18.12% | FAIL |
| a5-qwen38-tp4-decode-c1-p126000 | decode | 56 | 25.808 / 25.757 / 26.012 | 21.309 | -17.43% | FAIL |
| a5-qwen38-tp4-decode-c2-p126000 | decode | 53 | 28.147 / 28.200 / 28.244 | 22.076 | -21.57% | FAIL |
| a5-qwen38-tp4-decode-c4-p126000 | decode | 52 | 29.240 / 29.178 / 29.387 | 24.434 | -16.43% | FAIL |
| a5-qwen38-tp4-decode-c6-p126000 | decode | 49 | 30.974 / 30.930 / 31.177 | 23.525 | -24.05% | FAIL |
| a5-qwen38-tp4-decode-c8-p126000 | decode | 47 | 31.871 / 31.845 / 32.020 | 26.193 | -17.82% | FAIL |
| a3-v41-tp4dp4-decode-c4-p8512 | decode | 28 | 35.585 / 36.156 / 36.274 | 32.194 | -9.53% | PASS |

Communication summaries without device-task bindings can extend beyond a dependent Head. For verified hidden-state consumer chains, structural consumer start provides a conditional completion upper bound. Original summary intervals remain in the evidence; these bounds are not measured transport service times.
- a3-kimi4-tp16-128k-decode-c24-p4k: {"additive_body_time_cause": false, "affected_events": 78, "affected_forwards": 78, "basis": "structural_consumer_upper_bound", "physical_transport_completion_observed": false, "raw_envelope_total_ns": 646243092, "unassigned_summary_suffix_total_ns": 643576396}
- a3-qwen36-tp4-decode-c4-p126000: {"additive_body_time_cause": false, "affected_events": 96, "affected_forwards": 24, "basis": "structural_consumer_upper_bound", "physical_transport_completion_observed": false, "raw_envelope_total_ns": 3628147413, "unassigned_summary_suffix_total_ns": 3626517451}

| Case | Body validation basis | Target native timings used in rules |
|---|---|---|
| qwen36-a3-tp4-c128 | in_sample_native_physical_domains | True |
| qwen38-a3-tp4-c128 | retrospective_same_geometry_cross_capture | False |
| a5_qwen36_highconc_c4 | mixed_native_transfer_and_in_sample_hccl_gating | True |
| a5_qwen36_highconc_c40 | mixed_native_transfer_and_in_sample_hccl_gating | True |
| a5_qwen36_highconc_c128 | mixed_native_transfer_and_in_sample_hccl_gating | True |
| a5_qwen38_highconc_c4 | mixed_native_transfer_and_in_sample_hccl_gating | True |
| a5_qwen38_highconc_c32 | mixed_native_transfer_and_in_sample_hccl_gating | True |
| a5_qwen38_highconc_c128 | mixed_native_transfer_and_in_sample_hccl_gating | True |
| a5_glm53flash_heldout_c12_p4k | frozen_native_functions_from_prior_capture_training | False |
| a5_glm53flash_heldout_c24_p12k | frozen_native_functions_from_prior_capture_training | False |
| a5_glm53flash_heldout_c48_p4k | frozen_native_functions_from_prior_capture_training | False |
| a3_glm53flash_static_on_c10_p131201 | operator_calibrated_not_pristine_holdout | True |
| a3-qwen36-tp4-longctx-p-126976-c1 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-longctx-p-126976-c4 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-longctx-p-65536-c1 | frozen_native_service_transfer | False |
| a3-qwen36-tp4-longctx-p-65536-c4 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c1-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c12-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c16-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c2-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c24-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c32-p126000 | frozen_native_service_transfer | False |
| a3-qwen35-tp4-decode-c4-p126000 | frozen_native_service_transfer | False |
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

The source headline retains its largest population. Each execution geometry is scored separately; an all-population source pass requires complete scored coverage and every population to pass.

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
| qwen35-35b-a5-tp4-c4-graph | 4 | 4 | 4096 | 84 | 11.551 / 11.482 / 11.818 | 9.901 | -14.29% | PASS |
| qwen35-35b-a5-tp4-c4-graph | 1 | 4 | 4096 | 6 | 8.747 / 8.803 / 8.838 | — | — | unresolved |
| qwen35-35b-a5-tp4-c4-graph | 2 | 4 | 4096 | 1 | 9.700 / 9.700 / 9.700 | — | — | unresolved |

qwen35-35b-a5-tp4-c4-graph: scored 84 / 91 calls; all-population pass: None.
| a3_glm53_w4a8_tp16_tpot30_c2 | 2 | 6 | 4096 | 44 | 57.639 / 57.562 / 58.995 | 49.582 | -13.98% | PASS |
| a3_glm53_w4a8_tp16_tpot30_c2 | 1 | 6 | 4096 | 4 | 57.125 / 57.281 / 57.500 | — | — | unresolved |

a3_glm53_w4a8_tp16_tpot30_c2: scored 44 / 48 calls; all-population pass: None.
| a3_glm53_w4a8_tp16_tpot50_c2 | 2 | 6 | 4096 | 44 | 57.817 / 57.597 / 59.092 | 49.554 | -14.29% | PASS |
| a3_glm53_w4a8_tp16_tpot50_c2 | 1 | 6 | 4096 | 9 | 57.713 / 57.524 / 58.620 | — | — | unresolved |

a3_glm53_w4a8_tp16_tpot50_c2: scored 44 / 53 calls; all-population pass: None.
| a3_glm53_w4a8_tp16_tpot88_c8 | 8 | 6 | 4096 | 49 | 69.556 / 69.489 / 69.830 | 66.764 | -4.01% | PASS |
| a3_glm53_w4a8_tp16_tpot88_c8 | 1 | 6 | 4096 | 4 | 56.950 / 56.983 / 57.379 | — | — | unresolved |
| a3_glm53_w4a8_tp16_tpot88_c8 | 2 | 6 | 4096 | 3 | 56.847 / 56.896 / 57.002 | — | — | unresolved |
| a3_glm53_w4a8_tp16_tpot88_c8 | 6 | 6 | 4096 | 2 | 68.633 / 68.633 / 68.639 | — | — | unresolved |
| a3_glm53_w4a8_tp16_tpot88_c8 | 3 | 6 | 4096 | 2 | 58.058 / 58.058 / 58.239 | — | — | unresolved |
| a3_glm53_w4a8_tp16_tpot88_c8 | 4 | 6 | 4096 | 1 | 57.388 / 57.388 / 57.388 | — | — | unresolved |

a3_glm53_w4a8_tp16_tpot88_c8: scored 49 / 61 calls; all-population pass: None.
| a5_glm53flash_tp8_c16_p4k | 16 | 4 | 4104 | 30 | 33.031 / 33.026 / 33.164 | 29.476 | -10.76% | PASS |
| a5_glm53flash_tp8_c16_p4k | 2 | 4 | 4104 | 4 | 18.010 / 17.896 / 18.413 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p4k | 1 | 4 | 4104 | 3 | 15.697 / 15.705 / 15.723 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p4k | 6 | 4 | 4104 | 2 | 24.984 / 24.984 / 25.001 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p4k | 14 | 4 | 4104 | 1 | 33.211 / 33.211 / 33.211 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p4k | 12 | 4 | 4104 | 1 | 32.232 / 32.232 / 32.232 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p4k | 10 | 4 | 4104 | 1 | 31.923 / 31.923 / 31.923 | — | — | unresolved |
| a5_glm53flash_tp8_c16_p4k | 4 | 4 | 4104 | 1 | 21.417 / 21.417 / 21.417 | — | — | unresolved |

a5_glm53flash_tp8_c16_p4k: scored 30 / 43 calls; all-population pass: None.
| a5_glm53flash_tp8_c16_p8k | 16 | 4 | 8200 | 32 | 33.616 / 33.626 / 33.710 | 29.491 | -12.27% | PASS |
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
| a5_glm53flash_tp8_c32_p8k | 32 | 4 | 8200 | 35 | 38.713 / 38.722 / 38.759 | 34.652 | -10.49% | PASS |
| a5_glm53flash_tp8_c32_p8k | 30 | 4 | 8200 | 1 | 38.635 / 38.635 / 38.635 | — | — | unresolved |

a5_glm53flash_tp8_c32_p8k: scored 35 / 36 calls; all-population pass: None.
| a5_glm53flash_tp8_c4_p8k | 4 | 4 | 8200 | 11 | 21.418 / 21.408 / 21.432 | 18.666 | -12.85% | PASS |
| a5_glm53flash_tp8_c4_p8k | 1 | 4 | 8200 | 9 | 15.590 / 15.583 / 15.642 | — | — | unresolved |
| a5_glm53flash_tp8_c4_p8k | 2 | 4 | 8200 | 3 | 17.682 / 17.672 / 17.709 | — | — | unresolved |

a5_glm53flash_tp8_c4_p8k: scored 11 / 23 calls; all-population pass: None.
| a5_glm53flash_tp8_c8_p4k | 8 | 4 | 4104 | 30 | 28.833 / 28.828 / 28.885 | 25.200 | -12.60% | PASS |
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
| a3_glm53flash_tp16_aclgraph_c8 | 8 | 6 | 4096 | 47 | 46.859 / 46.817 / 47.175 | 41.817 | -10.76% | PASS |
| a3_glm53flash_tp16_aclgraph_c8 | 1 | 6 | 4096 | 6 | 33.545 / 33.104 / 34.940 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c8 | 4 | 6 | 4096 | 4 | 37.953 / 37.468 / 39.615 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c8 | 6 | 6 | 4096 | 3 | 45.218 / 44.930 / 46.274 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c8 | 2 | 6 | 4096 | 2 | 34.031 / 34.031 / 34.634 | — | — | unresolved |

a3_glm53flash_tp16_aclgraph_c8: scored 47 / 62 calls; all-population pass: None.
| a3_kimi4_tp8_w4a8_c16 | 16 | 1 | 4096 | 235 | 4.807 / 4.779 / 4.992 | 4.174 | -13.17% | PASS |
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
| a5_glm53flash_heldout_c12_p4k | 2 | 4 | 4104 | 20 | 18.133 / 18.108 / 18.148 | 15.490 | -14.58% | PASS |
| a5_glm53flash_heldout_c12_p4k | 3 | 4 | 4104 | 15 | 19.876 / 19.730 / 20.375 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 12 | 4 | 4104 | 10 | 32.310 / 32.084 / 32.482 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 6 | 4 | 4104 | 9 | 25.926 / 25.380 / 27.537 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 4 | 4 | 4104 | 5 | 21.675 / 21.618 / 21.897 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 8 | 4 | 4104 | 1 | 28.855 / 28.855 / 28.855 | — | — | unresolved |

a5_glm53flash_heldout_c12_p4k: scored 20 / 60 calls; all-population pass: None.
| a5_glm53flash_heldout_c24_p12k | 24 | 4 | 12296 | 21 | 38.995 / 39.210 / 39.263 | 33.641 | -13.73% | PASS |
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
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 | 2 | 126976 | 34 | 20.465 / 20.804 / 20.975 | 13.514 | -33.97% | FAIL |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 | 2 | 126976 | 16 | 16.107 / 16.100 / 16.156 | 8.201 | -49.08% | FAIL |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 | 2 | 126976 | 15 | 17.687 / 17.706 / 17.759 | 10.061 | -43.11% | FAIL |

a3-qwen35-tp4-longctx-p-126976-c4: scored 65 / 65 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 126976, bounds 126976–127104 tokens.
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 | 2 | 65536 | 55 | 16.750 / 16.724 / 16.909 | 8.833 | -47.27% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 | 2 | 65536 | 11 | 15.583 / 15.520 / 15.562 | 7.585 | -51.32% | FAIL |

a3-qwen35-tp4-longctx-p-65536-c2: scored 66 / 66 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65664 tokens.
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 | 2 | 65536 | 50 | 18.893 / 18.984 / 19.070 | 11.056 | -41.48% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 | 2 | 65536 | 8 | 15.649 / 15.561 / 16.432 | 7.585 | -51.53% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 | 2 | 65536 | 7 | 16.789 / 16.628 / 17.557 | 8.833 | -47.39% | FAIL |

a3-qwen35-tp4-longctx-p-65536-c4: scored 65 / 65 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65664 tokens.
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 | 2 | 65536 | 32 | 21.417 / 21.608 / 22.212 | 15.749 | -26.46% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 | 2 | 65536 | 17 | 18.901 / 18.818 / 19.256 | 11.056 | -41.50% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 | 2 | 65536 | 8 | 16.891 / 16.719 / 17.533 | 8.833 | -47.71% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 | 2 | 65536 | 8 | 15.502 / 15.507 / 15.581 | 7.585 | -51.07% | FAIL |

a3-qwen35-tp4-longctx-p-65536-c8: scored 65 / 65 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65664 tokens.
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 1 | 4 | 65536 | 10 | 14.477 / 14.397 / 14.516 | 9.027 | -37.65% | FAIL |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 2 | 4 | 65536 | 1 | 17.269 / 17.269 / 17.269 | 9.422 | -45.44% | FAIL |

a5-qwen35-tp4-longctx-p65536-c4-o32: scored 11 / 11 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65568 tokens.
| a5-qwen38-tp1-longctx-p126976-c4 | 1 | 4 | 126976 | 9 | 32.215 / 32.211 / 32.237 | 27.823 | -13.63% | PASS |
| a5-qwen38-tp1-longctx-p126976-c4 | 2 | 4 | 126976 | 8 | 35.503 / 35.500 / 35.516 | 28.757 | -19.00% | FAIL |

a5-qwen38-tp1-longctx-p126976-c4: scored 17 / 17 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 126976, bounds 126976–127008 tokens.
| a5-qwen38-tp1-longctx-p65536-c4 | 1 | 4 | 65536 | 5 | 24.481 / 24.481 / 24.493 | 20.197 | -17.50% | FAIL |
| a5-qwen38-tp1-longctx-p65536-c4 | 2 | 4 | 65536 | 4 | 26.848 / 26.851 / 26.858 | 21.131 | -21.29% | FAIL |
| a5-qwen38-tp1-longctx-p65536-c4 | 4 | 4 | 65536 | 2 | 29.056 / 29.056 / 29.389 | 22.959 | -20.98% | FAIL |

a5-qwen38-tp1-longctx-p65536-c4: scored 11 / 11 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65568 tokens.
| a3-qwen35-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 47 | 27.914 / 27.905 / 28.026 | 20.804 | -25.47% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 5 | 27.606 / 27.594 / 27.674 | 20.804 | -24.64% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 4 | 4 | 24512 | 3 | 20.159 / 20.179 / 20.344 | 12.714 | -36.93% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 2 | 26.737 / 26.737 / 26.783 | 20.804 | -22.19% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 6 | 4 | 24512 | 2 | 22.561 / 22.561 / 22.616 | 16.067 | -28.78% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 3 | 4 | 24512 | 2 | 19.339 / 19.339 / 19.366 | 11.314 | -41.50% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 2 | 4 | 24512 | 2 | 18.245 / 18.245 / 18.469 | 9.863 | -45.94% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 1 | 27.320 / 27.320 / 27.320 | 20.804 | -23.85% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 8 | 4 | 24512 | 1 | 25.229 / 25.229 / 25.229 | 18.899 | -25.09% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 1 | 4 | 24512 | 1 | 16.443 / 16.443 / 16.443 | 8.519 | -48.19% | FAIL |

a3-qwen35-tp4-decode-c12-p24512: scored 66 / 66 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 45 | 30.548 / 30.507 / 30.812 | 25.769 | -15.64% | FAIL |
| a3-qwen35-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 5 | 29.822 / 29.824 / 29.931 | 25.769 | -13.59% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 2 | 4 | 64512 | 3 | 18.649 / 18.670 / 18.717 | 10.712 | -42.56% | FAIL |
| a3-qwen35-tp4-decode-c12-p64512 | 1 | 4 | 64512 | 3 | 17.131 / 17.174 / 17.190 | 8.949 | -47.76% | FAIL |
| a3-qwen35-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 2 | 30.154 / 30.154 / 30.172 | 25.769 | -14.54% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 8 | 4 | 64512 | 2 | 27.144 / 27.144 / 27.191 | 22.176 | -18.30% | FAIL |
| a3-qwen35-tp4-decode-c12-p64512 | 4 | 4 | 64512 | 2 | 21.293 / 21.293 / 21.391 | 14.408 | -32.34% | FAIL |
| a3-qwen35-tp4-decode-c12-p64512 | 8 | 4 | 64512 | 1 | 26.644 / 26.644 / 26.644 | 22.176 | -16.77% | FAIL |
| a3-qwen35-tp4-decode-c12-p64512 | 6 | 4 | 64512 | 1 | 24.465 / 24.465 / 24.465 | 18.502 | -24.37% | FAIL |
| a3-qwen35-tp4-decode-c12-p64512 | 6 | 4 | 64512 | 1 | 24.030 / 24.030 / 24.030 | 18.502 | -23.01% | FAIL |

a3-qwen35-tp4-decode-c12-p64512: scored 65 / 65 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c12-p8512 | 12 | 4 | 8512 | 43 | 27.435 / 27.433 / 27.570 | 19.490 | -28.96% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 8 | 4 | 8512 | 4 | 24.846 / 24.637 / 25.539 | 17.599 | -29.16% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 12 | 4 | 8512 | 3 | 26.729 / 26.732 / 26.738 | 19.490 | -27.08% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 1 | 4 | 8512 | 3 | 16.478 / 16.400 / 16.704 | 8.310 | -49.56% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 12 | 4 | 8512 | 2 | 26.571 / 26.571 / 26.579 | 19.490 | -26.65% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 6 | 4 | 8512 | 2 | 22.579 / 22.579 / 23.015 | 15.086 | -33.18% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 2 | 4 | 8512 | 2 | 18.301 / 18.301 / 18.746 | 9.611 | -47.48% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 6 | 4 | 8512 | 1 | 22.895 / 22.895 / 22.895 | 15.086 | -34.11% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 4 | 4 | 8512 | 1 | 20.122 / 20.122 / 20.122 | 12.078 | -39.97% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 3 | 4 | 8512 | 1 | 19.868 / 19.868 / 19.868 | 10.789 | -45.70% | FAIL |

a3-qwen35-tp4-decode-c12-p8512: scored 62 / 62 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 58 | 33.166 / 33.160 / 33.280 | 29.772 | -10.23% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 2 | 4 | 96512 | 4 | 19.093 / 19.097 / 19.126 | 11.397 | -40.31% | FAIL |
| a3-qwen35-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 2 | 32.148 / 32.148 / 32.172 | 29.772 | -7.39% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 6 | 4 | 96512 | 2 | 24.892 / 24.892 / 24.934 | 20.559 | -17.41% | FAIL |
| a3-qwen35-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 1 | 32.464 / 32.464 / 32.464 | 29.772 | -8.29% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 1 | 30.525 / 30.525 / 30.525 | 29.772 | -2.47% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 8 | 4 | 96512 | 1 | 29.152 / 29.152 / 29.152 | 24.807 | -14.90% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 8 | 4 | 96512 | 1 | 28.172 / 28.172 / 28.172 | 24.807 | -11.94% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 6 | 4 | 96512 | 1 | 25.749 / 25.749 / 25.749 | 20.559 | -20.16% | FAIL |
| a3-qwen35-tp4-decode-c12-p96512 | 3 | 4 | 96512 | 1 | 20.650 / 20.650 / 20.650 | 13.536 | -34.45% | FAIL |

a3-qwen35-tp4-decode-c12-p96512: scored 72 / 72 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 66 | 35.550 / 35.558 / 35.723 | 26.891 | -24.36% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 4 | 35.286 / 35.290 / 35.309 | 26.891 | -23.79% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | 16 | 4 | 24512 | 2 | 29.030 / 29.030 / 29.088 | 22.779 | -21.53% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 1 | 35.290 / 35.290 / 35.290 | 26.891 | -23.80% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 1 | 35.251 / 35.251 / 35.251 | 26.891 | -23.72% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 1 | 32.578 / 32.578 / 32.578 | 26.891 | -17.46% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 1 | 32.499 / 32.499 / 32.499 | 26.891 | -17.26% | FAIL |

a3-qwen35-tp4-decode-c24-p24512: scored 76 / 76 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 57 | 31.676 / 31.677 / 31.775 | 22.727 | -28.25% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 5 | 31.676 / 31.674 / 31.785 | 22.727 | -28.25% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 1 | 4 | 8512 | 4 | 16.276 / 16.290 / 16.309 | 8.310 | -48.94% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 8 | 4 | 8512 | 3 | 24.803 / 24.876 / 24.914 | 17.599 | -29.04% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 2 | 31.743 / 31.743 / 31.762 | 22.727 | -28.40% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 6 | 4 | 8512 | 2 | 23.229 / 23.229 / 23.757 | 15.086 | -35.05% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 4 | 4 | 8512 | 2 | 19.631 / 19.631 / 19.754 | 12.078 | -38.47% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 1 | 30.205 / 30.205 / 30.205 | 22.727 | -24.76% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 1 | 30.045 / 30.045 / 30.045 | 22.727 | -24.36% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 16 | 4 | 8512 | 1 | 27.966 / 27.966 / 27.966 | 20.410 | -27.02% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 12 | 4 | 8512 | 1 | 27.150 / 27.150 / 27.150 | 19.490 | -28.21% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 12 | 4 | 8512 | 1 | 26.616 / 26.616 / 26.616 | 19.490 | -26.77% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 12 | 4 | 8512 | 1 | 26.505 / 26.505 / 26.505 | 19.490 | -26.46% | FAIL |

a3-qwen35-tp4-decode-c24-p8512: scored 81 / 81 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c2-p24512 | 1 | 4 | 24512 | 16 | 16.697 / 16.657 / 16.860 | 8.519 | -48.98% | FAIL |
| a3-qwen35-tp4-decode-c2-p24512 | 2 | 4 | 24512 | 2 | 18.147 / 18.147 / 18.217 | 9.863 | -45.65% | FAIL |

a3-qwen35-tp4-decode-c2-p24512: scored 18 / 18 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c2-p64512 | 1 | 4 | 64512 | 7 | 17.136 / 17.138 / 17.270 | 8.949 | -47.77% | FAIL |
| a3-qwen35-tp4-decode-c2-p64512 | 2 | 4 | 64512 | 4 | 18.681 / 18.662 / 18.872 | 10.712 | -42.66% | FAIL |

a3-qwen35-tp4-decode-c2-p64512: scored 11 / 11 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c2-p96512 | 1 | 4 | 96512 | 12 | 17.338 / 17.324 / 17.456 | 9.266 | -46.56% | FAIL |
| a3-qwen35-tp4-decode-c2-p96512 | 2 | 4 | 96512 | 1 | 19.025 / 19.025 / 19.025 | 11.397 | -40.09% | FAIL |

a3-qwen35-tp4-decode-c2-p96512: scored 13 / 13 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c6-p24512 | 6 | 4 | 24512 | 23 | 23.225 / 23.181 / 23.327 | 16.067 | -30.82% | FAIL |
| a3-qwen35-tp4-decode-c6-p24512 | 6 | 4 | 24512 | 10 | 22.732 / 22.725 / 22.825 | 16.067 | -29.32% | FAIL |
| a3-qwen35-tp4-decode-c6-p24512 | 1 | 4 | 24512 | 8 | 16.594 / 16.577 / 16.924 | 8.519 | -48.66% | FAIL |
| a3-qwen35-tp4-decode-c6-p24512 | 2 | 4 | 24512 | 3 | 18.051 / 18.068 / 18.143 | 9.863 | -45.36% | FAIL |
| a3-qwen35-tp4-decode-c6-p24512 | 3 | 4 | 24512 | 1 | 19.134 / 19.134 / 19.134 | 11.314 | -40.87% | FAIL |

a3-qwen35-tp4-decode-c6-p24512: scored 45 / 45 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c6-p64512 | 6 | 4 | 64512 | 40 | 24.666 / 24.667 / 24.763 | 18.502 | -24.99% | FAIL |
| a3-qwen35-tp4-decode-c6-p64512 | 2 | 4 | 64512 | 2 | 18.846 / 18.846 / 18.912 | 10.712 | -43.16% | FAIL |
| a3-qwen35-tp4-decode-c6-p64512 | 6 | 4 | 64512 | 1 | 24.044 / 24.044 / 24.044 | 18.502 | -23.05% | FAIL |
| a3-qwen35-tp4-decode-c6-p64512 | 3 | 4 | 64512 | 1 | 20.966 / 20.966 / 20.966 | 12.486 | -40.45% | FAIL |

a3-qwen35-tp4-decode-c6-p64512: scored 44 / 44 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c6-p8512 | 6 | 4 | 8512 | 21 | 22.846 / 22.849 / 22.926 | 15.086 | -33.97% | FAIL |
| a3-qwen35-tp4-decode-c6-p8512 | 6 | 4 | 8512 | 6 | 22.307 / 22.130 / 23.271 | 15.086 | -32.37% | FAIL |
| a3-qwen35-tp4-decode-c6-p8512 | 1 | 4 | 8512 | 4 | 16.413 / 16.480 / 16.495 | 8.310 | -49.37% | FAIL |
| a3-qwen35-tp4-decode-c6-p8512 | 4 | 4 | 8512 | 3 | 19.802 / 19.803 / 19.841 | 12.078 | -39.01% | FAIL |
| a3-qwen35-tp4-decode-c6-p8512 | 2 | 4 | 8512 | 3 | 17.950 / 17.777 / 18.306 | 9.611 | -46.45% | FAIL |

a3-qwen35-tp4-decode-c6-p8512: scored 37 / 37 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c6-p96512 | 6 | 4 | 96512 | 42 | 26.149 / 25.837 / 26.090 | 20.559 | -21.38% | FAIL |
| a3-qwen35-tp4-decode-c6-p96512 | 1 | 4 | 96512 | 3 | 17.198 / 17.217 / 17.249 | 9.266 | -46.12% | FAIL |
| a3-qwen35-tp4-decode-c6-p96512 | 4 | 4 | 96512 | 2 | 22.157 / 22.157 / 22.231 | 15.726 | -29.02% | FAIL |
| a3-qwen35-tp4-decode-c6-p96512 | 3 | 4 | 96512 | 2 | 20.734 / 20.734 / 20.752 | 13.536 | -34.72% | FAIL |
| a3-qwen35-tp4-decode-c6-p96512 | 6 | 4 | 96512 | 1 | 24.858 / 24.858 / 24.858 | 20.559 | -17.29% | FAIL |
| a3-qwen35-tp4-decode-c6-p96512 | 2 | 4 | 96512 | 1 | 19.098 / 19.098 / 19.098 | 11.397 | -40.32% | FAIL |

a3-qwen35-tp4-decode-c6-p96512: scored 51 / 51 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c2-p24512 | 2 | 4 | 24512 | 58 | 26.724 / 26.694 / 26.806 | 21.700 | -18.80% | FAIL |
| a3-qwen36-tp2-decode-c2-p24512 | 1 | 4 | 24512 | 4 | 24.082 / 24.057 / 24.170 | 19.554 | -18.80% | FAIL |

a3-qwen36-tp2-decode-c2-p24512: scored 62 / 62 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c2-p64512 | 2 | 4 | 64512 | 58 | 28.868 / 28.845 / 28.903 | 24.493 | -15.16% | FAIL |
| a3-qwen36-tp2-decode-c2-p64512 | 1 | 4 | 64512 | 2 | 25.571 / 25.571 / 25.671 | 20.956 | -18.05% | FAIL |

a3-qwen36-tp2-decode-c2-p64512: scored 60 / 60 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c2-p8512 | 2 | 4 | 8512 | 45 | 25.809 / 25.747 / 25.801 | 20.650 | -19.99% | FAIL |
| a3-qwen36-tp2-decode-c2-p8512 | 1 | 4 | 8512 | 1 | 23.898 / 23.898 / 23.898 | 19.139 | -19.92% | FAIL |

a3-qwen36-tp2-decode-c2-p8512: scored 46 / 46 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c2-p96512 | 2 | 4 | 96512 | 62 | 30.222 / 30.218 / 30.266 | 26.665 | -11.77% | PASS |
| a3-qwen36-tp2-decode-c2-p96512 | 1 | 4 | 96512 | 8 | 26.458 / 26.465 / 26.476 | 22.085 | -16.53% | FAIL |

a3-qwen36-tp2-decode-c2-p96512: scored 70 / 70 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c6-p24512 | 6 | 4 | 24512 | 71 | 33.717 / 33.762 / 33.825 | 29.011 | -13.96% | PASS |
| a3-qwen36-tp2-decode-c6-p24512 | 6 | 4 | 24512 | 3 | 32.197 / 32.189 / 32.215 | 29.011 | -9.90% | PASS |
| a3-qwen36-tp2-decode-c6-p24512 | 2 | 4 | 24512 | 3 | 26.611 / 26.592 / 26.658 | 21.700 | -18.46% | FAIL |
| a3-qwen36-tp2-decode-c6-p24512 | 3 | 4 | 24512 | 2 | 28.284 / 28.284 / 28.296 | 23.298 | -17.63% | FAIL |
| a3-qwen36-tp2-decode-c6-p24512 | 1 | 4 | 24512 | 2 | 24.086 / 24.086 / 24.086 | 19.554 | -18.82% | FAIL |

a3-qwen36-tp2-decode-c6-p24512: scored 81 / 81 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c6-p8512 | 6 | 4 | 8512 | 61 | 32.027 / 31.966 / 32.038 | 26.840 | -16.19% | FAIL |
| a3-qwen36-tp2-decode-c6-p8512 | 2 | 4 | 8512 | 4 | 25.655 / 25.632 / 25.749 | 20.650 | -19.51% | FAIL |
| a3-qwen36-tp2-decode-c6-p8512 | 4 | 4 | 8512 | 3 | 29.068 / 29.004 / 29.228 | 23.282 | -19.90% | FAIL |
| a3-qwen36-tp2-decode-c6-p8512 | 6 | 4 | 8512 | 2 | 31.017 / 31.017 / 31.028 | 26.840 | -13.47% | PASS |
| a3-qwen36-tp2-decode-c6-p8512 | 3 | 4 | 8512 | 2 | 26.970 / 26.970 / 26.987 | 21.688 | -19.58% | FAIL |

a3-qwen36-tp2-decode-c6-p8512: scored 72 / 72 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 56 | 30.908 / 30.898 / 30.968 | 24.882 | -19.50% | FAIL |
| a3-qwen38-tp4-decode-c12-p24512 | 1 | 4 | 24512 | 5 | 17.858 / 17.763 / 18.319 | 13.997 | -21.62% | FAIL |
| a3-qwen38-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 4 | 29.450 / 29.456 / 29.484 | 24.882 | -15.51% | FAIL |
| a3-qwen38-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 3 | 30.283 / 30.285 / 30.300 | 24.882 | -17.83% | FAIL |
| a3-qwen38-tp4-decode-c12-p24512 | 2 | 4 | 24512 | 2 | 19.259 / 19.259 / 19.377 | 14.759 | -23.37% | FAIL |
| a3-qwen38-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 1 | 28.776 / 28.776 / 28.776 | 24.882 | -13.53% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 6 | 4 | 24512 | 1 | 24.934 / 24.934 / 24.934 | 18.769 | -24.73% | FAIL |
| a3-qwen38-tp4-decode-c12-p24512 | 6 | 4 | 24512 | 1 | 24.287 / 24.287 / 24.287 | 18.769 | -22.72% | FAIL |
| a3-qwen38-tp4-decode-c12-p24512 | 3 | 4 | 24512 | 1 | 20.102 / 20.102 / 20.102 | 15.722 | -21.79% | FAIL |

a3-qwen38-tp4-decode-c12-p24512: scored 74 / 74 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 68 | 35.845 / 35.986 / 36.161 | 33.065 | -7.76% | PASS |
| a3-qwen38-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 5 | 32.176 / 32.177 / 32.195 | 33.065 | +2.76% | PASS |
| a3-qwen38-tp4-decode-c12-p64512 | 8 | 4 | 64512 | 2 | 31.108 / 31.108 / 31.443 | 26.425 | -15.05% | FAIL |
| a3-qwen38-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 1 | 34.707 / 34.707 / 34.707 | 33.065 | -4.73% | PASS |

a3-qwen38-tp4-decode-c12-p64512: scored 76 / 76 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 65 | 39.782 / 39.852 / 40.095 | 39.653 | -0.33% | PASS |
| a3-qwen38-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 3 | 35.379 / 35.367 / 35.422 | 39.653 | +12.08% | PASS |
| a3-qwen38-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 2 | 38.252 / 38.252 / 38.309 | 39.653 | +3.66% | PASS |
| a3-qwen38-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 1 | 37.966 / 37.966 / 37.966 | 39.653 | +4.44% | PASS |

a3-qwen38-tp4-decode-c12-p96512: scored 71 / 71 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c2-p24512 | 2 | 4 | 24512 | 11 | 19.404 / 19.244 / 20.150 | 14.759 | -23.94% | FAIL |
| a3-qwen38-tp4-decode-c2-p24512 | 1 | 4 | 24512 | 4 | 17.817 / 17.836 / 17.873 | 13.997 | -21.44% | FAIL |

a3-qwen38-tp4-decode-c2-p24512: scored 15 / 15 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c2-p64512 | 2 | 4 | 64512 | 20 | 20.210 / 20.021 / 20.180 | 16.161 | -20.03% | FAIL |
| a3-qwen38-tp4-decode-c2-p64512 | 1 | 4 | 64512 | 3 | 18.455 / 18.447 / 18.491 | 14.713 | -20.28% | FAIL |

a3-qwen38-tp4-decode-c2-p64512: scored 23 / 23 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c2-p96512 | 2 | 4 | 96512 | 24 | 20.989 / 20.830 / 21.239 | 17.291 | -17.62% | FAIL |
| a3-qwen38-tp4-decode-c2-p96512 | 1 | 4 | 96512 | 3 | 19.328 / 19.048 / 19.910 | 15.235 | -21.18% | FAIL |

a3-qwen38-tp4-decode-c2-p96512: scored 27 / 27 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c6-p24512 | 6 | 4 | 24512 | 38 | 24.761 / 24.752 / 24.829 | 18.769 | -24.20% | FAIL |
| a3-qwen38-tp4-decode-c6-p24512 | 6 | 4 | 24512 | 3 | 24.323 / 24.320 / 24.333 | 18.769 | -22.83% | FAIL |
| a3-qwen38-tp4-decode-c6-p24512 | 2 | 4 | 24512 | 2 | 19.597 / 19.597 / 19.909 | 14.759 | -24.69% | FAIL |
| a3-qwen38-tp4-decode-c6-p24512 | 1 | 4 | 24512 | 2 | 17.817 / 17.817 / 17.863 | 13.997 | -21.44% | FAIL |
| a3-qwen38-tp4-decode-c6-p24512 | 4 | 4 | 24512 | 1 | 22.503 / 22.503 / 22.503 | 17.039 | -24.28% | FAIL |

a3-qwen38-tp4-decode-c6-p24512: scored 46 / 46 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c6-p64512 | 6 | 4 | 64512 | 40 | 27.237 / 27.135 / 27.365 | 22.786 | -16.34% | FAIL |
| a3-qwen38-tp4-decode-c6-p64512 | 4 | 4 | 64512 | 5 | 23.956 / 23.825 / 24.480 | 19.831 | -17.22% | FAIL |
| a3-qwen38-tp4-decode-c6-p64512 | 3 | 4 | 64512 | 4 | 22.568 / 22.104 / 24.375 | 17.660 | -21.75% | FAIL |
| a3-qwen38-tp4-decode-c6-p64512 | 6 | 4 | 64512 | 2 | 26.501 / 26.501 / 26.502 | 22.786 | -14.02% | PASS |
| a3-qwen38-tp4-decode-c6-p64512 | 2 | 4 | 64512 | 2 | 20.478 / 20.478 / 20.765 | 16.161 | -21.08% | FAIL |
| a3-qwen38-tp4-decode-c6-p64512 | 1 | 4 | 64512 | 2 | 18.774 / 18.774 / 19.076 | 14.713 | -21.63% | FAIL |

a3-qwen38-tp4-decode-c6-p64512: scored 55 / 55 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c6-p96512 | 6 | 4 | 96512 | 42 | 29.560 / 29.308 / 29.565 | 26.174 | -11.45% | PASS |
| a3-qwen38-tp4-decode-c6-p96512 | 1 | 4 | 96512 | 6 | 19.227 / 19.055 / 20.072 | 15.235 | -20.77% | FAIL |
| a3-qwen38-tp4-decode-c6-p96512 | 3 | 4 | 96512 | 5 | 22.911 / 22.846 / 23.176 | 19.385 | -15.39% | FAIL |
| a3-qwen38-tp4-decode-c6-p96512 | 6 | 4 | 96512 | 4 | 28.344 / 28.354 / 28.383 | 26.174 | -7.65% | PASS |
| a3-qwen38-tp4-decode-c6-p96512 | 2 | 4 | 96512 | 4 | 20.979 / 20.931 / 21.140 | 17.291 | -17.58% | FAIL |
| a3-qwen38-tp4-decode-c6-p96512 | 4 | 4 | 96512 | 3 | 25.537 / 25.517 / 25.608 | 22.003 | -13.84% | PASS |

a3-qwen38-tp4-decode-c6-p96512: scored 64 / 64 calls; all-population pass: False.
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
| glm53flash-a5-tp8-c3 | 4 / 4 | kda | 34 | 0.413 / 0.421 | 0.383 / 0.403 | -7.26% / -4.40% |
| glm53flash-a5-tp8-c3 | 4 / 4 | mla | 11 | 0.639 / 0.634 | 0.534 / 0.534 | -16.45% / -15.76% |
| glm53flash-a5-tp8-c3 | 4 / 4 | dense_layer | 3 | 0.314 / 0.240 | 0.175 / 0.175 | -44.20% / -27.07% |
| glm53flash-a5-tp8-c3 | 4 / 4 | moe_layer | 42 | 0.479 / 0.424 | 0.437 / 0.403 | -8.74% / -5.06% |
| glm53flash-a5-tp8-c96 | 96 / 4 | kda | 34 | 0.971 / 1.009 | 1.073 / 1.112 | +10.49% / +10.24% |
| glm53flash-a5-tp8-c96 | 96 / 4 | mla | 11 | 2.233 / 2.234 | 2.319 / 2.319 | +3.84% / +3.83% |
| glm53flash-a5-tp8-c96 | 96 / 4 | dense_layer | 3 | 0.583 / 0.573 | 0.669 / 0.669 | +14.85% / +16.86% |
| glm53flash-a5-tp8-c96 | 96 / 4 | moe_layer | 42 | 1.330 / 1.011 | 1.428 / 1.112 | +7.43% / +10.06% |
| glm53flash-a5-tp8-c1 | 1 / 4 | kda | 34 | 0.301 / 0.299 | 0.277 / 0.288 | -7.84% / -3.41% |
| glm53flash-a5-tp8-c1 | 1 / 4 | mla | 11 | 0.495 / 0.491 | 0.403 / 0.403 | -18.57% / -17.94% |
| glm53flash-a5-tp8-c1 | 1 / 4 | dense_layer | 3 | 0.307 / 0.263 | 0.165 / 0.165 | -46.32% / -37.55% |
| glm53flash-a5-tp8-c1 | 1 / 4 | moe_layer | 42 | 0.351 / 0.302 | 0.318 / 0.288 | -9.41% / -4.58% |
| a5_kimi_k3_p32768_c1 | 1 / 1 | kda | 69 | 0.338 / 0.339 | 0.309 / 0.311 | -8.57% / -8.30% |
| a5_kimi_k3_p32768_c1 | 1 / 1 | mla | 24 | 0.383 / 0.376 | 0.300 / 0.299 | -21.80% / -20.32% |
| a5_kimi_k3_p32768_c1 | 1 / 1 | dense_layer | 1 | 0.258 / 0.258 | 0.182 / 0.182 | -29.28% / -29.28% |
| a5_kimi_k3_p32768_c1 | 1 / 1 | moe_layer | 92 | 0.351 / 0.341 | 0.308 / 0.311 | -12.17% / -8.80% |
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
| a3_glm53_dc4k_b4 | 4 / 1 | mla | 78 | 0.556 / 0.540 | 0.495 / 0.487 | -10.92% / -9.82% |
| a3_glm53_dc4k_b4 | 4 / 1 | dense_layer | 3 | 0.402 / 0.399 | 0.358 / 0.358 | -10.84% / -10.23% |
| a3_glm53_dc4k_b4 | 4 / 1 | moe_layer | 75 | 0.562 / 0.541 | 0.501 / 0.487 | -10.93% / -9.95% |
| a3_glm53_dc4k_b8 | 8 / 1 | mla | 78 | 0.603 / 0.587 | 0.566 / 0.559 | -6.20% / -4.79% |
| a3_glm53_dc4k_b8 | 8 / 1 | dense_layer | 3 | 0.416 / 0.413 | 0.366 / 0.366 | -11.96% / -11.37% |
| a3_glm53_dc4k_b8 | 8 / 1 | moe_layer | 75 | 0.611 / 0.588 | 0.574 / 0.559 | -6.04% / -4.87% |
| a3_glm53_dc16k_b1 | 1 / 1 | mla | 78 | 0.500 / 0.483 | 0.491 / 0.473 | -1.77% / -2.10% |
| a3_glm53_dc16k_b1 | 1 / 1 | dense_layer | 3 | 0.396 / 0.394 | 0.404 / 0.403 | +1.87% / +2.47% |
| a3_glm53_dc16k_b1 | 1 / 1 | moe_layer | 75 | 0.504 / 0.483 | 0.495 / 0.473 | -1.88% / -2.24% |
| qwen35-397b-a3-tp16-c48 | 64 / 4 | gdn | 45 | 1.236 / 1.203 | 1.107 / 1.108 | -10.37% / -7.95% |
| qwen35-397b-a3-tp16-c48 | 64 / 4 | gqa | 15 | 1.361 / 1.341 | 1.137 / 1.137 | -16.48% / -15.26% |
| qwen35-397b-a3-tp16-c48 | 64 / 4 | moe_layer | 60 | 1.267 / 1.279 | 1.115 / 1.108 | -12.01% / -13.39% |
| qwen35-397b-a3-tp16-c136 | 160 / 4 | gdn | 45 | 1.959 / 1.940 | 1.726 / 1.726 | -11.90% / -11.03% |
| qwen35-397b-a3-tp16-c136 | 160 / 4 | gqa | 15 | 2.054 / 2.022 | 1.805 / 1.805 | -12.16% / -10.75% |
| qwen35-397b-a3-tp16-c136 | 160 / 4 | moe_layer | 60 | 1.983 / 1.996 | 1.746 / 1.726 | -11.97% / -13.54% |
| qwen35-35b-a5-tp4-c64-graph | 64 / 4 | gdn | 30 | 0.555 / 0.547 | 0.513 / 0.513 | -7.44% / -6.17% |
| qwen35-35b-a5-tp4-c64-graph | 64 / 4 | gqa | 10 | 0.532 / 0.532 | 0.458 / 0.458 | -13.98% / -14.06% |
| qwen35-35b-a5-tp4-c64-graph | 64 / 4 | moe_layer | 40 | 0.549 / 0.546 | 0.499 / 0.513 | -9.02% / -5.95% |
| qwen35-35b-a5-tp4-c128-graph | 128 / 4 | gdn | 30 | 0.721 / 0.720 | 0.671 / 0.671 | -6.89% / -6.77% |
| qwen35-35b-a5-tp4-c128-graph | 128 / 4 | gqa | 10 | 0.695 / 0.695 | 0.592 / 0.592 | -14.88% / -14.79% |
| qwen35-35b-a5-tp4-c128-graph | 128 / 4 | moe_layer | 40 | 0.715 / 0.720 | 0.651 / 0.671 | -8.83% / -6.70% |
| qwen35-35b-a5-tp4-c4-graph | 4 / 4 | gdn | 30 | 0.285 / 0.282 | 0.249 / 0.249 | -12.83% / -11.89% |
| qwen35-35b-a5-tp4-c4-graph | 4 / 4 | gqa | 10 | 0.299 / 0.299 | 0.244 / 0.244 | -18.45% / -18.44% |
| qwen35-35b-a5-tp4-c4-graph | 4 / 4 | moe_layer | 40 | 0.289 / 0.283 | 0.248 / 0.249 | -14.28% / -12.11% |
| qwen36-a5-tp2-c12 | 12 / 4 | gdn | 48 | 0.409 / 0.404 | 0.370 / 0.370 | -9.45% / -8.37% |
| qwen36-a5-tp2-c12 | 12 / 4 | gqa | 16 | 0.285 / 0.284 | 0.232 / 0.232 | -18.49% / -18.46% |
| qwen36-a5-tp2-c12 | 12 / 4 | dense_layer | 64 | 0.378 / 0.402 | 0.336 / 0.370 | -11.16% / -7.95% |
| qwen36-a5-tp2-c96 | 96 / 4 | gdn | 48 | 1.065 / 1.059 | 1.046 / 1.046 | -1.78% / -1.21% |
| qwen36-a5-tp2-c96 | 96 / 4 | gqa | 16 | 0.793 / 0.793 | 0.790 / 0.790 | -0.44% / -0.41% |
| qwen36-a5-tp2-c96 | 96 / 4 | dense_layer | 64 | 0.997 / 1.058 | 0.982 / 1.046 | -1.52% / -1.10% |
| qwen36-a5-tp2-c1 | 1 / 4 | gdn | 48 | 0.193 / 0.192 | 0.175 / 0.175 | -9.26% / -8.67% |
| qwen36-a5-tp2-c1 | 1 / 4 | gqa | 16 | 0.188 / 0.188 | 0.145 / 0.145 | -22.96% / -23.02% |
| qwen36-a5-tp2-c1 | 1 / 4 | dense_layer | 64 | 0.192 / 0.191 | 0.167 / 0.175 | -12.62% / -8.51% |
| a3_glm53_w4a8_tp16_tpot30_c2 | 2 / 6 | mla | 78 | 0.739 / 0.743 | 0.636 / 0.616 | -13.97% / -17.15% |
| a3_glm53_w4a8_tp16_tpot30_c2 | 2 / 6 | dense_layer | 3 | 0.573 / 0.577 | 0.492 / 0.492 | -14.08% / -14.83% |
| a3_glm53_w4a8_tp16_tpot30_c2 | 2 / 6 | moe_layer | 75 | 0.746 / 0.746 | 0.641 / 0.616 | -13.97% / -17.44% |
| a3_glm53_w4a8_tp16_tpot50_c2 | 2 / 6 | mla | 78 | 0.741 / 0.741 | 0.635 / 0.615 | -14.29% / -16.99% |
| a3_glm53_w4a8_tp16_tpot50_c2 | 2 / 6 | dense_layer | 3 | 0.588 / 0.568 | 0.492 / 0.492 | -16.23% / -13.38% |
| a3_glm53_w4a8_tp16_tpot50_c2 | 2 / 6 | moe_layer | 75 | 0.747 / 0.742 | 0.641 / 0.615 | -14.22% / -17.09% |
| a3_glm53_w4a8_tp16_tpot88_c8 | 8 / 6 | mla | 78 | 0.892 / 0.867 | 0.856 / 0.829 | -4.01% / -4.28% |
| a3_glm53_w4a8_tp16_tpot88_c8 | 8 / 6 | dense_layer | 3 | 0.647 / 0.656 | 0.671 / 0.672 | +3.73% / +2.45% |
| a3_glm53_w4a8_tp16_tpot88_c8 | 8 / 6 | moe_layer | 75 | 0.901 / 0.867 | 0.863 / 0.829 | -4.23% / -4.33% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | 1 / 1 | mla | 40 | 0.328 / 0.299 | 0.311 / 0.300 | -5.30% / +0.34% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | 1 / 1 | moe_layer | 40 | 0.328 / 0.299 | 0.311 / 0.300 | -5.30% / +0.34% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | 1 / 1 | mla | 40 | 0.332 / 0.302 | 0.304 / 0.293 | -8.53% / -2.86% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | 1 / 1 | moe_layer | 40 | 0.332 / 0.302 | 0.304 / 0.293 | -8.53% / -2.86% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 8 / 1 | mla | 40 | 0.658 / 0.634 | 0.620 / 0.608 | -5.75% / -4.00% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 8 / 1 | moe_layer | 40 | 0.658 / 0.634 | 0.620 / 0.608 | -5.75% / -4.00% |
| a5_glm53flash_tp8_c16_p4k | 16 / 4 | kda | 34 | 0.647 / 0.677 | 0.599 / 0.634 | -7.42% / -6.32% |
| a5_glm53flash_tp8_c16_p4k | 16 / 4 | mla | 11 | 1.002 / 0.997 | 0.827 / 0.827 | -17.43% / -17.05% |
| a5_glm53flash_tp8_c16_p4k | 16 / 4 | dense_layer | 3 | 0.331 / 0.299 | 0.239 / 0.239 | -27.91% / -20.09% |
| a5_glm53flash_tp8_c16_p4k | 16 / 4 | moe_layer | 42 | 0.763 / 0.680 | 0.685 / 0.634 | -10.23% / -6.76% |
| a5_glm53flash_tp8_c16_p8k | 16 / 4 | kda | 34 | 0.646 / 0.677 | 0.599 / 0.633 | -7.34% / -6.38% |
| a5_glm53flash_tp8_c16_p8k | 16 / 4 | mla | 11 | 1.059 / 1.055 | 0.831 / 0.831 | -21.57% / -21.28% |
| a5_glm53flash_tp8_c16_p8k | 16 / 4 | dense_layer | 3 | 0.328 / 0.298 | 0.239 / 0.239 | -27.21% / -19.96% |
| a5_glm53flash_tp8_c16_p8k | 16 / 4 | moe_layer | 42 | 0.777 / 0.678 | 0.685 / 0.633 | -11.82% / -6.59% |
| a5_glm53flash_tp8_c32_p4k | 32 / 4 | kda | 34 | 0.721 / 0.752 | 0.677 / 0.714 | -6.09% / -5.04% |
| a5_glm53flash_tp8_c32_p4k | 32 / 4 | mla | 11 | 1.197 / 1.194 | 1.053 / 1.053 | -12.04% / -11.78% |
| a5_glm53flash_tp8_c32_p4k | 32 / 4 | dense_layer | 3 | 0.398 / 0.353 | 0.286 / 0.286 | -28.05% / -18.96% |
| a5_glm53flash_tp8_c32_p4k | 32 / 4 | moe_layer | 42 | 0.868 / 0.754 | 0.803 / 0.714 | -7.52% / -5.26% |
| a5_glm53flash_tp8_c32_p8k | 32 / 4 | kda | 34 | 0.720 / 0.751 | 0.676 / 0.713 | -6.13% / -4.94% |
| a5_glm53flash_tp8_c32_p8k | 32 / 4 | mla | 11 | 1.295 / 1.291 | 1.062 / 1.062 | -17.98% / -17.74% |
| a5_glm53flash_tp8_c32_p8k | 32 / 4 | dense_layer | 3 | 0.399 / 0.354 | 0.285 / 0.285 | -28.50% / -19.41% |
| a5_glm53flash_tp8_c32_p8k | 32 / 4 | moe_layer | 42 | 0.893 / 0.753 | 0.805 / 0.713 | -9.91% / -5.28% |
| a5_glm53flash_tp8_c4_p8k | 4 / 4 | kda | 34 | 0.412 / 0.425 | 0.376 / 0.395 | -8.68% / -6.90% |
| a5_glm53flash_tp8_c4_p8k | 4 / 4 | mla | 11 | 0.673 / 0.670 | 0.534 / 0.534 | -20.73% / -20.30% |
| a5_glm53flash_tp8_c4_p8k | 4 / 4 | dense_layer | 3 | 0.264 / 0.235 | 0.179 / 0.179 | -32.29% / -23.92% |
| a5_glm53flash_tp8_c4_p8k | 4 / 4 | moe_layer | 42 | 0.491 / 0.429 | 0.432 / 0.395 | -12.10% / -7.75% |
| a5_glm53flash_tp8_c64_p4k | 64 / 4 | kda | 34 | 0.853 / 0.886 | 0.857 / 0.900 | +0.43% / +1.51% |
| a5_glm53flash_tp8_c64_p4k | 64 / 4 | mla | 11 | 1.593 / 1.584 | 1.531 / 1.531 | -3.87% / -3.34% |
| a5_glm53flash_tp8_c64_p4k | 64 / 4 | dense_layer | 3 | 0.497 / 0.470 | 0.413 / 0.413 | -16.86% / -12.17% |
| a5_glm53flash_tp8_c64_p4k | 64 / 4 | moe_layer | 42 | 1.072 / 0.890 | 1.065 / 0.900 | -0.67% / +1.14% |
| a5_glm53flash_tp8_c8_p4k | 8 / 4 | kda | 34 | 0.567 / 0.589 | 0.525 / 0.555 | -7.53% / -5.67% |
| a5_glm53flash_tp8_c8_p4k | 8 / 4 | mla | 11 | 0.868 / 0.868 | 0.670 / 0.670 | -22.85% / -22.85% |
| a5_glm53flash_tp8_c8_p4k | 8 / 4 | dense_layer | 3 | 0.335 / 0.258 | 0.207 / 0.207 | -38.31% / -19.84% |
| a5_glm53flash_tp8_c8_p4k | 8 / 4 | moe_layer | 42 | 0.663 / 0.593 | 0.585 / 0.555 | -11.67% / -6.38% |
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
| a3_glm53flash_tp16_aclgraph_c8 | 8 / 6 | kda | 34 | 0.921 / 0.948 | 0.817 / 0.860 | -11.23% / -9.24% |
| a3_glm53flash_tp16_aclgraph_c8 | 8 / 6 | mla | 11 | 1.410 / 1.410 | 1.276 / 1.276 | -9.51% / -9.50% |
| a3_glm53flash_tp16_aclgraph_c8 | 8 / 6 | dense_layer | 3 | 0.624 / 0.618 | 0.374 / 0.374 | -40.07% / -39.50% |
| a3_glm53flash_tp16_aclgraph_c8 | 8 / 6 | moe_layer | 42 | 1.070 / 0.952 | 0.969 / 0.860 | -9.44% / -9.68% |
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
| a3_kimi4_tp8_w4a8_c16 | 16 / 1 | kda | 3 | 1.118 / 1.189 | 0.990 / 1.179 | -11.45% / -0.89% |
| a3_kimi4_tp8_w4a8_c16 | 16 / 1 | mla | 1 | 1.453 / 1.453 | 1.134 / 1.134 | -21.96% / -21.96% |
| a3_kimi4_tp8_w4a8_c16 | 16 / 1 | dense_layer | 1 | 0.849 / 0.849 | 0.612 / 0.612 | -27.99% / -27.99% |
| a3_kimi4_tp8_w4a8_c16 | 16 / 1 | moe_layer | 3 | 1.319 / 1.314 | 1.164 / 1.179 | -11.76% / -10.33% |
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
| a5_kimi_tp8_e16_bf16_c32_p16k | 32 / 1 | mla | 24 | 0.672 / 0.665 | 0.634 / 0.634 | -5.53% / -4.56% |
| a5_kimi_tp8_e16_bf16_c32_p16k | 32 / 1 | dense_layer | 1 | 0.362 / 0.362 | 0.252 / 0.252 | -30.39% / -30.39% |
| a5_kimi_tp8_e16_bf16_c32_p16k | 32 / 1 | moe_layer | 92 | 0.482 / 0.416 | 0.455 / 0.396 | -5.44% / -4.83% |
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
| qwen35-35b-a3-tp4-c144 | 160 / 4 | gdn | 30 | 1.579 / 1.574 | 1.375 / 1.375 | -12.92% / -12.65% |
| qwen35-35b-a3-tp4-c144 | 160 / 4 | gqa | 10 | 1.435 / 1.432 | 1.242 / 1.242 | -13.48% / -13.26% |
| qwen35-35b-a3-tp4-c144 | 160 / 4 | moe_layer | 40 | 1.543 / 1.572 | 1.342 / 1.375 | -13.05% / -12.54% |
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
| a5_qwen36_highconc_c4 | 4 / 4 | gdn | 48 | 0.216 / 0.177 | 0.187 / 0.187 | -13.51% / +5.35% |
| a5_qwen36_highconc_c4 | 4 / 4 | gqa | 16 | 0.183 / 0.183 | 0.162 / 0.162 | -11.76% / -11.45% |
| a5_qwen36_highconc_c4 | 4 / 4 | dense_layer | 64 | 0.208 / 0.178 | 0.180 / 0.187 | -13.12% / +5.09% |
| a5_qwen36_highconc_c40 | 40 / 4 | gdn | 48 | 0.333 / 0.308 | 0.296 / 0.296 | -11.19% / -3.84% |
| a5_qwen36_highconc_c40 | 40 / 4 | gqa | 16 | 0.290 / 0.290 | 0.242 / 0.242 | -16.61% / -16.63% |
| a5_qwen36_highconc_c40 | 40 / 4 | dense_layer | 64 | 0.322 / 0.307 | 0.282 / 0.296 | -12.41% / -3.58% |
| a5_qwen36_highconc_c128 | 128 / 4 | gdn | 48 | 0.516 / 0.500 | 0.514 / 0.514 | -0.26% / +2.78% |
| a5_qwen36_highconc_c128 | 128 / 4 | gqa | 16 | 0.488 / 0.488 | 0.452 / 0.452 | -7.42% / -7.41% |
| a5_qwen36_highconc_c128 | 128 / 4 | dense_layer | 64 | 0.509 / 0.500 | 0.499 / 0.514 | -1.98% / +2.89% |
| a5_qwen38_highconc_c4 | 4 / 4 | gdn | 48 | 0.208 / 0.208 | 0.193 / 0.193 | -6.99% / -6.96% |
| a5_qwen38_highconc_c4 | 4 / 4 | gqa | 16 | 0.188 / 0.182 | 0.132 / 0.132 | -29.69% / -27.42% |
| a5_qwen38_highconc_c4 | 4 / 4 | dense_layer | 64 | 0.203 / 0.207 | 0.178 / 0.193 | -12.24% / -6.74% |
| a5_qwen38_highconc_c32 | 32 / 4 | gdn | 48 | 0.381 / 0.382 | 0.354 / 0.354 | -7.17% / -7.28% |
| a5_qwen38_highconc_c32 | 32 / 4 | gqa | 16 | 0.278 / 0.274 | 0.192 / 0.192 | -30.74% / -29.86% |
| a5_qwen38_highconc_c32 | 32 / 4 | dense_layer | 64 | 0.355 / 0.379 | 0.313 / 0.354 | -11.77% / -6.63% |
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
| a5_glm53flash_heldout_c12_p4k | 2 / 4 | kda | 34 | 0.340 / 0.343 | 0.324 / 0.339 | -4.60% / -1.15% |
| a5_glm53flash_heldout_c12_p4k | 2 / 4 | mla | 11 | 0.598 / 0.595 | 0.407 / 0.407 | -32.07% / -31.66% |
| a5_glm53flash_heldout_c12_p4k | 2 / 4 | dense_layer | 3 | 0.289 / 0.237 | 0.173 / 0.173 | -40.01% / -26.95% |
| a5_glm53flash_heldout_c12_p4k | 2 / 4 | moe_layer | 42 | 0.411 / 0.346 | 0.356 / 0.339 | -13.29% / -2.21% |
| a5_glm53flash_heldout_c24_p12k | 24 / 4 | kda | 34 | 0.692 / 0.725 | 0.628 / 0.665 | -9.19% / -8.34% |
| a5_glm53flash_heldout_c24_p12k | 24 / 4 | mla | 11 | 1.406 / 1.404 | 1.116 / 1.116 | -20.62% / -20.54% |
| a5_glm53flash_heldout_c24_p12k | 24 / 4 | dense_layer | 3 | 0.345 / 0.334 | 0.255 / 0.255 | -26.22% / -23.72% |
| a5_glm53flash_heldout_c24_p12k | 24 / 4 | moe_layer | 42 | 0.904 / 0.728 | 0.783 / 0.665 | -13.39% / -8.74% |
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
| a3-qwen35-tp4-longctx-p-126976-c1 | 1 / 2 | gdn | 30 | 0.367 / 0.367 | 0.183 / 0.183 | -50.03% / -50.07% |
| a3-qwen35-tp4-longctx-p-126976-c1 | 1 / 2 | gqa | 10 | 0.499 / 0.500 | 0.270 / 0.270 | -45.96% / -46.08% |
| a3-qwen35-tp4-longctx-p-126976-c1 | 1 / 2 | moe_layer | 40 | 0.400 / 0.370 | 0.205 / 0.183 | -48.76% / -50.47% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 / 2 | gdn | 30 | 0.410 / 0.409 | 0.223 / 0.223 | -45.63% / -45.49% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 / 2 | gqa | 10 | 0.813 / 0.814 | 0.683 / 0.683 | -15.99% / -16.16% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 / 2 | moe_layer | 40 | 0.511 / 0.414 | 0.338 / 0.223 | -33.84% / -46.13% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 / 2 | gdn | 30 | 0.369 / 0.368 | 0.183 / 0.183 | -50.29% / -50.09% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 / 2 | gqa | 10 | 0.499 / 0.500 | 0.270 / 0.270 | -45.92% / -46.09% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 / 2 | moe_layer | 40 | 0.401 / 0.373 | 0.205 / 0.183 | -48.93% / -50.86% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 / 2 | gdn | 30 | 0.380 / 0.380 | 0.200 / 0.200 | -47.47% / -47.40% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 / 2 | gqa | 10 | 0.625 / 0.626 | 0.407 / 0.407 | -34.83% / -34.96% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 / 2 | moe_layer | 40 | 0.441 / 0.385 | 0.252 / 0.200 | -42.99% / -48.10% |
| a3-qwen35-tp4-longctx-p-65536-c1 | 1 / 2 | gdn | 30 | 0.368 / 0.366 | 0.183 / 0.183 | -50.14% / -49.89% |
| a3-qwen35-tp4-longctx-p-65536-c1 | 1 / 2 | gqa | 10 | 0.444 / 0.444 | 0.208 / 0.208 | -53.15% / -53.16% |
| a3-qwen35-tp4-longctx-p-65536-c1 | 1 / 2 | moe_layer | 40 | 0.387 / 0.368 | 0.190 / 0.183 | -51.00% / -50.14% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 / 2 | gdn | 30 | 0.385 / 0.381 | 0.200 / 0.200 | -48.16% / -47.55% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 / 2 | gqa | 10 | 0.516 / 0.517 | 0.284 / 0.284 | -44.89% / -45.00% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 / 2 | moe_layer | 40 | 0.418 / 0.385 | 0.221 / 0.200 | -47.15% / -48.15% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 / 2 | gdn | 30 | 0.369 / 0.365 | 0.183 / 0.183 | -50.31% / -49.72% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 / 2 | gqa | 10 | 0.446 / 0.447 | 0.208 / 0.208 | -53.33% / -53.41% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 / 2 | moe_layer | 40 | 0.388 / 0.367 | 0.190 / 0.183 | -51.18% / -49.97% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 / 2 | gdn | 30 | 0.411 / 0.410 | 0.223 / 0.223 | -45.77% / -45.59% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 / 2 | gqa | 10 | 0.653 / 0.652 | 0.437 / 0.437 | -33.06% / -32.98% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 / 2 | moe_layer | 40 | 0.471 / 0.416 | 0.276 / 0.223 | -41.37% / -46.38% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 / 2 | gdn | 30 | 0.371 / 0.366 | 0.183 / 0.183 | -50.55% / -49.83% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 / 2 | gqa | 10 | 0.448 / 0.447 | 0.208 / 0.208 | -53.55% / -53.47% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 / 2 | moe_layer | 40 | 0.390 / 0.369 | 0.190 / 0.183 | -51.41% / -50.32% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 / 2 | gdn | 30 | 0.386 / 0.381 | 0.200 / 0.200 | -48.31% / -47.53% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 / 2 | gqa | 10 | 0.517 / 0.517 | 0.284 / 0.284 | -45.01% / -45.08% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 / 2 | moe_layer | 40 | 0.419 / 0.384 | 0.221 / 0.200 | -47.29% / -48.05% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 / 2 | gdn | 30 | 0.430 / 0.429 | 0.276 / 0.276 | -35.67% / -35.52% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 / 2 | gqa | 10 | 0.849 / 0.851 | 0.746 / 0.746 | -12.16% / -12.44% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 / 2 | moe_layer | 40 | 0.534 / 0.431 | 0.394 / 0.276 | -26.33% / -35.87% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 / 2 | gdn | 30 | 0.416 / 0.408 | 0.223 / 0.223 | -46.48% / -45.41% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 / 2 | gqa | 10 | 0.636 / 0.636 | 0.437 / 0.437 | -31.33% / -31.28% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 / 2 | moe_layer | 40 | 0.471 / 0.416 | 0.276 / 0.223 | -41.37% / -46.46% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 / 2 | gdn | 30 | 0.390 / 0.382 | 0.200 / 0.200 | -48.75% / -47.74% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 / 2 | gqa | 10 | 0.517 / 0.518 | 0.284 / 0.284 | -45.00% / -45.11% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 / 2 | moe_layer | 40 | 0.421 / 0.387 | 0.221 / 0.200 | -47.60% / -48.35% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 / 2 | gdn | 30 | 0.367 / 0.366 | 0.183 / 0.183 | -49.98% / -49.86% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 / 2 | gqa | 10 | 0.445 / 0.446 | 0.208 / 0.208 | -53.24% / -53.30% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 / 2 | moe_layer | 40 | 0.386 / 0.367 | 0.190 / 0.183 | -50.91% / -50.01% |
| a3-qwen36-tp4-longctx-p-126976-c1 | 1 / 4 | gdn | 48 | 0.264 / 0.263 | 0.221 / 0.221 | -16.25% / -15.73% |
| a3-qwen36-tp4-longctx-p-126976-c1 | 1 / 4 | gqa | 16 | 0.387 / 0.387 | 0.321 / 0.321 | -17.01% / -17.16% |
| a3-qwen36-tp4-longctx-p-126976-c1 | 1 / 4 | dense_layer | 64 | 0.295 / 0.265 | 0.246 / 0.221 | -16.50% / -16.44% |
| a3-qwen36-tp4-longctx-p-126976-c4 | 4 / 4 | gdn | 48 | 0.313 / 0.312 | 0.257 / 0.257 | -18.06% / -17.83% |
| a3-qwen36-tp4-longctx-p-126976-c4 | 4 / 4 | gqa | 16 | 0.805 / 0.804 | 0.730 / 0.730 | -9.22% / -9.12% |
| a3-qwen36-tp4-longctx-p-126976-c4 | 4 / 4 | dense_layer | 64 | 0.436 / 0.315 | 0.375 / 0.257 | -13.99% / -18.51% |
| a3-qwen36-tp4-longctx-p-65536-c1 | 1 / 4 | gdn | 48 | 0.264 / 0.261 | 0.221 / 0.221 | -16.02% / -15.00% |
| a3-qwen36-tp4-longctx-p-65536-c1 | 1 / 4 | gqa | 16 | 0.334 / 0.330 | 0.255 / 0.255 | -23.59% / -22.58% |
| a3-qwen36-tp4-longctx-p-65536-c1 | 1 / 4 | dense_layer | 64 | 0.281 / 0.264 | 0.230 / 0.221 | -18.27% / -15.97% |
| a3-qwen36-tp4-longctx-p-65536-c4 | 4 / 4 | gdn | 48 | 0.315 / 0.312 | 0.257 / 0.257 | -18.60% / -17.75% |
| a3-qwen36-tp4-longctx-p-65536-c4 | 4 / 4 | gqa | 16 | 0.607 / 0.607 | 0.470 / 0.470 | -22.55% / -22.62% |
| a3-qwen36-tp4-longctx-p-65536-c4 | 4 / 4 | dense_layer | 64 | 0.388 / 0.315 | 0.310 / 0.257 | -20.14% / -18.45% |
| a5-qwen35-tp4-longctx-p126976-c1-hold | 1 / 4 | gdn | 30 | 0.223 / 0.222 | 0.104 / 0.104 | -53.19% / -52.98% |
| a5-qwen35-tp4-longctx-p126976-c1-hold | 1 / 4 | gqa | 10 | 1.148 / 1.148 | 1.066 / 1.066 | -7.12% / -7.12% |
| a5-qwen35-tp4-longctx-p126976-c1-hold | 1 / 4 | moe_layer | 40 | 0.454 / 0.223 | 0.345 / 0.104 | -24.09% / -53.24% |
| a5-qwen35-tp4-longctx-p126976-c1-o32 | 1 / 4 | gdn | 30 | 0.263 / 0.220 | 0.104 / 0.104 | -60.25% / -52.46% |
| a5-qwen35-tp4-longctx-p126976-c1-o32 | 1 / 4 | gqa | 10 | 1.143 / 1.143 | 1.066 / 1.066 | -6.74% / -6.72% |
| a5-qwen35-tp4-longctx-p126976-c1-o32 | 1 / 4 | moe_layer | 40 | 0.483 / 0.221 | 0.345 / 0.104 | -28.59% / -52.82% |
| a5-qwen35-tp4-longctx-p126976-c4-hold | 4 / 4 | gdn | 30 | 0.276 / 0.278 | 0.133 / 0.133 | -51.69% / -52.02% |
| a5-qwen35-tp4-longctx-p126976-c4-hold | 4 / 4 | gqa | 10 | 1.212 / 1.214 | 1.086 / 1.086 | -10.42% / -10.60% |
| a5-qwen35-tp4-longctx-p126976-c4-hold | 4 / 4 | moe_layer | 40 | 0.510 / 0.280 | 0.371 / 0.133 | -27.16% / -52.43% |
| a5-qwen35-tp4-longctx-p126976-c4-o32 | 1 / 4 | gdn | 30 | 0.222 / 0.221 | 0.104 / 0.104 | -52.89% / -52.66% |
| a5-qwen35-tp4-longctx-p126976-c4-o32 | 1 / 4 | gqa | 10 | 1.145 / 1.145 | 1.066 / 1.066 | -6.89% / -6.91% |
| a5-qwen35-tp4-longctx-p126976-c4-o32 | 1 / 4 | moe_layer | 40 | 0.453 / 0.223 | 0.345 / 0.104 | -23.80% / -53.13% |
| a5-qwen35-tp4-longctx-p65536-c1-hold | 1 / 4 | gdn | 30 | 0.222 / 0.221 | 0.104 / 0.104 | -52.96% / -52.69% |
| a5-qwen35-tp4-longctx-p65536-c1-hold | 1 / 4 | gqa | 10 | 0.698 / 0.698 | 0.589 / 0.589 | -15.61% / -15.62% |
| a5-qwen35-tp4-longctx-p65536-c1-hold | 1 / 4 | moe_layer | 40 | 0.341 / 0.222 | 0.226 / 0.104 | -33.85% / -52.91% |
| a5-qwen35-tp4-longctx-p65536-c1-o32 | 1 / 4 | gdn | 30 | 0.229 / 0.221 | 0.104 / 0.104 | -54.37% / -52.76% |
| a5-qwen35-tp4-longctx-p65536-c1-o32 | 1 / 4 | gqa | 10 | 0.699 / 0.699 | 0.589 / 0.589 | -15.74% / -15.76% |
| a5-qwen35-tp4-longctx-p65536-c1-o32 | 1 / 4 | moe_layer | 40 | 0.347 / 0.223 | 0.226 / 0.104 | -34.88% / -53.22% |
| a5-qwen35-tp4-longctx-p65536-c4-hold | 4 / 4 | gdn | 30 | 0.273 / 0.274 | 0.133 / 0.133 | -51.28% / -51.35% |
| a5-qwen35-tp4-longctx-p65536-c4-hold | 4 / 4 | gqa | 10 | 0.757 / 0.759 | 0.609 / 0.609 | -19.54% / -19.71% |
| a5-qwen35-tp4-longctx-p65536-c4-hold | 4 / 4 | moe_layer | 40 | 0.394 / 0.278 | 0.252 / 0.133 | -36.04% / -52.03% |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 1 / 4 | gdn | 30 | 0.249 / 0.221 | 0.104 / 0.104 | -58.04% / -52.79% |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 1 / 4 | gqa | 10 | 0.698 / 0.697 | 0.589 / 0.589 | -15.53% / -15.44% |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 1 / 4 | moe_layer | 40 | 0.361 / 0.222 | 0.226 / 0.104 | -37.51% / -52.98% |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 2 / 4 | gdn | 30 | 0.335 / 0.243 | 0.115 / 0.115 | -65.66% / -52.54% |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 2 / 4 | gqa | 10 | 0.718 / 0.718 | 0.597 / 0.597 | -16.87% / -16.89% |
| a5-qwen35-tp4-longctx-p65536-c4-o32 | 2 / 4 | moe_layer | 40 | 0.431 / 0.244 | 0.236 / 0.115 | -45.34% / -52.83% |
| a5-qwen38-tp1-longctx-p126976-c4 | 1 / 4 | gdn | 48 | 0.273 / 0.272 | 0.206 / 0.206 | -24.59% / -24.52% |
| a5-qwen38-tp1-longctx-p126976-c4 | 1 / 4 | gqa | 16 | 1.195 / 1.195 | 1.122 / 1.122 | -6.12% / -6.11% |
| a5-qwen38-tp1-longctx-p126976-c4 | 1 / 4 | dense_layer | 64 | 0.503 / 0.273 | 0.435 / 0.206 | -13.63% / -24.68% |
| a5-qwen38-tp1-longctx-p126976-c4 | 2 / 4 | gdn | 48 | 0.299 / 0.299 | 0.224 / 0.224 | -25.07% / -25.05% |
| a5-qwen38-tp1-longctx-p126976-c4 | 2 / 4 | gqa | 16 | 1.321 / 1.321 | 1.124 / 1.124 | -14.87% / -14.88% |
| a5-qwen38-tp1-longctx-p126976-c4 | 2 / 4 | dense_layer | 64 | 0.555 / 0.300 | 0.449 / 0.224 | -19.00% / -25.26% |
| a5-qwen38-tp1-longctx-p65536-c4 | 1 / 4 | gdn | 48 | 0.273 / 0.273 | 0.206 / 0.206 | -24.64% / -24.57% |
| a5-qwen38-tp1-longctx-p65536-c4 | 1 / 4 | gqa | 16 | 0.711 / 0.711 | 0.645 / 0.645 | -9.27% / -9.26% |
| a5-qwen38-tp1-longctx-p65536-c4 | 1 / 4 | dense_layer | 64 | 0.382 / 0.274 | 0.316 / 0.206 | -17.49% / -24.85% |
| a5-qwen38-tp1-longctx-p65536-c4 | 2 / 4 | gdn | 48 | 0.299 / 0.299 | 0.224 / 0.224 | -25.01% / -25.08% |
| a5-qwen38-tp1-longctx-p65536-c4 | 2 / 4 | gqa | 16 | 0.780 / 0.780 | 0.648 / 0.648 | -17.01% / -17.00% |
| a5-qwen38-tp1-longctx-p65536-c4 | 2 / 4 | dense_layer | 64 | 0.419 / 0.300 | 0.330 / 0.224 | -21.29% / -25.27% |
| a5-qwen38-tp1-longctx-p65536-c4 | 4 / 4 | gdn | 48 | 0.337 / 0.337 | 0.260 / 0.260 | -22.82% / -22.77% |
| a5-qwen38-tp1-longctx-p65536-c4 | 4 / 4 | gqa | 16 | 0.805 / 0.806 | 0.655 / 0.655 | -18.67% / -18.69% |
| a5-qwen38-tp1-longctx-p65536-c4 | 4 / 4 | dense_layer | 64 | 0.454 / 0.338 | 0.359 / 0.260 | -20.98% / -23.04% |
| a5-qwen36-tp8-longctx-p126976-c1-hold | 1 / 4 | gdn | 48 | 0.169 / 0.158 | 0.113 / 0.113 | -33.13% / -28.37% |
| a5-qwen36-tp8-longctx-p126976-c1-hold | 1 / 4 | gqa | 16 | 1.069 / 1.069 | 1.075 / 1.075 | +0.53% / +0.57% |
| a5-qwen36-tp8-longctx-p126976-c1-hold | 1 / 4 | dense_layer | 64 | 0.394 / 0.161 | 0.354 / 0.113 | -10.30% / -29.93% |
| a5-qwen36-tp8-longctx-p126976-c4-hold | 4 / 4 | gdn | 48 | 0.188 / 0.180 | 0.123 / 0.123 | -34.63% / -31.46% |
| a5-qwen36-tp8-longctx-p126976-c4-hold | 4 / 4 | gqa | 16 | 1.097 / 1.097 | 1.078 / 1.078 | -1.69% / -1.68% |
| a5-qwen36-tp8-longctx-p126976-c4-hold | 4 / 4 | dense_layer | 64 | 0.415 / 0.183 | 0.362 / 0.123 | -12.89% / -32.76% |
| a5-qwen36-tp8-longctx-p65536-c1-hold | 1 / 4 | gdn | 48 | 0.160 / 0.158 | 0.113 / 0.113 | -29.54% / -28.38% |
| a5-qwen36-tp8-longctx-p65536-c1-hold | 1 / 4 | gqa | 16 | 0.628 / 0.622 | 0.598 / 0.598 | -4.78% / -3.80% |
| a5-qwen36-tp8-longctx-p65536-c1-hold | 1 / 4 | dense_layer | 64 | 0.277 / 0.161 | 0.234 / 0.113 | -15.52% / -29.72% |
| a5-qwen36-tp8-longctx-p65536-c4-hold | 4 / 4 | gdn | 48 | 0.183 / 0.180 | 0.123 / 0.123 | -32.61% / -31.58% |
| a5-qwen36-tp8-longctx-p65536-c4-hold | 4 / 4 | gqa | 16 | 0.644 / 0.644 | 0.602 / 0.602 | -6.66% / -6.65% |
| a5-qwen36-tp8-longctx-p65536-c4-hold | 4 / 4 | dense_layer | 64 | 0.298 / 0.183 | 0.243 / 0.123 | -18.58% / -32.81% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | 1 / 1 | kda | 3 | 0.780 / 0.795 | 0.598 / 0.712 | -23.37% / -10.46% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | 1 / 1 | mla | 1 | 1.055 / 1.055 | 0.933 / 0.933 | -11.61% / -11.61% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | 1 / 1 | dense_layer | 1 | 0.813 / 0.813 | 0.370 / 0.370 | -54.51% / -54.51% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | 1 / 1 | moe_layer | 3 | 0.861 / 0.795 | 0.785 / 0.712 | -8.77% / -10.46% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | 12 / 1 | kda | 3 | 0.994 / 1.047 | 0.798 / 0.997 | -19.75% / -4.75% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | 12 / 1 | mla | 1 | 3.938 / 3.938 | 3.483 / 3.483 | -11.57% / -11.57% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | 12 / 1 | dense_layer | 1 | 0.789 / 0.789 | 0.400 / 0.400 | -49.30% / -49.30% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | 12 / 1 | moe_layer | 3 | 2.044 / 1.147 | 1.825 / 0.997 | -10.69% / -13.11% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | 16 / 1 | kda | 3 | 1.103 / 1.204 | 0.804 / 1.003 | -27.17% / -16.71% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | 16 / 1 | mla | 1 | 4.976 / 4.976 | 4.294 / 4.294 | -13.70% / -13.70% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | 16 / 1 | dense_layer | 1 | 0.774 / 0.774 | 0.406 / 0.406 | -47.55% / -47.55% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | 16 / 1 | moe_layer | 3 | 2.504 / 1.333 | 2.100 / 1.003 | -16.15% / -24.78% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | 2 / 1 | kda | 3 | 0.763 / 0.744 | 0.599 / 0.713 | -21.52% / -4.24% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | 2 / 1 | mla | 1 | 1.304 / 1.304 | 1.140 / 1.140 | -12.58% / -12.58% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | 2 / 1 | dense_layer | 1 | 0.698 / 0.698 | 0.371 / 0.371 | -46.91% / -46.91% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | 2 / 1 | moe_layer | 3 | 0.965 / 0.846 | 0.855 / 0.713 | -11.37% / -15.76% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | 24 / 1 | kda | 3 | 1.293 / 1.517 | 1.002 / 1.287 | -22.46% / -15.17% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | 24 / 1 | mla | 1 | 7.084 / 7.084 | 6.178 / 6.178 | -12.79% / -12.79% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | 24 / 1 | dense_layer | 1 | 0.754 / 0.754 | 0.433 / 0.433 | -42.62% / -42.62% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | 24 / 1 | moe_layer | 3 | 3.402 / 1.607 | 2.917 / 1.287 | -14.26% / -19.89% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | 32 / 1 | kda | 3 | 1.496 / 1.813 | 1.194 / 1.563 | -20.23% / -13.82% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | 32 / 1 | mla | 1 | 9.235 / 9.235 | 8.112 / 8.112 | -12.16% / -12.16% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | 32 / 1 | dense_layer | 1 | 0.790 / 0.790 | 0.455 / 0.455 | -42.34% / -42.34% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | 32 / 1 | moe_layer | 3 | 4.311 / 1.886 | 3.746 / 1.563 | -13.12% / -17.13% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | 4 / 1 | kda | 3 | 0.826 / 0.835 | 0.605 / 0.719 | -26.72% / -13.92% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | 4 / 1 | mla | 1 | 1.925 / 1.925 | 1.553 / 1.553 | -19.36% / -19.36% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | 4 / 1 | dense_layer | 1 | 0.719 / 0.719 | 0.377 / 0.377 | -47.54% / -47.54% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | 4 / 1 | moe_layer | 3 | 1.228 / 0.923 | 0.997 / 0.719 | -18.81% / -22.08% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | 48 / 1 | kda | 3 | 1.907 / 2.420 | 1.592 / 2.135 | -16.52% / -11.74% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | 48 / 1 | mla | 1 | 13.351 / 13.351 | 11.890 / 11.890 | -10.95% / -10.95% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | 48 / 1 | dense_layer | 1 | 0.848 / 0.848 | 0.505 / 0.505 | -40.41% / -40.41% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | 48 / 1 | moe_layer | 3 | 6.075 / 2.454 | 5.387 / 2.135 | -11.33% / -12.97% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | 6 / 1 | kda | 3 | 0.861 / 0.829 | 0.606 / 0.720 | -29.59% / -13.12% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | 6 / 1 | mla | 1 | 2.213 / 2.213 | 1.976 / 1.976 | -10.71% / -10.71% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | 6 / 1 | dense_layer | 1 | 0.805 / 0.805 | 0.378 / 0.378 | -53.07% / -53.07% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | 6 / 1 | moe_layer | 3 | 1.330 / 0.948 | 1.139 / 0.720 | -14.38% / -24.05% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | 64 / 1 | kda | 3 | 2.136 / 2.758 | 1.820 / 2.452 | -14.81% / -11.09% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | 64 / 1 | mla | 1 | 17.286 / 17.286 | 15.484 / 15.484 | -10.42% / -10.42% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | 64 / 1 | dense_layer | 1 | 0.871 / 0.871 | 0.556 / 0.556 | -36.23% / -36.23% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | 64 / 1 | moe_layer | 3 | 7.608 / 2.779 | 6.796 / 2.452 | -10.67% / -11.79% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | 8 / 1 | kda | 3 | 0.861 / 0.895 | 0.611 / 0.725 | -29.12% / -19.01% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | 8 / 1 | mla | 1 | 2.883 / 2.883 | 2.372 / 2.372 | -17.73% / -17.73% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | 8 / 1 | dense_layer | 1 | 0.696 / 0.696 | 0.383 / 0.383 | -45.00% / -45.00% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | 8 / 1 | moe_layer | 3 | 1.590 / 0.994 | 1.274 / 0.725 | -19.92% / -27.10% |
| a3-kimi4-tp8-longctx-decode-c12-p16k | 12 / 1 | kda | 3 | 0.990 / 1.054 | 0.798 / 0.997 | -19.41% / -5.40% |
| a3-kimi4-tp8-longctx-decode-c12-p16k | 12 / 1 | mla | 1 | 1.464 / 1.464 | 1.309 / 1.309 | -10.62% / -10.62% |
| a3-kimi4-tp8-longctx-decode-c12-p16k | 12 / 1 | dense_layer | 1 | 0.773 / 0.773 | 0.400 / 0.400 | -48.25% / -48.25% |
| a3-kimi4-tp8-longctx-decode-c12-p16k | 12 / 1 | moe_layer | 3 | 1.220 / 1.143 | 1.101 / 0.997 | -9.80% / -12.82% |
| a3-kimi4-tp8-longctx-decode-c12-p32k | 12 / 1 | kda | 3 | 0.961 / 1.056 | 0.798 / 0.997 | -17.01% / -5.63% |
| a3-kimi4-tp8-longctx-decode-c12-p32k | 12 / 1 | mla | 1 | 1.737 / 1.737 | 1.637 / 1.637 | -5.74% / -5.74% |
| a3-kimi4-tp8-longctx-decode-c12-p32k | 12 / 1 | dense_layer | 1 | 0.679 / 0.679 | 0.400 / 0.400 | -41.11% / -41.11% |
| a3-kimi4-tp8-longctx-decode-c12-p32k | 12 / 1 | moe_layer | 3 | 1.314 / 1.149 | 1.210 / 0.997 | -7.89% / -13.23% |
| a3-kimi4-tp8-longctx-decode-c12-p4k | 12 / 1 | kda | 3 | 0.985 / 1.050 | 0.798 / 0.997 | -19.02% / -5.08% |
| a3-kimi4-tp8-longctx-decode-c12-p4k | 12 / 1 | mla | 1 | 1.273 / 1.273 | 1.059 / 1.059 | -16.79% / -16.79% |
| a3-kimi4-tp8-longctx-decode-c12-p4k | 12 / 1 | dense_layer | 1 | 0.763 / 0.763 | 0.400 / 0.400 | -47.59% / -47.59% |
| a3-kimi4-tp8-longctx-decode-c12-p4k | 12 / 1 | moe_layer | 3 | 1.155 / 1.143 | 1.018 / 0.997 | -11.91% / -12.76% |
| a3-kimi4-tp8-longctx-decode-c12-p8k | 12 / 1 | kda | 3 | 0.974 / 1.052 | 0.798 / 0.997 | -18.08% / -5.25% |
| a3-kimi4-tp8-longctx-decode-c12-p8k | 12 / 1 | mla | 1 | 1.326 / 1.326 | 1.144 / 1.144 | -13.75% / -13.75% |
| a3-kimi4-tp8-longctx-decode-c12-p8k | 12 / 1 | dense_layer | 1 | 0.726 / 0.726 | 0.400 / 0.400 | -44.91% / -44.91% |
| a3-kimi4-tp8-longctx-decode-c12-p8k | 12 / 1 | moe_layer | 3 | 1.174 / 1.144 | 1.046 / 0.997 | -10.92% / -12.85% |
| a3-kimi4-tp8-longctx-decode-c24-p16k | 24 / 1 | kda | 3 | 1.320 / 1.515 | 1.002 / 1.287 | -24.07% / -15.03% |
| a3-kimi4-tp8-longctx-decode-c24-p16k | 24 / 1 | mla | 1 | 2.136 / 2.136 | 1.895 / 1.895 | -11.26% / -11.26% |
| a3-kimi4-tp8-longctx-decode-c24-p16k | 24 / 1 | dense_layer | 1 | 0.841 / 0.841 | 0.433 / 0.433 | -48.56% / -48.56% |
| a3-kimi4-tp8-longctx-decode-c24-p16k | 24 / 1 | moe_layer | 3 | 1.752 / 1.604 | 1.490 / 1.287 | -14.94% / -19.76% |
| a3-kimi4-tp8-longctx-decode-c24-p32k | 24 / 1 | kda | 3 | 1.277 / 1.521 | 1.002 / 1.287 | -21.49% / -15.40% |
| a3-kimi4-tp8-longctx-decode-c24-p32k | 24 / 1 | mla | 1 | 2.606 / 2.606 | 2.547 / 2.547 | -2.29% / -2.29% |
| a3-kimi4-tp8-longctx-decode-c24-p32k | 24 / 1 | dense_layer | 1 | 0.722 / 0.722 | 0.433 / 0.433 | -40.07% / -40.07% |
| a3-kimi4-tp8-longctx-decode-c24-p32k | 24 / 1 | moe_layer | 3 | 1.905 / 1.586 | 1.707 / 1.287 | -10.38% / -18.86% |
| a3-kimi4-tp8-longctx-decode-c24-p4k | 24 / 1 | kda | 3 | 1.290 / 1.510 | 1.002 / 1.287 | -22.30% / -14.77% |
| a3-kimi4-tp8-longctx-decode-c24-p4k | 24 / 1 | mla | 1 | 1.771 / 1.771 | 1.409 / 1.409 | -20.40% / -20.40% |
| a3-kimi4-tp8-longctx-decode-c24-p4k | 24 / 1 | dense_layer | 1 | 0.743 / 0.743 | 0.433 / 0.433 | -41.80% / -41.80% |
| a3-kimi4-tp8-longctx-decode-c24-p4k | 24 / 1 | moe_layer | 3 | 1.632 / 1.616 | 1.328 / 1.287 | -18.65% / -20.36% |
| a3-kimi4-tp8-longctx-decode-c24-p8k | 24 / 1 | kda | 3 | 1.316 / 1.512 | 1.002 / 1.287 | -23.86% / -14.87% |
| a3-kimi4-tp8-longctx-decode-c24-p8k | 24 / 1 | mla | 1 | 1.880 / 1.880 | 1.576 / 1.576 | -16.15% / -16.15% |
| a3-kimi4-tp8-longctx-decode-c24-p8k | 24 / 1 | dense_layer | 1 | 0.835 / 0.835 | 0.433 / 0.433 | -48.18% / -48.18% |
| a3-kimi4-tp8-longctx-decode-c24-p8k | 24 / 1 | moe_layer | 3 | 1.664 / 1.602 | 1.383 / 1.287 | -16.89% / -19.67% |
| a3-kimi4-tp8-longctx-decode-c2-p4k | 2 / 1 | kda | 3 | 0.791 / 0.774 | 0.599 / 0.713 | -24.28% / -7.93% |
| a3-kimi4-tp8-longctx-decode-c2-p4k | 2 / 1 | mla | 1 | 0.912 / 0.912 | 0.726 / 0.726 | -20.35% / -20.35% |
| a3-kimi4-tp8-longctx-decode-c2-p4k | 2 / 1 | dense_layer | 1 | 0.774 / 0.774 | 0.371 / 0.371 | -52.10% / -52.10% |
| a3-kimi4-tp8-longctx-decode-c2-p4k | 2 / 1 | moe_layer | 3 | 0.837 / 0.838 | 0.717 / 0.713 | -14.27% / -14.97% |
| a3-kimi4-tp8-longctx-decode-c48-p4k | 48 / 1 | kda | 3 | 1.913 / 2.423 | 1.592 / 2.135 | -16.76% / -11.88% |
| a3-kimi4-tp8-longctx-decode-c48-p4k | 48 / 1 | mla | 1 | 2.733 / 2.733 | 2.389 / 2.389 | -12.58% / -12.58% |
| a3-kimi4-tp8-longctx-decode-c48-p4k | 48 / 1 | dense_layer | 1 | 0.846 / 0.846 | 0.505 / 0.505 | -40.28% / -40.28% |
| a3-kimi4-tp8-longctx-decode-c48-p4k | 48 / 1 | moe_layer | 3 | 2.542 / 2.468 | 2.220 / 2.135 | -12.65% / -13.48% |
| a3-kimi4-tp8-longctx-decode-c6-p4k | 6 / 1 | kda | 3 | 0.887 / 0.857 | 0.606 / 0.720 | -31.69% / -15.99% |
| a3-kimi4-tp8-longctx-decode-c6-p4k | 6 / 1 | mla | 1 | 1.039 / 1.039 | 0.756 / 0.756 | -27.31% / -27.31% |
| a3-kimi4-tp8-longctx-decode-c6-p4k | 6 / 1 | dense_layer | 1 | 0.857 / 0.857 | 0.378 / 0.378 | -55.90% / -55.90% |
| a3-kimi4-tp8-longctx-decode-c6-p4k | 6 / 1 | moe_layer | 3 | 0.948 / 0.951 | 0.732 / 0.720 | -22.80% / -24.26% |
| a3-kimi4-tp8-longctx-decode-c8-p4k | 8 / 1 | kda | 3 | 0.915 / 0.888 | 0.611 / 0.725 | -33.26% / -18.40% |
| a3-kimi4-tp8-longctx-decode-c8-p4k | 8 / 1 | mla | 1 | 1.094 / 1.094 | 0.771 / 0.771 | -29.50% / -29.50% |
| a3-kimi4-tp8-longctx-decode-c8-p4k | 8 / 1 | dense_layer | 1 | 0.842 / 0.842 | 0.383 / 0.383 | -54.57% / -54.57% |
| a3-kimi4-tp8-longctx-decode-c8-p4k | 8 / 1 | moe_layer | 3 | 0.999 / 1.015 | 0.740 / 0.725 | -25.90% / -28.58% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | 1 / 1 | kda | 3 | 0.952 / 0.931 | 0.626 / 0.770 | -34.20% / -17.25% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | 1 / 1 | mla | 1 | 1.236 / 1.236 | 1.038 / 1.038 | -16.02% / -16.02% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | 1 / 1 | dense_layer | 1 | 0.931 / 0.931 | 0.338 / 0.338 | -63.66% / -63.66% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | 1 / 1 | moe_layer | 3 | 1.054 / 0.995 | 0.860 / 0.770 | -18.41% / -22.60% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | 12 / 1 | kda | 3 | 1.008 / 0.971 | 0.638 / 0.782 | -36.68% / -19.44% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | 12 / 1 | mla | 1 | 3.842 / 3.842 | 3.268 / 3.268 | -14.93% / -14.93% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | 12 / 1 | dense_layer | 1 | 0.971 / 0.971 | 0.350 / 0.350 | -63.95% / -63.95% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | 12 / 1 | moe_layer | 3 | 1.965 / 1.118 | 1.611 / 0.782 | -18.01% / -30.03% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | 16 / 1 | kda | 3 | 1.039 / 0.981 | 0.643 / 0.787 | -38.12% / -19.82% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | 16 / 1 | mla | 1 | 4.724 / 4.724 | 4.056 / 4.056 | -14.14% / -14.14% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | 16 / 1 | dense_layer | 1 | 0.971 / 0.971 | 0.355 / 0.355 | -63.49% / -63.49% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | 16 / 1 | moe_layer | 3 | 2.289 / 1.163 | 1.876 / 0.787 | -18.04% / -32.38% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | 2 / 1 | kda | 3 | 0.956 / 0.936 | 0.627 / 0.771 | -34.44% / -17.64% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | 2 / 1 | mla | 1 | 1.493 / 1.493 | 1.241 / 1.241 | -16.86% / -16.86% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | 2 / 1 | dense_layer | 1 | 0.936 / 0.936 | 0.339 / 0.339 | -63.80% / -63.80% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | 2 / 1 | moe_layer | 3 | 1.142 / 1.004 | 0.928 / 0.771 | -18.75% / -23.18% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | 24 / 1 | kda | 3 | 1.121 / 1.115 | 0.835 / 1.064 | -25.57% / -4.60% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | 24 / 1 | mla | 1 | 6.698 / 6.698 | 5.912 / 5.912 | -11.74% / -11.74% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | 24 / 1 | dense_layer | 1 | 0.884 / 0.884 | 0.376 / 0.376 | -57.45% / -57.45% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | 24 / 1 | moe_layer | 3 | 3.059 / 1.364 | 2.680 / 1.064 | -12.40% / -22.04% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | 32 / 1 | kda | 3 | 1.230 / 1.218 | 0.842 / 1.071 | -31.52% / -12.02% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | 32 / 1 | mla | 1 | 8.605 / 8.605 | 7.529 / 7.529 | -12.50% / -12.50% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | 32 / 1 | dense_layer | 1 | 0.985 / 0.985 | 0.384 / 0.384 | -61.03% / -61.03% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | 32 / 1 | moe_layer | 3 | 3.770 / 1.487 | 3.224 / 1.071 | -14.48% / -27.95% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | 4 / 1 | kda | 3 | 0.983 / 0.958 | 0.628 / 0.772 | -36.11% / -19.42% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | 4 / 1 | mla | 1 | 2.057 / 2.057 | 1.643 / 1.643 | -20.13% / -20.13% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | 4 / 1 | dense_layer | 1 | 0.958 / 0.958 | 0.340 / 0.340 | -64.50% / -64.50% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | 4 / 1 | moe_layer | 3 | 1.350 / 1.051 | 1.063 / 0.772 | -21.27% / -26.53% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | 48 / 1 | kda | 3 | 1.418 / 1.515 | 1.047 / 1.362 | -26.18% / -10.05% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | 48 / 1 | mla | 1 | 12.478 / 12.478 | 11.024 / 11.024 | -11.65% / -11.65% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | 48 / 1 | dense_layer | 1 | 1.007 / 1.007 | 0.417 / 0.417 | -58.62% / -58.62% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | 48 / 1 | moe_layer | 3 | 5.242 / 1.734 | 4.583 / 1.362 | -12.57% / -21.42% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | 6 / 1 | kda | 3 | 0.984 / 0.944 | 0.631 / 0.775 | -35.85% / -17.88% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | 6 / 1 | mla | 1 | 2.312 / 2.312 | 2.063 / 2.063 | -10.77% / -10.77% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | 6 / 1 | dense_layer | 1 | 0.944 / 0.944 | 0.343 / 0.343 | -63.66% / -63.66% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | 6 / 1 | moe_layer | 3 | 1.440 / 1.068 | 1.204 / 0.775 | -16.34% / -27.44% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | 64 / 1 | kda | 3 | 1.540 / 1.702 | 1.167 / 1.528 | -24.24% / -10.25% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | 64 / 1 | mla | 1 | 16.320 / 16.320 | 14.379 / 14.379 | -11.90% / -11.90% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | 64 / 1 | dense_layer | 1 | 0.991 / 0.991 | 0.445 / 0.445 | -55.05% / -55.05% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | 64 / 1 | moe_layer | 3 | 6.650 / 1.928 | 5.811 / 1.528 | -12.61% / -20.75% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | 8 / 1 | kda | 3 | 0.977 / 0.947 | 0.635 / 0.779 | -34.94% / -17.72% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | 8 / 1 | mla | 1 | 2.934 / 2.934 | 2.448 / 2.448 | -16.58% / -16.58% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | 8 / 1 | dense_layer | 1 | 0.912 / 0.912 | 0.347 / 0.347 | -61.92% / -61.92% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | 8 / 1 | moe_layer | 3 | 1.651 / 1.070 | 1.336 / 0.779 | -19.09% / -27.19% |
| a3-kimi4-tp16-128k-decode-c12-p16k | 12 / 1 | kda | 3 | 1.022 / 1.012 | 0.638 / 0.782 | -37.59% / -22.71% |
| a3-kimi4-tp16-128k-decode-c12-p16k | 12 / 1 | mla | 1 | 1.363 / 1.363 | 1.151 / 1.151 | -15.58% / -15.58% |
| a3-kimi4-tp16-128k-decode-c12-p16k | 12 / 1 | dense_layer | 1 | 1.012 / 1.012 | 0.350 / 0.350 | -65.42% / -65.42% |
| a3-kimi4-tp16-128k-decode-c12-p16k | 12 / 1 | moe_layer | 3 | 1.139 / 1.094 | 0.905 / 0.782 | -20.57% / -28.52% |
| a3-kimi4-tp16-128k-decode-c12-p32k | 12 / 1 | kda | 3 | 0.998 / 0.970 | 0.638 / 0.782 | -36.05% / -19.40% |
| a3-kimi4-tp16-128k-decode-c12-p32k | 12 / 1 | mla | 1 | 1.665 / 1.665 | 1.474 / 1.474 | -11.47% / -11.47% |
| a3-kimi4-tp16-128k-decode-c12-p32k | 12 / 1 | dense_layer | 1 | 0.970 / 0.970 | 0.350 / 0.350 | -63.93% / -63.93% |
| a3-kimi4-tp16-128k-decode-c12-p32k | 12 / 1 | moe_layer | 3 | 1.229 / 1.071 | 1.013 / 0.782 | -17.61% / -26.99% |
| a3-kimi4-tp16-128k-decode-c12-p4k | 12 / 1 | kda | 3 | 1.008 / 0.965 | 0.638 / 0.782 | -36.70% / -19.00% |
| a3-kimi4-tp16-128k-decode-c12-p4k | 12 / 1 | mla | 1 | 1.415 / 1.415 | 0.903 / 0.903 | -36.18% / -36.18% |
| a3-kimi4-tp16-128k-decode-c12-p4k | 12 / 1 | dense_layer | 1 | 0.965 / 0.965 | 0.350 / 0.350 | -63.75% / -63.75% |
| a3-kimi4-tp16-128k-decode-c12-p4k | 12 / 1 | moe_layer | 3 | 1.158 / 1.110 | 0.822 / 0.782 | -28.97% / -29.57% |
| a3-kimi4-tp16-128k-decode-c12-p8k | 12 / 1 | kda | 3 | 1.003 / 0.956 | 0.638 / 0.782 | -36.37% / -18.21% |
| a3-kimi4-tp16-128k-decode-c12-p8k | 12 / 1 | mla | 1 | 1.370 / 1.370 | 0.987 / 0.987 | -27.95% / -27.95% |
| a3-kimi4-tp16-128k-decode-c12-p8k | 12 / 1 | dense_layer | 1 | 0.951 / 0.951 | 0.350 / 0.350 | -63.21% / -63.21% |
| a3-kimi4-tp16-128k-decode-c12-p8k | 12 / 1 | moe_layer | 3 | 1.142 / 1.101 | 0.850 / 0.782 | -25.56% / -28.96% |
| a3-kimi4-tp16-128k-decode-c24-p16k | 24 / 1 | kda | 3 | 1.122 / 1.109 | 0.835 / 1.064 | -25.61% / -4.10% |
| a3-kimi4-tp16-128k-decode-c24-p16k | 24 / 1 | mla | 1 | 1.893 / 1.893 | 1.735 / 1.735 | -8.39% / -8.39% |
| a3-kimi4-tp16-128k-decode-c24-p16k | 24 / 1 | dense_layer | 1 | 0.914 / 0.914 | 0.376 / 0.376 | -58.86% / -58.86% |
| a3-kimi4-tp16-128k-decode-c24-p16k | 24 / 1 | moe_layer | 3 | 1.448 / 1.342 | 1.287 / 1.064 | -11.10% / -20.73% |
| a3-kimi4-tp16-128k-decode-c24-p32k | 24 / 1 | kda | 3 | 1.139 / 1.121 | 0.835 / 1.064 | -26.72% / -5.09% |
| a3-kimi4-tp16-128k-decode-c24-p32k | 24 / 1 | mla | 1 | 2.244 / 2.244 | 2.373 / 2.373 | +5.72% / +5.72% |
| a3-kimi4-tp16-128k-decode-c24-p32k | 24 / 1 | dense_layer | 1 | 0.934 / 0.934 | 0.376 / 0.376 | -59.74% / -59.74% |
| a3-kimi4-tp16-128k-decode-c24-p32k | 24 / 1 | moe_layer | 3 | 1.575 / 1.361 | 1.500 / 1.064 | -4.79% / -21.86% |
| a3-kimi4-tp16-128k-decode-c24-p4k | 24 / 1 | kda | 3 | 1.141 / 1.111 | 0.835 / 1.064 | -26.89% / -4.25% |
| a3-kimi4-tp16-128k-decode-c24-p4k | 24 / 1 | mla | 1 | 1.416 / 1.416 | 1.255 / 1.255 | -11.38% / -11.38% |
| a3-kimi4-tp16-128k-decode-c24-p4k | 24 / 1 | dense_layer | 1 | 0.961 / 0.961 | 0.376 / 0.376 | -60.85% / -60.85% |
| a3-kimi4-tp16-128k-decode-c24-p4k | 24 / 1 | moe_layer | 3 | 1.293 / 1.352 | 1.127 / 1.064 | -12.81% / -21.35% |
| a3-kimi4-tp16-128k-decode-c24-p8k | 24 / 1 | kda | 3 | 1.137 / 1.123 | 0.835 / 1.064 | -26.63% / -5.26% |
| a3-kimi4-tp16-128k-decode-c24-p8k | 24 / 1 | mla | 1 | 1.526 / 1.526 | 1.419 / 1.419 | -7.01% / -7.01% |
| a3-kimi4-tp16-128k-decode-c24-p8k | 24 / 1 | dense_layer | 1 | 0.946 / 0.946 | 0.376 / 0.376 | -60.25% / -60.25% |
| a3-kimi4-tp16-128k-decode-c24-p8k | 24 / 1 | moe_layer | 3 | 1.331 / 1.343 | 1.182 / 1.064 | -11.16% / -20.80% |
| a3-kimi4-tp16-128k-decode-c2-p4k | 2 / 1 | kda | 3 | 0.969 / 0.954 | 0.627 / 0.771 | -35.29% / -19.20% |
| a3-kimi4-tp16-128k-decode-c2-p4k | 2 / 1 | mla | 1 | 1.148 / 1.148 | 0.835 / 0.835 | -27.31% / -27.31% |
| a3-kimi4-tp16-128k-decode-c2-p4k | 2 / 1 | dense_layer | 1 | 0.954 / 0.954 | 0.339 / 0.339 | -64.49% / -64.49% |
| a3-kimi4-tp16-128k-decode-c2-p4k | 2 / 1 | moe_layer | 3 | 1.034 / 1.019 | 0.792 / 0.771 | -23.35% / -24.36% |
| a3-kimi4-tp16-128k-decode-c48-p4k | 48 / 1 | kda | 3 | 1.425 / 1.510 | 1.047 / 1.362 | -26.52% / -9.79% |
| a3-kimi4-tp16-128k-decode-c48-p4k | 48 / 1 | mla | 1 | 1.925 / 1.925 | 1.697 / 1.697 | -11.86% / -11.86% |
| a3-kimi4-tp16-128k-decode-c48-p4k | 48 / 1 | dense_layer | 1 | 1.011 / 1.011 | 0.417 / 0.417 | -58.78% / -58.78% |
| a3-kimi4-tp16-128k-decode-c48-p4k | 48 / 1 | moe_layer | 3 | 1.730 / 1.754 | 1.474 / 1.362 | -14.80% / -22.33% |
| a3-kimi4-tp16-128k-decode-c6-p4k | 6 / 1 | kda | 3 | 0.981 / 0.951 | 0.631 / 0.775 | -35.65% / -18.51% |
| a3-kimi4-tp16-128k-decode-c6-p4k | 6 / 1 | mla | 1 | 1.167 / 1.167 | 0.866 / 0.866 | -25.77% / -25.77% |
| a3-kimi4-tp16-128k-decode-c6-p4k | 6 / 1 | dense_layer | 1 | 0.937 / 0.937 | 0.343 / 0.343 | -63.38% / -63.38% |
| a3-kimi4-tp16-128k-decode-c6-p4k | 6 / 1 | moe_layer | 3 | 1.057 / 1.054 | 0.805 / 0.775 | -23.83% / -26.48% |
| a3-kimi4-tp16-128k-decode-c8-p4k | 8 / 1 | kda | 3 | 1.013 / 0.983 | 0.635 / 0.779 | -37.30% / -20.73% |
| a3-kimi4-tp16-128k-decode-c8-p4k | 8 / 1 | mla | 1 | 1.147 / 1.147 | 0.881 / 0.881 | -23.15% / -23.15% |
| a3-kimi4-tp16-128k-decode-c8-p4k | 8 / 1 | dense_layer | 1 | 0.983 / 0.983 | 0.347 / 0.347 | -64.67% / -64.67% |
| a3-kimi4-tp16-128k-decode-c8-p4k | 8 / 1 | moe_layer | 3 | 1.068 / 1.092 | 0.813 / 0.779 | -23.84% / -28.65% |
| a5_kimi_tp8_e16_bf16_128k_c1 | 1 / 1 | kda | 69 | 0.323 / 0.324 | 0.278 / 0.279 | -13.85% / -13.73% |
| a5_kimi_tp8_e16_bf16_128k_c1 | 1 / 1 | mla | 24 | 0.424 / 0.417 | 0.291 / 0.291 | -31.50% / -30.35% |
| a5_kimi_tp8_e16_bf16_128k_c1 | 1 / 1 | dense_layer | 1 | 0.276 / 0.276 | 0.208 / 0.208 | -24.54% / -24.54% |
| a5_kimi_tp8_e16_bf16_128k_c1 | 1 / 1 | moe_layer | 92 | 0.350 / 0.325 | 0.282 / 0.283 | -19.34% / -13.08% |
| a5_kimi_tp8_e16_bf16_128k_c2 | 2 / 1 | kda | 69 | 0.356 / 0.357 | 0.279 / 0.280 | -21.60% / -21.63% |
| a5_kimi_tp8_e16_bf16_128k_c2 | 2 / 1 | mla | 24 | 0.512 / 0.505 | 0.327 / 0.327 | -36.08% / -35.24% |
| a5_kimi_tp8_e16_bf16_128k_c2 | 2 / 1 | dense_layer | 1 | 0.288 / 0.288 | 0.209 / 0.209 | -27.57% / -27.57% |
| a5_kimi_tp8_e16_bf16_128k_c2 | 2 / 1 | moe_layer | 92 | 0.397 / 0.359 | 0.292 / 0.284 | -26.42% / -20.86% |
| a5_kimi_tp8_e16_bf16_128k_c4 | 4 / 1 | kda | 69 | 0.363 / 0.364 | 0.281 / 0.281 | -22.74% / -22.65% |
| a5_kimi_tp8_e16_bf16_128k_c4 | 4 / 1 | mla | 24 | 0.640 / 0.632 | 0.401 / 0.401 | -37.35% / -36.59% |
| a5_kimi_tp8_e16_bf16_128k_c4 | 4 / 1 | dense_layer | 1 | 0.302 / 0.302 | 0.210 / 0.210 | -30.50% / -30.50% |
| a5_kimi_tp8_e16_bf16_128k_c4 | 4 / 1 | moe_layer | 92 | 0.436 / 0.366 | 0.313 / 0.285 | -28.27% / -21.92% |
| a5_kimi_tp8_e16_bf16_128k_c6 | 6 / 1 | kda | 69 | 0.367 / 0.368 | 0.284 / 0.285 | -22.55% / -22.56% |
| a5_kimi_tp8_e16_bf16_128k_c6 | 6 / 1 | mla | 24 | 0.760 / 0.754 | 0.474 / 0.474 | -37.67% / -37.17% |
| a5_kimi_tp8_e16_bf16_128k_c6 | 6 / 1 | dense_layer | 1 | 0.308 / 0.308 | 0.214 / 0.214 | -30.61% / -30.61% |
| a5_kimi_tp8_e16_bf16_128k_c6 | 6 / 1 | moe_layer | 92 | 0.470 / 0.370 | 0.335 / 0.289 | -28.87% / -21.76% |
| a5_kimi_tp8_e16_bf16_128k_c8 | 8 / 1 | kda | 69 | 0.369 / 0.370 | 0.285 / 0.285 | -22.81% / -22.87% |
| a5_kimi_tp8_e16_bf16_128k_c8 | 8 / 1 | mla | 24 | 0.886 / 0.878 | 0.546 / 0.546 | -38.29% / -37.75% |
| a5_kimi_tp8_e16_bf16_128k_c8 | 8 / 1 | dense_layer | 1 | 0.301 / 0.301 | 0.214 / 0.214 | -28.95% / -28.95% |
| a5_kimi_tp8_e16_bf16_128k_c8 | 8 / 1 | moe_layer | 92 | 0.504 / 0.371 | 0.354 / 0.289 | -29.86% / -22.00% |
| a5_kimi_tp8_e16_bf16_128k_c12 | 12 / 1 | kda | 69 | 0.387 / 0.387 | 0.296 / 0.297 | -23.37% / -23.25% |
| a5_kimi_tp8_e16_bf16_128k_c12 | 12 / 1 | mla | 24 | 1.145 / 1.138 | 0.699 / 0.698 | -38.98% / -38.64% |
| a5_kimi_tp8_e16_bf16_128k_c12 | 12 / 1 | dense_layer | 1 | 0.314 / 0.314 | 0.227 / 0.227 | -27.68% / -27.68% |
| a5_kimi_tp8_e16_bf16_128k_c12 | 12 / 1 | moe_layer | 92 | 0.585 / 0.390 | 0.402 / 0.301 | -31.31% / -22.72% |
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
| a3-v41-tp4dp4-128k-c48 | 13 / 8 | mla | 40 | 1.849 / 1.392 | 1.596 / 1.459 | -13.68% / +4.77% |
| a3-v41-tp4dp4-128k-c48 | 13 / 8 | moe_layer | 40 | 1.849 / 1.392 | 1.596 / 1.459 | -13.68% / +4.77% |
| a3-v41-tp4dp4-128k-c64 | 17 / 8 | mla | 40 | 1.936 / 1.475 | 1.729 / 1.554 | -10.71% / +5.34% |
| a3-v41-tp4dp4-128k-c64 | 17 / 8 | moe_layer | 40 | 1.936 / 1.475 | 1.729 / 1.554 | -10.71% / +5.34% |
| a3-v41-tp4dp4-128k-c8 | 3 / 8 | mla | 40 | 1.339 / 1.163 | 1.297 / 1.255 | -3.12% / +7.93% |
| a3-v41-tp4dp4-128k-c8 | 3 / 8 | moe_layer | 40 | 1.339 / 1.163 | 1.297 / 1.255 | -3.12% / +7.93% |
| a3-qwen35-tp4-decode-c1-p126000 | 1 / 4 | gdn | 30 | 0.407 / 0.407 | 0.218 / 0.218 | -46.39% / -46.30% |
| a3-qwen35-tp4-decode-c1-p126000 | 1 / 4 | gqa | 10 | 0.526 / 0.526 | 0.303 / 0.303 | -42.35% / -42.38% |
| a3-qwen35-tp4-decode-c1-p126000 | 1 / 4 | moe_layer | 40 | 0.437 / 0.410 | 0.240 / 0.218 | -45.18% / -46.74% |
| a3-qwen35-tp4-decode-c12-p126000 | 12 / 4 | gdn | 30 | 0.654 / 0.652 | 0.469 / 0.469 | -28.30% / -28.01% |
| a3-qwen35-tp4-decode-c12-p126000 | 12 / 4 | gqa | 10 | 1.652 / 1.649 | 1.930 / 1.930 | +16.85% / +17.04% |
| a3-qwen35-tp4-decode-c12-p126000 | 12 / 4 | moe_layer | 40 | 0.904 / 0.658 | 0.834 / 0.469 | -7.67% / -28.68% |
| a3-qwen35-tp4-decode-c16-p126000 | 16 / 4 | gdn | 30 | 0.688 / 0.687 | 0.498 / 0.498 | -27.67% / -27.55% |
| a3-qwen35-tp4-decode-c16-p126000 | 16 / 4 | gqa | 10 | 1.999 / 1.996 | 2.454 / 2.454 | +22.77% / +22.91% |
| a3-qwen35-tp4-decode-c16-p126000 | 16 / 4 | moe_layer | 40 | 1.016 / 0.692 | 0.987 / 0.498 | -2.85% / -28.13% |
| a3-qwen35-tp4-decode-c2-p126000 | 2 / 4 | gdn | 30 | 0.447 / 0.443 | 0.247 / 0.247 | -44.66% / -44.20% |
| a3-qwen35-tp4-decode-c2-p126000 | 2 / 4 | gqa | 10 | 0.615 / 0.615 | 0.457 / 0.457 | -25.77% / -25.81% |
| a3-qwen35-tp4-decode-c2-p126000 | 2 / 4 | moe_layer | 40 | 0.489 / 0.447 | 0.300 / 0.247 | -38.72% / -44.62% |
| a3-qwen35-tp4-decode-c24-p126000 | 24 / 4 | gdn | 30 | 0.744 / 0.740 | 0.550 / 0.550 | -26.00% / -25.63% |
| a3-qwen35-tp4-decode-c24-p126000 | 24 / 4 | gqa | 10 | 4.115 / 4.114 | 3.679 / 3.679 | -10.60% / -10.57% |
| a3-qwen35-tp4-decode-c24-p126000 | 24 / 4 | moe_layer | 40 | 1.587 / 0.745 | 1.333 / 0.550 | -16.02% / -26.14% |
| a3-qwen35-tp4-decode-c32-p126000 | 32 / 4 | gdn | 30 | 0.794 / 0.790 | 0.614 / 0.614 | -22.64% / -22.29% |
| a3-qwen35-tp4-decode-c32-p126000 | 32 / 4 | gqa | 10 | 4.151 / 4.146 | 3.700 / 3.700 | -10.85% / -10.74% |
| a3-qwen35-tp4-decode-c32-p126000 | 32 / 4 | moe_layer | 40 | 1.633 / 0.798 | 1.385 / 0.614 | -15.15% / -23.07% |
| a3-qwen35-tp4-decode-c4-p126000 | 4 / 4 | gdn | 30 | 0.481 / 0.482 | 0.307 / 0.307 | -36.13% / -36.34% |
| a3-qwen35-tp4-decode-c4-p126000 | 4 / 4 | gqa | 10 | 0.842 / 0.843 | 0.774 / 0.774 | -8.14% / -8.21% |
| a3-qwen35-tp4-decode-c4-p126000 | 4 / 4 | moe_layer | 40 | 0.571 / 0.484 | 0.424 / 0.307 | -25.81% / -36.59% |
| a3-qwen35-tp4-decode-c48-p126000 | 48 / 4 | gdn | 30 | 0.909 / 0.906 | 0.717 / 0.717 | -21.12% / -20.80% |
| a3-qwen35-tp4-decode-c48-p126000 | 48 / 4 | gqa | 10 | 5.914 / 5.908 | 5.375 / 5.375 | -9.12% / -9.03% |
| a3-qwen35-tp4-decode-c48-p126000 | 48 / 4 | moe_layer | 40 | 2.160 / 0.913 | 1.882 / 0.717 | -12.91% / -21.45% |
| a3-qwen35-tp4-decode-c6-p126000 | 6 / 4 | gdn | 30 | 0.558 / 0.555 | 0.382 / 0.382 | -31.65% / -31.28% |
| a3-qwen35-tp4-decode-c6-p126000 | 6 / 4 | gqa | 10 | 1.079 / 1.075 | 1.086 / 1.086 | +0.65% / +0.98% |
| a3-qwen35-tp4-decode-c6-p126000 | 6 / 4 | moe_layer | 40 | 0.688 / 0.558 | 0.558 / 0.382 | -19.00% / -31.62% |
| a3-qwen35-tp4-decode-c64-p126000 | 64 / 4 | gdn | 30 | 1.011 / 1.007 | 0.804 / 0.804 | -20.48% / -20.18% |
| a3-qwen35-tp4-decode-c64-p126000 | 64 / 4 | gqa | 10 | 7.732 / 7.732 | 7.040 / 7.040 | -8.95% / -8.95% |
| a3-qwen35-tp4-decode-c64-p126000 | 64 / 4 | moe_layer | 40 | 2.691 / 1.011 | 2.363 / 0.804 | -12.20% / -20.51% |
| a3-qwen35-tp4-decode-c8-p126000 | 8 / 4 | gdn | 30 | 0.601 / 0.600 | 0.440 / 0.440 | -26.79% / -26.67% |
| a3-qwen35-tp4-decode-c8-p126000 | 8 / 4 | gqa | 10 | 1.294 / 1.292 | 1.404 / 1.404 | +8.50% / +8.67% |
| a3-qwen35-tp4-decode-c8-p126000 | 8 / 4 | moe_layer | 40 | 0.775 / 0.603 | 0.681 / 0.440 | -12.05% / -26.94% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gdn | 30 | 0.659 / 0.657 | 0.469 / 0.469 | -28.76% / -28.63% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gqa | 10 | 0.813 / 0.813 | 0.673 / 0.673 | -17.23% / -17.21% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | moe_layer | 40 | 0.697 / 0.664 | 0.520 / 0.469 | -25.40% / -29.32% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gdn | 30 | 0.658 / 0.656 | 0.469 / 0.469 | -28.67% / -28.43% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gqa | 10 | 0.785 / 0.786 | 0.673 / 0.673 | -14.25% / -14.39% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | moe_layer | 40 | 0.689 / 0.663 | 0.520 / 0.469 | -24.56% / -29.22% |
| a3-qwen35-tp4-decode-c12-p24512 | 4 / 4 | gdn | 30 | 0.489 / 0.482 | 0.307 / 0.307 | -37.16% / -36.31% |
| a3-qwen35-tp4-decode-c12-p24512 | 4 / 4 | gqa | 10 | 0.547 / 0.550 | 0.350 / 0.350 | -36.01% / -36.28% |
| a3-qwen35-tp4-decode-c12-p24512 | 4 / 4 | moe_layer | 40 | 0.503 / 0.489 | 0.318 / 0.307 | -36.85% / -37.16% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gdn | 30 | 0.637 / 0.637 | 0.469 / 0.469 | -26.31% / -26.34% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gqa | 10 | 0.761 / 0.760 | 0.673 / 0.673 | -11.56% / -11.47% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | moe_layer | 40 | 0.668 / 0.641 | 0.520 / 0.469 | -22.11% / -26.83% |
| a3-qwen35-tp4-decode-c12-p24512 | 6 / 4 | gdn | 30 | 0.544 / 0.542 | 0.382 / 0.382 | -29.79% / -29.54% |
| a3-qwen35-tp4-decode-c12-p24512 | 6 / 4 | gqa | 10 | 0.622 / 0.622 | 0.462 / 0.462 | -25.83% / -25.82% |
| a3-qwen35-tp4-decode-c12-p24512 | 6 / 4 | moe_layer | 40 | 0.563 / 0.550 | 0.402 / 0.382 | -28.70% / -30.56% |
| a3-qwen35-tp4-decode-c12-p24512 | 3 / 4 | gdn | 30 | 0.471 / 0.471 | 0.277 / 0.277 | -41.30% / -41.27% |
| a3-qwen35-tp4-decode-c12-p24512 | 3 / 4 | gqa | 10 | 0.517 / 0.517 | 0.301 / 0.301 | -41.73% / -41.72% |
| a3-qwen35-tp4-decode-c12-p24512 | 3 / 4 | moe_layer | 40 | 0.483 / 0.474 | 0.283 / 0.277 | -41.42% / -41.61% |
| a3-qwen35-tp4-decode-c12-p24512 | 2 / 4 | gdn | 30 | 0.449 / 0.444 | 0.247 / 0.247 | -44.87% / -44.26% |
| a3-qwen35-tp4-decode-c12-p24512 | 2 / 4 | gqa | 10 | 0.476 / 0.477 | 0.244 / 0.244 | -48.67% / -48.84% |
| a3-qwen35-tp4-decode-c12-p24512 | 2 / 4 | moe_layer | 40 | 0.455 / 0.447 | 0.247 / 0.247 | -45.86% / -44.69% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gdn | 30 | 0.640 / 0.639 | 0.469 / 0.469 | -26.72% / -26.62% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gqa | 10 | 0.808 / 0.803 | 0.673 / 0.673 | -16.76% / -16.20% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | moe_layer | 40 | 0.682 / 0.643 | 0.520 / 0.469 | -23.77% / -27.05% |
| a3-qwen35-tp4-decode-c12-p24512 | 8 / 4 | gdn | 30 | 0.608 / 0.599 | 0.440 / 0.440 | -27.54% / -26.54% |
| a3-qwen35-tp4-decode-c12-p24512 | 8 / 4 | gqa | 10 | 0.698 / 0.698 | 0.569 / 0.569 | -18.41% / -18.44% |
| a3-qwen35-tp4-decode-c12-p24512 | 8 / 4 | moe_layer | 40 | 0.630 / 0.606 | 0.472 / 0.440 | -25.02% / -27.39% |
| a3-qwen35-tp4-decode-c12-p24512 | 1 / 4 | gdn | 30 | 0.406 / 0.404 | 0.218 / 0.218 | -46.24% / -45.94% |
| a3-qwen35-tp4-decode-c12-p24512 | 1 / 4 | gqa | 10 | 0.423 / 0.426 | 0.197 / 0.197 | -53.49% / -53.76% |
| a3-qwen35-tp4-decode-c12-p24512 | 1 / 4 | moe_layer | 40 | 0.410 / 0.406 | 0.213 / 0.218 | -48.11% / -46.27% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gdn | 30 | 0.661 / 0.656 | 0.469 / 0.469 | -29.06% / -28.47% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gqa | 10 | 1.068 / 1.068 | 1.169 / 1.169 | +9.48% / +9.49% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | moe_layer | 40 | 0.763 / 0.664 | 0.644 / 0.469 | -15.57% / -29.37% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gdn | 30 | 0.659 / 0.656 | 0.469 / 0.469 | -28.78% / -28.51% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gqa | 10 | 1.003 / 1.005 | 1.169 / 1.169 | +16.56% / +16.37% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | moe_layer | 40 | 0.745 / 0.663 | 0.644 / 0.469 | -13.51% / -29.22% |
| a3-qwen35-tp4-decode-c12-p64512 | 2 / 4 | gdn | 30 | 0.445 / 0.443 | 0.247 / 0.247 | -44.39% / -44.12% |
| a3-qwen35-tp4-decode-c12-p64512 | 2 / 4 | gqa | 10 | 0.528 / 0.528 | 0.329 / 0.329 | -37.64% / -37.64% |
| a3-qwen35-tp4-decode-c12-p64512 | 2 / 4 | moe_layer | 40 | 0.466 / 0.445 | 0.268 / 0.247 | -42.48% / -44.46% |
| a3-qwen35-tp4-decode-c12-p64512 | 1 / 4 | gdn | 30 | 0.414 / 0.406 | 0.218 / 0.218 | -47.20% / -46.16% |
| a3-qwen35-tp4-decode-c12-p64512 | 1 / 4 | gqa | 10 | 0.470 / 0.471 | 0.240 / 0.240 | -48.92% / -49.03% |
| a3-qwen35-tp4-decode-c12-p64512 | 1 / 4 | moe_layer | 40 | 0.428 / 0.407 | 0.224 / 0.218 | -47.67% / -46.34% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gdn | 30 | 0.642 / 0.641 | 0.469 / 0.469 | -26.87% / -26.82% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gqa | 10 | 1.088 / 1.090 | 1.169 / 1.169 | +7.47% / +7.27% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | moe_layer | 40 | 0.753 / 0.645 | 0.644 / 0.469 | -14.47% / -27.23% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | gdn | 30 | 0.604 / 0.603 | 0.440 / 0.440 | -27.10% / -26.93% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | gqa | 10 | 0.900 / 0.900 | 0.897 / 0.897 | -0.37% / -0.38% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | moe_layer | 40 | 0.678 / 0.606 | 0.554 / 0.440 | -18.22% / -27.40% |
| a3-qwen35-tp4-decode-c12-p64512 | 4 / 4 | gdn | 30 | 0.491 / 0.483 | 0.307 / 0.307 | -37.45% / -36.43% |
| a3-qwen35-tp4-decode-c12-p64512 | 4 / 4 | gqa | 10 | 0.654 / 0.651 | 0.520 / 0.520 | -20.54% / -20.14% |
| a3-qwen35-tp4-decode-c12-p64512 | 4 / 4 | moe_layer | 40 | 0.532 / 0.487 | 0.360 / 0.307 | -32.25% / -36.95% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | gdn | 30 | 0.602 / 0.602 | 0.440 / 0.440 | -26.84% / -26.88% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | gqa | 10 | 0.856 / 0.848 | 0.897 / 0.897 | +4.72% / +5.78% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | moe_layer | 40 | 0.665 / 0.605 | 0.554 / 0.440 | -16.69% / -27.19% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | gdn | 30 | 0.560 / 0.560 | 0.382 / 0.382 | -31.79% / -31.88% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | gqa | 10 | 0.765 / 0.764 | 0.705 / 0.705 | -7.84% / -7.73% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | moe_layer | 40 | 0.611 / 0.563 | 0.463 / 0.382 | -24.29% / -32.18% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | gdn | 30 | 0.547 / 0.544 | 0.382 / 0.382 | -30.24% / -29.86% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | gqa | 10 | 0.759 / 0.759 | 0.705 / 0.705 | -7.10% / -7.14% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | moe_layer | 40 | 0.600 / 0.546 | 0.463 / 0.382 | -22.92% / -30.08% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gdn | 30 | 0.662 / 0.660 | 0.469 / 0.469 | -29.13% / -28.88% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gqa | 10 | 0.755 / 0.754 | 0.542 / 0.542 | -28.25% / -28.16% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | moe_layer | 40 | 0.685 / 0.663 | 0.487 / 0.469 | -28.89% / -29.22% |
| a3-qwen35-tp4-decode-c12-p8512 | 8 / 4 | gdn | 30 | 0.613 / 0.602 | 0.440 / 0.440 | -28.20% / -26.82% |
| a3-qwen35-tp4-decode-c12-p8512 | 8 / 4 | gqa | 10 | 0.642 / 0.644 | 0.439 / 0.439 | -31.64% / -31.76% |
| a3-qwen35-tp4-decode-c12-p8512 | 8 / 4 | moe_layer | 40 | 0.620 / 0.604 | 0.440 / 0.440 | -29.09% / -27.12% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gdn | 30 | 0.640 / 0.640 | 0.469 / 0.469 | -26.66% / -26.67% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gqa | 10 | 0.751 / 0.752 | 0.542 / 0.542 | -27.91% / -27.96% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | moe_layer | 40 | 0.668 / 0.642 | 0.487 / 0.469 | -27.01% / -26.94% |
| a3-qwen35-tp4-decode-c12-p8512 | 1 / 4 | gdn | 30 | 0.413 / 0.405 | 0.218 / 0.218 | -47.09% / -46.06% |
| a3-qwen35-tp4-decode-c12-p8512 | 1 / 4 | gqa | 10 | 0.407 / 0.408 | 0.176 / 0.176 | -56.75% / -56.88% |
| a3-qwen35-tp4-decode-c12-p8512 | 1 / 4 | moe_layer | 40 | 0.411 / 0.406 | 0.208 / 0.218 | -49.48% / -46.19% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gdn | 30 | 0.637 / 0.635 | 0.469 / 0.469 | -26.31% / -26.11% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gqa | 10 | 0.744 / 0.740 | 0.542 / 0.542 | -27.25% / -26.83% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | moe_layer | 40 | 0.664 / 0.643 | 0.487 / 0.469 | -26.57% / -26.98% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | gdn | 30 | 0.559 / 0.546 | 0.382 / 0.382 | -31.76% / -30.11% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | gqa | 10 | 0.577 / 0.577 | 0.364 / 0.364 | -37.02% / -36.96% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | moe_layer | 40 | 0.564 / 0.550 | 0.377 / 0.382 | -33.10% / -30.59% |
| a3-qwen35-tp4-decode-c12-p8512 | 2 / 4 | gdn | 30 | 0.460 / 0.444 | 0.247 / 0.247 | -46.22% / -44.24% |
| a3-qwen35-tp4-decode-c12-p8512 | 2 / 4 | gqa | 10 | 0.448 / 0.451 | 0.219 / 0.219 | -51.07% / -51.37% |
| a3-qwen35-tp4-decode-c12-p8512 | 2 / 4 | moe_layer | 40 | 0.457 / 0.446 | 0.240 / 0.247 | -47.41% / -44.50% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | gdn | 30 | 0.566 / 0.558 | 0.382 / 0.382 | -32.53% / -31.61% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | gqa | 10 | 0.590 / 0.591 | 0.364 / 0.364 | -38.36% / -38.48% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | moe_layer | 40 | 0.572 / 0.564 | 0.377 / 0.382 | -34.03% / -32.33% |
| a3-qwen35-tp4-decode-c12-p8512 | 4 / 4 | gdn | 30 | 0.501 / 0.486 | 0.307 / 0.307 | -38.74% / -36.88% |
| a3-qwen35-tp4-decode-c12-p8512 | 4 / 4 | gqa | 10 | 0.506 / 0.503 | 0.287 / 0.287 | -43.31% / -42.95% |
| a3-qwen35-tp4-decode-c12-p8512 | 4 / 4 | moe_layer | 40 | 0.502 / 0.490 | 0.302 / 0.307 | -39.89% / -37.36% |
| a3-qwen35-tp4-decode-c12-p8512 | 3 / 4 | gdn | 30 | 0.498 / 0.473 | 0.277 / 0.277 | -44.41% / -41.49% |
| a3-qwen35-tp4-decode-c12-p8512 | 3 / 4 | gqa | 10 | 0.491 / 0.490 | 0.249 / 0.249 | -49.31% / -49.21% |
| a3-qwen35-tp4-decode-c12-p8512 | 3 / 4 | moe_layer | 40 | 0.496 / 0.475 | 0.270 / 0.277 | -45.62% / -41.70% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gdn | 30 | 0.661 / 0.654 | 0.469 / 0.469 | -29.06% / -28.27% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gqa | 10 | 1.330 / 1.333 | 1.570 / 1.570 | +18.05% / +17.75% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | moe_layer | 40 | 0.828 / 0.660 | 0.744 / 0.469 | -10.16% / -28.96% |
| a3-qwen35-tp4-decode-c12-p96512 | 2 / 4 | gdn | 30 | 0.443 / 0.444 | 0.247 / 0.247 | -44.22% / -44.30% |
| a3-qwen35-tp4-decode-c12-p96512 | 2 / 4 | gqa | 10 | 0.576 / 0.578 | 0.398 / 0.398 | -30.98% / -31.15% |
| a3-qwen35-tp4-decode-c12-p96512 | 2 / 4 | moe_layer | 40 | 0.477 / 0.446 | 0.285 / 0.247 | -40.22% / -44.58% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gdn | 30 | 0.657 / 0.653 | 0.469 / 0.469 | -28.56% / -28.15% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gqa | 10 | 1.242 / 1.240 | 1.570 / 1.570 | +26.39% / +26.54% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | moe_layer | 40 | 0.803 / 0.662 | 0.744 / 0.469 | -7.31% / -29.17% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | gdn | 30 | 0.541 / 0.540 | 0.382 / 0.382 | -29.46% / -29.27% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | gqa | 10 | 0.863 / 0.863 | 0.911 / 0.911 | +5.52% / +5.56% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | moe_layer | 40 | 0.622 / 0.545 | 0.514 / 0.382 | -17.32% / -29.90% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gdn | 30 | 0.641 / 0.634 | 0.469 / 0.469 | -26.83% / -26.02% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gqa | 10 | 1.320 / 1.318 | 1.570 / 1.570 | +18.92% / +19.12% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | moe_layer | 40 | 0.811 / 0.642 | 0.744 / 0.469 | -8.22% / -26.94% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gdn | 30 | 0.638 / 0.635 | 0.469 / 0.469 | -26.46% / -26.09% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gqa | 10 | 1.136 / 1.135 | 1.570 / 1.570 | +38.21% / +38.28% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | moe_layer | 40 | 0.762 / 0.643 | 0.744 / 0.469 | -2.38% / -27.03% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | gdn | 30 | 0.609 / 0.605 | 0.440 / 0.440 | -27.67% / -27.26% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | gqa | 10 | 1.086 / 1.079 | 1.160 / 1.160 | +6.77% / +7.46% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | moe_layer | 40 | 0.728 / 0.615 | 0.620 / 0.440 | -14.83% / -28.44% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | gdn | 30 | 0.601 / 0.597 | 0.440 / 0.440 | -26.72% / -26.23% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | gqa | 10 | 1.012 / 1.014 | 1.160 / 1.160 | +14.59% / +14.38% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | moe_layer | 40 | 0.704 / 0.606 | 0.620 / 0.440 | -11.86% / -27.31% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | gdn | 30 | 0.558 / 0.557 | 0.382 / 0.382 | -31.61% / -31.52% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | gqa | 10 | 0.898 / 0.897 | 0.911 / 0.911 | +1.44% / +1.53% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | moe_layer | 40 | 0.643 / 0.561 | 0.514 / 0.382 | -20.07% / -31.96% |
| a3-qwen35-tp4-decode-c12-p96512 | 3 / 4 | gdn | 30 | 0.469 / 0.471 | 0.277 / 0.277 | -41.03% / -41.32% |
| a3-qwen35-tp4-decode-c12-p96512 | 3 / 4 | gqa | 10 | 0.655 / 0.658 | 0.524 / 0.524 | -20.04% / -20.45% |
| a3-qwen35-tp4-decode-c12-p96512 | 3 / 4 | moe_layer | 40 | 0.516 / 0.474 | 0.338 / 0.277 | -34.36% / -41.68% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.752 / 0.747 | 0.550 / 0.550 | -26.84% / -26.34% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.295 / 1.295 | 1.038 / 1.038 | -19.87% / -19.85% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.888 / 0.755 | 0.672 / 0.550 | -24.30% / -27.08% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.745 / 0.742 | 0.550 / 0.550 | -26.07% / -25.83% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.292 / 1.291 | 1.038 / 1.038 | -19.70% / -19.64% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.881 / 0.749 | 0.672 / 0.550 | -23.73% / -26.50% |
| a3-qwen35-tp4-decode-c24-p24512 | 16 / 4 | gdn | 30 | 0.680 / 0.676 | 0.498 / 0.498 | -26.83% / -26.36% |
| a3-qwen35-tp4-decode-c24-p24512 | 16 / 4 | gqa | 10 | 0.860 / 0.859 | 0.785 / 0.785 | -8.69% / -8.56% |
| a3-qwen35-tp4-decode-c24-p24512 | 16 / 4 | moe_layer | 40 | 0.725 / 0.682 | 0.569 / 0.498 | -21.46% / -27.02% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.747 / 0.742 | 0.550 / 0.550 | -26.27% / -25.83% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.287 / 1.290 | 1.038 / 1.038 | -19.36% / -19.55% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.882 / 0.748 | 0.672 / 0.550 | -23.75% / -26.45% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.745 / 0.743 | 0.550 / 0.550 | -26.14% / -25.87% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.286 / 1.290 | 1.038 / 1.038 | -19.34% / -19.54% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.881 / 0.747 | 0.672 / 0.550 | -23.66% / -26.34% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.728 / 0.728 | 0.550 / 0.550 | -24.34% / -24.41% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.072 / 1.071 | 1.038 / 1.038 | -3.25% / -3.10% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.814 / 0.731 | 0.672 / 0.550 | -17.39% / -24.75% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.731 / 0.726 | 0.550 / 0.550 | -24.67% / -24.19% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.055 / 1.057 | 1.038 / 1.038 | -1.64% / -1.83% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.812 / 0.732 | 0.672 / 0.550 | -17.19% / -24.85% |
| a3-qwen35-tp4-decode-c24-p64512 | 24 / 4 | gdn | 30 | 0.748 / 0.745 | 0.550 / 0.550 | -26.38% / -26.08% |
| a3-qwen35-tp4-decode-c24-p64512 | 24 / 4 | gqa | 10 | 2.241 / 2.240 | 2.079 / 2.079 | -7.24% / -7.21% |
| a3-qwen35-tp4-decode-c24-p64512 | 24 / 4 | moe_layer | 40 | 1.121 / 0.753 | 0.933 / 0.550 | -16.82% / -26.88% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.748 / 0.745 | 0.550 / 0.550 | -26.36% / -26.12% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.922 / 0.919 | 0.621 / 0.621 | -32.64% / -32.42% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.791 / 0.754 | 0.568 / 0.550 | -28.19% / -26.96% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.746 / 0.746 | 0.550 / 0.550 | -26.21% / -26.18% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.927 / 0.925 | 0.621 / 0.621 | -32.97% / -32.84% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.791 / 0.752 | 0.568 / 0.550 | -28.19% / -26.79% |
| a3-qwen35-tp4-decode-c24-p8512 | 1 / 4 | gdn | 30 | 0.405 / 0.406 | 0.218 / 0.218 | -46.14% / -46.23% |
| a3-qwen35-tp4-decode-c24-p8512 | 1 / 4 | gqa | 10 | 0.409 / 0.410 | 0.176 / 0.176 | -56.94% / -57.05% |
| a3-qwen35-tp4-decode-c24-p8512 | 1 / 4 | moe_layer | 40 | 0.406 / 0.407 | 0.208 / 0.218 | -48.86% / -46.30% |
| a3-qwen35-tp4-decode-c24-p8512 | 8 / 4 | gdn | 30 | 0.611 / 0.607 | 0.440 / 0.440 | -27.93% / -27.43% |
| a3-qwen35-tp4-decode-c24-p8512 | 8 / 4 | gqa | 10 | 0.645 / 0.643 | 0.439 / 0.439 | -31.92% / -31.72% |
| a3-qwen35-tp4-decode-c24-p8512 | 8 / 4 | moe_layer | 40 | 0.619 / 0.612 | 0.440 / 0.440 | -28.97% / -28.07% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.748 / 0.746 | 0.550 / 0.550 | -26.39% / -26.16% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.928 / 0.923 | 0.621 / 0.621 | -33.06% / -32.68% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.793 / 0.752 | 0.568 / 0.550 | -28.34% / -26.80% |
| a3-qwen35-tp4-decode-c24-p8512 | 6 / 4 | gdn | 30 | 0.576 / 0.561 | 0.382 / 0.382 | -33.77% / -31.91% |
| a3-qwen35-tp4-decode-c24-p8512 | 6 / 4 | gqa | 10 | 0.592 / 0.590 | 0.364 / 0.364 | -38.55% / -38.42% |
| a3-qwen35-tp4-decode-c24-p8512 | 6 / 4 | moe_layer | 40 | 0.580 / 0.566 | 0.377 / 0.382 | -34.99% / -32.55% |
| a3-qwen35-tp4-decode-c24-p8512 | 4 / 4 | gdn | 30 | 0.486 / 0.483 | 0.307 / 0.307 | -36.81% / -36.37% |
| a3-qwen35-tp4-decode-c24-p8512 | 4 / 4 | gqa | 10 | 0.503 / 0.503 | 0.287 / 0.287 | -42.96% / -42.96% |
| a3-qwen35-tp4-decode-c24-p8512 | 4 / 4 | moe_layer | 40 | 0.490 / 0.485 | 0.302 / 0.307 | -38.39% / -36.66% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.727 / 0.725 | 0.550 / 0.550 | -24.26% / -24.05% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.838 / 0.838 | 0.621 / 0.621 | -25.84% / -25.89% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.754 / 0.730 | 0.568 / 0.550 | -24.69% / -24.59% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.725 / 0.725 | 0.550 / 0.550 | -24.05% / -24.07% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.828 / 0.824 | 0.621 / 0.621 | -24.94% / -24.62% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.751 / 0.729 | 0.568 / 0.550 | -24.30% / -24.50% |
| a3-qwen35-tp4-decode-c24-p8512 | 16 / 4 | gdn | 30 | 0.674 / 0.674 | 0.498 / 0.498 | -26.18% / -26.16% |
| a3-qwen35-tp4-decode-c24-p8512 | 16 / 4 | gqa | 10 | 0.772 / 0.773 | 0.548 / 0.548 | -28.98% / -29.05% |
| a3-qwen35-tp4-decode-c24-p8512 | 16 / 4 | moe_layer | 40 | 0.699 / 0.680 | 0.510 / 0.498 | -26.95% / -26.84% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gdn | 30 | 0.655 / 0.657 | 0.469 / 0.469 | -28.37% / -28.58% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gqa | 10 | 0.748 / 0.745 | 0.542 / 0.542 | -27.56% / -27.33% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | moe_layer | 40 | 0.678 / 0.658 | 0.487 / 0.469 | -28.14% / -28.75% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gdn | 30 | 0.637 / 0.637 | 0.469 / 0.469 | -26.39% / -26.38% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gqa | 10 | 0.747 / 0.745 | 0.542 / 0.542 | -27.49% / -27.28% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | moe_layer | 40 | 0.665 / 0.642 | 0.487 / 0.469 | -26.70% / -26.92% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gdn | 30 | 0.634 / 0.633 | 0.469 / 0.469 | -26.03% / -25.93% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gqa | 10 | 0.745 / 0.745 | 0.542 / 0.542 | -27.32% / -27.27% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | moe_layer | 40 | 0.662 / 0.637 | 0.487 / 0.469 | -26.39% / -26.32% |
| a3-qwen35-tp4-decode-c24-p96512 | 24 / 4 | gdn | 30 | 0.746 / 0.743 | 0.550 / 0.550 | -26.20% / -25.88% |
| a3-qwen35-tp4-decode-c24-p96512 | 24 / 4 | gqa | 10 | 3.249 / 3.255 | 2.911 / 2.911 | -10.39% / -10.56% |
| a3-qwen35-tp4-decode-c24-p96512 | 24 / 4 | moe_layer | 40 | 1.372 / 0.748 | 1.141 / 0.550 | -16.84% / -26.42% |
| a3-qwen35-tp4-decode-c2-p24512 | 1 / 4 | gdn | 30 | 0.413 / 0.408 | 0.218 / 0.218 | -47.13% / -46.47% |
| a3-qwen35-tp4-decode-c2-p24512 | 1 / 4 | gqa | 10 | 0.428 / 0.429 | 0.197 / 0.197 | -54.01% / -54.09% |
| a3-qwen35-tp4-decode-c2-p24512 | 1 / 4 | moe_layer | 40 | 0.417 / 0.410 | 0.213 / 0.218 | -48.90% / -46.73% |
| a3-qwen35-tp4-decode-c2-p24512 | 2 / 4 | gdn | 30 | 0.446 / 0.443 | 0.247 / 0.247 | -44.58% / -44.11% |
| a3-qwen35-tp4-decode-c2-p24512 | 2 / 4 | gqa | 10 | 0.473 / 0.474 | 0.244 / 0.244 | -48.38% / -48.47% |
| a3-qwen35-tp4-decode-c2-p24512 | 2 / 4 | moe_layer | 40 | 0.453 / 0.446 | 0.247 / 0.247 | -45.57% / -44.54% |
| a3-qwen35-tp4-decode-c2-p64512 | 1 / 4 | gdn | 30 | 0.413 / 0.407 | 0.218 / 0.218 | -47.11% / -46.35% |
| a3-qwen35-tp4-decode-c2-p64512 | 1 / 4 | gqa | 10 | 0.472 / 0.473 | 0.240 / 0.240 | -49.21% / -49.23% |
| a3-qwen35-tp4-decode-c2-p64512 | 1 / 4 | moe_layer | 40 | 0.428 / 0.409 | 0.224 / 0.218 | -47.69% / -46.59% |
| a3-qwen35-tp4-decode-c2-p64512 | 2 / 4 | gdn | 30 | 0.447 / 0.442 | 0.247 / 0.247 | -44.63% / -44.01% |
| a3-qwen35-tp4-decode-c2-p64512 | 2 / 4 | gqa | 10 | 0.525 / 0.525 | 0.329 / 0.329 | -37.36% / -37.28% |
| a3-qwen35-tp4-decode-c2-p64512 | 2 / 4 | moe_layer | 40 | 0.466 / 0.445 | 0.268 / 0.247 | -42.58% / -44.44% |
| a3-qwen35-tp4-decode-c2-p8512 | 1 / 4 | gdn | 30 | 0.407 / 0.407 | 0.218 / 0.218 | -46.31% / -46.34% |
| a3-qwen35-tp4-decode-c2-p8512 | 1 / 4 | gqa | 10 | 0.409 / 0.412 | 0.176 / 0.176 | -56.97% / -57.27% |
| a3-qwen35-tp4-decode-c2-p8512 | 1 / 4 | moe_layer | 40 | 0.407 / 0.407 | 0.208 / 0.218 | -48.99% / -46.41% |
| a3-qwen35-tp4-decode-c2-p96512 | 1 / 4 | gdn | 30 | 0.410 / 0.408 | 0.218 / 0.218 | -46.79% / -46.48% |
| a3-qwen35-tp4-decode-c2-p96512 | 1 / 4 | gqa | 10 | 0.500 / 0.502 | 0.272 / 0.272 | -45.69% / -45.92% |
| a3-qwen35-tp4-decode-c2-p96512 | 1 / 4 | moe_layer | 40 | 0.433 / 0.411 | 0.232 / 0.218 | -46.47% / -46.87% |
| a3-qwen35-tp4-decode-c2-p96512 | 2 / 4 | gdn | 30 | 0.443 / 0.440 | 0.247 / 0.247 | -44.17% / -43.79% |
| a3-qwen35-tp4-decode-c2-p96512 | 2 / 4 | gqa | 10 | 0.571 / 0.569 | 0.398 / 0.398 | -30.30% / -30.14% |
| a3-qwen35-tp4-decode-c2-p96512 | 2 / 4 | moe_layer | 40 | 0.475 / 0.445 | 0.285 / 0.247 | -40.01% / -44.43% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | gdn | 30 | 0.563 / 0.557 | 0.382 / 0.382 | -32.22% / -31.51% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | gqa | 10 | 0.630 / 0.633 | 0.462 / 0.462 | -26.78% / -27.07% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | moe_layer | 40 | 0.580 / 0.562 | 0.402 / 0.382 | -30.74% / -32.02% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | gdn | 30 | 0.549 / 0.546 | 0.382 / 0.382 | -30.51% / -30.11% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | gqa | 10 | 0.623 / 0.625 | 0.462 / 0.462 | -25.87% / -26.09% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | moe_layer | 40 | 0.568 / 0.550 | 0.402 / 0.382 | -29.24% / -30.56% |
| a3-qwen35-tp4-decode-c6-p24512 | 1 / 4 | gdn | 30 | 0.410 / 0.409 | 0.218 / 0.218 | -46.72% / -46.57% |
| a3-qwen35-tp4-decode-c6-p24512 | 1 / 4 | gqa | 10 | 0.427 / 0.428 | 0.197 / 0.197 | -53.94% / -54.01% |
| a3-qwen35-tp4-decode-c6-p24512 | 1 / 4 | moe_layer | 40 | 0.414 / 0.410 | 0.213 / 0.218 | -48.58% / -46.76% |
| a3-qwen35-tp4-decode-c6-p24512 | 2 / 4 | gdn | 30 | 0.443 / 0.441 | 0.247 / 0.247 | -44.13% / -43.91% |
| a3-qwen35-tp4-decode-c6-p24512 | 2 / 4 | gqa | 10 | 0.474 / 0.476 | 0.244 / 0.244 | -48.49% / -48.69% |
| a3-qwen35-tp4-decode-c6-p24512 | 2 / 4 | moe_layer | 40 | 0.451 / 0.444 | 0.247 / 0.247 | -45.28% / -44.30% |
| a3-qwen35-tp4-decode-c6-p24512 | 3 / 4 | gdn | 30 | 0.466 / 0.467 | 0.277 / 0.277 | -40.64% / -40.79% |
| a3-qwen35-tp4-decode-c6-p24512 | 3 / 4 | gqa | 10 | 0.513 / 0.515 | 0.301 / 0.301 | -41.18% / -41.50% |
| a3-qwen35-tp4-decode-c6-p24512 | 3 / 4 | moe_layer | 40 | 0.478 / 0.469 | 0.283 / 0.277 | -40.78% / -41.04% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | gdn | 30 | 0.566 / 0.557 | 0.382 / 0.382 | -32.57% / -31.48% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | gqa | 10 | 0.766 / 0.767 | 0.705 / 0.705 | -7.92% / -8.09% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | moe_layer | 40 | 0.616 / 0.562 | 0.463 / 0.382 | -24.91% / -32.05% |
| a3-qwen35-tp4-decode-c6-p64512 | 2 / 4 | gdn | 30 | 0.451 / 0.444 | 0.247 / 0.247 | -45.18% / -44.27% |
| a3-qwen35-tp4-decode-c6-p64512 | 2 / 4 | gqa | 10 | 0.528 / 0.530 | 0.329 / 0.329 | -37.72% / -37.90% |
| a3-qwen35-tp4-decode-c6-p64512 | 2 / 4 | moe_layer | 40 | 0.471 / 0.447 | 0.268 / 0.247 | -43.08% / -44.66% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | gdn | 30 | 0.549 / 0.540 | 0.382 / 0.382 | -30.44% / -29.37% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | gqa | 10 | 0.756 / 0.748 | 0.705 / 0.705 | -6.69% / -5.70% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | moe_layer | 40 | 0.600 / 0.543 | 0.463 / 0.382 | -22.97% / -29.67% |
| a3-qwen35-tp4-decode-c6-p64512 | 3 / 4 | gdn | 30 | 0.503 / 0.469 | 0.277 / 0.277 | -44.97% / -40.96% |
| a3-qwen35-tp4-decode-c6-p64512 | 3 / 4 | gqa | 10 | 0.586 / 0.585 | 0.419 / 0.419 | -28.53% / -28.47% |
| a3-qwen35-tp4-decode-c6-p64512 | 3 / 4 | moe_layer | 40 | 0.524 / 0.471 | 0.312 / 0.277 | -40.38% / -41.30% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | gdn | 30 | 0.564 / 0.560 | 0.382 / 0.382 | -32.38% / -31.86% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | gqa | 10 | 0.589 / 0.593 | 0.364 / 0.364 | -38.24% / -38.65% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | moe_layer | 40 | 0.570 / 0.562 | 0.377 / 0.382 | -33.89% / -32.04% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | gdn | 30 | 0.552 / 0.543 | 0.382 / 0.382 | -30.82% / -29.69% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | gqa | 10 | 0.573 / 0.578 | 0.364 / 0.364 | -36.52% / -37.06% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | moe_layer | 40 | 0.557 / 0.545 | 0.377 / 0.382 | -32.29% / -29.99% |
| a3-qwen35-tp4-decode-c6-p8512 | 1 / 4 | gdn | 30 | 0.409 / 0.406 | 0.218 / 0.218 | -46.68% / -46.27% |
| a3-qwen35-tp4-decode-c6-p8512 | 1 / 4 | gqa | 10 | 0.410 / 0.411 | 0.176 / 0.176 | -57.09% / -57.19% |
| a3-qwen35-tp4-decode-c6-p8512 | 1 / 4 | moe_layer | 40 | 0.410 / 0.407 | 0.208 / 0.218 | -49.29% / -46.36% |
| a3-qwen35-tp4-decode-c6-p8512 | 4 / 4 | gdn | 30 | 0.490 / 0.486 | 0.307 / 0.307 | -37.40% / -36.84% |
| a3-qwen35-tp4-decode-c6-p8512 | 4 / 4 | gqa | 10 | 0.506 / 0.508 | 0.287 / 0.287 | -43.34% / -43.59% |
| a3-qwen35-tp4-decode-c6-p8512 | 4 / 4 | moe_layer | 40 | 0.494 / 0.489 | 0.302 / 0.307 | -38.92% / -37.22% |
| a3-qwen35-tp4-decode-c6-p8512 | 2 / 4 | gdn | 30 | 0.450 / 0.444 | 0.247 / 0.247 | -45.05% / -44.24% |
| a3-qwen35-tp4-decode-c6-p8512 | 2 / 4 | gqa | 10 | 0.442 / 0.442 | 0.219 / 0.219 | -50.42% / -50.41% |
| a3-qwen35-tp4-decode-c6-p8512 | 2 / 4 | moe_layer | 40 | 0.448 / 0.443 | 0.240 / 0.247 | -46.37% / -44.20% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | gdn | 30 | 0.562 / 0.558 | 0.382 / 0.382 | -32.05% / -31.62% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | gqa | 10 | 0.927 / 0.897 | 0.911 / 0.911 | -1.74% / +1.55% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | moe_layer | 40 | 0.653 / 0.560 | 0.514 / 0.382 | -21.30% / -31.87% |
| a3-qwen35-tp4-decode-c6-p96512 | 1 / 4 | gdn | 30 | 0.406 / 0.408 | 0.218 / 0.218 | -46.27% / -46.42% |
| a3-qwen35-tp4-decode-c6-p96512 | 1 / 4 | gqa | 10 | 0.498 / 0.500 | 0.272 / 0.272 | -45.45% / -45.63% |
| a3-qwen35-tp4-decode-c6-p96512 | 1 / 4 | moe_layer | 40 | 0.429 / 0.410 | 0.232 / 0.218 | -46.03% / -46.73% |
| a3-qwen35-tp4-decode-c6-p96512 | 4 / 4 | gdn | 30 | 0.487 / 0.484 | 0.307 / 0.307 | -36.96% / -36.60% |
| a3-qwen35-tp4-decode-c6-p96512 | 4 / 4 | gqa | 10 | 0.752 / 0.751 | 0.652 / 0.652 | -13.33% / -13.23% |
| a3-qwen35-tp4-decode-c6-p96512 | 4 / 4 | moe_layer | 40 | 0.553 / 0.489 | 0.393 / 0.307 | -28.93% / -37.16% |
| a3-qwen35-tp4-decode-c6-p96512 | 3 / 4 | gdn | 30 | 0.471 / 0.473 | 0.277 / 0.277 | -41.30% / -41.50% |
| a3-qwen35-tp4-decode-c6-p96512 | 3 / 4 | gqa | 10 | 0.657 / 0.655 | 0.524 / 0.524 | -20.31% / -20.09% |
| a3-qwen35-tp4-decode-c6-p96512 | 3 / 4 | moe_layer | 40 | 0.518 / 0.474 | 0.338 / 0.277 | -34.64% / -41.59% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | gdn | 30 | 0.540 / 0.541 | 0.382 / 0.382 | -29.33% / -29.50% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | gqa | 10 | 0.863 / 0.867 | 0.911 / 0.911 | +5.57% / +4.99% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | moe_layer | 40 | 0.621 / 0.544 | 0.514 / 0.382 | -17.21% / -29.82% |
| a3-qwen35-tp4-decode-c6-p96512 | 2 / 4 | gdn | 30 | 0.445 / 0.446 | 0.247 / 0.247 | -44.36% / -44.50% |
| a3-qwen35-tp4-decode-c6-p96512 | 2 / 4 | gqa | 10 | 0.573 / 0.571 | 0.398 / 0.398 | -30.65% / -30.32% |
| a3-qwen35-tp4-decode-c6-p96512 | 2 / 4 | moe_layer | 40 | 0.477 / 0.449 | 0.285 / 0.247 | -40.24% / -44.89% |
| a3-qwen36-tp2-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.370 / 0.368 | 0.310 / 0.310 | -16.09% / -15.69% |
| a3-qwen36-tp2-decode-c1-p126000 | 1 / 4 | gqa | 16 | 0.607 / 0.606 | 0.510 / 0.510 | -15.94% / -15.85% |
| a3-qwen36-tp2-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.429 / 0.371 | 0.360 / 0.310 | -16.04% / -16.41% |
| a3-qwen36-tp2-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.600 / 0.600 | 0.538 / 0.538 | -10.37% / -10.25% |
| a3-qwen36-tp2-decode-c12-p126000 | 12 / 4 | gqa | 16 | 4.006 / 4.006 | 3.801 / 3.801 | -5.12% / -5.11% |
| a3-qwen36-tp2-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 1.452 / 0.603 | 1.354 / 0.538 | -6.75% / -10.70% |
| a3-qwen36-tp2-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.666 / 0.666 | 0.615 / 0.615 | -7.77% / -7.65% |
| a3-qwen36-tp2-decode-c16-p126000 | 16 / 4 | gqa | 16 | 4.025 / 4.023 | 3.828 / 3.828 | -4.89% / -4.84% |
| a3-qwen36-tp2-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 1.506 / 0.669 | 1.418 / 0.615 | -5.84% / -8.13% |
| a3-qwen36-tp2-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.408 / 0.405 | 0.335 / 0.335 | -17.72% / -17.23% |
| a3-qwen36-tp2-decode-c2-p126000 | 2 / 4 | gqa | 16 | 0.775 / 0.775 | 0.786 / 0.786 | +1.37% / +1.36% |
| a3-qwen36-tp2-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.500 / 0.408 | 0.448 / 0.335 | -10.31% / -17.74% |
| a3-qwen36-tp2-decode-c24-p126000 | 24 / 4 | gdn | 48 | 0.796 / 0.795 | 0.781 / 0.781 | -1.86% / -1.74% |
| a3-qwen36-tp2-decode-c24-p126000 | 24 / 4 | gqa | 16 | 5.902 / 5.902 | 5.631 / 5.631 | -4.60% / -4.60% |
| a3-qwen36-tp2-decode-c24-p126000 | 24 / 4 | dense_layer | 64 | 2.073 / 0.797 | 1.994 / 0.781 | -3.81% / -1.94% |
| a3-qwen36-tp2-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.459 / 0.461 | 0.373 / 0.373 | -18.87% / -19.13% |
| a3-qwen36-tp2-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.171 / 1.170 | 1.331 / 1.331 | +13.66% / +13.70% |
| a3-qwen36-tp2-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.637 / 0.464 | 0.612 / 0.373 | -3.93% / -19.68% |
| a3-qwen36-tp2-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.489 / 0.489 | 0.411 / 0.411 | -15.99% / -15.99% |
| a3-qwen36-tp2-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.662 / 1.663 | 1.876 / 1.876 | +12.82% / +12.79% |
| a3-qwen36-tp2-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.782 / 0.493 | 0.777 / 0.411 | -0.68% / -16.76% |
| a3-qwen36-tp2-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.520 / 0.519 | 0.449 / 0.449 | -13.64% / -13.45% |
| a3-qwen36-tp2-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.959 / 1.960 | 2.421 / 2.421 | +23.60% / +23.53% |
| a3-qwen36-tp2-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.880 / 0.522 | 0.942 / 0.449 | +7.08% / -13.95% |
| a3-qwen36-tp2-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.602 / 0.601 | 0.538 / 0.538 | -10.62% / -10.53% |
| a3-qwen36-tp2-decode-c12-p24512 | 12 / 4 | gqa | 16 | 1.056 / 1.056 | 0.985 / 0.985 | -6.80% / -6.78% |
| a3-qwen36-tp2-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.716 / 0.603 | 0.650 / 0.538 | -9.21% / -10.72% |
| a3-qwen36-tp2-decode-c12-p64512 | 12 / 4 | gdn | 48 | 0.601 / 0.600 | 0.538 / 0.538 | -10.50% / -10.27% |
| a3-qwen36-tp2-decode-c12-p64512 | 12 / 4 | gqa | 16 | 2.170 / 2.170 | 2.095 / 2.095 | -3.46% / -3.46% |
| a3-qwen36-tp2-decode-c12-p64512 | 12 / 4 | dense_layer | 64 | 0.993 / 0.604 | 0.927 / 0.538 | -6.65% / -10.88% |
| a3-qwen36-tp2-decode-c12-p8512 | 12 / 4 | gdn | 48 | 0.602 / 0.601 | 0.538 / 0.538 | -10.58% / -10.43% |
| a3-qwen36-tp2-decode-c12-p8512 | 12 / 4 | gqa | 16 | 0.687 / 0.686 | 0.540 / 0.540 | -21.32% / -21.23% |
| a3-qwen36-tp2-decode-c12-p8512 | 12 / 4 | dense_layer | 64 | 0.623 / 0.603 | 0.539 / 0.538 | -13.54% / -10.71% |
| a3-qwen36-tp2-decode-c24-p24512 | 24 / 4 | gdn | 48 | 0.797 / 0.797 | 0.781 / 0.781 | -1.91% / -1.92% |
| a3-qwen36-tp2-decode-c24-p24512 | 24 / 4 | gqa | 16 | 1.410 / 1.407 | 1.406 / 1.406 | -0.29% / -0.08% |
| a3-qwen36-tp2-decode-c24-p24512 | 24 / 4 | dense_layer | 64 | 0.950 / 0.798 | 0.937 / 0.781 | -1.31% / -2.03% |
| a3-qwen36-tp2-decode-c24-p64512 | 24 / 4 | gdn | 48 | 0.796 / 0.796 | 0.781 / 0.781 | -1.83% / -1.80% |
| a3-qwen36-tp2-decode-c24-p64512 | 24 / 4 | gqa | 16 | 3.052 / 3.053 | 3.071 / 3.071 | +0.62% / +0.60% |
| a3-qwen36-tp2-decode-c24-p64512 | 24 / 4 | dense_layer | 64 | 1.360 / 0.797 | 1.354 / 0.781 | -0.45% / -1.97% |
| a3-qwen36-tp2-decode-c24-p8512 | 24 / 4 | gdn | 48 | 0.796 / 0.796 | 0.781 / 0.781 | -1.90% / -1.85% |
| a3-qwen36-tp2-decode-c24-p8512 | 24 / 4 | gqa | 16 | 0.868 / 0.868 | 0.740 / 0.740 | -14.75% / -14.76% |
| a3-qwen36-tp2-decode-c24-p8512 | 24 / 4 | dense_layer | 64 | 0.814 / 0.798 | 0.771 / 0.781 | -5.32% / -2.05% |
| a3-qwen36-tp2-decode-c2-p24512 | 2 / 4 | gdn | 48 | 0.410 / 0.409 | 0.335 / 0.335 | -18.26% / -18.00% |
| a3-qwen36-tp2-decode-c2-p24512 | 2 / 4 | gqa | 16 | 0.436 / 0.436 | 0.350 / 0.350 | -19.79% / -19.65% |
| a3-qwen36-tp2-decode-c2-p24512 | 2 / 4 | dense_layer | 64 | 0.417 / 0.412 | 0.339 / 0.335 | -18.66% / -18.59% |
| a3-qwen36-tp2-decode-c2-p24512 | 1 / 4 | gdn | 48 | 0.371 / 0.369 | 0.310 / 0.310 | -16.29% / -15.94% |
| a3-qwen36-tp2-decode-c2-p24512 | 1 / 4 | gqa | 16 | 0.390 / 0.391 | 0.291 / 0.291 | -25.38% / -25.57% |
| a3-qwen36-tp2-decode-c2-p24512 | 1 / 4 | dense_layer | 64 | 0.376 / 0.372 | 0.306 / 0.310 | -18.65% / -16.51% |
| a3-qwen36-tp2-decode-c2-p64512 | 2 / 4 | gdn | 48 | 0.407 / 0.406 | 0.335 / 0.335 | -17.58% / -17.43% |
| a3-qwen36-tp2-decode-c2-p64512 | 2 / 4 | gqa | 16 | 0.581 / 0.580 | 0.525 / 0.525 | -9.65% / -9.62% |
| a3-qwen36-tp2-decode-c2-p64512 | 2 / 4 | dense_layer | 64 | 0.450 / 0.408 | 0.383 / 0.335 | -15.02% / -17.79% |
| a3-qwen36-tp2-decode-c2-p64512 | 1 / 4 | gdn | 48 | 0.371 / 0.369 | 0.310 / 0.310 | -16.47% / -15.93% |
| a3-qwen36-tp2-decode-c2-p64512 | 1 / 4 | gqa | 16 | 0.481 / 0.480 | 0.379 / 0.379 | -21.21% / -21.07% |
| a3-qwen36-tp2-decode-c2-p64512 | 1 / 4 | dense_layer | 64 | 0.399 / 0.373 | 0.327 / 0.310 | -17.90% / -16.80% |
| a3-qwen36-tp2-decode-c2-p8512 | 2 / 4 | gdn | 48 | 0.409 / 0.408 | 0.335 / 0.335 | -17.97% / -17.73% |
| a3-qwen36-tp2-decode-c2-p8512 | 2 / 4 | gqa | 16 | 0.384 / 0.379 | 0.284 / 0.284 | -25.86% / -25.02% |
| a3-qwen36-tp2-decode-c2-p8512 | 2 / 4 | dense_layer | 64 | 0.403 / 0.407 | 0.323 / 0.335 | -19.85% / -17.51% |
| a3-qwen36-tp2-decode-c2-p8512 | 1 / 4 | gdn | 48 | 0.380 / 0.369 | 0.310 / 0.310 | -18.29% / -15.89% |
| a3-qwen36-tp2-decode-c2-p8512 | 1 / 4 | gqa | 16 | 0.351 / 0.350 | 0.265 / 0.265 | -24.53% / -24.27% |
| a3-qwen36-tp2-decode-c2-p8512 | 1 / 4 | dense_layer | 64 | 0.373 / 0.366 | 0.299 / 0.310 | -19.76% / -15.21% |
| a3-qwen36-tp2-decode-c2-p96512 | 2 / 4 | gdn | 48 | 0.404 / 0.403 | 0.335 / 0.335 | -17.00% / -16.86% |
| a3-qwen36-tp2-decode-c2-p96512 | 2 / 4 | gqa | 16 | 0.674 / 0.673 | 0.660 / 0.660 | -1.99% / -1.94% |
| a3-qwen36-tp2-decode-c2-p96512 | 2 / 4 | dense_layer | 64 | 0.472 / 0.407 | 0.417 / 0.335 | -11.64% / -17.61% |
| a3-qwen36-tp2-decode-c2-p96512 | 1 / 4 | gdn | 48 | 0.367 / 0.367 | 0.310 / 0.310 | -15.54% / -15.43% |
| a3-qwen36-tp2-decode-c2-p96512 | 1 / 4 | gqa | 16 | 0.549 / 0.549 | 0.449 / 0.449 | -18.09% / -18.13% |
| a3-qwen36-tp2-decode-c2-p96512 | 1 / 4 | dense_layer | 64 | 0.413 / 0.369 | 0.345 / 0.310 | -16.39% / -16.01% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | gdn | 48 | 0.492 / 0.490 | 0.411 / 0.411 | -16.57% / -16.28% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | gqa | 16 | 0.628 / 0.628 | 0.581 / 0.581 | -7.45% / -7.34% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | dense_layer | 64 | 0.526 / 0.494 | 0.453 / 0.411 | -13.85% / -16.90% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | gdn | 48 | 0.474 / 0.473 | 0.411 / 0.411 | -13.46% / -13.14% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | gqa | 16 | 0.586 / 0.586 | 0.581 / 0.581 | -0.84% / -0.81% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | dense_layer | 64 | 0.502 / 0.477 | 0.453 / 0.411 | -9.78% / -13.89% |
| a3-qwen36-tp2-decode-c6-p24512 | 2 / 4 | gdn | 48 | 0.410 / 0.408 | 0.335 / 0.335 | -18.12% / -17.89% |
| a3-qwen36-tp2-decode-c6-p24512 | 2 / 4 | gqa | 16 | 0.432 / 0.430 | 0.350 / 0.350 | -18.88% / -18.68% |
| a3-qwen36-tp2-decode-c6-p24512 | 2 / 4 | dense_layer | 64 | 0.415 / 0.412 | 0.339 / 0.335 | -18.32% / -18.61% |
| a3-qwen36-tp2-decode-c6-p24512 | 3 / 4 | gdn | 48 | 0.425 / 0.424 | 0.349 / 0.349 | -17.97% / -17.78% |
| a3-qwen36-tp2-decode-c6-p24512 | 3 / 4 | gqa | 16 | 0.490 / 0.490 | 0.410 / 0.410 | -16.31% / -16.33% |
| a3-qwen36-tp2-decode-c6-p24512 | 3 / 4 | dense_layer | 64 | 0.441 / 0.428 | 0.364 / 0.349 | -17.51% / -18.54% |
| a3-qwen36-tp2-decode-c6-p24512 | 1 / 4 | gdn | 48 | 0.370 / 0.369 | 0.310 / 0.310 | -16.15% / -15.80% |
| a3-qwen36-tp2-decode-c6-p24512 | 1 / 4 | gqa | 16 | 0.392 / 0.393 | 0.291 / 0.291 | -25.76% / -25.81% |
| a3-qwen36-tp2-decode-c6-p24512 | 1 / 4 | dense_layer | 64 | 0.376 / 0.371 | 0.306 / 0.310 | -18.66% / -16.44% |
| a3-qwen36-tp2-decode-c6-p64512 | 6 / 4 | gdn | 48 | 0.487 / 0.488 | 0.411 / 0.411 | -15.74% / -15.85% |
| a3-qwen36-tp2-decode-c6-p64512 | 6 / 4 | gqa | 16 | 1.018 / 1.013 | 1.093 / 1.093 | +7.40% / +7.85% |
| a3-qwen36-tp2-decode-c6-p64512 | 6 / 4 | dense_layer | 64 | 0.620 / 0.489 | 0.581 / 0.411 | -6.24% / -16.07% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | gdn | 48 | 0.493 / 0.491 | 0.411 / 0.411 | -16.76% / -16.34% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | gqa | 16 | 0.519 / 0.520 | 0.446 / 0.446 | -14.14% / -14.21% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | dense_layer | 64 | 0.500 / 0.494 | 0.419 / 0.411 | -16.08% / -16.88% |
| a3-qwen36-tp2-decode-c6-p8512 | 2 / 4 | gdn | 48 | 0.408 / 0.406 | 0.335 / 0.335 | -17.83% / -17.45% |
| a3-qwen36-tp2-decode-c6-p8512 | 2 / 4 | gqa | 16 | 0.376 / 0.375 | 0.284 / 0.284 | -24.40% / -24.25% |
| a3-qwen36-tp2-decode-c6-p8512 | 2 / 4 | dense_layer | 64 | 0.400 / 0.405 | 0.323 / 0.335 | -19.37% / -17.22% |
| a3-qwen36-tp2-decode-c6-p8512 | 4 / 4 | gdn | 48 | 0.459 / 0.457 | 0.373 / 0.373 | -18.84% / -18.55% |
| a3-qwen36-tp2-decode-c6-p8512 | 4 / 4 | gqa | 16 | 0.437 / 0.435 | 0.337 / 0.337 | -22.75% / -22.46% |
| a3-qwen36-tp2-decode-c6-p8512 | 4 / 4 | dense_layer | 64 | 0.454 / 0.455 | 0.364 / 0.373 | -19.79% / -18.03% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | gdn | 48 | 0.474 / 0.473 | 0.411 / 0.411 | -13.35% / -13.14% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | gqa | 16 | 0.514 / 0.516 | 0.446 / 0.446 | -13.33% / -13.63% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | dense_layer | 64 | 0.484 / 0.476 | 0.419 / 0.411 | -13.35% / -13.80% |
| a3-qwen36-tp2-decode-c6-p8512 | 3 / 4 | gdn | 48 | 0.423 / 0.424 | 0.349 / 0.349 | -17.64% / -17.71% |
| a3-qwen36-tp2-decode-c6-p8512 | 3 / 4 | gqa | 16 | 0.413 / 0.413 | 0.309 / 0.309 | -25.05% / -25.09% |
| a3-qwen36-tp2-decode-c6-p8512 | 3 / 4 | dense_layer | 64 | 0.421 / 0.420 | 0.339 / 0.349 | -19.46% / -16.90% |
| a3-qwen36-tp2-decode-c6-p96512 | 6 / 4 | gdn | 48 | 0.487 / 0.488 | 0.411 / 0.411 | -15.76% / -15.82% |
| a3-qwen36-tp2-decode-c6-p96512 | 6 / 4 | gqa | 16 | 1.317 / 1.318 | 1.505 / 1.505 | +14.25% / +14.19% |
| a3-qwen36-tp2-decode-c6-p96512 | 6 / 4 | dense_layer | 64 | 0.695 / 0.491 | 0.684 / 0.411 | -1.54% / -16.43% |
| a3-qwen36-tp4-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.279 / 0.276 | 0.221 / 0.221 | -20.72% / -19.88% |
| a3-qwen36-tp4-decode-c1-p126000 | 1 / 4 | gqa | 16 | 0.390 / 0.389 | 0.320 / 0.320 | -17.80% / -17.66% |
| a3-qwen36-tp4-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.307 / 0.280 | 0.246 / 0.221 | -19.79% / -20.87% |
| a3-qwen36-tp4-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.437 / 0.436 | 0.340 / 0.340 | -22.06% / -21.94% |
| a3-qwen36-tp4-decode-c12-p126000 | 12 / 4 | gqa | 16 | 1.454 / 1.453 | 1.828 / 1.828 | +25.76% / +25.79% |
| a3-qwen36-tp4-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 0.691 / 0.439 | 0.712 / 0.340 | +3.09% / -22.39% |
| a3-qwen36-tp4-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.482 / 0.480 | 0.383 / 0.383 | -20.45% / -20.14% |
| a3-qwen36-tp4-decode-c16-p126000 | 16 / 4 | gqa | 16 | 1.801 / 1.801 | 2.377 / 2.377 | +32.01% / +32.01% |
| a3-qwen36-tp4-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 0.812 / 0.483 | 0.882 / 0.383 | +8.64% / -20.58% |
| a3-qwen36-tp4-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.294 / 0.292 | 0.229 / 0.229 | -22.00% / -21.39% |
| a3-qwen36-tp4-decode-c2-p126000 | 2 / 4 | gqa | 16 | 0.482 / 0.474 | 0.453 / 0.453 | -6.01% / -4.47% |
| a3-qwen36-tp4-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.341 / 0.295 | 0.285 / 0.229 | -16.35% / -22.22% |
| a3-qwen36-tp4-decode-c24-p126000 | 24 / 4 | gdn | 48 | 0.551 / 0.550 | 0.481 / 0.481 | -12.72% / -12.68% |
| a3-qwen36-tp4-decode-c24-p126000 | 24 / 4 | gqa | 16 | 3.910 / 3.910 | 3.764 / 3.764 | -3.72% / -3.72% |
| a3-qwen36-tp4-decode-c24-p126000 | 24 / 4 | dense_layer | 64 | 1.390 / 0.553 | 1.302 / 0.481 | -6.40% / -13.08% |
| a3-qwen36-tp4-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.334 / 0.331 | 0.257 / 0.257 | -23.07% / -22.42% |
| a3-qwen36-tp4-decode-c4-p126000 | 4 / 4 | gqa | 16 | 0.682 / 0.675 | 0.731 / 0.731 | +7.19% / +8.35% |
| a3-qwen36-tp4-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.421 / 0.336 | 0.375 / 0.257 | -10.81% / -23.54% |
| a3-qwen36-tp4-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.364 / 0.362 | 0.272 / 0.272 | -25.32% / -24.95% |
| a3-qwen36-tp4-decode-c6-p126000 | 6 / 4 | gqa | 16 | 0.907 / 0.902 | 1.000 / 1.000 | +10.24% / +10.85% |
| a3-qwen36-tp4-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.500 / 0.366 | 0.454 / 0.272 | -9.20% / -25.74% |
| a3-qwen36-tp4-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.397 / 0.397 | 0.298 / 0.298 | -24.95% / -24.84% |
| a3-qwen36-tp4-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.092 / 1.092 | 1.279 / 1.279 | +17.12% / +17.18% |
| a3-qwen36-tp4-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.571 / 0.398 | 0.543 / 0.298 | -4.83% / -25.11% |
| a3-qwen38-tp2-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.369 / 0.369 | 0.310 / 0.310 | -15.96% / -15.92% |
| a3-qwen38-tp2-decode-c1-p126000 | 1 / 4 | gqa | 16 | 0.611 / 0.607 | 0.510 / 0.510 | -16.49% / -16.07% |
| a3-qwen38-tp2-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.430 / 0.371 | 0.360 / 0.310 | -16.15% / -16.40% |
| a3-qwen38-tp2-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.600 / 0.599 | 0.538 / 0.538 | -10.26% / -10.20% |
| a3-qwen38-tp2-decode-c12-p126000 | 12 / 4 | gqa | 16 | 4.025 / 4.010 | 3.801 / 3.801 | -5.56% / -5.20% |
| a3-qwen38-tp2-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 1.456 / 0.601 | 1.354 / 0.538 | -7.01% / -10.48% |
| a3-qwen38-tp2-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.661 / 0.661 | 0.615 / 0.615 | -7.02% / -7.05% |
| a3-qwen38-tp2-decode-c16-p126000 | 16 / 4 | gqa | 16 | 4.030 / 4.029 | 3.828 / 3.828 | -5.01% / -4.99% |
| a3-qwen38-tp2-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 1.503 / 0.663 | 1.418 / 0.615 | -5.68% / -7.32% |
| a3-qwen38-tp2-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.408 / 0.407 | 0.335 / 0.335 | -17.80% / -17.65% |
| a3-qwen38-tp2-decode-c2-p126000 | 2 / 4 | gqa | 16 | 0.780 / 0.778 | 0.786 / 0.786 | +0.77% / +1.03% |
| a3-qwen38-tp2-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.501 / 0.410 | 0.448 / 0.335 | -10.57% / -18.17% |
| a3-qwen38-tp2-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.454 / 0.454 | 0.373 / 0.373 | -17.93% / -17.89% |
| a3-qwen38-tp2-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.168 / 1.166 | 1.331 / 1.331 | +13.93% / +14.08% |
| a3-qwen38-tp2-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.632 / 0.458 | 0.612 / 0.373 | -3.22% / -18.65% |
| a3-qwen38-tp2-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.490 / 0.491 | 0.411 / 0.411 | -16.21% / -16.43% |
| a3-qwen38-tp2-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.669 / 1.669 | 1.876 / 1.876 | +12.37% / +12.40% |
| a3-qwen38-tp2-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.785 / 0.495 | 0.777 / 0.411 | -1.01% / -17.09% |
| a3-qwen38-tp2-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.519 / 0.519 | 0.449 / 0.449 | -13.51% / -13.46% |
| a3-qwen38-tp2-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.962 / 1.962 | 2.421 / 2.421 | +23.41% / +23.42% |
| a3-qwen38-tp2-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.880 / 0.523 | 0.942 / 0.449 | +7.07% / -14.03% |
| a3-qwen38-tp4-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.280 / 0.277 | 0.221 / 0.221 | -20.92% / -20.04% |
| a3-qwen38-tp4-decode-c1-p126000 | 1 / 4 | gqa | 16 | 0.400 / 0.391 | 0.320 / 0.320 | -19.90% / -18.03% |
| a3-qwen38-tp4-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.310 / 0.279 | 0.246 / 0.221 | -20.59% / -20.58% |
| a3-qwen38-tp4-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.438 / 0.436 | 0.340 / 0.340 | -22.21% / -21.89% |
| a3-qwen38-tp4-decode-c12-p126000 | 12 / 4 | gqa | 16 | 1.453 / 1.452 | 1.828 / 1.828 | +25.77% / +25.86% |
| a3-qwen38-tp4-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 0.692 / 0.438 | 0.712 / 0.340 | +3.00% / -22.25% |
| a3-qwen38-tp4-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.478 / 0.477 | 0.383 / 0.383 | -19.79% / -19.62% |
| a3-qwen38-tp4-decode-c16-p126000 | 16 / 4 | gqa | 16 | 1.800 / 1.800 | 2.377 / 2.377 | +32.07% / +32.06% |
| a3-qwen38-tp4-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 0.809 / 0.481 | 0.882 / 0.383 | +9.07% / -20.30% |
| a3-qwen38-tp4-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.295 / 0.292 | 0.229 / 0.229 | -22.20% / -21.45% |
| a3-qwen38-tp4-decode-c2-p126000 | 2 / 4 | gqa | 16 | 0.476 / 0.475 | 0.453 / 0.453 | -4.87% / -4.52% |
| a3-qwen38-tp4-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.340 / 0.296 | 0.285 / 0.229 | -16.13% / -22.49% |
| a3-qwen38-tp4-decode-c24-p126000 | 24 / 4 | gdn | 48 | 0.554 / 0.553 | 0.481 / 0.481 | -13.17% / -13.09% |
| a3-qwen38-tp4-decode-c24-p126000 | 24 / 4 | gqa | 16 | 3.899 / 3.896 | 3.764 / 3.764 | -3.44% / -3.37% |
| a3-qwen38-tp4-decode-c24-p126000 | 24 / 4 | dense_layer | 64 | 1.390 / 0.555 | 1.302 / 0.481 | -6.35% / -13.36% |
| a3-qwen38-tp4-decode-c32-p126000 | 32 / 4 | gdn | 48 | 0.623 / 0.623 | 0.568 / 0.568 | -8.91% / -8.86% |
| a3-qwen38-tp4-decode-c32-p126000 | 32 / 4 | gqa | 16 | 3.962 / 3.964 | 3.800 / 3.800 | -4.10% / -4.13% |
| a3-qwen38-tp4-decode-c32-p126000 | 32 / 4 | dense_layer | 64 | 1.458 / 0.624 | 1.376 / 0.568 | -5.64% / -9.02% |
| a3-qwen38-tp4-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.332 / 0.331 | 0.257 / 0.257 | -22.79% / -22.37% |
| a3-qwen38-tp4-decode-c4-p126000 | 4 / 4 | gqa | 16 | 0.676 / 0.675 | 0.731 / 0.731 | +8.18% / +8.35% |
| a3-qwen38-tp4-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.418 / 0.335 | 0.375 / 0.257 | -10.28% / -23.29% |
| a3-qwen38-tp4-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.364 / 0.363 | 0.272 / 0.272 | -25.22% / -25.05% |
| a3-qwen38-tp4-decode-c6-p126000 | 6 / 4 | gqa | 16 | 0.906 / 0.907 | 1.000 / 1.000 | +10.40% / +10.27% |
| a3-qwen38-tp4-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.499 / 0.366 | 0.454 / 0.272 | -9.07% / -25.65% |
| a3-qwen38-tp4-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.396 / 0.394 | 0.298 / 0.298 | -24.67% / -24.41% |
| a3-qwen38-tp4-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.089 / 1.088 | 1.279 / 1.279 | +17.49% / +17.62% |
| a3-qwen38-tp4-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.569 / 0.396 | 0.543 / 0.298 | -4.50% / -24.80% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.444 / 0.444 | 0.340 / 0.340 | -23.29% / -23.29% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gqa | 16 | 0.598 / 0.597 | 0.534 / 0.534 | -10.68% / -10.56% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.482 / 0.447 | 0.389 / 0.340 | -19.38% / -23.78% |
| a3-qwen38-tp4-decode-c12-p24512 | 1 / 4 | gdn | 48 | 0.277 / 0.275 | 0.221 / 0.221 | -20.04% / -19.37% |
| a3-qwen38-tp4-decode-c12-p24512 | 1 / 4 | gqa | 16 | 0.283 / 0.283 | 0.211 / 0.211 | -25.51% / -25.51% |
| a3-qwen38-tp4-decode-c12-p24512 | 1 / 4 | dense_layer | 64 | 0.278 / 0.276 | 0.219 / 0.221 | -21.43% / -19.68% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.424 / 0.425 | 0.340 / 0.340 | -19.80% / -19.92% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gqa | 16 | 0.565 / 0.565 | 0.534 / 0.534 | -5.43% / -5.51% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.459 / 0.427 | 0.389 / 0.340 | -15.39% / -20.28% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.441 / 0.442 | 0.340 / 0.340 | -22.88% / -23.04% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gqa | 16 | 0.566 / 0.564 | 0.534 / 0.534 | -5.63% / -5.38% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.472 / 0.444 | 0.389 / 0.340 | -17.71% / -23.37% |
| a3-qwen38-tp4-decode-c12-p24512 | 2 / 4 | gdn | 48 | 0.294 / 0.291 | 0.229 / 0.229 | -21.93% / -21.33% |
| a3-qwen38-tp4-decode-c12-p24512 | 2 / 4 | gqa | 16 | 0.320 / 0.320 | 0.234 / 0.234 | -26.74% / -26.73% |
| a3-qwen38-tp4-decode-c12-p24512 | 2 / 4 | dense_layer | 64 | 0.300 / 0.294 | 0.231 / 0.229 | -23.21% / -22.00% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.423 / 0.423 | 0.340 / 0.340 | -19.57% / -19.61% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gqa | 16 | 0.526 / 0.526 | 0.534 / 0.534 | +1.46% / +1.57% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.449 / 0.426 | 0.389 / 0.340 | -13.41% / -20.04% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | gdn | 48 | 0.372 / 0.366 | 0.272 / 0.272 | -26.86% / -25.67% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | gqa | 16 | 0.440 / 0.439 | 0.357 / 0.357 | -18.85% / -18.65% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | dense_layer | 64 | 0.389 / 0.368 | 0.293 / 0.272 | -24.59% / -26.07% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | gdn | 48 | 0.363 / 0.363 | 0.272 / 0.272 | -25.04% / -25.01% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | gqa | 16 | 0.427 / 0.425 | 0.357 / 0.357 | -16.35% / -15.99% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | dense_layer | 64 | 0.379 / 0.365 | 0.293 / 0.272 | -22.59% / -25.39% |
| a3-qwen38-tp4-decode-c12-p24512 | 3 / 4 | gdn | 48 | 0.304 / 0.304 | 0.238 / 0.238 | -21.71% / -21.68% |
| a3-qwen38-tp4-decode-c12-p24512 | 3 / 4 | gqa | 16 | 0.342 / 0.344 | 0.269 / 0.269 | -21.37% / -21.68% |
| a3-qwen38-tp4-decode-c12-p24512 | 3 / 4 | dense_layer | 64 | 0.313 / 0.306 | 0.246 / 0.238 | -21.62% / -22.33% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gdn | 48 | 0.443 / 0.443 | 0.340 / 0.340 | -23.12% / -23.07% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gqa | 16 | 0.909 / 0.908 | 1.045 / 1.045 | +14.97% / +15.07% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | dense_layer | 64 | 0.559 / 0.445 | 0.517 / 0.340 | -7.65% / -23.52% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gdn | 48 | 0.425 / 0.425 | 0.340 / 0.340 | -19.95% / -19.85% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gqa | 16 | 0.733 / 0.734 | 1.045 / 1.045 | +42.70% / +42.39% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | dense_layer | 64 | 0.502 / 0.426 | 0.517 / 0.340 | +2.90% / -20.18% |
| a3-qwen38-tp4-decode-c12-p64512 | 8 / 4 | gdn | 48 | 0.416 / 0.401 | 0.298 / 0.298 | -28.26% / -25.57% |
| a3-qwen38-tp4-decode-c12-p64512 | 8 / 4 | gqa | 16 | 0.695 / 0.694 | 0.757 / 0.757 | +8.94% / +9.12% |
| a3-qwen38-tp4-decode-c12-p64512 | 8 / 4 | dense_layer | 64 | 0.485 / 0.403 | 0.413 / 0.298 | -14.95% / -25.96% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gdn | 48 | 0.441 / 0.441 | 0.340 / 0.340 | -22.86% / -22.72% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gqa | 16 | 0.843 / 0.843 | 1.045 / 1.045 | +24.03% / +24.03% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | dense_layer | 64 | 0.542 / 0.444 | 0.517 / 0.340 | -4.62% / -23.26% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gdn | 48 | 0.442 / 0.442 | 0.340 / 0.340 | -22.97% / -23.01% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gqa | 16 | 1.158 / 1.157 | 1.457 / 1.457 | +25.83% / +25.93% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | dense_layer | 64 | 0.621 / 0.445 | 0.620 / 0.340 | -0.22% / -23.44% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gdn | 48 | 0.424 / 0.423 | 0.340 / 0.340 | -19.62% / -19.48% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gqa | 16 | 0.938 / 0.936 | 1.457 / 1.457 | +55.34% / +55.64% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | dense_layer | 64 | 0.552 / 0.425 | 0.620 / 0.340 | +12.22% / -19.98% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gdn | 48 | 0.440 / 0.441 | 0.340 / 0.340 | -22.68% / -22.87% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gqa | 16 | 1.067 / 1.066 | 1.457 / 1.457 | +36.52% / +36.62% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | dense_layer | 64 | 0.597 / 0.443 | 0.620 / 0.340 | +3.77% / -23.15% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gdn | 48 | 0.424 / 0.424 | 0.340 / 0.340 | -19.71% / -19.75% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gqa | 16 | 1.098 / 1.100 | 1.457 / 1.457 | +32.64% / +32.48% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | dense_layer | 64 | 0.593 / 0.427 | 0.620 / 0.340 | +4.55% / -20.28% |
| a3-qwen38-tp4-decode-c24-p24512 | 24 / 4 | gdn | 48 | 0.556 / 0.555 | 0.481 / 0.481 | -13.61% / -13.45% |
| a3-qwen38-tp4-decode-c24-p24512 | 24 / 4 | gqa | 16 | 1.055 / 1.056 | 0.948 / 0.948 | -10.19% / -10.24% |
| a3-qwen38-tp4-decode-c24-p24512 | 24 / 4 | dense_layer | 64 | 0.681 / 0.557 | 0.597 / 0.481 | -12.29% / -13.68% |
| a3-qwen38-tp4-decode-c24-p64512 | 24 / 4 | gdn | 48 | 0.556 / 0.555 | 0.481 / 0.481 | -13.50% / -13.48% |
| a3-qwen38-tp4-decode-c24-p64512 | 24 / 4 | gqa | 16 | 2.088 / 2.087 | 2.058 / 2.058 | -1.43% / -1.40% |
| a3-qwen38-tp4-decode-c24-p64512 | 24 / 4 | dense_layer | 64 | 0.939 / 0.556 | 0.875 / 0.481 | -6.79% / -13.58% |
| a3-qwen38-tp4-decode-c24-p96512 | 24 / 4 | gdn | 48 | 0.555 / 0.554 | 0.481 / 0.481 | -13.34% / -13.30% |
| a3-qwen38-tp4-decode-c24-p96512 | 24 / 4 | gqa | 16 | 3.031 / 3.033 | 2.946 / 2.946 | -2.81% / -2.87% |
| a3-qwen38-tp4-decode-c24-p96512 | 24 / 4 | dense_layer | 64 | 1.174 / 0.556 | 1.097 / 0.481 | -6.54% / -13.50% |
| a3-qwen38-tp4-decode-c2-p24512 | 2 / 4 | gdn | 48 | 0.294 / 0.292 | 0.229 / 0.229 | -22.05% / -21.48% |
| a3-qwen38-tp4-decode-c2-p24512 | 2 / 4 | gqa | 16 | 0.327 / 0.321 | 0.234 / 0.234 | -28.37% / -27.00% |
| a3-qwen38-tp4-decode-c2-p24512 | 2 / 4 | dense_layer | 64 | 0.302 / 0.295 | 0.231 / 0.229 | -23.76% / -22.18% |
| a3-qwen38-tp4-decode-c2-p24512 | 1 / 4 | gdn | 48 | 0.276 / 0.275 | 0.221 / 0.221 | -19.83% / -19.51% |
| a3-qwen38-tp4-decode-c2-p24512 | 1 / 4 | gqa | 16 | 0.282 / 0.282 | 0.211 / 0.211 | -25.42% / -25.35% |
| a3-qwen38-tp4-decode-c2-p24512 | 1 / 4 | dense_layer | 64 | 0.278 / 0.276 | 0.219 / 0.221 | -21.25% / -19.83% |
| a3-qwen38-tp4-decode-c2-p64512 | 2 / 4 | gdn | 48 | 0.294 / 0.290 | 0.229 / 0.229 | -21.95% / -21.03% |
| a3-qwen38-tp4-decode-c2-p64512 | 2 / 4 | gqa | 16 | 0.379 / 0.377 | 0.322 / 0.322 | -15.02% / -14.67% |
| a3-qwen38-tp4-decode-c2-p64512 | 2 / 4 | dense_layer | 64 | 0.315 / 0.292 | 0.253 / 0.229 | -19.86% / -21.39% |
| a3-qwen38-tp4-decode-c2-p64512 | 1 / 4 | gdn | 48 | 0.273 / 0.273 | 0.221 / 0.221 | -18.98% / -18.82% |
| a3-qwen38-tp4-decode-c2-p64512 | 1 / 4 | gqa | 16 | 0.331 / 0.330 | 0.255 / 0.255 | -22.87% / -22.74% |
| a3-qwen38-tp4-decode-c2-p64512 | 1 / 4 | dense_layer | 64 | 0.288 / 0.275 | 0.230 / 0.221 | -20.10% / -19.46% |
| a3-qwen38-tp4-decode-c2-p96512 | 2 / 4 | gdn | 48 | 0.295 / 0.291 | 0.229 / 0.229 | -22.16% / -21.22% |
| a3-qwen38-tp4-decode-c2-p96512 | 2 / 4 | gqa | 16 | 0.425 / 0.425 | 0.393 / 0.393 | -7.64% / -7.63% |
| a3-qwen38-tp4-decode-c2-p96512 | 2 / 4 | dense_layer | 64 | 0.327 / 0.293 | 0.270 / 0.229 | -17.45% / -21.76% |
| a3-qwen38-tp4-decode-c2-p96512 | 1 / 4 | gdn | 48 | 0.275 / 0.274 | 0.221 / 0.221 | -19.39% / -19.07% |
| a3-qwen38-tp4-decode-c2-p96512 | 1 / 4 | gqa | 16 | 0.381 / 0.361 | 0.288 / 0.288 | -24.50% / -20.27% |
| a3-qwen38-tp4-decode-c2-p96512 | 1 / 4 | dense_layer | 64 | 0.301 / 0.275 | 0.238 / 0.221 | -21.01% / -19.56% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | gdn | 48 | 0.367 / 0.366 | 0.272 / 0.272 | -25.91% / -25.68% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | gqa | 16 | 0.443 / 0.442 | 0.357 / 0.357 | -19.47% / -19.22% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | dense_layer | 64 | 0.386 / 0.369 | 0.293 / 0.272 | -24.06% / -26.18% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | gdn | 48 | 0.364 / 0.363 | 0.272 / 0.272 | -25.17% / -25.00% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | gqa | 16 | 0.427 / 0.426 | 0.357 / 0.357 | -16.37% / -16.17% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | dense_layer | 64 | 0.379 / 0.365 | 0.293 / 0.272 | -22.69% / -25.41% |
| a3-qwen38-tp4-decode-c6-p24512 | 2 / 4 | gdn | 48 | 0.301 / 0.292 | 0.229 / 0.229 | -23.73% / -21.46% |
| a3-qwen38-tp4-decode-c6-p24512 | 2 / 4 | gqa | 16 | 0.320 / 0.319 | 0.234 / 0.234 | -26.69% / -26.40% |
| a3-qwen38-tp4-decode-c6-p24512 | 2 / 4 | dense_layer | 64 | 0.305 / 0.294 | 0.231 / 0.229 | -24.51% / -21.93% |
| a3-qwen38-tp4-decode-c6-p24512 | 1 / 4 | gdn | 48 | 0.276 / 0.275 | 0.221 / 0.221 | -19.78% / -19.33% |
| a3-qwen38-tp4-decode-c6-p24512 | 1 / 4 | gqa | 16 | 0.283 / 0.283 | 0.211 / 0.211 | -25.54% / -25.53% |
| a3-qwen38-tp4-decode-c6-p24512 | 1 / 4 | dense_layer | 64 | 0.278 / 0.276 | 0.219 / 0.221 | -21.25% / -19.89% |
| a3-qwen38-tp4-decode-c6-p24512 | 4 / 4 | gdn | 48 | 0.344 / 0.334 | 0.257 / 0.257 | -25.40% / -23.08% |
| a3-qwen38-tp4-decode-c6-p24512 | 4 / 4 | gqa | 16 | 0.372 / 0.371 | 0.295 / 0.295 | -20.69% / -20.51% |
| a3-qwen38-tp4-decode-c6-p24512 | 4 / 4 | dense_layer | 64 | 0.351 / 0.335 | 0.266 / 0.257 | -24.15% / -23.50% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | gdn | 48 | 0.367 / 0.366 | 0.272 / 0.272 | -25.95% / -25.76% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | gqa | 16 | 0.598 / 0.597 | 0.608 / 0.608 | +1.75% / +1.87% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | dense_layer | 64 | 0.425 / 0.369 | 0.356 / 0.272 | -16.21% / -26.20% |
| a3-qwen38-tp4-decode-c6-p64512 | 4 / 4 | gdn | 48 | 0.336 / 0.333 | 0.257 / 0.257 | -23.71% / -22.93% |
| a3-qwen38-tp4-decode-c6-p64512 | 4 / 4 | gqa | 16 | 0.485 / 0.485 | 0.470 / 0.470 | -3.26% / -3.26% |
| a3-qwen38-tp4-decode-c6-p64512 | 4 / 4 | dense_layer | 64 | 0.374 / 0.335 | 0.310 / 0.257 | -17.07% / -23.31% |
| a3-qwen38-tp4-decode-c6-p64512 | 3 / 4 | gdn | 48 | 0.323 / 0.304 | 0.238 / 0.238 | -26.47% / -21.68% |
| a3-qwen38-tp4-decode-c6-p64512 | 3 / 4 | gqa | 16 | 0.437 / 0.438 | 0.390 / 0.390 | -10.78% / -10.97% |
| a3-qwen38-tp4-decode-c6-p64512 | 3 / 4 | dense_layer | 64 | 0.352 / 0.304 | 0.276 / 0.238 | -21.59% / -21.89% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | gdn | 48 | 0.364 / 0.363 | 0.272 / 0.272 | -25.19% / -25.15% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | gqa | 16 | 0.563 / 0.561 | 0.608 / 0.608 | +8.05% / +8.36% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | dense_layer | 64 | 0.413 / 0.366 | 0.356 / 0.272 | -13.88% / -25.64% |
| a3-qwen38-tp4-decode-c6-p64512 | 2 / 4 | gdn | 48 | 0.299 / 0.289 | 0.229 / 0.229 | -23.29% / -20.66% |
| a3-qwen38-tp4-decode-c6-p64512 | 2 / 4 | gqa | 16 | 0.380 / 0.379 | 0.322 / 0.322 | -15.34% / -14.97% |
| a3-qwen38-tp4-decode-c6-p64512 | 2 / 4 | dense_layer | 64 | 0.319 / 0.290 | 0.253 / 0.229 | -20.92% / -21.06% |
| a3-qwen38-tp4-decode-c6-p64512 | 1 / 4 | gdn | 48 | 0.280 / 0.273 | 0.221 / 0.221 | -21.00% / -18.87% |
| a3-qwen38-tp4-decode-c6-p64512 | 1 / 4 | gqa | 16 | 0.330 / 0.331 | 0.255 / 0.255 | -22.61% / -22.81% |
| a3-qwen38-tp4-decode-c6-p64512 | 1 / 4 | dense_layer | 64 | 0.293 / 0.276 | 0.230 / 0.221 | -21.45% / -19.73% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | gdn | 48 | 0.368 / 0.366 | 0.272 / 0.272 | -26.07% / -25.68% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | gqa | 16 | 0.741 / 0.727 | 0.820 / 0.820 | +10.64% / +12.79% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | dense_layer | 64 | 0.461 / 0.367 | 0.409 / 0.272 | -11.33% / -25.97% |
| a3-qwen38-tp4-decode-c6-p96512 | 1 / 4 | gdn | 48 | 0.280 / 0.274 | 0.221 / 0.221 | -20.82% / -19.08% |
| a3-qwen38-tp4-decode-c6-p96512 | 1 / 4 | gqa | 16 | 0.360 / 0.360 | 0.288 / 0.288 | -20.06% / -20.13% |
| a3-qwen38-tp4-decode-c6-p96512 | 1 / 4 | dense_layer | 64 | 0.300 / 0.276 | 0.238 / 0.221 | -20.59% / -19.64% |
| a3-qwen38-tp4-decode-c6-p96512 | 3 / 4 | gdn | 48 | 0.307 / 0.305 | 0.238 / 0.238 | -22.52% / -21.91% |
| a3-qwen38-tp4-decode-c6-p96512 | 3 / 4 | gqa | 16 | 0.508 / 0.503 | 0.498 / 0.498 | -2.01% / -0.90% |
| a3-qwen38-tp4-decode-c6-p96512 | 3 / 4 | dense_layer | 64 | 0.357 / 0.307 | 0.303 / 0.238 | -15.22% / -22.49% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | gdn | 48 | 0.365 / 0.364 | 0.272 / 0.272 | -25.42% / -25.30% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | gqa | 16 | 0.675 / 0.673 | 0.820 / 0.820 | +21.52% / +21.73% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | dense_layer | 64 | 0.442 / 0.366 | 0.409 / 0.272 | -7.51% / -25.61% |
| a3-qwen38-tp4-decode-c6-p96512 | 2 / 4 | gdn | 48 | 0.294 / 0.291 | 0.229 / 0.229 | -22.04% / -21.30% |
| a3-qwen38-tp4-decode-c6-p96512 | 2 / 4 | gqa | 16 | 0.426 / 0.426 | 0.393 / 0.393 | -7.83% / -7.72% |
| a3-qwen38-tp4-decode-c6-p96512 | 2 / 4 | dense_layer | 64 | 0.327 / 0.293 | 0.270 / 0.229 | -17.41% / -21.70% |
| a3-qwen38-tp4-decode-c6-p96512 | 4 / 4 | gdn | 48 | 0.336 / 0.334 | 0.257 / 0.257 | -23.73% / -23.20% |
| a3-qwen38-tp4-decode-c6-p96512 | 4 / 4 | gqa | 16 | 0.584 / 0.585 | 0.605 / 0.605 | +3.64% / +3.53% |
| a3-qwen38-tp4-decode-c6-p96512 | 4 / 4 | dense_layer | 64 | 0.398 / 0.337 | 0.344 / 0.257 | -13.69% / -23.79% |
| a5-qwen36-tp2-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.198 / 0.193 | 0.135 / 0.135 | -31.79% / -30.22% |
| a5-qwen36-tp2-decode-c1-p126000 | 1 / 4 | gqa | 16 | 1.112 / 1.111 | 1.077 / 1.077 | -3.11% / -3.08% |
| a5-qwen36-tp2-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.426 / 0.197 | 0.371 / 0.135 | -13.09% / -31.40% |
| a5-qwen36-tp2-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.404 / 0.404 | 0.244 / 0.244 | -39.63% / -39.61% |
| a5-qwen36-tp2-decode-c12-p126000 | 12 / 4 | gqa | 16 | 1.254 / 1.253 | 1.087 / 1.087 | -13.29% / -13.28% |
| a5-qwen36-tp2-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 0.617 / 0.406 | 0.455 / 0.244 | -26.25% / -39.84% |
| a5-qwen36-tp2-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.466 / 0.466 | 0.288 / 0.288 | -38.27% / -38.22% |
| a5-qwen36-tp2-decode-c16-p126000 | 16 / 4 | gqa | 16 | 1.290 / 1.290 | 1.151 / 1.151 | -10.78% / -10.80% |
| a5-qwen36-tp2-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 0.672 / 0.467 | 0.503 / 0.288 | -25.07% / -38.38% |
| a5-qwen36-tp2-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.221 / 0.217 | 0.130 / 0.130 | -41.04% / -40.11% |
| a5-qwen36-tp2-decode-c2-p126000 | 2 / 4 | gqa | 16 | 1.138 / 1.138 | 1.065 / 1.065 | -6.45% / -6.44% |
| a5-qwen36-tp2-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.450 / 0.221 | 0.364 / 0.130 | -19.17% / -41.11% |
| a5-qwen36-tp2-decode-c24-p126000 | 24 / 4 | gdn | 48 | 0.556 / 0.559 | 0.488 / 0.488 | -12.30% / -12.62% |
| a5-qwen36-tp2-decode-c24-p126000 | 24 / 4 | gqa | 16 | 2.320 / 2.320 | 2.304 / 2.304 | -0.70% / -0.69% |
| a5-qwen36-tp2-decode-c24-p126000 | 24 / 4 | dense_layer | 64 | 0.997 / 0.560 | 0.942 / 0.488 | -5.55% / -12.81% |
| a5-qwen36-tp2-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.261 / 0.258 | 0.172 / 0.172 | -34.20% / -33.56% |
| a5-qwen36-tp2-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.195 / 1.195 | 1.087 / 1.087 | -9.05% / -9.08% |
| a5-qwen36-tp2-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.494 / 0.261 | 0.400 / 0.172 | -19.00% / -34.27% |
| a5-qwen36-tp2-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.298 / 0.297 | 0.178 / 0.178 | -40.36% / -40.17% |
| a5-qwen36-tp2-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.287 / 1.288 | 1.074 / 1.074 | -16.60% / -16.62% |
| a5-qwen36-tp2-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.546 / 0.299 | 0.402 / 0.178 | -26.35% / -40.51% |
| a5-qwen36-tp2-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.336 / 0.336 | 0.196 / 0.196 | -41.60% / -41.57% |
| a5-qwen36-tp2-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.214 / 1.213 | 1.078 / 1.078 | -11.18% / -11.17% |
| a5-qwen36-tp2-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.555 / 0.337 | 0.417 / 0.196 | -24.98% / -41.73% |
| a5-qwen38-tp2-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.219 / 0.218 | 0.145 / 0.145 | -33.68% / -33.27% |
| a5-qwen38-tp2-decode-c1-p126000 | 1 / 4 | gqa | 16 | 1.117 / 1.117 | 1.079 / 1.079 | -3.39% / -3.41% |
| a5-qwen38-tp2-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.444 / 0.218 | 0.379 / 0.145 | -14.62% / -33.43% |
| a5-qwen38-tp2-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.430 / 0.432 | 0.257 / 0.257 | -40.11% / -40.48% |
| a5-qwen38-tp2-decode-c12-p126000 | 12 / 4 | gqa | 16 | 1.257 / 1.257 | 1.088 / 1.088 | -13.44% / -13.43% |
| a5-qwen38-tp2-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 0.637 / 0.434 | 0.465 / 0.257 | -26.95% / -40.64% |
| a5-qwen38-tp2-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.488 / 0.490 | 0.302 / 0.302 | -38.05% / -38.39% |
| a5-qwen38-tp2-decode-c16-p126000 | 16 / 4 | gqa | 16 | 1.318 / 1.317 | 1.152 / 1.152 | -12.61% / -12.57% |
| a5-qwen38-tp2-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 0.695 / 0.492 | 0.514 / 0.302 | -25.99% / -38.64% |
| a5-qwen38-tp2-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.243 / 0.242 | 0.141 / 0.141 | -42.17% / -41.88% |
| a5-qwen38-tp2-decode-c2-p126000 | 2 / 4 | gqa | 16 | 1.146 / 1.146 | 1.066 / 1.066 | -6.99% / -6.97% |
| a5-qwen38-tp2-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.469 / 0.242 | 0.372 / 0.141 | -20.67% / -42.03% |
| a5-qwen38-tp2-decode-c24-p126000 | 24 / 4 | gdn | 48 | 0.571 / 0.575 | 0.505 / 0.505 | -11.67% / -12.21% |
| a5-qwen38-tp2-decode-c24-p126000 | 24 / 4 | gqa | 16 | 2.312 / 2.312 | 2.304 / 2.304 | -0.32% / -0.34% |
| a5-qwen38-tp2-decode-c24-p126000 | 24 / 4 | dense_layer | 64 | 1.006 / 0.576 | 0.955 / 0.505 | -5.15% / -12.45% |
| a5-qwen38-tp2-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.283 / 0.282 | 0.183 / 0.183 | -35.43% / -35.33% |
| a5-qwen38-tp2-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.193 / 1.192 | 1.088 / 1.088 | -8.74% / -8.73% |
| a5-qwen38-tp2-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.510 / 0.283 | 0.409 / 0.183 | -19.84% / -35.50% |
| a5-qwen38-tp2-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.321 / 0.321 | 0.190 / 0.190 | -40.94% / -40.90% |
| a5-qwen38-tp2-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.289 / 1.289 | 1.075 / 1.075 | -16.61% / -16.59% |
| a5-qwen38-tp2-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.563 / 0.322 | 0.411 / 0.190 | -27.02% / -41.06% |
| a5-qwen38-tp2-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.359 / 0.361 | 0.208 / 0.208 | -41.94% / -42.25% |
| a5-qwen38-tp2-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.259 / 1.259 | 1.079 / 1.079 | -14.29% / -14.28% |
| a5-qwen38-tp2-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.584 / 0.362 | 0.426 / 0.208 | -27.03% / -42.48% |
| a5-qwen36-tp4-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.166 / 0.160 | 0.092 / 0.092 | -44.57% / -42.49% |
| a5-qwen36-tp4-decode-c1-p126000 | 1 / 4 | gqa | 16 | 1.099 / 1.099 | 1.042 / 1.042 | -5.24% / -5.25% |
| a5-qwen36-tp4-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.399 / 0.164 | 0.329 / 0.092 | -17.48% / -43.91% |
| a5-qwen36-tp4-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.197 / 0.191 | 0.105 / 0.105 | -46.78% / -45.34% |
| a5-qwen36-tp4-decode-c2-p126000 | 2 / 4 | gqa | 16 | 1.128 / 1.128 | 1.051 / 1.051 | -6.83% / -6.83% |
| a5-qwen36-tp4-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.429 / 0.195 | 0.341 / 0.105 | -20.55% / -46.44% |
| a5-qwen36-tp4-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.217 / 0.211 | 0.143 / 0.143 | -33.97% / -32.02% |
| a5-qwen36-tp4-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.155 / 1.155 | 1.081 / 1.081 | -6.41% / -6.39% |
| a5-qwen36-tp4-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.452 / 0.215 | 0.378 / 0.143 | -16.35% / -33.24% |
| a5-qwen36-tp4-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.236 / 0.232 | 0.132 / 0.132 | -43.79% / -42.82% |
| a5-qwen36-tp4-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.203 / 1.203 | 1.057 / 1.057 | -12.14% / -12.12% |
| a5-qwen36-tp4-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.477 / 0.235 | 0.364 / 0.132 | -23.85% / -43.54% |
| a5-qwen36-tp4-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.255 / 0.250 | 0.176 / 0.176 | -30.92% / -29.50% |
| a5-qwen36-tp4-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.211 / 1.211 | 1.092 / 1.092 | -9.81% / -9.83% |
| a5-qwen36-tp4-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.494 / 0.253 | 0.405 / 0.176 | -17.98% / -30.50% |
| a5-qwen38-tp4-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.172 / 0.168 | 0.096 / 0.096 | -43.86% / -42.67% |
| a5-qwen38-tp4-decode-c1-p126000 | 1 / 4 | gqa | 16 | 1.095 / 1.095 | 1.043 / 1.043 | -4.75% / -4.77% |
| a5-qwen38-tp4-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.402 / 0.173 | 0.333 / 0.096 | -17.27% / -44.27% |
| a5-qwen38-tp4-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.210 / 0.203 | 0.109 / 0.109 | -47.86% / -46.29% |
| a5-qwen38-tp4-decode-c2-p126000 | 2 / 4 | gqa | 16 | 1.127 / 1.127 | 1.052 / 1.052 | -6.69% / -6.69% |
| a5-qwen38-tp4-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.439 / 0.208 | 0.345 / 0.109 | -21.43% / -47.40% |
| a5-qwen38-tp4-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.226 / 0.223 | 0.148 / 0.148 | -34.25% / -33.51% |
| a5-qwen38-tp4-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.147 / 1.148 | 1.082 / 1.082 | -5.71% / -5.72% |
| a5-qwen38-tp4-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.456 / 0.225 | 0.382 / 0.148 | -16.30% / -34.08% |
| a5-qwen38-tp4-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.245 / 0.244 | 0.138 / 0.138 | -43.82% / -43.61% |
| a5-qwen38-tp4-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.198 / 1.198 | 1.057 / 1.057 | -11.73% / -11.73% |
| a5-qwen38-tp4-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.483 / 0.245 | 0.368 / 0.138 | -23.93% / -43.84% |
| a5-qwen38-tp4-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.261 / 0.260 | 0.182 / 0.182 | -30.41% / -30.14% |
| a5-qwen38-tp4-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.206 / 1.206 | 1.092 / 1.092 | -9.43% / -9.43% |
| a5-qwen38-tp4-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.497 / 0.261 | 0.409 / 0.182 | -17.69% / -30.44% |
| a3-v41-tp4dp4-decode-c4-p8512 | 1 / 8 | mla | 40 | 0.888 / 0.823 | 0.805 / 0.789 | -9.41% / -4.18% |
| a3-v41-tp4dp4-decode-c4-p8512 | 1 / 8 | moe_layer | 40 | 0.888 / 0.823 | 0.805 / 0.789 | -9.41% / -4.18% |
| a3-v41-tp4dp4-decode-c4-p8512 | 2 / 8 | mla | 40 | 1.201 / 1.130 | 1.258 / 1.240 | +4.78% / +9.74% |
| a3-v41-tp4dp4-decode-c4-p8512 | 2 / 8 | moe_layer | 40 | 1.201 / 1.130 | 1.258 / 1.240 | +4.78% / +9.74% |

Layer-group statistics summarize complete layer spans, not isolated attention or FFN kernel time. Group P50 is across layer means; steady-layer P50 remains the median of per-layer call P50 values in JSON. Full layer membership, extrema, stream details and alignment assumptions remain in the SHA256-pinned evidence.

Summary: {"compared": 280, "passed": 150, "requested_sources": 280, "sources": 280, "status_counts": {"compared": 280}}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
