# Complete Decode Body Operator Families

Only complete events inside the 27 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| glm53flash-a5-tp8-c96 / source-complete-30dcea1e | 16 / 18 | 1 / 1 | 17 / 19 | 14715 / 70983 | 0 |

## glm53flash-a5-tp8-c96 / source-complete-30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1134 | 0 / 1134 | 212.446 | 212.391 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 297 | 0 / 297 | 581.899 | 581.617 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1134 | 1134 / 0 | 117.949 | 119.225 | 115.614 | -2.335 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMla / unresolved | 297 | 0 / 297 | 430.921 | 426.659 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 918 | 0 / 918 | 113.836 | 113.776 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1215 | 0 / 1215 | 48.974 | 45.157 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1215 | 0 / 1215 | 47.518 | 46.882 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _copy_conv_state_kernel / unresolved | 1836 | 0 / 1836 | 29.417 | 28.750 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 1134 | 1134 / 0 | 42.304 | 42.410 | 159.682 | 117.378 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeInitRoutingV3 / unresolved | 1134 | 0 / 1134 | 32.655 | 32.641 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 1215 | 0 / 1215 | 26.608 | 26.398 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / ffn.hc_pre | 1215 | 0 / 1215 | 26.214 | 26.045 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| MatMulV3 / linear_qkvbfg_a | 918 | 918 / 0 | 33.612 | 33.590 | 49.345 | 15.734 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMlaMetadata / unresolved | 297 | 0 / 297 | 97.196 | 93.077 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 6048 | 0 / 6048 | 3.810 | 3.919 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 918 | 0 / 918 | 24.108 | 24.130 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 2430 | 0 / 2430 | 8.717 | 3.954 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 1215 | 1215 / 0 | 16.426 | 17.106 | 8.378 | -8.048 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 4968 | 0 / 4968 | 3.492 | 2.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeFinalizeRoutingV2 / unresolved | 1134 | 0 / 1134 | 14.292 | 14.264 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 297 | 0 / 297 | 53.160 | 53.133 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 1215 | 1215 / 0 | 12.982 | 12.959 | 8.378 | -4.604 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 918 | 918 / 0 | 14.384 | 14.370 | 13.729 | -0.655 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sort / unresolved | 297 | 0 / 297 | 39.033 | 39.036 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / router_selection | 1134 | 0 / 1134 | 9.167 | 9.075 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| QuantBatchMatmulV3 / shared.gate_up | 1134 | 1134 / 0 | 9.058 | 9.061 | 8.525 | -0.532 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / unresolved | 891 | 0 / 891 | 11.440 | 13.067 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 1134 | 0 / 1134 | 8.876 | 8.748 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 297 | 0 / 297 | 30.143 | 30.103 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 2727 | 0 / 2727 | 3.280 | 2.971 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 2133 | 0 / 2133 | 4.182 | 4.347 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 1215 | 1215 / 0 | 6.895 | 6.926 | 1.575 | -5.320 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ClipByValueV2 / unresolved | 2430 | 0 / 2430 | 3.159 | 3.221 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 1215 | 1215 / 0 | 6.311 | 6.171 | 1.575 | -4.736 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.gate_up.quantize | 1134 | 1134 / 0 | 6.190 | 6.178 | 1.312 | -4.878 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cumsum / unresolved | 1134 | 0 / 1134 | 6.041 | 6.038 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 297 | 0 / 297 | 22.309 | 22.186 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 1134 | 1134 / 0 | 5.642 | 5.637 | 2.659 | -2.983 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MaskedFill / unresolved | 1215 | 0 / 1215 | 5.096 | 5.782 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 297 | 297 / 0 | 19.112 | 19.096 | 19.687 | 0.575 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Muls / unresolved | 1512 | 0 / 1512 | 3.673 | 3.806 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 1215 | 0 / 1215 | 4.424 | 4.298 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1215 | 0 / 1215 | 4.380 | 4.309 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 918 | 0 / 918 | 5.469 | 5.423 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 1215 | 0 / 1215 | 4.092 | 4.053 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.down.quantize | 1134 | 1134 / 0 | 4.284 | 4.263 | 1.312 | -2.972 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 891 | 0 / 891 | 5.341 | 5.370 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 918 | 0 / 918 | 5.102 | 5.086 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 918 | 0 / 918 | 4.859 | 4.812 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 594 | 0 / 594 | 6.164 | 6.157 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 297 | 297 / 0 | 10.934 | 10.902 | 5.111 | -5.822 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SelectV2 / unresolved | 594 | 0 / 594 | 5.008 | 5.160 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 297 | 297 / 0 | 9.866 | 9.860 | 4.793 | -5.073 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| GreaterEqual / unresolved | 594 | 0 / 594 | 4.731 | 4.787 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 1215 | 0 / 1215 | 2.111 | 2.102 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 918 | 0 / 918 | 2.704 | 2.691 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 594 | 0 / 594 | 4.161 | 4.325 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 918 | 0 / 918 | 2.565 | 2.583 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 297 | 0 / 297 | 7.561 | 7.541 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 297 | 0 / 297 | 6.119 | 6.107 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 81 | 81 / 0 | 21.110 | 20.988 | 25.514 | 4.404 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LayerNormV4 / unresolved | 297 | 0 / 297 | 5.549 | 5.478 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 297 | 0 / 297 | 4.645 | 4.590 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 594 | 0 / 594 | 1.536 | 1.575 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / down | 81 | 81 / 0 | 11.134 | 11.100 | 10.339 | -0.795 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 81 | 81 / 0 | 6.081 | 6.082 | 1.312 | -4.769 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 81 | 81 / 0 | 4.752 | 4.743 | 1.312 | -3.440 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
