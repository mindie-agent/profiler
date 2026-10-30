# Current profiling validation

One canonical case registry and one recorded Sim package. Frozen native service functions are evaluated separately from Sim Body prediction. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.

| Case | Phase | Calls | Real mean / P50 / P90 ms | Sim ms | Error | Status |
|---|---|---:|---:|---:|---:|---|
| glm-a5-retrospective-concurrency-exclusion | native_service | — | — / — / — | — | — | completed |

| Experiment | Relation | Fitted domains | Passed / predicted populations |
|---|---|---:|---:|
| glm-a5-retrospective-concurrency-exclusion | retrospective_leave_concurrency_out | 25 | 144 / 150 |

Retrospective source holdout is not new blind validation. Native activity differences are not additive Body wall-time errors.

Summary: {"completed": 1, "experiments": 1, "passed": 144, "planned": 0, "populations": 150, "predicted": 150}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
