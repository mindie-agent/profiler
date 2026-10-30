# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "3b72ea2d"}.

Variant: `observed-service-hc-atomic-3b72ea2d`. Baseline: null.

Sim 0.8.0; 276 package files; SHA256 `57520ed725bfe6358585bd404f4cefa1f7702c00aabbc9294fecfb44a2f21db8`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 30 | 28.833324 | 28.828410 | 28.884507 | 23.473335 | -18.59% | compared |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | 3 | 25.112799 | 25.067088 | 25.282855 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | 2 | 21.340235 | 21.340235 | 21.389070 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | 2 | 18.881633 | 18.881633 | 19.871570 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | 1 | 16.092148 | 16.092148 | 16.092148 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 11 | 21.418246 | 21.408145 | 21.432068 | 16.381328 | -23.52% | compared |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | 9 | 15.589915 | 15.582603 | 15.642063 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | 3 | 17.682321 | 17.672472 | 17.709316 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 15.683328 | 15.670472 | 15.738329 | 11.953329 | -23.78% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; without separating that wait, elapsed time does not identify pure link bandwidth. The same observed boundary may calibrate per-call, per-group or payload-regime service responses. Explicit in-sample/heldout declarations are retained separately from contract eligibility; missing evaluation provenance remains not_declared.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 28.833324 | 28.568438 | 0.264886 | 0.92% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | 25.112799 | 24.844953 | 0.267846 | 1.07% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | 21.340235 | 21.068491 | 0.271744 | 1.27% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | 18.881633 | 18.617714 | 0.263919 | 1.40% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | 16.092148 | 15.828829 | 0.263319 | 1.64% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 21.418246 | 21.147118 | 0.271128 | 1.27% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | 15.589915 | 15.327661 | 0.262254 | 1.68% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | 17.682321 | 17.420494 | 0.261827 | 1.48% | not_established | 8 / 1 / 1 | auto / full |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 15.683328 | 15.421254 | 0.262074 | 1.67% | not_established | 8 / 1 / 1 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | dense_layer | 0 / 3 | 0.334844 | 0.257668 | 0.497291 | 0.166339 | -50.32% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | moe_layer | 31 / 42 | 0.662567 | 0.593192 | 0.867922 | 0.547008 | -17.44% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | dense_layer | 0 / 3 | 0.264436 | 0.235357 | 0.323452 | 0.143074 | -45.89% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | moe_layer | 1 / 42 | 0.491047 | 0.428691 | 0.670685 | 0.379812 | -22.65% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | dense_layer | 0 / 3 | 0.306520 | 0.263452 | 0.422210 | 0.133251 | -56.53% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | moe_layer | 30 / 42 | 0.351495 | 0.302211 | 0.492130 | 0.275085 | -21.74% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | kda | 31 / 34 | 0.567253 | 0.588717 | 0.597100 | 0.482556 | -14.93% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | mla | 0 / 11 | 0.867794 | 0.867858 | 0.875472 | 0.642403 | -25.97% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | kda | 1 / 34 | 0.412141 | 0.424787 | 0.432720 | 0.337551 | -18.10% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | mla | 0 / 11 | 0.673135 | 0.669531 | 0.677515 | 0.445871 | -33.76% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 30 / 34 | 0.301047 | 0.298533 | 0.305713 | 0.249518 | -17.12% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0 / 11 | 0.495159 | 0.491361 | 0.512266 | 0.315428 | -36.30% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | kda | 0.567253 | 0.562039 | 0.005215 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | mla | 0.867794 | 0.859921 | 0.007874 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | kda | 0.412141 | 0.406748 | 0.005393 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | mla | 0.673135 | 0.665243 | 0.007892 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 0.301047 | 0.295812 | 0.005235 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0.495159 | 0.487604 | 0.007555 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | all | 44 | 1320 | 0.643979 | 0.591855 | 0.513157 | -13.30% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | kda | 33 | 990 | 0.569374 | 0.588956 | 0.513157 | -12.87% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | mla | 11 | 330 | 0.867794 | 0.864061 | 0.642403 | -25.65% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | all | 44 | 484 | 0.479405 | 0.428782 | 0.356372 | -16.89% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | kda | 33 | 363 | 0.414829 | 0.424868 | 0.356372 | -16.12% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | mla | 11 | 121 | 0.673135 | 0.671351 | 0.445871 | -33.59% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | all | 44 | 2860 | 0.346822 | 0.301057 | 0.260770 | -13.38% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 33 | 2145 | 0.297376 | 0.298344 | 0.260770 | -12.59% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 11 | 715 | 0.495159 | 0.490270 | 0.315428 | -35.66% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 30 | 0.497291 | 0.498862 | 0.512161 | 0.166339 | -66.55% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 11 | 0.323452 | 0.280486 | 0.344031 | 0.143074 | -55.77% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 0.422210 | 0.438253 | 0.487926 | 0.133251 | -68.44% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 4 | 8 | 32 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | 4 | 6 | 24 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | 4 | 4 | 16 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | 4 | 2 | 8 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 4 | 4 | 16 | unknown | 8200 | 4 | — | 12.932970 | — | 10.172629 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | 4 | 1 | 4 | unknown | 8200 | 4 | — | 12.932970 | — | 10.172629 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | 4 | 2 | 8 | unknown | 8200 | 4 | — | 12.932970 | — | 10.172629 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 1 | — | 8.534735 | — | 7.355036 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | embedding | 30 | 0.003182 | 0.003112 | 0.003608 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | output_head_preparation | 30 | 0.005864 | 0.005867 | 0.006163 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | final_norm | 30 | 0.039579 | 0.039516 | 0.040315 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | lm_head | 30 | 0.051001 | 0.050651 | 0.052626 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | embedding | 3 | 0.003911 | 0.003955 | 0.004103 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | output_head_preparation | 3 | 0.006226 | 0.006167 | 0.006562 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | final_norm | 3 | 0.037290 | 0.037535 | 0.037677 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | lm_head | 3 | 0.049996 | 0.050208 | 0.050628 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | embedding | 2 | 0.003790 | 0.003790 | 0.004197 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | output_head_preparation | 2 | 0.005394 | 0.005394 | 0.005662 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | final_norm | 2 | 0.035840 | 0.035840 | 0.035918 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | lm_head | 2 | 0.050087 | 0.050087 | 0.050191 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | embedding | 2 | 0.002894 | 0.002894 | 0.003096 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | output_head_preparation | 2 | 0.005300 | 0.005300 | 0.005735 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | final_norm | 2 | 0.035452 | 0.035452 | 0.035793 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | lm_head | 2 | 0.048963 | 0.048963 | 0.049836 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | embedding | 1 | 0.003240 | 0.003240 | 0.003240 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | output_head_preparation | 1 | 0.004987 | 0.004987 | 0.004987 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | final_norm | 1 | 0.034165 | 0.034165 | 0.034165 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | lm_head | 1 | 0.048935 | 0.048935 | 0.048935 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | embedding | 11 | 0.003148 | 0.003088 | 0.003418 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | output_head_preparation | 11 | 0.005225 | 0.005255 | 0.005539 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | final_norm | 11 | 0.036308 | 0.036356 | 0.036607 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | lm_head | 11 | 0.050044 | 0.050001 | 0.050849 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | embedding | 9 | 0.002952 | 0.002875 | 0.003418 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | output_head_preparation | 9 | 0.005144 | 0.005175 | 0.005625 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | final_norm | 9 | 0.034639 | 0.034648 | 0.035308 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | lm_head | 9 | 0.048629 | 0.048585 | 0.049569 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | embedding | 3 | 0.003078 | 0.003057 | 0.003300 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | output_head_preparation | 3 | 0.005326 | 0.005324 | 0.005616 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | final_norm | 3 | 0.034953 | 0.035107 | 0.035348 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | lm_head | 3 | 0.049295 | 0.049272 | 0.049677 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | embedding | 65 | 0.003436 | 0.003402 | 0.003777 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | output_head_preparation | 65 | 0.005408 | 0.005362 | 0.005811 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | final_norm | 65 | 0.034594 | 0.034528 | 0.035106 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | lm_head | 65 | 0.048571 | 0.048453 | 0.049677 |

Summary: {"case_count": 9, "compared_cases": 3, "failed_cases": 0, "measured_cases": 9, "passed_cases": 0, "source_case_count": 3, "unresolved_cases": 6}
