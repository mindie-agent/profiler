# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "21c30821d87a757bace8cf6b2fffea2536db643e"}.

Variant: `glm78-low-complete-native-service`. Baseline: null.

Sim 0.8.0; 288 package files; SHA256 `9f88dac92812c58accec2c6416daa0ea181bd7e5d27b43d9046d1e843b7bfe10`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a3_glm53_dc16k_b1:q1_b1_m1 | 74 | 39.112085 | 39.104879 | 39.195917 | 38.334370 | -1.99% | compared |
| a3_glm53_dc4k_b1:q1_b1_m1 | 74 | 38.954827 | 38.942772 | 39.036040 | 38.046014 | -2.33% | compared |
| a3_glm53_dc4k_b2:q1_b2_m2 | 70 | 40.969878 | 40.934812 | 41.046340 | 39.766880 | -2.94% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; without separating that wait, elapsed time does not identify pure link bandwidth. The same observed boundary may calibrate per-call, per-group or payload-regime service responses. Explicit in-sample/heldout declarations are retained separately from contract eligibility; missing evaluation provenance remains not_declared.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a3_glm53_dc16k_b1:q1_b1_m1 | 39.112085 | 37.273101 | 1.838985 | 4.70% | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b1:q1_b1_m1 | 38.954827 | 37.243385 | 1.711442 | 4.39% | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b2:q1_b2_m2 | 40.969878 | 39.246789 | 1.723088 | 4.21% | not_established | 8 / 1 / 1 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | dense_layer | 3 / 3 | 0.396276 | 0.393697 | 0.402033 | 0.403677 | +1.87% |
| a3_glm53_dc16k_b1:q1_b1_m1 | moe_layer | 75 / 75 | 0.504482 | 0.483485 | 0.576161 | 0.494978 | -1.88% |
| a3_glm53_dc4k_b1:q1_b1_m1 | dense_layer | 3 / 3 | 0.387506 | 0.384723 | 0.394250 | 0.391821 | +1.11% |
| a3_glm53_dc4k_b1:q1_b1_m1 | moe_layer | 75 / 75 | 0.503075 | 0.484378 | 0.566864 | 0.491607 | -2.28% |
| a3_glm53_dc4k_b2:q1_b2_m2 | dense_layer | 3 / 3 | 0.403290 | 0.407802 | 0.410515 | 0.400055 | -0.80% |
| a3_glm53_dc4k_b2:q1_b2_m2 | moe_layer | 75 / 75 | 0.529285 | 0.509096 | 0.601701 | 0.514223 | -2.85% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 78 / 78 | 0.500321 | 0.482807 | 0.576161 | 0.491466 | -1.77% |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 78 / 78 | 0.498630 | 0.484310 | 0.566864 | 0.487769 | -2.18% |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 78 / 78 | 0.524439 | 0.508658 | 0.601701 | 0.509832 | -2.79% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 0.500321 | 0.477860 | 0.022460 |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 0.498630 | 0.477479 | 0.021151 |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 0.524439 | 0.503164 | 0.021275 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | all | 77 | 5698 | 0.501597 | 0.482860 | 0.472645 | -2.12% |
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 77 | 5698 | 0.501597 | 0.482860 | 0.472645 | -2.12% |
| a3_glm53_dc4k_b1:q1_b1_m1 | all | 77 | 5698 | 0.499986 | 0.484650 | 0.471904 | -2.63% |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 77 | 5698 | 0.499986 | 0.484650 | 0.471904 | -2.63% |
| a3_glm53_dc4k_b2:q1_b2_m2 | all | 77 | 5390 | 0.525918 | 0.508590 | 0.493756 | -2.92% |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 77 | 5390 | 0.525918 | 0.508590 | 0.493756 | -2.92% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | 74 | 0.402033 | 0.396682 | 0.411171 | 0.404202 | +0.54% |
| a3_glm53_dc4k_b1:q1_b1_m1 | 74 | 0.394250 | 0.385352 | 0.415732 | 0.392395 | -0.47% |
| a3_glm53_dc4k_b2:q1_b2_m2 | 70 | 0.410515 | 0.395952 | 0.454831 | 0.400703 | -2.39% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | 1 | 1 | 1 | unknown | 16384 | 1 | — | — | — | — |
| a3_glm53_dc4k_b1:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 1 | — | — | — | — |
| a3_glm53_dc4k_b2:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 2 | — | — | — | — |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | embedding | 74 | 0.007803 | 0.007780 | 0.007920 |
| a3_glm53_dc16k_b1:q1_b1_m1 | final_norm | 74 | 0.160420 | 0.160087 | 0.166337 |
| a3_glm53_dc16k_b1:q1_b1_m1 | lm_head | 74 | 0.221647 | 0.221575 | 0.223536 |
| a3_glm53_dc4k_b1:q1_b1_m1 | embedding | 74 | 0.007841 | 0.007839 | 0.007960 |
| a3_glm53_dc4k_b1:q1_b1_m1 | final_norm | 74 | 0.153796 | 0.153077 | 0.157037 |
| a3_glm53_dc4k_b1:q1_b1_m1 | lm_head | 74 | 0.216579 | 0.216606 | 0.217935 |
| a3_glm53_dc4k_b2:q1_b2_m2 | embedding | 70 | 0.002795 | 0.002780 | 0.003000 |
| a3_glm53_dc4k_b2:q1_b2_m2 | final_norm | 70 | 0.156513 | 0.156497 | 0.158957 |
| a3_glm53_dc4k_b2:q1_b2_m2 | lm_head | 70 | 0.227520 | 0.227626 | 0.229775 |

Summary: {"case_count": 3, "compared_cases": 3, "failed_cases": 0, "measured_cases": 3, "passed_cases": 3, "source_case_count": 3, "unresolved_cases": 0}
