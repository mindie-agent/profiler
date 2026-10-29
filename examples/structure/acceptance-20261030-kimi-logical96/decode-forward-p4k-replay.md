# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "aeb66892a20588825e0eb443894d5d9b6b71c641"}.

Variant: `kimi-logical96-p4k`. Baseline: null.

Sim 0.8.0; 246 package files; SHA256 `7f30d18bcf75f1f4974fb9a1cc4301d063636f7156431ad4f93019b5e3a70200`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 49 | 36.985292 | 36.952793 | 36.968819 | 25.944475 | -29.85% | compared |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 59 | 30.636854 | 30.614967 | 30.632466 | 22.974141 | -25.01% | compared |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 55 | 33.547630 | 33.515767 | 33.532651 | 23.120895 | -31.08% | compared |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 46 | 40.018728 | 40.017751 | 40.043741 | 29.883420 | -25.33% | compared |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 53 | 34.193709 | 34.177425 | 34.194190 | 23.414403 | -31.52% | compared |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 52 | 34.819213 | 34.791110 | 34.808453 | 24.000107 | -31.07% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 36.985292 | 36.304665 | 0.680627 | 1.84% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 30.636854 | 29.997042 | 0.639813 | 2.09% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 33.547630 | 32.856947 | 0.690684 | 2.06% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 40.018728 | 39.322926 | 0.695802 | 1.74% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 34.193709 | 33.491477 | 0.702232 | 2.05% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 34.819213 | 34.142215 | 0.676998 | 1.94% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | dense_layer | 0 / 1 | 0.335331 | 0.335331 | 0.335331 | 0.245133 | -26.90% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | moe_layer | 0 / 92 | 0.398339 | 0.387665 | 0.429149 | 0.279198 | -29.91% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | dense_layer | 0 / 1 | 0.277218 | 0.277218 | 0.277218 | 0.211561 | -23.68% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | moe_layer | 0 / 92 | 0.329965 | 0.323096 | 0.350795 | 0.247265 | -25.06% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | dense_layer | 0 / 1 | 0.302651 | 0.302651 | 0.302651 | 0.213139 | -29.58% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | moe_layer | 0 / 92 | 0.361328 | 0.354921 | 0.377885 | 0.248843 | -31.13% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | dense_layer | 1 / 1 | 0.337916 | 0.337916 | 0.337916 | 0.290186 | -14.12% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | moe_layer | 0 / 92 | 0.431283 | 0.415274 | 0.473567 | 0.321517 | -25.45% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | dense_layer | 0 / 1 | 0.293014 | 0.293014 | 0.293014 | 0.216295 | -26.18% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | moe_layer | 0 / 92 | 0.368455 | 0.361005 | 0.387096 | 0.251999 | -31.61% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | dense_layer | 0 / 1 | 0.310159 | 0.310159 | 0.310159 | 0.222607 | -28.23% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | moe_layer | 0 / 92 | 0.375068 | 0.367254 | 0.397893 | 0.258311 | -31.13% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 0 / 69 | 0.385013 | 0.385311 | 0.391916 | 0.286027 | -25.71% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 0 / 24 | 0.434026 | 0.426707 | 0.433591 | 0.258146 | -40.52% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | kda | 0 / 69 | 0.320268 | 0.320936 | 0.326067 | 0.253469 | -20.86% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | mla | 0 / 24 | 0.355645 | 0.348782 | 0.355492 | 0.227941 | -35.91% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | kda | 0 / 69 | 0.352595 | 0.353094 | 0.358531 | 0.255047 | -27.67% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | mla | 0 / 24 | 0.383988 | 0.376708 | 0.384608 | 0.229519 | -40.23% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 1 / 69 | 0.413032 | 0.413826 | 0.420032 | 0.329588 | -20.20% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 0 / 24 | 0.479865 | 0.472316 | 0.479303 | 0.297009 | -38.11% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | kda | 0 / 69 | 0.358666 | 0.359601 | 0.365194 | 0.258203 | -28.01% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | mla | 0 / 24 | 0.393454 | 0.386399 | 0.392108 | 0.232675 | -40.86% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | kda | 0 / 69 | 0.364444 | 0.364580 | 0.370731 | 0.264515 | -27.42% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | mla | 0 / 24 | 0.402906 | 0.396176 | 0.402359 | 0.238987 | -40.68% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 0.385013 | 0.379424 | 0.005589 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 0.434026 | 0.421850 | 0.012176 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | kda | 0.320268 | 0.315305 | 0.004963 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | mla | 0.355645 | 0.343375 | 0.012270 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | kda | 0.352595 | 0.346938 | 0.005657 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | mla | 0.383988 | 0.371592 | 0.012396 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 0.413032 | 0.407278 | 0.005754 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 0.479865 | 0.467530 | 0.012334 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | kda | 0.358666 | 0.352873 | 0.005793 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | mla | 0.393454 | 0.380967 | 0.012487 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | kda | 0.364444 | 0.358904 | 0.005540 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | mla | 0.402906 | 0.390743 | 0.012163 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | all | 92 | 4508 | 0.398339 | 0.387570 | 0.282904 | -27.01% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 68 | 3332 | 0.385744 | 0.385530 | 0.286298 | -25.74% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 24 | 1176 | 0.434026 | 0.426871 | 0.258033 | -39.55% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | all | 92 | 5428 | 0.329965 | 0.323043 | 0.250361 | -22.50% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | kda | 68 | 4012 | 0.320901 | 0.321012 | 0.253755 | -20.95% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | mla | 24 | 1416 | 0.355645 | 0.348701 | 0.227828 | -34.66% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | all | 92 | 5060 | 0.361328 | 0.354858 | 0.251939 | -29.00% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | kda | 68 | 3740 | 0.353330 | 0.353148 | 0.255333 | -27.70% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | mla | 24 | 1320 | 0.383988 | 0.376723 | 0.229406 | -39.10% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | all | 92 | 4232 | 0.431283 | 0.415334 | 0.326443 | -21.40% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 68 | 3128 | 0.414137 | 0.414040 | 0.329837 | -20.34% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 24 | 1104 | 0.479865 | 0.472222 | 0.296896 | -37.13% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | all | 92 | 4876 | 0.368455 | 0.361070 | 0.255095 | -29.35% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | kda | 68 | 3604 | 0.359632 | 0.359552 | 0.258489 | -28.11% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | mla | 24 | 1272 | 0.393454 | 0.386327 | 0.232562 | -39.80% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | all | 92 | 4784 | 0.375068 | 0.366904 | 0.261407 | -28.75% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | kda | 68 | 3536 | 0.365243 | 0.364788 | 0.264801 | -27.41% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | mla | 24 | 1248 | 0.402906 | 0.395987 | 0.238874 | -39.68% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 49 | 0.335331 | 0.302283 | 0.304588 | 0.245133 | -26.90% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 59 | 0.277218 | 0.257813 | 0.259545 | 0.211561 | -23.68% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 55 | 0.302651 | 0.269840 | 0.271908 | 0.213139 | -29.58% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 46 | 0.337916 | 0.337564 | 0.341257 | 0.290186 | -14.12% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 53 | 0.293014 | 0.277106 | 0.279247 | 0.216295 | -26.18% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 52 | 0.310159 | 0.281559 | 0.283741 | 0.222607 | -28.23% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 1 | 16 | 16 | unknown | 4104 | 16 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 1 | 1 | 1 | unknown | 4104 | 1 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 1 | 2 | 2 | unknown | 4104 | 2 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 1 | 32 | 32 | unknown | 4104 | 32 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 1 | 4 | 4 | unknown | 4104 | 4 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 1 | 8 | 8 | unknown | 4104 | 8 | — | — | — | — |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | embedding | 49 | 0.004593 | 0.004509 | 0.005168 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | final_norm | 49 | 0.004091 | 0.004082 | 0.004295 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | lm_head | 49 | 0.092424 | 0.092431 | 0.093127 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | embedding | 59 | 0.003171 | 0.003139 | 0.003410 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | final_norm | 59 | 0.002656 | 0.002643 | 0.002785 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | lm_head | 59 | 0.090801 | 0.090715 | 0.091604 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | embedding | 55 | 0.003310 | 0.003279 | 0.003502 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | final_norm | 55 | 0.003606 | 0.003582 | 0.003776 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | lm_head | 55 | 0.090726 | 0.090704 | 0.091558 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | embedding | 46 | 0.003423 | 0.003405 | 0.003697 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | final_norm | 46 | 0.005558 | 0.005548 | 0.005768 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | lm_head | 46 | 0.117594 | 0.117492 | 0.118427 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | embedding | 53 | 0.004472 | 0.004372 | 0.005045 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | final_norm | 53 | 0.003639 | 0.003622 | 0.003763 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | lm_head | 53 | 0.091033 | 0.090857 | 0.091549 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | embedding | 52 | 0.004275 | 0.004245 | 0.004557 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | final_norm | 52 | 0.003738 | 0.003722 | 0.003837 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | lm_head | 52 | 0.091316 | 0.091258 | 0.092021 |

Summary: {"case_count": 6, "compared_cases": 6, "failed_cases": 0, "measured_cases": 6, "passed_cases": 0, "source_case_count": 6, "unresolved_cases": 0}
