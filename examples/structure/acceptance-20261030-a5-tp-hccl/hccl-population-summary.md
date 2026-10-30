# A5 TP HCCL retained-Body evidence

9 local captures; 495 selected complete Bodies; 57,952 unique collective rows; 49,672 exact duplicate summaries removed. 8,598 AICPU rows are separate, never added to collective elapsed.

| Capture | TP / execution B / q | F | Type | Calls/F | Mean / P50 µs | Steady Mean / P50 µs | L0 attention Mean / P50 µs | Activity ms/F | BlockNum | Preceding tensor bytes (conditional) |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| a5_glm53flash_tp8_c16_p4k | 8 / 16 / 4 | 30 | hcom_allReduce_AicpuKernel | 90 | 34.413 / 32.355 | 33.463 / 32.376 | 121.100 / 116.487 | 3.0972 | 0 | [524288] |
| a5_glm53flash_tp8_c32_p4k | 8 / 32 / 4 | 31 | hcom_allReduce_AicpuKernel | 90 | 36.277 / 33.661 | 34.934 / 33.516 | 148.790 / 122.505 | 3.2649 | 0 | [1048576] |
| a5_glm53flash_tp8_c64_p4k | 8 / 64 / 4 | 31 | hcom_allReduce_AicpuKernel | 90 | 42.658 / 40.072 | 41.845 / 40.115 | 118.974 / 99.105 | 3.8392 | 0 | [2097152] |
| qwen35-35b-a5-tp4-c128-graph | 4 / 128 / 4 | 76 | hcom_allGather_ | 40 | 30.174 / 30.088 | 30.160 / 30.072 | — | 1.2070 | 64 | [524288] |
| qwen35-35b-a5-tp4-c128-graph | 4 / 128 / 4 | 76 | hcom_allReduce_ | 80 | 47.247 / 46.254 | 46.902 / 46.286 | 75.941 / 44.762 | 3.7798 | 60 | [2097152] |
| qwen35-35b-a5-tp4-c4-graph | 4 / 4 / 4 | 84 | hcom_allGather_ | 40 | 10.573 / 10.290 | 10.558 / 10.280 | — | 0.4229 | 64 | [16384] |
| qwen35-35b-a5-tp4-c4-graph | 4 / 4 / 4 | 84 | hcom_allReduce_ | 80 | 26.415 / 25.215 | 25.316 / 25.230 | 114.052 / 23.446 | 2.1132 | 60 | [65536] |
| qwen35-35b-a5-tp4-c64-graph | 4 / 64 / 4 | 79 | hcom_allGather_ | 40 | 24.071 / 23.750 | 24.086 / 23.770 | — | 0.9628 | 64 | [262144] |
| qwen35-35b-a5-tp4-c64-graph | 4 / 64 / 4 | 79 | hcom_allReduce_ | 80 | 36.153 / 32.931 | 33.387 / 32.928 | 255.963 / 302.044 | 2.8922 | 60 | [1048576] |
| qwen36-a5-tp2-c1 | 2 / 1 / 4 | 85 | hcom_allReduce_ | 128 | 10.833 / 9.960 | 10.511 / 9.957 | 50.935 / 9.400 | 1.3866 | 3 | [40960] |
| qwen36-a5-tp2-c12 | 2 / 12 / 4 | 55 | hcom_allReduce_ | 128 | 43.805 / 39.726 | 42.095 / 39.730 | 263.503 / 38.802 | 5.6070 | 3 | [491520] |
| qwen36-a5-tp2-c96 | 2 / 96 / 4 | 24 | hcom_allReduce_ | 128 | 129.800 / 127.204 | 127.436 / 127.209 | 429.909 / 126.384 | 16.6144 | 63 | [3932160] |

The byte column describes an actual preceding hidden tensor, not a measured HCCL payload. No bandwidth is inferred. `B` is shape-derived execution batch, not active client count. The payload association remains conditional. A model `ring_allreduce` recipe does not prove that HCCL selected ring.

Qwen36 TP2 c12/c96 layer0 starts with parameter Add and input RmsNorm; the long collective follows RecurrentGatedDeltaRule and output MatMul and precedes FFN normalization. It is inside the target body, not embedding tail. Exact source rows are preserved in `tests/fixtures/hccl/`.

The nine local capture roots contain kernel/op-statistic/step CSVs but no communication table, profiler DB, or other-rank file. Metadata only points to remote profiler directories; this pass does not fetch them.

| Capture | Collective type | Steady AIV mean µs | Scalar mean µs | MTE2 mean µs | MTE3 mean µs |
|---|---|---:|---:|---:|---:|
| a5_glm53flash_tp8_c16_p4k | hcom_allReduce_AicpuKernel | N/A | N/A | N/A | N/A |
| a5_glm53flash_tp8_c32_p4k | hcom_allReduce_AicpuKernel | N/A | N/A | N/A | N/A |
| a5_glm53flash_tp8_c64_p4k | hcom_allReduce_AicpuKernel | N/A | N/A | N/A | N/A |
| qwen35-35b-a5-tp4-c128-graph | hcom_allGather_ | 29.874 | 6.962 | 16.845 | 1.717 |
| qwen35-35b-a5-tp4-c128-graph | hcom_allReduce_ | 46.616 | 5.772 | 22.371 | 1.601 |
| qwen35-35b-a5-tp4-c4-graph | hcom_allGather_ | 10.273 | 3.268 | 0.373 | 0.077 |
| qwen35-35b-a5-tp4-c4-graph | hcom_allReduce_ | 25.031 | 4.908 | 9.422 | 0.887 |
| qwen35-35b-a5-tp4-c64-graph | hcom_allGather_ | 23.800 | 5.855 | 1.800 | 0.439 |
| qwen35-35b-a5-tp4-c64-graph | hcom_allReduce_ | 33.102 | 5.390 | 14.419 | 1.247 |
| qwen36-a5-tp2-c1 | hcom_allReduce_ | 10.224 | 2.322 | 1.828 | 1.153 |
| qwen36-a5-tp2-c12 | hcom_allReduce_ | 41.808 | 3.091 | 9.303 | 8.037 |
| qwen36-a5-tp2-c96 | hcom_allReduce_ | 127.149 | 13.271 | 56.289 | 2.229 |

PMU pipelines can overlap; these columns are not additive. Missing counters remain N/A; observed zero remains zero. `Wait Time(us)` is retained in JSON without interpreting it as network/peer wait.

Validation: 3,380 checks, zero failures; one retained-window CSV pass per source; no new collection or prediction. Peak worker 102.27 MiB. Full source identities, raw PMU counters, per-layer/per-forward counts, bounded longest-call locators and duplicate pairs remain in each ledger.
