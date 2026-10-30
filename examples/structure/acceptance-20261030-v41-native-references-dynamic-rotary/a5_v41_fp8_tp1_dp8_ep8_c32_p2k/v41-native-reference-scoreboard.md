# Complete native Body bucket conditional references

Runtime `5251d0d516d179d05831bd28e863d66df07e6f4f`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 20.002609 / 19.975000 | 8.451824 | 0.800104 / 0.338073 / -0.462031 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / KvCompressEpilogV2 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 4.702509 / 4.570000 | 1.312000 | 0.188100 / 0.052480 / -0.135620 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 5.615884 / 5.551500 | 1.312000 | 0.224635 / 0.052480 / -0.172155 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 5.043096 / 4.974000 | 1.312000 | 0.201724 / 0.052480 / -0.149244 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / InplacePartialRotaryMul / layers 2,8,14,20,24,28,32,36 | 8.000 | 4.405985 / 4.405000 | 1.312000 | 0.035248 / 0.010496 / -0.024752 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 2.820908 / 2.727000 | 1.312000 | 0.112836 / 0.052480 / -0.060356 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / KvCompressEpilogV2 / layers 2,8,14 | 3.000 | 2.962956 / 2.970000 | 0.000000 | 0.008889 / 0.000000 / -0.008889 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / KvCompressEpilogV2 / layers 20 | 1.000 | 3.084219 / 3.048000 | 1.312000 | 0.003084 / 0.001312 / -0.001772 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 2.457790 / 2.374000 | 0.000000 | 0.007373 / 0.000000 / -0.007373 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 2.339371 / 2.335000 | 0.000000 | 0.007018 / 0.000000 / -0.007018 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / InplacePartialRotaryMul / layers 20 | 1.000 | 2.319733 / 2.318000 | 1.312000 | 0.002320 / 0.001312 / -0.001008 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / InplacePartialRotaryMul / layers 20 | 1.000 | 2.304400 / 2.284000 | 1.312000 | 0.002304 / 0.001312 / -0.000992 | source_role_conditional_existing_semantic_program |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
