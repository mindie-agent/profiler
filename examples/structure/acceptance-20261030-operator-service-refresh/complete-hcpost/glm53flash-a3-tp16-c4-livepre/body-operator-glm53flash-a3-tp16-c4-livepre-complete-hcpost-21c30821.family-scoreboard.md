# Complete Decode Body Operator Families

Only complete events inside the 46 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Collective references retain unseparated peer wait. Their same-boundary service may be calibrated; this does not identify pure link bandwidth or complete missing native contracts.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| glm53flash-a3-tp16-c4-livepre / complete-hcpost-21c30821 | 20 / 21 | 0 / 0 | 20 / 21 | 23506 / 85146 | 0 |

## glm53flash-a3-tp16-c4-livepre / complete-hcpost-21c30821

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1932 | 0 / 1932 | 78.892 | 74.871 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV2 / unresolved | 1932 | 0 / 1932 | 71.775 | 70.612 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 1932 | 0 / 1932 | 42.138 | 37.591 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KvQuantSparseFlashAttentionVllm / unresolved | 506 | 0 / 506 | 156.697 | 156.283 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 2070 | 0 / 2070 | 35.791 | 24.601 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1564 | 0 / 1564 | 41.880 | 41.490 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV2 / unresolved | 1932 | 0 / 1932 | 32.036 | 31.941 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 2070 | 0 / 2070 | 29.542 | 29.220 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / ffn.hc_pre | 2070 | 0 / 2070 | 28.259 | 28.261 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / ffn_down_communication | 2070 | 0 / 2070 | 18.055 | 17.801 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 1932 | 0 / 1932 | 18.862 | 16.521 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| QuantBatchMatmulV3 / unresolved | 1932 | 0 / 1932 | 18.783 | 18.800 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_qkvbfg_a | 1564 | 1564 / 0 | 23.099 | 23.671 | 23.897 | 0.798 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MemSet / unresolved | 3864 | 0 / 3864 | 8.858 | 9.010 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PoolKeyIndexer / unresolved | 506 | 0 / 506 | 58.687 | 58.642 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 1932 | 1932 / 0 | 13.929 | 13.960 | 5.000 | -8.929 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 2070 | 2070 / 0 | 10.847 | 10.800 | 10.682 | -0.165 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ForeachAddList / unresolved | 1932 | 0 / 1932 | 11.444 | 11.351 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPost / attention.hc_post_group | 2070 | 2070 / 0 | 10.516 | 10.580 | 10.682 | 0.165 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| PadV3 / unresolved | 3864 | 0 / 3864 | 5.025 | 4.841 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 1932 | 0 / 1932 | 10.020 | 9.900 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 7774 | 0 / 7774 | 2.429 | 2.500 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1564 | 0 / 1564 | 11.704 | 11.580 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 2070 | 2070 / 0 | 8.147 | 7.900 | 2.500 | -5.647 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / norm1 | 2070 | 2070 / 0 | 8.081 | 7.661 | 2.500 | -5.581 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / linear_output | 1564 | 1564 / 0 | 9.797 | 9.780 | 6.471 | -3.326 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DequantSwigluQuant / unresolved | 1932 | 0 / 1932 | 7.764 | 7.520 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| KeyPool / unresolved | 506 | 0 / 506 | 28.272 | 28.301 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / qkv_a | 506 | 506 / 0 | 23.693 | 23.540 | 23.907 | 0.214 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / shared.gate_up.quantize | 1932 | 1932 / 0 | 5.328 | 5.200 | 2.500 | -2.828 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_q | 506 | 506 / 0 | 20.170 | 20.200 | 18.263 | -1.907 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / linear_decay_b + linear_gate_b | 3128 | 3128 / 0 | 3.206 | 3.150 | 5.000 | 1.794 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNorm / unresolved | 1012 | 0 / 1012 | 8.993 | 8.881 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1564 | 0 / 1564 | 5.197 | 5.120 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output | 506 | 506 / 0 | 14.170 | 14.140 | 12.367 | -1.804 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / unresolved | 1932 | 0 / 1932 | 3.657 | 3.500 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicBlockQuant / unresolved | 506 | 0 / 506 | 12.651 | 12.351 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 2530 | 0 / 2530 | 2.325 | 1.420 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GatherV3 / unresolved | 1012 | 0 / 1012 | 5.607 | 5.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / index_k | 1012 | 1012 / 0 | 5.376 | 5.560 | 23.855 | 18.479 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterUpdate / unresolved | 1564 | 0 / 1564 | 3.411 | 3.280 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdateSk / unresolved | 506 | 0 / 506 | 9.826 | 9.420 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Range / unresolved | 506 | 0 / 506 | 9.241 | 8.920 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 506 | 506 / 0 | 8.295 | 8.240 | 5.000 | -3.295 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / q_b | 506 | 506 / 0 | 7.617 | 7.580 | 9.127 | 1.510 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / unresolved | 506 | 0 / 506 | 7.551 | 7.560 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 506 | 506 / 0 | 6.938 | 6.780 | 5.000 | -1.938 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _pack_indices_kernel / unresolved | 506 | 0 / 506 | 5.998 | 6.000 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _write_keypool_caches_kernel / unresolved | 506 | 0 / 506 | 5.941 | 5.920 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_nonempty_keypool_inputs_kernel / unresolved | 506 | 0 / 506 | 4.173 | 4.120 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 506 | 0 / 506 | 4.088 | 4.100 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / gate_up | 138 | 138 / 0 | 14.527 | 14.380 | 12.101 | -2.426 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ClippedSwiglu / unresolved | 138 | 0 / 138 | 14.389 | 14.600 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / down | 138 | 138 / 0 | 12.926 | 13.200 | 5.009 | -7.918 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ConcatD / unresolved | 506 | 0 / 506 | 3.521 | 3.520 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV3 / index_norm | 506 | 506 / 0 | 3.268 | 3.400 | 2.500 | -0.768 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Less / unresolved | 506 | 0 / 506 | 2.173 | 2.200 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LogicalNot / unresolved | 506 | 0 / 506 | 1.322 | 1.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 506 | 0 / 506 | 1.305 | 1.300 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 138 | 138 / 0 | 4.637 | 4.580 | 2.500 | -2.137 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / down.quantize | 138 | 138 / 0 | 4.529 | 4.440 | 2.500 | -2.029 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
