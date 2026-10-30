# Complete native Body bucket conditional references

Runtime `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 10.686879 / 10.632500 | 2.296809 | 0.427475 / 0.091872 / -0.335603 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / MoeDistributeCombineV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 11.253534 / 11.174500 | 4.296934 | 0.450141 / 0.171877 / -0.278264 | float_combine_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / MoeDistributeDispatchV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 47.766450 / 35.269500 | 2.617145 | 1.910658 / 0.104686 / -1.805972 | MX32_dispatch_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 10.593415 / 10.482000 | 2.296809 | 0.423737 / 0.091872 / -0.331864 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 23.603552 / 23.476000 | 13.415820 | 0.944142 / 0.536633 / -0.407509 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 38.808787 / 38.660500 | 26.983465 | 1.552351 / 1.079339 / -0.473013 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 18.932363 / 18.897000 | 8.664508 | 0.757295 / 0.346580 / -0.410714 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / MqsmlaKernel___call__ / layers 0,1 | 2.000 | 7.890894 / 7.845000 | 6.510667 | 0.015782 / 0.013021 / -0.002760 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / MqsmlaKernel___call__ / layers 20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 20.000 | 9.937711 / 9.948000 | 20.016727 | 0.198754 / 0.400335 / +0.201580 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k / MqsmlaKernel___call__ / layers 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19 | 18.000 | 9.116251 / 9.153000 | 20.016727 | 0.164093 / 0.360301 / +0.196209 | retained_source_symbol_to_explicit_full_batch_mqsmla |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
