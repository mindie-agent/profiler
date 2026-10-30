# Complete native Body bucket conditional references

Runtime `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / MoeDistributeDispatchV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 18.548100 / 17.867000 | 2.865154 | 0.741924 / 0.114606 / -0.627318 | MX32_dispatch_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 11.294489 / 11.106500 | 2.298684 | 0.451780 / 0.091947 / -0.359832 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / MoeDistributeCombineV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 12.381461 / 12.229500 | 4.922582 | 0.495258 / 0.196903 / -0.298355 | float_combine_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 11.182508 / 11.022000 | 2.298684 | 0.447300 / 0.091947 / -0.355353 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 65.237524 / 64.667500 | 53.650991 | 2.609501 / 2.146040 / -0.463461 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 127.405740 / 126.789000 | 107.921571 | 5.096230 / 4.316863 / -0.779367 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 20.002609 / 19.975000 | 8.705776 | 0.800104 / 0.348231 / -0.451873 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / MqsmlaKernel___call__ / layers 0,1 | 2.000 | 13.400376 / 12.342500 | 6.510667 | 0.026801 / 0.013021 / -0.013779 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / MqsmlaKernel___call__ / layers 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19 | 18.000 | 30.876444 / 30.200000 | 20.016727 | 0.555776 / 0.360301 / -0.195475 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k / MqsmlaKernel___call__ / layers 20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 20.000 | 31.372409 / 30.919500 | 20.016727 | 0.627448 / 0.400335 / -0.227114 | retained_source_symbol_to_explicit_full_batch_mqsmla |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
