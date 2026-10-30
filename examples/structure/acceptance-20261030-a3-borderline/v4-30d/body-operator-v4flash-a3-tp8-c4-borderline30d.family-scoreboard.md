# Complete Decode Body Operator Families

Only complete events inside the 104 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| v4flash-a3-tp8-c4 / borderline30d | 12 / 13 | 0 / 0 | 12 / 13 | 51272 / 203424 | 0 |

## v4flash-a3-tp8-c4 / borderline30d

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 4472 | 0 / 4472 | 92.992 | 92.038 | — | — | 15% (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| Compressor / unresolved | 6448 | 0 / 6448 | 48.715 | 51.179 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmul / expert_down | 4472 | 0 / 4472 | 58.648 | 58.359 | — | — | 15% (unmodeled) | 0 / 0 | source_reference / reference_only |
| TransposeBatchMatMul / unresolved | 4472 | 0 / 4472 | 54.177 | 53.878 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| InplacePartialRotaryMul / unresolved | 15600 | 0 / 15600 | 13.057 | 4.440 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV2 / unresolved | 4472 | 0 / 4472 | 40.954 | 40.870 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ScatterNdUpdateSk / unresolved | 13104 | 0 / 13104 | 13.572 | 12.140 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DequantSwigluQuant / unresolved | 4472 | 0 / 4472 | 33.891 | 12.760 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| HcPre / attention.hc_pre | 4472 | 0 / 4472 | 32.049 | 31.360 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| HcPre / ffn.hc_pre | 4472 | 0 / 4472 | 31.929 | 31.180 | — | — | 15 us (unmodeled) | 0 / 0 | tensor_contract_and_conditional_whole_body_role / reference_only |
| SparseAttnSharedkv / unresolved | 4472 | 0 / 4472 | 29.660 | 26.239 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_allGather_ / ffn_down_communication | 4472 | 0 / 4472 | 29.415 | 28.459 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allReduce_ / attention_output_communication | 4472 | 0 / 4472 | 22.553 | 19.459 | 35.585 | 13.032 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| hcom_allReduce_ / ffn_down_communication | 4472 | 0 / 4472 | 21.006 | 17.740 | 35.585 | 14.580 | 15 us (unscored reference) | 0 / 0 | conditional_topology_region_to_declared_collective / reference_only |
| RmsNorm / unresolved | 8944 | 0 / 8944 | 10.474 | 10.589 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV2 / unresolved | 4472 | 0 / 4472 | 20.941 | 19.439 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 4472 | 0 / 4472 | 17.595 | 17.380 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / shared.down | 4472 | 4472 / 0 | 16.897 | 16.440 | 5.000 | -11.897 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / q_a | 4472 | 4472 / 0 | 16.335 | 16.339 | 10.705 | -5.630 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / unresolved | 4472 | 0 / 4472 | 15.895 | 15.780 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV2 / unresolved | 6656 | 0 / 6656 | 10.297 | 12.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| VllmAscendQuantLightningIndexerV2 / unresolved | 2184 | 0 / 2184 | 30.603 | 29.919 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / grouped_output_b + q_b | 4472 | 4472 / 0 | 12.314 | 12.320 | 5.587 | -6.727 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / router | 4472 | 4472 / 0 | 11.984 | 12.060 | 42.424 | 30.440 | 15 us | 0 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / kv_a | 4472 | 4472 / 0 | 11.744 | 11.720 | 10.701 | -1.043 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| QuantBatchMatmulV3 / index_q | 2184 | 2184 / 0 | 17.644 | 17.640 | 11.153 | -6.491 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / attention.hc_post_group | 4472 | 4472 / 0 | 7.932 | 7.860 | 2.500 | -5.432 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_weights | 2184 | 2184 / 0 | 15.861 | 15.859 | 11.273 | -4.588 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| HcPost / ffn.hc_post_group | 4472 | 4472 / 0 | 7.677 | 7.619 | 2.500 | -5.177 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| RmsNormDynamicQuant / unresolved | 4472 | 0 / 4472 | 6.449 | 6.420 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 4472 | 0 / 4472 | 6.047 | 5.840 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicQuant / unresolved | 4368 | 0 / 4368 | 5.986 | 6.600 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNorm / norm1 | 4472 | 4472 / 0 | 5.154 | 5.040 | 2.500 | -2.654 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / shared.gate_up.quantize | 4472 | 4472 / 0 | 5.080 | 5.100 | 2.500 | -2.580 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MatMulV2 / index_query_hadamard | 2184 | 2184 / 0 | 9.909 | 9.879 | 5.000 | -4.909 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| DynamicQuant / grouped_output_a.quantize + q_a.quantize | 4472 | 4472 / 0 | 4.355 | 4.340 | 2.500 | -1.855 | 15 us | 1 / 1 | tensor_contract_and_conditional_whole_body_role / compared |
| MoeGatingTopKHash / unresolved | 4472 | 0 / 4472 | 4.190 | 4.080 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 6552 | 0 / 6552 | 2.735 | 1.300 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNormCast / unresolved | 4472 | 0 / 4472 | 3.968 | 3.940 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 6864 | 0 / 6864 | 1.360 | 1.340 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Equal / unresolved | 312 | 0 / 312 | 2.519 | 2.260 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SelectV2 / unresolved | 312 | 0 / 312 | 2.001 | 2.020 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 312 | 0 / 312 | 1.480 | 1.480 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |

### Conditional source-role program references

Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.

| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GroupedMatmul / expert_down / layers 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42 | 4472 | 58.648 / 58.359 | 46.904 | 2.522 | 2.017 | capacity_vs_valid_rows_conditional |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
| v4flash-a3-tp8-c4 / borderline30d / GroupedMatmul / expert_down | 4472 | 0 | 4472 | 0 | 0 |
