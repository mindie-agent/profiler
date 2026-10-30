# Source caller and explicit HCCL conditional references

All rows remain source-symbol conditional references. Native tensor ABI, valid routing values and captured HCCL template are not invented.
Copy gather/scatter remain pooled; zero-fill/convolution are outside their cost. Controllers never add to HCOM elapsed.

| Source / native / role | Calls/F | Real Mean / P50 us | Sim us/call | Signed activity residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| qwen36-a5-tp2-c1-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 47.00 | 10.946095 / 10.573000 | 4.128742 | -0.320416 |
| qwen36-a5-tp2-c1-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 47.00 | 10.176453 / 9.834000 | 4.128742 | -0.284242 |
| qwen36-a5-tp2-c1-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 16.00 | 10.639587 / 9.762000 | 4.128742 | -0.104174 |
| qwen36-a5-tp2-c1-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 16.00 | 10.083787 / 9.691000 | 4.128742 | -0.095281 |
| qwen36-a5-tp2-c1-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 50.935129 / 9.400000 | 4.128742 | -0.046806 |
| qwen36-a5-tp2-c1-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 11.330412 / 11.523000 | 4.128742 | -0.007202 |
| qwen36-a5-tp2-c12-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 47.00 | 46.437653 / 45.606000 | 42.419665 | -0.188845 |
| qwen36-a5-tp2-c12-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 47.00 | 39.694136 / 39.648000 | 42.419665 | +0.128100 |
| qwen36-a5-tp2-c12-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 16.00 | 39.278982 / 39.225000 | 42.419665 | +0.050251 |
| qwen36-a5-tp2-c12-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 16.00 | 39.207670 / 39.168000 | 42.419665 | +0.051392 |
| qwen36-a5-tp2-c12-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 263.503036 / 38.802000 | 42.419665 | -0.221083 |
| qwen36-a5-tp2-c12-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 39.537218 / 39.662000 | 42.419665 | +0.002882 |
| qwen36-a5-tp2-c96-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 47.00 | 127.813172 / 127.705000 | 79.691308 | -2.261728 |
| qwen36-a5-tp2-c96-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 47.00 | 126.718916 / 126.499000 | 79.691308 | -2.210298 |
| qwen36-a5-tp2-c96-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 16.00 | 127.942378 / 127.498500 | 79.691308 | -0.772017 |
| qwen36-a5-tp2-c96-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 16.00 | 127.925716 / 127.689500 | 79.691308 | -0.771751 |
| qwen36-a5-tp2-c96-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 429.909333 / 126.384000 | 79.691308 | -0.350218 |
| qwen36-a5-tp2-c96-hccl-source / hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 127.572458 / 127.300000 | 79.691308 | -0.047881 |
| glmflash-a5-c16-copy-routing / MoeInitRoutingV3 / local_routing_mxfp8 | 11.00 | 22.832809 / 22.932500 | 1.312000 | -0.236729 |
| glmflash-a5-c16-copy-routing / MoeInitRoutingV3 / local_routing_mxfp8 | 31.00 | 23.074118 / 23.085500 | 1.312000 | -0.674626 |
| glmflash-a5-c16-copy-routing / _copy_conv_state_kernel / conv_state_copy_gather_scatter_cohort | 68.00 | 8.338639 / 8.284500 | 1.312000 | -0.477811 |
| glmflash-a5-c32-copy-routing / MoeInitRoutingV3 / local_routing_mxfp8 | 11.00 | 23.958299 / 23.987000 | 1.755819 | -0.244227 |
| glmflash-a5-c32-copy-routing / MoeInitRoutingV3 / local_routing_mxfp8 | 31.00 | 24.942623 / 25.097000 | 1.755819 | -0.718791 |
| glmflash-a5-c32-copy-routing / _copy_conv_state_kernel / conv_state_copy_gather_scatter_cohort | 68.00 | 12.895869 / 12.476500 | 1.312000 | -0.787703 |
| glmflash-a5-c64-copy-routing / MoeInitRoutingV3 / local_routing_mxfp8 | 11.00 | 28.475789 / 28.542000 | 3.275354 | -0.277205 |
| glmflash-a5-c64-copy-routing / MoeInitRoutingV3 / local_routing_mxfp8 | 31.00 | 28.871585 / 28.927000 | 3.275354 | -0.793483 |
| glmflash-a5-c64-copy-routing / _copy_conv_state_kernel / conv_state_copy_gather_scatter_cohort | 68.00 | 21.777109 / 21.506000 | 1.312000 | -1.391627 |

Residuals compare event activity to source service. They must not be summed into Body wall time.
