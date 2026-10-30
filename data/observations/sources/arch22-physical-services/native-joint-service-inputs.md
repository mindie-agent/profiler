# Native joint-service observed parameter inputs

These neutral inputs carry measured inclusive native-call responses for a future API. They do not install a floor or replacement and do not invent its interface. Case IDs are provenance only. Each response applies once to the complete source-native boundary, preserving dependencies and occupancy; it must not be repeated for internal phases or added to an already inclusive analytic total.

| Physical domain / native | Sources | F | Calls | Mean/P50 us | Evidence |
|---|---|---:|---:|---:|---|
| KvQuantSparseFlashAttention qrows=12 B=2 | a3_glm53_w4a8_tp16_tpot30_c2, a3_glm53_w4a8_tp16_tpot50_c2 | 88 | 6864 | 95.764102/95.082000 | complete_native_ABI_and_duration_population |
| KvQuantSparseFlashAttention qrows=48 B=8 | a3_glm53_w4a8_tp16_tpot88_c8 | 49 | 3822 | 209.251563/209.144000 | complete_native_ABI_and_duration_population |
| GroupedMatmul qrows=24 B=4 | glm53flash-a3-tp16-c4-livepre | 46 | 1932 | 42.137636/37.591000 | complete_duration_population_with_source_role_conditions |
| GroupedMatmulSwigluQuant qrows=24 B=4 | glm53flash-a3-tp16-c4-livepre | 46 | 1932 | 78.892150/74.871500 | complete_duration_population_with_source_role_conditions |
| KvQuantSparseFlashAttentionVllm qrows=24 B=4 | glm53flash-a3-tp16-c4-livepre | 46 | 506 | 156.697115/156.283000 | complete_duration_population_with_source_role_conditions |
| HcPre qrows=24 B=4 | glm53flash-a3-tp16-c4-livepre | 46 | 4140 | 28.900801/28.821000 | complete_duration_population_with_source_role_conditions |
| HcPost qrows=24 B=4 | glm53flash-a3-tp16-c4-livepre | 46 | 4140 | 10.681547/10.700000 | complete_duration_population_with_source_role_conditions |
| GroupedMatmul qrows=96 B=16 | glm53flash-a3-tp16-c16-livepre | 37 | 1554 | 71.926631/71.581000 | complete_duration_population_with_source_role_conditions |
| GroupedMatmulSwigluQuant qrows=96 B=16 | glm53flash-a3-tp16-c16-livepre | 37 | 1554 | 142.415490/142.163000 | complete_duration_population_with_source_role_conditions |
| KvQuantSparseFlashAttentionVllm qrows=96 B=16 | glm53flash-a3-tp16-c16-livepre | 37 | 407 | 377.579678/377.447000 | complete_duration_population_with_source_role_conditions |
| HcPre qrows=96 B=16 | glm53flash-a3-tp16-c16-livepre | 37 | 3330 | 34.703259/33.861000 | complete_duration_population_with_source_role_conditions |
| HcPost qrows=96 B=16 | glm53flash-a3-tp16-c16-livepre | 37 | 3330 | 20.144186/19.780000 | complete_duration_population_with_source_role_conditions |

GLM78 c2 sources have identical full ABI, Block20/Mix40 and declared context domain, so their complete timing histograms are pooled; each original source and its PMU denominator remain separate. The c8 domain is separate. PMU numeric populations are 3432/3430/3809 while timing populations are 3432/3432/3822.

Livepre c4/c16 HCPre/HCPost/up/down/SFA provide complete 90/90/42/42/11-call-per-Forward histograms, with source-role and dtype conditions. HC attention/FFN populations share their declared source program and are pooled with each original 45-call population retained. Examples do not prove full-population ABI or Block configuration, so these fields remain absent. This limits strict binding, but does not erase their valid whole-native duration response. No active route count is inferred from capacity. KDA/MLA subgroup histograms remain inspectable.

All proposed values are observed, in-sample, in microseconds per native call. No Body residual, pass status, or model/case name determines any value or domain. No raw scan or simulation was run.
