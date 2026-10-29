# Complete Decode Body Operator Families

Only complete events inside the 35 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_glm53flash_tp8_c32_p8k / 86c1ee8f | 18 / 18 | 0 / 1 | 18 / 19 | 19075 / 90825 | 0 |

## a5_glm53flash_tp8_c32_p8k / 86c1ee8f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1470 | 0 / 1470 | 207.849 | 207.460 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1470 | 1470 / 0 | 109.853 | 110.481 | 87.876 | -21.977 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 385 | 0 / 385 | 218.772 | 218.705 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 385 | 0 / 385 | 153.329 | 153.215 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1575 | 0 / 1575 | 36.168 | 32.281 | 29.881 | -6.286 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1575 | 0 / 1575 | 36.137 | 35.532 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| RecurrentKda / unresolved | 1190 | 0 / 1190 | 44.025 | 44.062 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeInitRoutingV3 / unresolved | 1470 | 0 / 1470 | 24.737 | 24.852 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 1190 | 1190 / 0 | 26.307 | 26.424 | 16.566 | -9.742 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _copy_conv_state_kernel / unresolved | 2380 | 0 / 2380 | 12.624 | 12.438 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 1470 | 1470 / 0 | 19.930 | 20.008 | 19.750 | -0.181 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 7840 | 0 / 7840 | 3.618 | 3.752 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 1575 | 0 / 1575 | 16.534 | 16.295 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / ffn.hc_pre | 1575 | 0 / 1575 | 16.156 | 15.992 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| SparseFlashMlaMetadata / unresolved | 385 | 0 / 385 | 58.595 | 55.515 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 3150 | 0 / 3150 | 6.248 | 3.953 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 6440 | 0 / 6440 | 2.930 | 2.030 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1190 | 0 / 1190 | 13.052 | 13.098 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 1575 | 1575 / 0 | 8.074 | 8.081 | 2.793 | -5.281 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeFinalizeRoutingV2 / unresolved | 1470 | 0 / 1470 | 8.595 | 8.582 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 1190 | 1190 / 0 | 10.287 | 10.296 | 4.699 | -5.587 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 1470 | 0 / 1470 | 7.959 | 7.907 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 1575 | 1575 / 0 | 7.360 | 7.286 | 2.793 | -4.567 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.gate_up | 1470 | 1470 / 0 | 7.570 | 7.546 | 8.505 | 0.935 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 2765 | 0 / 2765 | 4.001 | 4.115 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1155 | 0 / 1155 | 8.925 | 8.736 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 3535 | 0 / 3535 | 2.907 | 2.623 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / router_selection | 1470 | 0 / 1470 | 6.604 | 6.508 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| ClipByValueV2 / unresolved | 3150 | 0 / 3150 | 2.971 | 2.838 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 1575 | 1575 / 0 | 5.525 | 5.496 | 1.312 | -4.213 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cumsum / unresolved | 1470 | 0 / 1470 | 5.685 | 5.740 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 385 | 0 / 385 | 21.136 | 21.091 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 1470 | 1470 / 0 | 5.270 | 5.311 | 1.312 | -3.958 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MaskedFill / unresolved | 1575 | 0 / 1575 | 4.813 | 5.365 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 1575 | 1575 / 0 | 4.602 | 4.551 | 1.312 | -3.290 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 1470 | 1470 / 0 | 4.423 | 4.417 | 1.578 | -2.845 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / shared.down.quantize | 1470 | 1470 / 0 | 4.357 | 4.353 | 1.312 | -3.045 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sort / unresolved | 385 | 0 / 385 | 16.620 | 16.615 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 385 | 0 / 385 | 15.560 | 15.505 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 1190 | 0 / 1190 | 4.950 | 4.974 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 1960 | 0 / 1960 | 2.910 | 2.922 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 385 | 385 / 0 | 14.624 | 14.605 | 6.685 | -7.939 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 1155 | 0 / 1155 | 4.832 | 4.785 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 1575 | 0 / 1575 | 3.525 | 3.535 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1575 | 0 / 1575 | 3.380 | 3.287 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 385 | 0 / 385 | 13.008 | 13.077 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1190 | 0 / 1190 | 4.022 | 4.030 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1190 | 0 / 1190 | 3.622 | 3.597 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 770 | 0 / 770 | 5.453 | 5.462 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 385 | 385 / 0 | 8.696 | 8.690 | 1.721 | -6.975 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 770 | 0 / 770 | 4.284 | 4.239 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 385 | 385 / 0 | 8.349 | 8.342 | 2.582 | -5.766 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 1575 | 0 / 1575 | 2.010 | 2.026 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 1190 | 0 / 1190 | 2.642 | 2.594 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 1190 | 0 / 1190 | 2.559 | 2.611 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 770 | 0 / 770 | 3.748 | 4.124 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 770 | 0 / 770 | 3.351 | 3.318 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 385 | 0 / 385 | 5.913 | 5.926 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 385 | 0 / 385 | 5.617 | 5.507 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 385 | 0 / 385 | 5.039 | 5.009 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 385 | 0 / 385 | 4.233 | 4.197 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 385 | 0 / 385 | 3.685 | 3.676 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 105 | 105 / 0 | 11.517 | 11.447 | 8.624 | -2.893 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Fill / unresolved | 770 | 0 / 770 | 1.453 | 1.498 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / down | 105 | 105 / 0 | 7.047 | 7.045 | 3.569 | -3.478 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 105 | 105 / 0 | 5.304 | 5.295 | 1.312 | -3.992 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 105 | 105 / 0 | 4.295 | 4.313 | 1.312 | -2.983 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
