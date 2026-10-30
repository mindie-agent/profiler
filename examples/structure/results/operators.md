# Current profiling validation

One canonical case registry and one recorded Sim package. All costs are fresh in this run. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.

| Case | Phase | Calls | Real mean / P50 / P90 ms | Sim ms | Error | Status |
|---|---|---:|---:|---:|---:|---|
| qwen36-a5-tp2-c1 | decode | — | — / — / — | — | — | completed |

| Case | Tier | Passed / compared cohorts | Scored events |
|---|---|---:|---:|
| qwen36-a5-tp2-c1 | micro_absolute_15us | 13 / 13 | 48960 |

Summary: {"compared": 0, "operator_tiers": {"micro_absolute_15us": {"compared": 13, "events": 48960, "passed": 13}}, "passed": 0, "requested_sources": 1, "sources": 1, "status_counts": {"operator_compared": 1}}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
