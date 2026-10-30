# Complete native Body bucket conditional references

Runtime `5251d0d516d179d05831bd28e863d66df07e6f4f`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 18.966882 / 18.925000 | 8.410556 | 0.758675 / 0.336422 / -0.422253 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / KvCompressEpilogV2 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 4.510856 / 3.953500 | 1.312000 | 0.180434 / 0.052480 / -0.127954 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 5.303014 / 5.196000 | 1.312000 | 0.212121 / 0.052480 / -0.159641 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 4.772552 / 4.725000 | 1.312000 | 0.190902 / 0.052480 / -0.138422 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 2.687406 / 2.515000 | 1.312000 | 0.107496 / 0.052480 / -0.055016 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / KvCompressEpilogV2 / layers 2,8,14 | 3.000 | 2.967979 / 3.017000 | 0.000000 | 0.008904 / 0.000000 / -0.008904 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / KvCompressEpilogV2 / layers 20 | 1.000 | 3.171172 / 3.140000 | 1.312000 | 0.003171 / 0.001312 / -0.001859 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / InplacePartialRotaryMul / layers 2,8,14,20,24,28,32,36 | 8.000 | 2.858506 / 2.851000 | 1.312000 | 0.022868 / 0.010496 / -0.012372 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 2.359929 / 2.339000 | 0.000000 | 0.007080 / 0.000000 / -0.007080 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 2.146584 / 2.051000 | 0.000000 | 0.006440 / 0.000000 / -0.006440 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / InplacePartialRotaryMul / layers 20 | 1.000 | 2.075690 / 2.058000 | 1.312000 | 0.002076 / 0.001312 / -0.000764 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / InplacePartialRotaryMul / layers 20 | 1.000 | 2.065648 / 2.050000 | 1.312000 | 0.002066 / 0.001312 / -0.000754 | source_role_conditional_existing_semantic_program |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
