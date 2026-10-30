# Complete native Body bucket conditional references

Runtime `30dcea1e335778b3d6c6f9ba67cce3e84a5adbba`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 18.932363 / 18.897000 | 8.410556 | 0.757295 / 0.336422 / -0.420872 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / KvCompressEpilogV2 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 3.131366 / 2.598000 | 1.312000 | 0.125255 / 0.052480 / -0.072775 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 5.297281 / 5.195000 | 1.312000 | 0.211891 / 0.052480 / -0.159411 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 4.756522 / 4.707000 | 1.312000 | 0.190261 / 0.052480 / -0.137781 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / InplacePartialRotaryMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 2.622317 / 2.512000 | 1.312000 | 0.104893 / 0.052480 / -0.052413 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / InplacePartialRotaryMul / layers 2,8,14,20,24,28,32,36 | 8.000 | 2.844110 / 2.835000 | 1.312000 | 0.022753 / 0.010496 / -0.012257 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / KvCompressEpilogV2 / layers 20 | 1.000 | 2.731258 / 2.694000 | 1.312000 | 0.002731 / 0.001312 / -0.001419 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / KvCompressEpilogV2 / layers 2,8,14 | 3.000 | 2.584766 / 2.620000 | 0.000000 | 0.007754 / 0.000000 / -0.007754 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 2.228196 / 2.252000 | 0.000000 | 0.006685 / 0.000000 / -0.006685 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / InplacePartialRotaryMul / layers 2,8,14 | 3.000 | 2.263298 / 2.308000 | 0.000000 | 0.006790 / 0.000000 / -0.006790 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / InplacePartialRotaryMul / layers 20 | 1.000 | 2.346225 / 2.335000 | 1.312000 | 0.002346 / 0.001312 / -0.001034 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / InplacePartialRotaryMul / layers 20 | 1.000 | 2.332874 / 2.319000 | 1.312000 | 0.002333 / 0.001312 / -0.001021 | source_role_conditional_existing_semantic_program |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
