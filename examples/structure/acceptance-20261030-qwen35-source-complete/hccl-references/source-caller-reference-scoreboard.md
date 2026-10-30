# Source caller and explicit HCCL conditional references

All rows remain source-symbol conditional references. Native tensor ABI, valid routing values and captured HCCL template are not invented.
Copy gather/scatter remain pooled; zero-fill/convolution are outside their cost. Controllers never add to HCOM elapsed.

| Source / native / role | Calls/F | Real Mean / P50 us | Sim us/call | Signed activity residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| qwen35-35b-a5-tp4-c4-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 29.00 | 25.456769 / 25.280000 | 4.544062 | -0.606469 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 29.00 | 25.222540 / 25.232000 | 4.544062 | -0.599676 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allGather_ / allgather_explicit_source_collective | 29.00 | 10.691865 / 10.405000 | 2.058419 | -0.250370 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 10.00 | 25.336713 / 25.269500 | 4.544062 | -0.207927 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 10.00 | 25.159486 / 24.926000 | 4.544062 | -0.206154 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 114.052000 / 23.446000 | 4.544062 | -0.109508 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allGather_ / allgather_explicit_source_collective | 10.00 | 10.168339 / 10.094000 | 2.058419 | -0.081099 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 24.477810 / 24.487000 | 4.544062 | -0.019934 |
| qwen35-35b-a5-tp4-c4-graph / hcom_allGather_ / allgather_explicit_source_collective | 1.00 | 11.191619 / 10.977000 | 2.058419 | -0.009133 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 29.00 | 34.542823 / 34.110000 | 18.697990 | -0.459500 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 29.00 | 32.245504 / 32.228000 | 18.697990 | -0.392878 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allGather_ / allgather_explicit_source_collective | 29.00 | 24.291574 / 23.927000 | 10.493952 | -0.400131 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 10.00 | 34.464948 / 33.238500 | 18.697990 | -0.157670 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 10.00 | 32.270027 / 32.175500 | 18.697990 | -0.135720 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 255.963127 / 302.044000 | 18.697990 | -0.237265 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allGather_ / allgather_explicit_source_collective | 10.00 | 23.489103 / 23.202000 | 10.493952 | -0.129952 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 32.044835 / 31.979000 | 18.697990 | -0.013347 |
| qwen35-35b-a5-tp4-c64-graph / hcom_allGather_ / allgather_explicit_source_collective | 1.00 | 23.499089 / 23.363000 | 10.493952 | -0.013005 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 29.00 | 47.802890 / 47.500500 | 33.795349 | -0.406219 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 29.00 | 45.498117 / 45.441500 | 33.795349 | -0.339380 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allGather_ / allgather_explicit_source_collective | 29.00 | 30.145511 / 30.069500 | 10.096208 | -0.581430 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 10.00 | 49.640213 / 48.313000 | 33.795349 | -0.158449 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 10.00 | 45.619630 / 45.457500 | 33.795349 | -0.118243 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allGather_ / allgather_explicit_source_collective | 10.00 | 30.201721 / 30.095000 | 10.096208 | -0.201055 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 75.941382 / 44.762000 | 33.795349 | -0.042146 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 45.491368 / 45.426500 | 33.795349 | -0.011696 |
| qwen35-35b-a5-tp4-c128-graph / hcom_allGather_ / allgather_explicit_source_collective | 1.00 | 30.735553 / 30.698500 | 10.096208 | -0.020639 |

Residuals compare event activity to source service. They must not be summed into Body wall time.
