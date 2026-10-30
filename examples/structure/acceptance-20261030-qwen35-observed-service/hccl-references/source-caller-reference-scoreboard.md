# Source caller and explicit HCCL conditional references

All rows remain source-symbol conditional references. Native tensor ABI, valid routing values and captured HCCL template are not invented.
Copy gather/scatter remain pooled; zero-fill/convolution are outside their cost. Controllers never add to HCOM elapsed.

| Source / native / role | Calls/F | Real Mean / P50 us | Sim us/call | Signed activity residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| qwen35-35b-a5-tp4-c4-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 29.00 | 25.456769 / 25.280000 | 25.316179 | -0.004077 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 29.00 | 25.222540 / 25.232000 | 25.316179 | +0.002716 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allGather_ / allgather_explicit_source_collective | 29.00 | 10.691865 / 10.405000 | 10.573478 | -0.003433 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 10.00 | 25.336713 / 25.269500 | 25.316179 | -0.000205 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 10.00 | 25.159486 / 24.926000 | 25.316179 | +0.001567 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 114.052000 / 23.446000 | 25.316179 | -0.088736 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allGather_ / allgather_explicit_source_collective | 10.00 | 10.168339 / 10.094000 | 10.573478 | +0.004051 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 24.477810 / 24.487000 | 25.316179 | +0.000838 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allGather_ / allgather_explicit_source_collective | 1.00 | 11.191619 / 10.977000 | 10.573478 | -0.000618 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 29.00 | 34.542823 / 34.110000 | 35.760755 | +0.035320 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 29.00 | 32.245504 / 32.228000 | 35.760755 | +0.101942 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allGather_ / allgather_explicit_source_collective | 29.00 | 24.291574 / 23.927000 | 20.057754 | -0.122781 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 10.00 | 34.464948 / 33.238500 | 35.760755 | +0.012958 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 10.00 | 32.270027 / 32.175500 | 35.760755 | +0.034907 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 255.963127 / 302.044000 | 35.760755 | -0.220202 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allGather_ / allgather_explicit_source_collective | 10.00 | 23.489103 / 23.202000 | 20.057754 | -0.034313 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 32.044835 / 31.979000 | 35.760755 | +0.003716 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allGather_ / allgather_explicit_source_collective | 1.00 | 23.499089 / 23.363000 | 20.057754 | -0.003441 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 29.00 | 47.802890 / 47.500500 | 46.901636 | -0.026136 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 29.00 | 45.498117 / 45.441500 | 46.901636 | +0.040702 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allGather_ / allgather_explicit_source_collective | 29.00 | 30.145511 / 30.069500 | 30.174314 | +0.000835 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 10.00 | 49.640213 / 48.313000 | 46.901636 | -0.027386 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 10.00 | 45.619630 / 45.457500 | 46.901636 | +0.012820 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allGather_ / allgather_explicit_source_collective | 10.00 | 30.201721 / 30.095000 | 30.174314 | -0.000274 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 75.941382 / 44.762000 | 46.901636 | -0.029040 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 45.491368 / 45.426500 | 46.901636 | +0.001410 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allGather_ / allgather_explicit_source_collective | 1.00 | 30.735553 / 30.698500 | 30.174314 | -0.000561 |

Residuals compare event activity to source service. They must not be summed into Body wall time.
