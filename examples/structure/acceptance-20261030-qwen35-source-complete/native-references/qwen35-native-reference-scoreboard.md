# Qwen3.5 typed caller native Body references

Runtime `3b532649a613aa82589b95204dec3d84e916114b`; all rows are conditional references, outside strict accuracy.
Exact native histograms are retained. Captured layer counts weight fresh source programs; no per-layer measured P50 is invented. TopK is a partial-work boundary: its observed third FP32 output is not modeled.

| Case / native | Calls/F | Real Mean / P50 us | Sim mean reference us | Real activity / Sim service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| qwen35-35b-a5-tp4-c4-graph / GroupedMatmul | 80.000 | 27.974743 / 26.754500 | 12.812550 | 2.237979 / 1.025004 / -1.212975 |
| qwen35-35b-a5-tp4-c4-graph / MoeDistributeDispatchV3 | 40.000 | 17.245965 / 16.954500 | 2.242899 | 0.689839 / 0.089716 / -0.600123 |
| qwen35-35b-a5-tp4-c4-graph / DequantSwigluQuant | 40.000 | 7.299230 / 7.286000 | 6.699758 | 0.291969 / 0.267990 / -0.023979 |
| qwen35-35b-a5-tp4-c4-graph / MoeGatingTopK | 40.000 | 3.141281 / 3.130000 | 1.312000 | 0.125651 / 0.052480 / -0.073171 |
| qwen35-35b-a5-tp4-c4-graph / MoeDistributeCombineV3 | 40.000 | 11.677635 / 11.374500 | 3.376874 | 0.467105 / 0.135075 / -0.332030 |
| qwen35-35b-a5-tp4-c64-graph / GroupedMatmul | 80.000 | 51.347337 / 53.046000 | 26.628461 | 4.107787 / 2.130277 / -1.977510 |
| qwen35-35b-a5-tp4-c64-graph / DequantSwigluQuant | 40.000 | 54.031062 / 54.304000 | 13.391758 | 2.161242 / 0.535670 / -1.625572 |
| qwen35-35b-a5-tp4-c64-graph / MoeDistributeDispatchV3 | 40.000 | 28.795800 / 29.043500 | 7.027383 | 1.151832 / 0.281095 / -0.870737 |
| qwen35-35b-a5-tp4-c64-graph / MoeGatingTopK | 40.000 | 6.696034 / 6.681000 | 1.312000 | 0.267841 / 0.052480 / -0.215361 |
| qwen35-35b-a5-tp4-c64-graph / MoeDistributeCombineV3 | 40.000 | 27.371084 / 28.149000 | 8.216762 | 1.094843 / 0.328670 / -0.766173 |
| qwen35-35b-a5-tp4-c64-graph / TensorMove | — | — | — | outside_selected_FFN_caller; attention_layout_copy_not_reclassified |
| qwen35-35b-a5-tp4-c64-graph / TensorMove | — | — | — | outside_selected_FFN_caller; attention_layout_copy_not_reclassified |
| qwen35-35b-a5-tp4-c128-graph / GroupedMatmul | 80.000 | 52.597890 / 54.684500 | 27.784270 | 4.207831 / 2.222742 / -1.985090 |
| qwen35-35b-a5-tp4-c128-graph / DequantSwigluQuant | 40.000 | 56.560073 / 56.844500 | 13.391758 | 2.262403 / 0.535670 / -1.726733 |
| qwen35-35b-a5-tp4-c128-graph / MoeDistributeDispatchV3 | 40.000 | 41.178457 / 41.103500 | 12.047800 | 1.647138 / 0.481912 / -1.165226 |
| qwen35-35b-a5-tp4-c128-graph / MoeGatingTopK | 40.000 | 7.244563 / 7.225500 | 1.312000 | 0.289783 / 0.052480 / -0.237303 |
| qwen35-35b-a5-tp4-c128-graph / MoeDistributeCombineV3 | 40.000 | 43.109088 / 43.058000 | 14.633523 | 1.724364 / 0.585341 / -1.139023 |
| qwen35-35b-a5-tp4-c128-graph / TensorMove | — | — | — | outside_selected_FFN_caller; attention_layout_copy_not_reclassified |
| qwen35-35b-a5-tp4-c128-graph / TensorMove | — | — | — | outside_selected_FFN_caller; attention_layout_copy_not_reclassified |

Source service residuals cannot be added to explain Body wall time. Full ABI, source/case/runtime identity, exact histograms and program multiplicities are retained in JSON.
