# Complete native Body bucket conditional references

Runtime `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 10.635869 / 10.586000 | 2.296809 | 0.425435 / 0.091872 / -0.333562 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / MoeDistributeCombineV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 11.208854 / 11.140500 | 4.296934 | 0.448354 / 0.171877 / -0.276477 | float_combine_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / MoeDistributeDispatchV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 29.449466 / 16.841500 | 2.617145 | 1.177979 / 0.104686 / -1.073293 | MX32_dispatch_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 10.537539 / 10.437500 | 2.296809 | 0.421502 / 0.091872 / -0.329629 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 23.656089 / 23.572000 | 13.415820 | 0.946244 / 0.536633 / -0.409611 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 38.541206 / 38.378000 | 26.983465 | 1.541648 / 1.079339 / -0.462310 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 18.966882 / 18.925000 | 8.664508 | 0.758675 / 0.346580 / -0.412095 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / MqsmlaKernel___call__ / layers 0,1 | 2.000 | 11.092469 / 11.153000 | 6.510667 | 0.022185 / 0.013021 / -0.009164 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / MqsmlaKernel___call__ / layers 20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 20.000 | 29.224306 / 29.082500 | 20.016727 | 0.584486 / 0.400335 / -0.184152 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 / MqsmlaKernel___call__ / layers 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19 | 18.000 | 29.070478 / 28.659000 | 20.016727 | 0.523269 / 0.360301 / -0.162968 | retained_source_symbol_to_explicit_full_batch_mqsmla |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
