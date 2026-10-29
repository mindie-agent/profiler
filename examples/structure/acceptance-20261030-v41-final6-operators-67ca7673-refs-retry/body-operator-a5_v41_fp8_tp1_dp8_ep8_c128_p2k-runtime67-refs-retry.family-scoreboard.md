# Complete Decode Body Operator Families

Only complete events inside the 73 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs-retry | 18 / 18 | 0 / 0 | 18 / 18 | 42851 / 127446 | 0 |

## a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs-retry

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 2920 | 0 / 2920 | 250.141 | 248.818 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 2920 | 0 / 2920 | 123.273 | 122.228 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 2920 | 0 / 2920 | 34.021 | 34.734 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| QuantBatchMatmulV3 / grouped_output_b | 2920 | 2920 / 0 | 21.429 | 21.417 | 17.075 | -4.354 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 2920 | 0 / 2920 | 21.093 | 21.082 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 2920 | 0 / 2920 | 21.045 | 19.659 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| InplacePartialRotaryMul / unresolved | 9928 | 0 / 9928 | 5.095 | 5.294 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 2920 | 2920 / 0 | 16.909 | 16.807 | 11.131 | -5.777 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeDistributeCombineV3 / expert_combine_native | 2920 | 0 / 2920 | 15.402 | 15.216 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 3650 | 0 / 3650 | 11.519 | 11.223 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 2920 | 2920 / 0 | 12.334 | 12.320 | 10.723 | -1.611 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPre / ffn.hc_pre | 2920 | 0 / 2920 | 12.209 | 11.944 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| HcPre / attention.hc_pre | 2920 | 0 / 2920 | 12.178 | 12.002 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| SwigluGroupQuant / unresolved | 5840 | 0 / 5840 | 4.496 | 4.456 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 6278 | 0 / 6278 | 3.870 | 3.873 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 2920 | 2920 / 0 | 7.481 | 7.428 | 4.909 | -2.573 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| KvCompressEpilogV2 / unresolved | 3212 | 0 / 3212 | 6.121 | 6.165 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_a | 2920 | 2920 / 0 | 6.173 | 6.147 | 3.169 | -3.003 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 2920 | 0 / 2920 | 5.857 | 5.822 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopKHash / unresolved | 2920 | 0 / 2920 | 5.433 | 5.492 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 6644 | 0 / 6644 | 2.374 | 2.091 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 3066 | 0 / 3066 | 4.962 | 4.923 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 2920 | 2920 / 0 | 5.096 | 5.073 | 1.578 | -3.518 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 2920 | 2920 / 0 | 5.033 | 5.016 | 1.312 | -3.721 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / attention.hc_post_group | 2920 | 2920 / 0 | 4.907 | 4.881 | 1.312 | -3.595 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 2920 | 2920 / 0 | 4.889 | 4.887 | 1.312 | -3.577 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_a.quantize | 2920 | 2920 / 0 | 4.634 | 4.589 | 1.312 | -3.322 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_b.quantize | 3504 | 3504 / 0 | 3.783 | 3.743 | 1.312 | -2.471 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 2920 | 2920 / 0 | 4.176 | 4.177 | 1.312 | -2.864 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _quantize_mxfp4_indexer_kernel / unresolved | 584 | 0 / 584 | 20.764 | 19.503 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / grouped_output_b.quantize | 2920 | 2920 / 0 | 4.120 | 4.109 | 1.312 | -2.808 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 2920 | 2920 / 0 | 4.104 | 4.080 | 1.312 | -2.792 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _Z15metadata_kernel4Args_interface / unresolved | 434 | 0 / 434 | 21.331 | 20.197 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 146 | 0 / 146 | 60.575 | 60.566 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 2920 | 0 / 2920 | 2.769 | 2.948 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_weights | 584 | 584 / 0 | 12.241 | 12.175 | 2.508 | -9.734 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Equal / unresolved | 3066 | 0 / 3066 | 2.218 | 2.179 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Neg / unresolved | 2920 | 0 / 2920 | 2.010 | 1.931 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantSparseLightningIndexer / unresolved | 292 | 0 / 292 | 18.026 | 17.915 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 2920 | 0 / 2920 | 1.685 | 1.747 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantLightningIndexer / unresolved | 292 | 0 / 292 | 13.967 | 12.334 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_indexer_indices_kernel / unresolved | 584 | 0 / 584 | 6.707 | 6.684 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_host_uva_gather_dequant_kernel / unresolved | 146 | 0 / 146 | 25.685 | 26.114 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 584 | 584 / 0 | 5.483 | 5.431 | 1.578 | -3.905 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 584 | 0 / 584 | 2.903 | 2.863 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_mxfp4_indexer_cache_kernel / unresolved | 292 | 0 / 292 | 5.348 | 5.354 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _hash_ids_kernel / unresolved | 73 | 0 / 73 | 20.806 | 20.609 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 146 | 146 / 0 | 9.554 | 9.336 | 1.312 | -8.242 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _pool_kernel / unresolved | 219 | 0 / 219 | 5.167 | 5.145 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_gate_kernel / unresolved | 146 | 0 / 146 | 7.197 | 7.157 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _cache_update_kernel / unresolved | 219 | 0 / 219 | 3.571 | 3.558 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 64 | 0 / 64 | 10.545 | 10.419 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / compress_gates + compress_values | 73 | 73 / 0 | 8.741 | 8.752 | 2.511 | -6.230 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 219 | 0 / 219 | 2.733 | 2.719 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 146 | 0 / 146 | 3.931 | 3.896 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 73 | 0 / 73 | 6.516 | 6.436 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 146 | 0 / 146 | 3.145 | 2.908 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalOr / unresolved | 146 | 0 / 146 | 1.902 | 1.539 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 73 | 0 / 73 | 2.637 | 2.603 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 73 | 0 / 73 | 2.153 | 2.085 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 2920 | 12.178 / 12.002 | 26.538 | 0.487 | 1.062 | partial_base_program_reference_premix_branch_unresolved |
| HcPre / ffn.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 2920 | 12.209 / 11.944 | 26.538 | 0.488 | 1.062 | partial_base_program_reference_premix_branch_unresolved |
| MqsmlaKernel___call__ / attention_core / layers 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 1460 | 35.488 / 35.584 | 25.248 | 0.710 | 0.505 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1314 | 34.016 / 33.648 | 25.248 | 0.612 | 0.454 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 0, 1 | 146 | 19.397 / 12.614 | 25.248 | 0.039 | 0.050 | source_symbol_to_declared_attention_program |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs-retry / GroupedMatmul / expert_down | 2920 | 0 | 0 | 2920 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs-retry / GroupedMatmul / expert_up | 2920 | 0 | 0 | 2920 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs-retry / HcPre / attention.hc_pre | 2920 | 0 | 2920 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs-retry / HcPre / ffn.hc_pre | 2920 | 0 | 2920 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs-retry / MoeDistributeCombineV3 / expert_combine_native | 2920 | 0 | 0 | 2920 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs-retry / MoeDistributeDispatchV3 / expert_dispatch_native | 2920 | 0 | 0 | 2920 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k / runtime67-refs-retry / MqsmlaKernel___call__ / attention_core | 2920 | 0 | 2920 | 0 | 0 |
