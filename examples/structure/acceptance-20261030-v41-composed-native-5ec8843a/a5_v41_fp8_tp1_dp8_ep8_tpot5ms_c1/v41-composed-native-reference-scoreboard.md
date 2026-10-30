# Complete native Body bucket conditional references

Runtime `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 10.636344 / 10.581500 | 2.296809 | 0.425454 / 0.091872 / -0.333581 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / MoeDistributeCombineV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 11.198396 / 11.141000 | 4.296934 | 0.447936 / 0.171877 / -0.276058 | float_combine_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / MoeDistributeDispatchV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 45.331516 / 33.640500 | 2.617145 | 1.813261 / 0.104686 / -1.708575 | MX32_dispatch_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 10.536788 / 10.441500 | 2.296809 | 0.421472 / 0.091872 / -0.329599 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 23.639004 / 23.542500 | 13.415820 | 0.945560 / 0.536633 / -0.408927 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 38.591890 / 38.458000 | 26.983465 | 1.543676 / 1.079339 / -0.464337 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 18.923557 / 18.895000 | 8.664508 | 0.756942 / 0.346580 / -0.410362 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / MqsmlaKernel___call__ / layers 0,1 | 2.000 | 8.169980 / 8.110000 | 6.510667 | 0.016340 / 0.013021 / -0.003319 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / MqsmlaKernel___call__ / layers 20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 20.000 | 10.066866 / 10.133500 | 20.016727 | 0.201337 / 0.400335 / +0.198997 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / MqsmlaKernel___call__ / layers 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19 | 18.000 | 9.205144 / 9.201500 | 20.016727 | 0.165693 / 0.360301 / +0.194608 | retained_source_symbol_to_explicit_full_batch_mqsmla |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
