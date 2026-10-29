# Complete Decode Body Operator Families

Only complete events inside the 63 accepted target-body windows from 1 sources enter this report. Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.
Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.
Declaration arms may reuse captures. Calls summed across arms are not independent observations.
Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. Communication elapsed retains peer wait and is shown only as a declared-program reference, never used to recalibrate bandwidth.

| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_k3_p32768_c1 / runtime86-context32768-matrix-only | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 212940 | 0 |

## a5_kimi_k3_p32768_c1 / runtime86-context32768-matrix-only

| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| GroupedMatmul / unresolved | 21735 | 0 / 21735 | 20.268 | 15.502 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| GroupedMatmulSituQuant / grouped_gate_up_situ_quant | 5796 | 0 / 5796 | 74.250 | 74.020 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| SituMxQuant / shared.situ_quant | 5796 | 0 / 5796 | 65.155 | 64.681 | — | — | 15% (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV4 / shared.gate_up | 5796 | 0 / 5796 | 30.427 | 31.123 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / unresolved | 10143 | 0 / 10143 | 17.326 | 11.756 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeDispatchV3 / unresolved | 5796 | 0 / 5796 | 24.530 | 24.218 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| AttnResFwd / unresolved | 11781 | 0 / 11781 | 10.555 | 10.219 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeDistributeCombineV3 / unresolved | 5796 | 0 / 5796 | 14.645 | 14.674 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / attention_output_communication | 5859 | 0 / 5859 | 13.851 | 13.650 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| QuantBatchMatmulV4 / shared.down | 5796 | 0 / 5796 | 13.143 | 13.194 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| hcom_reduceScatter_ / ffn_down_communication | 5859 | 0 / 5859 | 12.459 | 12.359 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allGather_ / attention_output_communication | 5859 | 0 / 5859 | 9.618 | 9.415 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| hcom_allGather_ / ffn_down_communication | 5922 | 0 / 5922 | 9.325 | 9.324 | — | — | 15 us (unmodeled) | 0 / 0 | unresolved / unresolved |
| MatMulV3 / linear_output | 4347 | 0 / 4347 | 12.553 | 12.540 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| PadV3 / unresolved | 14679 | 0 / 14679 | 3.706 | 3.647 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| FusedInferAttentionScore / unresolved | 1512 | 0 / 1512 | 32.351 | 32.296 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / latent_down.quantize | 11592 | 0 / 11592 | 4.138 | 4.116 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RecurrentKda / unresolved | 4347 | 0 / 4347 | 9.601 | 9.513 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MlaPrologV3 / mla_prolog | 1512 | 0 / 1512 | 22.248 | 22.218 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ForeachAddList / unresolved | 5796 | 0 / 5796 | 4.613 | 4.596 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MoeGatingTopK / unresolved | 5796 | 0 / 5796 | 4.446 | 4.507 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / output_gate | 1512 | 0 / 1512 | 16.937 | 16.905 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| CausalConv1d / unresolved | 4347 | 0 / 4347 | 5.180 | 5.142 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Fill / unresolved | 16065 | 0 / 16065 | 1.380 | 1.354 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| MatMulV3 / output | 1512 | 0 / 1512 | 12.576 | 12.572 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / linear_q.quantize | 4347 | 0 / 4347 | 4.126 | 4.090 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| RmsNormDynamicMxQuant / latent_up.quantize | 5796 | 0 / 5796 | 3.000 | 3.038 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Sigmoid / unresolved | 5922 | 0 / 5922 | 2.366 | 2.469 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| ZerosLike / unresolved | 5859 | 0 / 5859 | 2.225 | 2.368 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| layer_norm_gated_fwd_kernel / unresolved | 4347 | 0 / 4347 | 2.600 | 2.572 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Cast / unresolved | 6174 | 0 / 6174 | 1.598 | 1.479 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| TransposeBatchMatMul / v_expand | 1512 | 0 / 1512 | 5.877 | 5.880 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| DynamicMxQuant / unresolved | 1638 | 0 / 1638 | 4.042 | 3.994 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Mul / unresolved | 1764 | 0 / 1764 | 2.560 | 2.578 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| QuantBatchMatmulV3 / unresolved | 126 | 0 / 126 | 19.882 | 19.642 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Slice / unresolved | 126 | 0 / 126 | 4.366 | 4.427 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Tanh / unresolved | 126 | 0 / 126 | 3.369 | 3.248 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Muls / unresolved | 126 | 0 / 126 | 3.085 | 3.163 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| Index / unresolved | 63 | 0 / 63 | 5.062 | 5.054 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |
| BroadcastTo / unresolved | 63 | 0 / 63 | 2.377 | 2.357 | — | — | 15 us (unmodeled) | 0 / 0 | unmodeled / unresolved |


## Retained source-reference coverage

Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.

| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |
| --- | ---: | ---: | ---: | ---: | ---: |
