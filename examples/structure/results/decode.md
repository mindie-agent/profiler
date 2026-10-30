# Current profiling validation

One canonical case registry and one recorded Sim package. Selected costs are freshly replayed; unchanged cases retain verified evidence from this same Sim package. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.

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
| qwen35-35b-a3-tp4-c144 | decode | 25 | 61.750 / 61.784 / 62.102 | 60.393 | -2.20% | PASS |
| qwen35-35b-a3-tp4-c320 | decode | 21 | 99.692 / 99.679 / 100.090 | 107.334 | +7.67% | PASS |
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
| a3_glm53flash_heldout_c12_p4k | decode | 13 | 23.412 / 23.008 / 23.288 | 21.869 | -6.59% | PASS |
| a3_glm53flash_heldout_c24_p12k | decode | 14 | 23.601 / 23.242 / 23.719 | 21.986 | -6.84% | PASS |
| a5_glm53flash_heldout_c12_p4k | decode | 20 | 18.133 / 18.108 / 18.148 | 15.458 | -14.75% | PASS |
| a5_glm53flash_heldout_c24_p12k | decode | 21 | 38.995 / 39.210 / 39.263 | 33.630 | -13.76% | PASS |
| a5_glm53flash_heldout_c48_p4k | decode | 26 | 43.228 / 43.355 / 43.400 | 42.692 | -1.24% | PASS |
| a3_glm53flash_static_on_c10_p131201 | decode | 68 | 22.603 / 22.348 / 23.552 | 23.704 | +4.87% | FAIL |
| a3-qwen35-tp4-longctx-p-126976-c1 | decode | 65 | 16.054 / 16.058 / 16.121 | 32.083 | +99.84% | FAIL |
| a3-qwen35-tp4-longctx-p-126976-c4 | decode | 34 | 20.465 / 20.804 / 20.975 | 33.676 | +64.55% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c1 | decode | 64 | 15.530 / 15.511 / 15.646 | 20.168 | +29.86% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c2 | decode | 55 | 16.750 / 16.724 / 16.909 | 20.827 | +24.34% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c4 | decode | 50 | 18.893 / 18.984 / 19.070 | 21.760 | +15.17% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c8 | decode | 32 | 21.417 / 21.608 / 22.212 | 23.862 | +11.42% | FAIL |
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
| a5_glm53flash_heldout_c12_p4k | 2 | 4 | 4104 | 20 | 18.133 / 18.108 / 18.148 | 15.458 | -14.75% | PASS |
| a5_glm53flash_heldout_c12_p4k | 3 | 4 | 4104 | 15 | 19.876 / 19.730 / 20.375 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 12 | 4 | 4104 | 10 | 32.310 / 32.084 / 32.482 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 6 | 4 | 4104 | 9 | 25.926 / 25.380 / 27.537 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 4 | 4 | 4104 | 5 | 21.675 / 21.618 / 21.897 | — | — | unresolved |
| a5_glm53flash_heldout_c12_p4k | 8 | 4 | 4104 | 1 | 28.855 / 28.855 / 28.855 | — | — | unresolved |

a5_glm53flash_heldout_c12_p4k: scored 20 / 60 calls; all-population pass: None.
| a5_glm53flash_heldout_c24_p12k | 24 | 4 | 12296 | 21 | 38.995 / 39.210 / 39.263 | 33.630 | -13.76% | PASS |
| a5_glm53flash_heldout_c24_p12k | 12 | 4 | 12296 | 10 | 32.978 / 32.904 / 33.062 | — | — | unresolved |
| a5_glm53flash_heldout_c24_p12k | 16 | 4 | 12296 | 6 | 34.357 / 34.349 / 34.465 | — | — | unresolved |
| a5_glm53flash_heldout_c24_p12k | 8 | 4 | 12296 | 4 | 29.935 / 29.876 / 30.133 | — | — | unresolved |

a5_glm53flash_heldout_c24_p12k: scored 21 / 41 calls; all-population pass: None.
| a5_glm53flash_heldout_c48_p4k | 48 | 4 | 4104 | 26 | 43.228 / 43.355 / 43.400 | 42.692 | -1.24% | PASS |
| a5_glm53flash_heldout_c48_p4k | 32 | 4 | 4104 | 9 | 38.189 / 38.157 / 38.314 | — | — | unresolved |
| a5_glm53flash_heldout_c48_p4k | 24 | 4 | 4104 | 2 | 37.382 / 37.382 / 37.552 | — | — | unresolved |

a5_glm53flash_heldout_c48_p4k: scored 26 / 37 calls; all-population pass: None.
| a3_glm53flash_static_on_c10_p131201 | 1 | 6 | 131201 | 68 | 22.603 / 22.348 / 23.552 | 23.704 | +4.87% | PASS |
| a3_glm53flash_static_on_c10_p131201 | 4 | 6 | 131201 | 13 | 28.251 / 27.985 / 28.308 | 37.773 | +33.71% | FAIL |
| a3_glm53flash_static_on_c10_p131201 | 8 | 6 | 131201 | 12 | 31.580 / 31.520 / 31.998 | 53.766 | +70.25% | FAIL |
| a3_glm53flash_static_on_c10_p131201 | 2 | 6 | 131201 | 3 | 25.713 / 24.344 / 28.811 | 28.392 | +10.42% | PASS |
| a3_glm53flash_static_on_c10_p131201 | 3 | 6 | 131201 | 1 | 31.415 / 31.415 / 31.415 | 33.053 | +5.22% | PASS |
| a3_glm53flash_static_on_c10_p131201 | 7 | 6 | 131201 | 1 | 35.748 / 35.748 / 35.748 | 49.878 | +39.53% | FAIL |

a3_glm53flash_static_on_c10_p131201: scored 98 / 98 calls; all-population pass: False.
Context: same_run_prompt_plus_requested_output_bounds; representative 131201, bounds 131201–131265 tokens. 131201 is a conditional initial-context representative. The requested 64 output tokens only bound context growth; no per-step sequence-length values are retained. KV cache capacity is not active context.
| a3-qwen35-tp4-longctx-p-126976-c4 | 4 | 2 | 126976 | 34 | 20.465 / 20.804 / 20.975 | 33.676 | +64.55% | FAIL |
| a3-qwen35-tp4-longctx-p-126976-c4 | 1 | 2 | 126976 | 16 | 16.107 / 16.100 / 16.156 | 32.083 | +99.19% | FAIL |
| a3-qwen35-tp4-longctx-p-126976-c4 | 2 | 2 | 126976 | 15 | 17.687 / 17.706 / 17.759 | 32.742 | +85.12% | FAIL |

a3-qwen35-tp4-longctx-p-126976-c4: scored 65 / 65 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 126976, bounds 126976–127104 tokens.
| a3-qwen35-tp4-longctx-p-65536-c2 | 2 | 2 | 65536 | 55 | 16.750 / 16.724 / 16.909 | 20.827 | +24.34% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c2 | 1 | 2 | 65536 | 11 | 15.583 / 15.520 / 15.562 | 20.168 | +29.42% | FAIL |

a3-qwen35-tp4-longctx-p-65536-c2: scored 66 / 66 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65664 tokens.
| a3-qwen35-tp4-longctx-p-65536-c4 | 4 | 2 | 65536 | 50 | 18.893 / 18.984 / 19.070 | 21.760 | +15.17% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c4 | 1 | 2 | 65536 | 8 | 15.649 / 15.561 / 16.432 | 20.168 | +28.88% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c4 | 2 | 2 | 65536 | 7 | 16.789 / 16.628 / 17.557 | 20.827 | +24.05% | FAIL |

a3-qwen35-tp4-longctx-p-65536-c4: scored 65 / 65 calls; all-population pass: False.
Context: same_capture_client_prompt_usage_and_requested_output_budget; not_per_call_KV_tensor_values; representative 65536, bounds 65536–65664 tokens.
| a3-qwen35-tp4-longctx-p-65536-c8 | 8 | 2 | 65536 | 32 | 21.417 / 21.608 / 22.212 | 23.862 | +11.42% | PASS |
| a3-qwen35-tp4-longctx-p-65536-c8 | 4 | 2 | 65536 | 17 | 18.901 / 18.818 / 19.256 | 21.760 | +15.13% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c8 | 2 | 2 | 65536 | 8 | 16.891 / 16.719 / 17.533 | 20.827 | +23.30% | FAIL |
| a3-qwen35-tp4-longctx-p-65536-c8 | 1 | 2 | 65536 | 8 | 15.502 / 15.507 / 15.581 | 20.168 | +30.10% | FAIL |

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

Summary: {"compared": 108, "passed": 85, "requested_sources": 108, "sources": 108, "status_counts": {"compared": 108}}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
