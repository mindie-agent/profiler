# Source caller and explicit HCCL conditional references

All rows remain source-symbol conditional references. Native tensor ABI, valid routing values and captured HCCL template are not invented.
Copy gather/scatter remain pooled; zero-fill/convolution are outside their cost. Controllers never add to HCOM elapsed.

| Source / native / role | Calls/F | Real Mean / P50 us | Sim us/call | Signed activity residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| a3_kimi4_tp8_w4a8_c32_aicpu_ts_mesh / hcom_allGather_ / allgather_explicit_source_collective | 1.00 | 221.270014 / 202.216000 | 4.446575 | -0.216823 |
| a3_kimi4_tp8_w4a8_c32_aicpu_ts_mesh / hcom_allGather_ / allgather_explicit_source_collective | 2.00 | 66.884673 / 31.939500 | 4.446575 | -0.124876 |
| a3_kimi4_tp8_w4a8_c32_aicpu_ts_mesh / hcom_allGather_ / allgather_explicit_source_collective | 2.00 | 26.833593 / 26.549500 | 4.446575 | -0.044774 |
| a3_kimi4_tp8_w4a8_c32_aicpu_ts_mesh / hcom_allGather_ / allgather_explicit_source_collective | 1.00 | 48.289300 / 21.860000 | 4.446575 | -0.043843 |
| a3_kimi4_tp8_w4a8_c32_aicpu_ts_mesh / hcom_reduceScatter_ / reduce_scatter_explicit_source_collective | 2.00 | 23.497430 / 23.719000 | 5.354522 | -0.036286 |
| a3_kimi4_tp8_w4a8_c32_aicpu_ts_mesh / hcom_reduceScatter_ / reduce_scatter_explicit_source_collective | 2.00 | 20.910502 / 18.380000 | 5.354522 | -0.031112 |
| a3_kimi4_tp8_w4a8_c32_aicpu_ts_mesh / hcom_reduceScatter_ / reduce_scatter_explicit_source_collective | 1.00 | 41.500250 / 29.329500 | 5.354522 | -0.036146 |
| a3_kimi4_tp8_w4a8_c32_aicpu_ts_mesh / hcom_reduceScatter_ / reduce_scatter_explicit_source_collective | 1.00 | 29.563386 / 29.349500 | 5.354522 | -0.024209 |
| a3_kimi4_tp8_w4a8_c32_aicpu_ts_mesh / hcom_allGather_ / allgather_explicit_source_collective | 1.00 | 28.995514 / 28.939000 | 4.446575 | -0.024549 |
| a3_kimi4_tp8_w4a8_c32_aicpu_ts_mesh / hcom_reduceScatter_ / reduce_scatter_explicit_source_collective | 1.00 | 25.296123 / 18.410000 | 5.354522 | -0.019942 |
| a3_kimi4_tp8_w4a8_c32_aicpu_ts_mesh / hcom_reduceScatter_ / reduce_scatter_explicit_source_collective | 1.00 | 22.145218 / 22.200000 | 5.354522 | -0.016791 |
| a3_kimi4_tp8_w4a8_c32_aicpu_ts_mesh / hcom_allGather_ | 440 calls unresolved | collective_region_not_one_declared_call_per_layer_forward | — | — |

Residuals compare event activity to source service. They must not be summed into Body wall time.
