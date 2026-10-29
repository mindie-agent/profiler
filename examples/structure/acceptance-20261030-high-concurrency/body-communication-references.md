# Complete Body Communication by Layer Kind and Physical Program

The buckets use complete model topology alignment. GDN and GQA collective programs stay separate. These are conditional references; native elapsed includes peer wait and cannot calibrate link bandwidth. They do not change the prior 12-arm operator scoreboard or enter its scored denominator.

| Case | Layer kind / block / declared role | Calls | Real mean us | Real P50 us | Sim reference us | Diff us | Reference tolerance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| a5_qwen36_highconc_c128 | gdn / attention / linear_reduce | 1824 | 81.530 | 66.266 | 48.606 | -32.925 | outside (unscored) |
| a5_qwen36_highconc_c128 | gqa / attention / tp_attn | 608 | 73.299 | 72.073 | 48.606 | -24.693 | outside (unscored) |
| a5_qwen36_highconc_c128 | gdn / ffn / tp | 1824 | 64.239 | 64.206 | 48.606 | -15.634 | outside (unscored) |
| a5_qwen36_highconc_c128 | gqa / ffn / tp | 608 | 63.948 | 63.946 | 48.606 | -15.342 | outside (unscored) |
| a5_qwen36_highconc_c4 | gdn / attention / linear_reduce | 3504 | 61.908 | 23.244 | 25.931 | -35.977 | outside (unscored) |
| a5_qwen36_highconc_c4 | gqa / attention / tp_attn | 1168 | 24.240 | 23.529 | 25.931 | 1.691 | within (unscored) |
| a5_qwen36_highconc_c4 | gdn / ffn / tp | 3504 | 21.976 | 21.891 | 25.931 | 3.956 | within (unscored) |
| a5_qwen36_highconc_c4 | gqa / ffn / tp | 1168 | 21.989 | 21.956 | 25.931 | 3.943 | within (unscored) |
| a5_qwen36_highconc_c40 | gdn / attention / linear_reduce | 2592 | 58.791 | 32.182 | 32.514 | -26.277 | outside (unscored) |
| a5_qwen36_highconc_c40 | gqa / attention / tp_attn | 864 | 35.826 | 35.657 | 32.514 | -3.312 | within (unscored) |
| a5_qwen36_highconc_c40 | gdn / ffn / tp | 2592 | 30.927 | 30.693 | 32.514 | 1.588 | within (unscored) |
| a5_qwen36_highconc_c40 | gqa / ffn / tp | 864 | 30.577 | 30.497 | 32.514 | 1.937 | within (unscored) |
| a5_qwen38_highconc_c128 | gdn / attention / linear_reduce | 1392 | 79.592 | 79.195 | 30.862 | -48.730 | outside (unscored) |
| a5_qwen38_highconc_c128 | gqa / attention / tp_attn | 464 | 79.629 | 78.483 | 30.862 | -48.767 | outside (unscored) |
| a5_qwen38_highconc_c128 | gdn / ffn / tp | 1392 | 76.826 | 76.629 | 30.862 | -45.964 | outside (unscored) |
| a5_qwen38_highconc_c128 | gqa / ffn / tp | 464 | 76.434 | 76.275 | 30.862 | -45.572 | outside (unscored) |
| a5_qwen38_highconc_c32 | gdn / attention / linear_reduce | 2304 | 38.341 | 36.834 | 15.816 | -22.526 | outside (unscored) |
| a5_qwen38_highconc_c32 | gqa / attention / tp_attn | 768 | 36.991 | 36.346 | 15.816 | -21.176 | outside (unscored) |
| a5_qwen38_highconc_c32 | gdn / ffn / tp | 2304 | 34.882 | 34.719 | 15.816 | -19.066 | outside (unscored) |
| a5_qwen38_highconc_c32 | gqa / ffn / tp | 768 | 34.787 | 34.649 | 15.816 | -18.971 | outside (unscored) |
| a5_qwen38_highconc_c4 | gdn / attention / linear_reduce | 2160 | 18.655 | 18.451 | 11.427 | -7.228 | within (unscored) |
| a5_qwen38_highconc_c4 | gqa / attention / tp_attn | 720 | 16.753 | 16.481 | 11.427 | -5.326 | within (unscored) |
| a5_qwen38_highconc_c4 | gdn / ffn / tp | 2160 | 16.614 | 16.456 | 11.427 | -5.187 | within (unscored) |
| a5_qwen38_highconc_c4 | gqa / ffn / tp | 720 | 16.735 | 16.552 | 11.427 | -5.308 | within (unscored) |

## Existing model programs behind capture ABI gaps

Per-forward values are kernel-activity sums, not body wall time. These programs already exist in Sim; their reference costs must not be added again. Unfused-subgraph references do not claim an atomic fused-kernel latency.

| Case | Native family / layer kind / block | Calls | Real mean / P50 us | Reference us | Real activity ms/forward | Sim service ms/forward | Status / boundary |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| a5_qwen36_highconc_c128 | DynamicQuantV2 / gdn / attention | 1824 | 7.494 / 7.449 | — | 0.360 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c128 | l2norm_fwd_kernel2 / gdn / attention | 3648 | 3.075 / 2.886 | 1.312 | 0.295 | 0.126 | reference_only / semantic_device_program |
| a5_qwen36_highconc_c128 | _layer_norm_fwd_1pass_kernel_npu / gdn / attention | 1824 | 6.519 / 6.452 | 1.312 | 0.313 | 0.063 | reference_only / semantic_device_program |
| a5_qwen36_highconc_c128 | AddRmsNormDynamicQuant / gdn / ffn | 1824 | 15.340 / 15.292 | — | 0.736 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c128 | DynamicQuantV2 / gdn / ffn | 1824 | 6.140 / 6.110 | — | 0.295 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c128 | AddRmsNorm / gdn / attention | 1786 | 8.789 / 8.765 | — | 0.413 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c128 | AddRmsNormDynamicQuant / gqa / attention | 608 | 12.148 / 12.114 | — | 0.194 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c128 | split_qkv_rmsnorm_mrope_kernel / gqa / attention | 608 | 26.844 / 26.806 | 3.148 | 0.429 | 0.050 | reference_only / unfused_subgraph_reference |
| a5_qwen36_highconc_c128 | DynamicQuantV2 / gqa / attention | 608 | 5.567 / 5.550 | — | 0.089 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c128 | AddRmsNormDynamicQuant / gqa / ffn | 608 | 12.621 / 12.596 | — | 0.202 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c128 | DynamicQuantV2 / gqa / ffn | 608 | 5.743 / 5.690 | — | 0.092 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c4 | DynamicQuantV2 / gdn / attention | 3504 | 4.049 / 4.054 | — | 0.194 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c4 | l2norm_fwd_kernel2 / gdn / attention | 7008 | 1.817 / 1.841 | 1.312 | 0.174 | 0.126 | reference_only / semantic_device_program |
| a5_qwen36_highconc_c4 | _layer_norm_fwd_1pass_kernel_npu / gdn / attention | 3504 | 3.375 / 3.333 | 1.312 | 0.162 | 0.063 | reference_only / semantic_device_program |
| a5_qwen36_highconc_c4 | AddRmsNormDynamicQuant / gdn / ffn | 3504 | 5.429 / 5.430 | — | 0.261 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c4 | DynamicQuantV2 / gdn / ffn | 3504 | 3.877 / 3.882 | — | 0.186 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c4 | AddRmsNorm / gdn / attention | 3431 | 4.089 / 4.093 | — | 0.192 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c4 | AddRmsNormDynamicQuant / gqa / attention | 1168 | 5.434 / 5.439 | — | 0.087 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c4 | split_qkv_rmsnorm_mrope_kernel / gqa / attention | 1168 | 5.634 / 5.654 | 2.640 | 0.090 | 0.042 | reference_only / unfused_subgraph_reference |
| a5_qwen36_highconc_c4 | DynamicQuantV2 / gqa / attention | 1168 | 3.762 / 3.776 | — | 0.060 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c4 | AddRmsNormDynamicQuant / gqa / ffn | 1168 | 5.422 / 5.454 | — | 0.087 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c4 | DynamicQuantV2 / gqa / ffn | 1168 | 3.911 / 3.914 | — | 0.063 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c40 | DynamicQuantV2 / gdn / attention | 2592 | 6.016 / 5.927 | — | 0.289 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c40 | l2norm_fwd_kernel2 / gdn / attention | 5184 | 2.429 / 2.287 | 1.312 | 0.233 | 0.126 | reference_only / semantic_device_program |
| a5_qwen36_highconc_c40 | _layer_norm_fwd_1pass_kernel_npu / gdn / attention | 2592 | 4.702 / 4.725 | 1.312 | 0.226 | 0.063 | reference_only / semantic_device_program |
| a5_qwen36_highconc_c40 | AddRmsNormDynamicQuant / gdn / ffn | 2592 | 9.468 / 9.434 | — | 0.454 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c40 | DynamicQuantV2 / gdn / ffn | 2592 | 5.528 / 5.531 | — | 0.265 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c40 | AddRmsNorm / gdn / attention | 2538 | 6.297 / 6.301 | — | 0.296 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c40 | AddRmsNormDynamicQuant / gqa / attention | 864 | 8.251 / 8.233 | — | 0.132 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c40 | split_qkv_rmsnorm_mrope_kernel / gqa / attention | 864 | 13.451 / 13.287 | 2.788 | 0.215 | 0.045 | reference_only / unfused_subgraph_reference |
| a5_qwen36_highconc_c40 | DynamicQuantV2 / gqa / attention | 864 | 4.893 / 4.841 | — | 0.078 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c40 | AddRmsNormDynamicQuant / gqa / ffn | 864 | 8.525 / 8.493 | — | 0.136 | — | boundary_unresolved /  |
| a5_qwen36_highconc_c40 | DynamicQuantV2 / gqa / ffn | 864 | 5.228 / 5.178 | — | 0.084 | — | boundary_unresolved /  |
| a5_qwen38_highconc_c128 | l2norm_fwd_kernel2 / gdn / attention | 2784 | 3.779 / 3.898 | 1.312 | 0.363 | 0.126 | reference_only / semantic_device_program |
| a5_qwen38_highconc_c128 | _layer_norm_fwd_1pass_kernel_npu / gdn / attention | 1392 | 8.186 / 8.182 | 1.312 | 0.393 | 0.063 | reference_only / semantic_device_program |
| a5_qwen38_highconc_c128 | AddRmsNormDynamicMxQuant / gdn / ffn | 1392 | 14.009 / 13.983 | — | 0.672 | — | boundary_unresolved /  |
| a5_qwen38_highconc_c128 | AddRmsNorm / gdn / attention | 1363 | 9.873 / 9.845 | — | 0.464 | — | boundary_unresolved /  |
| a5_qwen38_highconc_c128 | AddRmsNormDynamicMxQuant / gqa / attention | 464 | 12.301 / 12.283 | — | 0.197 | — | boundary_unresolved /  |
| a5_qwen38_highconc_c128 | split_qkv_rmsnorm_mrope_kernel / gqa / attention | 464 | 28.389 / 28.261 | 3.542 | 0.454 | 0.057 | reference_only / unfused_subgraph_reference |
| a5_qwen38_highconc_c128 | AddRmsNormDynamicMxQuant / gqa / ffn | 464 | 12.340 / 12.348 | — | 0.197 | — | boundary_unresolved /  |
| a5_qwen38_highconc_c32 | l2norm_fwd_kernel2 / gdn / attention | 4608 | 2.769 / 2.575 | 1.312 | 0.266 | 0.126 | reference_only / semantic_device_program |
| a5_qwen38_highconc_c32 | _layer_norm_fwd_1pass_kernel_npu / gdn / attention | 2304 | 5.123 / 5.125 | 1.312 | 0.246 | 0.063 | reference_only / semantic_device_program |
| a5_qwen38_highconc_c32 | AddRmsNormDynamicMxQuant / gdn / ffn | 2304 | 7.733 / 7.718 | — | 0.371 | — | boundary_unresolved /  |
| a5_qwen38_highconc_c32 | AddRmsNorm / gdn / attention | 2256 | 5.956 / 5.947 | — | 0.280 | — | boundary_unresolved /  |
| a5_qwen38_highconc_c32 | AddRmsNormDynamicMxQuant / gqa / attention | 768 | 7.146 / 7.104 | — | 0.114 | — | boundary_unresolved /  |
| a5_qwen38_highconc_c32 | split_qkv_rmsnorm_mrope_kernel / gqa / attention | 768 | 11.381 / 11.252 | 2.853 | 0.182 | 0.046 | reference_only / unfused_subgraph_reference |
| a5_qwen38_highconc_c32 | AddRmsNormDynamicMxQuant / gqa / ffn | 768 | 7.275 / 7.274 | — | 0.116 | — | boundary_unresolved /  |
| a5_qwen38_highconc_c4 | l2norm_fwd_kernel2 / gdn / attention | 4320 | 2.102 / 2.072 | 1.312 | 0.202 | 0.126 | reference_only / semantic_device_program |
| a5_qwen38_highconc_c4 | _layer_norm_fwd_1pass_kernel_npu / gdn / attention | 2160 | 3.803 / 3.768 | 1.312 | 0.183 | 0.063 | reference_only / semantic_device_program |
| a5_qwen38_highconc_c4 | AddRmsNormDynamicMxQuant / gdn / ffn | 2160 | 4.405 / 4.322 | — | 0.211 | — | boundary_unresolved /  |
| a5_qwen38_highconc_c4 | AddRmsNorm / gdn / attention | 2115 | 4.302 / 4.266 | — | 0.202 | — | boundary_unresolved /  |
| a5_qwen38_highconc_c4 | AddRmsNormDynamicMxQuant / gqa / attention | 720 | 4.180 / 4.136 | — | 0.067 | — | boundary_unresolved /  |
| a5_qwen38_highconc_c4 | split_qkv_rmsnorm_mrope_kernel / gqa / attention | 720 | 6.254 / 6.247 | 2.653 | 0.100 | 0.042 | reference_only / unfused_subgraph_reference |
| a5_qwen38_highconc_c4 | AddRmsNormDynamicMxQuant / gqa / ffn | 720 | 4.141 / 4.130 | — | 0.066 | — | boundary_unresolved /  |
