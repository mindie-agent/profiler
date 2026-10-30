# Complete native Body bucket conditional references

Runtime `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / MoeDistributeDispatchV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 17.898152 / 17.040500 | 2.699815 | 0.715926 / 0.107993 / -0.607933 | MX32_dispatch_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / MoeDistributeCombineV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 11.810211 / 11.729000 | 4.620868 | 0.472408 / 0.184835 / -0.287574 | float_combine_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 11.735896 / 11.691000 | 2.297434 | 0.469436 / 0.091897 / -0.377538 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 11.977505 / 11.948000 | 2.297434 | 0.479100 / 0.091897 / -0.387203 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 37.438619 / 37.167000 | 26.827543 | 1.497545 / 1.073102 / -0.424443 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 68.076110 / 67.778500 | 53.962833 | 2.723044 / 2.158513 / -0.564531 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 19.389470 / 19.359500 | 8.678264 | 0.775579 / 0.347131 / -0.428448 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / MqsmlaKernel___call__ / layers 20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 20.000 | 29.623077 / 29.503500 | 20.016727 | 0.592462 / 0.400335 / -0.192127 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / MqsmlaKernel___call__ / layers 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19 | 18.000 | 29.914692 / 29.194000 | 20.016727 | 0.538464 / 0.360301 / -0.178163 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k / MqsmlaKernel___call__ / layers 0,1 | 2.000 | 11.257043 / 11.309000 | 6.510667 | 0.022514 / 0.013021 / -0.009493 | retained_source_symbol_to_explicit_full_batch_mqsmla |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
