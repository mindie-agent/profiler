# GLM family / role activity residuals

These are completed-program comparisons against unchanged saved observations. Activity residuals are not additive body wall-time attribution.
Strict, conditional reference and missing-prediction populations remain separate. P50 is identified by its exact population; a whole-family P50 does not describe a scored subset.
Saved comparison runtime arm: `86c1ee8f`. Raw capture reads: 0; separate declared-program control executions: 0.

## glm53flash-a3-tp16-c16-livepre

Selected Forward: 37 / 108; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 96, "sequences_per_replica": 16, "tokens_per_sequence": 6}`.
Declared conditional execution: `{"context": 4096, "phase": "decode", "scope": "body", "sequences": 16, "tokens": 6}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| HcPost / attention.hc_post_group | 45.000 | 20.206429 / 19.701000 | 6.702545 | -0.607675 | strict_tensor_cohort |
| MatMulV2 / index_k | 22.000 | 7.501405 / 8.160000 | 35.103030 | +0.607236 | strict_tensor_cohort |
| HcPost / ffn.hc_post_group | 45.000 | 20.081944 / 19.840000 | 6.702545 | -0.602073 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre | 45.000 | 33.367166 / 33.321000 | 170.549236 | +6.173193 | conditional_cohort_program_reference |
| HcPre / ffn.hc_pre | 45.000 | 36.039351 / 36.780000 | 170.549236 | +6.052945 | conditional_cohort_program_reference |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 142.415490 / 142.163000 | 285.782843 | +6.021429 | conditional_cohort_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 142.415490 / 142.163000 | — | +5.981451 | no_strict_prediction |
| KvQuantSparseFlashAttentionVllm / unresolved | 11.000 | 377.579678 / 377.447000 | — | +4.153376 | no_strict_prediction |
| MoeDistributeCombineV2 / unresolved | 42.000 | 74.555821 / 70.811000 | — | +3.131344 | no_strict_prediction |

## Saved owner-candidate controls

The following same-runtime, same-operator controls isolate the historical 83f720ae owner-candidate change. A later whole-runtime delta must not be attributed solely to this change.

| Source / shape | Original us | Owner candidates us | Original tile | Selected tile |
| --- | ---: | ---: | --- | --- |
