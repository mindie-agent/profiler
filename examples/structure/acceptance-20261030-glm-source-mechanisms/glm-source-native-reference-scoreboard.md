# Complete native Body bucket conditional references

Runtime `18c423c7297fc3b3e92a5eb34f204df40a2a6cb6`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_glm53flash_tp8_c64_p4k / GroupedMatmulSwigluQuantV2 / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 31.000 | 211.180266 / 210.918000 | 161.024512 | 6.546588 / 4.991760 / -1.554828 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c64_p4k / SparseFlashMla / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 288.254073 / 285.492000 | 590.348288 | 3.170795 / 6.493831 / +3.323036 | whole_batch_indexed_attention_reference |
| a5_glm53flash_tp8_c64_p4k / RecurrentKda / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 34.000 | 78.338271 / 78.285000 | 103.616000 | 2.663501 / 3.522944 / +0.859443 | whole_batch_generic_gating_and_recurrent_reference |
| a5_glm53flash_tp8_c64_p4k / GroupedMatmulSwigluQuantV2 / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 210.830821 / 210.350000 | 161.024512 | 2.319139 / 1.771270 / -0.547869 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c32_p4k / GroupedMatmulSwigluQuantV2 / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 31.000 | 207.720145 / 207.499000 | 159.681024 | 6.439324 / 4.950112 / -1.489213 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c32_p4k / GroupedMatmulSwigluQuantV2 / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 208.274751 / 208.143000 | 159.681024 | 2.291022 / 1.756491 / -0.534531 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c32_p4k / SparseFlashMla / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 153.517238 / 153.209000 | 295.174144 | 1.688690 / 3.246916 / +1.558226 | whole_batch_indexed_attention_reference |
| a5_glm53flash_tp8_c32_p4k / RecurrentKda / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 34.000 | 43.986928 / 44.073000 | 53.120000 | 1.495556 / 1.806080 / +0.310524 | whole_batch_generic_gating_and_recurrent_reference |
| glm53flash-a5-tp8-c1 / GroupedMatmulSwigluQuantV2 / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 31.000 | 33.520268 / 33.438000 | 19.967488 | 1.039128 / 0.618992 / -0.420136 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| glm53flash-a5-tp8-c1 / SparseFlashMla / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 51.517269 / 51.481000 | 32.271515 | 0.566690 / 0.354987 / -0.211703 | whole_batch_indexed_attention_reference |
| glm53flash-a5-tp8-c1 / RecurrentKda / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 34.000 | 13.003602 / 12.695000 | 4.202000 | 0.442122 / 0.142868 / -0.299254 | whole_batch_generic_gating_and_recurrent_reference |
| glm53flash-a5-tp8-c1 / GroupedMatmulSwigluQuantV2 / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 33.520629 / 33.389000 | 19.967488 | 0.368727 / 0.219642 / -0.149085 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a3_glm53flash_tp16_aclgraph_c32 / KvQuantSparseFlashAttentionVllm / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 829.848284 / 829.977000 | 1298.268160 | 9.128331 / 14.280950 / +5.152619 | whole_batch_packed528_int8_analytic_reference |
| a3_glm53flash_tp16_aclgraph_c64 / KvQuantSparseFlashAttentionVllm / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 1632.353474 / 1632.673000 | 2596.536320 | 17.955888 / 28.561900 / +10.606011 | whole_batch_packed528_int8_analytic_reference |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
