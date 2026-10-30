# Complete native Body bucket conditional references

Runtime `30dcea1e335778b3d6c6f9ba67cce3e84a5adbba`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_glm53flash_tp8_c16_p8k / GroupedMatmulSwigluQuantV2 / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 31.000 | 205.998794 / 205.726500 | 163.550332 | 6.385963 / 5.070060 / -1.315902 | FP8_MX_expert_gate_up_activation_quant_source_fused_reference |
| a5_glm53flash_tp8_c16_p8k / GroupedMatmulSwigluQuantV2 / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 206.404088 / 206.335500 | 163.550332 | 2.270445 / 1.799054 / -0.471391 | FP8_MX_expert_gate_up_activation_quant_source_fused_reference |
| a5_glm53flash_tp8_c16_p8k / SparseFlashMla / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 86.857787 / 86.709500 | 147.587072 | 0.955436 / 1.623458 / +0.668022 | whole_batch_indexed_attention_reference |
| a5_glm53flash_tp8_c16_p8k / RecurrentKda / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 34.000 | 25.508517 / 25.294000 | 13.748154 | 0.867290 / 0.467437 / -0.399852 | whole_batch_symbolic_accepted_state_source_reference |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
