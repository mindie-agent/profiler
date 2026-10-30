# Complete native Body bucket conditional references

Runtime `30dcea1e335778b3d6c6f9ba67cce3e84a5adbba`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 21.093003 / 21.082500 | 8.638236 | 0.843720 / 0.345529 / -0.498191 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 6.679812 / 6.330000 | 1.312000 | 0.267192 / 0.052480 / -0.214712 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / KvCompressEpilogV2 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 6.378764 / 6.304000 | 1.312000 | 0.255151 / 0.052480 / -0.202671 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 5.583497 / 5.466000 | 1.312000 | 0.223340 / 0.052480 / -0.170860 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / InplacePartialRotaryMul / layers 2,8,14,20,24,28,32,36 | 8.000 | 4.736997 / 4.698500 | 1.312000 | 0.037896 / 0.010496 / -0.027400 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 3.536547 / 3.330500 | 1.312000 | 0.141462 / 0.052480 / -0.088982 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / KvCompressEpilogV2 / layers 2,8,14 | 3.000 | 3.535046 / 3.529000 | 0.000000 | 0.010605 / 0.000000 / -0.010605 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / KvCompressEpilogV2 / layers 20 | 1.000 | 3.548274 / 3.509000 | 1.312000 | 0.003548 / 0.001312 / -0.002236 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 3.106740 / 3.102000 | 0.000000 | 0.009320 / 0.000000 / -0.009320 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 2.752648 / 2.713000 | 0.000000 | 0.008258 / 0.000000 / -0.008258 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / InplacePartialRotaryMul / layers 20 | 1.000 | 2.720671 / 2.706000 | 1.312000 | 0.002721 / 0.001312 / -0.001409 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / InplacePartialRotaryMul / layers 20 | 1.000 | 2.676973 / 2.675000 | 1.312000 | 0.002677 / 0.001312 / -0.001365 | source_role_conditional_existing_semantic_program |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
