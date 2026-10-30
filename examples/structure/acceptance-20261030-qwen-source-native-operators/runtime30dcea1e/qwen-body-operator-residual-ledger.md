# Qwen source-GDN: full-family and Body results

**Strict operator cohorts pass 70/75; all six complete-Body comparisons remain outside 15%.** The 187,674 scored events are a subset of 717,482 retained native events from 403 selected Body forwards (450 complete source forwards). Six gating, six FIA and six FFN all-reduce program references remain conditional and do not enter strict accuracy.

| Source | Body predicted / actual ms | Body error | Top three positive activity residuals, ms/Forward | Largest unpaired native activity, ms/Forward |
|---|---:|---:|---|---|
| qwen35-35b-a5-tp4-c128-graph | 14.845 / 28.585 | -48.1% | hcom_allReduce_ / ffn_down_communication 1.068; RecurrentGatedDeltaRule / decode_recurrent_scan 0.370; CausalConv1d / short_convolution 0.322 | GroupedMatmul / unresolved 4.208; DequantSwigluQuant / unresolved 2.262; hcom_allReduce_ / attention_output_communication 1.959 |
| qwen35-35b-a5-tp4-c4-graph | 5.368 / 11.551 | -53.5% | hcom_allReduce_ / ffn_down_communication 0.567; CausalConv1d / short_convolution 0.181; FusedInferAttentionScore / unresolved 0.130 | GroupedMatmul / unresolved 2.238; hcom_allReduce_ / attention_output_communication 1.104; MoeDistributeDispatchV3 / unresolved 0.690 |
| qwen35-35b-a5-tp4-c64-graph | 10.942 / 21.957 | -50.2% | hcom_allReduce_ / ffn_down_communication 0.697; CausalConv1d / short_convolution 0.246; FusedInferAttentionScore / unresolved 0.200 | GroupedMatmul / unresolved 4.108; DequantSwigluQuant / unresolved 2.161; hcom_allReduce_ / attention_output_communication 1.602 |
| qwen36-a5-tp2-c1 | 7.672 / 12.318 | -37.7% | hcom_allReduce_ / ffn_down_communication 0.423; fused_gdn_gating_kernel / unresolved 0.355; CausalConv1d / short_convolution 0.273 | hcom_allReduce_ / attention_output_communication 0.727; DynamicQuantV2 / unresolved 0.368; Add / unresolved 0.325 |
| qwen36-a5-tp2-c12 | 14.041 / 24.226 | -42.0% | hcom_allReduce_ / ffn_down_communication 2.223; CausalConv1d / short_convolution 0.548; fused_gdn_gating_kernel / unresolved 0.482 | hcom_allReduce_ / attention_output_communication 3.073; DynamicQuantV2 / unresolved 0.772; AddRmsNormDynamicQuant / unresolved 0.674 |
| qwen36-a5-tp2-c96 | 45.491 / 63.853 | -28.8% | hcom_allReduce_ / ffn_down_communication 7.309; CausalConv1d / short_convolution 1.264; RecurrentGatedDeltaRule / decode_recurrent_scan 1.213 | hcom_allReduce_ / attention_output_communication 8.433; AddRmsNormDynamicQuant / unresolved 1.032; DynamicQuantV2 / unresolved 1.000 |

The residual column only compares matched or explicitly conditional populations. It must not be added to reconstruct Body wall time; HCOM includes peer waiting. Unpaired entries lack a current one-to-one comparison and do not imply that Sim omitted their work.

GDN role checks confirm exactly one native gate and one recurrent call per GDN layer, and the Body schedule contains the same number of each program (Qwen3.5: 30; Qwen3.6: 48). Per-source scheduled groups, actual device interval union, internal uncovered gaps, and communication splits are retained in the JSON ledger. There is no evidence in this review of GDN events being assigned to another layer type.

| Source | Gating observed mean / P50 us | Conditional predicted us | Difference ms/Forward |
|---|---:|---:|---:|
| qwen35-35b-a5-tp4-c128-graph | 6.481 / 6.510 | 42.444 | +1.079 |
| qwen35-35b-a5-tp4-c4-graph | 5.242 / 4.984 | 11.138 | +0.177 |
| qwen35-35b-a5-tp4-c64-graph | 6.260 / 6.301 | 42.444 | +1.086 |
| qwen36-a5-tp2-c1 | 14.513 / 14.507 | 7.112 | -0.355 |
| qwen36-a5-tp2-c12 | 83.485 / 82.982 | 73.439 | -0.482 |
| qwen36-a5-tp2-c96 | 120.051 / 120.044 | 97.215 | -1.096 |

Qwen3.6 c12 gating is only 0.482 ms/Forward below measured activity, while Body is 10.185 ms short. Its conditional FFN all-reduce reference is 2.223 ms below measured elapsed activity; attention-output communication contributes another 3.073 ms of unpaired activity. The remaining work requires complete-source and communication scheduling analysis, not a gating-only correction.

All 75 strict programs and six reference workers completed in 61.482 s; maximum worker RSS 131.52 MiB. Standard operator review: 3,244 checks; standard Body review: 1,485 checks; source/geometry/reference ledger: 138 checks. No raw scan or extra prediction was used for these reviews.

| Source | Total actual all-reduce ms/Forward | Attention all-reduce layer0 mean / P50 us | Attention steady call mean / P50 us | Actual internal uncovered gap ms |
|---|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c128-graph | 3.780 | 75.941 / 44.762 | 48.274 / 47.556 | 0.284 |
| qwen35-35b-a5-tp4-c4-graph | 2.113 | 114.052 / 23.446 | 25.381 / 25.213 | 0.417 |
| qwen35-35b-a5-tp4-c64-graph | 2.892 | 255.963 / 302.044 | 34.523 / 34.042 | 0.386 |
| qwen36-a5-tp2-c1 | 1.387 | 50.935 / 9.400 | 10.727 / 10.243 | 0.363 |
| qwen36-a5-tp2-c12 | 5.607 | 263.503 / 38.802 | 44.601 / 42.074 | 0.368 |
| qwen36-a5-tp2-c96 | 16.614 | 429.909 / 126.384 | 127.030 / 126.665 | 0.288 |

For these six retained populations, actual native activity sums equal the saved same-device activity unions; duplicate/overlapping native rows do not explain the Body difference. The representative model scheduled-interval sums also equal its Body span, though compact aggregate equality is not a reconstruction of every dependency. Layer0 all-reduce has source-specific tail outliers, especially Qwen3.5 c64; the retained single-rank observations cannot prove cross-rank arrival skew. Steady communication remains substantial and cannot be removed or calibrated into link bandwidth.

Qwen3.5 c128: Body shortfall is 13.740 ms, while unpaired grouped-matmul activity is 4.208 ms and total observed all-reduce activity is 3.780 ms/Forward. Neither quantity alone explains the whole difference; the full coverage ledger retains 18.078 ms/Forward of unpaired native activity, without interpreting it as omitted Sim budget.
