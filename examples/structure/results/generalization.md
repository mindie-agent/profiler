# Current profiling validation

One canonical case registry and one recorded Sim package. Frozen native service functions are evaluated separately from Sim Body prediction. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.


| Experiment | Relation | Fitted domains | Passed / predicted / total populations | Admitted / Body events |
|---|---|---:|---:|---:|
| glm-a5-retrospective-concurrency-exclusion | retrospective_leave_concurrency_out | 25 | 144 / 150 / 150 | — |
| a5-heldout-frozen-native-functions | frozen_training_function_transfer_to_new_capture | 25 | 70 / 73 / 73 | — |
| qwen-cross-TP-matrix-physical-functions | retrospective_cross_TP_frozen_training_validation | 2 | 29 / 30 / 30 | — |
| kimi-a5-retrospective-concurrency-exclusion | retrospective_leave_concurrency_out | 52 | 452 / 454 / 494 | 806074 / 3348783 |
| kimi-a3-retrospective-concurrency-exclusion | retrospective_leave_concurrency_out | 35 | 81 / 83 / 92 | 53265 / 196839 |
| glm-a5-frozen-grouped-hccl-new-captures | retrospective_new_capture_native_function_transfer_no_body_fit | 2 | 6 / 6 / 6 | — |
| glm-a5-frozen-helpers-new-captures | retrospective_new_capture_helper_function_transfer_no_body_fit | 6 | 13 / 18 / 18 | — |
| kimi-a3-tp8-new-client-native-coverage | client_observation_only; native_generalization_not_run | — | — / — / — | — |
| kimi-a3-tp16-new-client-native-coverage | client_observation_only; native_generalization_not_run | — | — / — / — | — |

kimi-a3-tp8-new-client-native-coverage: device_capture_missing; retained client Decode metrics do not provide native latency populations. Coverage: {"body_accuracy_available": false, "client_concurrency": [2, 6, 8, 12, 24, 48, 64], "client_requests": 840, "client_runs": 39, "decode_device_captures": 0, "decode_sweep_runs": 28, "duplicate_prof_summary_copies_excluded": 11, "ep": 8, "failed_requests": 0, "native_populations": null, "output_tokens": 119296, "prefill_only_device_captures_excluded": 6, "profile_intended_runs": 11, "prompt_tokens": [4096, 8192, 16384, 32768], "successful_requests": 840, "tp": 8}

kimi-a3-tp16-new-client-native-coverage: device_capture_missing; retained client Decode metrics do not provide native latency populations. Coverage: {"body_accuracy_available": false, "client_concurrency": [2, 6, 8, 12, 24, 48, 64], "client_requests": 840, "client_runs": 39, "decode_device_captures": 0, "decode_sweep_runs": 28, "duplicate_prof_summary_copies_excluded": 11, "ep": 16, "failed_requests": 0, "native_populations": null, "output_tokens": 119296, "prefill_only_device_captures_excluded": 6, "profile_intended_runs": 11, "prompt_tokens": [4096, 8192, 16384, 32768], "successful_requests": 840, "tp": 16}

Retrospective source holdout is not new blind validation. Native activity differences are not additive Body wall-time errors.

Summary: {"completed": 7, "experiments": 9, "passed": 795, "planned": 2, "populations": 863, "predicted": 814}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
