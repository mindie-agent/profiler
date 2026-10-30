# Complete native Body bucket conditional references

Runtime `18c423c7`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| glm53flash-a5-tp8-c1 / GroupedMatmulSwigluQuantV2 / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 31.000 | 33.520268 / 33.438000 | 19.967488 | 1.039128 / 0.618992 / -0.420136 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| glm53flash-a5-tp8-c1 / SparseFlashMla / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 51.517269 / 51.481000 | 32.271515 | 0.566690 / 0.354987 / -0.211703 | whole_batch_indexed_attention_reference |
| glm53flash-a5-tp8-c1 / RecurrentKda / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 34.000 | 13.003602 / 12.695000 | 4.202000 | 0.442122 / 0.142868 / -0.299254 | whole_batch_generic_gating_and_recurrent_reference |
| glm53flash-a5-tp8-c1 / GroupedMatmulSwigluQuantV2 / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 33.520629 / 33.389000 | 19.967488 | 0.368727 / 0.219642 / -0.149085 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
