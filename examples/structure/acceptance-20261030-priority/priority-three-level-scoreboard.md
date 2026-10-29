# Priority Decode body, layer and operator scoreboard

Coverage status: **partial**. Missing predictions and unmatched roles stay visible.

Current selected Body arms: **18/66 passed**. One latest completed receipt per measured source/geometry, selected in input order; each row retains its own runtime and case.

Body: **20/81 prediction arms passed**; 66 unique sources, 222 measured geometry populations, 5250 unique complete Forwards (includes deferred populations).

Invalidated prediction rows: **31**. Their measured populations remain; superseded predictions and layer errors are excluded from accuracy statistics.

Current operator strict accuracy (latest input receipt per source/geometry): heavy_relative_15pct: **6/23**; micro_absolute_15us: **508/528**. Conditional references are excluded.

Strict event coverage: **1,056,988/6,364,462** events across 38 measured source/geometry populations. A high pass rate within this subset does not establish whole-model accuracy.

Local replay receipts with explicit comparison coverage. Body errors are measured wall-clock differences; operator priorities are nonadditive kernel activity residuals per complete Forward.

## Whole Decode Body — sorted by absolute ms error

| Case / variant | Status | Calls | Real Mean / P50 / P90 ms | Activity ms | Sim ms | Diff ms | Mean / P50 error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b4:q1_b4_m4 / legacy_glm53_78_layer_w4a8 / `5d7c051180a9` | compared | 67 | 43.438 / 43.437 / 43.598 | — | 72.002 | 28.564 | 65.760% / 65.763% |
| qwen36-a5-tp2-c96:q4_b96_m384 / None / `5d7c051180a9` | compared | 24 | 63.853 / 63.562 / 65.419 | 63.565 | 45.126 | -18.727 | -29.328% / -29.004% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / None / `57d40b5b7469` | compared | 47 | 97.375 / 97.487 / 97.895 | 95.785 | 79.099 | -18.276 | -18.769% / -18.862% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 / glm_indexed_owner_and_projection_controls / `b79e1539e4db` | compared | 37 | 41.069 / 40.940 / 41.282 | 39.691 | 59.176 | 18.107 | 44.089% / 44.543% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 / glm78_tp16_ep16_int8kv_conditional / `0b82bdf55fb7` | compared | 44 | 57.817 / 57.597 / 59.092 | 55.203 | 39.721 | -18.096 | -31.299% / -31.037% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 / glm78_tp16_ep16_int8kv_conditional / `0b82bdf55fb7` | compared | 44 | 57.639 / 57.562 / 58.995 | 55.027 | 39.721 | -17.918 | -31.087% / -30.994% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 / qwen397_tp_join_reduce_source_contract / `b79e1539e4db` | compared | 18 | 119.054 / 119.131 / 119.486 | 118.048 | 102.780 | -16.275 | -13.670% / -13.725% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 / None / `5d7c051180a9` | compared | 76 | 28.585 / 28.571 / 28.704 | 28.300 | 14.677 | -13.908 | -48.655% / -48.630% |
| qwen36-a5-tp2-c12:q4_b12_m48 / None / `5d7c051180a9` | compared | 55 | 24.226 / 24.053 / 24.711 | 23.858 | 10.999 | -13.227 | -54.600% / -54.273% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / None / `57d40b5b7469` | compared | 49 | 69.361 / 69.418 / 69.528 | 67.823 | 57.412 | -11.949 | -17.227% / -17.296% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / glm78_tp16_ep16_int8kv_conditional / `0b82bdf55fb7` | compared | 49 | 69.556 / 69.489 / 69.830 | 66.970 | 57.630 | -11.926 | -17.146% / -17.066% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / None / `5d7c051180a9` | compared | 79 | 21.957 / 22.001 / 22.068 | 21.571 | 10.219 | -11.738 | -53.458% / -53.551% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 / quant-fixed-window8 / `f097037ac70c` | compared | 41 | 44.666 / 44.645 / 44.662 | 43.971 | 33.159 | -11.507 | -25.763% / -25.728% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 / quant-fixed-window8 / `f097037ac70c` | compared | 47 | 39.247 / 39.245 / 39.263 | 38.567 | 27.990 | -11.257 | -28.683% / -28.679% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 / quant-fixed-window8 / `f097037ac70c` | compared | 51 | 35.964 / 35.962 / 35.979 | 35.282 | 25.316 | -10.649 | -29.610% / -29.605% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 / quant-fixed-window8 / `f097037ac70c` | compared | 52 | 34.816 / 34.794 / 34.813 | 34.115 | 24.427 | -10.389 | -29.840% / -29.794% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 / quant-fixed-window8 / `f097037ac70c` | compared | 49 | 36.985 / 36.953 / 36.969 | 36.305 | 26.780 | -10.206 | -27.594% / -27.530% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 / quant-fixed-window8 / `f097037ac70c` | compared | 52 | 34.819 / 34.791 / 34.808 | 34.142 | 24.710 | -10.109 | -29.032% / -28.975% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 / quant-fixed-window8 / `f097037ac70c` | compared | 53 | 34.194 / 34.177 / 34.194 | 33.491 | 24.125 | -10.069 | -29.447% / -29.413% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 / quant-fixed-window8 / `f097037ac70c` | compared | 54 | 33.876 / 33.858 / 33.873 | 33.190 | 23.982 | -9.893 | -29.205% / -29.168% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 / quant-fixed-window8 / `f097037ac70c` | compared | 55 | 33.548 / 33.516 / 33.533 | 32.857 | 23.831 | -9.716 | -28.963% / -28.896% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 / quant-fixed-window8 / `f097037ac70c` | compared | 46 | 40.019 / 40.018 / 40.044 | 39.323 | 30.738 | -9.281 | -23.190% / -23.189% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / None / `57d40b5b7469` | compared | 32 | 33.616 / 33.626 / 33.710 | 33.358 | 24.404 | -9.212 | -27.403% / -27.424% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / None / `57d40b5b7469` | compared | 30 | 28.833 / 28.828 / 28.885 | 28.568 | 19.882 | -8.951 | -31.046% / -31.034% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / None / `57d40b5b7469` | compared | 30 | 33.031 / 33.026 / 33.164 | 32.773 | 24.217 | -8.814 | -26.684% / -26.675% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / None / `57d40b5b7469` | compared | 31 | 46.528 / 46.499 / 46.645 | 46.293 | 37.833 | -8.695 | -18.688% / -18.636% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None / `5d7c051180a9` | compared | 46 | 29.762 / 29.664 / 30.046 | 28.242 | 37.949 | 8.187 | 27.510% / 27.930% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 / None / `57d40b5b7469` | compared | 75 | 26.328 / 26.306 / 26.336 | 26.229 | 18.285 | -8.044 | -30.551% / -30.492% |
| a3_glm53_dc4k_b2:q1_b2_m2 / legacy_glm53_78_layer_w4a8 / `5d7c051180a9` | compared | 70 | 40.970 / 40.935 / 41.046 | — | 48.792 | 7.823 | 19.093% / 19.195% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 / None / `f097037ac70c` | compared | 73 | 27.286 / 27.266 / 27.290 | 27.188 | 19.508 | -7.778 | -28.505% / -28.452% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / qwen397_tp_join_reduce_source_contract / `b79e1539e4db` | compared | 23 | 76.089 / 76.132 / 76.632 | 75.005 | 68.312 | -7.777 | -10.221% / -10.272% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / None / `57d40b5b7469` | compared | 11 | 21.418 / 21.408 / 21.432 | 21.147 | 13.922 | -7.497 | -35.001% / -34.970% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / None / `57d40b5b7469` | compared | 50 | 53.893 / 53.871 / 54.021 | 52.393 | 46.557 | -7.336 | -13.612% / -13.576% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / None / `57d40b5b7469` | compared | 35 | 38.713 / 38.722 / 38.759 | 38.458 | 31.428 | -7.285 | -18.818% / -18.836% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 / quant-fixed-window8 / `f097037ac70c` | compared | 59 | 30.823 / 30.822 / 30.839 | 30.184 | 23.760 | -7.063 | -22.916% / -22.912% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / glm_indexed_owner_and_projection_controls / `b79e1539e4db` | compared | 53 | 21.068 / 21.057 / 21.170 | 20.805 | 14.025 | -7.043 | -33.429% / -33.397% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 / quant-fixed-window8 / `f097037ac70c` | compared | 59 | 30.637 / 30.615 / 30.632 | 29.997 | 23.684 | -6.952 | -22.693% / -22.638% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / None / `57d40b5b7469` | compared | 31 | 37.669 / 37.665 / 37.761 | 37.413 | 31.049 | -6.620 | -17.574% / -17.566% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / None / `5d7c051180a9` | compared | 84 | 11.551 / 11.482 / 11.818 | 11.135 | 5.049 | -6.503 | -56.294% / -56.029% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm_indexed_owner_and_projection_controls / `b79e1539e4db` | compared | 65 | 15.683 / 15.670 / 15.738 | 15.421 | 9.498 | -6.185 | -39.439% / -39.389% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / None / `57d40b5b7469` | compared | 47 | 46.859 / 46.817 / 47.175 | 45.372 | 40.676 | -6.183 | -13.196% / -13.118% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 / None / `57d40b5b7469` | compared | 105 | 18.625 / 18.616 / 18.640 | 18.526 | 12.480 | -6.144 | -32.991% / -32.960% |
| a3_glm53_dc4k_b1:q1_b1_m1 / glm_indexed_owner_and_projection_controls / `b79e1539e4db` | compared | 74 | 38.955 / 38.943 / 39.036 | — | 33.573 | -5.382 | -13.816% / -13.789% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 / None / `57d40b5b7469` | compared | 129 | 14.929 / 14.914 / 14.929 | 14.832 | 9.649 | -5.281 | -35.371% / -35.306% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 / None / `57d40b5b7469` | compared | 145 | 13.292 / 12.803 / 12.817 | 13.196 | 8.200 | -5.091 | -38.304% / -35.950% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 / None / `57d40b5b7469` | compared | 151 | 13.239 / 13.209 / 13.227 | 13.143 | 8.200 | -5.038 | -38.058% / -37.917% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 / None / `57d40b5b7469` | compared | 152 | 13.135 / 13.129 / 13.145 | 13.039 | 8.200 | -4.934 | -37.567% / -37.542% |
| qwen36-a5-tp2-c1:q4_b1_m4 / None / `5d7c051180a9` | compared | 85 | 12.318 / 12.279 / 12.362 | 11.956 | 7.413 | -4.905 | -39.822% / -39.630% |
| v4flash-a3-tp8-c4:q2_b4_m8 / None / `5d7c051180a9` | compared | 104 | 32.486 / 32.416 / 32.734 | 30.611 | 27.589 | -4.897 | -15.075% / -14.892% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / kimi_checkpoint_sp_right_pad_conditional_1f5b2971 / `f097037ac70c` | compared | 63 | 32.555 / 32.533 / 32.674 | — | 28.767 | -3.789 | -11.638% / -11.577% |
| glm53flash-a5-tp8-c96:q4_b96_m384 / None / `5d7c051180a9` | compared | 27 | 57.590 / 57.573 / 57.734 | 57.355 | 54.015 | -3.574 | -6.207% / -6.179% |
| glm53flash-a3-tp16-c2:q6_b2_m12 / None / `5d7c051180a9` | compared | 46 | 34.118 / 33.910 / 35.073 | 32.625 | 30.804 | -3.314 | -9.714% / -9.159% |
| a3_glm53_dc4k_b8:q1_b8_m8 / glm_indexed_owner_and_projection_controls / `b79e1539e4db` | compared | 61 | 47.113 / 47.149 / 47.402 | — | 44.050 | -3.063 | -6.502% / -6.572% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 / None / `f097037ac70c` | compared | 29 | 48.582 / 48.412 / 48.662 | 47.883 | 51.618 | 3.036 | 6.250% / 6.624% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 / None / `f097037ac70c` | compared | 48 | 47.654 / 47.425 / 47.666 | 46.949 | 50.240 | 2.586 | 5.428% / 5.936% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 / None / `f097037ac70c` | compared | 32 | 49.985 / 49.802 / 50.230 | 49.318 | 52.408 | 2.423 | 4.847% / 5.231% |
| a3_glm53_dc16k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 / `5d7c051180a9` | compared | 74 | 39.112 / 39.105 / 39.196 | — | 36.961 | -2.151 | -5.501% / -5.483% |
| v4flash-a3-tp8-c8:q2_b8_m16 / None / `5d7c051180a9` | compared | 104 | 37.763 / 37.868 / 38.082 | 36.154 | 35.758 | -2.005 | -5.309% / -5.572% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None / `5d7c051180a9` | compared | 46 | 39.841 / 39.798 / 40.057 | 38.324 | 37.949 | -1.892 | -4.750% / -4.647% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 / None / `f097037ac70c` | compared | 21 | 61.811 / 61.629 / 62.042 | 61.115 | 63.336 | 1.525 | 2.467% / 2.770% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 / quant-fixed-window8 / `f097037ac70c` | compared | 235 | 4.807 / 4.779 / 4.992 | 4.709 | 3.698 | -1.110 | -23.081% / -22.629% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 / quant-fixed-window8 / `f097037ac70c` | compared | 220 | 6.714 / 6.665 / 6.923 | 6.609 | 5.671 | -1.043 | -15.528% / -14.907% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 / None / `f097037ac70c` | compared | 22 | 54.967 / 54.880 / 55.047 | 54.296 | 55.855 | 0.888 | 1.616% / 1.776% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 / quant-fixed-window8 / `f097037ac70c` | compared | 246 | 3.476 / 3.438 / 3.656 | 3.380 | 2.627 | -0.849 | -24.425% / -23.581% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 / quant-fixed-window8 / `f097037ac70c` | compared | 196 | 9.615 / 9.550 / 9.774 | 9.502 | 8.924 | -0.691 | -7.186% / -6.546% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 / quant-fixed-window8 / `f097037ac70c` | compared | 254 | 3.180 / 3.128 / 3.432 | 3.088 | 2.567 | -0.613 | -19.275% / -17.922% |
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

## Layer 0 and steady layer groups

The steady P50 column is median of per-layer call P50, unless a separately linked receipt supplies exact pooled statistics.

| Case | Group | Layers | Real Mean ms | Median layer-call P50 ms | Sim Mean ms | Mean / P50 error |
|---|---|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b4:q1_b4_m4 / legacy_glm53_78_layer_w4a8 | Layer 0 / mla / dense_layer | 1 | 0.4118 | 0.4071 | 0.6140 | 49.118% / 50.826% |
| a3_glm53_dc4k_b4:q1_b4_m4 / legacy_glm53_78_layer_w4a8 | Steady / mla / dense_layer | 2 | 0.3968 | 0.3931 | 0.6140 | 54.728% / 56.217% |
| a3_glm53_dc4k_b4:q1_b4_m4 / legacy_glm53_78_layer_w4a8 | Steady / mla / moe_layer | 75 | 0.5622 | 0.5411 | 0.9355 | 66.402% / 72.867% |
| qwen36-a5-tp2-c96:q4_b96_m384 / None | Layer 0 / gdn / dense_layer | 1 | 1.3691 | 1.0682 | 0.7556 | -44.813% / -29.265% |
| qwen36-a5-tp2-c96:q4_b96_m384 / None | Steady / gdn / dense_layer | 47 | 1.0584 | 1.0584 | 0.7556 | -28.615% / -28.614% |
| qwen36-a5-tp2-c96:q4_b96_m384 / None | Steady / gqa / dense_layer | 16 | 0.7931 | 0.7928 | 0.5537 | -30.186% / -30.151% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / None | Layer 0 / kda / dense_layer | 1 | 1.3232 | 1.3221 | 1.0892 | -17.687% / -17.616% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / None | Steady / kda / dense_layer | 2 | 1.2997 | 1.3012 | 1.0892 | -16.193% / -16.294% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / None | Steady / mla / moe_layer | 11 | 3.5285 | 3.5319 | 2.2117 | -37.319% / -37.379% |
| a3_glm53flash_tp16_aclgraph_c64:q6_b64_m384 / None | Steady / kda / moe_layer | 31 | 1.7609 | 1.7632 | 1.6614 | -5.651% / -5.775% |
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
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / None | Layer 0 / kda / dense_layer | 1 | 0.9534 | 0.9082 | 0.6822 | -28.447% / -24.884% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / None | Steady / kda / dense_layer | 2 | 0.8762 | 0.8787 | 0.6822 | -22.143% / -22.363% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / None | Steady / mla / moe_layer | 11 | 2.3319 | 2.3310 | 1.5446 | -33.763% / -33.737% |
| a3_glm53flash_tp16_aclgraph_c32:q6_b32_m192 / None | Steady / kda / moe_layer | 31 | 1.3210 | 1.3204 | 1.2379 | -6.293% / -6.249% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / glm78_tp16_ep16_int8kv_conditional | Layer 0 / mla / dense_layer | 1 | 0.6710 | 0.6210 | 0.4517 | -32.682% / -27.268% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / glm78_tp16_ep16_int8kv_conditional | Steady / mla / dense_layer | 2 | 0.6345 | 0.6104 | 0.4517 | -28.816% / -26.005% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 / glm78_tp16_ep16_int8kv_conditional | Steady / mla / moe_layer | 75 | 0.9015 | 0.8670 | 0.7503 | -16.768% / -13.452% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / None | Layer 0 / gdn / moe_layer | 1 | 0.7737 | 0.8216 | 0.2645 | -65.808% / -67.803% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / None | Steady / gdn / moe_layer | 29 | 0.5470 | 0.5467 | 0.2645 | -51.637% / -51.614% |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 / None | Steady / gqa / moe_layer | 10 | 0.5320 | 0.5323 | 0.2283 | -57.085% / -57.109% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.3620 | 0.3384 | 0.3055 | -15.605% / -9.711% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 / quant-fixed-window8 | Steady / kda / moe_layer | 68 | 0.4145 | 0.4142 | 0.3386 | -18.315% / -18.259% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 / quant-fixed-window8 | Steady / mla / moe_layer | 24 | 0.6715 | 0.6644 | 0.4090 | -39.089% / -38.434% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.3047 | 0.3023 | 0.2622 | -13.943% / -13.252% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 / quant-fixed-window8 | Steady / kda / moe_layer | 68 | 0.3858 | 0.3856 | 0.2952 | -23.485% / -23.440% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 / quant-fixed-window8 | Steady / mla / moe_layer | 24 | 0.5293 | 0.5223 | 0.3183 | -39.860% / -39.054% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.2840 | 0.2810 | 0.2397 | -15.606% / -14.710% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 / quant-fixed-window8 | Steady / kda / moe_layer | 68 | 0.3653 | 0.3650 | 0.2724 | -25.431% / -25.372% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 / quant-fixed-window8 | Steady / mla / moe_layer | 24 | 0.4517 | 0.4454 | 0.2726 | -39.651% / -38.808% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.2974 | 0.2770 | 0.2334 | -21.527% / -15.745% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 / quant-fixed-window8 | Steady / kda / moe_layer | 68 | 0.3596 | 0.3592 | 0.2661 | -26.018% / -25.938% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 / quant-fixed-window8 | Steady / mla / moe_layer | 24 | 0.4192 | 0.4125 | 0.2537 | -39.496% / -38.503% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.3353 | 0.3023 | 0.2622 | -21.802% / -13.253% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 / quant-fixed-window8 | Steady / kda / moe_layer | 68 | 0.3857 | 0.3855 | 0.2952 | -23.470% / -23.427% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 / quant-fixed-window8 | Steady / mla / moe_layer | 24 | 0.4340 | 0.4269 | 0.2679 | -38.272% / -37.238% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.3102 | 0.2816 | 0.2397 | -22.718% / -14.868% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 / quant-fixed-window8 | Steady / kda / moe_layer | 68 | 0.3652 | 0.3648 | 0.2724 | -25.428% / -25.335% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 / quant-fixed-window8 | Steady / mla / moe_layer | 24 | 0.4029 | 0.3960 | 0.2474 | -38.605% / -37.532% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.2930 | 0.2771 | 0.2334 | -20.351% / -15.778% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 / quant-fixed-window8 | Steady / kda / moe_layer | 68 | 0.3596 | 0.3596 | 0.2661 | -26.020% / -26.003% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 / quant-fixed-window8 | Steady / mla / moe_layer | 24 | 0.3935 | 0.3863 | 0.2411 | -38.734% / -37.604% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.2876 | 0.2698 | 0.2302 | -19.937% / -14.665% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 / quant-fixed-window8 | Steady / kda / moe_layer | 68 | 0.3531 | 0.3529 | 0.2629 | -25.547% / -25.503% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 / quant-fixed-window8 | Steady / mla / moe_layer | 24 | 0.3989 | 0.3918 | 0.2442 | -38.784% / -37.667% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.3027 | 0.2698 | 0.2302 | -23.929% / -14.680% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 / quant-fixed-window8 | Steady / kda / moe_layer | 68 | 0.3533 | 0.3531 | 0.2629 | -25.593% / -25.555% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 / quant-fixed-window8 | Steady / mla / moe_layer | 24 | 0.3840 | 0.3767 | 0.2379 | -38.046% / -36.851% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.3379 | 0.3376 | 0.3055 | -9.589% / -9.495% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 / quant-fixed-window8 | Steady / kda / moe_layer | 68 | 0.4141 | 0.4140 | 0.3386 | -18.246% / -18.227% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 / quant-fixed-window8 | Steady / mla / moe_layer | 24 | 0.4799 | 0.4722 | 0.3082 | -35.779% / -34.740% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / None | Layer 0 / kda / dense_layer | 1 | 0.3876 | 0.4019 | 0.1696 | -56.257% / -57.814% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / None | Steady / kda / dense_layer | 2 | 0.2980 | 0.2974 | 0.1696 | -43.106% / -42.983% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / None | Steady / mla / moe_layer | 11 | 1.0591 | 1.0543 | 0.6235 | -41.134% / -40.868% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 / None | Steady / kda / moe_layer | 31 | 0.6768 | 0.6768 | 0.5496 | -18.796% / -18.795% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / None | Layer 0 / kda / dense_layer | 1 | 0.4973 | 0.4989 | 0.1495 | -69.939% / -70.033% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / None | Steady / kda / dense_layer | 2 | 0.2536 | 0.2520 | 0.1495 | -41.056% / -40.683% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / None | Steady / mla / moe_layer | 11 | 0.8678 | 0.8641 | 0.4917 | -43.337% / -43.093% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 / None | Steady / kda / moe_layer | 31 | 0.5897 | 0.5893 | 0.4524 | -23.288% / -23.234% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / None | Layer 0 / kda / dense_layer | 1 | 0.3980 | 0.3937 | 0.1696 | -57.393% / -56.931% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / None | Steady / kda / dense_layer | 2 | 0.2982 | 0.2982 | 0.1696 | -43.145% / -43.138% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / None | Steady / mla / moe_layer | 11 | 1.0018 | 0.9978 | 0.6064 | -39.468% / -39.225% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 / None | Steady / kda / moe_layer | 31 | 0.6779 | 0.6772 | 0.5496 | -18.929% / -18.840% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / None | Layer 0 / kda / dense_layer | 1 | 0.5510 | 0.5299 | 0.3125 | -43.282% / -41.023% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / None | Steady / kda / dense_layer | 2 | 0.4693 | 0.4691 | 0.3125 | -33.408% / -33.377% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / None | Steady / mla / moe_layer | 11 | 1.5929 | 1.5839 | 0.9837 | -38.247% / -37.895% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 / None | Steady / kda / moe_layer | 31 | 0.8876 | 0.8877 | 0.8411 | -5.235% / -5.249% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None | Layer 0 / kda / dense_layer | 1 | 0.8292 | 0.7249 | 0.4474 | -46.044% / -38.275% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None | Steady / kda / dense_layer | 2 | 0.2964 | 0.2961 | 0.4474 | 50.956% / 51.096% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None | Steady / mla / moe_layer | 11 | 0.9295 | 0.9276 | 0.8975 | -3.445% / -3.245% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 / None | Steady / kda / moe_layer | 31 | 0.5827 | 0.5821 | 0.8624 | 48.002% / 48.147% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 / None | Layer 0 / mla / moe_layer | 1 | 0.7498 | 0.7292 | 0.4471 | -40.378% / -38.688% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 / None | Steady / mla / moe_layer | 39 | 0.6558 | 0.6334 | 0.4574 | -30.256% / -27.787% |
| a3_glm53_dc4k_b2:q1_b2_m2 / legacy_glm53_78_layer_w4a8 | Layer 0 / mla / dense_layer | 1 | 0.4105 | 0.3960 | 0.4397 | 7.121% / 11.061% |
| a3_glm53_dc4k_b2:q1_b2_m2 / legacy_glm53_78_layer_w4a8 | Steady / mla / dense_layer | 2 | 0.3997 | 0.3865 | 0.4397 | 10.026% / 13.773% |
| a3_glm53_dc4k_b2:q1_b2_m2 / legacy_glm53_78_layer_w4a8 | Steady / mla / moe_layer | 75 | 0.5293 | 0.5092 | 0.6330 | 19.591% / 24.318% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 / None | Layer 0 / mla / moe_layer | 1 | 0.8025 | 0.7842 | 0.4768 | -40.579% / -39.191% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 / None | Steady / mla / moe_layer | 39 | 0.6790 | 0.6545 | 0.4880 | -28.136% / -25.445% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / qwen397_tp_join_reduce_source_contract | Layer 0 / gdn / moe_layer | 1 | 1.3503 | 1.2865 | 1.1042 | -18.226% / -14.168% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / qwen397_tp_join_reduce_source_contract | Steady / gdn / moe_layer | 44 | 1.2329 | 1.2077 | 1.1042 | -10.437% / -8.569% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 / qwen397_tp_join_reduce_source_contract | Steady / gqa / moe_layer | 15 | 1.3614 | 1.3469 | 1.2415 | -8.812% / -7.829% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / None | Layer 0 / kda / dense_layer | 1 | 0.3235 | 0.2805 | 0.1398 | -56.778% / -50.157% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / None | Steady / kda / dense_layer | 2 | 0.2349 | 0.2350 | 0.1398 | -40.491% / -40.504% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / None | Steady / mla / moe_layer | 11 | 0.6731 | 0.6714 | 0.3473 | -48.410% / -48.273% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 / None | Steady / kda / moe_layer | 31 | 0.4264 | 0.4251 | 0.3123 | -26.758% / -26.529% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / None | Layer 0 / kda / dense_layer | 1 | 0.6895 | 0.6689 | 0.4850 | -29.657% / -27.484% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / None | Steady / kda / dense_layer | 2 | 0.6561 | 0.6366 | 0.4850 | -26.071% / -23.803% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / None | Steady / mla / moe_layer | 11 | 1.6861 | 1.6864 | 1.2074 | -28.394% / -28.406% |
| a3_glm53flash_tp16_aclgraph_c16:q6_b16_m96 / None | Steady / kda / moe_layer | 31 | 1.0740 | 1.0740 | 1.0265 | -4.420% / -4.422% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / None | Layer 0 / kda / dense_layer | 1 | 0.4891 | 0.4818 | 0.2158 | -55.871% / -55.204% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / None | Steady / kda / dense_layer | 2 | 0.3535 | 0.3535 | 0.2158 | -38.952% / -38.940% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / None | Steady / mla / moe_layer | 11 | 1.2946 | 1.2899 | 0.8264 | -36.166% / -35.935% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 / None | Steady / kda / moe_layer | 31 | 0.7508 | 0.7507 | 0.6997 | -6.811% / -6.797% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.2595 | 0.2581 | 0.2287 | -11.886% / -11.424% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 / quant-fixed-window8 | Steady / kda / moe_layer | 68 | 0.3208 | 0.3208 | 0.2613 | -18.540% / -18.543% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 / quant-fixed-window8 | Steady / mla / moe_layer | 24 | 0.3644 | 0.3577 | 0.2395 | -34.293% / -33.060% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / glm_indexed_owner_and_projection_controls | Layer 0 / kda / dense_layer | 1 | 0.4650 | 0.4745 | 0.1476 | -68.256% / -68.890% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / glm_indexed_owner_and_projection_controls | Steady / kda / dense_layer | 2 | 0.2383 | 0.2328 | 0.1476 | -38.059% / -36.597% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / glm_indexed_owner_and_projection_controls | Steady / mla / moe_layer | 11 | 0.6392 | 0.6337 | 0.3466 | -45.778% / -45.309% |
| glm53flash-a5-tp8-c3:q4_b4_m16 / glm_indexed_owner_and_projection_controls | Steady / kda / moe_layer | 31 | 0.4224 | 0.4216 | 0.3152 | -25.389% / -25.256% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.2772 | 0.2578 | 0.2287 | -17.520% / -11.312% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 / quant-fixed-window8 | Steady / kda / moe_layer | 68 | 0.3209 | 0.3210 | 0.2613 | -18.566% / -18.594% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 / quant-fixed-window8 | Steady / mla / moe_layer | 24 | 0.3556 | 0.3487 | 0.2363 | -33.552% / -32.229% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / None | Layer 0 / kda / dense_layer | 1 | 0.4873 | 0.4626 | 0.2158 | -55.711% / -53.348% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / None | Steady / kda / dense_layer | 2 | 0.3528 | 0.3529 | 0.2158 | -38.828% / -38.837% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / None | Steady / mla / moe_layer | 11 | 1.1973 | 1.1925 | 0.7919 | -33.858% / -33.591% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 / None | Steady / kda / moe_layer | 31 | 0.7518 | 0.7522 | 0.6997 | -6.927% / -6.981% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / None | Layer 0 / gdn / moe_layer | 1 | 0.3868 | 0.2973 | 0.1242 | -67.899% / -58.244% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / None | Steady / gdn / moe_layer | 29 | 0.2819 | 0.2827 | 0.1242 | -55.959% / -56.087% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 / None | Steady / gqa / moe_layer | 10 | 0.2989 | 0.2992 | 0.1324 | -55.697% / -55.742% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm_indexed_owner_and_projection_controls | Layer 0 / kda / dense_layer | 1 | 0.4222 | 0.4383 | 0.1284 | -69.600% / -70.713% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm_indexed_owner_and_projection_controls | Steady / kda / dense_layer | 2 | 0.2487 | 0.2314 | 0.1284 | -48.386% / -44.529% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm_indexed_owner_and_projection_controls | Steady / mla / moe_layer | 11 | 0.4952 | 0.4903 | 0.2353 | -52.477% / -52.003% |
| glm53flash-a5-tp8-c1:q4_b1_m4 / glm_indexed_owner_and_projection_controls | Steady / kda / moe_layer | 31 | 0.3005 | 0.2985 | 0.2105 | -29.965% / -29.500% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / None | Layer 0 / kda / dense_layer | 1 | 0.6412 | 0.5810 | 0.4011 | -37.441% / -30.961% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / None | Steady / kda / dense_layer | 2 | 0.6152 | 0.5329 | 0.4011 | -34.801% / -24.730% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / None | Steady / mla / moe_layer | 11 | 1.4099 | 1.4072 | 1.0288 | -27.027% / -26.888% |
| a3_glm53flash_tp16_aclgraph_c8:q6_b8_m48 / None | Steady / kda / moe_layer | 31 | 0.9493 | 0.9478 | 0.9082 | -4.323% / -4.174% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 / None | Layer 0 / mla / moe_layer | 1 | 0.5279 | 0.5209 | 0.3023 | -42.739% / -41.963% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 / None | Steady / mla / moe_layer | 39 | 0.4640 | 0.4441 | 0.3123 | -32.698% / -29.682% |
| a3_glm53_dc4k_b1:q1_b1_m1 / glm_indexed_owner_and_projection_controls | Layer 0 / mla / dense_layer | 1 | 0.3943 | 0.3854 | 0.3526 | -10.563% / -8.497% |
| a3_glm53_dc4k_b1:q1_b1_m1 / glm_indexed_owner_and_projection_controls | Steady / mla / dense_layer | 2 | 0.3841 | 0.3775 | 0.3526 | -8.207% / -6.585% |
| a3_glm53_dc4k_b1:q1_b1_m1 / glm_indexed_owner_and_projection_controls | Steady / mla / moe_layer | 75 | 0.5031 | 0.4848 | 0.4335 | -13.823% / -10.574% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 / None | Layer 0 / mla / moe_layer | 1 | 0.4353 | 0.4201 | 0.2316 | -46.783% / -44.863% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 / None | Steady / mla / moe_layer | 39 | 0.3716 | 0.3526 | 0.2415 | -35.017% / -31.524% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 / None | Layer 0 / mla / moe_layer | 1 | 0.8501 | 0.3611 | 0.1955 | -77.007% / -45.863% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 / None | Steady / mla / moe_layer | 39 | 0.3189 | 0.3014 | 0.2053 | -35.647% / -31.893% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 / None | Layer 0 / mla / moe_layer | 1 | 0.8470 | 0.8162 | 0.1955 | -76.923% / -76.052% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 / None | Steady / mla / moe_layer | 39 | 0.3177 | 0.3003 | 0.2053 | -35.389% / -31.650% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 / None | Layer 0 / mla / moe_layer | 1 | 0.8189 | 0.8103 | 0.1955 | -76.130% / -75.876% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 / None | Steady / mla / moe_layer | 39 | 0.3157 | 0.2984 | 0.2053 | -34.990% / -31.206% |
| qwen36-a5-tp2-c1:q4_b1_m4 / None | Layer 0 / gdn / dense_layer | 1 | 0.2400 | 0.1984 | 0.1154 | -51.909% / -41.833% |
| qwen36-a5-tp2-c1:q4_b1_m4 / None | Steady / gdn / dense_layer | 47 | 0.1919 | 0.1915 | 0.1154 | -39.861% / -39.732% |
| qwen36-a5-tp2-c1:q4_b1_m4 / None | Steady / gqa / dense_layer | 16 | 0.1880 | 0.1876 | 0.1171 | -37.704% / -37.562% |
| v4flash-a3-tp8-c4:q2_b4_m8 / None | Layer 0 / mla / moe_layer | 1 | 0.7568 | 0.7178 | 0.5579 | -26.289% / -22.282% |
| v4flash-a3-tp8-c4:q2_b4_m8 / None | Steady / mla / moe_layer | 42 | 0.7543 | 0.7537 | 0.6436 | -14.674% / -14.607% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / kimi_checkpoint_sp_right_pad_conditional_1f5b2971 | Layer 0 / kda / dense_layer | 1 | 0.2579 | 0.2383 | 0.1850 | -28.258% / -22.349% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / kimi_checkpoint_sp_right_pad_conditional_1f5b2971 | Steady / kda / moe_layer | 68 | 0.3399 | 0.3386 | 0.3140 | -7.619% / -7.257% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 / kimi_checkpoint_sp_right_pad_conditional_1f5b2971 | Steady / mla / moe_layer | 24 | 0.3835 | 0.3747 | 0.3005 | -21.646% / -19.793% |
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
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 / None | Layer 0 / mla / moe_layer | 1 | 1.4227 | 1.2523 | 1.2726 | -10.555% / 1.616% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 / None | Steady / mla / moe_layer | 39 | 1.2164 | 1.1586 | 1.2909 | 6.129% / 11.417% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 / None | Layer 0 / mla / moe_layer | 1 | 1.9490 | 1.6565 | 1.2400 | -36.378% / -25.145% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 / None | Steady / mla / moe_layer | 39 | 1.1795 | 1.1292 | 1.2564 | 6.525% / 11.267% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 / None | Layer 0 / mla / moe_layer | 1 | 1.4398 | 1.2987 | 1.2913 | -10.313% / -0.567% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 / None | Steady / mla / moe_layer | 39 | 1.2521 | 1.1883 | 1.3107 | 4.675% / 10.300% |
| a3_glm53_dc16k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 | Layer 0 / mla / dense_layer | 1 | 0.4020 | 0.3967 | 0.3526 | -12.294% / -11.111% |
| a3_glm53_dc16k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 | Steady / mla / dense_layer | 2 | 0.3934 | 0.3879 | 0.3526 | -10.369% / -9.102% |
| a3_glm53_dc16k_b1:q1_b1_m1 / legacy_glm53_78_layer_w4a8 | Steady / mla / moe_layer | 75 | 0.5045 | 0.4834 | 0.4787 | -5.110% / -0.982% |
| v4flash-a3-tp8-c8:q2_b8_m16 / None | Layer 0 / mla / moe_layer | 1 | 0.8072 | 0.7668 | 0.7432 | -7.929% / -3.069% |
| v4flash-a3-tp8-c8:q2_b8_m16 / None | Steady / mla / moe_layer | 42 | 0.8787 | 0.8831 | 0.8337 | -5.126% / -5.595% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None | Layer 0 / kda / dense_layer | 1 | 0.6141 | 0.5825 | 0.4474 | -27.138% / -23.185% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None | Steady / kda / dense_layer | 2 | 0.6160 | 0.5541 | 0.4474 | -27.368% / -19.246% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None | Steady / mla / moe_layer | 11 | 1.1665 | 1.1644 | 0.8975 | -23.064% / -22.924% |
| glm53flash-a3-tp16-c4:q6_b4_m24 / None | Steady / kda / moe_layer | 31 | 0.8101 | 0.8087 | 0.8624 | 6.462% / 6.640% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 / None | Layer 0 / mla / moe_layer | 1 | 1.6498 | 1.4734 | 1.5524 | -5.900% / 5.367% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 / None | Steady / mla / moe_layer | 39 | 1.5477 | 1.4627 | 1.5842 | 2.359% / 8.305% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.9021 | 0.9359 | 0.5081 | -43.678% / -45.710% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 / quant-fixed-window8 | Steady / kda / moe_layer | 2 | 1.2773 | 1.2657 | 1.0751 | -15.832% / -15.058% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 / quant-fixed-window8 | Steady / mla / moe_layer | 1 | 1.4535 | 1.4525 | 1.0208 | -29.769% / -29.719% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.8847 | 0.9181 | 0.6202 | -29.897% / -32.448% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 / quant-fixed-window8 | Steady / kda / moe_layer | 2 | 1.8592 | 1.8408 | 1.6975 | -8.699% / -7.784% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 / quant-fixed-window8 | Steady / mla / moe_layer | 1 | 2.1726 | 2.1723 | 1.6366 | -24.673% / -24.664% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 / None | Layer 0 / mla / moe_layer | 1 | 1.6970 | 1.5640 | 1.3736 | -19.058% / -12.176% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 / None | Steady / mla / moe_layer | 39 | 1.3715 | 1.3077 | 1.3970 | 1.858% / 6.825% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.8688 | 0.8927 | 0.4299 | -50.522% / -51.848% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 / quant-fixed-window8 | Steady / kda / moe_layer | 2 | 0.8910 | 0.8481 | 0.7419 | -16.735% / -12.529% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 / quant-fixed-window8 | Steady / mla / moe_layer | 1 | 0.9683 | 0.9617 | 0.6931 | -28.417% / -27.921% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.9604 | 0.9526 | 0.8444 | -12.084% / -11.364% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 / quant-fixed-window8 | Steady / kda / moe_layer | 2 | 2.7714 | 2.7569 | 2.7106 | -2.195% / -1.680% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 / quant-fixed-window8 | Steady / mla / moe_layer | 1 | 3.2092 | 3.2089 | 2.6374 | -17.819% / -17.812% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 / quant-fixed-window8 | Layer 0 / kda / dense_layer | 1 | 0.9219 | 0.9116 | 0.4149 | -55.000% / -54.491% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 / quant-fixed-window8 | Steady / kda / moe_layer | 2 | 0.7774 | 0.7254 | 0.7269 | -6.505% / 0.197% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 / quant-fixed-window8 | Steady / mla / moe_layer | 1 | 0.8359 | 0.7994 | 0.6781 | -18.876% / -15.169% |

## Heavy >50us operators — activity residual priority

| Case | Operator / role | Calls | Real / Sim us | Diff us | Absolute ms / Forward | Tier pass |
|---|---|---:|---:|---:|---:|---|
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | GroupedMatmulSituQuant / grouped_gate_up_situ_quant | 5796 | 74.250 / 7.735 | -66.515 | 6.119 | None (reference_only) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1554 | 142.415 / 285.783 | 143.367 | 6.021 | None (reference_only) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | SituMxQuant / shared.situ_quant | 5796 | 65.155 / 1.312 | -63.843 | 5.874 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c8 / matrix-extension / `ab58f99ac6e3` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 226.015 / 307.364 | 81.349 | 3.417 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension / `ab58f99ac6e3` | HcPre / attention.hc_pre | 2115 | 66.201 / 140.178 | 73.977 | 3.329 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension / `ab58f99ac6e3` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 245.405 / 320.328 | 74.923 | 3.147 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c32 / matrix-extension / `ab58f99ac6e3` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2058 | 243.005 / 312.922 | 69.917 | 2.937 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension / `ab58f99ac6e3` | HcPre / ffn.hc_pre | 2115 | 75.216 / 140.178 | 64.962 | 2.923 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c16 / matrix-extension / `ab58f99ac6e3` | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2100 | 241.813 / 309.212 | 67.399 | 2.831 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c32 / matrix-extension / `ab58f99ac6e3` | HcPre / attention.hc_pre | 2205 | 52.080 / 87.498 | 35.419 | 1.594 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c32 / matrix-extension / `ab58f99ac6e3` | HcPre / ffn.hc_pre | 2205 | 52.730 / 87.498 | 34.768 | 1.565 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension / `ab58f99ac6e3` | MatMulV2 / linear_qkvbfg_a | 1598 | 64.341 / 101.405 | 37.064 | 1.260 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension / `ab58f99ac6e3` | HcPost / attention.hc_post_group | 2115 | 51.747 / 26.810 | -24.937 | 1.122 | False (compared) |
| a5_glm53flash_tp8_c64_p4k / glm-flash-ws9 / `ab58f99ac6e3` | GroupedMatmul / expert_down | 1302 | 115.777 / 93.730 | -22.047 | 0.926 | False (compared) |
| a5_glm53flash_tp8_c32_p8k / glm-flash-ws9 / `ab58f99ac6e3` | GroupedMatmul / expert_down | 1470 | 109.853 / 89.495 | -20.357 | 0.855 | False (compared) |
| a5_glm53flash_tp8_c32_p4k / glm-flash-ws9 / `ab58f99ac6e3` | GroupedMatmul / expert_down | 1302 | 109.824 / 89.495 | -20.328 | 0.854 | False (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | GroupedMatmul / expert_down | 2226 | 51.524 / 34.915 | -16.609 | 0.698 | False (compared) |
| a5_glm53flash_tp8_c16_p4k / glm-flash-ws9 / `ab58f99ac6e3` | GroupedMatmul / expert_down | 1260 | 103.104 / 87.379 | -15.725 | 0.660 | False (compared) |
| a5_glm53flash_tp8_c16_p8k / glm-flash-ws9 / `ab58f99ac6e3` | GroupedMatmul / expert_down | 1344 | 102.724 / 87.379 | -15.345 | 0.644 | True (compared) |
| a5_glm53flash_tp8_c8_p4k / glm-flash-ws9 / `ab58f99ac6e3` | GroupedMatmul / expert_down | 1260 | 91.186 / 76.841 | -14.345 | 0.602 | False (compared) |
| a5_glm53flash_tp8_c4_p8k / glm-flash-ws9 / `ab58f99ac6e3` | GroupedMatmul / expert_down | 462 | 51.435 / 38.424 | -13.011 | 0.546 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension / `ab58f99ac6e3` | MatMulV2 / qkv_a | 517 | 56.384 / 101.486 | 45.102 | 0.496 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension / `ab58f99ac6e3` | MatMulV2 / index_q | 517 | 59.327 / 70.876 | 11.549 | 0.127 | False (compared) |
| a3_kimi4_tp8_w4a8_c64 / kimi-variants / `ddbc84222bf7` | QuantBatchMatmulV3 / gate_up | 196 | 60.636 / 89.300 | 28.664 | 0.029 | False (compared) |
| a3_kimi4_tp8_w4a8_c32 / kimi-variants / `ddbc84222bf7` | QuantBatchMatmulV3 / gate_up | 220 | 56.800 / 79.579 | 22.779 | 0.023 | False (compared) |
| a3_kimi4_tp8_w4a8_c16 / kimi-variants / `ddbc84222bf7` | QuantBatchMatmulV3 / gate_up | 235 | 55.989 / 74.718 | 18.729 | 0.019 | False (compared) |
| a3_kimi4_tp8_w4a8_c4 / kimi-variants / `ddbc84222bf7` | QuantBatchMatmulV3 / gate_up | 246 | 54.590 / 72.287 | 17.698 | 0.018 | False (compared) |
| a3_kimi4_tp8_w4a8_c1 / kimi-variants / `ddbc84222bf7` | QuantBatchMatmulV3 / gate_up | 254 | 56.548 / 72.287 | 15.739 | 0.016 | False (compared) |
| a5_kimi_tp8_e16_bf16_c32_p16k / kimi-variants / `ddbc84222bf7` | MatMulV3 / gate_up | 41 | 59.157 / 52.713 | -6.444 | 0.006 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p4k / kimi-variants / `ddbc84222bf7` | MatMulV3 / gate_up | 46 | 59.094 / 52.713 | -6.381 | 0.006 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p16k / kimi-variants / `ddbc84222bf7` | MatMulV3 / gate_up | 47 | 53.443 / 47.325 | -6.118 | 0.006 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p4k / kimi-variants / `ddbc84222bf7` | MatMulV3 / gate_up | 49 | 53.114 / 47.325 | -5.789 | 0.006 | True (compared) |
| a3_kimi4_tp8_w4a8_c64 / kimi-variants / `ddbc84222bf7` | MatMulV2 / output_gate | 196 | 51.145 / 52.683 | 1.538 | 0.002 | True (compared) |

## Micro <=50us operators — activity residual priority

| Case | Operator / role | Calls | Real / Sim us | Diff us | Absolute ms / Forward | Tier pass |
|---|---|---:|---:|---:|---:|---|
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | HcPre / attention.hc_pre | 1665 | 33.367 / 170.549 | 137.182 | 6.173 | None (reference_only) |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 / `df7c8117e01b` | HcPre / ffn.hc_pre | 1665 | 36.039 / 170.549 | 134.510 | 6.053 | None (reference_only) |
| a5_glm53flash_tp8_c32_p4k / glm-flash-ws9 / `ab58f99ac6e3` | MatMulV3 / router | 1302 | 19.915 / 159.682 | 139.767 | 5.870 | False (compared) |
| a5_glm53flash_tp8_c32_p8k / glm-flash-ws9 / `ab58f99ac6e3` | MatMulV3 / router | 1470 | 19.930 / 159.682 | 139.752 | 5.870 | False (compared) |
| a5_glm53flash_tp8_c64_p4k / glm-flash-ws9 / `ab58f99ac6e3` | MatMulV3 / router | 1302 | 29.762 / 159.682 | 129.920 | 5.457 | False (compared) |
| a5_glm53flash_tp8_c16_p8k / glm-flash-ws9 / `ab58f99ac6e3` | MatMulV3 / router | 1344 | 13.497 / 80.004 | 66.506 | 2.793 | False (compared) |
| a5_glm53flash_tp8_c16_p4k / glm-flash-ws9 / `ab58f99ac6e3` | MatMulV3 / router | 1260 | 13.545 / 80.004 | 66.459 | 2.791 | False (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | QuantBatchMatmulV4 / shared.gate_up | 5796 | 30.427 / 3.963 | -26.464 | 2.435 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension / `ab58f99ac6e3` | QuantBatchMatmulV3 / shared.down | 1974 | 41.694 / 8.888 | -32.806 | 1.378 | False (compared) |
| a5_glm53flash_tp8_c8_p4k / glm-flash-ws9 / `ab58f99ac6e3` | MatMulV3 / router | 1260 | 12.319 / 40.165 | 27.846 | 1.170 | False (compared) |
| a5_kimi_tp8_e16_bf16_c32_p16k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_down | 3772 | 26.876 / 14.433 | -12.443 | 1.145 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p4k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_down | 4232 | 26.875 / 14.433 | -12.442 | 1.145 | True (compared) |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical / `886c1fa5bd45` | QuantBatchMatmulV4 / shared.down | 5796 | 13.143 / 1.578 | -11.565 | 1.064 | None (reference_only) |
| a5_kimi_tp8_e16_bf16_c16_p16k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_down | 4324 | 25.351 / 14.206 | -11.145 | 1.025 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p4k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_down | 4508 | 25.319 / 14.206 | -11.113 | 1.022 | True (compared) |
| a3_glm53flash_tp16_aclgraph_c32 / matrix-extension / `ab58f99ac6e3` | QuantBatchMatmulV3 / shared.down | 2058 | 28.641 / 5.000 | -23.641 | 0.993 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c16 / matrix-extension / `ab58f99ac6e3` | HcPre / attention.hc_pre | 2250 | 39.826 / 61.158 | 21.332 | 0.960 | None (reference_only) |
| a5_kimi_tp8_e16_bf16_c8_p4k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_down | 4784 | 24.439 / 14.093 | -10.346 | 0.952 | True (compared) |
| a5_kimi_tp8_e16_bf16_c8_p16k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_down | 4692 | 24.431 / 14.093 | -10.338 | 0.951 | True (compared) |
| a5_kimi_tp8_e16_bf16_c4_p4k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_down | 4876 | 24.291 / 14.093 | -10.198 | 0.938 | True (compared) |
| a5_kimi_tp8_e16_bf16_c4_p16k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_down | 4784 | 24.241 / 14.093 | -10.149 | 0.934 | True (compared) |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension / `ab58f99ac6e3` | HcPost / ffn.hc_post_group | 2115 | 47.315 / 26.810 | -20.505 | 0.923 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c16 / matrix-extension / `ab58f99ac6e3` | HcPre / ffn.hc_pre | 2250 | 41.007 / 61.158 | 20.151 | 0.907 | None (reference_only) |
| a5_kimi_tp8_e16_bf16_c2_p4k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_down | 5060 | 23.910 / 14.093 | -9.818 | 0.903 | True (compared) |
| a5_kimi_tp8_e16_bf16_c2_p16k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_down | 4968 | 23.893 / 14.093 | -9.800 | 0.902 | True (compared) |
| a5_kimi_tp8_e16_bf16_c1_p4k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_down | 5428 | 23.858 / 14.093 | -9.765 | 0.898 | True (compared) |
| a5_kimi_tp8_e16_bf16_c1_p16k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_down | 5428 | 23.857 / 14.093 | -9.765 | 0.898 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p16k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_up | 3772 | 22.659 / 14.303 | -8.357 | 0.769 | True (compared) |
| a5_kimi_tp8_e16_bf16_c32_p4k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_up | 4232 | 22.651 / 14.303 | -8.348 | 0.768 | True (compared) |
| a3_glm53flash_tp16_aclgraph_c32 / matrix-extension / `ab58f99ac6e3` | HcPost / attention.hc_post_group | 2205 | 30.239 / 13.405 | -16.834 | 0.758 | False (compared) |
| a3_glm53flash_tp16_aclgraph_c8 / matrix-extension / `ab58f99ac6e3` | HcPre / attention.hc_pre | 2115 | 37.137 / 53.826 | 16.689 | 0.751 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c8 / matrix-extension / `ab58f99ac6e3` | HcPre / ffn.hc_pre | 2115 | 37.220 / 53.826 | 16.606 | 0.747 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c32 / matrix-extension / `ab58f99ac6e3` | MatMulV2 / index_k | 1078 | 8.236 / 40.495 | 32.258 | 0.710 | False (compared) |
| a5_kimi_tp8_e16_bf16_c16_p4k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_up | 4508 | 21.792 / 14.180 | -7.613 | 0.700 | True (compared) |
| a5_kimi_tp8_e16_bf16_c16_p16k / kimi-variants / `ddbc84222bf7` | MatMulV3 / latent_up | 4324 | 21.790 / 14.180 | -7.610 | 0.700 | True (compared) |
| a3_glm53flash_tp16_aclgraph_c32 / matrix-extension / `ab58f99ac6e3` | HcPost / ffn.hc_post_group | 2205 | 28.713 / 13.405 | -15.308 | 0.689 | False (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | HcPre / attention.hc_pre | 2385 | 11.753 / 26.539 | 14.787 | 0.665 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c16 / matrix-extension / `ab58f99ac6e3` | QuantBatchMatmulV3 / shared.down | 2100 | 20.759 / 5.000 | -15.759 | 0.662 | False (compared) |
| glm53flash-a5-tp8-c3 / new17 / `df7c8117e01b` | HcPre / ffn.hc_pre | 2385 | 11.905 / 26.539 | 14.634 | 0.659 | None (reference_only) |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension / `ab58f99ac6e3` | MatMulV2 / index_k | 1034 | 10.620 / 40.495 | 29.875 | 0.657 | False (compared) |

## Highest unscored activity — coverage gaps, not zero predictions

| Case | Operator / role | Unscored calls | Unscored observed activity ms / Forward | Status |
|---|---|---:|---:|---|
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension | KvQuantSparseFlashAttentionVllm / unresolved | 517 | 17.956 | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 10.307 | reference_only |
| a3_glm53flash_tp16_aclgraph_c32 / matrix-extension | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2058 | 10.206 | reference_only |
| a3_glm53flash_tp16_aclgraph_c16 / matrix-extension | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 2100 | 10.156 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / v41-dp8 | GroupedMatmul / expert_up | 3000 | 9.704 | reference_only |
| a3_glm53flash_tp16_aclgraph_c8 / matrix-extension | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1974 | 9.493 | reference_only |
| a3_glm53flash_tp16_aclgraph_c32 / matrix-extension | KvQuantSparseFlashAttentionVllm / unresolved | 539 | 9.128 | unresolved |
| a5_glm53flash_tp8_c64_p4k / glm-flash-ws9 | GroupedMatmulSwigluQuantV2 / unresolved | 1302 | 8.866 | unresolved |
| a5_glm53flash_tp8_c32_p4k / glm-flash-ws9 | GroupedMatmulSwigluQuantV2 / unresolved | 1302 | 8.730 | unresolved |
| a5_glm53flash_tp8_c32_p8k / glm-flash-ws9 | GroupedMatmulSwigluQuantV2 / unresolved | 1470 | 8.730 | unresolved |
| a5_glm53flash_tp8_c16_p4k / glm-flash-ws9 | GroupedMatmulSwigluQuantV2 / unresolved | 1260 | 8.662 | unresolved |
| a5_glm53flash_tp8_c16_p8k / glm-flash-ws9 | GroupedMatmulSwigluQuantV2 / unresolved | 1344 | 8.656 | unresolved |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension | RecurrentKda / unresolved | 1598 | 8.348 | unresolved |
| a5_glm53flash_tp8_c8_p4k / glm-flash-ws9 | GroupedMatmulSwigluQuantV2 / unresolved | 1260 | 7.753 | unresolved |
| a5_kimi_tp8_e16_bf16_c4_p4k / kimi-variants | MatMulV3 / unresolved | 28143 | 7.451 | unresolved |
| a5_kimi_tp8_e16_bf16_c4_p16k / kimi-variants | MatMulV3 / unresolved | 27612 | 7.448 | unresolved |
| a5_kimi_tp8_e16_bf16_c2_p16k / kimi-variants | MatMulV3 / unresolved | 28674 | 7.325 | unresolved |
| a5_kimi_tp8_e16_bf16_c2_p4k / kimi-variants | MatMulV3 / unresolved | 29205 | 7.323 | unresolved |
| a5_kimi_tp8_e16_bf16_c1_p4k / kimi-variants | MatMulV3 / unresolved | 31329 | 7.269 | unresolved |
| a5_kimi_tp8_e16_bf16_c1_p16k / kimi-variants | MatMulV3 / unresolved | 31329 | 7.268 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | GroupedMatmul / unresolved | 21735 | 6.993 | unresolved |
| a5_kimi_k3_p32768_c1 / kimi-checkpoint-conditional-canonical | GroupedMatmulSituQuant / grouped_gate_up_situ_quant | 5796 | 6.831 | reference_only |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension | hcom_allReduce_ / attention_output_communication | 2115 | 6.713 | reference_only |
| a5_kimi_tp8_e16_bf16_c32_p16k / kimi-variants | FusedInferAttentionScore / unresolved | 984 | 6.338 | reference_only |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension | hcom_allReduce_ / ffn_down_communication | 2115 | 6.083 | unresolved |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1554 | 5.981 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / matrix-extension | GroupedMatmul / expert_up | 4200 | 5.096 | reference_only |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension | GroupedMatmul / expert_down | 1974 | 5.080 | reference_only |
| a3_glm53flash_tp16_aclgraph_c32 / matrix-extension | GroupedMatmul / expert_down | 2058 | 5.045 | reference_only |
| a3_glm53flash_tp16_aclgraph_c16 / matrix-extension | GroupedMatmul / expert_down | 2100 | 5.020 | reference_only |
| a3_glm53flash_tp16_aclgraph_c32 / matrix-extension | RecurrentKda / unresolved | 1666 | 4.888 | unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / v41-dp8 | GroupedMatmul / expert_down | 3000 | 4.794 | reference_only |
| a3_glm53flash_tp16_aclgraph_c8 / matrix-extension | GroupedMatmul / expert_down | 1974 | 4.779 | reference_only |
| a3_glm53flash_tp16_aclgraph_c16 / matrix-extension | KvQuantSparseFlashAttentionVllm / unresolved | 550 | 4.663 | unresolved |
| a5_kimi_tp8_e16_bf16_c32_p4k / kimi-variants | GroupedMatmul / expert_up | 4232 | 4.254 | reference_only |
| a5_kimi_tp8_e16_bf16_c32_p16k / kimi-variants | GroupedMatmul / expert_up | 3772 | 4.252 | reference_only |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / new17 | KvQuantSparseFlashAttentionVllm / unresolved | 407 | 4.153 | unresolved |
| glm53flash-a5-tp8-c3 / new17 | GroupedMatmulSwigluQuantV2 / unresolved | 2226 | 4.147 | unresolved |
| a5_glm53flash_tp8_c4_p8k / glm-flash-ws9 | GroupedMatmulSwigluQuantV2 / unresolved | 462 | 4.135 | unresolved |
| a5_kimi_tp8_e16_bf16_c16_p16k / kimi-variants | GroupedMatmul / expert_up | 4324 | 4.052 | reference_only |

## Source-role references — already costed work is not an extra budget

Reference differences have distinct evidence and are excluded from strict cohort accuracy counts.

| Case | Operator / region | Real / reference us | Real / Sim service ms per Forward | Residual ms | Boundary |
|---|---|---:|---:|---:|---|
| a5_kimi_tp8_e16_bf16_c2_p16k / kimi-variants / `ddbc84222bf7` | MoeDistributeCombineV3 / expert_combine_native / kda / ffn | 34.585 / 3.240 | 3.182 / 0.298 | -2.884 | transport_unpack_weighted_combine_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / kimi-variants / `ddbc84222bf7` | MoeDistributeCombineV3 / expert_combine_native / kda / ffn | 34.497 / 3.240 | 3.174 / 0.298 | -2.876 | transport_unpack_weighted_combine_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / kimi-variants / `ddbc84222bf7` | MoeDistributeDispatchV3 / expert_dispatch_native / kda / ffn | 34.207 / 3.624 | 3.147 / 0.333 | -2.814 | pack_transport_output_quant_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / kimi-variants / `ddbc84222bf7` | MoeDistributeDispatchV3 / expert_dispatch_native / kda / ffn | 34.197 / 3.624 | 3.146 / 0.333 | -2.813 | pack_transport_output_quant_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / v41-dp8 / `ab58f99ac6e3` | GroupedMatmul / expert_up / mla / ffn | 242.599 / 172.655 | 9.704 / 6.906 | -2.798 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c16_p4k / kimi-variants / `ddbc84222bf7` | MoeDistributeDispatchV3 / expert_dispatch_native / kda / ffn | 33.414 / 3.368 | 3.074 / 0.310 | -2.764 | pack_transport_output_quant_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / kimi-variants / `ddbc84222bf7` | MoeDistributeDispatchV3 / expert_dispatch_native / kda / ffn | 33.413 / 3.368 | 3.074 / 0.310 | -2.764 | pack_transport_output_quant_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / kimi-variants / `ddbc84222bf7` | MoeDistributeDispatchV3 / expert_dispatch_native / kda / ffn | 32.982 / 3.240 | 3.034 / 0.298 | -2.736 | pack_transport_output_quant_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / kimi-variants / `ddbc84222bf7` | MoeDistributeDispatchV3 / expert_dispatch_native / kda / ffn | 32.913 / 3.240 | 3.028 / 0.298 | -2.730 | pack_transport_output_quant_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / kimi-variants / `ddbc84222bf7` | MoeDistributeDispatchV3 / expert_dispatch_native / kda / ffn | 31.864 / 3.240 | 2.931 / 0.298 | -2.633 | pack_transport_output_quant_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / kimi-variants / `ddbc84222bf7` | MoeDistributeDispatchV3 / expert_dispatch_native / kda / ffn | 31.842 / 3.240 | 2.929 / 0.298 | -2.631 | pack_transport_output_quant_reference |
| a5_kimi_tp8_e16_bf16_c2_p16k / kimi-variants / `ddbc84222bf7` | MoeDistributeDispatchV3 / expert_dispatch_native / kda / ffn | 31.565 / 3.240 | 2.904 / 0.298 | -2.606 | pack_transport_output_quant_reference |
| a5_kimi_tp8_e16_bf16_c2_p4k / kimi-variants / `ddbc84222bf7` | MoeDistributeDispatchV3 / expert_dispatch_native / kda / ffn | 31.532 / 3.240 | 2.901 / 0.298 | -2.603 | pack_transport_output_quant_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / kimi-variants / `ddbc84222bf7` | MoeDistributeDispatchV3 / expert_dispatch_native / kda / ffn | 31.335 / 3.240 | 2.883 / 0.298 | -2.585 | pack_transport_output_quant_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / kimi-variants / `ddbc84222bf7` | MoeDistributeDispatchV3 / expert_dispatch_native / kda / ffn | 31.319 / 3.240 | 2.881 / 0.298 | -2.583 | pack_transport_output_quant_reference |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / linear_reduce / gdn / attention | 79.592 / 30.862 | 3.820 / 1.481 | -2.339 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gdn / ffn | 76.826 / 30.862 | 3.688 / 1.481 | -2.206 | reference_only |
| a5_kimi_tp8_e16_bf16_c32_p4k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 46.237 / 23.889 | 4.254 / 2.198 | -2.056 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c32_p16k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 46.220 / 23.889 | 4.252 / 2.198 | -2.054 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c16_p16k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 44.038 / 22.487 | 4.052 / 2.069 | -1.983 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c16_p4k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 43.967 / 22.487 | 4.045 / 2.069 | -1.976 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c8_p16k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 42.682 / 22.059 | 3.927 / 2.029 | -1.897 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c8_p4k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 42.630 / 22.059 | 3.922 / 2.029 | -1.893 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c4_p16k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 41.471 / 22.059 | 3.815 / 2.029 | -1.786 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c4_p4k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 41.239 / 22.059 | 3.794 / 2.029 | -1.765 | capacity_vs_valid_rows_conditional |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / linear_reduce / gdn / attention | 61.908 / 25.931 | 2.972 / 1.245 | -1.727 | reference_only |
| a3_glm53flash_tp16_aclgraph_c64 / matrix-extension / `ab58f99ac6e3` | GroupedMatmul / expert_down / mla / ffn | 120.959 / 160.177 | 5.080 / 6.727 | 1.647 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / matrix-extension / `ab58f99ac6e3` | GroupedMatmul / expert_up / mla / ffn | 127.406 / 86.330 | 5.096 / 3.453 | -1.643 | capacity_vs_valid_rows_conditional |
| a3_glm53flash_tp16_aclgraph_c8 / matrix-extension / `ab58f99ac6e3` | GroupedMatmul / expert_down / mla / ffn | 113.793 / 152.643 | 4.779 / 6.411 | 1.632 | capacity_vs_valid_rows_conditional |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / linear_reduce / gdn / attention | 81.530 / 48.606 | 3.913 / 2.333 | -1.580 | reference_only |
| a3_glm53flash_tp16_aclgraph_c32 / matrix-extension / `ab58f99ac6e3` | GroupedMatmul / expert_down / mla / ffn | 120.125 / 155.873 | 5.045 / 6.547 | 1.501 | capacity_vs_valid_rows_conditional |
| a3_glm53flash_tp16_aclgraph_c16 / matrix-extension / `ab58f99ac6e3` | GroupedMatmul / expert_down / mla / ffn | 119.516 / 153.715 | 5.020 / 6.456 | 1.436 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / matrix-extension / `ab58f99ac6e3` | MoeDistributeDispatchV3 / expert_dispatch_native / mla / ffn | 47.766 / 15.361 | 1.911 / 0.614 | -1.296 | pack_transport_output_quant_reference |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / linear_reduce / gdn / attention | 58.791 / 32.514 | 2.822 / 1.561 | -1.261 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / v41-dp8 / `ab58f99ac6e3` | GroupedMatmul / expert_down / mla / ffn | 119.854 / 88.639 | 4.794 / 3.546 | -1.249 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / v41-dp8 / `ab58f99ac6e3` | MoeDistributeDispatchV3 / expert_dispatch_native / mla / ffn | 45.332 / 15.361 | 1.813 / 0.614 | -1.199 | pack_transport_output_quant_reference |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / linear_reduce / gdn / attention | 38.341 / 15.816 | 1.840 / 0.759 | -1.081 | reference_only |
| a5_kimi_tp8_e16_bf16_c16_p4k / kimi-variants / `ddbc84222bf7` | MoeDistributeCombineV3 / expert_combine_native / kda / ffn | 14.726 / 3.368 | 1.355 / 0.310 | -1.045 | transport_unpack_weighted_combine_reference |
| a5_kimi_tp8_e16_bf16_c16_p16k / kimi-variants / `ddbc84222bf7` | MoeDistributeCombineV3 / expert_combine_native / kda / ffn | 14.691 / 3.368 | 1.352 / 0.310 | -1.042 | transport_unpack_weighted_combine_reference |
| a5_kimi_tp8_e16_bf16_c1_p16k / kimi-variants / `ddbc84222bf7` | MoeDistributeCombineV3 / expert_combine_native / kda / ffn | 14.550 / 3.240 | 1.339 / 0.298 | -1.041 | transport_unpack_weighted_combine_reference |
| a5_kimi_tp8_e16_bf16_c1_p4k / kimi-variants / `ddbc84222bf7` | MoeDistributeCombineV3 / expert_combine_native / kda / ffn | 14.544 / 3.240 | 1.338 / 0.298 | -1.040 | transport_unpack_weighted_combine_reference |
| a5_kimi_tp8_e16_bf16_c8_p4k / kimi-variants / `ddbc84222bf7` | MoeDistributeCombineV3 / expert_combine_native / kda / ffn | 14.508 / 3.240 | 1.335 / 0.298 | -1.037 | transport_unpack_weighted_combine_reference |
| a5_kimi_tp8_e16_bf16_c8_p16k / kimi-variants / `ddbc84222bf7` | MoeDistributeCombineV3 / expert_combine_native / kda / ffn | 14.491 / 3.240 | 1.333 / 0.298 | -1.035 | transport_unpack_weighted_combine_reference |
| a5_kimi_tp8_e16_bf16_c4_p4k / kimi-variants / `ddbc84222bf7` | MoeDistributeCombineV3 / expert_combine_native / kda / ffn | 14.448 / 3.240 | 1.329 / 0.298 | -1.031 | transport_unpack_weighted_combine_reference |
| a5_kimi_tp8_e16_bf16_c4_p16k / kimi-variants / `ddbc84222bf7` | MoeDistributeCombineV3 / expert_combine_native / kda / ffn | 14.338 / 3.240 | 1.319 / 0.298 | -1.021 | transport_unpack_weighted_combine_reference |
| a5_kimi_tp8_e16_bf16_c32_p16k / kimi-variants / `ddbc84222bf7` | MoeDistributeCombineV3 / expert_combine_native / kda / ffn | 14.615 / 3.624 | 1.345 / 0.333 | -1.011 | transport_unpack_weighted_combine_reference |
| a5_kimi_tp8_e16_bf16_c32_p4k / kimi-variants / `ddbc84222bf7` | MoeDistributeCombineV3 / expert_combine_native / kda / ffn | 14.584 / 3.624 | 1.342 / 0.333 | -1.008 | transport_unpack_weighted_combine_reference |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / matrix-extension / `ab58f99ac6e3` | GroupedMatmul / expert_up / mla / ffn | 68.076 / 44.765 | 2.723 / 1.791 | -0.932 | capacity_vs_valid_rows_conditional |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gdn / ffn | 34.882 / 15.816 | 1.674 / 0.759 | -0.915 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / matrix-extension / `ab58f99ac6e3` | GroupedMatmul / expert_down / mla / ffn | 65.238 / 44.321 | 2.610 / 1.773 | -0.837 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c32_p4k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 22.016 / 12.931 | 2.025 / 1.190 | -0.836 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c32_p16k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 22.006 / 12.931 | 2.025 / 1.190 | -0.835 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c16_p4k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 21.325 / 12.501 | 1.962 / 1.150 | -0.812 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c16_p16k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 21.305 / 12.501 | 1.960 / 1.150 | -0.810 | capacity_vs_valid_rows_conditional |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp_attn / gqa / attention | 79.629 / 30.862 | 1.274 / 0.494 | -0.780 | reference_only |
| a5_kimi_tp8_e16_bf16_c8_p4k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 20.594 / 12.286 | 1.895 / 1.130 | -0.764 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c8_p16k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 20.570 / 12.286 | 1.892 / 1.130 | -0.762 | capacity_vs_valid_rows_conditional |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / tp / gdn / ffn | 64.239 / 48.606 | 3.083 / 2.333 | -0.750 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gqa / ffn | 76.434 / 30.862 | 1.223 / 0.494 | -0.729 | reference_only |
| a5_kimi_tp8_e16_bf16_c4_p16k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 20.097 / 12.286 | 1.849 / 1.130 | -0.719 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c4_p4k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 20.066 / 12.286 | 1.846 / 1.130 | -0.716 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / matrix-extension / `ab58f99ac6e3` | GroupedMatmul / expert_up / mla / ffn | 38.809 / 22.384 | 1.552 / 0.895 | -0.657 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / v41-dp8 / `ab58f99ac6e3` | GroupedMatmul / expert_up / mla / ffn | 38.592 / 22.384 | 1.544 / 0.895 | -0.648 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / v41-dp8 / `ab58f99ac6e3` | GroupedMatmul / expert_up / mla / ffn | 38.541 / 22.384 | 1.542 / 0.895 | -0.646 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / matrix-extension / `ab58f99ac6e3` | GroupedMatmul / expert_down / mla / ffn | 37.439 / 22.163 | 1.498 / 0.887 | -0.611 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / v41-dp8 / `ab58f99ac6e3` | MoeDistributeDispatchV3 / expert_dispatch_native / mla / ffn | 29.449 / 15.361 | 1.178 / 0.614 | -0.564 | pack_transport_output_quant_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / v41-dp8 / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 29.224 / 1.578 | 0.584 / 0.032 | -0.553 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / matrix-extension / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 29.623 / 3.156 | 0.592 / 0.063 | -0.529 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / matrix-extension / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 31.372 / 6.312 | 0.627 / 0.126 | -0.501 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / v41-dp8 / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 29.070 / 1.578 | 0.523 / 0.028 | -0.495 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / matrix-extension / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 29.915 / 3.156 | 0.538 / 0.057 | -0.482 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / v41-dp8 / `ab58f99ac6e3` | GroupedMatmul / expert_down / mla / ffn | 23.656 / 11.821 | 0.946 / 0.473 | -0.473 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / v41-dp8 / `ab58f99ac6e3` | GroupedMatmul / expert_down / mla / ffn | 23.639 / 11.821 | 0.946 / 0.473 | -0.473 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / matrix-extension / `ab58f99ac6e3` | GroupedMatmul / expert_down / mla / ffn | 23.604 / 11.821 | 0.944 / 0.473 | -0.471 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / matrix-extension / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 30.876 / 6.312 | 0.556 / 0.114 | -0.442 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / v41-dp8 / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 33.567 / 12.624 | 0.671 / 0.252 | -0.419 | source_symbol_to_declared_attention_program |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 28.389 / 3.542 | 0.454 / 0.057 | -0.398 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / tp_attn / gqa / attention | 73.299 / 48.606 | 1.173 / 0.778 | -0.395 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / v41-dp8 / `ab58f99ac6e3` | HcPre / ffn.hc_pre / mla / ffn | 11.660 / 21.490 | 0.466 / 0.860 | 0.393 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / v41-dp8 / `ab58f99ac6e3` | HcPre / attention.hc_pre / mla / attention | 11.719 / 21.490 | 0.469 / 0.860 | 0.391 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / v41-dp8 / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 33.893 / 12.624 | 0.610 / 0.227 | -0.383 | source_symbol_to_declared_attention_program |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 26.844 / 3.148 | 0.429 / 0.050 | -0.379 | reference_only |
| a5_kimi_tp8_e16_bf16_c2_p16k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 16.222 / 12.286 | 1.492 / 1.130 | -0.362 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c2_p4k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 16.222 / 12.286 | 1.492 / 1.130 | -0.362 | capacity_vs_valid_rows_conditional |
| a3_kimi4_tp8_w4a8_c1 / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 55.722 / 175.598 | 0.167 / 0.527 | 0.360 | capacity_vs_valid_rows_conditional |
| a3_kimi4_tp8_w4a8_c64 / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 1095.630 / 1214.924 | 3.287 / 3.645 | 0.358 | capacity_vs_valid_rows_conditional |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / linear_reduce / gdn / attention | 18.655 / 11.427 | 0.895 / 0.548 | -0.347 | reference_only |
| a5_kimi_tp8_e16_bf16_c1_p16k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 16.052 / 12.286 | 1.477 / 1.130 | -0.346 | capacity_vs_valid_rows_conditional |
| a5_kimi_tp8_e16_bf16_c1_p4k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 16.045 / 12.286 | 1.476 / 1.130 | -0.346 | capacity_vs_valid_rows_conditional |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp_attn / gqa / attention | 36.991 / 15.816 | 0.592 / 0.253 | -0.339 | reference_only |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 8.186 / 1.312 | 0.393 / 0.063 | -0.330 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / matrix-extension / `ab58f99ac6e3` | HcPre / ffn.hc_pre / mla / ffn | 11.183 / 18.995 | 0.447 / 0.760 | 0.312 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / matrix-extension / `ab58f99ac6e3` | HcPre / attention.hc_pre / mla / attention | 11.294 / 18.995 | 0.452 / 0.760 | 0.308 | partial_base_program_reference_premix_branch_unresolved |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gqa / ffn | 34.787 / 15.816 | 0.557 / 0.253 | -0.304 | reference_only |
| a3_kimi4_tp8_w4a8_c64 / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 520.577 / 613.046 | 1.562 / 1.839 | 0.277 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / v41-dp8 / `ab58f99ac6e3` | HcPre / attention.hc_pre / mla / attention | 10.537 / 17.123 | 0.421 / 0.685 | 0.263 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / v41-dp8 / `ab58f99ac6e3` | HcPre / attention.hc_pre / mla / attention | 10.538 / 17.123 | 0.422 / 0.685 | 0.263 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / matrix-extension / `ab58f99ac6e3` | HcPre / attention.hc_pre / mla / attention | 10.593 / 17.123 | 0.424 / 0.685 | 0.261 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / v41-dp8 / `ab58f99ac6e3` | HcPre / ffn.hc_pre / mla / ffn | 10.636 / 17.123 | 0.425 / 0.685 | 0.259 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / v41-dp8 / `ab58f99ac6e3` | HcPre / ffn.hc_pre / mla / ffn | 10.636 / 17.123 | 0.425 / 0.685 | 0.259 | partial_base_program_reference_premix_branch_unresolved |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / matrix-extension / `ab58f99ac6e3` | HcPre / ffn.hc_pre / mla / ffn | 10.687 / 17.123 | 0.427 / 0.685 | 0.257 | partial_base_program_reference_premix_branch_unresolved |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 6.519 / 1.312 | 0.313 / 0.063 | -0.250 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gdn / ffn | 16.614 / 11.427 | 0.797 / 0.548 | -0.249 | reference_only |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | hcom_allReduce_ / tp / gqa / ffn | 63.948 / 48.606 | 1.023 / 0.778 | -0.245 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / matrix-extension / `ab58f99ac6e3` | HcPre / attention.hc_pre / mla / attention | 11.736 / 17.747 | 0.469 / 0.710 | 0.240 | partial_base_program_reference_premix_branch_unresolved |
| a5_qwen38_highconc_c128 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 3.779 / 1.312 | 0.363 / 0.126 | -0.237 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / matrix-extension / `ab58f99ac6e3` | HcPre / ffn.hc_pre / mla / ffn | 11.978 / 17.747 | 0.479 / 0.710 | 0.231 | partial_base_program_reference_premix_branch_unresolved |
| a3_kimi4_tp8_w4a8_c4 / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 103.723 / 175.598 | 0.311 / 0.527 | 0.216 | capacity_vs_valid_rows_conditional |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / tp / gdn / ffn | 21.976 / 25.931 | 1.055 / 1.245 | 0.190 | reference_only |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 5.123 / 1.312 | 0.246 / 0.063 | -0.183 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 13.451 / 2.788 | 0.215 / 0.045 | -0.171 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / v41-dp8 / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 10.067 / 1.578 | 0.201 / 0.032 | -0.170 | source_symbol_to_declared_attention_program |
| a5_qwen36_highconc_c128 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 3.075 / 1.312 | 0.295 / 0.126 | -0.169 | reference_only |
| a3_kimi4_tp8_w4a8_c32 / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 631.825 / 688.064 | 1.895 / 2.064 | 0.169 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / matrix-extension / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 9.938 / 1.578 | 0.199 / 0.032 | -0.167 | source_symbol_to_declared_attention_program |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 4.702 / 1.312 | 0.226 / 0.063 | -0.163 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / v41-dp8 / `ab58f99ac6e3` | MoeDistributeCombineV3 / expert_combine_native / mla / ffn | 19.057 / 15.009 | 0.762 / 0.600 | -0.162 | transport_unpack_weighted_combine_reference |
| a3_kimi4_tp8_w4a8_c1 / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 38.730 / 89.061 | 0.116 / 0.267 | 0.151 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / v41-dp8 / `ab58f99ac6e3` | MoeDistributeDispatchV3 / expert_dispatch_native / mla / ffn | 19.944 / 16.321 | 0.798 / 0.653 | -0.145 | pack_transport_output_quant_reference |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 2.769 / 1.312 | 0.266 / 0.126 | -0.140 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / v41-dp8 / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 9.205 / 1.578 | 0.166 / 0.028 | -0.137 | source_symbol_to_declared_attention_program |
| a5_qwen38_highconc_c32 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 11.381 / 2.853 | 0.182 / 0.046 | -0.136 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / matrix-extension / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 9.116 / 1.578 | 0.164 / 0.028 | -0.136 | source_symbol_to_declared_attention_program |
| a3_kimi4_tp8_w4a8_c32 / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 303.243 / 345.826 | 0.910 / 1.037 | 0.128 | capacity_vs_valid_rows_conditional |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 3.803 / 1.312 | 0.183 / 0.063 | -0.120 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / v41-dp8 / `ab58f99ac6e3` | MoeDistributeCombineV3 / expert_combine_native / mla / ffn | 11.198 / 14.049 | 0.448 / 0.562 | 0.114 | transport_unpack_weighted_combine_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / v41-dp8 / `ab58f99ac6e3` | MoeDistributeCombineV3 / expert_combine_native / mla / ffn | 11.209 / 14.049 | 0.448 / 0.562 | 0.114 | transport_unpack_weighted_combine_reference |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / matrix-extension / `ab58f99ac6e3` | MoeDistributeCombineV3 / expert_combine_native / mla / ffn | 11.254 / 14.049 | 0.450 / 0.562 | 0.112 | transport_unpack_weighted_combine_reference |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / matrix-extension / `ab58f99ac6e3` | MoeDistributeDispatchV3 / expert_dispatch_native / mla / ffn | 18.548 / 15.773 | 0.742 / 0.631 | -0.111 | pack_transport_output_quant_reference |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 2.429 / 1.312 | 0.233 / 0.126 | -0.107 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | _layer_norm_fwd_1pass_kernel_npu /  / gdn / attention | 3.375 / 1.312 | 0.162 / 0.063 | -0.099 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / matrix-extension / `ab58f99ac6e3` | MoeDistributeDispatchV3 / expert_dispatch_native / mla / ffn | 17.898 / 15.498 | 0.716 / 0.620 | -0.096 | pack_transport_output_quant_reference |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / matrix-extension / `ab58f99ac6e3` | MoeDistributeCombineV3 / expert_combine_native / mla / ffn | 11.810 / 14.186 | 0.472 / 0.567 | 0.095 | transport_unpack_weighted_combine_reference |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp_attn / gqa / attention | 16.753 / 11.427 | 0.268 / 0.183 | -0.085 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_AicpuKernel / tp / gqa / ffn | 16.735 / 11.427 | 0.268 / 0.183 | -0.085 | reference_only |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / matrix-extension / `ab58f99ac6e3` | MoeDistributeCombineV3 / expert_combine_native / mla / ffn | 12.381 / 14.461 | 0.495 / 0.578 | 0.083 | transport_unpack_weighted_combine_reference |
| a3_kimi4_tp8_w4a8_c4 / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 62.615 / 89.061 | 0.188 / 0.267 | 0.079 | capacity_vs_valid_rows_conditional |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / tp / gdn / ffn | 30.927 / 32.514 | 1.484 / 1.561 | 0.076 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 2.102 / 1.312 | 0.202 / 0.126 | -0.076 | reference_only |
| a3_kimi4_tp8_w4a8_c16 / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 324.459 / 346.695 | 0.973 / 1.040 | 0.067 | capacity_vs_valid_rows_conditional |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / tp / gqa / ffn | 21.989 / 25.931 | 0.352 / 0.415 | 0.063 | reference_only |
| a5_qwen38_highconc_c4 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 6.254 / 2.653 | 0.100 / 0.042 | -0.058 | reference_only |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / tp_attn / gqa / attention | 35.826 / 32.514 | 0.573 / 0.520 | -0.053 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | l2norm_fwd_kernel2 /  / gdn / attention | 1.817 / 1.312 | 0.174 / 0.126 | -0.049 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | split_qkv_rmsnorm_mrope_kernel /  / gqa / attention | 5.634 / 2.640 | 0.090 / 0.042 | -0.048 | reference_only |
| a5_kimi_tp8_e16_bf16_c2_p4k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 22.426 / 22.059 | 2.063 / 2.029 | -0.034 | capacity_vs_valid_rows_conditional |
| a5_qwen36_highconc_c40 / `886c1fa5bd45` | hcom_allReduce_ / tp / gqa / ffn | 30.577 / 32.514 | 0.489 / 0.520 | 0.031 | reference_only |
| a5_qwen36_highconc_c4 / `886c1fa5bd45` | hcom_allReduce_ / tp_attn / gqa / attention | 24.240 / 25.931 | 0.388 / 0.415 | 0.027 | reference_only |
| a5_kimi_tp8_e16_bf16_c2_p16k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 22.335 / 22.059 | 2.055 / 2.029 | -0.025 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / v41-dp8 / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 11.092 / 1.578 | 0.022 / 0.003 | -0.019 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / matrix-extension / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 11.257 / 3.156 | 0.023 / 0.006 | -0.016 | source_symbol_to_declared_attention_program |
| a3_kimi4_tp8_w4a8_c16 / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_down / kda / ffn | 168.962 / 174.251 | 0.507 / 0.523 | 0.016 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / matrix-extension / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 13.400 / 6.312 | 0.027 / 0.013 | -0.014 | source_symbol_to_declared_attention_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / v41-dp8 / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 8.170 / 1.578 | 0.016 / 0.003 | -0.013 | source_symbol_to_declared_attention_program |
| a5_kimi_tp8_e16_bf16_c1_p4k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 21.918 / 22.059 | 2.016 / 2.029 | 0.013 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / matrix-extension / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 7.891 / 1.578 | 0.016 / 0.003 | -0.013 | source_symbol_to_declared_attention_program |
| a5_kimi_tp8_e16_bf16_c1_p16k / kimi-variants / `ddbc84222bf7` | GroupedMatmul / expert_up / kda / ffn | 21.957 / 22.059 | 2.020 / 2.029 | 0.009 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / v41-dp8 / `ab58f99ac6e3` | MqsmlaKernel___call__ / attention_core / mla / attention | 16.005 / 12.624 | 0.032 / 0.025 | -0.007 | source_symbol_to_declared_attention_program |
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
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority-operators/body-operator-family-scoreboard.json), SHA256 `7126d4a275a5f005537517386747e366322a7bed7365763e21cb3a66319b13fc`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority-operators-5935c87b/body-operator-family-scoreboard.json), SHA256 `4f475bce99de8a8908c8fa745ea1ab9cabb8c570ef3b3ec5ef7c9d5d7f29265e`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-v41-operators-09811dad/body-operator-family-scoreboard.json), SHA256 `53e528b2254c3ca55b4eb9e1afa5fc4e46f89ed6ccbee3059639dbbaed10175d`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-glm-operators-09811dad/body-operator-family-scoreboard.json), SHA256 `66c1e8335a7585608524322f2415ffc5648ae91d2259deadbc47fb8b99391f73`
- [body-operator-family-scoreboard.json](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-operators-332f0420/body-operator-family-scoreboard.json), SHA256 `e2d2bfaffcb017ffa47bc5ac3af1c0e5612951ac21d5dd6324797d9ef31efa6d`
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
