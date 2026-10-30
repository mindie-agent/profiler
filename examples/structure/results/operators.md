# Current profiling validation

One canonical case registry and one recorded Sim package. All costs are fresh in this run. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.


| Case | Tier | Passed / compared cohorts | Scored events |
|---|---|---:|---:|
| qwen35-397b-a3-tp16-c48 | micro_absolute_15us | 19 / 19 | 18630 |
| qwen35-397b-a3-tp16-c48 | heavy_relative_15pct | 3 / 3 | 3795 |
| qwen36-a5-tp2-c96 | micro_absolute_15us | 8 / 10 | 9600 |
| qwen36-a5-tp2-c96 | heavy_relative_15pct | 1 / 3 | 4224 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | micro_absolute_15us | 18 / 18 | 44025 |
| a5_glm53flash_tp8_c4_p8k | micro_absolute_15us | 16 / 16 | 4543 |
| a5_glm53flash_tp8_c4_p8k | heavy_relative_15pct | 1 / 1 | 462 |
| a3_kimi4_tp8_w4a8_c1 | micro_absolute_15us | 16 / 16 | 8382 |
| a3_kimi4_tp8_w4a8_c1 | heavy_relative_15pct | 0 / 1 | 254 |
| a3_kimi4_tp8_w4a8_c16 | micro_absolute_15us | 18 / 18 | 8460 |
| a3_kimi4_tp8_w4a8_c16 | heavy_relative_15pct | 0 / 1 | 235 |
| a3_kimi4_tp8_w4a8_c32 | micro_absolute_15us | 18 / 18 | 7920 |
| a3_kimi4_tp8_w4a8_c32 | heavy_relative_15pct | 0 / 1 | 220 |
| a3_kimi4_tp8_w4a8_c4 | micro_absolute_15us | 16 / 16 | 7380 |
| a3_kimi4_tp8_w4a8_c4 | heavy_relative_15pct | 0 / 1 | 246 |
| a3_kimi4_tp8_w4a8_c64 | micro_absolute_15us | 17 / 17 | 6860 |
| a3_kimi4_tp8_w4a8_c64 | heavy_relative_15pct | 1 / 2 | 392 |
| a5_kimi_tp8_e16_bf16_c16_p16k | heavy_relative_15pct | 2 / 2 | 1175 |
| a5_kimi_tp8_e16_bf16_c16_p16k | micro_absolute_15us | 12 / 12 | 36942 |
| a5_kimi_tp8_e16_bf16_c16_p4k | micro_absolute_15us | 13 / 13 | 39690 |
| a5_kimi_tp8_e16_bf16_c16_p4k | heavy_relative_15pct | 1 / 1 | 49 |
| a5_kimi_tp8_e16_bf16_c1_p16k | micro_absolute_15us | 13 / 13 | 41064 |
| a5_kimi_tp8_e16_bf16_c1_p4k | micro_absolute_15us | 13 / 13 | 41064 |
| a5_kimi_tp8_e16_bf16_c2_p16k | micro_absolute_15us | 12 / 12 | 33858 |
| a5_kimi_tp8_e16_bf16_c2_p4k | micro_absolute_15us | 12 / 12 | 34485 |
| a5_kimi_tp8_e16_bf16_c32_p16k | heavy_relative_15pct | 2 / 2 | 1025 |
| a5_kimi_tp8_e16_bf16_c32_p16k | micro_absolute_15us | 12 / 12 | 32226 |
| a5_kimi_tp8_e16_bf16_c32_p4k | heavy_relative_15pct | 2 / 2 | 1150 |
| a5_kimi_tp8_e16_bf16_c32_p4k | micro_absolute_15us | 12 / 12 | 36156 |
| a5_kimi_tp8_e16_bf16_c4_p16k | micro_absolute_15us | 12 / 12 | 32604 |
| a5_kimi_tp8_e16_bf16_c4_p4k | micro_absolute_15us | 12 / 12 | 33231 |
| a5_kimi_tp8_e16_bf16_c8_p16k | heavy_relative_15pct | 1 / 1 | 1224 |
| a5_kimi_tp8_e16_bf16_c8_p16k | micro_absolute_15us | 13 / 13 | 40137 |
| a5_kimi_tp8_e16_bf16_c8_p4k | micro_absolute_15us | 14 / 14 | 42172 |
| a5_glm53flash_heldout_c12_p4k | micro_absolute_15us | 22 / 23 | 14060 |
| a5_glm53flash_heldout_c24_p12k | micro_absolute_15us | 22 / 22 | 13881 |
| a5_glm53flash_heldout_c24_p12k | heavy_relative_15pct | 1 / 1 | 882 |

| Case | Selected / observed geometries | Selected / observed Forward calls | Scope |
|---|---:|---:|---|
| qwen35-397b-a3-tp16-c48 | 1 / 1 | 23 / 23 | primary_population |
| qwen36-a5-tp2-c96 | 1 / 1 | 24 / 24 | primary_population |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 1 / 1 | 75 / 75 | primary_population |
| a5_glm53flash_tp8_c4_p8k | 1 / 3 | 11 / 23 | primary_population |
| a3_kimi4_tp8_w4a8_c1 | 1 / 1 | 254 / 254 | primary_population |
| a3_kimi4_tp8_w4a8_c16 | 1 / 2 | 235 / 238 | primary_population |
| a3_kimi4_tp8_w4a8_c32 | 1 / 6 | 220 / 229 | primary_population |
| a3_kimi4_tp8_w4a8_c4 | 1 / 3 | 246 / 253 | primary_population |
| a3_kimi4_tp8_w4a8_c64 | 1 / 7 | 196 / 207 | primary_population |
| a5_kimi_tp8_e16_bf16_c16_p16k | 1 / 1 | 47 / 47 | primary_population |
| a5_kimi_tp8_e16_bf16_c16_p4k | 1 / 1 | 49 / 49 | primary_population |
| a5_kimi_tp8_e16_bf16_c1_p16k | 1 / 1 | 59 / 59 | primary_population |
| a5_kimi_tp8_e16_bf16_c1_p4k | 1 / 1 | 59 / 59 | primary_population |
| a5_kimi_tp8_e16_bf16_c2_p16k | 1 / 1 | 54 / 54 | primary_population |
| a5_kimi_tp8_e16_bf16_c2_p4k | 1 / 1 | 55 / 55 | primary_population |
| a5_kimi_tp8_e16_bf16_c32_p16k | 1 / 1 | 41 / 41 | primary_population |
| a5_kimi_tp8_e16_bf16_c32_p4k | 1 / 1 | 46 / 46 | primary_population |
| a5_kimi_tp8_e16_bf16_c4_p16k | 1 / 1 | 52 / 52 | primary_population |
| a5_kimi_tp8_e16_bf16_c4_p4k | 1 / 1 | 53 / 53 | primary_population |
| a5_kimi_tp8_e16_bf16_c8_p16k | 1 / 1 | 51 / 51 | primary_population |
| a5_kimi_tp8_e16_bf16_c8_p4k | 1 / 1 | 52 / 52 | primary_population |
| a5_glm53flash_heldout_c12_p4k | 1 / 6 | 20 / 60 | primary_population |
| a5_glm53flash_heldout_c24_p12k | 1 / 4 | 21 / 41 | primary_population |

Contract and fusion-boundary exclusions remain in the complete family population and SHA256-pinned evidence. A strict cohort score does not cover unscored families or unselected geometry populations.

Summary: {"compared": 0, "operator_tiers": {"heavy_relative_15pct": {"compared": 22, "events": 15333, "passed": 15}, "micro_absolute_15us": {"compared": 343, "events": 587370, "passed": 340}}, "passed": 0, "requested_sources": 23, "sources": 23, "status_counts": {"operator_compared": 23}, "strict_compared": 365, "strict_passed": 355}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
