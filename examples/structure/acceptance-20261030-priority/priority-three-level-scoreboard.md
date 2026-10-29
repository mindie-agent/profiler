# Priority Decode body, layer and operator scoreboard

Coverage status: **partial**. Missing predictions and unmatched roles stay visible.

Body: **6/24 prediction arms passed**; 23 unique sources, 83 measured geometry populations, 1564 unique complete Forwards (includes deferred populations).

Operator strict accuracy: heavy_relative_15pct: **0/1**; micro_absolute_15us: **11/11**. Conditional references are excluded.

Local replay receipts with explicit comparison coverage. Body errors are measured wall-clock differences; operator priorities are nonadditive kernel activity residuals per complete Forward.

## Whole Decode Body — sorted by absolute ms error

| Case / variant | Status | Calls | Real Mean / P50 / P90 ms | Activity ms | Sim ms | Diff ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / None / `5d7c051180a9` | compared | 18 | 119.054 / 119.131 / 119.486 | 118.048 | 1404.679 | 1285.625 | 1079.864% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / None / `5d7c051180a9` | compared | 23 | 76.089 / 76.132 / 76.632 | 75.005 | 512.836 | 436.747 | 573.995% |
| a3_glm53_dc4k_b8:q1_b8_m8 / legacy_glm53_78_layer_w4a8 / `5d7c051180a9` | compared | 61 | 47.113 / 47.149 / 47.402 | — | 116.779 | 69.666 | 147.868% |
| a3_glm53_dc4k_b4:q1_b4_m4 / legacy_glm53_78_layer_w4a8 / `5d7c051180a9` | compared | 67 | 43.438 / 43.437 / 43.598 | — | 72.002 | 28.564 | 65.760% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / None / `5d7c051180a9` | compared | 37 | 41.069 / 40.940 / 41.282 | 39.691 | 64.735 | 23.665 | 57.624% |
| qwen36-a5-tp2-c96:q4_b96_m384 / None / `5d7c051180a9` | compared | 24 | 63.853 / 63.562 / 65.419 | 63.565 | 45.126 | -18.727 | -29.328% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / retained_longctx_declaration_baseline / `5d7c051180a9` | compared | 63 | 32.555 / 32.533 / 32.674 | — | 50.999 | 18.443 | 56.651% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / kimi_current_checkpoint_reference_conditional / `5d7c051180a9` | compared | 63 | 32.555 / 32.533 / 32.674 | — | 46.902 | 14.347 | 44.069% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / None / `5d7c051180a9` | compared | 76 | 28.585 / 28.571 / 28.704 | 28.300 | 14.677 | -13.908 | -48.655% |
| qwen36-a5-tp2-c12:q4_b12_m48 / None / `5d7c051180a9` | compared | 55 | 24.226 / 24.053 / 24.711 | 23.858 | 10.999 | -13.227 | -54.600% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / None / `5d7c051180a9` | compared | 79 | 21.957 / 22.001 / 22.068 | 21.571 | 10.219 | -11.738 | -53.458% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None / `5d7c051180a9` | compared | 46 | 29.762 / 29.664 / 30.046 | 28.242 | 37.949 | 8.187 | 27.510% |
| a3_glm53_dc4k_b2:q1_b2_m2 / legacy_glm53_78_layer_w4a8 / `5d7c051180a9` | compared | 70 | 40.970 / 40.935 / 41.046 | — | 48.792 | 7.823 | 19.093% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / None / `5d7c051180a9` | compared | 84 | 11.551 / 11.482 / 11.818 | 11.135 | 5.049 | -6.503 | -56.294% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / None / `5d7c051180a9` | compared | 53 | 21.068 / 21.057 / 21.170 | 20.805 | 14.583 | -6.484 | -30.778% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / None / `5d7c051180a9` | compared | 65 | 15.683 / 15.670 / 15.738 | 15.421 | 10.029 | -5.654 | -36.051% |
| qwen36-a5-tp2-c1:q4_b1_m4 / None / `5d7c051180a9` | compared | 85 | 12.318 / 12.279 / 12.362 | 11.956 | 7.413 | -4.905 | -39.822% |
| v4flash-a3-tp8-c4:q2_b4_m8 / None / `5d7c051180a9` | compared | 104 | 32.486 / 32.416 / 32.734 | 30.611 | 27.589 | -4.897 | -15.075% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / None / `5d7c051180a9` | compared | 27 | 57.590 / 57.573 / 57.734 | 57.355 | 54.015 | -3.574 | -6.207% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / None / `5d7c051180a9` | compared | 46 | 34.118 / 33.910 / 35.073 | 32.625 | 30.804 | -3.314 | -9.714% |
| a3_glm53_dc16k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 / `5d7c051180a9` | compared | 74 | 39.112 / 39.105 / 39.196 | — | 36.961 | -2.151 | -5.501% |
| v4flash-a3-tp8-c8:q2_b8_m16 / None / `5d7c051180a9` | compared | 104 | 37.763 / 37.868 / 38.082 | 36.154 | 35.758 | -2.005 | -5.309% |
| a3_glm53_dc4k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 / `5d7c051180a9` | compared | 74 | 38.955 / 38.943 / 39.036 | — | 36.961 | -1.994 | -5.119% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None / `5d7c051180a9` | compared | 46 | 39.841 / 39.798 / 40.057 | 38.324 | 37.949 | -1.892 | -4.750% |
| glm53flash-a3-tp16-c4-livepre:q6_b3_m18 / None / `unknown` | prediction_deferred | 11 | 28.126 / 28.052 / 28.206 | 26.591 | — | — | —% |
| glm53flash-a3-tp16-c4-livepre:q6_b1_m6 / None / `unknown` | prediction_deferred | 10 | 23.447 / 23.179 / 23.585 | 21.956 | — | — | —% |
| glm53flash-a3-tp16-c4-livepre:q6_b2_m12 / None / `unknown` | prediction_deferred | 6 | 26.154 / 25.840 / 27.873 | 24.653 | — | — | —% |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 / None / `unknown` | prediction_deferred | 16 | 33.619 / 33.419 / 33.980 | 32.091 | — | — | —% |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 / None / `unknown` | prediction_deferred | 13 | 23.486 / 23.363 / 23.611 | 22.012 | — | — | —% |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 / None / `unknown` | prediction_deferred | 9 | 28.227 / 28.041 / 29.858 | 26.716 | — | — | —% |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 / None / `unknown` | prediction_deferred | 7 | 35.014 / 34.765 / 36.431 | 33.490 | — | — | —% |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 / None / `unknown` | prediction_deferred | 6 | 37.826 / 37.534 / 39.879 | 36.322 | — | — | —% |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 / None / `unknown` | prediction_deferred | 5 | 26.385 / 25.916 / 28.429 | 24.885 | — | — | —% |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 / None / `unknown` | prediction_deferred | 4 | 43.282 / 42.788 / 45.252 | 41.753 | — | — | —% |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 / None / `unknown` | prediction_deferred | 4 | 30.244 / 29.665 / 32.051 | 28.749 | — | — | —% |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 / None / `unknown` | prediction_deferred | 3 | 35.070 / 34.379 / 36.534 | 33.686 | — | — | —% |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 / None / `unknown` | prediction_deferred | 2 | 41.544 / 41.544 / 43.477 | 40.004 | — | — | —% |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 / None / `unknown` | prediction_deferred | 1 | 44.811 / 44.811 / 44.811 | 43.263 | — | — | —% |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 / None / `unknown` | prediction_deferred | 1 | 44.980 / 44.980 / 44.980 | 43.459 | — | — | —% |
| glm53flash-a3-tp16-c2:q6_b1_m6 / None / `unknown` | prediction_deferred | 12 | 33.269 / 33.260 / 33.461 | 31.832 | — | — | —% |
| glm53flash-a3-tp16-c4:q6_b1_m6 / None / `unknown` | prediction_deferred | 8 | 33.514 / 33.637 / 34.066 | 32.078 | — | — | —% |
| glm53flash-a3-tp16-c4:q6_b3_m18 / None / `unknown` | prediction_deferred | 4 | 36.347 / 36.075 / 37.439 | 34.842 | — | — | —% |
| glm53flash-a3-tp16-c4:q6_b2_m12 / None / `unknown` | prediction_deferred | 3 | 35.089 / 34.649 / 36.996 | 33.596 | — | — | —% |
| v4flash-a3-tp8-c4:q2_b1_m2 / None / `unknown` | prediction_deferred | 4 | 29.500 / 29.512 / 29.661 | 27.578 | — | — | —% |
| v4flash-a3-tp8-c8:q2_b2_m4 / None / `unknown` | prediction_deferred | 3 | 31.294 / 31.234 / 31.612 | 29.525 | — | — | —% |
| v4flash-a3-tp8-c8:q2_b1_m2 / None / `unknown` | prediction_deferred | 2 | 29.355 / 29.355 / 29.422 | 27.414 | — | — | —% |
| v4flash-a3-tp8-c8:q2_b4_m8 / None / `unknown` | prediction_deferred | 2 | 32.488 / 32.488 / 32.562 | 30.756 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b1_m4 / None / `unknown` | prediction_deferred | 3 | 8.739 / 8.828 / 8.913 | 8.327 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b60_m240 / None / `unknown` | prediction_deferred | 1 | 21.444 / 21.444 / 21.444 | 21.053 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b56_m224 / None / `unknown` | prediction_deferred | 1 | 20.972 / 20.972 / 20.972 | 20.566 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b52_m208 / None / `unknown` | prediction_deferred | 1 | 20.950 / 20.950 / 20.950 | 20.546 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b48_m192 / None / `unknown` | prediction_deferred | 1 | 20.070 / 20.070 / 20.070 | 19.634 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b44_m176 / None / `unknown` | prediction_deferred | 1 | 20.103 / 20.103 / 20.103 | 19.666 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b40_m160 / None / `unknown` | prediction_deferred | 1 | 19.908 / 19.908 / 19.908 | 19.464 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b34_m136 / None / `unknown` | prediction_deferred | 1 | 19.149 / 19.149 / 19.149 | 18.712 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b26_m104 / None / `unknown` | prediction_deferred | 1 | 16.774 / 16.774 / 16.774 | 16.340 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b18_m72 / None / `unknown` | prediction_deferred | 1 | 15.810 / 15.810 / 15.810 | 15.372 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b12_m48 / None / `unknown` | prediction_deferred | 1 | 15.124 / 15.124 / 15.124 | 14.696 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b10_m40 / None / `unknown` | prediction_deferred | 1 | 14.944 / 14.944 / 14.944 | 14.515 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b8_m32 / None / `unknown` | prediction_deferred | 1 | 14.550 / 14.550 / 14.550 | 14.120 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b4_m16 / None / `unknown` | prediction_deferred | 1 | 11.638 / 11.638 / 11.638 | 11.221 | — | — | —% |
| qwen35-35b-a5-tp4-c64-graph:q4_b2_m8 / None / `unknown` | prediction_deferred | 1 | 9.812 / 9.812 / 9.812 | 9.397 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b124_m496 / None / `unknown` | prediction_deferred | 2 | 28.335 / 28.335 / 28.358 | 28.063 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b6_m24 / None / `unknown` | prediction_deferred | 2 | 12.927 / 12.927 / 13.229 | 12.506 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b2_m8 / None / `unknown` | prediction_deferred | 2 | 9.874 / 9.874 / 9.959 | 9.460 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b1_m4 / None / `unknown` | prediction_deferred | 1 | 8.488 / 8.488 / 8.488 | 8.078 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b120_m480 / None / `unknown` | prediction_deferred | 1 | 27.852 / 27.852 / 27.852 | 27.567 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b116_m464 / None / `unknown` | prediction_deferred | 1 | 27.866 / 27.866 / 27.866 | 27.596 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b108_m432 / None / `unknown` | prediction_deferred | 1 | 27.249 / 27.249 / 27.249 | 26.956 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b96_m384 / None / `unknown` | prediction_deferred | 1 | 24.930 / 24.930 / 24.930 | 24.521 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b84_m336 / None / `unknown` | prediction_deferred | 1 | 25.698 / 25.698 / 25.698 | 25.282 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b72_m288 / None / `unknown` | prediction_deferred | 1 | 24.146 / 24.146 / 24.146 | 23.730 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b58_m232 / None / `unknown` | prediction_deferred | 1 | 21.377 / 21.377 / 21.377 | 20.980 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b50_m200 / None / `unknown` | prediction_deferred | 1 | 21.026 / 21.026 / 21.026 | 20.635 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b42_m168 / None / `unknown` | prediction_deferred | 1 | 19.976 / 19.976 / 19.976 | 19.526 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b38_m152 / None / `unknown` | prediction_deferred | 1 | 19.185 / 19.185 / 19.185 | 18.745 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b28_m112 / None / `unknown` | prediction_deferred | 1 | 16.372 / 16.372 / 16.372 | 15.929 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b18_m72 / None / `unknown` | prediction_deferred | 1 | 15.838 / 15.838 / 15.838 | 15.409 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b12_m48 / None / `unknown` | prediction_deferred | 1 | 15.127 / 15.127 / 15.127 | 14.696 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b10_m40 / None / `unknown` | prediction_deferred | 1 | 14.935 / 14.935 / 14.935 | 14.508 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b8_m32 / None / `unknown` | prediction_deferred | 1 | 14.334 / 14.334 / 14.334 | 13.899 | — | — | —% |
| qwen35-35b-a5-tp4-c128-graph:q4_b4_m16 / None / `unknown` | prediction_deferred | 1 | 11.424 / 11.424 / 11.424 | 11.005 | — | — | —% |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 / None / `unknown` | prediction_deferred | 6 | 8.747 / 8.803 / 8.838 | 8.336 | — | — | —% |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 / None / `unknown` | prediction_deferred | 1 | 9.700 / 9.700 / 9.700 | 9.287 | — | — | —% |

## Layer 0 and steady layer groups

The steady P50 column is median of per-layer call P50, unless a separately linked receipt supplies exact pooled statistics.

| Case | Group | Layers | Real Mean ms | Median layer-call P50 ms | Sim Mean ms | Mean error |
|---|---|---:|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / None | Layer 0 / gdn / moe_layer | 1 | 2.0473 | 1.9983 | 23.3595 | 1041.003% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / None | Steady / gdn / moe_layer | 44 | 1.9572 | 1.9352 | 23.3595 | 1093.507% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / None | Steady / gqa / moe_layer | 15 | 2.0544 | 2.0314 | 23.5668 | 1047.154% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / None | Layer 0 / gdn / moe_layer | 1 | 1.3503 | 1.2865 | 8.5130 | 530.434% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / None | Steady / gdn / moe_layer | 44 | 1.2329 | 1.2077 | 8.5130 | 590.482% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / None | Steady / gqa / moe_layer | 15 | 1.3614 | 1.3469 | 8.6502 | 535.374% |
| a3_glm53_dc4k_b8:q1_b8_m8 / legacy_glm53_78_layer_w4a8 | Layer 0 / mla / dense_layer | 1 | 0.4244 | 0.4227 | 0.9647 | 127.307% |
| a3_glm53_dc4k_b8:q1_b8_m8 / legacy_glm53_78_layer_w4a8 | Steady / mla / dense_layer | 2 | 0.4119 | 0.4111 | 0.9647 | 134.232% |
| a3_glm53_dc4k_b8:q1_b8_m8 / legacy_glm53_78_layer_w4a8 | Steady / mla / moe_layer | 75 | 0.6105 | 0.5863 | 1.5185 | 148.705% |
| a3_glm53_dc4k_b4:q1_b4_m4 / legacy_glm53_78_layer_w4a8 | Layer 0 / mla / dense_layer | 1 | 0.4118 | 0.4071 | 0.6140 | 49.118% |
| a3_glm53_dc4k_b4:q1_b4_m4 / legacy_glm53_78_layer_w4a8 | Steady / mla / dense_layer | 2 | 0.3968 | 0.3931 | 0.6140 | 54.728% |
| a3_glm53_dc4k_b4:q1_b4_m4 / legacy_glm53_78_layer_w4a8 | Steady / mla / moe_layer | 75 | 0.5622 | 0.5411 | 0.9355 | 66.402% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / None | Layer 0 / kda / dense_layer | 1 | 1.0092 | 0.8498 | 0.7670 | -24.004% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / None | Steady / kda / dense_layer | 2 | 0.4246 | 0.4245 | 0.7670 | 80.631% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / None | Steady / mla / moe_layer | 11 | 1.3710 | 1.3767 | 1.5678 | 14.350% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / None | Steady / kda / moe_layer | 31 | 0.7767 | 0.7741 | 1.4577 | 87.674% |
| qwen36-a5-tp2-c96:q4_b96_m384 / None | Layer 0 / gdn / dense_layer | 1 | 1.3691 | 1.0682 | 0.7556 | -44.813% |
| qwen36-a5-tp2-c96:q4_b96_m384 / None | Steady / gdn / dense_layer | 47 | 1.0584 | 1.0584 | 0.7556 | -28.615% |
| qwen36-a5-tp2-c96:q4_b96_m384 / None | Steady / gqa / dense_layer | 16 | 0.7931 | 0.7928 | 0.5537 | -30.186% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / retained_longctx_declaration_baseline | Layer 0 / kda / dense_layer | 1 | 0.2579 | 0.2383 | 0.2268 | -12.056% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / retained_longctx_declaration_baseline | Steady / kda / moe_layer | 68 | 0.3399 | 0.3386 | 0.5567 | 63.759% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / retained_longctx_declaration_baseline | Steady / mla / moe_layer | 24 | 0.3835 | 0.3747 | 0.5382 | 40.326% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / kimi_current_checkpoint_reference_conditional | Layer 0 / kda / dense_layer | 1 | 0.2579 | 0.2383 | 0.1767 | -31.494% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / kimi_current_checkpoint_reference_conditional | Steady / kda / moe_layer | 68 | 0.3399 | 0.3386 | 0.5109 | 50.290% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / kimi_current_checkpoint_reference_conditional | Steady / mla / moe_layer | 24 | 0.3835 | 0.3747 | 0.4993 | 30.197% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / None | Layer 0 / gdn / moe_layer | 1 | 0.7544 | 0.7238 | 0.3803 | -49.595% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / None | Steady / gdn / moe_layer | 29 | 0.7199 | 0.7199 | 0.3803 | -47.175% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / None | Steady / gqa / moe_layer | 10 | 0.6953 | 0.6941 | 0.3269 | -52.991% |
| qwen36-a5-tp2-c12:q4_b12_m48 / None | Layer 0 / gdn / dense_layer | 1 | 0.6168 | 0.3931 | 0.1825 | -70.421% |
| qwen36-a5-tp2-c12:q4_b12_m48 / None | Steady / gdn / dense_layer | 47 | 0.4044 | 0.4033 | 0.1825 | -54.884% |
| qwen36-a5-tp2-c12:q4_b12_m48 / None | Steady / gqa / dense_layer | 16 | 0.2846 | 0.2843 | 0.1401 | -50.788% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / None | Layer 0 / gdn / moe_layer | 1 | 0.7737 | 0.8216 | 0.2645 | -65.808% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / None | Steady / gdn / moe_layer | 29 | 0.5470 | 0.5467 | 0.2645 | -51.637% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / None | Steady / gqa / moe_layer | 10 | 0.5320 | 0.5323 | 0.2283 | -57.085% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None | Layer 0 / kda / dense_layer | 1 | 0.8292 | 0.7249 | 0.4474 | -46.044% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None | Steady / kda / dense_layer | 2 | 0.2964 | 0.2961 | 0.4474 | 50.956% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None | Steady / mla / moe_layer | 11 | 0.9295 | 0.9276 | 0.8975 | -3.445% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None | Steady / kda / moe_layer | 31 | 0.5827 | 0.5821 | 0.8624 | 48.002% |
| a3_glm53_dc4k_b2:q1_b2_m2 / legacy_glm53_78_layer_w4a8 | Layer 0 / mla / dense_layer | 1 | 0.4105 | 0.3960 | 0.4397 | 7.121% |
| a3_glm53_dc4k_b2:q1_b2_m2 / legacy_glm53_78_layer_w4a8 | Steady / mla / dense_layer | 2 | 0.3997 | 0.3865 | 0.4397 | 10.026% |
| a3_glm53_dc4k_b2:q1_b2_m2 / legacy_glm53_78_layer_w4a8 | Steady / mla / moe_layer | 75 | 0.5293 | 0.5092 | 0.6330 | 19.591% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / None | Layer 0 / gdn / moe_layer | 1 | 0.3868 | 0.2973 | 0.1242 | -67.899% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / None | Steady / gdn / moe_layer | 29 | 0.2819 | 0.2827 | 0.1242 | -55.959% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / None | Steady / gqa / moe_layer | 10 | 0.2989 | 0.2992 | 0.1324 | -55.697% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / None | Layer 0 / kda / dense_layer | 1 | 0.4650 | 0.4745 | 0.1650 | -64.516% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / None | Steady / kda / dense_layer | 2 | 0.2383 | 0.2328 | 0.1650 | -30.761% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / None | Steady / mla / moe_layer | 11 | 0.6392 | 0.6337 | 0.3436 | -46.243% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / None | Steady / kda / moe_layer | 31 | 0.4224 | 0.4216 | 0.3325 | -21.271% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / None | Layer 0 / kda / dense_layer | 1 | 0.4222 | 0.4383 | 0.1447 | -65.729% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / None | Steady / kda / dense_layer | 2 | 0.2487 | 0.2314 | 0.1447 | -41.813% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / None | Steady / mla / moe_layer | 11 | 0.4952 | 0.4903 | 0.2331 | -52.924% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / None | Steady / kda / moe_layer | 31 | 0.3005 | 0.2985 | 0.2268 | -24.526% |
| qwen36-a5-tp2-c1:q4_b1_m4 / None | Layer 0 / gdn / dense_layer | 1 | 0.2400 | 0.1984 | 0.1154 | -51.909% |
| qwen36-a5-tp2-c1:q4_b1_m4 / None | Steady / gdn / dense_layer | 47 | 0.1919 | 0.1915 | 0.1154 | -39.861% |
| qwen36-a5-tp2-c1:q4_b1_m4 / None | Steady / gqa / dense_layer | 16 | 0.1880 | 0.1876 | 0.1171 | -37.704% |
| v4flash-a3-tp8-c4:q2_b4_m8 / None | Layer 0 / mla / moe_layer | 1 | 0.7568 | 0.7178 | 0.5579 | -26.289% |
| v4flash-a3-tp8-c4:q2_b4_m8 / None | Steady / mla / moe_layer | 42 | 0.7543 | 0.7537 | 0.6436 | -14.674% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / None | Layer 0 / kda / dense_layer | 1 | 0.6036 | 0.5889 | 0.6393 | 5.904% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / None | Steady / kda / dense_layer | 2 | 0.5724 | 0.5723 | 0.6393 | 11.686% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / None | Steady / mla / moe_layer | 11 | 2.2334 | 2.2329 | 1.3768 | -38.353% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / None | Steady / kda / moe_layer | 31 | 1.0088 | 1.0088 | 1.1920 | 18.161% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / None | Layer 0 / kda / dense_layer | 1 | 0.5732 | 0.5010 | 0.3996 | -30.294% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / None | Steady / kda / dense_layer | 2 | 0.5965 | 0.5414 | 0.3996 | -33.013% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / None | Steady / mla / moe_layer | 11 | 0.9546 | 0.9395 | 0.7215 | -24.418% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / None | Steady / kda / moe_layer | 31 | 0.7032 | 0.6643 | 0.6990 | -0.602% |
| a3_glm53_dc16k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 | Layer 0 / mla / dense_layer | 1 | 0.4020 | 0.3967 | 0.3526 | -12.294% |
| a3_glm53_dc16k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 | Steady / mla / dense_layer | 2 | 0.3934 | 0.3879 | 0.3526 | -10.369% |
| a3_glm53_dc16k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 | Steady / mla / moe_layer | 75 | 0.5045 | 0.4834 | 0.4787 | -5.110% |
| v4flash-a3-tp8-c8:q2_b8_m16 / None | Layer 0 / mla / moe_layer | 1 | 0.8072 | 0.7668 | 0.7432 | -7.929% |
| v4flash-a3-tp8-c8:q2_b8_m16 / None | Steady / mla / moe_layer | 42 | 0.8787 | 0.8831 | 0.8337 | -5.126% |
| a3_glm53_dc4k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 | Layer 0 / mla / dense_layer | 1 | 0.3943 | 0.3854 | 0.3526 | -10.563% |
| a3_glm53_dc4k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 | Steady / mla / dense_layer | 2 | 0.3841 | 0.3775 | 0.3526 | -8.207% |
| a3_glm53_dc4k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 | Steady / mla / moe_layer | 75 | 0.5031 | 0.4848 | 0.4787 | -4.844% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None | Layer 0 / kda / dense_layer | 1 | 0.6141 | 0.5825 | 0.4474 | -27.138% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None | Steady / kda / dense_layer | 2 | 0.6160 | 0.5541 | 0.4474 | -27.368% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None | Steady / mla / moe_layer | 11 | 1.1665 | 1.1644 | 0.8975 | -23.064% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None | Steady / kda / moe_layer | 31 | 0.8101 | 0.8087 | 0.8624 | 6.462% |

## Heavy >50us operators — activity residual priority

| Case | Operator / role | Calls | Real / Sim us | Diff us | Absolute ms / Forward | Tier pass |
|---|---|---:|---:|---:|---:|---|
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | GroupedMatmulSituQuant / grouped_gate_up_situ_quant | 5796 | 74.250 / 7.735 | -66.515 | 6.119 | None (reference_only) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | SituMxQuant / shared.situ_quant | 5796 | 65.155 / 1.312 | -63.843 | 5.874 | False (compared) |

## Micro <=50us operators — activity residual priority

| Case | Operator / role | Calls | Real / Sim us | Diff us | Absolute ms / Forward | Tier pass |
|---|---|---:|---:|---:|---:|---|
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | QuantBatchMatmulV4 / shared.gate_up | 5796 | 30.427 / 3.963 | -26.464 | 2.435 | None (reference_only) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | QuantBatchMatmulV4 / shared.down | 5796 | 13.143 / 1.578 | -11.565 | 1.064 | None (reference_only) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | DynamicMxQuant / latent_down.quantize | 11592 | 4.138 / 1.312 | -2.826 | 0.520 | True (compared) |
| a5_kimi_k3_p32768_c1 / cases / `886c1fa5bd45` | MatMulV3 / linear_output | 4347 | 12.553 / 6.345 | -6.208 | 0.428 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | MatMulV3 / linear_output | 4347 | 12.553 / 6.345 | -6.208 | 0.428 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | DynamicMxQuant / linear_q.quantize | 4347 | 4.126 / 1.312 | -2.814 | 0.194 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | RmsNormDynamicMxQuant / latent_up.quantize | 5796 | 3.000 / 1.312 | -1.688 | 0.155 | True (compared) |
| a5_kimi_k3_p32768_c1 / cases / `886c1fa5bd45` | MatMulV3 / output | 1512 | 12.576 / 6.345 | -6.231 | 0.150 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | MatMulV3 / output | 1512 | 12.576 / 6.345 | -6.231 | 0.150 | True (compared) |
| a5_kimi_k3_p32768_c1 / cases / `886c1fa5bd45` | TransposeBatchMatMul / v_expand | 1512 | 5.877 / 1.578 | -4.299 | 0.103 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | TransposeBatchMatMul / v_expand | 1512 | 5.877 / 1.578 | -4.299 | 0.103 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | MlaPrologV3 / mla_prolog | 1512 | 22.248 / 25.040 | 2.792 | 0.067 | None (reference_only) |
| a5_kimi_k3_p32768_c1 / cases / `886c1fa5bd45` | MatMulV3 / output_gate|q_a | 1512 | 16.937 / 14.799 | -2.137 | 0.051 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | MatMulV3 / output_gate | 1512 | 16.937 / 14.799 | -2.137 | 0.051 | True (compared) |

## Highest unscored activity — coverage gaps, not zero predictions

| Case | Operator / role | Unscored calls | Unscored observed activity ms / Forward | Status |
|---|---|---:|---:|---|
| a5_kimi_k3_p32768_c1 / cases | GroupedMatmul / unresolved | 21735 | 6.993 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | GroupedMatmul / unresolved | 21735 | 6.993 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | GroupedMatmulSituQuant / unresolved | 5796 | 6.831 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | GroupedMatmulSituQuant / grouped_gate_up_situ_quant | 5796 | 6.831 | reference_only |
| a5_kimi_k3_p32768_c1 / cases | SituMxQuant / unresolved | 5796 | 5.994 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | QuantBatchMatmulV4 / unresolved | 11592 | 4.008 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | QuantBatchMatmulV4 / shared.gate_up | 5796 | 2.799 | reference_only |
| a5_kimi_k3_p32768_c1 / cases | MatMulV3 / unresolved | 10143 | 2.789 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | MatMulV3 / unresolved | 10143 | 2.789 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | MoeDistributeDispatchV3 / unresolved | 5796 | 2.257 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | MoeDistributeDispatchV3 / unresolved | 5796 | 2.257 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | AttnResFwd / unresolved | 11781 | 1.974 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | AttnResFwd / unresolved | 11781 | 1.974 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | MoeDistributeCombineV3 / unresolved | 5796 | 1.347 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | MoeDistributeCombineV3 / unresolved | 5796 | 1.347 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | hcom_reduceScatter_ / attention_output_communication | 5859 | 1.288 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | hcom_reduceScatter_ / attention_output_communication | 5859 | 1.288 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | QuantBatchMatmulV4 / shared.down | 5796 | 1.209 | reference_only |
| a5_kimi_k3_p32768_c1 / cases | hcom_reduceScatter_ / ffn_down_communication | 5859 | 1.159 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | hcom_reduceScatter_ / ffn_down_communication | 5859 | 1.159 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | DynamicMxQuant / unresolved | 17577 | 1.151 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | hcom_allGather_ / attention_output_communication | 5859 | 0.894 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | hcom_allGather_ / attention_output_communication | 5859 | 0.894 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | hcom_allGather_ / ffn_down_communication | 5922 | 0.877 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | hcom_allGather_ / ffn_down_communication | 5922 | 0.877 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | PadV3 / unresolved | 14679 | 0.864 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | PadV3 / unresolved | 14679 | 0.864 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | FusedInferAttentionScore / unresolved | 1512 | 0.776 | reference_only |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | FusedInferAttentionScore / unresolved | 1512 | 0.776 | reference_only |
| a5_kimi_k3_p32768_c1 / cases | RecurrentKda / unresolved | 4347 | 0.662 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | RecurrentKda / unresolved | 4347 | 0.662 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | MlaPrologV3 / unresolved | 1512 | 0.534 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | MlaPrologV3 / mla_prolog | 1512 | 0.534 | reference_only |
| a5_kimi_k3_p32768_c1 / cases | ForeachAddList / unresolved | 5796 | 0.424 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | ForeachAddList / unresolved | 5796 | 0.424 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | MoeGatingTopK / unresolved | 5796 | 0.409 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | MoeGatingTopK / unresolved | 5796 | 0.409 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | CausalConv1d / unresolved | 4347 | 0.357 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | CausalConv1d / unresolved | 4347 | 0.357 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | Fill / unresolved | 16065 | 0.352 | unresolved |

## Source-role references — already costed work is not an extra budget

Reference differences have distinct evidence and are excluded from strict cohort accuracy counts.

| Case | Operator / region | Real / reference us | Real / Sim service ms per Forward | Residual ms | Boundary |
|---|---|---:|---:|---:|---|
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / gdn / attention | 79.592 / 30.862 | 3.820 / 1.481 | -2.339 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / gdn / ffn | 76.826 / 30.862 | 3.688 / 1.481 | -2.206 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / gdn / attention | 61.908 / 25.931 | 2.972 / 1.245 | -1.727 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / gdn / attention | 81.530 / 48.606 | 3.913 / 2.333 | -1.580 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / gdn / attention | 58.791 / 32.514 | 2.822 / 1.561 | -1.261 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / gdn / attention | 38.341 / 15.816 | 1.840 / 0.759 | -1.081 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / gdn / ffn | 34.882 / 15.816 | 1.674 / 0.759 | -0.915 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / gqa / attention | 79.629 / 30.862 | 1.274 / 0.494 | -0.780 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / gdn / ffn | 64.239 / 48.606 | 3.083 / 2.333 | -0.750 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / gqa / ffn | 76.434 / 30.862 | 1.223 / 0.494 | -0.729 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel / gqa / attention | 28.389 / 3.542 | 0.454 / 0.057 | -0.398 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / gqa / attention | 73.299 / 48.606 | 1.173 / 0.778 | -0.395 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel / gqa / attention | 26.844 / 3.148 | 0.429 / 0.050 | -0.379 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / gdn / attention | 18.655 / 11.427 | 0.895 / 0.548 | -0.347 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / gqa / attention | 36.991 / 15.816 | 0.592 / 0.253 | -0.339 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu / gdn / attention | 8.186 / 1.312 | 0.393 / 0.063 | -0.330 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / gqa / ffn | 34.787 / 15.816 | 0.557 / 0.253 | -0.304 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu / gdn / attention | 6.519 / 1.312 | 0.313 / 0.063 | -0.250 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / gdn / ffn | 16.614 / 11.427 | 0.797 / 0.548 | -0.249 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / gqa / ffn | 63.948 / 48.606 | 1.023 / 0.778 | -0.245 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | l2norm_fwd_kernel2 / gdn / attention | 3.779 / 1.312 | 0.363 / 0.126 | -0.237 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / gdn / ffn | 21.976 / 25.931 | 1.055 / 1.245 | 0.190 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu / gdn / attention | 5.123 / 1.312 | 0.246 / 0.063 | -0.183 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel / gqa / attention | 13.451 / 2.788 | 0.215 / 0.045 | -0.171 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | l2norm_fwd_kernel2 / gdn / attention | 3.075 / 1.312 | 0.295 / 0.126 | -0.169 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu / gdn / attention | 4.702 / 1.312 | 0.226 / 0.063 | -0.163 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | l2norm_fwd_kernel2 / gdn / attention | 2.769 / 1.312 | 0.266 / 0.126 | -0.140 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel / gqa / attention | 11.381 / 2.853 | 0.182 / 0.046 | -0.136 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu / gdn / attention | 3.803 / 1.312 | 0.183 / 0.063 | -0.120 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | l2norm_fwd_kernel2 / gdn / attention | 2.429 / 1.312 | 0.233 / 0.126 | -0.107 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu / gdn / attention | 3.375 / 1.312 | 0.162 / 0.063 | -0.099 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / gqa / attention | 16.753 / 11.427 | 0.268 / 0.183 | -0.085 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / gqa / ffn | 16.735 / 11.427 | 0.268 / 0.183 | -0.085 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / gdn / ffn | 30.927 / 32.514 | 1.484 / 1.561 | 0.076 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | l2norm_fwd_kernel2 / gdn / attention | 2.102 / 1.312 | 0.202 / 0.126 | -0.076 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / gqa / ffn | 21.989 / 25.931 | 0.352 / 0.415 | 0.063 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel / gqa / attention | 6.254 / 2.653 | 0.100 / 0.042 | -0.058 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / gqa / attention | 35.826 / 32.514 | 0.573 / 0.520 | -0.053 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | l2norm_fwd_kernel2 / gdn / attention | 1.817 / 1.312 | 0.174 / 0.126 | -0.049 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel / gqa / attention | 5.634 / 2.640 | 0.090 / 0.042 | -0.048 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / gqa / ffn | 30.577 / 32.514 | 0.489 / 0.520 | 0.031 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / gqa / attention | 24.240 / 25.931 | 0.388 / 0.415 | 0.027 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | DynamicQuantV2 / gdn / attention | 7.494 / — | 0.360 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicQuant / gdn / ffn | 15.340 / — | 0.736 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | DynamicQuantV2 / gdn / ffn | 6.140 / — | 0.295 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | AddRmsNorm / gdn / attention | 8.789 / — | 0.413 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicQuant / gqa / attention | 12.148 / — | 0.194 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | DynamicQuantV2 / gqa / attention | 5.567 / — | 0.089 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicQuant / gqa / ffn | 12.621 / — | 0.202 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | DynamicQuantV2 / gqa / ffn | 5.743 / — | 0.092 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | DynamicQuantV2 / gdn / attention | 4.049 / — | 0.194 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicQuant / gdn / ffn | 5.429 / — | 0.261 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | DynamicQuantV2 / gdn / ffn | 3.877 / — | 0.186 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | AddRmsNorm / gdn / attention | 4.089 / — | 0.192 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicQuant / gqa / attention | 5.434 / — | 0.087 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | DynamicQuantV2 / gqa / attention | 3.762 / — | 0.060 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicQuant / gqa / ffn | 5.422 / — | 0.087 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | DynamicQuantV2 / gqa / ffn | 3.911 / — | 0.063 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | DynamicQuantV2 / gdn / attention | 6.016 / — | 0.289 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | AddRmsNormDynamicQuant / gdn / ffn | 9.468 / — | 0.454 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | DynamicQuantV2 / gdn / ffn | 5.528 / — | 0.265 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | AddRmsNorm / gdn / attention | 6.297 / — | 0.296 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | AddRmsNormDynamicQuant / gqa / attention | 8.251 / — | 0.132 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | DynamicQuantV2 / gqa / attention | 4.893 / — | 0.078 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | AddRmsNormDynamicQuant / gqa / ffn | 8.525 / — | 0.136 / — | — | boundary_unresolved |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | DynamicQuantV2 / gqa / ffn | 5.228 / — | 0.084 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant / gdn / ffn | 14.009 / — | 0.672 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | AddRmsNorm / gdn / attention | 9.873 / — | 0.464 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant / gqa / attention | 12.301 / — | 0.197 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant / gqa / ffn | 12.340 / — | 0.197 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant / gdn / ffn | 7.733 / — | 0.371 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | AddRmsNorm / gdn / attention | 5.956 / — | 0.280 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant / gqa / attention | 7.146 / — | 0.114 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant / gqa / ffn | 7.275 / — | 0.116 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant / gdn / ffn | 4.405 / — | 0.211 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | AddRmsNorm / gdn / attention | 4.302 / — | 0.202 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant / gqa / attention | 4.180 / — | 0.067 / — | — | boundary_unresolved |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | AddRmsNormDynamicMxQuant / gqa / ffn | 4.141 / — | 0.066 / — | — | boundary_unresolved |

## Receipt identities

- [decode-forward-priority-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-priority-replay.json), SHA256 `dc6d63fe09130151285b50390ccc53136dee834959de127c39e0337018c8d912`
- [decode-forward-second-wave-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-second-wave-replay.json), SHA256 `574bd3ac3b05bded807b10c34d91933c170bb66fbe88eeb301b4b93ef92111c6`
- [decode-forward-kimi-checkpoint-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-kimi-checkpoint-replay.json), SHA256 `f6e82a724d94250f1db854587fcfaf9ca0296c2596c0bcb00cc0525331f42429`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority-operators/body-operator-family-scoreboard.json), SHA256 `7126d4a275a5f005537517386747e366322a7bed7365763e21cb3a66319b13fc`
- [body-communication-references.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-high-concurrency/body-communication-references.json), SHA256 `dd98c1ba7677ea8d5ef9ea1670c69937a4f8fa2e24ec096c7392c3440ace0caa`

Additional coverage/source evidence (not silently promoted into body or operator predictions):

- [v41-existing-assets-20261030.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/v41-existing-assets-20261030.json), SHA256 `797183bf8f17978a219a4b96d8340de4b4a01442f66ae48b028aeb130be3f88f`
- [glm-three-level-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm/glm-three-level-evidence.json), SHA256 `f008c591bd6749b522d4500e047629bcd4f30438e54858c90ec5183c458a9f9a`
- [retained-source-evidence.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm78-v41/retained-source-evidence.json), SHA256 `cd28e3e6433de424c43d24327d7ad0b08e2ef27eb47cd9410a7bd8fa9fbb30ca`
- [decode-forward-auto-acceptance.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm78-v41/decode-forward-auto-acceptance.json), SHA256 `8241478fcadddf83641ca52edc1f622a624b2d50c57c60394447ca70eec0b18e`

- Rows retain their own source/runtime/geometry; independently produced receipts are not merged into a synthetic run.
- Per-forward kernel activity residual ranks work to investigate; overlap prevents interpreting its sum as body wall-clock error.
- Unscored activity is a matching/model-boundary coverage gap, not proof that Sim omitted the corresponding work.
- Layer median-of-call-P50 and exact pooled P50 are distinct populations.
