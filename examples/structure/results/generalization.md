# Current profiling validation

One canonical case registry and one recorded Sim package. Frozen native service functions are evaluated separately from Sim Body prediction. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.


| Experiment | Relation | Fitted domains | Passed / predicted / total populations | Admitted / Body events |
|---|---|---:|---:|---:|
| glm-a5-retrospective-concurrency-exclusion | retrospective_leave_concurrency_out | 25 | 144 / 150 / 150 | — |
| a5-heldout-frozen-native-functions | frozen_training_function_transfer_to_new_capture | 25 | 70 / 73 / 73 | — |
| qwen-cross-TP-matrix-physical-functions | retrospective_cross_TP_frozen_training_validation | 2 | 29 / 30 / 30 | — |
| kimi-a5-retrospective-concurrency-exclusion | retrospective_leave_concurrency_out | 52 | 452 / 454 / 494 | 806074 / 3348783 |
| kimi-a3-retrospective-concurrency-exclusion | retrospective_leave_concurrency_out | 35 | 81 / 83 / 92 | 53265 / 196839 |

Retrospective source holdout is not new blind validation. Native activity differences are not additive Body wall-time errors.

Summary: {"completed": 5, "experiments": 5, "passed": 776, "planned": 0, "populations": 839, "predicted": 790}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
