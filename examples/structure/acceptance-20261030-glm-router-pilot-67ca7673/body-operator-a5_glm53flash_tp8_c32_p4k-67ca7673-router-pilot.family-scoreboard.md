# Complete Decode Body Operator Families

Only complete events inside the 31 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_glm53flash_tp8_c32_p4k / 67ca7673-router-pilot | 1 / 1 | 0 / 0 | 1 / 1 | 1302 / 80445 | 0 |

## a5_glm53flash_tp8_c32_p4k / 67ca7673-router-pilot

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1302 | 0 / 1302 | 207.865 | 207.616 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1302 | 0 / 1302 | 109.824 | 110.412 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMla / unresolved | 341 | 0 / 341 | 153.517 | 153.209 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1395 | 0 / 1395 | 36.341 | 36.058 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1395 | 0 / 1395 | 36.213 | 32.117 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1054 | 0 / 1054 | 43.987 | 44.073 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 341 | 0 / 341 | 121.532 | 121.562 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeInitRoutingV3 / unresolved | 1302 | 0 / 1302 | 24.685 | 24.843 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 1054 | 0 / 1054 | 26.517 | 26.599 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _copy_conv_state_kernel / unresolved | 2108 | 0 / 2108 | 12.896 | 12.476 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 1302 | 1302 / 0 | 19.915 | 19.981 | 19.750 | -0.165 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 6944 | 0 / 6944 | 3.616 | 3.741 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 1395 | 0 / 1395 | 16.554 | 16.336 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 1395 | 0 / 1395 | 16.095 | 15.947 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMlaMetadata / unresolved | 341 | 0 / 341 | 58.347 | 54.620 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 2790 | 0 / 2790 | 6.255 | 3.947 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 5704 | 0 / 5704 | 2.935 | 2.034 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1054 | 0 / 1054 | 13.045 | 13.113 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 1395 | 0 / 1395 | 8.079 | 8.107 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeFinalizeRoutingV2 / unresolved | 1302 | 0 / 1302 | 8.615 | 8.595 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 1054 | 0 / 1054 | 10.354 | 10.358 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 1395 | 0 / 1395 | 7.378 | 7.312 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 1302 | 0 / 1302 | 7.858 | 7.826 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 1302 | 0 / 1302 | 7.584 | 7.555 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 2449 | 0 / 2449 | 3.995 | 4.117 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1023 | 0 / 1023 | 8.909 | 8.679 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 3131 | 0 / 3131 | 2.892 | 2.544 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / router_selection | 1302 | 0 / 1302 | 6.633 | 6.528 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 2790 | 0 / 2790 | 2.954 | 2.813 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 1395 | 0 / 1395 | 5.554 | 5.503 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cumsum / unresolved | 1302 | 0 / 1302 | 5.612 | 5.705 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 341 | 0 / 341 | 21.113 | 21.074 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 1302 | 0 / 1302 | 5.266 | 5.299 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 1395 | 0 / 1395 | 4.805 | 5.359 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 1395 | 0 / 1395 | 4.607 | 4.552 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 1302 | 0 / 1302 | 4.424 | 4.414 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.down.quantize | 1302 | 0 / 1302 | 4.349 | 4.343 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 341 | 0 / 341 | 16.602 | 16.621 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 341 | 0 / 341 | 15.415 | 15.298 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 1054 | 0 / 1054 | 4.977 | 4.973 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 1736 | 0 / 1736 | 2.906 | 2.934 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 341 | 0 / 341 | 14.627 | 14.589 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 1395 | 0 / 1395 | 3.556 | 3.542 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 1023 | 0 / 1023 | 4.844 | 4.795 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1395 | 0 / 1395 | 3.358 | 3.261 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 341 | 0 / 341 | 12.922 | 12.969 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1054 | 0 / 1054 | 3.998 | 3.997 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1054 | 0 / 1054 | 3.631 | 3.622 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 682 | 0 / 682 | 5.468 | 5.481 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 341 | 0 / 341 | 8.709 | 8.716 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 682 | 0 / 682 | 4.265 | 4.221 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 341 | 0 / 341 | 8.328 | 8.331 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 1395 | 0 / 1395 | 2.033 | 2.051 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 1054 | 0 / 1054 | 2.635 | 2.594 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 1054 | 0 / 1054 | 2.568 | 2.622 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 682 | 0 / 682 | 3.760 | 3.756 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 682 | 0 / 682 | 3.365 | 3.317 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 341 | 0 / 341 | 5.884 | 5.916 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 341 | 0 / 341 | 5.604 | 5.457 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 341 | 0 / 341 | 5.069 | 5.034 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 341 | 0 / 341 | 4.242 | 4.221 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 341 | 0 / 341 | 3.701 | 3.666 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 93 | 0 / 93 | 11.509 | 11.425 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 682 | 0 / 682 | 1.446 | 1.497 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / down | 93 | 0 / 93 | 7.035 | 7.002 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / gate_up.quantize | 93 | 0 / 93 | 5.285 | 5.293 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / down.quantize | 93 | 0 / 93 | 4.304 | 4.279 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
