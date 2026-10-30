# Complete native Body bucket conditional references

Runtime `30dcea1e335778b3d6c6f9ba67cce3e84a5adbba`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 18.923557 / 18.895000 | 8.410556 | 0.756942 / 0.336422 / -0.420520 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / KvCompressEpilogV2 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 3.145907 / 2.630000 | 1.312000 | 0.125836 / 0.052480 / -0.073356 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 5.311230 / 5.198000 | 1.312000 | 0.212449 / 0.052480 / -0.159969 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 4.765409 / 4.716000 | 1.312000 | 0.190616 / 0.052480 / -0.138136 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 2.651662 / 2.506000 | 1.312000 | 0.106066 / 0.052480 / -0.053586 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / KvCompressEpilogV2 / layers 2,8,14 | 3.000 | 2.701311 / 2.653000 | 0.000000 | 0.008104 / 0.000000 / -0.008104 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / InplacePartialRotaryMul / layers 2,8,14,20,24,28,32,36 | 8.000 | 2.860778 / 2.855000 | 1.312000 | 0.022886 / 0.010496 / -0.012390 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / KvCompressEpilogV2 / layers 20 | 1.000 | 2.654888 / 2.592000 | 1.312000 | 0.002655 / 0.001312 / -0.001343 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 2.358669 / 2.343500 | 0.000000 | 0.007076 / 0.000000 / -0.007076 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 2.156897 / 2.055000 | 0.000000 | 0.006471 / 0.000000 / -0.006471 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / InplacePartialRotaryMul / layers 20 | 1.000 | 2.079125 / 2.064500 | 1.312000 | 0.002079 / 0.001312 / -0.000767 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / InplacePartialRotaryMul / layers 20 | 1.000 | 2.074105 / 2.059000 | 1.312000 | 0.002074 / 0.001312 / -0.000762 | source_role_conditional_existing_semantic_program |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
