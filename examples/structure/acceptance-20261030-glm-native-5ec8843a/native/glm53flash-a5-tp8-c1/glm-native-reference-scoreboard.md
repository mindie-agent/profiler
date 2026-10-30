# Complete native Body bucket conditional references

Runtime `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| glm53flash-a5-tp8-c1 / GroupedMatmulSwigluQuantV2 / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 31.000 | 33.520268 / 33.438000 | 18.155890 | 1.039128 / 0.562833 / -0.476296 | FP8_MX_expert_gate_up_activation_quant_source_fused_reference |
| glm53flash-a5-tp8-c1 / SparseFlashMla / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 51.517269 / 51.481000 | 32.271515 | 0.566690 / 0.354987 / -0.211703 | whole_batch_indexed_attention_reference |
| glm53flash-a5-tp8-c1 / RecurrentKda / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 34.000 | 13.003602 / 12.695000 | 6.101150 | 0.442122 / 0.207439 / -0.234683 | whole_batch_symbolic_accepted_state_source_reference |
| glm53flash-a5-tp8-c1 / GroupedMatmulSwigluQuantV2 / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 33.520629 / 33.389000 | 18.155890 | 0.368727 / 0.199715 / -0.169012 | FP8_MX_expert_gate_up_activation_quant_source_fused_reference |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
