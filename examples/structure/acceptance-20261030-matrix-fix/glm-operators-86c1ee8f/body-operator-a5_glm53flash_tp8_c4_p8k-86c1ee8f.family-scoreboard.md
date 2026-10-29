# Complete Decode Body Operator Families

Only complete events inside the 11 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_glm53flash_tp8_c4_p8k / 86c1ee8f | 18 / 18 | 0 / 1 | 18 / 19 | 5995 / 28424 | 0 |

## a5_glm53flash_tp8_c4_p8k / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 462 | 0 / 462 | 98.458 | 98.182 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 462 | 462 / 0 | 51.435 | 51.334 | 38.227 | -13.208 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 495 | 0 / 495 | 23.918 | 22.357 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 495 | 0 / 495 | 21.899 | 20.531 | 25.785 | 3.886 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| MoeInitRoutingV3 / unresolved | 462 | 0 / 462 | 21.821 | 21.538 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 374 | 374 / 0 | 18.014 | 17.927 | 9.089 | -8.924 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 2464 | 0 / 2464 | 2.608 | 2.140 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 121 | 0 / 121 | 52.802 | 52.896 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 495 | 0 / 495 | 11.933 | 11.783 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 495 | 0 / 495 | 11.761 | 11.581 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 121 | 0 / 121 | 48.097 | 49.747 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 374 | 0 / 374 | 14.290 | 13.915 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMlaMetadata / unresolved | 121 | 0 / 121 | 39.293 | 36.752 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 990 | 0 / 990 | 4.716 | 3.554 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 462 | 462 / 0 | 9.708 | 9.543 | 4.093 | -5.615 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 2024 | 0 / 2024 | 1.867 | 1.847 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 462 | 462 / 0 | 7.366 | 7.275 | 4.682 | -2.684 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _copy_conv_state_kernel / unresolved | 748 | 0 / 748 | 4.524 | 4.452 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 374 | 0 / 374 | 8.331 | 8.139 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 374 | 374 / 0 | 6.738 | 6.710 | 2.393 | -4.345 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 462 | 0 / 462 | 5.415 | 5.330 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 363 | 0 / 363 | 6.439 | 6.408 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1111 | 0 / 1111 | 2.037 | 1.637 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 495 | 495 / 0 | 4.542 | 4.522 | 1.312 | -3.230 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cumsum / unresolved | 462 | 0 / 462 | 4.828 | 4.643 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 495 | 495 / 0 | 4.462 | 4.465 | 1.312 | -3.150 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 462 | 462 / 0 | 4.763 | 4.737 | 1.312 | -3.451 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeFinalizeRoutingV2 / unresolved | 462 | 0 / 462 | 4.756 | 4.720 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 869 | 0 / 869 | 2.470 | 2.526 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 374 | 0 / 374 | 5.613 | 5.579 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 495 | 495 / 0 | 4.071 | 4.063 | 1.312 | -2.759 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 495 | 495 / 0 | 4.034 | 4.038 | 1.312 | -2.722 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 462 | 462 / 0 | 4.212 | 4.173 | 1.578 | -2.634 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ClipByValueV2 / unresolved | 990 | 0 / 990 | 1.829 | 1.818 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 495 | 0 / 495 | 3.588 | 3.630 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.down.quantize | 462 | 462 / 0 | 3.690 | 3.691 | 1.312 | -2.378 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / router_selection | 462 | 0 / 462 | 3.530 | 3.514 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| DynamicMxQuant / unresolved | 363 | 0 / 363 | 4.456 | 4.458 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 616 | 0 / 616 | 2.114 | 2.050 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 121 | 0 / 121 | 10.111 | 10.121 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 121 | 121 / 0 | 9.590 | 9.573 | 3.510 | -6.079 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| layer_norm_gated_fwd_kernel / unresolved | 374 | 0 / 374 | 2.952 | 2.784 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 121 | 0 / 121 | 9.030 | 9.027 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 374 | 0 / 374 | 2.855 | 2.837 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 242 | 0 / 242 | 4.184 | 4.135 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 495 | 0 / 495 | 2.004 | 1.904 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 121 | 0 / 121 | 8.038 | 8.008 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 121 | 0 / 121 | 8.004 | 7.994 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 242 | 0 / 242 | 3.868 | 3.865 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 495 | 0 / 495 | 1.830 | 1.723 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 242 | 0 / 242 | 3.479 | 3.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 121 | 121 / 0 | 6.749 | 6.744 | 1.578 | -5.171 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Range / unresolved | 374 | 0 / 374 | 2.093 | 1.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 495 | 0 / 495 | 1.532 | 1.448 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 121 | 121 / 0 | 6.185 | 6.172 | 1.578 | -4.607 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Less / unresolved | 374 | 0 / 374 | 1.993 | 1.742 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 242 | 0 / 242 | 2.808 | 2.720 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 121 | 0 / 121 | 5.115 | 5.095 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 121 | 0 / 121 | 4.254 | 4.213 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 121 | 0 / 121 | 3.353 | 3.350 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 121 | 0 / 121 | 3.072 | 3.066 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 242 | 0 / 242 | 1.452 | 1.444 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 33 | 33 / 0 | 8.698 | 8.648 | 4.697 | -4.001 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 33 | 33 / 0 | 5.470 | 5.447 | 1.825 | -3.645 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 33 | 33 / 0 | 4.585 | 4.567 | 1.312 | -3.273 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 33 | 33 / 0 | 3.864 | 3.832 | 1.312 | -2.552 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
