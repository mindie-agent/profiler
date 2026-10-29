# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "1f5b2971"}.

Variant: `glm78_tp16_ep16_int8kv_conditional`. Baseline: null.

Sim 0.8.0; 225 package files; SHA256 `0b82bdf55fb758dbb2560586b32b7bc88ea951da8f97e1bc8d869c94dd6c2a62`; package `/Users/maoxx241/code/sim-rewrite-20261027/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 44 | 57.639270 | 57.561540 | 58.994579 | 39.720800 | -31.09% | compared |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | 4 | 57.124636 | 57.281174 | 57.499588 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 44 | 57.817112 | 57.597031 | 59.091621 | 39.720800 | -31.30% | compared |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | 9 | 57.713255 | 57.524210 | 58.619531 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 49 | 69.556298 | 69.488848 | 69.830375 | 57.630200 | -17.15% | compared |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | 4 | 56.950323 | 56.982838 | 57.378767 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | 3 | 56.846876 | 56.895876 | 57.002119 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | 2 | 68.632741 | 68.632741 | 68.639131 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | 2 | 58.058190 | 58.058190 | 58.239184 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | 1 | 57.387626 | 57.387626 | 57.387626 | — | — | unresolved: prediction_deferred_by_population_priority |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 57.639270 | 55.026876 | 2.612393 | 4.53% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | 57.124636 | 54.590343 | 2.534293 | 4.44% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 57.817112 | 55.202675 | 2.614437 | 4.52% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | 57.713255 | 55.178693 | 2.534562 | 4.39% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 69.556298 | 66.970324 | 2.585974 | 3.72% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | 56.950323 | 54.416393 | 2.533930 | 4.45% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | 56.846876 | 54.171133 | 2.675742 | 4.71% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | 68.632741 | 65.996625 | 2.636115 | 3.84% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | 58.058190 | 55.387721 | 2.670469 | 4.60% | not_established | 16 / 1 / 16 | auto / full |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | 57.387626 | 54.748359 | 2.639267 | 4.60% | not_established | 16 / 1 / 16 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | dense_layer | 0 / 3 | 0.573069 | 0.577426 | 0.585758 | 0.354106 | -38.21% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | moe_layer | 0 / 75 | 0.745549 | 0.745723 | 0.781082 | 0.515446 | -30.86% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | dense_layer | 0 / 3 | 0.587706 | 0.567711 | 0.627936 | 0.354106 | -39.75% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | moe_layer | 0 / 75 | 0.747336 | 0.742162 | 0.785962 | 0.515446 | -31.03% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | dense_layer | 0 / 3 | 0.646681 | 0.655584 | 0.670978 | 0.451687 | -30.15% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | moe_layer | 0 / 75 | 0.901497 | 0.866973 | 1.013966 | 0.750335 | -16.77% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | mla | 0 / 78 | 0.738916 | 0.743060 | 0.781082 | 0.509241 | -31.08% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | mla | 0 / 78 | 0.741196 | 0.741208 | 0.785962 | 0.509241 | -31.29% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | mla | 0 / 78 | 0.891696 | 0.866537 | 1.013966 | 0.738849 | -17.14% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | mla | 0.738916 | 0.705473 | 0.033443 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | mla | 0.741196 | 0.707727 | 0.033469 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | mla | 0.891696 | 0.858594 | 0.033102 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | all | 77 | 3388 | 0.740905 | 0.713924 | 0.499693 | -30.01% |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | mla | 77 | 3388 | 0.740905 | 0.713924 | 0.499693 | -30.01% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | all | 77 | 3388 | 0.742667 | 0.714665 | 0.499693 | -30.08% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | mla | 77 | 3388 | 0.742667 | 0.714665 | 0.499693 | -30.08% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | all | 77 | 3773 | 0.894563 | 0.866817 | 0.725990 | -16.25% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | mla | 77 | 3773 | 0.894563 | 0.866817 | 0.725990 | -16.25% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 44 | 0.585758 | 0.542520 | 0.733755 | 0.354106 | -39.55% |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 44 | 0.627936 | 0.549071 | 0.813657 | 0.354106 | -43.61% |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 49 | 0.670978 | 0.621032 | 0.820996 | 0.451687 | -32.68% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 2 | 81.123653 | 76.399375 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot30_c2:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 2 | 81.123653 | 76.399375 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 2 | 80.812579 | 76.184906 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot50_c2:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 2 | 80.812579 | 76.184906 | — | 68.544460 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 6 | 8 | 48 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | 6 | 6 | 36 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | 6 | 3 | 18 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 8 | 94.443606 | 89.441874 | — | 87.944505 |

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
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | embedding | 49 | 0.006817 | 0.006780 | 0.007080 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | final_norm | 49 | 0.237354 | 0.236984 | 0.239424 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | lm_head | 49 | 0.175891 | 0.175883 | 0.177523 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | embedding | 4 | 0.003640 | 0.003670 | 0.003760 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | final_norm | 4 | 0.214025 | 0.213995 | 0.214944 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b1_m6 | lm_head | 4 | 0.128073 | 0.128013 | 0.129162 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | embedding | 3 | 0.004373 | 0.004380 | 0.004400 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | final_norm | 3 | 0.220524 | 0.221044 | 0.221585 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b2_m12 | lm_head | 3 | 0.144196 | 0.144463 | 0.145003 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | embedding | 2 | 0.009291 | 0.009291 | 0.009360 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | final_norm | 2 | 0.236475 | 0.236475 | 0.239465 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b6_m36 | lm_head | 2 | 0.179673 | 0.179673 | 0.180283 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | embedding | 2 | 0.005621 | 0.005621 | 0.005721 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | final_norm | 2 | 0.222944 | 0.222944 | 0.223365 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b3_m18 | lm_head | 2 | 0.171333 | 0.171333 | 0.171443 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | embedding | 1 | 0.007061 | 0.007061 | 0.007061 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | final_norm | 1 | 0.225365 | 0.225365 | 0.225365 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b4_m24 | lm_head | 1 | 0.163543 | 0.163543 | 0.163543 |

Summary: {"case_count": 10, "compared_cases": 3, "failed_cases": 0, "measured_cases": 10, "passed_cases": 0, "source_case_count": 3, "unresolved_cases": 7}
