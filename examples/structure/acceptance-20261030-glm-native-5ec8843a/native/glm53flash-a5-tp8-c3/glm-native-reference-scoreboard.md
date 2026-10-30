# Complete native Body bucket conditional references

Runtime `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| glm53flash-a5-tp8-c3 / GroupedMatmulSwigluQuantV2 / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 31.000 | 98.658061 / 98.458000 | 72.457672 | 3.058400 / 2.246188 / -0.812212 | FP8_MX_expert_gate_up_activation_quant_source_fused_reference |
| glm53flash-a5-tp8-c3 / GroupedMatmulSwigluQuantV2 / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 98.925573 / 98.791000 | 72.457672 | 1.088181 / 0.797034 / -0.291147 | FP8_MX_expert_gate_up_activation_quant_source_fused_reference |
| glm53flash-a5-tp8-c3 / SparseFlashMla / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 52.103756 / 52.102000 | 36.896768 | 0.573141 / 0.405864 / -0.167277 | whole_batch_indexed_attention_reference |
| glm53flash-a5-tp8-c3 / RecurrentKda / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 34.000 | 14.052676 / 13.812500 | 6.315970 | 0.477791 / 0.214743 / -0.263048 | whole_batch_symbolic_accepted_state_source_reference |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
