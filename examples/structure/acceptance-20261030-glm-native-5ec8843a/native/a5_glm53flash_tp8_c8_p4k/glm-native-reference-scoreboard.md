# Complete native Body bucket conditional references

Runtime `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_glm53flash_tp8_c8_p4k / GroupedMatmulSwigluQuantV2 / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 31.000 | 184.394300 / 183.975500 | 144.860048 | 5.716223 / 4.490661 / -1.225562 | FP8_MX_expert_gate_up_activation_quant_source_fused_reference |
| a5_glm53flash_tp8_c8_p4k / GroupedMatmulSwigluQuantV2 / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 185.149567 / 184.762500 | 144.860048 | 2.036645 / 1.593461 / -0.443185 | FP8_MX_expert_gate_up_activation_quant_source_fused_reference |
| a5_glm53flash_tp8_c8_p4k / SparseFlashMla / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 53.600127 / 53.585500 | 73.793536 | 0.589601 / 0.811729 / +0.222127 | whole_batch_indexed_attention_reference |
| a5_glm53flash_tp8_c8_p4k / RecurrentKda / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 34.000 | 16.454747 / 16.289000 | 6.874077 | 0.559461 / 0.233719 / -0.325743 | whole_batch_symbolic_accepted_state_source_reference |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
