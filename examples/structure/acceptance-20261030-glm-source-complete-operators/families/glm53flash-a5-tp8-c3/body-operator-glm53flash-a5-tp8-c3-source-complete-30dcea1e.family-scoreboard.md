# Complete Decode Body Operator Families

Only complete events inside the 53 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| glm53flash-a5-tp8-c3 / source-complete-30dcea1e | 18 / 18 | 1 / 1 | 19 / 19 | 28885 / 136952 | 0 |

## glm53flash-a5-tp8-c3 / source-complete-30dcea1e

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 2226 | 0 / 2226 | 98.728 | 98.517 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 2226 | 2226 / 0 | 51.524 | 51.382 | 46.054 | -5.470 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / attention_output_communication | 2385 | 0 / 2385 | 26.142 | 20.766 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 2385 | 0 / 2385 | 23.333 | 21.872 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeInitRoutingV3 / unresolved | 2226 | 0 / 2226 | 20.738 | 20.654 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 1802 | 1802 / 0 | 17.826 | 17.762 | 9.089 | -8.736 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 11872 | 0 / 11872 | 2.624 | 2.156 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 583 | 0 / 583 | 52.104 | 52.102 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 2385 | 0 / 2385 | 11.905 | 11.728 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 2385 | 0 / 2385 | 11.753 | 11.566 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| RecurrentKda / unresolved | 1802 | 0 / 1802 | 14.053 | 13.812 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 4770 | 0 / 4770 | 4.727 | 3.586 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMlaMetadata / unresolved | 583 | 0 / 583 | 37.380 | 34.307 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 2226 | 2226 / 0 | 9.420 | 9.392 | 21.989 | 12.569 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 9752 | 0 / 9752 | 1.844 | 1.745 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 2226 | 2226 / 0 | 7.335 | 7.236 | 4.682 | -2.653 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _copy_conv_state_kernel / unresolved | 3604 | 0 / 3604 | 4.259 | 4.257 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1802 | 0 / 1802 | 8.145 | 7.968 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 1802 | 1802 / 0 | 6.624 | 6.613 | 2.393 | -4.231 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 583 | 0 / 583 | 20.381 | 20.366 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 2226 | 0 / 2226 | 5.189 | 5.139 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1749 | 0 / 1749 | 6.437 | 6.422 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 5353 | 0 / 5353 | 2.010 | 1.631 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 2385 | 2385 / 0 | 4.505 | 4.489 | 1.312 | -3.193 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 2385 | 2385 / 0 | 4.478 | 4.465 | 1.312 | -3.166 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeFinalizeRoutingV2 / unresolved | 2226 | 0 / 2226 | 4.736 | 4.709 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 2226 | 2226 / 0 | 4.666 | 4.617 | 1.312 | -3.354 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cumsum / unresolved | 2226 | 0 / 2226 | 4.614 | 4.535 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 4187 | 0 / 4187 | 2.447 | 2.392 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 1802 | 0 / 1802 | 5.601 | 5.593 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 2385 | 2385 / 0 | 3.999 | 3.995 | 1.312 | -2.687 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 2385 | 2385 / 0 | 3.973 | 3.968 | 1.312 | -2.661 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 2226 | 2226 / 0 | 4.214 | 4.182 | 1.578 | -2.636 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ClipByValueV2 / unresolved | 4770 | 0 / 4770 | 1.828 | 1.822 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 2385 | 0 / 2385 | 3.540 | 3.594 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.down.quantize | 2226 | 2226 / 0 | 3.591 | 3.584 | 1.312 | -2.279 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / router_selection | 2226 | 0 / 2226 | 3.520 | 3.504 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| DynamicMxQuant / unresolved | 1749 | 0 / 1749 | 4.453 | 4.465 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 2968 | 0 / 2968 | 2.053 | 2.021 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 583 | 583 / 0 | 9.445 | 9.462 | 3.510 | -5.935 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TopKV2 / unresolved | 583 | 0 / 583 | 9.215 | 9.101 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 583 | 0 / 583 | 9.035 | 9.048 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1802 | 0 / 1802 | 2.910 | 2.789 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1802 | 0 / 1802 | 2.843 | 2.794 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 1166 | 0 / 1166 | 4.205 | 4.154 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 2385 | 0 / 2385 | 1.950 | 1.888 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 583 | 0 / 583 | 7.842 | 7.848 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 583 | 0 / 583 | 7.761 | 7.731 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 1166 | 0 / 1166 | 3.725 | 3.708 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 2385 | 0 / 2385 | 1.812 | 1.705 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 1166 | 0 / 1166 | 3.450 | 3.456 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 1802 | 0 / 1802 | 2.050 | 1.869 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 583 | 583 / 0 | 6.187 | 6.153 | 1.578 | -4.609 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TransposeBatchMatMul / v_expand | 583 | 583 / 0 | 6.127 | 6.083 | 1.578 | -4.549 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 2385 | 0 / 2385 | 1.456 | 1.431 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 1802 | 0 / 1802 | 1.851 | 1.890 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 1166 | 0 / 1166 | 2.854 | 2.686 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 583 | 0 / 583 | 5.058 | 5.049 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 583 | 0 / 583 | 4.251 | 4.227 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 583 | 0 / 583 | 3.391 | 3.376 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 583 | 0 / 583 | 3.023 | 3.016 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 1166 | 0 / 1166 | 1.505 | 1.510 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 159 | 159 / 0 | 8.778 | 8.692 | 4.697 | -4.081 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 159 | 159 / 0 | 5.435 | 5.426 | 1.825 | -3.610 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 159 | 159 / 0 | 4.612 | 4.551 | 1.312 | -3.300 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 159 | 159 / 0 | 3.858 | 3.839 | 1.312 | -2.546 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
