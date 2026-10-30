# Current profiling validation

One canonical case registry and one recorded Sim package. All costs are fresh in this run. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.

| Case | Phase | Calls | Real mean / P50 / P90 ms | Sim ms | Error | Status |
|---|---|---:|---:|---:|---:|---|
| qwen36-a5-tp2-c12 | decode | — | — / — / — | — | — | failed |
| glm53flash-a3-tp16-c4-livepre | decode | — | — / — / — | — | — | failed |
| a5_kimi_tp8_e16_bf16_c32_p4k | decode | — | — / — / — | — | — | failed |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | decode | — | — / — / — | — | — | failed |
| a5_glm53flash_tp8_c64_p4k | decode | — | — / — / — | — | — | failed |
| qwen35-35b-a5-tp4-c64-graph | decode | — | — / — / — | — | — | failed |

| Case | Complete target cycles | Cycle mean / P50 ms | Client token TPOT P50 ms | Serving status |
|---|---:|---:|---:|---|
| qwen36-a5-tp2-c12 | 54 | 33.707 / 33.608 | 12.657 | serving_prediction_timeout |
| glm53flash-a3-tp16-c4-livepre | 46 | 39.847 / 39.684 | 14.697 | serving_prediction_failed |
| a5_kimi_tp8_e16_bf16_c32_p4k | 45 | 40.432 / 40.432 | 69.663 | serving_prediction_failed |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 74 | 27.023 / 27.002 | 28.943 | serving_prediction_failed |
| a5_glm53flash_tp8_c64_p4k | 30 | 59.973 / 59.772 | 29.828 | serving_prediction_failed |
| qwen35-35b-a5-tp4-c64-graph | 79 | 32.250 / 31.906 | 12.000 | serving_prediction_failed |

Device target cycles, completion-token TPOT and client delivery have different boundaries. Uncovered cycle intervals are not assigned to Host scheduling without evidence.

Summary: {"compared": 0, "passed": 0, "requested_sources": 6, "sources": 6, "status_counts": {"failed": 6}}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
