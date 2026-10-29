# Kimi Family / Role Residuals

12 sources; 618 selected complete forwards. Exact saved duration histograms are unchanged.

Activity residuals below are diagnostic device-service differences, not a decomposition of Body wall time.

Largest costed activity gaps, keeping evidence tiers explicit (not an accuracy pass/fail ranking):

| Family / role | Evidence tier | Activity deficit ms/forward |
|---|---|---:|
| GroupedMatmul / expert_up | conditional_source_reference_not_strict | 1.217306 |
| MatMulV3 / latent_down | strict_tensor_cohort_conditional_topology | 0.968498 |
| MatMulV3 / latent_up | strict_tensor_cohort_conditional_topology | 0.651216 |

| Strict family / role | Scored calls | Unmodelled activity excluded | Residual ms/forward |
|---|---:|---:|---:|
| MatMulV3 / latent_down | 56856 | 0 calls | 0.968498 |
| MatMulV3 / latent_up | 56856 | 0 calls | 0.651216 |
| RmsNorm / latent_norm | 56856 | 0 calls | 0.246410 |

Conditional references (separate from strict accuracy; routed valid rows remain declared):

| Family / role | Reference calls | Residual ms/forward |
|---|---:|---:|
| GroupedMatmul / expert_up | 56856 | 1.217306 |
| GroupedMatmul / expert_down | 56856 | 0.622594 |

Outside strict coverage (may include the conditional references above; not a second additive budget):

| Family / role | Unscored activity ms/forward |
|---|---:|
| MatMulV3 / unresolved | 5.720764 |
| GroupedMatmul / expert_up | 3.276558 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 2.985803 |

Per-source strict Top3 (underprediction activity ms/forward):

| Case | First | Second | Third |
|---|---|---|---|
| a5_kimi_tp8_e16_bf16_c16_p16k | MatMulV3/latent_down: 1.0253 | MatMulV3/latent_up: 0.7002 | MatMulV3/shared.down: 0.4772 |
| a5_kimi_tp8_e16_bf16_c16_p4k | MatMulV3/latent_down: 1.0224 | MatMulV3/latent_up: 0.7004 | MatMulV3/shared.down: 0.4753 |
| a5_kimi_tp8_e16_bf16_c1_p16k | MatMulV3/latent_down: 0.8983 | MatMulV3/latent_up: 0.5958 | RmsNorm/latent_norm: 0.2346 |
| a5_kimi_tp8_e16_bf16_c1_p4k | MatMulV3/latent_down: 0.8984 | MatMulV3/latent_up: 0.5936 | RmsNorm/latent_norm: 0.2383 |
| a5_kimi_tp8_e16_bf16_c2_p16k | MatMulV3/latent_down: 0.9016 | MatMulV3/latent_up: 0.6117 | RmsNorm/latent_norm: 0.2336 |
| a5_kimi_tp8_e16_bf16_c2_p4k | MatMulV3/latent_down: 0.9032 | MatMulV3/latent_up: 0.6108 | RmsNorm/latent_norm: 0.2336 |
| a5_kimi_tp8_e16_bf16_c32_p16k | MatMulV3/latent_down: 1.1447 | MatMulV3/latent_up: 0.7688 | MatMulV3/shared.down: 0.5326 |
| a5_kimi_tp8_e16_bf16_c32_p4k | MatMulV3/latent_down: 1.1447 | MatMulV3/latent_up: 0.7680 | MatMulV3/shared.down: 0.5338 |
| a5_kimi_tp8_e16_bf16_c4_p16k | MatMulV3/latent_down: 0.9337 | MatMulV3/latent_up: 0.6291 | RmsNorm/latent_norm: 0.2280 |
| a5_kimi_tp8_e16_bf16_c4_p4k | MatMulV3/latent_down: 0.9382 | MatMulV3/latent_up: 0.6285 | RmsNorm/latent_norm: 0.2280 |
| a5_kimi_tp8_e16_bf16_c8_p16k | MatMulV3/latent_down: 0.9511 | MatMulV3/latent_up: 0.6360 | MatMulV3/shared.gate_up: 0.4749 |
| a5_kimi_tp8_e16_bf16_c8_p4k | MatMulV3/latent_down: 0.9519 | MatMulV3/latent_up: 0.6370 | MatMulV3/shared.gate_up: 0.4761 |

Strict rows compare only their exact scored event subset; unscored is not zero cost.
Source-reference groups remain conditional and are excluded from strict Top3.
Activity differences overlap in time and cannot be added to explain Body wall-clock error.
Cross-runtime changes do not isolate underfilled candidates; a same-runtime ablation is required.
