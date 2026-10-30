# Complete native Body bucket conditional references

Runtime `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 12.177582 / 12.002500 | 2.403430 | 0.487103 / 0.096137 / -0.390966 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / MoeDistributeCombineV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 15.402066 / 15.216500 | 6.948567 | 0.616083 / 0.277943 / -0.338140 | float_combine_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / MoeDistributeDispatchV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 21.045282 / 19.659000 | 4.591666 | 0.841811 / 0.183667 / -0.658145 | MX32_dispatch_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 12.209314 / 11.944000 | 2.403430 | 0.488373 / 0.096137 / -0.392235 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 250.140776 / 248.818000 | 216.599901 | 10.005631 / 8.663996 / -1.341635 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 123.273158 / 122.228000 | 107.420765 | 4.930926 / 4.296831 / -0.634096 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 21.093003 / 21.082500 | 8.881490 | 0.843720 / 0.355260 / -0.488461 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / MqsmlaKernel___call__ / layers 20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 20.000 | 35.488209 / 35.584000 | 20.140057 | 0.709764 / 0.402801 / -0.306963 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / MqsmlaKernel___call__ / layers 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19 | 18.000 | 34.016027 / 33.648000 | 20.140057 | 0.612288 / 0.362521 / -0.249767 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / MqsmlaKernel___call__ / layers 0,1 | 2.000 | 19.397301 / 12.614000 | 6.633997 | 0.038795 / 0.013268 / -0.025527 | retained_source_symbol_to_explicit_full_batch_mqsmla |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
