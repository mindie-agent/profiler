# Complete Decode Body Operator Families

Only complete events inside the 287 accepted target-body windows enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Two declaration arms reuse the same six captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_qwen36_highconc_c128 / source-gdn-native | 12 / 12 | 1 / 1 | 13 / 13 | 21888 / 71744 | 0 |
| a5_qwen36_highconc_c128 / source-gdn | 12 / 12 | 0 / 1 | 12 / 13 | 21888 / 71744 | 0 |
| a5_qwen36_highconc_c4 / source-gdn-native | 13 / 13 | 0 / 0 | 13 / 13 | 42048 / 130816 | 0 |
| a5_qwen36_highconc_c4 / source-gdn | 13 / 13 | 0 / 0 | 13 / 13 | 42048 / 130816 | 0 |
| a5_qwen36_highconc_c40 / source-gdn-native | 13 / 13 | 0 / 0 | 13 / 13 | 31104 / 96768 | 0 |
| a5_qwen36_highconc_c40 / source-gdn | 13 / 13 | 0 / 0 | 13 / 13 | 31104 / 96768 | 0 |
| a5_qwen38_highconc_c128 / source-gdn-native | 11 / 12 | 1 / 3 | 12 / 15 | 19024 / 53360 | 0 |
| a5_qwen38_highconc_c128 / source-gdn | 11 / 12 | 0 / 3 | 11 / 15 | 19024 / 53360 | 0 |
| a5_qwen38_highconc_c32 / source-gdn-native | 15 / 15 | 0 / 0 | 15 / 15 | 31488 / 83712 | 0 |
| a5_qwen38_highconc_c32 / source-gdn | 14 / 15 | 0 / 0 | 14 / 15 | 31488 / 83712 | 0 |
| a5_qwen38_highconc_c4 / source-gdn-native | 15 / 15 | 0 / 0 | 15 / 15 | 29520 / 78480 | 0 |
| a5_qwen38_highconc_c4 / source-gdn | 15 / 15 | 0 / 0 | 15 / 15 | 29520 / 78480 | 0 |

## a5_qwen36_highconc_c128 / source-gdn-native

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| hcom_allReduce_ / attention_output_communication | 2432 | 0 / 2432 | 79.472 | 66.415 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 1824 | 1824 / 0 | 92.435 | 92.270 | 83.997 | -8.438 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_ / ffn_down_communication | 2432 | 0 / 2432 | 64.167 | 64.146 | 48.606 | -15.561 | 15% (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| FusedInferAttentionScore / unresolved | 608 | 0 / 608 | 152.255 | 151.555 | 135.004 | -17.251 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / gate_up | 2432 | 2432 / 0 | 37.315 | 37.251 | 52.167 | 14.853 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| fused_gdn_gating_kernel / unresolved | 1824 | 0 / 1824 | 44.290 | 44.233 | 32.009 | -12.281 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / down | 2432 | 2432 / 0 | 21.954 | 21.838 | 23.804 | 1.850 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicQuant / unresolved | 3040 | 0 / 3040 | 14.158 | 14.842 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / linear_qkvz | 1824 | 1824 / 0 | 20.071 | 19.968 | 21.090 | 1.018 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuantV2 / unresolved | 4864 | 0 / 4864 | 6.527 | 6.272 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 1824 | 1824 / 0 | 16.486 | 16.473 | 15.771 | -0.715 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 1824 | 1824 / 0 | 14.792 | 14.807 | 3.490 | -11.302 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 4256 | 0 / 4256 | 4.197 | 4.256 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / swiglu | 2432 | 2432 / 0 | 7.339 | 7.298 | 1.671 | -5.668 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 608 | 0 / 608 | 26.844 | 26.806 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNorm / unresolved | 1786 | 0 / 1786 | 8.789 | 8.765 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 1824 | 1824 / 0 | 8.589 | 8.610 | 10.897 | 2.308 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 6080 | 0 / 6080 | 2.365 | 2.297 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 3648 | 0 / 3648 | 3.920 | 4.059 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / k_flat + q_flat | 3648 | 0 / 3648 | 3.850 | 3.814 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 608 | 608 / 0 | 20.046 | 19.924 | 21.090 | 1.043 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 1824 | 0 / 1824 | 6.519 | 6.452 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 3648 | 0 / 3648 | 3.075 | 2.886 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 1824 | 0 / 1824 | 5.198 | 5.184 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 3648 | 0 / 3648 | 2.309 | 2.314 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 1824 | 1824 / 0 | 4.532 | 4.527 | 1.312 | -3.220 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / output | 608 | 608 / 0 | 13.568 | 13.412 | 10.150 | -3.418 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 1824 | 0 / 1824 | 4.506 | 4.488 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / v_flat | 1824 | 1824 / 0 | 3.818 | 3.808 | 1.312 | -2.506 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / cache | 608 | 608 / 0 | 7.184 | 7.181 | 1.312 | -5.872 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 608 | 0 / 608 | 5.416 | 5.332 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 608 | 0 / 608 | 5.100 | 5.168 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 608 | 0 / 608 | 3.366 | 3.350 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 38 | 0 / 38 | 7.970 | 7.960 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_qwen36_highconc_c128 / source-gdn

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| hcom_allReduce_ / attention_output_communication | 2432 | 0 / 2432 | 79.472 | 66.415 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 1824 | 1824 / 0 | 92.435 | 92.270 | 115.837 | 23.401 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_ / ffn_down_communication | 2432 | 0 / 2432 | 64.167 | 64.146 | 48.606 | -15.561 | 15% (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| FusedInferAttentionScore / unresolved | 608 | 0 / 608 | 152.255 | 151.555 | 135.004 | -17.251 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / gate_up | 2432 | 2432 / 0 | 37.315 | 37.251 | 52.167 | 14.853 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| fused_gdn_gating_kernel / unresolved | 1824 | 0 / 1824 | 44.290 | 44.233 | 32.009 | -12.281 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / down | 2432 | 2432 / 0 | 21.954 | 21.838 | 23.804 | 1.850 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicQuant / unresolved | 3040 | 0 / 3040 | 14.158 | 14.842 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / linear_qkvz | 1824 | 1824 / 0 | 20.071 | 19.968 | 21.090 | 1.018 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuantV2 / unresolved | 4864 | 0 / 4864 | 6.527 | 6.272 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 1824 | 1824 / 0 | 16.486 | 16.473 | 15.771 | -0.715 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 1824 | 1824 / 0 | 14.792 | 14.807 | 3.490 | -11.302 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 4256 | 0 / 4256 | 4.197 | 4.256 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / swiglu | 2432 | 2432 / 0 | 7.339 | 7.298 | 1.671 | -5.668 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 608 | 0 / 608 | 26.844 | 26.806 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNorm / unresolved | 1786 | 0 / 1786 | 8.789 | 8.765 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 1824 | 1824 / 0 | 8.589 | 8.610 | 10.897 | 2.308 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 6080 | 0 / 6080 | 2.365 | 2.297 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 3648 | 0 / 3648 | 3.920 | 4.059 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / k_flat + q_flat | 3648 | 0 / 3648 | 3.850 | 3.814 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 608 | 608 / 0 | 20.046 | 19.924 | 21.090 | 1.043 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 1824 | 0 / 1824 | 6.519 | 6.452 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 3648 | 0 / 3648 | 3.075 | 2.886 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 1824 | 0 / 1824 | 5.198 | 5.184 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 3648 | 0 / 3648 | 2.309 | 2.314 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 1824 | 1824 / 0 | 4.532 | 4.527 | 1.312 | -3.220 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / output | 608 | 608 / 0 | 13.568 | 13.412 | 10.150 | -3.418 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 1824 | 0 / 1824 | 4.506 | 4.488 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / v_flat | 1824 | 1824 / 0 | 3.818 | 3.808 | 1.312 | -2.506 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / cache | 608 | 608 / 0 | 7.184 | 7.181 | 1.312 | -5.872 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 608 | 0 / 608 | 5.416 | 5.332 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 608 | 0 / 608 | 5.100 | 5.168 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 608 | 0 / 608 | 3.366 | 3.350 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 38 | 0 / 38 | 7.970 | 7.960 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_qwen36_highconc_c4 / source-gdn-native

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| hcom_allReduce_ / attention_output_communication | 4672 | 0 / 4672 | 52.491 | 23.322 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_ / ffn_down_communication | 4672 | 0 / 4672 | 21.979 | 21.906 | 25.931 | 3.953 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| QuantBatchMatmulV3 / gate_up | 4672 | 4672 / 0 | 12.583 | 12.551 | 11.247 | -1.336 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 1168 | 0 / 1168 | 48.263 | 48.316 | 4.219 | -44.044 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| fused_gdn_gating_kernel / unresolved | 3504 | 0 / 3504 | 12.731 | 12.787 | 8.215 | -4.516 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / down | 4672 | 4672 / 0 | 8.006 | 7.947 | 4.824 | -3.182 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuantV2 / unresolved | 9344 | 0 / 9344 | 3.931 | 3.944 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 3504 | 3504 / 0 | 9.567 | 9.551 | 6.283 | -3.284 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / linear_qkvz | 3504 | 3504 / 0 | 9.202 | 9.127 | 5.668 | -3.534 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicQuant / unresolved | 5840 | 0 / 5840 | 5.429 | 5.434 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 3504 | 3504 / 0 | 7.147 | 7.130 | 3.400 | -3.747 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 3504 | 3504 / 0 | 6.923 | 6.892 | 1.312 | -5.611 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 11680 | 0 / 11680 | 2.034 | 2.103 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 3504 | 3504 / 0 | 6.553 | 6.537 | 2.177 | -4.377 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 8176 | 0 / 8176 | 2.434 | 2.424 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / swiglu | 4672 | 4672 / 0 | 3.491 | 3.525 | 1.312 | -2.179 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNorm / unresolved | 3431 | 0 / 3431 | 4.089 | 4.093 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / k_flat + q_flat | 7008 | 0 / 7008 | 1.938 | 1.943 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 7008 | 0 / 7008 | 1.817 | 1.841 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 3504 | 0 / 3504 | 3.375 | 3.333 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 7008 | 0 / 7008 | 1.675 | 1.648 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 3504 | 0 / 3504 | 3.228 | 3.211 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 1168 | 1168 / 0 | 9.169 | 9.085 | 5.668 | -3.500 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / convolution_input_contiguous | 3504 | 3504 / 0 | 2.386 | 2.369 | 1.312 | -1.074 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / v_flat | 3504 | 3504 / 0 | 2.176 | 2.172 | 1.312 | -0.864 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 3504 | 0 / 3504 | 2.064 | 2.045 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / output | 1168 | 1168 / 0 | 6.082 | 6.016 | 1.752 | -4.330 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 1168 | 0 / 1168 | 5.634 | 5.654 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterPaKvCache / cache | 1168 | 1168 / 0 | 3.359 | 3.397 | 1.312 | -2.047 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 1168 | 0 / 1168 | 3.177 | 3.189 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1168 | 0 / 1168 | 2.568 | 2.623 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1168 | 0 / 1168 | 2.355 | 2.385 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 73 | 0 / 73 | 4.303 | 4.295 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_qwen36_highconc_c4 / source-gdn

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| hcom_allReduce_ / attention_output_communication | 4672 | 0 / 4672 | 52.491 | 23.322 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_ / ffn_down_communication | 4672 | 0 / 4672 | 21.979 | 21.906 | 25.931 | 3.953 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| QuantBatchMatmulV3 / gate_up | 4672 | 4672 / 0 | 12.583 | 12.551 | 11.247 | -1.336 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 1168 | 0 / 1168 | 48.263 | 48.316 | 4.219 | -44.044 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| fused_gdn_gating_kernel / unresolved | 3504 | 0 / 3504 | 12.731 | 12.787 | 8.215 | -4.516 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / down | 4672 | 4672 / 0 | 8.006 | 7.947 | 4.824 | -3.182 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuantV2 / unresolved | 9344 | 0 / 9344 | 3.931 | 3.944 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 3504 | 3504 / 0 | 9.567 | 9.551 | 6.963 | -2.604 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / linear_qkvz | 3504 | 3504 / 0 | 9.202 | 9.127 | 5.668 | -3.534 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicQuant / unresolved | 5840 | 0 / 5840 | 5.429 | 5.434 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 3504 | 3504 / 0 | 7.147 | 7.130 | 3.400 | -3.747 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 3504 | 3504 / 0 | 6.923 | 6.892 | 1.312 | -5.611 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 11680 | 0 / 11680 | 2.034 | 2.103 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 3504 | 3504 / 0 | 6.553 | 6.537 | 2.177 | -4.377 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 8176 | 0 / 8176 | 2.434 | 2.424 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / swiglu | 4672 | 4672 / 0 | 3.491 | 3.525 | 1.312 | -2.179 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNorm / unresolved | 3431 | 0 / 3431 | 4.089 | 4.093 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / k_flat + q_flat | 7008 | 0 / 7008 | 1.938 | 1.943 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 7008 | 0 / 7008 | 1.817 | 1.841 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 3504 | 0 / 3504 | 3.375 | 3.333 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 7008 | 0 / 7008 | 1.675 | 1.648 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 3504 | 0 / 3504 | 3.228 | 3.211 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 1168 | 1168 / 0 | 9.169 | 9.085 | 5.668 | -3.500 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / convolution_input_contiguous | 3504 | 3504 / 0 | 2.386 | 2.369 | 1.312 | -1.074 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / v_flat | 3504 | 3504 / 0 | 2.176 | 2.172 | 1.312 | -0.864 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 3504 | 0 / 3504 | 2.064 | 2.045 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / output | 1168 | 1168 / 0 | 6.082 | 6.016 | 1.752 | -4.330 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 1168 | 0 / 1168 | 5.634 | 5.654 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterPaKvCache / cache | 1168 | 1168 / 0 | 3.359 | 3.397 | 1.312 | -2.047 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 1168 | 0 / 1168 | 3.177 | 3.189 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1168 | 0 / 1168 | 2.568 | 2.623 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1168 | 0 / 1168 | 2.355 | 2.385 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 73 | 0 / 73 | 4.303 | 4.295 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_qwen36_highconc_c40 / source-gdn-native

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| hcom_allReduce_ / attention_output_communication | 3456 | 0 / 3456 | 53.050 | 32.498 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| fused_gdn_gating_kernel / unresolved | 2592 | 0 / 2592 | 41.796 | 41.786 | 32.009 | -9.787 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| hcom_allReduce_ / ffn_down_communication | 3456 | 0 / 3456 | 30.839 | 30.621 | 32.514 | 1.675 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2592 | 2592 / 0 | 32.850 | 32.781 | 27.503 | -5.347 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / gate_up | 3456 | 3456 / 0 | 22.103 | 22.095 | 27.100 | 4.998 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 864 | 0 / 864 | 85.399 | 84.654 | 42.189 | -43.210 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / down | 3456 | 3456 / 0 | 13.496 | 13.462 | 12.113 | -1.383 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicQuant / unresolved | 4320 | 0 / 4320 | 9.036 | 8.964 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuantV2 / unresolved | 6912 | 0 / 6912 | 5.594 | 5.607 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / linear_qkvz | 2592 | 2592 / 0 | 13.392 | 13.252 | 10.538 | -2.854 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 2592 | 2592 / 0 | 12.908 | 12.821 | 2.467 | -10.441 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 2592 | 2592 / 0 | 11.748 | 11.705 | 8.072 | -3.676 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_beta_alpha | 2592 | 2592 / 0 | 8.450 | 8.401 | 10.897 | 2.447 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 6048 | 0 / 6048 | 3.513 | 3.575 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / swiglu | 3456 | 3456 / 0 | 5.955 | 5.881 | 1.312 | -4.643 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 8640 | 0 / 8640 | 2.093 | 2.132 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / k_flat + q_flat | 5184 | 0 / 5184 | 3.428 | 3.405 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNorm / unresolved | 2538 | 0 / 2538 | 6.297 | 6.301 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 2592 | 0 / 2592 | 4.956 | 5.007 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 5184 | 0 / 5184 | 2.429 | 2.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 2592 | 0 / 2592 | 4.702 | 4.725 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 864 | 864 / 0 | 13.468 | 13.372 | 10.538 | -2.930 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 864 | 0 / 864 | 13.451 | 13.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 2592 | 0 / 2592 | 4.073 | 4.030 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 5184 | 0 / 5184 | 2.012 | 2.049 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 2592 | 2592 / 0 | 3.706 | 3.667 | 1.312 | -2.394 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / v_flat | 2592 | 2592 / 0 | 3.336 | 3.313 | 1.312 | -2.024 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / output | 864 | 864 / 0 | 9.128 | 9.037 | 4.945 | -4.183 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / cache | 864 | 864 / 0 | 5.976 | 5.937 | 1.312 | -4.664 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 864 | 0 / 864 | 4.975 | 4.955 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 864 | 0 / 864 | 4.137 | 4.078 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 864 | 0 / 864 | 3.308 | 3.298 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 54 | 0 / 54 | 5.985 | 5.985 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_qwen36_highconc_c40 / source-gdn

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| hcom_allReduce_ / attention_output_communication | 3456 | 0 / 3456 | 53.050 | 32.498 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| fused_gdn_gating_kernel / unresolved | 2592 | 0 / 2592 | 41.796 | 41.786 | 32.009 | -9.787 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| hcom_allReduce_ / ffn_down_communication | 3456 | 0 / 3456 | 30.839 | 30.621 | 32.514 | 1.675 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2592 | 2592 / 0 | 32.850 | 32.781 | 37.501 | 4.651 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / gate_up | 3456 | 3456 / 0 | 22.103 | 22.095 | 27.100 | 4.998 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 864 | 0 / 864 | 85.399 | 84.654 | 42.189 | -43.210 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / down | 3456 | 3456 / 0 | 13.496 | 13.462 | 12.113 | -1.383 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicQuant / unresolved | 4320 | 0 / 4320 | 9.036 | 8.964 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuantV2 / unresolved | 6912 | 0 / 6912 | 5.594 | 5.607 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / linear_qkvz | 2592 | 2592 / 0 | 13.392 | 13.252 | 10.538 | -2.854 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 2592 | 2592 / 0 | 12.908 | 12.821 | 2.467 | -10.441 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 2592 | 2592 / 0 | 11.748 | 11.705 | 8.072 | -3.676 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_beta_alpha | 2592 | 2592 / 0 | 8.450 | 8.401 | 10.897 | 2.447 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 6048 | 0 / 6048 | 3.513 | 3.575 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / swiglu | 3456 | 3456 / 0 | 5.955 | 5.881 | 1.312 | -4.643 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 8640 | 0 / 8640 | 2.093 | 2.132 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / k_flat + q_flat | 5184 | 0 / 5184 | 3.428 | 3.405 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNorm / unresolved | 2538 | 0 / 2538 | 6.297 | 6.301 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 2592 | 0 / 2592 | 4.956 | 5.007 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 5184 | 0 / 5184 | 2.429 | 2.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 2592 | 0 / 2592 | 4.702 | 4.725 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 864 | 864 / 0 | 13.468 | 13.372 | 10.538 | -2.930 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 864 | 0 / 864 | 13.451 | 13.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 2592 | 0 / 2592 | 4.073 | 4.030 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 5184 | 0 / 5184 | 2.012 | 2.049 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 2592 | 2592 / 0 | 3.706 | 3.667 | 1.312 | -2.394 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / v_flat | 2592 | 2592 / 0 | 3.336 | 3.313 | 1.312 | -2.024 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / output | 864 | 864 / 0 | 9.128 | 9.037 | 4.945 | -4.183 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / cache | 864 | 864 / 0 | 5.976 | 5.937 | 1.312 | -4.664 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 864 | 0 / 864 | 4.975 | 4.955 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 864 | 0 / 864 | 4.137 | 4.078 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 864 | 0 / 864 | 3.308 | 3.298 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 54 | 0 / 54 | 5.985 | 5.985 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_qwen38_highconc_c128 / source-gdn-native

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 1392 | 1392 / 0 | 183.795 | 183.780 | 167.995 | -15.801 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1856 | 0 / 1856 | 79.602 | 79.050 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1856 | 0 / 1856 | 76.728 | 76.537 | 30.862 | -45.866 | 15% (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| QuantBatchMatmulV3 / gate_up | 1856 | 1856 / 0 | 64.799 | 64.864 | 93.737 | 28.938 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| fused_gdn_gating_kernel / unresolved | 1392 | 0 / 1392 | 75.749 | 75.754 | 56.488 | -19.261 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MatMulV3 / linear_qkvz | 1392 | 1392 / 0 | 55.579 | 55.566 | 80.238 | 24.659 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 464 | 0 / 464 | 152.750 | 151.778 | 135.397 | -17.353 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / down | 1856 | 1856 / 0 | 35.567 | 35.562 | 44.582 | 9.016 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 1392 | 1392 / 0 | 39.372 | 39.355 | 6.980 | -32.392 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 1392 | 1392 / 0 | 26.871 | 26.815 | 30.665 | 3.794 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicMxQuant / unresolved | 2320 | 0 / 2320 | 13.334 | 13.570 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / swiglu | 1856 | 1856 / 0 | 9.619 | 9.553 | 3.342 | -6.277 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 3248 | 0 / 3248 | 4.360 | 4.381 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 464 | 464 / 0 | 30.232 | 30.223 | 41.730 | 11.498 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNorm / unresolved | 1363 | 0 / 1363 | 9.873 | 9.845 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 464 | 0 / 464 | 28.389 | 28.261 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 1392 | 1392 / 0 | 8.998 | 8.912 | 11.864 | 2.866 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 1856 | 1856 / 0 | 6.729 | 6.720 | 1.689 | -5.041 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TensorMove / unresolved | 2784 | 0 / 2784 | 4.366 | 4.422 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 4640 | 0 / 4640 | 2.477 | 2.588 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 1392 | 0 / 1392 | 8.186 | 8.182 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / k_flat + q_flat | 2784 | 0 / 2784 | 3.885 | 3.840 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 2784 | 0 / 2784 | 3.779 | 3.898 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 1392 | 0 / 1392 | 5.379 | 5.365 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / output | 464 | 464 / 0 | 15.499 | 15.486 | 16.422 | 0.924 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / convolution_input_contiguous | 1392 | 1392 / 0 | 4.885 | 4.867 | 1.312 | -3.573 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / alpha_contiguous + beta_contiguous | 2784 | 0 / 2784 | 2.328 | 2.337 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 1392 | 0 / 1392 | 4.531 | 4.519 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / v_flat | 1392 | 1392 / 0 | 3.991 | 3.974 | 1.312 | -2.679 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / cache | 464 | 464 / 0 | 7.558 | 7.510 | 1.312 | -6.246 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 464 | 0 / 464 | 5.695 | 5.623 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / output.quantize | 464 | 464 / 0 | 5.517 | 5.508 | 1.312 | -4.205 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 464 | 0 / 464 | 4.758 | 4.756 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 464 | 0 / 464 | 4.394 | 4.322 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 29 | 0 / 29 | 8.147 | 8.139 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_qwen38_highconc_c128 / source-gdn

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 1392 | 1392 / 0 | 183.795 | 183.780 | 231.673 | 47.878 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1856 | 0 / 1856 | 79.602 | 79.050 | — | — | 15% (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1856 | 0 / 1856 | 76.728 | 76.537 | 30.862 | -45.866 | 15% (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| QuantBatchMatmulV3 / gate_up | 1856 | 1856 / 0 | 64.799 | 64.864 | 93.737 | 28.938 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| fused_gdn_gating_kernel / unresolved | 1392 | 0 / 1392 | 75.749 | 75.754 | 56.488 | -19.261 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MatMulV3 / linear_qkvz | 1392 | 1392 / 0 | 55.579 | 55.566 | 80.238 | 24.659 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 464 | 0 / 464 | 152.750 | 151.778 | 135.397 | -17.353 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / down | 1856 | 1856 / 0 | 35.567 | 35.562 | 44.582 | 9.016 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 1392 | 1392 / 0 | 39.372 | 39.355 | 6.980 | -32.392 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 1392 | 1392 / 0 | 26.871 | 26.815 | 30.665 | 3.794 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicMxQuant / unresolved | 2320 | 0 / 2320 | 13.334 | 13.570 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / swiglu | 1856 | 1856 / 0 | 9.619 | 9.553 | 3.342 | -6.277 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 3248 | 0 / 3248 | 4.360 | 4.381 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 464 | 464 / 0 | 30.232 | 30.223 | 41.730 | 11.498 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNorm / unresolved | 1363 | 0 / 1363 | 9.873 | 9.845 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 464 | 0 / 464 | 28.389 | 28.261 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 1392 | 1392 / 0 | 8.998 | 8.912 | 11.864 | 2.866 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 1856 | 1856 / 0 | 6.729 | 6.720 | 1.689 | -5.041 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TensorMove / unresolved | 2784 | 0 / 2784 | 4.366 | 4.422 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 4640 | 0 / 4640 | 2.477 | 2.588 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 1392 | 0 / 1392 | 8.186 | 8.182 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / k_flat + q_flat | 2784 | 0 / 2784 | 3.885 | 3.840 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 2784 | 0 / 2784 | 3.779 | 3.898 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 1392 | 0 / 1392 | 5.379 | 5.365 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / output | 464 | 464 / 0 | 15.499 | 15.486 | 16.422 | 0.924 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / convolution_input_contiguous | 1392 | 1392 / 0 | 4.885 | 4.867 | 1.312 | -3.573 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / alpha_contiguous + beta_contiguous | 2784 | 0 / 2784 | 2.328 | 2.337 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 1392 | 0 / 1392 | 4.531 | 4.519 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / v_flat | 1392 | 1392 / 0 | 3.991 | 3.974 | 1.312 | -2.679 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / cache | 464 | 464 / 0 | 7.558 | 7.510 | 1.312 | -6.246 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 464 | 0 / 464 | 5.695 | 5.623 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / output.quantize | 464 | 464 / 0 | 5.517 | 5.508 | 1.312 | -4.205 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 464 | 0 / 464 | 4.758 | 4.756 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 464 | 0 / 464 | 4.394 | 4.322 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 29 | 0 / 29 | 8.147 | 8.139 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_qwen38_highconc_c32 / source-gdn-native

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| fused_gdn_gating_kernel / unresolved | 2304 | 0 / 2304 | 68.790 | 67.444 | 56.488 | -12.302 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| hcom_allReduce_AicpuKernel / attention_output_communication | 3072 | 0 / 3072 | 38.004 | 36.662 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 3072 | 0 / 3072 | 34.858 | 34.696 | 15.816 | -19.043 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2304 | 2304 / 0 | 41.519 | 41.453 | 41.999 | 0.480 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_qkvz | 2304 | 2304 / 0 | 35.101 | 35.094 | 20.432 | -14.669 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / gate_up | 3072 | 3072 / 0 | 22.210 | 22.177 | 31.275 | 9.066 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 3072 | 3072 / 0 | 15.255 | 15.240 | 17.802 | 2.547 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 768 | 0 / 768 | 60.822 | 60.145 | 33.849 | -26.973 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MatMulV3 / linear_output | 2304 | 2304 / 0 | 17.137 | 17.142 | 12.379 | -4.757 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 2304 | 2304 / 0 | 16.508 | 16.570 | 2.025 | -14.484 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicMxQuant / unresolved | 3840 | 0 / 3840 | 7.524 | 7.542 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 5376 | 0 / 5376 | 3.943 | 4.093 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / swiglu | 3072 | 3072 / 0 | 6.636 | 6.583 | 1.312 | -5.324 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / k_flat + q_flat | 4608 | 0 / 4608 | 3.791 | 3.752 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 2304 | 2304 / 0 | 7.456 | 7.375 | 11.864 | 4.409 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 7680 | 0 / 7680 | 2.164 | 2.182 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / down.quantize | 3072 | 3072 / 0 | 5.296 | 5.322 | 1.312 | -3.984 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / qkv | 768 | 768 / 0 | 20.021 | 19.980 | 10.625 | -9.397 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNorm / unresolved | 2256 | 0 / 2256 | 5.956 | 5.947 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 4608 | 0 / 4608 | 2.769 | 2.575 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 2304 | 0 / 2304 | 5.175 | 5.178 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 2304 | 0 / 2304 | 5.123 | 5.125 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 2304 | 0 / 2304 | 4.397 | 4.410 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 4608 | 0 / 4608 | 2.082 | 2.074 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 2304 | 2304 / 0 | 4.097 | 4.060 | 1.312 | -2.785 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 768 | 0 / 768 | 11.381 | 11.252 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / v_flat | 2304 | 2304 / 0 | 3.737 | 3.728 | 1.312 | -2.425 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / output | 768 | 768 / 0 | 8.343 | 8.337 | 6.538 | -1.805 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / cache | 768 | 768 / 0 | 6.322 | 6.313 | 1.312 | -5.010 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 768 | 0 / 768 | 5.328 | 5.293 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / output.quantize | 768 | 768 / 0 | 4.824 | 4.780 | 1.312 | -3.512 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 768 | 0 / 768 | 3.920 | 3.910 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 768 | 0 / 768 | 3.365 | 3.357 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 48 | 0 / 48 | 5.754 | 5.797 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_qwen38_highconc_c32 / source-gdn

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| fused_gdn_gating_kernel / unresolved | 2304 | 0 / 2304 | 68.790 | 67.444 | 56.488 | -12.302 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| hcom_allReduce_AicpuKernel / attention_output_communication | 3072 | 0 / 3072 | 38.004 | 36.662 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 3072 | 0 / 3072 | 34.858 | 34.696 | 15.816 | -19.043 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2304 | 2304 / 0 | 41.519 | 41.453 | 57.918 | 16.399 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_qkvz | 2304 | 2304 / 0 | 35.101 | 35.094 | 20.432 | -14.669 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / gate_up | 3072 | 3072 / 0 | 22.210 | 22.177 | 31.275 | 9.066 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 3072 | 3072 / 0 | 15.255 | 15.240 | 17.802 | 2.547 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| FusedInferAttentionScore / unresolved | 768 | 0 / 768 | 60.822 | 60.145 | 33.849 | -26.973 | 15% (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| MatMulV3 / linear_output | 2304 | 2304 / 0 | 17.137 | 17.142 | 12.379 | -4.757 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 2304 | 2304 / 0 | 16.508 | 16.570 | 2.025 | -14.484 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicMxQuant / unresolved | 3840 | 0 / 3840 | 7.524 | 7.542 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 5376 | 0 / 5376 | 3.943 | 4.093 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / swiglu | 3072 | 3072 / 0 | 6.636 | 6.583 | 1.312 | -5.324 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / k_flat + q_flat | 4608 | 0 / 4608 | 3.791 | 3.752 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 2304 | 2304 / 0 | 7.456 | 7.375 | 11.864 | 4.409 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Add / unresolved | 7680 | 0 / 7680 | 2.164 | 2.182 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / down.quantize | 3072 | 3072 / 0 | 5.296 | 5.322 | 1.312 | -3.984 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / qkv | 768 | 768 / 0 | 20.021 | 19.980 | 10.625 | -9.397 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNorm / unresolved | 2256 | 0 / 2256 | 5.956 | 5.947 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 4608 | 0 / 4608 | 2.769 | 2.575 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 2304 | 0 / 2304 | 5.175 | 5.178 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 2304 | 0 / 2304 | 5.123 | 5.125 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 2304 | 0 / 2304 | 4.397 | 4.410 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 4608 | 0 / 4608 | 2.082 | 2.074 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 2304 | 2304 / 0 | 4.097 | 4.060 | 1.312 | -2.785 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 768 | 0 / 768 | 11.381 | 11.252 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / v_flat | 2304 | 2304 / 0 | 3.737 | 3.728 | 1.312 | -2.425 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / output | 768 | 768 / 0 | 8.343 | 8.337 | 6.538 | -1.805 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / cache | 768 | 768 / 0 | 6.322 | 6.313 | 1.312 | -5.010 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 768 | 0 / 768 | 5.328 | 5.293 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / output.quantize | 768 | 768 / 0 | 4.824 | 4.780 | 1.312 | -3.512 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 768 | 0 / 768 | 3.920 | 3.910 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 768 | 0 / 768 | 3.365 | 3.357 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 48 | 0 / 48 | 5.754 | 5.797 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_qwen38_highconc_c4 / source-gdn-native

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| QuantBatchMatmulV3 / gate_up | 2880 | 2880 / 0 | 18.467 | 18.380 | 17.333 | -1.134 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_qkvz | 2160 | 2160 / 0 | 24.459 | 24.358 | 11.242 | -13.217 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / attention_output_communication | 2880 | 0 / 2880 | 18.179 | 17.790 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| fused_gdn_gating_kernel / unresolved | 2160 | 0 / 2160 | 22.255 | 22.093 | 15.176 | -7.079 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 2880 | 0 / 2880 | 16.645 | 16.474 | 11.427 | -5.218 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| FusedInferAttentionScore / unresolved | 720 | 0 / 720 | 49.032 | 48.981 | 4.231 | -44.801 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / down | 2880 | 2880 / 0 | 10.639 | 10.620 | 9.821 | -0.818 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 2160 | 2160 / 0 | 11.243 | 11.206 | 6.751 | -4.492 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2160 | 2160 / 0 | 11.102 | 11.097 | 6.678 | -4.424 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 2160 | 2160 / 0 | 7.524 | 7.476 | 1.312 | -6.212 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicMxQuant / unresolved | 3600 | 0 / 3600 | 4.307 | 4.218 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 7200 | 0 / 7200 | 2.054 | 2.110 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 2160 | 2160 / 0 | 6.599 | 6.503 | 3.112 | -3.487 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 5040 | 0 / 5040 | 2.749 | 2.514 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / swiglu | 2880 | 2880 / 0 | 3.908 | 3.900 | 1.312 | -2.596 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 2880 | 2880 / 0 | 3.866 | 3.867 | 1.312 | -2.554 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / k_flat + q_flat | 4320 | 0 / 4320 | 2.243 | 2.238 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNorm / unresolved | 2115 | 0 / 2115 | 4.302 | 4.266 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 4320 | 0 / 4320 | 2.102 | 2.072 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 2160 | 2160 / 0 | 4.193 | 4.157 | 1.312 | -2.881 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ConcatD / unresolved | 2160 | 0 / 2160 | 3.934 | 3.869 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 2160 | 0 / 2160 | 3.803 | 3.768 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 4320 | 0 / 4320 | 1.752 | 1.784 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 720 | 720 / 0 | 9.356 | 9.351 | 5.808 | -3.548 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 2160 | 0 / 2160 | 2.468 | 2.435 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / v_flat | 2160 | 2160 / 0 | 2.128 | 2.125 | 1.312 | -0.816 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 720 | 0 / 720 | 6.254 | 6.247 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / output | 720 | 720 / 0 | 5.696 | 5.680 | 3.485 | -2.211 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / output.quantize | 720 | 720 / 0 | 4.102 | 4.079 | 1.312 | -2.790 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / cache | 720 | 720 / 0 | 3.833 | 3.818 | 1.312 | -2.521 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 720 | 0 / 720 | 3.420 | 3.433 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 720 | 0 / 720 | 3.301 | 3.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 720 | 0 / 720 | 2.948 | 2.944 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 45 | 0 / 45 | 4.128 | 4.131 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

## a5_qwen38_highconc_c4 / source-gdn

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| QuantBatchMatmulV3 / gate_up | 2880 | 2880 / 0 | 18.467 | 18.380 | 17.333 | -1.134 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_qkvz | 2160 | 2160 / 0 | 24.459 | 24.358 | 11.242 | -13.217 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / attention_output_communication | 2880 | 0 / 2880 | 18.179 | 17.790 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| fused_gdn_gating_kernel / unresolved | 2160 | 0 / 2160 | 22.255 | 22.093 | 15.176 | -7.079 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 2880 | 0 / 2880 | 16.645 | 16.474 | 11.427 | -5.218 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| FusedInferAttentionScore / unresolved | 720 | 0 / 720 | 49.032 | 48.981 | 4.231 | -44.801 | 15 us (unscored reference) | 0 / 0 | conditional_source_role_program; not_a_tensor_contract_cohort / reference_only |
| QuantBatchMatmulV3 / down | 2880 | 2880 / 0 | 10.639 | 10.620 | 9.821 | -0.818 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 2160 | 2160 / 0 | 11.243 | 11.206 | 6.751 | -4.492 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RecurrentGatedDeltaRule / decode_recurrent_scan | 2160 | 2160 / 0 | 11.102 | 11.097 | 8.542 | -2.560 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| CausalConv1d / short_convolution | 2160 | 2160 / 0 | 7.524 | 7.476 | 1.312 | -6.212 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| AddRmsNormDynamicMxQuant / unresolved | 3600 | 0 / 3600 | 4.307 | 4.218 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 7200 | 0 / 7200 | 2.054 | 2.110 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_beta_alpha | 2160 | 2160 / 0 | 6.599 | 6.503 | 3.112 | -3.487 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 5040 | 0 / 5040 | 2.749 | 2.514 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SwiGlu / swiglu | 2880 | 2880 / 0 | 3.908 | 3.900 | 1.312 | -2.596 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 2880 | 2880 / 0 | 3.866 | 3.867 | 1.312 | -2.554 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / k_flat + q_flat | 4320 | 0 / 4320 | 2.243 | 2.238 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AddRmsNorm / unresolved | 2115 | 0 / 2115 | 4.302 | 4.266 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| l2norm_fwd_kernel2 / unresolved | 4320 | 0 / 4320 | 2.102 | 2.072 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / convolution_input_contiguous | 2160 | 2160 / 0 | 4.193 | 4.157 | 1.312 | -2.881 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ConcatD / unresolved | 2160 | 0 / 2160 | 3.934 | 3.869 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _layer_norm_fwd_1pass_kernel_npu / unresolved | 2160 | 0 / 2160 | 3.803 | 3.768 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / alpha_contiguous + beta_contiguous | 4320 | 0 / 4320 | 1.752 | 1.784 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / qkv | 720 | 720 / 0 | 9.356 | 9.351 | 5.808 | -3.548 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 2160 | 0 / 2160 | 2.468 | 2.435 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / v_flat | 2160 | 2160 / 0 | 2.128 | 2.125 | 1.312 | -0.816 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| split_qkv_rmsnorm_mrope_kernel / unresolved | 720 | 0 / 720 | 6.254 | 6.247 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / output | 720 | 720 / 0 | 5.696 | 5.680 | 3.485 | -2.211 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / output.quantize | 720 | 720 / 0 | 4.102 | 4.079 | 1.312 | -2.790 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterPaKvCache / cache | 720 | 720 / 0 | 3.833 | 3.818 | 1.312 | -2.521 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Index / unresolved | 720 | 0 / 720 | 3.420 | 3.433 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 720 | 0 / 720 | 3.301 | 3.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 720 | 0 / 720 | 2.948 | 2.944 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 45 | 0 / 45 | 4.128 | 4.131 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
