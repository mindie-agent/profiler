# Complete Decode Body Operator Families

Only complete events inside the 65 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| glm53flash-a5-tp8-c1 / body-fixed-grid-0b822d0e | 19 / 19 | 0 / 0 | 19 / 19 | 35425 / 167960 | 0 |

## glm53flash-a5-tp8-c1 / body-fixed-grid-0b822d0e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 2730 | 0 / 2730 | 33.520 | 33.429 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 2925 | 0 / 2925 | 23.103 | 17.851 | 25.346 | 2.243 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| GroupedMatmul / expert_down | 2730 | 2730 / 0 | 22.482 | 22.473 | 9.569 | -12.913 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 2925 | 0 / 2925 | 20.753 | 18.202 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeInitRoutingV3 / unresolved | 2730 | 0 / 2730 | 20.796 | 20.692 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 2210 | 2210 / 0 | 16.983 | 16.915 | 8.288 | -8.695 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMla / unresolved | 715 | 0 / 715 | 51.517 | 51.481 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 2925 | 0 / 2925 | 11.217 | 11.078 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 2925 | 0 / 2925 | 11.033 | 10.866 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| Slice / unresolved | 14560 | 0 / 14560 | 2.151 | 1.935 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 2210 | 0 / 2210 | 13.004 | 12.695 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 5850 | 0 / 5850 | 4.571 | 3.506 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMlaMetadata / unresolved | 715 | 0 / 715 | 34.980 | 31.811 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 2730 | 2730 / 0 | 8.756 | 8.742 | 16.546 | 7.790 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.gate_up | 2730 | 2730 / 0 | 7.072 | 6.974 | 4.273 | -2.800 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 11960 | 0 / 11960 | 1.522 | 1.559 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _copy_conv_state_kernel / unresolved | 4420 | 0 / 4420 | 3.684 | 3.564 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 2210 | 0 / 2210 | 6.755 | 6.612 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 2210 | 2210 / 0 | 6.347 | 6.348 | 2.152 | -4.194 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 2730 | 2730 / 0 | 4.972 | 4.928 | 1.312 | -3.660 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / unresolved | 2145 | 0 / 2145 | 6.259 | 6.362 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cumsum / unresolved | 2730 | 0 / 2730 | 4.537 | 4.547 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 6565 | 0 / 6565 | 1.866 | 1.641 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 2925 | 2925 / 0 | 4.150 | 4.115 | 1.312 | -2.838 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeFinalizeRoutingV2 / unresolved | 2730 | 0 / 2730 | 4.432 | 4.418 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 2925 | 2925 / 0 | 4.123 | 4.091 | 1.312 | -2.811 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 2730 | 0 / 2730 | 4.213 | 4.196 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 2730 | 2730 / 0 | 4.156 | 4.133 | 1.578 | -2.578 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 5135 | 0 / 5135 | 2.079 | 2.009 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 5850 | 0 / 5850 | 1.621 | 1.633 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 2145 | 0 / 2145 | 4.420 | 4.297 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 2925 | 0 / 2925 | 3.129 | 3.018 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / router_selection | 2730 | 0 / 2730 | 3.213 | 3.193 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 715 | 0 / 715 | 12.144 | 12.159 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 2925 | 2925 / 0 | 2.718 | 2.687 | 1.312 | -1.406 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 2925 | 2925 / 0 | 2.714 | 2.694 | 1.312 | -1.402 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ViewCopy / unresolved | 2210 | 0 / 2210 | 3.514 | 3.501 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 3640 | 0 / 3640 | 2.023 | 1.993 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.down.quantize | 2730 | 2730 / 0 | 2.479 | 2.470 | 1.312 | -1.167 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / index_q | 715 | 715 / 0 | 8.899 | 8.873 | 3.176 | -5.722 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TopKV2 / unresolved | 715 | 0 / 715 | 8.805 | 8.722 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 715 | 0 / 715 | 8.432 | 8.423 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 2210 | 0 / 2210 | 2.657 | 2.630 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 1430 | 0 / 1430 | 3.989 | 3.984 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 715 | 0 / 715 | 7.612 | 7.539 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 2925 | 0 / 2925 | 1.798 | 1.750 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 2210 | 0 / 2210 | 2.257 | 2.192 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 2925 | 0 / 2925 | 1.661 | 1.641 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 715 | 715 / 0 | 5.979 | 5.961 | 1.578 | -4.401 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeBatchMatMul / q_absorb | 715 | 715 / 0 | 5.976 | 5.929 | 1.578 | -4.398 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 2925 | 0 / 2925 | 1.457 | 1.434 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 2210 | 0 / 2210 | 1.905 | 1.818 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 1430 | 0 / 1430 | 2.879 | 2.795 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 2210 | 0 / 2210 | 1.769 | 1.683 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 1430 | 0 / 1430 | 2.482 | 2.485 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 715 | 0 / 715 | 4.792 | 4.772 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 715 | 0 / 715 | 4.498 | 4.498 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 1430 | 0 / 1430 | 2.116 | 2.079 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 715 | 0 / 715 | 3.361 | 3.358 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 1430 | 0 / 1430 | 1.487 | 1.452 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 715 | 0 / 715 | 2.792 | 2.797 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 715 | 0 / 715 | 2.428 | 2.413 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 195 | 195 / 0 | 8.466 | 8.429 | 4.276 | -4.190 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 195 | 195 / 0 | 5.176 | 5.175 | 1.642 | -3.534 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 195 | 195 / 0 | 5.041 | 5.037 | 1.312 | -3.729 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 195 | 195 / 0 | 3.820 | 3.825 | 1.312 | -2.508 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
