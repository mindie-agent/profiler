# Large-Call Failed Cohorts

Selection: status=compared, accuracy_tier=relative_15pct, accuracy_pass=false. Observed complete-event mean > 50 us; absolute relative error > 15%.
Sort: `observed_activity_ms_descending; declaration_variant_cohort_id_tiebreak`. JSON retains all 233 failed cohorts; this table shows the first 30.

Receipt SHA256: `adf90344f80c7b075a9ac9751d8073185aa776473a385641ca89f77bfd94ac7f`.
Script SHA256: `4c660b4d36fa30291c026807f4774300d239a93c597ac03cdcfa185dd637aea1`.

Each observed call is one captured native profiler event. The prediction boundary is reported separately. Contract positions and stored tensor shapes/dtypes are shown verbatim; excluded fields remain subject to contract_scope in JSON.
Variant totals reuse captures. Activity sums can overlap and are not full-model latency. A homogeneous cohort does not identify a layer, invocation, or DP replica.

| Tier | Passed / compared cohorts | Failed |
| --- | ---: | ---: |
| relative_15pct | 81 / 314 | 233 |
| absolute_15us | 138 / 163 | 25 |
| All scored | 219 / 477 | 258 |

| # | Declaration / variant | Native / cohort suffix | Calls | Observed mean / p50 us | Predicted us | Signed / abs diff us | Relative | Signed / abs total gap ms | Prediction boundary / single program | Saved tensor contract |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | a3_glm53_prefill / selected_native_fusion | SparseFlashAttention / 13439ff547cd | 78 | 13199.665 / 13208.966 | 6121.175 | -7078.489 / 7078.489 | -53.63% | -552.122 / 552.122 | semantic_device_program / True | `["sparse_attention_active","SparseFlashAttention",[[[4096,8,512],"bf16","ND"],[[4096,8,64],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"],[[1,64],"bf16","ND"]],[[4096,8,512],"bf16","ND"]]` |
| 2 | a3_glm53_prefill / source_declared_unfused_reference | SparseFlashAttention / 1cbb0d3c26c0 | 78 | 13199.665 / 13208.966 | 6121.175 | -7078.489 / 7078.489 | -53.63% | -552.122 / 552.122 | semantic_device_program / True | `["sparse_attention_active","SparseFlashAttention",[[[4096,8,512],"bf16","ND"],[[4096,8,64],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"],[[1,64],"bf16","ND"]],[[4096,8,512],"bf16","ND"]]` |
| 3 | a3_glm53_prefill_shared_quant / source_shared_int32_conditional | SparseFlashAttention / d2dac293ab63 | 78 | 13199.665 / 13208.966 | 6121.175 | -7078.489 / 7078.489 | -53.63% | -552.122 / 552.122 | semantic_device_program / True | `["sparse_attention_active","SparseFlashAttention",[[[4096,8,512],"bf16","ND"],[[4096,8,64],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"],[[1,64],"bf16","ND"]],[[4096,8,512],"bf16","ND"]]` |
| 4 | a3_glm53_decode / selected_native_fusion | SparseFlashAttention / 94938c7f56bb | 5772 | 90.731 / 90.319 | 1.987 | -88.743 / 88.743 | -97.81% | -512.226 / 512.226 | semantic_device_program / True | `["sparse_attention_active","SparseFlashAttention",[[[1,8,512],"bf16","ND"],[[1,8,64],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"],[[1,64],"bf16","ND"]],[[1,8,512],"bf16","ND"]]` |
| 5 | a3_glm53_decode / source_declared_unfused_reference | SparseFlashAttention / b79a42d13139 | 5772 | 90.731 / 90.319 | 5.000 | -85.731 / 85.731 | -94.49% | -494.838 / 494.838 | semantic_device_program / True | `["sparse_attention_active","SparseFlashAttention",[[[1,8,512],"bf16","ND"],[[1,8,64],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"],[[1,64],"bf16","ND"]],[[1,8,512],"bf16","ND"]]` |
| 6 | a3_glm53_decode_shared_quant / source_shared_int32_conditional | SparseFlashAttention / 3999142577be | 5772 | 90.731 / 90.319 | 5.000 | -85.731 / 85.731 | -94.49% | -494.838 / 494.838 | semantic_device_program / True | `["sparse_attention_active","SparseFlashAttention",[[[1,8,512],"bf16","ND"],[[1,8,64],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"],[[1,64],"bf16","ND"]],[[1,8,512],"bf16","ND"]]` |
| 7 | a3_glm53_decode / selected_native_fusion | GroupedMatmulSwigluQuantV2 / 3a074dca1390 | 5550 | 88.039 / 86.478 | 10.756 | -77.283 / 77.283 | -87.78% | -428.919 / 428.919 | semantic_device_program / True | `["grouped_mlp_parameters_active","GroupedMatmulSwigluQuantV2",[256,6144,256],["int8","int4","int8"]]` |
| 8 | a5_kimi_k3_decode_checkpoint / current_checkpoint_conditional | SituMxQuant / cd38938eb970 | 6898 | 65.134 / 64.697 | 0.002 | -65.132 / 65.132 | -100.00% | -449.283 / 449.283 | semantic_device_program / True | `["situ_mxquant_active","SituMxQuant",[[1,1536],"bf16","ND"],[[1,768],"fp8_e4m3","ND"],[[1,12,2],"fp8_e8m0","ND"]]` |
| 9 | a5_kimi_k3_decode_checkpoint_eager_single_group / source_single_group_mxfp8_conditional | SituMxQuant / 5ebf5baf27a2 | 6898 | 65.134 / 64.697 | 0.002 | -65.132 / 65.132 | -100.00% | -449.283 / 449.283 | semantic_device_program / True | `["situ_mxquant_active","SituMxQuant",[[1,1536],"bf16","ND"],[[1,768],"fp8_e4m3","ND"],[[1,12,2],"fp8_e8m0","ND"]]` |
| 10 | a5_qwen38 / case_default | QuantBatchMatmulV3 / 7eeeedd94470 | 64 | 6770.419 / 6770.202 | 11925.185 | +5154.766 / 5154.766 | +76.14% | +329.905 / 329.905 | semantic_device_program / True | `["matrix",[16384,34816,5120],"fp8_e4m3","fp8_e4m3","bf16",[16384,80,2],"fp8_e8m0"]` |
| 11 | a5_qwen38_paged_prefill_q16384 / paged_body_geometry_conditional | QuantBatchMatmulV3 / 8d9096800427 | 64 | 6770.419 / 6770.202 | 11925.185 | +5154.766 / 5154.766 | +76.14% | +329.905 / 329.905 | semantic_device_program / True | `["matrix",[16384,34816,5120],"fp8_e4m3","fp8_e4m3","bf16",[16384,80,2],"fp8_e8m0"]` |
| 12 | a5_qwen38 / case_default | MatMulV3 / 930e55d79ec5 | 48 | 6375.719 / 6375.468 | 10762.600 | +4386.881 / 4386.881 | +68.81% | +210.570 / 210.570 | semantic_device_program / True | `["matrix",[16384,16384,5120],"bf16","bf16","bf16",[],""]` |
| 13 | a5_qwen38_paged_prefill_q16384 / paged_body_geometry_conditional | MatMulV3 / 945014f82cda | 48 | 6375.719 / 6375.468 | 10762.600 | +4386.881 / 4386.881 | +68.81% | +210.570 / 210.570 | semantic_device_program / True | `["matrix",[16384,16384,5120],"bf16","bf16","bf16",[],""]` |
| 14 | a3_glm53_decode / selected_native_fusion | GroupedMatmul / 2caca0f1f70b | 5550 | 52.907 / 51.539 | 6.152 | -46.755 / 46.755 | -88.37% | -259.493 / 259.493 | semantic_device_program / True | `["grouped_matrix",[256,8,6144,256],"int8","int4","bf16",[8],"fp32"]` |
| 15 | a5_qwen38 / case_default | QuantBatchMatmulV3 / de486add4978 | 64 | 3392.825 / 3392.483 | 5906.295 | +2513.470 / 2513.470 | +74.08% | +160.862 / 160.862 | semantic_device_program / True | `["matrix",[16384,5120,17408],"fp8_e4m3","fp8_e4m3","bf16",[16384,272,2],"fp8_e8m0"]` |
| 16 | a5_qwen38_paged_prefill_q16384 / paged_body_geometry_conditional | QuantBatchMatmulV3 / 7c1da0e60109 | 64 | 3392.825 / 3392.483 | 5906.295 | +2513.470 / 2513.470 | +74.08% | +160.862 / 160.862 | semantic_device_program / True | `["matrix",[16384,5120,17408],"fp8_e4m3","fp8_e4m3","bf16",[16384,272,2],"fp8_e8m0"]` |
| 17 | a5_qwen38 / case_default | FusedInferAttentionScore / 4ddffadf9767 | 17 | 12573.041 / 12574.640 | 7626.473 | -4946.568 / 4946.568 | -39.34% | -84.092 / 84.092 | semantic_device_program / True | `["attention_active_qkv","FusedInferAttentionScore",[[[16384,24,256],"bf16","ND"],[[16384,4,256],"bf16","ND"],[[16384,4,256],"bf16","ND"]],[[[16384,24,256],"bf16","ND"]]]` |
| 18 | a5_qwen38_steady / selected_steady_matrix_conditional | FusedInferAttentionScore / 0ee628c336ca | 17 | 12573.041 / 12574.640 | 7626.473 | -4946.568 / 4946.568 | -39.34% | -84.092 / 84.092 | semantic_device_program / True | `["attention_active_qkv","FusedInferAttentionScore",[[[16384,24,256],"bf16","ND"],[[16384,4,256],"bf16","ND"],[[16384,4,256],"bf16","ND"]],[[[16384,24,256],"bf16","ND"]]]` |
| 19 | a3_v4pro / case_default | SparseAttnSharedkv / c25114bb3a72 | 120 | 1180.346 / 1183.006 | 126.921 | -1053.426 / 1053.426 | -89.25% | -126.411 / 126.411 | semantic_device_program / True | `["sparse_attention_active","SparseAttnSharedkv",[[[1024,8,512],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"]],[[1024,8,512],"bf16","ND"]]` |
| 20 | a3_v4pro / selected_native_fusion | SparseAttnSharedkv / ce6ddf963a94 | 120 | 1180.346 / 1183.006 | 126.921 | -1053.426 / 1053.426 | -89.25% | -126.411 / 126.411 | semantic_device_program / True | `["sparse_attention_active","SparseAttnSharedkv",[[[1024,8,512],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"]],[[1024,8,512],"bf16","ND"]]` |
| 21 | a3_v4pro_compressor_fp32 / source_compressor_fp32_conditional_reference | SparseAttnSharedkv / 051b8ae192c3 | 120 | 1180.346 / 1183.006 | 126.921 | -1053.426 / 1053.426 | -89.25% | -126.411 / 126.411 | semantic_device_program / True | `["sparse_attention_active","SparseAttnSharedkv",[[[1024,8,512],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"]],[[1024,8,512],"bf16","ND"]]` |
| 22 | a5_qwen38 / case_default | MatMulV3 / 1cea4d0a470c | 51 | 2394.718 / 2394.683 | 4034.762 | +1640.043 / 1640.043 | +68.49% | +83.642 / 83.642 | semantic_device_program / True | `["matrix",[16384,5120,6144],"bf16","bf16","bf16",[],""]` |
| 23 | a5_qwen38_paged_prefill_q16384 / paged_body_geometry_conditional | MatMulV3 / c7bb67e65ffa | 51 | 2394.718 / 2394.683 | 4034.762 | +1640.043 / 1640.043 | +68.49% | +83.642 / 83.642 | semantic_device_program / True | `["matrix",[16384,5120,6144],"bf16","bf16","bf16",[],""]` |
| 24 | a3_v4pro / case_default | HcPost / ea18a55f6ba0 | 496 | 202.098 / 202.126 | 110.169 | -91.930 / 91.930 | -45.49% | -45.597 / 45.597 | semantic_device_program / True | `["hyper_connection_active","HcPost",[[[1024,7168],"bf16","ND"],[[1024,4,7168],"bf16","ND"],[[1024,4],"fp32","ND"],[[1024,4,4],"fp32","ND"]],[[[1024,4,7168],"bf16","ND"]]]` |
| 25 | a3_v4pro / selected_native_fusion | HcPost / 092ed31d70ce | 496 | 202.098 / 202.126 | 129.751 | -72.348 / 72.348 | -35.80% | -35.885 / 35.885 | semantic_device_program / True | `["hyper_connection_active","HcPost",[[[1024,7168],"bf16","ND"],[[1024,4,7168],"bf16","ND"],[[1024,4],"fp32","ND"],[[1024,4,4],"fp32","ND"]],[[[1024,4,7168],"bf16","ND"]]]` |
| 26 | a3_v4pro_compressor_fp32 / source_compressor_fp32_conditional_reference | HcPost / b25f17118a6e | 496 | 202.098 / 202.126 | 129.751 | -72.348 / 72.348 | -35.80% | -35.885 / 35.885 | semantic_device_program / True | `["hyper_connection_active","HcPost",[[[1024,7168],"bf16","ND"],[[1024,4,7168],"bf16","ND"],[[1024,4],"fp32","ND"],[[1024,4,4],"fp32","ND"]],[[[1024,4,7168],"bf16","ND"]]]` |
| 27 | a3_v4pro / selected_native_fusion | HcPre / 04d26de41982 | 496 | 191.803 / 193.156 | 316.457 | +124.653 / 124.653 | +64.99% | +61.828 / 61.828 | semantic_device_program / True | `["hyper_connection_active","HcPre",[[[1024,4,7168],"bf16","ND"],[[24,28672],"fp32","ND"],[[3],"fp32","ND"],[[24],"fp32","ND"]],[[[1024,7168],"bf16","ND"],[[1024,4],"fp32","ND"],[[1024,4,4],"fp32","ND"]]]` |
| 28 | a3_v4pro_compressor_fp32 / source_compressor_fp32_conditional_reference | HcPre / 556710268857 | 496 | 191.803 / 193.156 | 316.457 | +124.653 / 124.653 | +64.99% | +61.828 / 61.828 | semantic_device_program / True | `["hyper_connection_active","HcPre",[[[1024,4,7168],"bf16","ND"],[[24,28672],"fp32","ND"],[[3],"fp32","ND"],[[24],"fp32","ND"]],[[[1024,7168],"bf16","ND"],[[1024,4],"fp32","ND"],[[1024,4,4],"fp32","ND"]]]` |
| 29 | a3_glm53_prefill / selected_native_fusion | GroupedMatmul / 45f07848984e | 75 | 1225.255 / 1219.896 | 1894.139 | +668.884 / 668.884 | +54.59% | +50.166 / 50.166 | semantic_device_program / True | `["grouped_matrix",[256,32768,6144,256],"int8","int4","bf16",[32768],"fp32"]` |
| 30 | a3_v4f / case_default | SparseAttnSharedkv / a28b4388de80 | 21 | 3738.519 / 3737.845 | 1406.401 | -2332.118 / 2332.118 | -62.38% | -48.974 / 48.974 | semantic_device_program / True | `["sparse_attention_active","SparseAttnSharedkv",[[[4096,8,512],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"]],[[4096,8,512],"bf16","ND"]]` |

## Reference Costs Excluded From Accuracy

71 reference cohorts / 137499 observed calls. These are not passing comparisons.

| Reason | Cohorts | Calls | Observed activity ms | Predicted reference ms |
| --- | ---: | ---: | ---: | ---: |
| mxfp4_native_execution_unmodeled | 15 | 66128 | 4327.130 | 248002.574 |
| quantized_epilogue_unmodeled | 11 | 23244 | 2241.104 | 1001.108 |
| unfused_subgraph_is_not_the_observed_native_kernel | 45 | 48127 | 2358.409 | 4168.478 |

## Case Evidence And Model Coverage

Model coverage is copied only when present in the saved comparison. `not_projected` does not mean complete; this report makes no additional sim calls.

| Declaration / variant | Capture | Recorded raw source SHA256 | Model coverage |
| --- | --- | --- | --- |
| a3_glm53_prefill / source_declared_unfused_reference | a3_glm53_prefill | `ded3a03adc7a82b0801acc6a88bb85589b8f3a3f3a4a416a1322ebfb514c614f` | not_projected |
| a3_glm53_prefill / selected_native_fusion | a3_glm53_prefill | `ded3a03adc7a82b0801acc6a88bb85589b8f3a3f3a4a416a1322ebfb514c614f` | not_projected |
| a3_glm53_prefill_shared_quant / source_shared_int32_conditional | a3_glm53_prefill | `ded3a03adc7a82b0801acc6a88bb85589b8f3a3f3a4a416a1322ebfb514c614f` | not_projected |
| a3_glm53_decode / source_declared_unfused_reference | a3_glm53_decode | `ed5e9696949d51c2d1d31ab099a71a2c98722d5719f004fcf90c9ceff036f60c` | not_projected |
| a3_glm53_decode / selected_native_fusion | a3_glm53_decode | `ed5e9696949d51c2d1d31ab099a71a2c98722d5719f004fcf90c9ceff036f60c` | not_projected |
| a3_glm53_decode_shared_quant / source_shared_int32_conditional | a3_glm53_decode | `ed5e9696949d51c2d1d31ab099a71a2c98722d5719f004fcf90c9ceff036f60c` | not_projected |
| a3_qwen35 / case_default | a3_qwen35 | `2c2fb28ab36674f8eaef52042e1350a949a972225b4d4c5f52da1fe27fa58b53` | not_projected |
| a3_qwen35_paged_prefill_q8192 / paged_body_geometry_conditional | a3_qwen35 | `2c2fb28ab36674f8eaef52042e1350a949a972225b4d4c5f52da1fe27fa58b53` | not_projected |
| a3_qwen35_paged_decode_q1 / paged_body_geometry_conditional | a3_qwen35 | `2c2fb28ab36674f8eaef52042e1350a949a972225b4d4c5f52da1fe27fa58b53` | not_projected |
| a3_qwen35_paged_decode_q2 / paged_body_geometry_conditional | a3_qwen35 | `2c2fb28ab36674f8eaef52042e1350a949a972225b4d4c5f52da1fe27fa58b53` | not_projected |
| a3_qwen36 / case_default | a3_qwen36 | `797260bd9ea48a7fb75831c397a6c0716be11233f4df953d299e5bdf99084d7f` | not_projected |
| a3_qwen36_paged_prefill_q8192 / paged_body_geometry_conditional | a3_qwen36 | `797260bd9ea48a7fb75831c397a6c0716be11233f4df953d299e5bdf99084d7f` | not_projected |
| a3_qwen36_paged_decode_q1 / paged_body_geometry_conditional | a3_qwen36 | `797260bd9ea48a7fb75831c397a6c0716be11233f4df953d299e5bdf99084d7f` | not_projected |
| a3_qwen36_paged_decode_q4 / paged_body_geometry_conditional | a3_qwen36 | `797260bd9ea48a7fb75831c397a6c0716be11233f4df953d299e5bdf99084d7f` | not_projected |
| a3_v4f / case_default | a3_v4f | `b56b7439213cc9f76eaae63347393d4add6ae5c985bf28a6a7737f5783c81788` | not_projected |
| a3_v4f / selected_native_fusion | a3_v4f | `b56b7439213cc9f76eaae63347393d4add6ae5c985bf28a6a7737f5783c81788` | not_projected |
| a3_v4f_compressor_fp32 / source_compressor_fp32_conditional_reference | a3_v4f | `b56b7439213cc9f76eaae63347393d4add6ae5c985bf28a6a7737f5783c81788` | not_projected |
| a3_v4f_shared_quant / source_shared_int32_conditional | a3_v4f | `b56b7439213cc9f76eaae63347393d4add6ae5c985bf28a6a7737f5783c81788` | not_projected |
| a3_v4pro / case_default | a3_v4pro | `5ffe5625942e4caf787ce047438576527b8513452d6dd6871b24682a19968abd` | not_projected |
| a3_v4pro / selected_native_fusion | a3_v4pro | `5ffe5625942e4caf787ce047438576527b8513452d6dd6871b24682a19968abd` | not_projected |
| a3_v4pro_compressor_fp32 / source_compressor_fp32_conditional_reference | a3_v4pro | `5ffe5625942e4caf787ce047438576527b8513452d6dd6871b24682a19968abd` | not_projected |
| a5_kimi_k3 / case_default | a5_kimi_k3 | `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648` | not_projected |
| a5_kimi_k3_decode / source_declared_unfused_reference | a5_kimi_k3 | `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648` | not_projected |
| a5_kimi_k3_checkpoint / current_checkpoint_conditional | a5_kimi_k3 | `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648` | not_projected |
| a5_kimi_k3_decode_checkpoint / current_checkpoint_conditional | a5_kimi_k3 | `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648` | not_projected |
| a5_kimi_k3_checkpoint_eager_single_group / source_single_group_mxfp8_conditional | a5_kimi_k3 | `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648` | not_projected |
| a5_kimi_k3_decode_checkpoint_eager_single_group / source_single_group_mxfp8_conditional | a5_kimi_k3 | `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648` | not_projected |
| a5_kimi_k3_checkpoint_eager_single_group_sp / source_sp_single_group_mxfp8_conditional | a5_kimi_k3 | `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648` | not_projected |
| a5_qwen38 / case_default | a5_qwen38 | `ec7fbcff6138d06fd7d0ed20497d8d4af2f78a179372db976090d4206a3d17ca` | not_projected |
| a5_qwen38_steady / selected_steady_matrix_conditional | a5_qwen38 | `ec7fbcff6138d06fd7d0ed20497d8d4af2f78a179372db976090d4206a3d17ca` | not_projected |
| a5_qwen38_paged_prefill_q16384 / paged_body_geometry_conditional | a5_qwen38 | `ec7fbcff6138d06fd7d0ed20497d8d4af2f78a179372db976090d4206a3d17ca` | not_projected |
| a5_qwen38_paged_decode_q1 / paged_body_geometry_conditional | a5_qwen38 | `ec7fbcff6138d06fd7d0ed20497d8d4af2f78a179372db976090d4206a3d17ca` | not_projected |
| a5_qwen38_paged_decode_q4 / paged_body_geometry_conditional | a5_qwen38 | `ec7fbcff6138d06fd7d0ed20497d8d4af2f78a179372db976090d4206a3d17ca` | not_projected |
| a5_qwen38_paged_decode_q1_staged / source_paged_decode_program_conditional | a5_qwen38 | `ec7fbcff6138d06fd7d0ed20497d8d4af2f78a179372db976090d4206a3d17ca` | not_projected |
| a5_qwen38_paged_decode_q4_staged / source_paged_decode_program_conditional | a5_qwen38 | `ec7fbcff6138d06fd7d0ed20497d8d4af2f78a179372db976090d4206a3d17ca` | not_projected |
