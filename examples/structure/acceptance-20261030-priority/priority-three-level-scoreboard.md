# Priority Decode body, layer and operator scoreboard

Coverage status: **partial**. Missing predictions and unmatched roles stay visible.

Current selected Body arms: **9/29 passed**. One latest completed receipt per measured source/geometry, selected in input order; each row retains its own runtime and case.

Body: **11/40 prediction arms passed**; 29 unique sources, 96 measured geometry populations, 2098 unique complete Forwards (includes deferred populations).

Operator strict accuracy: heavy_relative_15pct: **0/2**; micro_absolute_15us: **68/69**. Conditional references are excluded.

Local replay receipts with explicit comparison coverage. Body errors are measured wall-clock differences; operator priorities are nonadditive kernel activity residuals per complete Forward.

## Whole Decode Body — sorted by absolute ms error

| Case / variant | Status | Calls | Real Mean / P50 / P90 ms | Activity ms | Sim ms | Diff ms | Mean / P50 error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b4:q1_b4_m4 / legacy_glm53_78_layer_w4a8 / `5d7c051180a9` | compared | 67 | 43.438 / 43.437 / 43.598 | — | 72.002 | 28.564 | 65.760% / 65.763% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / kimi_checkpoint_sp_right_pad_conditional_1f5b2971 / `0b82bdf55fb7` | compared | 63 | 32.555 / 32.533 / 32.674 | — | 54.184 | 21.628 | 66.435% / 66.549% |
| qwen36-a5-tp2-c96:q4_b96_m384 / None / `5d7c051180a9` | compared | 24 | 63.853 / 63.562 / 65.419 | 63.565 | 45.126 | -18.727 | -29.328% / -29.004% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / glm_indexed_owner_and_projection_controls / `b79e1539e4db` | compared | 37 | 41.069 / 40.940 / 41.282 | 39.691 | 59.176 | 18.107 | 44.089% / 44.543% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / glm78_tp16_ep16_int8kv_conditional / `0b82bdf55fb7` | compared | 44 | 57.817 / 57.597 / 59.092 | 55.203 | 39.721 | -18.096 | -31.299% / -31.037% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / glm78_tp16_ep16_int8kv_conditional / `0b82bdf55fb7` | compared | 44 | 57.639 / 57.562 / 58.995 | 55.027 | 39.721 | -17.918 | -31.087% / -30.994% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / qwen397_tp_join_reduce_source_contract / `b79e1539e4db` | compared | 18 | 119.054 / 119.131 / 119.486 | 118.048 | 102.780 | -16.275 | -13.670% / -13.725% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / None / `5d7c051180a9` | compared | 76 | 28.585 / 28.571 / 28.704 | 28.300 | 14.677 | -13.908 | -48.655% / -48.630% |
| qwen36-a5-tp2-c12:q4_b12_m48 / None / `5d7c051180a9` | compared | 55 | 24.226 / 24.053 / 24.711 | 23.858 | 10.999 | -13.227 | -54.600% / -54.273% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / glm78_tp16_ep16_int8kv_conditional / `0b82bdf55fb7` | compared | 49 | 69.556 / 69.489 / 69.830 | 66.970 | 57.630 | -11.926 | -17.146% / -17.066% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / None / `5d7c051180a9` | compared | 79 | 21.957 / 22.001 / 22.068 | 21.571 | 10.219 | -11.738 | -53.458% / -53.551% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None / `5d7c051180a9` | compared | 46 | 29.762 / 29.664 / 30.046 | 28.242 | 37.949 | 8.187 | 27.510% / 27.930% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 / None / `b79e1539e4db` | compared | 75 | 26.328 / 26.306 / 26.336 | 26.229 | 18.285 | -8.044 | -30.551% / -30.492% |
| a3_glm53_dc4k_b2:q1_b2_m2 / legacy_glm53_78_layer_w4a8 / `5d7c051180a9` | compared | 70 | 40.970 / 40.935 / 41.046 | — | 48.792 | 7.823 | 19.093% / 19.195% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / qwen397_tp_join_reduce_source_contract / `b79e1539e4db` | compared | 23 | 76.089 / 76.132 / 76.632 | 75.005 | 68.312 | -7.777 | -10.221% / -10.272% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / glm_indexed_owner_and_projection_controls / `b79e1539e4db` | compared | 53 | 21.068 / 21.057 / 21.170 | 20.805 | 14.025 | -7.043 | -33.429% / -33.397% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / None / `5d7c051180a9` | compared | 84 | 11.551 / 11.482 / 11.818 | 11.135 | 5.049 | -6.503 | -56.294% / -56.029% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm_indexed_owner_and_projection_controls / `b79e1539e4db` | compared | 65 | 15.683 / 15.670 / 15.738 | 15.421 | 9.498 | -6.185 | -39.439% / -39.389% |
| a3_glm53_dc4k_b1:q1_b1_m1 / glm_indexed_owner_and_projection_controls / `b79e1539e4db` | compared | 74 | 38.955 / 38.943 / 39.036 | — | 33.573 | -5.382 | -13.816% / -13.789% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 / None / `b79e1539e4db` | compared | 145 | 13.292 / 12.803 / 12.817 | 13.196 | 8.200 | -5.091 | -38.304% / -35.950% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 / None / `b79e1539e4db` | compared | 152 | 13.135 / 13.129 / 13.145 | 13.039 | 8.200 | -4.934 | -37.567% / -37.542% |
| qwen36-a5-tp2-c1:q4_b1_m4 / None / `5d7c051180a9` | compared | 85 | 12.318 / 12.279 / 12.362 | 11.956 | 7.413 | -4.905 | -39.822% / -39.630% |
| v4flash-a3-tp8-c4:q2_b4_m8 / None / `5d7c051180a9` | compared | 104 | 32.486 / 32.416 / 32.734 | 30.611 | 27.589 | -4.897 | -15.075% / -14.892% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / None / `5d7c051180a9` | compared | 27 | 57.590 / 57.573 / 57.734 | 57.355 | 54.015 | -3.574 | -6.207% / -6.179% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / None / `5d7c051180a9` | compared | 46 | 34.118 / 33.910 / 35.073 | 32.625 | 30.804 | -3.314 | -9.714% / -9.159% |
| a3_glm53_dc4k_b8:q1_b8_m8 / glm_indexed_owner_and_projection_controls / `b79e1539e4db` | compared | 61 | 47.113 / 47.149 / 47.402 | — | 44.050 | -3.063 | -6.502% / -6.572% |
| a3_glm53_dc16k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 / `5d7c051180a9` | compared | 74 | 39.112 / 39.105 / 39.196 | — | 36.961 | -2.151 | -5.501% / -5.483% |
| v4flash-a3-tp8-c8:q2_b8_m16 / None / `5d7c051180a9` | compared | 104 | 37.763 / 37.868 / 38.082 | 36.154 | 35.758 | -2.005 | -5.309% / -5.572% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None / `5d7c051180a9` | compared | 46 | 39.841 / 39.798 / 40.057 | 38.324 | 37.949 | -1.892 | -4.750% / -4.647% |
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

## Layer 0 and steady layer groups

The steady P50 column is median of per-layer call P50, unless a separately linked receipt supplies exact pooled statistics.

| Case | Group | Layers | Real Mean ms | Median layer-call P50 ms | Sim Mean ms | Mean / P50 error |
|---|---|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b4:q1_b4_m4 / legacy_glm53_78_layer_w4a8 | Layer 0 / mla / dense_layer | 1 | 0.4118 | 0.4071 | 0.6140 | 49.118% / 50.826% |
| a3_glm53_dc4k_b4:q1_b4_m4 / legacy_glm53_78_layer_w4a8 | Steady / mla / dense_layer | 2 | 0.3968 | 0.3931 | 0.6140 | 54.728% / 56.217% |
| a3_glm53_dc4k_b4:q1_b4_m4 / legacy_glm53_78_layer_w4a8 | Steady / mla / moe_layer | 75 | 0.5622 | 0.5411 | 0.9355 | 66.402% / 72.867% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / kimi_checkpoint_sp_right_pad_conditional_1f5b2971 | Layer 0 / kda / dense_layer | 1 | 0.2579 | 0.2383 | 0.1850 | -28.258% / -22.349% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / kimi_checkpoint_sp_right_pad_conditional_1f5b2971 | Steady / kda / moe_layer | 68 | 0.3399 | 0.3386 | 0.5903 | 73.650% / 74.331% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / kimi_checkpoint_sp_right_pad_conditional_1f5b2971 | Steady / mla / moe_layer | 24 | 0.3835 | 0.3747 | 0.5768 | 50.389% / 53.946% |
| qwen36-a5-tp2-c96:q4_b96_m384 / None | Layer 0 / gdn / dense_layer | 1 | 1.3691 | 1.0682 | 0.7556 | -44.813% / -29.265% |
| qwen36-a5-tp2-c96:q4_b96_m384 / None | Steady / gdn / dense_layer | 47 | 1.0584 | 1.0584 | 0.7556 | -28.615% / -28.614% |
| qwen36-a5-tp2-c96:q4_b96_m384 / None | Steady / gqa / dense_layer | 16 | 0.7931 | 0.7928 | 0.5537 | -30.186% / -30.151% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / glm_indexed_owner_and_projection_controls | Layer 0 / kda / dense_layer | 1 | 1.0092 | 0.8498 | 0.7050 | -30.142% / -17.032% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / glm_indexed_owner_and_projection_controls | Steady / kda / dense_layer | 2 | 0.4246 | 0.4245 | 0.7050 | 66.042% / 66.092% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / glm_indexed_owner_and_projection_controls | Steady / mla / moe_layer | 11 | 1.3710 | 1.3767 | 1.5075 | 9.955% / 9.501% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / glm_indexed_owner_and_projection_controls | Steady / kda / moe_layer | 31 | 0.7767 | 0.7741 | 1.3058 | 68.114% / 68.681% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / glm78_tp16_ep16_int8kv_conditional | Layer 0 / mla / dense_layer | 1 | 0.6279 | 0.5491 | 0.3541 | -43.608% / -35.508% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / glm78_tp16_ep16_int8kv_conditional | Steady / mla / dense_layer | 2 | 0.5676 | 0.5344 | 0.3541 | -37.613% / -33.739% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / glm78_tp16_ep16_int8kv_conditional | Steady / mla / moe_layer | 75 | 0.7473 | 0.7151 | 0.5154 | -31.029% / -27.919% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / glm78_tp16_ep16_int8kv_conditional | Layer 0 / mla / dense_layer | 1 | 0.5858 | 0.5425 | 0.3541 | -39.547% / -34.729% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / glm78_tp16_ep16_int8kv_conditional | Steady / mla / dense_layer | 2 | 0.5667 | 0.5291 | 0.3541 | -37.517% / -33.073% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / glm78_tp16_ep16_int8kv_conditional | Steady / mla / moe_layer | 75 | 0.7455 | 0.7151 | 0.5154 | -30.864% / -27.915% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / qwen397_tp_join_reduce_source_contract | Layer 0 / gdn / moe_layer | 1 | 2.0473 | 1.9983 | 1.6612 | -18.860% / -16.870% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / qwen397_tp_join_reduce_source_contract | Steady / gdn / moe_layer | 44 | 1.9572 | 1.9352 | 1.6612 | -15.126% / -14.159% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / qwen397_tp_join_reduce_source_contract | Steady / gqa / moe_layer | 15 | 2.0544 | 2.0314 | 1.8685 | -9.049% / -8.019% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / None | Layer 0 / gdn / moe_layer | 1 | 0.7544 | 0.7238 | 0.3803 | -49.595% / -47.460% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / None | Steady / gdn / moe_layer | 29 | 0.7199 | 0.7199 | 0.3803 | -47.175% / -47.179% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / None | Steady / gqa / moe_layer | 10 | 0.6953 | 0.6941 | 0.3269 | -52.991% / -52.909% |
| qwen36-a5-tp2-c12:q4_b12_m48 / None | Layer 0 / gdn / dense_layer | 1 | 0.6168 | 0.3931 | 0.1825 | -70.421% / -53.586% |
| qwen36-a5-tp2-c12:q4_b12_m48 / None | Steady / gdn / dense_layer | 47 | 0.4044 | 0.4033 | 0.1825 | -54.884% / -54.760% |
| qwen36-a5-tp2-c12:q4_b12_m48 / None | Steady / gqa / dense_layer | 16 | 0.2846 | 0.2843 | 0.1401 | -50.788% / -50.733% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / glm78_tp16_ep16_int8kv_conditional | Layer 0 / mla / dense_layer | 1 | 0.6710 | 0.6210 | 0.4517 | -32.682% / -27.268% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / glm78_tp16_ep16_int8kv_conditional | Steady / mla / dense_layer | 2 | 0.6345 | 0.6104 | 0.4517 | -28.816% / -26.005% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / glm78_tp16_ep16_int8kv_conditional | Steady / mla / moe_layer | 75 | 0.9015 | 0.8670 | 0.7503 | -16.768% / -13.452% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / None | Layer 0 / gdn / moe_layer | 1 | 0.7737 | 0.8216 | 0.2645 | -65.808% / -67.803% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / None | Steady / gdn / moe_layer | 29 | 0.5470 | 0.5467 | 0.2645 | -51.637% / -51.614% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / None | Steady / gqa / moe_layer | 10 | 0.5320 | 0.5323 | 0.2283 | -57.085% / -57.109% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None | Layer 0 / kda / dense_layer | 1 | 0.8292 | 0.7249 | 0.4474 | -46.044% / -38.275% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None | Steady / kda / dense_layer | 2 | 0.2964 | 0.2961 | 0.4474 | 50.956% / 51.096% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None | Steady / mla / moe_layer | 11 | 0.9295 | 0.9276 | 0.8975 | -3.445% / -3.245% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None | Steady / kda / moe_layer | 31 | 0.5827 | 0.5821 | 0.8624 | 48.002% / 48.147% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 / None | Layer 0 / mla / moe_layer | 1 | 0.7498 | 0.7292 | 0.4471 | -40.378% / -38.688% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 / None | Steady / mla / moe_layer | 39 | 0.6558 | 0.6334 | 0.4574 | -30.256% / -27.787% |
| a3_glm53_dc4k_b2:q1_b2_m2 / legacy_glm53_78_layer_w4a8 | Layer 0 / mla / dense_layer | 1 | 0.4105 | 0.3960 | 0.4397 | 7.121% / 11.061% |
| a3_glm53_dc4k_b2:q1_b2_m2 / legacy_glm53_78_layer_w4a8 | Steady / mla / dense_layer | 2 | 0.3997 | 0.3865 | 0.4397 | 10.026% / 13.773% |
| a3_glm53_dc4k_b2:q1_b2_m2 / legacy_glm53_78_layer_w4a8 | Steady / mla / moe_layer | 75 | 0.5293 | 0.5092 | 0.6330 | 19.591% / 24.318% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / qwen397_tp_join_reduce_source_contract | Layer 0 / gdn / moe_layer | 1 | 1.3503 | 1.2865 | 1.1042 | -18.226% / -14.168% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / qwen397_tp_join_reduce_source_contract | Steady / gdn / moe_layer | 44 | 1.2329 | 1.2077 | 1.1042 | -10.437% / -8.569% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / qwen397_tp_join_reduce_source_contract | Steady / gqa / moe_layer | 15 | 1.3614 | 1.3469 | 1.2415 | -8.812% / -7.829% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / glm_indexed_owner_and_projection_controls | Layer 0 / kda / dense_layer | 1 | 0.4650 | 0.4745 | 0.1476 | -68.256% / -68.890% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / glm_indexed_owner_and_projection_controls | Steady / kda / dense_layer | 2 | 0.2383 | 0.2328 | 0.1476 | -38.059% / -36.597% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / glm_indexed_owner_and_projection_controls | Steady / mla / moe_layer | 11 | 0.6392 | 0.6337 | 0.3466 | -45.778% / -45.309% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / glm_indexed_owner_and_projection_controls | Steady / kda / moe_layer | 31 | 0.4224 | 0.4216 | 0.3152 | -25.389% / -25.256% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / None | Layer 0 / gdn / moe_layer | 1 | 0.3868 | 0.2973 | 0.1242 | -67.899% / -58.244% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / None | Steady / gdn / moe_layer | 29 | 0.2819 | 0.2827 | 0.1242 | -55.959% / -56.087% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / None | Steady / gqa / moe_layer | 10 | 0.2989 | 0.2992 | 0.1324 | -55.697% / -55.742% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm_indexed_owner_and_projection_controls | Layer 0 / kda / dense_layer | 1 | 0.4222 | 0.4383 | 0.1284 | -69.600% / -70.713% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm_indexed_owner_and_projection_controls | Steady / kda / dense_layer | 2 | 0.2487 | 0.2314 | 0.1284 | -48.386% / -44.529% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm_indexed_owner_and_projection_controls | Steady / mla / moe_layer | 11 | 0.4952 | 0.4903 | 0.2353 | -52.477% / -52.003% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm_indexed_owner_and_projection_controls | Steady / kda / moe_layer | 31 | 0.3005 | 0.2985 | 0.2105 | -29.965% / -29.500% |
| a3_glm53_dc4k_b1:q1_b1_m1 / glm_indexed_owner_and_projection_controls | Layer 0 / mla / dense_layer | 1 | 0.3943 | 0.3854 | 0.3526 | -10.563% / -8.497% |
| a3_glm53_dc4k_b1:q1_b1_m1 / glm_indexed_owner_and_projection_controls | Steady / mla / dense_layer | 2 | 0.3841 | 0.3775 | 0.3526 | -8.207% / -6.585% |
| a3_glm53_dc4k_b1:q1_b1_m1 / glm_indexed_owner_and_projection_controls | Steady / mla / moe_layer | 75 | 0.5031 | 0.4848 | 0.4335 | -13.823% / -10.574% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 / None | Layer 0 / mla / moe_layer | 1 | 0.8501 | 0.3611 | 0.1955 | -77.007% / -45.863% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 / None | Steady / mla / moe_layer | 39 | 0.3189 | 0.3014 | 0.2053 | -35.647% / -31.893% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 / None | Layer 0 / mla / moe_layer | 1 | 0.8189 | 0.8103 | 0.1955 | -76.130% / -75.876% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 / None | Steady / mla / moe_layer | 39 | 0.3157 | 0.2984 | 0.2053 | -34.990% / -31.206% |
| qwen36-a5-tp2-c1:q4_b1_m4 / None | Layer 0 / gdn / dense_layer | 1 | 0.2400 | 0.1984 | 0.1154 | -51.909% / -41.833% |
| qwen36-a5-tp2-c1:q4_b1_m4 / None | Steady / gdn / dense_layer | 47 | 0.1919 | 0.1915 | 0.1154 | -39.861% / -39.732% |
| qwen36-a5-tp2-c1:q4_b1_m4 / None | Steady / gqa / dense_layer | 16 | 0.1880 | 0.1876 | 0.1171 | -37.704% / -37.562% |
| v4flash-a3-tp8-c4:q2_b4_m8 / None | Layer 0 / mla / moe_layer | 1 | 0.7568 | 0.7178 | 0.5579 | -26.289% / -22.282% |
| v4flash-a3-tp8-c4:q2_b4_m8 / None | Steady / mla / moe_layer | 42 | 0.7543 | 0.7537 | 0.6436 | -14.674% / -14.607% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / None | Layer 0 / kda / dense_layer | 1 | 0.6036 | 0.5889 | 0.6393 | 5.904% / 8.553% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / None | Steady / kda / dense_layer | 2 | 0.5724 | 0.5723 | 0.6393 | 11.686% / 11.710% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / None | Steady / mla / moe_layer | 11 | 2.2334 | 2.2329 | 1.3768 | -38.353% / -38.338% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / None | Steady / kda / moe_layer | 31 | 1.0088 | 1.0088 | 1.1920 | 18.161% / 18.163% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / None | Layer 0 / kda / dense_layer | 1 | 0.5732 | 0.5010 | 0.3996 | -30.294% / -20.248% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / None | Steady / kda / dense_layer | 2 | 0.5965 | 0.5414 | 0.3996 | -33.013% / -26.194% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / None | Steady / mla / moe_layer | 11 | 0.9546 | 0.9395 | 0.7215 | -24.418% / -23.201% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / None | Steady / kda / moe_layer | 31 | 0.7032 | 0.6643 | 0.6990 | -0.602% / 5.221% |
| a3_glm53_dc4k_b8:q1_b8_m8 / glm_indexed_owner_and_projection_controls | Layer 0 / mla / dense_layer | 1 | 0.4244 | 0.4227 | 0.3646 | -14.080% / -13.728% |
| a3_glm53_dc4k_b8:q1_b8_m8 / glm_indexed_owner_and_projection_controls | Steady / mla / dense_layer | 2 | 0.4119 | 0.4111 | 0.3646 | -11.462% / -11.306% |
| a3_glm53_dc4k_b8:q1_b8_m8 / glm_indexed_owner_and_projection_controls | Steady / mla / moe_layer | 75 | 0.6105 | 0.5863 | 0.5727 | -6.191% / -2.316% |
| a3_glm53_dc16k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 | Layer 0 / mla / dense_layer | 1 | 0.4020 | 0.3967 | 0.3526 | -12.294% / -11.111% |
| a3_glm53_dc16k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 | Steady / mla / dense_layer | 2 | 0.3934 | 0.3879 | 0.3526 | -10.369% / -9.102% |
| a3_glm53_dc16k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 | Steady / mla / moe_layer | 75 | 0.5045 | 0.4834 | 0.4787 | -5.110% / -0.982% |
| v4flash-a3-tp8-c8:q2_b8_m16 / None | Layer 0 / mla / moe_layer | 1 | 0.8072 | 0.7668 | 0.7432 | -7.929% / -3.069% |
| v4flash-a3-tp8-c8:q2_b8_m16 / None | Steady / mla / moe_layer | 42 | 0.8787 | 0.8831 | 0.8337 | -5.126% / -5.595% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None | Layer 0 / kda / dense_layer | 1 | 0.6141 | 0.5825 | 0.4474 | -27.138% / -23.185% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None | Steady / kda / dense_layer | 2 | 0.6160 | 0.5541 | 0.4474 | -27.368% / -19.246% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None | Steady / mla / moe_layer | 11 | 1.1665 | 1.1644 | 0.8975 | -23.064% / -22.924% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None | Steady / kda / moe_layer | 31 | 0.8101 | 0.8087 | 0.8624 | 6.462% / 6.640% |

## Heavy >50us operators — activity residual priority

| Case | Operator / role | Calls | Real / Sim us | Diff us | Absolute ms / Forward | Tier pass |
|---|---|---:|---:|---:|---:|---|
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | GroupedMatmulSituQuant / grouped_gate_up_situ_quant | 5796 | 74.250 / 7.735 | -66.515 | 6.119 | None (reference_only) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1554 | 142.415 / 285.783 | 143.367 | 6.021 | None (reference_only) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | SituMxQuant / shared.situ_quant | 5796 | 65.155 / 1.312 | -63.843 | 5.874 | False (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | GroupedMatmul / expert_down | 2226 | 51.524 / 34.915 | -16.609 | 0.698 | False (compared) |

## Micro <=50us operators — activity residual priority

| Case | Operator / role | Calls | Real / Sim us | Diff us | Absolute ms / Forward | Tier pass |
|---|---|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | HcPre / attention.hc_pre | 1665 | 33.367 / 170.549 | 137.182 | 6.173 | None (reference_only) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | HcPre / ffn.hc_pre | 1665 | 36.039 / 170.549 | 134.510 | 6.053 | None (reference_only) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | QuantBatchMatmulV4 / shared.gate_up | 5796 | 30.427 / 3.963 | -26.464 | 2.435 | None (reference_only) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | QuantBatchMatmulV4 / shared.down | 5796 | 13.143 / 1.578 | -11.565 | 1.064 | None (reference_only) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | HcPre / attention.hc_pre | 2385 | 11.753 / 26.539 | 14.787 | 0.665 | None (reference_only) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | HcPre / ffn.hc_pre | 2385 | 11.905 / 26.539 | 14.634 | 0.659 | None (reference_only) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | HcPost / attention.hc_post_group | 1665 | 20.206 / 6.703 | -13.504 | 0.608 | True (compared) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | MatMulV2 / index_k | 814 | 7.501 / 35.103 | 27.602 | 0.607 | False (compared) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | HcPost / ffn.hc_post_group | 1665 | 20.082 / 6.703 | -13.379 | 0.602 | True (compared) |
| glm53flash-a5-tp8-c1 / new17 / `df7c8117e01b` | GroupedMatmul / expert_down | 2730 | 22.482 / 8.760 | -13.722 | 0.576 | True (compared) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | QuantBatchMatmulV3 / shared.down | 1554 | 17.836 / 5.000 | -12.836 | 0.539 | True (compared) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | RmsNorm / norm1 | 1665 | 14.380 / 2.500 | -11.880 | 0.535 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | DynamicMxQuant / latent_down.quantize | 11592 | 4.138 / 1.312 | -2.826 | 0.520 | True (compared) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | RmsNorm / norm2 | 1665 | 13.716 / 2.500 | -11.216 | 0.505 | True (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | MatMulV3 / router | 2226 | 9.420 / 20.437 | 11.018 | 0.463 | True (compared) |
| a5_kimi_k3_p32768_c1 / cases / `886c1fa5bd45` | MatMulV3 / linear_output | 4347 | 12.553 / 6.345 | -6.208 | 0.428 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | MatMulV3 / linear_output | 4347 | 12.553 / 6.345 | -6.208 | 0.428 | True (compared) |
| glm53flash-a5-tp8-c1 / new17 / `df7c8117e01b` | HcPre / attention.hc_pre | 2925 | 11.033 / 20.492 | 9.459 | 0.426 | None (reference_only) |
| glm53flash-a5-tp8-c1 / new17 / `df7c8117e01b` | HcPre / ffn.hc_pre | 2925 | 11.217 / 20.492 | 9.275 | 0.417 | None (reference_only) |
| glm53flash-a5-tp8-c1 / new17 / `df7c8117e01b` | MatMulV3 / router | 2730 | 8.756 / 16.544 | 7.788 | 0.327 | True (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | MatMulV3 / linear_qkvbfg_a | 1802 | 17.826 / 9.002 | -8.824 | 0.300 | True (compared) |
| glm53flash-a5-tp8-c1 / new17 / `df7c8117e01b` | MatMulV3 / linear_qkvbfg_a | 2210 | 16.983 / 8.208 | -8.775 | 0.298 | True (compared) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | DynamicQuant / shared.gate_up.quantize | 1554 | 8.780 / 2.500 | -6.280 | 0.264 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | DynamicMxQuant / linear_q.quantize | 4347 | 4.126 / 1.312 | -2.814 | 0.194 | True (compared) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | MatMulV2 / linear_qkvbfg_a | 1258 | 29.863 / 35.273 | 5.410 | 0.184 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | RmsNormDynamicMxQuant / latent_up.quantize | 5796 | 3.000 / 1.312 | -1.688 | 0.155 | True (compared) |
| glm53flash-a5-tp8-c1 / new17 / `df7c8117e01b` | DynamicMxQuant / shared.gate_up.quantize | 2730 | 4.972 / 1.312 | -3.660 | 0.154 | True (compared) |
| a5_kimi_k3_p32768_c1 / cases / `886c1fa5bd45` | MatMulV3 / output | 1512 | 12.576 / 6.345 | -6.231 | 0.150 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | MatMulV3 / output | 1512 | 12.576 / 6.345 | -6.231 | 0.150 | True (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | MatMulV3 / linear_output | 1802 | 6.624 / 2.306 | -4.318 | 0.147 | True (compared) |
| glm53flash-a5-tp8-c1 / new17 / `df7c8117e01b` | MatMulV3 / linear_output | 2210 | 6.347 / 2.117 | -4.230 | 0.144 | True (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | HcPost / attention.hc_post_group | 2385 | 4.505 / 1.312 | -3.193 | 0.144 | True (compared) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | MatMulV2 / linear_output | 1258 | 13.384 / 9.167 | -4.217 | 0.143 | True (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | HcPost / ffn.hc_post_group | 2385 | 4.478 / 1.312 | -3.166 | 0.142 | True (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | DynamicMxQuant / shared.gate_up.quantize | 2226 | 4.666 / 1.312 | -3.354 | 0.141 | True (compared) |
| glm53flash-a5-tp8-c1 / new17 / `df7c8117e01b` | HcPost / attention.hc_post_group | 2925 | 4.150 / 1.312 | -2.838 | 0.128 | True (compared) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | MatMulV2 / linear_decay_b|linear_gate_b | 2516 | 3.128 / 5.000 | 1.872 | 0.127 | True (compared) |
| glm53flash-a5-tp8-c1 / new17 / `df7c8117e01b` | HcPost / ffn.hc_post_group | 2925 | 4.123 / 1.312 | -2.811 | 0.127 | True (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | RmsNorm / norm2 | 2385 | 3.999 / 1.312 | -2.687 | 0.121 | True (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | RmsNorm / norm1 | 2385 | 3.973 / 1.312 | -2.661 | 0.120 | True (compared) |

## Highest unscored activity — coverage gaps, not zero predictions

| Case | Operator / role | Unscored calls | Unscored observed activity ms / Forward | Status |
|---|---|---:|---:|---|
| a5_kimi_k3_p32768_c1 / cases | GroupedMatmul / unresolved | 21735 | 6.993 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | GroupedMatmul / unresolved | 21735 | 6.993 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | GroupedMatmulSituQuant / unresolved | 5796 | 6.831 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | GroupedMatmulSituQuant / grouped_gate_up_situ_quant | 5796 | 6.831 | reference_only |
| a5_kimi_k3_p32768_c1 / cases | SituMxQuant / unresolved | 5796 | 5.994 | unresolved |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1554 | 5.981 | reference_only |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | KvQuantSparseFlashAttentionVllm / unresolved | 407 | 4.153 | unresolved |
| glm53flash-a5-tp8-c3 / new17 | GroupedMatmulSwigluQuantV2 / unresolved | 2226 | 4.147 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | QuantBatchMatmulV4 / unresolved | 11592 | 4.008 | unresolved |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | MoeDistributeCombineV2 / unresolved | 1554 | 3.131 | unresolved |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | GroupedMatmul / unresolved | 1554 | 3.021 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | QuantBatchMatmulV4 / shared.gate_up | 5796 | 2.799 | reference_only |
| a5_kimi_k3_p32768_c1 / cases | MatMulV3 / unresolved | 10143 | 2.789 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | MatMulV3 / unresolved | 10143 | 2.789 | unresolved |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | RecurrentKda / unresolved | 1258 | 2.690 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | MoeDistributeDispatchV3 / unresolved | 5796 | 2.257 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | MoeDistributeDispatchV3 / unresolved | 5796 | 2.257 | unresolved |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | hcom_allReduce_ / attention_output_communication | 1665 | 2.099 | reference_only |
| a5_kimi_k3_p32768_c1 / cases | AttnResFwd / unresolved | 11781 | 1.974 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | AttnResFwd / unresolved | 11781 | 1.974 | unresolved |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | HcPre / ffn.hc_pre | 1665 | 1.622 | reference_only |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | HcPre / attention.hc_pre | 1665 | 1.502 | reference_only |
| glm53flash-a5-tp8-c1 / new17 | GroupedMatmulSwigluQuantV2 / unresolved | 2730 | 1.408 | unresolved |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | MoeDistributeDispatchV2 / unresolved | 1554 | 1.364 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | MoeDistributeCombineV3 / unresolved | 5796 | 1.347 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | MoeDistributeCombineV3 / unresolved | 5796 | 1.347 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | hcom_reduceScatter_ / attention_output_communication | 5859 | 1.288 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | hcom_reduceScatter_ / attention_output_communication | 5859 | 1.288 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | QuantBatchMatmulV4 / shared.down | 5796 | 1.209 | reference_only |
| glm53flash-a5-tp8-c3 / new17 | hcom_allReduce_AicpuKernel / attention_output_communication | 2385 | 1.176 | reference_only |
| a5_kimi_k3_p32768_c1 / cases | hcom_reduceScatter_ / ffn_down_communication | 5859 | 1.159 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | hcom_reduceScatter_ / ffn_down_communication | 5859 | 1.159 | unresolved |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | hcom_allReduce_ / ffn_down_communication | 1665 | 1.155 | reference_only |
| a5_kimi_k3_p32768_c1 / cases | DynamicMxQuant / unresolved | 17577 | 1.151 | unresolved |
| glm53flash-a5-tp8-c3 / new17 | hcom_allReduce_AicpuKernel / ffn_down_communication | 2385 | 1.050 | unresolved |
| glm53flash-a5-tp8-c1 / new17 | hcom_allReduce_AicpuKernel / attention_output_communication | 2925 | 1.040 | reference_only |
| glm53flash-a5-tp8-c1 / new17 | hcom_allReduce_AicpuKernel / ffn_down_communication | 2925 | 0.934 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | hcom_allGather_ / attention_output_communication | 5859 | 0.894 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | hcom_allGather_ / attention_output_communication | 5859 | 0.894 | unresolved |
| a5_kimi_k3_p32768_c1 / cases | hcom_allGather_ / ffn_down_communication | 5922 | 0.877 | unresolved |

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
- [decode-forward-system-fix-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-system-fix-replay.json), SHA256 `1cf66ae57bb9e7603c248c4c1a4810e7f2c5610e480333c91e4487becb6617fc`
- [decode-forward-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm78-v41/decode-forward-replay.json), SHA256 `c05015ddbd7e42c0bf907c6eed83723ea232632d21d68ce94383ca8984d76296`
- [decode-forward-glm-runtime-controls-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-glm-runtime-controls-replay.json), SHA256 `56a171a8f6373f450dfd8ac191cc0c5a564aa10943bdc07f413285c9f057a757`
- [decode-forward-qwen397-join-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-qwen397-join-replay.json), SHA256 `2ec24d3aaa8ffc0cbfcd97ab8a75c45e5844ef3ccbc0c574be83258d59da53d3`
- [decode-forward-v41-dp8-replay.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-dp8/decode-forward-v41-dp8-replay.json), SHA256 `08bb49ccccd27929c15d1736b35016fb0c86dafa92ba8b0df667011fae10f1e0`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority-operators/body-operator-family-scoreboard.json), SHA256 `7126d4a275a5f005537517386747e366322a7bed7365763e21cb3a66319b13fc`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority-operators-5935c87b/body-operator-family-scoreboard.json), SHA256 `4f475bce99de8a8908c8fa745ea1ab9cabb8c570ef3b3ec5ef7c9d5d7f29265e`
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
