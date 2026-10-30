# Complete native Body bucket conditional references

Runtime `5251d0d516d179d05831bd28e863d66df07e6f4f`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 19.389470 / 19.359500 | 8.424312 | 0.775579 / 0.336972 / -0.438606 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 5.458868 / 5.383500 | 1.312000 | 0.218355 / 0.052480 / -0.165875 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / KvCompressEpilogV2 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 4.232911 / 4.040500 | 1.312000 | 0.169316 / 0.052480 / -0.116836 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 5.025616 / 4.973000 | 1.312000 | 0.201025 / 0.052480 / -0.148545 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / InplacePartialRotaryMul / layers 2,8,14,20,24,28,32,36 | 8.000 | 4.370517 / 4.362000 | 1.312000 | 0.034964 / 0.010496 / -0.024468 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 2.664417 / 2.599000 | 1.312000 | 0.106577 / 0.052480 / -0.054097 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / KvCompressEpilogV2 / layers 20 | 1.000 | 3.085775 / 3.075000 | 1.312000 | 0.003086 / 0.001312 / -0.001774 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / KvCompressEpilogV2 / layers 2,8,14 | 3.000 | 2.960140 / 2.967000 | 0.000000 | 0.008880 / 0.000000 / -0.008880 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 2.572504 / 2.499000 | 0.000000 | 0.007718 / 0.000000 / -0.007718 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 2.247630 / 2.241000 | 0.000000 | 0.006743 / 0.000000 / -0.006743 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / InplacePartialRotaryMul / layers 20 | 1.000 | 2.264426 / 2.270000 | 1.312000 | 0.002264 / 0.001312 / -0.000952 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / InplacePartialRotaryMul / layers 20 | 1.000 | 2.245922 / 2.252000 | 1.312000 | 0.002246 / 0.001312 / -0.000934 | source_role_conditional_existing_semantic_program |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
