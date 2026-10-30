# Complete Decode Body Operator Families

Only complete events inside the 32 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_glm53flash_tp8_c16_p8k / source-complete-30dcea1e | 18 / 18 | 1 / 1 | 19 / 19 | 17440 / 83040 | 0 |

## a5_glm53flash_tp8_c16_p8k / source-complete-30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1344 | 0 / 1344 | 206.105 | 205.956 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1344 | 1344 / 0 | 102.724 | 102.578 | 104.565 | 1.841 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1440 | 0 / 1440 | 34.790 | 34.321 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1440 | 0 / 1440 | 33.869 | 31.148 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 352 | 0 / 352 | 126.802 | 126.864 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeInitRoutingV3 / unresolved | 1344 | 0 / 1344 | 22.800 | 22.881 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 352 | 0 / 352 | 86.858 | 86.710 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1088 | 0 / 1088 | 25.509 | 25.294 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 1088 | 1088 / 0 | 22.732 | 22.767 | 12.294 | -10.439 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 7168 | 0 / 7168 | 3.042 | 2.916 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 1440 | 0 / 1440 | 14.576 | 14.436 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 1440 | 0 / 1440 | 14.474 | 14.170 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| MatMulV3 / router | 1344 | 1344 / 0 | 13.497 | 13.474 | 10.507 | -2.991 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMlaMetadata / unresolved | 352 | 0 / 352 | 50.775 | 47.837 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _copy_conv_state_kernel / unresolved | 2176 | 0 / 2176 | 8.170 | 8.200 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 2880 | 0 / 2880 | 5.712 | 3.752 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 5888 | 0 / 5888 | 2.600 | 1.931 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1088 | 0 / 1088 | 11.723 | 11.664 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 1344 | 0 / 1344 | 7.408 | 7.379 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeFinalizeRoutingV2 / unresolved | 1344 | 0 / 1344 | 7.295 | 7.289 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 1344 | 1344 / 0 | 6.950 | 6.921 | 6.320 | -0.629 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / attention.hc_post_group | 1440 | 1440 / 0 | 6.437 | 6.449 | 1.396 | -5.041 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 1088 | 1088 / 0 | 8.398 | 8.413 | 3.381 | -5.016 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 2528 | 0 / 2528 | 3.522 | 3.146 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 1440 | 1440 / 0 | 6.060 | 5.992 | 1.396 | -4.663 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 3232 | 0 / 3232 | 2.694 | 2.366 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 1440 | 1440 / 0 | 5.972 | 5.817 | 1.312 | -4.660 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 1440 | 1440 / 0 | 5.614 | 5.603 | 1.312 | -4.302 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / router_selection | 1344 | 0 / 1344 | 5.812 | 5.734 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| QuantBatchMatmulV3 / unresolved | 1056 | 0 / 1056 | 7.378 | 7.794 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cumsum / unresolved | 1344 | 0 / 1344 | 5.385 | 5.519 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 2880 | 0 / 2880 | 2.425 | 2.389 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 1344 | 1344 / 0 | 5.052 | 5.062 | 1.312 | -3.740 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.down.quantize | 1344 | 1344 / 0 | 4.918 | 4.910 | 1.312 | -3.606 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ViewCopy / unresolved | 1088 | 0 / 1088 | 5.858 | 5.864 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 1440 | 0 / 1440 | 4.260 | 4.521 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 1344 | 1344 / 0 | 4.002 | 3.994 | 1.578 | -2.424 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 1056 | 0 / 1056 | 4.740 | 4.691 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 1792 | 0 / 1792 | 2.639 | 2.615 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 352 | 0 / 352 | 13.114 | 13.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 1440 | 0 / 1440 | 2.985 | 2.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 352 | 352 / 0 | 12.044 | 12.020 | 4.871 | -7.173 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 1440 | 0 / 1440 | 2.674 | 2.592 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 352 | 0 / 352 | 10.932 | 10.946 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1088 | 0 / 1088 | 3.505 | 3.603 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 704 | 0 / 704 | 5.381 | 5.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 352 | 0 / 352 | 10.551 | 10.430 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 704 | 0 / 704 | 5.230 | 5.160 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1088 | 0 / 1088 | 3.262 | 3.235 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 352 | 0 / 352 | 9.201 | 9.175 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 1088 | 0 / 1088 | 2.470 | 2.481 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 352 | 352 / 0 | 7.526 | 7.509 | 1.578 | -5.948 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SelectV2 / unresolved | 704 | 0 / 704 | 3.539 | 3.463 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 352 | 352 / 0 | 7.074 | 7.125 | 1.827 | -5.247 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 1440 | 0 / 1440 | 1.701 | 1.658 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 352 | 0 / 352 | 6.768 | 6.657 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 704 | 0 / 704 | 3.130 | 3.197 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 1088 | 0 / 1088 | 2.001 | 1.866 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 352 | 0 / 352 | 5.866 | 5.881 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 352 | 0 / 352 | 4.546 | 4.478 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 352 | 0 / 352 | 4.138 | 4.106 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 352 | 0 / 352 | 3.333 | 3.329 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 704 | 0 / 704 | 1.440 | 1.488 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 96 | 96 / 0 | 9.034 | 9.007 | 6.380 | -2.655 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 96 | 96 / 0 | 6.432 | 6.416 | 2.573 | -3.859 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 96 | 96 / 0 | 4.990 | 5.044 | 1.312 | -3.678 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 96 | 96 / 0 | 4.392 | 4.427 | 1.312 | -3.080 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
