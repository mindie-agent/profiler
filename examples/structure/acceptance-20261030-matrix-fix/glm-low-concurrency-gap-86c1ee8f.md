# GLM family / role activity residuals

These are completed-program comparisons against unchanged saved observations. Activity residuals are not additive body wall-time attribution.
Strict, conditional reference and missing-prediction populations remain separate. P50 is identified by its exact population; a whole-family P50 does not describe a scored subset.
Saved comparison runtime arm: `86c1ee8f`. Raw capture reads: 0; separate declared-program control executions: 0.

## glm53flash-a5-tp8-c1

Selected Forward: 65 / 65; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 4, "sequences_per_replica": 1, "tokens_per_sequence": 4}`.
Declared conditional execution: `{"context": 4104, "phase": "decode", "scope": "body", "sequences": 1, "tokens": 4}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down | 42.000 | 22.481670 / 22.473000 | 8.800237 | -0.574620 | strict_tensor_cohort |
| MatMulV3 / router | 42.000 | 8.756307 / 8.742500 | 16.544000 | +0.327083 | strict_tensor_cohort |
| MatMulV3 / linear_qkvbfg_a | 34.000 | 16.983133 / 16.915000 | 8.208353 | -0.298343 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre | 45.000 | 11.033061 / 10.866000 | 20.491576 | +0.425633 | conditional_cohort_program_reference |
| HcPre / ffn.hc_pre | 45.000 | 11.216654 / 11.078000 | 20.491576 | +0.417371 | conditional_cohort_program_reference |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 23.102891 / 17.851000 | 25.346286 | +0.100953 | conditional_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 42.000 | 33.520363 / 33.429000 | — | +1.407855 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 23.102891 / 17.851000 | — | +1.039630 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 45.000 | 20.753405 / 18.202000 | — | +0.933903 | no_strict_prediction |

## glm53flash-a5-tp8-c3

Selected Forward: 53 / 53; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 16, "sequences_per_replica": 4, "tokens_per_sequence": 4}`.
Declared conditional execution: `{"context": 4104, "phase": "decode", "scope": "body", "sequences": 4, "tokens": 4}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down | 42.000 | 51.524202 / 51.382000 | 34.955437 | -0.695888 | strict_tensor_cohort |
| MatMulV3 / router | 42.000 | 9.419784 / 9.392000 | 20.437333 | +0.462737 | strict_tensor_cohort |
| MatMulV3 / linear_qkvbfg_a | 34.000 | 17.825856 / 17.762000 | 9.002139 | -0.300006 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre | 45.000 | 11.752889 / 11.566000 | 26.539394 | +0.665393 | conditional_cohort_program_reference |
| HcPre / ffn.hc_pre | 45.000 | 11.905497 / 11.728000 | 26.539394 | +0.658525 | conditional_cohort_program_reference |
| MoeGatingTopK / router_selection | 42.000 | 3.519770 / 3.504000 | 3.936000 | +0.017482 | conditional_cohort_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 42.000 | 98.728124 / 98.517500 | — | +4.146581 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 26.141899 / 20.766000 | — | +1.176385 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 45.000 | 23.333207 / 21.872000 | — | +1.049994 | no_strict_prediction |

## Saved owner-candidate controls

The following same-runtime, same-operator controls isolate the historical 83f720ae owner-candidate change. A later whole-runtime delta must not be attributed solely to this change.

| Source / shape | Original us | Owner candidates us | Original tile | Selected tile |
| --- | ---: | ---: | --- | --- |
