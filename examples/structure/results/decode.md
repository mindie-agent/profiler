# Current profiling validation

One canonical case registry and one recorded Sim package. Selected costs are freshly replayed; unchanged cases retain verified evidence from this same Sim package. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.

| Case | Phase | Calls | Real mean / P50 / P90 ms | Sim ms | Error | Status |
|---|---|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c4-livepre | decode | 46 | 29.762 / 29.664 / 30.046 | 30.314 | +1.86% | PASS |
| glm53flash-a3-tp16-c16-livepre | decode | 37 | 41.069 / 40.940 / 41.282 | 44.390 | +8.09% | PASS |
| glm53flash-a3-tp16-c2 | decode | 46 | 34.118 / 33.910 / 35.073 | 31.755 | -6.93% | PASS |
| glm53flash-a3-tp16-c4 | decode | 46 | 39.841 / 39.798 / 40.057 | 36.959 | -7.24% | PASS |
| glm53flash-a5-tp8-c3 | decode | 53 | 21.068 / 21.057 / 21.170 | 18.891 | -10.33% | PASS |
| glm53flash-a5-tp8-c96 | decode | 27 | 57.590 / 57.573 / 57.734 | 61.965 | +7.60% | PASS |
| glm53flash-a5-tp8-c1 | decode | 65 | 15.683 / 15.670 / 15.738 | 13.868 | -11.58% | PASS |
| a5_kimi_k3_p32768_c1 | decode | 63 | 32.555 / 32.533 / 32.674 | 28.561 | -12.27% | PASS |
| v4flash-a3-tp8-c4 | decode | 104 | 32.486 / 32.416 / 32.734 | 29.272 | -9.89% | PASS |
| v4flash-a3-tp8-c8 | decode | 104 | 37.763 / 37.868 / 38.082 | 34.707 | -8.09% | PASS |
| a3_glm53_dc4k_b1 | decode | 74 | 38.955 / 38.943 / 39.036 | 38.046 | -2.33% | PASS |
| a3_glm53_dc4k_b2 | decode | 70 | 40.970 / 40.935 / 41.046 | 39.767 | -2.94% | PASS |
| a3_glm53_dc4k_b4 | decode | 67 | 43.438 / 43.437 / 43.598 | 38.631 | -11.07% | PASS |
| a3_glm53_dc4k_b8 | decode | 61 | 47.113 / 47.149 / 47.402 | 44.125 | -6.34% | PASS |
| a3_glm53_dc16k_b1 | decode | 74 | 39.112 / 39.105 / 39.196 | 38.334 | -1.99% | PASS |
| qwen35-397b-a3-tp16-c48 | decode | 23 | 76.089 / 76.132 / 76.632 | 66.783 | -12.23% | PASS |
| qwen35-397b-a3-tp16-c136 | decode | 18 | 119.054 / 119.131 / 119.486 | 104.482 | -12.24% | PASS |
| qwen35-35b-a5-tp4-c64-graph | decode | 79 | 21.957 / 22.001 / 22.068 | 19.975 | -9.03% | PASS |
| qwen35-35b-a5-tp4-c128-graph | decode | 76 | 28.585 / 28.571 / 28.704 | 26.049 | -8.87% | PASS |
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
| a5_glm53flash_tp8_c4_p8k | decode | 11 | 21.418 / 21.408 / 21.432 | 18.161 | -15.21% | FAIL |
| a5_glm53flash_tp8_c64_p4k | decode | 31 | 46.528 / 46.499 / 46.645 | 45.964 | -1.21% | PASS |
| a5_glm53flash_tp8_c8_p4k | decode | 30 | 28.833 / 28.828 / 28.885 | 25.200 | -12.60% | PASS |
| a3_glm53flash_tp16_aclgraph_c16 | decode | 50 | 53.893 / 53.871 / 54.021 | 49.051 | -8.99% | PASS |
| a3_glm53flash_tp16_aclgraph_c32 | decode | 49 | 69.361 / 69.418 / 69.528 | 64.340 | -7.24% | PASS |
| a3_glm53flash_tp16_aclgraph_c64 | decode | 47 | 97.375 / 97.487 / 97.895 | 95.905 | -1.51% | PASS |
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
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | decode | 21 | 61.811 / 61.629 / 62.042 | 63.541 | +2.80% | PASS |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | decode | 29 | 48.582 / 48.412 / 48.662 | 51.673 | +6.36% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k | decode | 73 | 27.286 / 27.266 / 27.290 | 25.540 | -6.40% | PASS |
| qwen35-35b-a3-tp4-c144 | decode | 25 | 61.750 / 61.784 / 62.102 | 53.574 | -13.24% | PASS |
| qwen35-35b-a3-tp4-c320 | decode | 21 | 99.692 / 99.679 / 100.090 | 94.011 | -5.70% | PASS |
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
| a5_glm53flash_heldout_c12_p4k | decode | 20 | 18.133 / 18.108 / 18.148 | 15.201 | -16.17% | FAIL |
| a5_glm53flash_heldout_c24_p12k | decode | 21 | 38.995 / 39.210 / 39.263 | 31.147 | -20.12% | FAIL |
| a5_glm53flash_heldout_c48_p4k | decode | 26 | 43.228 / 43.355 / 43.400 | 41.035 | -5.07% | PASS |
| a3_glm53flash_static_on_c10_p131201 | decode | 68 | 22.603 / 22.348 / 23.552 | 23.072 | +2.07% | FAIL |
| a3-qwen35-tp4-longctx-p-126976-c1 | decode | 65 | 16.054 / 16.058 / 16.121 | 31.468 | +96.01% | FAIL |
| a3-qwen35-tp4-longctx-p-126976-c4 | decode | 34 | 20.465 / 20.804 / 20.975 | 33.008 | +61.29% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c1 | decode | 64 | 15.530 / 15.511 / 15.646 | 19.552 | +25.90% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c2 | decode | 55 | 16.750 / 16.724 / 16.909 | 20.194 | +20.56% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c4 | decode | 50 | 18.893 / 18.984 / 19.070 | 21.093 | +11.64% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c8 | decode | 32 | 21.417 / 21.608 / 22.212 | 23.126 | +7.98% | FAIL |
| a3-qwen36-tp4-longctx-p-126976-c1 | decode | 10 | 18.924 / 18.932 / 19.020 | 52.773 | +178.88% | FAIL |
| a3-qwen36-tp4-longctx-p-126976-c4 | decode | 47 | 27.951 / 27.941 / 28.060 | 54.663 | +95.57% | FAIL |
| a3-qwen36-tp4-longctx-p-65536-c1 | decode | 15 | 18.048 / 17.939 / 18.590 | 33.708 | +86.77% | FAIL |
| a3-qwen36-tp4-longctx-p-65536-c4 | decode | 49 | 24.880 / 24.783 / 25.010 | 35.598 | +43.08% | FAIL |
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
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | decode | 242 | 3.397 / 3.323 / 3.643 | 2.734 | -19.50% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | decode | 228 | 6.922 / 6.899 / 7.128 | 4.966 | -28.25% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | decode | 198 | 8.287 / 8.231 / 8.548 | 5.468 | -34.02% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | decode | 240 | 3.593 / 3.568 / 3.831 | 2.861 | -20.40% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | decode | 153 | 10.962 / 10.873 / 11.210 | 7.322 | -33.21% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | decode | 124 | 13.725 / 13.665 / 13.952 | 9.150 | -33.33% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | decode | 243 | 4.403 / 4.366 / 4.615 | 3.126 | -29.00% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | decode | 91 | 19.074 / 19.036 / 19.275 | 12.870 | -32.52% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | decode | 233 | 4.795 / 4.727 / 5.001 | 3.377 | -29.58% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | decode | 74 | 23.694 / 23.656 / 23.841 | 15.822 | -33.23% | FAIL |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | decode | 236 | 5.467 / 5.396 / 5.675 | 3.633 | -33.56% | FAIL |
| a3-kimi4-tp8-longctx-decode-c12-p16k | decode | 189 | 4.435 / 4.402 / 4.659 | 3.704 | -16.49% | FAIL |
| a3-kimi4-tp8-longctx-decode-c12-p32k | decode | 189 | 4.621 / 4.558 / 4.808 | 3.892 | -15.77% | FAIL |
| a3-kimi4-tp8-longctx-decode-c12-p4k | decode | 191 | 4.229 / 4.195 / 4.479 | 3.575 | -15.48% | FAIL |
| a3-kimi4-tp8-longctx-decode-c12-p8k | decode | 190 | 4.249 / 4.217 / 4.437 | 3.609 | -15.05% | FAIL |
| a3-kimi4-tp8-longctx-decode-c24-p16k | decode | 190 | 6.096 / 6.046 / 6.322 | 4.796 | -21.33% | FAIL |
| a3-kimi4-tp8-longctx-decode-c24-p32k | decode | 193 | 6.437 / 6.353 / 6.658 | 5.174 | -19.62% | FAIL |
| a3-kimi4-tp8-longctx-decode-c24-p4k | decode | 200 | 5.641 / 5.582 / 5.874 | 4.538 | -19.55% | FAIL |
| a3-kimi4-tp8-longctx-decode-c24-p8k | decode | 195 | 5.829 / 5.787 / 6.088 | 4.607 | -20.96% | FAIL |
| a3-kimi4-tp8-longctx-decode-c2-p4k | decode | 200 | 3.285 / 3.243 / 3.520 | 2.629 | -19.98% | FAIL |
| a3-kimi4-tp8-longctx-decode-c48-p4k | decode | 159 | 8.472 / 8.430 / 8.705 | 7.303 | -13.80% | PASS |
| a3-kimi4-tp8-longctx-decode-c6-p4k | decode | 186 | 3.701 / 3.632 / 3.935 | 2.681 | -27.57% | FAIL |
| a3-kimi4-tp8-longctx-decode-c8-p4k | decode | 191 | 3.839 / 3.765 / 4.168 | 2.705 | -29.54% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | decode | 228 | 4.093 / 3.992 / 4.443 | 3.108 | -24.05% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | decode | 207 | 6.865 / 6.792 / 7.109 | 4.507 | -34.34% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | decode | 206 | 7.840 / 7.747 / 8.108 | 5.005 | -36.16% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | decode | 232 | 4.362 / 4.303 / 4.648 | 3.233 | -25.87% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | decode | 167 | 10.062 / 10.014 / 10.358 | 6.845 | -31.98% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | decode | 138 | 12.295 / 12.243 / 12.550 | 7.856 | -36.11% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | decode | 226 | 5.008 / 4.905 / 5.299 | 3.484 | -30.42% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | decode | 103 | 16.734 / 16.715 / 16.992 | 10.726 | -35.90% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | decode | 222 | 5.264 / 5.192 / 5.571 | 3.744 | -28.87% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | decode | 83 | 20.942 / 20.922 / 21.125 | 13.219 | -36.88% | FAIL |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | decode | 212 | 5.865 / 5.802 / 6.140 | 3.999 | -31.82% | FAIL |
| a3-kimi4-tp16-128k-decode-c12-p16k | decode | 180 | 4.430 / 4.375 / 4.726 | 3.245 | -26.76% | FAIL |
| a3-kimi4-tp16-128k-decode-c12-p32k | decode | 178 | 4.659 / 4.586 / 4.886 | 3.433 | -26.30% | FAIL |
| a3-kimi4-tp16-128k-decode-c12-p4k | decode | 162 | 4.439 / 4.155 / 4.610 | 3.116 | -29.81% | FAIL |
| a3-kimi4-tp16-128k-decode-c12-p8k | decode | 173 | 4.379 / 4.203 / 4.614 | 3.150 | -28.06% | FAIL |
| a3-kimi4-tp16-128k-decode-c24-p16k | decode | 175 | 5.260 / 5.124 / 5.362 | 4.319 | -17.88% | FAIL |
| a3-kimi4-tp16-128k-decode-c24-p32k | decode | 186 | 5.661 / 5.606 / 5.932 | 4.697 | -17.04% | FAIL |
| a3-kimi4-tp16-128k-decode-c24-p4k | decode | 177 | 8.082 / 5.032 / 12.608 | 4.061 | -49.75% | FAIL |
| a3-kimi4-tp16-128k-decode-c24-p8k | decode | 179 | 4.939 / 4.913 / 5.134 | 4.130 | -16.37% | FAIL |
| a3-kimi4-tp16-128k-decode-c2-p4k | decode | 186 | 4.055 / 3.989 / 4.321 | 3.001 | -25.99% | FAIL |
| a3-kimi4-tp16-128k-decode-c48-p4k | decode | 172 | 6.201 / 6.157 / 6.393 | 5.159 | -16.80% | FAIL |
| a3-kimi4-tp16-128k-decode-c6-p4k | decode | 181 | 4.110 / 4.033 / 4.408 | 3.048 | -25.83% | FAIL |
| a3-kimi4-tp16-128k-decode-c8-p4k | decode | 183 | 4.188 / 4.058 / 4.447 | 3.071 | -26.67% | FAIL |
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
| a3-v41-tp4dp4-128k-c48 | decode | 61 | 74.011 / 73.921 / 74.097 | 63.836 | -13.75% | PASS |
| a3-v41-tp4dp4-128k-c64 | decode | 58 | 77.498 / 77.469 / 77.623 | 69.116 | -10.82% | PASS |
| a3-v41-tp4dp4-128k-c8 | decode | 82 | 53.618 / 53.549 / 53.745 | 51.898 | -3.21% | PASS |
| a3-qwen35-tp4-decode-c1-p126000 | decode | 169 | 17.505 / 17.528 / 17.656 | 32.594 | +86.20% | FAIL |
| a3-qwen35-tp4-decode-c12-p126000 | decode | 97 | 36.173 / 36.158 / 36.304 | 42.174 | +16.59% | FAIL |
| a3-qwen35-tp4-decode-c16-p126000 | decode | 87 | 40.651 / 40.639 / 40.884 | 43.093 | +6.01% | PASS |
| a3-qwen35-tp4-decode-c2-p126000 | decode | 156 | 19.585 / 19.593 / 19.734 | 33.741 | +72.28% | FAIL |
| a3-qwen35-tp4-decode-c24-p126000 | decode | 57 | 63.494 / 63.631 / 63.779 | 69.324 | +9.18% | PASS |
| a3-qwen35-tp4-decode-c32-p126000 | decode | 55 | 65.343 / 65.297 / 65.724 | 71.442 | +9.33% | PASS |
| a3-qwen35-tp4-decode-c4-p126000 | decode | 138 | 22.871 / 22.871 / 23.010 | 36.079 | +57.75% | FAIL |
| a3-qwen35-tp4-decode-c48-p126000 | decode | 42 | 86.442 / 86.447 / 86.585 | — | — | failed |
| a3-qwen35-tp4-decode-c6-p126000 | decode | 121 | 27.566 / 27.525 / 27.659 | 38.910 | +41.15% | FAIL |
| a3-qwen35-tp4-decode-c64-p126000 | decode | 34 | 107.680 / 107.516 / 108.525 | — | — | failed |
| a3-qwen35-tp4-decode-c8-p126000 | decode | 111 | 31.009 / 30.990 / 31.159 | 41.215 | +32.91% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | decode | 47 | 27.914 / 27.905 / 28.026 | 22.491 | -19.43% | FAIL |
| a3-qwen35-tp4-decode-c12-p64512 | decode | 45 | 30.548 / 30.507 / 30.812 | 30.248 | -0.98% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | decode | 43 | 27.435 / 27.433 / 27.570 | 19.388 | -29.33% | FAIL |
| a3-qwen35-tp4-decode-c12-p96512 | decode | 58 | 33.166 / 33.160 / 33.280 | 36.454 | +9.91% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | decode | 66 | 35.550 / 35.558 / 35.723 | 29.960 | -15.72% | FAIL |
| a3-qwen35-tp4-decode-c24-p64512 | decode | 63 | 44.868 / 44.851 / 45.016 | 45.474 | +1.35% | PASS |
| a3-qwen35-tp4-decode-c24-p8512 | decode | 57 | 31.676 / 31.677 / 31.775 | 23.754 | -25.01% | FAIL |
| a3-qwen35-tp4-decode-c24-p96512 | decode | 52 | 54.896 / 55.004 / 55.143 | 57.886 | +5.45% | PASS |
| a3-qwen35-tp4-decode-c2-p24512 | decode | 16 | 16.697 / 16.657 / 16.860 | 12.912 | -22.67% | FAIL |
| a3-qwen35-tp4-decode-c2-p64512 | decode | 7 | 17.136 / 17.138 / 17.270 | 20.669 | +20.62% | FAIL |
| a3-qwen35-tp4-decode-c2-p8512 | decode | 7 | 16.319 / 16.333 / 16.372 | 9.809 | -39.89% | FAIL |
| a3-qwen35-tp4-decode-c2-p96512 | decode | 12 | 17.338 / 17.324 / 17.456 | 26.875 | +55.01% | FAIL |
| a3-qwen35-tp4-decode-c6-p24512 | decode | 23 | 23.225 / 23.181 / 23.327 | 19.228 | -17.21% | FAIL |
| a3-qwen35-tp4-decode-c6-p64512 | decode | 40 | 24.666 / 24.667 / 24.763 | 26.985 | +9.40% | FAIL |
| a3-qwen35-tp4-decode-c6-p8512 | decode | 21 | 22.846 / 22.849 / 22.926 | 16.124 | -29.42% | FAIL |
| a3-qwen35-tp4-decode-c6-p96512 | decode | 42 | 26.149 / 25.837 / 26.090 | 33.191 | +26.93% | FAIL |
| a3-qwen36-tp2-decode-c1-p126000 | decode | 118 | 27.505 / 27.460 / 27.662 | 57.708 | +109.81% | FAIL |
| a3-qwen36-tp2-decode-c12-p126000 | decode | 40 | 92.965 / 92.683 / 93.492 | — | — | failed |
| a3-qwen36-tp2-decode-c16-p126000 | decode | 39 | 96.424 / 96.221 / 97.153 | — | — | failed |
| a3-qwen36-tp2-decode-c2-p126000 | decode | 107 | 32.035 / 32.023 / 32.214 | 59.019 | +84.24% | FAIL |
| a3-qwen36-tp2-decode-c24-p126000 | decode | 29 | 132.699 / 132.704 / 132.775 | — | — | failed |
| a3-qwen36-tp2-decode-c4-p126000 | decode | 88 | 40.819 / 40.826 / 41.229 | 61.016 | +49.48% | FAIL |
| a3-qwen36-tp2-decode-c6-p126000 | decode | 74 | 50.103 / 50.017 / 50.304 | 63.051 | +25.84% | FAIL |
| a3-qwen36-tp2-decode-c8-p126000 | decode | 66 | 56.360 / 56.274 / 56.741 | 65.122 | +15.55% | FAIL |
| a3-qwen36-tp2-decode-c12-p24512 | decode | 63 | 45.843 / 45.864 / 46.024 | 45.940 | +0.21% | PASS |
| a3-qwen36-tp2-decode-c12-p64512 | decode | 46 | 63.620 / 63.439 / 64.028 | 70.761 | +11.22% | PASS |
| a3-qwen36-tp2-decode-c12-p8512 | decode | 68 | 39.923 / 39.905 / 40.004 | 36.010 | -9.80% | PASS |
| a3-qwen36-tp2-decode-c24-p24512 | decode | 49 | 60.836 / 60.802 / 60.974 | 66.534 | +9.37% | PASS |
| a3-qwen36-tp2-decode-c24-p64512 | decode | 34 | 87.080 / 87.073 / 87.154 | — | — | failed |
| a3-qwen36-tp2-decode-c24-p8512 | decode | 56 | 52.156 / 52.152 / 52.263 | 51.640 | -0.99% | PASS |
| a3-qwen36-tp2-decode-c2-p24512 | decode | 58 | 26.724 / 26.694 / 26.806 | 27.529 | +3.01% | PASS |
| a3-qwen36-tp2-decode-c2-p64512 | decode | 58 | 28.868 / 28.845 / 28.903 | 39.939 | +38.35% | FAIL |
| a3-qwen36-tp2-decode-c2-p8512 | decode | 45 | 25.809 / 25.747 / 25.801 | 22.564 | -12.57% | PASS |
| a3-qwen36-tp2-decode-c2-p96512 | decode | 62 | 30.222 / 30.218 / 30.266 | 49.869 | +65.01% | FAIL |
| a3-qwen36-tp2-decode-c6-p24512 | decode | 71 | 33.717 / 33.762 / 33.825 | 31.561 | -6.40% | PASS |
| a3-qwen36-tp2-decode-c6-p64512 | decode | 71 | 39.714 / 39.641 / 39.741 | 43.971 | +10.72% | PASS |
| a3-qwen36-tp2-decode-c6-p8512 | decode | 61 | 32.027 / 31.966 / 32.038 | 26.596 | -16.96% | FAIL |
| a3-qwen36-tp2-decode-c6-p96512 | decode | 64 | 44.510 / 44.533 / 44.618 | 53.901 | +21.10% | FAIL |
| a3-qwen36-tp4-decode-c1-p126000 | decode | 132 | 19.697 / 19.667 / 19.812 | 52.468 | +166.38% | FAIL |
| a3-qwen36-tp4-decode-c12-p126000 | decode | 83 | 44.267 / 44.229 / 44.445 | 58.923 | +33.11% | FAIL |
| a3-qwen36-tp4-decode-c16-p126000 | decode | 72 | 51.997 / 51.884 / 52.229 | 61.260 | +17.81% | FAIL |
| a3-qwen36-tp4-decode-c2-p126000 | decode | 128 | 21.879 / 21.733 / 21.892 | 52.914 | +141.84% | FAIL |
| a3-qwen36-tp4-decode-c24-p126000 | decode | 42 | 89.034 / 88.904 / 89.802 | — | — | failed |
| a3-qwen36-tp4-decode-c4-p126000 | decode | 121 | 34.324 / 26.842 / 63.003 | 54.358 | +58.37% | FAIL |
| a3-qwen36-tp4-decode-c6-p126000 | decode | 105 | 32.038 / 31.950 / 32.050 | 55.234 | +72.40% | FAIL |
| a3-qwen36-tp4-decode-c8-p126000 | decode | 97 | 36.585 / 36.585 / 36.725 | 56.621 | +54.76% | FAIL |
| a3-qwen38-tp2-decode-c1-p126000 | decode | 119 | 27.543 / 27.497 / 27.703 | 57.708 | +109.52% | FAIL |
| a3-qwen38-tp2-decode-c12-p126000 | decode | 40 | 93.228 / 93.357 / 93.478 | — | — | failed |
| a3-qwen38-tp2-decode-c16-p126000 | decode | 39 | 96.251 / 96.054 / 96.900 | — | — | failed |
| a3-qwen38-tp2-decode-c2-p126000 | decode | 107 | 32.136 / 32.139 / 32.349 | 59.019 | +83.66% | FAIL |
| a3-qwen38-tp2-decode-c4-p126000 | decode | 90 | 40.524 / 40.550 / 40.876 | 61.016 | +50.57% | FAIL |
| a3-qwen38-tp2-decode-c6-p126000 | decode | 74 | 50.273 / 50.197 / 50.502 | 63.051 | +25.42% | FAIL |
| a3-qwen38-tp2-decode-c8-p126000 | decode | 66 | 56.370 / 56.313 / 56.643 | 65.122 | +15.53% | FAIL |
| a3-qwen38-tp4-decode-c1-p126000 | decode | 135 | 19.886 / 19.681 / 19.804 | 52.468 | +163.84% | FAIL |
| a3-qwen38-tp4-decode-c12-p126000 | decode | 84 | 44.305 / 44.261 / 44.463 | 58.923 | +32.99% | FAIL |
| a3-qwen38-tp4-decode-c16-p126000 | decode | 73 | 51.793 / 51.612 / 52.084 | 61.260 | +18.28% | FAIL |
| a3-qwen38-tp4-decode-c2-p126000 | decode | 137 | 21.825 / 21.761 / 21.870 | 52.914 | +142.45% | FAIL |
| a3-qwen38-tp4-decode-c24-p126000 | decode | 43 | 88.988 / 88.982 / 89.108 | — | — | failed |
| a3-qwen38-tp4-decode-c32-p126000 | decode | 41 | 93.356 / 93.203 / 93.861 | — | — | failed |
| a3-qwen38-tp4-decode-c4-p126000 | decode | 124 | 26.807 / 26.771 / 26.837 | 54.358 | +102.78% | FAIL |
| a3-qwen38-tp4-decode-c6-p126000 | decode | 108 | 31.992 / 31.979 / 32.091 | 55.234 | +72.65% | FAIL |
| a3-qwen38-tp4-decode-c8-p126000 | decode | 98 | 36.460 / 36.463 / 36.611 | 56.621 | +55.29% | FAIL |
| a3-qwen38-tp4-decode-c12-p24512 | decode | 56 | 30.908 / 30.898 / 30.968 | 27.432 | -11.25% | FAIL |
| a3-qwen38-tp4-decode-c12-p64512 | decode | 68 | 35.845 / 35.986 / 36.161 | 39.843 | +11.15% | FAIL |
| a3-qwen38-tp4-decode-c12-p96512 | decode | 65 | 39.782 / 39.852 / 40.095 | 49.772 | +25.11% | FAIL |
| a3-qwen38-tp4-decode-c24-p24512 | decode | 65 | 43.632 / 43.656 / 43.714 | 42.590 | -2.39% | PASS |
| a3-qwen38-tp4-decode-c24-p64512 | decode | 49 | 60.117 / 60.324 / 60.463 | 67.411 | +12.13% | PASS |
| a3-qwen38-tp4-decode-c24-p96512 | decode | 40 | 75.162 / 75.093 / 75.331 | 87.270 | +16.11% | FAIL |
| a3-qwen38-tp4-decode-c2-p24512 | decode | 11 | 19.404 / 19.244 / 20.150 | 21.423 | +10.41% | FAIL |
| a3-qwen38-tp4-decode-c2-p64512 | decode | 20 | 20.210 / 20.021 / 20.180 | 33.834 | +67.41% | FAIL |
| a3-qwen38-tp4-decode-c2-p96512 | decode | 24 | 20.989 / 20.830 / 21.239 | 43.764 | +108.51% | FAIL |
| a3-qwen38-tp4-decode-c6-p24512 | decode | 38 | 24.761 / 24.752 / 24.829 | 23.743 | -4.11% | FAIL |
| a3-qwen38-tp4-decode-c6-p64512 | decode | 40 | 27.237 / 27.135 / 27.365 | 36.154 | +32.74% | FAIL |
| a3-qwen38-tp4-decode-c6-p96512 | decode | 42 | 29.560 / 29.308 / 29.565 | 46.083 | +55.90% | FAIL |
| a5-qwen36-tp2-decode-c1-p126000 | decode | 54 | 27.332 / 27.209 / 27.445 | 22.522 | -17.60% | FAIL |
| a5-qwen36-tp2-decode-c12-p126000 | decode | 38 | 39.512 / 39.500 / 39.595 | — | — | failed |
| a5-qwen36-tp2-decode-c16-p126000 | decode | 35 | 43.048 / 43.038 / 43.179 | — | — | failed |
| a5-qwen36-tp2-decode-c2-p126000 | decode | 52 | 28.841 / 28.804 / 28.991 | 22.665 | -21.41% | FAIL |
| a5-qwen36-tp2-decode-c24-p126000 | decode | 25 | 63.879 / 63.873 / 63.963 | — | — | failed |
| a5-qwen36-tp2-decode-c4-p126000 | decode | 48 | 31.689 / 31.648 / 31.862 | 23.317 | -26.42% | FAIL |
| a5-qwen36-tp2-decode-c6-p126000 | decode | 43 | 34.972 / 34.963 / 35.029 | 23.969 | -31.46% | FAIL |
| a5-qwen36-tp2-decode-c8-p126000 | decode | 41 | 35.597 / 35.582 / 35.641 | 24.348 | -31.60% | FAIL |
| a5-qwen38-tp2-decode-c1-p126000 | decode | 53 | 28.447 / 28.429 / 28.570 | 23.054 | -18.96% | FAIL |
| a5-qwen38-tp2-decode-c12-p126000 | decode | 37 | 40.788 / 40.789 / 40.880 | — | — | failed |
| a5-qwen38-tp2-decode-c16-p126000 | decode | 34 | 44.535 / 44.520 / 44.705 | — | — | failed |
| a5-qwen38-tp2-decode-c2-p126000 | decode | 51 | 30.056 / 30.048 / 30.111 | 23.197 | -22.82% | FAIL |
| a5-qwen38-tp2-decode-c24-p126000 | decode | 24 | 64.457 / 64.427 / 64.559 | — | — | failed |
| a5-qwen38-tp2-decode-c4-p126000 | decode | 47 | 32.711 / 32.699 / 32.777 | 23.874 | -27.02% | FAIL |
| a5-qwen38-tp2-decode-c6-p126000 | decode | 42 | 36.091 / 36.084 / 36.136 | 24.551 | -31.97% | FAIL |
| a5-qwen38-tp2-decode-c8-p126000 | decode | 40 | 37.428 / 37.420 / 37.480 | 24.954 | -33.33% | FAIL |
| a5-qwen36-tp4-decode-c1-p126000 | decode | 58 | 25.585 / 25.621 / 25.711 | 21.436 | -16.22% | FAIL |
| a5-qwen36-tp4-decode-c2-p126000 | decode | 54 | 27.536 / 27.580 / 27.663 | 21.534 | -21.80% | FAIL |
| a5-qwen36-tp4-decode-c4-p126000 | decode | 52 | 28.964 / 28.988 / 29.039 | 21.776 | -24.82% | FAIL |
| a5-qwen36-tp4-decode-c6-p126000 | decode | 49 | 30.604 / 30.612 / 30.773 | 22.301 | -27.13% | FAIL |
| a5-qwen36-tp4-decode-c8-p126000 | decode | 48 | 31.660 / 31.718 / 31.765 | 22.544 | -28.79% | FAIL |
| a5-qwen38-tp4-decode-c1-p126000 | decode | 56 | 25.808 / 25.757 / 26.012 | 21.675 | -16.02% | FAIL |
| a5-qwen38-tp4-decode-c2-p126000 | decode | 53 | 28.147 / 28.200 / 28.244 | 21.771 | -22.65% | FAIL |
| a5-qwen38-tp4-decode-c4-p126000 | decode | 52 | 29.240 / 29.178 / 29.387 | 22.024 | -24.68% | FAIL |
| a5-qwen38-tp4-decode-c6-p126000 | decode | 49 | 30.974 / 30.930 / 31.177 | 22.560 | -27.17% | FAIL |
| a5-qwen38-tp4-decode-c8-p126000 | decode | 47 | 31.871 / 31.845 / 32.020 | 22.812 | -28.42% | FAIL |
| a3-v41-tp4dp4-decode-c4-p8512 | decode | 28 | 35.585 / 36.156 / 36.274 | 32.194 | -9.53% | PASS |

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
| qwen35-35b-a5-tp4-c128-graph | 128 | 4 | 4096 | 76 | 28.585 / 28.571 / 28.704 | 26.049 | -8.87% | PASS |
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
| a5_glm53flash_tp8_c4_p8k | 4 | 4 | 8200 | 11 | 21.418 / 21.408 / 21.432 | 18.161 | -15.21% | FAIL |
| a5_glm53flash_tp8_c4_p8k | 1 | 4 | 8200 | 9 | 15.590 / 15.583 / 15.642 | — | — | unresolved |
| a5_glm53flash_tp8_c4_p8k | 2 | 4 | 8200 | 3 | 17.682 / 17.672 / 17.709 | — | — | unresolved |

a5_glm53flash_tp8_c4_p8k: scored 11 / 23 calls; all-population pass: False.
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
| a3_glm53flash_tp16_aclgraph_c32 | 32 | 6 | 4096 | 49 | 69.361 / 69.418 / 69.528 | 64.340 | -7.24% | PASS |
| a3_glm53flash_tp16_aclgraph_c32 | 12 | 6 | 4096 | 5 | 52.894 / 53.227 / 53.859 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c32 | 1 | 6 | 4096 | 3 | 33.667 / 33.176 / 34.874 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c32 | 24 | 6 | 4096 | 3 | 63.044 / 62.507 / 64.216 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c32 | 16 | 6 | 4096 | 2 | 54.274 / 54.274 / 54.610 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c32 | 8 | 6 | 4096 | 1 | 46.500 / 46.500 / 46.500 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c32 | 6 | 6 | 4096 | 1 | 46.451 / 46.451 / 46.451 | — | — | unresolved |
| a3_glm53flash_tp16_aclgraph_c32 | 2 | 6 | 4096 | 1 | 33.133 / 33.133 / 33.133 | — | — | unresolved |

a3_glm53flash_tp16_aclgraph_c32: scored 49 / 65 calls; all-population pass: None.
| a3_glm53flash_tp16_aclgraph_c64 | 64 | 6 | 4096 | 47 | 97.375 / 97.487 / 97.895 | 95.905 | -1.51% | PASS |
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
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 17 | 8 | 4096 | 21 | 61.811 / 61.629 / 62.042 | 63.541 | +2.80% | PASS |
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
| a5_glm53flash_heldout_c12_p4k | 2 | 4 | 4104 | 20 | 18.133 / 18.108 / 18.148 | 15.201 | -16.17% | FAIL |
| a5_glm53flash_heldout_c12_p4k | 3 | 4 | 4104 | 15 | 19.876 / 19.730 / 20.375 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 12 | 4 | 4104 | 10 | 32.310 / 32.084 / 32.482 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 6 | 4 | 4104 | 9 | 25.926 / 25.380 / 27.537 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 4 | 4 | 4104 | 5 | 21.675 / 21.618 / 21.897 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 8 | 4 | 4104 | 1 | 28.855 / 28.855 / 28.855 | — | — | unresolved |

a5_glm53flash_heldout_c12_p4k: scored 20 / 60 calls; all-population pass: False.
| a5_glm53flash_heldout_c24_p12k | 24 | 4 | 12296 | 21 | 38.995 / 39.210 / 39.263 | 31.147 | -20.12% | FAIL |
| a5_glm53flash_heldout_c24_p12k | 12 | 4 | 12296 | 10 | 32.978 / 32.904 / 33.062 | — | — | unresolved |
| a5_glm53flash_heldout_c24_p12k | 16 | 4 | 12296 | 6 | 34.357 / 34.349 / 34.465 | — | — | unresolved |
| a5_glm53flash_heldout_c24_p12k | 8 | 4 | 12296 | 4 | 29.935 / 29.876 / 30.133 | — | — | unresolved |

a5_glm53flash_heldout_c24_p12k: scored 21 / 41 calls; all-population pass: False.
| a5_glm53flash_heldout_c48_p4k | 48 | 4 | 4104 | 26 | 43.228 / 43.355 / 43.400 | 41.035 | -5.07% | PASS |
| a5_glm53flash_heldout_c48_p4k | 32 | 4 | 4104 | 9 | 38.189 / 38.157 / 38.314 | — | — | unresolved |
| a5_glm53flash_heldout_c48_p4k | 24 | 4 | 4104 | 2 | 37.382 / 37.382 / 37.552 | — | — | unresolved |

a5_glm53flash_heldout_c48_p4k: scored 26 / 37 calls; all-population pass: None.
| a3_glm53flash_static_on_c10_p131201 | 1 | 6 | 131201 | 68 | 22.603 / 22.348 / 23.552 | 23.072 | +2.07% | PASS |
| a3_glm53flash_static_on_c10_p131201 | 4 | 6 | 131201 | 13 | 28.251 / 27.985 / 28.308 | 32.885 | +16.40% | FAIL |
| a3_glm53flash_static_on_c10_p131201 | 8 | 6 | 131201 | 12 | 31.580 / 31.520 / 31.998 | 43.217 | +36.85% | FAIL |
| a3_glm53flash_static_on_c10_p131201 | 2 | 6 | 131201 | 3 | 25.713 / 24.344 / 28.811 | 26.340 | +2.44% | PASS |
| a3_glm53flash_static_on_c10_p131201 | 3 | 6 | 131201 | 1 | 31.415 / 31.415 / 31.415 | 29.575 | -5.86% | PASS |
| a3_glm53flash_static_on_c10_p131201 | 7 | 6 | 131201 | 1 | 35.748 / 35.748 / 35.748 | 40.745 | +13.98% | PASS |

a3_glm53flash_static_on_c10_p131201: scored 98 / 98 calls; all-population pass: False.
Context: same_run_prompt_plus_requested_output_bounds; representative 131201, bounds 131201–131265 tokens. 131201 is a conditional initial-context representative. The requested 64 output tokens only bound context growth; no per-step sequence-length values are retained. KV cache capacity is not active context.
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 | 2 | 126976 | 34 | 20.465 / 20.804 / 20.975 | 33.008 | +61.29% | FAIL |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 | 2 | 126976 | 16 | 16.107 / 16.100 / 16.156 | 31.468 | +95.37% | FAIL |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 | 2 | 126976 | 15 | 17.687 / 17.706 / 17.759 | 32.109 | +81.54% | FAIL |

a3-qwen35-tp4-longctx-p-126976-c4: scored 65 / 65 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 126976, bounds 126976–127104 tokens.
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 | 2 | 65536 | 55 | 16.750 / 16.724 / 16.909 | 20.194 | +20.56% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 | 2 | 65536 | 11 | 15.583 / 15.520 / 15.562 | 19.552 | +25.47% | FAIL |

a3-qwen35-tp4-longctx-p-65536-c2: scored 66 / 66 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65664 tokens.
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 | 2 | 65536 | 50 | 18.893 / 18.984 / 19.070 | 21.093 | +11.64% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 | 2 | 65536 | 8 | 15.649 / 15.561 / 16.432 | 19.552 | +24.94% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 | 2 | 65536 | 7 | 16.789 / 16.628 / 17.557 | 20.194 | +20.28% | FAIL |

a3-qwen35-tp4-longctx-p-65536-c4: scored 65 / 65 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65664 tokens.
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 | 2 | 65536 | 32 | 21.417 / 21.608 / 22.212 | 23.126 | +7.98% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 | 2 | 65536 | 17 | 18.901 / 18.818 / 19.256 | 21.093 | +11.60% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 | 2 | 65536 | 8 | 16.891 / 16.719 / 17.533 | 20.194 | +19.55% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 | 2 | 65536 | 8 | 15.502 / 15.507 / 15.581 | 19.552 | +26.12% | FAIL |

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
| a3-qwen35-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 47 | 27.914 / 27.905 / 28.026 | 22.491 | -19.43% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 5 | 27.606 / 27.594 / 27.674 | 22.491 | -18.53% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 4 | 4 | 24512 | 3 | 20.159 / 20.179 / 20.344 | 16.397 | -18.66% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 2 | 26.737 / 26.737 / 26.783 | 22.491 | -15.88% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 6 | 4 | 24512 | 2 | 22.561 / 22.561 / 22.616 | 19.228 | -14.78% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | 3 | 4 | 24512 | 2 | 19.339 / 19.339 / 19.366 | 15.208 | -21.36% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 2 | 4 | 24512 | 2 | 18.245 / 18.245 / 18.469 | 14.058 | -22.95% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 1 | 27.320 / 27.320 / 27.320 | 22.491 | -17.67% | FAIL |
| a3-qwen35-tp4-decode-c12-p24512 | 8 | 4 | 24512 | 1 | 25.229 / 25.229 / 25.229 | 21.533 | -14.65% | PASS |
| a3-qwen35-tp4-decode-c12-p24512 | 1 | 4 | 24512 | 1 | 16.443 / 16.443 / 16.443 | 12.912 | -21.47% | FAIL |

a3-qwen35-tp4-decode-c12-p24512: scored 66 / 66 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 45 | 30.548 / 30.507 / 30.812 | 30.248 | -0.98% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 5 | 29.822 / 29.824 / 29.931 | 30.248 | +1.43% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 2 | 4 | 64512 | 3 | 18.649 / 18.670 / 18.717 | 21.816 | +16.98% | FAIL |
| a3-qwen35-tp4-decode-c12-p64512 | 1 | 4 | 64512 | 3 | 17.131 / 17.174 / 17.190 | 20.669 | +20.66% | FAIL |
| a3-qwen35-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 2 | 30.154 / 30.154 / 30.172 | 30.248 | +0.31% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 8 | 4 | 64512 | 2 | 27.144 / 27.144 / 27.191 | 29.290 | +7.91% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 4 | 4 | 64512 | 2 | 21.293 / 21.293 / 21.391 | 24.154 | +13.44% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 8 | 4 | 64512 | 1 | 26.644 / 26.644 / 26.644 | 29.290 | +9.93% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 6 | 4 | 64512 | 1 | 24.465 / 24.465 / 24.465 | 26.985 | +10.30% | PASS |
| a3-qwen35-tp4-decode-c12-p64512 | 6 | 4 | 64512 | 1 | 24.030 / 24.030 / 24.030 | 26.985 | +12.29% | PASS |

a3-qwen35-tp4-decode-c12-p64512: scored 65 / 65 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c12-p8512 | 12 | 4 | 8512 | 43 | 27.435 / 27.433 / 27.570 | 19.388 | -29.33% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 8 | 4 | 8512 | 4 | 24.846 / 24.637 / 25.539 | 18.430 | -25.82% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 12 | 4 | 8512 | 3 | 26.729 / 26.732 / 26.738 | 19.388 | -27.46% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 1 | 4 | 8512 | 3 | 16.478 / 16.400 / 16.704 | 9.809 | -40.47% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 12 | 4 | 8512 | 2 | 26.571 / 26.571 / 26.579 | 19.388 | -27.03% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 6 | 4 | 8512 | 2 | 22.579 / 22.579 / 23.015 | 16.124 | -28.59% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 2 | 4 | 8512 | 2 | 18.301 / 18.301 / 18.746 | 10.955 | -40.14% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 6 | 4 | 8512 | 1 | 22.895 / 22.895 / 22.895 | 16.124 | -29.57% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 4 | 4 | 8512 | 1 | 20.122 / 20.122 / 20.122 | 13.294 | -33.93% | FAIL |
| a3-qwen35-tp4-decode-c12-p8512 | 3 | 4 | 8512 | 1 | 19.868 / 19.868 / 19.868 | 12.105 | -39.08% | FAIL |

a3-qwen35-tp4-decode-c12-p8512: scored 62 / 62 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 58 | 33.166 / 33.160 / 33.280 | 36.454 | +9.91% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 2 | 4 | 96512 | 4 | 19.093 / 19.097 / 19.126 | 28.022 | +46.76% | FAIL |
| a3-qwen35-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 2 | 32.148 / 32.148 / 32.172 | 36.454 | +13.39% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 6 | 4 | 96512 | 2 | 24.892 / 24.892 / 24.934 | 33.191 | +33.34% | FAIL |
| a3-qwen35-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 1 | 32.464 / 32.464 / 32.464 | 36.454 | +12.29% | PASS |
| a3-qwen35-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 1 | 30.525 / 30.525 / 30.525 | 36.454 | +19.43% | FAIL |
| a3-qwen35-tp4-decode-c12-p96512 | 8 | 4 | 96512 | 1 | 29.152 / 29.152 / 29.152 | 35.496 | +21.76% | FAIL |
| a3-qwen35-tp4-decode-c12-p96512 | 8 | 4 | 96512 | 1 | 28.172 / 28.172 / 28.172 | 35.496 | +26.00% | FAIL |
| a3-qwen35-tp4-decode-c12-p96512 | 6 | 4 | 96512 | 1 | 25.749 / 25.749 / 25.749 | 33.191 | +28.90% | FAIL |
| a3-qwen35-tp4-decode-c12-p96512 | 3 | 4 | 96512 | 1 | 20.650 / 20.650 / 20.650 | 29.171 | +41.26% | FAIL |

a3-qwen35-tp4-decode-c12-p96512: scored 72 / 72 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 66 | 35.550 / 35.558 / 35.723 | 29.960 | -15.72% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 4 | 35.286 / 35.290 / 35.309 | 29.960 | -15.09% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | 16 | 4 | 24512 | 2 | 29.030 / 29.030 / 29.088 | 23.411 | -19.35% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 1 | 35.290 / 35.290 / 35.290 | 29.960 | -15.10% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 1 | 35.251 / 35.251 / 35.251 | 29.960 | -15.01% | FAIL |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 1 | 32.578 / 32.578 / 32.578 | 29.960 | -8.04% | PASS |
| a3-qwen35-tp4-decode-c24-p24512 | 24 | 4 | 24512 | 1 | 32.499 / 32.499 / 32.499 | 29.960 | -7.81% | PASS |

a3-qwen35-tp4-decode-c24-p24512: scored 76 / 76 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 57 | 31.676 / 31.677 / 31.775 | 23.754 | -25.01% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 5 | 31.676 / 31.674 / 31.785 | 23.754 | -25.01% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 1 | 4 | 8512 | 4 | 16.276 / 16.290 / 16.309 | 9.809 | -39.73% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 8 | 4 | 8512 | 3 | 24.803 / 24.876 / 24.914 | 18.430 | -25.70% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 2 | 31.743 / 31.743 / 31.762 | 23.754 | -25.17% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 6 | 4 | 8512 | 2 | 23.229 / 23.229 / 23.757 | 16.124 | -30.59% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 4 | 4 | 8512 | 2 | 19.631 / 19.631 / 19.754 | 13.294 | -32.28% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 1 | 30.205 / 30.205 / 30.205 | 23.754 | -21.36% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 24 | 4 | 8512 | 1 | 30.045 / 30.045 / 30.045 | 23.754 | -20.94% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 16 | 4 | 8512 | 1 | 27.966 / 27.966 / 27.966 | 20.308 | -27.38% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 12 | 4 | 8512 | 1 | 27.150 / 27.150 / 27.150 | 19.388 | -28.59% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 12 | 4 | 8512 | 1 | 26.616 / 26.616 / 26.616 | 19.388 | -27.16% | FAIL |
| a3-qwen35-tp4-decode-c24-p8512 | 12 | 4 | 8512 | 1 | 26.505 / 26.505 / 26.505 | 19.388 | -26.85% | FAIL |

a3-qwen35-tp4-decode-c24-p8512: scored 81 / 81 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c2-p24512 | 1 | 4 | 24512 | 16 | 16.697 / 16.657 / 16.860 | 12.912 | -22.67% | FAIL |
| a3-qwen35-tp4-decode-c2-p24512 | 2 | 4 | 24512 | 2 | 18.147 / 18.147 / 18.217 | 14.058 | -22.53% | FAIL |

a3-qwen35-tp4-decode-c2-p24512: scored 18 / 18 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c2-p64512 | 1 | 4 | 64512 | 7 | 17.136 / 17.138 / 17.270 | 20.669 | +20.62% | FAIL |
| a3-qwen35-tp4-decode-c2-p64512 | 2 | 4 | 64512 | 4 | 18.681 / 18.662 / 18.872 | 21.816 | +16.78% | FAIL |

a3-qwen35-tp4-decode-c2-p64512: scored 11 / 11 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c2-p96512 | 1 | 4 | 96512 | 12 | 17.338 / 17.324 / 17.456 | 26.875 | +55.01% | FAIL |
| a3-qwen35-tp4-decode-c2-p96512 | 2 | 4 | 96512 | 1 | 19.025 / 19.025 / 19.025 | 28.022 | +47.29% | FAIL |

a3-qwen35-tp4-decode-c2-p96512: scored 13 / 13 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c6-p24512 | 6 | 4 | 24512 | 23 | 23.225 / 23.181 / 23.327 | 19.228 | -17.21% | FAIL |
| a3-qwen35-tp4-decode-c6-p24512 | 6 | 4 | 24512 | 10 | 22.732 / 22.725 / 22.825 | 19.228 | -15.42% | FAIL |
| a3-qwen35-tp4-decode-c6-p24512 | 1 | 4 | 24512 | 8 | 16.594 / 16.577 / 16.924 | 12.912 | -22.19% | FAIL |
| a3-qwen35-tp4-decode-c6-p24512 | 2 | 4 | 24512 | 3 | 18.051 / 18.068 / 18.143 | 14.058 | -22.12% | FAIL |
| a3-qwen35-tp4-decode-c6-p24512 | 3 | 4 | 24512 | 1 | 19.134 / 19.134 / 19.134 | 15.208 | -20.52% | FAIL |

a3-qwen35-tp4-decode-c6-p24512: scored 45 / 45 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c6-p64512 | 6 | 4 | 64512 | 40 | 24.666 / 24.667 / 24.763 | 26.985 | +9.40% | PASS |
| a3-qwen35-tp4-decode-c6-p64512 | 2 | 4 | 64512 | 2 | 18.846 / 18.846 / 18.912 | 21.816 | +15.76% | FAIL |
| a3-qwen35-tp4-decode-c6-p64512 | 6 | 4 | 64512 | 1 | 24.044 / 24.044 / 24.044 | 26.985 | +12.23% | PASS |
| a3-qwen35-tp4-decode-c6-p64512 | 3 | 4 | 64512 | 1 | 20.966 / 20.966 / 20.966 | 22.965 | +9.53% | PASS |

a3-qwen35-tp4-decode-c6-p64512: scored 44 / 44 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c6-p8512 | 6 | 4 | 8512 | 21 | 22.846 / 22.849 / 22.926 | 16.124 | -29.42% | FAIL |
| a3-qwen35-tp4-decode-c6-p8512 | 6 | 4 | 8512 | 6 | 22.307 / 22.130 / 23.271 | 16.124 | -27.72% | FAIL |
| a3-qwen35-tp4-decode-c6-p8512 | 1 | 4 | 8512 | 4 | 16.413 / 16.480 / 16.495 | 9.809 | -40.24% | FAIL |
| a3-qwen35-tp4-decode-c6-p8512 | 4 | 4 | 8512 | 3 | 19.802 / 19.803 / 19.841 | 13.294 | -32.87% | FAIL |
| a3-qwen35-tp4-decode-c6-p8512 | 2 | 4 | 8512 | 3 | 17.950 / 17.777 / 18.306 | 10.955 | -38.97% | FAIL |

a3-qwen35-tp4-decode-c6-p8512: scored 37 / 37 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen35-tp4-decode-c6-p96512 | 6 | 4 | 96512 | 42 | 26.149 / 25.837 / 26.090 | 33.191 | +26.93% | FAIL |
| a3-qwen35-tp4-decode-c6-p96512 | 1 | 4 | 96512 | 3 | 17.198 / 17.217 / 17.249 | 26.875 | +56.27% | FAIL |
| a3-qwen35-tp4-decode-c6-p96512 | 4 | 4 | 96512 | 2 | 22.157 / 22.157 / 22.231 | 30.360 | +37.02% | FAIL |
| a3-qwen35-tp4-decode-c6-p96512 | 3 | 4 | 96512 | 2 | 20.734 / 20.734 / 20.752 | 29.171 | +40.69% | FAIL |
| a3-qwen35-tp4-decode-c6-p96512 | 6 | 4 | 96512 | 1 | 24.858 / 24.858 / 24.858 | 33.191 | +33.52% | FAIL |
| a3-qwen35-tp4-decode-c6-p96512 | 2 | 4 | 96512 | 1 | 19.098 / 19.098 / 19.098 | 28.022 | +46.72% | FAIL |

a3-qwen35-tp4-decode-c6-p96512: scored 51 / 51 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c2-p24512 | 2 | 4 | 24512 | 58 | 26.724 / 26.694 / 26.806 | 27.529 | +3.01% | PASS |
| a3-qwen36-tp2-decode-c2-p24512 | 1 | 4 | 24512 | 4 | 24.082 / 24.057 / 24.170 | 26.218 | +8.87% | PASS |

a3-qwen36-tp2-decode-c2-p24512: scored 62 / 62 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c2-p64512 | 2 | 4 | 64512 | 58 | 28.868 / 28.845 / 28.903 | 39.939 | +38.35% | FAIL |
| a3-qwen36-tp2-decode-c2-p64512 | 1 | 4 | 64512 | 2 | 25.571 / 25.571 / 25.671 | 38.628 | +51.06% | FAIL |

a3-qwen36-tp2-decode-c2-p64512: scored 60 / 60 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c2-p8512 | 2 | 4 | 8512 | 45 | 25.809 / 25.747 / 25.801 | 22.564 | -12.57% | PASS |
| a3-qwen36-tp2-decode-c2-p8512 | 1 | 4 | 8512 | 1 | 23.898 / 23.898 / 23.898 | 21.253 | -11.07% | PASS |

a3-qwen36-tp2-decode-c2-p8512: scored 46 / 46 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c2-p96512 | 2 | 4 | 96512 | 62 | 30.222 / 30.218 / 30.266 | 49.869 | +65.01% | FAIL |
| a3-qwen36-tp2-decode-c2-p96512 | 1 | 4 | 96512 | 8 | 26.458 / 26.465 / 26.476 | 48.558 | +83.53% | FAIL |

a3-qwen36-tp2-decode-c2-p96512: scored 70 / 70 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c6-p24512 | 6 | 4 | 24512 | 71 | 33.717 / 33.762 / 33.825 | 31.561 | -6.40% | PASS |
| a3-qwen36-tp2-decode-c6-p24512 | 6 | 4 | 24512 | 3 | 32.197 / 32.189 / 32.215 | 31.561 | -1.98% | PASS |
| a3-qwen36-tp2-decode-c6-p24512 | 2 | 4 | 24512 | 3 | 26.611 / 26.592 / 26.658 | 27.529 | +3.45% | PASS |
| a3-qwen36-tp2-decode-c6-p24512 | 3 | 4 | 24512 | 2 | 28.284 / 28.284 / 28.296 | 28.271 | -0.05% | PASS |
| a3-qwen36-tp2-decode-c6-p24512 | 1 | 4 | 24512 | 2 | 24.086 / 24.086 / 24.086 | 26.218 | +8.85% | PASS |

a3-qwen36-tp2-decode-c6-p24512: scored 81 / 81 calls; all-population pass: True.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen36-tp2-decode-c6-p8512 | 6 | 4 | 8512 | 61 | 32.027 / 31.966 / 32.038 | 26.596 | -16.96% | FAIL |
| a3-qwen36-tp2-decode-c6-p8512 | 2 | 4 | 8512 | 4 | 25.655 / 25.632 / 25.749 | 22.564 | -12.05% | PASS |
| a3-qwen36-tp2-decode-c6-p8512 | 4 | 4 | 8512 | 3 | 29.068 / 29.004 / 29.228 | 24.560 | -15.51% | FAIL |
| a3-qwen36-tp2-decode-c6-p8512 | 6 | 4 | 8512 | 2 | 31.017 / 31.017 / 31.028 | 26.596 | -14.25% | PASS |
| a3-qwen36-tp2-decode-c6-p8512 | 3 | 4 | 8512 | 2 | 26.970 / 26.970 / 26.987 | 23.306 | -13.58% | PASS |

a3-qwen36-tp2-decode-c6-p8512: scored 72 / 72 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 8512, bounds 8512–9024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 56 | 30.908 / 30.898 / 30.968 | 27.432 | -11.25% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 1 | 4 | 24512 | 5 | 17.858 / 17.763 / 18.319 | 20.977 | +17.46% | FAIL |
| a3-qwen38-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 4 | 29.450 / 29.456 / 29.484 | 27.432 | -6.85% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 3 | 30.283 / 30.285 / 30.300 | 27.432 | -9.41% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 2 | 4 | 24512 | 2 | 19.259 / 19.259 / 19.377 | 21.423 | +11.23% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 12 | 4 | 24512 | 1 | 28.776 / 28.776 / 28.776 | 27.432 | -4.67% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 6 | 4 | 24512 | 1 | 24.934 / 24.934 / 24.934 | 23.743 | -4.78% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 6 | 4 | 24512 | 1 | 24.287 / 24.287 / 24.287 | 23.743 | -2.24% | PASS |
| a3-qwen38-tp4-decode-c12-p24512 | 3 | 4 | 24512 | 1 | 20.102 / 20.102 / 20.102 | 21.899 | +8.94% | PASS |

a3-qwen38-tp4-decode-c12-p24512: scored 74 / 74 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 68 | 35.845 / 35.986 / 36.161 | 39.843 | +11.15% | PASS |
| a3-qwen38-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 5 | 32.176 / 32.177 / 32.195 | 39.843 | +23.83% | FAIL |
| a3-qwen38-tp4-decode-c12-p64512 | 8 | 4 | 64512 | 2 | 31.108 / 31.108 / 31.443 | 37.541 | +20.68% | FAIL |
| a3-qwen38-tp4-decode-c12-p64512 | 12 | 4 | 64512 | 1 | 34.707 / 34.707 / 34.707 | 39.843 | +14.80% | PASS |

a3-qwen38-tp4-decode-c12-p64512: scored 76 / 76 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 65 | 39.782 / 39.852 / 40.095 | 49.772 | +25.11% | FAIL |
| a3-qwen38-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 3 | 35.379 / 35.367 / 35.422 | 49.772 | +40.68% | FAIL |
| a3-qwen38-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 2 | 38.252 / 38.252 / 38.309 | 49.772 | +30.12% | FAIL |
| a3-qwen38-tp4-decode-c12-p96512 | 12 | 4 | 96512 | 1 | 37.966 / 37.966 / 37.966 | 49.772 | +31.10% | FAIL |

a3-qwen38-tp4-decode-c12-p96512: scored 71 / 71 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c2-p24512 | 2 | 4 | 24512 | 11 | 19.404 / 19.244 / 20.150 | 21.423 | +10.41% | PASS |
| a3-qwen38-tp4-decode-c2-p24512 | 1 | 4 | 24512 | 4 | 17.817 / 17.836 / 17.873 | 20.977 | +17.73% | FAIL |

a3-qwen38-tp4-decode-c2-p24512: scored 15 / 15 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c2-p64512 | 2 | 4 | 64512 | 20 | 20.210 / 20.021 / 20.180 | 33.834 | +67.41% | FAIL |
| a3-qwen38-tp4-decode-c2-p64512 | 1 | 4 | 64512 | 3 | 18.455 / 18.447 / 18.491 | 33.388 | +80.91% | FAIL |

a3-qwen38-tp4-decode-c2-p64512: scored 23 / 23 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c2-p96512 | 2 | 4 | 96512 | 24 | 20.989 / 20.830 / 21.239 | 43.764 | +108.51% | FAIL |
| a3-qwen38-tp4-decode-c2-p96512 | 1 | 4 | 96512 | 3 | 19.328 / 19.048 / 19.910 | 43.317 | +124.11% | FAIL |

a3-qwen38-tp4-decode-c2-p96512: scored 27 / 27 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 96512, bounds 96512–97024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c6-p24512 | 6 | 4 | 24512 | 38 | 24.761 / 24.752 / 24.829 | 23.743 | -4.11% | PASS |
| a3-qwen38-tp4-decode-c6-p24512 | 6 | 4 | 24512 | 3 | 24.323 / 24.320 / 24.333 | 23.743 | -2.38% | PASS |
| a3-qwen38-tp4-decode-c6-p24512 | 2 | 4 | 24512 | 2 | 19.597 / 19.597 / 19.909 | 21.423 | +9.32% | PASS |
| a3-qwen38-tp4-decode-c6-p24512 | 1 | 4 | 24512 | 2 | 17.817 / 17.817 / 17.863 | 20.977 | +17.73% | FAIL |
| a3-qwen38-tp4-decode-c6-p24512 | 4 | 4 | 24512 | 1 | 22.503 / 22.503 / 22.503 | 22.867 | +1.62% | PASS |

a3-qwen38-tp4-decode-c6-p24512: scored 46 / 46 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 24512, bounds 24512–25024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c6-p64512 | 6 | 4 | 64512 | 40 | 27.237 / 27.135 / 27.365 | 36.154 | +32.74% | FAIL |
| a3-qwen38-tp4-decode-c6-p64512 | 4 | 4 | 64512 | 5 | 23.956 / 23.825 / 24.480 | 35.278 | +47.26% | FAIL |
| a3-qwen38-tp4-decode-c6-p64512 | 3 | 4 | 64512 | 4 | 22.568 / 22.104 / 24.375 | 34.309 | +52.03% | FAIL |
| a3-qwen38-tp4-decode-c6-p64512 | 6 | 4 | 64512 | 2 | 26.501 / 26.501 / 26.502 | 36.154 | +36.42% | FAIL |
| a3-qwen38-tp4-decode-c6-p64512 | 2 | 4 | 64512 | 2 | 20.478 / 20.478 / 20.765 | 33.834 | +65.22% | FAIL |
| a3-qwen38-tp4-decode-c6-p64512 | 1 | 4 | 64512 | 2 | 18.774 / 18.774 / 19.076 | 33.388 | +77.84% | FAIL |

a3-qwen38-tp4-decode-c6-p64512: scored 55 / 55 calls; all-population pass: False.
Context: retained_request_prompt_usage; representative 64512, bounds 64512–65024 tokens. The initial prompt is a conditional representative, not a per-step KV length. Token bounds describe the associated client run; cache/table capacities are not active context.
| a3-qwen38-tp4-decode-c6-p96512 | 6 | 4 | 96512 | 42 | 29.560 / 29.308 / 29.565 | 46.083 | +55.90% | FAIL |
| a3-qwen38-tp4-decode-c6-p96512 | 1 | 4 | 96512 | 6 | 19.227 / 19.055 / 20.072 | 43.317 | +125.29% | FAIL |
| a3-qwen38-tp4-decode-c6-p96512 | 3 | 4 | 96512 | 5 | 22.911 / 22.846 / 23.176 | 44.239 | +93.09% | FAIL |
| a3-qwen38-tp4-decode-c6-p96512 | 6 | 4 | 96512 | 4 | 28.344 / 28.354 / 28.383 | 46.083 | +62.59% | FAIL |
| a3-qwen38-tp4-decode-c6-p96512 | 2 | 4 | 96512 | 4 | 20.979 / 20.931 / 21.140 | 43.764 | +108.61% | FAIL |
| a3-qwen38-tp4-decode-c6-p96512 | 4 | 4 | 96512 | 3 | 25.537 / 25.517 / 25.608 | 45.208 | +77.03% | FAIL |

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
| glm53flash-a5-tp8-c96 | 96 / 4 | kda | 34 | 0.971 / 1.009 | 1.072 / 1.111 | +10.42% / +10.16% |
| glm53flash-a5-tp8-c96 | 96 / 4 | mla | 11 | 2.233 / 2.234 | 2.319 / 2.319 | +3.81% / +3.79% |
| glm53flash-a5-tp8-c96 | 96 / 4 | dense_layer | 3 | 0.583 / 0.573 | 0.669 / 0.669 | +14.85% / +16.86% |
| glm53flash-a5-tp8-c96 | 96 / 4 | moe_layer | 42 | 1.330 / 1.011 | 1.428 / 1.111 | +7.37% / +9.98% |
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
| qwen35-397b-a3-tp16-c48 | 64 / 4 | gdn | 45 | 1.236 / 1.203 | 1.106 / 1.106 | -10.51% / -8.09% |
| qwen35-397b-a3-tp16-c48 | 64 / 4 | gqa | 15 | 1.361 / 1.341 | 1.135 / 1.135 | -16.61% / -15.39% |
| qwen35-397b-a3-tp16-c48 | 64 / 4 | moe_layer | 60 | 1.267 / 1.279 | 1.113 / 1.106 | -12.15% / -13.53% |
| qwen35-397b-a3-tp16-c136 | 160 / 4 | gdn | 45 | 1.959 / 1.940 | 1.722 / 1.722 | -12.12% / -11.26% |
| qwen35-397b-a3-tp16-c136 | 160 / 4 | gqa | 15 | 2.054 / 2.022 | 1.800 / 1.800 | -12.37% / -10.97% |
| qwen35-397b-a3-tp16-c136 | 160 / 4 | moe_layer | 60 | 1.983 / 1.996 | 1.741 / 1.722 | -12.19% / -13.76% |
| qwen35-35b-a5-tp4-c64-graph | 64 / 4 | gdn | 30 | 0.555 / 0.547 | 0.513 / 0.513 | -7.44% / -6.17% |
| qwen35-35b-a5-tp4-c64-graph | 64 / 4 | gqa | 10 | 0.532 / 0.532 | 0.458 / 0.458 | -13.98% / -14.06% |
| qwen35-35b-a5-tp4-c64-graph | 64 / 4 | moe_layer | 40 | 0.549 / 0.546 | 0.499 / 0.513 | -9.02% / -5.95% |
| qwen35-35b-a5-tp4-c128-graph | 128 / 4 | gdn | 30 | 0.721 / 0.720 | 0.671 / 0.671 | -6.93% / -6.80% |
| qwen35-35b-a5-tp4-c128-graph | 128 / 4 | gqa | 10 | 0.695 / 0.695 | 0.592 / 0.592 | -14.91% / -14.83% |
| qwen35-35b-a5-tp4-c128-graph | 128 / 4 | moe_layer | 40 | 0.715 / 0.720 | 0.651 / 0.671 | -8.87% / -6.74% |
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
| a5_glm53flash_tp8_c4_p8k | 4 / 4 | mla | 11 | 0.673 / 0.670 | 0.488 / 0.488 | -27.56% / -27.17% |
| a5_glm53flash_tp8_c4_p8k | 4 / 4 | dense_layer | 3 | 0.264 / 0.235 | 0.179 / 0.179 | -32.29% / -23.92% |
| a5_glm53flash_tp8_c4_p8k | 4 / 4 | moe_layer | 42 | 0.491 / 0.429 | 0.420 / 0.395 | -14.55% / -7.75% |
| a5_glm53flash_tp8_c64_p4k | 64 / 4 | kda | 34 | 0.853 / 0.886 | 0.857 / 0.900 | +0.41% / +1.48% |
| a5_glm53flash_tp8_c64_p4k | 64 / 4 | mla | 11 | 1.593 / 1.584 | 1.531 / 1.531 | -3.89% / -3.36% |
| a5_glm53flash_tp8_c64_p4k | 64 / 4 | dense_layer | 3 | 0.497 / 0.470 | 0.413 / 0.413 | -16.86% / -12.17% |
| a5_glm53flash_tp8_c64_p4k | 64 / 4 | moe_layer | 42 | 1.072 / 0.890 | 1.065 / 0.900 | -0.69% / +1.11% |
| a5_glm53flash_tp8_c8_p4k | 8 / 4 | kda | 34 | 0.567 / 0.589 | 0.525 / 0.555 | -7.53% / -5.67% |
| a5_glm53flash_tp8_c8_p4k | 8 / 4 | mla | 11 | 0.868 / 0.868 | 0.670 / 0.670 | -22.85% / -22.85% |
| a5_glm53flash_tp8_c8_p4k | 8 / 4 | dense_layer | 3 | 0.335 / 0.258 | 0.207 / 0.207 | -38.31% / -19.84% |
| a5_glm53flash_tp8_c8_p4k | 8 / 4 | moe_layer | 42 | 0.663 / 0.593 | 0.585 / 0.555 | -11.67% / -6.38% |
| a3_glm53flash_tp16_aclgraph_c16 | 16 / 6 | kda | 34 | 1.038 / 1.074 | 0.895 / 0.939 | -13.79% / -12.53% |
| a3_glm53flash_tp16_aclgraph_c16 | 16 / 6 | mla | 11 | 1.686 / 1.687 | 1.693 / 1.693 | +0.40% / +0.34% |
| a3_glm53flash_tp16_aclgraph_c16 | 16 / 6 | dense_layer | 3 | 0.667 / 0.670 | 0.438 / 0.438 | -34.36% / -34.58% |
| a3_glm53flash_tp16_aclgraph_c16 | 16 / 6 | moe_layer | 42 | 1.234 / 1.078 | 1.137 / 0.939 | -7.92% / -12.86% |
| a3_glm53flash_tp16_aclgraph_c32 | 32 / 6 | kda | 34 | 1.284 / 1.318 | 1.066 / 1.112 | -16.97% / -15.69% |
| a3_glm53flash_tp16_aclgraph_c32 | 32 / 6 | mla | 11 | 2.332 / 2.330 | 2.554 / 2.554 | +9.51% / +9.60% |
| a3_glm53flash_tp16_aclgraph_c32 | 32 / 6 | dense_layer | 3 | 0.902 / 0.886 | 0.596 / 0.596 | -33.90% / -32.72% |
| a3_glm53flash_tp16_aclgraph_c32 | 32 / 6 | moe_layer | 42 | 1.586 / 1.326 | 1.489 / 1.112 | -6.08% / -16.17% |
| a3_glm53flash_tp16_aclgraph_c64 | 64 / 6 | kda | 34 | 1.721 / 1.760 | 1.428 / 1.478 | -17.03% / -15.98% |
| a3_glm53flash_tp16_aclgraph_c64 | 64 / 6 | mla | 11 | 3.529 / 3.531 | 4.305 / 4.305 | +22.01% / +21.94% |
| a3_glm53flash_tp16_aclgraph_c64 | 64 / 6 | dense_layer | 3 | 1.308 / 1.302 | 0.906 / 0.906 | -30.69% / -30.42% |
| a3_glm53flash_tp16_aclgraph_c64 | 64 / 6 | moe_layer | 42 | 2.224 / 1.764 | 2.219 / 1.478 | -0.23% / -16.20% |
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
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 17 / 8 | mla | 40 | 1.544 / 1.461 | 1.589 / 1.553 | +2.88% / +6.26% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 17 / 8 | moe_layer | 40 | 1.544 / 1.461 | 1.589 / 1.553 | +2.88% / +6.26% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | 4 / 8 | mla | 40 | 1.213 / 1.160 | 1.292 / 1.273 | +6.47% / +9.75% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | 4 / 8 | moe_layer | 40 | 1.213 / 1.160 | 1.292 / 1.273 | +6.47% / +9.75% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k | 16 / 1 | mla | 40 | 0.682 / 0.655 | 0.638 / 0.626 | -6.40% / -4.38% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k | 16 / 1 | moe_layer | 40 | 0.682 / 0.655 | 0.638 / 0.626 | -6.40% / -4.38% |
| qwen35-35b-a3-tp4-c144 | 160 / 4 | gdn | 30 | 1.579 / 1.574 | 1.373 / 1.373 | -13.06% / -12.78% |
| qwen35-35b-a3-tp4-c144 | 160 / 4 | gqa | 10 | 1.435 / 1.432 | 1.240 / 1.240 | -13.63% / -13.42% |
| qwen35-35b-a3-tp4-c144 | 160 / 4 | moe_layer | 40 | 1.543 / 1.572 | 1.339 / 1.373 | -13.19% / -12.68% |
| qwen35-35b-a3-tp4-c320 | 320 / 4 | gdn | 30 | 2.609 / 2.608 | 2.410 / 2.410 | -7.65% / -7.62% |
| qwen35-35b-a3-tp4-c320 | 320 / 4 | gqa | 10 | 2.138 / 2.137 | 2.172 / 2.172 | +1.58% / +1.63% |
| qwen35-35b-a3-tp4-c320 | 320 / 4 | moe_layer | 40 | 2.491 / 2.601 | 2.350 / 2.410 | -5.67% / -7.37% |
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
| a5_glm53flash_heldout_c12_p4k | 2 / 4 | mla | 11 | 0.598 / 0.595 | 0.380 / 0.380 | -36.47% / -36.09% |
| a5_glm53flash_heldout_c12_p4k | 2 / 4 | dense_layer | 3 | 0.289 / 0.237 | 0.173 / 0.173 | -40.01% / -26.95% |
| a5_glm53flash_heldout_c12_p4k | 2 / 4 | moe_layer | 42 | 0.411 / 0.346 | 0.350 / 0.339 | -14.97% / -2.21% |
| a5_glm53flash_heldout_c24_p12k | 24 / 4 | kda | 34 | 0.692 / 0.725 | 0.628 / 0.665 | -9.19% / -8.34% |
| a5_glm53flash_heldout_c24_p12k | 24 / 4 | mla | 11 | 1.406 / 1.404 | 0.889 / 0.889 | -36.75% / -36.69% |
| a5_glm53flash_heldout_c24_p12k | 24 / 4 | dense_layer | 3 | 0.345 / 0.334 | 0.255 / 0.255 | -26.22% / -23.72% |
| a5_glm53flash_heldout_c24_p12k | 24 / 4 | moe_layer | 42 | 0.904 / 0.728 | 0.723 / 0.665 | -19.96% / -8.74% |
| a5_glm53flash_heldout_c48_p4k | 48 / 4 | kda | 34 | 0.786 / 0.821 | 0.801 / 0.845 | +1.92% / +2.88% |
| a5_glm53flash_heldout_c48_p4k | 48 / 4 | mla | 11 | 1.501 / 1.498 | 1.256 / 1.256 | -16.38% / -16.17% |
| a5_glm53flash_heldout_c48_p4k | 48 / 4 | dense_layer | 3 | 0.419 / 0.411 | 0.346 / 0.346 | -17.53% / -15.96% |
| a5_glm53flash_heldout_c48_p4k | 48 / 4 | moe_layer | 42 | 0.999 / 0.823 | 0.952 / 0.845 | -4.70% / +2.61% |
| a3_glm53flash_static_on_c10_p131201 | 1 / 6 | kda | 34 | 0.449 / 0.450 | 0.448 / 0.466 | -0.30% / +3.51% |
| a3_glm53flash_static_on_c10_p131201 | 1 / 6 | mla | 11 | 0.662 / 0.661 | 0.713 / 0.713 | +7.77% / +7.97% |
| a3_glm53flash_static_on_c10_p131201 | 1 / 6 | dense_layer | 3 | 0.427 / 0.248 | 0.258 / 0.258 | -39.61% / +4.21% |
| a3_glm53flash_static_on_c10_p131201 | 1 / 6 | moe_layer | 42 | 0.506 / 0.455 | 0.531 / 0.466 | +4.83% / +2.56% |
| a3_glm53flash_static_on_c10_p131201 | 4 / 6 | kda | 34 | 0.577 / 0.571 | 0.606 / 0.639 | +5.08% / +11.90% |
| a3_glm53flash_static_on_c10_p131201 | 4 / 6 | mla | 11 | 0.780 / 0.771 | 1.115 / 1.115 | +43.02% / +44.67% |
| a3_glm53flash_static_on_c10_p131201 | 4 / 6 | dense_layer | 3 | 0.603 / 0.295 | 0.271 / 0.271 | -55.09% / -8.33% |
| a3_glm53flash_static_on_c10_p131201 | 4 / 6 | moe_layer | 42 | 0.628 / 0.577 | 0.764 / 0.639 | +21.53% / +10.66% |
| a3_glm53flash_static_on_c10_p131201 | 8 / 6 | kda | 34 | 0.592 / 0.583 | 0.746 / 0.789 | +26.09% / +35.21% |
| a3_glm53flash_static_on_c10_p131201 | 8 / 6 | mla | 11 | 1.038 / 1.036 | 1.623 / 1.623 | +56.42% / +56.68% |
| a3_glm53flash_static_on_c10_p131201 | 8 / 6 | dense_layer | 3 | 0.625 / 0.345 | 0.301 / 0.301 | -51.81% / -12.54% |
| a3_glm53flash_static_on_c10_p131201 | 8 / 6 | moe_layer | 42 | 0.706 / 0.601 | 1.007 / 0.789 | +42.69% / +31.29% |
| a3_glm53flash_static_on_c10_p131201 | 2 / 6 | kda | 34 | 0.530 / 0.499 | 0.507 / 0.531 | -4.44% / +6.36% |
| a3_glm53flash_static_on_c10_p131201 | 2 / 6 | mla | 11 | 0.693 / 0.688 | 0.828 / 0.828 | +19.39% / +20.29% |
| a3_glm53flash_static_on_c10_p131201 | 2 / 6 | dense_layer | 3 | 0.883 / 0.264 | 0.261 / 0.261 | -70.47% / -1.05% |
| a3_glm53flash_static_on_c10_p131201 | 2 / 6 | moe_layer | 42 | 0.548 / 0.504 | 0.609 / 0.531 | +11.06% / +5.34% |
| a3_glm53flash_static_on_c10_p131201 | 3 / 6 | kda | 34 | 0.677 / 0.549 | 0.556 / 0.584 | -17.88% / +6.41% |
| a3_glm53flash_static_on_c10_p131201 | 3 / 6 | mla | 11 | 0.758 / 0.759 | 0.970 / 0.970 | +27.90% / +27.85% |
| a3_glm53flash_static_on_c10_p131201 | 3 / 6 | dense_layer | 3 | 1.895 / 0.289 | 0.265 / 0.265 | -86.00% / -8.12% |
| a3_glm53flash_static_on_c10_p131201 | 3 / 6 | moe_layer | 42 | 0.611 / 0.565 | 0.685 / 0.584 | +12.07% / +3.38% |
| a3_glm53flash_static_on_c10_p131201 | 7 / 6 | kda | 34 | 0.704 / 0.638 | 0.713 / 0.754 | +1.34% / +18.12% |
| a3_glm53flash_static_on_c10_p131201 | 7 / 6 | mla | 11 | 1.069 / 1.060 | 1.499 / 1.499 | +40.21% / +41.35% |
| a3_glm53flash_static_on_c10_p131201 | 7 / 6 | dense_layer | 3 | 1.405 / 0.339 | 0.296 / 0.296 | -78.93% / -12.65% |
| a3_glm53flash_static_on_c10_p131201 | 7 / 6 | moe_layer | 42 | 0.750 / 0.648 | 0.949 / 0.754 | +26.60% / +16.31% |
| a3-qwen35-tp4-longctx-p-126976-c1 | 1 / 2 | gdn | 30 | 0.367 / 0.367 | 0.183 / 0.183 | -50.03% / -50.07% |
| a3-qwen35-tp4-longctx-p-126976-c1 | 1 / 2 | gqa | 10 | 0.499 / 0.500 | 2.596 / 2.596 | +420.17% / +419.04% |
| a3-qwen35-tp4-longctx-p-126976-c1 | 1 / 2 | moe_layer | 40 | 0.400 / 0.370 | 0.787 / 0.183 | +96.60% / -50.47% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 / 2 | gdn | 30 | 0.410 / 0.409 | 0.223 / 0.223 | -45.63% / -45.49% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 / 2 | gqa | 10 | 0.813 / 0.814 | 2.632 / 2.632 | +223.94% / +223.27% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 / 2 | moe_layer | 40 | 0.511 / 0.414 | 0.825 / 0.223 | +61.60% / -46.13% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 / 2 | gdn | 30 | 0.369 / 0.368 | 0.183 / 0.183 | -50.29% / -50.09% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 / 2 | gqa | 10 | 0.499 / 0.500 | 2.596 / 2.596 | +420.57% / +418.98% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 / 2 | moe_layer | 40 | 0.401 / 0.373 | 0.787 / 0.183 | +95.94% / -50.86% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 / 2 | gdn | 30 | 0.380 / 0.380 | 0.200 / 0.200 | -47.47% / -47.40% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 / 2 | gqa | 10 | 0.625 / 0.626 | 2.612 / 2.612 | +318.21% / +317.35% |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 / 2 | moe_layer | 40 | 0.441 / 0.385 | 0.803 / 0.200 | +81.92% / -48.10% |
| a3-qwen35-tp4-longctx-p-65536-c1 | 1 / 2 | gdn | 30 | 0.368 / 0.366 | 0.183 / 0.183 | -50.14% / -49.89% |
| a3-qwen35-tp4-longctx-p-65536-c1 | 1 / 2 | gqa | 10 | 0.444 / 0.444 | 1.405 / 1.405 | +216.23% / +216.15% |
| a3-qwen35-tp4-longctx-p-65536-c1 | 1 / 2 | moe_layer | 40 | 0.387 / 0.368 | 0.489 / 0.183 | +26.30% / -50.14% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 / 2 | gdn | 30 | 0.385 / 0.381 | 0.200 / 0.200 | -48.16% / -47.55% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 / 2 | gqa | 10 | 0.516 / 0.517 | 1.420 / 1.420 | +175.43% / +174.90% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 / 2 | moe_layer | 40 | 0.418 / 0.385 | 0.505 / 0.200 | +20.82% / -48.15% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 / 2 | gdn | 30 | 0.369 / 0.365 | 0.183 / 0.183 | -50.31% / -49.72% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 / 2 | gqa | 10 | 0.446 / 0.447 | 1.405 / 1.405 | +214.96% / +214.48% |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 / 2 | moe_layer | 40 | 0.388 / 0.367 | 0.489 / 0.183 | +25.84% / -49.97% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 / 2 | gdn | 30 | 0.411 / 0.410 | 0.223 / 0.223 | -45.77% / -45.59% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 / 2 | gqa | 10 | 0.653 / 0.652 | 1.441 / 1.441 | +120.74% / +121.00% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 / 2 | moe_layer | 40 | 0.471 / 0.416 | 0.527 / 0.223 | +11.85% / -46.38% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 / 2 | gdn | 30 | 0.371 / 0.366 | 0.183 / 0.183 | -50.55% / -49.83% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 / 2 | gqa | 10 | 0.448 / 0.447 | 1.405 / 1.405 | +213.51% / +214.04% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 / 2 | moe_layer | 40 | 0.390 / 0.369 | 0.489 / 0.183 | +25.25% / -50.32% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 / 2 | gdn | 30 | 0.386 / 0.381 | 0.200 / 0.200 | -48.31% / -47.53% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 / 2 | gqa | 10 | 0.517 / 0.517 | 1.420 / 1.420 | +174.87% / +174.49% |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 / 2 | moe_layer | 40 | 0.419 / 0.384 | 0.505 / 0.200 | +20.50% / -48.05% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 / 2 | gdn | 30 | 0.430 / 0.429 | 0.276 / 0.276 | -35.67% / -35.52% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 / 2 | gqa | 10 | 0.849 / 0.851 | 1.483 / 1.483 | +74.75% / +74.20% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 / 2 | moe_layer | 40 | 0.534 / 0.431 | 0.578 / 0.276 | +8.17% / -35.87% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 / 2 | gdn | 30 | 0.416 / 0.408 | 0.223 / 0.223 | -46.48% / -45.41% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 / 2 | gqa | 10 | 0.636 / 0.636 | 1.441 / 1.441 | +126.42% / +126.59% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 / 2 | moe_layer | 40 | 0.471 / 0.416 | 0.527 / 0.223 | +11.85% / -46.46% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 / 2 | gdn | 30 | 0.390 / 0.382 | 0.200 / 0.200 | -48.75% / -47.74% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 / 2 | gqa | 10 | 0.517 / 0.518 | 1.420 / 1.420 | +174.92% / +174.35% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 / 2 | moe_layer | 40 | 0.421 / 0.387 | 0.505 / 0.200 | +19.80% / -48.35% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 / 2 | gdn | 30 | 0.367 / 0.366 | 0.183 / 0.183 | -49.98% / -49.86% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 / 2 | gqa | 10 | 0.445 / 0.446 | 1.405 / 1.405 | +215.63% / +215.21% |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 / 2 | moe_layer | 40 | 0.386 / 0.367 | 0.489 / 0.183 | +26.52% / -50.01% |
| a3-qwen36-tp4-longctx-p-126976-c1 | 1 / 4 | gdn | 48 | 0.264 / 0.263 | 0.221 / 0.221 | -16.25% / -15.73% |
| a3-qwen36-tp4-longctx-p-126976-c1 | 1 / 4 | gqa | 16 | 0.387 / 0.387 | 2.634 / 2.634 | +581.10% / +579.88% |
| a3-qwen36-tp4-longctx-p-126976-c1 | 1 / 4 | dense_layer | 64 | 0.295 / 0.265 | 0.825 / 0.221 | +179.51% / -16.44% |
| a3-qwen36-tp4-longctx-p-126976-c4 | 4 / 4 | gdn | 48 | 0.313 / 0.312 | 0.257 / 0.257 | -18.06% / -17.83% |
| a3-qwen36-tp4-longctx-p-126976-c4 | 4 / 4 | gqa | 16 | 0.805 / 0.804 | 2.647 / 2.647 | +228.93% / +229.32% |
| a3-qwen36-tp4-longctx-p-126976-c4 | 4 / 4 | dense_layer | 64 | 0.436 / 0.315 | 0.854 / 0.257 | +95.87% / -18.51% |
| a3-qwen36-tp4-longctx-p-65536-c1 | 1 / 4 | gdn | 48 | 0.264 / 0.261 | 0.221 / 0.221 | -16.02% / -15.00% |
| a3-qwen36-tp4-longctx-p-65536-c1 | 1 / 4 | gqa | 16 | 0.334 / 0.330 | 1.442 / 1.442 | +331.60% / +337.34% |
| a3-qwen36-tp4-longctx-p-65536-c1 | 1 / 4 | dense_layer | 64 | 0.281 / 0.264 | 0.527 / 0.221 | +87.21% / -15.97% |
| a3-qwen36-tp4-longctx-p-65536-c4 | 4 / 4 | gdn | 48 | 0.315 / 0.312 | 0.257 / 0.257 | -18.60% / -17.75% |
| a3-qwen36-tp4-longctx-p-65536-c4 | 4 / 4 | gqa | 16 | 0.607 / 0.607 | 1.455 / 1.455 | +139.89% / +139.69% |
| a3-qwen36-tp4-longctx-p-65536-c4 | 4 / 4 | dense_layer | 64 | 0.388 / 0.315 | 0.556 / 0.257 | +43.33% / -18.45% |
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
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | 1 / 1 | kda | 3 | 0.780 / 0.795 | 0.631 / 0.745 | -19.14% / -6.31% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | 1 / 1 | mla | 1 | 1.055 / 1.055 | 0.821 / 0.821 | -22.18% / -22.18% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | 1 / 1 | dense_layer | 1 | 0.813 / 0.813 | 0.403 / 0.403 | -50.44% / -50.44% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c1 | 1 / 1 | moe_layer | 3 | 0.861 / 0.795 | 0.770 / 0.745 | -10.53% / -6.31% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | 12 / 1 | kda | 3 | 0.994 / 1.047 | 0.842 / 1.041 | -15.33% / -0.55% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | 12 / 1 | mla | 1 | 3.938 / 3.938 | 2.423 / 2.423 | -38.49% / -38.49% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | 12 / 1 | dense_layer | 1 | 0.789 / 0.789 | 0.444 / 0.444 | -43.73% / -43.73% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c12 | 12 / 1 | moe_layer | 3 | 2.044 / 1.147 | 1.501 / 1.041 | -26.55% / -9.28% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | 16 / 1 | kda | 3 | 1.103 / 1.204 | 0.848 / 1.047 | -23.19% / -13.06% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | 16 / 1 | mla | 1 | 4.976 / 4.976 | 2.907 / 2.907 | -41.58% / -41.58% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | 16 / 1 | dense_layer | 1 | 0.774 / 0.774 | 0.450 / 0.450 | -41.88% / -41.88% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c16 | 16 / 1 | moe_layer | 3 | 2.504 / 1.333 | 1.667 / 1.047 | -33.45% / -21.49% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | 2 / 1 | kda | 3 | 0.763 / 0.744 | 0.632 / 0.746 | -17.12% / +0.26% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | 2 / 1 | mla | 1 | 1.304 / 1.304 | 0.943 / 0.943 | -27.67% / -27.67% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | 2 / 1 | dense_layer | 1 | 0.698 / 0.698 | 0.404 / 0.404 | -42.10% / -42.10% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c2 | 2 / 1 | moe_layer | 3 | 0.965 / 0.846 | 0.812 / 0.746 | -15.84% / -11.80% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | 24 / 1 | kda | 3 | 1.293 / 1.517 | 1.053 / 1.338 | -18.55% / -11.84% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | 24 / 1 | mla | 1 | 7.084 / 7.084 | 4.144 / 4.144 | -41.50% / -41.50% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | 24 / 1 | dense_layer | 1 | 0.754 / 0.754 | 0.483 / 0.483 | -35.91% / -35.91% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c24 | 24 / 1 | moe_layer | 3 | 3.402 / 1.607 | 2.273 / 1.338 | -33.19% / -16.74% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | 32 / 1 | kda | 3 | 1.496 / 1.813 | 1.251 / 1.620 | -16.41% / -10.67% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | 32 / 1 | mla | 1 | 9.235 / 9.235 | 5.378 / 5.378 | -41.76% / -41.76% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | 32 / 1 | dense_layer | 1 | 0.790 / 0.790 | 0.513 / 0.513 | -35.11% / -35.11% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c32 | 32 / 1 | moe_layer | 3 | 4.311 / 1.886 | 2.873 / 1.620 | -33.37% / -14.10% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | 4 / 1 | kda | 3 | 0.826 / 0.835 | 0.640 / 0.754 | -22.52% / -9.77% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | 4 / 1 | mla | 1 | 1.925 / 1.925 | 1.187 / 1.187 | -38.38% / -38.38% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | 4 / 1 | dense_layer | 1 | 0.719 / 0.719 | 0.412 / 0.412 | -42.72% / -42.72% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c4 | 4 / 1 | moe_layer | 3 | 1.228 / 0.923 | 0.898 / 0.754 | -26.87% / -18.32% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | 48 / 1 | kda | 3 | 1.907 / 2.420 | 1.662 / 2.206 | -12.83% / -8.84% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | 48 / 1 | mla | 1 | 13.351 / 13.351 | 7.862 / 7.862 | -41.11% / -41.11% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | 48 / 1 | dense_layer | 1 | 0.848 / 0.848 | 0.576 / 0.576 | -32.12% / -32.12% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c48 | 48 / 1 | moe_layer | 3 | 6.075 / 2.454 | 4.091 / 2.206 | -32.65% / -10.11% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | 6 / 1 | kda | 3 | 0.861 / 0.829 | 0.643 / 0.757 | -25.25% / -8.61% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | 6 / 1 | mla | 1 | 2.213 / 2.213 | 1.429 / 1.429 | -35.42% / -35.42% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | 6 / 1 | dense_layer | 1 | 0.805 / 0.805 | 0.415 / 0.415 | -48.44% / -48.44% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c6 | 6 / 1 | moe_layer | 3 | 1.330 / 0.948 | 0.981 / 0.757 | -26.22% / -20.11% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | 64 / 1 | kda | 3 | 2.136 / 2.758 | 1.903 / 2.535 | -10.90% / -8.06% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | 64 / 1 | mla | 1 | 17.286 / 17.286 | 10.090 / 10.090 | -41.63% / -41.63% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | 64 / 1 | dense_layer | 1 | 0.871 / 0.871 | 0.639 / 0.639 | -26.64% / -26.64% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c64 | 64 / 1 | moe_layer | 3 | 7.608 / 2.779 | 5.054 / 2.535 | -33.57% / -8.78% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | 8 / 1 | kda | 3 | 0.861 / 0.895 | 0.648 / 0.762 | -24.78% / -14.84% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | 8 / 1 | mla | 1 | 2.883 / 2.883 | 1.671 / 1.671 | -42.03% / -42.03% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | 8 / 1 | dense_layer | 1 | 0.696 / 0.696 | 0.420 / 0.420 | -39.63% / -39.63% |
| a3-kimi4-tp8-longctx-decode-128k-in126k-out3k-c8 | 8 / 1 | moe_layer | 3 | 1.590 / 0.994 | 1.065 / 0.762 | -33.04% / -23.34% |
| a3-kimi4-tp8-longctx-decode-c12-p16k | 12 / 1 | kda | 3 | 0.990 / 1.054 | 0.842 / 1.041 | -14.97% / -1.23% |
| a3-kimi4-tp8-longctx-decode-c12-p16k | 12 / 1 | mla | 1 | 1.464 / 1.464 | 1.160 / 1.160 | -20.79% / -20.79% |
| a3-kimi4-tp8-longctx-decode-c12-p16k | 12 / 1 | dense_layer | 1 | 0.773 / 0.773 | 0.444 / 0.444 | -42.57% / -42.57% |
| a3-kimi4-tp8-longctx-decode-c12-p16k | 12 / 1 | moe_layer | 3 | 1.220 / 1.143 | 1.080 / 1.041 | -11.47% / -8.98% |
| a3-kimi4-tp8-longctx-decode-c12-p32k | 12 / 1 | kda | 3 | 0.961 / 1.056 | 0.842 / 1.041 | -12.44% / -1.47% |
| a3-kimi4-tp8-longctx-decode-c12-p32k | 12 / 1 | mla | 1 | 1.737 / 1.737 | 1.349 / 1.349 | -22.34% / -22.34% |
| a3-kimi4-tp8-longctx-decode-c12-p32k | 12 / 1 | dense_layer | 1 | 0.679 / 0.679 | 0.444 / 0.444 | -34.63% / -34.63% |
| a3-kimi4-tp8-longctx-decode-c12-p32k | 12 / 1 | moe_layer | 3 | 1.314 / 1.149 | 1.143 / 1.041 | -12.98% / -9.40% |
| a3-kimi4-tp8-longctx-decode-c12-p4k | 12 / 1 | kda | 3 | 0.985 / 1.050 | 0.842 / 1.041 | -14.57% / -0.90% |
| a3-kimi4-tp8-longctx-decode-c12-p4k | 12 / 1 | mla | 1 | 1.273 / 1.273 | 1.031 / 1.031 | -19.02% / -19.02% |
| a3-kimi4-tp8-longctx-decode-c12-p4k | 12 / 1 | dense_layer | 1 | 0.763 / 0.763 | 0.444 / 0.444 | -41.83% / -41.83% |
| a3-kimi4-tp8-longctx-decode-c12-p4k | 12 / 1 | moe_layer | 3 | 1.155 / 1.143 | 1.037 / 1.041 | -10.20% / -8.92% |
| a3-kimi4-tp8-longctx-decode-c12-p8k | 12 / 1 | kda | 3 | 0.974 / 1.052 | 0.842 / 1.041 | -13.57% / -1.08% |
| a3-kimi4-tp8-longctx-decode-c12-p8k | 12 / 1 | mla | 1 | 1.326 / 1.326 | 1.065 / 1.065 | -19.66% / -19.66% |
| a3-kimi4-tp8-longctx-decode-c12-p8k | 12 / 1 | dense_layer | 1 | 0.726 / 0.726 | 0.444 / 0.444 | -38.86% / -38.86% |
| a3-kimi4-tp8-longctx-decode-c12-p8k | 12 / 1 | moe_layer | 3 | 1.174 / 1.144 | 1.049 / 1.041 | -10.65% / -9.01% |
| a3-kimi4-tp8-longctx-decode-c24-p16k | 24 / 1 | kda | 3 | 1.320 / 1.515 | 1.053 / 1.338 | -20.24% / -11.70% |
| a3-kimi4-tp8-longctx-decode-c24-p16k | 24 / 1 | mla | 1 | 2.136 / 2.136 | 1.619 / 1.619 | -24.21% / -24.21% |
| a3-kimi4-tp8-longctx-decode-c24-p16k | 24 / 1 | dense_layer | 1 | 0.841 / 0.841 | 0.483 / 0.483 | -42.55% / -42.55% |
| a3-kimi4-tp8-longctx-decode-c24-p16k | 24 / 1 | moe_layer | 3 | 1.752 / 1.604 | 1.431 / 1.338 | -18.28% / -16.61% |
| a3-kimi4-tp8-longctx-decode-c24-p32k | 24 / 1 | kda | 3 | 1.277 / 1.521 | 1.053 / 1.338 | -17.53% / -12.08% |
| a3-kimi4-tp8-longctx-decode-c24-p32k | 24 / 1 | mla | 1 | 2.606 / 2.606 | 1.996 / 1.996 | -23.40% / -23.40% |
| a3-kimi4-tp8-longctx-decode-c24-p32k | 24 / 1 | dense_layer | 1 | 0.722 / 0.722 | 0.483 / 0.483 | -33.08% / -33.08% |
| a3-kimi4-tp8-longctx-decode-c24-p32k | 24 / 1 | moe_layer | 3 | 1.905 / 1.586 | 1.557 / 1.338 | -18.24% / -15.68% |
| a3-kimi4-tp8-longctx-decode-c24-p4k | 24 / 1 | kda | 3 | 1.290 / 1.510 | 1.053 / 1.338 | -18.38% / -11.42% |
| a3-kimi4-tp8-longctx-decode-c24-p4k | 24 / 1 | mla | 1 | 1.771 / 1.771 | 1.361 / 1.361 | -23.15% / -23.15% |
| a3-kimi4-tp8-longctx-decode-c24-p4k | 24 / 1 | dense_layer | 1 | 0.743 / 0.743 | 0.483 / 0.483 | -35.00% / -35.00% |
| a3-kimi4-tp8-longctx-decode-c24-p4k | 24 / 1 | moe_layer | 3 | 1.632 / 1.616 | 1.345 / 1.338 | -17.58% / -17.23% |
| a3-kimi4-tp8-longctx-decode-c24-p8k | 24 / 1 | kda | 3 | 1.316 / 1.512 | 1.053 / 1.338 | -20.02% / -11.52% |
| a3-kimi4-tp8-longctx-decode-c24-p8k | 24 / 1 | mla | 1 | 1.880 / 1.880 | 1.430 / 1.430 | -23.91% / -23.91% |
| a3-kimi4-tp8-longctx-decode-c24-p8k | 24 / 1 | dense_layer | 1 | 0.835 / 0.835 | 0.483 / 0.483 | -42.13% / -42.13% |
| a3-kimi4-tp8-longctx-decode-c24-p8k | 24 / 1 | moe_layer | 3 | 1.664 / 1.602 | 1.368 / 1.338 | -17.79% / -16.52% |
| a3-kimi4-tp8-longctx-decode-c2-p4k | 2 / 1 | kda | 3 | 0.791 / 0.774 | 0.632 / 0.746 | -20.04% / -3.59% |
| a3-kimi4-tp8-longctx-decode-c2-p4k | 2 / 1 | mla | 1 | 0.912 / 0.912 | 0.711 / 0.711 | -22.01% / -22.01% |
| a3-kimi4-tp8-longctx-decode-c2-p4k | 2 / 1 | dense_layer | 1 | 0.774 / 0.774 | 0.404 / 0.404 | -47.77% / -47.77% |
| a3-kimi4-tp8-longctx-decode-c2-p4k | 2 / 1 | moe_layer | 3 | 0.837 / 0.838 | 0.735 / 0.746 | -12.20% / -10.96% |
| a3-kimi4-tp8-longctx-decode-c48-p4k | 48 / 1 | kda | 3 | 1.913 / 2.423 | 1.662 / 2.206 | -13.08% / -8.98% |
| a3-kimi4-tp8-longctx-decode-c48-p4k | 48 / 1 | mla | 1 | 2.733 / 2.733 | 2.295 / 2.295 | -16.03% / -16.03% |
| a3-kimi4-tp8-longctx-decode-c48-p4k | 48 / 1 | dense_layer | 1 | 0.846 / 0.846 | 0.576 / 0.576 | -31.97% / -31.97% |
| a3-kimi4-tp8-longctx-decode-c48-p4k | 48 / 1 | moe_layer | 3 | 2.542 / 2.468 | 2.236 / 2.206 | -12.04% / -10.63% |
| a3-kimi4-tp8-longctx-decode-c6-p4k | 6 / 1 | kda | 3 | 0.887 / 0.857 | 0.643 / 0.757 | -27.48% / -11.63% |
| a3-kimi4-tp8-longctx-decode-c6-p4k | 6 / 1 | mla | 1 | 1.039 / 1.039 | 0.733 / 0.733 | -29.47% / -29.47% |
| a3-kimi4-tp8-longctx-decode-c6-p4k | 6 / 1 | dense_layer | 1 | 0.857 / 0.857 | 0.415 / 0.415 | -51.55% / -51.55% |
| a3-kimi4-tp8-longctx-decode-c6-p4k | 6 / 1 | moe_layer | 3 | 0.948 / 0.951 | 0.749 / 0.757 | -20.96% / -20.34% |
| a3-kimi4-tp8-longctx-decode-c8-p4k | 8 / 1 | kda | 3 | 0.915 / 0.888 | 0.648 / 0.762 | -29.18% / -14.20% |
| a3-kimi4-tp8-longctx-decode-c8-p4k | 8 / 1 | mla | 1 | 1.094 / 1.094 | 0.743 / 0.743 | -32.05% / -32.05% |
| a3-kimi4-tp8-longctx-decode-c8-p4k | 8 / 1 | dense_layer | 1 | 0.842 / 0.842 | 0.420 / 0.420 | -50.14% / -50.14% |
| a3-kimi4-tp8-longctx-decode-c8-p4k | 8 / 1 | moe_layer | 3 | 0.999 / 1.015 | 0.756 / 0.762 | -24.34% / -24.90% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | 1 / 1 | kda | 3 | 0.952 / 0.931 | 0.712 / 0.856 | -25.23% / -8.07% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | 1 / 1 | mla | 1 | 1.236 / 1.236 | 0.932 / 0.932 | -24.59% / -24.59% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | 1 / 1 | dense_layer | 1 | 0.931 / 0.931 | 0.424 / 0.424 | -54.49% / -54.49% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c1 | 1 / 1 | moe_layer | 3 | 1.054 / 0.995 | 0.881 / 0.856 | -16.37% / -14.02% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | 12 / 1 | kda | 3 | 1.008 / 0.971 | 0.733 / 0.877 | -27.27% / -9.67% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | 12 / 1 | mla | 1 | 3.842 / 3.842 | 2.271 / 2.271 | -40.90% / -40.90% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | 12 / 1 | dense_layer | 1 | 0.971 / 0.971 | 0.445 / 0.445 | -54.18% / -54.18% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c12 | 12 / 1 | moe_layer | 3 | 1.965 / 1.118 | 1.341 / 0.877 | -31.72% / -21.54% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | 16 / 1 | kda | 3 | 1.039 / 0.981 | 0.737 / 0.881 | -28.99% / -10.16% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | 16 / 1 | mla | 1 | 4.724 / 4.724 | 2.754 / 2.754 | -41.69% / -41.69% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | 16 / 1 | dense_layer | 1 | 0.971 / 0.971 | 0.449 / 0.449 | -53.72% / -53.72% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c16 | 16 / 1 | moe_layer | 3 | 2.289 / 1.163 | 1.506 / 0.881 | -34.23% / -24.23% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | 2 / 1 | kda | 3 | 0.956 / 0.936 | 0.713 / 0.857 | -25.45% / -8.45% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | 2 / 1 | mla | 1 | 1.493 / 1.493 | 1.054 / 1.054 | -29.40% / -29.40% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | 2 / 1 | dense_layer | 1 | 0.936 / 0.936 | 0.425 / 0.425 | -54.62% / -54.62% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c2 | 2 / 1 | moe_layer | 3 | 1.142 / 1.004 | 0.923 / 0.857 | -19.20% / -14.62% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | 24 / 1 | kda | 3 | 1.121 / 1.115 | 0.936 / 1.165 | -16.52% / +4.50% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | 24 / 1 | mla | 1 | 6.698 / 6.698 | 3.995 / 3.995 | -40.36% / -40.36% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | 24 / 1 | dense_layer | 1 | 0.884 / 0.884 | 0.478 / 0.478 | -45.98% / -45.98% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c24 | 24 / 1 | moe_layer | 3 | 3.059 / 1.364 | 2.108 / 1.165 | -31.08% / -14.61% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | 32 / 1 | kda | 3 | 1.230 / 1.218 | 0.950 / 1.179 | -22.73% / -3.14% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | 32 / 1 | mla | 1 | 8.605 / 8.605 | 4.965 / 4.965 | -42.30% / -42.30% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | 32 / 1 | dense_layer | 1 | 0.985 / 0.985 | 0.492 / 0.492 | -50.05% / -50.05% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c32 | 32 / 1 | moe_layer | 3 | 3.770 / 1.487 | 2.441 / 1.179 | -35.24% / -20.68% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | 4 / 1 | kda | 3 | 0.983 / 0.958 | 0.715 / 0.859 | -27.25% / -10.34% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | 4 / 1 | mla | 1 | 2.057 / 2.057 | 1.297 / 1.297 | -36.94% / -36.94% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | 4 / 1 | dense_layer | 1 | 0.958 / 0.958 | 0.427 / 0.427 | -55.42% / -55.42% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c4 | 4 / 1 | moe_layer | 3 | 1.350 / 1.051 | 1.005 / 0.859 | -25.51% / -18.25% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | 48 / 1 | kda | 3 | 1.418 / 1.515 | 1.169 / 1.484 | -17.61% / -2.03% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | 48 / 1 | mla | 1 | 12.478 / 12.478 | 7.180 / 7.180 | -42.46% / -42.46% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | 48 / 1 | dense_layer | 1 | 1.007 / 1.007 | 0.538 / 0.538 | -46.56% / -46.56% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c48 | 48 / 1 | moe_layer | 3 | 5.242 / 1.734 | 3.382 / 1.484 | -35.47% / -14.42% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | 6 / 1 | kda | 3 | 0.984 / 0.944 | 0.720 / 0.864 | -26.77% / -8.42% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | 6 / 1 | mla | 1 | 2.312 / 2.312 | 1.542 / 1.542 | -33.31% / -33.31% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | 6 / 1 | dense_layer | 1 | 0.944 / 0.944 | 0.432 / 0.432 | -54.19% / -54.19% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c6 | 6 / 1 | moe_layer | 3 | 1.440 / 1.068 | 1.090 / 0.864 | -24.28% / -19.08% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | 64 / 1 | kda | 3 | 1.540 / 1.702 | 1.302 / 1.663 | -15.49% / -2.33% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | 64 / 1 | mla | 1 | 16.320 / 16.320 | 9.272 / 9.272 | -43.19% / -43.19% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | 64 / 1 | dense_layer | 1 | 0.991 / 0.991 | 0.580 / 0.580 | -41.45% / -41.45% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c64 | 64 / 1 | moe_layer | 3 | 6.650 / 1.928 | 4.199 / 1.663 | -36.86% / -13.76% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | 8 / 1 | kda | 3 | 0.977 / 0.947 | 0.725 / 0.869 | -25.79% / -8.29% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | 8 / 1 | mla | 1 | 2.934 / 2.934 | 1.784 / 1.784 | -39.21% / -39.21% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | 8 / 1 | dense_layer | 1 | 0.912 / 0.912 | 0.437 / 0.437 | -52.13% / -52.13% |
| a3-kimi4-tp16-128k-decode-128k-in126k-out3k-c8 | 8 / 1 | moe_layer | 3 | 1.651 / 1.070 | 1.174 / 0.869 | -28.89% / -18.84% |
| a3-kimi4-tp16-128k-decode-c12-p16k | 12 / 1 | kda | 3 | 1.022 / 1.012 | 0.733 / 0.877 | -28.31% / -13.35% |
| a3-kimi4-tp16-128k-decode-c12-p16k | 12 / 1 | mla | 1 | 1.363 / 1.363 | 1.008 / 1.008 | -26.07% / -26.07% |
| a3-kimi4-tp16-128k-decode-c12-p16k | 12 / 1 | dense_layer | 1 | 1.012 / 1.012 | 0.445 / 0.445 | -56.05% / -56.05% |
| a3-kimi4-tp16-128k-decode-c12-p16k | 12 / 1 | moe_layer | 3 | 1.139 / 1.094 | 0.920 / 0.877 | -19.21% / -19.85% |
| a3-kimi4-tp16-128k-decode-c12-p32k | 12 / 1 | kda | 3 | 0.998 / 0.970 | 0.733 / 0.877 | -26.54% / -9.63% |
| a3-kimi4-tp16-128k-decode-c12-p32k | 12 / 1 | mla | 1 | 1.665 / 1.665 | 1.196 / 1.196 | -28.16% / -28.16% |
| a3-kimi4-tp16-128k-decode-c12-p32k | 12 / 1 | dense_layer | 1 | 0.970 / 0.970 | 0.445 / 0.445 | -54.16% / -54.16% |
| a3-kimi4-tp16-128k-decode-c12-p32k | 12 / 1 | moe_layer | 3 | 1.229 / 1.071 | 0.983 / 0.877 | -20.01% / -18.14% |
| a3-kimi4-tp16-128k-decode-c12-p4k | 12 / 1 | kda | 3 | 1.008 / 0.965 | 0.733 / 0.877 | -27.29% / -9.18% |
| a3-kimi4-tp16-128k-decode-c12-p4k | 12 / 1 | mla | 1 | 1.415 / 1.415 | 0.879 / 0.879 | -37.88% / -37.88% |
| a3-kimi4-tp16-128k-decode-c12-p4k | 12 / 1 | dense_layer | 1 | 0.965 / 0.965 | 0.445 / 0.445 | -53.93% / -53.93% |
| a3-kimi4-tp16-128k-decode-c12-p4k | 12 / 1 | moe_layer | 3 | 1.158 / 1.110 | 0.877 / 0.877 | -24.20% / -21.03% |
| a3-kimi4-tp16-128k-decode-c12-p8k | 12 / 1 | kda | 3 | 1.003 / 0.956 | 0.733 / 0.877 | -26.92% / -8.29% |
| a3-kimi4-tp16-128k-decode-c12-p8k | 12 / 1 | mla | 1 | 1.370 / 1.370 | 0.913 / 0.913 | -33.33% / -33.33% |
| a3-kimi4-tp16-128k-decode-c12-p8k | 12 / 1 | dense_layer | 1 | 0.951 / 0.951 | 0.445 / 0.445 | -53.24% / -53.24% |
| a3-kimi4-tp16-128k-decode-c12-p8k | 12 / 1 | moe_layer | 3 | 1.142 / 1.101 | 0.889 / 0.877 | -22.18% / -20.35% |
| a3-kimi4-tp16-128k-decode-c24-p16k | 24 / 1 | kda | 3 | 1.122 / 1.109 | 0.936 / 1.165 | -16.56% / +5.05% |
| a3-kimi4-tp16-128k-decode-c24-p16k | 24 / 1 | mla | 1 | 1.893 / 1.893 | 1.469 / 1.469 | -22.41% / -22.41% |
| a3-kimi4-tp16-128k-decode-c24-p16k | 24 / 1 | dense_layer | 1 | 0.914 / 0.914 | 0.478 / 0.478 | -47.77% / -47.77% |
| a3-kimi4-tp16-128k-decode-c24-p16k | 24 / 1 | moe_layer | 3 | 1.448 / 1.342 | 1.266 / 1.165 | -12.54% / -13.17% |
| a3-kimi4-tp16-128k-decode-c24-p32k | 24 / 1 | kda | 3 | 1.139 / 1.121 | 0.936 / 1.165 | -17.81% / +3.96% |
| a3-kimi4-tp16-128k-decode-c24-p32k | 24 / 1 | mla | 1 | 2.244 / 2.244 | 1.847 / 1.847 | -17.73% / -17.73% |
| a3-kimi4-tp16-128k-decode-c24-p32k | 24 / 1 | dense_layer | 1 | 0.934 / 0.934 | 0.478 / 0.478 | -48.87% / -48.87% |
| a3-kimi4-tp16-128k-decode-c24-p32k | 24 / 1 | moe_layer | 3 | 1.575 / 1.361 | 1.392 / 1.165 | -11.63% / -14.41% |
| a3-kimi4-tp16-128k-decode-c24-p4k | 24 / 1 | kda | 3 | 1.141 / 1.111 | 0.936 / 1.165 | -18.00% / +4.88% |
| a3-kimi4-tp16-128k-decode-c24-p4k | 24 / 1 | mla | 1 | 4.657 / 4.657 | 1.211 / 1.211 | -73.99% / -73.99% |
| a3-kimi4-tp16-128k-decode-c24-p4k | 24 / 1 | dense_layer | 1 | 0.961 / 0.961 | 0.478 / 0.478 | -50.29% / -50.29% |
| a3-kimi4-tp16-128k-decode-c24-p4k | 24 / 1 | moe_layer | 3 | 2.374 / 1.352 | 1.181 / 1.165 | -50.26% / -13.85% |
| a3-kimi4-tp16-128k-decode-c24-p8k | 24 / 1 | kda | 3 | 1.137 / 1.123 | 0.936 / 1.165 | -17.71% / +3.77% |
| a3-kimi4-tp16-128k-decode-c24-p8k | 24 / 1 | mla | 1 | 1.526 / 1.526 | 1.280 / 1.280 | -16.09% / -16.09% |
| a3-kimi4-tp16-128k-decode-c24-p8k | 24 / 1 | dense_layer | 1 | 0.946 / 0.946 | 0.478 / 0.478 | -49.52% / -49.52% |
| a3-kimi4-tp16-128k-decode-c24-p8k | 24 / 1 | moe_layer | 3 | 1.331 / 1.343 | 1.204 / 1.165 | -9.55% / -13.25% |
| a3-kimi4-tp16-128k-decode-c2-p4k | 2 / 1 | kda | 3 | 0.969 / 0.954 | 0.713 / 0.857 | -26.42% / -10.19% |
| a3-kimi4-tp16-128k-decode-c2-p4k | 2 / 1 | mla | 1 | 1.148 / 1.148 | 0.822 / 0.822 | -28.42% / -28.42% |
| a3-kimi4-tp16-128k-decode-c2-p4k | 2 / 1 | dense_layer | 1 | 0.954 / 0.954 | 0.425 / 0.425 | -55.48% / -55.48% |
| a3-kimi4-tp16-128k-decode-c2-p4k | 2 / 1 | moe_layer | 3 | 1.034 / 1.019 | 0.845 / 0.857 | -18.22% / -15.93% |
| a3-kimi4-tp16-128k-decode-c48-p4k | 48 / 1 | kda | 3 | 1.425 / 1.510 | 1.169 / 1.484 | -18.00% / -1.75% |
| a3-kimi4-tp16-128k-decode-c48-p4k | 48 / 1 | mla | 1 | 1.925 / 1.925 | 1.613 / 1.613 | -16.23% / -16.23% |
| a3-kimi4-tp16-128k-decode-c48-p4k | 48 / 1 | dense_layer | 1 | 1.011 / 1.011 | 0.538 / 0.538 | -46.77% / -46.77% |
| a3-kimi4-tp16-128k-decode-c48-p4k | 48 / 1 | moe_layer | 3 | 1.730 / 1.754 | 1.527 / 1.484 | -11.74% / -15.41% |
| a3-kimi4-tp16-128k-decode-c6-p4k | 6 / 1 | kda | 3 | 0.981 / 0.951 | 0.720 / 0.864 | -26.55% / -9.12% |
| a3-kimi4-tp16-128k-decode-c6-p4k | 6 / 1 | mla | 1 | 1.167 / 1.167 | 0.846 / 0.846 | -27.50% / -27.50% |
| a3-kimi4-tp16-128k-decode-c6-p4k | 6 / 1 | dense_layer | 1 | 0.937 / 0.937 | 0.432 / 0.432 | -53.85% / -53.85% |
| a3-kimi4-tp16-128k-decode-c6-p4k | 6 / 1 | moe_layer | 3 | 1.057 / 1.054 | 0.858 / 0.864 | -18.84% / -18.01% |
| a3-kimi4-tp16-128k-decode-c8-p4k | 8 / 1 | kda | 3 | 1.013 / 0.983 | 0.725 / 0.869 | -28.49% / -11.64% |
| a3-kimi4-tp16-128k-decode-c8-p4k | 8 / 1 | mla | 1 | 1.147 / 1.147 | 0.856 / 0.856 | -25.36% / -25.36% |
| a3-kimi4-tp16-128k-decode-c8-p4k | 8 / 1 | dense_layer | 1 | 0.983 / 0.983 | 0.437 / 0.437 | -55.59% / -55.59% |
| a3-kimi4-tp16-128k-decode-c8-p4k | 8 / 1 | moe_layer | 3 | 1.068 / 1.092 | 0.864 / 0.869 | -19.05% / -20.47% |
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
| a3-v41-tp4dp4-128k-c48 | 13 / 8 | mla | 40 | 1.849 / 1.392 | 1.596 / 1.459 | -13.69% / +4.76% |
| a3-v41-tp4dp4-128k-c48 | 13 / 8 | moe_layer | 40 | 1.849 / 1.392 | 1.596 / 1.459 | -13.69% / +4.76% |
| a3-v41-tp4dp4-128k-c64 | 17 / 8 | mla | 40 | 1.936 / 1.475 | 1.728 / 1.553 | -10.76% / +5.27% |
| a3-v41-tp4dp4-128k-c64 | 17 / 8 | moe_layer | 40 | 1.936 / 1.475 | 1.728 / 1.553 | -10.76% / +5.27% |
| a3-v41-tp4dp4-128k-c8 | 3 / 8 | mla | 40 | 1.339 / 1.163 | 1.297 / 1.255 | -3.12% / +7.93% |
| a3-v41-tp4dp4-128k-c8 | 3 / 8 | moe_layer | 40 | 1.339 / 1.163 | 1.297 / 1.255 | -3.12% / +7.93% |
| a3-qwen35-tp4-decode-c1-p126000 | 1 / 4 | gdn | 30 | 0.407 / 0.407 | 0.218 / 0.218 | -46.39% / -46.30% |
| a3-qwen35-tp4-decode-c1-p126000 | 1 / 4 | gqa | 10 | 0.526 / 0.526 | 2.604 / 2.604 | +395.13% / +394.84% |
| a3-qwen35-tp4-decode-c1-p126000 | 1 / 4 | moe_layer | 40 | 0.437 / 0.410 | 0.815 / 0.218 | +86.49% / -46.74% |
| a3-qwen35-tp4-decode-c12-p126000 | 12 / 4 | gdn | 30 | 0.654 / 0.652 | 0.469 / 0.469 | -28.30% / -28.01% |
| a3-qwen35-tp4-decode-c12-p126000 | 12 / 4 | gqa | 10 | 1.652 / 1.649 | 2.810 / 2.810 | +70.13% / +70.40% |
| a3-qwen35-tp4-decode-c12-p126000 | 12 / 4 | moe_layer | 40 | 0.904 / 0.658 | 1.054 / 0.469 | +16.68% / -28.68% |
| a3-qwen35-tp4-decode-c16-p126000 | 16 / 4 | gdn | 30 | 0.688 / 0.687 | 0.498 / 0.498 | -27.67% / -27.55% |
| a3-qwen35-tp4-decode-c16-p126000 | 16 / 4 | gqa | 10 | 1.999 / 1.996 | 2.817 / 2.817 | +40.93% / +41.08% |
| a3-qwen35-tp4-decode-c16-p126000 | 16 / 4 | moe_layer | 40 | 1.016 / 0.692 | 1.077 / 0.498 | +6.08% / -28.13% |
| a3-qwen35-tp4-decode-c2-p126000 | 2 / 4 | gdn | 30 | 0.447 / 0.443 | 0.247 / 0.247 | -44.66% / -44.20% |
| a3-qwen35-tp4-decode-c2-p126000 | 2 / 4 | gqa | 10 | 0.615 / 0.615 | 2.632 / 2.632 | +327.95% / +327.74% |
| a3-qwen35-tp4-decode-c2-p126000 | 2 / 4 | moe_layer | 40 | 0.489 / 0.447 | 0.844 / 0.247 | +72.51% / -44.62% |
| a3-qwen35-tp4-decode-c24-p126000 | 24 / 4 | gdn | 30 | 0.744 / 0.740 | 0.550 / 0.550 | -26.00% / -25.63% |
| a3-qwen35-tp4-decode-c24-p126000 | 24 / 4 | gqa | 10 | 4.115 / 4.114 | 5.281 / 5.281 | +28.33% / +28.38% |
| a3-qwen35-tp4-decode-c24-p126000 | 24 / 4 | moe_layer | 40 | 1.587 / 0.745 | 1.733 / 0.550 | +9.23% / -26.14% |
| a3-qwen35-tp4-decode-c32-p126000 | 32 / 4 | gdn | 30 | 0.794 / 0.790 | 0.614 / 0.614 | -22.64% / -22.29% |
| a3-qwen35-tp4-decode-c32-p126000 | 32 / 4 | gqa | 10 | 4.151 / 4.146 | 5.302 / 5.302 | +27.75% / +27.90% |
| a3-qwen35-tp4-decode-c32-p126000 | 32 / 4 | moe_layer | 40 | 1.633 / 0.798 | 1.786 / 0.614 | +9.38% / -23.07% |
| a3-qwen35-tp4-decode-c4-p126000 | 4 / 4 | gdn | 30 | 0.481 / 0.482 | 0.307 / 0.307 | -36.13% / -36.34% |
| a3-qwen35-tp4-decode-c4-p126000 | 4 / 4 | gqa | 10 | 0.842 / 0.843 | 2.687 / 2.687 | +219.02% / +218.76% |
| a3-qwen35-tp4-decode-c4-p126000 | 4 / 4 | moe_layer | 40 | 0.571 / 0.484 | 0.902 / 0.307 | +57.94% / -36.59% |
| a3-qwen35-tp4-decode-c6-p126000 | 6 / 4 | gdn | 30 | 0.558 / 0.555 | 0.382 / 0.382 | -31.65% / -31.28% |
| a3-qwen35-tp4-decode-c6-p126000 | 6 / 4 | gqa | 10 | 1.079 / 1.075 | 2.746 / 2.746 | +154.57% / +155.39% |
| a3-qwen35-tp4-decode-c6-p126000 | 6 / 4 | moe_layer | 40 | 0.688 / 0.558 | 0.973 / 0.382 | +41.28% / -31.62% |
| a3-qwen35-tp4-decode-c8-p126000 | 8 / 4 | gdn | 30 | 0.601 / 0.600 | 0.440 / 0.440 | -26.79% / -26.67% |
| a3-qwen35-tp4-decode-c8-p126000 | 8 / 4 | gqa | 10 | 1.294 / 1.292 | 2.801 / 2.801 | +116.43% / +116.77% |
| a3-qwen35-tp4-decode-c8-p126000 | 8 / 4 | moe_layer | 40 | 0.775 / 0.603 | 1.030 / 0.440 | +33.03% / -26.94% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gdn | 30 | 0.659 / 0.657 | 0.469 / 0.469 | -28.76% / -28.63% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gqa | 10 | 0.813 / 0.813 | 0.842 / 0.842 | +3.52% / +3.54% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | moe_layer | 40 | 0.697 / 0.664 | 0.562 / 0.469 | -19.35% / -29.32% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gdn | 30 | 0.658 / 0.656 | 0.469 / 0.469 | -28.67% / -28.43% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gqa | 10 | 0.785 / 0.786 | 0.842 / 0.842 | +7.25% / +7.08% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | moe_layer | 40 | 0.689 / 0.663 | 0.562 / 0.469 | -18.45% / -29.22% |
| a3-qwen35-tp4-decode-c12-p24512 | 4 / 4 | gdn | 30 | 0.489 / 0.482 | 0.307 / 0.307 | -37.16% / -36.31% |
| a3-qwen35-tp4-decode-c12-p24512 | 4 / 4 | gqa | 10 | 0.547 / 0.550 | 0.719 / 0.719 | +31.25% / +30.69% |
| a3-qwen35-tp4-decode-c12-p24512 | 4 / 4 | moe_layer | 40 | 0.503 / 0.489 | 0.410 / 0.307 | -18.56% / -37.16% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gdn | 30 | 0.637 / 0.637 | 0.469 / 0.469 | -26.31% / -26.34% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gqa | 10 | 0.761 / 0.760 | 0.842 / 0.842 | +10.61% / +10.72% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | moe_layer | 40 | 0.668 / 0.641 | 0.562 / 0.469 | -15.79% / -26.83% |
| a3-qwen35-tp4-decode-c12-p24512 | 6 / 4 | gdn | 30 | 0.544 / 0.542 | 0.382 / 0.382 | -29.79% / -29.54% |
| a3-qwen35-tp4-decode-c12-p24512 | 6 / 4 | gqa | 10 | 0.622 / 0.622 | 0.778 / 0.778 | +24.95% / +24.96% |
| a3-qwen35-tp4-decode-c12-p24512 | 6 / 4 | moe_layer | 40 | 0.563 / 0.550 | 0.481 / 0.382 | -14.67% / -30.56% |
| a3-qwen35-tp4-decode-c12-p24512 | 3 / 4 | gdn | 30 | 0.471 / 0.471 | 0.277 / 0.277 | -41.30% / -41.27% |
| a3-qwen35-tp4-decode-c12-p24512 | 3 / 4 | gqa | 10 | 0.517 / 0.517 | 0.691 / 0.691 | +33.53% / +33.55% |
| a3-qwen35-tp4-decode-c12-p24512 | 3 / 4 | moe_layer | 40 | 0.483 / 0.474 | 0.380 / 0.277 | -21.26% / -41.61% |
| a3-qwen35-tp4-decode-c12-p24512 | 2 / 4 | gdn | 30 | 0.449 / 0.444 | 0.247 / 0.247 | -44.87% / -44.26% |
| a3-qwen35-tp4-decode-c12-p24512 | 2 / 4 | gqa | 10 | 0.476 / 0.477 | 0.664 / 0.664 | +39.52% / +39.05% |
| a3-qwen35-tp4-decode-c12-p24512 | 2 / 4 | moe_layer | 40 | 0.455 / 0.447 | 0.351 / 0.247 | -22.83% / -44.69% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gdn | 30 | 0.640 / 0.639 | 0.469 / 0.469 | -26.72% / -26.62% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | gqa | 10 | 0.808 / 0.803 | 0.842 / 0.842 | +4.11% / +4.81% |
| a3-qwen35-tp4-decode-c12-p24512 | 12 / 4 | moe_layer | 40 | 0.682 / 0.643 | 0.562 / 0.469 | -17.59% / -27.05% |
| a3-qwen35-tp4-decode-c12-p24512 | 8 / 4 | gdn | 30 | 0.608 / 0.599 | 0.440 / 0.440 | -27.54% / -26.54% |
| a3-qwen35-tp4-decode-c12-p24512 | 8 / 4 | gqa | 10 | 0.698 / 0.698 | 0.832 / 0.832 | +19.35% / +19.29% |
| a3-qwen35-tp4-decode-c12-p24512 | 8 / 4 | moe_layer | 40 | 0.630 / 0.606 | 0.538 / 0.440 | -14.57% / -27.39% |
| a3-qwen35-tp4-decode-c12-p24512 | 1 / 4 | gdn | 30 | 0.406 / 0.404 | 0.218 / 0.218 | -46.24% / -45.94% |
| a3-qwen35-tp4-decode-c12-p24512 | 1 / 4 | gqa | 10 | 0.423 / 0.426 | 0.636 / 0.636 | +50.31% / +49.44% |
| a3-qwen35-tp4-decode-c12-p24512 | 1 / 4 | moe_layer | 40 | 0.410 / 0.406 | 0.323 / 0.218 | -21.34% / -46.27% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gdn | 30 | 0.661 / 0.656 | 0.469 / 0.469 | -29.06% / -28.47% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gqa | 10 | 1.068 / 1.068 | 1.617 / 1.617 | +51.41% / +51.43% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | moe_layer | 40 | 0.763 / 0.664 | 0.756 / 0.469 | -0.89% / -29.37% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gdn | 30 | 0.659 / 0.656 | 0.469 / 0.469 | -28.78% / -28.51% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gqa | 10 | 1.003 / 1.005 | 1.617 / 1.617 | +61.21% / +60.95% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | moe_layer | 40 | 0.745 / 0.663 | 0.756 / 0.469 | +1.52% / -29.22% |
| a3-qwen35-tp4-decode-c12-p64512 | 2 / 4 | gdn | 30 | 0.445 / 0.443 | 0.247 / 0.247 | -44.39% / -44.12% |
| a3-qwen35-tp4-decode-c12-p64512 | 2 / 4 | gqa | 10 | 0.528 / 0.528 | 1.439 / 1.439 | +172.74% / +172.77% |
| a3-qwen35-tp4-decode-c12-p64512 | 2 / 4 | moe_layer | 40 | 0.466 / 0.445 | 0.545 / 0.247 | +17.14% / -44.46% |
| a3-qwen35-tp4-decode-c12-p64512 | 1 / 4 | gdn | 30 | 0.414 / 0.406 | 0.218 / 0.218 | -47.20% / -46.16% |
| a3-qwen35-tp4-decode-c12-p64512 | 1 / 4 | gqa | 10 | 0.470 / 0.471 | 1.412 / 1.412 | +200.59% / +199.91% |
| a3-qwen35-tp4-decode-c12-p64512 | 1 / 4 | moe_layer | 40 | 0.428 / 0.407 | 0.517 / 0.218 | +20.85% / -46.34% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gdn | 30 | 0.642 / 0.641 | 0.469 / 0.469 | -26.87% / -26.82% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | gqa | 10 | 1.088 / 1.090 | 1.617 / 1.617 | +48.63% / +48.36% |
| a3-qwen35-tp4-decode-c12-p64512 | 12 / 4 | moe_layer | 40 | 0.753 / 0.645 | 0.756 / 0.469 | +0.40% / -27.23% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | gdn | 30 | 0.604 / 0.603 | 0.440 / 0.440 | -27.10% / -26.93% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | gqa | 10 | 0.900 / 0.900 | 1.608 / 1.608 | +78.67% / +78.64% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | moe_layer | 40 | 0.678 / 0.606 | 0.732 / 0.440 | +8.01% / -27.40% |
| a3-qwen35-tp4-decode-c12-p64512 | 4 / 4 | gdn | 30 | 0.491 / 0.483 | 0.307 / 0.307 | -37.45% / -36.43% |
| a3-qwen35-tp4-decode-c12-p64512 | 4 / 4 | gqa | 10 | 0.654 / 0.651 | 1.494 / 1.494 | +128.49% / +129.63% |
| a3-qwen35-tp4-decode-c12-p64512 | 4 / 4 | moe_layer | 40 | 0.532 / 0.487 | 0.604 / 0.307 | +13.58% / -36.95% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | gdn | 30 | 0.602 / 0.602 | 0.440 / 0.440 | -26.84% / -26.88% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | gqa | 10 | 0.856 / 0.848 | 1.608 / 1.608 | +87.80% / +89.70% |
| a3-qwen35-tp4-decode-c12-p64512 | 8 / 4 | moe_layer | 40 | 0.665 / 0.605 | 0.732 / 0.440 | +10.04% / -27.19% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | gdn | 30 | 0.560 / 0.560 | 0.382 / 0.382 | -31.79% / -31.88% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | gqa | 10 | 0.765 / 0.764 | 1.553 / 1.553 | +103.04% / +103.28% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | moe_layer | 40 | 0.611 / 0.563 | 0.675 / 0.382 | +10.42% / -32.18% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | gdn | 30 | 0.547 / 0.544 | 0.382 / 0.382 | -30.24% / -29.86% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | gqa | 10 | 0.759 / 0.759 | 1.553 / 1.553 | +104.68% / +104.59% |
| a3-qwen35-tp4-decode-c12-p64512 | 6 / 4 | moe_layer | 40 | 0.600 / 0.546 | 0.675 / 0.382 | +12.42% / -30.08% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gdn | 30 | 0.662 / 0.660 | 0.469 / 0.469 | -29.13% / -28.88% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gqa | 10 | 0.755 / 0.754 | 0.531 / 0.531 | -29.60% / -29.51% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | moe_layer | 40 | 0.685 / 0.663 | 0.485 / 0.469 | -29.26% / -29.22% |
| a3-qwen35-tp4-decode-c12-p8512 | 8 / 4 | gdn | 30 | 0.613 / 0.602 | 0.440 / 0.440 | -28.20% / -26.82% |
| a3-qwen35-tp4-decode-c12-p8512 | 8 / 4 | gqa | 10 | 0.642 / 0.644 | 0.522 / 0.522 | -18.72% / -18.86% |
| a3-qwen35-tp4-decode-c12-p8512 | 8 / 4 | moe_layer | 40 | 0.620 / 0.604 | 0.461 / 0.440 | -25.74% / -27.12% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gdn | 30 | 0.640 / 0.640 | 0.469 / 0.469 | -26.66% / -26.67% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gqa | 10 | 0.751 / 0.752 | 0.531 / 0.531 | -29.26% / -29.32% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | moe_layer | 40 | 0.668 / 0.642 | 0.485 / 0.469 | -27.39% / -26.94% |
| a3-qwen35-tp4-decode-c12-p8512 | 1 / 4 | gdn | 30 | 0.413 / 0.405 | 0.218 / 0.218 | -47.09% / -46.06% |
| a3-qwen35-tp4-decode-c12-p8512 | 1 / 4 | gqa | 10 | 0.407 / 0.408 | 0.326 / 0.326 | -19.95% / -20.17% |
| a3-qwen35-tp4-decode-c12-p8512 | 1 / 4 | moe_layer | 40 | 0.411 / 0.406 | 0.245 / 0.218 | -40.37% / -46.19% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gdn | 30 | 0.637 / 0.635 | 0.469 / 0.469 | -26.31% / -26.11% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | gqa | 10 | 0.744 / 0.740 | 0.531 / 0.531 | -28.62% / -28.21% |
| a3-qwen35-tp4-decode-c12-p8512 | 12 / 4 | moe_layer | 40 | 0.664 / 0.643 | 0.485 / 0.469 | -26.96% / -26.98% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | gdn | 30 | 0.559 / 0.546 | 0.382 / 0.382 | -31.76% / -30.11% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | gqa | 10 | 0.577 / 0.577 | 0.467 / 0.467 | -19.03% / -18.95% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | moe_layer | 40 | 0.564 / 0.550 | 0.403 / 0.382 | -28.50% / -30.59% |
| a3-qwen35-tp4-decode-c12-p8512 | 2 / 4 | gdn | 30 | 0.460 / 0.444 | 0.247 / 0.247 | -46.22% / -44.24% |
| a3-qwen35-tp4-decode-c12-p8512 | 2 / 4 | gqa | 10 | 0.448 / 0.451 | 0.353 / 0.353 | -21.04% / -21.54% |
| a3-qwen35-tp4-decode-c12-p8512 | 2 / 4 | moe_layer | 40 | 0.457 / 0.446 | 0.274 / 0.247 | -40.05% / -44.50% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | gdn | 30 | 0.566 / 0.558 | 0.382 / 0.382 | -32.53% / -31.61% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | gqa | 10 | 0.590 / 0.591 | 0.467 / 0.467 | -20.75% / -20.91% |
| a3-qwen35-tp4-decode-c12-p8512 | 6 / 4 | moe_layer | 40 | 0.572 / 0.564 | 0.403 / 0.382 | -29.49% / -32.33% |
| a3-qwen35-tp4-decode-c12-p8512 | 4 / 4 | gdn | 30 | 0.501 / 0.486 | 0.307 / 0.307 | -38.74% / -36.88% |
| a3-qwen35-tp4-decode-c12-p8512 | 4 / 4 | gqa | 10 | 0.506 / 0.503 | 0.408 / 0.408 | -19.28% / -18.77% |
| a3-qwen35-tp4-decode-c12-p8512 | 4 / 4 | moe_layer | 40 | 0.502 / 0.490 | 0.332 / 0.307 | -33.84% / -37.36% |
| a3-qwen35-tp4-decode-c12-p8512 | 3 / 4 | gdn | 30 | 0.498 / 0.473 | 0.277 / 0.277 | -44.41% / -41.49% |
| a3-qwen35-tp4-decode-c12-p8512 | 3 / 4 | gqa | 10 | 0.491 / 0.490 | 0.381 / 0.381 | -22.53% / -22.39% |
| a3-qwen35-tp4-decode-c12-p8512 | 3 / 4 | moe_layer | 40 | 0.496 / 0.475 | 0.303 / 0.277 | -38.99% / -41.70% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gdn | 30 | 0.661 / 0.654 | 0.469 / 0.469 | -29.06% / -28.27% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gqa | 10 | 1.330 / 1.333 | 2.238 / 2.238 | +68.30% / +67.88% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | moe_layer | 40 | 0.828 / 0.660 | 0.911 / 0.469 | +10.00% / -28.96% |
| a3-qwen35-tp4-decode-c12-p96512 | 2 / 4 | gdn | 30 | 0.443 / 0.444 | 0.247 / 0.247 | -44.22% / -44.30% |
| a3-qwen35-tp4-decode-c12-p96512 | 2 / 4 | gqa | 10 | 0.576 / 0.578 | 2.060 / 2.060 | +257.55% / +256.64% |
| a3-qwen35-tp4-decode-c12-p96512 | 2 / 4 | moe_layer | 40 | 0.477 / 0.446 | 0.701 / 0.247 | +46.97% / -44.58% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gdn | 30 | 0.657 / 0.653 | 0.469 / 0.469 | -28.56% / -28.15% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gqa | 10 | 1.242 / 1.240 | 2.238 / 2.238 | +80.20% / +80.42% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | moe_layer | 40 | 0.803 / 0.662 | 0.911 / 0.469 | +13.49% / -29.17% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | gdn | 30 | 0.541 / 0.540 | 0.382 / 0.382 | -29.46% / -29.27% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | gqa | 10 | 0.863 / 0.863 | 2.174 / 2.174 | +151.85% / +151.95% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | moe_layer | 40 | 0.622 / 0.545 | 0.830 / 0.382 | +33.48% / -29.90% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gdn | 30 | 0.641 / 0.634 | 0.469 / 0.469 | -26.83% / -26.02% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gqa | 10 | 1.320 / 1.318 | 2.238 / 2.238 | +69.54% / +69.83% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | moe_layer | 40 | 0.811 / 0.642 | 0.911 / 0.469 | +12.39% / -26.94% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gdn | 30 | 0.638 / 0.635 | 0.469 / 0.469 | -26.46% / -26.09% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | gqa | 10 | 1.136 / 1.135 | 2.238 / 2.238 | +97.05% / +97.15% |
| a3-qwen35-tp4-decode-c12-p96512 | 12 / 4 | moe_layer | 40 | 0.762 / 0.643 | 0.911 / 0.469 | +19.53% / -27.03% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | gdn | 30 | 0.609 / 0.605 | 0.440 / 0.440 | -27.67% / -27.26% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | gqa | 10 | 1.086 / 1.079 | 2.229 / 2.229 | +105.15% / +106.48% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | moe_layer | 40 | 0.728 / 0.615 | 0.887 / 0.440 | +21.87% / -28.44% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | gdn | 30 | 0.601 / 0.597 | 0.440 / 0.440 | -26.72% / -26.23% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | gqa | 10 | 1.012 / 1.014 | 2.229 / 2.229 | +120.18% / +119.78% |
| a3-qwen35-tp4-decode-c12-p96512 | 8 / 4 | moe_layer | 40 | 0.704 / 0.606 | 0.887 / 0.440 | +26.12% / -27.31% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | gdn | 30 | 0.558 / 0.557 | 0.382 / 0.382 | -31.61% / -31.52% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | gqa | 10 | 0.898 / 0.897 | 2.174 / 2.174 | +142.11% / +142.33% |
| a3-qwen35-tp4-decode-c12-p96512 | 6 / 4 | moe_layer | 40 | 0.643 / 0.561 | 0.830 / 0.382 | +29.03% / -31.96% |
| a3-qwen35-tp4-decode-c12-p96512 | 3 / 4 | gdn | 30 | 0.469 / 0.471 | 0.277 / 0.277 | -41.03% / -41.32% |
| a3-qwen35-tp4-decode-c12-p96512 | 3 / 4 | gqa | 10 | 0.655 / 0.658 | 2.087 / 2.087 | +218.72% / +217.09% |
| a3-qwen35-tp4-decode-c12-p96512 | 3 / 4 | moe_layer | 40 | 0.516 / 0.474 | 0.729 / 0.277 | +41.45% / -41.68% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.752 / 0.747 | 0.550 / 0.550 | -26.84% / -26.34% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.295 / 1.295 | 1.345 / 1.345 | +3.83% / +3.86% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.888 / 0.755 | 0.749 / 0.550 | -15.66% / -27.08% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.745 / 0.742 | 0.550 / 0.550 | -26.07% / -25.83% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.292 / 1.291 | 1.345 / 1.345 | +4.05% / +4.13% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.881 / 0.749 | 0.749 / 0.550 | -15.03% / -26.50% |
| a3-qwen35-tp4-decode-c24-p24512 | 16 / 4 | gdn | 30 | 0.680 / 0.676 | 0.498 / 0.498 | -26.83% / -26.36% |
| a3-qwen35-tp4-decode-c24-p24512 | 16 / 4 | gqa | 10 | 0.860 / 0.859 | 0.848 / 0.848 | -1.34% / -1.20% |
| a3-qwen35-tp4-decode-c24-p24512 | 16 / 4 | moe_layer | 40 | 0.725 / 0.682 | 0.585 / 0.498 | -19.28% / -27.02% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.747 / 0.742 | 0.550 / 0.550 | -26.27% / -25.83% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.287 / 1.290 | 1.345 / 1.345 | +4.49% / +4.25% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.882 / 0.748 | 0.749 / 0.550 | -15.05% / -26.45% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.745 / 0.743 | 0.550 / 0.550 | -26.14% / -25.87% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.286 / 1.290 | 1.345 / 1.345 | +4.52% / +4.26% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.881 / 0.747 | 0.749 / 0.550 | -14.94% / -26.34% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.728 / 0.728 | 0.550 / 0.550 | -24.34% / -24.41% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.072 / 1.071 | 1.345 / 1.345 | +25.37% / +25.55% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.814 / 0.731 | 0.749 / 0.550 | -7.96% / -24.75% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gdn | 30 | 0.731 / 0.726 | 0.550 / 0.550 | -24.67% / -24.19% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | gqa | 10 | 1.055 / 1.057 | 1.345 / 1.345 | +27.45% / +27.21% |
| a3-qwen35-tp4-decode-c24-p24512 | 24 / 4 | moe_layer | 40 | 0.812 / 0.732 | 0.749 / 0.550 | -7.73% / -24.85% |
| a3-qwen35-tp4-decode-c24-p64512 | 24 / 4 | gdn | 30 | 0.748 / 0.745 | 0.550 / 0.550 | -26.38% / -26.08% |
| a3-qwen35-tp4-decode-c24-p64512 | 24 / 4 | gqa | 10 | 2.241 / 2.240 | 2.896 / 2.896 | +29.23% / +29.28% |
| a3-qwen35-tp4-decode-c24-p64512 | 24 / 4 | moe_layer | 40 | 1.121 / 0.753 | 1.137 / 0.550 | +1.41% / -26.88% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.748 / 0.745 | 0.550 / 0.550 | -26.36% / -26.12% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.922 / 0.919 | 0.724 / 0.724 | -21.50% / -21.25% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.791 / 0.754 | 0.594 / 0.550 | -24.95% / -26.96% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.746 / 0.746 | 0.550 / 0.550 | -26.21% / -26.18% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.927 / 0.925 | 0.724 / 0.724 | -21.89% / -21.74% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.791 / 0.752 | 0.594 / 0.550 | -24.95% / -26.79% |
| a3-qwen35-tp4-decode-c24-p8512 | 1 / 4 | gdn | 30 | 0.405 / 0.406 | 0.218 / 0.218 | -46.14% / -46.23% |
| a3-qwen35-tp4-decode-c24-p8512 | 1 / 4 | gqa | 10 | 0.409 / 0.410 | 0.326 / 0.326 | -20.30% / -20.50% |
| a3-qwen35-tp4-decode-c24-p8512 | 1 / 4 | moe_layer | 40 | 0.406 / 0.407 | 0.245 / 0.218 | -39.64% / -46.30% |
| a3-qwen35-tp4-decode-c24-p8512 | 8 / 4 | gdn | 30 | 0.611 / 0.607 | 0.440 / 0.440 | -27.93% / -27.43% |
| a3-qwen35-tp4-decode-c24-p8512 | 8 / 4 | gqa | 10 | 0.645 / 0.643 | 0.522 / 0.522 | -19.04% / -18.81% |
| a3-qwen35-tp4-decode-c24-p8512 | 8 / 4 | moe_layer | 40 | 0.619 / 0.612 | 0.461 / 0.440 | -25.62% / -28.07% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.748 / 0.746 | 0.550 / 0.550 | -26.39% / -26.16% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.928 / 0.923 | 0.724 / 0.724 | -22.00% / -21.56% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.793 / 0.752 | 0.594 / 0.550 | -25.11% / -26.80% |
| a3-qwen35-tp4-decode-c24-p8512 | 6 / 4 | gdn | 30 | 0.576 / 0.561 | 0.382 / 0.382 | -33.77% / -31.91% |
| a3-qwen35-tp4-decode-c24-p8512 | 6 / 4 | gqa | 10 | 0.592 / 0.590 | 0.467 / 0.467 | -21.00% / -20.84% |
| a3-qwen35-tp4-decode-c24-p8512 | 6 / 4 | moe_layer | 40 | 0.580 / 0.566 | 0.403 / 0.382 | -30.51% / -32.55% |
| a3-qwen35-tp4-decode-c24-p8512 | 4 / 4 | gdn | 30 | 0.486 / 0.483 | 0.307 / 0.307 | -36.81% / -36.37% |
| a3-qwen35-tp4-decode-c24-p8512 | 4 / 4 | gqa | 10 | 0.503 / 0.503 | 0.408 / 0.408 | -18.78% / -18.78% |
| a3-qwen35-tp4-decode-c24-p8512 | 4 / 4 | moe_layer | 40 | 0.490 / 0.485 | 0.332 / 0.307 | -32.19% / -36.66% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.727 / 0.725 | 0.550 / 0.550 | -24.26% / -24.05% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.838 / 0.838 | 0.724 / 0.724 | -13.58% / -13.63% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.754 / 0.730 | 0.594 / 0.550 | -21.29% / -24.59% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gdn | 30 | 0.725 / 0.725 | 0.550 / 0.550 | -24.05% / -24.07% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | gqa | 10 | 0.828 / 0.824 | 0.724 / 0.724 | -12.53% / -12.15% |
| a3-qwen35-tp4-decode-c24-p8512 | 24 / 4 | moe_layer | 40 | 0.751 / 0.729 | 0.594 / 0.550 | -20.88% / -24.50% |
| a3-qwen35-tp4-decode-c24-p8512 | 16 / 4 | gdn | 30 | 0.674 / 0.674 | 0.498 / 0.498 | -26.18% / -26.16% |
| a3-qwen35-tp4-decode-c24-p8512 | 16 / 4 | gqa | 10 | 0.772 / 0.773 | 0.538 / 0.538 | -30.30% / -30.37% |
| a3-qwen35-tp4-decode-c24-p8512 | 16 / 4 | moe_layer | 40 | 0.699 / 0.680 | 0.508 / 0.498 | -27.32% / -26.84% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gdn | 30 | 0.655 / 0.657 | 0.469 / 0.469 | -28.37% / -28.58% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gqa | 10 | 0.748 / 0.745 | 0.531 / 0.531 | -28.92% / -28.70% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | moe_layer | 40 | 0.678 / 0.658 | 0.485 / 0.469 | -28.52% / -28.75% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gdn | 30 | 0.637 / 0.637 | 0.469 / 0.469 | -26.39% / -26.38% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gqa | 10 | 0.747 / 0.745 | 0.531 / 0.531 | -28.86% / -28.65% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | moe_layer | 40 | 0.665 / 0.642 | 0.485 / 0.469 | -27.08% / -26.92% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gdn | 30 | 0.634 / 0.633 | 0.469 / 0.469 | -26.03% / -25.93% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | gqa | 10 | 0.745 / 0.745 | 0.531 / 0.531 | -28.69% / -28.64% |
| a3-qwen35-tp4-decode-c24-p8512 | 12 / 4 | moe_layer | 40 | 0.662 / 0.637 | 0.485 / 0.469 | -26.78% / -26.32% |
| a3-qwen35-tp4-decode-c24-p96512 | 24 / 4 | gdn | 30 | 0.746 / 0.743 | 0.550 / 0.550 | -26.20% / -25.88% |
| a3-qwen35-tp4-decode-c24-p96512 | 24 / 4 | gqa | 10 | 3.249 / 3.255 | 4.137 / 4.137 | +27.33% / +27.10% |
| a3-qwen35-tp4-decode-c24-p96512 | 24 / 4 | moe_layer | 40 | 1.372 / 0.748 | 1.447 / 0.550 | +5.50% / -26.42% |
| a3-qwen35-tp4-decode-c2-p24512 | 1 / 4 | gdn | 30 | 0.413 / 0.408 | 0.218 / 0.218 | -47.13% / -46.47% |
| a3-qwen35-tp4-decode-c2-p24512 | 1 / 4 | gqa | 10 | 0.428 / 0.429 | 0.636 / 0.636 | +48.61% / +48.35% |
| a3-qwen35-tp4-decode-c2-p24512 | 1 / 4 | moe_layer | 40 | 0.417 / 0.410 | 0.323 / 0.218 | -22.54% / -46.73% |
| a3-qwen35-tp4-decode-c2-p24512 | 2 / 4 | gdn | 30 | 0.446 / 0.443 | 0.247 / 0.247 | -44.58% / -44.11% |
| a3-qwen35-tp4-decode-c2-p24512 | 2 / 4 | gqa | 10 | 0.473 / 0.474 | 0.664 / 0.664 | +40.31% / +40.07% |
| a3-qwen35-tp4-decode-c2-p24512 | 2 / 4 | moe_layer | 40 | 0.453 / 0.446 | 0.351 / 0.247 | -22.41% / -44.54% |
| a3-qwen35-tp4-decode-c2-p64512 | 1 / 4 | gdn | 30 | 0.413 / 0.407 | 0.218 / 0.218 | -47.11% / -46.35% |
| a3-qwen35-tp4-decode-c2-p64512 | 1 / 4 | gqa | 10 | 0.472 / 0.473 | 1.412 / 1.412 | +198.88% / +198.76% |
| a3-qwen35-tp4-decode-c2-p64512 | 1 / 4 | moe_layer | 40 | 0.428 / 0.409 | 0.517 / 0.218 | +20.81% / -46.59% |
| a3-qwen35-tp4-decode-c2-p64512 | 2 / 4 | gdn | 30 | 0.447 / 0.442 | 0.247 / 0.247 | -44.63% / -44.01% |
| a3-qwen35-tp4-decode-c2-p64512 | 2 / 4 | gqa | 10 | 0.525 / 0.525 | 1.439 / 1.439 | +174.01% / +174.34% |
| a3-qwen35-tp4-decode-c2-p64512 | 2 / 4 | moe_layer | 40 | 0.466 / 0.445 | 0.545 / 0.247 | +16.95% / -44.44% |
| a3-qwen35-tp4-decode-c2-p8512 | 1 / 4 | gdn | 30 | 0.407 / 0.407 | 0.218 / 0.218 | -46.31% / -46.34% |
| a3-qwen35-tp4-decode-c2-p8512 | 1 / 4 | gqa | 10 | 0.409 / 0.412 | 0.326 / 0.326 | -20.35% / -20.91% |
| a3-qwen35-tp4-decode-c2-p8512 | 1 / 4 | moe_layer | 40 | 0.407 / 0.407 | 0.245 / 0.218 | -39.79% / -46.41% |
| a3-qwen35-tp4-decode-c2-p96512 | 1 / 4 | gdn | 30 | 0.410 / 0.408 | 0.218 / 0.218 | -46.79% / -46.48% |
| a3-qwen35-tp4-decode-c2-p96512 | 1 / 4 | gqa | 10 | 0.500 / 0.502 | 2.033 / 2.033 | +306.41% / +304.76% |
| a3-qwen35-tp4-decode-c2-p96512 | 1 / 4 | moe_layer | 40 | 0.433 / 0.411 | 0.672 / 0.218 | +55.26% / -46.87% |
| a3-qwen35-tp4-decode-c2-p96512 | 2 / 4 | gdn | 30 | 0.443 / 0.440 | 0.247 / 0.247 | -44.17% / -43.79% |
| a3-qwen35-tp4-decode-c2-p96512 | 2 / 4 | gqa | 10 | 0.571 / 0.569 | 2.060 / 2.060 | +261.05% / +261.87% |
| a3-qwen35-tp4-decode-c2-p96512 | 2 / 4 | moe_layer | 40 | 0.475 / 0.445 | 0.701 / 0.247 | +47.50% / -44.43% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | gdn | 30 | 0.563 / 0.557 | 0.382 / 0.382 | -32.22% / -31.51% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | gqa | 10 | 0.630 / 0.633 | 0.778 / 0.778 | +23.36% / +22.86% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | moe_layer | 40 | 0.580 / 0.562 | 0.481 / 0.382 | -17.12% / -32.02% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | gdn | 30 | 0.549 / 0.546 | 0.382 / 0.382 | -30.51% / -30.11% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | gqa | 10 | 0.623 / 0.625 | 0.778 / 0.778 | +24.89% / +24.51% |
| a3-qwen35-tp4-decode-c6-p24512 | 6 / 4 | moe_layer | 40 | 0.568 / 0.550 | 0.481 / 0.382 | -15.32% / -30.56% |
| a3-qwen35-tp4-decode-c6-p24512 | 1 / 4 | gdn | 30 | 0.410 / 0.409 | 0.218 / 0.218 | -46.72% / -46.57% |
| a3-qwen35-tp4-decode-c6-p24512 | 1 / 4 | gqa | 10 | 0.427 / 0.428 | 0.636 / 0.636 | +48.84% / +48.63% |
| a3-qwen35-tp4-decode-c6-p24512 | 1 / 4 | moe_layer | 40 | 0.414 / 0.410 | 0.323 / 0.218 | -22.06% / -46.76% |
| a3-qwen35-tp4-decode-c6-p24512 | 2 / 4 | gdn | 30 | 0.443 / 0.441 | 0.247 / 0.247 | -44.13% / -43.91% |
| a3-qwen35-tp4-decode-c6-p24512 | 2 / 4 | gqa | 10 | 0.474 / 0.476 | 0.664 / 0.664 | +40.00% / +39.46% |
| a3-qwen35-tp4-decode-c6-p24512 | 2 / 4 | moe_layer | 40 | 0.451 / 0.444 | 0.351 / 0.247 | -22.00% / -44.30% |
| a3-qwen35-tp4-decode-c6-p24512 | 3 / 4 | gdn | 30 | 0.466 / 0.467 | 0.277 / 0.277 | -40.64% / -40.79% |
| a3-qwen35-tp4-decode-c6-p24512 | 3 / 4 | gqa | 10 | 0.513 / 0.515 | 0.691 / 0.691 | +34.78% / +34.04% |
| a3-qwen35-tp4-decode-c6-p24512 | 3 / 4 | moe_layer | 40 | 0.478 / 0.469 | 0.380 / 0.277 | -20.40% / -41.04% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | gdn | 30 | 0.566 / 0.557 | 0.382 / 0.382 | -32.57% / -31.48% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | gqa | 10 | 0.766 / 0.767 | 1.553 / 1.553 | +102.85% / +102.49% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | moe_layer | 40 | 0.616 / 0.562 | 0.675 / 0.382 | +9.52% / -32.05% |
| a3-qwen35-tp4-decode-c6-p64512 | 2 / 4 | gdn | 30 | 0.451 / 0.444 | 0.247 / 0.247 | -45.18% / -44.27% |
| a3-qwen35-tp4-decode-c6-p64512 | 2 / 4 | gqa | 10 | 0.528 / 0.530 | 1.439 / 1.439 | +172.41% / +171.65% |
| a3-qwen35-tp4-decode-c6-p64512 | 2 / 4 | moe_layer | 40 | 0.471 / 0.447 | 0.545 / 0.247 | +15.92% / -44.66% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | gdn | 30 | 0.549 / 0.540 | 0.382 / 0.382 | -30.44% / -29.37% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | gqa | 10 | 0.756 / 0.748 | 1.553 / 1.553 | +105.56% / +107.75% |
| a3-qwen35-tp4-decode-c6-p64512 | 6 / 4 | moe_layer | 40 | 0.600 / 0.543 | 0.675 / 0.382 | +12.35% / -29.67% |
| a3-qwen35-tp4-decode-c6-p64512 | 3 / 4 | gdn | 30 | 0.503 / 0.469 | 0.277 / 0.277 | -44.97% / -40.96% |
| a3-qwen35-tp4-decode-c6-p64512 | 3 / 4 | gqa | 10 | 0.586 / 0.585 | 1.467 / 1.467 | +150.36% / +150.57% |
| a3-qwen35-tp4-decode-c6-p64512 | 3 / 4 | moe_layer | 40 | 0.524 / 0.471 | 0.574 / 0.277 | +9.67% / -41.30% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | gdn | 30 | 0.564 / 0.560 | 0.382 / 0.382 | -32.38% / -31.86% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | gqa | 10 | 0.589 / 0.593 | 0.467 / 0.467 | -20.60% / -21.13% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | moe_layer | 40 | 0.570 / 0.562 | 0.403 / 0.382 | -29.34% / -32.04% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | gdn | 30 | 0.552 / 0.543 | 0.382 / 0.382 | -30.82% / -29.69% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | gqa | 10 | 0.573 / 0.578 | 0.467 / 0.467 | -18.39% / -19.09% |
| a3-qwen35-tp4-decode-c6-p8512 | 6 / 4 | moe_layer | 40 | 0.557 / 0.545 | 0.403 / 0.382 | -27.63% / -29.99% |
| a3-qwen35-tp4-decode-c6-p8512 | 1 / 4 | gdn | 30 | 0.409 / 0.406 | 0.218 / 0.218 | -46.68% / -46.27% |
| a3-qwen35-tp4-decode-c6-p8512 | 1 / 4 | gqa | 10 | 0.410 / 0.411 | 0.326 / 0.326 | -20.56% / -20.76% |
| a3-qwen35-tp4-decode-c6-p8512 | 1 / 4 | moe_layer | 40 | 0.410 / 0.407 | 0.245 / 0.218 | -40.14% / -46.36% |
| a3-qwen35-tp4-decode-c6-p8512 | 4 / 4 | gdn | 30 | 0.490 / 0.486 | 0.307 / 0.307 | -37.40% / -36.84% |
| a3-qwen35-tp4-decode-c6-p8512 | 4 / 4 | gqa | 10 | 0.506 / 0.508 | 0.408 / 0.408 | -19.32% / -19.68% |
| a3-qwen35-tp4-decode-c6-p8512 | 4 / 4 | moe_layer | 40 | 0.494 / 0.489 | 0.332 / 0.307 | -32.78% / -37.22% |
| a3-qwen35-tp4-decode-c6-p8512 | 2 / 4 | gdn | 30 | 0.450 / 0.444 | 0.247 / 0.247 | -45.05% / -44.24% |
| a3-qwen35-tp4-decode-c6-p8512 | 2 / 4 | gqa | 10 | 0.442 / 0.442 | 0.353 / 0.353 | -20.00% / -19.98% |
| a3-qwen35-tp4-decode-c6-p8512 | 2 / 4 | moe_layer | 40 | 0.448 / 0.443 | 0.274 / 0.247 | -38.87% / -44.20% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | gdn | 30 | 0.562 / 0.558 | 0.382 / 0.382 | -32.05% / -31.62% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | gqa | 10 | 0.927 / 0.897 | 2.174 / 2.174 | +134.53% / +142.39% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | moe_layer | 40 | 0.653 / 0.560 | 0.830 / 0.382 | +27.06% / -31.87% |
| a3-qwen35-tp4-decode-c6-p96512 | 1 / 4 | gdn | 30 | 0.406 / 0.408 | 0.218 / 0.218 | -46.27% / -46.42% |
| a3-qwen35-tp4-decode-c6-p96512 | 1 / 4 | gqa | 10 | 0.498 / 0.500 | 2.033 / 2.033 | +308.24% / +306.90% |
| a3-qwen35-tp4-decode-c6-p96512 | 1 / 4 | moe_layer | 40 | 0.429 / 0.410 | 0.672 / 0.218 | +56.53% / -46.73% |
| a3-qwen35-tp4-decode-c6-p96512 | 4 / 4 | gdn | 30 | 0.487 / 0.484 | 0.307 / 0.307 | -36.96% / -36.60% |
| a3-qwen35-tp4-decode-c6-p96512 | 4 / 4 | gqa | 10 | 0.752 / 0.751 | 2.115 / 2.115 | +181.32% / +181.67% |
| a3-qwen35-tp4-decode-c6-p96512 | 4 / 4 | moe_layer | 40 | 0.553 / 0.489 | 0.759 / 0.307 | +37.19% / -37.16% |
| a3-qwen35-tp4-decode-c6-p96512 | 3 / 4 | gdn | 30 | 0.471 / 0.473 | 0.277 / 0.277 | -41.30% / -41.50% |
| a3-qwen35-tp4-decode-c6-p96512 | 3 / 4 | gqa | 10 | 0.657 / 0.655 | 2.087 / 2.087 | +217.64% / +218.53% |
| a3-qwen35-tp4-decode-c6-p96512 | 3 / 4 | moe_layer | 40 | 0.518 / 0.474 | 0.729 / 0.277 | +40.86% / -41.59% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | gdn | 30 | 0.540 / 0.541 | 0.382 / 0.382 | -29.33% / -29.50% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | gqa | 10 | 0.863 / 0.867 | 2.174 / 2.174 | +151.98% / +150.60% |
| a3-qwen35-tp4-decode-c6-p96512 | 6 / 4 | moe_layer | 40 | 0.621 / 0.544 | 0.830 / 0.382 | +33.66% / -29.82% |
| a3-qwen35-tp4-decode-c6-p96512 | 2 / 4 | gdn | 30 | 0.445 / 0.446 | 0.247 / 0.247 | -44.36% / -44.50% |
| a3-qwen35-tp4-decode-c6-p96512 | 2 / 4 | gqa | 10 | 0.573 / 0.571 | 2.060 / 2.060 | +259.23% / +260.96% |
| a3-qwen35-tp4-decode-c6-p96512 | 2 / 4 | moe_layer | 40 | 0.477 / 0.449 | 0.701 / 0.247 | +46.93% / -44.89% |
| a3-qwen36-tp2-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.370 / 0.368 | 0.310 / 0.310 | -16.09% / -15.69% |
| a3-qwen36-tp2-decode-c1-p126000 | 1 / 4 | gqa | 16 | 0.607 / 0.606 | 2.676 / 2.676 | +341.15% / +341.65% |
| a3-qwen36-tp2-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.429 / 0.371 | 0.902 / 0.310 | +110.19% / -16.41% |
| a3-qwen36-tp2-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.408 / 0.405 | 0.335 / 0.335 | -17.72% / -17.23% |
| a3-qwen36-tp2-decode-c2-p126000 | 2 / 4 | gqa | 16 | 0.775 / 0.775 | 2.682 / 2.682 | +246.00% / +245.95% |
| a3-qwen36-tp2-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.500 / 0.408 | 0.922 / 0.335 | +84.60% / -17.74% |
| a3-qwen36-tp2-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.459 / 0.461 | 0.373 / 0.373 | -18.87% / -19.13% |
| a3-qwen36-tp2-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.171 / 1.170 | 2.696 / 2.696 | +130.29% / +130.36% |
| a3-qwen36-tp2-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.637 / 0.464 | 0.953 / 0.373 | +49.64% / -19.68% |
| a3-qwen36-tp2-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.489 / 0.489 | 0.411 / 0.411 | -15.99% / -15.99% |
| a3-qwen36-tp2-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.662 / 1.663 | 2.709 / 2.709 | +62.95% / +62.91% |
| a3-qwen36-tp2-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.782 / 0.493 | 0.985 / 0.411 | +25.96% / -16.76% |
| a3-qwen36-tp2-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.520 / 0.519 | 0.449 / 0.449 | -13.64% / -13.45% |
| a3-qwen36-tp2-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.959 / 1.960 | 2.722 / 2.722 | +38.96% / +38.89% |
| a3-qwen36-tp2-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.880 / 0.522 | 1.018 / 0.449 | +15.64% / -13.95% |
| a3-qwen36-tp2-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.602 / 0.601 | 0.538 / 0.538 | -10.62% / -10.53% |
| a3-qwen36-tp2-decode-c12-p24512 | 12 / 4 | gqa | 16 | 1.056 / 1.056 | 1.257 / 1.257 | +18.98% / +19.00% |
| a3-qwen36-tp2-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.716 / 0.603 | 0.718 / 0.538 | +0.31% / -10.72% |
| a3-qwen36-tp2-decode-c12-p64512 | 12 / 4 | gdn | 48 | 0.601 / 0.600 | 0.538 / 0.538 | -10.50% / -10.27% |
| a3-qwen36-tp2-decode-c12-p64512 | 12 / 4 | gqa | 16 | 2.170 / 2.170 | 2.808 / 2.808 | +29.42% / +29.42% |
| a3-qwen36-tp2-decode-c12-p64512 | 12 / 4 | dense_layer | 64 | 0.993 / 0.604 | 1.106 / 0.538 | +11.30% / -10.88% |
| a3-qwen36-tp2-decode-c12-p8512 | 12 / 4 | gdn | 48 | 0.602 / 0.601 | 0.538 / 0.538 | -10.58% / -10.43% |
| a3-qwen36-tp2-decode-c12-p8512 | 12 / 4 | gqa | 16 | 0.687 / 0.686 | 0.636 / 0.636 | -7.38% / -7.28% |
| a3-qwen36-tp2-decode-c12-p8512 | 12 / 4 | dense_layer | 64 | 0.623 / 0.603 | 0.563 / 0.538 | -9.70% / -10.71% |
| a3-qwen36-tp2-decode-c24-p24512 | 24 / 4 | gdn | 48 | 0.797 / 0.797 | 0.781 / 0.781 | -1.91% / -1.92% |
| a3-qwen36-tp2-decode-c24-p24512 | 24 / 4 | gqa | 16 | 1.410 / 1.407 | 1.814 / 1.814 | +28.69% / +28.96% |
| a3-qwen36-tp2-decode-c24-p24512 | 24 / 4 | dense_layer | 64 | 0.950 / 0.798 | 1.040 / 0.781 | +9.44% / -2.03% |
| a3-qwen36-tp2-decode-c24-p8512 | 24 / 4 | gdn | 48 | 0.796 / 0.796 | 0.781 / 0.781 | -1.90% / -1.85% |
| a3-qwen36-tp2-decode-c24-p8512 | 24 / 4 | gqa | 16 | 0.868 / 0.868 | 0.883 / 0.883 | +1.81% / +1.80% |
| a3-qwen36-tp2-decode-c24-p8512 | 24 / 4 | dense_layer | 64 | 0.814 / 0.798 | 0.807 / 0.781 | -0.91% / -2.05% |
| a3-qwen36-tp2-decode-c2-p24512 | 2 / 4 | gdn | 48 | 0.410 / 0.409 | 0.335 / 0.335 | -18.26% / -18.00% |
| a3-qwen36-tp2-decode-c2-p24512 | 2 / 4 | gqa | 16 | 0.436 / 0.436 | 0.714 / 0.714 | +63.69% / +63.98% |
| a3-qwen36-tp2-decode-c2-p24512 | 2 / 4 | dense_layer | 64 | 0.417 / 0.412 | 0.430 / 0.335 | +3.18% / -18.59% |
| a3-qwen36-tp2-decode-c2-p24512 | 1 / 4 | gdn | 48 | 0.371 / 0.369 | 0.310 / 0.310 | -16.29% / -15.94% |
| a3-qwen36-tp2-decode-c2-p24512 | 1 / 4 | gqa | 16 | 0.390 / 0.391 | 0.708 / 0.708 | +81.34% / +80.89% |
| a3-qwen36-tp2-decode-c2-p24512 | 1 / 4 | dense_layer | 64 | 0.376 / 0.372 | 0.410 / 0.310 | +9.07% / -16.51% |
| a3-qwen36-tp2-decode-c2-p64512 | 2 / 4 | gdn | 48 | 0.407 / 0.406 | 0.335 / 0.335 | -17.58% / -17.43% |
| a3-qwen36-tp2-decode-c2-p64512 | 2 / 4 | gqa | 16 | 0.581 / 0.580 | 1.490 / 1.490 | +156.64% / +156.71% |
| a3-qwen36-tp2-decode-c2-p64512 | 2 / 4 | dense_layer | 64 | 0.450 / 0.408 | 0.624 / 0.335 | +38.57% / -17.79% |
| a3-qwen36-tp2-decode-c2-p64512 | 1 / 4 | gdn | 48 | 0.371 / 0.369 | 0.310 / 0.310 | -16.47% / -15.93% |
| a3-qwen36-tp2-decode-c2-p64512 | 1 / 4 | gqa | 16 | 0.481 / 0.480 | 1.483 / 1.483 | +208.52% / +209.05% |
| a3-qwen36-tp2-decode-c2-p64512 | 1 / 4 | dense_layer | 64 | 0.399 / 0.373 | 0.604 / 0.310 | +51.34% / -16.80% |
| a3-qwen36-tp2-decode-c2-p8512 | 2 / 4 | gdn | 48 | 0.409 / 0.408 | 0.335 / 0.335 | -17.97% / -17.73% |
| a3-qwen36-tp2-decode-c2-p8512 | 2 / 4 | gqa | 16 | 0.384 / 0.379 | 0.404 / 0.404 | +5.32% / +6.52% |
| a3-qwen36-tp2-decode-c2-p8512 | 2 / 4 | dense_layer | 64 | 0.403 / 0.407 | 0.353 / 0.335 | -12.42% / -17.51% |
| a3-qwen36-tp2-decode-c2-p8512 | 1 / 4 | gdn | 48 | 0.380 / 0.369 | 0.310 / 0.310 | -18.29% / -15.89% |
| a3-qwen36-tp2-decode-c2-p8512 | 1 / 4 | gqa | 16 | 0.351 / 0.350 | 0.397 / 0.397 | +13.07% / +13.46% |
| a3-qwen36-tp2-decode-c2-p8512 | 1 / 4 | dense_layer | 64 | 0.373 / 0.366 | 0.332 / 0.310 | -10.90% / -15.21% |
| a3-qwen36-tp2-decode-c2-p96512 | 2 / 4 | gdn | 48 | 0.404 / 0.403 | 0.335 / 0.335 | -17.00% / -16.86% |
| a3-qwen36-tp2-decode-c2-p96512 | 2 / 4 | gqa | 16 | 0.674 / 0.673 | 2.111 / 2.111 | +213.28% / +213.43% |
| a3-qwen36-tp2-decode-c2-p96512 | 2 / 4 | dense_layer | 64 | 0.472 / 0.407 | 0.779 / 0.335 | +65.26% / -17.61% |
| a3-qwen36-tp2-decode-c2-p96512 | 1 / 4 | gdn | 48 | 0.367 / 0.367 | 0.310 / 0.310 | -15.54% / -15.43% |
| a3-qwen36-tp2-decode-c2-p96512 | 1 / 4 | gqa | 16 | 0.549 / 0.549 | 2.104 / 2.104 | +283.47% / +283.28% |
| a3-qwen36-tp2-decode-c2-p96512 | 1 / 4 | dense_layer | 64 | 0.413 / 0.369 | 0.759 / 0.310 | +83.83% / -16.01% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | gdn | 48 | 0.492 / 0.490 | 0.411 / 0.411 | -16.57% / -16.28% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | gqa | 16 | 0.628 / 0.628 | 0.741 / 0.741 | +17.91% / +18.06% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | dense_layer | 64 | 0.526 / 0.494 | 0.493 / 0.411 | -6.27% / -16.90% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | gdn | 48 | 0.474 / 0.473 | 0.411 / 0.411 | -13.46% / -13.14% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | gqa | 16 | 0.586 / 0.586 | 0.741 / 0.741 | +26.33% / +26.38% |
| a3-qwen36-tp2-decode-c6-p24512 | 6 / 4 | dense_layer | 64 | 0.502 / 0.477 | 0.493 / 0.411 | -1.85% / -13.89% |
| a3-qwen36-tp2-decode-c6-p24512 | 2 / 4 | gdn | 48 | 0.410 / 0.408 | 0.335 / 0.335 | -18.12% / -17.89% |
| a3-qwen36-tp2-decode-c6-p24512 | 2 / 4 | gqa | 16 | 0.432 / 0.430 | 0.714 / 0.714 | +65.54% / +65.96% |
| a3-qwen36-tp2-decode-c6-p24512 | 2 / 4 | dense_layer | 64 | 0.415 / 0.412 | 0.430 / 0.335 | +3.62% / -18.61% |
| a3-qwen36-tp2-decode-c6-p24512 | 3 / 4 | gdn | 48 | 0.425 / 0.424 | 0.349 / 0.349 | -17.97% / -17.78% |
| a3-qwen36-tp2-decode-c6-p24512 | 3 / 4 | gqa | 16 | 0.490 / 0.490 | 0.721 / 0.721 | +47.14% / +47.08% |
| a3-qwen36-tp2-decode-c6-p24512 | 3 / 4 | dense_layer | 64 | 0.441 / 0.428 | 0.442 / 0.349 | +0.10% / -18.54% |
| a3-qwen36-tp2-decode-c6-p24512 | 1 / 4 | gdn | 48 | 0.370 / 0.369 | 0.310 / 0.310 | -16.15% / -15.80% |
| a3-qwen36-tp2-decode-c6-p24512 | 1 / 4 | gqa | 16 | 0.392 / 0.393 | 0.708 / 0.708 | +80.41% / +80.31% |
| a3-qwen36-tp2-decode-c6-p24512 | 1 / 4 | dense_layer | 64 | 0.376 / 0.371 | 0.410 / 0.310 | +9.06% / -16.44% |
| a3-qwen36-tp2-decode-c6-p64512 | 6 / 4 | gdn | 48 | 0.487 / 0.488 | 0.411 / 0.411 | -15.74% / -15.85% |
| a3-qwen36-tp2-decode-c6-p64512 | 6 / 4 | gqa | 16 | 1.018 / 1.013 | 1.517 / 1.517 | +49.03% / +49.65% |
| a3-qwen36-tp2-decode-c6-p64512 | 6 / 4 | dense_layer | 64 | 0.620 / 0.489 | 0.687 / 0.411 | +10.84% / -16.07% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | gdn | 48 | 0.493 / 0.491 | 0.411 / 0.411 | -16.76% / -16.34% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | gqa | 16 | 0.519 / 0.520 | 0.431 / 0.431 | -17.08% / -17.15% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | dense_layer | 64 | 0.500 / 0.494 | 0.416 / 0.411 | -16.85% / -16.88% |
| a3-qwen36-tp2-decode-c6-p8512 | 2 / 4 | gdn | 48 | 0.408 / 0.406 | 0.335 / 0.335 | -17.83% / -17.45% |
| a3-qwen36-tp2-decode-c6-p8512 | 2 / 4 | gqa | 16 | 0.376 / 0.375 | 0.404 / 0.404 | +7.40% / +7.62% |
| a3-qwen36-tp2-decode-c6-p8512 | 2 / 4 | dense_layer | 64 | 0.400 / 0.405 | 0.353 / 0.335 | -11.90% / -17.22% |
| a3-qwen36-tp2-decode-c6-p8512 | 4 / 4 | gdn | 48 | 0.459 / 0.457 | 0.373 / 0.373 | -18.84% / -18.55% |
| a3-qwen36-tp2-decode-c6-p8512 | 4 / 4 | gqa | 16 | 0.437 / 0.435 | 0.417 / 0.417 | -4.47% / -4.11% |
| a3-qwen36-tp2-decode-c6-p8512 | 4 / 4 | dense_layer | 64 | 0.454 / 0.455 | 0.384 / 0.373 | -15.38% / -18.03% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | gdn | 48 | 0.474 / 0.473 | 0.411 / 0.411 | -13.35% / -13.14% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | gqa | 16 | 0.514 / 0.516 | 0.431 / 0.431 | -16.30% / -16.59% |
| a3-qwen36-tp2-decode-c6-p8512 | 6 / 4 | dense_layer | 64 | 0.484 / 0.476 | 0.416 / 0.411 | -14.14% / -13.80% |
| a3-qwen36-tp2-decode-c6-p8512 | 3 / 4 | gdn | 48 | 0.423 / 0.424 | 0.349 / 0.349 | -17.64% / -17.71% |
| a3-qwen36-tp2-decode-c6-p8512 | 3 / 4 | gqa | 16 | 0.413 / 0.413 | 0.411 / 0.411 | -0.56% / -0.60% |
| a3-qwen36-tp2-decode-c6-p8512 | 3 / 4 | dense_layer | 64 | 0.421 / 0.420 | 0.364 / 0.349 | -13.45% / -16.90% |
| a3-qwen36-tp2-decode-c6-p96512 | 6 / 4 | gdn | 48 | 0.487 / 0.488 | 0.411 / 0.411 | -15.76% / -15.82% |
| a3-qwen36-tp2-decode-c6-p96512 | 6 / 4 | gqa | 16 | 1.317 / 1.318 | 2.137 / 2.137 | +62.27% / +62.19% |
| a3-qwen36-tp2-decode-c6-p96512 | 6 / 4 | dense_layer | 64 | 0.695 / 0.491 | 0.842 / 0.411 | +21.22% / -16.43% |
| a3-qwen36-tp4-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.279 / 0.276 | 0.221 / 0.221 | -20.72% / -19.88% |
| a3-qwen36-tp4-decode-c1-p126000 | 1 / 4 | gqa | 16 | 0.390 / 0.389 | 2.615 / 2.615 | +570.78% / +571.92% |
| a3-qwen36-tp4-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.307 / 0.280 | 0.820 / 0.221 | +167.10% / -20.87% |
| a3-qwen36-tp4-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.437 / 0.436 | 0.340 / 0.340 | -22.06% / -21.94% |
| a3-qwen36-tp4-decode-c12-p126000 | 12 / 4 | gqa | 16 | 1.454 / 1.453 | 2.661 / 2.661 | +83.09% / +83.13% |
| a3-qwen36-tp4-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 0.691 / 0.439 | 0.921 / 0.340 | +33.24% / -22.39% |
| a3-qwen36-tp4-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.482 / 0.480 | 0.383 / 0.383 | -20.45% / -20.14% |
| a3-qwen36-tp4-decode-c16-p126000 | 16 / 4 | gqa | 16 | 1.801 / 1.801 | 2.678 / 2.678 | +48.72% / +48.73% |
| a3-qwen36-tp4-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 0.812 / 0.483 | 0.957 / 0.383 | +17.92% / -20.58% |
| a3-qwen36-tp4-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.294 / 0.292 | 0.229 / 0.229 | -22.00% / -21.39% |
| a3-qwen36-tp4-decode-c2-p126000 | 2 / 4 | gqa | 16 | 0.482 / 0.474 | 2.619 / 2.619 | +443.25% / +452.14% |
| a3-qwen36-tp4-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.341 / 0.295 | 0.827 / 0.229 | +142.43% / -22.22% |
| a3-qwen36-tp4-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.646 / 0.332 | 0.257 / 0.257 | -60.26% / -22.60% |
| a3-qwen36-tp4-decode-c4-p126000 | 4 / 4 | gqa | 16 | 0.682 / 0.675 | 2.628 / 2.628 | +285.29% / +289.46% |
| a3-qwen36-tp4-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.655 / 0.336 | 0.849 / 0.257 | +29.71% / -23.74% |
| a3-qwen36-tp4-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.364 / 0.362 | 0.272 / 0.272 | -25.32% / -24.95% |
| a3-qwen36-tp4-decode-c6-p126000 | 6 / 4 | gqa | 16 | 0.907 / 0.902 | 2.636 / 2.636 | +190.69% / +192.29% |
| a3-qwen36-tp4-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.500 / 0.366 | 0.863 / 0.272 | +72.63% / -25.74% |
| a3-qwen36-tp4-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.397 / 0.397 | 0.298 / 0.298 | -24.95% / -24.84% |
| a3-qwen36-tp4-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.092 / 1.092 | 2.644 / 2.644 | +142.12% / +142.24% |
| a3-qwen36-tp4-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.571 / 0.398 | 0.885 / 0.298 | +54.95% / -25.11% |
| a3-qwen38-tp2-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.369 / 0.369 | 0.310 / 0.310 | -15.96% / -15.92% |
| a3-qwen38-tp2-decode-c1-p126000 | 1 / 4 | gqa | 16 | 0.611 / 0.607 | 2.676 / 2.676 | +338.30% / +340.51% |
| a3-qwen38-tp2-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.430 / 0.371 | 0.902 / 0.310 | +109.92% / -16.40% |
| a3-qwen38-tp2-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.408 / 0.407 | 0.335 / 0.335 | -17.80% / -17.65% |
| a3-qwen38-tp2-decode-c2-p126000 | 2 / 4 | gqa | 16 | 0.780 / 0.778 | 2.682 / 2.682 | +243.95% / +244.85% |
| a3-qwen38-tp2-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.501 / 0.410 | 0.922 / 0.335 | +84.06% / -18.17% |
| a3-qwen38-tp2-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.454 / 0.454 | 0.373 / 0.373 | -17.93% / -17.89% |
| a3-qwen38-tp2-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.168 / 1.166 | 2.696 / 2.696 | +130.83% / +131.13% |
| a3-qwen38-tp2-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.632 / 0.458 | 0.953 / 0.373 | +50.75% / -18.65% |
| a3-qwen38-tp2-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.490 / 0.491 | 0.411 / 0.411 | -16.21% / -16.43% |
| a3-qwen38-tp2-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.669 / 1.669 | 2.709 / 2.709 | +62.30% / +62.34% |
| a3-qwen38-tp2-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.785 / 0.495 | 0.985 / 0.411 | +25.53% / -17.09% |
| a3-qwen38-tp2-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.519 / 0.519 | 0.449 / 0.449 | -13.51% / -13.46% |
| a3-qwen38-tp2-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.962 / 1.962 | 2.722 / 2.722 | +38.76% / +38.76% |
| a3-qwen38-tp2-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.880 / 0.523 | 1.018 / 0.449 | +15.62% / -14.03% |
| a3-qwen38-tp4-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.280 / 0.277 | 0.221 / 0.221 | -20.92% / -20.04% |
| a3-qwen38-tp4-decode-c1-p126000 | 1 / 4 | gqa | 16 | 0.400 / 0.391 | 2.615 / 2.615 | +553.59% / +568.86% |
| a3-qwen38-tp4-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.310 / 0.279 | 0.820 / 0.221 | +164.43% / -20.58% |
| a3-qwen38-tp4-decode-c12-p126000 | 12 / 4 | gdn | 48 | 0.438 / 0.436 | 0.340 / 0.340 | -22.21% / -21.89% |
| a3-qwen38-tp4-decode-c12-p126000 | 12 / 4 | gqa | 16 | 1.453 / 1.452 | 2.661 / 2.661 | +83.11% / +83.23% |
| a3-qwen38-tp4-decode-c12-p126000 | 12 / 4 | dense_layer | 64 | 0.692 / 0.438 | 0.921 / 0.340 | +33.13% / -22.25% |
| a3-qwen38-tp4-decode-c16-p126000 | 16 / 4 | gdn | 48 | 0.478 / 0.477 | 0.383 / 0.383 | -19.79% / -19.62% |
| a3-qwen38-tp4-decode-c16-p126000 | 16 / 4 | gqa | 16 | 1.800 / 1.800 | 2.678 / 2.678 | +48.79% / +48.78% |
| a3-qwen38-tp4-decode-c16-p126000 | 16 / 4 | dense_layer | 64 | 0.809 / 0.481 | 0.957 / 0.383 | +18.38% / -20.30% |
| a3-qwen38-tp4-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.295 / 0.292 | 0.229 / 0.229 | -22.20% / -21.45% |
| a3-qwen38-tp4-decode-c2-p126000 | 2 / 4 | gqa | 16 | 0.476 / 0.475 | 2.619 / 2.619 | +449.84% / +451.88% |
| a3-qwen38-tp4-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.340 / 0.296 | 0.827 / 0.229 | +143.06% / -22.49% |
| a3-qwen38-tp4-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.332 / 0.331 | 0.257 / 0.257 | -22.79% / -22.37% |
| a3-qwen38-tp4-decode-c4-p126000 | 4 / 4 | gqa | 16 | 0.676 / 0.675 | 2.628 / 2.628 | +288.84% / +289.45% |
| a3-qwen38-tp4-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.418 / 0.335 | 0.849 / 0.257 | +103.11% / -23.29% |
| a3-qwen38-tp4-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.364 / 0.363 | 0.272 / 0.272 | -25.22% / -25.05% |
| a3-qwen38-tp4-decode-c6-p126000 | 6 / 4 | gqa | 16 | 0.906 / 0.907 | 2.636 / 2.636 | +191.09% / +190.77% |
| a3-qwen38-tp4-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.499 / 0.366 | 0.863 / 0.272 | +72.88% / -25.65% |
| a3-qwen38-tp4-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.396 / 0.394 | 0.298 / 0.298 | -24.67% / -24.41% |
| a3-qwen38-tp4-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.089 / 1.088 | 2.644 / 2.644 | +142.87% / +143.13% |
| a3-qwen38-tp4-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.569 / 0.396 | 0.885 / 0.298 | +55.48% / -24.80% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.444 / 0.444 | 0.340 / 0.340 | -23.29% / -23.29% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gqa | 16 | 0.598 / 0.597 | 0.693 / 0.693 | +15.99% / +16.14% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.482 / 0.447 | 0.429 / 0.340 | -11.12% / -23.78% |
| a3-qwen38-tp4-decode-c12-p24512 | 1 / 4 | gdn | 48 | 0.277 / 0.275 | 0.221 / 0.221 | -20.04% / -19.37% |
| a3-qwen38-tp4-decode-c12-p24512 | 1 / 4 | gqa | 16 | 0.283 / 0.283 | 0.647 / 0.647 | +128.83% / +128.81% |
| a3-qwen38-tp4-decode-c12-p24512 | 1 / 4 | dense_layer | 64 | 0.278 / 0.276 | 0.328 / 0.221 | +17.75% / -19.68% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.424 / 0.425 | 0.340 / 0.340 | -19.80% / -19.92% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gqa | 16 | 0.565 / 0.565 | 0.693 / 0.693 | +22.80% / +22.69% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.459 / 0.427 | 0.429 / 0.340 | -6.72% / -20.28% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.441 / 0.442 | 0.340 / 0.340 | -22.88% / -23.04% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gqa | 16 | 0.566 / 0.564 | 0.693 / 0.693 | +22.54% / +22.86% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.472 / 0.444 | 0.429 / 0.340 | -9.28% / -23.37% |
| a3-qwen38-tp4-decode-c12-p24512 | 2 / 4 | gdn | 48 | 0.294 / 0.291 | 0.229 / 0.229 | -21.93% / -21.33% |
| a3-qwen38-tp4-decode-c12-p24512 | 2 / 4 | gqa | 16 | 0.320 / 0.320 | 0.651 / 0.651 | +103.38% / +103.40% |
| a3-qwen38-tp4-decode-c12-p24512 | 2 / 4 | dense_layer | 64 | 0.300 / 0.294 | 0.335 / 0.229 | +11.46% / -22.00% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gdn | 48 | 0.423 / 0.423 | 0.340 / 0.340 | -19.57% / -19.61% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | gqa | 16 | 0.526 / 0.526 | 0.693 / 0.693 | +31.75% / +31.89% |
| a3-qwen38-tp4-decode-c12-p24512 | 12 / 4 | dense_layer | 64 | 0.449 / 0.426 | 0.429 / 0.340 | -4.53% / -20.04% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | gdn | 48 | 0.372 / 0.366 | 0.272 / 0.272 | -26.86% / -25.67% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | gqa | 16 | 0.440 / 0.439 | 0.668 / 0.668 | +51.81% / +52.18% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | dense_layer | 64 | 0.389 / 0.368 | 0.371 / 0.272 | -4.61% / -26.07% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | gdn | 48 | 0.363 / 0.363 | 0.272 / 0.272 | -25.04% / -25.01% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | gqa | 16 | 0.427 / 0.425 | 0.668 / 0.668 | +56.49% / +57.16% |
| a3-qwen38-tp4-decode-c12-p24512 | 6 / 4 | dense_layer | 64 | 0.379 / 0.365 | 0.371 / 0.272 | -2.08% / -25.39% |
| a3-qwen38-tp4-decode-c12-p24512 | 3 / 4 | gdn | 48 | 0.304 / 0.304 | 0.238 / 0.238 | -21.71% / -21.68% |
| a3-qwen38-tp4-decode-c12-p24512 | 3 / 4 | gqa | 16 | 0.342 / 0.344 | 0.655 / 0.655 | +91.38% / +90.64% |
| a3-qwen38-tp4-decode-c12-p24512 | 3 / 4 | dense_layer | 64 | 0.313 / 0.306 | 0.342 / 0.238 | +9.17% / -22.33% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gdn | 48 | 0.443 / 0.443 | 0.340 / 0.340 | -23.12% / -23.07% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gqa | 16 | 0.909 / 0.908 | 1.469 / 1.469 | +61.56% / +61.70% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | dense_layer | 64 | 0.559 / 0.445 | 0.623 / 0.340 | +11.29% / -23.52% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gdn | 48 | 0.425 / 0.425 | 0.340 / 0.340 | -19.95% / -19.85% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gqa | 16 | 0.733 / 0.734 | 1.469 / 1.469 | +100.53% / +100.10% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | dense_layer | 64 | 0.502 / 0.426 | 0.623 / 0.340 | +23.99% / -20.18% |
| a3-qwen38-tp4-decode-c12-p64512 | 8 / 4 | gdn | 48 | 0.416 / 0.401 | 0.298 / 0.298 | -28.26% / -25.57% |
| a3-qwen38-tp4-decode-c12-p64512 | 8 / 4 | gqa | 16 | 0.695 / 0.694 | 1.452 / 1.452 | +108.88% / +109.22% |
| a3-qwen38-tp4-decode-c12-p64512 | 8 / 4 | dense_layer | 64 | 0.485 / 0.403 | 0.587 / 0.298 | +20.83% / -25.96% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gdn | 48 | 0.441 / 0.441 | 0.340 / 0.340 | -22.86% / -22.72% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | gqa | 16 | 0.843 / 0.843 | 1.469 / 1.469 | +74.30% / +74.29% |
| a3-qwen38-tp4-decode-c12-p64512 | 12 / 4 | dense_layer | 64 | 0.542 / 0.444 | 0.623 / 0.340 | +14.93% / -23.26% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gdn | 48 | 0.442 / 0.442 | 0.340 / 0.340 | -22.97% / -23.01% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gqa | 16 | 1.158 / 1.157 | 2.089 / 2.089 | +80.46% / +80.59% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | dense_layer | 64 | 0.621 / 0.445 | 0.778 / 0.340 | +25.25% / -23.44% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gdn | 48 | 0.424 / 0.423 | 0.340 / 0.340 | -19.62% / -19.48% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gqa | 16 | 0.938 / 0.936 | 2.089 / 2.089 | +122.78% / +123.20% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | dense_layer | 64 | 0.552 / 0.425 | 0.778 / 0.340 | +40.85% / -19.98% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gdn | 48 | 0.440 / 0.441 | 0.340 / 0.340 | -22.68% / -22.87% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gqa | 16 | 1.067 / 1.066 | 2.089 / 2.089 | +95.78% / +95.93% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | dense_layer | 64 | 0.597 / 0.443 | 0.778 / 0.340 | +30.26% / -23.15% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gdn | 48 | 0.424 / 0.424 | 0.340 / 0.340 | -19.71% / -19.75% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | gqa | 16 | 1.098 / 1.100 | 2.089 / 2.089 | +90.22% / +89.99% |
| a3-qwen38-tp4-decode-c12-p96512 | 12 / 4 | dense_layer | 64 | 0.593 / 0.427 | 0.778 / 0.340 | +31.23% / -20.28% |
| a3-qwen38-tp4-decode-c24-p24512 | 24 / 4 | gdn | 48 | 0.556 / 0.555 | 0.481 / 0.481 | -13.61% / -13.45% |
| a3-qwen38-tp4-decode-c24-p24512 | 24 / 4 | gqa | 16 | 1.055 / 1.056 | 1.220 / 1.220 | +15.61% / +15.55% |
| a3-qwen38-tp4-decode-c24-p24512 | 24 / 4 | dense_layer | 64 | 0.681 / 0.557 | 0.665 / 0.481 | -2.29% / -13.68% |
| a3-qwen38-tp4-decode-c24-p64512 | 24 / 4 | gdn | 48 | 0.556 / 0.555 | 0.481 / 0.481 | -13.50% / -13.48% |
| a3-qwen38-tp4-decode-c24-p64512 | 24 / 4 | gqa | 16 | 2.088 / 2.087 | 2.771 / 2.771 | +32.75% / +32.79% |
| a3-qwen38-tp4-decode-c24-p64512 | 24 / 4 | dense_layer | 64 | 0.939 / 0.556 | 1.053 / 0.481 | +12.21% / -13.58% |
| a3-qwen38-tp4-decode-c24-p96512 | 24 / 4 | gdn | 48 | 0.555 / 0.554 | 0.481 / 0.481 | -13.34% / -13.30% |
| a3-qwen38-tp4-decode-c24-p96512 | 24 / 4 | gqa | 16 | 3.031 / 3.033 | 4.013 / 4.013 | +32.38% / +32.29% |
| a3-qwen38-tp4-decode-c24-p96512 | 24 / 4 | dense_layer | 64 | 1.174 / 0.556 | 1.364 / 0.481 | +16.18% / -13.50% |
| a3-qwen38-tp4-decode-c2-p24512 | 2 / 4 | gdn | 48 | 0.294 / 0.292 | 0.229 / 0.229 | -22.05% / -21.48% |
| a3-qwen38-tp4-decode-c2-p24512 | 2 / 4 | gqa | 16 | 0.327 / 0.321 | 0.651 / 0.651 | +98.86% / +102.67% |
| a3-qwen38-tp4-decode-c2-p24512 | 2 / 4 | dense_layer | 64 | 0.302 / 0.295 | 0.335 / 0.229 | +10.66% / -22.18% |
| a3-qwen38-tp4-decode-c2-p24512 | 1 / 4 | gdn | 48 | 0.276 / 0.275 | 0.221 / 0.221 | -19.83% / -19.51% |
| a3-qwen38-tp4-decode-c2-p24512 | 1 / 4 | gqa | 16 | 0.282 / 0.282 | 0.647 / 0.647 | +129.09% / +129.31% |
| a3-qwen38-tp4-decode-c2-p24512 | 1 / 4 | dense_layer | 64 | 0.278 / 0.276 | 0.328 / 0.221 | +18.02% / -19.83% |
| a3-qwen38-tp4-decode-c2-p64512 | 2 / 4 | gdn | 48 | 0.294 / 0.290 | 0.229 / 0.229 | -21.95% / -21.03% |
| a3-qwen38-tp4-decode-c2-p64512 | 2 / 4 | gqa | 16 | 0.379 / 0.377 | 1.427 / 1.427 | +276.40% / +277.94% |
| a3-qwen38-tp4-decode-c2-p64512 | 2 / 4 | dense_layer | 64 | 0.315 / 0.292 | 0.529 / 0.229 | +67.77% / -21.39% |
| a3-qwen38-tp4-decode-c2-p64512 | 1 / 4 | gdn | 48 | 0.273 / 0.273 | 0.221 / 0.221 | -18.98% / -18.82% |
| a3-qwen38-tp4-decode-c2-p64512 | 1 / 4 | gqa | 16 | 0.331 / 0.330 | 1.422 / 1.422 | +329.76% / +330.50% |
| a3-qwen38-tp4-decode-c2-p64512 | 1 / 4 | dense_layer | 64 | 0.288 / 0.275 | 0.522 / 0.221 | +81.32% / -19.46% |
| a3-qwen38-tp4-decode-c2-p96512 | 2 / 4 | gdn | 48 | 0.295 / 0.291 | 0.229 / 0.229 | -22.16% / -21.22% |
| a3-qwen38-tp4-decode-c2-p96512 | 2 / 4 | gqa | 16 | 0.425 / 0.425 | 2.047 / 2.047 | +381.47% / +381.53% |
| a3-qwen38-tp4-decode-c2-p96512 | 2 / 4 | dense_layer | 64 | 0.327 / 0.293 | 0.684 / 0.229 | +108.95% / -21.76% |
| a3-qwen38-tp4-decode-c2-p96512 | 1 / 4 | gdn | 48 | 0.275 / 0.274 | 0.221 / 0.221 | -19.39% / -19.07% |
| a3-qwen38-tp4-decode-c2-p96512 | 1 / 4 | gqa | 16 | 0.381 / 0.361 | 2.043 / 2.043 | +435.81% / +465.87% |
| a3-qwen38-tp4-decode-c2-p96512 | 1 / 4 | dense_layer | 64 | 0.301 / 0.275 | 0.677 / 0.221 | +124.61% / -19.56% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | gdn | 48 | 0.367 / 0.366 | 0.272 / 0.272 | -25.91% / -25.68% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | gqa | 16 | 0.443 / 0.442 | 0.668 / 0.668 | +50.65% / +51.12% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | dense_layer | 64 | 0.386 / 0.369 | 0.371 / 0.272 | -3.94% / -26.18% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | gdn | 48 | 0.364 / 0.363 | 0.272 / 0.272 | -25.17% / -25.00% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | gqa | 16 | 0.427 / 0.426 | 0.668 / 0.668 | +56.45% / +56.83% |
| a3-qwen38-tp4-decode-c6-p24512 | 6 / 4 | dense_layer | 64 | 0.379 / 0.365 | 0.371 / 0.272 | -2.21% / -25.41% |
| a3-qwen38-tp4-decode-c6-p24512 | 2 / 4 | gdn | 48 | 0.301 / 0.292 | 0.229 / 0.229 | -23.73% / -21.46% |
| a3-qwen38-tp4-decode-c6-p24512 | 2 / 4 | gqa | 16 | 0.320 / 0.319 | 0.651 / 0.651 | +103.52% / +104.31% |
| a3-qwen38-tp4-decode-c6-p24512 | 2 / 4 | dense_layer | 64 | 0.305 / 0.294 | 0.335 / 0.229 | +9.58% / -21.93% |
| a3-qwen38-tp4-decode-c6-p24512 | 1 / 4 | gdn | 48 | 0.276 / 0.275 | 0.221 / 0.221 | -19.78% / -19.33% |
| a3-qwen38-tp4-decode-c6-p24512 | 1 / 4 | gqa | 16 | 0.283 / 0.283 | 0.647 / 0.647 | +128.72% / +128.76% |
| a3-qwen38-tp4-decode-c6-p24512 | 1 / 4 | dense_layer | 64 | 0.278 / 0.276 | 0.328 / 0.221 | +18.02% / -19.89% |
| a3-qwen38-tp4-decode-c6-p24512 | 4 / 4 | gdn | 48 | 0.344 / 0.334 | 0.257 / 0.257 | -25.40% / -23.08% |
| a3-qwen38-tp4-decode-c6-p24512 | 4 / 4 | gqa | 16 | 0.372 / 0.371 | 0.659 / 0.659 | +77.19% / +77.61% |
| a3-qwen38-tp4-decode-c6-p24512 | 4 / 4 | dense_layer | 64 | 0.351 / 0.335 | 0.357 / 0.257 | +1.80% / -23.50% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | gdn | 48 | 0.367 / 0.366 | 0.272 / 0.272 | -25.95% / -25.76% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | gqa | 16 | 0.598 / 0.597 | 1.444 / 1.444 | +141.56% / +141.85% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | dense_layer | 64 | 0.425 / 0.369 | 0.565 / 0.272 | +32.94% / -26.20% |
| a3-qwen38-tp4-decode-c6-p64512 | 4 / 4 | gdn | 48 | 0.336 / 0.333 | 0.257 / 0.257 | -23.71% / -22.93% |
| a3-qwen38-tp4-decode-c6-p64512 | 4 / 4 | gqa | 16 | 0.485 / 0.485 | 1.435 / 1.435 | +195.60% / +195.60% |
| a3-qwen38-tp4-decode-c6-p64512 | 4 / 4 | dense_layer | 64 | 0.374 / 0.335 | 0.551 / 0.257 | +47.53% / -23.31% |
| a3-qwen38-tp4-decode-c6-p64512 | 3 / 4 | gdn | 48 | 0.323 / 0.304 | 0.238 / 0.238 | -26.47% / -21.68% |
| a3-qwen38-tp4-decode-c6-p64512 | 3 / 4 | gqa | 16 | 0.437 / 0.438 | 1.431 / 1.431 | +227.10% / +226.41% |
| a3-qwen38-tp4-decode-c6-p64512 | 3 / 4 | dense_layer | 64 | 0.352 / 0.304 | 0.536 / 0.238 | +52.33% / -21.89% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | gdn | 48 | 0.364 / 0.363 | 0.272 / 0.272 | -25.19% / -25.15% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | gqa | 16 | 0.563 / 0.561 | 1.444 / 1.444 | +156.51% / +157.25% |
| a3-qwen38-tp4-decode-c6-p64512 | 6 / 4 | dense_layer | 64 | 0.413 / 0.366 | 0.565 / 0.272 | +36.64% / -25.64% |
| a3-qwen38-tp4-decode-c6-p64512 | 2 / 4 | gdn | 48 | 0.299 / 0.289 | 0.229 / 0.229 | -23.29% / -20.66% |
| a3-qwen38-tp4-decode-c6-p64512 | 2 / 4 | gqa | 16 | 0.380 / 0.379 | 1.427 / 1.427 | +274.98% / +276.59% |
| a3-qwen38-tp4-decode-c6-p64512 | 2 / 4 | dense_layer | 64 | 0.319 / 0.290 | 0.529 / 0.229 | +65.56% / -21.06% |
| a3-qwen38-tp4-decode-c6-p64512 | 1 / 4 | gdn | 48 | 0.280 / 0.273 | 0.221 / 0.221 | -21.00% / -18.87% |
| a3-qwen38-tp4-decode-c6-p64512 | 1 / 4 | gqa | 16 | 0.330 / 0.331 | 1.422 / 1.422 | +331.23% / +330.11% |
| a3-qwen38-tp4-decode-c6-p64512 | 1 / 4 | dense_layer | 64 | 0.293 / 0.276 | 0.522 / 0.221 | +78.25% / -19.73% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | gdn | 48 | 0.368 / 0.366 | 0.272 / 0.272 | -26.07% / -25.68% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | gqa | 16 | 0.741 / 0.727 | 2.064 / 2.064 | +178.56% / +183.97% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | dense_layer | 64 | 0.461 / 0.367 | 0.720 / 0.272 | +56.12% / -25.97% |
| a3-qwen38-tp4-decode-c6-p96512 | 1 / 4 | gdn | 48 | 0.280 / 0.274 | 0.221 / 0.221 | -20.82% / -19.08% |
| a3-qwen38-tp4-decode-c6-p96512 | 1 / 4 | gqa | 16 | 0.360 / 0.360 | 2.043 / 2.043 | +467.34% / +466.85% |
| a3-qwen38-tp4-decode-c6-p96512 | 1 / 4 | dense_layer | 64 | 0.300 / 0.276 | 0.677 / 0.221 | +125.79% / -19.64% |
| a3-qwen38-tp4-decode-c6-p96512 | 3 / 4 | gdn | 48 | 0.307 / 0.305 | 0.238 / 0.238 | -22.52% / -21.91% |
| a3-qwen38-tp4-decode-c6-p96512 | 3 / 4 | gqa | 16 | 0.508 / 0.503 | 2.051 / 2.051 | +303.57% / +308.14% |
| a3-qwen38-tp4-decode-c6-p96512 | 3 / 4 | dense_layer | 64 | 0.357 / 0.307 | 0.691 / 0.238 | +93.47% / -22.49% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | gdn | 48 | 0.365 / 0.364 | 0.272 / 0.272 | -25.42% / -25.30% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | gqa | 16 | 0.675 / 0.673 | 2.064 / 2.064 | +205.96% / +206.49% |
| a3-qwen38-tp4-decode-c6-p96512 | 6 / 4 | dense_layer | 64 | 0.442 / 0.366 | 0.720 / 0.272 | +62.83% / -25.61% |
| a3-qwen38-tp4-decode-c6-p96512 | 2 / 4 | gdn | 48 | 0.294 / 0.291 | 0.229 / 0.229 | -22.04% / -21.30% |
| a3-qwen38-tp4-decode-c6-p96512 | 2 / 4 | gqa | 16 | 0.426 / 0.426 | 2.047 / 2.047 | +380.52% / +381.07% |
| a3-qwen38-tp4-decode-c6-p96512 | 2 / 4 | dense_layer | 64 | 0.327 / 0.293 | 0.684 / 0.229 | +109.03% / -21.70% |
| a3-qwen38-tp4-decode-c6-p96512 | 4 / 4 | gdn | 48 | 0.336 / 0.334 | 0.257 / 0.257 | -23.73% / -23.20% |
| a3-qwen38-tp4-decode-c6-p96512 | 4 / 4 | gqa | 16 | 0.584 / 0.585 | 2.056 / 2.056 | +251.91% / +251.53% |
| a3-qwen38-tp4-decode-c6-p96512 | 4 / 4 | dense_layer | 64 | 0.398 / 0.337 | 0.706 / 0.257 | +77.33% / -23.79% |
| a5-qwen36-tp2-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.198 / 0.193 | 0.115 / 0.115 | -41.92% / -40.59% |
| a5-qwen36-tp2-decode-c1-p126000 | 1 / 4 | gqa | 16 | 1.112 / 1.111 | 1.063 / 1.063 | -4.39% / -4.36% |
| a5-qwen36-tp2-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.426 / 0.197 | 0.352 / 0.115 | -17.46% / -41.59% |
| a5-qwen36-tp2-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.221 / 0.217 | 0.117 / 0.117 | -46.80% / -45.95% |
| a5-qwen36-tp2-decode-c2-p126000 | 2 / 4 | gqa | 16 | 1.138 / 1.138 | 1.065 / 1.065 | -6.45% / -6.44% |
| a5-qwen36-tp2-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.450 / 0.221 | 0.354 / 0.117 | -21.28% / -46.86% |
| a5-qwen36-tp2-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.261 / 0.258 | 0.129 / 0.129 | -50.38% / -49.89% |
| a5-qwen36-tp2-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.195 / 1.195 | 1.069 / 1.069 | -10.53% / -10.55% |
| a5-qwen36-tp2-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.494 / 0.261 | 0.364 / 0.129 | -26.30% / -50.43% |
| a5-qwen36-tp2-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.298 / 0.297 | 0.142 / 0.142 | -52.58% / -52.42% |
| a5-qwen36-tp2-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.287 / 1.288 | 1.074 / 1.074 | -16.60% / -16.62% |
| a5-qwen36-tp2-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.546 / 0.299 | 0.375 / 0.142 | -31.36% / -52.69% |
| a5-qwen36-tp2-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.336 / 0.336 | 0.148 / 0.148 | -55.98% / -55.97% |
| a5-qwen36-tp2-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.214 / 1.213 | 1.078 / 1.078 | -11.18% / -11.17% |
| a5-qwen36-tp2-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.555 / 0.337 | 0.380 / 0.148 | -31.51% / -56.09% |
| a5-qwen38-tp2-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.219 / 0.218 | 0.125 / 0.125 | -42.83% / -42.47% |
| a5-qwen38-tp2-decode-c1-p126000 | 1 / 4 | gqa | 16 | 1.117 / 1.117 | 1.065 / 1.065 | -4.67% / -4.69% |
| a5-qwen38-tp2-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.444 / 0.218 | 0.360 / 0.125 | -18.81% / -42.61% |
| a5-qwen38-tp2-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.243 / 0.242 | 0.128 / 0.128 | -47.39% / -47.13% |
| a5-qwen38-tp2-decode-c2-p126000 | 2 / 4 | gqa | 16 | 1.146 / 1.146 | 1.066 / 1.066 | -6.99% / -6.97% |
| a5-qwen38-tp2-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.469 / 0.242 | 0.362 / 0.128 | -22.69% / -47.26% |
| a5-qwen38-tp2-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.283 / 0.282 | 0.140 / 0.140 | -50.34% / -50.26% |
| a5-qwen38-tp2-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.193 / 1.192 | 1.071 / 1.071 | -10.22% / -10.21% |
| a5-qwen38-tp2-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.510 / 0.283 | 0.373 / 0.140 | -26.91% / -50.40% |
| a5-qwen38-tp2-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.321 / 0.321 | 0.153 / 0.153 | -52.30% / -52.27% |
| a5-qwen38-tp2-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.289 / 1.289 | 1.075 / 1.075 | -16.61% / -16.59% |
| a5-qwen38-tp2-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.563 / 0.322 | 0.384 / 0.153 | -31.87% / -52.39% |
| a5-qwen38-tp2-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.359 / 0.361 | 0.160 / 0.160 | -55.40% / -55.64% |
| a5-qwen38-tp2-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.259 / 1.259 | 1.079 / 1.079 | -14.29% / -14.28% |
| a5-qwen38-tp2-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.584 / 0.362 | 0.390 / 0.160 | -33.24% / -55.82% |
| a5-qwen36-tp4-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.166 / 0.160 | 0.097 / 0.097 | -41.60% / -39.41% |
| a5-qwen36-tp4-decode-c1-p126000 | 1 / 4 | gqa | 16 | 1.099 / 1.099 | 1.050 / 1.050 | -4.50% / -4.51% |
| a5-qwen36-tp4-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.399 / 0.164 | 0.335 / 0.097 | -16.05% / -40.91% |
| a5-qwen36-tp4-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.197 / 0.191 | 0.098 / 0.098 | -50.01% / -48.65% |
| a5-qwen36-tp4-decode-c2-p126000 | 2 / 4 | gqa | 16 | 1.128 / 1.128 | 1.051 / 1.051 | -6.83% / -6.83% |
| a5-qwen36-tp4-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.429 / 0.195 | 0.336 / 0.098 | -21.66% / -49.69% |
| a5-qwen36-tp4-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.217 / 0.211 | 0.102 / 0.102 | -52.89% / -51.50% |
| a5-qwen36-tp4-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.155 / 1.155 | 1.054 / 1.054 | -8.77% / -8.75% |
| a5-qwen36-tp4-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.452 / 0.215 | 0.340 / 0.102 | -24.69% / -52.37% |
| a5-qwen36-tp4-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.236 / 0.232 | 0.112 / 0.112 | -52.33% / -51.51% |
| a5-qwen36-tp4-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.203 / 1.203 | 1.057 / 1.057 | -12.14% / -12.12% |
| a5-qwen36-tp4-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.477 / 0.235 | 0.348 / 0.112 | -27.01% / -52.12% |
| a5-qwen36-tp4-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.255 / 0.250 | 0.116 / 0.116 | -54.34% / -53.41% |
| a5-qwen36-tp4-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.211 / 1.211 | 1.060 / 1.060 | -12.46% / -12.48% |
| a5-qwen36-tp4-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.494 / 0.253 | 0.352 / 0.116 | -28.68% / -54.07% |
| a5-qwen38-tp4-decode-c1-p126000 | 1 / 4 | gdn | 48 | 0.172 / 0.168 | 0.101 / 0.101 | -41.00% / -39.74% |
| a5-qwen38-tp4-decode-c1-p126000 | 1 / 4 | gqa | 16 | 1.095 / 1.095 | 1.051 / 1.051 | -4.00% / -4.02% |
| a5-qwen38-tp4-decode-c1-p126000 | 1 / 4 | dense_layer | 64 | 0.402 / 0.173 | 0.339 / 0.101 | -15.84% / -41.43% |
| a5-qwen38-tp4-decode-c2-p126000 | 2 / 4 | gdn | 48 | 0.210 / 0.203 | 0.103 / 0.103 | -50.89% / -49.41% |
| a5-qwen38-tp4-decode-c2-p126000 | 2 / 4 | gqa | 16 | 1.127 / 1.127 | 1.052 / 1.052 | -6.69% / -6.69% |
| a5-qwen38-tp4-decode-c2-p126000 | 2 / 4 | dense_layer | 64 | 0.439 / 0.208 | 0.340 / 0.103 | -22.52% / -50.46% |
| a5-qwen38-tp4-decode-c4-p126000 | 4 / 4 | gdn | 48 | 0.226 / 0.223 | 0.107 / 0.107 | -52.46% / -51.93% |
| a5-qwen38-tp4-decode-c4-p126000 | 4 / 4 | gqa | 16 | 1.147 / 1.148 | 1.055 / 1.055 | -8.09% / -8.10% |
| a5-qwen38-tp4-decode-c4-p126000 | 4 / 4 | dense_layer | 64 | 0.456 / 0.225 | 0.344 / 0.107 | -24.55% / -52.34% |
| a5-qwen38-tp4-decode-c6-p126000 | 6 / 4 | gdn | 48 | 0.245 / 0.244 | 0.117 / 0.117 | -52.03% / -51.85% |
| a5-qwen38-tp4-decode-c6-p126000 | 6 / 4 | gqa | 16 | 1.198 / 1.198 | 1.057 / 1.057 | -11.73% / -11.73% |
| a5-qwen38-tp4-decode-c6-p126000 | 6 / 4 | dense_layer | 64 | 0.483 / 0.245 | 0.352 / 0.117 | -27.05% / -52.05% |
| a5-qwen38-tp4-decode-c8-p126000 | 8 / 4 | gdn | 48 | 0.261 / 0.260 | 0.122 / 0.122 | -53.30% / -53.12% |
| a5-qwen38-tp4-decode-c8-p126000 | 8 / 4 | gqa | 16 | 1.206 / 1.206 | 1.060 / 1.060 | -12.09% / -12.09% |
| a5-qwen38-tp4-decode-c8-p126000 | 8 / 4 | dense_layer | 64 | 0.497 / 0.261 | 0.356 / 0.122 | -28.31% / -53.33% |
| a3-v41-tp4dp4-decode-c4-p8512 | 1 / 8 | mla | 40 | 0.888 / 0.823 | 0.805 / 0.789 | -9.41% / -4.18% |
| a3-v41-tp4dp4-decode-c4-p8512 | 1 / 8 | moe_layer | 40 | 0.888 / 0.823 | 0.805 / 0.789 | -9.41% / -4.18% |
| a3-v41-tp4dp4-decode-c4-p8512 | 2 / 8 | mla | 40 | 1.201 / 1.130 | 1.258 / 1.240 | +4.78% / +9.74% |
| a3-v41-tp4dp4-decode-c4-p8512 | 2 / 8 | moe_layer | 40 | 1.201 / 1.130 | 1.258 / 1.240 | +4.78% / +9.74% |

Layer-group statistics summarize complete layer spans, not isolated attention or FFN kernel time. Group P50 is across layer means; steady-layer P50 remains the median of per-layer call P50 values in JSON. Full layer membership, extrema, stream details and alignment assumptions remain in the SHA256-pinned evidence.

Summary: {"compared": 263, "passed": 108, "requested_sources": 280, "sources": 280, "status_counts": {"compared": 263, "failed": 17}}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
