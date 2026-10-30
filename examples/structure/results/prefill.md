# Current profiling validation

One canonical case registry and one recorded Sim package. Selected costs are freshly replayed; unchanged cases retain verified evidence from this same Sim package. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.

| Case | Phase | Calls | Real mean / P50 / P90 ms | Sim ms | Error | Status |
|---|---|---:|---:|---:|---:|---|
| v4f-prefill-p4096 | prefill | 1 | 542.752 / 542.752 / 542.752 | 511.960 | -5.67% | PASS |
| v4f-prefill-p16384 | prefill | 1 | 1764.528 / 1764.528 / 1764.528 | 1665.612 | -5.61% | PASS |
| v4f-prefill-p65536 | prefill | 1 | 7957.380 / 7957.380 / 7957.380 | 7675.158 | -3.55% | PASS |
| v4f-prefill-p126976 | prefill | 1 | 17835.289 / 17835.289 / 17835.289 | 17388.292 | -2.51% | PASS |
| v4pro-prefill-p4096 | prefill | 1 | 2586.233 / 2586.233 / 2586.233 | 2544.557 | -1.61% | PASS |
| v4pro-prefill-p16384 | prefill | 1 | 10313.726 / 10313.726 / 10313.726 | 10426.983 | +1.10% | PASS |
| v4pro-prefill-p61440 | prefill | 0 | — / — / — | — | — | unresolved |
| qwen36-a5-prof_p4096_c1 | prefill | 1 | 156.479 / 156.479 / 156.479 | 169.657 | +8.42% | PASS |
| qwen36-a5-prof_p16384_c1 | prefill | 1 | 436.568 / 436.568 / 436.568 | 460.114 | +5.39% | PASS |
| qwen36-a5-p65536_c1_o32 | prefill | 1 | 2034.690 / 2034.690 / 2034.690 | 2023.481 | -0.55% | PASS |
| qwen36-a5-prof_p126976_c1 | prefill | 1 | 4602.319 / 4602.319 / 4602.319 | 4366.028 | -5.13% | PASS |
| qwen35-a5-p1024 | prefill | 1 | 140.251 / 140.251 / 140.251 | 135.290 | -3.54% | PASS |
| qwen35-a5-p4096 | prefill | 1 | 142.868 / 142.868 / 142.868 | 133.241 | -6.74% | PASS |
| qwen35-a5-p65536 | prefill | 1 | 1372.007 / 1372.007 / 1372.007 | 1372.848 | +0.06% | PASS |
| qwen35-a5-p126976 | prefill | 1 | 3275.422 / 3275.422 / 3275.422 | 3072.221 | -6.20% | PASS |
| a3_glm53flash_heldout_s5_prefill_p16384_c1 | prefill | 0 | — / — / — | — | — | observed_only |
| a3_glm53flash_heldout_s5_prefill_p16384_c4 | prefill | 0 | — / — / — | — | — | observed_only |
| a3_glm53flash_heldout_s5_prefill_p2048_c1 | prefill | 0 | — / — / — | — | — | observed_only |
| a3_glm53flash_heldout_s5_prefill_p2048_c4 | prefill | 0 | — / — / — | — | — | observed_only |
| a3_glm53flash_heldout_s5_prefill_p32768_c1 | prefill | 0 | — / — / — | — | — | observed_only |
| a3_glm53flash_heldout_s5_prefill_p32768_c4 | prefill | 0 | — / — / — | — | — | observed_only |
| a3_glm53flash_heldout_s5_prefill_p4096_c1 | prefill | 0 | — / — / — | — | — | observed_only |
| a3_glm53flash_heldout_s5_prefill_p4096_c4 | prefill | 0 | — / — / — | — | — | observed_only |
| a3_glm53flash_heldout_s5_prefill_p8192_c1 | prefill | 0 | — / — / — | — | — | observed_only |
| a3_glm53flash_heldout_s5_prefill_p8192_c4 | prefill | 0 | — / — / — | — | — | observed_only |
| a5_kimi_k3_p32768_c1 | prefill | 1 | 4291.836 / 4291.836 / 4291.836 | 4117.323 | -4.07% | PASS |

| Case | B / q | Layer group | Layers | Real mean / P50 ms | Sim mean / P50 ms | Mean / P50 error |
|---|---|---|---:|---:|---:|---:|

Layer-group statistics summarize complete layer spans, not isolated attention or FFN kernel time. Group P50 is across layer means; steady-layer P50 remains the median of per-layer call P50 values in JSON. Full layer membership, extrema, stream details and alignment assumptions remain in the SHA256-pinned evidence.

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
| a3_glm53flash_heldout_s5_prefill_p16384_c1 | 2729.099 | — | None |
| a3_glm53flash_heldout_s5_prefill_p16384_c4 | 6950.875 | — | None |
| a3_glm53flash_heldout_s5_prefill_p2048_c1 | 685.956 | — | None |
| a3_glm53flash_heldout_s5_prefill_p2048_c4 | 1332.368 | — | None |
| a3_glm53flash_heldout_s5_prefill_p32768_c1 | 4922.888 | — | None |
| a3_glm53flash_heldout_s5_prefill_p32768_c4 | 12694.102 | — | None |
| a3_glm53flash_heldout_s5_prefill_p4096_c1 | 883.659 | — | None |
| a3_glm53flash_heldout_s5_prefill_p4096_c4 | 2206.948 | — | None |
| a3_glm53flash_heldout_s5_prefill_p8192_c1 | 1340.904 | — | None |
| a3_glm53flash_heldout_s5_prefill_p8192_c4 | 3545.694 | — | None |
| a5_kimi_k3_p32768_c1 | 4730.300 | — | True |

Prefill Body sums complete device chunk spans. Client TTFT includes other stages and is not substituted for Body.

Summary: {"compared": 15, "passed": 15, "requested_sources": 26, "sources": 26, "status_counts": {"compared": 15, "observed_only": 10, "unresolved": 1}}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
