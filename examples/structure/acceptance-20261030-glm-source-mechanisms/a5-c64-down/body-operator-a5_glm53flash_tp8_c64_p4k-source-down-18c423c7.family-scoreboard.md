# Complete Decode Body Operator Families

Only complete events inside the 31 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_glm53flash_tp8_c64_p4k / source-down-18c423c7 | 0 / 0 | 1 / 1 | 1 / 1 | 1302 / 81499 | 0 |

## a5_glm53flash_tp8_c64_p4k / source-down-18c423c7

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuantV2 / unresolved | 1302 | 0 / 1302 | 211.089 | 210.722 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1302 | 1302 / 0 | 115.777 | 117.337 | 111.195 | -4.582 | 15% | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| SparseFlashMla / unresolved | 341 | 0 / 341 | 288.254 | 285.492 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1054 | 0 / 1054 | 78.338 | 78.285 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_lightning_indexer_score_kernel / unresolved | 341 | 0 / 341 | 218.721 | 218.708 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / attention_output_communication | 1395 | 0 / 1395 | 43.605 | 39.492 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_AicpuKernel / ffn_down_communication | 1395 | 0 / 1395 | 41.711 | 41.084 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _copy_conv_state_kernel / unresolved | 2108 | 0 / 2108 | 21.777 | 21.506 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / router | 1302 | 0 / 1302 | 29.762 | 29.854 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeInitRoutingV3 / unresolved | 1302 | 0 / 1302 | 28.768 | 28.822 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_qkvbfg_a | 1054 | 0 / 1054 | 31.997 | 32.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 1395 | 0 / 1395 | 22.094 | 21.964 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 1395 | 0 / 1395 | 21.748 | 21.578 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SparseFlashMlaMetadata / unresolved | 341 | 0 / 341 | 81.800 | 78.398 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 6944 | 0 / 6944 | 3.773 | 3.921 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 2790 | 0 / 2790 | 7.874 | 4.164 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 5704 | 0 / 5704 | 3.188 | 2.179 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1054 | 0 / 1054 | 17.222 | 17.235 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 1395 | 0 / 1395 | 11.932 | 12.155 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeFinalizeRoutingV2 / unresolved | 1302 | 0 / 1302 | 11.587 | 11.571 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / ffn.hc_post_group | 1395 | 0 / 1395 | 10.161 | 10.116 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _expand_pool_indices / unresolved | 341 | 0 / 341 | 37.120 | 37.108 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / linear_output | 1054 | 0 / 1054 | 12.008 | 11.988 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.gate_up | 1302 | 0 / 1302 | 8.562 | 8.569 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 1302 | 0 / 1302 | 8.429 | 8.347 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / router_selection | 1302 | 0 / 1302 | 7.892 | 7.804 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 1023 | 0 / 1023 | 10.038 | 11.037 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 2449 | 0 / 2449 | 4.088 | 4.256 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 3131 | 0 / 3131 | 3.102 | 2.958 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sort / unresolved | 341 | 0 / 341 | 27.759 | 27.745 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 1395 | 0 / 1395 | 6.345 | 6.415 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TopKV2 / unresolved | 341 | 0 / 341 | 25.459 | 25.405 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ClipByValueV2 / unresolved | 2790 | 0 / 2790 | 3.028 | 3.046 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cumsum / unresolved | 1302 | 0 / 1302 | 5.776 | 5.813 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.gate_up.quantize | 1302 | 0 / 1302 | 5.657 | 5.668 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 1395 | 0 / 1395 | 5.235 | 5.070 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 1395 | 0 / 1395 | 5.029 | 5.658 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 1302 | 0 / 1302 | 5.137 | 5.131 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _glm5_next_kpool_tail_compress_kernel / unresolved | 341 | 0 / 341 | 17.601 | 17.373 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TensorMove / unresolved | 1395 | 0 / 1395 | 4.191 | 4.140 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 1736 | 0 / 1736 | 3.310 | 3.426 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 1395 | 0 / 1395 | 4.098 | 4.018 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Add / unresolved | 1395 | 0 / 1395 | 4.043 | 4.018 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1054 | 0 / 1054 | 5.329 | 5.300 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / shared.down.quantize | 1302 | 0 / 1302 | 4.279 | 4.275 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / index_q | 341 | 0 / 341 | 16.317 | 16.387 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 1023 | 0 / 1023 | 5.146 | 5.153 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ViewCopy / unresolved | 1054 | 0 / 1054 | 4.804 | 4.774 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterUpdate / unresolved | 1054 | 0 / 1054 | 4.315 | 4.299 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ReduceSum / unresolved | 682 | 0 / 682 | 5.859 | 5.814 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 341 | 0 / 341 | 11.640 | 11.662 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 341 | 0 / 341 | 10.637 | 10.617 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 1395 | 0 / 1395 | 2.109 | 2.118 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 682 | 0 / 682 | 4.274 | 4.194 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 1054 | 0 / 1054 | 2.602 | 2.591 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 682 | 0 / 682 | 4.011 | 4.139 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 1054 | 0 / 1054 | 2.505 | 2.529 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GreaterEqual / unresolved | 682 | 0 / 682 | 3.836 | 3.810 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _store_kpool_tail_kernel / unresolved | 341 | 0 / 341 | 6.424 | 6.377 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdate / unresolved | 341 | 0 / 341 | 6.033 | 6.002 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV4 / unresolved | 341 | 0 / 341 | 5.640 | 5.551 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 93 | 0 / 93 | 16.365 | 16.294 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 341 | 0 / 341 | 4.219 | 4.198 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 682 | 0 / 682 | 1.454 | 1.488 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / down | 93 | 0 / 93 | 9.280 | 9.267 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / gate_up.quantize | 93 | 0 / 93 | 5.630 | 5.609 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / down.quantize | 93 | 0 / 93 | 4.374 | 4.371 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
