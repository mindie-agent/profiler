# GLM family / role activity residuals

These are completed-program comparisons against unchanged saved observations. Activity residuals are not additive body wall-time attribution.
Strict, conditional reference and missing-prediction populations remain separate. P50 is identified by its exact population; a whole-family P50 does not describe a scored subset.
Saved comparison runtime arm: `67ca7673`. Raw capture reads: 0; separate declared-program control executions: 321.

## a5_glm53flash_tp8_c32_p4k

Selected Forward: 31 / 37; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 128, "sequences_per_replica": 32, "tokens_per_sequence": 4}`.
Declared conditional execution: `{"context": 4104, "phase": "decode", "scope": "body", "sequences": 32, "tokens": 4}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down | 42.000 | 109.823710 / 110.412500 | 87.875533 | -0.921823 | strict_tensor_cohort |
| MatMulV3 / linear_qkvbfg_a | 34.000 | 26.517168 / 26.598500 | 16.565962 | -0.338341 | strict_tensor_cohort |
| HcPost / attention.hc_post_group | 45.000 | 8.079065 / 8.107000 | 2.792727 | -0.237885 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| HcPre / ffn.hc_pre | 45.000 | 16.094834 / 15.947000 | 25.185311 | +0.409071 | conditional_cohort_program_reference |
| HcPre / attention.hc_pre | 45.000 | 16.554465 / 16.336000 | 25.185311 | +0.388388 | conditional_cohort_program_reference |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 36.213117 / 32.117000 | 29.881143 | -0.284939 | conditional_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 42.000 | 207.865399 / 207.616000 | — | +8.730347 | no_strict_prediction |
| SparseFlashMla / unresolved | 11.000 | 153.517238 / 153.209000 | — | +1.688690 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 45.000 | 36.340983 / 36.058000 | — | +1.635344 | no_strict_prediction |

## a3_glm53flash_tp16_aclgraph_c16

Selected Forward: 50 / 65; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 96, "sequences_per_replica": 16, "tokens_per_sequence": 6}`.
Declared conditional execution: `{"context": 4096, "phase": "decode", "scope": "body", "sequences": 16, "tokens": 6}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| QuantBatchMatmulV3 / shared.down | 42.000 | 20.758582 / 21.221000 | 5.000000 | -0.661860 | strict_tensor_cohort |
| HcPost / attention.hc_post_group | 45.000 | 21.016595 / 20.701000 | 6.702545 | -0.644132 | strict_tensor_cohort |
| HcPost / ffn.hc_post_group | 45.000 | 19.447442 / 19.800000 | 6.702545 | -0.573520 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 241.813110 / 241.925000 | 309.212347 | +2.830768 | conditional_cohort_program_reference |
| hcom_allReduce_ / attention_output_communication | 45.000 | 58.617251 / 58.341000 | 82.523265 | +1.075771 | conditional_program_reference |
| HcPre / attention.hc_pre | 45.000 | 39.825860 / 39.140500 | 61.206478 | +0.962128 | conditional_cohort_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 241.813110 / 241.925000 | — | +10.156151 | no_strict_prediction |
| GroupedMatmul / expert_down | 42.000 | 119.515611 / 118.882000 | — | +5.019656 | no_strict_prediction |
| KvQuantSparseFlashAttentionVllm / unresolved | 11.000 | 423.889944 / 423.878000 | — | +4.662789 | no_strict_prediction |

## a3_glm53flash_tp16_aclgraph_c32

Selected Forward: 49 / 65; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 192, "sequences_per_replica": 32, "tokens_per_sequence": 6}`.
Declared conditional execution: `{"context": 4096, "phase": "decode", "scope": "body", "sequences": 32, "tokens": 6}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| QuantBatchMatmulV3 / shared.down | 42.000 | 28.640508 / 29.241000 | 5.000000 | -0.992901 | strict_tensor_cohort |
| HcPost / attention.hc_post_group | 45.000 | 30.239390 / 29.960000 | 13.405091 | -0.757543 | strict_tensor_cohort |
| HcPost / ffn.hc_post_group | 45.000 | 28.713158 / 28.261000 | 13.405091 | -0.688863 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 243.004965 / 243.004500 | 312.921712 | +2.936503 | conditional_cohort_program_reference |
| HcPre / attention.hc_pre | 45.000 | 52.079518 / 51.581000 | 87.561105 | +1.596671 | conditional_cohort_program_reference |
| HcPre / ffn.hc_pre | 45.000 | 52.730372 / 52.241000 | 87.561105 | +1.567383 | conditional_cohort_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 243.004965 / 243.004500 | — | +10.206209 | no_strict_prediction |
| KvQuantSparseFlashAttentionVllm / unresolved | 11.000 | 829.848284 / 829.977000 | — | +9.128331 | no_strict_prediction |
| GroupedMatmul / expert_down | 42.000 | 120.124715 / 119.862000 | — | +5.045238 | no_strict_prediction |

## a3_glm53flash_tp16_aclgraph_c64

Selected Forward: 47 / 69; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 384, "sequences_per_replica": 64, "tokens_per_sequence": 6}`.
Declared conditional execution: `{"context": 4096, "phase": "decode", "scope": "body", "sequences": 64, "tokens": 6}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| QuantBatchMatmulV3 / shared.down | 42.000 | 41.693854 / 43.221000 | 8.887816 | -1.377854 | strict_tensor_cohort |
| MatMulV2 / linear_qkvbfg_a | 34.000 | 64.340868 / 64.531500 | 101.404548 | +1.260165 | strict_tensor_cohort |
| HcPost / attention.hc_post_group | 45.000 | 51.747264 / 51.981000 | 26.810182 | -1.122169 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre | 45.000 | 66.201462 / 66.121000 | 140.274938 | +3.333306 | conditional_cohort_program_reference |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 245.404965 / 245.005000 | 320.328223 | +3.146777 | conditional_cohort_program_reference |
| HcPre / ffn.hc_pre | 45.000 | 75.215619 / 77.602000 | 140.274938 | +2.927669 | conditional_cohort_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| KvQuantSparseFlashAttentionVllm / unresolved | 11.000 | 1632.353474 / 1632.673000 | — | +17.955888 | no_strict_prediction |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 245.404965 / 245.005000 | — | +10.307009 | no_strict_prediction |
| RecurrentKda / unresolved | 34.000 | 245.540307 / 250.525000 | — | +8.348370 | no_strict_prediction |

## a3_glm53flash_tp16_aclgraph_c8

Selected Forward: 47 / 62; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 48, "sequences_per_replica": 8, "tokens_per_sequence": 6}`.
Declared conditional execution: `{"context": 4096, "phase": "decode", "scope": "body", "sequences": 8, "tokens": 6}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| QuantBatchMatmulV3 / shared.down | 42.000 | 18.706672 / 19.281000 | 5.000000 | -0.575680 | strict_tensor_cohort |
| HcPost / attention.hc_post_group | 45.000 | 16.098113 / 15.220000 | 3.351273 | -0.573608 | strict_tensor_cohort |
| HcPost / ffn.hc_post_group | 45.000 | 15.306410 / 14.480000 | 3.351273 | -0.537981 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 226.014961 / 225.564000 | 307.363773 | +3.416650 | conditional_cohort_program_reference |
| hcom_allReduce_ / attention_output_communication | 45.000 | 46.774581 / 43.241000 | 78.761633 | +1.439417 | conditional_program_reference |
| HcPre / attention.hc_pre | 45.000 | 37.136530 / 36.921000 | 53.874366 | +0.753203 | conditional_cohort_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 226.014961 / 225.564000 | — | +9.492628 | no_strict_prediction |
| GroupedMatmul / expert_down | 42.000 | 113.792990 / 112.992500 | — | +4.779306 | no_strict_prediction |
| KvQuantSparseFlashAttentionVllm / unresolved | 11.000 | 260.822161 / 260.605000 | — | +2.869044 | no_strict_prediction |

## a5_glm53flash_tp8_c16_p4k

Selected Forward: 30 / 43; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 64, "sequences_per_replica": 16, "tokens_per_sequence": 4}`.
Declared conditional execution: `{"context": 4104, "phase": "decode", "scope": "body", "sequences": 16, "tokens": 4}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down | 42.000 | 103.103622 / 102.831500 | 86.575128 | -0.694197 | strict_tensor_cohort |
| MatMulV3 / linear_qkvbfg_a | 34.000 | 22.750231 / 22.714500 | 12.293648 | -0.355524 | strict_tensor_cohort |
| HcPost / attention.hc_post_group | 45.000 | 6.545442 / 6.587000 | 1.396364 | -0.231709 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| HcPre / ffn.hc_pre | 45.000 | 14.502584 / 14.361000 | 22.827167 | +0.374606 | conditional_cohort_program_reference |
| HcPre / attention.hc_pre | 45.000 | 14.527364 / 14.265000 | 22.827167 | +0.373491 | conditional_cohort_program_reference |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 34.090064 / 31.334500 | 27.540571 | -0.294727 | conditional_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 42.000 | 206.227306 / 205.998000 | — | +8.661547 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 45.000 | 34.736936 / 34.072000 | — | +1.563162 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 34.090064 / 31.334500 | — | +1.534053 | no_strict_prediction |

## a5_glm53flash_tp8_c16_p8k

Selected Forward: 32 / 42; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 64, "sequences_per_replica": 16, "tokens_per_sequence": 4}`.
Declared conditional execution: `{"context": 8200, "phase": "decode", "scope": "body", "sequences": 16, "tokens": 4}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down | 42.000 | 102.723711 / 102.577500 | 86.575128 | -0.678240 | strict_tensor_cohort |
| MatMulV3 / linear_qkvbfg_a | 34.000 | 22.732266 / 22.766500 | 12.293648 | -0.354913 | strict_tensor_cohort |
| HcPost / attention.hc_post_group | 45.000 | 6.437415 / 6.449500 | 1.396364 | -0.226847 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre | 45.000 | 14.473638 / 14.170000 | 22.827167 | +0.375909 | conditional_cohort_program_reference |
| HcPre / ffn.hc_pre | 45.000 | 14.575522 / 14.436000 | 22.827167 | +0.371324 | conditional_cohort_program_reference |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 33.869449 / 31.147500 | 27.540571 | -0.284800 | conditional_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 42.000 | 206.104943 / 205.956000 | — | +8.656408 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 45.000 | 34.790455 / 34.321000 | — | +1.565570 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 33.869449 / 31.147500 | — | +1.524125 | no_strict_prediction |

## a5_glm53flash_tp8_c32_p8k

Selected Forward: 35 / 36; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 128, "sequences_per_replica": 32, "tokens_per_sequence": 4}`.
Declared conditional execution: `{"context": 8200, "phase": "decode", "scope": "body", "sequences": 32, "tokens": 4}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down | 42.000 | 109.852636 / 110.480500 | 87.875533 | -0.923038 | strict_tensor_cohort |
| MatMulV3 / linear_qkvbfg_a | 34.000 | 26.307467 / 26.423500 | 16.565962 | -0.331211 | strict_tensor_cohort |
| HcPost / attention.hc_post_group | 45.000 | 8.074132 / 8.081000 | 2.792727 | -0.237663 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| HcPre / ffn.hc_pre | 45.000 | 16.156022 / 15.992000 | 25.185311 | +0.406318 | conditional_cohort_program_reference |
| HcPre / attention.hc_pre | 45.000 | 16.533962 / 16.295000 | 25.185311 | +0.389311 | conditional_cohort_program_reference |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 36.167619 / 32.281000 | 29.881143 | -0.282891 | conditional_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 42.000 | 207.848620 / 207.460500 | — | +8.729642 | no_strict_prediction |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 11.000 | 218.772068 / 218.705000 | — | +2.406493 | no_strict_prediction |
| SparseFlashMla / unresolved | 11.000 | 153.329047 / 153.215000 | — | +1.686620 | no_strict_prediction |

## a5_glm53flash_tp8_c4_p8k

Selected Forward: 11 / 23; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 16, "sequences_per_replica": 4, "tokens_per_sequence": 4}`.
Declared conditional execution: `{"context": 8200, "phase": "decode", "scope": "body", "sequences": 4, "tokens": 4}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down | 42.000 | 51.435175 / 51.333500 | 38.227437 | -0.554725 | strict_tensor_cohort |
| MatMulV3 / linear_qkvbfg_a | 34.000 | 18.013869 / 17.927000 | 9.089412 | -0.303432 | strict_tensor_cohort |
| QuantBatchMatmulV3 / shared.gate_up | 42.000 | 7.366050 / 7.275000 | 1.578000 | -0.243098 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre | 45.000 | 11.760531 / 11.581000 | 22.566303 | +0.486260 | conditional_cohort_program_reference |
| HcPre / ffn.hc_pre | 45.000 | 11.932707 / 11.783000 | 22.566303 | +0.478512 | conditional_cohort_program_reference |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 21.899271 / 20.531000 | 25.785143 | +0.174864 | conditional_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 42.000 | 98.457779 / 98.182000 | — | +4.135227 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 45.000 | 23.918246 / 22.357000 | — | +1.076321 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 21.899271 / 20.531000 | — | +0.985467 | no_strict_prediction |

## a5_glm53flash_tp8_c64_p4k

Selected Forward: 31 / 31; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 256, "sequences_per_replica": 64, "tokens_per_sequence": 4}`.
Declared conditional execution: `{"context": 4104, "phase": "decode", "scope": "body", "sequences": 64, "tokens": 4}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down | 42.000 | 115.776834 / 117.336500 | 90.476344 | -1.062621 | strict_tensor_cohort |
| HcPost / attention.hc_post_group | 45.000 | 11.931811 / 12.155000 | 5.585455 | -0.285586 | strict_tensor_cohort |
| RmsNorm / norm2 | 45.000 | 6.344769 / 6.415000 | 1.312000 | -0.226475 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| HcPre / ffn.hc_pre | 45.000 | 21.747629 / 21.578000 | 31.740455 | +0.449677 | conditional_cohort_program_reference |
| HcPre / attention.hc_pre | 45.000 | 22.094420 / 21.964000 | 31.740455 | +0.434072 | conditional_cohort_program_reference |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 43.604663 / 39.492000 | 34.562286 | -0.406907 | conditional_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 42.000 | 211.088745 / 210.722500 | — | +8.865727 | no_strict_prediction |
| SparseFlashMla / unresolved | 11.000 | 288.254073 / 285.492000 | — | +3.170795 | no_strict_prediction |
| RecurrentKda / unresolved | 34.000 | 78.338271 / 78.285000 | — | +2.663501 | no_strict_prediction |

## a5_glm53flash_tp8_c8_p4k

Selected Forward: 30 / 38; observed geometry: `{"batch_basis": "captured_paged_attention_block_table_rows", "context_basis": "not_observed_from_cache_capacity", "context_tokens": null, "query_rows": 32, "sequences_per_replica": 8, "tokens_per_sequence": 4}`.
Declared conditional execution: `{"context": 4104, "phase": "decode", "scope": "body", "sequences": 8, "tokens": 4}`. Declared context is not observed active KV length.

### Strict residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down | 42.000 | 91.186176 / 90.988000 | 76.438589 | -0.619399 | strict_tensor_cohort |
| MatMulV3 / linear_qkvbfg_a | 34.000 | 20.058085 / 19.984000 | 10.157490 | -0.336620 | strict_tensor_cohort |
| MatMulV3 / router | 42.000 | 12.318930 / 12.226500 | 6.587640 | -0.240714 | strict_tensor_cohort |

### Conditional reference residual Top 3

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre | 45.000 | 13.619847 / 13.420500 | 22.566303 | +0.402591 | conditional_cohort_program_reference |
| HcPre / ffn.hc_pre | 45.000 | 14.085336 / 13.919000 | 22.566303 | +0.381644 | conditional_cohort_program_reference |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 28.658934 / 23.094000 | 26.370286 | -0.102989 | conditional_program_reference |

### Unscored activity Top 3 — exposure, not prediction error

| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 42.000 | 184.592108 / 184.146500 | — | +7.752869 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / attention_output_communication | 45.000 | 28.658934 / 23.094000 | — | +1.289652 | no_strict_prediction |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 45.000 | 27.877279 / 27.107000 | — | +1.254478 | no_strict_prediction |

## Saved owner-candidate controls

The following same-runtime, same-operator controls isolate the historical 83f720ae owner-candidate change. A later whole-runtime delta must not be attributed solely to this change.

| Source / shape | Original us | Owner candidates us | Original tile | Selected tile |
| --- | ---: | ---: | --- | --- |
| body-operator-a5_glm53flash_tp8_c16_p4k-glm-flash-ws9.case.json / [64, 288, 4096] | 80.003879 | 10.506674 | {'tile_m': 128, 'tile_n': 128, 'tile_k': 64, 'compute_m': 128, 'compute_n': 128, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} | {'tile_m': 32, 'tile_n': 32, 'tile_k': 128, 'compute_m': 32, 'compute_n': 32, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} |
| body-operator-a5_glm53flash_tp8_c16_p8k-glm-flash-ws9.case.json / [64, 288, 4096] | 80.003879 | 10.506674 | {'tile_m': 128, 'tile_n': 128, 'tile_k': 64, 'compute_m': 128, 'compute_n': 128, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} | {'tile_m': 32, 'tile_n': 32, 'tile_k': 128, 'compute_m': 32, 'compute_n': 32, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} |
| body-operator-a5_glm53flash_tp8_c32_p4k-glm-flash-ws9.case.json / [128, 288, 4096] | 159.681939 | 19.749818 | {'tile_m': 128, 'tile_n': 128, 'tile_k': 64, 'compute_m': 128, 'compute_n': 128, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} | {'tile_m': 16, 'tile_n': 32, 'tile_k': 128, 'compute_m': 16, 'compute_n': 32, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} |
| body-operator-a5_glm53flash_tp8_c32_p8k-glm-flash-ws9.case.json / [128, 288, 4096] | 159.681939 | 19.749818 | {'tile_m': 128, 'tile_n': 128, 'tile_k': 64, 'compute_m': 128, 'compute_n': 128, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} | {'tile_m': 16, 'tile_n': 32, 'tile_k': 128, 'compute_m': 16, 'compute_n': 32, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} |
| body-operator-a5_glm53flash_tp8_c4_p8k-glm-flash-ws9.case.json / [16, 288, 4096] | 21.988848 | 4.092850 | {'tile_m': 128, 'tile_n': 128, 'tile_k': 64, 'compute_m': 128, 'compute_n': 128, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} | {'tile_m': 16, 'tile_n': 16, 'tile_k': 128, 'compute_m': 16, 'compute_n': 16, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} |
| body-operator-a5_glm53flash_tp8_c64_p4k-glm-flash-ws9.case.json / [256, 288, 4096] | 159.681939 | 31.493818 | {'tile_m': 128, 'tile_n': 128, 'tile_k': 64, 'compute_m': 128, 'compute_n': 128, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} | {'tile_m': 32, 'tile_n': 32, 'tile_k': 128, 'compute_m': 32, 'compute_n': 32, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} |
| body-operator-a5_glm53flash_tp8_c8_p4k-glm-flash-ws9.case.json / [32, 288, 4096] | 40.164848 | 6.587640 | {'tile_m': 128, 'tile_n': 128, 'tile_k': 64, 'compute_m': 128, 'compute_n': 128, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} | {'tile_m': 16, 'tile_n': 32, 'tile_k': 128, 'compute_m': 16, 'compute_n': 32, 'slots': 2, 'compute_slots': 2, 'reuse_inputs': True, 'reuse_weights': True} |

## Same-runtime underfilled-only controls

Control runtime: `86c1ee8f`; kept separate from the saved comparison arm above.

All three arms share each exact declared operator and runtime. Only `underfilled_candidates` changes; narrow candidates and dtype stay fixed. These controls do not bind a native invocation or predict a body critical path.

| Declared recipe / shape / compute | Default us | Disabled us | Explicit underfilled us |
| --- | ---: | ---: | ---: |
| hc_projection / [128, 24, 16384] / fp32 | 16.006303 | 15.948121 | 16.006303 |
| linear_qkvbfg_a / [128, 3336, 4096] / bf16 | 16.565962 | 16.565962 | 16.565962 |
| linear_gate_b / [128, 1024, 128] / bf16 | 1.578000 | 1.578000 | 1.578000 |
| linear_decay_b / [128, 1024, 128] / bf16 | 1.578000 | 1.578000 | 1.578000 |
| linear_output / [128, 4096, 1024] / bf16 | 4.699477 | 4.699477 | 4.699477 |
| dense_gate_up / [128, 3072, 4096] / fp8_e4m3 | 8.623760 | 8.623760 | 8.623760 |
| dense_down / [128, 4096, 1536] / fp8_e4m3 | 3.569296 | 3.569296 | 3.569296 |
| qkv_a / [128, 2048, 4096] / bf16 | 16.484042 | 16.484042 | 16.484042 |
| q_b / [128, 2048, 1536] / bf16 | 6.554345 | 6.554345 | 6.554345 |
| q_absorb / [1024, 512, 256] / bf16 | 1.720568 | 1.720568 | 1.720568 |
| index_k / [128, 128, 4096] / bf16 | 16.430545 | 16.430545 | 3.025889 |
| index_q / [128, 4096, 1536] / bf16 | 6.685417 | 6.685417 | 6.685417 |
| index_weights / [128, 32, 4096] / bf16 | 10.123636 | 10.123636 | 2.012230 |
| v_expand / [1024, 256, 512] / bf16 | 2.582466 | 2.582466 | 2.582466 |
| output / [128, 4096, 2048] / bf16 | 8.671356 | 8.671356 | 8.671356 |
| router / [128, 288, 4096] / fp32 | 19.749818 | 159.681939 | 19.749818 |
| dense_gate_up / [128, 512, 4096] / fp8_e4m3 | 8.504727 | 8.504727 | 3.154162 |
| dense_down / [128, 4096, 256] / fp8_e4m3 | 1.578000 | 1.578000 | 1.578000 |
