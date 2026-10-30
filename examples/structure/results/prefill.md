# Current profiling validation

One canonical case registry and one recorded Sim package. All costs are fresh in this run. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.

| Case | Phase | Calls | Real mean / P50 / P90 ms | Sim ms | Error | Status |
|---|---|---:|---:|---:|---:|---|
| v4f-prefill-p4096 | prefill | 1 | 542.752 / 542.752 / 542.752 | 326.252 | -39.89% | FAIL |
| v4f-prefill-p16384 | prefill | 1 | 1764.528 / 1764.528 / 1764.528 | 1343.323 | -23.87% | FAIL |
| v4f-prefill-p65536 | prefill | 1 | 7957.380 / 7957.380 / 7957.380 | 6386.000 | -19.75% | FAIL |
| v4f-prefill-p126976 | prefill | 1 | 17835.289 / 17835.289 / 17835.289 | 14785.414 | -17.10% | FAIL |
| v4pro-prefill-p4096 | prefill | 1 | 2586.233 / 2586.233 / 2586.233 | 948.464 | -63.33% | FAIL |
| v4pro-prefill-p16384 | prefill | 1 | 10313.726 / 10313.726 / 10313.726 | 4042.611 | -60.80% | FAIL |
| v4pro-prefill-p61440 | prefill | 0 | — / — / — | — | — | unresolved |
| qwen36-a5-prof_p4096_c1 | prefill | 1 | 156.479 / 156.479 / 156.479 | 114.441 | -26.87% | FAIL |
| qwen36-a5-prof_p16384_c1 | prefill | 1 | 436.568 / 436.568 / 436.568 | 460.114 | +5.39% | PASS |
| qwen36-a5-p65536_c1_o32 | prefill | 1 | 2034.690 / 2034.690 / 2034.690 | 2023.481 | -0.55% | PASS |
| qwen36-a5-prof_p126976_c1 | prefill | 1 | 4602.319 / 4602.319 / 4602.319 | 4366.028 | -5.13% | PASS |
| qwen35-a5-p1024 | prefill | 1 | 140.251 / 140.251 / 140.251 | 36.844 | -73.73% | FAIL |
| qwen35-a5-p4096 | prefill | 1 | 142.868 / 142.868 / 142.868 | 133.073 | -6.86% | PASS |
| qwen35-a5-p65536 | prefill | 1 | 1372.007 / 1372.007 / 1372.007 | 2289.725 | +66.89% | FAIL |
| qwen35-a5-p126976 | prefill | 1 | 3275.422 / 3275.422 / 3275.422 | 4807.607 | +46.78% | FAIL |

| Case | Client TTFT ms | Predicted TTFT ms | Query coverage complete |
|---|---:|---:|---|
| v4f-prefill-p4096 | 610.650 | — | True |
| v4f-prefill-p16384 | 1944.961 | — | True |
| v4f-prefill-p65536 | — | — | True |
| v4f-prefill-p126976 | 19097.967 | — | True |
| v4pro-prefill-p4096 | — | — | True |
| v4pro-prefill-p16384 | 10837.339 | — | True |
| v4pro-prefill-p61440 | 42570.116 | — | False |
| qwen36-a5-prof_p4096_c1 | 205.339 | — | True |
| qwen36-a5-prof_p16384_c1 | 521.208 | — | True |
| qwen36-a5-p65536_c1_o32 | — | — | True |
| qwen36-a5-prof_p126976_c1 | 5094.314 | — | True |
| qwen35-a5-p1024 | 180.315 | — | True |
| qwen35-a5-p4096 | 186.032 | — | True |
| qwen35-a5-p65536 | 1835.448 | — | True |
| qwen35-a5-p126976 | 4262.595 | — | True |

Prefill Body sums complete device chunk spans. Client TTFT includes other stages and is not substituted for Body.

Summary: {"compared": 14, "passed": 4, "requested_sources": 15, "sources": 15, "status_counts": {"compared": 14, "unresolved": 1}}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
