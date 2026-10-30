# Complete native Body bucket conditional references

Runtime `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.
No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.

| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / MoeDistributeDispatchV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 19.943554 / 18.578500 | 3.195833 | 0.797742 / 0.127833 / -0.669909 | MX32_dispatch_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 11.659871 / 11.412500 | 2.316294 | 0.466395 / 0.092652 / -0.373743 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / MoeDistributeCombineV3 / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 19.056645 / 18.961500 | 5.526011 | 0.762266 / 0.221040 / -0.541225 | float_combine_complete_source_protocol_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / HcPre / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 11.718719 / 11.552000 | 2.316294 | 0.468749 / 0.092652 / -0.376097 | arch35_HCPre_public_three_output_source_partial_reference |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 119.854329 / 118.821000 | 107.297885 | 4.794173 / 4.291915 / -0.502258 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / GroupedMatmul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 242.599300 / 241.330500 | 215.839046 | 9.703972 / 8.633562 / -1.070410 | capacity_vs_valid_rows_conditional |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / TransposeQuantBatchMatMul / layers 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 40.000 | 20.491553 / 20.480000 | 8.760801 | 0.819662 / 0.350432 / -0.469230 | source_role_conditional_existing_semantic_program |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / MqsmlaKernel___call__ / layers 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19 | 18.000 | 33.893339 / 34.158000 | 20.016727 | 0.610080 / 0.360301 / -0.249779 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / MqsmlaKernel___call__ / layers 0,1 | 2.000 | 16.005460 / 12.506500 | 6.510667 | 0.032011 / 0.013021 / -0.018990 | retained_source_symbol_to_explicit_full_batch_mqsmla |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / MqsmlaKernel___call__ / layers 20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39 | 20.000 | 33.567316 / 32.496000 | 20.016727 | 0.671346 / 0.400335 / -0.271012 | retained_source_symbol_to_explicit_full_batch_mqsmla |

Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.
