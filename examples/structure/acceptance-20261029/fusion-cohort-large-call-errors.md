# Large-Call Failed Cohorts

Selection: status=compared, accuracy_tier=relative_15pct, accuracy_pass=false. Observed complete-event mean > 50 us; absolute relative error > 15%.
Sort: `observed_activity_ms_descending; declaration_variant_cohort_id_tiebreak`. JSON retains all 109 failed cohorts; this table shows the first 30.

Receipt SHA256: `27c84748367ab934e66106b2b3c4aa55ee85f0a7809869e7300b94a550f1f0b9`.
Script SHA256: `170f3b387694ecbf826bf1281caefdbb2693ecec6dd5e605b14caddf4d229323`.

Each observed call is one captured native profiler event. The prediction boundary is reported separately. Contract positions and stored tensor shapes/dtypes are shown verbatim; excluded fields remain subject to contract_scope in JSON.
Variant totals reuse captures. Activity sums can overlap and are not full-model latency. A homogeneous cohort does not identify a layer, invocation, or DP replica.

| # | Declaration / variant | Native / cohort suffix | Calls | Observed mean / p50 us | Predicted us | Signed / abs diff us | Relative | Signed / abs total gap ms | Prediction boundary / single program | Saved tensor contract |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | a3_glm53_prefill / selected_native_fusion | SparseFlashAttention / 542edf3818da | 78 | 13199.665 / 13208.966 | 6121.175 | -7078.489 / 7078.489 | -53.63% | -552.122 / 552.122 | semantic_device_program / True | `["sparse_attention_active","SparseFlashAttention",[[[4096,8,512],"bf16","ND"],[[4096,8,64],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"],[[1,64],"bf16","ND"]],[[4096,8,512],"bf16","ND"]]` |
| 2 | a3_glm53_prefill / source_declared_unfused_reference | SparseFlashAttention / 1b1064dfab35 | 78 | 13199.665 / 13208.966 | 6121.175 | -7078.489 / 7078.489 | -53.63% | -552.122 / 552.122 | semantic_device_program / True | `["sparse_attention_active","SparseFlashAttention",[[[4096,8,512],"bf16","ND"],[[4096,8,64],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"],[[1,64],"bf16","ND"]],[[4096,8,512],"bf16","ND"]]` |
| 3 | a3_glm53_decode / selected_native_fusion | SparseFlashAttention / ecae7f7c3a2b | 5772 | 90.731 / 90.319 | 1.987 | -88.743 / 88.743 | -97.81% | -512.226 / 512.226 | semantic_device_program / True | `["sparse_attention_active","SparseFlashAttention",[[[1,8,512],"bf16","ND"],[[1,8,64],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"],[[1,64],"bf16","ND"]],[[1,8,512],"bf16","ND"]]` |
| 4 | a3_glm53_decode / source_declared_unfused_reference | SparseFlashAttention / cf44fc3ac641 | 5772 | 90.731 / 90.319 | 5.000 | -85.731 / 85.731 | -94.49% | -494.838 / 494.838 | semantic_device_program / True | `["sparse_attention_active","SparseFlashAttention",[[[1,8,512],"bf16","ND"],[[1,8,64],"bf16","ND"]],[[[1,512],"bf16","ND"],[[1,512],"bf16","ND"],[[1,64],"bf16","ND"]],[[1,8,512],"bf16","ND"]]` |
| 5 | a3_glm53_decode / selected_native_fusion | GroupedMatmulSwigluQuantV2 / b37bb16a059a | 5550 | 88.039 / 86.478 | 10.756 | -77.283 / 77.283 | -87.78% | -428.919 / 428.919 | semantic_device_program / True | `["grouped_mlp_parameters_active","GroupedMatmulSwigluQuantV2",[256,6144,256],["int8","int4","int8"]]` |
| 6 | a5_kimi_k3_decode_checkpoint / current_checkpoint_conditional | SituMxQuant / 0c1fe00eaf00 | 6898 | 65.134 / 64.697 | 0.002 | -65.132 / 65.132 | -100.00% | -449.283 / 449.283 | semantic_device_program / True | `["situ_mxquant_active","SituMxQuant",[[1,1536],"bf16","ND"],[[1,768],"fp8_e4m3","ND"],[[1,12,2],"fp8_e8m0","ND"]]` |
| 7 | a5_qwen38 / case_default | QuantBatchMatmulV3 / 7d9306ad5205 | 64 | 6770.419 / 6770.202 | 11925.185 | +5154.766 / 5154.766 | +76.14% | +329.905 / 329.905 | semantic_device_program / True | `["matrix",[16384,34816,5120],"fp8_e4m3","fp8_e4m3","bf16",[16384,80,2],"fp8_e8m0"]` |
| 8 | a5_qwen38 / case_default | MatMulV3 / 216ecf09d79c | 48 | 6375.719 / 6375.468 | 10762.600 | +4386.881 / 4386.881 | +68.81% | +210.570 / 210.570 | semantic_device_program / True | `["matrix",[16384,16384,5120],"bf16","bf16","bf16",[],""]` |
| 9 | a3_glm53_decode / selected_native_fusion | GroupedMatmul / c70bd4c562e1 | 5550 | 52.907 / 51.539 | 6.152 | -46.755 / 46.755 | -88.37% | -259.493 / 259.493 | semantic_device_program / True | `["grouped_matrix",[256,8,6144,256],"int8","int4","bf16",[8],"fp32"]` |
| 10 | a5_qwen38 / case_default | QuantBatchMatmulV3 / b6debf48bfc2 | 64 | 3392.825 / 3392.483 | 5906.295 | +2513.470 / 2513.470 | +74.08% | +160.862 / 160.862 | semantic_device_program / True | `["matrix",[16384,5120,17408],"fp8_e4m3","fp8_e4m3","bf16",[16384,272,2],"fp8_e8m0"]` |
| 11 | a5_qwen38 / case_default | FusedInferAttentionScore / 89922200818e | 17 | 12573.041 / 12574.640 | 7626.473 | -4946.568 / 4946.568 | -39.34% | -84.092 / 84.092 | semantic_device_program / True | `["attention_active_qkv","FusedInferAttentionScore",[[[16384,24,256],"bf16","ND"],[[16384,4,256],"bf16","ND"],[[16384,4,256],"bf16","ND"]],[[[16384,24,256],"bf16","ND"]]]` |
| 12 | a5_qwen38 / case_default | MatMulV3 / 3a2be000f5af | 51 | 2394.718 / 2394.683 | 4034.762 | +1640.043 / 1640.043 | +68.49% | +83.642 / 83.642 | semantic_device_program / True | `["matrix",[16384,5120,6144],"bf16","bf16","bf16",[],""]` |
| 13 | a3_v4pro / case_default | HcPost / 078648060a0d | 496 | 202.098 / 202.126 | 110.169 | -91.930 / 91.930 | -45.49% | -45.597 / 45.597 | semantic_device_program / True | `["hyper_connection_active","HcPost",[[[1024,7168],"bf16","ND"],[[1024,4,7168],"bf16","ND"],[[1024,4],"fp32","ND"],[[1024,4,4],"fp32","ND"]],[[[1024,4,7168],"bf16","ND"]]]` |
| 14 | a3_v4pro / selected_native_fusion | HcPost / 47567f4eb87f | 496 | 202.098 / 202.126 | 129.751 | -72.348 / 72.348 | -35.80% | -35.885 / 35.885 | semantic_device_program / True | `["hyper_connection_active","HcPost",[[[1024,7168],"bf16","ND"],[[1024,4,7168],"bf16","ND"],[[1024,4],"fp32","ND"],[[1024,4,4],"fp32","ND"]],[[[1024,4,7168],"bf16","ND"]]]` |
| 15 | a3_v4pro / selected_native_fusion | HcPre / b56509c134ee | 496 | 191.803 / 193.156 | 316.457 | +124.653 / 124.653 | +64.99% | +61.828 / 61.828 | semantic_device_program / True | `["hyper_connection_active","HcPre",[[[1024,4,7168],"bf16","ND"],[[24,28672],"fp32","ND"],[[3],"fp32","ND"],[[24],"fp32","ND"]],[[[1024,7168],"bf16","ND"],[[1024,4],"fp32","ND"],[[1024,4,4],"fp32","ND"]]]` |
| 16 | a3_glm53_prefill / selected_native_fusion | GroupedMatmul / 0a6c5aa341d0 | 75 | 1225.255 / 1219.896 | 1894.139 | +668.884 / 668.884 | +54.59% | +50.166 / 50.166 | semantic_device_program / True | `["grouped_matrix",[256,32768,6144,256],"int8","int4","bf16",[32768],"fp32"]` |
| 17 | a5_qwen38 / case_default | ChunkGatedDeltaRuleFwdPrepare / 5c107df89221 | 48 | 1540.079 / 1539.949 | 1228.428 | -311.651 / 311.651 | -20.24% | -14.959 / 14.959 | semantic_device_program / True | `["ChunkGatedDeltaRuleFwdPrepare",[[1,16,16384,128],[1,16,16384,128],[1,48,16384,128],[1,48,16384],[1,48,16384],[2],[512]],[[1,48,16384],[1,48,16384,128],[1,48,16384,128],[1,48,16384,64],[1,16,16384,128],[1,16,16384,128],[1,16,16384],[1,16,16384],[1,48,16384]],["bf16","bf16","bf16","fp32","... [full contract in JSON]` |
| 18 | a3_glm53_prefill / selected_native_fusion | MlaPrologV3 / bbf395bf49ac | 57 | 1248.166 / 1249.035 | 451.382 | -796.784 / 796.784 | -63.84% | -45.417 / 45.417 | semantic_device_program / True | `["mla_prolog_active","MlaPrologV3",[[4096,6144],"int8","ND"],[[[6144,2048],"int8"],[[2048,2048],"int8"],[[8,192,512],"bf16"],[[6144,576],"int8"],[[2048],"bf16"],[[512],"bf16"]],[[[1,512],"bf16","ND"],[[1,64],"bf16","ND"]],[[[4096,8,512],"bf16","ND"],[[4096,8,64],"bf16","ND"],[[],null,null]]]` |
| 19 | a3_qwen35 / case_default | GroupedMatmul / 0e4f36908a3b | 80 | 689.328 / 690.584 | 322.728 | -366.599 / 366.599 | -53.18% | -29.328 / 29.328 | semantic_device_program / True | `["grouped_matrix",[256,65536,2048,128],"int8","int8","bf16",[65536],"fp32"]` |
| 20 | a5_kimi_k3_checkpoint / current_checkpoint_conditional | SituMxQuant / 856b244c2fce | 368 | 147.124 / 79.740 | 14.953 | -132.172 / 132.172 | -89.84% | -48.639 / 48.639 | semantic_device_program / True | `["situ_mxquant_active","SituMxQuant",[[8192,1536],"bf16","ND"],[[8192,768],"fp8_e4m3","ND"],[[8192,12,2],"fp8_e8m0","ND"]]` |
| 21 | a5_kimi_k3_checkpoint / current_checkpoint_conditional | DynamicMxQuant / b3ceb1b6cb36 | 744 | 71.230 / 70.787 | 44.499 | -26.731 / 26.731 | -37.53% | -19.888 / 19.888 | semantic_device_program / True | `["DynamicMxQuant",[8192,7168],"bf16","fp8_e4m3",[8192,112,2],"fp8_e8m0"]` |
| 22 | a5_qwen38 / case_default | QuantBatchMatmulV3 / 6ce7bb626c5b | 16 | 2790.927 / 2790.525 | 4910.529 | +2119.602 / 2119.602 | +75.95% | +33.914 / 33.914 | semantic_device_program / True | `["matrix",[16384,14336,5120],"fp8_e4m3","fp8_e4m3","bf16",[16384,80,2],"fp8_e8m0"]` |
| 23 | a5_kimi_k3 / case_default | MatMulV3 / 72dff4755bf4 | 96 | 425.070 / 425.021 | 706.323 | +281.253 / 281.253 | +66.17% | +27.000 / 27.000 | semantic_device_program / True | `["matrix",[8192,1536,7168],"bf16","bf16","bf16",[],""]` |
| 24 | a5_kimi_k3_checkpoint / current_checkpoint_conditional | MatMulV3 / 34b20ca9d879 | 96 | 425.070 / 425.021 | 706.323 | +281.253 / 281.253 | +66.17% | +27.000 / 27.000 | semantic_device_program / True | `["matrix",[8192,1536,7168],"bf16","bf16","bf16",[],""]` |
| 25 | a3_v4f / selected_native_fusion | HcPre / 4f3328e62760 | 88 | 431.534 / 430.531 | 721.545 | +290.011 / 290.011 | +67.20% | +25.521 / 25.521 | semantic_device_program / True | `["hyper_connection_active","HcPre",[[[4096,4,4096],"bf16","ND"],[[24,16384],"fp32","ND"],[[3],"fp32","ND"],[[24],"fp32","ND"]],[[[4096,4096],"bf16","ND"],[[4096,4],"fp32","ND"],[[4096,4,4],"fp32","ND"]]]` |
| 26 | a3_glm53_prefill / selected_native_fusion | AddRmsNormBias / 384f73111f32 | 153 | 247.871 / 248.955 | 167.806 | -80.065 / 80.065 | -32.30% | -12.250 / 12.250 | semantic_device_program / True | `["native_tensor_abi","AddRmsNormBias",[[[4096,6144],"bf16","ND"],[[4096,6144],"bf16","ND"],[[6144],"bf16","ND"],[[6144],"bf16","ND"]],[[[4096,6144],"bf16","ND"],[[4096,1],"fp32","ND"],[[4096,6144],"bf16","ND"]]]` |
| 27 | a3_glm53_prefill / source_declared_unfused_reference | AddRmsNormBias / e8fe342fb3b6 | 153 | 247.871 / 248.955 | 167.806 | -80.065 / 80.065 | -32.30% | -12.250 / 12.250 | semantic_device_program / True | `["native_tensor_abi","AddRmsNormBias",[[[4096,6144],"bf16","ND"],[[4096,6144],"bf16","ND"],[[6144],"bf16","ND"],[[6144],"bf16","ND"]],[[[4096,6144],"bf16","ND"],[[4096,1],"fp32","ND"],[[4096,6144],"bf16","ND"]]]` |
| 28 | a5_kimi_k3 / case_default | layer_norm_gated_fwd_kernel / 34d2c585f1bb | 276 | 136.262 / 136.218 | 18.874 | -117.388 / 117.388 | -86.15% | -32.399 / 32.399 | semantic_device_program / True | `["gated_norm_active_rows","layer_norm_gated_fwd_kernel",[[98304,128],"bf16","ND"],[[128],"bf16","ND"]]` |
| 29 | a5_kimi_k3_checkpoint / current_checkpoint_conditional | layer_norm_gated_fwd_kernel / 21b3f1fdc980 | 276 | 136.262 / 136.218 | 18.874 | -117.388 / 117.388 | -86.15% | -32.399 / 32.399 | semantic_device_program / True | `["gated_norm_active_rows","layer_norm_gated_fwd_kernel",[[98304,128],"bf16","ND"],[[128],"bf16","ND"]]` |
| 30 | a3_v4f / case_default | HcPost / 1bcd6bfd65cd | 88 | 418.375 / 418.062 | 251.931 | -166.444 / 166.444 | -39.78% | -14.647 / 14.647 | semantic_device_program / True | `["hyper_connection_active","HcPost",[[[4096,4096],"bf16","ND"],[[4096,4,4096],"bf16","ND"],[[4096,4],"fp32","ND"],[[4096,4,4],"fp32","ND"]],[[[4096,4,4096],"bf16","ND"]]]` |

## Reference Costs Excluded From Accuracy

32 reference cohorts / 64916 observed calls. These are not passing comparisons.

| Reason | Cohorts | Calls | Observed activity ms | Predicted reference ms |
| --- | ---: | ---: | ---: | ---: |
| mxfp4_native_execution_unmodeled | 6 | 29063 | 1764.757 | 82697.332 |
| quantized_epilogue_unmodeled | 6 | 11746 | 1169.609 | 600.411 |
| unfused_subgraph_is_not_the_observed_native_kernel | 20 | 24107 | 951.917 | 2128.866 |

## Case Evidence And Model Coverage

Model coverage is copied only when present in the saved comparison. `not_projected` does not mean complete; this report makes no additional sim calls.

| Declaration / variant | Capture | Recorded raw source SHA256 | Model coverage |
| --- | --- | --- | --- |
| a3_glm53_prefill / source_declared_unfused_reference | a3_glm53_prefill | `ded3a03adc7a82b0801acc6a88bb85589b8f3a3f3a4a416a1322ebfb514c614f` | not_projected |
| a3_glm53_prefill / selected_native_fusion | a3_glm53_prefill | `ded3a03adc7a82b0801acc6a88bb85589b8f3a3f3a4a416a1322ebfb514c614f` | not_projected |
| a3_glm53_decode / source_declared_unfused_reference | a3_glm53_decode | `ed5e9696949d51c2d1d31ab099a71a2c98722d5719f004fcf90c9ceff036f60c` | not_projected |
| a3_glm53_decode / selected_native_fusion | a3_glm53_decode | `ed5e9696949d51c2d1d31ab099a71a2c98722d5719f004fcf90c9ceff036f60c` | not_projected |
| a3_qwen35 / case_default | a3_qwen35 | `2c2fb28ab36674f8eaef52042e1350a949a972225b4d4c5f52da1fe27fa58b53` | not_projected |
| a3_qwen36 / case_default | a3_qwen36 | `797260bd9ea48a7fb75831c397a6c0716be11233f4df953d299e5bdf99084d7f` | not_projected |
| a3_v4f / case_default | a3_v4f | `b56b7439213cc9f76eaae63347393d4add6ae5c985bf28a6a7737f5783c81788` | not_projected |
| a3_v4f / selected_native_fusion | a3_v4f | `b56b7439213cc9f76eaae63347393d4add6ae5c985bf28a6a7737f5783c81788` | not_projected |
| a3_v4pro / case_default | a3_v4pro | `5ffe5625942e4caf787ce047438576527b8513452d6dd6871b24682a19968abd` | not_projected |
| a3_v4pro / selected_native_fusion | a3_v4pro | `5ffe5625942e4caf787ce047438576527b8513452d6dd6871b24682a19968abd` | not_projected |
| a5_kimi_k3 / case_default | a5_kimi_k3 | `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648` | not_projected |
| a5_kimi_k3_decode / source_declared_unfused_reference | a5_kimi_k3 | `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648` | not_projected |
| a5_kimi_k3_checkpoint / current_checkpoint_conditional | a5_kimi_k3 | `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648` | not_projected |
| a5_kimi_k3_decode_checkpoint / current_checkpoint_conditional | a5_kimi_k3 | `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648` | not_projected |
| a5_qwen38 / case_default | a5_qwen38 | `ec7fbcff6138d06fd7d0ed20497d8d4af2f78a179372db976090d4206a3d17ca` | not_projected |
