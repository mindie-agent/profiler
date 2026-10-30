# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "672a595fb1e102208d9fc904fad0ec9180fa437a"}.

Sim 0.8.0; 283 package files; SHA256 `c347250c5f5e8aeccd0abda9d2a96a8e22928e2ed8668aed825671276f0e2ce5`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 44 | 57.639270 | 57.561540 | 58.994579 | 42.447117 | -26.36% | compared |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | 4 | 57.124636 | 57.281174 | 57.499588 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 44 | 57.817112 | 57.597031 | 59.091621 | 42.454402 | -26.57% | compared |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | 9 | 57.713255 | 57.524210 | 58.619531 | — | — | unresolved: prediction_deferred_by_population_priority |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; without separating that wait, elapsed time does not identify pure link bandwidth. The same observed boundary may calibrate per-call, per-group or payload-regime service responses. Explicit in-sample/heldout declarations are retained separately from contract eligibility; missing evaluation provenance remains not_declared.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 57.639270 | 55.026876 | 2.612393 | 4.53% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | 57.124636 | 54.590343 | 2.534293 | 4.44% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 57.817112 | 55.202675 | 2.614437 | 4.52% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | 57.713255 | 55.178693 | 2.534562 | 4.39% | not_established | 16 / 1 / 16 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | dense_layer | 0 / 3 | 0.573069 | 0.577426 | 0.585758 | 0.450615 | -21.37% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | moe_layer | 0 / 75 | 0.745549 | 0.745723 | 0.781082 | 0.547937 | -26.51% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | dense_layer | 0 / 3 | 0.587706 | 0.567711 | 0.627936 | 0.450675 | -23.32% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | moe_layer | 0 / 75 | 0.747336 | 0.742162 | 0.785962 | 0.548032 | -26.67% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | mla | 0 / 78 | 0.738916 | 0.743060 | 0.781082 | 0.544194 | -26.35% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | mla | 0 / 78 | 0.741196 | 0.741208 | 0.785962 | 0.544287 | -26.57% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | mla | 0.738916 | 0.705473 | 0.033443 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | mla | 0.741196 | 0.707727 | 0.033469 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | all | 77 | 3388 | 0.740905 | 0.713924 | 0.529443 | -25.84% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | mla | 77 | 3388 | 0.740905 | 0.713924 | 0.529443 | -25.84% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | all | 77 | 3388 | 0.742667 | 0.714665 | 0.529526 | -25.91% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | mla | 77 | 3388 | 0.742667 | 0.714665 | 0.529526 | -25.91% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 44 | 0.585758 | 0.542520 | 0.733755 | 0.450615 | -23.07% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 44 | 0.627936 | 0.549071 | 0.813657 | 0.450675 | -28.23% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 2 | 81.123653 | 76.399375 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 2 | 81.123653 | 76.399375 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 2 | 80.812579 | 76.184906 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 2 | 80.812579 | 76.184906 | — | 68.544460 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | embedding | 44 | 0.004439 | 0.004430 | 0.004660 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | final_norm | 44 | 0.224448 | 0.218014 | 0.222065 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | lm_head | 44 | 0.144133 | 0.144193 | 0.145663 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | embedding | 4 | 0.003600 | 0.003440 | 0.004201 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | final_norm | 4 | 0.213759 | 0.213774 | 0.214284 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | lm_head | 4 | 0.128878 | 0.128733 | 0.129703 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | embedding | 44 | 0.004420 | 0.004410 | 0.004640 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | final_norm | 44 | 0.219680 | 0.218044 | 0.219305 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | lm_head | 44 | 0.144156 | 0.144263 | 0.145303 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | embedding | 9 | 0.003396 | 0.003360 | 0.003940 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | final_norm | 9 | 0.223267 | 0.213164 | 0.302506 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | lm_head | 9 | 0.129758 | 0.129442 | 0.131202 |

Summary: {"case_count": 4, "compared_cases": 2, "failed_cases": 0, "measured_cases": 4, "passed_cases": 0, "source_case_count": 2, "unresolved_cases": 2}
