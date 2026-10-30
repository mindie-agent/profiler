# Complete native Body bucket conditional references

Runtime `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_glm53flash_tp8_c32_p4k / GroupedMatmulSwigluQuantV2 / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 31.000 | 207.720145 / 207.499000 | 165.203383 | 6.439324 / 5.121305 / -1.318020 | FP8_MX_expert_gate_up_activation_quant_source_fused_reference |
| a5_glm53flash_tp8_c32_p4k / GroupedMatmulSwigluQuantV2 / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 208.274751 / 208.143000 | 165.203383 | 2.291022 / 1.817237 / -0.473785 | FP8_MX_expert_gate_up_activation_quant_source_fused_reference |
| a5_glm53flash_tp8_c32_p4k / SparseFlashMla / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 153.517238 / 153.209000 | 295.174144 | 1.688690 / 3.246916 / +1.558226 | whole_batch_indexed_attention_reference |
| a5_glm53flash_tp8_c32_p4k / RecurrentKda / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 34.000 | 43.986928 / 44.073000 | 27.496309 | 1.495556 / 0.934874 / -0.560681 | whole_batch_symbolic_accepted_state_source_reference |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
