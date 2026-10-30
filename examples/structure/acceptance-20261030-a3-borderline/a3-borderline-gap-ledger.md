# A3 near-threshold Body and family ledger

Fixed Sim `30dcea1e`. Residual sign is Sim − Real. Native activity/service differences are not additive Body wall-clock causes.

## v4flash-a3-tp8-c4

Selected 104 / 108 complete forwards; 43 layers. Body Real Mean/P50 32.485961/32.416312 ms, Sim 26.525128 ms (-18.35%). The lower 15% bound is 27.613067 ms; shortfall 1.087939 ms.
Measured activity union 30.611484 ms, internal uncovered gap 1.874477 ms. Both original measurements are retained.

| Same-direction Top3 / role | Evidence | Calls/F | Real Mean / P50 us | Sim us | Sim−Real ms/F |
| --- | --- | ---: | ---: | ---: | ---: |
| QuantBatchMatmulV3 / shared.down | strict_cohort | 43.000 | 16.897495 / 16.440000 | 5.000000 | -0.511592 |
| GroupedMatmul / expert_down | conditional_source_reference | 43.000 | 58.647545 / 58.359000 | 46.903631 | -0.504988 |
| QuantBatchMatmulV3 / grouped_output_b|q_b | strict_cohort | 43.000 | 12.313952 / 12.320000 | 5.587147 | -0.289253 |

Largest opposite-direction rows:
- MatMulV2 / router: +1.308926 ms/F (strict_cohort).
- HcPre / ffn.hc_pre: +0.876594 ms/F (conditional_declared_subgraph).
- HcPre / attention.hc_pre: +0.871432 ms/F (conditional_declared_subgraph).

| Unpriced family / role | Calls/F | Real Mean / P50 us | Unpriced activity ms/F |
| --- | ---: | ---: | ---: |
| Compressor / unresolved | 62.000 | 48.715027 / 51.179000 | 3.020332 |
| TransposeBatchMatMul / unresolved | 43.000 | 54.177110 / 53.878000 | 2.329616 |
| InplacePartialRotaryMul / unresolved | 150.000 | 13.056761 / 4.440000 | 1.958514 |
| MoeDistributeDispatchV2 / unresolved | 43.000 | 40.954346 / 40.869500 | 1.761037 |
| ScatterNdUpdateSk / unresolved | 126.000 | 13.572121 / 12.140000 | 1.710087 |
| DequantSwigluQuant / unresolved | 43.000 | 33.890610 / 12.760000 | 1.457296 |
| SparseAttnSharedkv / unresolved | 43.000 | 29.659619 / 26.239000 | 1.275364 |
| hcom_allGather_ / ffn_down_communication | 43.000 | 29.414945 / 28.459000 | 1.264843 |
| RmsNorm / unresolved | 86.000 | 10.474008 / 10.589500 | 0.900765 |
| MoeDistributeCombineV2 / unresolved | 43.000 | 20.940570 / 19.439000 | 0.900445 |
| ForeachAddList / unresolved | 43.000 | 17.594728 / 17.380000 | 0.756573 |
| QuantBatchMatmulV3 / unresolved | 43.000 | 15.895458 / 15.780000 | 0.683505 |

All priced rows, original histograms via source references, per-layer means, exact source/case/runtime identities and remaining unpriced families are retained in JSON.

## a3_kimi4_tp8_w4a8_c32

Selected 220 / 229 complete forwards; 4 layers. Body Real Mean/P50 6.713782/6.664787 ms, Sim 5.348630 ms (-20.33%). The lower 15% bound is 5.706714 ms; shortfall 0.358085 ms.
Measured activity union 6.609395 ms, internal uncovered gap 0.104386 ms. Both original measurements are retained.

| Same-direction Top3 / role | Evidence | Calls/F | Real Mean / P50 us | Sim us | Sim−Real ms/F |
| --- | --- | ---: | ---: | ---: | ---: |
| RecurrentKda / kda_recurrent | conditional_source_reference | 3.000 | 102.068853 / 102.738000 | 53.063632 | -0.147016 |
| FusedInferAttentionScore / latent_attention_complete_batch | conditional_source_reference | 1.000 | 277.585550 / 277.455000 | 160.000000 | -0.117586 |
| CausalConv1d / short_convolution | conditional_source_reference | 3.000 | 22.027298 / 21.080000 | 2.500000 | -0.058582 |

Largest opposite-direction rows:
- GroupedMatmul / expert_up: +0.168717 ms/F (conditional_source_reference).
- GroupedMatmul / expert_down: +0.127749 ms/F (conditional_source_reference).
- QuantBatchMatmulV3 / gate_up: +0.022779 ms/F (strict_cohort).

| Unpriced family / role | Calls/F | Real Mean / P50 us | Unpriced activity ms/F |
| --- | ---: | ---: | ---: |
| DequantSituQuant / unresolved | 6.000 | 83.005390 / 82.918500 | 0.498032 |
| hcom_allGather_ / attention_output_communication | 4.000 | 96.008718 / 32.769000 | 0.384035 |
| MatMulV2 / unresolved | 3.000 | 65.008202 / 66.609000 | 0.195025 |
| QuantBatchMatmulV3 / unresolved | 7.000 | 26.512106 / 21.760000 | 0.185585 |
| MoeDistributeDispatchV2 / unresolved | 3.000 | 58.278774 / 58.639000 | 0.174836 |
| hcom_allGather_ / ffn_down_communication | 5.000 | 31.767925 / 26.599000 | 0.158840 |
| MoeDistributeCombineV2 / unresolved | 3.000 | 42.027815 / 39.629500 | 0.126083 |
| hcom_reduceScatter_ / ffn_down_communication | 4.000 | 27.660082 / 24.049500 | 0.110640 |
| hcom_reduceScatter_ / attention_output_communication | 4.000 | 24.170128 / 18.580000 | 0.096681 |
| AttnResFwd / unresolved | 9.000 | 10.625631 / 10.600000 | 0.095631 |
| MatMulV3 / unresolved | 3.000 | 25.649632 / 23.959500 | 0.076949 |
| ForeachAddList / unresolved | 3.000 | 17.216430 / 17.340000 | 0.051649 |

The 1,760 `reduce_scatterAicpuKernel` records are confirmed AI_CPU / Block0 / Mix0. Their 1.375535 ms/F elapsed overlay is isolated from service residuals. The existing alias filter recognizes `reducescatterAicpuKernel`, so this underscore variant needs a separate boundary regression; no Body time is subtracted here.

The old FIA 5 us reference selected one of 32 sequences. This ledger replaces that reference with all 32 declared programs costed together (160 us), not with a manually multiplied budget. It remains conditional: native physical 16 heads differ from declared logical 12, context scalar values are missing, and 32 unfused programs differ from one native batch call.

All priced rows, original histograms via source references, per-layer means, exact source/case/runtime identities and remaining unpriced families are retained in JSON.
