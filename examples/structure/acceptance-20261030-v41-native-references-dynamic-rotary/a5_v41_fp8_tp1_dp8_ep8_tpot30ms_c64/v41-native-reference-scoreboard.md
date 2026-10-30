# Complete native Body bucket conditional references

Runtime `5251d0d516d179d05831bd28e863d66df07e6f4f`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 20.491553 / 20.480000 | 8.506849 | 0.819662 / 0.340274 / -0.479388 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 6.454362 / 6.206000 | 1.312000 | 0.258174 / 0.052480 / -0.205694 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / KvCompressEpilogV2 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 5.737828 / 5.587500 | 1.312000 | 0.229513 / 0.052480 / -0.177033 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 5.156772 / 5.083000 | 1.312000 | 0.206271 / 0.052480 / -0.153791 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / InplacePartialRotaryMul / layers 2,8,14,20,24,28,32,36 | 8.000 | 4.583718 / 4.566000 | 1.312000 | 0.036670 / 0.010496 / -0.026174 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 3.832207 / 3.641000 | 1.312000 | 0.153288 / 0.052480 / -0.100808 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / KvCompressEpilogV2 / layers 2,8,14 | 3.000 | 3.583564 / 3.587000 | 0.000000 | 0.010751 / 0.000000 / -0.010751 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / KvCompressEpilogV2 / layers 20 | 1.000 | 3.270347 / 3.340000 | 1.312000 | 0.003270 / 0.001312 / -0.001958 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 3.009787 / 3.028000 | 0.000000 | 0.009029 / 0.000000 / -0.009029 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 2.531693 / 2.466000 | 0.000000 | 0.007595 / 0.000000 / -0.007595 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / InplacePartialRotaryMul / layers 20 | 1.000 | 2.448093 / 2.440000 | 1.312000 | 0.002448 / 0.001312 / -0.001136 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / InplacePartialRotaryMul / layers 20 | 1.000 | 2.375733 / 2.370000 | 1.312000 | 0.002376 / 0.001312 / -0.001064 | source_role_conditional_existing_semantic_program |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
