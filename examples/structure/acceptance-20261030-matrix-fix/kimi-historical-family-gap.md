# Kimi Family / Role Residuals

12 sources; 618 selected complete forwards. Exact saved duration histograms are unchanged.

Activity residuals below are diagnostic device-service differences, not a decomposition of Body wall time.

| Strict family / role | Scored calls | Unmodelled activity excluded | Residual ms/forward |
|---|---:|---:|---:|
| MatMulV3 / latent_down | 56856 | 0 calls | 1.045594 |
| MatMulV3 / latent_up | 56856 | 0 calls | 0.651216 |
| MatMulV3 / shared.gate_up | 26312 | 0 calls | 0.508361 |

Unscored coverage priorities (prediction and prediction error unavailable):

| Family / role | Unscored activity ms/forward |
|---|---:|
| MatMulV3 / unresolved | 5.720764 |
| GroupedMatmul / expert_up | 3.276558 |
| MoeDistributeDispatchV3 / expert_dispatch_native | 2.985803 |

Per-source strict Top3 (underprediction activity ms/forward):

| Case | First | Second | Third |
|---|---|---|---|
| a5_kimi_tp8_e16_bf16_c16_p16k | MatMulV3/shared.gate_up: 1.0983 | MatMulV3/latent_down: 1.0658 | MatMulV3/latent_up: 0.7002 |
| a5_kimi_tp8_e16_bf16_c16_p4k | MatMulV3/shared.gate_up: 1.1002 | MatMulV3/latent_down: 1.0628 | MatMulV3/latent_up: 0.7004 |
| a5_kimi_tp8_e16_bf16_c1_p16k | MatMulV3/latent_down: 0.9989 | MatMulV3/latent_up: 0.5958 | RmsNorm/latent_norm: 0.2346 |
| a5_kimi_tp8_e16_bf16_c1_p4k | MatMulV3/latent_down: 0.9990 | MatMulV3/latent_up: 0.5936 | RmsNorm/latent_norm: 0.2383 |
| a5_kimi_tp8_e16_bf16_c2_p16k | MatMulV3/latent_down: 1.0022 | MatMulV3/latent_up: 0.6117 | RmsNorm/latent_norm: 0.2336 |
| a5_kimi_tp8_e16_bf16_c2_p4k | MatMulV3/latent_down: 1.0038 | MatMulV3/latent_up: 0.6108 | RmsNorm/latent_norm: 0.2336 |
| a5_kimi_tp8_e16_bf16_c32_p16k | MatMulV3/latent_down: 1.1447 | MatMulV3/shared.gate_up: 1.0728 | MatMulV3/latent_up: 0.7688 |
| a5_kimi_tp8_e16_bf16_c32_p4k | MatMulV3/latent_down: 1.1447 | MatMulV3/shared.gate_up: 1.0729 | MatMulV3/latent_up: 0.7680 |
| a5_kimi_tp8_e16_bf16_c4_p16k | MatMulV3/latent_down: 1.0343 | MatMulV3/latent_up: 0.6291 | RmsNorm/latent_norm: 0.2280 |
| a5_kimi_tp8_e16_bf16_c4_p4k | MatMulV3/latent_down: 1.0388 | MatMulV3/latent_up: 0.6285 | RmsNorm/latent_norm: 0.2280 |
| a5_kimi_tp8_e16_bf16_c8_p16k | MatMulV3/shared.gate_up: 1.1188 | MatMulV3/latent_down: 1.0517 | MatMulV3/latent_up: 0.6360 |
| a5_kimi_tp8_e16_bf16_c8_p4k | MatMulV3/shared.gate_up: 1.1201 | MatMulV3/latent_down: 1.0525 | MatMulV3/latent_up: 0.6370 |

Strict rows compare only their exact scored event subset; unscored is not zero cost.
Source-reference groups remain conditional and are excluded from strict Top3.
Activity differences overlap in time and cannot be added to explain Body wall-clock error.
Cross-runtime changes do not isolate underfilled candidates; a same-runtime ablation is required.
