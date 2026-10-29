# Complete Decode Body Operator Families

Only complete events inside the 30 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_glm53flash_tp8_c8_p4k / 67ca7673 | 18 / 18 | 0 / 1 | 18 / 19 | 16350 / 77520 | 0 |

## a5_glm53flash_tp8_c8_p4k / 67ca7673

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1260 | 0 / 1260 | 184.592 | 184.147 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1260 | 1260 / 0 | 91.186 | 90.988 | 76.439 | -14.748 | 15% | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1350 | 0 / 1350 | 28.659 | 23.094 | 26.370 | -2.289 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1350 | 0 / 1350 | 27.877 | 27.107 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MoeInitRoutingV3 / unresolved | 1260 | 0 / 1260 | 21.641 | 21.509 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 330 | 0 / 330 | 69.982 | 69.982 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 1020 | 1020 / 0 | 20.058 | 19.984 | 10.157 | -9.901 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPre / ffn.hc_pre | 1350 | 0 / 1350 | 14.085 | 13.919 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| Slice / unresolved | 6720 | 0 / 6720 | 2.797 | 2.424 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 1350 | 0 / 1350 | 13.620 | 13.421 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| SparseFlashMla / unresolved | 330 | 0 / 330 | 53.600 | 53.586 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1020 | 0 / 1020 | 16.455 | 16.289 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 1260 | 1260 / 0 | 12.319 | 12.226 | 6.588 | -5.731 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMlaMetadata / unresolved | 330 | 0 / 330 | 43.981 | 41.179 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 2700 | 0 / 2700 | 5.075 | 3.628 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 5520 | 0 / 5520 | 2.331 | 1.898 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _copy_conv_state_kernel / unresolved | 2040 | 0 / 2040 | 5.823 | 5.816 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 1260 | 0 / 1260 | 7.253 | 7.213 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1020 | 0 / 1020 | 8.920 | 8.912 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 1260 | 1260 / 0 | 6.450 | 6.428 | 1.578 | -4.872 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 1350 | 1350 / 0 | 5.651 | 5.638 | 1.312 | -4.339 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm2 | 1350 | 1350 / 0 | 5.592 | 5.572 | 1.312 | -4.280 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / linear_output | 1020 | 1020 / 0 | 7.355 | 7.335 | 2.723 | -4.632 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ZerosLike / unresolved | 2370 | 0 / 2370 | 2.998 | 2.724 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeFinalizeRoutingV2 / unresolved | 1260 | 0 / 1260 | 5.590 | 5.567 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 1350 | 1350 / 0 | 5.067 | 5.034 | 1.312 | -3.755 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Mul / unresolved | 3030 | 0 / 3030 | 2.217 | 1.858 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 1350 | 1350 / 0 | 4.953 | 4.931 | 1.312 | -3.641 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cumsum / unresolved | 1260 | 0 / 1260 | 5.238 | 5.396 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 990 | 0 / 990 | 6.514 | 6.824 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 1260 | 1260 / 0 | 4.908 | 4.912 | 1.312 | -3.596 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ViewCopy / unresolved | 1020 | 0 / 1020 | 5.735 | 5.721 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 2700 | 0 / 2700 | 2.007 | 2.069 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / router_selection | 1260 | 0 / 1260 | 4.114 | 4.046 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| MaskedFill / unresolved | 1350 | 0 / 1350 | 3.726 | 3.715 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.down.quantize | 1260 | 1260 / 0 | 3.824 | 3.814 | 1.312 | -2.512 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / shared.down | 1260 | 1260 / 0 | 3.782 | 3.772 | 1.578 | -2.204 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / unresolved | 990 | 0 / 990 | 4.696 | 4.646 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1020 | 0 / 1020 | 4.153 | 3.848 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 1680 | 0 / 1680 | 2.401 | 2.421 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 660 | 0 / 660 | 5.371 | 5.387 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 330 | 330 / 0 | 10.543 | 10.458 | 3.964 | -6.579 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Sigmoid / unresolved | 1350 | 0 / 1350 | 2.445 | 2.421 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 330 | 0 / 330 | 9.863 | 9.678 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 330 | 0 / 330 | 9.646 | 9.611 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 330 | 0 / 330 | 9.609 | 9.573 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 660 | 0 / 660 | 4.719 | 4.647 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1020 | 0 / 1020 | 2.952 | 2.962 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 1350 | 0 / 1350 | 2.200 | 2.095 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 330 | 0 / 330 | 8.327 | 8.328 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 1020 | 0 / 1020 | 2.366 | 2.530 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 1020 | 0 / 1020 | 2.327 | 2.362 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 660 | 0 / 660 | 3.548 | 3.455 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 330 | 330 / 0 | 7.082 | 7.080 | 1.578 | -5.504 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 1350 | 0 / 1350 | 1.599 | 1.507 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 330 | 330 / 0 | 6.389 | 6.287 | 1.578 | -4.811 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LayerNormV4 / unresolved | 330 | 0 / 330 | 6.007 | 5.972 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 660 | 0 / 660 | 2.894 | 2.829 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 330 | 0 / 330 | 5.225 | 5.160 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 330 | 0 / 330 | 3.885 | 3.857 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 330 | 0 / 330 | 3.467 | 3.445 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 660 | 0 / 660 | 1.477 | 1.488 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 90 | 90 / 0 | 8.263 | 8.241 | 5.258 | -3.005 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / down | 90 | 90 / 0 | 5.747 | 5.734 | 2.074 | -3.673 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / gate_up.quantize | 90 | 90 / 0 | 4.856 | 4.832 | 1.312 | -3.544 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicMxQuant / down.quantize | 90 | 90 / 0 | 4.348 | 4.357 | 1.312 | -3.036 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
