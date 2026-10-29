# Kimi 主体算子活动量：按结构区域排列

完整主体主几何内的原生事件按结构区域分组，每组按实测活动毫秒/Forward降序排列。
活动量是事件时长之和，包含真实通信等待且可能跨 stream 重叠，不能相加当作主体跨度。未匹配不等于 Sim 漏算；完整成本/契约覆盖见全族表。

## a3_kimi4_tp8_w4a8_c1 / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| reduce_scatterAicpuKernel / unresolved | 969 | 174.605 | 0.666110 | 0 / 2032 |
| hcom_allGather_ / attention_output_communication | 762 | 150.598 | 0.451793 | 0 / 1016 |
| MatMulV2 / unresolved | 1524 | 37.351 | 0.224105 | 0 / 2032 |
| QuantBatchMatmulV3 / unresolved | 762 | 34.244 | 0.102733 | 0 / 2794 |
| hcom_reduceScatter_ / attention_output_communication | 762 | 28.789 | 0.086368 | 0 / 1016 |
| RecurrentKda / unresolved | 762 | 17.320 | 0.051960 | 0 / 762 |
| PadV3 / unresolved | 762 | 15.624 | 0.046873 | 0 / 2286 |
| CausalConv1d / unresolved | 762 | 11.275 | 0.033825 | 0 / 762 |
| AttnResFwd / unresolved | 762 | 8.741 | 0.026224 | 0 / 2286 |
| MemSet / unresolved | 762 | 8.714 | 0.026142 | 0 / 2286 |
| DynamicQuant / unresolved | 762 | 3.173 | 0.009520 | 0 / 1270 |
| layer_norm_gated_fwd_kernel / unresolved | 762 | 2.406 | 0.007219 | 0 / 762 |
| ZerosLike / unresolved | 762 | 1.498 | 0.004493 | 0 / 1016 |
| Sigmoid / unresolved | 762 | 1.338 | 0.004013 | 0 / 1270 |
| Cast / unresolved | 762 | 1.294 | 0.003883 | 0 / 1524 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| reduce_scatterAicpuKernel / unresolved | 172 | 169.621 | 0.114862 | 0 / 2032 |
| MatMulV2 / unresolved | 508 | 27.676 | 0.055352 | 0 / 2032 |
| hcom_allGather_ / attention_output_communication | 254 | 43.048 | 0.043048 | 0 / 1016 |
| FusedInferAttentionScore / unresolved | 254 | 36.842 | 0.036842 | 0 / 254 |
| QuantBatchMatmulV3 / unresolved | 508 | 17.828 | 0.035656 | 0 / 2794 |
| PadV3 / unresolved | 762 | 10.631 | 0.031894 | 0 / 2286 |
| hcom_reduceScatter_ / attention_output_communication | 254 | 27.879 | 0.027879 | 0 / 1016 |
| MemSet / unresolved | 762 | 6.782 | 0.020347 | 0 / 2286 |
| TransposeBatchMatMul / unresolved | 254 | 12.738 | 0.012738 | 0 / 254 |
| AttnResFwd / unresolved | 254 | 9.848 | 0.009848 | 0 / 2286 |
| RmsNorm / unresolved | 508 | 4.905 | 0.009811 | 0 / 508 |
| BatchMatMulV2 / unresolved | 254 | 7.695 | 0.007695 | 0 / 254 |
| DynamicQuant / unresolved | 508 | 2.780 | 0.005560 | 0 / 1270 |
| Slice / unresolved | 508 | 2.278 | 0.004556 | 0 / 1016 |
| ScatterPaKvCache / unresolved | 254 | 2.443 | 0.002443 | 0 / 254 |
| Mul / unresolved | 254 | 1.947 | 0.001947 | 0 / 1270 |
| Sigmoid / unresolved | 254 | 1.683 | 0.001683 | 0 / 1270 |
| ZerosLike / unresolved | 254 | 1.565 | 0.001565 | 0 / 1016 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| reduce_scatterAicpuKernel / unresolved | 871 | 168.863 | 0.579055 | 0 / 2032 |
| hcom_allGather_ / ffn_down_communication | 762 | 58.084 | 0.174251 | 0 / 1270 |
| GroupedMatmul / expert_up | 508 | 55.952 | 0.111904 | 0 / 762 |
| MoeDistributeDispatchV2 / unresolved | 508 | 53.834 | 0.107668 | 0 / 762 |
| hcom_reduceScatter_ / ffn_down_communication | 762 | 28.257 | 0.084772 | 0 / 1016 |
| GroupedMatmul / expert_down | 508 | 38.343 | 0.076687 | 0 / 762 |
| QuantBatchMatmulV3 / unresolved | 1016 | 15.887 | 0.063549 | 0 / 2794 |
| hcom_allGather_ / ffn_down_communication | 508 | 29.597 | 0.059194 | 0 / 1270 |
| QuantBatchMatmulV3 / latent_down | 508 | 29.285 | 0.058571 | 762 / 762 |
| QuantBatchMatmulV3 / latent_up | 508 | 28.849 | 0.057698 | 762 / 762 |
| QuantBatchMatmulV3 / gate_up | 254 | 56.548 | 0.056548 | 254 / 254 |
| MoeDistributeDispatchV2 / unresolved | 254 | 55.451 | 0.055451 | 0 / 762 |
| GroupedMatmul / expert_up | 254 | 55.262 | 0.055262 | 0 / 762 |
| MoeDistributeCombineV2 / unresolved | 508 | 22.735 | 0.045469 | 0 / 762 |
| MatMulV3 / unresolved | 508 | 21.772 | 0.043544 | 0 / 762 |
| DequantSituQuant / unresolved | 1016 | 10.559 | 0.042235 | 0 / 1524 |
| GroupedMatmul / expert_down | 254 | 39.504 | 0.039504 | 0 / 762 |
| QuantBatchMatmulV3 / down | 254 | 35.765 | 0.035765 | 254 / 254 |
| PadV3 / unresolved | 508 | 16.783 | 0.033566 | 0 / 2286 |
| ForeachAddList / unresolved | 508 | 16.416 | 0.032832 | 0 / 762 |
| AttnResFwd / unresolved | 762 | 10.447 | 0.031340 | 0 / 2286 |
| QuantBatchMatmulV3 / unresolved | 508 | 15.573 | 0.031146 | 0 / 2794 |
| QuantBatchMatmulV3 / latent_down | 254 | 29.008 | 0.029008 | 762 / 762 |
| QuantBatchMatmulV3 / latent_up | 254 | 28.020 | 0.028020 | 762 / 762 |
| hcom_reduceScatter_ / ffn_down_communication | 254 | 22.814 | 0.022814 | 0 / 1016 |
| MatMulV3 / unresolved | 254 | 21.334 | 0.021334 | 0 / 762 |
| DequantSituQuant / unresolved | 508 | 10.417 | 0.020834 | 0 / 1524 |
| AttnResFwd / unresolved | 508 | 10.034 | 0.020069 | 0 / 2286 |
| Mul / unresolved | 1016 | 4.746 | 0.018985 | 0 / 1270 |
| MemSet / unresolved | 508 | 8.867 | 0.017735 | 0 / 2286 |
| PadV3 / unresolved | 254 | 16.370 | 0.016370 | 0 / 2286 |
| ForeachAddList / unresolved | 254 | 16.303 | 0.016303 | 0 / 762 |
| MoeDistributeCombineV2 / unresolved | 254 | 15.333 | 0.015333 | 0 / 762 |
| Cast / unresolved | 762 | 4.945 | 0.014836 | 0 / 1524 |
| reduce_scatterAicpuKernel / unresolved | 20 | 180.843 | 0.014240 | 0 / 2032 |
| DynamicQuant / latent_down.quantize | 1016 | 3.068 | 0.012272 | 1524 / 1524 |
| RealDiv / unresolved | 508 | 5.441 | 0.010883 | 0 / 508 |
| Tanh / unresolved | 508 | 5.376 | 0.010753 | 0 / 508 |
| MoeGatingTopK / unresolved | 508 | 5.103 | 0.010205 | 0 / 762 |
| MemSet / unresolved | 254 | 8.865 | 0.008865 | 0 / 2286 |
| Index / unresolved | 254 | 8.173 | 0.008173 | 0 / 254 |
| RmsNorm / latent_norm | 508 | 4.062 | 0.008124 | 762 / 762 |
| DynamicQuant / latent_down.quantize | 508 | 3.314 | 0.006627 | 1524 / 1524 |
| Sigmoid / unresolved | 254 | 6.480 | 0.006480 | 0 / 1270 |
| DynamicQuant / latent_up.quantize | 508 | 2.671 | 0.005343 | 762 / 762 |
| Slice / unresolved | 508 | 2.513 | 0.005026 | 0 / 1016 |
| MoeGatingTopK / unresolved | 254 | 4.704 | 0.004704 | 0 / 762 |
| DynamicQuant / gate_up.quantize | 254 | 4.649 | 0.004649 | 254 / 254 |
| DynamicQuant / down.quantize | 254 | 4.452 | 0.004452 | 254 / 254 |
| RmsNorm / latent_norm | 254 | 3.278 | 0.003278 | 762 / 762 |
| IndexCheck / unresolved | 254 | 2.790 | 0.002790 | 0 / 254 |
| DynamicQuant / latent_up.quantize | 254 | 2.599 | 0.002599 | 762 / 762 |

## a3_kimi4_tp8_w4a8_c16 / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| reduce_scatterAicpuKernel / unresolved | 885 | 171.709 | 0.646650 | 0 / 1880 |
| hcom_allGather_ / attention_output_communication | 705 | 133.486 | 0.400457 | 0 / 940 |
| MatMulV2 / unresolved | 705 | 61.218 | 0.183653 | 0 / 705 |
| RecurrentKda / unresolved | 705 | 59.769 | 0.179308 | 0 / 705 |
| QuantBatchMatmulV3 / unresolved | 705 | 33.722 | 0.101165 | 0 / 1645 |
| MatMulV2 / linear_output | 705 | 32.512 | 0.097535 | 705 / 705 |
| hcom_reduceScatter_ / attention_output_communication | 705 | 22.253 | 0.066758 | 0 / 940 |
| CausalConv1d / unresolved | 705 | 17.706 | 0.053119 | 0 / 705 |
| AttnResFwd / unresolved | 705 | 9.603 | 0.028808 | 0 / 2115 |
| layer_norm_gated_fwd_kernel / unresolved | 705 | 7.316 | 0.021949 | 0 / 705 |
| ZerosLike / unresolved | 705 | 5.981 | 0.017944 | 0 / 940 |
| DynamicQuant / linear_q.quantize | 705 | 5.025 | 0.015076 | 705 / 705 |
| AsStrided / unresolved | 705 | 4.259 | 0.012777 | 0 / 940 |
| Slice / unresolved | 705 | 4.233 | 0.012698 | 0 / 2350 |
| Sigmoid / unresolved | 705 | 1.650 | 0.004950 | 0 / 1175 |
| Cast / unresolved | 705 | 1.363 | 0.004090 | 0 / 1410 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| FusedInferAttentionScore / unresolved | 235 | 159.143 | 0.159143 | 0 / 235 |
| MatMulV2 / output_gate | 235 | 31.337 | 0.031337 | 235 / 235 |
| MatMulV2 / output | 235 | 28.446 | 0.028446 | 235 / 235 |
| hcom_allGather_ / attention_output_communication | 235 | 26.072 | 0.026072 | 0 / 940 |
| PadV3 / unresolved | 470 | 12.608 | 0.025216 | 0 / 470 |
| QuantBatchMatmulV3 / unresolved | 235 | 23.856 | 0.023856 | 0 / 1645 |
| hcom_reduceScatter_ / attention_output_communication | 235 | 20.707 | 0.020707 | 0 / 940 |
| Transpose / unresolved | 235 | 20.407 | 0.020407 | 0 / 235 |
| RmsNorm / unresolved | 470 | 7.485 | 0.014970 | 0 / 470 |
| MemSet / unresolved | 470 | 7.158 | 0.014316 | 0 / 470 |
| TransposeBatchMatMul / v_expand | 235 | 13.460 | 0.013460 | 235 / 235 |
| QuantBatchMatmulV3 / q_b | 235 | 12.942 | 0.012942 | 235 / 235 |
| Slice / unresolved | 1175 | 2.547 | 0.012735 | 0 / 2350 |
| AttnResFwd / unresolved | 235 | 10.045 | 0.010045 | 0 / 2115 |
| BatchMatMulV2 / unresolved | 235 | 8.370 | 0.008370 | 0 / 235 |
| Mul / unresolved | 235 | 6.328 | 0.006328 | 0 / 1175 |
| ZerosLike / unresolved | 235 | 5.603 | 0.005603 | 0 / 940 |
| AsStrided / unresolved | 235 | 5.530 | 0.005530 | 0 / 940 |
| Sigmoid / unresolved | 235 | 5.428 | 0.005428 | 0 / 1175 |
| DynamicQuant / q_b.quantize | 235 | 5.267 | 0.005267 | 235 / 235 |
| ScatterPaKvCache / unresolved | 235 | 5.110 | 0.005110 | 0 / 235 |
| DynamicQuant / q_a.quantize | 235 | 5.051 | 0.005051 | 235 / 235 |
| reduce_scatterAicpuKernel / unresolved | 1 | 167.876 | 0.000714 | 0 / 1880 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| reduce_scatterAicpuKernel / unresolved | 994 | 169.957 | 0.718881 | 0 / 1880 |
| GroupedMatmul / expert_up | 470 | 327.510 | 0.655020 | 0 / 705 |
| GroupedMatmul / expert_down | 470 | 170.491 | 0.340982 | 0 / 705 |
| GroupedMatmul / expert_up | 235 | 318.357 | 0.318357 | 0 / 705 |
| DequantSituQuant / unresolved | 940 | 44.924 | 0.179695 | 0 / 1410 |
| GroupedMatmul / expert_down | 235 | 165.905 | 0.165905 | 0 / 705 |
| hcom_allGather_ / ffn_down_communication | 705 | 53.052 | 0.159156 | 0 / 1175 |
| MoeDistributeDispatchV2 / unresolved | 470 | 55.749 | 0.111497 | 0 / 705 |
| DequantSituQuant / unresolved | 470 | 44.503 | 0.089007 | 0 / 1410 |
| hcom_reduceScatter_ / ffn_down_communication | 705 | 26.413 | 0.079239 | 0 / 940 |
| MoeDistributeDispatchV2 / unresolved | 235 | 61.544 | 0.061544 | 0 / 705 |
| QuantBatchMatmulV3 / latent_down | 470 | 29.550 | 0.059099 | 705 / 705 |
| QuantBatchMatmulV3 / latent_up | 470 | 28.277 | 0.056555 | 705 / 705 |
| QuantBatchMatmulV3 / gate_up | 235 | 55.989 | 0.055989 | 235 / 235 |
| MoeDistributeCombineV2 / unresolved | 470 | 27.980 | 0.055960 | 0 / 705 |
| MatMulV3 / unresolved | 470 | 25.686 | 0.051372 | 0 / 705 |
| hcom_allGather_ / ffn_down_communication | 470 | 25.666 | 0.051331 | 0 / 1175 |
| MoeDistributeCombineV2 / unresolved | 235 | 39.469 | 0.039469 | 0 / 705 |
| QuantBatchMatmulV3 / unresolved | 470 | 18.923 | 0.037846 | 0 / 1645 |
| QuantBatchMatmulV3 / down | 235 | 35.416 | 0.035416 | 235 / 235 |
| ForeachAddList / unresolved | 470 | 17.602 | 0.035205 | 0 / 705 |
| AttnResFwd / unresolved | 705 | 10.077 | 0.030232 | 0 / 2115 |
| QuantBatchMatmulV3 / latent_down | 235 | 29.352 | 0.029352 | 705 / 705 |
| QuantBatchMatmulV3 / latent_up | 235 | 28.718 | 0.028718 | 705 / 705 |
| QuantBatchMatmulV3 / shared.down | 470 | 13.296 | 0.026593 | 705 / 705 |
| MatMulV3 / unresolved | 235 | 24.778 | 0.024778 | 0 / 705 |
| AttnResFwd / unresolved | 470 | 10.703 | 0.021407 | 0 / 2115 |
| QuantBatchMatmulV3 / unresolved | 235 | 19.323 | 0.019323 | 0 / 1645 |
| Mul / unresolved | 940 | 4.830 | 0.019321 | 0 / 1175 |
| hcom_reduceScatter_ / ffn_down_communication | 235 | 17.577 | 0.017577 | 0 / 940 |
| ForeachAddList / unresolved | 235 | 16.541 | 0.016541 | 0 / 705 |
| Cast / unresolved | 705 | 5.439 | 0.016318 | 0 / 1410 |
| Index / unresolved | 235 | 14.727 | 0.014727 | 0 / 235 |
| QuantBatchMatmulV3 / shared.down | 235 | 13.242 | 0.013242 | 705 / 705 |
| Tanh / unresolved | 470 | 5.961 | 0.011923 | 0 / 470 |
| RealDiv / unresolved | 470 | 5.960 | 0.011920 | 0 / 470 |
| MoeGatingTopK / unresolved | 470 | 5.380 | 0.010759 | 0 / 705 |
| DynamicQuant / shared.gate_up.quantize | 470 | 5.298 | 0.010596 | 705 / 705 |
| RmsNorm / latent_norm | 470 | 4.362 | 0.008724 | 705 / 705 |
| DynamicQuant / latent_down.quantize | 470 | 4.024 | 0.008048 | 705 / 705 |
| Sigmoid / unresolved | 235 | 7.375 | 0.007375 | 0 / 1175 |
| MoeGatingTopK / unresolved | 235 | 5.746 | 0.005746 | 0 / 705 |
| IndexCheck / unresolved | 235 | 5.547 | 0.005547 | 0 / 235 |
| DynamicQuant / shared.gate_up.quantize | 235 | 5.327 | 0.005327 | 705 / 705 |
| DynamicQuant / gate_up.quantize | 235 | 5.280 | 0.005280 | 235 / 235 |
| DynamicQuant / latent_up.quantize | 470 | 2.593 | 0.005186 | 705 / 705 |
| Slice / unresolved | 470 | 2.576 | 0.005153 | 0 / 2350 |
| RmsNorm / latent_norm | 235 | 5.000 | 0.005000 | 705 / 705 |
| DynamicQuant / down.quantize | 235 | 4.547 | 0.004547 | 235 / 235 |
| DynamicQuant / latent_down.quantize | 235 | 3.854 | 0.003854 | 705 / 705 |
| DynamicQuant / latent_up.quantize | 235 | 2.591 | 0.002591 | 705 / 705 |

## a3_kimi4_tp8_w4a8_c32 / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| reduce_scatterAicpuKernel / unresolved | 742 | 169.569 | 0.571910 | 0 / 1760 |
| hcom_allGather_ / attention_output_communication | 660 | 118.346 | 0.355039 | 0 / 880 |
| RecurrentKda / unresolved | 660 | 102.069 | 0.306207 | 0 / 660 |
| MatMulV2 / unresolved | 660 | 65.008 | 0.195025 | 0 / 660 |
| MatMulV2 / linear_output | 660 | 38.618 | 0.115853 | 660 / 660 |
| QuantBatchMatmulV3 / unresolved | 660 | 35.018 | 0.105053 | 0 / 1540 |
| hcom_reduceScatter_ / attention_output_communication | 660 | 22.372 | 0.067117 | 0 / 880 |
| CausalConv1d / unresolved | 660 | 22.027 | 0.066082 | 0 / 660 |
| AttnResFwd / unresolved | 660 | 9.348 | 0.028044 | 0 / 1980 |
| ZerosLike / unresolved | 660 | 8.101 | 0.024304 | 0 / 880 |
| layer_norm_gated_fwd_kernel / unresolved | 660 | 6.586 | 0.019757 | 0 / 660 |
| DynamicQuant / linear_q.quantize | 660 | 6.290 | 0.018871 | 660 / 660 |
| AsStrided / unresolved | 660 | 5.060 | 0.015180 | 0 / 880 |
| Slice / unresolved | 660 | 4.432 | 0.013295 | 0 / 2200 |
| Sigmoid / unresolved | 660 | 1.460 | 0.004380 | 0 / 1100 |
| Cast / unresolved | 660 | 1.394 | 0.004183 | 0 / 1320 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| FusedInferAttentionScore / unresolved | 220 | 277.586 | 0.277586 | 0 / 220 |
| MatMulV2 / output_gate | 220 | 42.152 | 0.042152 | 220 / 220 |
| PadV3 / unresolved | 440 | 15.115 | 0.030231 | 0 / 440 |
| MatMulV2 / output | 220 | 29.754 | 0.029754 | 220 / 220 |
| hcom_reduceScatter_ / attention_output_communication | 220 | 29.563 | 0.029563 | 0 / 880 |
| hcom_allGather_ / attention_output_communication | 220 | 28.996 | 0.028996 | 0 / 880 |
| RmsNorm / unresolved | 440 | 11.555 | 0.023111 | 0 / 440 |
| QuantBatchMatmulV3 / unresolved | 220 | 21.800 | 0.021800 | 0 / 1540 |
| Transpose / unresolved | 220 | 20.731 | 0.020731 | 0 / 220 |
| MemSet / unresolved | 440 | 7.115 | 0.014229 | 0 / 440 |
| TransposeBatchMatMul / v_expand | 220 | 13.361 | 0.013361 | 220 / 220 |
| QuantBatchMatmulV3 / q_b | 220 | 12.678 | 0.012678 | 220 / 220 |
| Slice / unresolved | 1100 | 2.203 | 0.011016 | 0 / 2200 |
| Mul / unresolved | 220 | 10.507 | 0.010507 | 0 / 1100 |
| AttnResFwd / unresolved | 220 | 10.484 | 0.010484 | 0 / 1980 |
| BatchMatMulV2 / unresolved | 220 | 8.623 | 0.008623 | 0 / 220 |
| TensorMove / unresolved | 220 | 8.356 | 0.008356 | 0 / 220 |
| ScatterPaKvCache / unresolved | 220 | 8.155 | 0.008155 | 0 / 220 |
| ZerosLike / unresolved | 220 | 7.883 | 0.007883 | 0 / 880 |
| Sigmoid / unresolved | 220 | 7.867 | 0.007867 | 0 / 1100 |
| DynamicQuant / q_a.quantize | 220 | 6.622 | 0.006622 | 220 / 220 |
| AsStrided / unresolved | 220 | 5.654 | 0.005654 | 0 / 880 |
| DynamicQuant / q_b.quantize | 220 | 4.692 | 0.004692 | 220 / 220 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| GroupedMatmul / expert_up | 440 | 635.877 | 1.271755 | 0 / 660 |
| reduce_scatterAicpuKernel / unresolved | 1018 | 173.671 | 0.803625 | 0 / 1760 |
| GroupedMatmul / expert_up | 220 | 623.719 | 0.623719 | 0 / 660 |
| GroupedMatmul / expert_down | 440 | 305.145 | 0.610289 | 0 / 660 |
| DequantSituQuant / unresolved | 880 | 83.025 | 0.332099 | 0 / 1320 |
| GroupedMatmul / expert_down | 220 | 299.440 | 0.299440 | 0 / 660 |
| DequantSituQuant / unresolved | 440 | 82.967 | 0.165933 | 0 / 1320 |
| MoeDistributeDispatchV2 / unresolved | 440 | 57.562 | 0.115125 | 0 / 660 |
| hcom_allGather_ / ffn_down_communication | 660 | 33.985 | 0.101956 | 0 / 1100 |
| hcom_reduceScatter_ / ffn_down_communication | 660 | 29.498 | 0.088495 | 0 / 880 |
| MoeDistributeCombineV2 / unresolved | 440 | 41.887 | 0.083773 | 0 / 660 |
| MoeDistributeDispatchV2 / unresolved | 220 | 59.712 | 0.059712 | 0 / 660 |
| QuantBatchMatmulV3 / latent_down | 440 | 29.492 | 0.058983 | 660 / 660 |
| hcom_allGather_ / ffn_down_communication | 440 | 28.442 | 0.056883 | 0 / 1100 |
| QuantBatchMatmulV3 / gate_up | 220 | 56.800 | 0.056800 | 220 / 220 |
| QuantBatchMatmulV3 / latent_up | 440 | 27.901 | 0.055801 | 660 / 660 |
| MatMulV3 / unresolved | 440 | 26.911 | 0.053821 | 0 / 660 |
| MoeDistributeCombineV2 / unresolved | 220 | 42.310 | 0.042310 | 0 / 660 |
| QuantBatchMatmulV3 / unresolved | 440 | 19.456 | 0.038912 | 0 / 1540 |
| QuantBatchMatmulV3 / down | 220 | 36.931 | 0.036931 | 220 / 220 |
| ForeachAddList / unresolved | 440 | 17.607 | 0.035215 | 0 / 660 |
| AttnResFwd / unresolved | 660 | 11.505 | 0.034514 | 0 / 1980 |
| QuantBatchMatmulV3 / shared.down | 440 | 15.778 | 0.031557 | 660 / 660 |
| QuantBatchMatmulV3 / latent_down | 220 | 29.872 | 0.029872 | 660 / 660 |
| QuantBatchMatmulV3 / latent_up | 220 | 28.244 | 0.028244 | 660 / 660 |
| MatMulV3 / unresolved | 220 | 23.128 | 0.023128 | 0 / 660 |
| AttnResFwd / unresolved | 440 | 11.294 | 0.022588 | 0 / 1980 |
| Index / unresolved | 220 | 22.538 | 0.022538 | 0 / 220 |
| hcom_reduceScatter_ / ffn_down_communication | 220 | 22.145 | 0.022145 | 0 / 880 |
| Mul / unresolved | 880 | 5.137 | 0.020547 | 0 / 1100 |
| QuantBatchMatmulV3 / unresolved | 220 | 19.821 | 0.019821 | 0 / 1540 |
| Cast / unresolved | 660 | 5.714 | 0.017142 | 0 / 1320 |
| ForeachAddList / unresolved | 220 | 16.434 | 0.016434 | 0 / 660 |
| QuantBatchMatmulV3 / shared.down | 220 | 14.920 | 0.014920 | 660 / 660 |
| DynamicQuant / shared.gate_up.quantize | 440 | 7.000 | 0.014000 | 660 / 660 |
| Tanh / unresolved | 440 | 6.725 | 0.013449 | 0 / 440 |
| RealDiv / unresolved | 440 | 6.236 | 0.012472 | 0 / 440 |
| MoeGatingTopK / unresolved | 440 | 5.892 | 0.011784 | 0 / 660 |
| IndexCheck / unresolved | 220 | 10.310 | 0.010310 | 0 / 220 |
| RmsNorm / latent_norm | 440 | 4.755 | 0.009510 | 660 / 660 |
| DynamicQuant / latent_down.quantize | 440 | 4.093 | 0.008187 | 660 / 660 |
| DynamicQuant / latent_up.quantize | 440 | 3.922 | 0.007843 | 660 / 660 |
| Sigmoid / unresolved | 220 | 7.838 | 0.007838 | 0 / 1100 |
| DynamicQuant / gate_up.quantize | 220 | 6.874 | 0.006874 | 220 / 220 |
| DynamicQuant / shared.gate_up.quantize | 220 | 6.827 | 0.006827 | 660 / 660 |
| MoeGatingTopK / unresolved | 220 | 6.134 | 0.006134 | 0 / 660 |
| Slice / unresolved | 440 | 2.886 | 0.005772 | 0 / 2200 |
| RmsNorm / latent_norm | 220 | 5.360 | 0.005360 | 660 / 660 |
| DynamicQuant / down.quantize | 220 | 4.613 | 0.004613 | 220 / 220 |
| DynamicQuant / latent_down.quantize | 220 | 4.501 | 0.004501 | 660 / 660 |
| DynamicQuant / latent_up.quantize | 220 | 3.873 | 0.003873 | 660 / 660 |

## a3_kimi4_tp8_w4a8_c4 / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| reduce_scatterAicpuKernel / unresolved | 936 | 169.805 | 0.646087 | 0 / 1968 |
| hcom_allGather_ / attention_output_communication | 738 | 128.546 | 0.385637 | 0 / 984 |
| MatMulV2 / unresolved | 1476 | 39.408 | 0.236449 | 0 / 1968 |
| RecurrentKda / unresolved | 738 | 34.298 | 0.102895 | 0 / 738 |
| QuantBatchMatmulV3 / unresolved | 738 | 33.406 | 0.100219 | 0 / 2706 |
| hcom_reduceScatter_ / attention_output_communication | 738 | 24.827 | 0.074480 | 0 / 984 |
| PadV3 / unresolved | 738 | 17.597 | 0.052791 | 0 / 2214 |
| CausalConv1d / unresolved | 738 | 16.004 | 0.048011 | 0 / 738 |
| MemSet / unresolved | 738 | 9.098 | 0.027295 | 0 / 2214 |
| AttnResFwd / unresolved | 738 | 8.777 | 0.026330 | 0 / 2214 |
| DynamicQuant / unresolved | 738 | 4.191 | 0.012573 | 0 / 1968 |
| AsStrided / unresolved | 738 | 3.948 | 0.011845 | 0 / 984 |
| layer_norm_gated_fwd_kernel / unresolved | 738 | 3.656 | 0.010969 | 0 / 738 |
| ZerosLike / unresolved | 738 | 2.274 | 0.006822 | 0 / 984 |
| Slice / unresolved | 738 | 1.735 | 0.005206 | 0 / 2460 |
| Sigmoid / unresolved | 738 | 1.425 | 0.004276 | 0 / 1230 |
| Cast / unresolved | 738 | 1.377 | 0.004130 | 0 / 1476 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| FusedInferAttentionScore / unresolved | 246 | 60.488 | 0.060488 | 0 / 246 |
| MatMulV2 / unresolved | 492 | 28.222 | 0.056443 | 0 / 1968 |
| reduce_scatterAicpuKernel / unresolved | 58 | 161.603 | 0.038101 | 0 / 1968 |
| QuantBatchMatmulV3 / unresolved | 492 | 17.893 | 0.035787 | 0 / 2706 |
| PadV3 / unresolved | 738 | 11.769 | 0.035308 | 0 / 2214 |
| hcom_allGather_ / attention_output_communication | 246 | 29.195 | 0.029195 | 0 / 984 |
| hcom_reduceScatter_ / attention_output_communication | 246 | 27.324 | 0.027324 | 0 / 984 |
| MemSet / unresolved | 738 | 7.659 | 0.022978 | 0 / 2214 |
| Transpose / unresolved | 246 | 19.072 | 0.019072 | 0 / 246 |
| TransposeBatchMatMul / unresolved | 246 | 12.912 | 0.012912 | 0 / 246 |
| RmsNorm / unresolved | 492 | 5.617 | 0.011234 | 0 / 492 |
| AttnResFwd / unresolved | 246 | 9.775 | 0.009775 | 0 / 2214 |
| Slice / unresolved | 1230 | 1.929 | 0.009643 | 0 / 2460 |
| BatchMatMulV2 / unresolved | 246 | 7.631 | 0.007631 | 0 / 246 |
| DynamicQuant / unresolved | 492 | 3.547 | 0.007095 | 0 / 1968 |
| AsStrided / unresolved | 246 | 5.104 | 0.005104 | 0 / 984 |
| ScatterPaKvCache / unresolved | 246 | 2.893 | 0.002893 | 0 / 246 |
| Mul / unresolved | 246 | 2.506 | 0.002506 | 0 / 1230 |
| Sigmoid / unresolved | 246 | 2.482 | 0.002482 | 0 / 1230 |
| ZerosLike / unresolved | 246 | 2.434 | 0.002434 | 0 / 984 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| reduce_scatterAicpuKernel / unresolved | 967 | 174.352 | 0.685359 | 0 / 1968 |
| GroupedMatmul / expert_up | 492 | 103.880 | 0.207760 | 0 / 738 |
| hcom_allGather_ / ffn_down_communication | 738 | 49.927 | 0.149781 | 0 / 1230 |
| GroupedMatmul / expert_down | 492 | 63.552 | 0.127104 | 0 / 738 |
| MoeDistributeDispatchV2 / unresolved | 492 | 55.996 | 0.111992 | 0 / 738 |
| GroupedMatmul / expert_up | 246 | 103.410 | 0.103410 | 0 / 738 |
| hcom_reduceScatter_ / ffn_down_communication | 738 | 25.354 | 0.076061 | 0 / 984 |
| QuantBatchMatmulV3 / unresolved | 984 | 15.930 | 0.063721 | 0 / 2706 |
| DequantSituQuant / unresolved | 984 | 15.671 | 0.062682 | 0 / 1476 |
| GroupedMatmul / expert_down | 246 | 60.741 | 0.060741 | 0 / 738 |
| QuantBatchMatmulV3 / latent_down | 492 | 29.691 | 0.059383 | 738 / 738 |
| QuantBatchMatmulV3 / latent_up | 492 | 29.082 | 0.058165 | 738 / 738 |
| MoeDistributeDispatchV2 / unresolved | 246 | 54.795 | 0.054795 | 0 / 738 |
| QuantBatchMatmulV3 / gate_up | 246 | 54.590 | 0.054590 | 246 / 246 |
| hcom_allGather_ / ffn_down_communication | 492 | 26.795 | 0.053590 | 0 / 1230 |
| MoeDistributeCombineV2 / unresolved | 492 | 23.156 | 0.046311 | 0 / 738 |
| MatMulV3 / unresolved | 492 | 22.800 | 0.045600 | 0 / 738 |
| QuantBatchMatmulV3 / down | 246 | 36.832 | 0.036832 | 246 / 246 |
| ForeachAddList / unresolved | 492 | 16.527 | 0.033053 | 0 / 738 |
| AttnResFwd / unresolved | 738 | 10.394 | 0.031183 | 0 / 2214 |
| QuantBatchMatmulV3 / unresolved | 492 | 15.513 | 0.031026 | 0 / 2706 |
| DequantSituQuant / unresolved | 492 | 15.244 | 0.030488 | 0 / 1476 |
| QuantBatchMatmulV3 / latent_down | 246 | 29.421 | 0.029421 | 738 / 738 |
| PadV3 / unresolved | 492 | 14.463 | 0.028926 | 0 / 2214 |
| QuantBatchMatmulV3 / latent_up | 246 | 28.092 | 0.028092 | 738 / 738 |
| MoeDistributeCombineV2 / unresolved | 246 | 24.959 | 0.024959 | 0 / 738 |
| MatMulV3 / unresolved | 246 | 21.479 | 0.021479 | 0 / 738 |
| AttnResFwd / unresolved | 492 | 10.027 | 0.020053 | 0 / 2214 |
| hcom_reduceScatter_ / ffn_down_communication | 246 | 18.904 | 0.018904 | 0 / 984 |
| Mul / unresolved | 984 | 4.619 | 0.018478 | 0 / 1230 |
| MemSet / unresolved | 492 | 8.866 | 0.017732 | 0 / 2214 |
| PadV3 / unresolved | 246 | 17.370 | 0.017370 | 0 / 2214 |
| ForeachAddList / unresolved | 246 | 16.019 | 0.016019 | 0 / 738 |
| Cast / unresolved | 738 | 4.908 | 0.014725 | 0 / 1476 |
| RealDiv / unresolved | 492 | 5.456 | 0.010913 | 0 / 492 |
| Tanh / unresolved | 492 | 5.343 | 0.010686 | 0 / 492 |
| MoeGatingTopK / unresolved | 492 | 5.140 | 0.010280 | 0 / 738 |
| MemSet / unresolved | 246 | 8.912 | 0.008912 | 0 / 2214 |
| Index / unresolved | 246 | 8.476 | 0.008476 | 0 / 246 |
| DynamicQuant / unresolved | 492 | 4.223 | 0.008447 | 0 / 1968 |
| RmsNorm / latent_norm | 492 | 4.049 | 0.008099 | 738 / 738 |
| Sigmoid / unresolved | 246 | 6.505 | 0.006505 | 0 / 1230 |
| DynamicQuant / latent_down.quantize | 492 | 3.034 | 0.006068 | 738 / 738 |
| reduce_scatterAicpuKernel / unresolved | 7 | 205.470 | 0.005847 | 0 / 1968 |
| DynamicQuant / latent_up.quantize | 492 | 2.663 | 0.005327 | 738 / 738 |
| Slice / unresolved | 492 | 2.417 | 0.004833 | 0 / 2460 |
| MoeGatingTopK / unresolved | 246 | 4.730 | 0.004730 | 0 / 738 |
| DynamicQuant / gate_up.quantize | 246 | 4.681 | 0.004681 | 246 / 246 |
| DynamicQuant / down.quantize | 246 | 4.535 | 0.004535 | 246 / 246 |
| DynamicQuant / unresolved | 246 | 4.212 | 0.004212 | 0 / 1968 |
| RmsNorm / latent_norm | 246 | 3.884 | 0.003884 | 738 / 738 |
| DynamicQuant / latent_down.quantize | 246 | 3.400 | 0.003400 | 738 / 738 |
| IndexCheck / unresolved | 246 | 3.296 | 0.003296 | 0 / 246 |
| DynamicQuant / latent_up.quantize | 246 | 2.664 | 0.002664 | 738 / 738 |

## a3_kimi4_tp8_w4a8_c64 / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| reduce_scatterAicpuKernel / unresolved | 646 | 171.988 | 0.566860 | 0 / 1568 |
| RecurrentKda / unresolved | 588 | 176.676 | 0.530028 | 0 / 588 |
| MatMulV2 / unresolved | 588 | 90.415 | 0.271245 | 0 / 588 |
| hcom_allGather_ / attention_output_communication | 588 | 71.668 | 0.215005 | 0 / 784 |
| MatMulV2 / linear_output | 588 | 40.050 | 0.120151 | 588 / 588 |
| QuantBatchMatmulV3 / unresolved | 588 | 35.209 | 0.105628 | 0 / 1372 |
| CausalConv1d / unresolved | 588 | 29.315 | 0.087946 | 0 / 588 |
| hcom_reduceScatter_ / attention_output_communication | 588 | 24.511 | 0.073533 | 0 / 784 |
| AttnResFwd / unresolved | 588 | 10.362 | 0.031086 | 0 / 1764 |
| layer_norm_gated_fwd_kernel / unresolved | 588 | 9.717 | 0.029150 | 0 / 588 |
| DynamicQuant / linear_q.quantize | 588 | 9.091 | 0.027274 | 588 / 588 |
| ZerosLike / unresolved | 588 | 8.867 | 0.026601 | 0 / 784 |
| AsStrided / unresolved | 588 | 6.272 | 0.018817 | 0 / 784 |
| Slice / unresolved | 588 | 4.722 | 0.014166 | 0 / 1960 |
| Sigmoid / unresolved | 588 | 1.529 | 0.004588 | 0 / 980 |
| Cast / unresolved | 588 | 1.465 | 0.004395 | 0 / 1176 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| FusedInferAttentionScore / unresolved | 196 | 505.614 | 0.505614 | 0 / 196 |
| MatMulV2 / output_gate | 196 | 51.145 | 0.051145 | 196 / 196 |
| hcom_allGather_ / attention_output_communication | 196 | 31.823 | 0.031823 | 0 / 784 |
| PadV3 / unresolved | 392 | 15.684 | 0.031368 | 0 / 392 |
| hcom_reduceScatter_ / attention_output_communication | 196 | 29.788 | 0.029788 | 0 / 784 |
| MatMulV2 / output | 196 | 26.683 | 0.026683 | 196 / 196 |
| QuantBatchMatmulV3 / unresolved | 196 | 22.612 | 0.022612 | 0 / 1372 |
| RmsNorm / unresolved | 392 | 10.323 | 0.020645 | 0 / 392 |
| TransposeBatchMatMul / v_expand | 196 | 16.602 | 0.016602 | 196 / 196 |
| MemSet / unresolved | 392 | 7.343 | 0.014686 | 0 / 392 |
| QuantBatchMatmulV3 / q_b | 196 | 13.983 | 0.013983 | 196 / 196 |
| AttnResFwd / unresolved | 196 | 11.659 | 0.011659 | 0 / 1764 |
| Slice / unresolved | 980 | 2.231 | 0.011157 | 0 / 1960 |
| Mul / unresolved | 196 | 10.564 | 0.010564 | 0 / 980 |
| Transpose / unresolved | 196 | 9.704 | 0.009704 | 0 / 196 |
| DynamicQuant / q_a.quantize | 196 | 9.551 | 0.009551 | 196 / 196 |
| ScatterPaKvCache / unresolved | 196 | 9.477 | 0.009477 | 0 / 196 |
| BatchMatMulV2 / unresolved | 196 | 9.024 | 0.009024 | 0 / 196 |
| TensorMove / unresolved | 196 | 8.424 | 0.008424 | 0 / 196 |
| Sigmoid / unresolved | 196 | 8.004 | 0.008004 | 0 / 980 |
| ZerosLike / unresolved | 196 | 7.896 | 0.007896 | 0 / 784 |
| AsStrided / unresolved | 196 | 6.712 | 0.006712 | 0 / 784 |
| DynamicQuant / q_b.quantize | 196 | 4.646 | 0.004646 | 196 / 196 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| GroupedMatmul / expert_up | 392 | 1103.385 | 2.206770 | 0 / 588 |
| GroupedMatmul / expert_up | 196 | 1080.120 | 1.080120 | 0 / 588 |
| GroupedMatmul / expert_down | 392 | 527.603 | 1.055206 | 0 / 588 |
| reduce_scatterAicpuKernel / unresolved | 922 | 177.648 | 0.835670 | 0 / 1568 |
| DequantSituQuant / unresolved | 784 | 140.548 | 0.562192 | 0 / 1176 |
| GroupedMatmul / expert_down | 196 | 506.525 | 0.506525 | 0 / 588 |
| DequantSituQuant / unresolved | 392 | 138.924 | 0.277849 | 0 / 1176 |
| MoeDistributeDispatchV2 / unresolved | 392 | 62.483 | 0.124967 | 0 / 588 |
| hcom_allGather_ / ffn_down_communication | 588 | 30.508 | 0.091525 | 0 / 980 |
| hcom_reduceScatter_ / ffn_down_communication | 588 | 29.078 | 0.087233 | 0 / 784 |
| MatMulV3 / unresolved | 392 | 32.508 | 0.065016 | 0 / 588 |
| MoeDistributeDispatchV2 / unresolved | 196 | 62.672 | 0.062672 | 0 / 588 |
| MoeDistributeCombineV2 / unresolved | 392 | 31.284 | 0.062567 | 0 / 588 |
| hcom_allGather_ / ffn_down_communication | 392 | 31.007 | 0.062014 | 0 / 980 |
| QuantBatchMatmulV3 / latent_down | 392 | 30.402 | 0.060803 | 588 / 588 |
| QuantBatchMatmulV3 / gate_up | 196 | 60.636 | 0.060636 | 196 / 196 |
| QuantBatchMatmulV3 / latent_up | 392 | 27.936 | 0.055873 | 588 / 588 |
| QuantBatchMatmulV3 / unresolved | 392 | 20.951 | 0.041903 | 0 / 1372 |
| QuantBatchMatmulV3 / down | 196 | 40.148 | 0.040148 | 196 / 196 |
| MoeDistributeCombineV2 / unresolved | 196 | 39.266 | 0.039266 | 0 / 588 |
| ForeachAddList / unresolved | 392 | 19.360 | 0.038720 | 0 / 588 |
| AttnResFwd / unresolved | 588 | 12.126 | 0.036377 | 0 / 1764 |
| QuantBatchMatmulV3 / shared.down | 392 | 17.234 | 0.034469 | 588 / 588 |
| QuantBatchMatmulV3 / latent_down | 196 | 29.506 | 0.029506 | 588 / 588 |
| QuantBatchMatmulV3 / latent_up | 196 | 27.841 | 0.027841 | 588 / 588 |
| hcom_reduceScatter_ / ffn_down_communication | 196 | 27.338 | 0.027338 | 0 / 784 |
| Index / unresolved | 196 | 24.884 | 0.024884 | 0 / 196 |
| AttnResFwd / unresolved | 392 | 12.163 | 0.024326 | 0 / 1764 |
| Mul / unresolved | 784 | 6.049 | 0.024196 | 0 / 980 |
| DynamicQuant / shared.gate_up.quantize | 392 | 11.465 | 0.022930 | 588 / 588 |
| MatMulV3 / unresolved | 196 | 22.379 | 0.022379 | 0 / 588 |
| QuantBatchMatmulV3 / unresolved | 196 | 21.419 | 0.021419 | 0 / 1372 |
| Cast / unresolved | 588 | 5.975 | 0.017926 | 0 / 1176 |
| ForeachAddList / unresolved | 196 | 16.992 | 0.016992 | 0 / 588 |
| QuantBatchMatmulV3 / shared.down | 196 | 16.403 | 0.016403 | 588 / 588 |
| Tanh / unresolved | 392 | 7.806 | 0.015612 | 0 / 392 |
| MoeGatingTopK / unresolved | 392 | 6.523 | 0.013046 | 0 / 588 |
| RealDiv / unresolved | 392 | 6.384 | 0.012767 | 0 / 392 |
| IndexCheck / unresolved | 196 | 12.764 | 0.012764 | 0 / 196 |
| RmsNorm / latent_norm | 392 | 5.363 | 0.010726 | 588 / 588 |
| DynamicQuant / gate_up.quantize | 196 | 10.314 | 0.010314 | 196 / 196 |
| DynamicQuant / shared.gate_up.quantize | 196 | 10.236 | 0.010236 | 588 / 588 |
| DynamicQuant / latent_down.quantize | 392 | 4.603 | 0.009207 | 588 / 588 |
| Sigmoid / unresolved | 196 | 8.110 | 0.008110 | 0 / 980 |
| DynamicQuant / latent_up.quantize | 392 | 3.544 | 0.007088 | 588 / 588 |
| Slice / unresolved | 392 | 3.498 | 0.006996 | 0 / 1960 |
| MoeGatingTopK / unresolved | 196 | 6.630 | 0.006630 | 0 / 588 |
| DynamicQuant / down.quantize | 196 | 6.544 | 0.006544 | 196 / 196 |
| RmsNorm / latent_norm | 196 | 5.864 | 0.005864 | 588 / 588 |
| DynamicQuant / latent_down.quantize | 196 | 4.821 | 0.004821 | 588 / 588 |
| DynamicQuant / latent_up.quantize | 196 | 3.579 | 0.003579 | 588 / 588 |

## a5_kimi_tp8_e16_bf16_c16_p16k / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 6486 | 20.494 | 2.828189 | 0 / 11938 |
| RecurrentKda / unresolved | 3243 | 20.565 | 1.419015 | 0 / 3243 |
| hcom_reduceScatter_ / attention_output_communication | 3243 | 14.663 | 1.011741 | 0 / 4371 |
| MatMulV3 / linear_output | 3243 | 12.339 | 0.851373 | 3243 / 3243 |
| AttnResFwd / unresolved | 3243 | 11.227 | 0.774669 | 0 / 8789 |
| hcom_allGather_ / attention_output_communication | 3243 | 10.441 | 0.720402 | 0 / 4371 |
| CausalConv1d / unresolved | 3243 | 8.341 | 0.575498 | 0 / 3243 |
| Slice / unresolved | 6486 | 3.413 | 0.471043 | 0 / 26132 |
| AsStrided / unresolved | 3243 | 4.333 | 0.298985 | 0 / 3243 |
| layer_norm_gated_fwd_kernel / unresolved | 3243 | 3.461 | 0.238837 | 0 / 3243 |
| ZerosLike / unresolved | 3243 | 3.050 | 0.210440 | 0 / 4371 |
| Sigmoid / unresolved | 3243 | 2.151 | 0.148419 | 0 / 13066 |
| Cast / unresolved | 3243 | 1.740 | 0.120029 | 0 / 30550 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| FusedInferAttentionScore / unresolved | 1128 | 142.095 | 3.410281 | 0 / 1128 |
| MlaPrologV3 / unresolved | 1128 | 34.559 | 0.829421 | 0 / 1128 |
| MatMulV3 / q_a | 1128 | 19.145 | 0.459486 | 1128 / 1128 |
| hcom_reduceScatter_ / attention_output_communication | 1128 | 17.231 | 0.413545 | 0 / 4371 |
| MatMulV3 / unresolved | 1128 | 12.713 | 0.305104 | 0 / 11938 |
| AttnResFwd / unresolved | 1128 | 11.433 | 0.274386 | 0 / 8789 |
| hcom_allGather_ / attention_output_communication | 1128 | 10.491 | 0.251781 | 0 / 4371 |
| PadV3 / unresolved | 2256 | 4.301 | 0.206431 | 0 / 2256 |
| Slice / unresolved | 2256 | 3.749 | 0.179972 | 0 / 26132 |
| TransposeBatchMatMul / unresolved | 1128 | 5.418 | 0.130041 | 0 / 1128 |
| Mul / unresolved | 1128 | 3.317 | 0.079604 | 0 / 35908 |
| Sigmoid / unresolved | 1128 | 3.310 | 0.079447 | 0 / 13066 |
| ZerosLike / unresolved | 1128 | 2.970 | 0.071282 | 0 / 4371 |
| Cast / unresolved | 1128 | 1.894 | 0.045454 | 0 / 30550 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| GroupedMatmul / expert_up | 3196 | 44.710 | 3.040296 | 0 / 4324 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3196 | 33.593 | 2.284327 | 0 / 4324 |
| MatMulV3 / latent_down | 3196 | 25.673 | 1.745769 | 4324 / 4324 |
| MatMulV3 / latent_up | 3196 | 21.845 | 1.485478 | 4324 / 4324 |
| GroupedMatmul / expert_down | 3196 | 21.559 | 1.466033 | 0 / 4324 |
| MatMulV3 / shared.gate_up | 3196 | 20.872 | 1.419314 | 4324 / 4324 |
| Mul / unresolved | 25756 | 2.534 | 1.388551 | 0 / 35908 |
| Tanh / unresolved | 12878 | 4.033 | 1.104911 | 0 / 17390 |
| Cast / unresolved | 19317 | 2.621 | 1.077210 | 0 / 30550 |
| Muls / unresolved | 12878 | 3.798 | 1.040671 | 0 / 17390 |
| hcom_reduceScatter_ / ffn_down_communication | 3243 | 14.891 | 1.027462 | 0 / 4371 |
| Slice / unresolved | 12878 | 3.711 | 1.016688 | 0 / 26132 |
| GroupedMatmul / expert_up | 1128 | 42.134 | 1.011212 | 0 / 4324 |
| MoeDistributeCombineV3 / expert_combine_native | 3196 | 14.667 | 0.997343 | 0 / 4324 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 1128 | 32.905 | 0.789710 | 0 / 4324 |
| AttnResFwd / unresolved | 3243 | 11.054 | 0.762731 | 0 / 8789 |
| hcom_allGather_ / ffn_down_communication | 3243 | 10.309 | 0.711329 | 0 / 4418 |
| MatMulV3 / shared.down | 3196 | 8.639 | 0.587435 | 4324 / 4324 |
| MatMulV3 / latent_down | 1128 | 24.438 | 0.586504 | 4324 / 4324 |
| MatMulV3 / latent_up | 1128 | 21.634 | 0.519216 | 4324 / 4324 |
| MatMulV3 / unresolved | 3196 | 7.415 | 0.504246 | 0 / 11938 |
| Sigmoid / unresolved | 6439 | 3.679 | 0.504054 | 0 / 13066 |
| GroupedMatmul / expert_down | 1128 | 20.583 | 0.493996 | 0 / 4324 |
| MatMulV3 / shared.gate_up | 1128 | 20.237 | 0.485686 | 4324 / 4324 |
| Mul / unresolved | 9024 | 2.501 | 0.480201 | 0 / 35908 |
| Cast / unresolved | 6862 | 2.618 | 0.382155 | 0 / 30550 |
| Tanh / unresolved | 4512 | 3.969 | 0.380992 | 0 / 17390 |
| ForeachAddList / unresolved | 3196 | 5.525 | 0.375710 | 0 / 4324 |
| hcom_reduceScatter_ / ffn_down_communication | 1128 | 14.961 | 0.359059 | 0 / 4371 |
| Muls / unresolved | 4512 | 3.720 | 0.357116 | 0 / 17390 |
| MoeDistributeCombineV3 / expert_combine_native | 1128 | 14.758 | 0.354196 | 0 / 4324 |
| Slice / unresolved | 4512 | 3.541 | 0.339893 | 0 / 26132 |
| RmsNorm / latent_norm | 3196 | 4.217 | 0.286780 | 4324 / 4324 |
| AttnResFwd / unresolved | 1175 | 11.148 | 0.278703 | 0 / 8789 |
| hcom_allGather_ / ffn_down_communication | 1175 | 10.240 | 0.256000 | 0 / 4418 |
| MoeGatingTopK / unresolved | 3196 | 3.301 | 0.224485 | 0 / 4324 |
| MatMulV3 / shared.down | 1128 | 8.576 | 0.205813 | 4324 / 4324 |
| MatMulV3 / unresolved | 1128 | 7.672 | 0.184121 | 0 / 11938 |
| Sigmoid / unresolved | 2256 | 3.724 | 0.178730 | 0 / 13066 |
| ForeachAddList / unresolved | 1128 | 5.500 | 0.132003 | 0 / 4324 |
| RmsNorm / latent_norm | 1128 | 4.212 | 0.101092 | 4324 / 4324 |
| MoeGatingTopK / unresolved | 1128 | 3.296 | 0.079107 | 0 / 4324 |
| MatMulV3 / gate_up | 47 | 53.443 | 0.053443 | 47 / 47 |
| MatMulV3 / down | 47 | 25.433 | 0.025433 | 47 / 47 |
| Index / unresolved | 47 | 5.230 | 0.005230 | 0 / 47 |
| Fill / unresolved | 94 | 1.655 | 0.003309 | 0 / 94 |
| BroadcastTo / unresolved | 47 | 2.460 | 0.002460 | 0 / 47 |

## a5_kimi_tp8_e16_bf16_c16_p4k / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 6762 | 20.491 | 2.827825 | 0 / 12446 |
| RecurrentKda / unresolved | 3381 | 20.482 | 1.413285 | 0 / 3381 |
| hcom_reduceScatter_ / attention_output_communication | 3381 | 14.737 | 1.016850 | 0 / 4557 |
| MatMulV3 / linear_output | 3381 | 12.313 | 0.849624 | 3381 / 3381 |
| AttnResFwd / unresolved | 3381 | 11.233 | 0.775100 | 0 / 9163 |
| hcom_allGather_ / attention_output_communication | 3381 | 10.901 | 0.752145 | 0 / 4557 |
| CausalConv1d / unresolved | 3381 | 8.332 | 0.574897 | 0 / 3381 |
| Slice / unresolved | 6762 | 3.416 | 0.471355 | 0 / 27244 |
| AsStrided / unresolved | 3381 | 4.331 | 0.298832 | 0 / 3381 |
| layer_norm_gated_fwd_kernel / unresolved | 3381 | 3.461 | 0.238787 | 0 / 3381 |
| ZerosLike / unresolved | 3381 | 3.051 | 0.210520 | 0 / 4557 |
| Sigmoid / unresolved | 3381 | 2.154 | 0.148634 | 0 / 13622 |
| Cast / unresolved | 3381 | 1.733 | 0.119596 | 0 / 31850 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| FusedInferAttentionScore / unresolved | 1176 | 47.673 | 1.144145 | 0 / 1176 |
| MlaPrologV3 / unresolved | 1176 | 34.540 | 0.828959 | 0 / 1176 |
| MatMulV3 / q_a | 1176 | 19.147 | 0.459527 | 1176 / 1176 |
| hcom_reduceScatter_ / attention_output_communication | 1176 | 16.237 | 0.389693 | 0 / 4557 |
| MatMulV3 / unresolved | 1176 | 12.723 | 0.305355 | 0 / 12446 |
| AttnResFwd / unresolved | 1176 | 11.413 | 0.273921 | 0 / 9163 |
| hcom_allGather_ / attention_output_communication | 1176 | 10.499 | 0.251983 | 0 / 4557 |
| PadV3 / unresolved | 2352 | 4.288 | 0.205821 | 0 / 2352 |
| Slice / unresolved | 2352 | 3.746 | 0.179792 | 0 / 27244 |
| TransposeBatchMatMul / unresolved | 1176 | 5.420 | 0.130083 | 0 / 1176 |
| Mul / unresolved | 1176 | 3.317 | 0.079604 | 0 / 37436 |
| Sigmoid / unresolved | 1176 | 3.300 | 0.079207 | 0 / 13622 |
| ZerosLike / unresolved | 1176 | 2.973 | 0.071342 | 0 / 4557 |
| Cast / unresolved | 1176 | 1.895 | 0.045484 | 0 / 31850 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| GroupedMatmul / expert_up | 3332 | 44.619 | 3.034101 | 0 / 4508 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3332 | 33.586 | 2.283865 | 0 / 4508 |
| MatMulV3 / latent_down | 3332 | 25.630 | 1.742828 | 4508 / 4508 |
| MatMulV3 / latent_up | 3332 | 21.855 | 1.486108 | 4508 / 4508 |
| GroupedMatmul / expert_down | 3332 | 21.582 | 1.467583 | 0 / 4508 |
| MatMulV3 / shared.gate_up | 3332 | 20.902 | 1.421309 | 4508 / 4508 |
| Mul / unresolved | 26852 | 2.534 | 1.388665 | 0 / 37436 |
| Tanh / unresolved | 13426 | 4.025 | 1.102923 | 0 / 18130 |
| Cast / unresolved | 20139 | 2.621 | 1.077194 | 0 / 31850 |
| Muls / unresolved | 13426 | 3.797 | 1.040306 | 0 / 18130 |
| hcom_reduceScatter_ / ffn_down_communication | 3381 | 14.901 | 1.028188 | 0 / 4557 |
| Slice / unresolved | 13426 | 3.712 | 1.016965 | 0 / 27244 |
| GroupedMatmul / expert_up | 1176 | 42.118 | 1.010827 | 0 / 4508 |
| MoeDistributeCombineV3 / expert_combine_native | 3332 | 14.714 | 1.000520 | 0 / 4508 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 1176 | 32.927 | 0.790239 | 0 / 4508 |
| AttnResFwd / unresolved | 3381 | 11.086 | 0.764901 | 0 / 9163 |
| hcom_allGather_ / ffn_down_communication | 3381 | 10.280 | 0.709339 | 0 / 4606 |
| MatMulV3 / latent_down | 1176 | 24.437 | 0.586487 | 4508 / 4508 |
| MatMulV3 / shared.down | 3332 | 8.614 | 0.585754 | 4508 / 4508 |
| MatMulV3 / latent_up | 1176 | 21.616 | 0.518796 | 4508 / 4508 |
| Sigmoid / unresolved | 6713 | 3.686 | 0.504962 | 0 / 13622 |
| MatMulV3 / unresolved | 3332 | 7.411 | 0.503982 | 0 / 12446 |
| GroupedMatmul / expert_down | 1176 | 20.597 | 0.494332 | 0 / 4508 |
| MatMulV3 / shared.gate_up | 1176 | 20.232 | 0.485578 | 4508 / 4508 |
| Mul / unresolved | 9408 | 2.503 | 0.480583 | 0 / 37436 |
| Cast / unresolved | 7154 | 2.622 | 0.382879 | 0 / 31850 |
| Tanh / unresolved | 4704 | 3.965 | 0.380607 | 0 / 18130 |
| ForeachAddList / unresolved | 3332 | 5.526 | 0.375743 | 0 / 4508 |
| hcom_reduceScatter_ / ffn_down_communication | 1176 | 14.973 | 0.359346 | 0 / 4557 |
| Muls / unresolved | 4704 | 3.728 | 0.357848 | 0 / 18130 |
| MoeDistributeCombineV3 / expert_combine_native | 1176 | 14.760 | 0.354233 | 0 / 4508 |
| Slice / unresolved | 4704 | 3.548 | 0.340635 | 0 / 27244 |
| RmsNorm / latent_norm | 3332 | 4.208 | 0.286126 | 4508 / 4508 |
| AttnResFwd / unresolved | 1225 | 11.155 | 0.278884 | 0 / 9163 |
| hcom_allGather_ / ffn_down_communication | 1225 | 10.294 | 0.257341 | 0 / 4606 |
| MoeGatingTopK / unresolved | 3332 | 3.301 | 0.224462 | 0 / 4508 |
| MatMulV3 / shared.down | 1176 | 8.570 | 0.205681 | 4508 / 4508 |
| MatMulV3 / unresolved | 1176 | 7.662 | 0.183884 | 0 / 12446 |
| Sigmoid / unresolved | 2352 | 3.725 | 0.178809 | 0 / 13622 |
| ForeachAddList / unresolved | 1176 | 5.500 | 0.131995 | 0 / 4508 |
| RmsNorm / latent_norm | 1176 | 4.214 | 0.101134 | 4508 / 4508 |
| MoeGatingTopK / unresolved | 1176 | 3.298 | 0.079150 | 0 / 4508 |
| MatMulV3 / gate_up | 49 | 53.114 | 0.053114 | 49 / 49 |
| MatMulV3 / down | 49 | 25.535 | 0.025535 | 49 / 49 |
| Index / unresolved | 49 | 5.317 | 0.005317 | 0 / 49 |
| Fill / unresolved | 98 | 1.669 | 0.003337 | 0 / 98 |
| BroadcastTo / unresolved | 49 | 2.427 | 0.002427 | 0 / 49 |

## a5_kimi_tp8_e16_bf16_c1_p16k / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 12213 | 16.744 | 3.466049 | 0 / 31329 |
| hcom_reduceScatter_ / attention_output_communication | 4071 | 14.238 | 0.982391 | 0 / 5487 |
| AttnResFwd / unresolved | 4071 | 10.890 | 0.751380 | 0 / 11033 |
| RecurrentKda / unresolved | 4071 | 10.653 | 0.735035 | 0 / 4071 |
| hcom_allGather_ / attention_output_communication | 4071 | 8.254 | 0.569533 | 0 / 5487 |
| CausalConv1d / unresolved | 4071 | 5.231 | 0.360964 | 0 / 4071 |
| PadV3 / unresolved | 4071 | 4.029 | 0.277985 | 0 / 13747 |
| layer_norm_gated_fwd_kernel / unresolved | 4071 | 2.903 | 0.200336 | 0 / 4071 |
| ZerosLike / unresolved | 4071 | 2.611 | 0.180158 | 0 / 5487 |
| Sigmoid / unresolved | 4071 | 2.094 | 0.144505 | 0 / 16402 |
| Cast / unresolved | 4071 | 1.652 | 0.113987 | 0 / 38350 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MlaPrologV3 / unresolved | 1416 | 32.549 | 0.781174 | 0 / 1416 |
| MatMulV3 / unresolved | 2832 | 14.565 | 0.699137 | 0 / 31329 |
| FusedInferAttentionScore / unresolved | 1416 | 24.374 | 0.584972 | 0 / 1416 |
| hcom_reduceScatter_ / attention_output_communication | 1416 | 15.658 | 0.375799 | 0 / 5487 |
| PadV3 / unresolved | 4248 | 3.952 | 0.284532 | 0 / 13747 |
| AttnResFwd / unresolved | 1416 | 11.161 | 0.267875 | 0 / 11033 |
| hcom_allGather_ / attention_output_communication | 1416 | 8.205 | 0.196921 | 0 / 5487 |
| TransposeBatchMatMul / unresolved | 1416 | 5.368 | 0.128839 | 0 / 1416 |
| ZerosLike / unresolved | 1416 | 2.620 | 0.062875 | 0 / 5487 |
| Mul / unresolved | 1416 | 2.620 | 0.062875 | 0 / 45076 |
| Sigmoid / unresolved | 1416 | 2.475 | 0.059409 | 0 / 16402 |
| Cast / unresolved | 1416 | 1.988 | 0.047709 | 0 / 38350 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 12036 | 11.275 | 2.300018 | 0 / 31329 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4012 | 31.353 | 2.132008 | 0 / 5428 |
| MatMulV3 / latent_down | 4012 | 23.900 | 1.625166 | 5428 / 5428 |
| GroupedMatmul / expert_up | 4012 | 21.913 | 1.490068 | 0 / 5428 |
| MatMulV3 / latent_up | 4012 | 20.635 | 1.403201 | 5428 / 5428 |
| Mul / unresolved | 32332 | 2.365 | 1.295875 | 0 / 45076 |
| GroupedMatmul / expert_down | 4012 | 16.037 | 1.090513 | 0 / 5428 |
| MoeDistributeCombineV3 / expert_combine_native | 4012 | 14.593 | 0.992357 | 0 / 5428 |
| Tanh / unresolved | 16166 | 3.445 | 0.943843 | 0 / 21830 |
| Cast / unresolved | 24249 | 2.198 | 0.903190 | 0 / 38350 |
| hcom_reduceScatter_ / ffn_down_communication | 4071 | 12.538 | 0.865102 | 0 / 5487 |
| Muls / unresolved | 16166 | 3.064 | 0.839594 | 0 / 21830 |
| MatMulV3 / unresolved | 4248 | 11.145 | 0.802458 | 0 / 31329 |
| AttnResFwd / unresolved | 4071 | 10.920 | 0.753514 | 0 / 11033 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 1416 | 31.223 | 0.749352 | 0 / 5428 |
| hcom_allGather_ / ffn_down_communication | 4071 | 9.909 | 0.683747 | 0 / 5546 |
| Slice / unresolved | 8142 | 4.632 | 0.639151 | 0 / 10974 |
| MatMulV3 / latent_down | 1416 | 23.737 | 0.569698 | 5428 / 5428 |
| GroupedMatmul / expert_up | 1416 | 22.083 | 0.529983 | 0 / 5428 |
| Sigmoid / unresolved | 8083 | 3.662 | 0.501740 | 0 / 16402 |
| MatMulV3 / latent_up | 1416 | 20.476 | 0.491429 | 5428 / 5428 |
| Mul / unresolved | 11328 | 2.310 | 0.443425 | 0 / 45076 |
| GroupedMatmul / expert_down | 1416 | 16.093 | 0.386238 | 0 / 5428 |
| MoeDistributeCombineV3 / expert_combine_native | 1416 | 14.426 | 0.346227 | 0 / 5428 |
| Tanh / unresolved | 5664 | 3.482 | 0.334272 | 0 / 21830 |
| Cast / unresolved | 8614 | 2.257 | 0.329589 | 0 / 38350 |
| ForeachAddList / unresolved | 4012 | 4.795 | 0.326079 | 0 / 5428 |
| hcom_reduceScatter_ / ffn_down_communication | 1416 | 12.504 | 0.300090 | 0 / 5487 |
| Muls / unresolved | 5664 | 3.014 | 0.289388 | 0 / 21830 |
| AttnResFwd / unresolved | 1475 | 11.196 | 0.279908 | 0 / 11033 |
| PadV3 / unresolved | 4012 | 3.977 | 0.270444 | 0 / 13747 |
| RmsNorm / latent_norm | 4012 | 3.811 | 0.259144 | 5428 / 5428 |
| hcom_allGather_ / ffn_down_communication | 1475 | 9.570 | 0.239258 | 0 / 5546 |
| Slice / unresolved | 2832 | 4.633 | 0.222385 | 0 / 10974 |
| MoeGatingTopK / unresolved | 4012 | 3.148 | 0.214075 | 0 / 5428 |
| Sigmoid / unresolved | 2832 | 3.938 | 0.189047 | 0 / 16402 |
| ForeachAddList / unresolved | 1416 | 4.754 | 0.114095 | 0 / 5428 |
| RmsNorm / latent_norm | 1416 | 4.007 | 0.096175 | 5428 / 5428 |
| PadV3 / unresolved | 1416 | 4.006 | 0.096137 | 0 / 13747 |
| MoeGatingTopK / unresolved | 1416 | 2.873 | 0.068942 | 0 / 5428 |
| MatMulV3 / gate_up | 59 | 44.882 | 0.044882 | 59 / 59 |
| MatMulV3 / down | 59 | 23.900 | 0.023900 | 59 / 59 |
| Index / unresolved | 59 | 4.695 | 0.004695 | 0 / 59 |
| Fill / unresolved | 118 | 1.567 | 0.003134 | 0 / 118 |
| BroadcastTo / unresolved | 59 | 2.539 | 0.002539 | 0 / 59 |

## a5_kimi_tp8_e16_bf16_c1_p4k / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 12213 | 16.742 | 3.465522 | 0 / 31329 |
| hcom_reduceScatter_ / attention_output_communication | 4071 | 14.250 | 0.983272 | 0 / 5487 |
| AttnResFwd / unresolved | 4071 | 10.883 | 0.750903 | 0 / 11033 |
| RecurrentKda / unresolved | 4071 | 10.701 | 0.738343 | 0 / 4071 |
| hcom_allGather_ / attention_output_communication | 4071 | 8.508 | 0.587026 | 0 / 5487 |
| CausalConv1d / unresolved | 4071 | 5.221 | 0.360260 | 0 / 4071 |
| PadV3 / unresolved | 4071 | 4.024 | 0.277680 | 0 / 13747 |
| layer_norm_gated_fwd_kernel / unresolved | 4071 | 2.899 | 0.200025 | 0 / 4071 |
| ZerosLike / unresolved | 4071 | 2.615 | 0.180449 | 0 / 5487 |
| Sigmoid / unresolved | 4071 | 2.091 | 0.144288 | 0 / 16402 |
| Cast / unresolved | 4071 | 1.657 | 0.114307 | 0 / 38350 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MlaPrologV3 / unresolved | 1416 | 32.518 | 0.780425 | 0 / 1416 |
| MatMulV3 / unresolved | 2832 | 14.532 | 0.697552 | 0 / 31329 |
| FusedInferAttentionScore / unresolved | 1416 | 16.075 | 0.385805 | 0 / 1416 |
| hcom_reduceScatter_ / attention_output_communication | 1416 | 15.821 | 0.379700 | 0 / 5487 |
| PadV3 / unresolved | 4248 | 3.851 | 0.277258 | 0 / 13747 |
| AttnResFwd / unresolved | 1416 | 11.160 | 0.267848 | 0 / 11033 |
| hcom_allGather_ / attention_output_communication | 1416 | 8.205 | 0.196927 | 0 / 5487 |
| TransposeBatchMatMul / unresolved | 1416 | 5.328 | 0.127880 | 0 / 1416 |
| Mul / unresolved | 1416 | 2.721 | 0.065315 | 0 / 45076 |
| ZerosLike / unresolved | 1416 | 2.613 | 0.062723 | 0 / 5487 |
| Sigmoid / unresolved | 1416 | 2.490 | 0.059758 | 0 / 16402 |
| Cast / unresolved | 1416 | 1.990 | 0.047762 | 0 / 38350 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 12036 | 11.296 | 2.304410 | 0 / 31329 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 4012 | 31.373 | 2.133396 | 0 / 5428 |
| MatMulV3 / latent_down | 4012 | 23.932 | 1.627343 | 5428 / 5428 |
| GroupedMatmul / expert_up | 4012 | 21.905 | 1.489556 | 0 / 5428 |
| MatMulV3 / latent_up | 4012 | 20.609 | 1.401388 | 5428 / 5428 |
| Mul / unresolved | 32332 | 2.373 | 1.300574 | 0 / 45076 |
| GroupedMatmul / expert_down | 4012 | 16.039 | 1.090661 | 0 / 5428 |
| MoeDistributeCombineV3 / expert_combine_native | 4012 | 14.589 | 0.992037 | 0 / 5428 |
| Tanh / unresolved | 16166 | 3.439 | 0.942256 | 0 / 21830 |
| Cast / unresolved | 24249 | 2.224 | 0.914234 | 0 / 38350 |
| hcom_reduceScatter_ / ffn_down_communication | 4071 | 12.535 | 0.864920 | 0 / 5487 |
| Muls / unresolved | 16166 | 3.065 | 0.839764 | 0 / 21830 |
| MatMulV3 / unresolved | 4248 | 11.130 | 0.801368 | 0 / 31329 |
| AttnResFwd / unresolved | 4071 | 10.921 | 0.753518 | 0 / 11033 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 1416 | 31.225 | 0.749407 | 0 / 5428 |
| hcom_allGather_ / ffn_down_communication | 4071 | 9.859 | 0.680247 | 0 / 5546 |
| Slice / unresolved | 8142 | 4.624 | 0.638146 | 0 / 10974 |
| MatMulV3 / latent_down | 1416 | 23.649 | 0.567582 | 5428 / 5428 |
| GroupedMatmul / expert_up | 1416 | 21.953 | 0.526866 | 0 / 5428 |
| Sigmoid / unresolved | 8083 | 3.671 | 0.502896 | 0 / 16402 |
| MatMulV3 / latent_up | 1416 | 20.463 | 0.491113 | 5428 / 5428 |
| Mul / unresolved | 11328 | 2.318 | 0.445144 | 0 / 45076 |
| GroupedMatmul / expert_down | 1416 | 16.063 | 0.385520 | 0 / 5428 |
| MoeDistributeCombineV3 / expert_combine_native | 1416 | 14.416 | 0.345987 | 0 / 5428 |
| Tanh / unresolved | 5664 | 3.489 | 0.334960 | 0 / 21830 |
| Cast / unresolved | 8614 | 2.280 | 0.332819 | 0 / 38350 |
| ForeachAddList / unresolved | 4012 | 4.793 | 0.325894 | 0 / 5428 |
| hcom_reduceScatter_ / ffn_down_communication | 1416 | 12.496 | 0.299896 | 0 / 5487 |
| Muls / unresolved | 5664 | 3.013 | 0.289263 | 0 / 21830 |
| AttnResFwd / unresolved | 1475 | 11.196 | 0.279898 | 0 / 11033 |
| PadV3 / unresolved | 4012 | 3.978 | 0.270488 | 0 / 13747 |
| RmsNorm / latent_norm | 4012 | 3.862 | 0.262632 | 5428 / 5428 |
| hcom_allGather_ / ffn_down_communication | 1475 | 9.577 | 0.239430 | 0 / 5546 |
| Slice / unresolved | 2832 | 4.633 | 0.222381 | 0 / 10974 |
| MoeGatingTopK / unresolved | 4012 | 3.146 | 0.213944 | 0 / 5428 |
| Sigmoid / unresolved | 2832 | 3.940 | 0.189098 | 0 / 16402 |
| ForeachAddList / unresolved | 1416 | 4.743 | 0.113827 | 0 / 5428 |
| RmsNorm / latent_norm | 1416 | 4.014 | 0.096335 | 5428 / 5428 |
| PadV3 / unresolved | 1416 | 3.997 | 0.095922 | 0 / 13747 |
| MoeGatingTopK / unresolved | 1416 | 2.875 | 0.069000 | 0 / 5428 |
| MatMulV3 / gate_up | 59 | 45.165 | 0.045165 | 59 / 59 |
| MatMulV3 / down | 59 | 23.163 | 0.023163 | 59 / 59 |
| Index / unresolved | 59 | 4.549 | 0.004549 | 0 / 59 |
| Fill / unresolved | 118 | 1.585 | 0.003169 | 0 / 118 |
| BroadcastTo / unresolved | 59 | 2.497 | 0.002497 | 0 / 59 |

## a5_kimi_tp8_e16_bf16_c2_p16k / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 11178 | 16.849 | 3.487663 | 0 / 28674 |
| hcom_reduceScatter_ / attention_output_communication | 3726 | 13.568 | 0.936199 | 0 / 5022 |
| RecurrentKda / unresolved | 3726 | 10.990 | 0.758339 | 0 / 3726 |
| AttnResFwd / unresolved | 3726 | 10.904 | 0.752395 | 0 / 10098 |
| hcom_allGather_ / attention_output_communication | 3726 | 9.822 | 0.677719 | 0 / 5022 |
| CausalConv1d / unresolved | 3726 | 5.810 | 0.400885 | 0 / 3726 |
| Slice / unresolved | 7452 | 2.673 | 0.368925 | 0 / 30024 |
| AsStrided / unresolved | 3726 | 4.011 | 0.276775 | 0 / 3726 |
| PadV3 / unresolved | 3726 | 4.005 | 0.276356 | 0 / 12582 |
| layer_norm_gated_fwd_kernel / unresolved | 3726 | 3.430 | 0.236678 | 0 / 3726 |
| ZerosLike / unresolved | 3726 | 2.836 | 0.195687 | 0 / 5022 |
| Sigmoid / unresolved | 3726 | 2.081 | 0.143561 | 0 / 15012 |
| Cast / unresolved | 3726 | 1.653 | 0.114026 | 0 / 35208 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MlaPrologV3 / unresolved | 1296 | 32.727 | 0.785455 | 0 / 1296 |
| FusedInferAttentionScore / unresolved | 1296 | 32.503 | 0.780061 | 0 / 1296 |
| MatMulV3 / unresolved | 2592 | 14.649 | 0.703167 | 0 / 28674 |
| hcom_reduceScatter_ / attention_output_communication | 1296 | 15.041 | 0.360989 | 0 / 5022 |
| PadV3 / unresolved | 3888 | 4.056 | 0.292016 | 0 / 12582 |
| AttnResFwd / unresolved | 1296 | 11.119 | 0.266852 | 0 / 10098 |
| hcom_allGather_ / attention_output_communication | 1296 | 9.732 | 0.233570 | 0 / 5022 |
| Slice / unresolved | 2592 | 2.852 | 0.136905 | 0 / 30024 |
| TransposeBatchMatMul / unresolved | 1296 | 5.426 | 0.130225 | 0 / 1296 |
| Mul / unresolved | 1296 | 2.804 | 0.067297 | 0 / 41256 |
| Sigmoid / unresolved | 1296 | 2.757 | 0.066167 | 0 / 15012 |
| ZerosLike / unresolved | 1296 | 2.663 | 0.063916 | 0 / 5022 |
| Cast / unresolved | 1296 | 1.957 | 0.046961 | 0 / 35208 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MoeDistributeCombineV3 / expert_combine_native | 3672 | 34.932 | 2.375402 | 0 / 4968 |
| MatMulV3 / unresolved | 11016 | 11.395 | 2.324493 | 0 / 28674 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3672 | 31.655 | 2.152521 | 0 / 4968 |
| MatMulV3 / latent_down | 3672 | 23.946 | 1.628342 | 4968 / 4968 |
| GroupedMatmul / expert_up | 3672 | 22.341 | 1.519212 | 0 / 4968 |
| MatMulV3 / latent_up | 3672 | 20.837 | 1.416896 | 4968 / 4968 |
| Mul / unresolved | 29592 | 2.450 | 1.342427 | 0 / 41256 |
| GroupedMatmul / expert_down | 3672 | 16.186 | 1.100639 | 0 / 4968 |
| Slice / unresolved | 14796 | 3.575 | 0.979583 | 0 / 30024 |
| hcom_reduceScatter_ / ffn_down_communication | 3726 | 14.099 | 0.972817 | 0 / 5022 |
| Tanh / unresolved | 14796 | 3.459 | 0.947745 | 0 / 19980 |
| Cast / unresolved | 22194 | 2.196 | 0.902444 | 0 / 35208 |
| Muls / unresolved | 14796 | 3.265 | 0.894639 | 0 / 19980 |
| MatMulV3 / unresolved | 3888 | 11.244 | 0.809533 | 0 / 28674 |
| MoeDistributeCombineV3 / expert_combine_native | 1296 | 33.601 | 0.806436 | 0 / 4968 |
| AttnResFwd / unresolved | 3726 | 10.964 | 0.756493 | 0 / 10098 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 1296 | 31.311 | 0.751453 | 0 / 4968 |
| hcom_allGather_ / ffn_down_communication | 3726 | 10.044 | 0.693003 | 0 / 5076 |
| MatMulV3 / latent_down | 1296 | 23.742 | 0.569808 | 4968 / 4968 |
| GroupedMatmul / expert_up | 1296 | 22.317 | 0.535602 | 0 / 4968 |
| MatMulV3 / latent_up | 1296 | 20.568 | 0.493636 | 4968 / 4968 |
| Mul / unresolved | 10368 | 2.457 | 0.471706 | 0 / 41256 |
| Sigmoid / unresolved | 7398 | 2.984 | 0.408863 | 0 / 15012 |
| GroupedMatmul / expert_down | 1296 | 16.323 | 0.391757 | 0 / 4968 |
| hcom_reduceScatter_ / ffn_down_communication | 1296 | 14.102 | 0.338454 | 0 / 5022 |
| ForeachAddList / unresolved | 3672 | 4.976 | 0.338360 | 0 / 4968 |
| Slice / unresolved | 5184 | 3.431 | 0.329343 | 0 / 30024 |
| Cast / unresolved | 7992 | 2.209 | 0.326909 | 0 / 35208 |
| Tanh / unresolved | 5184 | 3.382 | 0.324637 | 0 / 19980 |
| Muls / unresolved | 5184 | 3.289 | 0.315700 | 0 / 19980 |
| AttnResFwd / unresolved | 1350 | 11.212 | 0.280292 | 0 / 10098 |
| PadV3 / unresolved | 3672 | 3.973 | 0.270196 | 0 / 12582 |
| RmsNorm / latent_norm | 3672 | 3.799 | 0.258349 | 4968 / 4968 |
| hcom_allGather_ / ffn_down_communication | 1350 | 9.805 | 0.245122 | 0 / 5076 |
| MoeGatingTopK / unresolved | 3672 | 2.976 | 0.202388 | 0 / 4968 |
| Sigmoid / unresolved | 2592 | 3.096 | 0.148611 | 0 / 15012 |
| ForeachAddList / unresolved | 1296 | 4.974 | 0.119369 | 0 / 4968 |
| PadV3 / unresolved | 1296 | 3.999 | 0.095987 | 0 / 12582 |
| RmsNorm / latent_norm | 1296 | 3.999 | 0.095973 | 4968 / 4968 |
| MoeGatingTopK / unresolved | 1296 | 2.902 | 0.069641 | 0 / 4968 |
| MatMulV3 / gate_up | 54 | 46.925 | 0.046925 | 54 / 54 |
| MatMulV3 / down | 54 | 23.406 | 0.023406 | 54 / 54 |
| Index / unresolved | 54 | 4.472 | 0.004472 | 0 / 54 |
| BroadcastTo / unresolved | 108 | 1.633 | 0.003265 | 0 / 108 |
| Fill / unresolved | 108 | 1.584 | 0.003169 | 0 / 108 |

## a5_kimi_tp8_e16_bf16_c2_p4k / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 11385 | 16.833 | 3.484444 | 0 / 29205 |
| hcom_reduceScatter_ / attention_output_communication | 3795 | 13.457 | 0.928566 | 0 / 5115 |
| RecurrentKda / unresolved | 3795 | 11.241 | 0.775637 | 0 / 3795 |
| AttnResFwd / unresolved | 3795 | 10.903 | 0.752285 | 0 / 10285 |
| hcom_allGather_ / attention_output_communication | 3795 | 10.069 | 0.694794 | 0 / 5115 |
| CausalConv1d / unresolved | 3795 | 5.814 | 0.401170 | 0 / 3795 |
| Slice / unresolved | 7590 | 2.673 | 0.368895 | 0 / 30580 |
| AsStrided / unresolved | 3795 | 4.018 | 0.277266 | 0 / 3795 |
| PadV3 / unresolved | 3795 | 4.007 | 0.276453 | 0 / 12815 |
| layer_norm_gated_fwd_kernel / unresolved | 3795 | 3.430 | 0.236687 | 0 / 3795 |
| ZerosLike / unresolved | 3795 | 2.830 | 0.195297 | 0 / 5115 |
| Sigmoid / unresolved | 3795 | 2.086 | 0.143967 | 0 / 15290 |
| Cast / unresolved | 3795 | 1.653 | 0.114033 | 0 / 35860 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MlaPrologV3 / unresolved | 1320 | 32.739 | 0.785745 | 0 / 1320 |
| MatMulV3 / unresolved | 2640 | 14.606 | 0.701081 | 0 / 29205 |
| FusedInferAttentionScore / unresolved | 1320 | 18.074 | 0.433774 | 0 / 1320 |
| hcom_reduceScatter_ / attention_output_communication | 1320 | 14.890 | 0.357357 | 0 / 5115 |
| PadV3 / unresolved | 3960 | 4.022 | 0.289573 | 0 / 12815 |
| AttnResFwd / unresolved | 1320 | 11.126 | 0.267021 | 0 / 10285 |
| hcom_allGather_ / attention_output_communication | 1320 | 9.624 | 0.230979 | 0 / 5115 |
| Slice / unresolved | 2640 | 2.849 | 0.136751 | 0 / 30580 |
| TransposeBatchMatMul / unresolved | 1320 | 5.392 | 0.129419 | 0 / 1320 |
| Mul / unresolved | 1320 | 2.812 | 0.067491 | 0 / 42020 |
| Sigmoid / unresolved | 1320 | 2.758 | 0.066195 | 0 / 15290 |
| ZerosLike / unresolved | 1320 | 2.667 | 0.064018 | 0 / 5115 |
| Cast / unresolved | 1320 | 1.956 | 0.046954 | 0 / 35860 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MoeDistributeCombineV3 / expert_combine_native | 3740 | 34.858 | 2.370359 | 0 / 5060 |
| MatMulV3 / unresolved | 11220 | 11.407 | 2.327003 | 0 / 29205 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3740 | 31.621 | 2.150242 | 0 / 5060 |
| MatMulV3 / latent_down | 3740 | 23.948 | 1.628486 | 5060 / 5060 |
| GroupedMatmul / expert_up | 3740 | 22.462 | 1.527384 | 0 / 5060 |
| MatMulV3 / latent_up | 3740 | 20.805 | 1.414760 | 5060 / 5060 |
| Mul / unresolved | 30140 | 2.438 | 1.336285 | 0 / 42020 |
| GroupedMatmul / expert_down | 3740 | 16.192 | 1.101085 | 0 / 5060 |
| Slice / unresolved | 15070 | 3.576 | 0.979769 | 0 / 30580 |
| hcom_reduceScatter_ / ffn_down_communication | 3795 | 14.075 | 0.971203 | 0 / 5115 |
| Tanh / unresolved | 15070 | 3.452 | 0.945902 | 0 / 20350 |
| Cast / unresolved | 22605 | 2.195 | 0.902136 | 0 / 35860 |
| Muls / unresolved | 15070 | 3.292 | 0.902035 | 0 / 20350 |
| MatMulV3 / unresolved | 3960 | 11.260 | 0.810723 | 0 / 29205 |
| MoeDistributeCombineV3 / expert_combine_native | 1320 | 33.472 | 0.803330 | 0 / 5060 |
| AttnResFwd / unresolved | 3795 | 10.975 | 0.757258 | 0 / 10285 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 1320 | 31.280 | 0.750730 | 0 / 5060 |
| hcom_allGather_ / ffn_down_communication | 3795 | 10.074 | 0.695138 | 0 / 5170 |
| MatMulV3 / latent_down | 1320 | 23.802 | 0.571258 | 5060 / 5060 |
| GroupedMatmul / expert_up | 1320 | 22.324 | 0.535773 | 0 / 5060 |
| MatMulV3 / latent_up | 1320 | 20.622 | 0.494922 | 5060 / 5060 |
| Mul / unresolved | 10560 | 2.434 | 0.467406 | 0 / 42020 |
| Sigmoid / unresolved | 7535 | 2.981 | 0.408457 | 0 / 15290 |
| GroupedMatmul / expert_down | 1320 | 16.304 | 0.391307 | 0 / 5060 |
| ForeachAddList / unresolved | 3740 | 4.976 | 0.338351 | 0 / 5060 |
| hcom_reduceScatter_ / ffn_down_communication | 1320 | 14.097 | 0.338335 | 0 / 5115 |
| Slice / unresolved | 5280 | 3.415 | 0.327813 | 0 / 30580 |
| Cast / unresolved | 8140 | 2.209 | 0.326865 | 0 / 35860 |
| Tanh / unresolved | 5280 | 3.389 | 0.325328 | 0 / 20350 |
| Muls / unresolved | 5280 | 3.322 | 0.318959 | 0 / 20350 |
| AttnResFwd / unresolved | 1375 | 11.203 | 0.280072 | 0 / 10285 |
| PadV3 / unresolved | 3740 | 3.970 | 0.269985 | 0 / 12815 |
| RmsNorm / latent_norm | 3740 | 3.800 | 0.258401 | 5060 / 5060 |
| hcom_allGather_ / ffn_down_communication | 1375 | 9.850 | 0.246244 | 0 / 5170 |
| MoeGatingTopK / unresolved | 3740 | 2.979 | 0.202581 | 0 / 5060 |
| Sigmoid / unresolved | 2640 | 3.112 | 0.149373 | 0 / 15290 |
| ForeachAddList / unresolved | 1320 | 4.973 | 0.119350 | 0 / 5060 |
| RmsNorm / latent_norm | 1320 | 3.997 | 0.095927 | 5060 / 5060 |
| PadV3 / unresolved | 1320 | 3.996 | 0.095907 | 0 / 12815 |
| MoeGatingTopK / unresolved | 1320 | 2.897 | 0.069530 | 0 / 5060 |
| MatMulV3 / gate_up | 55 | 46.726 | 0.046726 | 55 / 55 |
| MatMulV3 / down | 55 | 23.565 | 0.023565 | 55 / 55 |
| Index / unresolved | 55 | 4.564 | 0.004564 | 0 / 55 |
| Fill / unresolved | 110 | 1.628 | 0.003256 | 0 / 110 |
| BroadcastTo / unresolved | 110 | 1.528 | 0.003056 | 0 / 110 |

## a5_kimi_tp8_e16_bf16_c32_p16k / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 5658 | 21.498 | 2.966707 | 0 / 10414 |
| RecurrentKda / unresolved | 2829 | 30.551 | 2.108002 | 0 / 2829 |
| hcom_reduceScatter_ / attention_output_communication | 2829 | 15.995 | 1.103678 | 0 / 3813 |
| MatMulV3 / linear_output | 2829 | 13.836 | 0.954697 | 2829 / 2829 |
| AttnResFwd / unresolved | 2829 | 11.421 | 0.788027 | 0 / 7667 |
| hcom_allGather_ / attention_output_communication | 2829 | 11.195 | 0.772470 | 0 / 3813 |
| CausalConv1d / unresolved | 2829 | 10.981 | 0.757705 | 0 / 2829 |
| Slice / unresolved | 5658 | 3.493 | 0.482042 | 0 / 22796 |
| AsStrided / unresolved | 2829 | 4.873 | 0.336227 | 0 / 2829 |
| layer_norm_gated_fwd_kernel / unresolved | 2829 | 3.576 | 0.246772 | 0 / 2829 |
| ZerosLike / unresolved | 2829 | 3.290 | 0.226978 | 0 / 3813 |
| Sigmoid / unresolved | 2829 | 2.172 | 0.149860 | 0 / 11398 |
| Cast / unresolved | 2829 | 1.758 | 0.121308 | 0 / 26650 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| FusedInferAttentionScore / unresolved | 984 | 264.091 | 6.338186 | 0 / 984 |
| MlaPrologV3 / unresolved | 984 | 41.668 | 1.000038 | 0 / 984 |
| hcom_reduceScatter_ / attention_output_communication | 984 | 20.701 | 0.496822 | 0 / 3813 |
| MatMulV3 / q_a | 984 | 19.244 | 0.461855 | 984 / 984 |
| MatMulV3 / unresolved | 984 | 14.090 | 0.338153 | 0 / 10414 |
| AttnResFwd / unresolved | 984 | 11.616 | 0.278774 | 0 / 7667 |
| hcom_allGather_ / attention_output_communication | 984 | 10.645 | 0.255490 | 0 / 3813 |
| PadV3 / unresolved | 1968 | 4.530 | 0.217460 | 0 / 1968 |
| Slice / unresolved | 1968 | 3.946 | 0.189418 | 0 / 22796 |
| TransposeBatchMatMul / unresolved | 984 | 5.608 | 0.134588 | 0 / 984 |
| Sigmoid / unresolved | 984 | 3.658 | 0.087793 | 0 / 11398 |
| Mul / unresolved | 984 | 3.361 | 0.080659 | 0 / 31324 |
| ZerosLike / unresolved | 984 | 3.208 | 0.076993 | 0 / 3813 |
| Cast / unresolved | 984 | 1.898 | 0.045553 | 0 / 26650 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| GroupedMatmul / expert_up | 2788 | 47.327 | 3.218207 | 0 / 3772 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 2788 | 34.501 | 2.346072 | 0 / 3772 |
| MatMulV3 / latent_down | 2788 | 27.415 | 1.864236 | 3772 / 3772 |
| MatMulV3 / latent_up | 2788 | 22.713 | 1.544515 | 3772 / 3772 |
| MatMulV3 / shared.gate_up | 2788 | 22.520 | 1.531368 | 3772 / 3772 |
| GroupedMatmul / expert_down | 2788 | 22.302 | 1.516547 | 0 / 3772 |
| Mul / unresolved | 22468 | 2.513 | 1.376864 | 0 / 31324 |
| Cast / unresolved | 16851 | 2.935 | 1.206369 | 0 / 26650 |
| Tanh / unresolved | 11234 | 4.251 | 1.164696 | 0 / 15170 |
| hcom_reduceScatter_ / ffn_down_communication | 2829 | 15.784 | 1.089104 | 0 / 3813 |
| Muls / unresolved | 11234 | 3.952 | 1.082816 | 0 / 15170 |
| GroupedMatmul / expert_up | 984 | 43.083 | 1.033997 | 0 / 3772 |
| Slice / unresolved | 11234 | 3.767 | 1.032206 | 0 / 22796 |
| MoeDistributeCombineV3 / expert_combine_native | 2788 | 14.571 | 0.990855 | 0 / 3772 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 984 | 33.375 | 0.801012 | 0 / 3772 |
| AttnResFwd / unresolved | 2829 | 11.318 | 0.780951 | 0 / 7667 |
| hcom_allGather_ / ffn_down_communication | 2829 | 10.770 | 0.743133 | 0 / 3854 |
| MatMulV3 / shared.down | 2788 | 9.555 | 0.649707 | 3772 / 3772 |
| MatMulV3 / latent_down | 984 | 25.347 | 0.608319 | 3772 / 3772 |
| Sigmoid / unresolved | 5617 | 3.948 | 0.540927 | 0 / 11398 |
| MatMulV3 / latent_up | 984 | 22.506 | 0.540144 | 3772 / 3772 |
| MatMulV3 / unresolved | 2788 | 7.585 | 0.515801 | 0 / 10414 |
| MatMulV3 / shared.gate_up | 984 | 21.327 | 0.511853 | 3772 / 3772 |
| GroupedMatmul / expert_down | 984 | 21.167 | 0.508014 | 0 / 3772 |
| Mul / unresolved | 7872 | 2.434 | 0.467399 | 0 / 31324 |
| Cast / unresolved | 5986 | 2.923 | 0.426697 | 0 / 26650 |
| Tanh / unresolved | 3936 | 4.150 | 0.398423 | 0 / 15170 |
| ForeachAddList / unresolved | 2788 | 5.813 | 0.395302 | 0 / 3772 |
| hcom_reduceScatter_ / ffn_down_communication | 984 | 16.030 | 0.384729 | 0 / 3813 |
| Muls / unresolved | 3936 | 3.875 | 0.372016 | 0 / 15170 |
| MoeDistributeCombineV3 / expert_combine_native | 984 | 14.738 | 0.353721 | 0 / 3772 |
| Slice / unresolved | 3936 | 3.651 | 0.350478 | 0 / 22796 |
| RmsNorm / latent_norm | 2788 | 4.287 | 0.291524 | 3772 / 3772 |
| AttnResFwd / unresolved | 1025 | 11.361 | 0.284034 | 0 / 7667 |
| hcom_allGather_ / ffn_down_communication | 1025 | 10.703 | 0.267569 | 0 / 3854 |
| MoeGatingTopK / unresolved | 2788 | 3.518 | 0.239205 | 0 / 3772 |
| MatMulV3 / shared.down | 984 | 9.448 | 0.226759 | 3772 / 3772 |
| Sigmoid / unresolved | 1968 | 3.960 | 0.190099 | 0 / 11398 |
| MatMulV3 / unresolved | 984 | 7.596 | 0.182305 | 0 / 10414 |
| ForeachAddList / unresolved | 984 | 5.801 | 0.139230 | 0 / 3772 |
| RmsNorm / latent_norm | 984 | 4.263 | 0.102309 | 3772 / 3772 |
| MoeGatingTopK / unresolved | 984 | 3.498 | 0.083952 | 0 / 3772 |
| MatMulV3 / gate_up | 41 | 59.157 | 0.059157 | 41 / 41 |
| MatMulV3 / down | 41 | 27.331 | 0.027331 | 41 / 41 |
| Index / unresolved | 41 | 5.823 | 0.005823 | 0 / 41 |
| TensorMove / unresolved | 41 | 3.933 | 0.003933 | 0 / 41 |
| Fill / unresolved | 82 | 1.683 | 0.003367 | 0 / 82 |
| BroadcastTo / unresolved | 41 | 2.351 | 0.002351 | 0 / 41 |

## a5_kimi_tp8_e16_bf16_c32_p4k / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 6348 | 21.497 | 2.966625 | 0 / 11684 |
| RecurrentKda / unresolved | 3174 | 30.461 | 2.101811 | 0 / 3174 |
| hcom_reduceScatter_ / attention_output_communication | 3174 | 15.932 | 1.099313 | 0 / 4278 |
| MatMulV3 / linear_output | 3174 | 13.776 | 0.950570 | 3174 / 3174 |
| AttnResFwd / unresolved | 3174 | 11.421 | 0.788048 | 0 / 8602 |
| CausalConv1d / unresolved | 3174 | 10.930 | 0.754190 | 0 / 3174 |
| hcom_allGather_ / attention_output_communication | 3174 | 10.792 | 0.744669 | 0 / 4278 |
| Slice / unresolved | 6348 | 3.491 | 0.481787 | 0 / 25576 |
| AsStrided / unresolved | 3174 | 4.869 | 0.335995 | 0 / 3174 |
| layer_norm_gated_fwd_kernel / unresolved | 3174 | 3.579 | 0.246972 | 0 / 3174 |
| ZerosLike / unresolved | 3174 | 3.283 | 0.226510 | 0 / 4278 |
| Sigmoid / unresolved | 3174 | 2.173 | 0.149962 | 0 / 12788 |
| Cast / unresolved | 3174 | 1.762 | 0.121560 | 0 / 29900 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| FusedInferAttentionScore / unresolved | 1104 | 74.792 | 1.795006 | 0 / 1104 |
| MlaPrologV3 / unresolved | 1104 | 41.661 | 0.999866 | 0 / 1104 |
| MatMulV3 / q_a | 1104 | 19.252 | 0.462050 | 1104 / 1104 |
| hcom_reduceScatter_ / attention_output_communication | 1104 | 18.328 | 0.439883 | 0 / 4278 |
| MatMulV3 / unresolved | 1104 | 14.073 | 0.337756 | 0 / 11684 |
| AttnResFwd / unresolved | 1104 | 11.613 | 0.278704 | 0 / 8602 |
| hcom_allGather_ / attention_output_communication | 1104 | 10.665 | 0.255967 | 0 / 4278 |
| PadV3 / unresolved | 2208 | 4.528 | 0.217367 | 0 / 2208 |
| Slice / unresolved | 2208 | 3.952 | 0.189684 | 0 / 25576 |
| TransposeBatchMatMul / unresolved | 1104 | 5.589 | 0.134135 | 0 / 1104 |
| Sigmoid / unresolved | 1104 | 3.657 | 0.087775 | 0 / 12788 |
| Mul / unresolved | 1104 | 3.365 | 0.080771 | 0 / 35144 |
| ZerosLike / unresolved | 1104 | 3.209 | 0.077009 | 0 / 4278 |
| Cast / unresolved | 1104 | 1.898 | 0.045545 | 0 / 29900 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| GroupedMatmul / expert_up | 3128 | 47.354 | 3.220059 | 0 / 4232 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3128 | 34.475 | 2.344293 | 0 / 4232 |
| MatMulV3 / latent_down | 3128 | 27.416 | 1.864313 | 4232 / 4232 |
| MatMulV3 / latent_up | 3128 | 22.707 | 1.544081 | 4232 / 4232 |
| MatMulV3 / shared.gate_up | 3128 | 22.516 | 1.531059 | 4232 / 4232 |
| GroupedMatmul / expert_down | 3128 | 22.315 | 1.517393 | 0 / 4232 |
| Mul / unresolved | 25208 | 2.512 | 1.376832 | 0 / 35144 |
| Cast / unresolved | 18906 | 2.935 | 1.206201 | 0 / 29900 |
| Tanh / unresolved | 12604 | 4.251 | 1.164760 | 0 / 17020 |
| hcom_reduceScatter_ / ffn_down_communication | 3174 | 15.730 | 1.085379 | 0 / 4278 |
| Muls / unresolved | 12604 | 3.948 | 1.081739 | 0 / 17020 |
| GroupedMatmul / expert_up | 1104 | 43.074 | 1.033778 | 0 / 4232 |
| Slice / unresolved | 12604 | 3.766 | 1.032004 | 0 / 25576 |
| MoeDistributeCombineV3 / expert_combine_native | 3128 | 14.526 | 0.987788 | 0 / 4232 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 1104 | 33.410 | 0.801831 | 0 / 4232 |
| AttnResFwd / unresolved | 3174 | 11.324 | 0.781373 | 0 / 8602 |
| hcom_allGather_ / ffn_down_communication | 3174 | 10.712 | 0.739147 | 0 / 4324 |
| MatMulV3 / shared.down | 3128 | 9.574 | 0.651066 | 4232 / 4232 |
| MatMulV3 / latent_down | 1104 | 25.342 | 0.608217 | 4232 / 4232 |
| MatMulV3 / latent_up | 1104 | 22.491 | 0.539776 | 4232 / 4232 |
| Sigmoid / unresolved | 6302 | 3.939 | 0.539654 | 0 / 12788 |
| MatMulV3 / unresolved | 3128 | 7.586 | 0.515874 | 0 / 11684 |
| MatMulV3 / shared.gate_up | 1104 | 21.341 | 0.512195 | 4232 / 4232 |
| GroupedMatmul / expert_down | 1104 | 21.170 | 0.508081 | 0 / 4232 |
| Mul / unresolved | 8832 | 2.437 | 0.467857 | 0 / 35144 |
| Cast / unresolved | 6716 | 2.919 | 0.426235 | 0 / 29900 |
| Tanh / unresolved | 4416 | 4.151 | 0.398485 | 0 / 17020 |
| ForeachAddList / unresolved | 3128 | 5.811 | 0.395137 | 0 / 4232 |
| hcom_reduceScatter_ / ffn_down_communication | 1104 | 16.007 | 0.384174 | 0 / 4278 |
| Muls / unresolved | 4416 | 3.865 | 0.371026 | 0 / 17020 |
| MoeDistributeCombineV3 / expert_combine_native | 1104 | 14.746 | 0.353902 | 0 / 4232 |
| Slice / unresolved | 4416 | 3.646 | 0.350000 | 0 / 25576 |
| RmsNorm / latent_norm | 3128 | 4.291 | 0.291817 | 4232 / 4232 |
| AttnResFwd / unresolved | 1150 | 11.369 | 0.284230 | 0 / 8602 |
| hcom_allGather_ / ffn_down_communication | 1150 | 10.723 | 0.268078 | 0 / 4324 |
| MoeGatingTopK / unresolved | 3128 | 3.516 | 0.239069 | 0 / 4232 |
| MatMulV3 / shared.down | 1104 | 9.441 | 0.226577 | 4232 / 4232 |
| Sigmoid / unresolved | 2208 | 3.956 | 0.189886 | 0 / 12788 |
| MatMulV3 / unresolved | 1104 | 7.574 | 0.181766 | 0 / 11684 |
| ForeachAddList / unresolved | 1104 | 5.797 | 0.139120 | 0 / 4232 |
| RmsNorm / latent_norm | 1104 | 4.266 | 0.102394 | 4232 / 4232 |
| MoeGatingTopK / unresolved | 1104 | 3.501 | 0.084025 | 0 / 4232 |
| MatMulV3 / gate_up | 46 | 59.094 | 0.059094 | 46 / 46 |
| MatMulV3 / down | 46 | 27.431 | 0.027431 | 46 / 46 |
| Index / unresolved | 46 | 5.696 | 0.005696 | 0 / 46 |
| TensorMove / unresolved | 46 | 3.987 | 0.003987 | 0 / 46 |
| Fill / unresolved | 92 | 1.702 | 0.003404 | 0 / 92 |
| BroadcastTo / unresolved | 46 | 2.461 | 0.002461 | 0 / 46 |

## a5_kimi_tp8_e16_bf16_c4_p16k / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 10764 | 16.899 | 3.498117 | 0 / 27612 |
| hcom_reduceScatter_ / attention_output_communication | 3588 | 13.830 | 0.954248 | 0 / 4836 |
| RecurrentKda / unresolved | 3588 | 11.858 | 0.818202 | 0 / 3588 |
| AttnResFwd / unresolved | 3588 | 10.921 | 0.753553 | 0 / 9724 |
| hcom_allGather_ / attention_output_communication | 3588 | 9.942 | 0.686015 | 0 / 4836 |
| CausalConv1d / unresolved | 3588 | 6.929 | 0.478091 | 0 / 3588 |
| Slice / unresolved | 7176 | 2.948 | 0.406841 | 0 / 28912 |
| PadV3 / unresolved | 3588 | 4.039 | 0.278719 | 0 / 12116 |
| AsStrided / unresolved | 3588 | 4.020 | 0.277365 | 0 / 3588 |
| layer_norm_gated_fwd_kernel / unresolved | 3588 | 3.437 | 0.237141 | 0 / 3588 |
| ZerosLike / unresolved | 3588 | 2.871 | 0.198127 | 0 / 4836 |
| Sigmoid / unresolved | 3588 | 2.120 | 0.146312 | 0 / 14456 |
| Cast / unresolved | 3588 | 1.724 | 0.118924 | 0 / 33904 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| FusedInferAttentionScore / unresolved | 1248 | 48.025 | 1.152601 | 0 / 1248 |
| MlaPrologV3 / unresolved | 1248 | 32.878 | 0.789072 | 0 / 1248 |
| MatMulV3 / unresolved | 2496 | 14.775 | 0.709183 | 0 / 27612 |
| hcom_reduceScatter_ / attention_output_communication | 1248 | 15.219 | 0.365257 | 0 / 4836 |
| PadV3 / unresolved | 3744 | 4.169 | 0.300178 | 0 / 12116 |
| AttnResFwd / unresolved | 1248 | 11.092 | 0.266211 | 0 / 9724 |
| hcom_allGather_ / attention_output_communication | 1248 | 9.677 | 0.232243 | 0 / 4836 |
| Slice / unresolved | 2496 | 3.391 | 0.162774 | 0 / 28912 |
| TransposeBatchMatMul / unresolved | 1248 | 5.338 | 0.128110 | 0 / 1248 |
| Mul / unresolved | 1248 | 2.986 | 0.071674 | 0 / 39728 |
| ZerosLike / unresolved | 1248 | 2.805 | 0.067309 | 0 / 4836 |
| Sigmoid / unresolved | 1248 | 2.790 | 0.066954 | 0 / 14456 |
| Cast / unresolved | 1248 | 1.936 | 0.046469 | 0 / 33904 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| GroupedMatmul / expert_up | 3536 | 41.747 | 2.838823 | 0 / 4784 |
| MatMulV3 / unresolved | 10608 | 11.778 | 2.402763 | 0 / 27612 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3536 | 31.948 | 2.172451 | 0 / 4784 |
| MatMulV3 / latent_down | 3536 | 24.446 | 1.662333 | 4784 / 4784 |
| MatMulV3 / latent_up | 3536 | 20.973 | 1.426174 | 4784 / 4784 |
| GroupedMatmul / expert_down | 3536 | 20.190 | 1.372915 | 0 / 4784 |
| Mul / unresolved | 28496 | 2.167 | 1.187361 | 0 / 39728 |
| MoeDistributeCombineV3 / expert_combine_native | 3536 | 14.381 | 0.977912 | 0 / 4784 |
| GroupedMatmul / expert_up | 1248 | 40.690 | 0.976549 | 0 / 4784 |
| Slice / unresolved | 14248 | 3.549 | 0.972349 | 0 / 28912 |
| Tanh / unresolved | 14248 | 3.539 | 0.969789 | 0 / 19240 |
| hcom_reduceScatter_ / ffn_down_communication | 3588 | 13.725 | 0.947010 | 0 / 4836 |
| Muls / unresolved | 14248 | 3.371 | 0.923786 | 0 / 19240 |
| Cast / unresolved | 21372 | 2.217 | 0.910992 | 0 / 33904 |
| MatMulV3 / unresolved | 3744 | 11.638 | 0.837926 | 0 / 27612 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 1248 | 31.626 | 0.759013 | 0 / 4784 |
| AttnResFwd / unresolved | 3588 | 10.966 | 0.756688 | 0 / 9724 |
| hcom_allGather_ / ffn_down_communication | 3588 | 9.867 | 0.680836 | 0 / 4888 |
| MatMulV3 / latent_down | 1248 | 23.660 | 0.567851 | 4784 / 4784 |
| MatMulV3 / latent_up | 1248 | 20.906 | 0.501756 | 4784 / 4784 |
| GroupedMatmul / expert_down | 1248 | 19.836 | 0.476053 | 0 / 4784 |
| Sigmoid / unresolved | 7124 | 3.265 | 0.447297 | 0 / 14456 |
| Mul / unresolved | 9984 | 2.156 | 0.414035 | 0 / 39728 |
| ForeachAddList / unresolved | 3536 | 5.320 | 0.361733 | 0 / 4784 |
| MoeDistributeCombineV3 / expert_combine_native | 1248 | 14.215 | 0.341151 | 0 / 4784 |
| Tanh / unresolved | 4992 | 3.551 | 0.340888 | 0 / 19240 |
| hcom_reduceScatter_ / ffn_down_communication | 1248 | 13.751 | 0.330032 | 0 / 4836 |
| Cast / unresolved | 7696 | 2.200 | 0.325574 | 0 / 33904 |
| Slice / unresolved | 4992 | 3.382 | 0.324651 | 0 / 28912 |
| Muls / unresolved | 4992 | 3.326 | 0.319270 | 0 / 19240 |
| AttnResFwd / unresolved | 1300 | 11.283 | 0.282064 | 0 / 9724 |
| PadV3 / unresolved | 3536 | 4.070 | 0.276733 | 0 / 12116 |
| RmsNorm / latent_norm | 3536 | 3.790 | 0.257700 | 4784 / 4784 |
| hcom_allGather_ / ffn_down_communication | 1300 | 9.622 | 0.240559 | 0 / 4888 |
| MoeGatingTopK / unresolved | 3536 | 3.053 | 0.207613 | 0 / 4784 |
| Sigmoid / unresolved | 2496 | 3.345 | 0.160569 | 0 / 14456 |
| ForeachAddList / unresolved | 1248 | 5.296 | 0.127111 | 0 / 4784 |
| PadV3 / unresolved | 1248 | 4.072 | 0.097722 | 0 / 12116 |
| RmsNorm / latent_norm | 1248 | 3.791 | 0.090993 | 4784 / 4784 |
| MoeGatingTopK / unresolved | 1248 | 3.054 | 0.073285 | 0 / 4784 |
| MatMulV3 / gate_up | 52 | 47.970 | 0.047970 | 52 / 52 |
| MatMulV3 / down | 52 | 24.444 | 0.024444 | 52 / 52 |
| Index / unresolved | 52 | 4.797 | 0.004797 | 0 / 52 |
| Fill / unresolved | 104 | 1.638 | 0.003276 | 0 / 104 |
| BroadcastTo / unresolved | 104 | 1.592 | 0.003185 | 0 / 104 |

## a5_kimi_tp8_e16_bf16_c4_p4k / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 10971 | 16.898 | 3.497959 | 0 / 28143 |
| hcom_reduceScatter_ / attention_output_communication | 3657 | 13.810 | 0.952903 | 0 / 4929 |
| RecurrentKda / unresolved | 3657 | 11.919 | 0.822379 | 0 / 3657 |
| AttnResFwd / unresolved | 3657 | 10.942 | 0.754988 | 0 / 9911 |
| hcom_allGather_ / attention_output_communication | 3657 | 9.843 | 0.679145 | 0 / 4929 |
| CausalConv1d / unresolved | 3657 | 6.919 | 0.477437 | 0 / 3657 |
| Slice / unresolved | 7314 | 2.948 | 0.406857 | 0 / 29468 |
| PadV3 / unresolved | 3657 | 4.056 | 0.279896 | 0 / 12349 |
| AsStrided / unresolved | 3657 | 4.018 | 0.277249 | 0 / 3657 |
| layer_norm_gated_fwd_kernel / unresolved | 3657 | 3.436 | 0.237116 | 0 / 3657 |
| ZerosLike / unresolved | 3657 | 2.871 | 0.198067 | 0 / 4929 |
| Sigmoid / unresolved | 3657 | 2.122 | 0.146392 | 0 / 14734 |
| Cast / unresolved | 3657 | 1.721 | 0.118716 | 0 / 34556 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MlaPrologV3 / unresolved | 1272 | 32.878 | 0.789074 | 0 / 1272 |
| MatMulV3 / unresolved | 2544 | 14.848 | 0.712715 | 0 / 28143 |
| FusedInferAttentionScore / unresolved | 1272 | 23.007 | 0.552166 | 0 / 1272 |
| hcom_reduceScatter_ / attention_output_communication | 1272 | 14.761 | 0.354272 | 0 / 4929 |
| PadV3 / unresolved | 3816 | 4.140 | 0.298047 | 0 / 12349 |
| AttnResFwd / unresolved | 1272 | 11.092 | 0.266219 | 0 / 9911 |
| hcom_allGather_ / attention_output_communication | 1272 | 9.748 | 0.233943 | 0 / 4929 |
| Slice / unresolved | 2544 | 3.392 | 0.162793 | 0 / 29468 |
| TransposeBatchMatMul / unresolved | 1272 | 5.339 | 0.128137 | 0 / 1272 |
| Mul / unresolved | 1272 | 2.982 | 0.071566 | 0 / 40492 |
| ZerosLike / unresolved | 1272 | 2.812 | 0.067495 | 0 / 4929 |
| Sigmoid / unresolved | 1272 | 2.810 | 0.067439 | 0 / 14734 |
| Cast / unresolved | 1272 | 1.936 | 0.046456 | 0 / 34556 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| GroupedMatmul / expert_up | 3604 | 41.531 | 2.824118 | 0 / 4876 |
| MatMulV3 / unresolved | 10812 | 11.776 | 2.402388 | 0 / 28143 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3604 | 31.922 | 2.170697 | 0 / 4876 |
| MatMulV3 / latent_down | 3604 | 24.524 | 1.667663 | 4876 / 4876 |
| MatMulV3 / latent_up | 3604 | 20.964 | 1.425542 | 4876 / 4876 |
| GroupedMatmul / expert_down | 3604 | 20.191 | 1.372955 | 0 / 4876 |
| Mul / unresolved | 29044 | 2.141 | 1.173249 | 0 / 40492 |
| MoeDistributeCombineV3 / expert_combine_native | 3604 | 14.523 | 0.987543 | 0 / 4876 |
| Slice / unresolved | 14522 | 3.548 | 0.972098 | 0 / 29468 |
| GroupedMatmul / expert_up | 1272 | 40.412 | 0.969882 | 0 / 4876 |
| Tanh / unresolved | 14522 | 3.536 | 0.968813 | 0 / 19610 |
| hcom_reduceScatter_ / ffn_down_communication | 3657 | 13.702 | 0.945462 | 0 / 4929 |
| Muls / unresolved | 14522 | 3.375 | 0.924728 | 0 / 19610 |
| Cast / unresolved | 21783 | 2.223 | 0.913595 | 0 / 34556 |
| MatMulV3 / unresolved | 3816 | 11.645 | 0.838433 | 0 / 28143 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 1272 | 31.616 | 0.758791 | 0 / 4876 |
| AttnResFwd / unresolved | 3657 | 10.953 | 0.755779 | 0 / 9911 |
| hcom_allGather_ / ffn_down_communication | 3657 | 9.941 | 0.685950 | 0 / 4982 |
| MatMulV3 / latent_down | 1272 | 23.629 | 0.567093 | 4876 / 4876 |
| MatMulV3 / latent_up | 1272 | 20.909 | 0.501822 | 4876 / 4876 |
| GroupedMatmul / expert_down | 1272 | 19.712 | 0.473099 | 0 / 4876 |
| Sigmoid / unresolved | 7261 | 3.262 | 0.446881 | 0 / 14734 |
| Mul / unresolved | 10176 | 2.124 | 0.407737 | 0 / 40492 |
| ForeachAddList / unresolved | 3604 | 5.312 | 0.361232 | 0 / 4876 |
| MoeDistributeCombineV3 / expert_combine_native | 1272 | 14.236 | 0.341654 | 0 / 4876 |
| Tanh / unresolved | 5088 | 3.546 | 0.340462 | 0 / 19610 |
| hcom_reduceScatter_ / ffn_down_communication | 1272 | 13.746 | 0.329898 | 0 / 4929 |
| Cast / unresolved | 7844 | 2.199 | 0.325505 | 0 / 34556 |
| Slice / unresolved | 5088 | 3.389 | 0.325340 | 0 / 29468 |
| Muls / unresolved | 5088 | 3.319 | 0.318587 | 0 / 19610 |
| AttnResFwd / unresolved | 1325 | 11.269 | 0.281727 | 0 / 9911 |
| PadV3 / unresolved | 3604 | 4.067 | 0.276584 | 0 / 12349 |
| RmsNorm / latent_norm | 3604 | 3.790 | 0.257688 | 4876 / 4876 |
| hcom_allGather_ / ffn_down_communication | 1325 | 9.703 | 0.242564 | 0 / 4982 |
| MoeGatingTopK / unresolved | 3604 | 3.053 | 0.207627 | 0 / 4876 |
| Sigmoid / unresolved | 2544 | 3.348 | 0.160716 | 0 / 14734 |
| ForeachAddList / unresolved | 1272 | 5.295 | 0.127081 | 0 / 4876 |
| PadV3 / unresolved | 1272 | 4.061 | 0.097452 | 0 / 12349 |
| RmsNorm / latent_norm | 1272 | 3.791 | 0.090983 | 4876 / 4876 |
| MoeGatingTopK / unresolved | 1272 | 3.040 | 0.072966 | 0 / 4876 |
| MatMulV3 / gate_up | 53 | 48.255 | 0.048255 | 53 / 53 |
| MatMulV3 / down | 53 | 23.717 | 0.023717 | 53 / 53 |
| Index / unresolved | 53 | 4.732 | 0.004732 | 0 / 53 |
| Fill / unresolved | 106 | 1.618 | 0.003235 | 0 / 106 |
| BroadcastTo / unresolved | 106 | 1.598 | 0.003196 | 0 / 106 |

## a5_kimi_tp8_e16_bf16_c8_p16k / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 7038 | 19.580 | 2.701984 | 0 / 12954 |
| RecurrentKda / unresolved | 3519 | 15.605 | 1.076779 | 0 / 3519 |
| hcom_reduceScatter_ / attention_output_communication | 3519 | 14.099 | 0.972826 | 0 / 4743 |
| MatMulV3 / linear_output | 3519 | 11.974 | 0.826182 | 3519 / 3519 |
| AttnResFwd / unresolved | 3519 | 10.977 | 0.757436 | 0 / 9537 |
| hcom_allGather_ / attention_output_communication | 3519 | 10.340 | 0.713479 | 0 / 4743 |
| CausalConv1d / unresolved | 3519 | 7.058 | 0.486969 | 0 / 3519 |
| Slice / unresolved | 7038 | 3.390 | 0.467874 | 0 / 28356 |
| AsStrided / unresolved | 3519 | 4.068 | 0.280668 | 0 / 3519 |
| layer_norm_gated_fwd_kernel / unresolved | 3519 | 3.431 | 0.236766 | 0 / 3519 |
| ZerosLike / unresolved | 3519 | 2.953 | 0.203786 | 0 / 4743 |
| Sigmoid / unresolved | 3519 | 2.084 | 0.143811 | 0 / 14178 |
| Cast / unresolved | 3519 | 1.672 | 0.115382 | 0 / 33150 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| FusedInferAttentionScore / unresolved | 1224 | 79.395 | 1.905489 | 0 / 1224 |
| MlaPrologV3 / unresolved | 1224 | 33.425 | 0.802206 | 0 / 1224 |
| MatMulV3 / q_a | 1224 | 18.792 | 0.451018 | 1224 / 1224 |
| hcom_reduceScatter_ / attention_output_communication | 1224 | 15.699 | 0.376775 | 0 / 4743 |
| MatMulV3 / unresolved | 1224 | 12.287 | 0.294876 | 0 / 12954 |
| AttnResFwd / unresolved | 1224 | 11.208 | 0.269003 | 0 / 9537 |
| hcom_allGather_ / attention_output_communication | 1224 | 10.295 | 0.247088 | 0 / 4743 |
| Slice / unresolved | 2448 | 3.686 | 0.176926 | 0 / 28356 |
| PadV3 / unresolved | 2448 | 3.626 | 0.174050 | 0 / 2448 |
| TransposeBatchMatMul / unresolved | 1224 | 5.417 | 0.129997 | 0 / 1224 |
| Mul / unresolved | 1224 | 3.161 | 0.075860 | 0 / 38964 |
| Sigmoid / unresolved | 1224 | 3.063 | 0.073522 | 0 / 14178 |
| ZerosLike / unresolved | 1224 | 2.886 | 0.069254 | 0 / 4743 |
| Cast / unresolved | 1224 | 1.918 | 0.046028 | 0 / 33150 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| GroupedMatmul / expert_up | 3468 | 43.152 | 2.934311 | 0 / 4692 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3468 | 33.123 | 2.252352 | 0 / 4692 |
| MatMulV3 / latent_down | 3468 | 24.670 | 1.677526 | 4692 / 4692 |
| MatMulV3 / latent_up | 3468 | 21.065 | 1.432442 | 4692 / 4692 |
| GroupedMatmul / expert_down | 3468 | 20.706 | 1.408027 | 0 / 4692 |
| MatMulV3 / shared.gate_up | 3468 | 20.191 | 1.372994 | 4692 / 4692 |
| Mul / unresolved | 27948 | 2.240 | 1.227606 | 0 / 38964 |
| GroupedMatmul / expert_up | 1224 | 41.352 | 0.992437 | 0 / 4692 |
| MoeDistributeCombineV3 / expert_combine_native | 3468 | 14.494 | 0.985586 | 0 / 4692 |
| Slice / unresolved | 13974 | 3.575 | 0.979598 | 0 / 28356 |
| hcom_reduceScatter_ / ffn_down_communication | 3519 | 14.186 | 0.978863 | 0 / 4743 |
| Tanh / unresolved | 13974 | 3.557 | 0.974561 | 0 / 18870 |
| Muls / unresolved | 13974 | 3.421 | 0.937362 | 0 / 18870 |
| Cast / unresolved | 20961 | 2.273 | 0.934130 | 0 / 33150 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 1224 | 32.584 | 0.782013 | 0 / 4692 |
| AttnResFwd / unresolved | 3519 | 10.894 | 0.751655 | 0 / 9537 |
| hcom_allGather_ / ffn_down_communication | 3519 | 10.004 | 0.690297 | 0 / 4794 |
| MatMulV3 / latent_down | 1224 | 23.755 | 0.570126 | 4692 / 4692 |
| MatMulV3 / shared.down | 3468 | 8.377 | 0.569658 | 4692 / 4692 |
| MatMulV3 / unresolved | 3468 | 7.800 | 0.530377 | 0 / 12954 |
| MatMulV3 / latent_up | 1224 | 20.936 | 0.502469 | 4692 / 4692 |
| GroupedMatmul / expert_down | 1224 | 20.183 | 0.484390 | 0 / 4692 |
| MatMulV3 / shared.gate_up | 1224 | 19.612 | 0.470682 | 4692 / 4692 |
| Sigmoid / unresolved | 6987 | 3.263 | 0.447062 | 0 / 14178 |
| Mul / unresolved | 9792 | 2.225 | 0.427195 | 0 / 38964 |
| ForeachAddList / unresolved | 3468 | 5.345 | 0.363468 | 0 / 4692 |
| MoeDistributeCombineV3 / expert_combine_native | 1224 | 14.483 | 0.347584 | 0 / 4692 |
| hcom_reduceScatter_ / ffn_down_communication | 1224 | 14.234 | 0.341623 | 0 / 4743 |
| Tanh / unresolved | 4896 | 3.522 | 0.338070 | 0 / 18870 |
| Cast / unresolved | 7446 | 2.276 | 0.332246 | 0 / 33150 |
| Slice / unresolved | 4896 | 3.417 | 0.328011 | 0 / 28356 |
| Muls / unresolved | 4896 | 3.397 | 0.326092 | 0 / 18870 |
| AttnResFwd / unresolved | 1275 | 11.135 | 0.278385 | 0 / 9537 |
| RmsNorm / latent_norm | 3468 | 4.013 | 0.272877 | 4692 / 4692 |
| hcom_allGather_ / ffn_down_communication | 1275 | 9.780 | 0.244510 | 0 / 4794 |
| MoeGatingTopK / unresolved | 3468 | 2.991 | 0.203384 | 0 / 4692 |
| MatMulV3 / shared.down | 1224 | 8.292 | 0.199018 | 4692 / 4692 |
| MatMulV3 / unresolved | 1224 | 7.683 | 0.184386 | 0 / 12954 |
| Sigmoid / unresolved | 2448 | 3.321 | 0.159386 | 0 / 14178 |
| ForeachAddList / unresolved | 1224 | 5.328 | 0.127868 | 0 / 4692 |
| RmsNorm / latent_norm | 1224 | 3.993 | 0.095821 | 4692 / 4692 |
| MoeGatingTopK / unresolved | 1224 | 3.019 | 0.072455 | 0 / 4692 |
| MatMulV3 / gate_up | 51 | 49.535 | 0.049535 | 51 / 51 |
| MatMulV3 / down | 51 | 24.165 | 0.024165 | 51 / 51 |
| Index / unresolved | 51 | 4.871 | 0.004871 | 0 / 51 |
| Fill / unresolved | 102 | 1.664 | 0.003328 | 0 / 102 |
| BroadcastTo / unresolved | 51 | 2.438 | 0.002438 | 0 / 51 |

## a5_kimi_tp8_e16_bf16_c8_p4k / kimi-variants

### KDA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MatMulV3 / unresolved | 7176 | 19.583 | 2.702516 | 0 / 13208 |
| RecurrentKda / unresolved | 3588 | 15.498 | 1.069391 | 0 / 3588 |
| hcom_reduceScatter_ / attention_output_communication | 3588 | 14.296 | 0.986423 | 0 / 4836 |
| MatMulV3 / linear_output | 3588 | 11.969 | 0.825830 | 3588 / 3588 |
| AttnResFwd / unresolved | 3588 | 10.949 | 0.755503 | 0 / 9724 |
| hcom_allGather_ / attention_output_communication | 3588 | 10.774 | 0.743390 | 0 / 4836 |
| CausalConv1d / unresolved | 3588 | 7.043 | 0.485989 | 0 / 3588 |
| Slice / unresolved | 7176 | 3.392 | 0.468121 | 0 / 28912 |
| AsStrided / unresolved | 3588 | 4.069 | 0.280773 | 0 / 3588 |
| layer_norm_gated_fwd_kernel / unresolved | 3588 | 3.434 | 0.236948 | 0 / 3588 |
| ZerosLike / unresolved | 3588 | 2.956 | 0.203962 | 0 / 4836 |
| Sigmoid / unresolved | 3588 | 2.080 | 0.143494 | 0 / 14456 |
| Cast / unresolved | 3588 | 1.671 | 0.115293 | 0 / 33800 |

### MLA attention

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| MlaPrologV3 / unresolved | 1248 | 33.437 | 0.802489 | 0 / 1248 |
| FusedInferAttentionScore / unresolved | 1248 | 31.708 | 0.760991 | 0 / 1248 |
| MatMulV3 / q_a | 1248 | 18.715 | 0.449164 | 1248 / 1248 |
| hcom_reduceScatter_ / attention_output_communication | 1248 | 15.124 | 0.362978 | 0 / 4836 |
| MatMulV3 / unresolved | 1248 | 12.073 | 0.289761 | 0 / 13208 |
| AttnResFwd / unresolved | 1248 | 11.182 | 0.268359 | 0 / 9724 |
| hcom_allGather_ / attention_output_communication | 1248 | 10.418 | 0.250035 | 0 / 4836 |
| Slice / unresolved | 2496 | 3.688 | 0.177011 | 0 / 28912 |
| PadV3 / unresolved | 2496 | 3.633 | 0.174367 | 0 / 2496 |
| TransposeBatchMatMul / unresolved | 1248 | 5.407 | 0.129762 | 0 / 1248 |
| Mul / unresolved | 1248 | 3.173 | 0.076152 | 0 / 39728 |
| Sigmoid / unresolved | 1248 | 2.932 | 0.070358 | 0 / 14456 |
| ZerosLike / unresolved | 1248 | 2.881 | 0.069156 | 0 / 4836 |
| Cast / unresolved | 1248 | 1.917 | 0.046011 | 0 / 33800 |

### FFN

| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |
|---|---:|---:|---:|---:|
| GroupedMatmul / expert_up | 3536 | 43.112 | 2.931633 | 0 / 4784 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3536 | 33.053 | 2.247600 | 0 / 4784 |
| MatMulV3 / latent_down | 3536 | 24.661 | 1.676947 | 4784 / 4784 |
| MatMulV3 / latent_up | 3536 | 21.078 | 1.433307 | 4784 / 4784 |
| GroupedMatmul / expert_down | 3536 | 20.746 | 1.410749 | 0 / 4784 |
| MatMulV3 / shared.gate_up | 3536 | 20.215 | 1.374641 | 4784 / 4784 |
| Mul / unresolved | 28496 | 2.240 | 1.227415 | 0 / 39728 |
| GroupedMatmul / expert_up | 1248 | 41.264 | 0.990345 | 0 / 4784 |
| MoeDistributeCombineV3 / expert_combine_native | 3536 | 14.530 | 0.988019 | 0 / 4784 |
| hcom_reduceScatter_ / ffn_down_communication | 3588 | 14.253 | 0.983425 | 0 / 4836 |
| Slice / unresolved | 14248 | 3.571 | 0.978509 | 0 / 28912 |
| Tanh / unresolved | 14248 | 3.557 | 0.974719 | 0 / 19240 |
| Muls / unresolved | 14248 | 3.413 | 0.935126 | 0 / 19240 |
| Cast / unresolved | 21372 | 2.275 | 0.934936 | 0 / 33800 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 1248 | 32.518 | 0.780441 | 0 / 4784 |
| AttnResFwd / unresolved | 3588 | 10.883 | 0.750931 | 0 / 9724 |
| hcom_allGather_ / ffn_down_communication | 3588 | 10.036 | 0.692498 | 0 / 4888 |
| MatMulV3 / latent_down | 1248 | 23.809 | 0.571423 | 4784 / 4784 |
| MatMulV3 / shared.down | 3536 | 8.362 | 0.568621 | 4784 / 4784 |
| MatMulV3 / unresolved | 3536 | 7.815 | 0.531395 | 0 / 13208 |
| MatMulV3 / latent_up | 1248 | 20.940 | 0.502564 | 4784 / 4784 |
| GroupedMatmul / expert_down | 1248 | 20.163 | 0.483917 | 0 / 4784 |
| MatMulV3 / shared.gate_up | 1248 | 19.596 | 0.470297 | 4784 / 4784 |
| Sigmoid / unresolved | 7124 | 3.281 | 0.449486 | 0 / 14456 |
| Mul / unresolved | 9984 | 2.222 | 0.426593 | 0 / 39728 |
| ForeachAddList / unresolved | 3536 | 5.302 | 0.360517 | 0 / 4784 |
| MoeDistributeCombineV3 / expert_combine_native | 1248 | 14.448 | 0.346744 | 0 / 4784 |
| hcom_reduceScatter_ / ffn_down_communication | 1248 | 14.215 | 0.341164 | 0 / 4836 |
| Tanh / unresolved | 4992 | 3.524 | 0.338345 | 0 / 19240 |
| Cast / unresolved | 7592 | 2.273 | 0.331889 | 0 / 33800 |
| Slice / unresolved | 4992 | 3.412 | 0.327593 | 0 / 28912 |
| Muls / unresolved | 4992 | 3.393 | 0.325759 | 0 / 19240 |
| AttnResFwd / unresolved | 1300 | 11.117 | 0.277914 | 0 / 9724 |
| RmsNorm / latent_norm | 3536 | 4.020 | 0.273357 | 4784 / 4784 |
| hcom_allGather_ / ffn_down_communication | 1300 | 9.855 | 0.246383 | 0 / 4888 |
| MoeGatingTopK / unresolved | 3536 | 2.988 | 0.203190 | 0 / 4784 |
| MatMulV3 / shared.down | 1248 | 8.282 | 0.198772 | 4784 / 4784 |
| MatMulV3 / unresolved | 1248 | 7.728 | 0.185474 | 0 / 13208 |
| Sigmoid / unresolved | 2496 | 3.326 | 0.159660 | 0 / 14456 |
| ForeachAddList / unresolved | 1248 | 5.319 | 0.127666 | 0 / 4784 |
| RmsNorm / latent_norm | 1248 | 4.003 | 0.096071 | 4784 / 4784 |
| MoeGatingTopK / unresolved | 1248 | 3.019 | 0.072450 | 0 / 4784 |
| MatMulV3 / gate_up | 52 | 49.715 | 0.049715 | 52 / 52 |
| MatMulV3 / down | 52 | 24.347 | 0.024347 | 52 / 52 |
| Index / unresolved | 52 | 4.963 | 0.004963 | 0 / 52 |
| Fill / unresolved | 104 | 1.655 | 0.003311 | 0 / 104 |
| BroadcastTo / unresolved | 52 | 2.410 | 0.002410 | 0 / 52 |
