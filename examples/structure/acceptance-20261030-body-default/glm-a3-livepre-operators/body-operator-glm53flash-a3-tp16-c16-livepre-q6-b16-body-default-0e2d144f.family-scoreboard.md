# Complete Decode Body Operator Families

Only complete events inside the 37 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| glm53flash-a3-tp16-c16-livepre-q6-b16 / body-default-0e2d144f | 20 / 21 | 0 / 0 | 20 / 21 | 18907 / 62678 | 0 |

## glm53flash-a3-tp16-c16-livepre-q6-b16 / body-default-0e2d144f

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 1554 | 0 / 1554 | 142.415 | 142.163 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| KvQuantSparseFlashAttentionVllm / unresolved | 407 | 0 / 407 | 377.580 | 377.447 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV2 / unresolved | 1554 | 0 / 1554 | 74.556 | 70.811 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / unresolved | 1554 | 0 / 1554 | 71.927 | 71.581 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 1258 | 0 / 1258 | 79.110 | 77.241 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / attention_output_communication | 1665 | 0 / 1665 | 46.638 | 34.101 | 82.523 | 35.886 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| HcPre / ffn.hc_pre | 1665 | 0 / 1665 | 36.039 | 36.780 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / attention.hc_pre | 1665 | 0 / 1665 | 33.367 | 33.321 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| MoeDistributeDispatchV2 / unresolved | 1554 | 0 / 1554 | 32.486 | 32.221 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allReduce_ / ffn_down_communication | 1665 | 0 / 1665 | 25.677 | 25.381 | 82.523 | 56.846 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| MatMulV2 / linear_qkvbfg_a | 1258 | 1258 / 0 | 29.863 | 30.021 | 35.545 | 5.682 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / attention.hc_post_group | 1665 | 1665 / 0 | 20.206 | 19.701 | 6.703 | -13.504 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 1665 | 1665 / 0 | 20.082 | 19.840 | 6.703 | -13.379 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| hcom_allGather_ / ffn_down_communication | 1554 | 0 / 1554 | 20.074 | 19.161 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| QuantBatchMatmulV3 / unresolved | 1554 | 0 / 1554 | 18.541 | 18.100 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 1554 | 1554 / 0 | 17.836 | 17.920 | 5.000 | -12.836 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| PoolKeyIndexer / unresolved | 407 | 0 / 407 | 65.111 | 64.921 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 1665 | 1665 / 0 | 14.380 | 14.141 | 2.500 | -11.880 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV3 / unresolved | 1554 | 0 / 1554 | 15.208 | 15.160 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm2 | 1665 | 1665 / 0 | 13.716 | 13.760 | 2.500 | -11.216 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Slice / unresolved | 6253 | 0 / 6253 | 3.450 | 3.880 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 1554 | 0 / 1554 | 13.166 | 12.940 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 1258 | 0 / 1258 | 16.133 | 16.120 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / linear_output | 1258 | 1258 / 0 | 13.384 | 13.460 | 8.258 | -5.126 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| KeyPool / unresolved | 407 | 0 / 407 | 39.431 | 39.521 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / shared.gate_up.quantize | 1554 | 1554 / 0 | 8.780 | 8.780 | 2.500 | -6.280 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / qkv_a | 407 | 407 / 0 | 32.191 | 32.240 | 35.586 | 3.395 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DequantSwigluQuant / unresolved | 1554 | 0 / 1554 | 7.825 | 6.841 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / index_q | 407 | 407 / 0 | 26.980 | 26.941 | 21.911 | -5.069 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterUpdate / unresolved | 1258 | 0 / 1258 | 8.065 | 8.040 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 1258 | 0 / 1258 | 7.218 | 6.920 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / unresolved | 814 | 0 / 814 | 10.911 | 10.860 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / output | 407 | 407 / 0 | 19.687 | 19.680 | 15.084 | -4.603 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / linear_decay_b + linear_gate_b | 2516 | 2516 / 0 | 3.128 | 3.091 | 5.000 | 1.872 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopK / unresolved | 1554 | 0 / 1554 | 4.467 | 4.320 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / index_k | 814 | 814 / 0 | 7.501 | 8.160 | 35.375 | 27.873 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Cast / unresolved | 2035 | 0 / 2035 | 2.952 | 1.980 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicBlockQuant / unresolved | 407 | 0 / 407 | 14.107 | 13.820 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GatherV3 / unresolved | 814 | 0 / 814 | 6.496 | 6.440 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / q_b | 407 | 407 / 0 | 9.982 | 10.000 | 13.701 | 3.719 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Range / unresolved | 407 | 0 / 407 | 9.818 | 9.001 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _pack_indices_kernel / unresolved | 407 | 0 / 407 | 9.743 | 9.740 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 407 | 407 / 0 | 8.607 | 8.600 | 5.012 | -3.595 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ScatterNdUpdateSk / unresolved | 407 | 0 / 407 | 8.518 | 8.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 407 | 0 / 407 | 8.295 | 8.280 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| _prepare_nonempty_keypool_inputs_kernel / unresolved | 407 | 0 / 407 | 8.027 | 8.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ConcatD / unresolved | 407 | 0 / 407 | 7.728 | 7.720 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / q_absorb | 407 | 407 / 0 | 7.689 | 7.681 | 5.000 | -2.689 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| _write_keypool_caches_kernel / unresolved | 407 | 0 / 407 | 7.669 | 7.560 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MaskedFill / unresolved | 407 | 0 / 407 | 6.213 | 6.220 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| LayerNormV3 / index_norm | 407 | 407 / 0 | 4.965 | 4.960 | 2.500 | -2.465 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / gate_up | 111 | 111 / 0 | 17.560 | 17.580 | 18.354 | 0.793 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| TensorMove / unresolved | 407 | 0 / 407 | 4.776 | 4.780 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / down | 111 | 111 / 0 | 14.904 | 14.780 | 7.122 | -7.782 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| ClippedSwiglu / unresolved | 111 | 0 / 111 | 8.634 | 8.500 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Less / unresolved | 407 | 0 / 407 | 2.226 | 2.220 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / gate_up.quantize | 111 | 111 / 0 | 7.834 | 7.700 | 2.500 | -5.334 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| Muls / unresolved | 407 | 0 / 407 | 1.618 | 1.620 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / down.quantize | 111 | 111 / 0 | 5.051 | 5.040 | 2.500 | -2.551 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| LogicalNot / unresolved | 407 | 0 / 407 | 1.354 | 1.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
