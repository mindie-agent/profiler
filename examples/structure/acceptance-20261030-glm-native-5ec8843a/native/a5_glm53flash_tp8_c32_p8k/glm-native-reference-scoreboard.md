# Complete native Body bucket conditional references

Runtime `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_glm53flash_tp8_c32_p8k / GroupedMatmulSwigluQuantV2 / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 31.000 | 207.698392 / 207.331000 | 165.203383 | 6.438650 / 5.121305 / -1.317345 | FP8_MX_expert_gate_up_activation_quant_source_fused_reference |
| a5_glm53flash_tp8_c32_p8k / GroupedMatmulSwigluQuantV2 / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 208.271990 / 207.963000 | 165.203383 | 2.290992 / 1.817237 / -0.473755 | FP8_MX_expert_gate_up_activation_quant_source_fused_reference |
| a5_glm53flash_tp8_c32_p8k / SparseFlashMla / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 153.329047 / 153.215000 | 295.174144 | 1.686620 / 3.246916 / +1.560296 | whole_batch_indexed_attention_reference |
| a5_glm53flash_tp8_c32_p8k / RecurrentKda / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 34.000 | 44.024733 / 44.062500 | 27.496309 | 1.496841 / 0.934874 / -0.561966 | whole_batch_symbolic_accepted_state_source_reference |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
