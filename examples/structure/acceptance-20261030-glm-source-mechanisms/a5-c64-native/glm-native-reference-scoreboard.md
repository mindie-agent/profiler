# Complete native Body bucket conditional references

Runtime `18c423c7`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_glm53flash_tp8_c64_p4k / GroupedMatmulSwigluQuantV2 / layers 4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 31.000 | 211.180266 / 210.918000 | 161.024512 | 6.546588 / 4.991760 / -1.554828 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |
| a5_glm53flash_tp8_c64_p4k / SparseFlashMla / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 288.254073 / 285.492000 | 590.348288 | 3.170795 / 6.493831 / +3.323036 | whole_batch_indexed_attention_reference |
| a5_glm53flash_tp8_c64_p4k / RecurrentKda / layers 0,1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,28,29,30,32,33,34,36,37,38,40,41,42,44 | 34.000 | 78.338271 / 78.285000 | 103.616000 | 2.663501 / 3.522944 / +0.859443 | whole_batch_generic_gating_and_recurrent_reference |
| a5_glm53flash_tp8_c64_p4k / GroupedMatmulSwigluQuantV2 / layers 3,7,11,15,19,23,27,31,35,39,43 | 11.000 | 210.830821 / 210.350000 | 161.024512 | 2.319139 / 1.771270 / -0.547869 | FP8_MX_expert_gate_up_activation_quant_decomposed_reference |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
