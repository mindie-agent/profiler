# Current profiling validation

One canonical case registry and one recorded Sim package. All costs are fresh in this run. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.

| Case | Phase | Calls | Real mean / P50 / P90 ms | Sim ms | Error | Status |
|---|---|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c4-livepre | decode | 46 | 29.762 / 29.664 / 30.046 | 29.545 | -0.73% | PASS |
| glm53flash-a3-tp16-c16-livepre | decode | 37 | 41.069 / 40.940 / 41.282 | 40.882 | -0.46% | PASS |
| glm53flash-a3-tp16-c2 | decode | 46 | 34.118 / 33.910 / 35.073 | 31.018 | -9.09% | PASS |
| glm53flash-a3-tp16-c4 | decode | 46 | 39.841 / 39.798 / 40.057 | 36.251 | -9.01% | PASS |
| glm53flash-a5-tp8-c3 | decode | 53 | 21.068 / 21.057 / 21.170 | 18.663 | -11.41% | PASS |
| glm53flash-a5-tp8-c96 | decode | 27 | 57.590 / 57.573 / 57.734 | 59.368 | +3.09% | PASS |
| glm53flash-a5-tp8-c1 | decode | 65 | 15.683 / 15.670 / 15.738 | 13.652 | -12.95% | PASS |
| a5_kimi_k3_p32768_c1 | decode | 63 | 32.555 / 32.533 / 32.674 | 28.561 | -12.27% | PASS |
| v4flash-a3-tp8-c4 | decode | 104 | 32.486 / 32.416 / 32.734 | 29.272 | -9.89% | PASS |
| v4flash-a3-tp8-c8 | decode | 104 | 37.763 / 37.868 / 38.082 | 34.707 | -8.09% | PASS |
| a3_glm53_dc4k_b1 | decode | 74 | 38.955 / 38.943 / 39.036 | 38.046 | -2.33% | PASS |
| a3_glm53_dc4k_b2 | decode | 70 | 40.970 / 40.935 / 41.046 | 39.767 | -2.94% | PASS |
| a3_glm53_dc4k_b4 | decode | 67 | 43.438 / 43.437 / 43.598 | 38.631 | -11.07% | PASS |
| a3_glm53_dc4k_b8 | decode | 61 | 47.113 / 47.149 / 47.402 | 44.125 | -6.34% | PASS |
| a3_glm53_dc16k_b1 | decode | 74 | 39.112 / 39.105 / 39.196 | 38.334 | -1.99% | PASS |
| qwen35-397b-a3-tp16-c48 | decode | 23 | 76.089 / 76.132 / 76.632 | 61.285 | -19.46% | FAIL |
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
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | decode | 75 | 26.328 / 26.306 / 26.336 | — | — | failed |
| a5_glm53flash_tp8_c16_p4k | decode | 30 | 33.031 / 33.026 / 33.164 | 30.187 | -8.61% | PASS |
| a5_glm53flash_tp8_c16_p8k | decode | 32 | 33.616 / 33.626 / 33.710 | 30.768 | -8.47% | PASS |
| a5_glm53flash_tp8_c32_p4k | decode | 31 | 37.669 / 37.665 / 37.761 | 35.809 | -4.94% | PASS |
| a5_glm53flash_tp8_c32_p8k | decode | 35 | 38.713 / 38.722 / 38.759 | 36.852 | -4.81% | PASS |
| a5_glm53flash_tp8_c4_p8k | decode | 11 | 21.418 / 21.408 / 21.432 | 18.623 | -13.05% | PASS |
| a5_glm53flash_tp8_c64_p4k | decode | 31 | 46.528 / 46.499 / 46.645 | 47.971 | +3.10% | PASS |
| a5_glm53flash_tp8_c8_p4k | decode | 30 | 28.833 / 28.828 / 28.885 | 25.915 | -10.12% | PASS |
| a3_glm53flash_tp16_aclgraph_c16 | decode | 50 | 53.893 / 53.871 / 54.021 | 49.637 | -7.90% | PASS |
| a3_glm53flash_tp16_aclgraph_c32 | decode | 49 | 69.361 / 69.418 / 69.528 | 65.400 | -5.71% | PASS |
| a3_glm53flash_tp16_aclgraph_c64 | decode | 47 | 97.375 / 97.487 / 97.895 | 97.858 | +0.50% | PASS |
| a3_glm53flash_tp16_aclgraph_c8 | decode | 47 | 46.859 / 46.817 / 47.175 | 42.056 | -10.25% | PASS |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k | decode | 129 | 14.929 / 14.914 / 14.929 | — | — | failed |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k | decode | 105 | 18.625 / 18.616 / 18.640 | — | — | failed |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k | decode | 151 | 13.239 / 13.209 / 13.227 | — | — | failed |
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
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k | decode | 73 | 27.286 / 27.266 / 27.290 | — | — | failed |
| qwen35-35b-a3-tp4-c144 | decode | 25 | 61.750 / 61.784 / 62.102 | 60.393 | -2.20% | PASS |
| qwen35-35b-a3-tp4-c320 | decode | 21 | 99.692 / 99.679 / 100.090 | 107.334 | +7.67% | PASS |
| qwen36-a3-tp4-c64 | decode | 27 | 62.520 / 62.407 / 62.858 | 61.622 | -1.44% | PASS |
| qwen36-a3-tp4-c128 | decode | 22 | 97.566 / 97.506 / 97.890 | 115.144 | +18.02% | FAIL |
| qwen38-a3-tp4-c64 | decode | 27 | 62.648 / 62.586 / 63.058 | 61.622 | -1.64% | PASS |
| qwen38-a3-tp4-c128 | decode | 22 | 97.457 / 97.455 / 97.787 | 115.144 | +18.15% | FAIL |
| qwen35-35b-a5-tp4-c8-eager | decode | 78 | 167.719 / 166.703 / 176.962 | 6.790 | -95.95% | FAIL |
| qwen35-35b-a5-tp4-c16-eager | decode | 81 | 170.298 / 167.098 / 186.266 | 7.899 | -95.36% | FAIL |
| qwen35-35b-a5-tp4-c32-eager | decode | 78 | 168.740 / 168.003 / 175.220 | 8.931 | -94.71% | FAIL |
| a5_qwen36_highconc_c4 | decode | 73 | 13.342 / 13.245 / 13.485 | 7.911 | -40.71% | FAIL |
| a5_qwen36_highconc_c40 | decode | 54 | 20.684 / 20.612 / 21.334 | 14.079 | -31.93% | FAIL |
| a5_qwen36_highconc_c128 | decode | 38 | 32.609 / 32.227 / 33.851 | 24.198 | -25.79% | FAIL |
| a5_qwen38_highconc_c4 | decode | 45 | 13.027 / 13.005 / 13.167 | 7.559 | -41.97% | FAIL |
| a5_qwen38_highconc_c32 | decode | 48 | 22.791 / 22.711 / 22.894 | 14.569 | -36.08% | FAIL |
| a5_qwen38_highconc_c128 | decode | 29 | 45.689 / 45.690 / 45.735 | 35.495 | -22.31% | FAIL |

Summary: {"compared": 76, "passed": 64, "requested_sources": 81, "sources": 81, "status_counts": {"compared": 76, "failed": 5}}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
