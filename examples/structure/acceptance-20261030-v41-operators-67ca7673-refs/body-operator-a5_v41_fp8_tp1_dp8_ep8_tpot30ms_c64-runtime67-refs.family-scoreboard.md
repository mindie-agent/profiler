# Complete Decode Body Operator Families

Only complete events inside the 75 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs | 18 / 18 | 0 / 0 | 18 / 18 | 44025 / 130725 | 0 |

## a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / expert_up | 3000 | 0 / 3000 | 242.599 | 241.331 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 3000 | 0 / 3000 | 119.854 | 118.821 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MqsmlaKernel___call__ / attention_core | 3000 | 0 / 3000 | 32.836 | 33.035 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| QuantBatchMatmulV3 / grouped_output_b | 3000 | 3000 / 0 | 20.692 | 20.686 | 16.528 | -4.165 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeQuantBatchMatMul / unresolved | 3000 | 0 / 3000 | 20.492 | 20.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / expert_dispatch_native | 3000 | 0 / 3000 | 19.944 | 18.578 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / expert_combine_native | 3000 | 0 / 3000 | 19.057 | 18.962 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| InplacePartialRotaryMul / unresolved | 10200 | 0 / 10200 | 4.969 | 4.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_b | 3000 | 3000 / 0 | 16.742 | 16.628 | 10.697 | -6.046 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / unresolved | 3750 | 0 / 3750 | 10.821 | 10.698 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 3000 | 3000 / 0 | 12.082 | 12.063 | 10.370 | -1.712 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPre / attention.hc_pre | 3000 | 0 / 3000 | 11.719 | 11.552 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| HcPre / ffn.hc_pre | 3000 | 0 / 3000 | 11.660 | 11.412 | — | — | 15 us (unmodeled) | 0 / 0 | source_reference / reference_only |
| SwigluGroupQuant / unresolved | 6000 | 0 / 6000 | 4.221 | 4.134 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 3000 | 3000 / 0 | 7.307 | 7.261 | 4.730 | -2.578 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 6450 | 0 / 6450 | 2.999 | 2.985 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvCompressEpilogV2 / unresolved | 3300 | 0 / 3300 | 5.535 | 5.452 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / q_a | 3000 | 3000 / 0 | 6.024 | 5.988 | 2.837 | -3.187 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 3150 | 0 / 3150 | 4.802 | 4.764 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopKHash / unresolved | 3000 | 0 / 3000 | 5.001 | 5.064 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / kv_a | 3000 | 3000 / 0 | 4.999 | 4.982 | 1.578 | -3.421 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 3000 | 0 / 3000 | 4.915 | 4.913 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 3000 | 3000 / 0 | 4.822 | 4.806 | 1.312 | -3.510 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_b.quantize | 3600 | 3600 / 0 | 4.014 | 4.001 | 1.312 | -2.702 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / attention.hc_post_group | 3000 | 3000 / 0 | 4.627 | 4.592 | 1.312 | -3.315 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 6825 | 0 / 6825 | 1.984 | 2.053 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / grouped_output_b.quantize | 3000 | 3000 / 0 | 4.074 | 4.069 | 1.312 | -2.762 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 3000 | 3000 / 0 | 4.050 | 4.026 | 1.312 | -2.738 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / q_a.quantize | 3000 | 3000 / 0 | 3.822 | 3.805 | 1.312 | -2.510 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 3000 | 3000 / 0 | 3.318 | 3.290 | 1.312 | -2.006 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 3000 | 3000 / 0 | 3.250 | 3.247 | 1.312 | -1.938 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _quantize_mxfp4_indexer_kernel / unresolved | 600 | 0 / 600 | 16.150 | 15.082 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 150 | 0 / 150 | 59.867 | 59.847 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _Z15metadata_kernel4Args_interface / unresolved | 450 | 0 / 450 | 18.983 | 19.549 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 3000 | 0 / 3000 | 2.410 | 2.400 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_weights | 600 | 600 / 0 | 11.876 | 11.782 | 1.879 | -9.997 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Equal / unresolved | 3150 | 0 / 3150 | 2.083 | 1.960 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantSparseLightningIndexer / unresolved | 300 | 0 / 300 | 18.595 | 18.593 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Neg / unresolved | 3000 | 0 / 3000 | 1.734 | 1.623 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 3000 | 0 / 3000 | 1.542 | 1.460 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantLightningIndexer / unresolved | 300 | 0 / 300 | 13.395 | 11.555 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_indexer_indices_kernel / unresolved | 600 | 0 / 600 | 5.988 | 5.968 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / index_q | 600 | 600 / 0 | 5.346 | 5.295 | 1.578 | -3.768 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _engram_host_uva_gather_dequant_kernel / unresolved | 150 | 0 / 150 | 13.464 | 13.014 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 600 | 0 / 600 | 2.790 | 2.758 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_mxfp4_indexer_cache_kernel / unresolved | 300 | 0 / 300 | 5.047 | 5.024 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _hash_ids_kernel / unresolved | 75 | 0 / 75 | 20.107 | 20.044 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pool_kernel / unresolved | 225 | 0 / 225 | 4.734 | 4.717 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / compress_norm | 150 | 150 / 0 | 6.527 | 6.301 | 1.312 | -5.215 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _engram_gate_kernel / unresolved | 150 | 0 / 150 | 6.165 | 6.166 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _cache_update_kernel / unresolved | 225 | 0 / 225 | 3.406 | 3.392 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalOr / unresolved | 150 | 0 / 150 | 4.999 | 4.405 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / compress_gates + compress_values | 75 | 75 / 0 | 8.637 | 8.675 | 1.881 | -6.756 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 225 | 0 / 225 | 2.832 | 2.814 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 150 | 0 / 150 | 3.728 | 3.828 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _engram_req_index_kernel / unresolved | 75 | 0 / 75 | 5.797 | 5.720 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _fold_indexer_rows / unresolved | 75 | 0 / 75 | 2.606 | 2.575 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 75 | 0 / 75 | 2.098 | 2.070 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| HcPre / attention.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 3000 | 11.719 / 11.552 | 21.524 | 0.469 | 0.861 | partial_base_program_reference_premix_branch_unresolved |
| HcPre / ffn.hc_pre / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 3000 | 11.660 / 11.412 | 21.524 | 0.466 | 0.861 | partial_base_program_reference_premix_branch_unresolved |
| MqsmlaKernel___call__ / attention_core / layers 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 1350 | 33.893 / 34.158 | 12.624 | 0.610 | 0.227 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 0, 1 | 150 | 16.005 / 12.507 | 12.624 | 0.032 | 0.025 | source_symbol_to_declared_attention_program |
| MqsmlaKernel___call__ / attention_core / layers 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 1500 | 33.567 / 32.496 | 12.624 | 0.671 | 0.252 | source_symbol_to_declared_attention_program |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / GroupedMatmul / expert_down | 3000 | 0 | 0 | 3000 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / GroupedMatmul / expert_up | 3000 | 0 | 0 | 3000 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / HcPre / attention.hc_pre | 3000 | 0 | 3000 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / HcPre / ffn.hc_pre | 3000 | 0 | 3000 | 0 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / MoeDistributeCombineV3 / expert_combine_native | 3000 | 0 | 0 | 3000 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / MoeDistributeDispatchV3 / expert_dispatch_native | 3000 | 0 | 0 | 3000 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / runtime67-refs / MqsmlaKernel___call__ / attention_core | 3000 | 0 | 3000 | 0 | 0 |
