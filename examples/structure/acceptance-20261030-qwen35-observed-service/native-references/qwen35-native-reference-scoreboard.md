# Qwen3.5 typed caller native Body references

Runtime `84d80b40dca5a462ff32b971152c2f2e81abfc4b`; all rows are conditional references, outside strict accuracy.
Exact native histograms are retained. Captured layer counts weight fresh source programs; no per-layer measured P50 is invented. TopK is a partial-work boundary: its observed third FP32 output is not modeled.

| Case / native | Calls/F | Real Mean / P50 us | Sim mean reference us | Real activity / Sim service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| qwen35-35b-a5-tp4-c4-graph / GroupedMatmul | 80.000 | 27.974743 / 26.754500 | 25.673669 | 2.237979 / 2.053893 / -0.184086 |
| qwen35-35b-a5-tp4-c4-graph / MoeDistributeDispatchV3 | 40.000 | 17.245965 / 16.954500 | 17.245965 | 0.689839 / 0.689839 / +0.000000 |
| qwen35-35b-a5-tp4-c4-graph / DequantSwigluQuant | 40.000 | 7.299230 / 7.286000 | 1.312000 | 0.291969 / 0.052480 / -0.239489 |
| qwen35-35b-a5-tp4-c4-graph / MoeGatingTopK | 40.000 | 3.141281 / 3.130000 | 1.312000 | 0.125651 / 0.052480 / -0.073171 |
| qwen35-35b-a5-tp4-c4-graph / MoeDistributeCombineV3 | 40.000 | 11.677635 / 11.374500 | 11.677635 | 0.467105 / 0.467105 / +0.000000 |
| qwen35-35b-a5-tp4-c64-graph / GroupedMatmul | 80.000 | 51.347337 / 53.046000 | 51.347337 | 4.107787 / 4.107787 / +0.000000 |
| qwen35-35b-a5-tp4-c64-graph / DequantSwigluQuant | 40.000 | 54.031062 / 54.304000 | 54.031062 | 2.161242 / 2.161242 / +0.000000 |
| qwen35-35b-a5-tp4-c64-graph / MoeDistributeDispatchV3 | 40.000 | 28.795800 / 29.043500 | 28.826203 | 1.151832 / 1.153048 / +0.001216 |
| qwen35-35b-a5-tp4-c64-graph / MoeGatingTopK | 40.000 | 6.696034 / 6.681000 | 1.312000 | 0.267841 / 0.052480 / -0.215361 |
| qwen35-35b-a5-tp4-c64-graph / MoeDistributeCombineV3 | 40.000 | 27.371084 / 28.149000 | 26.886403 | 1.094843 / 1.075456 / -0.019387 |
| qwen35-35b-a5-tp4-c64-graph / TensorMove | — | — | — | outside_selected_FFN_caller; attention_layout_copy_not_reclassified |
| qwen35-35b-a5-tp4-c64-graph / TensorMove | — | — | — | outside_selected_FFN_caller; attention_layout_copy_not_reclassified |
| qwen35-35b-a5-tp4-c128-graph / GroupedMatmul | 80.000 | 52.597890 / 54.684500 | 51.347337 | 4.207831 / 4.107787 / -0.100044 |
| qwen35-35b-a5-tp4-c128-graph / DequantSwigluQuant | 40.000 | 56.560073 / 56.844500 | 54.031062 | 2.262403 / 2.161242 / -0.101160 |
| qwen35-35b-a5-tp4-c128-graph / MoeDistributeDispatchV3 | 40.000 | 41.178457 / 41.103500 | 41.178457 | 1.647138 / 1.647138 / +0.000000 |
| qwen35-35b-a5-tp4-c128-graph / MoeGatingTopK | 40.000 | 7.244563 / 7.225500 | 1.312000 | 0.289783 / 0.052480 / -0.237303 |
| qwen35-35b-a5-tp4-c128-graph / MoeDistributeCombineV3 | 40.000 | 43.109088 / 43.058000 | 43.109088 | 1.724364 / 1.724364 / +0.000000 |
| qwen35-35b-a5-tp4-c128-graph / TensorMove | — | — | — | outside_selected_FFN_caller; attention_layout_copy_not_reclassified |
| qwen35-35b-a5-tp4-c128-graph / TensorMove | — | — | — | outside_selected_FFN_caller; attention_layout_copy_not_reclassified |

Source service residuals cannot be added to explain Body wall time. Full ABI, source/case/runtime identity, exact histograms and program multiplicities are retained in JSON.
